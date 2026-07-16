---
card: spring-amqp
gi: 13
slug: messagepostprocessor
title: "MessagePostProcessor"
---

## 1. What it is

`MessagePostProcessor` is a functional interface (`Message postProcessMessage(Message message)`) that lets application code modify a `Message` after the configured `MessageConverter` has already produced it, but immediately before it's sent (or, on the receiving side, immediately after it's received). It's the standard extension point for setting things a converter alone doesn't handle — custom headers, expiration, priority — without abandoning the convenience of `convertAndSend`'s automatic object serialization.

## 2. Why & when

You reach for a `MessagePostProcessor` whenever a message needs adjustment that's orthogonal to its actual payload conversion:

- **Setting a per-message expiration or priority** — these are `MessageProperties` settings unrelated to how the payload itself is serialized; a post-processor is the clean place to set them without hand-building the entire `Message` manually just for this one property.
- **Adding a custom header derived from context outside the payload object itself** — a tenant ID, a trace ID pulled from the current request context, or an environment tag can be added to the message's headers via a post-processor, keeping this cross-cutting concern out of the domain object being serialized.
- **Compression or encryption of the message body** — a post-processor can transform the already-serialized bytes (compress them, encrypt them) after conversion but before sending, layering a transport-level concern on top of the payload's own serialization without polluting the domain object with knowledge of compression or encryption.

## 3. Core concept

Think of the `MessageConverter` as a factory that packages your product into a standard box (serializing the object into message bytes), and the `MessagePostProcessor` as the last worker on the loading dock who applies a shipping label, a "fragile" sticker, or a special "expires by" stamp onto that already-packed box right before it goes onto the truck — the box's contents are already finalized by this point; the post-processor only touches the box's exterior markings (the message's properties and headers), never reaching back inside to change what was actually packed.

```java
public void publishUrgentOrder(Order order) {
    rabbitTemplate.convertAndSend("order.exchange", "order.created", order, message -> {
        message.getMessageProperties().setPriority(9);
        message.getMessageProperties().setExpiration("30000"); // milliseconds, as a string
        message.getMessageProperties().setHeader("tenant-id", currentTenantContext.getTenantId());
        return message;
    });
}
```

The `Order` object is converted to a `Message` exactly as usual; the lambda then adjusts that already-built `Message`'s properties before it's actually sent.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A MessagePostProcessor runs after the MessageConverter has already produced a Message, adjusting properties and headers on it before the final send, without touching the already-serialized body" >
  <rect x="20" y="20" width="160" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order object</text>

  <line x1="180" y1="42" x2="240" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a14)"/>
  <rect x="240" y="20" width="160" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MessageConverter</text>

  <line x1="400" y1="42" x2="460" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a14)"/>
  <rect x="460" y="20" width="160" height="45" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MessagePostProcessor</text>

  <text x="540" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">adjusts properties/headers only --</text>
  <text x="540" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">body bytes already finalized by the converter</text>
</svg>

The post-processor is the last stop before sending, touching only the message's exterior metadata.

## 5. Runnable example

The scenario: adjusting a message's priority, expiration, and tenant header without changing the underlying domain object, simulated with a plain in-memory model standing in for `Message`/`MessageProperties` and a post-processor function (no real RabbitMQ broker needed to demonstrate the post-processing step itself), starting with a basic header addition, then adding expiration and priority together, then adding a chain of multiple post-processors applied in sequence to show how independent concerns compose cleanly.

### Level 1 — Basic

```java
// MessagePostProcessorDemo.java
import java.util.*;
import java.util.function.*;

public class MessagePostProcessorDemo {
    static class MessageProperties {
        Map<String, Object> headers = new HashMap<>();
    }

    static class Message {
        byte[] body;
        MessageProperties properties = new MessageProperties();
        Message(byte[] body) { this.body = body; }
    }

    // Stand-in for a MessagePostProcessor: Message -> Message.
    static Message applyPostProcessor(Message message, Function<Message, Message> postProcessor) {
        return postProcessor.apply(message);
    }

    public static void main(String[] args) {
        Message message = new Message("{\"id\":\"ORD-1\"}".getBytes());

        message = applyPostProcessor(message, m -> {
            m.properties.headers.put("tenant-id", "tenant-42");
            return m;
        });

        System.out.println("Headers after post-processing: " + message.properties.headers);
    }
}
```

How to run: `java MessagePostProcessorDemo.java`. Expected output: `Headers after post-processing: {tenant-id=tenant-42}` — a header added to an already-converted message without touching its body.

### Level 2 — Intermediate

```java
// MessagePostProcessorDemo.java
import java.util.*;
import java.util.function.*;

public class MessagePostProcessorDemo {
    static class MessageProperties {
        Map<String, Object> headers = new HashMap<>();
        Integer priority;
        String expiration;
    }

    static class Message {
        byte[] body;
        MessageProperties properties = new MessageProperties();
        Message(byte[] body) { this.body = body; }
    }

    // Real-world concern: a single post-processor commonly sets several properties at once --
    // priority and expiration are both MessageProperties settings entirely unrelated to how the
    // body itself was serialized by the converter.
    static Message applyUrgentOrderPostProcessing(Message message) {
        message.properties.priority = 9;
        message.properties.expiration = "30000"; // milliseconds, expires if unconsumed that long
        message.properties.headers.put("tenant-id", "tenant-42");
        return message;
    }

    public static void main(String[] args) {
        Message message = new Message("{\"id\":\"ORD-1\"}".getBytes());
        message = applyUrgentOrderPostProcessing(message);

        System.out.println("Priority: " + message.properties.priority);
        System.out.println("Expiration (ms): " + message.properties.expiration);
        System.out.println("Headers: " + message.properties.headers);
        System.out.println("Body unchanged: " + new String(message.body));
    }
}
```

