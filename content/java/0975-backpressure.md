---
card: java
gi: 975
slug: backpressure
title: Backpressure
---

## 1. What it is

Backpressure is the general strategy of letting a slow consumer signal to a fast producer, "slow down, I can't keep up," rather than letting the producer push data unconditionally and forcing the consumer (or some buffer in between) to deal with the overflow however it can. It's a concept that appears across many layers of computing — TCP's own flow-control window is a form of backpressure at the network layer, an `Executor`'s bounded task queue rejecting new work once full is a form of backpressure at the thread-pool layer, and, most directly relevant here, the [Reactive Streams specification's `Subscription.request(n)`](0974-reactive-streams-spec-flow-api.md) mechanism is backpressure applied specifically to asynchronous data-stream processing. Without any backpressure mechanism, a mismatch between producer and consumer speed has only a few possible outcomes, all bad: an unbounded buffer growing until memory is exhausted, data being silently dropped, or the producer blocking in an uncontrolled, unpredictable way.

## 2. Why & when

Backpressure matters anywhere the rate at which data becomes available is not naturally matched to the rate at which it can be processed — a fast network connection streaming data into a service whose downstream database write is comparatively slow, a UI event stream producing mouse-move events far faster than a listener can meaningfully react to each one, or a batch job reading rows from a source system faster than a rate-limited external API it must call for each row. The three broad strategies for handling this mismatch — buffer (accept everything and queue it, accepting the risk of unbounded memory growth if the mismatch is sustained), drop (discard excess items, accepting data loss to bound memory usage), or signal-and-slow-down (explicit backpressure, having the consumer tell the producer to actually stop or slow producing) — are not equally appropriate in every situation: buffering suits short, bursty mismatches with a bounded, known maximum burst size; dropping suits scenarios where losing some data (an intermediate mouse-move event, a metric sample) is acceptable; and genuine backpressure suits scenarios where every item matters and neither unbounded memory growth nor data loss is acceptable, at the cost of needing the producer itself to be capable of actually pausing or slowing down when asked.

## 3. Core concept

```
WITHOUT backpressure (producer pushes unconditionally):
  Producer: item, item, item, item, item, item, item, ...  (fast)
  Consumer:   process...........................  (slow)
  Result: unbounded buffer growth, OR dropped items, OR producer blocks unpredictably

WITH backpressure (consumer explicitly controls pace):
  Consumer: "I'm ready for 2 more"  -->  Producer sends exactly 2  -->  Consumer processes them
  Consumer: "I'm ready for 2 more"  -->  Producer sends exactly 2  -->  ... (repeat)
  Result: producer's rate is GENUINELY governed by consumer's actual processing speed

Three broad strategies for a producer/consumer speed mismatch:
  1. BUFFER   -- queue excess items; risks unbounded memory growth if sustained
  2. DROP     -- discard excess items; risks data loss, but bounds memory
  3. BACKPRESSURE -- consumer signals producer to slow down; no data loss, no unbounded growth,
                     but requires the producer to be capable of actually pausing
```

Genuine backpressure is distinguished from buffering or dropping by making the *rate itself* — not just what happens to excess data — a negotiated, explicit part of the producer/consumer contract.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three strategies for a producer faster than its consumer: an unbounded buffer growing without limit, items being dropped, and explicit backpressure where the consumer's request governs the producer's actual rate" >
  <text x="110" y="16" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Buffer (unbounded)</text>
  <rect x="20" y="30" width="180" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">queue keeps GROWING</text>

  <text x="320" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Drop</text>
  <rect x="230" y="30" width="180" height="30" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="49" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">excess items DISCARDED</text>

  <text x="530" y="16" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Backpressure</text>
  <rect x="440" y="30" width="180" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">rate genuinely SLOWED</text>

  <text x="320" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only backpressure changes the PRODUCER's actual rate --</text>
  <text x="320" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">buffering and dropping just change what happens to the MISMATCH after the fact</text>
</svg>

*Buffering and dropping cope with a speed mismatch after the fact; backpressure resolves it by actually slowing the producer down.*

## 5. Runnable example

