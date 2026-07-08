---
card: java
gi: 397
slug: executors-factory-fixed-cached-single-scheduled
title: Executors factory (fixed/cached/single/scheduled)
---

## 1. What it is

`Executors` is a factory class (not to be confused with `Executor`, the interface) that hands out pre-configured `ExecutorService` implementations so you don't have to construct a `ThreadPoolExecutor` by hand. The four you'll meet constantly are: `newFixedThreadPool(n)` (exactly `n` reusable threads, extra tasks queue up), `newCachedThreadPool()` (no fixed size — creates threads as needed and reuses idle ones, killing them after 60 seconds of inactivity), `newSingleThreadExecutor()` (exactly one thread, so tasks run one at a time in submission order), and `newScheduledThreadPool(n)` (a pool that also supports delayed and periodic execution).

## 2. Why & when

Building a `ThreadPoolExecutor` directly means deciding core pool size, maximum pool size, keep-alive time, and the work queue type yourself — reasonable for fine-tuned production tuning, but overkill for the common cases. `Executors` bundles up sensible defaults for those common cases so you can express *intent* directly: "I want exactly N workers" (`newFixedThreadPool`), "I want strict one-at-a-time ordering" (`newSingleThreadExecutor`), "I have a bursty, unpredictable workload and don't want to size a pool up front" (`newCachedThreadPool`), or "I need to run something later or repeatedly" (`newScheduledThreadPool`).

Picking the wrong one has real consequences: a `newCachedThreadPool()` fed millions of long-running tasks will happily create millions of threads and exhaust memory, since it has no upper bound. A `newFixedThreadPool()` sized too small under a bursty load queues everything else, adding latency. Choosing the right factory method up front is the first, cheapest form of concurrency tuning.

## 3. Core concept

Picture a coffee shop staffing model. `newFixedThreadPool(3)` is "always exactly 3 baristas on shift, regardless of how busy it gets — a line forms if there are more than 3 orders." `newCachedThreadPool()` is "call in extra baristas the moment a queue forms, and send them home the moment they've been idle a while — but there's no cap on how many you might call in." `newSingleThreadExecutor()` is "exactly one barista, so orders are made strictly in the order they arrived." `newScheduledThreadPool(n)` adds a clock to the mix — baristas who can also handle "make this drink in 10 minutes" or "make this drink every hour."

| Factory method | Threads | Best for |
|---|---|---|
| `newSingleThreadExecutor()` | 1 | Strict ordering, no concurrency needed |
| `newFixedThreadPool(n)` | exactly `n` | Known, steady workload |
| `newCachedThreadPool()` | unbounded, reused | Many short-lived, bursty tasks |
| `newScheduledThreadPool(n)` | `n`, timer-aware | Delayed or periodic tasks |

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four Executors factory methods produce different pool shapes: single thread, fixed count, unbounded cached, and scheduled">
  <rect x="8" y="8" width="624" height="204" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="12" font-family="sans-serif">Executors factory methods</text>

  <rect x="20" y="45" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">newSingleThreadExecutor()</text>
  <circle cx="90" cy="100" r="8" fill="#6db33f"/>
  <text x="90" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 thread, strict order</text>

  <rect x="180" y="45" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">newFixedThreadPool(3)</text>
  <circle cx="230" cy="100" r="8" fill="#6db33f"/><circle cx="250" cy="100" r="8" fill="#6db33f"/><circle cx="270" cy="100" r="8" fill="#6db33f"/>
  <text x="250" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">exactly 3, extras queue</text>

  <rect x="340" y="45" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="410" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">newCachedThreadPool()</text>
  <circle cx="380" cy="100" r="8" fill="#f85149"/><circle cx="400" cy="100" r="8" fill="#f85149"/><circle cx="420" cy="100" r="8" fill="#f85149"/><circle cx="440" cy="100" r="8" fill="#f85149"/>
  <text x="410" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">grows/shrinks, no cap</text>

  <rect x="500" y="45" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="565" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">newScheduledThreadPool(n)</text>
  <text x="565" y="105" fill="#e6edf3" font-size="18" text-anchor="middle" font-family="sans-serif">⏱</text>
  <text x="565" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delayed / periodic</text>

  <text x="20" y="165" fill="#8b949e" font-size="10" font-family="sans-serif">Pick the shape that matches the workload: steady, bursty, ordered, or time-based.</text>
</svg>

The four factory methods produce four different pool "shapes" — pick based on how the workload behaves, not habit.

## 5. Runnable example

