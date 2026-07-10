---
card: java
gi: 836
slug: blockingqueue-family-array-linked-priority-delay-synchronous
title: BlockingQueue family (Array/Linked/Priority/Delay/Synchronous)
---

## 1. What it is

`BlockingQueue<E>` extends [`Queue`](0805-queue.md) with **blocking** insertion and removal methods — `put(e)` (waits if the queue is full, for bounded implementations) and `take()` (waits if the queue is empty) — designed specifically for producer-consumer coordination between threads, without any manual `wait`/`notify` or polling loop needed. The JDK provides five implementations, each suited to a different shape of problem: `ArrayBlockingQueue` (fixed-capacity, array-backed, FIFO), `LinkedBlockingQueue` (optionally-bounded, node-based, FIFO), `PriorityBlockingQueue` (unbounded, orders elements by priority like [`PriorityQueue`](0833-priorityqueue-binary-heap.md), but thread-safe and blocking), `DelayQueue` (elements become available only after their individual delay expires), and `SynchronousQueue` (holds no elements at all — every `put` must be matched by a waiting `take`, a direct hand-off between exactly one producer and one consumer).

## 2. Why & when

Coordinating producer and consumer threads manually — a producer checking "is there room?" and a consumer checking "is there anything?" — requires careful `wait`/`notify`/`notifyAll` code that's notoriously easy to get wrong (missed signals, spurious wakeups, lost notifications). `BlockingQueue` implementations handle all of that internally: `put` and `take` block automatically exactly when needed and wake up automatically exactly when conditions change, with correct handling of all the classic concurrency pitfalls. Reach for `ArrayBlockingQueue` when a fixed, bounded buffer size is a deliberate backpressure mechanism (producers must slow down once the buffer fills); `LinkedBlockingQueue` for a similar role with either no bound or a very large one; `PriorityBlockingQueue` for a producer-consumer pipeline where consumers should always get the highest-priority item next; `DelayQueue` for scheduling — "process this once its delay expires, not before"; and `SynchronousQueue` for direct thread-to-thread handoff with zero buffering, common in thread-pool implementations like `Executors.newCachedThreadPool()`.

## 3. Core concept

```java
BlockingQueue<String> jobs = new ArrayBlockingQueue<>(2); // fixed capacity of 2

jobs.put("job-1"); // succeeds immediately
jobs.put("job-2"); // succeeds immediately, queue is now full

// A third put() call from another thread would BLOCK here until a consumer calls take()
// to make room -- no busy-waiting, no manual synchronization needed.

String next = jobs.take(); // blocks if empty; here it returns "job-1" immediately, since one is present
```

`put`/`take` are the blocking pair; `offer`/`poll` (inherited from `Queue`, plus timed overloads like `offer(e, timeout, unit)`) provide non-blocking or bounded-wait alternatives for code that doesn't want to block indefinitely.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer thread calls put to add work; a consumer thread calls take to remove it; both block automatically exactly when the queue is full or empty, respectively">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="110" y="55" fill="#e6edf3" font-size="10" text-anchor="middle">producer thread</text>

    <line x1="180" y1="50" x2="250" y2="50" stroke="#3fb950" stroke-width="2" marker-end="url(#a836)"/>
    <text x="215" y="40" fill="#3fb950" font-size="9" text-anchor="middle">put()</text>

    <rect x="260" y="70" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="320" y="100" fill="#e6edf3" font-size="10" text-anchor="middle">BlockingQueue</text>

    <line x1="380" y1="90" x2="460" y2="90" stroke="#f0883e" stroke-width="2" marker-end="url(#a836b)"/>
    <text x="420" y="80" fill="#f0883e" font-size="9" text-anchor="middle">take()</text>

    <rect x="460" y="70" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="530" y="95" fill="#e6edf3" font-size="10" text-anchor="middle">consumer thread</text>
  </g>
  <text x="320" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">put() blocks automatically if full; take() blocks automatically if empty — no manual wait/notify needed</text>

  <defs>
    <marker id="a836" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a836b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

