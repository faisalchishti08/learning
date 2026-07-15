---
card: spring-integration
gi: 21
slug: transformer
title: "Transformer"
---

## 1. What it is

`@Transformer` is the endpoint archetype (from the taxonomy in card 0019) whose sole job is converting a message's content — its payload, its headers, or both — into a different shape, and forwarding exactly one resulting message onward. Unlike `@ServiceActivator` (card 0020), which is about invoking business logic and may or may not care about its input/output shapes, a `Transformer`'s entire purpose *is* the shape change: parsing a string into an object, converting units, enriching headers, or reformatting a payload for the next endpoint downstream.

## 2. Why & when

You reach for `Transformer` specifically when a message needs to change shape before the next step can use it, and that shape change is itself the whole job:

- **Two endpoints expect incompatible message shapes** — an inbound adapter (card 0018) produces raw bytes or strings, but the next `@ServiceActivator` expects a parsed domain object — a `Transformer` sits between them doing exactly that conversion, keeping both endpoints simple and single-purpose.
- **You want the conversion logic named and independently testable**, separate from whatever business logic comes before or after it — a dedicated `Transformer` method can be tested with a plain input/output assertion, with no messaging setup required.
- **A message needs enrichment rather than full conversion** — adding a computed header, a timestamp, a derived field — while otherwise passing the payload through; `Transformer` covers this too, since "transform" just means "produce a different message," which can be a lightly modified version of the original.

## 3. Core concept

Think of `Transformer` like a customs office at a border crossing, converting goods' paperwork into the format the destination country requires, without changing what the goods fundamentally are. A shipment declared in one country's units and forms crosses the border and comes out the other side re-labeled in the destination's units and forms — same underlying cargo, different representation — ready for whatever the receiving country's systems expect next.

```java
@Transformer(inputChannel = "rawOrders", outputChannel = "parsedOrders")
public Order parse(String rawCsvLine) {
    String[] parts = rawCsvLine.split(",");
    return new Order(parts[0], Double.parseDouble(parts[1]));
}
```

Every message sent to `rawOrders` has its `String` payload passed to `parse`, and the returned `Order` is automatically wrapped into a new message sent to `parsedOrders` — the method itself contains nothing but the actual conversion logic.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Transformer converts a message's payload from one shape to another between input and output channels">
  <rect x="20" y="60" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">input channel</text>
  <text x="80" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">payload: raw CSV string</text>

  <line x1="140" y1="85" x2="210" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#t1)"/>

  <rect x="220" y="55" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Transformer</text>
  <text x="320" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">parse(String) -&gt; Order</text>

  <line x1="420" y1="85" x2="490" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#t2)"/>

  <rect x="500" y="60" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">output channel</text>
  <text x="560" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">payload: Order object</text>

  <defs>
    <marker id="t1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="t2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The payload's type genuinely changes crossing the transformer — `String` in, `Order` out — while exactly one message flows through, unlike `Splitter` (card 0024).

## 5. Runnable example

The scenario: a raw CSV order line arriving from an external system, starting with basic parsing into a domain object, then header enrichment alongside payload transformation, and finally a transformer chain converting through multiple representations.

### Level 1 — Basic

```java
// BasicTransformerDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicTransformerDemo {
    record Order(String id, double amount) {}

    static Order parse(String rawCsvLine) { // the transformer's actual logic
        String[] parts = rawCsvLine.split(",");
        return new Order(parts[0], Double.parseDouble(parts[1]));
    }

    public static void main(String[] args) {
        DirectChannel rawOrders = new DirectChannel();
        DirectChannel parsedOrders = new DirectChannel();
        parsedOrders.subscribe(m -> System.out.println("Parsed: " + m.getPayload()));

        // what @Transformer(inputChannel="rawOrders", outputChannel="parsedOrders") does for you:
        rawOrders.subscribe(m -> {
            Order order = parse((String) m.getPayload());
            parsedOrders.send(MessageBuilder.withPayload(order).build());
        });

        rawOrders.send(MessageBuilder.withPayload("ORD-1,199.99").build());
    }
}
```

How to run: `java BasicTransformerDemo.java`. Expected output: `Parsed: Order[id=ORD-1, amount=199.99]` — the raw CSV string was fully converted into a typed domain object by the time it reached the output channel's subscriber.

### Level 2 — Intermediate

A transformer can enrich headers alongside (or instead of) changing the payload — here, stamping a `parsedAt` timestamp header while also parsing the payload, useful for downstream endpoints (or monitoring) that need to know when conversion happened.

```java
// EnrichingTransformerDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.time.Instant;

public class EnrichingTransformerDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel rawOrders = new DirectChannel();
        DirectChannel parsedOrders = new DirectChannel();
        parsedOrders.subscribe(m -> System.out.println(
            "Parsed: " + m.getPayload() + " (parsedAt=" + m.getHeaders().get("parsedAt") + ")"));

        rawOrders.subscribe(m -> {
            String[] parts = ((String) m.getPayload()).split(",");
            Order order = new Order(parts[0], Double.parseDouble(parts[1]));
            parsedOrders.send(MessageBuilder.withPayload(order)
                .setHeader("parsedAt", Instant.now().toString()) // enrichment alongside conversion
                .build());
        });

        rawOrders.send(MessageBuilder.withPayload("ORD-1,199.99").build());
    }
}
```

