---
card: microservices
gi: 153
slug: spring-integration-enterprise-integration-patterns
title: "Spring Integration enterprise integration patterns"
---

## 1. What it is

Spring Integration is a framework implementing the classic Enterprise Integration Patterns (EIP) catalog — reusable, named solutions to recurring messaging problems like Router (send a message down one of several paths based on content), Splitter (break one message into several), Aggregator (combine several messages into one), and Filter (drop messages that don't meet a condition) — as composable Java components wired together into an integration flow, independent of any specific messaging broker.

## 2. Why & when

Messaging integration logic that goes beyond simple produce/consume — routing an order to different handlers based on its region, splitting a bulk order into individual line-item messages, waiting for multiple related responses before proceeding — quickly becomes a tangle of custom conditional logic if hand-written from scratch each time. The EIP catalog names and standardizes these recurring shapes, and Spring Integration provides ready-made, tested, composable implementations of each pattern, so building "route by content, then split, then aggregate the results" becomes assembling well-known building blocks rather than inventing bespoke logic.

Reach for Spring Integration when an integration flow needs more than simple produce/consume — genuine content-based routing, splitting and re-aggregating messages, transformation chains, or bridging between different messaging systems (file, JMS, HTTP, a message broker) within one coherent flow definition. For a single, straightforward produce-transform-consume pipeline, [Spring Cloud Stream's functional model](0146-spring-cloud-stream-functional-programming-model-supplier-fu.md) is usually simpler and sufficient.

## 3. Core concept

An integration flow is built by composing named EIP components — a Router directs a message down one of multiple channels based on a routing function; a Splitter transforms one message into a collection, emitting each element as its own message; an Aggregator collects related messages (correlated by some key) until a completion condition is met, then emits one combined result.

```java
// mirrors Spring Integration's IntegrationFlow DSL, conceptually
IntegrationFlow orderFlow = IntegrationFlow.from("order-input")
    .route(order -> order.region(), r -> r  // ROUTER: dispatch by content
        .subFlowMapping("us", sf -> sf.channel("us-orders"))
        .subFlowMapping("eu", sf -> sf.channel("eu-orders")))
    .get();
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An order message enters a Router, which sends it down one of two channels based on region; each channel's messages could then flow through further Splitter or Aggregator components before reaching their final handler">
  <rect x="20" y="70" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="97" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Order message</text>

  <rect x="200" y="70" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="260" y="97" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Router (by region)</text>

  <rect x="380" y="20" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="44" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">us-orders channel</text>
  <rect x="380" y="130" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="154" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">eu-orders channel</text>

  <line x1="140" y1="92" x2="198" y2="92" stroke="#8b949e" marker-end="url(#arr34)"/>
  <line x1="320" y1="82" x2="378" y2="45" stroke="#8b949e" marker-end="url(#arr34)"/>
  <line x1="320" y1="102" x2="378" y2="145" stroke="#8b949e" marker-end="url(#arr34)"/>

  <defs>
    <marker id="arr34" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The Router pattern decides a message's path entirely from its content, dispatching to one of several downstream channels.

## 5. Runnable example

Scenario: a bulk-order processing pipeline that starts with hand-written, tangled routing-and-splitting logic (the problem EIP components solve), refactors that logic into separate, composable Router and Splitter components mirroring Spring Integration's own building blocks, and finally adds an Aggregator that waits for and combines multiple related split results back into a single completion event.

### Level 1 — Basic

```java
// File: TangledRoutingAndSplitting.java -- routing AND splitting logic hand-written
// and mixed together, hard to reuse or reason about independently.
import java.util.*;

public class TangledRoutingAndSplitting {
    record BulkOrder(int orderId, String region, List<String> lineItems) {}

    public static void main(String[] args) {
        BulkOrder order = new BulkOrder(42, "us", List.of("widget", "gadget", "gizmo"));

        // routing decision AND splitting logic ALL tangled into one method
        if (order.region().equals("us")) {
            for (String item : order.lineItems()) {
                System.out.println("[us-orders handler] processing line item: " + item + " (order " + order.orderId() + ")");
            }
        } else if (order.region().equals("eu")) {
            for (String item : order.lineItems()) {
                System.out.println("[eu-orders handler] processing line item: " + item + " (order " + order.orderId() + ")");
            }
        }
        System.out.println("Adding a THIRD region means duplicating this whole if/else + loop structure again.");
    }
}
```

**How to run:** `javac TangledRoutingAndSplitting.java && java TangledRoutingAndSplitting` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RouterAndSplitterComponents.java -- routing and splitting refactored
// into SEPARATE, composable EIP-style components, mirroring Spring Integration's own patterns.
import java.util.*;
import java.util.function.*;

public class RouterAndSplitterComponents {
    record BulkOrder(int orderId, String region, List<String> lineItems) {}
    record LineItemMessage(int orderId, String item) {}

    // ROUTER: a reusable component that dispatches based on a content-derived key -- nothing else
    static class Router<T> {
        Map<String, Consumer<T>> routes = new HashMap<>();
        Function<T, String> keySelector;
        Router(Function<T, String> keySelector) { this.keySelector = keySelector; }
        void addRoute(String key, Consumer<T> handler) { routes.put(key, handler); }
        void route(T message) { routes.getOrDefault(keySelector.apply(message), m -> System.out.println("no route for: " + m)).accept(message); }
    }

    // SPLITTER: a reusable component that turns ONE message into MANY -- nothing else
    static class Splitter<T, R> {
        Function<T, List<R>> splitFunction;
        Consumer<R> downstream;
        Splitter(Function<T, List<R>> splitFunction, Consumer<R> downstream) { this.splitFunction = splitFunction; this.downstream = downstream; }
        void split(T message) { splitFunction.apply(message).forEach(downstream); }
    }

    public static void main(String[] args) {
        Consumer<LineItemMessage> lineItemHandler = msg -> System.out.println("  processing line item: " + msg.item() + " (order " + msg.orderId() + ")");

        Splitter<BulkOrder, LineItemMessage> splitter = new Splitter<>(
            order -> order.lineItems().stream().map(item -> new LineItemMessage(order.orderId(), item)).toList(),
            lineItemHandler);

        Router<BulkOrder> router = new Router<>(BulkOrder::region);
        router.addRoute("us", order -> { System.out.println("[us-orders]"); splitter.split(order); });
        router.addRoute("eu", order -> { System.out.println("[eu-orders]"); splitter.split(order); });

        router.route(new BulkOrder(42, "us", List.of("widget", "gadget", "gizmo")));
        System.out.println("Router and Splitter are SEPARATE, independently reusable components -- adding a region only needs one addRoute call.");
    }
}
```

**How to run:** `javac RouterAndSplitterComponents.java && java RouterAndSplitterComponents` (JDK 17+).

Expected output:
```
[us-orders]
  processing line item: widget (order 42)
  processing line item: gadget (order 42)
  processing line item: gizmo (order 42)
Router and Splitter are SEPARATE, independently reusable components -- adding a region only needs one addRoute call.
```

### Level 3 — Advanced

```java
// File: SplitterWithAggregator.java -- adds an AGGREGATOR that waits for ALL split
// line items to complete before emitting ONE combined "order fully processed" event.
import java.util.*;
import java.util.function.*;

public class SplitterWithAggregator {
    record BulkOrder(int orderId, List<String> lineItems) {}
    record LineItemMessage(int orderId, String item, int totalItemsInOrder) {}
    record LineItemProcessed(int orderId, String item) {}

    static class Splitter {
        Consumer<LineItemMessage> downstream;
        Splitter(Consumer<LineItemMessage> downstream) { this.downstream = downstream; }
        void split(BulkOrder order) {
            for (String item : order.lineItems()) downstream.accept(new LineItemMessage(order.orderId(), item, order.lineItems().size()));
        }
    }

    // AGGREGATOR: correlates related messages by orderId, waits until it has received
    // as many as expected, THEN emits ONE combined completion event
    static class Aggregator {
        Map<Integer, List<LineItemProcessed>> collectedByOrderId = new HashMap<>();
        Consumer<Integer> onOrderFullyProcessed;
        Aggregator(Consumer<Integer> onOrderFullyProcessed) { this.onOrderFullyProcessed = onOrderFullyProcessed; }

        void aggregate(LineItemProcessed processed, int expectedCount) {
            List<LineItemProcessed> collected = collectedByOrderId.computeIfAbsent(processed.orderId(), k -> new ArrayList<>());
            collected.add(processed);
            System.out.println("  [aggregator] collected " + collected.size() + "/" + expectedCount + " for order " + processed.orderId());
            if (collected.size() == expectedCount) { // COMPLETION CONDITION met -- emit the combined result
                onOrderFullyProcessed.accept(processed.orderId());
                collectedByOrderId.remove(processed.orderId()); // reset for any future order with the same id
            }
        }
    }

    public static void main(String[] args) {
        Aggregator aggregator = new Aggregator(orderId -> System.out.println("*** Order " + orderId + " FULLY PROCESSED -- all line items complete ***"));

        Consumer<LineItemMessage> lineItemHandler = msg -> {
            System.out.println("  processing line item: " + msg.item() + " (order " + msg.orderId() + ")");
            LineItemProcessed processed = new LineItemProcessed(msg.orderId(), msg.item());
            aggregator.aggregate(processed, msg.totalItemsInOrder()); // feed each split result INTO the aggregator
        };

        Splitter splitter = new Splitter(lineItemHandler);
        splitter.split(new BulkOrder(42, List.of("widget", "gadget", "gizmo")));
    }
}
```

**How to run:** `javac SplitterWithAggregator.java && java SplitterWithAggregator` (JDK 17+).

Expected output:
```
  processing line item: widget (order 42)
  [aggregator] collected 1/3 for order 42
  processing line item: gadget (order 42)
  [aggregator] collected 2/3 for order 42
  processing line item: gizmo (order 42)
  [aggregator] collected 3/3 for order 42
*** Order 42 FULLY PROCESSED -- all line items complete ***
```

## 6. Walkthrough

1. **Level 1** — the `if`/`else if` branches and the per-region `for` loop are all written inline in `main`, meaning both the routing decision and the splitting behavior would need to be copy-pasted and modified for any new region.
2. **Level 2, extracting the Router** — `Router<T>` knows only about mapping a key (derived by `keySelector`) to a registered handler; it has no knowledge of splitting, line items, or anything order-specific — it is a genuinely generic, reusable pattern implementation.
3. **Level 2, extracting the Splitter** — `Splitter<T, R>` knows only about applying a function that turns one input into a list, then forwarding each resulting element to a downstream consumer; it has no knowledge of regions or routing.
4. **Level 2, composing them together** — `router.addRoute("us", order -> { ...; splitter.split(order); })` connects the two independently-defined components, but neither component's own implementation needed to change to be combined this way.
5. **Level 3, the Aggregator's correlation** — `Aggregator.aggregate` uses `processed.orderId()` as the correlation key into `collectedByOrderId`, accumulating each `LineItemProcessed` result under that order's own growing list — this is analogous to Spring Integration's `CorrelationStrategy`.
6. **Level 3, the completion condition** — after adding the new result, `aggregate` checks `collected.size() == expectedCount`; `expectedCount` is threaded through from the original `BulkOrder.lineItems().size()` via `LineItemMessage.totalItemsInOrder()`, so the aggregator knows exactly how many results to wait for before considering the order complete — analogous to Spring Integration's `ReleaseStrategy`.
7. **Level 3, tracing the full flow** — `splitter.split` calls `lineItemHandler` three times (once per line item); each call processes the item, wraps it as a `LineItemProcessed`, and immediately feeds it into `aggregator.aggregate`; the first two calls print `"collected 1/3"` and `"collected 2/3"` without triggering completion, but the third call's `collected.size()` reaches `3`, matching `expectedCount`, which triggers `onOrderFullyProcessed` and prints the final combined completion event — demonstrating a Splitter and Aggregator working together as a matched pair, exactly the "split, process independently, recombine" shape the EIP catalog names and Spring Integration implements as ready-made, composable components.

## 7. Gotchas & takeaways

> **Gotcha:** an Aggregator waiting for a completion condition that never arrives (a split message lost, or one line item's processing permanently failing) will hold its partial state in memory indefinitely unless configured with a timeout or a discard policy — Spring Integration's `AggregatingMessageHandler` supports exactly this via a `group-timeout`, but it has to be configured deliberately, since the default behavior can otherwise leak memory on incomplete groups over time.

- Spring Integration provides composable, reusable implementations of the classic Enterprise Integration Patterns catalog — Router, Splitter, Aggregator, Filter, and others — independent of any specific messaging broker.
- Extracting routing and splitting logic into separate, single-purpose components (rather than tangled, hand-written conditional logic) makes each independently reusable and easier to reason about.
- The Splitter and Aggregator patterns are natural complements: Splitter breaks one message into many for independent, potentially parallel processing; Aggregator correlates and recombines related results back into one.
- An Aggregator needs both a correlation strategy (how to group related messages) and a completion/release strategy (when the group is considered done) to function correctly.
- Aggregators holding incomplete groups indefinitely, waiting for a completion condition that may never be met, are a real memory-leak risk unless a timeout or discard policy is deliberately configured.
