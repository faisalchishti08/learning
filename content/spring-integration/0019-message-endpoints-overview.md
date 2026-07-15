---
card: spring-integration
gi: 19
slug: message-endpoints-overview
title: "Message endpoints overview"
---

## 1. What it is

A message endpoint is any component that connects to one or more channels and does something with the messages flowing through them — as distinct from a channel itself (the pipe) or an adapter (the boundary to the outside world, card 0018). Spring Integration provides several standard endpoint archetypes, each with a specific job: `ServiceActivator` (invoke a method, card 0020), `Transformer` (change the payload/headers, card 0021), `Filter` (conditionally drop messages, card 0022), `Router` (send to one of several channels based on content, card 0023), and `Splitter` (turn one message into many, card 0024) — the next five cards each cover one in depth.

## 2. Why & when

Understanding the endpoint taxonomy matters because it tells you which building block fits a given need, instead of writing bespoke handler code for jobs the framework already has a named, well-understood shape for:

- **You need to invoke existing business logic in response to a message** — a `ServiceActivator` wraps a plain method call, letting messaging-unaware service code participate in a flow without itself depending on Spring Integration types.
- **A message's shape needs to change before the next step can use it** — a `Transformer` converts payload/header content into whatever downstream expects, keeping that conversion logic in one clearly-named place rather than buried inside a handler.
- **Some messages shouldn't proceed at all**, or **one message needs to become several**, or **different messages need to go down different paths** — `Filter`, `Splitter`, and `Router` respectively are the named, purpose-built endpoints for exactly those three shapes of decision, rather than reinventing conditional logic ad hoc inside a generic handler.

## 3. Core concept

Think of a message flow like a factory assembly line, where channels are the conveyor belts and endpoints are the labeled stations along the line: an inspection station (`Filter`) that pulls defective items off the belt, a repackaging station (`Transformer`) that changes an item's container, a sorting station (`Router`) that sends items down different belts based on their label, a station that breaks a pallet into individual boxes (`Splitter`), and a station where an actual worker does the core job (`ServiceActivator`). Each station has one clear responsibility; a complex flow is built by chaining stations together along belts, not by building one station that tries to do everything.

```java
// The common shape: every endpoint subscribes to an input channel and (usually) sends to an output channel.
DirectChannel input = new DirectChannel();
DirectChannel output = new DirectChannel();

input.subscribe(message -> {
    // whatever this endpoint's specific job is (validate, transform, route, split, invoke a service...)
    Object result = message.getPayload().toString().toUpperCase();
    output.send(MessageBuilder.withPayload(result).build());
});
```

Every endpoint type covered in cards 0020–0024 follows this same "subscribe to input, do a specific job, optionally produce output for the next channel" shape — the difference between them is purely what happens inside that job.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A flow assembled from labeled endpoint stations connected by channels: filter, transformer, service activator, router, splitter">
  <rect x="10" y="70" width="90" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="55" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Filter</text>

  <line x1="100" y1="92" x2="130" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#en1)"/>

  <rect x="135" y="70" width="90" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="180" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Transformer</text>

  <line x1="225" y1="92" x2="255" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#en1)"/>

  <rect x="260" y="70" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ServiceActivator</text>

  <line x1="370" y1="92" x2="400" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#en1)"/>

  <rect x="405" y="70" width="90" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="450" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Router</text>

  <line x1="450" y1="70" x2="450" y2="30" stroke="#6db33f" stroke-width="1.5" marker-end="url(#en1)"/>
  <line x1="450" y1="115" x2="450" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#en1)"/>
  <text x="490" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">channel A</text>
  <text x="490" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">channel B</text>

  <defs>
    <marker id="en1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each labeled station is one endpoint type; cards 0020–0024 cover Filter, Transformer, ServiceActivator, Router, and Splitter individually.

## 5. Runnable example

The scenario: an order-processing pipeline chaining several endpoint archetypes together, starting with a minimal two-station chain, then adding a third station, and finally a full five-station flow showing how the archetypes compose.

### Level 1 — Basic

```java
// TwoStationChainDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class TwoStationChainDemo {
    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();
        DirectChannel processed = new DirectChannel();

        processed.subscribe(m -> System.out.println("Final station received: " + m.getPayload()));

        // a single "transformer-shaped" station: uppercase the payload, forward to the next channel
        intake.subscribe(m -> {
            String upper = m.getPayload().toString().toUpperCase();
            processed.send(MessageBuilder.withPayload(upper).build());
        });

        intake.send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java TwoStationChainDemo.java`. Expected output: `Final station received: ORDER-1` — a minimal two-station chain: one endpoint transforms, forwards to a channel, and a second endpoint (here, just a print) receives the result.

### Level 2 — Intermediate

Adding a filter-shaped station before the transformer shows how endpoints compose by each doing one job and handing off — the filter only forwards messages that pass a condition, and anything it doesn't forward simply never reaches the stations after it.

```java
// ThreeStationChainDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class ThreeStationChainDemo {
    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();
        DirectChannel afterFilter = new DirectChannel();
        DirectChannel afterTransform = new DirectChannel();

        afterTransform.subscribe(m -> System.out.println("Final station received: " + m.getPayload()));

        // transformer-shaped station
        afterFilter.subscribe(m -> {
            String upper = m.getPayload().toString().toUpperCase();
            afterTransform.send(MessageBuilder.withPayload(upper).build());
        });

        // filter-shaped station: only forward payloads starting with "order-"
        intake.subscribe(m -> {
            String payload = m.getPayload().toString();
            if (payload.startsWith("order-")) {
                afterFilter.send(m);
            } else {
                System.out.println("Filter station DROPPED: " + payload);
            }
        });

        intake.send(MessageBuilder.withPayload("order-1").build());  // passes filter
        intake.send(MessageBuilder.withPayload("spam-99").build());  // dropped by filter
    }
}
```

