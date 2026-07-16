---
card: spring-amqp
gi: 4
slug: message-abstraction-message-messageproperties
title: "Message abstraction (Message, MessageProperties)"
---

## 1. What it is

Spring AMQP's `Message` class is a simple wrapper pairing a raw `byte[]` body with a `MessageProperties` object carrying metadata — content type, content encoding, headers, delivery mode, priority, correlation ID, and more. Every message that goes over the wire to or from RabbitMQ is, at the framework level, represented this way; higher-level conveniences like `RabbitTemplate.convertAndSend(Object)` (covered in card 0007) sit on top of this, converting a Java object to a `Message` (and back) automatically, but the `Message`/`MessageProperties` pair is the actual wire-level representation underneath.

## 2. Why & when

You work directly with `Message` and `MessageProperties` when the byte-level or metadata-level details matter more than automatic object conversion:

- **Setting or reading custom headers for routing or tracing** — a correlation ID for distributed tracing, or a custom header a headers exchange (card 0002) matches on, needs to be set explicitly on `MessageProperties` rather than relying on whatever a generic object-to-JSON converter happens to produce.
- **Controlling delivery mode explicitly** — choosing persistent versus non-persistent delivery (whether the broker should survive a restart with the message intact) is a `MessageProperties` setting, not something inferred from the payload type.
- **Working with a payload that isn't a plain Java object needing conversion** — receiving raw bytes (a binary file, a pre-serialized protocol buffer) and wanting direct access to those bytes without an automatic converter interfering.

## 3. Core concept

Think of a `Message` like a physical parcel: the `body` is whatever's inside the box (raw bytes, whatever they represent), and `MessageProperties` is everything written on the shipping label stuck to the outside — sender, tracking number, "fragile" or "priority" stickers (headers), and whether it needs signature confirmation (delivery mode). The postal system (the broker) only ever looks at the label to make routing and handling decisions; it never opens the box to inspect what's inside, which is exactly why routing and delivery guarantees live on `MessageProperties` rather than depending on the payload's actual content.

```java
MessageProperties properties = new MessageProperties();
properties.setContentType(MessageProperties.CONTENT_TYPE_JSON);
properties.setDeliveryMode(MessageDeliveryMode.PERSISTENT);
properties.setCorrelationId("req-12345");
properties.setHeader("region", "us");

Message message = new Message("{\"orderId\":\"ORD-1\"}".getBytes(StandardCharsets.UTF_8), properties);
rabbitTemplate.send("order.exchange", "order.created", message);
```

The routing key (`"order.created"`) determines which queue this reaches; the `region` header is a separate piece of metadata a headers exchange, or downstream consumer logic, could act on independently.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Message pairs a raw byte array body with MessageProperties metadata such as content type, delivery mode, correlation ID, and custom headers, similar to a parcel and its shipping label" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Message.body (byte[])</text>
  <text x="35" y="50" fill="#e6edf3" font-size="8" font-family="monospace">{"orderId":"ORD-1"}</text>
  <text x="35" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">opaque bytes to the broker --</text>
  <text x="35" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">never inspected for routing</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MessageProperties (the "label")</text>
  <text x="355" y="42" fill="#e6edf3" font-size="7" font-family="monospace">contentType: application/json</text>
  <text x="355" y="60" fill="#e6edf3" font-size="7" font-family="monospace">deliveryMode: PERSISTENT</text>
  <text x="355" y="78" fill="#e6edf3" font-size="7" font-family="monospace">correlationId: req-12345</text>
  <text x="355" y="96" fill="#79c0ff" font-size="7" font-family="monospace">headers: {region: us}</text>
</svg>

The broker acts entirely on the "label"; the "contents" are opaque bytes it never inspects.

## 5. Runnable example

The scenario: building and inspecting messages with different metadata configurations, simulated with a plain Java model of `Message`/`MessageProperties` (no real RabbitMQ connection needed to demonstrate the body/properties pairing itself), starting with a basic message construction, then adding custom headers used for a routing-like decision, then adding delivery-mode-aware handling to show how metadata drives broker behavior distinct from the payload content.

### Level 1 — Basic

