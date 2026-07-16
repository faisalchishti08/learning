---
card: spring-amqp
gi: 7
slug: amqptemplate-rabbittemplate
title: "AmqpTemplate / RabbitTemplate"
---

## 1. What it is

`AmqpTemplate` is the broker-agnostic interface (from `spring-amqp`, card 0003) for sending and receiving messages, and `RabbitTemplate` is its RabbitMQ-specific implementation — the single most commonly used class in Spring AMQP applications. It provides both low-level methods (`send(Message)`) working directly with the `Message`/`MessageProperties` abstraction (card 0004), and high-level convenience methods (`convertAndSend(Object)`, `receiveAndConvert()`) that automatically serialize and deserialize plain Java objects using a configured `MessageConverter`, so most application code never touches raw bytes at all.

## 2. Why & when

You reach for `RabbitTemplate` for essentially all synchronous, template-style interaction with RabbitMQ:

- **Publishing a message from application code** — `convertAndSend(exchange, routingKey, object)` is the standard way to publish, letting the template's configured converter handle turning a Java object into message bytes without manual serialization code cluttering business logic.
- **Synchronous request/reply messaging** — `convertSendAndReceive(...)` publishes a message and blocks waiting for a correlated reply, useful when a caller genuinely needs a response before proceeding, unlike the fire-and-forget pattern of a plain send.
- **Direct synchronous receive (as an alternative to the listener-container-based asynchronous consumption covered in the messaging patterns section)** — `receiveAndConvert(queueName)` pulls a single message on demand, useful for polling-style consumption or administrative/debugging tasks rather than continuous, high-throughput consuming.

## 3. Core concept

Think of `RabbitTemplate` like a full-service delivery counter at a shipping company: you can hand over a raw, already-packed box yourself (the low-level `send(Message)` method) if you want full control over exactly how it's packed and labeled, or you can just hand over the item you want shipped and let the counter staff pack, label, and ship it for you (the high-level `convertAndSend(Object)` method, using a configured converter behind the scenes) — same destination and delivery mechanism either way, different levels of involvement in the packing details.

```java
@Autowired
private RabbitTemplate rabbitTemplate;

// High-level: converter handles serialization automatically
public void publishOrder(Order order) {
    rabbitTemplate.convertAndSend("order.exchange", "order.created", order);
}

// Low-level: full manual control over the Message and its properties
public void publishRawOrder(Order order, byte[] serializedBytes) {
    MessageProperties props = new MessageProperties();
    props.setContentType(MessageProperties.CONTENT_TYPE_JSON);
    rabbitTemplate.send("order.exchange", "order.created", new Message(serializedBytes, props));
}
```

Both methods ultimately produce the same kind of `Message` on the wire; the high-level method just handles the conversion step automatically.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RabbitTemplate offers a high-level convertAndSend path that auto-converts a Java object, and a low-level send path working directly with Message and MessageProperties, both ultimately producing the same wire-level AMQP message" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">High-level: convertAndSend(Object)</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">Order order = new Order(...)</text>
  <text x="35" y="65" fill="#79c0ff" font-size="7" font-family="monospace">MessageConverter serializes it</text>
  <text x="35" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">application code stays object-focused</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Low-level: send(Message)</text>
  <text x="355" y="45" fill="#e6edf3" font-size="7" font-family="monospace">new MessageProperties() ...</text>
  <text x="355" y="65" fill="#e6edf3" font-size="7" font-family="monospace">new Message(bytes, props)</text>
  <text x="355" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">full manual control, more boilerplate</text>
</svg>

Both paths reach the same wire format; the high-level path just automates the conversion step.

## 5. Runnable example

The scenario: publishing an order both ways and performing a synchronous request/reply exchange, simulated with a plain in-memory model standing in for `RabbitTemplate` (no real RabbitMQ broker needed to demonstrate the high-level-versus-low-level API distinction and the request/reply pattern), starting with a basic high-level convert-and-send, then adding the equivalent low-level send for comparison, then adding a synchronous request/reply exchange.

