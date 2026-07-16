---
card: spring-amqp
gi: 11
slug: sending-messages-convertandsend
title: "Sending messages (convertAndSend)"
---

## 1. What it is

`convertAndSend` is `RabbitTemplate`'s primary method for publishing messages, available in several overloaded forms: `convertAndSend(routingKey, object)` sends to the template's configured default exchange, `convertAndSend(exchange, routingKey, object)` specifies both explicitly, and each accepts an optional `MessagePostProcessor` (card 0013) for last-moment customization. It takes a plain Java object, runs it through the configured `MessageConverter` (card 0012) to produce message bytes, wraps it in a `Message`, and publishes it — the single method responsible for the overwhelming majority of all message-sending code in a Spring AMQP application.

## 2. Why & when

You reach for `convertAndSend` as the default way to publish, in preference to more manual approaches, whenever:

- **The payload is a plain Java object that should be serialized automatically** — an `Order`, a `Notification`, any domain object — letting the configured converter (typically JSON) handle serialization keeps business logic free of manual marshaling code.
- **The exchange and routing key are known at the call site** — the three-argument overload is the most explicit and most commonly used form, making the destination clear from reading the call itself rather than relying on a template-level default exchange configured elsewhere.
- **A default exchange is genuinely appropriate for a given template instance** — the two-argument overload (routing key only) is useful when a `RabbitTemplate` bean is dedicated to publishing to one particular exchange throughout its lifetime, configured once via `setExchange(...)` rather than repeated at every call site.

## 3. Core concept

Think of `convertAndSend` as handing a finished letter to a mail clerk who already knows how to fold it, put it in an envelope, and address it correctly, versus doing all of that yourself. You provide the letter's actual content (the Java object) and where it should go (exchange and routing key); the clerk (the configured `MessageConverter`) handles turning your content into the properly formatted envelope (the `Message` with serialized bytes and correct content-type headers) before it ever leaves your hands.

```java
@Service
public class OrderPublisher {

    private final RabbitTemplate rabbitTemplate;

    public OrderPublisher(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void publishOrderCreated(Order order) {
        rabbitTemplate.convertAndSend("order.exchange", "order.created", order);
    }
}
```

The `Order` object is handed directly to `convertAndSend`; the configured converter (elsewhere in configuration) determines exactly how it becomes bytes on the wire.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="convertAndSend takes exchange, routing key, and a plain object; internally it runs the object through the configured MessageConverter to produce a Message, then publishes it exactly like the lower-level send method would" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order order = ...</text>

  <line x1="200" y1="42" x2="270" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a13)"/>
  <rect x="270" y="20" width="150" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">convertAndSend(...)</text>

  <line x1="345" y1="65" x2="345" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a13)"/>
  <text x="345" y="82" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">internally: MessageConverter</text>

  <rect x="270" y="95" width="150" height="35" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Message (bytes)</text>

  <line x1="420" y1="112" x2="490" y2="112" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a13)"/>
  <rect x="490" y="90" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Published to broker</text>
</svg>

The object-to-bytes conversion happens transparently inside the single method call.

## 5. Runnable example

The scenario: publishing order events using different `convertAndSend` overloads, simulated with a plain in-memory model standing in for `RabbitTemplate.convertAndSend` and its converter step (no real RabbitMQ broker needed to demonstrate the overload distinctions and their appropriate use cases), starting with the three-argument form, then adding the two-argument default-exchange form for a dedicated template, then adding a scenario comparing both against a shared template used for multiple destinations to show why explicit exchange naming usually wins.

### Level 1 — Basic

```java
// ConvertAndSendDemo.java
public class ConvertAndSendDemo {
    record Order(String id, double amount) {}

    // Stand-in for RabbitTemplate.convertAndSend(exchange, routingKey, object).
    static void convertAndSend(String exchange, String routingKey, Object payload) {
        Order order = (Order) payload;
        String serialized = "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
        System.out.println("Published to exchange=" + exchange + " key=" + routingKey + " body=" + serialized);
    }

    public static void main(String[] args) {
        convertAndSend("order.exchange", "order.created", new Order("ORD-1", 42.50));
    }
}
```

How to run: `java ConvertAndSendDemo.java`. Expected output: `Published to exchange=order.exchange key=order.created body={"id":"ORD-1","amount":42.5}` — the most explicit, three-argument form naming both exchange and routing key at the call site.

### Level 2 — Intermediate

```java
// ConvertAndSendDemo.java
public class ConvertAndSendDemo {
    record Order(String id, double amount) {}

    // Real-world concern: a template dedicated to one exchange can use the shorter, two-argument
    // overload -- the exchange is configured once (via setExchange) rather than repeated at
    // every call site, appropriate when a RabbitTemplate bean serves exactly one purpose.
    static class DedicatedOrderTemplate {
        private final String defaultExchange;
        DedicatedOrderTemplate(String defaultExchange) { this.defaultExchange = defaultExchange; }

        void convertAndSend(String routingKey, Object payload) {
            Order order = (Order) payload;
            String serialized = "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
            System.out.println("Published to exchange=" + defaultExchange + " key=" + routingKey + " body=" + serialized);
        }
    }

    public static void main(String[] args) {
        DedicatedOrderTemplate orderTemplate = new DedicatedOrderTemplate("order.exchange");
        orderTemplate.convertAndSend("order.created", new Order("ORD-1", 42.50));
        orderTemplate.convertAndSend("order.shipped", new Order("ORD-1", 42.50));
    }
}
```