*`put()` and `take()` block automatically exactly when the queue is full or empty — no manual `wait`/`notify` coordination code needed.*

## 5. Runnable example

Scenario: a background job-processing pipeline, growing from a basic bounded producer-consumer pair, to priority-ordered job processing, to a scheduled retry mechanism using `DelayQueue`.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class JobPipelineBasic {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> jobs = new ArrayBlockingQueue<>(2); // capacity 2 -- deliberate backpressure

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 4; i++) {
                    jobs.put("job-" + i); // blocks automatically once the queue fills up
                    System.out.println("produced job-" + i);
                }
            } catch (InterruptedException ignored) {}
        });

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 1; i <= 4; i++) {
                    String job = jobs.take(); // blocks automatically if the queue is empty
                    System.out.println("consumed " + job);
                    Thread.sleep(50); // simulate slower processing than production
                }
            } catch (InterruptedException ignored) {}
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }
}
```

**How to run:** `java JobPipelineBasic.java` (JDK 17+). Exact interleaving of "produced"/"consumed" lines can vary slightly by timing, but all four jobs are always produced and consumed correctly, with the producer automatically pausing whenever the two-slot buffer fills.

Expected output shape:
```
produced job-1
produced job-2
consumed job-1
produced job-3
consumed job-2
produced job-4
consumed job-3
consumed job-4
```

No manual locking, `wait`, or `notify` calls were needed — `put`'s automatic blocking once the buffer reaches capacity, and `take`'s automatic blocking when empty, handle all the coordination.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class PriorityJobPipeline {
    record Job(String name, int priority) implements Comparable<Job> {
        @Override public int compareTo(Job other) { return Integer.compare(priority, other.priority); }
    }

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Job> jobs = new PriorityBlockingQueue<>(); // unbounded, priority-ordered, thread-safe

        jobs.put(new Job("cleanup", 5));
        jobs.put(new Job("deploy-hotfix", 1)); // most urgent
        jobs.put(new Job("send-report", 3));

        System.out.println("processing order (lowest priority number first):");
        for (int i = 0; i < 3; i++) {
            Job next = jobs.take(); // always returns the current highest-priority job
            System.out.println("  " + next.name() + " (priority " + next.priority() + ")");
        }
    }
}
```

**How to run:** `java PriorityJobPipeline.java`.

Expected output:
```
processing order (lowest priority number first):
  deploy-hotfix (priority 1)
  send-report (priority 3)
  cleanup (priority 5)
```

