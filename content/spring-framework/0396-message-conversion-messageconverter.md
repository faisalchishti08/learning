---
card: spring-framework
gi: 396
slug: message-conversion-messageconverter
title: "Message conversion (MessageConverter)"
---

## 1. What it is

`MessageConverter` (in the JMS package, `org.springframework.jms.support.converter.MessageConverter`) is the interface that translates between plain Java objects and JMS `Message` objects. `JmsTemplate` uses one on the way out (`toMessage`) whenever you call `convertAndSend`, and `@JmsListener` uses one on the way in (`fromMessage`) to turn a raw JMS `Message` into the typed parameter your listener method expects.

```java
public interface MessageConverter {
    Message toMessage(Object object, Session session) throws JMSException, MessageConversionException;
    Object fromMessage(Message message) throws JMSException, MessageConversionException;
}
```

## 2. Why & when

JMS itself only understands a handful of low-level message types — `TextMessage`, `BytesMessage`, `ObjectMessage`, `MapMessage` — none of which are your domain objects. Without a converter, every producer and consumer would need to manually serialize and parse those message bodies, duplicating the same boilerplate at every send and receive call. `MessageConverter` centralizes that translation once, so the rest of your code deals only in domain types (`OrderPlaced`, `PaymentReceived`, ...).

Spring ships a few implementations:

- **`SimpleMessageConverter`** (the default) — handles `String` ↔ `TextMessage`, `byte[]` ↔ `BytesMessage`, `Map` ↔ `MapMessage`, and `Serializable` ↔ `ObjectMessage`. Works out of the box but ties consumers to Java's native serialization for arbitrary objects, which is fragile across versions and languages.
- **`MappingJackson2MessageConverter`** — serializes objects to/from JSON `TextMessage`s using Jackson, the same library Spring MVC uses for REST payloads. This is the practical default for most modern applications, since JSON is language-neutral and human-readable on the wire.
- **`MarshallingMessageConverter`** — delegates to a JAXB or other `Marshaller`/`Unmarshaller` for XML payloads, useful when integrating with systems that require XML.

Choose `MappingJackson2MessageConverter` unless you have a specific reason (XML integration contracts, legacy Java-only consumers) to use something else.

## 3. Core concept

```
 Send side:                              Receive side:
 OrderPlaced (Java object)               TextMessage (on the wire)
       |                                        |
       v                                        v
 converter.toMessage(order, session)     converter.fromMessage(message)
       |                                        |
       v                                        v
 TextMessage{ body: '{"orderId":...}' }   OrderPlaced (Java object)
```

The same converter instance is configured on both `JmsTemplate` (send) and the listener container factory (receive) — using different converters on each side would mean producers and consumers speak different wire formats.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Object serialized to JMS message on send, deserialized back to object on receive">
  <rect x="10" y="30" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderPlaced object</text>

  <rect x="245" y="30" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TextMessage (JSON)</text>

  <rect x="480" y="30" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderPlaced object</text>

  <line x1="160" y1="53" x2="240" y2="53" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="200" y="45" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">toMessage</text>

  <line x1="395" y1="53" x2="475" y2="53" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="435" y="45" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">fromMessage</text>

  <text x="320" y="120" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">the broker only ever sees/stores the middle box</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Both endpoints agree on the same converter, so the broker's opaque byte payload round-trips correctly.

## 5. Runnable example

### Level 1 — Basic

Compare the default `SimpleMessageConverter` against `MappingJackson2MessageConverter` outside of any broker, just by calling `toMessage`/`fromMessage` directly against an in-memory fake session — showing exactly what each produces.

```java
import jakarta.jms.Session;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.SimpleMessageConverter;

import java.io.Serializable;

public class ConverterBasic {

    record OrderPlaced(String orderId, int quantity) implements Serializable {}

    public static void main(String[] args) throws Exception {
        var connectionFactory = new ActiveMQJMSConnectionFactory("vm://0");
        try (var connection = connectionFactory.createConnection()) {
            Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);

            var simple = new SimpleMessageConverter();
            var simpleMessage = simple.toMessage(new OrderPlaced("order-1", 2), session);
            System.out.println("SimpleMessageConverter -> " + simpleMessage.getClass().getSimpleName());

            var jackson = new MappingJackson2MessageConverter();
            var jacksonMessage = jackson.toMessage(new OrderPlaced("order-1", 2), session);
            System.out.println("Jackson -> " + jacksonMessage.getClass().getSimpleName()
                    + " body=" + jacksonMessage.getBody(String.class));
        }
    }
}
```

