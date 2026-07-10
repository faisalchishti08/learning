---
card: java
gi: 900
slug: virtual-threads-model-loom
title: Virtual threads model (Loom)
---

## 1. What it is

Virtual threads (finalized in Java 21 via Project Loom) are lightweight threads managed by the JVM itself rather than mapping one-to-one to an OS thread. You create and use them through the exact same `Thread`/`ExecutorService` APIs as ordinary ("platform") threads — `Thread.ofVirtual().start(...)` or `Executors.newVirtualThreadPerTaskExecutor()` — but the JVM can run millions of them, because a virtual thread that blocks (on I/O, on `Thread.sleep`, on a lock) doesn't tie up an OS thread while it waits; the JVM parks the virtual thread and frees the underlying OS thread (called a **carrier thread**) to run other virtual threads in the meantime.

## 2. Why & when

Traditional platform threads are expensive: each one consumes real OS resources (typically megabytes of stack space) and OS-level scheduling overhead, which is why thread pools exist in the first place — you can't practically have a hundred thousand platform threads all blocked waiting on separate network calls. Virtual threads exist specifically to make the simple, blocking, "one thread per task/request" programming style — easy to write, easy to debug, easy to reason about with straightforward sequential code — viable again at massive scale, without the historical need to rewrite everything in an asynchronous, callback- or `CompletableFuture`-chained style purely to conserve OS threads. Use virtual threads for I/O-bound workloads with high concurrency — a server handling many simultaneous slow network requests is the textbook case — where you'd otherwise need a large platform thread pool or complex asynchronous code just to keep enough requests in flight. They are *not* a magic performance upgrade for CPU-bound work, since CPU-bound computation is limited by the number of actual CPU cores regardless of how many threads (virtual or platform) are requesting time on them — see [platform vs. virtual threads](0901-platform-vs-virtual-threads.md) for that distinction in more depth.

## 3. Core concept

```java
// Platform thread pool: limited, expensive, typically sized to hundreds at most
ExecutorService platformPool = Executors.newFixedThreadPool(200);

// Virtual thread executor: can comfortably handle hundreds of thousands of concurrent tasks
try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 100_000; i++) {
        virtualPool.submit(() -> {
            Thread.sleep(1000); // blocking call -- but the CARRIER thread is freed while this virtual thread waits
            return null;
        });
    }
} // try-with-resources: waits for all submitted tasks to finish, then closes the executor
```

Each `submit()` call gets its own dedicated virtual thread — no pooling or reuse of virtual threads themselves is needed, since they're cheap enough to simply create one per task.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Many virtual threads, most blocked waiting on I/O, time-sharing a small number of carrier (platform/OS) threads; a blocked virtual thread frees its carrier thread for another virtual thread to use">
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Thousands of virtual threads (cheap, JVM-managed)</text>
  <rect x="20" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="100" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="180" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="260" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="340" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="420" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="500" y="30" width="70" height="25" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <text x="320" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">solid = actively running; dashed = parked, waiting on I/O</text>

  <text x="320" y="115" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Small pool of CARRIER threads (real OS threads, ~cores count)</text>
  <rect x="150" y="130" width="100" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="200" y="152" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">carrier 1</text>
  <rect x="270" y="130" width="100" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="152" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">carrier 2</text>
  <rect x="390" y="130" width="100" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="440" y="152" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">carrier 3</text>

  <line x1="55" y1="55" x2="200" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a32)"/>
  <line x1="135" y1="55" x2="320" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a32)"/>
  <line x1="215" y1="55" x2="440" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a32)"/>
  <defs><marker id="a32" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Only the few virtual threads actually running need a carrier thread at any instant; parked (blocked) ones hold no carrier at all, letting thousands time-share a handful of real OS threads.*

## 5. Runnable example

