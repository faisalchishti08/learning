---
card: java
gi: 399
slug: threadpoolexecutor
title: ThreadPoolExecutor
---

## 1. What it is

`ThreadPoolExecutor` is the concrete class behind almost every pool the `Executors` factory hands out — `newFixedThreadPool` and friends are just convenience constructors that call `new ThreadPoolExecutor(...)` with particular arguments baked in. Constructing it directly gives you full control over five things: **core pool size** (threads kept alive even when idle), **maximum pool size** (the hard cap), **keep-alive time** (how long extra threads above the core size may sit idle before being killed), the **work queue** (where tasks wait when all core threads are busy), and a **`RejectedExecutionHandler`** (what happens when the queue is also full).

## 2. Why & when

`Executors`' factory methods are fine defaults, but production systems often need finer control than "always exactly N threads" or "unbounded threads." A `ThreadPoolExecutor` built by hand lets you say precisely: "keep 2 threads warm at all times, allow bursts up to 10, queue up to 50 pending tasks beyond that, and if even the queue fills up, do *this specific thing* instead of silently accepting unlimited work" (which is exactly the failure mode of `newCachedThreadPool` under sustained load, or `newFixedThreadPool` with an unbounded queue that can grow until the JVM runs out of memory).

You reach for a hand-built `ThreadPoolExecutor` any time you need bounded resource usage with predictable backpressure — a web server's request-handling pool, a task queue that must never silently accumulate unbounded memory, or anywhere you want visibility into what's happening via methods like `getActiveCount()` or `getQueue().size()`.

## 3. Core concept

```java
import java.util.concurrent.*;

ThreadPoolExecutor pool = new ThreadPoolExecutor(
    2,                                  // core pool size: threads always kept alive
    5,                                  // maximum pool size: hard cap under load
    30, TimeUnit.SECONDS,               // keep-alive: how long extra threads may idle before dying
    new ArrayBlockingQueue<>(10),       // work queue: holds pending tasks once core threads are busy
    new ThreadPoolExecutor.CallerRunsPolicy() // rejection handler: what to do when queue AND max threads are full
);
```

The pool grows in a specific order under load: (1) use an idle core thread if one exists; (2) if all core threads are busy, queue the task; (3) if the queue is also full, create a new thread up to the maximum; (4) if even the maximum is reached and the queue is full, hand the task to the `RejectedExecutionHandler`.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ThreadPoolExecutor task admission order: core threads, then queue, then extra threads up to maximum, then the rejection handler">
  <rect x="8" y="8" width="624" height="244" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#e6edf3" font-size="12" font-family="sans-serif">New task arrives -&gt; where does it go?</text>

  <rect x="20" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1. idle core thread?</text>

  <rect x="200" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="275" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2. room in queue?</text>

  <rect x="380" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="455" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">3. below max threads?</text>

  <rect x="470" y="130" width="140" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="155" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">4. RejectedExecutionHandler</text>

  <line x1="170" y1="65" x2="200" y2="65" stroke="#8b949e" marker-end="url(#a3)"/>
  <text x="185" y="58" fill="#8b949e" font-size="8">no</text>
  <line x1="350" y1="65" x2="380" y2="65" stroke="#8b949e" marker-end="url(#a3)"/>
  <text x="365" y="58" fill="#8b949e" font-size="8">full</text>
  <line x1="455" y1="85" x2="540" y2="130" stroke="#8b949e" marker-end="url(#a3)"/>
  <text x="500" y="105" fill="#8b949e" font-size="8">at max, queue full</text>

  <text x="95" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">run immediately</text>
  <text x="275" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wait in queue</text>
  <text x="455" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spawn new thread</text>

  <defs><marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Tasks flow through four stages in strict order: core thread, then queue, then extra thread, then rejection.

## 5. Runnable example

