---
card: spring-integration
gi: 2
slug: message-payload-headers
title: "Message (payload + headers)"
---

## 1. What it is

`org.springframework.messaging.Message<T>` is Spring Integration's fundamental unit of data — every single thing that flows through a Spring Integration application is wrapped in one. A `Message` has exactly two parts: the **payload** (the actual business data being carried, of generic type `T`) and the **headers** (`MessageHeaders`, a read-only map of metadata about that payload — where it came from, what type it is, a correlation identifier, and anything else attached along the way).

## 2. Why & when

Passing raw business objects (a plain `Order`, a plain `String`) through an integration pipeline works fine until the pipeline needs to know something *about* the data that isn't part of the data itself — which channel it arrived on, when it was created, what the original file name was, whether it's a retry. Bolting that metadata onto the business object itself (adding a `sourceChannel` field to `Order`) pollutes the domain model with integration-specific concerns it has no business knowing about. `Message<T>` exists to carry both together, cleanly separated: the payload stays a plain, unpolluted domain object, and everything integration-specific rides alongside in headers.

Reach for explicit `Message<T>` construction (rather than letting a payload pass through implicitly, which many endpoints support) when:

- Metadata about the payload needs to travel with it — a correlation ID for later aggregation, a reply-channel reference, a custom header a downstream router will inspect.
- Building a message from scratch to send into a Spring Integration flow, such as from a plain scheduled trigger or a custom event source.

## 3. Core concept

Think of a `Message<T>` like a physical package being shipped: the payload is whatever's actually inside the box (the thing the recipient cares about), and the headers are everything printed on the shipping label — sender address, tracking number, fragile/handle-with-care markings, which depot it passed through. The recipient (whatever endpoint eventually consumes the message) primarily wants the contents, but the label's information is what let the package get routed correctly along the way, and a curious recipient can always check the label for extra context without opening the box differently.

```java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

Message<String> message = MessageBuilder
    .withPayload("order-123")
    .setHeader("correlationId", "abc-456")
    .setHeader("source", "web-checkout")
    .build();

String payload = message.getPayload();               // "order-123"
Object correlationId = message.getHeaders().get("correlationId"); // "abc-456"
```

Some headers are standard and automatically managed by the framework — `id` (a unique `UUID` per message) and `timestamp` (creation time) are set automatically by `MessageBuilder` unless explicitly overridden, and `MessageHeaders` itself is immutable once built: headers can't be changed in place, only carried forward (optionally with additions) into a new `Message` via `MessageBuilder.fromMessage(...)`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Message wraps a payload and a MessageHeaders map together as one immutable unit flowing through the integration pipeline">
  <rect x="40" y="30" width="560" height="140" rx="10" fill="none" stroke="#8b949e" stroke-dasharray="4,4"/>
  <text x="320" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Message&lt;T&gt;</text>

  <rect x="70" y="55" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="190" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Payload</text>
  <text x="190" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"order-123"</text>
  <text x="190" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the actual business data</text>

  <rect x="340" y="55" width="240" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="80" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageHeaders</text>
  <text x="460" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">id, timestamp</text>
  <text x="460" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">correlationId, source</text>
  <text x="460" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(read-only metadata)</text>
</svg>

Payload and headers travel together as one immutable `Message`, cleanly separating business data from integration metadata.

## 5. Runnable example

The scenario: building and inspecting messages for an order pipeline, starting with a bare payload, then adding meaningful headers, and finally deriving a new message from an existing one while preserving and extending its metadata.

### Level 1 — Basic

```java
// BasicMessageDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicMessageDemo {
    public static void main(String[] args) {
        Message<String> message = MessageBuilder.withPayload("order-123").build();

        System.out.println("Payload: " + message.getPayload());
        System.out.println("Auto-generated id: " + message.getHeaders().getId());
        System.out.println("Auto-generated timestamp: " + message.getHeaders().getTimestamp());
    }
}
```

**How to run:** run with Spring Messaging on the classpath: `java BasicMessageDemo.java`. Expected output: `Payload: order-123` followed by a random UUID for the id and a numeric epoch-millis timestamp — both generated automatically by `MessageBuilder` without any explicit header being set.

### Level 2 — Intermediate

Real pipelines need custom headers carrying meaningful integration metadata, not just the automatic `id`/`timestamp`.

```java
// AnnotatedOrderMessage.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class AnnotatedOrderMessage {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        Order order = new Order("123", 49.99);

        Message<Order> message = MessageBuilder
            .withPayload(order)
            .setHeader("source", "web-checkout")
            .setHeader("correlationId", "abc-456")
            .setHeader("retryCount", 0)
            .build();

        System.out.println("Order amount: " + message.getPayload().amount());
        System.out.println("Came from: " + message.getHeaders().get("source"));
        System.out.println("Correlation: " + message.getHeaders().get("correlationId"));
    }
}
```

**How to run:** run `java AnnotatedOrderMessage.java`. Expected output: `Order amount: 49.99`, `Came from: web-checkout`, `Correlation: abc-456` — the `Order` payload stays a plain, unpolluted domain record, while every piece of integration-specific metadata (source, correlation ID, retry count) lives entirely in the headers.

