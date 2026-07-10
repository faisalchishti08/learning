---
card: java
gi: 974
slug: reactive-streams-spec-flow-api
title: Reactive Streams spec (Flow API)
---

## 1. What it is

The Reactive Streams specification is a small, standardized set of four interfaces — `Publisher`, `Subscriber`, `Subscription`, and `Processor` — defining a common protocol for asynchronous, non-blocking data processing with built-in [backpressure](0975-backpressure.md): a `Publisher` produces items, a `Subscriber` consumes them, and a `Subscription` (obtained when a `Subscriber` subscribes to a `Publisher`) is the object the `Subscriber` uses to explicitly request only as many items as it's currently ready to handle, rather than being overwhelmed by items arriving faster than it can process them. Java 9 incorporated this exact specification directly into the JDK as `java.util.concurrent.Flow`, containing the identical four interfaces (as static nested interfaces of `Flow`), specifically so that different reactive libraries (Project Reactor, RxJava, Akka Streams) could all interoperate through one shared, standard vocabulary rather than each defining its own incompatible publisher/subscriber types.

## 2. Why & when

This specification exists to solve a fundamental problem with naive asynchronous data production: without any coordination, a fast producer (a network stream reading data faster than the network itself is the bottleneck, a database returning rows faster than a slow downstream consumer can process them) can overwhelm a slow consumer, forcing an unbounded buffer to grow without limit (risking an eventual `OutOfMemoryError`) or forcing the producer to simply drop data it has nowhere to put. The Reactive Streams protocol solves this by making the *consumer* the one who controls the pace: a `Subscriber` calls `Subscription.request(n)` to explicitly say "I'm ready for up to `n` more items," and a well-behaved `Publisher` is contractually obligated never to deliver more items than have been requested — this reversal (consumer pulls, rather than producer pushes unconditionally) is exactly what backpressure means in this context, and it's the specification's single most important guarantee. You reach for the `Flow` API (or a full-featured reactive library built on the same interfaces, like Project Reactor) specifically when building systems that need to process potentially unbounded, asynchronous data streams — I/O-bound services, streaming APIs, or any pipeline where a slow consumer must never be silently flooded by a fast producer.

## 3. Core concept

```
Flow.Publisher<T>     -- produces items of type T
    subscribe(Flow.Subscriber<? super T> subscriber)

Flow.Subscriber<T>    -- consumes items of type T
    onSubscribe(Flow.Subscription subscription)   -- called first, gives the Subscriber control
    onNext(T item)                                 -- called for each item, but ONLY as many
                                                    -- as were explicitly requested
    onError(Throwable t)                           -- called if the Publisher fails
    onComplete()                                    -- called when the Publisher finishes normally

Flow.Subscription     -- the Subscriber's remote control over the Publisher's pace
    request(long n)    -- "I'm ready for up to n more items" -- THIS is backpressure
    cancel()           -- "stop sending me items entirely"

Sequence:
  subscribe() -> onSubscribe(subscription) -> subscriber calls subscription.request(n)
  -> Publisher sends AT MOST n items via onNext() -> subscriber may request more, or
  -> onComplete() / onError() when the stream ends
```

The `Subscription.request(n)` call is the entire mechanism: a `Publisher` is never allowed to push more items than have been explicitly requested, which is what makes this protocol genuinely backpressure-aware rather than a simple, unconditional push-based callback system.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Publisher and Subscriber exchanging an onSubscribe call, a request(n) call from the Subscriber, and a bounded sequence of onNext calls from the Publisher, never exceeding the requested count" >
  <rect x="20" y="20" width="180" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="39" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Publisher</text>

  <rect x="440" y="20" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="39" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Subscriber</text>

  <line x1="200" y1="35" x2="440" y2="35" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">onSubscribe(subscription)</text>

  <line x1="440" y1="70" x2="200" y2="70" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="320" y="65" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">subscription.request(3) -- "send me 3"</text>

  <line x1="200" y1="105" x2="440" y2="105" stroke="#6db33f" marker-end="url(#a)"/>
  <text x="320" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">onNext(item1)</text>
  <line x1="200" y1="125" x2="440" y2="125" stroke="#6db33f" marker-end="url(#a)"/>
  <text x="320" y="120" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">onNext(item2)</text>
  <line x1="200" y1="145" x2="440" y2="145" stroke="#6db33f" marker-end="url(#a)"/>
  <text x="320" y="140" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">onNext(item3) -- STOPS here, exactly 3 requested</text>

  <line x1="200" y1="175" x2="440" y2="175" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(waits for another request(n) before sending more)</text>
