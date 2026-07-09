---
card: java
gi: 598
slug: reactive-streams-flow-api-publisher-subscriber-processor-sub
title: Reactive Streams Flow API (Publisher/Subscriber/Processor/Subscription)
---

## 1. What it is

The Reactive Streams Flow API is a set of four interfaces introduced in Java 9 under `java.util.concurrent.Flow`: `Publisher<T>`, `Subscriber<T>`, `Processor<T,R>`, and `Subscription`. Together they define a standard for asynchronous stream processing with non-blocking backpressure — a protocol where a `Subscriber` controls how much data it can handle, and a `Publisher` respects that limit, preventing the subscriber from being overwhelmed. Java 9's `Flow` API is the JDK's interoperation contract for reactive streams; the actual reactive implementations (RxJava, Project Reactor, Akka Streams) implement these interfaces, and the JDK ships a minimal `SubmissionPublisher` as a reference implementation.

## 2. Why & when

Asynchronous systems face a fundamental problem: a fast producer can overwhelm a slow consumer. Without a backpressure protocol, the consumer either buffers indefinitely (running out of memory) or drops data (losing information). The Reactive Streams specification, developed collaboratively by engineers from Netflix, Pivotal, Lightbend, and others, defines a standard protocol with exactly this problem in mind. Java 9 bakes these four interfaces directly into the JDK so that all reactive libraries can interoperate through a common contract — a `Publisher` from Reactor can feed a `Subscriber` from RxJava without adapters, because both implement `java.util.concurrent.Flow.Publisher`.

## 3. Core concept

```java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;

// Publisher: produces items
SubmissionPublisher<String> publisher = new SubmissionPublisher<>();

// Subscriber: consumes items with backpressure
publisher.subscribe(new Subscriber<>() {
    private Subscription subscription;

    public void onSubscribe(Subscription s) {
        this.subscription = s;
        s.request(1); // request 1 item at a time (backpressure)
    }

    public void onNext(String item) {
        System.out.println("Received: " + item);
        subscription.request(1); // request next after processing
    }

    public void onError(Throwable t) { t.printStackTrace(); }
    public void onComplete() { System.out.println("Done."); }
});

publisher.submit("Hello");
publisher.submit("World");
publisher.close();
```

The protocol has four signals: `onSubscribe` (the handshake — subscriber receives a `Subscription` to control demand), `onNext` (a data item), `onError` (terminal failure), and `onComplete` (terminal success). The `Subscription` object is the backpressure mechanism: a `Subscriber` calls `subscription.request(n)` to signal it is ready for up to `n` more items. The `Publisher` MUST NOT send more items than have been requested.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reactive Streams flow: Publisher → Subscriber with backpressure via Subscription.request(n)">
  <rect x="20" y="10" width="600" height="190" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="130" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="105" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Publisher&lt;T&gt;</text>

  <text x="210" y="50" fill="#8b949e" font-size="10" font-family="monospace">──subscribe(sub)──►</text>

  <rect x="430" y="30" width="140" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="500" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Subscriber&lt;T&gt;</text>

  <text x="500" y="100" fill="#8b949e" font-size="10" font-family="monospace">◄── onSubscribe(s) ──</text>
  <text x="205" y="100" fill="#8b949e" font-size="10" font-family="monospace">─── request(n) ────►</text>

  <rect x="40" y="110" width="80" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="80" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">item 1</text>
  <text x="130" y="132" fill="#8b949e" font-size="10" font-family="monospace">── onNext ──►</text>

  <rect x="455" y="110" width="80" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="495" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">process</text>
  <text x="500" y="155" fill="#8b949e" font-size="10" font-family="monospace">◄── request(1) ──</text>

  <text x="40" y="175" fill="#8b949e" font-size="10" font-family="sans-serif">onComplete() / onError(t) — terminal signals</text>
  <text x="40" y="192" fill="#8b949e" font-size="10" font-family="sans-serif">Backpressure: Subscriber controls demand via Subscription.request(n)</text>