How to run: `java MessagePostProcessorDemo.java`. Expected output: `Priority: 9`, `Expiration (ms): 30000`, `Headers: {tenant-id=tenant-42}`, then `Body unchanged: {"id":"ORD-1"}` — three independent metadata adjustments applied together, with the already-serialized body left completely untouched throughout.

### Level 3 — Advanced

```java
// MessagePostProcessorDemo.java
import java.util.*;
import java.util.function.*;

public class MessagePostProcessorDemo {
    static class MessageProperties {
        Map<String, Object> headers = new HashMap<>();
        Integer priority;
        String expiration;
    }

    static class Message {
        byte[] body;
        MessageProperties properties = new MessageProperties();
        Message(byte[] body) { this.body = body; }
    }

    // Production concern: multiple, independent post-processors (added by different parts of
    // the application -- a tracing library adding a trace ID, a tenancy layer adding tenant
    // context, business logic setting priority) should compose cleanly in sequence, each only
    // touching its own concern without needing to know about the others.
    static Message applyChain(Message message, List<Function<Message, Message>> postProcessors) {
        Message current = message;
        for (Function<Message, Message> pp : postProcessors) {
            current = pp.apply(current);
        }
        return current;
    }

    public static void main(String[] args) {
        Function<Message, Message> addTraceId = m -> {
            m.properties.headers.put("trace-id", "trace-abc-123");
            return m;
        };
        Function<Message, Message> addTenantId = m -> {
            m.properties.headers.put("tenant-id", "tenant-42");
            return m;
        };
        Function<Message, Message> setUrgentPriority = m -> {
            m.properties.priority = 9;
            m.properties.expiration = "30000";
            return m;
        };

        Message message = new Message("{\"id\":\"ORD-1\"}".getBytes());
        message = applyChain(message, List.of(addTraceId, addTenantId, setUrgentPriority));

        System.out.println("Final headers: " + message.properties.headers);
        System.out.println("Final priority: " + message.properties.priority);
        System.out.println("Final expiration: " + message.properties.expiration);
    }
}
```

How to run: `java MessagePostProcessorDemo.java`. Expected output: `Final headers: {trace-id=trace-abc-123, tenant-id=tenant-42}`, `Final priority: 9`, `Final expiration: 30000` — three independently-defined post-processors, each responsible for one concern, composing cleanly into a single fully-adjusted message without any of them needing to know about the others' existence.

## 6. Walkthrough

Trace a message through conversion and post-processing on the way to being sent.

1. **Object conversion**: `convertAndSend(exchange, routingKey, order, postProcessor)` first runs the `Order` object through the configured `MessageConverter`, producing a `Message` with a serialized body and baseline properties (content type, at minimum) exactly as it would without any post-processor involved.
2. **Post-processor invoked**: immediately after conversion but before the actual network send, `RabbitTemplate` calls the supplied `MessagePostProcessor`'s `postProcessMessage(message)` method, passing the already-built `Message`.
3. **Properties adjusted**: the post-processor's logic reads and modifies whatever it needs on `message.getMessageProperties()` — priority, expiration, custom headers — and returns the (typically same, mutated) `Message` object.
4. **Chaining multiple concerns**: when several independent post-processors need to apply (tracing, tenancy, business-specific settings), they can be composed in sequence, each handling its own concern without needing awareness of what the others already did or will do — as demonstrated in Level 3.
5. **Final send**: once every configured post-processor has run, the now-fully-adjusted `Message` is sent to the broker exactly as it would be without any post-processing — the post-processing step is purely a customization layered onto the normal `convertAndSend` flow, not a separate sending mechanism.
6. **Receiving side (symmetric capability)**: `MessagePostProcessor` can also be applied on the receiving side (via `RabbitTemplate.receive(...)` overloads accepting a post-processor), letting a consumer inspect or adjust a `Message`'s properties immediately after receipt, before any object conversion happens — a less commonly used but available symmetric capability.

```
order object -> MessageConverter -> Message (body + baseline properties)
  -> MessagePostProcessor #1 (e.g. add trace-id header)
    -> MessagePostProcessor #2 (e.g. add tenant-id header)
      -> MessagePostProcessor #3 (e.g. set priority + expiration)
        -> final Message -> actually sent to broker
```

## 7. Gotchas & takeaways

> **Gotcha:** a `MessagePostProcessor` that returns a *different* `Message` object than the one it was given (rather than mutating and returning the same instance) is perfectly valid per the interface contract, but forgetting to actually `return` anything (or accidentally returning `null`) silently breaks the send — always ensure a post-processor returns a genuine, non-null `Message`, since the compiler won't catch a logic mistake here the way it would a type error.

- `MessagePostProcessor` is the right tool for anything that belongs on the message's properties/headers rather than in the payload object itself — mixing cross-cutting metadata (tracing, tenancy) into the domain object being serialized would pollute that object with concerns unrelated to its actual business meaning.
- Multiple post-processors compose cleanly in sequence specifically because each one only touches its own narrow concern — this is a deliberate design pattern worth following in custom post-processors, rather than writing one large post-processor that tries to handle several unrelated adjustments at once.
- Because a post-processor runs after conversion, it has access to the fully-formed `Message` (including whatever content type and baseline properties the converter already set) — useful when a post-processor's logic needs to know the payload's serialized size or content type to make its own decision (compressing only above a certain size threshold, for instance).
- The receiving-side use of `MessagePostProcessor` is less common in everyday application code than the sending-side use, but exists for symmetric reasons — inspecting or adjusting message properties immediately upon receipt, before any object deserialization happens.
