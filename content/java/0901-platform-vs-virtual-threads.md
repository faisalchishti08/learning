---
card: java
gi: 901
slug: platform-vs-virtual-threads
title: Platform vs virtual threads
---

## 1. What it is

A **platform thread** is a thin wrapper around an operating-system thread — a one-to-one mapping where every Java `Thread` corresponds to exactly one OS-level thread, with its own OS-allocated stack (often megabytes) and OS-level scheduling. A **virtual thread** is a JVM-managed abstraction that runs *on top of* a small pool of platform threads (called **carrier threads**) — many virtual threads share and take turns on a much smaller number of carriers, with the JVM (not the OS) handling the scheduling of which virtual thread runs on which carrier at any given moment. Both expose the identical `Thread` API; code you write doesn't need to know or care which kind of thread it's running on, except in a few specific situations covered below and in [carrier threads & pinning](0902-carrier-threads-pinning.md).

## 2. Why & when

The choice matters because the two models have fundamentally different cost profiles and are suited to different kinds of work. Platform threads are the right (and only sensible) choice for genuinely CPU-bound work — since a platform thread maps directly to a schedulable OS thread, and CPU-bound work is ultimately limited by the number of actual CPU cores, having more platform threads than cores for pure computation just adds context-switching overhead with no benefit (see [thread pool sizing strategies](0876-thread-pool-sizing-strategies.md)). Virtual threads are the right choice for I/O-bound work with high concurrency — many requests or tasks that spend most of their time waiting (on network calls, database queries, file I/O) rather than computing — since the JVM can multiplex thousands or millions of blocked virtual threads onto a handful of carrier threads, achieving massive concurrency without the OS-level resource cost that the same number of platform threads would require. Mixing them up — using virtual threads for CPU-bound work, or trying to scale platform threads to virtual-thread-like concurrency for I/O-bound work — either provides no benefit or actively wastes resources.

## 3. Core concept

```java
// Platform thread pool: right for CPU-bound work, sized near the core count
ExecutorService cpuBoundPool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

// Virtual thread executor: right for I/O-bound work with high concurrency
ExecutorService ioBoundPool = Executors.newVirtualThreadPerTaskExecutor();

cpuBoundPool.submit(() -> computeExpensiveHash(data));      // pure computation -- benefits from platform threads
ioBoundPool.submit(() -> fetchFromSlowDatabase(query));       // mostly waiting -- benefits from virtual threads
```

The two executors coexist in the same application, each handling the kind of workload it's actually suited for — there's no requirement to pick one model exclusively for an entire codebase.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison: platform threads map one-to-one to OS threads and scale to hundreds; virtual threads share a small pool of carrier threads and scale to millions for I/O-bound work, but provide no benefit for CPU-bound work">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">CPU-bound: platform threads = right tool</text>
  <rect x="20" y="35" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="50" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">core1</text>
  <rect x="90" y="35" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">core2</text>
  <rect x="160" y="35" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="190" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">core3</text>
  <text x="120" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 platform thread per core, fully busy computing</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">I/O-bound: virtual threads = right tool</text>
  <rect x="330" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="365" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="400" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="435" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="470" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="505" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="540" y="35" width="30" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <text x="450" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thousands of mostly-waiting virtual threads, few carrier threads needed</text>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Using virtual threads for the LEFT scenario, or platform threads for the RIGHT one,</text>
  <text x="320" y="158" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">provides no benefit (CPU-bound) or wastes resources (I/O-bound at scale).</text>
</svg>

*Match the thread model to the workload: platform threads for compute-bound work near the core count, virtual threads for I/O-bound work at high concurrency.*

## 5. Runnable example

