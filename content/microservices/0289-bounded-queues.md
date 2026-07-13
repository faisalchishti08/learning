---
card: microservices
gi: 289
slug: bounded-queues
title: "Bounded queues"
---

## 1. What it is

A bounded queue is a queue with a fixed maximum capacity: once it holds that many items, any attempt to add another either blocks the caller, fails immediately, or rejects the new item — it can never grow past its configured limit. This is the concrete data structure that makes [backpressure](0288-backpressure-as-protection.md) enforceable: the bound is what actually stops a producer from getting arbitrarily far ahead of a consumer, converting an abstract "slow down" signal into a hard, physical limit.

## 2. Why & when

An unbounded queue anywhere in a system — a thread pool's work queue, an in-memory buffer between pipeline stages, a message broker's client-side buffer — is effectively a promise to accumulate unlimited memory if the producer ever outpaces the consumer for long enough. It doesn't matter how unlikely that seems under normal conditions; a single slow dependency, a traffic spike, or a stuck consumer thread is enough to trigger unbounded growth, and by the time it's visible as a symptom (rising memory, GC pressure, eventual `OutOfMemoryError`), the root cause can be hard to trace back to "that one queue we forgot to bound."

Bounding a queue forces an explicit decision about what happens when it's full — and that decision (block, reject, or drop) should be made deliberately for each specific use case, rather than left as an accident of using an unbounded default. Use bounded queues for essentially every in-memory queue in a production system: thread pool work queues, buffers between async pipeline stages, in-process message buffers — anywhere work can accumulate faster than it's consumed.

## 3. Core concept

Java's `java.util.concurrent` package provides bounded queue implementations directly; the choice of what happens on a full queue is made explicit via which method is called.

```java
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;

ArrayBlockingQueue<String> queue = new ArrayBlockingQueue<>(100); // fixed capacity, never grows

queue.put("item");                       // BLOCKS if full, until space frees up
boolean accepted = queue.offer("item");  // returns FALSE immediately if full, never blocks
boolean acceptedWithWait = queue.offer("item", 2, TimeUnit.SECONDS); // blocks up to a bound, then gives up
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bounded queue holds a fixed maximum number of slots; once every slot is filled, the three possible policies for a new arriving item are to block the caller until space frees up, to reject the item immediately, or to wait only up to a bounded timeout before giving up">
  <rect x="30" y="40" width="220" height="50" rx="6" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="35" y="45" width="35" height="40" fill="#6db33f" opacity="0.35"/>
  <rect x="73" y="45" width="35" height="40" fill="#6db33f" opacity="0.35"/>
  <rect x="111" y="45" width="35" height="40" fill="#6db33f" opacity="0.35"/>
  <rect x="149" y="45" width="35" height="40" fill="#6db33f" opacity="0.35"/>
  <rect x="187" y="45" width="35" height="40" fill="#6db33f" opacity="0.35"/>
  <text x="140" y="30" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">FULL bounded queue (fixed slots)</text>

  <text x="380" y="35" fill="#8b949e" font-size="7.5" font-family="sans-serif">put(): BLOCKS until space frees</text>
  <text x="380" y="65" fill="#8b949e" font-size="7.5" font-family="sans-serif">offer(): rejects IMMEDIATELY</text>
  <text x="380" y="95" fill="#8b949e" font-size="7.5" font-family="sans-serif">offer(timeout): waits, THEN gives up</text>
  <line x1="255" y1="60" x2="370" y2="35" stroke="#8b949e" marker-end="url(#arr289)"/>
  <line x1="255" y1="65" x2="370" y2="65" stroke="#8b949e" marker-end="url(#arr289)"/>
  <line x1="255" y1="70" x2="370" y2="95" stroke="#8b949e" marker-end="url(#arr289)"/>

  <defs><marker id="arr289" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A full bounded queue forces an explicit choice: block, reject immediately, or wait up to a bound before giving up.

## 5. Runnable example

Scenario: an unbounded thread pool queue that silently accumulates unbounded pending work under sustained overload, extended to a bounded queue with a rejection policy that fails fast once full, and finally a bounded queue combined with a custom rejection handler that sheds low-priority work while still accepting critical work, tying together bounded queues with priority-aware load shedding.

### Level 1 — Basic

```java
// File: UnboundedThreadPoolQueue.java -- a thread pool backed by an
// UNBOUNDED queue: submitting work always "succeeds" immediately, even
// if the pool can never keep up, silently accumulating unbounded pending tasks.
import java.util.concurrent.*;

