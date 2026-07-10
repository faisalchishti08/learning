---
card: java
gi: 930
slug: parallel-gc
title: Parallel GC
---

## 1. What it is

Parallel GC (enabled with `-XX:+UseParallelGC`, and the default collector on many older JVM versions for server-class machines) uses the same fundamental algorithms as [Serial GC](0929-serial-gc.md) — copying for the young generation, mark-compact for the old — but spreads the actual marking, copying, and compacting work across multiple GC worker threads instead of just one. It is still a fully [stop-the-world](0936-stop-the-world-pauses.md) collector: every application thread halts for the duration of a collection, exactly as with Serial GC. The difference is entirely about how much wall-clock time that halt takes — with N worker threads sharing the load on an N-core machine, a given amount of GC work finishes roughly N times faster in wall-clock terms, even though the total amount of CPU work performed is similar to (often slightly more than) the single-threaded equivalent, due to coordination overhead.

## 2. Why & when

Parallel GC is designed to optimize for **throughput** — the total amount of application work completed per unit of time, counting GC overhead as pure loss to be minimized in aggregate — rather than for minimizing any individual pause's duration. This makes it a strong fit for batch jobs, offline data processing, and other workloads where occasional multi-hundred-millisecond (or longer) pauses are acceptable as long as the *overall* throughput is high, because CPU cores otherwise idle during a stop-the-world pause are instead put to work sharing that pause's cost. It is the wrong choice for latency-sensitive services — a web server or trading system that must bound the *worst-case* pause a single request might experience — because Parallel GC's pauses, while shorter than Serial GC's on the same hardware, are still full stop-the-world events whose duration still grows with heap and live-set size; a large heap under memory pressure can still produce pauses in the hundreds of milliseconds to seconds, which is precisely the problem concurrent, low-pause collectors like [G1](0932-g1-gc.md), [ZGC](0933-zgc.md), and [Shenandoah](0934-shenandoah.md) were built to solve.

## 3. Core concept

```
Application threads running...
        |
        v
[ALL APPLICATION THREADS STOPPED]
        |
        v
   GC worker thread 1  --\
   GC worker thread 2  ---> all working IN PARALLEL on the SAME collection
   GC worker thread 3  --/    (same copying / mark-compact algorithms as Serial GC,
   GC worker thread N  -/      just split across threads)
        |
        v
[APPLICATION THREADS RESUME]

Goal: maximize THROUGHPUT (total app work done / total time),
      not minimize any single pause's duration.
```

The algorithm performed is identical to Serial GC's — only the number of threads sharing the same stop-the-world work changes, which shortens wall-clock pause time roughly in proportion to available cores, at the cost of thread-coordination overhead.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Parallel GC pause with four worker threads sharing the same young or old generation collection work, compared against Serial GC's single thread">
  <text x="150" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Serial GC (1 thread)</text>
  <rect x="60" y="25" width="180" height="20" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="39" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">GC thread #1 -- long pause</text>

  <text x="470" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Parallel GC (4 threads)</text>
  <rect x="380" y="25" width="180" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="36" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GC thread #1</text>
  <rect x="380" y="45" width="180" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="56" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GC thread #2</text>
  <rect x="380" y="65" width="180" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="76" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GC thread #3</text>
  <rect x="380" y="85" width="180" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="96" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GC thread #4</text>
  <text x="470" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">same total work, shorter wall-clock pause</text>

  <line x1="330" y1="20" x2="330" y2="120" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both fully stop-the-world --</text>
  <text x="320" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Parallel just finishes the same</text>
  <text x="320" y="176" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">work faster using more cores</text>
</svg>

*Parallel GC performs the same stop-the-world algorithm as Serial GC, but splits the work across multiple threads to shorten wall-clock pause time.*

## 5. Runnable example

Scenario: measure Parallel GC's throughput characteristics starting with a basic multi-threaded collection baseline, then adding old-generation retention pressure, then comparing throughput and pause behavior directly against Serial GC on identical, sustained multi-core-friendly workloads.

### Level 1 — Basic

```java
public class ParallelGcBaseline {
    public static void main(String[] args) {
        for (int i = 0; i < 3_000_000; i++) {
            byte[] garbage = new byte[64];
        }
        System.out.println("done -- check -Xlog:gc for 'Pause Young (Parallel Scavenge)' events");
    }
}
```

**How to run:** `java -Xlog:gc -XX:+UseParallelGC ParallelGcBaseline.java` (JDK 17+).

Expected output shape:
```
[0.02s][info][gc] GC(0) Pause Young (Parallel Scavenge) ... 8M->1M(32M) 1.4ms
[0.04s][info][gc] GC(1) Pause Young (Parallel Scavenge) ... 9M->1M(32M) 1.2ms
...
done -- check -Xlog:gc for 'Pause Young (Parallel Scavenge)' events
```

Multiple GC worker threads copy the young generation's survivors simultaneously, which on a multi-core machine tends to produce shorter individual pauses than the equivalent single-threaded Serial GC collection would for the same amount of live data.

### Level 2 — Intermediate

