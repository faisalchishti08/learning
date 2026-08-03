---
card: data-structures
gi: 193
slug: concurrent-queues-overview
title: Concurrent queues (overview)
---

## 1. What it is

`java.util.concurrent` provides several thread-safe queue implementations, each suited to a different producer/consumer pattern: `ConcurrentLinkedQueue` (lock-free, unbounded), `LinkedBlockingQueue`/`ArrayBlockingQueue` (blocking, with optional capacity limits), and `PriorityBlockingQueue` (blocking, priority-ordered). All let multiple threads safely add and remove elements without external synchronization.

## 2. Why & when

Queues are the natural structure for producer/consumer coordination: one or more threads produce work items, one or more threads consume and process them. Plain `java.util` queues (`ArrayDeque`, `LinkedList`) are not thread-safe and will corrupt under concurrent access. The `java.util.concurrent` queue family solves this, and the choice between them comes down to two questions: do you want lock-free, non-blocking access, or do you want consumers to **block** (wait) when the queue is empty? And do you need a **bounded** capacity to apply backpressure?

## 3. Core concept

**`ConcurrentLinkedQueue`.** A lock-free, unbounded FIFO queue using compare-and-swap (CAS) operations instead of locks. `offer`/`poll` never block — `poll` on an empty queue returns `null` immediately rather than waiting. Best for high-throughput scenarios where you can tolerate polling in a loop, or where "nothing to do right now" is handled gracefully without blocking a thread.

**`LinkedBlockingQueue` / `ArrayBlockingQueue`.** Both implement `BlockingQueue`, adding `put` (blocks if the queue is full, only relevant when bounded) and `take` (blocks if the queue is empty, waiting until an element becomes available) — exactly the primitives needed for a classic producer/consumer setup, where consumer threads should simply sleep until there is work, rather than busy-poll. `ArrayBlockingQueue` is backed by a fixed-size circular array (must specify a capacity at construction — always bounded). `LinkedBlockingQueue` is backed by linked nodes and can be unbounded (default) or given an optional capacity limit.

**`PriorityBlockingQueue`.** A blocking queue backed by a [binary heap](0116-heap-property-array-representation.md), like `PriorityQueue`, but thread-safe and blocking: `take()` waits if the queue is empty, and always returns the current smallest (or highest-priority) element once available. Unbounded by default.

**Why bounded queues matter for backpressure.** An unbounded queue between a fast producer and a slow consumer can grow without limit, eventually exhausting memory. A bounded queue (`ArrayBlockingQueue`, or `LinkedBlockingQueue` with a capacity) makes `put` block once full, naturally slowing the producer down to match the consumer's pace — this is the mechanism behind "backpressure" in many real systems, including `java.util.concurrent.ThreadPoolExecutor`'s internal work queue.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer thread putting items into a bounded blocking queue, blocking when full, and a consumer thread taking items, blocking when empty">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="40" y="30" width="90" height="30" fill="#161b22" stroke="#79c0ff"/><text x="85" y="50" text-anchor="middle" font-size="9">Producer</text>
    <rect x="480" y="30" width="90" height="30" fill="#161b22" stroke="#f0883e"/><text x="525" y="50" text-anchor="middle" font-size="9">Consumer</text>

    <rect x="200" y="70" width="240" height="40" fill="#0d1117" stroke="#8b949e"/>
    <text x="320" y="94" text-anchor="middle" font-size="9">ArrayBlockingQueue (capacity 3): [x, x, x]</text>

    <line x1="130" y1="45" x2="200" y2="90" stroke="#79c0ff"/><text x="150" y="70" font-size="8" fill="#f44336">put() BLOCKS -- queue full</text>
    <line x1="440" y1="90" x2="480" y2="45" stroke="#f0883e"/><text x="440" y="65" font-size="8" fill="#3fb950">take() succeeds -- frees a slot</text>

    <text x="200" y="150" font-size="9" fill="#8b949e">once take() removes one item, producer's blocked put() can proceed</text>
    <text x="200" y="170" font-size="9" fill="#8b949e">this is backpressure: a slow consumer naturally throttles a fast producer</text>
  </g>
</svg>

A bounded blocking queue couples producer and consumer speed automatically, no manual throttling code needed.

## 5. Runnable example