### Level 1 — Basic

```java
// RabbitTemplateDemo.java
public class RabbitTemplateDemo {
    record Order(String id, double amount) {}

    // Stand-in for RabbitTemplate.convertAndSend(exchange, routingKey, object).
    static void convertAndSend(String exchange, String routingKey, Object payload) {
        String serialized = "{\"id\":\"" + ((Order) payload).id() + "\",\"amount\":" + ((Order) payload).amount() + "}";
        System.out.println("[convertAndSend] exchange=" + exchange + " key=" + routingKey + " body=" + serialized);
    }

    public static void main(String[] args) {
        convertAndSend("order.exchange", "order.created", new Order("ORD-1", 42.50));
    }
}
```

How to run: `java RabbitTemplateDemo.java`. Expected output: `[convertAndSend] exchange=order.exchange key=order.created body={"id":"ORD-1","amount":42.5}` — a plain Java object published without any manual serialization code in the caller.

### Level 2 — Intermediate

```java
// RabbitTemplateDemo.java
import java.util.*;

public class RabbitTemplateDemo {
    record Order(String id, double amount) {}
    record MessageProperties(String contentType, Map<String, Object> headers) {}
    record Message(byte[] body, MessageProperties properties) {}

    static void convertAndSend(String exchange, String routingKey, Object payload) {
        String serialized = "{\"id\":\"" + ((Order) payload).id() + "\",\"amount\":" + ((Order) payload).amount() + "}";
        System.out.println("[convertAndSend] exchange=" + exchange + " key=" + routingKey + " body=" + serialized);
    }

    // Real-world concern: the low-level path is what convertAndSend does internally --
    // seeing it explicitly clarifies what the high-level method is automating away.
    static void send(String exchange, String routingKey, Message message) {
        System.out.println("[send] exchange=" + exchange + " key=" + routingKey
            + " contentType=" + message.properties().contentType()
            + " body=" + new String(message.body()));
    }

    public static void main(String[] args) {
        convertAndSend("order.exchange", "order.created", new Order("ORD-1", 42.50));

        // The manual equivalent: build the Message yourself instead of letting a converter do it.
        String serialized = "{\"id\":\"ORD-1\",\"amount\":42.5}";
        MessageProperties props = new MessageProperties("application/json", Map.of());
        send("order.exchange", "order.created", new Message(serialized.getBytes(), props));
    }
}
```

How to run: `java RabbitTemplateDemo.java`. Expected output: two lines showing the same effective destination, routing key, and body content, one produced automatically by `convertAndSend`, the other built manually via `send` — demonstrating that both API levels ultimately produce the same wire-level result, differing only in how much serialization work the caller does explicitly.

### Level 3 — Advanced

```java
// RabbitTemplateDemo.java
import java.util.concurrent.*;

public class RabbitTemplateDemo {
    record Order(String id, double amount) {}
    record PriceQuote(String orderId, double quotedPrice) {}

    // Production concern: convertSendAndReceive blocks the caller until a correlated reply
    // arrives (or times out) -- modeled here with a CompletableFuture standing in for the
    // request/reply correlation RabbitTemplate performs internally via a temporary reply queue.
    static PriceQuote convertSendAndReceive(String exchange, String routingKey, Order order, long timeoutMillis)
            throws Exception {
        CompletableFuture<PriceQuote> replyFuture = CompletableFuture.supplyAsync(() -> {
            System.out.println("[request] published order " + order.id() + " to " + exchange + "/" + routingKey);
            try { Thread.sleep(100); } catch (InterruptedException ignored) {}
            System.out.println("[reply] pricing service responded");
            return new PriceQuote(order.id(), order.amount() * 1.08); // simulated tax calculation reply
        });
        return replyFuture.get(timeoutMillis, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) throws Exception {
        Order order = new Order("ORD-1", 42.50);
        PriceQuote quote = convertSendAndReceive("pricing.exchange", "price.quote.request", order, 1000);
        System.out.println("Received quote: orderId=" + quote.orderId() + ", quotedPrice=" + quote.quotedPrice());
    }
}
```

