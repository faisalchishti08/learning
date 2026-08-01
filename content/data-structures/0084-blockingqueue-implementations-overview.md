---
card: data-structures
gi: 84
slug: blockingqueue-implementations-overview
title: BlockingQueue implementations (overview)
---

## 1. What it is

A `BlockingQueue` is a queue from `java.util.concurrent` that adds **blocking** behavior on top of ordinary queue operations: `put()` waits if the queue is full (instead of failing), and `take()` waits if the queue is empty (instead of returning `null`). This makes it the standard tool for safely passing work between threads — one thread produces, another consumes, without either needing to poll in a loop.

## 2. Why & when

Use a `BlockingQueue` whenever multiple threads need to hand off work safely: a producer thread generating tasks and one or more consumer threads processing them (a producer-consumer pipeline), or a fixed-size thread pool's work queue. Plain `ArrayDeque` is explicitly **not** thread-safe — using it from multiple threads without external locking can corrupt its internal state. `BlockingQueue` implementations handle the locking internally, and add the waiting behavior a producer-consumer handoff needs.

## 3. Core concept

**What backs it, and the choice between implementations.** `BlockingQueue` is an interface; several implementations trade off differently:
- **`ArrayBlockingQueue`** — a fixed-capacity, array-backed queue. You must choose a capacity upfront; `put()` blocks once full. Good when you want to cap how much unprocessed work can pile up.
- **`LinkedBlockingQueue`** — node-backed, optionally bounded (unbounded by default). More flexible capacity, slightly more overhead per element than the array-backed version.
- **`PriorityBlockingQueue`** — an unbounded blocking queue that orders elements by priority instead of FIFO, combining `PriorityQueue`'s ordering with blocking `take()`.
- **`SynchronousQueue`** — holds **zero** elements; every `put()` must wait for a matching `take()` and vice versa, a direct hand-off between exactly one producer and one consumer at a time.

**Ordering and complexity guarantees.** `ArrayBlockingQueue` and `LinkedBlockingQueue` are FIFO. `PriorityBlockingQueue` is priority-ordered. All standard `put`/`take` operations are O(1) (or O(log n) for the priority variant), same as their non-blocking counterparts — the added cost is the internal locking/waiting machinery, not the algorithmic complexity.

**When to choose it.** Choose a bounded queue (`ArrayBlockingQueue`, or `LinkedBlockingQueue` with a capacity) when you want backpressure — producers should slow down if consumers cannot keep up. Choose `SynchronousQueue` for a direct hand-off with no buffering at all. Never use a plain, non-blocking queue (`ArrayDeque`, `LinkedList`) across threads without your own external synchronization.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer thread calling put on a bounded blocking queue and a consumer thread calling take, with the producer blocking when the queue is full and the consumer blocking when it is empty">
  <g font-family="sans-serif" font-size="11">
    <rect x="30" y="70" width="100" height="40" fill="#161b22" stroke="#79c0ff" rx="4"/><text x="80" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">Producer thread</text>
    <rect x="270" y="60" width="140" height="60" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="340" y="85" fill="#e6edf3" text-anchor="middle" font-size="9">BlockingQueue</text>
    <text x="340" y="103" fill="#8b949e" text-anchor="middle" font-size="9">capacity: fixed</text>
    <rect x="510" y="70" width="100" height="40" fill="#161b22" stroke="#a5d6ff" rx="4"/><text x="560" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">Consumer thread</text>
    <line x1="130" y1="90" x2="266" y2="90" stroke="#79c0ff" marker-end="url(#bq)"/>
    <text x="198" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">put() -- blocks if full</text>
    <line x1="410" y1="90" x2="506" y2="90" stroke="#a5d6ff" marker-end="url(#bq)"/>
    <text x="458" y="80" fill="#a5d6ff" text-anchor="middle" font-size="9">take() -- blocks if empty</text>
    <defs><marker id="bq" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
  </g>
</svg>