```java
// ConcurrentQueues.java
import java.util.concurrent.*;
import java.util.*;

public class ConcurrentQueues {

    // Basic: ConcurrentLinkedQueue -- lock-free, non-blocking, poll() returns null on empty.
    static void basicLevel() {
        ConcurrentLinkedQueue<Integer> queue = new ConcurrentLinkedQueue<>();
        queue.offer(1);
        queue.offer(2);

        System.out.println("basic: poll() -> " + queue.poll());
        System.out.println("basic: poll() -> " + queue.poll());
        System.out.println("basic: poll() on empty queue -> " + queue.poll()); // null, does not block
    }

    // Intermediate: a producer/consumer pair using LinkedBlockingQueue's blocking take().
    static void intermediateLevel() throws InterruptedException {
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>();

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 5; i++) {
                try {
                    queue.put(i);
                    System.out.println("intermediate: produced -> " + i);
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });

        Thread consumer = new Thread(() -> {
            for (int i = 0; i < 5; i++) {
                try {
                    int value = queue.take(); // blocks until an item is available
                    System.out.println("intermediate: consumed -> " + value);
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }

    // Advanced: a bounded ArrayBlockingQueue demonstrating backpressure -- a fast producer blocks on a full queue.
    static void advancedLevel() throws InterruptedException {
        BlockingQueue<Integer> boundedQueue = new ArrayBlockingQueue<>(2); // tiny capacity to force blocking

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 4; i++) {
                try {
                    long start = System.nanoTime();
                    boundedQueue.put(i); // blocks once the queue holds 2 items
                    long waited = System.nanoTime() - start;
                    System.out.printf("advanced: put(%d) took %.1f ms%n", i, waited / 1_000_000.0);
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });

        producer.start();
        Thread.sleep(200); // let the producer fill the queue and start blocking on put(3)

        System.out.println("advanced: consumer slowly draining -> " + boundedQueue.take());
        Thread.sleep(200);
        System.out.println("advanced: consumer slowly draining -> " + boundedQueue.take());

        producer.join();
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ConcurrentQueues.java`

## 6. Walkthrough

`ConcurrentLinkedQueue`: `offer(1)`, `offer(2)` add without any blocking, using CAS internally to safely update the queue's linked structure even under concurrent access. `poll()` twice returns `1` then `2`, FIFO order. A third `poll()` on the now-empty queue returns `null` immediately — the calling thread is never paused waiting for something to appear.

`LinkedBlockingQueue` producer/consumer: the producer thread calls `put(i)` for `i = 1..5`, and the consumer thread calls `take()` five times. Because the queue is unbounded, `put` never blocks here. But `take()` **does** block whenever the consumer catches up and the queue is momentarily empty — it simply waits, using no CPU, until the producer's next `put` makes an element available, then wakes and returns it. This coordination (wait-for-data) is exactly what makes `BlockingQueue` suited to producer/consumer designs, compared to a non-blocking queue that would force the consumer to busy-poll in a loop.

`ArrayBlockingQueue(2)` (capacity `2`): the producer calls `put(1)` and `put(2)` immediately, filling the queue. Calling `put(3)` next **blocks**, since the queue is full — the producer thread pauses here, doing no work, until space frees up. Meanwhile, `Thread.sleep(200)` in the main thread lets this blocking actually happen before the "consumer" calls `take()`, which removes one element (`1`), freeing a slot — at that instant, the producer's blocked `put(3)` call unblocks and completes. This is backpressure in action: the producer is automatically throttled to the consumer's pace, with no manual rate-limiting code required.

**Complexity.** `ConcurrentLinkedQueue`: `offer`/`poll` `O(1)`, lock-free. `LinkedBlockingQueue`/`ArrayBlockingQueue`: `put`/`take` `O(1)`, using a lock (or two separate locks for head/tail in `LinkedBlockingQueue`, allowing concurrent producers and consumers to proceed somewhat independently). `PriorityBlockingQueue`: `put`/`take` `O(log n)`, matching the underlying heap.

## 7. Gotchas & takeaways

> `poll()` (non-blocking, returns `null` on empty) and `take()` (blocking, waits for an element) look similar but behave completely differently under an empty queue — using `poll()` in a producer/consumer loop when you actually needed `take()`'s blocking wait forces you to write your own busy-polling loop, wasting CPU.

- Always catch `InterruptedException` correctly around blocking calls (`put`, `take`) — the idiomatic response is to call `Thread.currentThread().interrupt()` to restore the interrupted status, then exit the loop, rather than silently swallowing the exception.
- Choose a bounded queue (`ArrayBlockingQueue`, or `LinkedBlockingQueue` with an explicit capacity) whenever an unbounded queue between a fast producer and slow consumer could grow without limit and exhaust memory — the bound gives you backpressure for free.
- `PriorityBlockingQueue` inherits `PriorityQueue`'s caveat: iterating it directly does not yield sorted order, only repeated `take()`/`poll()` calls do.
