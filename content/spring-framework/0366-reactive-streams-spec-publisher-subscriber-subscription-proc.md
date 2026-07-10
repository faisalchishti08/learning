---
card: spring-framework
gi: 366
slug: reactive-streams-spec-publisher-subscriber-subscription-proc
title: "Reactive Streams spec (Publisher/Subscriber/Subscription/Processor)"
---

## 1. What it is

Reactive Streams is a language-agnostic specification (part of the JDK itself since Java 9, as `java.util.concurrent.Flow`) defining four core interfaces — `Publisher`, `Subscriber`, `Subscription`, `Processor` — that establish a standard contract for asynchronous stream processing with built-in backpressure. Project Reactor's `Mono`/`Flux` (and other reactive libraries like RxJava) all implement this same underlying specification, which is *why* they interoperate: any Reactive-Streams-compliant `Publisher` can feed any Reactive-Streams-compliant `Subscriber`, regardless of which library produced or consumes it.

```java
public interface Publisher<T> {
    void subscribe(Subscriber<? super T> subscriber);
}

public interface Subscriber<T> {
    void onSubscribe(Subscription subscription);
    void onNext(T item);
    void onError(Throwable throwable);
    void onComplete();
}

public interface Subscription {
    void request(long n);
    void cancel();
}
```

## 2. Why & when

Before Reactive Streams, every reactive library (RxJava, Akka Streams, Reactor) had its own incompatible abstractions — code written against one library's `Observable` couldn't directly interoperate with another's stream type without manual adapter code. Reactive Streams standardized the *contract* (not a specific implementation), so libraries built against it are automatically interoperable at their boundaries.

You rarely implement these four interfaces directly — `Mono`/`Flux` already implement `Publisher`, and Reactor's operators handle `Subscriber`/`Subscription` internally. Understanding the specification matters when:

- Debugging genuinely low-level reactive issues (why is backpressure not working as expected, what does "request(n)" actually mean) — the mental model only makes full sense once you've seen these interfaces directly.
- Integrating with a reactive library other than Reactor (RxJava, Akka Streams) — knowing they share this common contract explains why bridging between them (`Flux.from(rxJavaObservable)`) is straightforward.
- Understanding *why* `Mono`/`Flux` behave the way they do (laziness, backpressure, cancellation) — these behaviors are direct consequences of the underlying specification's rules, not arbitrary Reactor design choices.

## 3. Core concept

```
The four core interfaces and their relationship:

  Publisher<T>       — a source of potentially unbounded T values
      .subscribe(Subscriber<T> s)

  Subscriber<T>       — consumes values, notified of lifecycle events
      onSubscribe(Subscription)  <- called FIRST, before any data
      onNext(T)                   <- called for EACH emitted value
      onError(Throwable)          <- called on failure (TERMINAL — no further calls after)
      onComplete()                <- called on success (TERMINAL — no further calls after)

  Subscription        — the CONTROL CHANNEL between Publisher and Subscriber
      request(long n)   <- Subscriber tells Publisher "I can handle n MORE items"
      cancel()          <- Subscriber tells Publisher "stop sending, I'm done"

  Processor<T,R>       — BOTH a Subscriber<T> AND a Publisher<R>
      (a bridge/transformation stage — Mono/Flux operators are conceptually
       built from chains of these, though Reactor abstracts this away)

The interaction sequence (the SPEC's defined protocol):

  1. subscriber.subscribe(publisher)  [or publisher.subscribe(subscriber)]
  2. publisher calls subscriber.onSubscribe(subscription)
  3. subscriber calls subscription.request(n)   <- THIS is what starts data flowing
  4. publisher calls subscriber.onNext(item) — AT MOST n times, never more than requested
  5. eventually: onComplete() OR onError(), never both, never more than once
```