How to run: `java RabbitTemplateDemo.java`. Expected output: `[request] published order ORD-1 ...`, then `[reply] pricing service responded`, then `Received quote: orderId=ORD-1, quotedPrice=45.9` — the caller blocks until the correlated reply arrives, exactly the synchronous request/reply pattern `convertSendAndReceive` provides over what is, under the hood, still an asynchronous messaging protocol.

## 6. Walkthrough

Trace a request/reply exchange through `RabbitTemplate`, contrasting it with a plain publish.

1. **Plain publish (fire-and-forget)**: `convertAndSend(exchange, routingKey, order)` serializes the order using the configured `MessageConverter`, builds a `Message`, and sends it — the calling thread continues immediately afterward with no expectation of any reply.
2. **Request/reply setup**: `convertSendAndReceive(exchange, routingKey, order)` does the same publish, but first sets up a temporary, exclusive reply queue (or uses a configured direct-reply-to mechanism) and attaches a correlation ID to the outgoing message's properties.
3. **Request published**: the message goes out exactly as with a plain send, but the correlation ID travels with it, letting whatever consumes and replies to it know which reply queue and correlation ID to use for the response.
4. **Calling thread blocks**: the calling thread waits (up to a configured timeout) for a reply message to arrive on that temporary reply queue with the matching correlation ID — this is where the synchronous feel comes from, layered over what is, underneath, still an asynchronous publish/consume mechanism.
5. **Reply arrives and is correlated**: once a reply with the matching correlation ID arrives, `RabbitTemplate` matches it to the waiting caller and returns the deserialized reply object (via the same `MessageConverter` used for sending) from the blocked call.
6. **Timeout handling**: if no reply arrives within the configured timeout, the call returns `null` (or throws, depending on configuration) rather than blocking indefinitely — a caller relying on request/reply needs to handle this "no answer came back" case explicitly.

```
convertSendAndReceive(exchange, routingKey, order)
  -> set up temporary reply queue + correlation ID
    -> publish request message (with correlation ID attached)
      -> calling thread BLOCKS, waiting for a matching reply
        -> [elsewhere] consumer processes request, publishes reply with same correlation ID
          -> RabbitTemplate matches reply to waiting caller -> returns deserialized reply
             (or: timeout elapses -> null / exception)
```

## 7. Gotchas & takeaways

> **Gotcha:** `convertSendAndReceive` blocks the calling thread for up to its configured timeout — using it inside a high-throughput, latency-sensitive code path (rather than reserving it for genuinely synchronous use cases) can tie up threads waiting on replies in a way that a purely asynchronous publish-and-continue pattern never would; reach for it deliberately, not as the default way to interact with a queue.

- `convertAndSend`/`convertSendAndReceive` cover the vast majority of real application code; reach for the lower-level `send`/`receive` methods working directly with `Message` only when fine-grained control over properties or the body's exact byte representation is genuinely needed.
- The `MessageConverter` configured on the `RabbitTemplate` (commonly a JSON converter) determines both how outgoing objects are serialized and how incoming replies are deserialized — a mismatch between what a producer sends and what a converter expects to receive is a common source of deserialization errors that surface at runtime, not compile time.
- Because `RabbitTemplate` is thread-safe and designed to be a shared, long-lived bean (much like `CachingConnectionFactory` underneath it), inject and reuse a single instance across the application rather than constructing new ones per operation.
- Request/reply over AMQP, while convenient via `convertSendAndReceive`, reintroduces some of the tight coupling and latency AMQP's usual asynchronous model avoids — use it where a genuine synchronous answer is required, and prefer plain asynchronous publish/consume patterns everywhere else for better throughput and looser coupling.
