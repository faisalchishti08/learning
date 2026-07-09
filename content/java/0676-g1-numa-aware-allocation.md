---
card: java
gi: 676
slug: g1-numa-aware-allocation
title: G1 NUMA-aware allocation
---

## 1. What it is

**Java 14** taught the **G1 garbage collector** to be **NUMA-aware** (JEP 345, "NUMA-Aware Memory Allocation for G1"). NUMA stands for **Non-Uniform Memory Access** — a hardware design used in most modern multi-socket servers where each CPU socket has its own bank of "local" memory that it can read and write quickly, plus access to other sockets' "remote" memory that is slower to reach because the request has to cross an interconnect between sockets. Before Java 14, G1 allocated new objects into young-generation regions without any awareness of this layout, so a thread running on socket 0 could easily end up allocating into memory physically attached to socket 1 — every access to that object then paid a remote-memory penalty. G1's NUMA support (a technique the older **Parallel GC** already had) makes G1 place a thread's new allocations into memory local to the socket that thread is running on, whenever the JVM detects it is running on a NUMA system with `-XX:+UseG1GC -XX:+UseNUMA`.

## 2. Why & when

Large heaps on multi-socket hardware are exactly where G1 is most commonly deployed — it was designed as the default collector for server-class applications with several gigabytes of heap. On such hardware, the difference between local and remote memory access latency can be substantial (often 20–50% slower for remote access, sometimes more depending on the interconnect), and that penalty is paid on every single field read or write of an object stored in remote memory. Since young-generation objects are, by definition, the ones being actively allocated and mutated right now, misplacing them onto the wrong socket is one of the costlier possible memory-layout mistakes a collector can make. Reach for `-XX:+UseNUMA` alongside G1 when you're running a heap-heavy Java service on a multi-socket (or multi-die) server — database engines, in-memory caches, large application servers — and you have `numactl --hardware` (Linux) or equivalent confirming more than one NUMA node is present. On a single-socket machine, laptop, or container restricted to one NUMA node, the flag is a harmless no-op since there is no "remote" memory to avoid.

## 3. Core concept

```bash
# Before Java 14: NUMA-aware allocation only available with the (now largely legacy) Parallel GC
java -XX:+UseParallelGC -XX:+UseNUMA -Xmx8g MyApp

# Java 14 onward: the same NUMA-awareness, now available for G1 — the modern default collector
java -XX:+UseG1GC -XX:+UseNUMA -Xmx8g MyApp
```

