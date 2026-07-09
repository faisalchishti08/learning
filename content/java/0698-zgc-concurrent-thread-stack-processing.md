---
card: java
gi: 698
slug: zgc-concurrent-thread-stack-processing
title: ZGC concurrent thread-stack processing
---

## 1. What it is

**Java 16** taught **ZGC** to process **thread stacks concurrently** rather than during a stop-the-world pause (JEP 376). Garbage collectors need to scan each application thread's stack to find **GC roots** — local variables that reference heap objects, which anchor those objects as reachable. Before this change, even ZGC (a collector otherwise designed around minimizing stop-the-world pauses) had to briefly pause each thread to scan its stack safely, since a thread's stack changes constantly as it executes. Java 16 moved this stack-scanning work to run **concurrently**, while application threads continue executing, removing one of the last remaining sources of stop-the-world pause time in ZGC's design.

## 2. Why & when

ZGC's whole design philosophy is minimizing pause times so they don't scale with heap size, but stack scanning had remained an exception: because a thread's stack is actively being read from and written to by that very thread while it runs, safely scanning it traditionally required briefly stopping the thread first, to guarantee the collector sees a consistent snapshot rather than a stack mutating mid-scan. As applications used more threads (common in highly concurrent server workloads), the cumulative pause time spent stopping every thread to scan its stack became a larger and larger fraction of ZGC's total pause time, working against the exact goal ZGC exists to achieve. This JEP applied a technique to make stack scanning safe to perform concurrently, without stopping the owning thread — closing this gap and making ZGC's pauses even less dependent on the number of live threads. This is, like [Elastic Metaspace](0697-elastic-metaspace.md), an internal collector implementation improvement with no application-facing API — but it's directly relevant to any application already choosing ZGC for latency-sensitive workloads with many threads, since it further reduces pause times exactly there.

## 3. Core concept

```bash
# No new flags or APIs — this is an internal ZGC algorithm improvement
java -XX:+UseZGC -Xlog:gc,gc+phases -Xmx8g MyApp

# Compare pause-time logs before/after this change conceptually:
# Pre-Java 16 ZGC: pause time includes a "stop threads to scan stacks" component
# Java 16+ ZGC: stack scanning happens concurrently; pauses shrink further
```

You observe the benefit through GC pause-time logs and phase timings, not through any new code you write — the improvement lives entirely inside ZGC's implementation.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 16, ZGC stopped each application thread briefly to scan its stack; Java 16 lets stack scanning run concurrently without stopping threads">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before Java 16</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thread stops briefly</text>
  <text x="160" y="90" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">stack scanned (paused)</text>
  <text x="160" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thread resumes</text>
  <text x="160" y="145" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">pause scales with thread count</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16+</text>
  <text x="480" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thread keeps running</text>
  <text x="480" y="90" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">stack scanned concurrently</text>
  <text x="480" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">no separate pause needed</text>
  <text x="480" y="145" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">pause less dependent on thread count</text>
</svg>

The same stack-scanning work happens either as a brief per-thread pause or concurrently alongside continued execution.

## 5. Runnable example

Scenario: a multi-threaded workload with many active threads under ZGC — first a baseline with a handful of threads doing allocation-heavy work while logging GC pause times, then scaling up the thread count substantially to see whether pause times grow with thread count, then a small harness that reports both total GC pause time and thread count together for a clear before/after-style comparison an operator could use when evaluating ZGC across releases.

### Level 1 — Basic

```java
// File: FewThreadsWorkload.java
import java.util.concurrent.CountDownLatch;

public class FewThreadsWorkload {
    public static void main(String[] args) throws InterruptedException {
        int threadCount = 4;
        CountDownLatch done = new CountDownLatch(threadCount);
        long start = System.nanoTime();

        for (int t = 0; t < threadCount; t++) {
            new Thread(() -> {
                byte[][] buffers = new byte[1000][];
                for (int round = 0; round < 2000; round++) {
                    for (int i = 0; i < buffers.length; i++) {
                        buffers[i] = new byte[512];
                    }
                }
                done.countDown();
            }).start();
        }

        done.await();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Threads: " + threadCount + ", elapsed: " + elapsedMs + " ms");
    }
}
```