Scenario: a notification service that resizes and sends user avatar images. The same job — process a batch of avatar uploads — is handled by a different pool shape at each level, showing how the choice changes behaviour without changing the task logic.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class AvatarQueueSingle {
    static void processAvatar(String user) throws InterruptedException {
        System.out.println("Processing " + user + " on " + Thread.currentThread().getName());
        Thread.sleep(50);
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newSingleThreadExecutor();

        for (String user : new String[]{"alice", "bob", "carol"}) {
            pool.submit(() -> {
                try { processAvatar(user); } catch (InterruptedException ignored) { }
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java AvatarQueueSingle.java`

`newSingleThreadExecutor()` guarantees the three avatars are processed strictly one after another, in submission order (alice, then bob, then carol) — useful when order matters, but there's no parallelism at all here, so three uploads take three times as long as one.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class AvatarQueueFixed {
    static void processAvatar(String user) throws InterruptedException {
        System.out.println("Processing " + user + " on " + Thread.currentThread().getName());
        Thread.sleep(50);
    }

    public static void main(String[] args) throws InterruptedException {
        // Known, steady workload: size the pool to the number of CPU cores available
        int workers = Runtime.getRuntime().availableProcessors();
        ExecutorService pool = Executors.newFixedThreadPool(Math.max(2, workers));

        for (String user : new String[]{"alice", "bob", "carol", "dave"}) {
            pool.submit(() -> {
                try { processAvatar(user); } catch (InterruptedException ignored) { }
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java AvatarQueueFixed.java`

Now several avatars process **concurrently** on different threads (you'll see different thread names in the output), since the pool is sized to match available CPU cores — a fixed pool is the right tool once the workload is steady and roughly known in advance.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class AvatarQueueCachedBursty {
    static void processAvatar(String user) throws InterruptedException {
        System.out.println("Processing " + user + " on " + Thread.currentThread().getName());
        Thread.sleep(50);
    }

    public static void main(String[] args) throws InterruptedException {
        // Bursty, unpredictable load (e.g. a viral sign-up spike): let the pool grow and shrink on demand
        ExecutorService pool = Executors.newCachedThreadPool();

        String[] burst = {"alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi"};
        CountDownLatch done = new CountDownLatch(burst.length);

        for (String user : burst) {
            pool.submit(() -> {
                try {
                    processAvatar(user);
                } catch (InterruptedException ignored) {
                } finally {
                    done.countDown();
                }
            });
        }

        done.await(); // wait until all 8 avatars are done before shutting the pool down
        System.out.println("Burst of " + burst.length + " avatars finished.");
        pool.shutdown();
    }
}
```

**How to run:** `java AvatarQueueCachedBursty.java`

`newCachedThreadPool()` spins up as many threads as needed for the whole burst of 8 (rather than queuing behind a fixed 2–4 workers), running them all essentially at once — exactly the shape you want for a short, unpredictable spike, but risky for a sustained heavy load since nothing caps how many threads it can create. `CountDownLatch` is used here to correctly wait for all 8 tasks before shutting the pool down.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `Executors.newCachedThreadPool()` creates a pool with zero core threads and an effectively unbounded maximum — it starts with no worker threads at all. `CountDownLatch done = new CountDownLatch(8)` creates a counter starting at 8, one per avatar in the burst.

The `for` loop submits all 8 tasks in a tight loop. Because a cached pool has no fixed thread count, the pool creates a new worker thread for each submission that doesn't find an idle one waiting — in practice, since all 8 submissions happen almost instantly, most or all of them get their own new thread, so all 8 `processAvatar` calls begin running in parallel almost immediately (in contrast to Level 1's forced serial order or Level 2's cap at CPU-core count).

Each task runs `processAvatar(user)`, prints its own name and thread, sleeps 50ms to simulate image-processing work, and then — in the `finally` block, so it runs whether or not `processAvatar` threw — calls `done.countDown()`, decrementing the shared counter by one.

Meanwhile, the main thread calls `done.await()` immediately after submitting all 8 tasks; this blocks `main` until the counter reaches zero. Once all 8 worker threads have called `countDown()`, `await()` returns, `main` prints the "finished" line, and `pool.shutdown()` lets the (now idle) worker threads terminate.

Expected output (order of the 8 "Processing ..." lines will vary run to run, since they run concurrently):
```
Processing alice on pool-1-thread-1
Processing bob on pool-1-thread-2
Processing carol on pool-1-thread-3
... (5 more, interleaved)
Burst of 8 avatars finished.
```

## 7. Gotchas & takeaways

> `newCachedThreadPool()` has **no upper bound** on thread count. Feeding it millions of tasks (especially long-running ones) can create thousands of live OS threads and exhaust memory or hit OS thread limits — reach for `newFixedThreadPool` or a manually-tuned `ThreadPoolExecutor` (see the next tutorial) once load is sustained rather than a short burst.

- `newSingleThreadExecutor()`: exactly one thread, guarantees strict submission-order execution — use when task order matters more than throughput.
- `newFixedThreadPool(n)`: exactly `n` reusable threads, extra tasks queue — use for steady, roughly-known workloads.
- `newCachedThreadPool()`: grows on demand, shrinks after 60s of idling, no cap — use for short, bursty, unpredictable workloads only.
- `newScheduledThreadPool(n)`: like a fixed pool but also supports `schedule`, `scheduleAtFixedRate`, and `scheduleWithFixedDelay` (covered in the ScheduledExecutorService tutorial).
- Whichever factory method you choose, you still own its lifecycle — always `shutdown()` it when done.
