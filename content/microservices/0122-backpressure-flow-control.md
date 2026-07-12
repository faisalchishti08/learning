---
card: microservices
gi: 122
slug: backpressure-flow-control
title: "Backpressure & flow control"
---

## 1. What it is

Backpressure is a signal, flowing backward from a slower consumer to a faster producer, that says "slow down, I can't keep up" — and flow control is the mechanism that acts on that signal, whether by the producer throttling itself, the broker buffering messages up to a limit, or the system rejecting new work once capacity is exhausted. Without it, a fast producer and a slow consumer combine to grow an unbounded backlog until something (usually memory) runs out.

## 2. Why & when

An asynchronous system decouples producer and consumer in time exactly as [the asynchronous messaging model](0111-asynchronous-messaging-model.md) intends, but that decoupling has a cost: if nothing limits how far ahead of the consumer the producer is allowed to get, a burst of production (or a consumer slowdown) grows the backlog without bound, consuming ever more memory or disk on the broker until it, or the producer, crashes. Backpressure exists to convert that unbounded growth into a bounded, controlled response — either the producer waits, the broker rejects excess messages, or older/less important messages are dropped, chosen deliberately rather than accidentally by whatever runs out of resources first.

Design explicit backpressure into any pipeline where the production rate can plausibly and sustainedly exceed the consumption rate — this includes almost any real event-driven pipeline under load, not just obviously bursty ones. See also [backpressure in synchronous calls](0084-backpressure-in-synchronous-calls.md) for the related but distinct problem in request/response paths.

## 3. Core concept

A bounded buffer between producer and consumer is the simplest backpressure mechanism: once it fills up, the producer is forced to either block (wait for room), drop the new message, or receive an explicit rejection it can react to — any of these is preferable to an unbounded buffer that grows until the process runs out of memory.

```java
// bounded queue: capacity 100 -- forces a decision once full, instead of growing forever
BlockingQueue<Message> buffer = new ArrayBlockingQueue<>(100);

// producer's choice when full: block (backpressure applied), or use offer() to fail fast instead
buffer.put(message);          // BLOCKS the producer until the consumer makes room
boolean accepted = buffer.offer(message); // or: return false immediately if full, producer decides what to do
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unbounded buffer grows without limit as a fast producer outpaces a slow consumer; a bounded buffer applies backpressure once full, forcing the producer to slow down, drop, or reject" >
  <text x="150" y="25" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Unbounded (bad)</text>
  <rect x="30" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <rect x="30" y="40" width="240" height="30" fill="#79c0ff" opacity="0.35"/>
  <text x="150" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">grows forever...</text>
  <text x="150" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; out of memory eventually</text>

  <text x="480" y="25" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Bounded (backpressure)</text>
  <rect x="360" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="360" y="40" width="240" height="30" fill="#6db33f" opacity="0.35"/>
  <text x="480" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">FULL -- capacity 100</text>
  <text x="480" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">producer blocks, drops, or is rejected</text>

  <rect x="30" y="130" width="580" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="320" y="155" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">A bound turns an accidental crash into a deliberate, chosen response</text>
</svg>

Bounding the buffer converts an eventual, uncontrolled failure into an explicit, handled decision point.

## 5. Runnable example

Scenario: a producer/consumer pipeline that starts unbounded and demonstrates unchecked memory growth under a slow consumer, then bounds the buffer so the producer blocks (applies backpressure) once full, and finally adds an explicit "drop or reject" policy so the producer can choose not to block at all.

### Level 1 — Basic

```java
// File: UnboundedGrowth.java -- a fast producer, a slow consumer, NO limit: the queue just grows.
import java.util.concurrent.*;

public class UnboundedGrowth {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> buffer = new LinkedBlockingQueue<>(); // UNBOUNDED -- no capacity argument
        ExecutorService consumerThread = Executors.newSingleThreadExecutor();
        consumerThread.submit(() -> {
            try {
                while (true) { buffer.take(); Thread.sleep(20); } // slow consumer: 1 item / 20ms
            } catch (InterruptedException ignored) { }
        });