```java
// MessagePropertiesDemo.java
import java.nio.charset.StandardCharsets;
import java.util.*;

public class MessagePropertiesDemo {
    static class MessageProperties {
        String contentType;
        Map<String, Object> headers = new HashMap<>();
    }

    static class Message {
        byte[] body;
        MessageProperties properties;
        Message(byte[] body, MessageProperties properties) { this.body = body; this.properties = properties; }
    }

    public static void main(String[] args) {
        MessageProperties props = new MessageProperties();
        props.contentType = "application/json";

        Message message = new Message("{\"orderId\":\"ORD-1\"}".getBytes(StandardCharsets.UTF_8), props);

        System.out.println("Content type: " + message.properties.contentType);
        System.out.println("Body: " + new String(message.body, StandardCharsets.UTF_8));
    }
}
```

How to run: `java MessagePropertiesDemo.java`. Expected output: `Content type: application/json` then `Body: {"orderId":"ORD-1"}` — the body and properties travel together as one `Message` but remain conceptually distinct pieces of information.

### Level 2 — Intermediate

```java
// MessagePropertiesDemo.java
import java.nio.charset.StandardCharsets;
import java.util.*;

public class MessagePropertiesDemo {
    static class MessageProperties {
        String contentType;
        String correlationId;
        Map<String, Object> headers = new HashMap<>();
    }

    static class Message {
        byte[] body;
        MessageProperties properties;
        Message(byte[] body, MessageProperties properties) { this.body = body; this.properties = properties; }
    }

    // Real-world concern: a custom header drives a downstream routing-like decision --
    // independent of the actual body content, which the broker/consumer logic here never parses.
    static String decideQueueByHeader(Message message) {
        Object region = message.properties.headers.get("region");
        if ("us".equals(region)) return "usOrdersQueue";
        if ("eu".equals(region)) return "euOrdersQueue";
        return "defaultOrdersQueue";
    }

    public static void main(String[] args) {
        MessageProperties props = new MessageProperties();
        props.contentType = "application/json";
        props.correlationId = "req-12345";
        props.headers.put("region", "eu");

        Message message = new Message("{\"orderId\":\"ORD-1\"}".getBytes(StandardCharsets.UTF_8), props);

        System.out.println("Correlation ID: " + message.properties.correlationId);
        System.out.println("Routed to: " + decideQueueByHeader(message));
    }
}
```

How to run: `java MessagePropertiesDemo.java`. Expected output: `Correlation ID: req-12345` then `Routed to: euOrdersQueue` — the routing decision made entirely from the `region` header, with the JSON body content never inspected at all for this decision.

### Level 3 — Advanced

```java
// MessagePropertiesDemo.java
import java.nio.charset.StandardCharsets;
import java.util.*;

public class MessagePropertiesDemo {
    enum DeliveryMode { PERSISTENT, NON_PERSISTENT }

    static class MessageProperties {
        String contentType;
        DeliveryMode deliveryMode = DeliveryMode.NON_PERSISTENT;
        Map<String, Object> headers = new HashMap<>();
    }

    static class Message {
        byte[] body;
        MessageProperties properties;
        Message(byte[] body, MessageProperties properties) { this.body = body; this.properties = properties; }
    }

    // Production concern: delivery mode determines whether a broker persists the message to
    // disk (surviving a restart) or keeps it in memory only -- a metadata decision entirely
    // separate from the payload, and one that trades durability against throughput.
    static class SimulatedBroker {
        List<Message> diskPersistedMessages = new ArrayList<>();
        List<Message> memoryOnlyMessages = new ArrayList<>();

        void enqueue(Message message) {
            if (message.properties.deliveryMode == DeliveryMode.PERSISTENT) {
                diskPersistedMessages.add(message);
                System.out.println("Persisted to disk (survives restart)");
            } else {
                memoryOnlyMessages.add(message);
                System.out.println("Kept in memory only (lost on restart)");
            }
        }

        void simulateRestart() {
            System.out.println("-- broker restarts --");
            System.out.println("Disk-persisted messages surviving restart: " + diskPersistedMessages.size());
            System.out.println("Memory-only messages surviving restart: " + 0); // lost
            memoryOnlyMessages.clear();
        }
    }

    public static void main(String[] args) {
        SimulatedBroker broker = new SimulatedBroker();

        MessageProperties criticalProps = new MessageProperties();
        criticalProps.deliveryMode = DeliveryMode.PERSISTENT;
        broker.enqueue(new Message("critical order data".getBytes(StandardCharsets.UTF_8), criticalProps));

        MessageProperties transientProps = new MessageProperties();
        transientProps.deliveryMode = DeliveryMode.NON_PERSISTENT;
        broker.enqueue(new Message("transient metric ping".getBytes(StandardCharsets.UTF_8), transientProps));

        broker.simulateRestart();
    }
}
```

