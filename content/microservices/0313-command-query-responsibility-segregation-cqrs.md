---
card: microservices
gi: 313
slug: command-query-responsibility-segregation-cqrs
title: "Command Query Responsibility Segregation (CQRS)"
---

## 1. What it is

CQRS is the architectural principle of using entirely separate models — and often entirely separate code paths, and even separate databases — for writing data (commands, which change state) versus reading it (queries, which return state without changing it). Rather than one unified model serving both, the write side is optimized for correctly validating and applying changes, while the read side is optimized purely for serving the specific shapes of data readers actually need, as fast as possible.

## 2. Why & when

A single, shared model for both reads and writes forces a compromise: the model needs to represent enough structure and validation logic to safely handle every kind of write, while also being shaped in a way that's efficient to query for every kind of read a client might need — and those two sets of requirements often pull in genuinely different directions. A write model for placing an order needs strict validation, business rule enforcement, and transactional consistency around a handful of fields; a read model for displaying an order history page might want a completely different, denormalized shape combining data from several sources, pre-joined and pre-formatted purely for fast, direct display.

CQRS separates these concerns: the command side stays focused and strict, handling only validated state changes; the read side (see [CQRS read models](0314-cqrs-read-models-materialized-views.md)) can be shaped however is most convenient for reading — often multiple different read models, each optimized for a specific query pattern, kept updated asynchronously from the command side via events. Use CQRS when read and write patterns for the same conceptual data genuinely diverge significantly — different shapes, different scaling needs, different query patterns — not as a default for every piece of data, since maintaining separate models (and the synchronization between them) adds real complexity that isn't justified when reads and writes are simple and closely aligned.

## 3. Core concept

Commands are handled by a write model focused on validation and correctness; queries are served by a separately-maintained read model, shaped purely for efficient reading.

```java
// COMMAND side: strict, validated, focused purely on correctly applying a change.
@Service
class OrderCommandService {
    public void placeOrder(PlaceOrderCommand command) {
        validate(command); // business rules enforced HERE
        Order order = new Order(command.customerId(), command.lines());
        orderWriteRepository.save(order); // WRITE-optimized model
        eventPublisher.publish(new OrderPlacedEvent(order)); // triggers read-model updates ASYNCHRONOUSLY
    }
}

// QUERY side: a SEPARATE, denormalized model, shaped purely for fast reads.
@Service
class OrderQueryService {
    public OrderSummaryView getOrderSummary(String orderId) {
        return orderReadModelRepository.findSummaryById(orderId); // READ-optimized, pre-joined, denormalized
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A command enters the write model, which validates it and applies the change, publishing an event; a separate read model, updated asynchronously by that event, is what queries actually read from, allowing the write and read sides to be shaped completely independently for their own distinct purposes">
  <rect x="30" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">COMMAND side</text>
  <text x="120" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">validated writes, strict model</text>

  <rect x="430" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">QUERY side</text>
  <text x="520" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">denormalized, read-optimized model</text>

  <line x1="210" y1="55" x2="430" y2="55" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr313)"/>
  <text x="320" y="45" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">event, ASYNCHRONOUS</text>

  <text x="120" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">writes go HERE</text>
  <text x="520" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reads go HERE</text>

  <defs><marker id="arr313" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Writes flow through a strict, validated command model; reads are served from a separately-shaped, asynchronously-updated model.

## 5. Runnable example

Scenario: a single unified model straining to serve both a strict write path and an awkward, expensive read path, extended to genuinely separate command and query models with the query side pre-shaped for fast reads, and finally the asynchronous event-driven bridge that keeps the read model updated after each command, the actual mechanism connecting the two sides.

### Level 1 — Basic

```java
// File: UnifiedModelStrain.java -- ONE model serves both writing orders
// (needs validation) and reading a summary view (needs joined,
// formatted data) -- the read path has to do expensive work EVERY TIME
// because there is no separately-shaped read model.
import java.util.*;

public class UnifiedModelStrain {
    record OrderLine(String sku, int quantity) {}
    record Order(String id, String customerId, List<OrderLine> lines) {}

    static Map<String, String> productNames = Map.of("sku-1", "Wireless Mouse");
    static Map<String, String> customerNames = Map.of("cust-1", "Alice");
    static Map<String, Order> orders = new HashMap<>();

    static void placeOrder(Order order) {
        // validation would go here in a real system
        orders.put(order.id(), order);
    }

    // The READ path has to do ALL the joining/formatting work, EVERY TIME
    // it's called, because there's no separately maintained read model.
    static String getOrderSummary(String orderId) {
        Order order = orders.get(orderId);
        String customerName = customerNames.get(order.customerId()); // JOIN #1, done on EVERY read
        StringBuilder items = new StringBuilder();
        for (OrderLine line : order.lines()) {
            items.append(line.quantity()).append("x ").append(productNames.get(line.sku())).append(" "); // JOIN #2, EVERY read
        }
        return customerName + "'s order: " + items.toString().trim();
    }