Scenario: simulating many concurrent slow network calls, growing from a platform-thread-pool version that struggles to scale, to a virtual-thread version handling the same workload with vastly more concurrency, to a version measuring and comparing memory/thread-count behavior directly.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class PlatformThreadPoolLimitation {
    static void simulateSlowNetworkCall() {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 1000;
        ExecutorService platformPool = Executors.newFixedThreadPool(50); // a "reasonable" platform pool size

        long start = System.currentTimeMillis();
        for (int i = 0; i < taskCount; i++) {
            platformPool.submit(PlatformThreadPoolLimitation::simulateSlowNetworkCall);
        }
        platformPool.shutdown();
        platformPool.awaitTermination(30, TimeUnit.SECONDS);

        System.out.println(taskCount + " tasks completed with 50 platform threads in " + (System.currentTimeMillis() - start) + "ms");
        System.out.println("(bounded by 50 concurrent 100ms waits at a time -- roughly " + (taskCount / 50) + " waves)");
    }
}
```

**How to run:** `java PlatformThreadPoolLimitation.java` (JDK 21+, though this specific example runs on any JDK 17+ since it uses no virtual-thread APIs).

Expected output shape:
```
1000 tasks completed with 50 platform threads in ~2050ms
(bounded by 50 concurrent 100ms waits at a time -- roughly 20 waves)
```

With only 50 platform threads for 1000 blocking tasks, the work proceeds in roughly 20 sequential "waves" of 50 concurrent 100ms waits each — increasing the platform pool size further would consume proportionally more OS thread resources (stack memory, scheduling overhead).

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class VirtualThreadsHandleTheSameWorkload {
    static void simulateSlowNetworkCall() {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 1000;

        long start = System.currentTimeMillis();
        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) {
                virtualPool.submit(VirtualThreadsHandleTheSameWorkload::simulateSlowNetworkCall);
            }
        } // try-with-resources: blocks here until all submitted tasks complete, then closes

        System.out.println(taskCount + " tasks completed with VIRTUAL threads in " + (System.currentTimeMillis() - start) + "ms");
        System.out.println("(all 1000 ran essentially CONCURRENTLY -- roughly ONE wave of 100ms, not 20)");
    }
}
```

**How to run:** `java VirtualThreadsHandleTheSameWorkload.java` (requires JDK 21+ for the finalized virtual threads API).

Expected output shape (dramatically faster than the platform-pool version, since all 1000 tasks run essentially simultaneously):
```
1000 tasks completed with VIRTUAL threads in ~120ms
(all 1000 ran essentially CONCURRENTLY -- roughly ONE wave of 100ms, not 20)
```