</svg>

The `Subscription` is the key to backpressure: the `Subscriber` calls `request(n)` to pull data, and the `Publisher` must obey that limit.

## 5. Runnable example

Scenario: a news feed publisher that emits headlines to a subscriber, which processes them with simulated latency — starting with a basic one-at-a-time subscriber, extending to a batching subscriber that requests items in chunks, and finally adding a `Processor` that transforms items mid-stream with backpressure-preserving behaviour.

### Level 1 — Basic

```java
// File: FlowBasic.java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;

public class FlowBasic {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<String> pub = new SubmissionPublisher<>();

        pub.subscribe(new Subscriber<>() {
            private Subscription sub;

            public void onSubscribe(Subscription s) {
                this.sub = s;
                s.request(1); // request first item
            }

            public void onNext(String item) {
                System.out.println("News: " + item);
                sub.request(1); // request next after processing
            }

            public void onError(Throwable t) { t.printStackTrace(); }
            public void onComplete() { System.out.println("Feed ended."); }
        });

        pub.submit("Markets rally on earnings report");
        pub.submit("New framework release announced");
        pub.close();

        Thread.sleep(500); // wait for async delivery
    }
}
```

**How to run:** `java FlowBasic.java`

Expected output:
```
News: Markets rally on earnings report
News: New framework release announced
Feed ended.
```