How to run: add `spring-jms`, Jackson, and an embedded broker dependency (e.g. Artemis), then `java ConverterBasic.java`.

`SimpleMessageConverter` turns a `Serializable` record into an `ActiveMQObjectMessage` — the JVM's native object serialization, opaque bytes only another Java process with the same class on its classpath can read. `MappingJackson2MessageConverter` turns the same record into a `TextMessage` containing a readable JSON string — inspectable in any broker admin console and consumable by non-Java clients.

### Level 2 — Intermediate

Wire the Jackson converter into a real `JmsTemplate`/`@JmsListener` round trip and inspect the actual JSON on the wire by also reading it with a plain listener.

```java
import jakarta.jms.ConnectionFactory;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.jms.annotation.EnableJms;
import org.springframework.jms.annotation.JmsListener;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageType;

import java.io.Serializable;

public class ConverterIntermediate {

    record OrderPlaced(String orderId, int quantity) implements Serializable {}

    @Configuration
    @EnableJms
    static class Config {
        @Bean
        ConnectionFactory connectionFactory() { return new ActiveMQJMSConnectionFactory("vm://0"); }

        @Bean
        MappingJackson2MessageConverter converter() {
            var c = new MappingJackson2MessageConverter();
            c.setTargetType(MessageType.TEXT);
            c.setTypeIdPropertyName("_type");   // JSON field carrying the target Java type
            return c;
        }

        @Bean
        JmsTemplate jmsTemplate(ConnectionFactory cf, MappingJackson2MessageConverter conv) {
            var template = new JmsTemplate(cf);
            template.setMessageConverter(conv);
            return template;
        }
    }

    @org.springframework.stereotype.Component
    static class Listener {
        @JmsListener(destination = "orders.queue")
        void onOrder(OrderPlaced order) {
            System.out.println("Typed listener got: " + order);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(Config.class, Listener.class);
        context.getBean(JmsTemplate.class).convertAndSend("orders.queue", new OrderPlaced("order-2", 5));
        Thread.sleep(500);
        context.close();
    }
}
```

How to run: same dependencies as Level 1, then `java ConverterIntermediate.java`.

`setTypeIdPropertyName("_type")` tells the converter to embed the fully-qualified target class name as a JSON field (`_type`) inside the message body — that's how `fromMessage` knows to deserialize into `OrderPlaced` specifically rather than a generic `Map`, without you writing any manual type-lookup code.

### Level 3 — Advanced

A converter that only speaks Jackson breaks the moment a non-Java or legacy system needs to read the same queue with its own JSON parser that doesn't understand `_type`. Production integrations often need a converter that omits Java-specific type metadata and instead maps message body to a target type based on the JMS message's own `type` header — decoupling the wire format from Java class names entirely.

```java
import jakarta.jms.ConnectionFactory;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.jms.annotation.EnableJms;
import org.springframework.jms.annotation.JmsListener;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.core.MessagePostProcessor;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageType;

import java.io.Serializable;
import java.util.Map;

public class ConverterAdvanced {

    record OrderPlaced(String orderId, int quantity) implements Serializable {}

    @Configuration
    @EnableJms
    static class Config {
        @Bean
        ConnectionFactory connectionFactory() { return new ActiveMQJMSConnectionFactory("vm://0"); }

        @Bean
        MappingJackson2MessageConverter converter() {
            var c = new MappingJackson2MessageConverter();
            c.setTargetType(MessageType.TEXT);
            // No Java-class type metadata on the wire: language-neutral payload.
            c.setTypeIdMappings(Map.of("order-placed", OrderPlaced.class));
            c.setTypeIdPropertyName("eventType");
            return c;
        }

        @Bean
        JmsTemplate jmsTemplate(ConnectionFactory cf, MappingJackson2MessageConverter conv) {
            var template = new JmsTemplate(cf);
            template.setMessageConverter(conv);
            return template;
        }
    }

    @org.springframework.stereotype.Component
    static class Listener {
        @JmsListener(destination = "orders.queue")
        void onOrder(OrderPlaced order) {
            System.out.println("Portable listener got: " + order);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(Config.class, Listener.class);
        JmsTemplate jmsTemplate = context.getBean(JmsTemplate.class);

        MessagePostProcessor addEventType = message -> {
            message.setStringProperty("eventType", "order-placed");
            return message;
        };
        jmsTemplate.convertAndSend("orders.queue", new OrderPlaced("order-3", 1), addEventType);

        Thread.sleep(500);
        context.close();
    }
}
```