public class UnboundedThreadPoolQueue {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new LinkedBlockingQueue<>()); // UNBOUNDED queue -- no limit at all

        for (int i = 0; i < 100000; i++) {
            int taskId = i;
            pool.submit(() -> { try { Thread.sleep(100); } catch (InterruptedException ignored) {} });
        }
        ThreadPoolExecutor tpe = (ThreadPoolExecutor) pool;
        System.out.println("Submitted 100,000 tasks instantly. Queue size right now: " + tpe.getQueue().size()
                + " (all accepted, all sitting in unbounded memory, 2 threads can only process 2 at a time)");
        pool.shutdownNow();
    }
}
```

How to run: `java UnboundedThreadPoolQueue.java`

One hundred thousand tasks are submitted to a pool with only 2 worker threads and an unbounded queue. Every single `submit` call succeeds instantly, regardless of the massive mismatch between submission rate and processing capacity — the queue size printed immediately after is close to 100,000, all held in memory, with the 2 threads able to work through only about 20 tasks per second (100ms each). In a real service under sustained overload, this exact pattern is a common cause of `OutOfMemoryError`, because nothing ever signals "stop, I can't keep up" back to whatever is submitting the work.

### Level 2 — Intermediate

```java
// File: BoundedQueueWithRejection.java -- the SAME pool configuration,
// but now the queue is bounded; once full, new submissions are REJECTED
// immediately via the pool's rejection policy instead of accumulating
// without limit.
import java.util.concurrent.*;

public class BoundedQueueWithRejection {
    public static void main(String[] args) {
        ExecutorService pool = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(50), // BOUNDED: at most 50 pending tasks
                new ThreadPoolExecutor.AbortPolicy()); // reject with RejectedExecutionException once full

        int accepted = 0, rejected = 0;
        for (int i = 0; i < 200; i++) {
            try {
                pool.submit(() -> { try { Thread.sleep(50); } catch (InterruptedException ignored) {} });
                accepted++;
            } catch (RejectedExecutionException e) {
                rejected++;
            }
        }
        System.out.println("Submitted 200 tasks: accepted=" + accepted + " rejected=" + rejected
                + " (capped at capacity + 2 in-flight, instead of accepting all 200 into unbounded memory)");
        pool.shutdownNow();
    }
}
```

How to run: `java BoundedQueueWithRejection.java`

The queue is now bounded at 50, and the pool uses `AbortPolicy`, which throws `RejectedExecutionException` for any submission once both the 2 worker threads are busy and the 50-slot queue is full. Submitting 200 tasks in a tight loop quickly fills the queue; once full, subsequent `submit` calls throw immediately, and the surrounding `try/catch` counts them as `rejected`. The accepted count caps out around 52 (2 in-flight + 50 queued) rather than accepting all 200 — the caller gets an immediate, explicit signal that the pool is overwhelmed instead of the work silently piling up.

### Level 3 — Advanced

```java
// File: BoundedQueueWithPriorityAwareRejection.java -- combines a
// bounded queue with a CUSTOM rejection handler that inspects the
// rejected task's priority: low-priority work is dropped silently
// (logged, not executed), but high-priority work is executed directly
// on the CALLER's thread as a last resort, so critical work is never lost
// purely because the queue happened to be full.
import java.util.concurrent.*;

public class BoundedQueueWithPriorityAwareRejection {
    static class PrioritizedTask implements Runnable {
        final boolean highPriority; final String name;
        PrioritizedTask(String name, boolean highPriority) { this.name = name; this.highPriority = highPriority; }
        public void run() {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        }
    }

    public static void main(String[] args) {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(20),
                (rejectedRunnable, executor) -> {
                    PrioritizedTask task = (PrioritizedTask) rejectedRunnable;
                    if (task.highPriority) {
                        System.out.println("  QUEUE FULL: high-priority '" + task.name + "' runs on CALLER thread instead of being lost");
                        rejectedRunnable.run(); // CallerRunsPolicy-style: execute it anyway, just not on a pool thread
                    } else {
                        System.out.println("  QUEUE FULL: low-priority '" + task.name + "' DROPPED (logged, not executed)");
                    }
                });