This `request(n)` mechanism is the entire foundation of **backpressure** (explored fully in the next card): a subscriber controls the *rate* of data flow by explicitly requesting only as much as it can currently handle.

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Reactive Streams protocol sequence</text>

  <rect x="20" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="80" text-anchor="middle" fill="#6db33f" font-size="11">Publisher</text>

  <rect x="540" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="630" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">Subscriber</text>

  <line x1="200" y1="70" x2="540" y2="70" stroke="#8b949e" marker-end="url(#a42)"/>
  <text x="370" y="63" text-anchor="middle" fill="#8b949e" font-size="9">1. onSubscribe(subscription)</text>

  <line x1="540" y1="100" x2="200" y2="100" stroke="#6db33f" marker-end="url(#a42)"/>
  <text x="370" y="115" text-anchor="middle" fill="#6db33f" font-size="9">2. subscription.request(n)</text>

  <line x1="200" y1="140" x2="540" y2="140" stroke="#8b949e" marker-end="url(#a42)"/>
  <text x="370" y="133" text-anchor="middle" fill="#8b949e" font-size="9">3. onNext(item) × up to n</text>

  <line x1="200" y1="175" x2="540" y2="175" stroke="#8b949e" marker-end="url(#a42)"/>
  <text x="370" y="168" text-anchor="middle" fill="#8b949e" font-size="9">4. onComplete() or onError(ex)</text>

  <defs>
    <marker id="a42" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The subscriber must explicitly request data via the `Subscription` before the publisher emits anything — this is backpressure by design.*

## 5. Runnable example

### Level 1 — Basic