How to run: same dependencies as Level 1, then `java ConverterAdvanced.java`.

`setTypeIdMappings(Map.of("order-placed", OrderPlaced.class))` decouples the on-the-wire type token (`"order-placed"`, a stable business name) from the Java class name (`OrderPlaced`, which could be refactored or renamed without breaking older consumers). `MessagePostProcessor` runs after conversion but before sending, letting you stamp the `eventType` property that a non-Java consumer could use to pick a parser — this is the same `MessagePostProcessor` mechanism you'd use to set any custom JMS header.

## 6. Walkthrough

Trace `ConverterAdvanced.main`:

1. **Send call.** `jmsTemplate.convertAndSend("orders.queue", new OrderPlaced("order-3", 1), addEventType)` first hands the `OrderPlaced` record to the configured `MappingJackson2MessageConverter`.
2. **Conversion (`toMessage`).** The converter serializes the record to JSON and, because a `typeIdMappings`/`typeIdPropertyName` are configured, adds an `eventType` field with value `"order-placed"` (the mapped token, not the Java class name) into the JSON body itself — producing a `TextMessage`.
3. **Post-processing.** The `MessagePostProcessor` then runs against that already-built `TextMessage`, adding a JMS *header* property `eventType=order-placed` (in addition to the JSON field of the same name) — useful because JMS headers can be used in broker-side message selectors without parsing the body.
4. **Publish.** The finished `TextMessage` is sent to `orders.queue`:

   ```
   TextMessage on orders.queue:
     header:  eventType = "order-placed"
     body:    {"eventType":"order-placed","orderId":"order-3","quantity":1}
   ```
5. **Delivery.** The listener container's consumer thread receives this `TextMessage` and hands it to the same `MappingJackson2MessageConverter` bean's `fromMessage`.
6. **Conversion back (`fromMessage`).** The converter reads the `eventType` field from the JSON body, looks it up in `typeIdMappings`, finds `OrderPlaced.class`, and deserializes the rest of the JSON into a new `OrderPlaced` record.
7. **Listener invocation.** `onOrder(order)` runs with the reconstructed `OrderPlaced("order-3", 1)`, printing it — the listener code never touched JSON, JMS headers, or type tokens directly; all of that lived in the converter configuration.

```
OrderPlaced record
   -> Jackson converter -> JSON TextMessage (with eventType field)
   -> MessagePostProcessor -> + eventType header
   -> broker -> listener container
   -> Jackson converter (fromMessage, reads eventType) -> OrderPlaced record
   -> onOrder(order)
```

## 7. Gotchas & takeaways

> Gotcha: the default `SimpleMessageConverter` serializes arbitrary objects via `ObjectMessage`, which uses raw Java serialization — this is not just a format concern but a security one, since deserializing an `ObjectMessage` from an untrusted or compromised producer can execute arbitrary code via deserialization gadget chains. Prefer a JSON-based converter (`MappingJackson2MessageConverter`) for anything beyond a trusted, fully-Java, tightly-controlled system.

- Configure the *same* `MessageConverter` bean on both the sending `JmsTemplate` and the receiving listener container factory — mismatched converters on either end are a common source of `MessageConversionException` at runtime.
- Prefer `MappingJackson2MessageConverter` for new integrations: it's human-readable, broker-tool-friendly, and doesn't require the consumer to be Java.
- Use `typeIdMappings` with a stable string token instead of the raw Java class name whenever another team or system might consume the same queue — it decouples your wire contract from your internal class naming and package structure.
- `MessagePostProcessor` is the right hook for adding JMS headers or properties (for broker-side message selectors, correlation IDs, priorities) without polluting the JSON body itself.