</svg>

*The Publisher delivers exactly as many items as requested, never more, waiting for the Subscriber's next request before continuing.*

## 5. Runnable example

Scenario: build a small counting publisher and a backpressure-respecting subscriber from scratch, evolving from a basic single-request exchange, to a realistic incremental-request pattern processing a bounded stream, to a more advanced case demonstrating what happens when a subscriber deliberately requests slower than the publisher could otherwise produce.

### Level 1 — Basic

```java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;

public class FlowBasic {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();

        Subscriber<Integer> subscriber = new Subscriber<>() {
            Subscription subscription;

            public void onSubscribe(Subscription subscription) {
                this.subscription = subscription;
                subscription.request(1); // request just ONE item to start
            }

            public void onNext(Integer item) {
                System.out.println("received: " + item);
                subscription.request(1); // request the NEXT one, one at a time
            }

            public void onError(Throwable throwable) {
                System.out.println("error: " + throwable);
            }

            public void onComplete() {
                System.out.println("done");
            }
        };

        publisher.subscribe(subscriber);
        publisher.submit(1);
        publisher.submit(2);
        publisher.submit(3);
        publisher.close();

        Thread.sleep(200); // let the async delivery finish before the program exits
    }
}
```

**How to run:** `java FlowBasic.java` (JDK 17+; `Flow` and `SubmissionPublisher` have been part of the JDK since Java 9).

Expected output:
```
received: 1
received: 2
received: 3
done
```

The subscriber requests exactly one item at a time (`request(1)` in both `onSubscribe` and again after each `onNext`), so the publisher only ever delivers one item before waiting for the next explicit request — this is backpressure in its simplest form: the subscriber, not the publisher, controls the pace of delivery.

### Level 2 — Intermediate

```java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.CountDownLatch;

public class FlowBatchedRequests {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        CountDownLatch done = new CountDownLatch(1);

        Subscriber<Integer> subscriber = new Subscriber<>() {
            Subscription subscription;
            int received = 0;

            public void onSubscribe(Subscription subscription) {
                this.subscription = subscription;
                subscription.request(3); // request a BATCH of 3 upfront
            }

            public void onNext(Integer item) {
                received++;
                System.out.println("received: " + item + " (count=" + received + ")");
                if (received % 3 == 0) {
                    subscription.request(3); // request the NEXT batch of 3
                }
            }

            public void onError(Throwable throwable) { done.countDown(); }
            public void onComplete() { System.out.println("done"); done.countDown(); }
        };

        publisher.subscribe(subscriber);
        for (int i = 1; i <= 6; i++) publisher.submit(i);
        publisher.close();

        done.await();
    }
}
```

**How to run:** `java FlowBatchedRequests.java` (JDK 17+).

Expected output:
```
received: 1 (count=1)
received: 2 (count=2)
received: 3 (count=3)
received: 4 (count=4)
received: 5 (count=5)
received: 6 (count=6)
done
```

The real-world concern added: requesting items in batches of 3 rather than one at a time reduces the overhead of constantly calling `request` after every single item, a realistic tuning tradeoff for a subscriber that can comfortably process a small batch at once — the underlying backpressure guarantee is unchanged: the publisher never delivers more than has been cumulatively requested at any point.

### Level 3 — Advanced

```java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.CountDownLatch;

public class FlowSlowConsumer {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        CountDownLatch done = new CountDownLatch(1);

        Subscriber<Integer> slowSubscriber = new Subscriber<>() {
            Subscription subscription;

            public void onSubscribe(Subscription subscription) {
                this.subscription = subscription;
                subscription.request(1);
            }

            public void onNext(Integer item) {
                try {
                    Thread.sleep(200); // SIMULATE slow processing per item
                } catch (InterruptedException ignored) {}
                System.out.println("processed: " + item + " at " + System.currentTimeMillis());
                subscription.request(1); // only request the NEXT item once this one is fully processed
            }

            public void onError(Throwable throwable) { done.countDown(); }
            public void onComplete() { System.out.println("done"); done.countDown(); }
        };

        publisher.subscribe(slowSubscriber);
        long start = System.currentTimeMillis();
        for (int i = 1; i <= 5; i++) {
            publisher.submit(i); // the publisher can submit FAST -- backpressure handles the mismatch
        }
        publisher.close();
        System.out.println("all 5 submitted at " + System.currentTimeMillis() + " (start was " + start + ")");

        done.await();
    }
}
```