How to run: `java MessagePropertiesDemo.java`. Expected output: `Persisted to disk (survives restart)` for the critical message, `Kept in memory only (lost on restart)` for the transient one, then after the simulated restart, `Disk-persisted messages surviving restart: 1` and `Memory-only messages surviving restart: 0` — demonstrating that delivery mode, a `MessageProperties` setting entirely independent of the payload's content, is what determines durability guarantees.

## 6. Walkthrough

Trace a message from construction through broker handling based purely on its properties.

1. **Construction**: application code builds a `MessageProperties` object, setting whatever metadata matters for this message — content type (so a consumer knows how to deserialize the body), delivery mode (durability), a correlation ID (tracing/request-matching), and any custom headers needed for routing or business logic.
2. **Body attachment**: the actual payload — already serialized to bytes, however that serialization happened (manually, or via a message converter as in card 0007) — is paired with those properties to form the complete `Message`.
3. **Send**: `RabbitTemplate.send(exchange, routingKey, message)` transmits both the body and the properties over the wire; the routing key (separate from the properties in the AMQP protocol itself, though conceptually related) determines which queue(s) the exchange routes this to.
4. **Broker-side handling based on properties, not body**: the broker reads `MessageProperties.deliveryMode` to decide whether to persist the message to disk; reads headers if a headers exchange is being used; and generally never parses or interprets the message body at all — it only moves those opaque bytes from producer to consumer.
5. **Consumer receives**: on the consuming side, the same `Message` object (body plus properties) arrives, and the consumer's logic reads whatever properties it needs (content type to choose a deserializer, correlation ID to match against an outstanding request, custom headers to make a processing decision) before finally interpreting the body bytes according to whatever format the content type indicates.
6. **Restart resilience determined entirely by delivery mode**: if the broker restarts before an unacknowledged, persistently-delivered message is consumed, that message survives and is redelivered; a non-persistent message in the same situation is simply gone — a distinction made entirely by the `deliveryMode` property, unrelated to what the message actually contained.

```
build MessageProperties (contentType, deliveryMode, correlationId, headers)
  -> pair with body bytes -> Message
    -> send(exchange, routingKey, message)
      -> broker reads properties (not body) for: persistence decision, header-based routing
        -> consumer receives Message -> reads properties to interpret body correctly
```

## 7. Gotchas & takeaways

> **Gotcha:** setting a custom header on `MessageProperties` and expecting a *direct* or *topic* exchange to route based on it is a common mistake — direct and topic exchanges route exclusively on the routing key; only a headers exchange (card 0002) reads header values for routing decisions, so a header set for one exchange type's routing purposes is silently ignored by another.

- `Message` and `MessageProperties` are the actual wire-level representation; higher-level conveniences like automatic object-to-JSON conversion (card 0007) are built on top of constructing these two objects correctly, not a separate mechanism.
- Delivery mode is a durability/performance trade-off made per message, not a global broker setting — high-volume, loss-tolerable messages (metrics, heartbeats) are reasonable candidates for non-persistent delivery, while anything requiring guaranteed delivery through a restart needs persistent delivery, generally paired with a durable queue.
- Content type on `MessageProperties` is metadata the *consumer* relies on to know how to interpret the body bytes — setting it accurately (and consistently between producer and consumer) avoids deserialization failures that are otherwise hard to diagnose from the broker side alone.
- Correlation IDs and custom headers are the primary mechanism for carrying request-tracing or business-routing metadata alongside a message without needing to embed that metadata inside the serialized payload itself, keeping the payload's shape focused purely on business data.