Implementing the raw `Flow` interfaces directly (Java's built-in Reactive Streams types) to see the protocol with no library abstraction hiding it:

```java
// RawReactiveStreamsDemo.java
import java.util.List;
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;

public class RawReactiveStreamsDemo {

    static class LoggingSubscriber implements Subscriber<String> {
        private Subscription subscription;

        @Override
        public void onSubscribe(Subscription subscription) {
            this.subscription = subscription;
            System.out.println("onSubscribe: requesting 2 items");
            subscription.request(2);   // explicitly ask for 2 items to start
        }

        @Override
        public void onNext(String item) {
            System.out.println("onNext: " + item);
            subscription.request(1);   // ask for ONE more after processing each
        }

        @Override
        public void onError(Throwable throwable) {
            System.out.println("onError: " + throwable.getMessage());
        }

        @Override
        public void onComplete() {
            System.out.println("onComplete");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<String> publisher = new SubmissionPublisher<>();
        publisher.subscribe(new LoggingSubscriber());

        for (String product : List.of("Drill", "Hammer", "Nail")) {
            publisher.submit(product);
        }
        publisher.close();

        Thread.sleep(200);   // give the async delivery time to complete before main() exits
    }
}
```

**How to run:**
```bash
java RawReactiveStreamsDemo.java
# onSubscribe: requesting 2 items
# onNext: Drill
# onNext: Hammer
# onNext: Nail
# onComplete
```

`SubmissionPublisher` (JDK's built-in `Publisher` implementation) and the hand-written `LoggingSubscriber` communicate entirely through the four-method contract — `onSubscribe` fires first, giving the subscriber a `Subscription` it uses to `request(...)` items explicitly, and each `onNext` call triggers another `request(1)` to keep the flow going one item at a time.

### Level 2 — Intermediate

Demonstrating the request-count contract strictly — a subscriber that requests fewer items than the publisher has, showing the publisher genuinely waits rather than emitting unrequested items:

```java
// StrictRequestDemo.java
import java.util.concurrent.Flow.*;
import java.util.concurrent.SubmissionPublisher;

public class StrictRequestDemo {

    static class SlowSubscriber implements Subscriber<Integer> {
        private Subscription subscription;
        private int received = 0;

        @Override
        public void onSubscribe(Subscription subscription) {
            this.subscription = subscription;
            System.out.println("Requesting only 1 item initially");
            subscription.request(1);   // deliberately request just ONE, even though more are coming
        }

        @Override
        public void onNext(Integer item) {
            received++;
            System.out.println("Received: " + item + " (total so far: " + received + ")");
            if (received < 3) {
                System.out.println("  -> requesting 1 more");
                subscription.request(1);
            } else {
                System.out.println("  -> cancelling, no more needed");
                subscription.cancel();   // stop early, demonstrating cancel()
            }
        }

        @Override public void onError(Throwable t) { System.out.println("onError: " + t); }
        @Override public void onComplete() { System.out.println("onComplete"); }
    }

    public static void main(String[] args) throws InterruptedException {
        SubmissionPublisher<Integer> publisher = new SubmissionPublisher<>();
        publisher.subscribe(new SlowSubscriber());

        for (int i = 1; i <= 10; i++) {
            System.out.println("Publisher: submitting " + i);
            publisher.submit(i);
            Thread.sleep(20);   // small delay so the interleaved logging is readable
        }
        publisher.close();
        Thread.sleep(200);
    }
}
```

**How to run:**
```bash
java StrictRequestDemo.java
# Requesting only 1 item initially
# Publisher: submitting 1
# Received: 1 (total so far: 1)
#   -> requesting 1 more
# Publisher: submitting 2
# Received: 2 (total so far: 2)
#   -> requesting 1 more
# Publisher: submitting 3
# Received: 3 (total so far: 3)
#   -> cancelling, no more needed
# Publisher: submitting 4
# ... (4 through 10 submitted, but subscriber never processes them — cancelled)
```

**What changed:** The subscriber deliberately requests items one at a time and cancels after receiving three, even though the publisher tries to submit ten. Because `SubmissionPublisher` respects the Reactive Streams backpressure contract, it queues submissions the subscriber hasn't requested yet (or in this specific JDK implementation, `submit` can block the producer if the subscriber's demand runs out and the internal buffer fills — a form of backpressure applied back to the producer) — the subscriber is never overwhelmed with more `onNext` calls than it explicitly asked for via `request(n)`.

### Level 3 — Advanced

Bridging between the raw `Flow` API and Project Reactor's `Flux` — demonstrating the interoperability the shared specification enables, since `Flux` can both consume a raw `Publisher` and expose itself as one:

```java
// InteropDemo.java
import reactor.core.publisher.Flux;
import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.List;

public class InteropDemo {

    record Product(String name, double price) {}

    public static void main(String[] args) throws InterruptedException {
        // A RAW java.util.concurrent.Flow.Publisher — no Reactor involved in producing it
        SubmissionPublisher<Product> rawPublisher = new SubmissionPublisher<>();

        // Reactor's Flux can wrap ANY compliant Publisher<T> directly, because
        // Flow.Publisher and Reactor's Publisher both conform to the SAME spec.
        Flux<Product> flux = Flux.from(rawPublisher);

        // Now use ordinary Reactor operators on data that originated from a
        // COMPLETELY different library's Publisher implementation.
        flux
            .filter(p -> p.price() > 10)
            .map(p -> new Product(p.name().toUpperCase(), p.price()))
            .subscribe(
                p -> System.out.println("Processed: " + p),
                error -> System.out.println("Error: " + error),
                () -> System.out.println("Stream complete")
            );

        for (Product p : List.of(new Product("Drill", 29.99), new Product("Nail", 0.50), new Product("Hammer", 14.99))) {
            rawPublisher.submit(p);
        }
        rawPublisher.close();

        Thread.sleep(200);
    }
}
```

**How to run:**
```bash
java InteropDemo.java
# Processed: Product[name=DRILL, price=29.99]
# Processed: Product[name=HAMMER, price=14.99]
# Stream complete
```

**What changed and why:**
- `Flux.from(rawPublisher)` works seamlessly even though `rawPublisher` is a raw JDK `SubmissionPublisher`, entirely unaware of Project Reactor's existence — this is only possible because both `java.util.concurrent.Flow.Publisher` and Reactor's `org.reactivestreams.Publisher` conform to the identical Reactive Streams specification (in fact, `Flow.Publisher` was specifically designed as a JDK-native mirror of the external `org.reactivestreams` interfaces, and Reactor provides adapters between the two).
- Every downstream operator (`filter`, `map`) and the terminal `subscribe` behave exactly as they would for a `Flux` built entirely within Reactor — the interoperability is complete and transparent, demonstrating the practical payoff of a shared, standardized contract rather than each reactive library needing bespoke bridging code for every other library it might need to interoperate with.
- This is precisely why Spring WebFlux can accept a `Mono`/`Flux` from application code, internally interoperate with a reactive database driver's own `Publisher` types (which may or may not literally be Reactor types), and consistently apply backpressure end-to-end — the entire chain, from database driver through WebFlux to the HTTP response, speaks the same underlying protocol.

## 6. Walkthrough

**Execution: `RawReactiveStreamsDemo.main()` (Level 1 code), tracing the exact protocol sequence.**

1. `publisher.subscribe(new LoggingSubscriber())` is called. Per the specification, this triggers the publisher to call `subscriber.onSubscribe(subscription)` — handing the subscriber a `Subscription` object that represents this specific publisher-subscriber pairing's control channel.
2. Inside `onSubscribe`: the subscriber stores the `subscription` reference (needed for all future `request`/`cancel` calls) and immediately calls `subscription.request(2)` — explicitly telling the publisher "I am ready to receive up to 2 items right now." Per the spec, the publisher **must not** call `onNext` more times than the cumulative outstanding `request` count allows.
3. Back in `main()`, the loop calls `publisher.submit("Drill")`, `publisher.submit("Hammer")`, `publisher.submit("Nail")` in sequence — `SubmissionPublisher` queues these internally and, because the subscriber has outstanding demand (`request(2)` was called), begins delivering them via `onNext` calls, asynchronously, on a separate thread from the one that called `submit`.
4. `onNext("Drill")` fires: the subscriber prints it, then calls `subscription.request(1)` again — replenishing its demand by one, since the initial `request(2)` has now been partially consumed (one delivered, one remaining before this new request).
5. `onNext("Hammer")` fires similarly: prints it, requests one more.
6. `onNext("Nail")` fires: prints it, requests one more (though no further items remain to be submitted).
7. `publisher.close()` (called from `main()`) signals that no more items will ever be submitted. Because the subscriber's outstanding demand has been satisfied (all three submitted items were delivered) and no more items exist, the publisher calls `subscriber.onComplete()` — the terminal, success-path signal per the specification.
8. `onComplete()` fires, printing `"onComplete"` — no further `onNext`, `onError`, or another `onComplete` call will ever occur for this subscription, per the specification's strict "at most one terminal signal" rule.

## 7. Gotchas & takeaways

> **Calling `onNext` more times than the cumulative `request(n)` count allows is a specification violation** — any compliant `Publisher` implementation (including `SubmissionPublisher`, Reactor's `Flux`, RxJava's `Observable`-via-adapter) must never do this. If you're implementing a raw `Publisher` yourself (rare, but possible), violating this rule breaks the fundamental backpressure guarantee the entire specification exists to provide.

> **`onError` and `onComplete` are mutually exclusive and each can occur at most once** — a compliant subscriber implementation should never expect (or need to handle) both being called for the same subscription, nor either being called more than once. Reactor's own operators enforce and rely on this invariant internally.

> **The raw `Flow`/Reactive Streams interfaces are rarely used directly in application code** — you'll work with `Mono`/`Flux` (or another library's higher-level abstraction) almost exclusively. Understanding the raw specification is valuable for genuinely understanding *why* reactive code behaves as it does (laziness, backpressure, termination rules), not for day-to-day implementation.

- Reactive Streams (`Publisher`/`Subscriber`/`Subscription`/`Processor`) is a language-level specification, mirrored in the JDK as `java.util.concurrent.Flow`, that standardizes asynchronous stream processing with built-in backpressure.
- `Subscription.request(n)` is the core backpressure mechanism — a subscriber explicitly controls how much data a publisher may send it at any given time.
- `onComplete`/`onError` are terminal, mutually exclusive, and occur at most once per subscription — a strict invariant every compliant implementation upholds.
- Because Reactor, RxJava, and other reactive libraries all implement the same specification, they interoperate directly without custom bridging code — this is the entire point of standardizing the contract rather than just the implementation.