How to run: `java ThreeStationChainDemo.java`. Expected output: `Final station received: ORDER-1` for the first message, and `Filter station DROPPED: spam-99` for the second — the second message never reaches the transformer or final stations at all, since the filter station stopped it.

### Level 3 — Advanced

A full five-station flow — filter, transformer, service activator, router, and (conceptually) a downstream split — shows the archetypes from card 0019's overview composing into a realistic pipeline; each subsequent card (0020–0024) will build out one of these stations in much greater depth.

```java
// FiveStationFlowDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class FiveStationFlowDemo {
    record Order(String id, double amount, String type) {}

    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();
        DirectChannel validated = new DirectChannel();
        DirectChannel parsed = new DirectChannel();
        DirectChannel highValue = new DirectChannel();
        DirectChannel standard = new DirectChannel();

        highValue.subscribe(m -> System.out.println("[HIGH-VALUE PATH] Service activator invoked for: " + m.getPayload()));
        standard.subscribe(m -> System.out.println("[STANDARD PATH] Service activator invoked for: " + m.getPayload()));

        // ROUTER station: send to one of two channels based on content
        parsed.subscribe(m -> {
            Order order = (Order) m.getPayload();
            if (order.amount() > 100.0) highValue.send(m); else standard.send(m);
        });

        // TRANSFORMER station: raw string -> domain object
        validated.subscribe(m -> {
            String[] parts = m.getPayload().toString().split("\\|");
            Order order = new Order(parts[0], Double.parseDouble(parts[1]), parts[2]);
            parsed.send(MessageBuilder.withPayload(order).build());
        });

        // FILTER station: only "order" type messages proceed
        intake.subscribe(m -> {
            String raw = m.getPayload().toString();
            if (raw.contains("|order|") || raw.endsWith("|order")) {
                validated.send(m);
            } else {
                System.out.println("Filter station DROPPED non-order message: " + raw);
            }
        });

        intake.send(MessageBuilder.withPayload("ORD-1|199.99|order").build()); // high-value path
        intake.send(MessageBuilder.withPayload("ORD-2|25.00|order").build());  // standard path
        intake.send(MessageBuilder.withPayload("PING-1|0|heartbeat").build()); // dropped by filter
    }
}
```

How to run: `java FiveStationFlowDemo.java`. Expected output: `[HIGH-VALUE PATH] Service activator invoked for: Order[id=ORD-1, amount=199.99, type=order]`, then `[STANDARD PATH] Service activator invoked for: Order[id=ORD-2, amount=25.0, type=order]`, then `Filter station DROPPED non-order message: PING-1|0|heartbeat` — three different messages, each taking a different path through the same five-station pipeline based on the filter and router decisions.

## 6. Walkthrough

Tracing `FiveStationFlowDemo` for the `ORD-1` message in execution order:

1. `intake.send("ORD-1|199.99|order")` triggers the filter station's subscriber, which checks whether the raw string indicates an order — it does, so the message is forwarded unchanged to `validated`.
2. The transformer station on `validated` splits the raw string on `|`, parses the amount as a `double`, and constructs an `Order` domain record — this is where the shape genuinely changes, from an opaque string to a typed object — then sends the new message to `parsed`.
3. The router station on `parsed` inspects the `Order`'s `amount` field: `199.99 > 100.0` is true, so the message is forwarded to `highValue` rather than `standard`.
4. The service-activator-shaped station on `highValue` receives the fully parsed, routed `Order` and prints confirmation that "business logic" ran on the high-value path.
5. For `ORD-2` (amount `25.00`), the exact same filter and transformer stations run, but the router's condition is now false, so it goes to `standard` instead — same stations, different path, purely from a data-driven decision.
6. For `PING-1`, the filter station's condition fails immediately — the message never reaches the transformer, router, or either service-activator station at all; the pipeline as a whole made a decision without four of its five stations ever seeing the message.

```
intake --[Filter]--> validated --[Transformer]--> parsed --[Router]--> highValue --[ServiceActivator]
                                                              \--> standard --[ServiceActivator]
```

## 7. Gotchas & takeaways

> It's tempting to write one large handler that filters, transforms, and routes all in a single lambda — and it will work. But it loses exactly what naming each responsibility as a distinct endpoint archetype buys you: each station in `FiveStationFlowDemo` can be tested, replaced, or reasoned about independently, and the *next channel* between stations is a natural place to add logging, metrics, or a `ChannelInterceptor` (card 0015) targeting just that one hand-off. Collapsing stations together trades that composability for a slightly shorter method.

- A message endpoint is any component that does a specific job on messages flowing between channels; Spring Integration names five common archetypes: `ServiceActivator`, `Transformer`, `Filter`, `Router`, and `Splitter` (cards 0020–0024).
- Each archetype has one clear responsibility, and real flows are built by chaining multiple endpoints together via channels, mirroring an assembly line's labeled stations.
- Endpoints share a common shape: subscribe to an input channel, perform their specific job, and (usually) send a result to an output channel for the next station.
- Choosing the right named archetype for a given job (rather than one large generic handler) keeps each step independently testable, replaceable, and interceptable.
- The next five cards each take one archetype from this overview and go deep on its specific behavior, configuration options, and edge cases.