How to run: `java ConvertAndSendDemo.java`. Expected output: both sends target `exchange=order.exchange` automatically without repeating it at either call site — appropriate when this particular template instance is dedicated entirely to publishing order-related events to one specific exchange.

### Level 3 — Advanced

```java
// ConvertAndSendDemo.java
public class ConvertAndSendDemo {
    record Order(String id, double amount) {}
    record Notification(String message) {}

    // Production concern: a SHARED template used for multiple, unrelated destinations should
    // use the explicit exchange-naming overload -- relying on a "default exchange" here would
    // require constantly reconfiguring it, and risks accidentally publishing to the wrong
    // destination if the default was last set for a different purpose.
    static class SharedTemplate {
        void convertAndSend(String exchange, String routingKey, Object payload) {
            String serialized = payload instanceof Order o
                ? "{\"id\":\"" + o.id() + "\",\"amount\":" + o.amount() + "}"
                : "{\"message\":\"" + ((Notification) payload).message() + "\"}";
            System.out.println("Published to exchange=" + exchange + " key=" + routingKey + " body=" + serialized);
        }
    }

    public static void main(String[] args) {
        SharedTemplate sharedTemplate = new SharedTemplate();

        // Same template instance, two entirely unrelated destinations -- explicit naming avoids
        // any ambiguity or reliance on whatever "default exchange" happened to be set last.
        sharedTemplate.convertAndSend("order.exchange", "order.created", new Order("ORD-1", 42.50));
        sharedTemplate.convertAndSend("notification.exchange", "notification.sent", new Notification("Order confirmed"));
    }
}
```

How to run: `java ConvertAndSendDemo.java`. Expected output: two published lines, each targeting a completely different exchange and routing key, using the same shared template instance — demonstrating why the explicit three-argument overload is the safer, clearer default for any template that publishes to more than one logical destination.

## 6. Walkthrough

Trace a single `convertAndSend` call from Java object to wire-level message.

1. **Method call**: application code calls `rabbitTemplate.convertAndSend("order.exchange", "order.created", order)`, passing a plain `Order` object as the payload — no manual serialization anywhere in this call.
2. **Converter invoked internally**: `RabbitTemplate` internally delegates to its configured `MessageConverter` (card 0012), passing the `Order` object; the converter serializes it (commonly to JSON) and produces the raw bytes that will become the message body.
3. **MessageProperties populated**: the converter also sets appropriate `MessageProperties` (card 0004) on the resulting `Message` — most importantly, the content type (`application/json`, for a JSON converter), so a consumer on the other end knows how to deserialize it correctly.
4. **Message published**: with a complete `Message` object now assembled (body plus properties), `RabbitTemplate` calls its lower-level `send(exchange, routingKey, message)` internally — this is the same underlying mechanism the manual, low-level API from card 0007 uses directly, just invoked automatically here.
5. **Broker delivery**: the message travels to the broker exactly as any other AMQP message would, subject to whatever exchange type and bindings are configured for `order.exchange` — the routing behavior itself is entirely unaffected by whether the message was built via `convertAndSend` or manually.
6. **Consumer-side symmetry**: on the receiving end, a consumer using the equivalent `receiveAndConvert()` (or a `@RabbitListener` with automatic argument conversion, card 0022) reverses this process — reading the content type, selecting the appropriate converter, and deserializing the bytes back into an `Order` object, completing the round trip transparently.

```
rabbitTemplate.convertAndSend(exchange, routingKey, order)
  -> MessageConverter.toMessage(order) -> serialized bytes + MessageProperties (content type set)
    -> Message assembled -> internal send(exchange, routingKey, message)
      -> published to broker -> routed per exchange/binding configuration
        -> consumer deserializes back to Order via the matching converter
```

## 7. Gotchas & takeaways

> **Gotcha:** relying on a `RabbitTemplate`'s configured default exchange (via the two-argument `convertAndSend(routingKey, object)` overload) on a template instance shared across multiple, unrelated publishing responsibilities is a common source of "why did this go to the wrong exchange" bugs — the default exchange is a single, mutable property on the template, and any code path that changes it (even temporarily, for a special case) affects every subsequent call using the short-form overload until it's reset.

- Prefer the explicit three-argument `convertAndSend(exchange, routingKey, object)` overload as the default habit — it makes every call self-contained and unambiguous, regardless of what else might be sharing the same template instance.
- The two-argument, default-exchange overload is reasonable specifically for a `RabbitTemplate` bean genuinely dedicated to one exchange for its entire lifecycle — a narrower and less common case than it might first appear.
- Whatever `MessageConverter` is configured drives both the serialization format and the resulting content-type header — consistency between what a producer's template is configured with and what a consumer's template (or listener) expects is essential, since a mismatch surfaces as a deserialization failure on the consuming side, not at publish time.
- `convertAndSend` accepting an optional `MessagePostProcessor` argument (card 0013) is the standard extension point for last-moment message customization — setting a custom header, adjusting an expiration, or similar per-message tweaks — without needing to abandon the convenience of automatic object conversion.
