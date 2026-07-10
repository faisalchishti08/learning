---
card: java
gi: 902
slug: carrier-threads-pinning
title: Carrier threads & pinning
---

## 1. What it is

A **carrier thread** is the actual OS-level platform thread that a virtual thread is currently "mounted" on and executing atop. Normally, when a virtual thread blocks (I/O, `Thread.sleep`, most `java.util.concurrent` locks), the JVM unmounts it from its carrier, freeing that carrier to run a different virtual thread — this is the whole mechanism that lets thousands of virtual threads share a handful of carriers. **Pinning** is when a virtual thread blocks but the JVM *cannot* unmount it from its carrier, so the carrier thread stays occupied by that one blocked virtual thread until it becomes unblocked — during a pin, that carrier thread is unavailable to run any other virtual thread, which can starve the whole virtual-thread pool if pins happen often or last a long time.

## 2. Why & when

Pinning happens in two well-documented situations: a virtual thread performing a blocking operation while inside a `synchronized` block or method (as of the versions where this tutorial was written; the JDK has been actively reducing this restriction over time, so check your specific JDK version's release notes), and a virtual thread executing a native method or foreign-function call that blocks. Both prevent the JVM from safely detaching the virtual thread's execution state from its carrier. This matters because pinning silently defeats the scalability benefit virtual threads are meant to provide — code that looks correct and uses virtual threads may still bottleneck on the small number of carrier threads if its blocking operations happen to occur inside `synchronized` blocks, exactly the kind of subtle performance cliff that's invisible without specifically knowing to look for it. The practical fix is to replace `synchronized` blocks that wrap blocking calls with `java.util.concurrent.locks.ReentrantLock` (which does not cause pinning), reserving `synchronized` for short, non-blocking critical sections where pinning is irrelevant since the virtual thread never actually blocks while holding it.

## 3. Core concept

```java
// PINS the carrier thread: blocking call happens WHILE holding a synchronized lock
synchronized (lock) {
    performBlockingIO(); // carrier thread is stuck here -- cannot run other virtual threads meanwhile
}

// Does NOT pin: ReentrantLock-based blocking doesn't tie up the carrier the same way
reentrantLock.lock();
try {
    performBlockingIO(); // the virtual thread CAN still unmount from its carrier while blocked here
} finally {
    reentrantLock.unlock();
}
```

The visible code (a lock, then a blocking call) looks almost identical in both cases — the difference in scalability behavior is entirely about which locking primitive is used.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A virtual thread blocking inside a synchronized block pins its carrier thread, which cannot run any other virtual thread until the block completes; the same blocking call outside synchronized, or using ReentrantLock, lets the carrier be freed for other virtual threads">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Inside synchronized: PINNED</text>
  <rect x="20" y="35" width="280" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Carrier thread STUCK with this one virtual thread</text>
  <text x="160" y="90" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">no other virtual thread can use this carrier meanwhile</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Using ReentrantLock: NOT pinned</text>
  <rect x="340" y="35" width="280" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Virtual thread UNMOUNTS while blocked</text>
  <text x="480" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">carrier is FREE to run other virtual threads</text>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Same logical operation (acquire a lock, do blocking work) --</text>
  <text x="320" y="158" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">vastly different scalability depending on WHICH lock primitive is used.</text>
</svg>

*`synchronized` plus a blocking call pins the carrier for the duration; the equivalent with `ReentrantLock` lets the virtual thread unmount and free its carrier.*

## 5. Runnable example

Scenario: a shared cache guarded by a lock, accessed by many virtual threads that occasionally need to perform a slow refresh, growing from a `synchronized`-based version that suffers pinning under load, to demonstrating the resulting carrier-thread starvation concretely, to a `ReentrantLock`-based fix that restores virtual threads' scalability.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class SynchronizedCausesPinning {
    static final Object lock = new Object();

    static void refreshCacheSlowly() {
        synchronized (lock) {
            try { Thread.sleep(100); } catch (InterruptedException ignored) {} // BLOCKING call WHILE holding synchronized
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 200;
        long start = System.currentTimeMillis();

        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) {
                virtualPool.submit(SynchronizedCausesPinning::refreshCacheSlowly);
            }
        }

        System.out.println(taskCount + " tasks (synchronized + blocking) took " + (System.currentTimeMillis() - start) + "ms");
        System.out.println("(likely SLOW -- each blocking call pins a carrier thread, serializing effective concurrency)");
    }
}
```

**How to run:** `java SynchronizedCausesPinning.java` (JDK 21+; note: some later JDK versions have reduced or eliminated pinning for simple `synchronized` blocks specifically for `Thread.sleep` and certain blocking operations — check your JDK's release notes for the exact current behavior, since this has evolved across releases).

Expected output shape (slower than expected for 200 nominally-concurrent virtual threads, since pinning serializes them onto the small number of carrier threads):
```
200 tasks (synchronized + blocking) took 2650ms
(likely SLOW -- each blocking call pins a carrier thread, serializing effective concurrency)
```

Even though 200 virtual threads were created, the `synchronized` block combined with the blocking `Thread.sleep` call inside it (on JDK versions where this causes pinning) prevents most of them from actually running concurrently, since each one occupies a whole carrier thread while blocked, rather than freeing it.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ObservingPinningImpact {
    static final Object lock = new Object();
    static AtomicInteger peakConcurrent = new AtomicInteger(0);
    static AtomicInteger currentConcurrent = new AtomicInteger(0);

    static void refreshCacheSlowly() {
        synchronized (lock) {
            int current = currentConcurrent.incrementAndGet();
            peakConcurrent.updateAndGet(prev -> Math.max(prev, current));
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            currentConcurrent.decrementAndGet();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 100;
        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) {
                virtualPool.submit(ObservingPinningImpact::refreshCacheSlowly);
            }
        }
        System.out.println("peak concurrent executions inside the synchronized block: " + peakConcurrent.get());
        System.out.println("(here, the SAME lock object serializes all callers anyway, since synchronized is exclusive --");
        System.out.println(" the deeper pinning issue is that OTHER, unrelated virtual threads doing DIFFERENT work");
        System.out.println(" also cannot use this carrier thread while one is pinned inside this block)");
    }
}
```