**How to run:** `java FlowSlowConsumer.java` (JDK 17+).

Expected output shape (illustrative — exact timestamps vary, but note submission happens almost instantly while processing is clearly paced 200ms apart):
```
all 5 submitted at 1730000000050 (start was 1730000000010)
processed: 1 at 1730000000260
processed: 2 at 1730000000460
processed: 3 at 1730000000660
processed: 4 at 1730000000860
processed: 5 at 1730000001060
done
```

The production-flavored hard case: `publisher.submit(...)` for all five items completes almost instantly (the publisher itself is fast), but `onNext`'s deliberately slow 200ms simulated processing means the subscriber only requests — and therefore only receives — the next item once it has genuinely finished with the current one; `SubmissionPublisher` internally buffers submitted items that haven't yet been requested, but the subscriber's own explicit pacing (`request(1)` only after finishing each item) is what prevents `onNext` from ever being invoked faster than the subscriber can actually keep up, which is exactly the backpressure guarantee this entire protocol exists to provide.

## 6. Walkthrough

Tracing the interaction between `publisher` and `slowSubscriber` end to end in `FlowSlowConsumer.main`:

1. `publisher.subscribe(slowSubscriber)` triggers `onSubscribe(subscription)` on the subscriber — inside this callback, `subscription.request(1)` is called immediately, telling the publisher "I am ready to receive exactly one item right now."
2. The main thread then rapidly calls `publisher.submit(1)` through `publisher.submit(5)` in a tight loop, followed by `publisher.close()` — all of this happens almost instantaneously, since `submit` just hands items to the publisher's internal buffering and delivery machinery; it does not block waiting for the subscriber to actually process anything.
3. Because exactly one item was requested so far, the publisher delivers only the first submitted item, `1`, via `onNext(1)` — the remaining submitted items (`2` through `5`) are held internally by the publisher, not yet delivered, since no further request has been made yet.
4. Inside `onNext(1)`, the subscriber deliberately sleeps for 200ms (simulating real processing work), then prints `"processed: 1 at ..."`, and only *after* this simulated work completes does it call `subscription.request(1)` again, asking for exactly one more item.
5. Only upon receiving this second `request(1)` call does the publisher deliver the next buffered item, `2`, via a fresh `onNext(2)` call — which again sleeps 200ms, prints, and requests once more, repeating this exact cycle for items `3`, `4`, and `5` in turn.
6. Because each `onNext` call must fully complete (including its 200ms simulated delay) before the next `request(1)` is made, and each subsequent item is only delivered after that request arrives, the printed "processed" timestamps end up spaced roughly 200ms apart — even though all five items were submitted by the publisher almost instantly at the very start — demonstrating that the subscriber's own explicit, one-at-a-time pacing is what ultimately governs the actual delivery rate, exactly the backpressure guarantee the Reactive Streams specification is designed to provide.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `Subscription.request(n)` at all (for instance, inside `onSubscribe`) means the subscriber will never receive any items — a `Publisher` conforming to the specification is contractually forbidden from delivering anything before it has been explicitly requested, so a subscriber that never requests silently receives nothing, with no error or warning of any kind; always ensure at least an initial `request` call happens somewhere, typically in `onSubscribe` itself.

- The Reactive Streams specification defines four interfaces — `Publisher`, `Subscriber`, `Subscription`, `Processor` — standardizing asynchronous, non-blocking data processing with built-in backpressure, incorporated into the JDK since Java 9 as `java.util.concurrent.Flow`.
- Backpressure works through `Subscription.request(n)`: the subscriber explicitly controls how many items it's ready for, and a well-behaved publisher is contractually forbidden from delivering more than has been requested.
- `onSubscribe` is always called first (giving the subscriber its `Subscription`), followed by zero or more `onNext` calls (bounded by cumulative requests), ending in either `onComplete` (normal completion) or `onError` (failure).
- A subscriber that never calls `request` receives no items at all, with no error — this is a common, silent mistake worth checking for first if a subscriber appears to receive nothing.
- Batching requests (requesting several items at once rather than one at a time) reduces request-call overhead while preserving the same fundamental backpressure guarantee.
- See [backpressure](0975-backpressure.md) for a deeper, more general look at the concept this specification's `request(n)` mechanism directly implements.