Scenario: an image-thumbnail service under load — the same pool handling incoming thumbnail jobs, evolved from a bare `ThreadPoolExecutor` with default (unbounded) behaviour assumptions, through a properly bounded queue that reveals backpressure, to a version with a custom rejection policy and live monitoring.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class ThumbnailPoolBasic {
    static void makeThumbnail(int id) throws InterruptedException {
        Thread.sleep(50);
        System.out.println("Thumbnail " + id + " done on " + Thread.currentThread().getName());
    }

    public static void main(String[] args) throws InterruptedException {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            2, 2, 0L, TimeUnit.MILLISECONDS,
            new LinkedBlockingQueue<>() // unbounded queue -- fine for now, dangerous later (see Level 2)
        );

        for (int i = 1; i <= 5; i++) {
            int id = i;
            pool.submit(() -> {
                try { makeThumbnail(id); } catch (InterruptedException ignored) { }
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java ThumbnailPoolBasic.java`

Two core threads process 5 thumbnail jobs; the other 3 wait in the (unbounded) `LinkedBlockingQueue` until a thread frees up. This works fine at small scale, but an unbounded queue means there's no limit on how many pending jobs could pile up in memory if uploads arrived faster than they can be processed.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ThumbnailPoolBounded {
    static void makeThumbnail(int id) throws InterruptedException {
        Thread.sleep(50);
        System.out.println("Thumbnail " + id + " done on " + Thread.currentThread().getName());
    }

    public static void main(String[] args) throws InterruptedException {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            2,                              // core: 2 threads always ready
            4,                              // max: burst up to 4 under load
            10, TimeUnit.SECONDS,           // extra threads above core die after 10s idle
            new ArrayBlockingQueue<>(3)     // bounded queue: only 3 pending jobs allowed to wait
        );

        for (int i = 1; i <= 5; i++) {
            int id = i;
            pool.submit(() -> {
                try { makeThumbnail(id); } catch (InterruptedException ignored) { }
            });
            System.out.println("Submitted " + id + " | active=" + pool.getActiveCount() + " queued=" + pool.getQueue().size());
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java ThumbnailPoolBounded.java`

With core=2 and a bounded queue of 3, submitting a 5th task while 2 are running and 3 are queued triggers the pool to spawn a 3rd, then 4th thread (up to `maximumPoolSize`) rather than growing the queue further — `getActiveCount()` and `getQueue().size()` let you observe this in real time instead of guessing.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ThumbnailPoolWithRejection {
    static void makeThumbnail(int id) throws InterruptedException {
        Thread.sleep(100);
        System.out.println("Thumbnail " + id + " done on " + Thread.currentThread().getName());
    }

    public static void main(String[] args) throws InterruptedException {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            1, 2, 0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(1), // deliberately tiny, to force rejection under this burst
            (task, executor) -> {        // custom RejectedExecutionHandler
                System.out.println("Rejected! Pool full: active=" + executor.getActiveCount()
                    + " queued=" + executor.getQueue().size());
            }
        );

        for (int i = 1; i <= 6; i++) {
            int id = i;
            pool.execute(() -> {
                try { makeThumbnail(id); } catch (InterruptedException ignored) { }
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java ThumbnailPoolWithRejection.java`

With only 2 max threads and a queue of capacity 1, submitting 6 jobs quickly overwhelms the pool's admission capacity (1 core thread + 1 extra thread + 1 queue slot = 3 tasks it can hold); the remaining jobs hit the custom `RejectedExecutionHandler` instead of crashing the program or silently growing unboundedly — a real production system might log this, retry with backoff, or shed load intentionally.

## 6. Walkthrough

Execution starts in `main`. The `ThreadPoolExecutor` is built with `corePoolSize=1`, `maximumPoolSize=2`, and a queue capacity of exactly 1 — meaning it can hold at most 3 tasks total before rejecting: 1 running on the core thread, 1 more thread it can spin up to the max, and 1 waiting in the queue.

The loop submits 6 tasks via `pool.execute(...)` in quick succession. Task 1 finds the core thread idle and starts running immediately (`makeThumbnail(1)` begins sleeping). Task 2 arrives while the core thread is busy, so it goes into the queue (which has room for exactly 1). Task 3 arrives: core thread still busy, queue now full — so the pool spins up a second thread (since `maximumPoolSize` is 2) and runs task 3 there directly, bypassing the queue.

Task 4 arrives: both threads are now busy (running tasks 1 and 3), and the queue's 1 slot is still occupied by task 2 — there is no more room anywhere, and the pool is already at its maximum, so task 4 is handed to the custom `RejectedExecutionHandler`, which prints a rejection message rather than throwing an uncaught exception or blocking. Tasks 5 and 6 are rejected for the same reason, arriving before either running task has finished and freed up capacity.

As tasks 1 and 3 finish (each after ~100ms), their threads become idle; task 2, still waiting in the queue, is then picked up and runs to completion. Finally `pool.shutdown()` and `awaitTermination` let the pool wind down once task 2 finishes.

Expected output (exact rejection count can shift slightly based on timing, but the shape is stable):
```
Thumbnail 1 done on pool-1-thread-1
Rejected! Pool full: active=2 queued=1
Rejected! Pool full: active=2 queued=1
Rejected! Pool full: active=2 queued=1
Thumbnail 3 done on pool-1-thread-2
Thumbnail 2 done on pool-1-thread-1
```

## 7. Gotchas & takeaways

> `Executors.newFixedThreadPool(n)` internally uses an **unbounded** `LinkedBlockingQueue`. Under sustained overload, tasks pile up in that queue forever instead of ever being rejected — this can quietly exhaust memory. If you need real backpressure, construct a `ThreadPoolExecutor` directly with a bounded queue, exactly like Level 2 and 3 above.

- The five knobs are: core pool size, maximum pool size, keep-alive time, work queue, and `RejectedExecutionHandler` — tune all five deliberately rather than accepting `Executors`' defaults blindly.
- Task admission order is: idle core thread → queue → new thread up to maximum → rejection handler. A bounded queue is what makes "new thread up to maximum" and "rejection" ever actually reachable.
- Built-in rejection policies include `AbortPolicy` (throws, the default), `CallerRunsPolicy` (runs the task on the *submitting* thread, a simple backpressure mechanism), `DiscardPolicy`, and `DiscardOldestPolicy` — or supply your own lambda, as shown above.
- `getActiveCount()`, `getQueue().size()`, `getPoolSize()`, and `getCompletedTaskCount()` give live visibility into a running pool — invaluable for debugging saturation issues.
- `Executors.newFixedThreadPool`/`newSingleThreadExecutor`/`newCachedThreadPool` are all just `ThreadPoolExecutor` under the hood with particular constructor arguments — knowing this class means you understand what those factory methods are really doing.