### Level 3 — Advanced

Since `MessageHeaders` is immutable, a step in the pipeline that needs to add or update a header (incrementing a retry count on a failed attempt, for instance) must build a *new* `Message`, carrying forward the existing headers via `MessageBuilder.fromMessage(...)` rather than trying to mutate the original.

```java
// RetryHeaderDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class RetryHeaderDemo {
    record Order(String id, double amount) {}

    static Message<Order> incrementRetry(Message<Order> original) {
        int currentRetry = (int) original.getHeaders().getOrDefault("retryCount", 0);
        // MessageHeaders is immutable — fromMessage() copies the existing headers into a new builder,
        // and setHeader() here overwrites just the one header we intend to change.
        return MessageBuilder.fromMessage(original)
            .setHeader("retryCount", currentRetry + 1)
            .build();
    }

    public static void main(String[] args) {
        Message<Order> original = MessageBuilder
            .withPayload(new Order("123", 49.99))
            .setHeader("source", "web-checkout")
            .setHeader("retryCount", 0)
            .build();

        Message<Order> afterFirstRetry = incrementRetry(original);
        Message<Order> afterSecondRetry = incrementRetry(afterFirstRetry);

        System.out.println("Original retryCount: " + original.getHeaders().get("retryCount"));
        System.out.println("After 1st retry: " + afterFirstRetry.getHeaders().get("retryCount"));
        System.out.println("After 2nd retry: " + afterSecondRetry.getHeaders().get("retryCount"));
        System.out.println("source header preserved throughout: " + afterSecondRetry.getHeaders().get("source"));
    }
}
```

**How to run:** run `java RetryHeaderDemo.java`. Expected output: `Original retryCount: 0`, `After 1st retry: 1`, `After 2nd retry: 2`, and `source header preserved throughout: web-checkout` — each call to `incrementRetry` produces a brand-new `Message` object; the original is never mutated (and couldn't be, since `MessageHeaders` is immutable), yet every unrelated header (`source`) survives unchanged across each derived message.

## 6. Walkthrough

Tracing the two `incrementRetry` calls, in execution order:

1. `original` is built with `retryCount=0` and `source="web-checkout"` explicitly set, plus `id`/`timestamp` generated automatically.
2. `incrementRetry(original)` reads `original.getHeaders().getOrDefault("retryCount", 0)`, getting `0`.
3. `MessageBuilder.fromMessage(original)` starts a new builder pre-populated with a **copy** of every header from `original` (including `source`, `retryCount`, `id`, and `timestamp`) and the same payload reference — nothing about `original` itself is touched.
4. `.setHeader("retryCount", 1)` overwrites just that one header on the new builder's working copy; `source` remains whatever it was copied as.
5. `.build()` produces `afterFirstRetry`, a distinct `Message` object from `original`, sharing the same payload but with `retryCount` now `1` and every other header carried forward unchanged.
6. `incrementRetry(afterFirstRetry)` repeats the same sequence starting from `afterFirstRetry`'s current `retryCount` (`1`), producing `afterSecondRetry` with `retryCount=2`.
7. Printing `original`'s `retryCount` at the end still shows `0` — confirming the original message was genuinely never mutated by either call, only ever read from to produce new, independent messages.

```
original:        retryCount=0, source="web-checkout"
   incrementRetry(original)
      -> fromMessage(original) copies ALL headers
      -> overwrite retryCount: 0 -> 1
afterFirstRetry:  retryCount=1, source="web-checkout"   (original UNCHANGED)
   incrementRetry(afterFirstRetry)
      -> fromMessage(afterFirstRetry) copies ALL headers
      -> overwrite retryCount: 1 -> 2
afterSecondRetry: retryCount=2, source="web-checkout"
```

## 7. Gotchas & takeaways

> `MessageHeaders` is immutable by design — there is no `setHeader` method on `Message` or `MessageHeaders` themselves. Any code that needs to "update" a header must build an entirely new `Message` via `MessageBuilder.fromMessage(existing).setHeader(...)...build()`, carrying forward every other header automatically. Forgetting `fromMessage(...)` and building fresh instead silently drops every header the original message was carrying.

- Keep the payload a plain domain object with no integration-specific fields — headers are exactly where routing, correlation, and metadata concerns belong instead.
- `id` and `timestamp` are set automatically by `MessageBuilder` and are effectively reserved standard headers — avoid overloading them for custom application meaning.
- Because `MessageHeaders` is immutable, "modifying" a message always means producing a new one — this is a deliberate design choice that makes messages safe to pass across threads and components without fear of one component's changes leaking into another's view of the same message.
- `MessageBuilder.fromMessage(original)` is the standard way to derive a new message while preserving existing headers — building a message from scratch when only one header needs to change is a common, easily-avoided mistake that silently discards the rest of the original headers.
- Headers are effectively untyped (`Map<String, Object>` under the hood) — casting a header's value to the expected type is the caller's responsibility, and a typo in a header name (or an unexpected type) fails only at the point of use, not at compile time.