    public static void main(String[] args) {
        placeOrder(new Order("order-1", "cust-1", List.of(new OrderLine("sku-1", 2))));
        System.out.println(getOrderSummary("order-1") + " -- this expensive joining/formatting repeats on EVERY read of EVERY order.");
    }
}
```

How to run: `java UnifiedModelStrain.java`

`getOrderSummary` re-does the same joins and formatting work — looking up customer name, looking up each line's product name, building a display string — every single time it's called, for every order, because there is no separate model pre-shaped for this specific read. For a high-traffic order-history page, this repeated work adds up significantly.

### Level 2 — Intermediate

```java
// File: SeparateCommandAndQueryModels.java -- the WRITE side stays
// strict and simple; a SEPARATE read model stores a PRE-BUILT, already
// formatted summary, so reads become a trivial lookup instead of
// repeated joining/formatting work.
import java.util.*;

public class SeparateCommandAndQueryModels {
    record OrderLine(String sku, int quantity) {}
    record Order(String id, String customerId, List<OrderLine> lines) {}

    static Map<String, String> productNames = Map.of("sku-1", "Wireless Mouse");
    static Map<String, String> customerNames = Map.of("cust-1", "Alice");

    // COMMAND side: strict write model.
    static Map<String, Order> orderWriteModel = new HashMap<>();

    // QUERY side: SEPARATE, pre-built, read-optimized model.
    static Map<String, String> orderReadModel = new HashMap<>();

    static void placeOrder(Order order) {
        orderWriteModel.put(order.id(), order); // write side: just the strict, validated data

        // Build the read-optimized summary ONCE, at write time, not on every read.
        String customerName = customerNames.get(order.customerId());
        StringBuilder items = new StringBuilder();
        for (OrderLine line : order.lines()) {
            items.append(line.quantity()).append("x ").append(productNames.get(line.sku())).append(" ");
        }
        orderReadModel.put(order.id(), customerName + "'s order: " + items.toString().trim());
    }

    static String getOrderSummary(String orderId) {
        return orderReadModel.get(orderId); // trivial lookup, NO joining/formatting at read time
    }

    public static void main(String[] args) {
        placeOrder(new Order("order-1", "cust-1", List.of(new OrderLine("sku-1", 2))));
        System.out.println(getOrderSummary("order-1") + " -- a TRIVIAL lookup, all the join/format work happened ONCE, at write time.");
    }
}
```

How to run: `java SeparateCommandAndQueryModels.java`

`orderWriteModel` and `orderReadModel` are two entirely separate structures. `placeOrder` (the command side) does its normal write plus, in this synchronous simplified version, immediately builds the pre-formatted read model entry. `getOrderSummary` (the query side) is now a trivial map lookup with no joining or formatting work at read time — the expensive work happened exactly once, at write time, rather than repeatedly on every read.

### Level 3 — Advanced

```java
// File: EventDrivenReadModelUpdate.java -- the REALISTIC CQRS shape: the
// command side publishes an event after writing, and the read model is
// updated ASYNCHRONOUSLY by a separate listener reacting to that event
// -- not synchronously inline with the write, which is how real CQRS
// systems decouple the two sides (and how the read model can lag
// slightly behind the write, i.e. eventual consistency).
import java.util.*;
import java.util.concurrent.*;

public class EventDrivenReadModelUpdate {
    record OrderLine(String sku, int quantity) {}
    record Order(String id, String customerId, List<OrderLine> lines) {}
    record OrderPlacedEvent(Order order) {}

    static Map<String, String> productNames = Map.of("sku-1", "Wireless Mouse");
    static Map<String, String> customerNames = Map.of("cust-1", "Alice");
    static Map<String, Order> orderWriteModel = new ConcurrentHashMap<>();
    static Map<String, String> orderReadModel = new ConcurrentHashMap<>();

    static List<java.util.function.Consumer<OrderPlacedEvent>> eventListeners = new ArrayList<>();

    // COMMAND side: writes, then PUBLISHES an event -- does NOT build the read model itself.
    static void placeOrder(Order order) {
        orderWriteModel.put(order.id(), order);
        OrderPlacedEvent event = new OrderPlacedEvent(order);
        for (var listener : eventListeners) {
            CompletableFuture.runAsync(() -> listener.accept(event)); // ASYNCHRONOUS -- decoupled from the write itself
        }
    }

    // READ MODEL UPDATER: a separate listener, reacting to the event,
    // builds the read-optimized summary -- this is where the "join" logic lives now.
    static void onOrderPlaced(OrderPlacedEvent event) {
        Order order = event.order();
        String customerName = customerNames.get(order.customerId());
        StringBuilder items = new StringBuilder();
        for (OrderLine line : order.lines()) items.append(line.quantity()).append("x ").append(productNames.get(line.sku())).append(" ");
        orderReadModel.put(order.id(), customerName + "'s order: " + items.toString().trim());
    }