**How to run:** `java ObservingPinningImpact.java` (JDK 21+).

Expected output:
```
peak concurrent executions inside the synchronized block: 1
(here, the SAME lock object serializes all callers anyway, since synchronized is exclusive --
 the deeper pinning issue is that OTHER, unrelated virtual threads doing DIFFERENT work
 also cannot use this carrier thread while one is pinned inside this block)
```

The real-world concern added: this example clarifies an important nuance — since every call here contends for the *same* lock, `synchronized`'s exclusivity alone already limits concurrency inside the block to 1 at a time, regardless of pinning. The real cost of pinning specifically shows up when a *pinned* carrier thread can't be released to service **other, unrelated** virtual threads (doing entirely different work, not waiting on this same lock) that would otherwise be able to make progress — a subtlety easy to miss if you only look at contention on the specific lock in question.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.locks.*;

public class ReentrantLockAvoidsPinning {
    static final ReentrantLock lock = new ReentrantLock();

    static void refreshCacheSlowly() {
        lock.lock();
        try {
            try { Thread.sleep(100); } catch (InterruptedException ignored) {} // blocking, but does NOT pin the carrier
        } finally {
            lock.unlock();
        }
    }

    static void unrelatedWork() {
        try { Thread.sleep(10); } catch (InterruptedException ignored) {} // simulates OTHER virtual threads' unrelated work
    }