**How to run:**
```
java -XX:+UseZGC -Xlog:gc -Xmx1g FewThreadsWorkload.java
```

Expected output shape (GC log lines interleaved with the final result; exact timings and the specific collection trigger reason vary by run):
```
[0.380s][info][gc] GC(3) Garbage Collection (Allocation Stall) 1024M(100%)->34M(3%)
...
Threads: 4, elapsed: 160 ms
```

### Level 2 — Intermediate

```java
// File: ManyThreadsWorkload.java
import java.util.concurrent.CountDownLatch;

public class ManyThreadsWorkload {
    public static void main(String[] args) throws InterruptedException {
        int threadCount = 200;
        CountDownLatch done = new CountDownLatch(threadCount);
        long start = System.nanoTime();

        for (int t = 0; t < threadCount; t++) {
            new Thread(() -> {
                byte[][] buffers = new byte[50][];
                for (int round = 0; round < 200; round++) {
                    for (int i = 0; i < buffers.length; i++) {
                        buffers[i] = new byte[512];
                    }
                }
                done.countDown();
            }).start();
        }

        done.await();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Threads: " + threadCount + ", elapsed: " + elapsedMs + " ms");
    }
}
```

**How to run with pause-time logging:**
```
java -XX:+UseZGC -Xlog:gc,safepoint -Xmx1g ManyThreadsWorkload.java
```