    static String getOrderSummary(String orderId) { return orderReadModel.getOrDefault(orderId, "(not yet available in read model)"); }

    public static void main(String[] args) throws InterruptedException {
        eventListeners.add(EventDrivenReadModelUpdate::onOrderPlaced);

        placeOrder(new Order("order-1", "cust-1", List.of(new OrderLine("sku-1", 2))));

        // Immediately after placing the order, the read model may NOT be updated yet --
        // this is the eventual consistency window CQRS accepts.
        System.out.println("Immediately after placeOrder(): " + getOrderSummary("order-1"));

        Thread.sleep(50); // give the async event listener time to run
        System.out.println("After the event listener has run: " + getOrderSummary("order-1"));
    }
}
```

How to run: `java EventDrivenReadModelUpdate.java`

`placeOrder` writes to `orderWriteModel` and publishes an `OrderPlacedEvent`, but does *not* itself build the read model — that responsibility now lives entirely in `onOrderPlaced`, a separate listener triggered asynchronously via `CompletableFuture.runAsync`. Because this dispatch is asynchronous, checking `getOrderSummary` immediately after `placeOrder` returns can show the read model not yet updated (a real, observable eventual-consistency window), while checking again after a short delay shows the fully-built summary once the listener has had a chance to run. This is the realistic CQRS shape: the command side and the read-model-building logic are decoupled by an event, and the read side may briefly lag behind the write side, which is the deliberate tradeoff CQRS makes in exchange for keeping the write and read models genuinely independent.

## 6. Walkthrough

Trace `EventDrivenReadModelUpdate.main` in order. **First**, `eventListeners` is populated with `onOrderPlaced` as the sole registered listener.

**`placeOrder(new Order(...))` is called.** Inside, `orderWriteModel.put("order-1", order)` executes synchronously and immediately — the command side's write completes right away. Then, an `OrderPlacedEvent` is constructed, and for each listener (just `onOrderPlaced` here), `CompletableFuture.runAsync(() -> listener.accept(event))` is called — this schedules the listener to run on a background thread pool and returns *immediately*, without waiting for the listener to actually execute. `placeOrder` itself returns right after this scheduling, having done no read-model work at all.

**`getOrderSummary("order-1")` is called immediately after `placeOrder` returns.** Because the background task scheduled a moment ago may not have run yet — it's racing against the main thread's very next line of code — `orderReadModel.getOrDefault("order-1", "(not yet available...)")` may well still find no entry for `"order-1"`, printing the "not yet available" fallback. This is not a bug; it's the real, observable eventual-consistency window CQRS accepts: the write has definitely succeeded, but the read model has not necessarily caught up yet.

**`Thread.sleep(50)` gives the background task time to actually run.** During this pause, the scheduled `onOrderPlaced(event)` call executes on its background thread: it extracts `order` from the event, looks up `customerName`, builds the formatted `items` string by iterating `order.lines()`, and calls `orderReadModel.put("order-1", ...)`, populating the read model with the fully composed summary.

**`getOrderSummary("order-1")` is called again**, and this time `orderReadModel` does contain an entry for `"order-1"` (the background task has had time to complete), so the fully-formatted summary string is returned and printed.

```
placeOrder() -- write model updated SYNCHRONOUSLY, event SCHEDULED asynchronously, method returns immediately
        |
        v (race: which happens first?)
getOrderSummary() called RIGHT AWAY -- read model MAY NOT be updated yet -- "(not yet available)"
        |
        v (async listener runs on a background thread, ~milliseconds later)
onOrderPlaced() builds the read model entry
        |
        v
getOrderSummary() called AGAIN, after a pause -- read model IS updated -- full summary returned
```

## 7. Gotchas & takeaways

> The eventual-consistency window between a command completing and its corresponding read model reflecting that change is real and observable, as this topic's Level 3 example directly demonstrates — code that reads immediately after writing and assumes it will see its own write reflected in the read model can encounter surprising, intermittent bugs if this window isn't accounted for.

- CQRS is justified when read and write shapes/patterns for the same data genuinely diverge significantly — it adds real complexity (a synchronization mechanism, eventual consistency to reason about) that isn't worth paying when reads and writes are simple and closely aligned.
- The command side should stay focused on correctness (validation, business rules, transactional writes); the read side should be shaped purely for the specific queries it needs to serve efficiently, independent of the write model's shape.
- The bridge between the two sides is almost always asynchronous (typically events), which is what introduces eventual consistency — a deliberate, accepted tradeoff in exchange for the two sides' independence, not an accidental flaw.
- See [CQRS read models / materialized views](0314-cqrs-read-models-materialized-views.md) for how the read side itself is typically built, and [keeping read models in sync via events](0315-keeping-read-models-in-sync-via-events.md) for the mechanics of the asynchronous bridge shown in Level 3.
