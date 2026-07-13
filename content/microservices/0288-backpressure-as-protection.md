---
card: microservices
gi: 288
slug: backpressure-as-protection
title: "Backpressure as protection"
---

## 1. What it is

Backpressure is a signal flowing *backward*, from a slower consumer to a faster producer, telling the producer to slow down or stop sending more work until the consumer catches up. As a resilience mechanism, it protects the consumer from being overwhelmed by preventing unbounded work from piling up in the first place, rather than letting it accumulate and then dealing with the consequences (memory exhaustion, cascading slowness, eventual crash) after the fact.

## 2. Why & when

When a producer generates work faster than a consumer can process it, that excess work has to go *somewhere* — it either queues up (consuming memory without bound), gets dropped silently (losing data), or the whole pipeline slows to the consumer's pace. Backpressure makes this an explicit, controlled choice: the consumer actively communicates "I'm full, stop sending" back to the producer, which then has to decide what to do (buffer up to a bound, block, drop, or apply its own upstream backpressure to its own producer).

This differs from [rate limiting](0273-rate-limiter-pattern.md) and [throttling](0279-throttling-load-shedding.md) in one key way: those are typically based on a configured policy (N requests per second), whereas backpressure is a real-time signal reflecting the consumer's *actual current capacity*, which can vary dynamically. Use backpressure anywhere a fast producer and a slower consumer are directly connected — a message queue consumer processing events slower than they're published, a reactive stream pipeline, a database connection pool being asked for more connections than exist. It is the mechanism that makes [bounded queues](0289-bounded-queues.md) actually effective, rather than just delaying the same overload by a fixed buffer size.

## 3. Core concept

A backpressure-aware channel exposes both a way for the producer to check "can I send more?" and a way for the consumer to signal "I'm ready for more" — the classic reactive-streams model uses an explicit `request(n)` from the consumer to pull exactly the amount of work it can currently handle.

