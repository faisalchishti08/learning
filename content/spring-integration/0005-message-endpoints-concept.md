---
card: spring-integration
gi: 5
slug: message-endpoints-concept
title: "Message endpoints concept"
---

## 1. What it is

A message endpoint is any component that connects application code to the messaging system described in card 0004 — it's the generic term for anything attached to one or more channels that does something with (or produces) messages: a handler that processes a message's payload, a gateway that lets non-messaging code send a message and get a reply, an adapter that bridges to an external system (a file system, HTTP, a database). Spring Integration provides several specific endpoint categories (service activators, routers, filters, transformers, and more, covered as their own patterns throughout later sections), and "message endpoint" is the umbrella concept all of them specialize.

## 2. Why & when

A channel alone just moves messages around; something has to actually *do* something with a message when it arrives — inspect it, transform it, act on it, decide where it goes next. Endpoints exist to be that "something," and the endpoint concept exists specifically to separate two concerns that are easy to conflate: **what the endpoint does** (its message-handling logic) from **how it's connected** (which channel(s) it reads from and writes to). Application code that implements an endpoint typically doesn't need to know about `Message` or channels directly at all — Spring Integration's endpoint infrastructure (message-handler adapters, `@ServiceActivator` and similar annotations) handles the connection, letting plain business logic sit at the center.

Recognize the message-endpoint concept applying whenever:

- A component needs to react to messages arriving on a channel and do real work with the payload — this is the general shape nearly every specific pattern in this section fits into.
- Business logic should stay decoupled from the messaging plumbing — a well-designed endpoint's core logic is often a plain method taking and returning plain objects, with the messaging-specific wiring handled separately by configuration or annotations.

## 3. Core concept

Think of an endpoint as an appliance plugged into an electrical outlet (the channel): the outlet doesn't know or care whether a toaster, a lamp, or a vacuum cleaner is plugged in, and the appliance itself doesn't need to understand how electricity is generated or distributed — it just does its one job (toasting, lighting, vacuuming) whenever current (a message) arrives. Spring Integration's endpoint infrastructure is the wiring and plug adapter that lets a plain, message-agnostic Java method (the appliance's actual function) be connected to a channel (the outlet) without that method needing to know anything about `Message`, headers, or channels at all.

```java
import org.springframework.integration.annotation.ServiceActivator;

public class OrderProcessor {
    // This method knows NOTHING about Message, MessageChannel, or Spring Integration internals —
    // it's plain business logic. The @ServiceActivator annotation is what wires it to a channel.
    @ServiceActivator(inputChannel = "orderChannel")
    public void process(String orderId) {
        System.out.println("Processing order: " + orderId);
    }
}
```

The framework automatically extracts the payload from the incoming `Message` and passes it as the method's argument (unless the method is written to accept a `Message<T>` directly for cases that genuinely need header access) — this is the essence of how endpoints keep business logic clean while still participating fully in the messaging system.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message endpoint bridges a channel to plain application logic, extracting the payload automatically so business code stays messaging-agnostic">
  <rect x="20" y="80" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orderChannel</text>

  <line x1="180" y1="105" x2="240" y2="105" stroke="#3fb950" stroke-width="2" marker-end="url(#v1)"/>

  <rect x="250" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Endpoint</text>
  <text x="340" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">extracts payload,</text>
  <text x="340" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">invokes plain method</text>
  <text x="340" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">process(String orderId)</text>

  <line x1="430" y1="105" x2="490" y2="105" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,3"/>

  <rect x="500" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no more messaging</text>

  <defs>
    <marker id="v1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The endpoint is the boundary where messaging concerns end and plain application logic begins.

## 5. Runnable example

The scenario: processing incoming orders through progressively more realistic endpoint-shaped logic — starting with a plain method invoked directly (illustrating the "just business logic" ideal), then simulating the channel-to-endpoint dispatch mechanism by hand, and finally an endpoint that also needs header information, showing when accepting a full `Message<T>` is the right call instead of just the payload.

### Level 1 — Basic

```java
// PlainOrderProcessor.java
public class PlainOrderProcessor {
    // This is the ideal: a plain method, no messaging types anywhere in its signature.
    public void process(String orderId) {
        System.out.println("Processing order: " + orderId);
    }

    public static void main(String[] args) {
        PlainOrderProcessor processor = new PlainOrderProcessor();
        processor.process("order-123"); // in a real Spring Integration app, a channel dispatch would call this
    }
}
```

**How to run:** run `java PlainOrderProcessor.java`. Expected output: `Processing order: order-123` — this method is exactly what would sit behind a real `@ServiceActivator`-annotated endpoint; the messaging framework's job is entirely about how it gets invoked, not about changing what it looks like.

### Level 2 — Intermediate