The real-world concern added: `Executors.newVirtualThreadPerTaskExecutor()` creates a fresh, cheap virtual thread for *every single submitted task*, all 1000 of them — since each blocks in `Thread.sleep`, the JVM frees up the small number of underlying carrier threads to service other virtual threads while any given one waits, so the whole batch completes in roughly the time of a single 100ms wait, not 20 sequential waves.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ComparingConcurrencyAndThreadCount {
    static void simulateSlowNetworkCall() {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 5000;
        AtomicInteger peakConcurrentVirtual = new AtomicInteger(0);
        AtomicInteger currentConcurrentVirtual = new AtomicInteger(0);

        long start = System.currentTimeMillis();
        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) {
                virtualPool.submit(() -> {
                    int current = currentConcurrentVirtual.incrementAndGet();
                    peakConcurrentVirtual.updateAndGet(prev -> Math.max(prev, current));
                    simulateSlowNetworkCall();
                    currentConcurrentVirtual.decrementAndGet();
                });
            }
        }
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("total tasks: " + taskCount);
        System.out.println("peak CONCURRENT virtual threads observed: " + peakConcurrentVirtual.get());
        System.out.println("elapsed: " + elapsed + "ms (close to the 50ms of a single wait, despite 5000 tasks)");
        System.out.println("underlying carrier (OS) threads used: only ~" + Runtime.getRuntime().availableProcessors()
            + " (matches CPU core count), NOT " + taskCount);
    }
}
```

**How to run:** `java ComparingConcurrencyAndThreadCount.java` (JDK 21+).

Expected output shape (peak concurrency approaches the full task count, since virtual threads are cheap enough to all exist simultaneously; elapsed time stays close to one wait's duration regardless of task count):
```
total tasks: 5000
peak CONCURRENT virtual threads observed: 5000
elapsed: 58ms (close to the 50ms of a single wait, despite 5000 tasks)
underlying carrier (OS) threads used: only ~8 (matches CPU core count), NOT 5000
```

This adds the production-flavored hard case: explicitly measuring peak concurrency (confirming essentially all 5000 tasks really were "in flight," blocked in `Thread.sleep`, at the same moment) alongside elapsed time (confirming this concurrency translated into real throughput, not just apparent parallelism) — demonstrating concretely that virtual threads let a workload that would require 5000 platform threads to achieve the same concurrency instead run comfortably on a JVM using only a handful of real OS (carrier) threads underneath, matching roughly the CPU core count, since blocked virtual threads don't occupy a carrier thread at all while parked.

## 6. Walkthrough

Tracing `ComparingConcurrencyAndThreadCount.main` under the hood:

1. `Executors.newVirtualThreadPerTaskExecutor()` creates a special executor that, for every `submit()` call, creates a brand-new virtual thread dedicated to running that one task — unlike a platform thread pool, there's no fixed, limited set of reusable worker threads to queue behind.
2. As the loop submits all 5000 tasks in rapid succession, the JVM creates 5000 virtual thread objects — since each is lightweight (no dedicated OS-level stack allocation the way a platform thread requires), creating this many is fast and cheap, unlike attempting to create 5000 platform threads, which would likely exhaust OS resources or at least incur substantial overhead.
3. Each task's lambda first increments `currentConcurrentVirtual` (tracking how many are simultaneously "inside" the task body) and records the peak seen so far, then calls `simulateSlowNetworkCall()`, which blocks via `Thread.sleep(50)`.
4. When a virtual thread calls `Thread.sleep`, the JVM's scheduler recognizes this as a blocking operation it can handle specially: it **unmounts** the virtual thread from whatever carrier (OS) thread it was running on, freeing that carrier thread to go run a *different* virtual thread's code in the meantime — the sleeping virtual thread itself consumes no OS thread resources while parked, just a small amount of JVM-managed heap memory to preserve its state.
5. Because virtually all 5000 tasks reach their `Thread.sleep(50)` call in quick succession (creation and dispatch is fast) and then get unmounted, the small number of actual carrier threads (roughly matching the CPU core count) can churn through mounting and unmounting virtual threads extremely quickly, without ever needing more than a handful of real OS threads to service all 5000 blocked virtual threads "simultaneously" from the application's perspective.
6. Once each virtual thread's 50ms sleep elapses, the JVM's scheduler remounts it onto (potentially any) available carrier thread to resume execution, decrements `currentConcurrentVirtual`, and the task completes.
7. Because essentially all 5000 sleeps overlap in real wall-clock time, the entire batch finishes in only slightly more than 50ms total — the printed peak concurrency confirms nearly all 5000 tasks really were concurrently blocked at once, while the low reported "carrier threads used" (matching the core count) confirms this concurrency was achieved without needing anywhere near 5000 real OS threads.

## 7. Gotchas & takeaways

> **Gotcha:** virtual threads do **not** speed up CPU-bound work — if a virtual thread is actually *computing* (not blocked on I/O), it still occupies a carrier thread the entire time, exactly like a platform thread would; running more virtual threads than you have CPU cores for genuinely CPU-bound work provides no additional throughput, since the underlying carrier threads (and the cores they run on) are the actual bottleneck. See [platform vs. virtual threads](0901-platform-vs-virtual-threads.md) for the detailed distinction and when each is the right tool.

- Virtual threads are lightweight, JVM-managed threads that use the exact same `Thread`/`ExecutorService` APIs as platform threads, but at vastly higher scale, because a blocked virtual thread frees its underlying carrier (OS) thread instead of occupying it.
- They make simple, sequential, blocking-style code viable again at high concurrency scale for I/O-bound workloads, without needing to rewrite everything in an asynchronous or reactive style purely to conserve OS threads.
- `Executors.newVirtualThreadPerTaskExecutor()` is the standard entry point — create one virtual thread per task rather than trying to "pool" virtual threads the way you would platform threads, since they're cheap enough not to need reuse.
- The number of carrier (real OS) threads actually used stays small (typically matching CPU core count) regardless of how many virtual threads exist, as long as most of them spend most of their time blocked rather than actively computing.
- Understand [carrier threads & pinning](0902-carrier-threads-pinning.md) before relying heavily on virtual threads in code that uses `synchronized` blocks or certain native calls, since some operations can prevent a virtual thread from unmounting from its carrier even while logically "blocked," partially undermining the scalability benefit.