```java
class BackpressureAwareQueue<T> {
    final java.util.concurrent.BlockingQueue<T> queue;
    BackpressureAwareQueue(int capacity) { queue = new java.util.concurrent.ArrayBlockingQueue<>(capacity); }

    // Producer BLOCKS here once the queue is full -- this IS the backpressure signal.
    void produce(T item) throws InterruptedException { queue.put(item); }

    // Consumer pulls at its own pace; each poll frees a slot for the producer.
    T consume() throws InterruptedException { return queue.take(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fast producer sends items into a bounded buffer consumed by a slower consumer; once the buffer fills, a backpressure signal flows backward to the producer, causing it to slow down or block instead of overwhelming the consumer with unbounded work">
  <rect x="20" y="60" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">fast producer</text>

  <line x1="130" y1="80" x2="230" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr288)"/>

  <rect x="240" y="60" width="160" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">bounded buffer (FULL)</text>

  <line x1="400" y1="80" x2="480" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr288)"/>

  <rect x="490" y="60" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">slow consumer</text>

  <path d="M320,100 Q320,140 75,140 Q75,140 75,100" stroke="#8b949e" fill="none" stroke-dasharray="3,3" marker-end="url(#arr288)"/>
  <text x="200" y="155" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">backpressure signal: "I'm full, slow down"</text>

  <defs><marker id="arr288" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The consumer's fullness flows backward to the producer, actively slowing it rather than letting unbounded work accumulate.

## 5. Runnable example

Scenario: an unbounded queue between a fast producer and slow consumer that grows without limit, extended to a bounded, blocking queue where the producer is forced to slow down once the buffer fills (real backpressure), and finally adding a reactive-style pull model where the consumer explicitly requests batches of work, giving it precise control over its own load.

### Level 1 — Basic

```java
// File: UnboundedQueueGrowsForever.java -- a fast producer and a slow
// consumer connected by an UNBOUNDED queue: nothing stops the queue
// from growing without limit, risking memory exhaustion.
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class UnboundedQueueGrowsForever {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>(); // NO capacity bound

        Thread producer = new Thread(() -> {
            for (int i = 0; i < 1000; i++) {
                queue.offer(i); // NEVER blocks -- always succeeds, queue just keeps growing
            }
        });
        producer.start();
        producer.join();

        // Consumer hasn't even started yet -- everything piled up in memory already.
        System.out.println("Producer finished instantly. Queue size: " + queue.size()
                + " items sitting in unbounded memory, consumer hasn't processed a single one yet.");
    }
}
```

How to run: `java UnboundedQueueGrowsForever.java`

The producer fires 1000 items into an unbounded `LinkedBlockingQueue` with no consumer running concurrently to drain it. Because the queue has no capacity limit, `offer` always succeeds instantly regardless of how far behind the consumer is — the producer finishes immediately, having accumulated all 1000 items in memory with zero backpressure. In a real system with a genuinely faster producer and a much slower consumer, this pattern accumulates unbounded memory until the process runs out of heap.

### Level 2 — Intermediate

```java
// File: BoundedQueueBlocksProducer.java -- the SAME producer/consumer,
// but now the queue has a fixed capacity; once full, the producer's
// put() call BLOCKS until the consumer frees a slot -- this blocking IS
// the backpressure.
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class BoundedQueueBlocksProducer {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(10); // capacity BOUND of 10

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 0; i < 30; i++) {
                    int item = queue.take();
                    Thread.sleep(50); // deliberately SLOW consumer
                    System.out.println("  consumed: " + item + " (queue size now " + queue.size() + ")");
                }
            } catch (InterruptedException ignored) {}
        });

        Thread producer = new Thread(() -> {
            try {
                for (int i = 0; i < 30; i++) {
                    long before = System.currentTimeMillis();
                    queue.put(i); // BLOCKS once the queue of 10 is full
                    long waited = System.currentTimeMillis() - before;
                    if (waited > 5) System.out.println("producer BLOCKED for " + waited + "ms sending item " + i + " -- backpressure!");
                }
            } catch (InterruptedException ignored) {}
        });

        consumer.start();
        producer.start();
        producer.join();
        consumer.join();
    }
}
```

How to run: `java BoundedQueueBlocksProducer.java`

The queue now has a fixed capacity of 10. The producer runs far faster than the deliberately slow consumer (50ms per item), so it quickly fills the queue to capacity. From that point on, every `queue.put(i)` call blocks until the consumer's `queue.take()` frees a slot — the printed "producer BLOCKED" messages show the producer being forced to slow down to roughly match the consumer's pace, entirely because the bounded queue refuses to accept more than 10 items at once. This is backpressure in its simplest, most direct form: the producer physically cannot get ahead of the consumer by more than the buffer's capacity.

### Level 3 — Advanced

```java
// File: PullBasedBackpressure.java -- a reactive-streams-style PULL
// model: the consumer explicitly requests a specific number of items at
// a time, giving it precise, self-paced control over its own load,
// rather than relying on the producer simply blocking on a full buffer.
import java.util.concurrent.*;
import java.util.*;

public class PullBasedBackpressure {
    static class PullBasedSource {
        final Queue<Integer> available = new ConcurrentLinkedQueue<>();
        { for (int i = 0; i < 1000; i++) available.add(i); } // simulates a large upstream data source

        // Consumer calls this to PULL exactly `n` items -- never more than it asked for.
        List<Integer> request(int n) {
            List<Integer> batch = new ArrayList<>();
            for (int i = 0; i < n && !available.isEmpty(); i++) batch.add(available.poll());
            return batch;
        }
        boolean hasMore() { return !available.isEmpty(); }
    }

