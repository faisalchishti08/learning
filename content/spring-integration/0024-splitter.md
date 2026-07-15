---
card: spring-integration
gi: 24
slug: splitter
title: "Splitter"
---

## 1. What it is

`@Splitter` is the endpoint archetype (from card 0019's taxonomy) whose job is turning one incoming message into several outgoing messages — the mirror image of `Transformer` (card 0021), which always produces exactly one result. A splitter method typically returns a `Collection`, an array, or an `Iterable`; the framework sends each element as its own separate message to the output channel, individually, in sequence, automatically stamping correlation headers so a later step (an `Aggregator`, covered in a future card) can, if needed, recombine them.

## 2. Why & when

You reach for `Splitter` specifically when a single unit of incoming work genuinely needs to become multiple independent units of downstream processing:

- **A message's payload is a collection that needs per-item processing** — an order containing a list of line items, each needing its own inventory check — a `Splitter` turns the one order message into N line-item messages, each processed independently (and potentially concurrently, if the output channel is an `ExecutorChannel`, card 0013).
- **You want each downstream item to be independently retryable or routable** — if one line item fails validation, it shouldn't block or invalidate the others; splitting first means each item's failure is isolated to its own message.
- **A batch needs to become a stream** — a file containing many records arrives as one message, but downstream processing genuinely operates one record at a time — a `Splitter` is the boundary where "one file" becomes "many records," conceptually inverse to how a `Splitter`'s output could later be recombined by an `Aggregator`.

## 3. Core concept

Think of `Splitter` like a mail room opening a single envelope that contains a stack of separate letters, and routing each individual letter onward to its own recipient, rather than delivering the whole stack as one bundle. The envelope (the original message) is unpacked, each letter (a resulting message) becomes its own independent item to process, and each carries a marker (a correlation header) tying it back to the envelope it came from — useful later if anyone needs to know "which batch did this letter belong to."

```java
@Splitter(inputChannel = "orders", outputChannel = "lineItems")
public List<LineItem> split(Order order) {
    return order.lineItems(); // one Order in, N LineItem messages out
}
```

Each element of the returned `List<LineItem>` becomes its own separate `Message<LineItem>` sent individually to `lineItems` — the subscriber on `lineItems` sees N separate invocations, not one invocation with a list payload.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitter turns one incoming message with a collection payload into several separate outgoing messages, each carrying one element and a correlation header">
  <rect x="20" y="70" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1 message</text>
  <text x="80" y="107" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">payload: List&lt;LineItem&gt;</text>

  <line x1="140" y1="95" x2="200" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#sp1)"/>

  <rect x="210" y="65" width="120" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Splitter</text>
  <text x="270" y="107" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one -&gt; many</text>

  <line x1="330" y1="80" x2="400" y2="30" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sp2)"/>
  <line x1="330" y1="95" x2="400" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sp2)"/>
  <line x1="330" y1="110" x2="400" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sp2)"/>

  <rect x="410" y="10" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="32" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LineItem #1</text>

  <rect x="410" y="78" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LineItem #2</text>

  <rect x="410" y="143" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="165" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LineItem #3</text>

  <defs>
    <marker id="sp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sp2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

One incoming message becomes N independent outgoing messages, each carrying one element and (in a real splitter) correlation headers linking it back to the original.

## 5. Runnable example

The scenario: an order containing multiple line items, starting with a basic split into individual messages, then correlation headers linking each item back to its origin, and finally each split item independently processed with isolated failure handling.

### Level 1 — Basic

```java
// BasicSplitterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.List;

public class BasicSplitterDemo {
    record LineItem(String sku, int quantity) {}
    record Order(String id, List<LineItem> lineItems) {}

    static List<LineItem> split(Order order) { // the splitter's actual logic
        return order.lineItems();
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel lineItems = new DirectChannel();
        lineItems.subscribe(m -> System.out.println("Processing line item: " + m.getPayload()));

        // what @Splitter(inputChannel="orders", outputChannel="lineItems") does for you:
        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            for (LineItem item : split(order)) {
                lineItems.send(MessageBuilder.withPayload(item).build()); // ONE message PER element
            }
        });

        Order order = new Order("ORD-1", List.of(
            new LineItem("SKU-A", 2), new LineItem("SKU-B", 1), new LineItem("SKU-C", 5)));
        orders.send(MessageBuilder.withPayload(order).build());
    }
}
```

How to run: `java BasicSplitterDemo.java`. Expected output: three separate lines, `Processing line item: LineItem[sku=SKU-A, quantity=2]`, then `SKU-B`, then `SKU-C` — one `Order` message became three independent `LineItem` messages, each individually received by the subscriber.

### Level 2 — Intermediate

A real splitter automatically stamps `correlationId` and `sequenceNumber`/`sequenceSize` headers on each resulting message, so downstream processing (or a later `Aggregator`) can identify which original message a given item came from and where it fits in the sequence.

```java
// CorrelatedSplitterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.List;
import java.util.UUID;

public class CorrelatedSplitterDemo {
    record LineItem(String sku, int quantity) {}
    record Order(String id, List<LineItem> lineItems) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel lineItems = new DirectChannel();
        lineItems.subscribe(m -> System.out.println(
            "Item " + m.getHeaders().get("sequenceNumber") + "/" + m.getHeaders().get("sequenceSize")
            + " (correlationId=" + m.getHeaders().get("correlationId") + "): " + m.getPayload()));

        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            String correlationId = UUID.randomUUID().toString().substring(0, 8);
            List<LineItem> items = order.lineItems();
            for (int i = 0; i < items.size(); i++) {
                lineItems.send(MessageBuilder.withPayload(items.get(i))
                    .setHeader("correlationId", correlationId)   // ties every item back to this ORDER
                    .setHeader("sequenceNumber", i + 1)
                    .setHeader("sequenceSize", items.size())
                    .build());
            }
        });

        Order order = new Order("ORD-1", List.of(
            new LineItem("SKU-A", 2), new LineItem("SKU-B", 1)));
        orders.send(MessageBuilder.withPayload(order).build());
    }
}
```

