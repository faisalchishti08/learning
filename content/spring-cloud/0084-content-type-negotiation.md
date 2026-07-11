---
card: spring-cloud
gi: 84
slug: content-type-negotiation
title: "Content type negotiation"
---

## 1. What it is

Content type negotiation is Spring Cloud Stream's mechanism for converting between the Java objects a `Function`/`Consumer`/`Supplier` works with and the actual bytes that travel over the broker — controlled by `spring.cloud.stream.bindings.<binding>.content-type` (defaulting to `application/json`), with built-in message converters handling JSON, and custom converters pluggable for other formats (Avro, Protobuf, plain text).

```properties
spring.cloud.stream.bindings.handleOrder-in-0.content-type=application/json
spring.cloud.stream.bindings.handleOrder-out-0.content-type=application/json

# a different binding using a different format entirely
spring.cloud.stream.bindings.legacyOrders-in-0.content-type=application/xml
```

## 2. Why & when

A `Function<OrderPlaced, InvoiceRequested>` bean operates on plain Java objects, but the broker only ever transports raw bytes — something has to serialize `OrderPlaced` into bytes before publishing and deserialize bytes back into `OrderPlaced` before the function runs. Content type negotiation is exactly that translation layer, decided declaratively per binding rather than requiring manual `ObjectMapper` calls scattered through application code.

Understand this mechanism when:

- Debugging a deserialization failure — a consumer receiving bytes it can't correctly parse into the expected Java type is one of the most common event-driven integration bugs, and the content-type configuration (does the consumer's expected type match what the producer actually serialized?) is the first place to look.
- Interoperating with a non-Spring, non-JSON producer or consumer — a legacy system publishing XML, or a schema-registry-based Avro/Protobuf pipeline — requires either a custom `MessageConverter` or reaching for a binder that natively supports that serialization format.
- Evolving a message schema over time — adding an optional field to `OrderPlaced` is usually safe with JSON's flexible deserialization, but understanding exactly how the current content-type's converter handles missing/extra fields is essential before making a change that could break existing consumers mid-rollout.

## 3. Core concept

```
 publish:    Java object (OrderPlaced)
                  |
                  v  MessageConverter, driven by content-type config
             raw bytes (JSON, by default) -----> sent to the broker

 consume:    raw bytes (from the broker)
                  |
                  v  MessageConverter, driven by content-type config
             Java object (OrderPlaced) -----> passed into the Function/Consumer
```

The same content-type configuration governs both directions — what a producer serializes to must match what a consumer expects to deserialize from, or the message arrives corrupted or unparseable.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Java object is serialized to JSON bytes by a message converter before being published, and the same bytes are deserialized back into a Java object by a matching converter on the consuming side">
  <rect x="20" y="70" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderPlaced (Java)</text>

  <line x1="160" y1="90" x2="220" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a84)"/>
  <text x="190" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">serialize</text>

  <rect x="225" y="70" width="190" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">{"orderId":"42",...} (bytes)</text>

  <line x1="415" y1="90" x2="475" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a84)"/>
  <text x="445" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">deserialize</text>

  <rect x="480" y="70" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderPlaced (Java)</text>

  <defs><marker id="a84" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The Java object round-trips through bytes on the wire; the content-type configuration governs both the serialization and deserialization steps.

## 5. Runnable example

The scenario: model the serialize/deserialize round trip for `OrderPlaced` events. Start with a naive, manually-serialized approach, then add a proper converter matching the configured content type, then handle a mismatch between producer and consumer content types.

### Level 1 — Basic

Manual, ad hoc serialization — what the converter mechanism replaces with a declarative, consistent approach.

```java
public class ContentTypeLevel1 {
    record OrderPlaced(String orderId, double amount) {}

    static String manualSerialize(OrderPlaced order) {
        return "{\"orderId\":\"" + order.orderId() + "\",\"amount\":" + order.amount() + "}"; // hand-built, error-prone
    }

    public static void main(String[] args) {
        OrderPlaced order = new OrderPlaced("42", 199.99);
        String bytes = manualSerialize(order);
        System.out.println("manually serialized: " + bytes);
    }
}
```

