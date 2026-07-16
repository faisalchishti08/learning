---
card: spring-integration
gi: 84
slug: reactive-streams-support
title: "Reactive Streams support"
---

## 1. What it is

Reactive Streams support (`IntegrationFlow.from(Publisher<?>)`, `.toReactivePublisher()`, `FluxMessageChannel`) lets a flow consume from or expose itself as a standard Reactive Streams `Publisher`/`Subscriber`, so it interoperates with Project Reactor, RxJava, or any other Reactive Streams-compliant library using the same backpressure protocol those libraries rely on. It's the mechanism that makes Spring Integration a genuine participant in a broader reactive pipeline, rather than a boundary that reactive code must awkwardly bridge into with blocking calls.

## 2. Why & when

You reach for Reactive Streams support when a flow needs to participate directly in a reactive pipeline, honoring backpressure end to end:

- **A flow's output feeds directly into a Reactor/RxJava pipeline, or vice versa** — exposing a Spring Integration flow as a `Publisher` (via `.toReactivePublisher()`) lets downstream reactive code subscribe to it using standard `Flux`/`Mono` operators, with backpressure signals propagating correctly instead of the flow producing messages faster than the consumer can handle.
- **A `FluxMessageChannel` replaces a traditional channel to get demand-driven flow control** — instead of messages being pushed onto a channel regardless of whether anything downstream is ready, a reactive channel only pulls the next message when a subscriber signals demand, naturally throttling a fast producer to match a slower consumer.
- **Do not reach for Reactive Streams support just to look modern** — for flows with modest throughput or no genuinely reactive consumer/producer on either end, ordinary imperative channels are simpler to reason about; the reactive model earns its complexity specifically when backpressure and non-blocking composition actually matter.

## 3. Core concept

Think of a traditional channel as a conveyor belt that keeps moving regardless of whether the person at the end can keep up — items pile up or get dropped if production outpaces consumption. A reactive, Reactive-Streams-based channel is more like a conveyor belt with the consumer holding the "go" button: the belt only advances one item at a time when the consumer explicitly signals they're ready for the next one (demand), so the producer is naturally paced to match — no pile-up, no dropped items, because production simply pauses until demand is signaled again.

```java
@Bean
public IntegrationFlow reactiveFlow() {
    return IntegrationFlow.from(FluxMessageChannel::new)
        .handle((String payload, headers) -> payload.toUpperCase())
        .toReactivePublisher();
}

// Elsewhere, a Reactor-based consumer applying its own backpressure-aware operators:
Flux.from(reactiveFlowPublisher)
    .limitRate(10) // only pulls 10 at a time, applying backpressure upstream through the flow
    .subscribe(result -> System.out.println("Received: " + result));
```

The `.limitRate(10)` call signals demand for only 10 items at a time; that demand signal propagates back through the flow to whatever is producing messages, throttling it to match.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A push-based channel produces messages regardless of consumer readiness, risking pile-up; a Reactive Streams channel only produces the next message when the consumer signals demand, keeping producer and consumer in sync" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Push-based channel</text>
  <rect x="20" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">producer -&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt; consumer (backlog builds)</text>
  <text x="160" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no signal to slow the producer down</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Reactive Streams channel</text>
  <rect x="340" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">producer &lt;- demand(N) - consumer</text>
  <text x="480" y="80" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">producer only sends up to N, then waits</text>

  <text x="320" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Demand signals let the consumer set the pace, not just absorb whatever arrives</text>
</svg>

Backpressure flips who controls the pace: the consumer requests, the producer waits until asked.

## 5. Runnable example

The scenario: a fast producer feeding a slower consumer, simulated with a simple demand-tracking queue standing in for a `FluxMessageChannel`'s backpressure protocol (no real Reactor/RxJava dependency needed to demonstrate the demand-driven throttling concept), starting with a naive push that overwhelms the consumer, then adding explicit demand signaling, then adding bounded buffering so a burst of demand doesn't unbounded-queue if the producer briefly outpaces even the requested rate.

### Level 1 — Basic

```java
// ReactiveBackpressureDemo.java
import java.util.*;

public class ReactiveBackpressureDemo {
    // Stand-in for a naive push-based channel: everything the producer makes goes straight in,
    // regardless of whether the consumer has asked for it or could keep up.
    static void pushEverything(List<Integer> produced, List<Integer> received) {
        received.addAll(produced); // consumer has no say in the pace
    }

    public static void main(String[] args) {
        List<Integer> produced = List.of(1, 2, 3, 4, 5);
        List<Integer> received = new ArrayList<>();
        pushEverything(produced, received);
        System.out.println("Received all at once: " + received);
    }
}
```

How to run: `java ReactiveBackpressureDemo.java`. Expected output: `Received all at once: [1, 2, 3, 4, 5]` — every item lands regardless of consumer readiness, the behavior a push-based channel exhibits with no backpressure at all.

### Level 2 — Intermediate

```java
// ReactiveBackpressureDemo.java
import java.util.*;

public class ReactiveBackpressureDemo {
    // Real-world concern: the consumer should control the pace by signaling how much it's
    // ready for -- the core idea behind Reactive Streams' request(n) demand signal.
    static class DemandDrivenChannel {
        private final Queue<Integer> available = new LinkedList<>();

        void produce(int item) { available.add(item); }

        List<Integer> request(int demand) {
            List<Integer> delivered = new ArrayList<>();
            for (int i = 0; i < demand && !available.isEmpty(); i++) {
                delivered.add(available.poll());
            }
            return delivered;
        }
    }

    public static void main(String[] args) {
        DemandDrivenChannel channel = new DemandDrivenChannel();
        for (int i = 1; i <= 10; i++) channel.produce(i);

        System.out.println("Consumer requests 3: " + channel.request(3));
        System.out.println("Consumer requests 3 more: " + channel.request(3));
        System.out.println("Consumer requests 10 (only 4 left): " + channel.request(10));
    }
}
```

