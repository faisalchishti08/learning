---
card: spring-integration
gi: 78
slug: message-transformation-object-json-xml-avro
title: "Message transformation (object<->JSON/XML, Avro)"
---

## 1. What it is

Built-in format transformers (`ObjectToJsonTransformer`/`JsonToObjectTransformer`, `Jackson2XmlTransformer`, `Marshaller`/`Unmarshaller`-based transformers for XML, and Avro-specific transformers) convert a message's payload between an in-memory Java object and a serialized wire format — JSON, XML, or Avro's compact binary format — without the flow needing to hand-write parsing or serialization code. This is a more specialized case of the generic Transformer component (card 0038 or nearby), pre-built specifically for these common object-to-wire-format conversions.

## 2. Why & when

You reach for a format transformer whenever a message crosses a boundary where the format on one side doesn't match the format the other side needs:

- **An HTTP or messaging endpoint needs JSON, but internal processing works with Java objects** — converting at the boundary (JSON in from an external caller, object internally, JSON out to a reply) keeps the bulk of the flow's logic working with typed objects rather than raw text everywhere.
- **A legacy or partner system expects XML** — some enterprise integrations, especially with older systems or ones following SOAP-adjacent conventions, still communicate exclusively in XML; a transformer converts a flow's internal object model to and from that format at the edges.
- **High-throughput or schema-strict pipelines need Avro** — Avro's compact binary encoding and built-in schema evolution support make it a common choice for data pipelines (often paired with Kafka, card 0059) where JSON's verbosity or lack of enforced schema would be a real cost at scale.

## 3. Core concept

Think of a Java object in memory as a fully-assembled piece of furniture sitting in a room. JSON, XML, and Avro are each a different way of packing that furniture for shipping: JSON is like a flat-pack box with a readable parts list anyone can open and inspect by eye; XML is a more heavily labeled, verbose box with nested compartments; Avro is a shrink-wrapped, vacuum-sealed package — smaller and faster to ship, but you need the exact packing schema on hand to unpack it correctly, since it doesn't carry the field names inline the way JSON and XML do.

```java
@Bean
public IntegrationFlow orderApiFlow() {
    return IntegrationFlow.from(Http.inboundGateway("/orders"))
        .transform(Transformers.fromJson(Order.class))     // JSON -> Order object
        .handle((Order order, headers) -> orderService.process(order))
        .transform(Transformers.toJson())                  // Order object -> JSON
        .get();
}
```

The flow's own logic works entirely with the `Order` object; JSON only exists at the two edges where the flow talks to an HTTP client.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A format transformer converts between a wire format (JSON, XML, or Avro binary) at the boundary and a plain Java object used internally by the flow" >
  <rect x="20" y="30" width="140" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Wire format</text>
  <text x="90" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JSON / XML / Avro</text>

  <line x1="160" y1="60" x2="260" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a3)"/>
  <text x="210" y="52" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">fromJson/Xml/Avro</text>

  <rect x="260" y="30" width="140" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Java object</text>
  <text x="330" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">flow's internal logic</text>

  <line x1="400" y1="75" x2="500" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <text x="450" y="90" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">toJson/Xml/Avro</text>

  <rect x="500" y="30" width="120" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Wire format</text>
  <text x="560" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">back out</text>

  <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
</svg>

Wire format only exists at the flow's edges; the middle works entirely with plain, typed objects.

## 5. Runnable example

The scenario: converting an order between JSON text and a Java object at flow boundaries, using plain string-based transformation to model the JSON<->object step without a JSON library dependency (genuinely runnable, focused on demonstrating the boundary-conversion pattern itself), starting with a basic round trip, then adding validation on the inbound conversion, then adding a second format (a simplified XML-like conversion) to show the transformer choice is independent of the flow's internal logic.

### Level 1 — Basic