How to run: `java ContentTypeLevel1.java`

Hand-building JSON strings works for a simple case but is fragile — no escaping of special characters, no handling of nested objects, and it has to be written and kept correct separately at every single publish call site.

### Level 2 — Intermediate

Add a proper, reusable `MessageConverter`-style abstraction, mirroring how content-type configuration drives consistent, centralized conversion.

```java
import java.util.regex.*;

public class ContentTypeLevel2 {
    record OrderPlaced(String orderId, double amount) {}

    interface MessageConverter<T> {
        String serialize(T value);
        T deserialize(String bytes);
    }

    static MessageConverter<OrderPlaced> jsonConverter = new MessageConverter<>() {
        public String serialize(OrderPlaced order) {
            return "{\"orderId\":\"" + order.orderId() + "\",\"amount\":" + order.amount() + "}";
        }
        public OrderPlaced deserialize(String bytes) {
            Matcher m = Pattern.compile("\"orderId\":\"(.*?)\".*\"amount\":([0-9.]+)").matcher(bytes);
            if (!m.find()) throw new IllegalArgumentException("cannot deserialize as OrderPlaced: " + bytes);
            return new OrderPlaced(m.group(1), Double.parseDouble(m.group(2)));
        }
    };

    public static void main(String[] args) {
        OrderPlaced original = new OrderPlaced("42", 199.99);

        String bytes = jsonConverter.serialize(original);
        System.out.println("published bytes: " + bytes);

        OrderPlaced roundTripped = jsonConverter.deserialize(bytes);
        System.out.println("consumer received: " + roundTripped);
        System.out.println("round-trip successful: " + original.equals(roundTripped));
    }
}
```

How to run: `java ContentTypeLevel2.java`

`jsonConverter` centralizes both directions of conversion in one reusable object — every publish call and every consume call goes through the *same* `serialize`/`deserialize` logic, exactly mirroring how a real `content-type=application/json` binding uses one consistent converter for every message on that binding, rather than each call site reimplementing serialization independently.

### Level 3 — Advanced