Scenario: simulate a fast data source feeding a slower consumer, demonstrating all three strategies on the identical underlying mismatch — starting with a basic unbounded-buffer approach and observing its growth, then a bounded, dropping alternative, then a genuinely backpressure-respecting version using the `Flow` API's request mechanism.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class BackpressureUnboundedBuffer {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> buffer = new LinkedBlockingQueue<>(); // UNBOUNDED -- no capacity limit

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 10; i++) {
                buffer.offer(i); // never blocks -- unbounded queue always accepts
            }
        });

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 0; i < 10; i++) {
                    Integer item = buffer.take();
                    Thread.sleep(100); // SLOW consumer
                    System.out.println("processed: " + item);
                }
            } catch (InterruptedException ignored) {}
        });

        producer.start();
        Thread.sleep(50); // let producer get ahead
        System.out.println("buffer size after producer got a head start: " + buffer.size());
        consumer.start();
        producer.join();
        consumer.join();
    }
}
```

**How to run:** `java BackpressureUnboundedBuffer.java` (JDK 17+).

Expected output shape (illustrative — the exact buffer size at the print point may vary slightly by timing):
```
buffer size after producer got a head start: 10
processed: 1
processed: 2
...
processed: 10
```

Because `buffer` has no capacity limit, the fast producer finishes submitting all 10 items almost instantly, well before the slow consumer (100ms per item) has processed even one — the buffer's size grows to hold every unprocessed item simultaneously; for a genuinely unbounded, sustained producer/consumer speed mismatch, this pattern would eventually exhaust available memory.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class BackpressureBoundedDropping {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> buffer = new ArrayBlockingQueue<>(3); // BOUNDED capacity of 3

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 10; i++) {
                boolean accepted = buffer.offer(i); // offer() does NOT block -- returns false if full
                if (!accepted) {
                    System.out.println("DROPPED item " + i + " -- buffer full");
                }
            }
        });

        Thread consumer = new Thread(() -> {
            try {
                for (int i = 0; i < 10; i++) {
                    Integer item = buffer.poll(500, TimeUnit.MILLISECONDS);
                    if (item == null) break;
                    Thread.sleep(100);
                    System.out.println("processed: " + item);
                }
            } catch (InterruptedException ignored) {}
        });

        producer.start();
        producer.join(); // let the (fast) producer finish completely first, to demonstrate dropping clearly
        consumer.start();
        consumer.join();
    }
}
```

**How to run:** `java BackpressureBoundedDropping.java` (JDK 17+).

Expected output shape (illustrative):
```
DROPPED item 4 -- buffer full
DROPPED item 5 -- buffer full
DROPPED item 6 -- buffer full
DROPPED item 7 -- buffer full
DROPPED item 8 -- buffer full
DROPPED item 9 -- buffer full
DROPPED item 10 -- buffer full
processed: 1
processed: 2
processed: 3
```

The real-world concern added: bounding the buffer's capacity to 3 and using non-blocking `offer` means the producer never waits, but items beyond the buffer's capacity are silently dropped rather than accumulating without bound — this trades data loss for a hard, predictable memory ceiling, appropriate when losing some items is acceptable but unbounded memory growth is not.

### Level 3 — Advanced

```java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.CountDownLatch;

public class BackpressureGenuine {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        CountDownLatch done = new CountDownLatch(1);

        Subscriber<Integer> subscriber = new Subscriber<>() {
            Subscription subscription;

            public void onSubscribe(Subscription subscription) {
                this.subscription = subscription;
                subscription.request(1);
            }

            public void onNext(Integer item) {
                try { Thread.sleep(100); } catch (InterruptedException ignored) {}
                System.out.println("processed: " + item);
                subscription.request(1); // only ask for more once genuinely ready
            }

            public void onError(Throwable t) { done.countDown(); }
            public void onComplete() { System.out.println("all done, nothing dropped or unbounded"); done.countDown(); }
        };

        publisher.subscribe(subscriber);
        for (int i = 1; i <= 10; i++) {
            publisher.submit(i); // publisher itself can submit fast -- SubmissionPublisher
                                   // buffers internally, but delivery is STILL request-gated
        }
        publisher.close();
        done.await();
    }
}
```

**How to run:** `java BackpressureGenuine.java` (JDK 17+).

Expected output:
```
processed: 1
processed: 2
processed: 3
processed: 4
processed: 5
processed: 6
processed: 7
processed: 8
processed: 9
processed: 10
all done, nothing dropped or unbounded
```