The real-world concern added: `PriorityBlockingQueue` combines [`PriorityQueue`](0833-priorityqueue-binary-heap.md)'s heap-based priority ordering with `BlockingQueue`'s thread-safe, blocking semantics — `take()` always returns the current highest-priority element (by `Comparable` or a supplied `Comparator`) and blocks if the queue happens to be empty, safe for multiple concurrent producer and consumer threads.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class DelayedRetryQueue {
    static class RetryTask implements Delayed {
        final String name;
        final long readyAtNanos;

        RetryTask(String name, long delayMillis) {
            this.name = name;
            this.readyAtNanos = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(delayMillis);
        }

        @Override
        public long getDelay(TimeUnit unit) {
            long remaining = readyAtNanos - System.nanoTime();
            return unit.convert(remaining, TimeUnit.NANOSECONDS);
        }

        @Override
        public int compareTo(Delayed other) {
            return Long.compare(this.getDelay(TimeUnit.NANOSECONDS), other.getDelay(TimeUnit.NANOSECONDS));
        }

        @Override public String toString() { return name; }
    }

    public static void main(String[] args) throws InterruptedException {
        DelayQueue<RetryTask> retryQueue = new DelayQueue<>();
        retryQueue.put(new RetryTask("retry-order-42", 300));
        retryQueue.put(new RetryTask("retry-order-7", 100)); // shorter delay -- ready FIRST despite being added second
        retryQueue.put(new RetryTask("retry-order-99", 200));

        System.out.println("waiting for tasks to become ready (take() blocks until each one's delay expires)...");
        long start = System.currentTimeMillis();
        for (int i = 0; i < 3; i++) {
            RetryTask ready = retryQueue.take(); // blocks until the SHORTEST remaining delay elapses
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("  ready at +" + elapsed + "ms: " + ready);
        }
    }
}
```

**How to run:** `java DelayedRetryQueue.java`. Exact millisecond timings vary slightly by machine, but the *order* is always shortest-delay-first, and each `take()` genuinely blocks until that task's delay has elapsed.

Expected output shape:
```
waiting for tasks to become ready (take() blocks until each one's delay expires)...
  ready at +~100ms: retry-order-7
  ready at +~200ms: retry-order-99
  ready at +~300ms: retry-order-42
```

This adds the production-flavored hard case: `DelayQueue`, which only ever makes an element available to `take()` once that specific element's `getDelay()` reaches zero or below — even though `"retry-order-42"` (300ms delay) was added first, `take()` correctly blocks past it and returns `"retry-order-7"` (100ms delay) first, since its delay expires soonest. This is exactly the mechanism behind scheduled-retry and delayed-task-execution systems: enqueue a task with "don't touch this until N milliseconds from now," and a consumer thread calling `take()` in a loop naturally processes each one exactly when — not before — it becomes ready.

## 6. Walkthrough

Tracing `DelayedRetryQueue.main`:

1. Three `RetryTask` objects are constructed with different delays (300ms, 100ms, 200ms) and `put` into the `DelayQueue` in that order. Each task's `readyAtNanos` field is computed at construction time as "now plus this task's delay."
2. The `for` loop calls `retryQueue.take()` three times. Internally, `DelayQueue` maintains its elements in a priority-queue-like structure ordered by remaining delay (via each element's `compareTo`, which compares `getDelay(TimeUnit.NANOSECONDS)`), so the element with the *soonest* expiration is always at the "front."
3. The first `take()` call checks the front element's `getDelay()` — initially, `"retry-order-7"` (100ms delay) has the smallest remaining delay of the three, so it's at the front. `take()` blocks until that specific delay reaches zero, then returns it — roughly 100ms after the program started.
4. The second `take()` call re-examines the (now two-element) queue: `"retry-order-99"` (200ms delay) now has the smallest remaining delay of what's left, so `take()` blocks until *its* delay expires (roughly 200ms after start) and returns it.
5. The third `take()` call similarly blocks until `"retry-order-42"`'s 300ms delay expires, then returns it — completing the sequence in delay order (`retry-order-7`, `retry-order-99`, `retry-order-42`), regardless of the original insertion order (`retry-order-42`, `retry-order-7`, `retry-order-99`).

## 7. Gotchas & takeaways

> **Gotcha:** `SynchronousQueue` (not shown in the runnable examples above, but part of the family) holds **zero** elements internally — calling `put()` on it blocks until another thread is simultaneously calling `take()`, and vice versa. Calling `size()` on a `SynchronousQueue` always returns `0`, even while threads are actively blocked inside `put`/`take` waiting for a handoff partner — a common point of confusion for anyone expecting it to behave like a "queue with capacity 1."

- `BlockingQueue` adds blocking `put`/`take` (plus timed `offer`/`poll` variants) to [`Queue`](0805-queue.md), designed for producer-consumer coordination without manual `wait`/`notify` code.
- `ArrayBlockingQueue` (fixed bound) and `LinkedBlockingQueue` (optionally bounded) are the general-purpose FIFO choices; `PriorityBlockingQueue` adds priority ordering; `DelayQueue` adds per-element readiness delays; `SynchronousQueue` provides zero-buffer, direct thread-to-thread handoff.
- A bounded queue's capacity acts as deliberate backpressure — producers automatically pause via `put()` once the buffer fills, rather than needing manual flow-control logic.
- `DelayQueue`'s `take()` only ever returns an element once its individual delay has expired, always in soonest-ready-first order, regardless of insertion order.
- These implementations are the standard building blocks behind thread-pool work queues (`ExecutorService` implementations typically use a `BlockingQueue` internally) and scheduled-retry systems.