How to run: `java EnrichingTransformerDemo.java`. Expected output: `Parsed: Order[id=ORD-1, amount=199.99] (parsedAt=2026-...)` — the transformer both changed the payload's type and added a new header the original raw message never had.

### Level 3 — Advanced

Chaining multiple transformers, each doing one focused conversion, mirrors a realistic pipeline: raw bytes to string, string to domain object, domain object to a summary DTO for an external API — each step independently simple, the composition doing the full job.

```java
// ChainedTransformersDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.nio.charset.StandardCharsets;

public class ChainedTransformersDemo {
    record Order(String id, double amount) {}
    record OrderSummaryDto(String orderId, String formattedAmount) {}

    public static void main(String[] args) {
        DirectChannel rawBytes = new DirectChannel();
        DirectChannel asString = new DirectChannel();
        DirectChannel asOrder = new DirectChannel();
        DirectChannel asDto = new DirectChannel();
        asDto.subscribe(m -> System.out.println("Final DTO ready for external API: " + m.getPayload()));

        // Transformer 3: Order -> OrderSummaryDto
        asOrder.subscribe(m -> {
            Order order = (Order) m.getPayload();
            OrderSummaryDto dto = new OrderSummaryDto(order.id(), String.format("$%.2f", order.amount()));
            asDto.send(MessageBuilder.withPayload(dto).build());
        });

        // Transformer 2: String -> Order
        asString.subscribe(m -> {
            String[] parts = ((String) m.getPayload()).split(",");
            Order order = new Order(parts[0], Double.parseDouble(parts[1]));
            asOrder.send(MessageBuilder.withPayload(order).build());
        });

        // Transformer 1: byte[] -> String
        rawBytes.subscribe(m -> {
            String decoded = new String((byte[]) m.getPayload(), StandardCharsets.UTF_8);
            asString.send(MessageBuilder.withPayload(decoded).build());
        });

        rawBytes.send(MessageBuilder.withPayload("ORD-1,199.99".getBytes(StandardCharsets.UTF_8)).build());
    }
}
```

How to run: `java ChainedTransformersDemo.java`. Expected output: `Final DTO ready for external API: OrderSummaryDto[orderId=ORD-1, formattedAmount=$199.99]` — the payload passed through three distinct type transformations (`byte[]` → `String` → `Order` → `OrderSummaryDto`), each transformer handling exactly one conversion step.

## 6. Walkthrough

Tracing `ChainedTransformersDemo` in execution order:

1. `rawBytes.send(...)` carries a `byte[]` payload — the raw form an inbound adapter (card 0018) might actually hand off, e.g. bytes read from a socket or file.
2. The first transformer's subscriber decodes those bytes into a UTF-8 `String` using `new String(bytes, StandardCharsets.UTF_8)`, wraps it into a new message, and sends it to `asString` — payload type has changed from `byte[]` to `String`.
3. The second transformer's subscriber splits that string on `,` and parses it into an `Order` record, sending the result to `asOrder` — payload type changes again, from `String` to `Order`.
4. The third transformer's subscriber reads the `Order`'s fields and constructs an `OrderSummaryDto` with a differently-formatted amount string, sending it to `asDto` — payload type changes a third time, from `Order` to `OrderSummaryDto`.
5. The final subscriber on `asDto` receives the fully-transformed DTO and prints it — this is the shape an outbound adapter (card 0018) would actually serialize and send to an external API.
6. At every step, each transformer only knew about its own input and output types — the first transformer has no idea an `OrderSummaryDto` will eventually exist, and the third has no idea the data originally arrived as raw bytes; each link in the chain is independently simple.

```
byte[] --[Transformer 1: decode]--> String --[Transformer 2: parse]--> Order --[Transformer 3: format]--> OrderSummaryDto
```

## 7. Gotchas & takeaways

> A `Transformer` method must return exactly one result (or `null`, to drop the message entirely — though `Filter`, card 0022, is the more explicit, self-documenting way to drop messages). Returning a `List` or array does **not** automatically fan it out into multiple messages the way a `Splitter` (card 0024) does; a common mistake is reaching for `Transformer` when what's actually needed is `Splitter`'s one-becomes-many semantics.

- `Transformer` converts a message's payload, headers, or both into a different shape, forwarding exactly one resulting message — the archetype whose entire job is the shape change itself.
- Use it to bridge incompatible shapes between two endpoints, to enrich a message with computed headers, or to keep conversion logic named and independently testable rather than buried inside business logic.
- A `Transformer` differs from `Splitter` (one message stays one message, even if the type changes) and from `Filter` (a `Transformer` changes shape; a `Filter` makes a keep/drop decision without changing shape).
- Chaining several small, single-purpose transformers is generally clearer than one transformer doing several unrelated conversions at once — each step stays independently testable and reorderable.
- Returning `null` from a transformer method drops the message silently; prefer an explicit `Filter` (card 0022) when the intent is genuinely "decide whether this message proceeds," since that intent is easy to miss buried inside a transformer.