Simulating the dispatch mechanism by hand (a simplified stand-in for what Spring Integration's real endpoint infrastructure does automatically) makes clear exactly what "extracting the payload and invoking a plain method" means in practice.

```java
// SimulatedEndpointDispatch.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.function.Consumer;

public class SimulatedEndpointDispatch {

    // A minimal stand-in for what @ServiceActivator's underlying infrastructure does:
    // receive a Message, extract its payload, invoke a plain-object-accepting handler.
    static void dispatchToEndpoint(Message<String> message, Consumer<String> plainMethod) {
        String payload = message.getPayload(); // the messaging-aware extraction step
        plainMethod.accept(payload);           // the plain business method never sees the Message itself
    }

    static void process(String orderId) {
        System.out.println("Processing order: " + orderId);
    }

    public static void main(String[] args) {
        Message<String> incoming = MessageBuilder.withPayload("order-123")
            .setHeader("source", "web-checkout")
            .build();

        dispatchToEndpoint(incoming, SimulatedEndpointDispatch::process);
    }
}
```

**How to run:** run `java SimulatedEndpointDispatch.java`. Expected output: `Processing order: order-123` — despite the incoming `Message` carrying a `source` header, `process(String orderId)` never sees it and doesn't need to; `dispatchToEndpoint` is where the messaging-specific unwrapping happens, exactly mirroring what `@ServiceActivator`'s real infrastructure does under the hood.

### Level 3 — Advanced

Some endpoints genuinely need header information (deciding behavior based on the `source` header, for instance) — in that case, the endpoint method should accept the full `Message<T>` rather than just the payload, an equally valid and supported style, used deliberately rather than by default.

```java
// HeaderAwareEndpoint.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class HeaderAwareEndpoint {

    // This endpoint DOES need header information, so it accepts the full Message<T> —
    // a deliberate choice, not the default, since it couples this method to messaging types.
    static void process(Message<String> message) {
        String orderId = message.getPayload();
        Object source = message.getHeaders().get("source");

        if ("web-checkout".equals(source)) {
            System.out.println("Standard processing for order " + orderId + " from web checkout.");
        } else if ("admin-override".equals(source)) {
            System.out.println("Expedited processing for order " + orderId + " (admin override).");
        } else {
            System.out.println("Unknown source for order " + orderId + " — flagging for review.");
        }
    }

    public static void main(String[] args) {
        process(MessageBuilder.withPayload("order-123").setHeader("source", "web-checkout").build());
        process(MessageBuilder.withPayload("order-124").setHeader("source", "admin-override").build());
        process(MessageBuilder.withPayload("order-125").build()); // no source header at all
    }
}
```

**How to run:** run `java HeaderAwareEndpoint.java`. Expected output:
```
Standard processing for order order-123 from web checkout.
Expedited processing for order order-124 (admin override).
Unknown source for order order-125 — flagging for review.
```
This endpoint deliberately accepts the full `Message<String>` rather than just a `String` payload, because its actual logic depends on header content (`source`) that a plain-payload method signature simply couldn't see.

## 6. Walkthrough

Tracing the three `process(Message<String>)` calls in `HeaderAwareEndpoint`, in execution order:

1. The first call builds a message with payload `"order-123"` and header `source="web-checkout"`; inside `process`, `message.getPayload()` extracts `"order-123"` and `message.getHeaders().get("source")` retrieves `"web-checkout"`, matching the first `if` branch and printing the standard-processing message.
2. The second call builds a message with payload `"order-124"` and header `source="admin-override"`; the same extraction happens, but this time the value matches the `else if` branch, printing the expedited-processing message — the exact same method logic branches differently purely based on header content invisible to a plain-payload-only endpoint.
3. The third call builds a message with payload `"order-125"` and **no** `source` header at all; `message.getHeaders().get("source")` returns `null`, which matches neither prior branch, falling through to the final `else` and printing the "flagging for review" message — demonstrating that an endpoint reading headers must also handle the case where an expected header is simply absent, since `MessageHeaders` never guarantees any header beyond the automatic `id`/`timestamp` will be present.

```
process(msg1: payload="order-123", source="web-checkout")   -> standard processing branch
process(msg2: payload="order-124", source="admin-override")  -> expedited processing branch
process(msg3: payload="order-125", source=<absent>)           -> unknown-source / review branch
```

## 7. Gotchas & takeaways

> Defaulting every endpoint method to accept a full `Message<T>` "just in case it needs headers later" is a common overcorrection — it needlessly couples business logic to messaging types for endpoints that never actually use header information, making the logic harder to unit-test in isolation (every test now has to build a `Message` rather than just passing a plain value) and obscuring, at a glance, whether the method actually depends on any header data at all.

- Prefer plain-object method signatures (Level 1/2's style) for endpoints whose logic genuinely only depends on the payload — this keeps business logic simple, easily unit-testable without any messaging types involved, and clearly signals "this method doesn't care about headers."
- Accept the full `Message<T>` (Level 3's style) only when the endpoint's logic genuinely needs header information to make a decision — this is a deliberate, visible signal to future readers that headers matter here.
- An absent header returns `null` from `MessageHeaders.get(...)` rather than throwing — any endpoint reading a header that isn't guaranteed to always be present needs to handle that `null` case explicitly, exactly as the third branch in Level 3 does.
- "Message endpoint" is the umbrella concept; the specific, named endpoint roles (service activator, router, filter, transformer, and others) each specialize it with more particular behavior and are each worth learning as their own named pattern, following directly from card 0001's broader EIP framing.
- The dividing line an endpoint draws — messaging concerns on one side, plain application logic on the other — is the main architectural payoff of the whole endpoint concept; a well-designed endpoint keeps that line clean rather than letting messaging types leak deep into business logic that has no real need for them.