        for (int i = 0; i < 200; i++) {
            buffer.put(i); // fast producer: essentially instant, no throttling
        }
        System.out.println("Producer finished putting 200 items almost instantly.");
        System.out.println("Buffer size right after producer finished: " + buffer.size() + " (most items still unconsumed, sitting in memory)");
        consumerThread.shutdownNow();
    }
}
```

**How to run:** `javac UnboundedGrowth.java && java UnboundedGrowth` (JDK 17+).

The producer floods 200 items into the queue almost instantly while the consumer can only drain roughly one every 20ms, so the buffer size printed right after is still close to 200 — with no limit, that gap grows without bound the longer this imbalance continues, which at real scale becomes an out-of-memory crash.

### Level 2 — Intermediate

```java
// File: BoundedBackpressure.java -- a bounded buffer forces the producer to BLOCK once full.
import java.util.concurrent.*;

public class BoundedBackpressure {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> buffer = new ArrayBlockingQueue<>(10); // BOUNDED: capacity 10
        ExecutorService consumerThread = Executors.newSingleThreadExecutor();
        consumerThread.submit(() -> {
            try {
                while (true) { buffer.take(); Thread.sleep(20); }
            } catch (InterruptedException ignored) { }
        });

        long start = System.currentTimeMillis();
        for (int i = 0; i < 50; i++) {
            buffer.put(i); // BLOCKS once the buffer hits capacity 10 -- backpressure applied to the producer itself
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Producer took " + elapsed + "ms to put 50 items (forced to slow down to roughly the consumer's pace)");
        System.out.println("Buffer never exceeded capacity 10, regardless of producer speed.");
        consumerThread.shutdownNow();
    }
}
```

**How to run:** `javac BoundedBackpressure.java && java BoundedBackpressure` (JDK 17+).

Expected output (elapsed time approximate): `Producer took ~800ms to put 50 items...` — because `ArrayBlockingQueue.put` blocks whenever the queue is at capacity, the producer is forced to slow down to roughly match the consumer's 20ms-per-item pace instead of racing ahead unchecked.

### Level 3 — Advanced

```java
// File: DropOrRejectPolicy.java -- gives the producer an explicit CHOICE instead of blocking:
// try to enqueue, and if full, apply a deliberate drop-oldest policy instead of stalling.
import java.util.concurrent.*;

public class DropOrRejectPolicy {
    static class BoundedDropOldestBuffer {
        private final ArrayBlockingQueue<Integer> queue;
        private int droppedCount = 0;
        BoundedDropOldestBuffer(int capacity) { queue = new ArrayBlockingQueue<>(capacity); }

