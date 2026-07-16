---
card: spring-amqp
gi: 12
slug: messageconverter-simplemessageconverter-jackson2jsonmessagec
title: "MessageConverter (SimpleMessageConverter, Jackson2JsonMessageConverter)"
---

## 1. What it is

`MessageConverter` is the interface `convertAndSend`/`receiveAndConvert` delegate to for turning a Java object into message bytes and back. `SimpleMessageConverter` (the default if none is configured) handles `String`, `byte[]`, and `Serializable` Java objects using Java's built-in serialization for anything else — simple, but producing a Java-specific, not cross-language-friendly, wire format. `Jackson2JsonMessageConverter` is the far more commonly used alternative in real applications, serializing objects to and from JSON using the Jackson library, producing a readable, language-agnostic wire format any consumer (Java or otherwise) can parse.

## 2. Why & when

Choosing the right converter is one of the most consequential configuration decisions in a Spring AMQP application:

- **`Jackson2JsonMessageConverter` should be the default choice for nearly all new applications** — JSON is human-readable (useful for debugging via the broker's management UI), doesn't require the consumer to be Java, and doesn't carry Java's serialization format's well-known fragility across class version changes.
- **`SimpleMessageConverter`'s Java serialization fallback is rarely the right choice deliberately** — it exists mainly for backward compatibility and simple `String`/`byte[]` cases; relying on its Java-serialization fallback for structured objects ties producer and consumer tightly to matching Java class definitions, the same brittleness discussed for RMI (Spring Integration card 0068).
- **A custom or content-type-aware composite converter is needed when a single format doesn't fit every message type** — an application publishing both JSON-friendly domain events and occasional raw binary payloads (an image, a PDF) needs a converter setup that dispatches based on content type rather than forcing everything through one converter.

## 3. Core concept

Think of `SimpleMessageConverter`'s Java-serialization fallback as writing a letter in a private family shorthand only people who grew up in that specific household can read — efficient within that closed group, but useless (or actively confusing) to anyone outside it. `Jackson2JsonMessageConverter`'s JSON output is like writing the same letter in a widely-taught, standard language — a little more verbose, perhaps, but readable by essentially anyone, immediately, without needing to share a private decoder ring in advance.

```java
@Bean
public MessageConverter jsonMessageConverter() {
    return new Jackson2JsonMessageConverter();
}

@Bean
public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory, MessageConverter jsonMessageConverter) {
    RabbitTemplate template = new RabbitTemplate(connectionFactory);
    template.setMessageConverter(jsonMessageConverter);
    return template;
}
```

Once configured, every `convertAndSend`/`receiveAndConvert` call on this template automatically uses JSON serialization, with no per-call converter selection needed.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SimpleMessageConverter falls back to Java serialization for arbitrary objects, producing a Java-specific binary format readable only by Java consumers with matching classes; Jackson2JsonMessageConverter produces readable, language-agnostic JSON" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SimpleMessageConverter (fallback)</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">Order -&gt; Java serialization</text>
  <text x="35" y="65" fill="#8b949e" font-size="7" font-family="monospace">binary, Java-class-specific</text>
  <text x="35" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">only readable by matching Java classes</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Jackson2JsonMessageConverter</text>
  <text x="355" y="45" fill="#e6edf3" font-size="7" font-family="monospace">Order -&gt; {"id":"ORD-1",...}</text>
  <text x="355" y="65" fill="#79c0ff" font-size="7" font-family="monospace">readable, language-agnostic</text>
  <text x="355" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">any consumer, any language, can parse</text>
</svg>

The converter choice determines both readability and how tightly producer and consumer are coupled to each other's implementation language.

## 5. Runnable example

The scenario: comparing serialization output between the two converter approaches, simulated with a plain Java model standing in for both converter types (no real Jackson or Java serialization mechanics needed to demonstrate the format and coupling difference), starting with a basic side-by-side comparison, then adding a cross-language-consumer scenario showing why one format works universally and the other doesn't, then adding a class-evolution scenario showing why JSON tolerates change better than Java serialization's tight coupling.

### Level 1 — Basic

```java
// MessageConverterDemo.java
public class MessageConverterDemo {
    record Order(String id, double amount) {}

    // Stand-in for Jackson2JsonMessageConverter: produces readable, self-describing JSON.
    static String toJson(Order order) {
        return "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    // Stand-in for SimpleMessageConverter's Java-serialization fallback: an opaque, Java-specific format.
    static String toJavaSerializedPlaceholder(Order order) {
        return "[JAVA_SERIALIZED: com.example.Order@" + Integer.toHexString(order.hashCode()) + "]";
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1", 42.50);
        System.out.println("JSON format:            " + toJson(order));
        System.out.println("Java-serialized format:  " + toJavaSerializedPlaceholder(order));
    }
}
```

How to run: `java MessageConverterDemo.java`. Expected output: the JSON line is readable text anyone could parse; the Java-serialized line is an opaque reference only meaningful to a JVM with the exact matching `Order` class — illustrating the fundamental readability gap between the two approaches.

### Level 2 — Intermediate

```java
// MessageConverterDemo.java
public class MessageConverterDemo {
    record Order(String id, double amount) {}

    static String toJson(Order order) {
        return "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    // Real-world concern: a non-Java consumer (a Python service, a Node.js service) can parse
    // JSON trivially, but has NO way to deserialize Java's native serialization format at all --
    // it's a Java-specific binary protocol, not a general-purpose interchange format.
    static Order parseJsonAsAnyLanguageWould(String json) {
        // Simulating what ANY language's JSON parser could trivially do -- extract fields by name.
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(json.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        return new Order(id, amount);
    }

    static boolean canNonJavaConsumerParse(String format) {
        return format.equals("JSON"); // Java serialization: no, by design
    }

    public static void main(String[] args) {
        Order original = new Order("ORD-1", 42.50);
        String json = toJson(original);

        System.out.println("Can a Python/Node.js consumer parse JSON? " + canNonJavaConsumerParse("JSON"));
        System.out.println("Can a Python/Node.js consumer parse Java serialization? " + canNonJavaConsumerParse("JAVA_SERIALIZATION"));

        Order roundTripped = parseJsonAsAnyLanguageWould(json);
        System.out.println("Round-tripped through JSON: " + roundTripped);
    }
}
```

How to run: `java MessageConverterDemo.java`. Expected output: `true` for JSON, `false` for Java serialization, then a successfully round-tripped `Order` object — demonstrating that JSON's interoperability isn't just a stylistic preference but a hard functional requirement whenever any non-Java consumer exists anywhere in the system.

### Level 3 — Advanced

```java
// MessageConverterDemo.java
public class MessageConverterDemo {
    record OrderV1(String id, double amount) {}
    record OrderV2(String id, double amount, String currency) {} // added a field later

    // Production concern: JSON deserialization can tolerate a NEW field appearing (ignored by an
    // older consumer) or a field being ABSENT (defaulted) far more gracefully than Java's native
    // serialization, which is notoriously brittle across class version changes (serialVersionUID
    // mismatches, field additions/removals) between producer and consumer JVMs.
    static OrderV1 parseIgnoringUnknownFields(String json) {
        // Simulating a JSON parser that simply ignores fields it doesn't know about (like "currency").
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(json.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        return new OrderV1(id, amount); // "currency" field silently ignored, no error
    }

    public static void main(String[] args) {
        // Producer has upgraded to OrderV2 (added "currency"), but this consumer still expects OrderV1's shape.
        OrderV2 newProducerOrder = new OrderV2("ORD-1", 42.50, "USD");
        String jsonFromNewProducer = "{\"id\":\"" + newProducerOrder.id() + "\",\"amount\":"
            + newProducerOrder.amount() + ",\"currency\":\"" + newProducerOrder.currency() + "\"}";

        System.out.println("JSON from upgraded producer: " + jsonFromNewProducer);

        OrderV1 consumedByOldConsumer = parseIgnoringUnknownFields(jsonFromNewProducer);
        System.out.println("Old consumer parsed successfully, ignoring new field: " + consumedByOldConsumer);
        System.out.println("(Java's native serialization would instead typically throw an "
            + "InvalidClassException here on a class-shape mismatch between producer and consumer)");
    }
}
```

How to run: `java MessageConverterDemo.java`. Expected output: the upgraded producer's JSON (including the new `currency` field) prints, followed by `Old consumer parsed successfully, ignoring new field: OrderV1[id=ORD-1, amount=42.5]` — the old consumer tolerating the schema change gracefully, plus an explanatory note that Java's native serialization would typically fail hard on the equivalent class-shape mismatch, exactly the brittleness that makes `Jackson2JsonMessageConverter` the safer choice for any system where producer and consumer might evolve independently over time.

## 6. Walkthrough

Trace a message through converter selection on both the producing and consuming sides.

1. **Converter configuration**: at application startup, a `Jackson2JsonMessageConverter` bean is registered and wired into the `RabbitTemplate` (for publishing) and, separately, into whatever consumes messages (a `SimpleMessageListenerContainer` or `@RabbitListener` infrastructure, card 0022) — both sides need matching, compatible converter configuration for the round trip to work.
2. **Producer-side serialization**: when `convertAndSend(exchange, routingKey, order)` runs, the configured converter's `toMessage(order, properties)` method serializes the `Order` object to JSON bytes and sets the `contentType` property to `application/json`.
3. **Message travels as opaque bytes**: as far as the broker is concerned, the message body is just bytes — it has no awareness of JSON, Java serialization, or any other format; the content-type header exists purely for the eventual consumer's benefit, not the broker's.
4. **Consumer-side deserialization**: when a message arrives at a consumer using the matching `Jackson2JsonMessageConverter`, its `fromMessage(message)` method reads the content-type header, confirms it's JSON, and deserializes the bytes back into the target Java type the listener method expects.
5. **Graceful handling of schema evolution**: if the JSON payload contains a field the consumer's target class doesn't know about (a newer producer having added a field), Jackson's default behavior typically ignores unknown fields rather than failing outright — letting producer and consumer evolve independently as long as changes are additive and backward-compatible.
6. **Mismatched converters fail at the consumer**: if a producer used one converter (say, JSON) while a consumer was mistakenly configured to expect Java-serialized bytes (or vice versa), the mismatch surfaces as a deserialization exception on the consuming side — a classic symptom of inconsistent converter configuration between independently-deployed producer and consumer applications.

```
producer: order object
  -> Jackson2JsonMessageConverter.toMessage() -> JSON bytes + contentType=application/json
    -> published, travels as opaque bytes through the broker
      -> consumer: Jackson2JsonMessageConverter.fromMessage()
        -> reads contentType, deserializes JSON back to target Java type
          (unknown fields tolerated; type/shape mismatches surface as errors here)
```

## 7. Gotchas & takeaways

> **Gotcha:** `SimpleMessageConverter`'s Java-serialization fallback is still the framework's default if no converter is explicitly configured — a team that never deliberately configures a `MessageConverter` bean is silently relying on Java serialization for any non-`String`/non-`byte[]` payload, tightly coupling producer and consumer to matching Java class definitions without ever having made that choice consciously; always explicitly configure `Jackson2JsonMessageConverter` (or another deliberate choice) rather than accepting the default by omission.

- `Jackson2JsonMessageConverter` should be the default choice for essentially all new Spring AMQP applications — its readability, language-agnosticism, and tolerance for additive schema changes all favor it over the Java-serialization fallback in nearly every real scenario.
- Producer and consumer must be configured with compatible converters for a message to round-trip successfully — this is an application-wide consistency concern, not something that can be mismatched on one side without consequence on the other.
- JSON's tolerance for schema evolution (ignoring unknown fields, defaulting missing ones depending on configuration) is a genuine operational advantage in systems where producer and consumer services deploy independently and aren't always perfectly version-synchronized.
- Reach for a custom or composite `MessageConverter` specifically when a single format doesn't fit every message type an application handles (mixed JSON and raw binary payloads, for instance) — but treat this as the exception, with JSON as the sensible default for the common case of structured domain objects.