How to run: `java ReactiveBackpressureDemo.java`. Expected output: `[1, 2, 3]`, then `[4, 5, 6]`, then `[7, 8, 9, 10]` — the consumer pulls only as much as it explicitly requests each time, never receiving more than its stated demand even when more is available upstream.

### Level 3 — Advanced

```java
// ReactiveBackpressureDemo.java
import java.util.*;

public class ReactiveBackpressureDemo {
    // Production concern: a producer can still momentarily outpace even a demand-aware
    // consumer (a burst arrives faster than the consumer's next request). A bounded buffer with
    // an explicit overflow policy prevents unbounded memory growth in that scenario, rather than
    // silently buffering an ever-growing backlog.
    static class BoundedDemandDrivenChannel {
        private final Deque<Integer> buffer = new ArrayDeque<>();
        private final int capacity;
        private int droppedCount = 0;

        BoundedDemandDrivenChannel(int capacity) { this.capacity = capacity; }

        void produce(int item) {
            if (buffer.size() >= capacity) {
                droppedCount++;
                System.out.println("Buffer full, dropping item " + item + " (overflow policy)");
                return;
            }
            buffer.add(item);
        }

        List<Integer> request(int demand) {
            List<Integer> delivered = new ArrayList<>();
            for (int i = 0; i < demand && !buffer.isEmpty(); i++) {
                delivered.add(buffer.poll());
            }
            return delivered;
        }

        int droppedCount() { return droppedCount; }
    }

    public static void main(String[] args) {
        BoundedDemandDrivenChannel channel = new BoundedDemandDrivenChannel(5);

        // A burst of 10 items produced before the consumer has requested anything at all.
        for (int i = 1; i <= 10; i++) channel.produce(i);

        System.out.println("Consumer requests 5: " + channel.request(5));
        System.out.println("Total dropped due to overflow: " + channel.droppedCount());
    }
}
```

How to run: `java ReactiveBackpressureDemo.java`. Expected output: five `Buffer full, dropping item ...` lines for items 6 through 10 (since the bounded buffer holds only 5 before any demand was requested), then `Consumer requests 5: [1, 2, 3, 4, 5]` and `Total dropped due to overflow: 5` — the bounded buffer's explicit overflow policy protecting memory when a burst outpaces even a demand-driven consumer, rather than growing without limit.

## 6. Walkthrough

Trace a message's journey through a reactive, demand-driven flow.

1. **Subscription**: a downstream Reactor or RxJava consumer subscribes to a flow exposed via `.toReactivePublisher()`, establishing the Reactive Streams contract between them.
2. **Initial demand signal**: the consumer (or an operator like `.limitRate(10)` acting on its behalf) sends an initial `request(n)` signal upstream through the flow, indicating how many messages it's currently ready to receive.
3. **Bounded production**: the flow's internal `FluxMessageChannel` only emits up to that requested amount, holding back any further messages until more demand is signaled — even if the flow's own producer (an inbound adapter, a transformation step) could technically generate messages faster.
4. **Consumption and further demand**: as the consumer processes each received message and becomes ready for more, it signals additional demand, and the flow releases the next batch — this negotiation repeats continuously for the life of the subscription.
5. **Overflow handling**: if the underlying producer genuinely cannot be paused (an external event source pushing data regardless of downstream readiness), a bounded buffer sits between production and the demand-driven interface, with an explicit policy (drop, error, or a bounded wait) for what happens when that buffer fills — silently growing an unbounded buffer is never the right default.
6. **Termination**: when the subscription ends (consumer cancels, or the flow completes/errors), both sides release resources cleanly, following the same Reactive Streams contract any other library implementing it would expect.

```
consumer subscribes
  -> consumer signals request(n)
    -> flow emits up to n messages, then waits
      -> consumer processes, signals more demand
        -> flow emits more (repeat)
  (if producer bursts faster than demand) -> bounded buffer -> explicit overflow policy
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing a blocking call into a step inside a reactive flow (a synchronous JDBC query, a blocking HTTP client call) defeats the entire purpose of Reactive Streams support — the demand-driven, non-blocking chain is only as good as its weakest link, and one blocking hop can stall the whole pipeline's ability to honor backpressure correctly.

- Reactive Streams support earns its complexity when a flow genuinely needs to interoperate with Reactor/RxJava and honor backpressure end to end; for a simple, moderate-throughput flow with no reactive consumer or producer on either side, a traditional channel is simpler and no less capable.
- A source that cannot itself be backpressured (many external event feeds, some hardware/sensor inputs) needs an explicit bounded buffer with a defined overflow policy between it and the demand-driven interface — Reactive Streams doesn't retroactively make an inherently push-only source backpressure-aware on its own.
- `FluxMessageChannel` and its non-reactive counterparts can coexist in the same application; a flow doesn't need to go "fully reactive" everywhere at once, but any point where the two paradigms meet needs deliberate design (typically an explicit buffering or blocking boundary) rather than an implicit, unexamined seam.
- Test reactive flows under actual backpressure conditions (a slow consumer, a bursty producer), not just the happy path where demand always exceeds supply — the interesting bugs in reactive systems tend to show up specifically when production and consumption rates diverge.
