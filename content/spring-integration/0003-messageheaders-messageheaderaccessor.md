---
card: spring-integration
gi: 3
slug: messageheaders-messageheaderaccessor
title: "MessageHeaders & MessageHeaderAccessor"
---

## 1. What it is

`MessageHeaders` (card 0002's read-only header map) is deliberately minimal and immutable — good for safety, awkward for building up a set of headers incrementally. `MessageHeaderAccessor` is the companion class that makes constructing and working with headers ergonomic: it wraps a `MessageHeaders` (or starts fresh) with typed getters for the standard headers (`getId()`, `getTimestamp()`), a fluent way to set custom headers, and subclass variants (like `MessageHeaderAccessor.getAccessor(message, ...)`) tailored to specific messaging protocols.

## 2. Why & when

Working directly with `MessageHeaders` as a raw `Map<String, Object>` means every access to a standard header requires remembering its exact string key and casting the result (`(String) headers.get("source")`, `(UUID) headers.get("id")`) — tedious and easy to get subtly wrong (a typo'd key silently returns `null` instead of failing to compile). `MessageHeaderAccessor` exists to wrap that map with a proper typed API, and — just as importantly — to serve as the standard mutable "builder-in-progress" object used while a message is being assembled, before it's frozen into an immutable `MessageHeaders` at the point a `Message` is finally built.

Reach for `MessageHeaderAccessor` when:

- Reading standard headers (`id`, `timestamp`) with proper types instead of manual casting from the raw map.
- Building up a set of headers across several steps or conditionally, before finally constructing the message — `MessageBuilder` actually uses a `MessageHeaderAccessor` internally for exactly this purpose.
- Working with a specific messaging protocol's headers (STOMP, AMQP) via a protocol-specific accessor subclass that exposes protocol headers with proper typed accessors, rather than through raw string keys.

## 3. Core concept

Think of `MessageHeaders` as a sealed, printed shipping label — official, final, unchangeable once affixed to the package. `MessageHeaderAccessor` is the label-printing terminal used *before* the label gets sealed and stuck onto the box: you can type in fields, correct a typo, add a tracking number, check what you've entered so far, all with a proper interface (typed fields, not just freehand scribbling) — and only when everything's ready does pressing "print" seal it into the actual immutable label (`MessageHeaders`) that ships with the package.

```java
import org.springframework.messaging.support.MessageHeaderAccessor;

MessageHeaderAccessor accessor = new MessageHeaderAccessor();
accessor.setHeader("source", "web-checkout");
accessor.setHeader("correlationId", "abc-456");

MessageHeaders headers = accessor.getMessageHeaders(); // finalize into the immutable form
System.out.println(headers.getId());        // typed UUID getter, no manual casting
System.out.println(headers.getTimestamp()); // typed Long getter
```

`MessageHeaderAccessor` also has a `setLeaveMutable(true)` mode and a corresponding `MessageHeaderAccessor.getMutableAccessor(message)` retrieval, letting a message's headers be "reopened" for further modification later in a flow under specific, deliberate circumstances — but this is the exception, not the default, and most code should treat headers as settled once a message is built.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MessageHeaderAccessor is a mutable working area for assembling headers before they are finalized into immutable MessageHeaders">
  <rect x="30" y="60" width="220" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageHeaderAccessor</text>
  <text x="140" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mutable, typed, fluent</text>
  <text x="140" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setHeader(...), getId(), ...</text>

  <line x1="250" y1="105" x2="320" y2="105" stroke="#3fb950" stroke-width="2" marker-end="url(#t1)"/>
  <text x="285" y="95" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">finalize</text>

  <rect x="330" y="60" width="220" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageHeaders</text>
  <text x="440" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">immutable, read-only</text>
  <text x="440" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ships with the Message</text>

  <defs>
    <marker id="t1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The accessor is the mutable working area; `MessageHeaders` is the frozen result that actually ships with the `Message`.

## 5. Runnable example

The scenario: assembling headers for an order message across a few conditional steps, starting with basic accessor usage, then building headers conditionally, and finally using a subclassed accessor for a specific protocol-flavored header set.

### Level 1 — Basic

```java
// BasicAccessorDemo.java
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.messaging.MessageHeaders;

public class BasicAccessorDemo {
    public static void main(String[] args) {
        MessageHeaderAccessor accessor = new MessageHeaderAccessor();
        accessor.setHeader("source", "web-checkout");
        accessor.setHeader("correlationId", "abc-456");

        MessageHeaders headers = accessor.getMessageHeaders();

        System.out.println("id: " + headers.getId());
        System.out.println("timestamp: " + headers.getTimestamp());
        System.out.println("source: " + headers.get("source"));
    }
}
```

**How to run:** run with Spring Messaging on the classpath: `java BasicAccessorDemo.java`. Expected output: a generated UUID for `id`, a numeric epoch-millis `timestamp`, and `source: web-checkout` — `getId()`/`getTimestamp()` return properly typed values without any manual casting from a raw map.

### Level 2 — Intermediate

Building headers conditionally across several steps — some headers only added if certain business conditions hold — is exactly what the mutable accessor is for, deferring the immutable freeze until everything's decided.

```java
// ConditionalHeaderBuilder.java
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.messaging.MessageHeaders;

public class ConditionalHeaderBuilder {
    record Order(String id, double amount, boolean expedited) {}

    static MessageHeaders buildHeaders(Order order) {
        MessageHeaderAccessor accessor = new MessageHeaderAccessor();
        accessor.setHeader("orderId", order.id());

        if (order.amount() > 100.0) {
            accessor.setHeader("requiresApproval", true); // only set for large orders
        }
        if (order.expedited()) {
            accessor.setHeader("priority", "HIGH"); // only set for expedited orders
        }

        return accessor.getMessageHeaders();
    }

    public static void main(String[] args) {
        MessageHeaders smallOrderHeaders = buildHeaders(new Order("1", 49.99, false));
        MessageHeaders largeExpeditedHeaders = buildHeaders(new Order("2", 250.00, true));

        System.out.println("Small order requiresApproval: " + smallOrderHeaders.get("requiresApproval"));
        System.out.println("Large expedited requiresApproval: " + largeExpeditedHeaders.get("requiresApproval"));
        System.out.println("Large expedited priority: " + largeExpeditedHeaders.get("priority"));
    }
}
```

**How to run:** run `java ConditionalHeaderBuilder.java`. Expected output: `Small order requiresApproval: null` (the header was never set for this order), `Large expedited requiresApproval: true`, and `Large expedited priority: HIGH` — headers are assembled conditionally through the mutable accessor, and only the headers actually set for each specific order end up present in its final, frozen `MessageHeaders`.

### Level 3 — Advanced

A protocol-specific accessor subclass (illustrated here with a simplified custom accessor pattern, mirroring how Spring's real STOMP/AMQP accessors work) exposes protocol-relevant headers through proper typed methods, rather than requiring every caller to know and use the exact string keys directly.

```java
// OrderHeaderAccessor.java — a custom accessor subclass exposing typed methods for this domain's headers
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.messaging.Message;

public class OrderHeaderAccessor extends MessageHeaderAccessor {
    private static final String ORDER_ID = "orderId";
    private static final String PRIORITY = "priority";

    public static OrderHeaderAccessor create() {
        return new OrderHeaderAccessor();
    }

    // Retrieves an existing OrderHeaderAccessor-compatible view over an already-built message's headers.
    public static OrderHeaderAccessor wrap(Message<?> message) {
        OrderHeaderAccessor accessor = new OrderHeaderAccessor();
        message.getHeaders().forEach(accessor::setHeader);
        return accessor;
    }

    public OrderHeaderAccessor setOrderId(String orderId) {
        setHeader(ORDER_ID, orderId);
        return this;
    }

    public String getOrderId() {
        return (String) getHeader(ORDER_ID);
    }

    public OrderHeaderAccessor setPriority(String priority) {
        setHeader(PRIORITY, priority);
        return this;
    }

    public String getPriority() {
        return (String) getHeader(PRIORITY);
    }
}
```

```java
// TypedAccessorDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class TypedAccessorDemo {
    public static void main(String[] args) {
        OrderHeaderAccessor accessor = OrderHeaderAccessor.create()
            .setOrderId("789")
            .setPriority("HIGH");

        Message<String> message = MessageBuilder
            .withPayload("order-payload")
            .setHeaders(accessor)
            .build();

        OrderHeaderAccessor readBack = OrderHeaderAccessor.wrap(message);
        System.out.println("Order ID (typed): " + readBack.getOrderId());
        System.out.println("Priority (typed): " + readBack.getPriority());
    }
}
```

**How to run:** run `java TypedAccessorDemo.java`. Expected output: `Order ID (typed): 789` and `Priority (typed): HIGH` — both the writing side (`setOrderId`, `setPriority`) and the reading side (`getOrderId`, `getPriority`) go through proper typed methods specific to this domain's headers, rather than every call site needing to know and correctly type-cast the raw string keys `"orderId"` and `"priority"` independently.

## 6. Walkthrough

Tracing `TypedAccessorDemo`, in execution order:

1. `OrderHeaderAccessor.create()` instantiates a fresh, mutable accessor with no headers set yet.
2. `.setOrderId("789")` calls the typed setter, which internally calls the inherited `setHeader("orderId", "789")` — the underlying storage is the same generic header map `MessageHeaderAccessor` always uses, but the *interface* exposed to calling code is domain-specific and typed.
3. `.setPriority("HIGH")` similarly sets the `"priority"` header, and both calls return `this`, enabling the fluent chaining shown.
4. `MessageBuilder.withPayload("order-payload").setHeaders(accessor)` incorporates the accessor's accumulated headers into the message being built — this is the point where the accessor's mutable working state feeds into the final, immutable `MessageHeaders` that the resulting `Message` will carry.
5. `.build()` finalizes the message; from this point on, its headers are immutable, exactly as described in card 0002.
6. `OrderHeaderAccessor.wrap(message)` demonstrates the reverse direction: given an already-built message, a new `OrderHeaderAccessor` is created and populated by copying every entry from `message.getHeaders()` into it via `setHeader`, giving typed read access (`getOrderId()`, `getPriority()`) back over data that arrived as a plain immutable header map.
7. The final two `println` calls confirm both typed values round-tripped correctly through the write-then-read cycle.

```
OrderHeaderAccessor.create()
   .setOrderId("789")    -> setHeader("orderId","789")   [mutable, typed API]
   .setPriority("HIGH")  -> setHeader("priority","HIGH")
-> MessageBuilder.setHeaders(accessor) -> build() -> immutable Message

OrderHeaderAccessor.wrap(message)
   -> copies message.getHeaders() entries into a fresh accessor
   -> getOrderId() / getPriority()   [typed read access over the same underlying data]
```

## 7. Gotchas & takeaways

> `MessageHeaderAccessor` instances are mutable and generally meant to be short-lived, used only during message construction (or explicit, deliberate header modification via `getMutableAccessor`) — holding onto and continuing to mutate an accessor after its headers have already been "finalized" into a `Message` does not retroactively change that already-built message, since `getMessageHeaders()`/`build()` captures a snapshot into the immutable form.

- Prefer `MessageHeaderAccessor` (or a domain-specific subclass) over manually reading/writing the raw `MessageHeaders` map whenever more than a header or two is involved, or whenever headers need to be assembled conditionally across multiple steps.
- Standard headers (`id`, `timestamp`) get proper typed getters (`getId()` returns a `UUID`, `getTimestamp()` returns a `Long`) directly on `MessageHeaders`/`MessageHeaderAccessor`, avoiding manual casting.
- `MessageBuilder` itself uses a `MessageHeaderAccessor` internally — reaching for the accessor directly (rather than always going through `MessageBuilder`) is most useful when headers need custom typed accessors or need to be assembled across a more involved sequence of conditional logic.
- A protocol- or domain-specific accessor subclass (Level 3's `OrderHeaderAccessor`, or Spring's own STOMP/AMQP accessors) turns error-prone raw string-key access into a proper typed API, catching a mistyped header name at compile time rather than silently returning `null` at runtime.
- The accessor is a construction-time or explicit-mutation-time tool; once a `Message` is built, its headers are immutable exactly as covered in card 0002 — modifying a message's headers afterward always means building a new message, whether via `MessageBuilder.fromMessage(...)` or an accessor wrapping the existing one.