```java
// FormatTransformDemo.java
public class FormatTransformDemo {
    record Order(String id, double amount) {}

    // Stand-in for Transformers.fromJson(Order.class): parses a tiny fixed JSON shape.
    static Order fromJson(String json) {
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(json.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        return new Order(id, amount);
    }

    // Stand-in for Transformers.toJson(): serializes back to the same tiny fixed JSON shape.
    static String toJson(Order order) {
        return "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    public static void main(String[] args) {
        String incomingJson = "{\"id\":\"ORD-1\",\"amount\":42.50}";
        Order order = fromJson(incomingJson);
        System.out.println("Parsed object: " + order);

        String outgoingJson = toJson(order);
        System.out.println("Serialized back: " + outgoingJson);
    }
}
```

How to run: `java FormatTransformDemo.java`. Expected output: `Parsed object: Order[id=ORD-1, amount=42.5]` then `Serialized back: {"id":"ORD-1","amount":42.5}` — a full JSON-to-object-to-JSON round trip, mirroring the two-transformer flow shape.

### Level 2 — Intermediate

```java
// FormatTransformDemo.java
public class FormatTransformDemo {
    record Order(String id, double amount) {}

    static class MalformedPayloadException extends RuntimeException {
        MalformedPayloadException(String msg) { super(msg); }
    }

    // Real-world concern: inbound data from an external caller isn't guaranteed well-formed --
    // a transformer that silently produces a garbage object (id="", amount=0.0) on bad input
    // hides the problem instead of surfacing it where it can be handled.
    static Order fromJson(String json) {
        if (!json.contains("\"id\"") || !json.contains("\"amount\"")) {
            throw new MalformedPayloadException("missing required fields in payload: " + json);
        }
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(json.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        return new Order(id, amount);
    }

    static String toJson(Order order) {
        return "{\"id\":\"" + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    public static void main(String[] args) {
        String[] incoming = {
            "{\"id\":\"ORD-1\",\"amount\":42.50}",
            "{\"amount\":10.00}" // missing "id"
        };

        for (String json : incoming) {
            try {
                Order order = fromJson(json);
                System.out.println("Parsed: " + order + " -> " + toJson(order));
            } catch (MalformedPayloadException ex) {
                System.out.println("Rejected payload: " + ex.getMessage());
            }
        }
    }
}
```

How to run: `java FormatTransformDemo.java`. Expected output: the well-formed payload parses and round-trips normally; the malformed one prints `Rejected payload: missing required fields in payload: ...` — the transformation step surfacing bad input explicitly rather than producing a silently corrupted object.

### Level 3 — Advanced

```java
// FormatTransformDemo.java
import java.util.function.*;

public class FormatTransformDemo {
    record Order(String id, double amount) {}

    static class MalformedPayloadException extends RuntimeException {
        MalformedPayloadException(String msg) { super(msg); }
    }

    static Order fromJson(String json) {
        if (!json.contains("\"id\"") || !json.contains("\"amount\"")) {
            throw new MalformedPayloadException("missing required fields (JSON): " + json);
        }
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(json.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        return new Order(id, amount);
    }

    // A second format (simplified XML-like), demonstrating that the internal Order object and
    // downstream logic don't change at all -- only the boundary transformer differs by format,
    // exactly like swapping ObjectToJsonTransformer for a Jackson2XmlTransformer in a real flow.
    static Order fromXml(String xml) {
        if (!xml.contains("<id>") || !xml.contains("<amount>")) {
            throw new MalformedPayloadException("missing required fields (XML): " + xml);
        }
        String id = xml.replaceAll(".*<id>([^<]+)</id>.*", "$1");
        double amount = Double.parseDouble(xml.replaceAll(".*<amount>([0-9.]+)</amount>.*", "$1"));
        return new Order(id, amount);
    }

    // Production concern: process the SAME downstream logic regardless of which format the
    // message arrived in -- the transformer choice is a pluggable boundary concern, not
    // something the business logic should ever need to know about.
    static void processOrder(String rawPayload, Function<String, Order> transformer) {
        try {
            Order order = transformer.apply(rawPayload);
            System.out.println("Processing order " + order.id() + " for $" + order.amount());
        } catch (MalformedPayloadException ex) {
            System.out.println("Rejected: " + ex.getMessage());
        }
    }

    public static void main(String[] args) {
        processOrder("{\"id\":\"ORD-1\",\"amount\":42.50}", FormatTransformDemo::fromJson);
        processOrder("<order><id>ORD-2</id><amount>15.00</amount></order>", FormatTransformDemo::fromXml);
        processOrder("<order><amount>5.00</amount></order>", FormatTransformDemo::fromXml); // missing id
    }
}
```