        void offerOrDropOldest(int item) {
            if (!queue.offer(item)) { // offer() never blocks -- returns false immediately if full
                queue.poll(); // make room by dropping the OLDEST item (a deliberate choice, not a crash)
                queue.offer(item); // now this succeeds
                droppedCount++;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BoundedDropOldestBuffer buffer = new BoundedDropOldestBuffer(5);
        ExecutorService consumerThread = Executors.newSingleThreadExecutor();
        // consumer is DELIBERATELY slower than the producer, to force the drop policy to trigger
        consumerThread.submit(() -> {
            try {
                while (true) {
                    Integer item = buffer.queue.poll(50, TimeUnit.MILLISECONDS);
                    if (item != null) System.out.println("  [consumer] processed: " + item);
                    Thread.sleep(30);
                }
            } catch (InterruptedException ignored) { }
        });

        for (int i = 0; i < 20; i++) {
            buffer.offerOrDropOldest(i); // NEVER blocks the producer, unlike Level 2
        }
        Thread.sleep(300); // let the consumer drain what's left
        System.out.println("Producer never blocked. Items dropped due to full buffer: " + buffer.droppedCount);
        consumerThread.shutdownNow();
    }
}
```

**How to run:** `javac DropOrRejectPolicy.java && java DropOrRejectPolicy` (JDK 17+).

Expected output (exact counts vary with timing, but `droppedCount` will be greater than 0):
```
  [consumer] processed: 0
  [consumer] processed: 1
  ...
Producer never blocked. Items dropped due to full buffer: 12
```

## 6. Walkthrough

1. **Level 1** — `buffer` is an unbounded `LinkedBlockingQueue`, so `buffer.put(i)` in the producer loop never has any reason to wait; it fires all 200 items into the queue in a tight, essentially instant loop while the consumer, sleeping 20ms between each `take()`, can barely make a dent — the printed `buffer.size()` right after the loop shows nearly all 200 items still sitting unconsumed in memory.
2. **Level 2, the capacity limit** — `buffer` is now an `ArrayBlockingQueue<>(10)`; internally, `put` on a full `ArrayBlockingQueue` blocks the calling thread until `take()` (called by the consumer) frees a slot.
3. **Level 2, backpressure in action** — because the producer's loop calls `put` fifty times but the queue can only ever hold 10 unconsumed items at once, the producer's ninth or tenth call onward starts blocking, waiting for the consumer's `Thread.sleep(20)`-paced draining to make room — the producer's *effective* speed is now capped by the consumer's speed, which is exactly what backpressure means.
4. **Level 2, the measured effect** — the elapsed time for fifty `put` calls (roughly 800ms) is far closer to fifty consumer-paced 20ms cycles than to an unthrottled loop, and `buffer`'s size never exceeds capacity 10 at any point, no matter how fast the producer would otherwise run.
5. **Level 3, choosing not to block** — `offerOrDropOldest` uses `queue.offer(item)`, which returns `false` immediately instead of blocking when the queue is full; on that `false`, it explicitly calls `queue.poll()` to evict the single oldest item, then retries the `offer`, which now succeeds because a slot was freed.
6. **Level 3, the producer's experience** — across all twenty calls to `offerOrDropOldest`, the producer's loop never pauses waiting for the consumer, unlike Level 2 — it always returns essentially instantly, at the cost of some items being deliberately discarded rather than delivered.
7. **Level 3, verifying the trade-off** — `droppedCount` is incremented every time the buffer was full at offer time, and the final printed value (a positive number in the sample run) is direct evidence that the drop-oldest policy activated repeatedly under sustained producer/consumer speed mismatch, converting what would have been either unbounded growth (Level 1) or producer stalling (Level 2) into bounded memory usage plus a controlled, visible data-loss trade-off instead.

## 7. Gotchas & takeaways

> **Gotcha:** "backpressure" is sometimes assumed to always mean "the producer blocks and waits," but blocking is only one policy among several (block, drop-oldest, drop-newest, reject-with-error) — picking the wrong one for a given workload can be worse than having no backpressure at all: blocking a producer that itself has upstream callers waiting on it can propagate the slowdown into a [cascading failure](0099-cascading-failures-from-synchronous-coupling.md), while silently dropping messages that must not be lost trades a memory problem for a correctness problem.

- Backpressure is the backward signal from a slow consumer that a fast producer needs to slow down; flow control is what acts on that signal.
- A bounded buffer is the foundational mechanism: it converts unbounded, uncontrolled memory growth into an explicit decision point once capacity is reached.
- Blocking the producer (`put`) is one valid policy, but not the only one — non-blocking alternatives (`offer` plus a drop or reject policy) trade guaranteed delivery for a producer that is never stalled.
- The right policy depends on whether losing a message is acceptable for that specific data: order events probably should block or be durably queued; a live metrics stream can often tolerate dropping stale points.
- Blocking backpressure can itself propagate backward through a chain of synchronous callers if the producer has its own upstream callers waiting on it — the same [cascading failure](0099-cascading-failures-from-synchronous-coupling.md) risk that motivated asynchronous messaging in the first place can resurface if backpressure isn't designed for deliberately.
