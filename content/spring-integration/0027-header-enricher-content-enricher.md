---
card: spring-integration
gi: 27
slug: header-enricher-content-enricher
title: "Header enricher / Content enricher"
---

## 1. What it is

A header enricher (`HeaderEnricher`, or `@Transformer` methods that only add headers) and a content enricher (`ContentEnricher`) are specialized `Transformer` variants (card 0021) whose whole job is *adding* information to a message rather than replacing it wholesale. A header enricher adds or overwrites specific headers while leaving the payload untouched; a content enricher typically fetches additional data (often from an external source, via a `requestChannel`) and merges it into the payload itself, producing an augmented version of the original object.

## 2. Why & when

You reach for these specifically when a message is *almost* complete but is missing a piece that needs to be added before it can proceed:

- **A message needs a computed or constant header added** — a timestamp, a static routing hint, a generated ID — without touching the payload at all; a header enricher is the narrowly-scoped, self-documenting way to do exactly that, rather than a general-purpose `Transformer` that happens to also pass the payload through unchanged.
- **A payload is missing a field that must be looked up elsewhere** — an `Order` arrives with a `customerId` but needs the customer's shipping address merged in before fulfillment — a content enricher calls out (often via a nested `requestChannel`/`replyChannel` exchange, the same mechanism `MessagingTemplate`, card 0016, uses) to fetch the missing piece and merges it into the payload.
- **You want enrichment to be a clearly separate, named step from core transformation logic** — keeping "what does this message need to look like for the next step" (a `Transformer`'s job) distinct from "what extra information does this message need before it looks like anything at all" (an enricher's job) keeps each step's intent obvious from its name alone.

## 3. Core concept

Think of a header enricher like a shipping label printer stamping "Fragile" and a tracking number onto a box without opening it — the contents are untouched, only the external labeling changes. A content enricher, by contrast, is like a fulfillment worker opening the box, checking what's missing, retrieving the missing item from a nearby shelf, and placing it inside before resealing — the contents themselves genuinely change, augmented rather than replaced.

```java
// Header enricher: adds headers, payload untouched
@Transformer(inputChannel = "orders", outputChannel = "taggedOrders")
public Message<Order> enrichHeaders(Message<Order> message) {
    return MessageBuilder.fromMessage(message)
        .setHeader("receivedAt", Instant.now().toString())
        .setHeader("source", "web")
        .build(); // same Order payload, new headers
}

// Content enricher: augments the payload itself, typically via a lookup
@Transformer(inputChannel = "orders", outputChannel = "enrichedOrders")
public Order enrichPayload(Order order) {
    Address address = addressLookupService.findFor(order.customerId());
    return order.withShippingAddress(address); // payload genuinely changed
}
```

Both are specialized transformers, differing only in whether the enrichment adds metadata (headers) or genuinely augments the domain content (payload).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Header enricher adds headers to a message leaving the payload untouched; content enricher looks up missing data and merges it into the payload itself">
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Header enricher</text>
  <rect x="20" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order (no headers)</text>

  <line x1="130" y1="57" x2="190" y2="57" stroke="#6db33f" stroke-width="2" marker-end="url(#he1)"/>

  <rect x="200" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="255" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">+ headers stamped</text>

  <text x="470" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Content enricher</text>
  <rect x="340" y="120" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="147" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order (no address)</text>

  <line x1="450" y1="142" x2="450" y2="90" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#he3)"/>
  <text x="500" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">lookup call</text>

  <rect x="400" y="55" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="460" y="77" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">address service</text>

  <line x1="450" y1="142" x2="560" y2="142" stroke="#79c0ff" stroke-width="2" marker-end="url(#he2)"/>

  <rect x="510" y="120" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="565" y="147" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order + address</text>

  <defs>
    <marker id="he1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="he2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="he3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Header enrichment leaves the payload's identity untouched; content enrichment genuinely augments it, typically via a lookup to another source.

## 5. Runnable example