Neither thread ever busy-polls: `put()` and `take()` each wait automatically when the queue cannot honor the request right away, resuming the instant the other side makes room or adds an item.

## 5. Runnable example

```java
// BlockingQueueOverview.java
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.PriorityBlockingQueue;
import java.util.concurrent.TimeUnit;

public class BlockingQueueOverview {

    // Basic: ArrayBlockingQueue -- fixed capacity, offer with a timeout instead of blocking forever.
    static void basicLevel() throws InterruptedException {
        BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(2);
        System.out.println("basic: offer 1 -> " + queue.offer(1));
        System.out.println("basic: offer 2 -> " + queue.offer(2));
        System.out.println("basic: offer 3, wait up to 200ms (queue is full) -> "
            + queue.offer(3, 200, TimeUnit.MILLISECONDS)); // false: still full after waiting
        System.out.println("basic: take -> " + queue.take());
    }

    // Intermediate: a real producer/consumer pair using put()/take(), which block instead of returning a sentinel.
    static void intermediateLevel() throws InterruptedException {
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>(5);

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 3; i++) {
                    queue.put(i); // blocks if the queue is full; here it never needs to, capacity is 5
                    System.out.println("intermediate: produced -> " + i);
                }
            } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 1; i <= 3; i++) {
                    int value = queue.take(); // blocks if the queue is empty until the producer adds something
                    System.out.println("intermediate: consumed -> " + value);
                }
            } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }

    // Advanced: PriorityBlockingQueue -- blocking take(), but priority order instead of FIFO.
    static void advancedLevel() throws InterruptedException {
        BlockingQueue<Integer> pq = new PriorityBlockingQueue<>();
        pq.put(5);
        pq.put(1);
        pq.put(3);
        System.out.println("advanced: PriorityBlockingQueue take order -> " + pq.take() + ", " + pq.take() + ", " + pq.take());
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BlockingQueueOverview.java`, then run `java BlockingQueueOverview.java`.

## 6. Walkthrough

1. `basicLevel()` creates an `ArrayBlockingQueue` with capacity `2`. The first two `offer` calls succeed. The third `offer(3, 200, TimeUnit.MILLISECONDS)` waits up to 200 milliseconds for room to appear, then returns `false`, since nothing removes an element in that window. `take()` then removes and returns `1`, the head.
2. `intermediateLevel()` runs a producer thread and a consumer thread concurrently against one shared `LinkedBlockingQueue`. The producer calls `put()` for values `1, 2, 3`; the consumer calls `take()` for the same count. Because the queue's capacity (5) is never exceeded here, `put()` never actually blocks — but if the consumer were slower, `put()` would automatically pause the producer once the queue filled, resuming the instant the consumer freed a slot, with no manual signaling code required.
3. `advancedLevel()` shows `PriorityBlockingQueue` combining two behaviors at once: `put()`/`take()` are safe across threads and block appropriately, while the actual order `take()` returns elements in is priority order (`1, 3, 5`), not the order they were put in (`5, 1, 3`).

## 7. Gotchas & takeaways

> Gotcha: forgetting to catch and correctly handle `InterruptedException` on `put()`/`take()` (for example, swallowing it silently instead of calling `Thread.currentThread().interrupt()` to restore the interrupt status) can make a thread's cancellation request disappear, leaving the thread running when it was supposed to stop.

- `BlockingQueue` adds thread-safe, waiting `put()`/`take()` on top of an ordinary queue — plain `ArrayDeque`/`LinkedList` are not safe across threads without external locking.
- `ArrayBlockingQueue` (bounded, array-backed), `LinkedBlockingQueue` (optionally bounded, node-backed), `PriorityBlockingQueue` (priority order), and `SynchronousQueue` (zero-capacity, direct hand-off) cover most producer-consumer needs.
- Bounded queues provide backpressure — producers block instead of the queue growing without limit.
- Related concepts: [FIFO semantics](0072-fifo-semantics.md), [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md).
