---
card: java
gi: 875
slug: threadpoolexecutor-configuration-core-max-queue-rejection
title: ThreadPoolExecutor configuration (core/max/queue/rejection)
---

## 1. What it is

`ThreadPoolExecutor` is the concrete class behind most `ExecutorService`s returned by the `Executors` factory methods, and it exposes the knobs that actually control pool behavior: **core pool size** (the number of threads kept alive even when idle), **maximum pool size** (the hard ceiling on threads, reached only once the work queue is full), a **work queue** (where submitted tasks wait for a free thread), **keep-alive time** (how long threads beyond the core size stay alive while idle before terminating), and a **rejection policy** (what happens when a task arrives but the queue is full and the pool is already at maximum size). Understanding how these four things interact — pool grows toward core, then queues, then grows toward max, then rejects — is the difference between a pool that behaves as intended under load and one that either wastes threads or silently drops or blocks on tasks it can't handle.

## 2. Why & when

The convenience factories in `Executors` (`newFixedThreadPool`, `newCachedThreadPool`, etc.) hide these parameters behind reasonable-looking defaults that are frequently *wrong* for production use — `newFixedThreadPool` uses an unbounded `LinkedBlockingQueue`, meaning the pool can never grow past its core size no matter how much work piles up, and an unbounded queue means you can run out of memory queuing tasks faster than they're processed, with no backpressure signal until it's too late. Configuring `ThreadPoolExecutor` directly matters whenever you need actual control: bounding the queue (so a sudden burst of load fails fast or applies backpressure instead of silently consuming unbounded memory), tuning core versus max to burst above the steady-state thread count under temporary spikes, or choosing a rejection policy deliberately (`AbortPolicy` throws, `CallerRunsPolicy` throttles the producer by running the task on the submitting thread, `DiscardPolicy` silently drops it) rather than accepting whatever the factory method happened to pick.

## 3. Core concept

```java
ThreadPoolExecutor pool = new ThreadPoolExecutor(
    2,                                   // core pool size -- always kept alive
    4,                                   // maximum pool size -- ceiling under load
    30, TimeUnit.SECONDS,                // keep-alive time for threads above core size
    new ArrayBlockingQueue<>(10),        // BOUNDED queue -- exactly 10 tasks can wait
    new ThreadPoolExecutor.CallerRunsPolicy() // what to do when queue AND max threads are full
);
```

Submission order: if fewer than `core` threads exist, start a new one; else if the queue has room, enqueue; else if fewer than `max` threads exist, start a new one (up to `max`); else invoke the rejection policy.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Task submission decision flow: use a core thread if available, else queue, else grow toward max, else reject">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Task submitted</text>

  <rect x="240" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Core thread free? Use it.</text>

  <rect x="240" y="80" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Queue has room? Enqueue.</text>

  <rect x="240" y="140" width="180" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="330" y="165" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Below max? Spawn new thread.</text>

  <rect x="460" y="140" width="160" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="165" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Else: REJECT (policy)</text>

  <line x1="200" y1="40" x2="236" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a13)"/>
  <line x1="330" y1="60" x2="330" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a13)"/>
  <line x1="330" y1="120" x2="330" y2="138" stroke="#8b949e" stroke-width="2" marker-end="url(#a13)"/>
  <line x1="420" y1="160" x2="456" y2="160" stroke="#8b949e" stroke-width="2" marker-end="url(#a13)"/>
  <defs><marker id="a13" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A bounded queue and a rejection policy give the pool a well-defined behavior under overload, instead of silently growing memory usage forever.*

## 5. Runnable example