The scenario: incoming orders needing both routing metadata and a missing shipping address filled in, starting with a basic header enrichment, then a content enrichment via a simulated lookup service, and finally both combined in one pipeline with a fallback for a failed lookup.

### Level 1 — Basic

```java
// BasicHeaderEnricherDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.time.Instant;

public class BasicHeaderEnricherDemo {
    record Order(String id) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel taggedOrders = new DirectChannel();
        taggedOrders.subscribe(m -> System.out.println(
            "Payload: " + m.getPayload() + " | receivedAt=" + m.getHeaders().get("receivedAt")
            + " | source=" + m.getHeaders().get("source")));

        // what a header enricher does: same payload, new/overwritten headers
        orders.subscribe(m -> taggedOrders.send(MessageBuilder.fromMessage(m)
            .setHeader("receivedAt", Instant.now().toString())
            .setHeader("source", "web")
            .build()));

        orders.send(MessageBuilder.withPayload(new Order("ORD-1")).build());
    }
}
```

How to run: `java BasicHeaderEnricherDemo.java`. Expected output: `Payload: Order[id=ORD-1] | receivedAt=2026-... | source=web` — the `Order` payload is identical to what was sent; only headers were added.

### Level 2 — Intermediate

A content enricher performs a lookup (here, a simulated address service) and merges the result into a *new* payload — the original `Order` is augmented, not just tagged, and the lookup itself follows the same request/reply shape `MessagingTemplate` (card 0016) uses internally.

```java
// ContentEnricherDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Map;

public class ContentEnricherDemo {
    record Order(String id, String customerId, String shippingAddress) {}
    record Address(String line1, String city) {}

    static final Map<String, Address> ADDRESS_DB = Map.of(
        "CUST-1", new Address("221B Baker St", "London"));

    static Address lookupAddress(String customerId) { // stand-in for an external lookup service
        return ADDRESS_DB.get(customerId);
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel enrichedOrders = new DirectChannel();
        enrichedOrders.subscribe(m -> System.out.println("Enriched payload: " + m.getPayload()));

        // what a content enricher does: lookup + merge into a NEW, augmented payload
        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            Address address = lookupAddress(order.customerId());
            Order enriched = new Order(order.id(), order.customerId(), address.line1() + ", " + address.city());
            enrichedOrders.send(MessageBuilder.withPayload(enriched).build());
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", "CUST-1", null)).build());
    }
}
```

How to run: `java ContentEnricherDemo.java`. Expected output: `Enriched payload: Order[id=ORD-1, customerId=CUST-1, shippingAddress=221B Baker St, London]` — the original `Order` had `shippingAddress=null`; the enricher's lookup filled it in, producing a genuinely more complete payload.

### Level 3 — Advanced

Combining both enrichers in one pipeline, plus a fallback for when a content-enrichment lookup fails to find anything — a realistic scenario where header enrichment (always succeeds, purely local) and content enrichment (can fail, depends on an external lookup) need different failure-handling expectations.

```java
// CombinedEnrichmentPipelineDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.time.Instant;
import java.util.Map;

public class CombinedEnrichmentPipelineDemo {
    record Order(String id, String customerId, String shippingAddress) {}
    record Address(String line1, String city) {}

    static final Map<String, Address> ADDRESS_DB = Map.of(
        "CUST-1", new Address("221B Baker St", "London"));

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel afterHeaderEnrich = new DirectChannel();
        DirectChannel afterContentEnrich = new DirectChannel();

        afterContentEnrich.subscribe(m -> System.out.println(
            "Final: " + m.getPayload() + " | source=" + m.getHeaders().get("source")));

        // Stage 2: content enricher, with a fallback for a failed lookup
        afterHeaderEnrich.subscribe(m -> {
            Order order = (Order) m.getPayload();
            Address address = ADDRESS_DB.get(order.customerId());
            Order enriched = (address != null)
                ? new Order(order.id(), order.customerId(), address.line1() + ", " + address.city())
                : new Order(order.id(), order.customerId(), "ADDRESS UNKNOWN — needs manual review");
            afterContentEnrich.send(MessageBuilder.fromMessage(m).setPayload(enriched).build());
        });

        // Stage 1: header enricher, always succeeds, purely local
        orders.subscribe(m -> afterHeaderEnrich.send(MessageBuilder.fromMessage(m)
            .setHeader("receivedAt", Instant.now().toString())
            .setHeader("source", "web")
            .build()));

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", "CUST-1", null)).build());   // lookup succeeds
        orders.send(MessageBuilder.withPayload(new Order("ORD-2", "CUST-UNKNOWN", null)).build()); // lookup fails
    }
}
```