Internally, G1 achieves this by tracking, per NUMA node, a pool of young-generation regions considered "local" to that node. When a thread running on a given CPU requests memory for a new object, G1's allocator first tries to hand out a region from the pool associated with that thread's current NUMA node (determined via the OS's NUMA APIs), falling back to any available region only if no local one exists. Old-generation and humongous regions are not NUMA-managed this way, since those objects tend to be longer-lived and accessed by varying threads over time, making a single "home node" less meaningful.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two NUMA nodes each with local memory; G1 places each thread's allocations into its own node's local regions instead of a remote node">
  <rect x="20" y="20" width="280" height="220" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">NUMA Node 0</text>
  <rect x="40" y="60" width="100" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="90" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CPU thread A</text>
  <rect x="160" y="60" width="100" height="40" rx="6" fill="#161b22" stroke="#8b949e"/>
  <text x="210" y="85" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Local RAM</text>
  <line x1="140" y1="80" x2="158" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="150" y="115" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">fast: local G1</text>
  <text x="150" y="127" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">young regions</text>

  <rect x="340" y="20" width="280" height="220" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">NUMA Node 1</text>
  <rect x="360" y="60" width="100" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="410" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CPU thread B</text>
  <rect x="480" y="60" width="100" height="40" rx="6" fill="#161b22" stroke="#8b949e"/>
  <text x="530" y="85" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Local RAM</text>
  <line x1="460" y1="80" x2="478" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#a2)"/>

  <line x1="90" y1="100" x2="410" y2="100" stroke="#f85149" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="250" y="150" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">slow cross-socket path — G1 now avoids this</text>
  <text x="250" y="163" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">for new object allocation</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Each thread allocates into young-generation regions on its own NUMA node's local memory, instead of regions that happen to sit on a remote socket.

## 5. Runnable example

Scenario: a service that reports which CPU/NUMA topology it's running on, then runs an allocation-heavy workload representative of request processing, then adds timing instrumentation to compare behavior with and without NUMA awareness enabled — the same allocation workload maturing from "just run it" to "actually measure whether the flag matters."

### Level 1 — Basic

```java
// File: TopologyCheck.java
public class TopologyCheck {
    public static void main(String[] args) {
        int cpus = Runtime.getRuntime().availableProcessors();
        System.out.println("Available CPUs visible to JVM: " + cpus);
        System.out.println("Max heap: " + (Runtime.getRuntime().maxMemory() / (1024 * 1024)) + " MB");
        System.out.println("To check NUMA nodes on Linux, run: numactl --hardware");
    }
}
```

**How to run:**
```
java -XX:+UseG1GC -XX:+UseNUMA TopologyCheck.java
```

Expected output (on an 8-core, single-socket dev machine):
```
Available CPUs visible to JVM: 8
Max heap: 4096 MB
To check NUMA nodes on Linux, run: numactl --hardware
```

This just confirms the JVM starts cleanly with the flags. On a single-node machine, `-XX:+UseNUMA` is silently a no-op — there's nothing "remote" to avoid — so this level doesn't yet prove NUMA placement is happening, only that the flags are accepted.

### Level 2 — Intermediate

```java
// File: AllocationWorkload.java
import java.util.concurrent.CountDownLatch;

public class AllocationWorkload {
    public static void main(String[] args) throws InterruptedException {
        int threadCount = Runtime.getRuntime().availableProcessors();
        CountDownLatch done = new CountDownLatch(threadCount);
        long start = System.nanoTime();

        for (int t = 0; t < threadCount; t++) {
            new Thread(() -> {
                byte[][] buffers = new byte[2000][];
                for (int round = 0; round < 500; round++) {
                    for (int i = 0; i < buffers.length; i++) {
                        buffers[i] = new byte[4096]; // simulate per-request allocation
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

**How to run, with GC logging so region behavior is visible:**
```
java -XX:+UseG1GC -XX:+UseNUMA -Xlog:gc -Xmx2g AllocationWorkload.java
```

Expected output:
```
[0.041s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 128M->24M(2048M) 6.201ms
[0.098s][info][gc] GC(1) Pause Young (Normal) (G1 Evacuation Pause) 152M->31M(2048M) 5.884ms
...
Threads: 8, elapsed: 742 ms
```

Each thread now allocates heavily and concurrently, which is what actually gives NUMA-aware placement something to do: on a multi-socket machine, G1 tries to satisfy each thread's `new byte[4096]` calls from young-generation regions local to whatever NUMA node that thread is currently scheduled on, rather than handing out whichever region happens to be free next.

### Level 3 — Advanced

```java
// File: NumaComparison.java
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;

public class NumaComparison {
    public static void main(String[] args) throws InterruptedException {
        int threadCount = Math.max(4, Runtime.getRuntime().availableProcessors());
        AtomicLong totalOps = new AtomicLong();
        CountDownLatch done = new CountDownLatch(threadCount);
        long start = System.nanoTime();

        for (int t = 0; t < threadCount; t++) {
            final int threadId = t;
            Thread worker = new Thread(() -> {
                long ops = 0;
                byte[][] buffers = new byte[1000][];
                for (int round = 0; round < 300; round++) {
                    for (int i = 0; i < buffers.length; i++) {
                        buffers[i] = new byte[2048];
                        buffers[i][0] = (byte) (threadId + round); // touch memory: forces real access, not just allocation
                        ops++;
                    }
                }
                totalOps.addAndGet(ops);
                done.countDown();
            }, "worker-" + t);
            worker.start();
        }

        done.await();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        double opsPerMs = totalOps.get() / (double) Math.max(1, elapsedMs);
        System.out.println("Threads: " + threadCount);
        System.out.println("Total allocations+touches: " + totalOps.get());
        System.out.println("Elapsed: " + elapsedMs + " ms");
        System.out.printf("Throughput: %.1f ops/ms%n", opsPerMs);
    }
}
```

**How to run, comparing with and without NUMA awareness on the same multi-socket machine:**
```
java -XX:+UseG1GC -XX:+UseNUMA -Xmx4g NumaComparison.java
java -XX:+UseG1GC -XX:-UseNUMA -Xmx4g NumaComparison.java
```

Expected output shape (exact numbers depend on hardware; on a genuine multi-socket NUMA machine the `-UseNUMA` run is typically measurably slower because more allocations land on remote-node memory):
```
Threads: 16
Total allocations+touches: 4800000
Elapsed: 1180 ms
Throughput: 4067.8 ops/ms
```
```
Threads: 16
Total allocations+touches: 4800000
Elapsed: 1450 ms
Throughput: 3310.3 ops/ms
```

This level not only allocates but **touches** each buffer (`buffers[i][0] = ...`), which is essential: allocation alone can be satisfied lazily by the OS, but writing to the memory forces the actual physical page to be resident and the cross-socket latency (if any) to be paid, making the comparison between `+UseNUMA` and `-UseNUMA` meaningful rather than measuring noise.

## 6. Walkthrough

1. `main` computes `threadCount` from `Runtime.getRuntime().availableProcessors()`, ensuring at least 4 worker threads regardless of core count, then records a `start` timestamp with `System.nanoTime()` before launching anything.
2. For each thread index `t`, a `Thread` named `"worker-N"` is created and immediately `.start()`-ed. The OS scheduler assigns each of these threads to run on some CPU core, which in turn belongs to some NUMA node — on a two-socket machine, roughly half the threads end up scheduled on node 0's cores and half on node 1's, though the exact assignment is up to the OS scheduler and can shift over time.
3. Inside each thread's body, a local `byte[1000][]` array (`buffers`) holds references to the objects this thread is about to churn through. The nested loop runs 300 rounds, and in each round it replaces every slot in `buffers` with a freshly allocated `new byte[2048]`.
4. **This is the critical moment G1's NUMA awareness affects:** when `new byte[2048]` executes, the JVM's allocator (specifically, the thread-local allocation buffer, or TLAB, mechanism G1 uses to hand out memory to threads without needing a global lock on every allocation) asks G1 for space. With `-XX:+UseNUMA` active and multiple NUMA nodes detected, G1 consults which node the *current* thread is running on and preferentially serves the request from a young-generation region whose physical memory lives on that same node. Without the flag (or on single-node hardware), G1 just hands out the next available region with no regard for topology.
5. Immediately after allocating, the code writes `buffers[i][0] = (byte) (threadId + round)` — a real memory write. This line exists specifically so the JVM (and the OS) cannot defer the page's physical placement; the write forces the byte to actually land in RAM, on whichever NUMA node that memory page is backed by. If that page is on a remote node relative to the CPU core the thread is running on, this write (and any future read of that buffer) pays the cross-socket latency penalty shown as the dashed red path in the diagram in part 4.
6. Each thread accumulates its own `ops` counter and, on finishing all 300 rounds, adds it to the shared `totalOps` (an `AtomicLong`, safe for concurrent increments from multiple threads) and calls `done.countDown()` on the shared `CountDownLatch`.
7. `main`'s `done.await()` blocks until every worker thread has called `countDown()`, guaranteeing all allocation work is finished before timing stops. `elapsedMs` is then computed from the same `start` timestamp taken in step 1, and `opsPerMs` is derived by dividing total operations by elapsed milliseconds — a simple throughput figure.
8. The two invocations shown (`+UseNUMA` vs `-UseNUMA`) run the identical program with only the flag flipped; on genuine multi-socket hardware, comparing the two `Throughput` lines is the concrete, empirical way to observe the benefit JEP 345 delivers — more allocations satisfied from local rather than remote memory typically shows up as a measurably higher ops/ms figure with the flag enabled.

```
worker thread ──► new byte[2048] ──► G1 TLAB allocator
                                          │
                            "which NUMA node is this thread on?"
                                          │
                       ┌──────────────────┴──────────────────┐
                       ▼                                     ▼
              local node has free                   local node full ──►
              young region? ── yes ──► serve from it   fall back to any
                                                        available region
```

## 7. Gotchas & takeaways

> `-XX:+UseNUMA` only has an effect if the JVM actually detects **more than one NUMA node** at startup — on a single-socket machine, a laptop, or a container/VM that has been pinned to one NUMA node by the orchestrator, the flag is accepted but does nothing observable. Don't expect a throughput difference from Level 3's comparison unless you genuinely run it on multi-socket hardware with `numactl --hardware` reporting more than one node.

- G1 gained NUMA awareness in Java 14 (JEP 345); Parallel GC already had it long before — this closed a long-standing capability gap between the two collectors.
- Only young-generation region allocation is NUMA-managed; old-generation and humongous-object regions are not, since those objects' access patterns don't map cleanly to a single "home" thread or node.
- The flag is a genuine no-op (not a slowdown) on non-NUMA hardware, so it is generally safe to include in a server's default JVM flags without needing per-environment conditionals.
- To see the effect for real, force the allocated memory to actually be touched (written to), as Level 3 does — measuring allocation speed alone can be misleading because physical page placement can be deferred by the OS until first write.
- Confirm your hardware's NUMA topology first (`numactl --hardware` on Linux, or platform-equivalent tools) before drawing conclusions from a benchmark — running the comparison on single-node hardware will correctly show no difference and should not be read as the feature "not working."