Scenario: a task-processing service, growing from the default (unbounded-queue) `newFixedThreadPool` that hides overload until memory runs out, to an explicitly-configured `ThreadPoolExecutor` with a bounded queue that starts rejecting, to a version using `CallerRunsPolicy` to throttle producers gracefully instead of losing tasks.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class DefaultFixedPoolHidesOverload {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2); // internally: unbounded LinkedBlockingQueue

        for (int i = 0; i < 10; i++) {
            final int id = i;
            pool.submit(() -> {
                try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                System.out.println("processed task " + id + " on " + Thread.currentThread().getName());
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("all 10 tasks completed -- but note: with 10,000 tasks instead of 10,");
        System.out.println("the unbounded queue would accept ALL of them instantly, hiding overload");
    }
}
```

**How to run:** `java DefaultFixedPoolHidesOverload.java` (JDK 17+).

Expected output shape (task order/thread names vary):
```
processed task 0 on pool-1-thread-1
processed task 1 on pool-1-thread-2
... (10 lines total)
all 10 tasks completed -- but note: with 10,000 tasks instead of 10,
the unbounded queue would accept ALL of them instantly, hiding overload
```

`newFixedThreadPool(2)` only ever uses 2 threads (core == max here), and backs them with an **unbounded** queue — any burst of submissions is silently absorbed into ever-growing memory, with no signal that the system is overloaded until it eventually runs out of heap.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class BoundedQueueRejects {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            2, 2,                                   // core == max: fixed at 2 threads
            0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(3),             // BOUNDED -- only 3 tasks may wait
            new ThreadPoolExecutor.AbortPolicy()     // reject (throw) once queue AND threads are full
        );

        int accepted = 0, rejected = 0;
        for (int i = 0; i < 10; i++) {
            final int id = i;
            try {
                pool.submit(() -> {
                    try { Thread.sleep(100); } catch (InterruptedException ignored) {}
                });
                accepted++;
            } catch (RejectedExecutionException e) {
                rejected++;
            }
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("accepted: " + accepted + ", rejected: " + rejected + " (2 threads + 3 queue slots = 5 max in flight)");
    }
}
```

**How to run:** `java BoundedQueueRejects.java`.

Expected output:
```
accepted: 5, rejected: 5
```

The real-world concern added: a bounded queue (capacity 3) on top of 2 fixed threads means at most 5 tasks (2 running + 3 queued) can be in flight at once — the 6th through 10th submissions arrive while the pool is already saturated, and `AbortPolicy` makes that fact loud and immediate (a thrown `RejectedExecutionException`) instead of silently growing an unbounded queue.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CallerRunsThrottling {
    public static void main(String[] args) throws InterruptedException {
        AtomicInteger tasksRunOnPoolThreads = new AtomicInteger(0);
        AtomicInteger tasksRunOnCallingThread = new AtomicInteger(0);

        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            2, 4,                                     // can grow from 2 up to 4 threads under load
            2, TimeUnit.SECONDS,                       // extra threads above core die after 2s idle
            new ArrayBlockingQueue<>(2),                // small bounded queue
            new ThreadPoolExecutor.CallerRunsPolicy()   // instead of rejecting, run it on the SUBMITTER's thread
        );

        String mainThreadName = Thread.currentThread().getName();

        for (int i = 0; i < 12; i++) {
            final int id = i;
            pool.submit(() -> {
                String runner = Thread.currentThread().getName();
                if (runner.equals(mainThreadName)) {
                    tasksRunOnCallingThread.incrementAndGet(); // pool was saturated -- caller did the work itself
                } else {
                    tasksRunOnPoolThreads.incrementAndGet();
                }
                try { Thread.sleep(30); } catch (InterruptedException ignored) {}
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("run on pool threads: " + tasksRunOnPoolThreads.get());
        System.out.println("run on the CALLING thread (throttled the producer): " + tasksRunOnCallingThread.get());
        System.out.println("total: " + (tasksRunOnPoolThreads.get() + tasksRunOnCallingThread.get()) + " (all 12 tasks still ran -- none lost)");
    }
}
```

**How to run:** `java CallerRunsThrottling.java`.

Expected output shape (exact split between pool-run and caller-run varies by timing, but the total is always 12):
```
run on pool threads: 8
run on the CALLING thread (throttled the producer): 4
total: 12 (all 12 tasks still ran -- none lost)
```

This adds the production-flavored hard case: instead of dropping or throwing on overload, `CallerRunsPolicy` makes the *submitting* thread (here, `main`) execute the rejected task itself, synchronously — this has the effect of throttling the producer (since `main` can't submit the next task until it finishes running this one), naturally slowing down the rate of submission to match the pool's actual processing capacity, with zero lost tasks.

## 6. Walkthrough

Tracing `CallerRunsThrottling.main` as it submits 12 tasks to a pool with core=2, max=4, queue capacity=2:

1. The first 2 submissions each start a new core thread (no threads exist yet, below core size) and begin running immediately.
2. The 3rd and 4th submissions find no free core thread but the queue has room (capacity 2, currently empty) — they enqueue.
3. The 5th and 6th submissions find the queue full (2/2) and the pool below max (2 < 4) — each triggers spawning a new thread, growing the pool to 4.
4. The 7th submission arrives to find the queue still full and the pool already at max (4/4) — this is where `CallerRunsPolicy` kicks in: instead of throwing or discarding, the pool runs this task's `Runnable.run()` directly on `main`'s own thread, synchronously, blocking `main` from submitting further tasks until this one completes.
5. Because `main` was busy running that task, by the time it returns and submits the 8th task, one of the earlier pool threads has likely finished and is free again — so the 8th submission may go straight to a pool thread or queue, depending on exact timing.
6. This pattern repeats for the remaining submissions: whenever the pool is fully saturated (queue full, threads at max) at the exact moment of submission, `main` itself absorbs that task's execution cost, which is precisely what naturally throttles the submission rate to match actual processing capacity.
7. After all 12 submissions return, `pool.shutdown()` and `awaitTermination` ensure every task (whether it ran on a pool thread or on `main`) has completed before the final counts are printed — confirming all 12 ran, split between "pool thread" and "caller thread" depending on how saturated the pool was at each submission instant.

## 7. Gotchas & takeaways

> **Gotcha:** `Executors.newFixedThreadPool` and `Executors.newCachedThreadPool` use an **unbounded** queue or an effectively unbounded thread count internally — under sustained overload, `newFixedThreadPool` can queue tasks until the JVM runs out of memory, and `newCachedThreadPool` can spawn unboundedly many threads until the OS refuses to create more. Neither factory method surfaces overload as a clear, actionable signal the way a deliberately bounded `ThreadPoolExecutor` does.

- Core pool size is the steady-state thread count kept alive even when idle; maximum pool size is only reached once the bounded queue is also full.
- A bounded work queue (`ArrayBlockingQueue` with a fixed capacity) is what actually gives you backpressure — an unbounded queue defers the overload problem into an out-of-memory crash instead of a clear rejection.
- Choose a rejection policy deliberately: `AbortPolicy` (throw, fail fast), `CallerRunsPolicy` (throttle the producer by making it do the work), `DiscardPolicy`/`DiscardOldestPolicy` (silently drop — usually risky, since dropped work is invisible unless you add your own logging).
- Prefer constructing `ThreadPoolExecutor` directly with explicit core/max/queue/policy values over the `Executors` convenience factories for any production service that needs predictable behavior under load.
- Keep-alive time only applies to threads *above* the core count; core threads stay alive indefinitely by default (unless `allowCoreThreadTimeOut(true)` is set).