How to run: `java CombinedEnrichmentPipelineDemo.java`. Expected output: `Final: Order[id=ORD-1, ..., shippingAddress=221B Baker St, London] | source=web` for the first order, and `Final: Order[id=ORD-2, ..., shippingAddress=ADDRESS UNKNOWN — needs manual review] | source=web` for the second — both orders got header enrichment unconditionally, but only the first got a successful content enrichment; the second fell back gracefully instead of the whole pipeline failing.

## 6. Walkthrough

Tracing `CombinedEnrichmentPipelineDemo` for the `ORD-2` message in execution order:

1. `orders.send(...)` for `Order[id=ORD-2, customerId=CUST-UNKNOWN, shippingAddress=null]` triggers the header-enricher-shaped subscriber.
2. The header enricher builds a new message from the original, adding `receivedAt` and `source` headers while keeping the `Order` payload completely unchanged — this stage cannot meaningfully fail; it's pure local computation.
3. The enriched message (same payload, new headers) is sent to `afterHeaderEnrich`, triggering the content-enricher-shaped subscriber.
4. The content enricher looks up `ADDRESS_DB.get("CUST-UNKNOWN")`, which returns `null` — the lookup found nothing, unlike `ORD-1`'s successful lookup.
5. Because `address` is `null`, the fallback branch constructs an `Order` with a stand-in shipping address value (`"ADDRESS UNKNOWN — needs manual review"`) instead of throwing or propagating a `null`, keeping the pipeline moving with a clearly-marked incomplete result rather than failing outright.
6. `MessageBuilder.fromMessage(m).setPayload(enriched).build()` preserves the headers set in step 2 (`receivedAt`, `source`) while replacing the payload — both the header-enrichment and content-enrichment results from the two stages are present in the final message received by `afterContentEnrich`'s subscriber.

```
Order(ORD-2, null address)
  --[Header enricher: always succeeds]--> Order(ORD-2, null address) + headers{receivedAt, source}
  --[Content enricher: lookup CUST-UNKNOWN -> null]--> fallback -> Order(ORD-2, "ADDRESS UNKNOWN...") + same headers
```

## 7. Gotchas & takeaways

> A content enricher performing a synchronous lookup (a database call, an HTTP request to another service) on every message directly adds that lookup's latency to the flow's overall processing time — and if the lookup service is slow or down, the enricher (and anything waiting on it) is affected too. Treat a content enricher's external dependency with the same care as any other network call: timeouts, fallbacks (as shown above), and — for hot paths — consider whether the enrichment can be cached or made asynchronous.

- A header enricher adds/overwrites headers, leaving the payload untouched; a content enricher augments the payload itself, typically via a lookup to another source — both are specialized `Transformer` (card 0021) variants.
- Use a header enricher for metadata that's cheap, local, and doesn't change the message's actual content; use a content enricher when a payload is genuinely missing information it needs before downstream steps can use it.
- Content enrichment often involves a request/reply exchange to an external source (conceptually the same pattern `MessagingTemplate`, card 0016, provides), so it can fail or add latency in ways header enrichment typically can't.
- Always plan a fallback for a failed content-enrichment lookup — sending an incomplete payload through with a clear marker is often better than letting the entire pipeline fail on missing external data.
- Keeping enrichment as its own named step (separate from core transformation and business logic) makes it obvious, from the flow's structure alone, exactly where and why external data gets pulled in.
