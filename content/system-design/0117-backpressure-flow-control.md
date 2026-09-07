---
card: system-design
gi: 117
slug: backpressure-flow-control
title: Backpressure & flow control
---

## 1. What it is

**Backpressure** is a signal from a slower downstream component (a consumer, a database) back to a faster upstream component (a producer) that says "slow down, I cannot keep up." **Flow control** is the general mechanism that applies this signal — buffering messages, blocking or slowing the producer, or dropping excess messages — so a fast producer does not overwhelm a slower consumer. Without it, an unbounded queue between a fast producer and a slow consumer grows forever, eventually exhausting memory or disk.

## 2. Why & when

Any pipeline where a producer can generate work faster than a consumer can process it needs backpressure, or the unprocessed backlog grows without bound — sensor data arriving faster than it can be written to a database, or a burst of API requests arriving faster than a service can handle them. Recognize the need for backpressure whenever you see an unbounded queue or buffer in a system design: it is a warning sign that under sustained load, memory usage will grow until the system crashes or degrades badly.

## 3. Core concept

- **Bounded buffers:** cap the queue's size; once full, apply one of the strategies below instead of growing forever.
- **Blocking (the producer waits):** the producer's send call blocks until the consumer catches up and makes room — simple, and guarantees no data loss, but slows the producer down to match the consumer's pace.
- **Dropping (shed load):** discard new or old messages once the buffer is full, accepting data loss to keep the system responsive — appropriate for data where losing some samples is acceptable (e.g. high-frequency metrics).
- **Load shedding at the edge:** reject new requests before they even enter the pipeline (e.g. return an HTTP 503) once the system is at capacity, rather than accepting work it cannot possibly finish in time.
- **Rate limiting the producer:** explicitly cap how fast a producer is allowed to send, independent of the buffer's current fullness, to keep the whole pipeline within a sustainable, predictable rate.
- **Reactive Streams' `request(n)` model:** a consumer explicitly tells the producer how many items it is ready to receive next; the producer never sends more than that, making backpressure part of the protocol itself rather than an emergency reaction to a full buffer.

## 4. Diagram

```
Without backpressure:                 With backpressure (bounded buffer + block):

  Producer (fast) ---> [ UNBOUNDED     Producer (fast) ---> [ BOUNDED buffer,
                          buffer,                              capacity=5 ]
                          growing            |  buffer full? producer BLOCKS
                          forever ]          v  until consumer frees a slot
                             |          Consumer (slow) processes at its own pace
                             v
                       Consumer (slow)
                       never catches up -> memory grows unbounded -> crash
```
*Caption: an unbounded buffer between a fast producer and slow consumer grows without limit; a bounded buffer with blocking forces the producer to match the consumer's real pace.*

## 5. Runnable example

**Level 1 — Basic.** An unbounded queue between a fast producer and slow consumer grows continuously.

**Level 2 — Bounded buffer with blocking.** A bounded queue forces the producer to wait once full.

**Level 3 — Load shedding.** A bounded buffer drops new messages once full instead of blocking, keeping the producer's own pace unaffected.

```java
// BackpressureDemo.java
import java.util.concurrent.*;
import java.util.*;

public class BackpressureDemo {

    public static void main(String[] args) throws InterruptedException {
        // Level 1: unbounded queue - producer never has to slow down, backlog just grows.
        Queue<Integer> unboundedQueue = new LinkedList<>();
        for (int i = 1; i <= 10; i++) unboundedQueue.add(i); // producer "fires and forgets", all 10 accepted instantly
        System.out.println("unbounded queue size after fast burst of 10: " + unboundedQueue.size() + " (no limit, keeps growing under sustained load)");

        // Level 2: bounded queue with blocking - producer is forced to wait once the buffer is full.
        BlockingQueue<Integer> boundedQueue = new ArrayBlockingQueue<>(3); // capacity of only 3
        int accepted = 0;
        for (int i = 1; i <= 3; i++) { boundedQueue.offer(i); accepted++; } // fills the buffer to capacity
        boolean fourthAccepted = boundedQueue.offer(4); // buffer is full - offer() returns false instead of blocking forever here
        System.out.println("bounded queue after filling to capacity 3: " + boundedQueue + ", 4th item accepted? " + fourthAccepted);
        System.out.println("-> a real producer using put() instead of offer() would BLOCK here until space frees up");

        boundedQueue.poll(); // consumer processes one item, freeing a slot
        boolean nowAccepted = boundedQueue.offer(4);
        System.out.println("after consumer frees a slot, 4th item accepted? " + nowAccepted + " -> " + boundedQueue);

        // Level 3: load shedding - bounded buffer drops new items instead of blocking the producer.
        Queue<Integer> shedBuffer = new LinkedList<>();
        int capacity = 3;
        int dropped = 0;
        for (int i = 1; i <= 6; i++) {
            if (shedBuffer.size() < capacity) {
                shedBuffer.add(i);
            } else {
                dropped++; // buffer full - shed this message instead of blocking or growing unbounded
            }
        }
        System.out.println("load-shedding buffer after producing 6 items into capacity " + capacity + ": " + shedBuffer);
        System.out.println("dropped (shed) messages: " + dropped + " -> producer never blocked, but data was lost");
    }
}
```

**How to run:** save as `BackpressureDemo.java`, then run `java BackpressureDemo.java`.

## 6. Walkthrough

1. Level 1 adds 10 items to a plain `LinkedList`-backed queue with no size limit; all 10 are accepted instantly, showing there is nothing here to ever slow the producer down, no matter how far behind the consumer falls.
2. Level 2 uses an `ArrayBlockingQueue` capped at 3. The first three `offer` calls succeed and fill it to capacity; the fourth `offer` call returns `false`, since the queue rejects the item rather than growing past its bound.
3. The comment notes that a real producer using the blocking `put()` method (rather than the non-blocking `offer()` used here for a clean demonstration) would pause execution entirely at that point, until the consumer frees space — this is backpressure actually slowing the producer down.
4. `boundedQueue.poll()` removes one item, simulating the consumer processing it and freeing a slot; the next `offer(4)` now succeeds, showing the producer can resume exactly once the consumer has made room.
5. Level 3 takes a different strategy for the same full-buffer situation: instead of blocking, items beyond the buffer's capacity are simply counted as `dropped` and discarded. The final buffer only ever holds 3 items, and the `dropped` count shows exactly how many messages were shed — the producer's own loop never paused, but 3 of the 6 messages were lost, illustrating the direct trade-off between blocking (no loss, but slower producer) and shedding (no slowdown, but lost data).

## 7. Gotchas & takeaways

> Gotcha: blocking backpressure that propagates all the way back through several chained services can turn a slowdown in one downstream component into a slowdown (or apparent hang) in every upstream service feeding it, even ones that have nothing to do with the original bottleneck. Trace where a block will actually propagate to before assuming "the producer just waits" is harmless.

- Backpressure signals a slower consumer's real capacity back to a faster producer, preventing an unbounded backlog from growing until the system runs out of memory.
- Blocking preserves every message but slows the producer to the consumer's pace; dropping (load shedding) keeps the producer's pace but loses data.
- An unbounded queue anywhere in a pipeline is a specific, concrete warning sign to look for when reviewing a system design for this problem.
- Related concepts: [Message queues (point-to-point)](0110-message-queues-point-to-point.md) (the buffering component backpressure protects), [Dead-letter queues & poison messages](0118-dead-letter-queues-poison-messages.md) (a related mechanism for messages that cannot be processed at all, rather than merely too slowly).