Expected output shape (200 threads now active concurrently; the `-Xlog:gc,safepoint` output shows individual safepoint operations like `XMarkEnd` and `XRelocateStart` with their own timings — ZGC's concurrent stack scanning means the increase in thread count does not translate into a proportional increase in stop-the-world pause time):
```
[0.235s][info][safepoint] Safepoint "XMarkEnd", Time since last: 5247750 ns, Reaching safepoint: 4170333 ns, Cleanup: 2250 ns, At safepoint: 18958 ns, Total: 4191541 ns
[0.260s][info][gc       ] GC(0) Garbage Collection (Warmup) 278M(27%)->674M(66%)
...
Threads: 200, elapsed: 64 ms
```

### Level 3 — Advanced

```java
// File: ThreadScalingReport.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.concurrent.CountDownLatch;
import java.util.List;

public class ThreadScalingReport {
    static long totalGcTime() {
        return ManagementFactory.getGarbageCollectorMXBeans().stream()
                .filter(b -> b.getName().contains("ZGC"))
                .mapToLong(GarbageCollectorMXBean::getCollectionTime)
                .sum();
    }

    static long runWorkload(int threadCount) throws InterruptedException {
        CountDownLatch done = new CountDownLatch(threadCount);
        for (int t = 0; t < threadCount; t++) {
            new Thread(() -> {
                byte[][] buffers = new byte[200][];
                for (int round = 0; round < 500; round++) {
                    for (int i = 0; i < buffers.length; i++) {
                        buffers[i] = new byte[512];
                    }
                }
                done.countDown();
            }).start();
        }
        done.await();
        return totalGcTime();
    }

    public static void main(String[] args) throws InterruptedException {
        int[] threadCounts = { 10, 50, 200 };
        long previousGcTime = totalGcTime();

        for (int count : threadCounts) {
            long gcTimeAfter = runWorkload(count);
            long delta = gcTimeAfter - previousGcTime;
            System.out.println("Threads=" + count + ": cumulative GC time delta=" + delta + "ms");
            previousGcTime = gcTimeAfter;
        }
    }
}
```

**How to run:**
```
java -XX:+UseZGC -Xmx1g ThreadScalingReport.java
```

Expected output shape (note that each thread performs the same fixed amount of allocation, so total allocation volume also scales with thread count — the interesting signal is that the GC time delta grows *sub-linearly* relative to that volume, e.g. a 4x jump in thread count from 50 to 200 produces roughly a 2x jump in GC time, not 4x, consistent with per-thread stack-scanning no longer being a proportional per-thread cost):
```
Threads=10: cumulative GC time delta=0ms
Threads=50: cumulative GC time delta=96ms
Threads=200: cumulative GC time delta=197ms
```

## 6. Walkthrough

1. `ThreadScalingReport.main` iterates over three increasing thread counts (`10`, `50`, `200`), calling `runWorkload(count)` for each and tracking `totalGcTime()`'s cumulative value before and after each run.
2. Inside `runWorkload`, `count` threads are launched, each running an identical small allocation loop (30 buffers of 512 bytes, refreshed 100 times), and a `CountDownLatch` ensures `main` waits for every thread in that wave to finish before measuring GC time again.
3. `totalGcTime()` sums `getCollectionTime()` across every `GarbageCollectorMXBean` whose name contains `"ZGC"` (matching however many beans this specific JDK version exposes for ZGC — one or several, depending on version, as discussed in [ZGC production-ready](0683-zgc-production-ready.md)) — giving the cumulative milliseconds ZGC has spent collecting since JVM startup, at the moment each call is made.
4. For each thread count in turn, the delta between the cumulative GC time *after* that wave's workload and the cumulative GC time recorded *before* it isolates roughly how much collection time that specific wave's allocation pressure (and its accompanying stack-scanning work, across however many threads were active) contributed.
5. Because each thread performs the same fixed amount of allocation work, increasing `threadCount` also increases the *total* allocation volume across the wave — so collection time isn't expected to stay perfectly flat. What Java 16's concurrent thread-stack scanning changes is that the **per-thread cost of scanning that thread's stack** no longer requires stopping it, so the growth in collection time as thread count rises should track roughly with total allocation volume, not be inflated by an additional, separate per-thread stack-scanning pause cost stacking on top. In the sample run above, a 4x increase in thread count (50 to 200) produced only around a 2x increase in GC time delta — a sub-linear relationship consistent with stack-scanning no longer adding a proportional per-thread tax.
6. Each wave's result line — thread count alongside the GC time delta attributable to it — is printed, giving a simple, three-point empirical picture of how (little) GC overhead scales with thread count under ZGC on Java 16+.

```
for threadCount in [10, 50, 200]:
    launch threadCount threads, each allocating a bounded amount
    wait for all to finish (CountDownLatch)
    measure delta in cumulative ZGC collection time
    print threadCount alongside that delta
```

## 7. Gotchas & takeaways

> The GC-time deltas measured here reflect **collection time only** (via `GarbageCollectorMXBean.getCollectionTime()`), not the separate, harder-to-measure-from-pure-Java concept of "stop-the-world pause time specifically attributable to stack scanning." A precise before/after comparison of this specific JEP's benefit is better done via `-Xlog:gc,safepoint` and vendor profiling tools than by application-level `MemoryMXBean`/`GarbageCollectorMXBean` measurements alone — treat this tutorial's numbers as illustrative of the qualitative pattern, not a rigorous benchmark.

- This is an **internal ZGC implementation change** with no new application-facing API — you can't "turn on" concurrent thread-stack scanning separately from ZGC itself; it's simply how ZGC's stack scanning works from Java 16 onward.
- The benefit scales with **thread count**: applications with many concurrently active threads (highly concurrent server workloads, thread-per-request architectures) benefit more than single- or few-threaded applications, where stack-scanning pause time was never a large contributor to begin with.
- This JEP, alongside [Elastic Metaspace](0697-elastic-metaspace.md) in the very same release, reflects a broader pattern of incremental, implementation-level JVM improvements that require no application code changes yet directly improve production behavior once you're running on the newer JDK.
- If evaluating whether to upgrade a latency-sensitive, high-thread-count ZGC-based service specifically for this improvement, the most reliable approach is comparing real `-Xlog:gc,safepoint` pause-time logs from representative production-like load on both JDK versions, rather than relying on a synthetic microbenchmark.
- ZGC's design continued evolving in JDK releases after Java 16 (including a later shift to a generational architecture) — treat any specific internal mechanism described here as accurate to the Java 16 era specifically, not necessarily a permanent characteristic of all future ZGC versions.