The simplest reactive pipeline: a `SubmissionPublisher` (JDK's built-in `Publisher` implementation) publishes two headlines. The `Subscriber` requests items one at a time, processes each, and requests the next. `pub.close()` signals completion, triggering `onComplete`. The `Thread.sleep` ensures `main` doesn't exit before the async delivery completes.

### Level 2 — Intermediate

```java
// File: FlowBatching.java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;
import java.util.ArrayList;
import java.util.List;

public class FlowBatching {
    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<String> pub = new SubmissionPublisher<>();

        pub.subscribe(new Subscriber<>() {
            private Subscription sub;
            private final int BATCH = 3;
            private final List<String> buffer = new ArrayList<>();

            public void onSubscribe(Subscription s) {
                this.sub = s;
                sub.request(BATCH); // request a batch upfront
            }

            public void onNext(String item) {
                buffer.add(item);
                if (buffer.size() >= BATCH) {
                    System.out.println("Processing batch: " + buffer);
                    buffer.clear();
                    sub.request(BATCH); // request next batch
                }
            }

            public void onError(Throwable t) { t.printStackTrace(); }
            public void onComplete() {
                if (!buffer.isEmpty()) {
                    System.out.println("Processing final batch: " + buffer);
                }
                System.out.println("Feed ended.");
            }
        });

        for (int i = 1; i <= 8; i++) {
            pub.submit("Headline #" + i);
        }
        pub.close();
        Thread.sleep(500);
    }
}
```

**How to run:** `java FlowBatching.java`

Expected output:
```
Processing batch: [Headline #1, Headline #2, Headline #3]
Processing batch: [Headline #4, Headline #5, Headline #6]
Processing final batch: [Headline #7, Headline #8]
Feed ended.
```

The real-world concern added: batching for efficiency. The subscriber requests 3 items at a time instead of 1, buffers them internally, and flushes the batch to processing when the buffer reaches the batch size. This is how reactive consumers optimise for throughput — fewer `request(n)` calls mean less signalling overhead. The `onComplete` handler ensures any remaining partial batch (items 7 and 8, which don't fill a full batch) is still processed.

### Level 3 — Advanced

```java
// File: FlowProcessorDemo.java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.CompletableFuture;

public class FlowProcessorDemo {

    // A Processor transforms items: extends both Publisher and Subscriber
    static class UppercaseProcessor extends SubmissionPublisher<String>
            implements Processor<String, String> {
        
        private Subscription upstream;

        public void onSubscribe(Subscription s) {
            this.upstream = s;
            s.request(Long.MAX_VALUE); // pull all — processor doesn't throttle
        }

        public void onNext(String item) {
            String transformed = item.toUpperCase();
            System.out.println("  [Processor] '" + item + "' → '" + transformed + "'");
            submit(transformed); // publish transformed item downstream
        }

        public void onError(Throwable t) {
            t.printStackTrace();
            closeExceptionally(t);
        }

        public void onComplete() {
            System.out.println("  [Processor] upstream complete");
            close(); // propagate completion downstream
        }
    }

    public static void main(String[] args) throws Exception {
        SubmissionPublisher<String> pub = new SubmissionPublisher<>();

        // Create and subscribe processor in the middle
        UppercaseProcessor processor = new UppercaseProcessor();
        pub.subscribe(processor);         // publisher → processor

        // End subscriber
        processor.subscribe(new Subscriber<>() {
            private Subscription sub;
            public void onSubscribe(Subscription s) {
                this.sub = s;
                s.request(1);
            }
            public void onNext(String item) {
                System.out.println("  [Subscriber] Received: " + item);
                sub.request(1);
            }
            public void onError(Throwable t) { t.printStackTrace(); }
            public void onComplete() { System.out.println("  [Subscriber] Done."); }
        });

        // Publish
        pub.submit("Breaking: market update");
        pub.submit("Weather: sunny skies");
        pub.submit("Sports: local team wins");
        pub.close();

        // Wait for async pipeline to finish
        CompletableFuture<Void> done = new CompletableFuture<>();
        processor.onCompletion(() -> done.complete(null));
        done.get();
    }
}
```

**How to run:** `java FlowProcessorDemo.java`

Expected output:
```
  [Processor] 'Breaking: market update' → 'BREAKING: MARKET UPDATE'
  [Subscriber] Received: BREAKING: MARKET UPDATE
  [Processor] 'Weather: sunny skies' → 'WEATHER: SUNNY SKIES'
  [Subscriber] Received: WEATHER: SUNNY SKIES
  [Processor] 'Sports: local team wins' → 'SPORTS: LOCAL TEAM WINS'
  [Subscriber] Received: SPORTS: LOCAL TEAM WINS
  [Processor] upstream complete
  [Subscriber] Done.
```

The production-flavoured addition: a `Processor<T, R>` (here `UppercaseProcessor`) that sits between the original publisher and the final subscriber, transforming items as they pass through. A `Processor` is both a `Subscriber` (to its upstream) and a `Publisher` (to its downstream), so it can participate in any position in a reactive pipeline — filtering, transforming, aggregating, or fanning out. The `onCompletion` callback and `CompletableFuture` pattern provide a clean way to wait for the asynchronous pipeline to drain, avoiding the fragile `Thread.sleep()` used in the simpler examples.

## 6. Walkthrough

Tracing the Level 3 processor pipeline from `main` to completion:

1. **Setup phase**: `main` creates a `SubmissionPublisher<String> pub`, an `UppercaseProcessor processor`, and an anonymous end `Subscriber`. `pub.subscribe(processor)` registers the processor as the publisher's subscriber. `processor.subscribe(endSubscriber)` registers the end subscriber as the processor's downstream subscriber.

   At this point, the processor has two roles:
   - As a `Subscriber`: it has received an `onSubscribe(upstreamSub)` call from `pub` (via its `onSubscribe` method), giving it an `upstream` `Subscription` with which it called `upstreamSub.request(Long.MAX_VALUE)` — telling the publisher "send everything you have."
   - As a `Publisher`: it has accepted the end subscriber, which in turn called `onSubscribe(downstreamSub)` on the end subscriber; the end subscriber requested 1 item.

2. **First item published**: `pub.submit("Breaking: market update")`. With the processor having requested `Long.MAX_VALUE`, `pub` delivers the item via `processor.onNext("Breaking: market update")`.

   Inside `onNext`:
   - `"Breaking: market update".toUpperCase()` → `"BREAKING: MARKET UPDATE"` — the data is transformed.
   - `super.submit("BREAKING: MARKET UPDATE")` — the processor publishes the transformed item to its own downstream subscribers (the end subscriber).
   - The end subscriber's `onNext("BREAKING: MARKET UPDATE")` is called. It prints the received item and calls `sub.request(1)` to signal readiness for the next.

   State after this step: the end subscriber has consumed 1 item and requested 1 more. The processor has processed 1 item and forwarded it.

3. **Second and third items**: `pub.submit("Weather: sunny skies")` and `pub.submit("Sports: local team wins")` follow the same path — each goes through `processor.onNext` → `toUpperCase()` → `processor.submit(transformed)` → end subscriber `onNext` → print + `request(1)`.

4. **Completion**: `pub.close()` is called after all three items are submitted. The publisher sends `onComplete()` to all its subscribers, including the processor. The processor's `onComplete()` method runs:
   - Prints `"[Processor] upstream complete"`.
   - Calls `super.close()` to propagate completion to the processor's own downstream subscribers.
   - The end subscriber receives `onComplete()` and prints `"[Subscriber] Done."`.

5. **Awaiting drain**: `processor.onCompletion(() -> done.complete(null))` registers a callback that fires when the processor has no more pending items. `done.get()` blocks until that callback fires, ensuring `main` doesn't exit before the pipeline drains. This replaces the fragile `Thread.sleep()` pattern.

```
pub ──subscribe──► Processor ──subscribe──► endSubscriber
                        │
   submit("Breaking") ──► onNext("Breaking")
                        │  → toUpperCase → "BREAKING"
                        │  → submit("BREAKING") ──────────► onNext("BREAKING")
                        │                                     → print + request(1)
   submit("Weather") ──► onNext("Weather")
                        │  → toUpperCase → "WEATHER"
                        │  → submit("WEATHER") ────────────► onNext("WEATHER")
                        │                                     → print + request(1)
   submit("Sports")  ──► onNext("Sports")
                        │  → ... → submit("SPORTS") ───────► onNext("SPORTS")
   close() ────────────► onComplete()
                        │  → close() ───────────────────────► onComplete()
                        ▼                                     ▼
                     Done.                                 Done.
```

## 7. Gotchas & takeaways

> `SubmissionPublisher.submit()` is asynchronous — calling `submit()` does not block and does not guarantee that the item has been delivered before `submit()` returns. If `main` exits immediately after publishing, items may be lost. Always use `close()` (which waits for buffered items to drain) or an explicit synchronisation mechanism like `CompletableFuture` if you need to observe completion in a simple `main` method.

- The `Flow` API is a **specification**, not a full reactive library — `SubmissionPublisher` is a minimal reference implementation. For production systems, use Project Reactor (`Flux`, `Mono`) or RxJava (`Flowable`, `Single`), both of which implement `Flow.Publisher` and provide rich operator sets.
- `Subscription.request(n)` is the backpressure mechanism — a subscriber that never calls `request()` will never receive items. A subscriber that calls `request(Long.MAX_VALUE)` is effectively saying "I have unbounded capacity" (push model), which is appropriate for in-memory processors like `UppercaseProcessor` but dangerous for I/O-bound consumers.
- The Reactive Streams specification rule 2.7 forbids calling `onNext` after `onComplete` or `onError` — violating this rule causes undefined behaviour. The `SubmissionPublisher` enforces this by throwing `IllegalStateException` if you `submit()` after `close()`.
- `Processor<T, R>` combines both `Subscriber<T>` and `Publisher<R>` — it must honour the subscriber contract with its upstream and the publisher contract with its downstream, including correct backpressure propagation. A processor that requests `Long.MAX_VALUE` from upstream but has a slow downstream may buffer unboundedly, defeating the purpose of backpressure.
- The `Flow` interfaces are in `java.util.concurrent`, not `java.util.stream` — reactive streams are about asynchronous push with backpressure, which is fundamentally a concurrency concern, not a data-in-collections concern. 