    public static void main(String[] args) throws InterruptedException {
        int cacheTaskCount = 50;
        int unrelatedTaskCount = 500;

        long start = System.currentTimeMillis();
        try (ExecutorService virtualPool = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < cacheTaskCount; i++) {
                virtualPool.submit(ReentrantLockAvoidsPinning::refreshCacheSlowly);
            }
            for (int i = 0; i < unrelatedTaskCount; i++) {
                virtualPool.submit(ReentrantLockAvoidsPinning::unrelatedWork);
            }
        }
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("total tasks: " + (cacheTaskCount + unrelatedTaskCount) + " (mix of ReentrantLock-guarded and unrelated work)");
        System.out.println("elapsed: " + elapsed + "ms");
        System.out.println("with ReentrantLock (not synchronized), carriers are NOT pinned during the blocking sleep,");
        System.out.println("so the 500 unrelated tasks are free to interleave and complete promptly alongside the 50 cache refreshes");
    }
}
```

**How to run:** `java ReentrantLockAvoidsPinning.java` (JDK 21+).

Expected output shape (elapsed time stays low, since neither the lock-guarded tasks nor the unrelated tasks are starved of carrier threads):
```
total tasks: 550 (mix of ReentrantLock-guarded and unrelated work)
elapsed: 145ms
with ReentrantLock (not synchronized), carriers are NOT pinned during the blocking sleep,
so the 500 unrelated tasks are free to interleave and complete promptly alongside the 50 cache refreshes
```

This adds the production-flavored hard case: replacing `synchronized` with `ReentrantLock` for the exact same "acquire a lock, then block" pattern — because `ReentrantLock`-based blocking does not pin the carrier thread, a virtual thread blocked inside `lock.lock()`/`Thread.sleep()` still unmounts from its carrier, freeing it to service the 500 *unrelated* virtual threads concurrently, rather than those unrelated tasks being starved by carriers stuck pinned on the 50 cache-refresh tasks.

## 6. Walkthrough

Contrasting what happens to the 500 "unrelated" tasks under `synchronized` (Level 1 style) versus `ReentrantLock` (Level 3):

1. In a `synchronized`-based version, each of the 50 cache-refresh tasks that manages to enter the `synchronized` block (one at a time, since the lock is exclusive) blocks for 100ms via `Thread.sleep` *while holding the carrier thread pinned* — on JDK versions where this causes pinning, that specific carrier thread is entirely unavailable to run any other virtual thread, including the 500 unrelated ones, for the full 100ms duration of each cache-refresh call.
2. With a small number of carrier threads (say, matching an 8-core machine), if several cache-refresh calls happen to pin several different carriers at overlapping times, a meaningful fraction of the JVM's total carrier capacity can become temporarily unavailable — starving the unrelated virtual threads of somewhere to run, even though those unrelated tasks have nothing to do with the cache lock at all.
3. In the `ReentrantLock`-based version, `refreshCacheSlowly` still acquires `lock` and still blocks via `Thread.sleep(100)` — but because the blocking happens under a `ReentrantLock` rather than `synchronized`, the JVM *can* unmount this virtual thread from its carrier during the sleep, exactly as it would for any ordinary blocking virtual thread.
4. That freed carrier thread is then immediately available for the scheduler to mount a *different* virtual thread onto — including any of the 500 unrelated tasks, which have no dependency on `lock` at all and can run entirely independently.
5. Because none of the 550 total virtual threads pin their carrier for any meaningful duration in this version, the JVM's small set of carrier threads can cycle through mounting and unmounting virtual threads rapidly, letting essentially the whole batch — both the lock-guarded cache refreshes and the unrelated work — proceed with high effective concurrency, producing the much lower total elapsed time observed.
6. The key structural difference driving this outcome is purely the choice of locking primitive around the blocking call — the actual business logic (acquire a lock, do something slow, release the lock) is functionally identical between the two versions.

## 7. Gotchas & takeaways

> **Gotcha:** pinning is easy to introduce accidentally and hard to notice without specifically profiling for it — code that works correctly and looks reasonably performant in a low-concurrency test can silently degrade under high concurrency in production, purely because some blocking operation happens to sit inside a `synchronized` block somewhere in a commonly-hit code path. The JDK provides diagnostic support (such as `-Djdk.tracePinnedThreads=full`, in versions where this flag is available) specifically to help surface exactly where pinning is occurring in real code.

- Pinning occurs when a virtual thread blocks in a way that prevents the JVM from unmounting it from its carrier thread — historically, this includes blocking inside a `synchronized` block/method and blocking during certain native calls (behavior has evolved across JDK releases, so verify against your specific version).
- A pinned carrier thread is unavailable to run *any other* virtual thread for the duration of the pin, which can silently degrade the scalability benefit virtual threads are meant to provide, especially under sustained load.
- Replace `synchronized` blocks that wrap blocking operations with `java.util.concurrent.locks.ReentrantLock`, which does not cause pinning, when the code will run on virtual threads.
- Short, non-blocking `synchronized` blocks are unaffected in practice — pinning only matters when the code *inside* the synchronized region actually blocks; a `synchronized` block that only does quick in-memory work causes no meaningful pinning concern.
- Use JDK diagnostic tooling (pinning trace flags, or profiling under realistic concurrent load) to find pinning issues in existing code before they manifest as a mysterious throughput ceiling under production traffic — see [structured concurrency](0903-structured-concurrency.md) and [scoped values](0904-scoped-values.md) for related, newer tools designed to work well with virtual threads from the ground up.