Scenario: a mixed workload with both a CPU-bound hashing step and an I/O-bound fetch step, growing from using platform threads for everything (fine for the compute step, wasteful at scale for the I/O step), to correctly using virtual threads for the I/O step, to a version explicitly measuring and confirming virtual threads provide zero benefit for the CPU-bound step.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class PlatformThreadsForEverything {
    static long cpuBoundHash(int n) {
        long h = n;
        for (int i = 0; i < 5_000_000; i++) h = (h * 31 + i) & 0xFFFFFFFL;
        return h;
    }

    static void ioBoundFetch() {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) throws InterruptedException {
        int cores = Runtime.getRuntime().availableProcessors();
        ExecutorService pool = Executors.newFixedThreadPool(cores); // sized for CPU-bound work

        long start = System.currentTimeMillis();
        for (int i = 0; i < cores; i++) {
            final int n = i;
            pool.submit(() -> cpuBoundHash(n));
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);
        System.out.println("CPU-bound batch (cores=" + cores + ") took " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

**How to run:** `java PlatformThreadsForEverything.java` (JDK 21+, though this file alone only needs JDK 17+).

Expected output shape (machine-dependent):
```
CPU-bound batch (cores=8) took 340ms
```

A platform thread pool sized to the core count is exactly right for this genuinely CPU-bound work — establishing a baseline to compare virtual threads against for the *same* kind of workload later.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class VirtualThreadsForIoBoundWork {
    static void ioBoundFetch() {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 2000;

        // Platform pool sized "reasonably" for I/O-bound work -- still limited
        ExecutorService platformPool = Executors.newFixedThreadPool(100);
        long start1 = System.currentTimeMillis();
        for (int i = 0; i < taskCount; i++) platformPool.submit(VirtualThreadsForIoBoundWork::ioBoundFetch);
        platformPool.shutdown();
        platformPool.awaitTermination(30, TimeUnit.SECONDS);
        System.out.println("platform pool (100 threads): " + (System.currentTimeMillis() - start1) + "ms for " + taskCount + " I/O-bound tasks");

        // Virtual threads: no artificial pool-size ceiling for this I/O-bound workload
        long start2 = System.currentTimeMillis();
        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) virtualPool.submit(VirtualThreadsForIoBoundWork::ioBoundFetch);
        }
        System.out.println("virtual threads: " + (System.currentTimeMillis() - start2) + "ms for " + taskCount + " I/O-bound tasks");
    }
}
```

**How to run:** `java VirtualThreadsForIoBoundWork.java` (JDK 21+).

Expected output shape (virtual threads dramatically faster for this I/O-bound, high-concurrency workload):
```
platform pool (100 threads): 1050ms for 2000 I/O-bound tasks
virtual threads: 62ms for 2000 I/O-bound tasks
```

The real-world concern added: with 2000 I/O-bound tasks each blocking for 50ms, a 100-thread platform pool needs roughly 20 sequential waves (2000/100), while virtual threads let essentially all 2000 run concurrently, completing in close to a single 50ms wait — a direct, measured demonstration of virtual threads' advantage specifically for this kind of workload.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ConfirmingNoBenefitForCpuBoundWork {
    static long cpuBoundHash(int n) {
        long h = n;
        for (int i = 0; i < 5_000_000; i++) h = (h * 31 + i) & 0xFFFFFFFL;
        return h;
    }

    static long runCpuBoundBatch(ExecutorService pool, int taskCount) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int i = 0; i < taskCount; i++) {
            final int n = i;
            pool.submit(() -> cpuBoundHash(n));
        }
        pool.shutdown();
        pool.awaitTermination(60, TimeUnit.SECONDS);
        return System.currentTimeMillis() - start;
    }

    public static void main(String[] args) throws InterruptedException {
        int cores = Runtime.getRuntime().availableProcessors();
        int taskCount = cores * 4; // more tasks than cores, to make contention/scheduling visible either way

        long platformElapsed = runCpuBoundBatch(Executors.newFixedThreadPool(cores), taskCount);
        long virtualElapsed = runCpuBoundBatch(Executors.newVirtualThreadPerTaskExecutor(), taskCount);

        System.out.println("cores: " + cores + ", CPU-bound tasks: " + taskCount);
        System.out.println("platform threads (sized to cores): " + platformElapsed + "ms");
        System.out.println("virtual threads (one per task): " + virtualElapsed + "ms");
        System.out.println("virtual threads provide NO speedup here -- CPU-bound work is limited by core count, not thread count/model");
    }
}
```

**How to run:** `java ConfirmingNoBenefitForCpuBoundWork.java` (JDK 21+).

Expected output shape (the two elapsed times are comparable — virtual threads are not meaningfully faster, and can occasionally be slightly slower due to virtual-thread scheduling overhead for pure compute):
```
cores: 8, CPU-bound tasks: 32
platform threads (sized to cores): 1380ms
virtual threads (one per task): 1410ms
virtual threads provide NO speedup here -- CPU-bound work is limited by core count, not thread count/model
```

This adds the production-flavored hard case: directly measuring that virtual threads provide **no meaningful benefit** for genuinely CPU-bound work — since a virtual thread actively computing (not blocked) still occupies a carrier thread the entire time it runs, and there are only as many carrier threads as there are useful CPU cores to run them on, creating one virtual thread per CPU-bound task doesn't let more of them "truly" run concurrently than the core count allows; both approaches are ultimately bottlenecked by the same underlying hardware constraint.

## 6. Walkthrough

Tracing why `virtualElapsed` in `ConfirmingNoBenefitForCpuBoundWork.main` doesn't beat `platformElapsed`:

1. `runCpuBoundBatch` with the platform pool submits 32 tasks to a pool of 8 platform threads (matching the core count) — each thread runs `cpuBoundHash` to completion (no blocking, pure computation) before picking up its next queued task, so the 32 tasks proceed in 4 waves of 8 fully-parallel, core-saturating computations.
2. `runCpuBoundBatch` with the virtual thread executor submits the same 32 tasks, each getting its own virtual thread — but since none of these tasks ever block (no I/O, no sleep, just tight computation), none of them ever unmount from their carrier thread; each virtual thread occupies a carrier thread for its *entire* duration, exactly like a platform thread would.
3. Because there are still only as many carrier threads as CPU cores (8, in this example) actually available to run virtual thread code simultaneously, at most 8 of the 32 virtual threads can be truly executing at any given instant — the remaining 24 simply wait their turn for a carrier thread to free up, just as the remaining platform-pool tasks waited their turn for a pool thread.
4. The JVM's virtual thread scheduler does add a small amount of overhead for managing the mounting/unmounting and scheduling of virtual threads onto carriers, compared to the OS directly scheduling platform threads — this is why the virtual-thread run can occasionally come out very slightly slower rather than exactly equal, though the difference is minor compared to the actual compute time.
5. Both approaches, in the end, are bottlenecked by the same fundamental constraint: 8 CPU cores can only usefully run 8 threads' worth of active computation at once, regardless of whether those 8 "slots" are filled by platform threads or virtual threads — creating more virtual threads than you have cores to run CPU-bound work on simply creates more contention for the same limited compute resource, providing no additional throughput.

## 7. Gotchas & takeaways

> **Gotcha:** it's tempting to assume "virtual threads are just better/faster threads" and switch everything to them — but for CPU-bound code, this provides zero benefit and adds a small amount of unnecessary scheduling overhead; the entire value proposition of virtual threads is specifically about efficiently handling *blocking* operations at scale, not about making computation itself faster.

- Platform threads map one-to-one to OS threads; virtual threads are JVM-managed and share a small pool of carrier (platform) threads, unmounting from their carrier whenever they block.
- Use platform threads, sized near the CPU core count, for genuinely CPU-bound work — see [thread pool sizing strategies](0876-thread-pool-sizing-strategies.md).
- Use virtual threads for I/O-bound work with high concurrency, where most threads spend most of their time blocked rather than computing — this is where the massive scalability advantage actually applies.
- Virtual threads provide no speedup for CPU-bound work, since an actively-computing virtual thread still occupies a carrier thread for its entire duration, and carrier thread availability is still bounded by CPU core count.
- Both thread models coexist naturally in the same application — use whichever is appropriate for each specific workload rather than picking one exclusively; see [carrier threads & pinning](0902-carrier-threads-pinning.md) for cases where a virtual thread can get unexpectedly "stuck" on its carrier even while nominally blocked.