The production-flavored hard case: using the [Reactive Streams `Flow` API](0974-reactive-streams-spec-flow-api.md), every single item submitted by the fast producer is eventually processed, with none dropped, and — critically — `onNext` is never invoked faster than the subscriber's own `request(1)` calls allow, since a well-behaved `Publisher` (which `SubmissionPublisher` is) never delivers more than has been requested; this achieves what neither the unbounded-buffer nor the dropping approach could: zero data loss *and* no risk of unbounded memory growth, because the actual delivery rate is genuinely governed by the consumer's own processing speed, not just buffered or discarded after the fact.

## 6. Walkthrough

Comparing the three examples' handling of the identical underlying "fast producer, slow consumer" scenario, in the order their strategies diverge:

1. In `BackpressureUnboundedBuffer`, the producer's ten `offer` calls all succeed immediately and unconditionally, since the `LinkedBlockingQueue` has no capacity limit — all ten items sit in the buffer simultaneously before the slow consumer has processed even the first one; for this small, bounded example, ten items is harmless, but the same pattern with a sustained, much larger mismatch (millions of items, or an unbounded stream) would grow the buffer without limit, eventually exhausting available heap memory.
2. In `BackpressureBoundedDropping`, the same fast producer instead uses a capacity-limited `ArrayBlockingQueue` of size 3 — once the buffer fills after the first three `offer` calls succeed, every subsequent `offer` call (for items 4 through 10) returns `false` immediately rather than blocking or growing the buffer, and the producer's logic explicitly logs each of these as dropped; memory usage is now bounded and predictable (never more than 3 buffered items), but at the direct cost of losing 7 of the original 10 items entirely.
3. In `BackpressureGenuine`, the fast producer still submits all ten items to `SubmissionPublisher` quickly — but `SubmissionPublisher`'s internal delivery mechanism is itself request-gated: it will buffer submitted-but-not-yet-requested items internally (up to its own configurable buffer capacity), but it will only ever *deliver* an item to the subscriber's `onNext` once the subscriber has actually requested it.
4. Because the subscriber requests exactly one item at a time, and only calls `request(1)` again after its own 100ms simulated processing of the current item has fully completed, `onNext` is invoked at a rate genuinely bounded by the subscriber's actual processing speed — not by however fast the producer happened to submit items.
5. This means all ten items are eventually processed, one every roughly 100ms, with none dropped and no risk of an ever-growing buffer, since the publisher's internal buffering is itself bounded by the specification's requirement to respect outstanding requests rather than deliver unconditionally.
6. `onComplete()` fires only after every submitted item has been delivered and the publisher has been closed — printing `"all done, nothing dropped or unbounded"`, which summarizes the core structural difference: genuine backpressure resolves the producer/consumer speed mismatch by governing the *actual delivery rate* itself, rather than choosing between accepting unbounded growth (buffering) or accepting data loss (dropping) as a consequence of that mismatch.

## 7. Gotchas & takeaways

> **Gotcha:** genuine backpressure requires the producer to actually be capable of pausing or slowing its own rate of production — for some data sources (a live sensor feed, a real-time video stream) this may not be physically possible at all, in which case buffering (with a deliberately chosen, bounded capacity) or dropping (with a deliberately chosen, acceptable loss policy) become the only realistic options, and understanding which of the three strategies is actually appropriate for a given data source's own constraints is as important as knowing how to implement any one of them.

- Backpressure is the strategy of letting a slow consumer explicitly control a fast producer's rate, rather than letting the producer push unconditionally and forcing an unbounded buffer, dropped data, or unpredictable blocking to absorb the mismatch.
- The three broad strategies for a producer/consumer speed mismatch — buffer, drop, or genuine backpressure — trade off memory bound, data loss, and producer-pausing capability differently; choose based on which of these costs is actually acceptable for a given data source.
- Only genuine backpressure changes the producer's actual delivery rate; buffering and dropping both just determine what happens to the mismatch after the fact, without altering how fast the producer is actually allowed to go.
- Java's [Reactive Streams `Flow` API](0974-reactive-streams-spec-flow-api.md) implements genuine backpressure via `Subscription.request(n)`, guaranteeing a well-behaved publisher never delivers more items than have been explicitly requested.
- Genuine backpressure requires the producer to be capable of actually pausing — for data sources that cannot pause (live feeds, real-time streams), buffering or dropping with a deliberately chosen policy may be the only realistic options.
- See [Reactive Streams spec (Flow API)](0974-reactive-streams-spec-flow-api.md) for the concrete Java implementation of the backpressure mechanism explored conceptually here.