    public static void main(String[] args) throws InterruptedException {
        PullBasedSource source = new PullBasedSource();
        int batchSize = 5; // consumer decides how much it can handle per round
        int totalProcessed = 0;

        while (source.hasMore() && totalProcessed < 20) {
            List<Integer> batch = source.request(batchSize); // consumer PULLS exactly what it wants
            for (int item : batch) {
                Thread.sleep(20); // simulate real per-item processing work
                totalProcessed++;
            }
            System.out.println("Consumer processed a batch of " + batch.size()
                    + " (self-paced, never overwhelmed since it only ever asked for " + batchSize + " at a time)");
        }
        System.out.println("Total processed: " + totalProcessed + ", remaining upstream: (source never pushed more than requested)");
    }
}
```

How to run: `java PullBasedBackpressure.java`

Instead of a producer pushing items and the consumer being forced to either keep up or block a full queue, the consumer here explicitly *pulls* a batch of exactly `batchSize` (5) items at a time via `source.request(5)`. The source never sends more than what was explicitly requested — there is no way for it to overwhelm the consumer, because the consumer is entirely in control of how much work enters its own processing loop at any moment. This is the model used by reactive streams (Project Reactor, RxJava) and the Reactive Streams specification's `Subscription.request(n)`: backpressure isn't just "block when full," it's the consumer actively declaring its own capacity up front.

## 6. Walkthrough

Trace `PullBasedBackpressure.main` in order. **First**, a `PullBasedSource` is created holding 1000 available items, and `batchSize` is fixed at 5.

**The `while` loop's first iteration** calls `source.request(5)`. Inside `request`, a loop pulls up to 5 items from the `available` queue via `poll()` (which removes and returns the head, or returns null if empty — here it always succeeds since there are 1000 available) and collects them into `batch`. The source's internal `available` queue shrinks by exactly 5 as a direct result of this call — nothing more was handed out than was explicitly asked for.

**Back in the main loop**, each of the 5 items in `batch` is "processed" (a 20ms sleep stands in for real work), incrementing `totalProcessed`. Only after all 5 are processed does the loop print its status and go back to the top of the `while`, checking `source.hasMore() && totalProcessed < 20`.

**This repeats**: iteration 2 pulls another batch of 5 (`totalProcessed` reaches 10), iteration 3 pulls another 5 (`totalProcessed` reaches 15), iteration 4 pulls a final batch of 5 (`totalProcessed` reaches 20) — at which point the loop condition `totalProcessed < 20` becomes false and the loop exits.

**The key structural point**: at no moment during this entire run did the source ever hand the consumer more than 5 items without being asked again. Contrast this with the Level 2 push model, where the producer sends continuously and the *queue's fixed capacity* is what limits how far ahead it can get — here, there is no queue at all in the traditional sense; the consumer's own `request(n)` calls are the only thing that ever releases work from the source. This is a stronger, more precise form of backpressure: capacity is expressed as "give me exactly this much, when I ask," not "keep sending until a buffer fills up."

```
consumer: request(5) -> source hands over exactly 5 items -> consumer processes all 5 -> request(5) again -> ...
                (source NEVER pushes anything the consumer didn't explicitly pull)
```

## 7. Gotchas & takeaways

> An unbounded queue between a fast producer and a slow consumer is not "safe because it never rejects anything" — it is a slow-motion memory leak that eventually crashes the consumer's process, just later and more unpredictably than an explicit rejection would have.

- Backpressure prevents overload by construction, rather than reacting to it after work has already piled up — it is proactive where [load shedding](0279-throttling-load-shedding.md) is reactive.
- A bounded, blocking queue is the simplest form of backpressure (the producer physically cannot outrun the consumer by more than the queue's capacity) but ties up the producer's thread while blocked, which has its own cost.
- A pull-based model (the consumer explicitly requesting a bounded amount of work) gives the consumer the most precise control over its own load and is the model used by the Reactive Streams specification underlying Project Reactor and RxJava.
- Backpressure needs to propagate end-to-end through a pipeline — a backpressure-aware stage that sits behind a stage with no backpressure support just moves the unbounded-buffering problem one hop upstream instead of solving it.