How to run: `java FormatTransformDemo.java`. Expected output: the JSON order and the XML order both process identically via the same `processOrder` logic, printing `Processing order ORD-1 for $42.5` and `Processing order ORD-2 for $15.0`; the malformed XML input is rejected with a clear message — demonstrating that swapping the wire format (as swapping `Transformers.fromJson(...)` for a `Jackson2XmlTransformer` would in a real flow) requires no change to the business logic that follows.

## 6. Walkthrough

Trace a message from external wire format, through internal processing, back to wire format.

1. **Inbound arrival**: an external caller sends a request whose body is JSON (or XML, or Avro-encoded binary), arriving at the flow's entry point — an HTTP inbound gateway, a Kafka consumer, or similar.
2. **Inbound transform**: a `.transform(Transformers.fromJson(Order.class))` step (or its XML/Avro equivalent) parses the raw payload into a typed `Order` object, raising a clear error if the payload doesn't match the expected shape rather than silently producing a partially-populated object.
3. **Internal processing**: every step in between works with the `Order` object directly — validating fields, computing derived values, persisting it — with no format-specific code anywhere in this middle section.
4. **Outbound transform**: before the reply leaves the flow, a `.transform(Transformers.toJson())` step (or the matching XML/Avro serializer) converts the processed `Order` back into the wire format the caller expects.
5. **Reply sent**: the serialized reply goes back over whatever transport brought the request in, completing the round trip with the caller never needing to know what internal representation the flow used in between.
6. **Format swap in isolation**: because the internal logic never touches the wire format directly, retargeting the same flow to a different external format (JSON to XML, or adding Avro for a Kafka-based variant of the same flow) is purely a matter of swapping the boundary transformers, not rewriting the processing logic in between.

```
external JSON/XML/Avro payload
  -> inbound transformer -> Order object
    -> [flow logic works only with Order, format-agnostic]
      -> outbound transformer -> external JSON/XML/Avro reply
```

## 7. Gotchas & takeaways

> **Gotcha:** a transformer that catches a parse failure and returns a default or empty object instead of raising an exception hides bad input as though it were valid data — always let a malformed payload surface as an explicit error (routed to an error channel, or rejected outright) rather than silently substituting a default value that downstream logic will treat as legitimate.

- Keep format-specific code confined to the transformer steps at the flow's edges; any format-awareness leaking into the middle of the flow is a sign the boundary wasn't drawn cleanly.
- Avro's schema-based binary encoding is more compact and faster to (de)serialize than JSON or XML, but requires the schema to be available (embedded, or from a schema registry) wherever deserialization happens — losing track of which schema version encoded a given message is a common source of Avro deserialization failures.
- XML transformation via a `Marshaller`/`Unmarshaller` pair (often JAXB-based) needs the object model annotated appropriately; retrofitting XML support onto a domain model not designed with XML in mind can require more mapping code than JSON's typically more direct object-to-JSON correspondence.
- Choosing the wire format is a boundary decision independent of the flow's internal design — the same internal `Order`-processing logic can serve a JSON-speaking HTTP client, an XML-speaking legacy partner, and an Avro-encoded Kafka topic simultaneously, provided each boundary has its own appropriate transformer.