Model a content-type mismatch — a consumer expecting JSON receiving XML instead (perhaps a legacy producer wasn't updated, or a binding was misconfigured) — and confirm it fails clearly rather than silently corrupting data.

```java
import java.util.regex.*;

public class ContentTypeLevel3 {
    record OrderPlaced(String orderId, double amount) {}

    interface MessageConverter<T> {
        String serialize(T value);
        T deserialize(String bytes);
    }

    static MessageConverter<OrderPlaced> jsonConverter = new MessageConverter<>() {
        public String serialize(OrderPlaced order) {
            return "{\"orderId\":\"" + order.orderId() + "\",\"amount\":" + order.amount() + "}";
        }
        public OrderPlaced deserialize(String bytes) {
            Matcher m = Pattern.compile("\"orderId\":\"(.*?)\".*\"amount\":([0-9.]+)").matcher(bytes);
            if (!m.find()) throw new IllegalArgumentException("cannot deserialize as JSON OrderPlaced: " + bytes);
            return new OrderPlaced(m.group(1), Double.parseDouble(m.group(2)));
        }
    };

    static MessageConverter<OrderPlaced> xmlConverter = new MessageConverter<>() {
        public String serialize(OrderPlaced order) {
            return "<order><id>" + order.orderId() + "</id><amount>" + order.amount() + "</amount></order>";
        }
        public OrderPlaced deserialize(String bytes) {
            Matcher m = Pattern.compile("<id>(.*?)</id>.*<amount>(.*?)</amount>").matcher(bytes);
            if (!m.find()) throw new IllegalArgumentException("cannot deserialize as XML OrderPlaced: " + bytes);
            return new OrderPlaced(m.group(1), Double.parseDouble(m.group(2)));
        }
    };

    public static void main(String[] args) {
        // a legacy producer, misconfigured or simply never updated, publishes XML
        OrderPlaced original = new OrderPlaced("42", 199.99);
        String xmlBytes = xmlConverter.serialize(original);
        System.out.println("legacy producer published: " + xmlBytes);

        // this consumer's binding is configured content-type=application/json -- expects JSON, gets XML
        try {
            OrderPlaced result = jsonConverter.deserialize(xmlBytes);
            System.out.println("consumer received: " + result);
        } catch (IllegalArgumentException e) {
            System.out.println("consumer FAILED to deserialize: " + e.getMessage());
            System.out.println("-- this is a content-type MISMATCH between producer and consumer configuration --");
        }
    }
}
```

How to run: `java ContentTypeLevel3.java`

`xmlConverter.serialize` produces XML-formatted bytes, but `jsonConverter.deserialize` (modeling a consumer whose binding is configured for `application/json`) attempts to parse them as JSON and fails with a clear exception, rather than silently producing corrupted or nonsensical data. This models exactly the real failure mode a content-type mismatch produces: a deserialization exception at the consumer, tracing back to a producer and consumer disagreeing about the actual wire format, even though both sides individually believe they're configured correctly.

## 6. Walkthrough

Trace the mismatch scenario in Level 3.

1. `xmlConverter.serialize(original)` runs, producing `"<order><id>42</id><amount>199.99</amount></order>"` — this models a legacy producer whose binding is configured (correctly, for its own purposes) with `content-type=application/xml`, publishing a real order event in the format it was actually built to produce.
2. The `try` block calls `jsonConverter.deserialize(xmlBytes)` — this models a consumer whose *own* binding configuration says `content-type=application/json`, so it applies the JSON-parsing regex to bytes that are actually XML.
3. Inside `jsonConverter.deserialize`, the regex `Pattern.compile("\"orderId\":\"(.*?)\".*\"amount\":([0-9.]+)")` is matched against the XML string — since the XML format has no `"orderId":"..."` substring at all, `m.find()` returns `false`, and the `if (!m.find())` branch throws `IllegalArgumentException` with a clear message.
4. The `catch` block catches this exception and prints both the raw error message and an explanatory note — in a real Spring Cloud Stream application, this kind of failure would typically surface as a `MessageConversionException` in the consumer's logs, and (depending on error-handling configuration, covered in the next card) potentially route the unparseable message to a dead-letter queue rather than crashing the whole consumer.

```
producer (content-type=application/xml)  -> publishes XML bytes
consumer (content-type=application/json) -> attempts to parse those bytes AS JSON -> fails clearly

the mismatch is in CONFIGURATION agreement, not in either converter being individually "wrong"
```

## 7. Gotchas & takeaways

> **Gotcha:** JSON's flexible, schema-less nature means adding a new *optional* field to a message type is usually a safe, backward-compatible change (older consumers simply ignore the unrecognized field), but *removing* or *renaming* an existing field a running consumer still expects is a breaking change that content-type negotiation alone won't catch or warn about — it will simply deserialize into a Java object with an unexpectedly null or default-valued field, often silently, unless the consumer's own validation logic notices.

- Content type negotiation is the declarative translation layer between Java objects and broker bytes, replacing ad hoc, per-call-site serialization code with one consistent, centrally-configured mechanism per binding.
- `content-type` must agree between producer and consumer for a given destination — a mismatch produces a clear deserialization failure on the consuming side, not silent corruption, but the *root cause* (configuration disagreement between two independently-deployed services) can still take real debugging effort to trace.
- JSON is the sensible default for most Spring-to-Spring messaging; reach for a schema-based format (Avro, Protobuf, often paired with a schema registry) when strict schema evolution guarantees, smaller message size, or interoperability with non-JVM systems matter more than JSON's simplicity.
- Understanding the serialize/deserialize round trip explicitly (as this card's example modeled directly) is what makes content-type mismatches diagnosable — recognizing "this is a converter-level failure, check what format each side is actually configured for" rather than treating it as an opaque, unexplained error.