```java
import java.util.*;

public class ParallelGcOldGenPressure {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 250_000; i++) {
            retained.add(new byte[200]);
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check the log for 'Pause Full (Parallel ...)' -- note multiple threads used");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx64m -XX:+UseParallelGC ParallelGcOldGenPressure.java` (JDK 17+).

Expected output shape:
```
[0.02s][info][gc] GC(0) Pause Young (Parallel Scavenge) ... 4M->1M(16M) 1.1ms
...
[0.28s][info][gc] GC(14) Pause Full (Parallel Old) ... 60M->22M(64M) 78ms
retained: 250000
check the log for 'Pause Full (Parallel ...)' -- note multiple threads used
```

The real-world concern added: the same forced full-collection scenario as Serial GC's old-generation example, but here the mark-compact work is distributed across the available GC worker threads, which — on a multi-core machine — tends to produce a noticeably shorter full-GC pause for the same retained-data volume than Serial GC's single-threaded equivalent.

### Level 3 — Advanced

```java
import java.util.*;

public class ParallelThroughputComparison {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.nanoTime();
        for (int i = 0; i < 500_000; i++) {
            retained.add(new byte[300]);
            if (i % 40_000 == 0) {
                for (int j = 0; j < 30_000; j++) {
                    byte[] churn = new byte[128];
                }
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("retained: " + retained.size() + ", elapsed: " + elapsedMs + "ms");
    }
}
```

**How to run:** compare with explicit thread counts to see the throughput effect scale: `java -Xlog:gc -Xmx128m -XX:+UseParallelGC -XX:ParallelGCThreads=1 ParallelThroughputComparison.java` versus `java -Xlog:gc -Xmx128m -XX:+UseParallelGC -XX:ParallelGCThreads=4 ParallelThroughputComparison.java` (JDK 17+, on a machine with at least 4 cores).

Expected output shape (illustrative):
```
(ParallelGCThreads=1): retained: 500000, elapsed: 790ms  -- effectively serial, coordination overhead for nothing
(ParallelGCThreads=4): retained: 500000, elapsed: 470ms  -- same work spread across 4 threads, less wall-clock time
```

The production-flavored hard case: explicitly constraining the worker-thread count demonstrates that Parallel GC's speedup comes specifically from spreading work across cores — with `ParallelGCThreads=1` it behaves like a slightly-worse Serial GC (paying coordination overhead with no parallelism benefit), while a higher thread count on genuinely available cores measurably improves total elapsed time, which is exactly the throughput-oriented tradeoff Parallel GC is designed around.

## 6. Walkthrough

Tracing `ParallelGcOldGenPressure.main` end to end:

1. The loop retains 250,000 small objects, none of which become garbage, so every young-generation collection this workload triggers must copy an ever-growing fraction of live data rather than reclaiming it.
2. Each young-generation pause stops all application threads and hands the copying work to the configured pool of GC worker threads (sized by `-XX:ParallelGCThreads`, defaulting to a value based on available cores) — each thread copies a share of the live objects into the target Survivor space concurrently with the others, then all resume together, and the application threads restart.
3. As objects survive enough young-generation collections, they are promoted into the old generation, which — driven by the small `-Xmx64m` cap — eventually fills.
4. A full collection triggers: the same multiple GC worker threads now perform the mark and compact phases across the entire heap in parallel, splitting the marking and relocation work by heap region rather than doing it single-threadedly — this is what the "Pause Full (Parallel Old)" log line reflects, and on a multi-core machine it completes faster in wall-clock time than Serial GC's equivalent single-threaded full collection, for the same underlying amount of work.
5. The program prints the retained count and exits, with the log evidence above showing multiple threads cooperating on both minor and full collections — confirming Parallel GC's core throughput-oriented design: use available cores to finish each stop-the-world pause faster, even though every application thread is still fully halted for its duration.

## 7. Gotchas & takeaways

> **Gotcha:** Parallel GC still fully stops every application thread for the duration of a collection — it optimizes wall-clock pause *duration* by using more threads, not pause *frequency* or the fact that a pause happens at all; for workloads that need bounded worst-case latency rather than high aggregate throughput, a concurrent collector like [G1](0932-g1-gc.md) is usually the better fit even though it has more coordination overhead.

- Parallel GC uses the identical copying (young) and mark-compact (old) algorithms as [Serial GC](0929-serial-gc.md), just spread across multiple GC worker threads instead of one.
- It is a throughput-oriented collector: it minimizes total time lost to GC across the whole run, not the duration of any individual pause.
- Every collection is still fully stop-the-world — all application threads halt for its entire duration, exactly as with Serial GC, just for less wall-clock time on a multi-core machine.
- `-XX:ParallelGCThreads=N` controls the worker pool size; too few threads on a large heap wastes available parallelism, while setting it to 1 makes it behave like a slightly slower Serial GC.
- Best suited to batch and throughput-sensitive workloads that can tolerate occasional multi-hundred-millisecond pauses; latency-sensitive services should generally prefer [G1](0932-g1-gc.md), [ZGC](0933-zgc.md), or [Shenandoah](0934-shenandoah.md) instead.