        for (int i = 0; i < 30; i++) {
            boolean isHigh = (i % 5 == 0); // every 5th task is high priority
            pool.submit(new PrioritizedTask("task-" + i, isHigh));
        }
        pool.shutdown();
        try { pool.awaitTermination(5, TimeUnit.SECONDS); } catch (InterruptedException ignored) {}
        System.out.println("Done.");
    }
}
```

How to run: `java BoundedQueueWithPriorityAwareRejection.java`

Thirty tasks are submitted, one in five marked high-priority, against a pool with only 20 queue slots and 2 worker threads. As the queue fills, the custom `RejectedExecutionHandler` intercepts every rejection: for a high-priority task, it runs the task directly on the *submitting* thread rather than losing it (a variation on Java's built-in `CallerRunsPolicy`, here made priority-aware); for a low-priority task, it logs the drop and discards it entirely. This shows bounded queues combined with a rejection policy doing real, deliberate load shedding — capacity is preserved for important work even under sustained overload, rather than either accepting everything unboundedly or rejecting everything indiscriminately once full.

## 6. Walkthrough

Trace `BoundedQueueWithPriorityAwareRejection.main` for the point where the queue first becomes full. **First**, the pool is constructed with `corePoolSize=2`, a 20-slot `ArrayBlockingQueue`, and a lambda implementing `RejectedExecutionHandler`.

**The loop submits 30 `PrioritizedTask` instances.** For the first roughly 22 submissions (2 running immediately on the pool's 2 threads, 20 queued), `pool.submit` succeeds normally — `ThreadPoolExecutor` accepts into the queue as long as there's room.

**Once the queue is full** (both threads busy with 50ms tasks, 20 more queued), the next `submit` call cannot be accepted through the normal path. `ThreadPoolExecutor` internally calls the configured `RejectedExecutionHandler.rejectedExecution(runnable, executor)` — this is where the custom lambda runs.

**Inside the lambda**, the rejected `Runnable` is cast back to `PrioritizedTask` to inspect its `highPriority` field. If `true`, the lambda calls `rejectedRunnable.run()` directly — this executes the task's `run()` method synchronously, on the *thread that called `submit`* (the main thread here), not on one of the pool's worker threads. This means the main thread briefly blocks for that task's 50ms of work, but the task is never lost. If `false`, the lambda just logs the drop and returns without calling `run()` at all — that task's work simply never happens.

**This repeats** for each subsequent submission that arrives while the queue remains full: every 5th task (index 0, 5, 10, 15, ...) is high-priority and gets executed inline on the caller's thread; the rest are silently dropped with a log line.

**Data/state transformation across layers**: a task enters at the "submission" layer (main thread calling `submit`) → the pool's internal queue layer either accepts it (added to the 20-slot buffer) or, once full, escalates to the rejection-handling layer → the rejection handler layer makes the final priority-based decision → the outcome is either the task executing on a pool worker thread (normal path), executing synchronously on the caller's thread (high-priority overflow path), or never executing at all (low-priority overflow path, dropped).

```
submit(task) -> pool has room? --yes--> queued, runs on a worker thread eventually
                        |no (queue FULL)
                        v
             rejectedExecution(task, pool) called
                        |
        high priority? --yes--> task.run() on the CALLER's thread (never lost)
                        |no
                        v
                   dropped, logged, never executed
```

## 7. Gotchas & takeaways

> An unbounded queue anywhere in a pipeline defeats every other resilience pattern applied downstream of it — a circuit breaker, a timeout, or a bulkhead protecting the *consumer* does nothing to stop unbounded memory growth in a queue feeding that consumer if the queue itself has no limit.

- Every in-memory queue in a production system should have an explicit, deliberately chosen capacity — there is rarely a good reason to leave one truly unbounded.
- The choice of what happens on a full queue (`put` blocks, `offer` rejects immediately, `offer(timeout)` waits briefly then rejects, or a custom `RejectedExecutionHandler`) should match the specific use case — a blocking producer thread has a different cost than a synchronous rejection.
- Java's default `Executors.newFixedThreadPool` and similar convenience factory methods use an unbounded `LinkedBlockingQueue` internally — constructing a `ThreadPoolExecutor` directly, as shown here, is necessary to get an explicitly bounded queue.
- Combine a bounded queue's rejection with priority information when available (as in Level 3) to shed low-value work under overload while still protecting the throughput of critical work, rather than treating all rejected work identically.