How to run: `java CorrelatedSplitterDemo.java`. Expected output: `Item 1/2 (correlationId=XXXXXXXX): LineItem[sku=SKU-A, quantity=2]` then `Item 2/2 (correlationId=XXXXXXXX): LineItem[sku=SKU-B, quantity=1]`, both sharing the *same* correlation ID — proving each split item still carries enough metadata to be traced back to the original order it came from, and to be recombined later if needed.

### Level 3 — Advanced

Each split item processed independently means one item's failure doesn't affect the others — shown here by a downstream handler that fails for one specific SKU, while the remaining items still process successfully, each failure/success isolated to its own message.

```java
// IsolatedFailureSplitterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.List;

public class IsolatedFailureSplitterDemo {
    record LineItem(String sku, int quantity) {}
    record Order(String id, List<LineItem> lineItems) {}

    static void checkInventory(LineItem item) { // simulated downstream processing that can fail per-item
        if (item.quantity() > 3) {
            throw new IllegalStateException("Insufficient inventory for " + item.sku());
        }
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel lineItems = new DirectChannel();

        lineItems.subscribe(m -> {
            LineItem item = (LineItem) m.getPayload();
            try {
                checkInventory(item);
                System.out.println("OK: " + item + " passed inventory check");
            } catch (Exception e) {
                System.out.println("FAILED (isolated, others unaffected): " + item + " -> " + e.getMessage());
            }
        });

        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            for (LineItem item : order.lineItems()) {
                lineItems.send(MessageBuilder.withPayload(item).build());
            }
        });

        Order order = new Order("ORD-1", List.of(
            new LineItem("SKU-A", 2),  // passes
            new LineItem("SKU-B", 10), // fails
            new LineItem("SKU-C", 1))); // passes, UNAFFECTED by SKU-B's failure
        orders.send(MessageBuilder.withPayload(order).build());
    }
}
```

How to run: `java IsolatedFailureSplitterDemo.java`. Expected output: `OK: LineItem[sku=SKU-A, quantity=2] passed inventory check`, then `FAILED (isolated, others unaffected): LineItem[sku=SKU-B, quantity=10] -> Insufficient inventory for SKU-B`, then `OK: LineItem[sku=SKU-C, quantity=1] passed inventory check` — `SKU-C` processes successfully despite `SKU-B` failing immediately before it, because splitting made each line item an independent message with its own isolated processing.

## 6. Walkthrough

Tracing `IsolatedFailureSplitterDemo` in execution order:

1. `orders.send(...)` delivers the single `Order` message (containing three line items) to the splitter's subscriber.
2. The splitter iterates `order.lineItems()` and calls `lineItems.send(...)` three times, once per item — each call is a completely separate `send()` invocation, producing three independent messages, not one message with a list payload.
3. Because `lineItems` is a `DirectChannel`, each `send()` synchronously dispatches to the downstream subscriber before the splitter's loop moves to the next item — so `SKU-A`'s full processing (try/catch and print) completes before `SKU-B`'s message is even sent.
4. For `SKU-A` (quantity 2), `checkInventory` doesn't throw, so the `try` block completes and `OK: ...` is printed.
5. For `SKU-B` (quantity 10), `checkInventory` throws `IllegalStateException`; this is caught locally within *that message's own processing*, printed as a failure — critically, this exception is scoped to `SKU-B`'s handling only, and does not propagate back up into the splitter's loop or affect the messages before or after it.
6. The splitter's loop, unaffected by `SKU-B`'s downstream failure (which happened inside a `try`/`catch` at the subscriber, not inside the splitter itself), proceeds to send `SKU-C`'s message, which passes its own inventory check independently.

```
Order[lineItems=[SKU-A(2), SKU-B(10), SKU-C(1)]]
  --[Splitter]--> LineItem(SKU-A,2) -> checkInventory OK   -> "OK: SKU-A..."
              --> LineItem(SKU-B,10)-> checkInventory THROWS -> caught locally -> "FAILED: SKU-B..."
              --> LineItem(SKU-C,1) -> checkInventory OK   -> "OK: SKU-C..." (UNAFFECTED by SKU-B)
```

## 7. Gotchas & takeaways

> Splitting a large collection into many individual messages on a synchronous channel like `DirectChannel` processes them strictly one at a time, on the sender's own thread — there's no parallelism gained just from splitting. If the point of splitting is to process items concurrently, the output channel needs to be something like `ExecutorChannel` (card 0013), not a plain `DirectChannel`; splitting alone only changes *how many messages* exist, not *how they're dispatched*.

- `@Splitter` turns one incoming message into several independent outgoing messages, one per element of a returned collection/array/iterable — the mirror image of `Transformer`'s (card 0021) always-one-result behavior.
- Use it when a batch or collection payload needs to become individually processable, independently retryable, or independently routable units.
- A real splitter automatically stamps correlation and sequence headers on each resulting message, preserving a link back to the original message and its position within the split.
- Splitting isolates failures to individual items — one item's downstream error doesn't prevent siblings split from the same original message from processing successfully.
- Splitting alone doesn't grant concurrency; pair it with a concurrency-providing output channel (`ExecutorChannel`, card 0013) if parallel processing of split items is actually the goal.
