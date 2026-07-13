---
card: microservices
gi: 321
slug: choreography-based-saga
title: "Choreography-based saga"
---

## 1. What it is

A **choreography-based saga** coordinates a multi-step [saga](0320-saga-pattern.md) with no central coordinator at all: each service does its own local transaction, then publishes an event describing what happened, and other services subscribe to the events they care about and react by doing their own next step. Coordination logic is spread across the services themselves — like dancers who each know their own steps and cues, rather than a choreographer directing them from the center.

## 2. Why & when

Choreography is the natural first choice when a saga has few steps and the services involved already communicate via events, building directly on asynchronous, event-driven communication between services. It avoids introducing a new coordinating component, keeps services maximally decoupled (a service only needs to know which events to listen for and which to publish, not who else is involved), and lets you add a new participant to the saga just by having it subscribe to an existing event — no change to any other service required.

The tradeoff shows up as the saga grows: with many steps, understanding "what happens when an order is placed" means tracing subscriptions across every service's codebase, since no single place shows the whole flow. Once that becomes hard to reason about, teams typically switch to an [orchestration-based saga](0322-orchestration-based-saga.md), which centralizes the flow in one place at the cost of a new coordinating component.

## 3. Core concept

Every step publishes an event; the next service(s) in the flow are simply subscribers to that event, and they publish their own event when done, continuing the chain. A failure anywhere publishes a "failed" event instead, and every earlier participant that subscribed to that failure event runs its own compensation independently.

```java
// Each service reacts to events; NONE of them knows the "whole" saga.
@EventListener void on(OrderPlacedEvent e)      { reserveStock(e.orderId()); publish(new StockReservedEvent(e.orderId())); }
@EventListener void on(StockReservedEvent e)    { chargePayment(e.orderId()); }
@EventListener void on(PaymentFailedEvent e)    { releaseStock(e.orderId()); } // compensation, reacting to a DIFFERENT service's failure
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service publishes OrderPlaced; inventory service reacts by reserving stock and publishing StockReserved; payment service reacts and publishes PaymentFailed; inventory service reacts to that failure by releasing stock -- no central coordinator anywhere">
  <rect x="20" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <rect x="240" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="315" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Inventory Service</text>
  <rect x="460" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="535" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Payment Service</text>

  <line x1="170" y1="37" x2="235" y2="37" stroke="#8b949e" marker-end="url(#a321)"/>
  <text x="200" y="27" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OrderPlaced</text>
  <line x1="390" y1="37" x2="455" y2="37" stroke="#8b949e" marker-end="url(#a321)"/>
  <text x="420" y="27" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">StockReserved</text>

  <line x1="460" y1="60" x2="315" y2="110" stroke="#f85149" marker-end="url(#a321b)"/>
  <text x="400" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">PaymentFailed</text>

  <rect x="240" y="120" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="315" y="142" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Inventory: release stock</text>
  <text x="320" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No central coordinator -- every arrow is a service reacting to an event it subscribed to</text>

  <defs>
    <marker id="a321" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a321b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Each service reacts to events it subscribes to and publishes its own; the saga's flow emerges from these independent reactions, not from one central script.

## 5. Runnable example

Scenario: a three-service order saga implemented via choreography — order, inventory, and payment services each only know their own event subscriptions — first shown succeeding, then extended to fail at payment and compensate via events, and finally hardened against a duplicate event causing a service to react twice.

### Level 1 — Basic

```java
// File: ChoreographySagaHappyPath.java -- three "services" (just classes
// here) each subscribe to one event and publish the next; no coordinator.
import java.util.*;
import java.util.function.Consumer;

public class ChoreographySagaHappyPath {
    interface Event {}
    record OrderPlaced(String orderId) implements Event {}
    record StockReserved(String orderId) implements Event {}
    record PaymentCharged(String orderId) implements Event {}

    static Map<Class<?>, List<Consumer<Event>>> subscribers = new HashMap<>();
    static void subscribe(Class<?> type, Consumer<Event> handler) {
        subscribers.computeIfAbsent(type, k -> new ArrayList<>()).add(handler);
    }
    static void publish(Event event) {
        subscribers.getOrDefault(event.getClass(), List.of()).forEach(h -> h.accept(event));
    }

    public static void main(String[] args) {
        // Inventory service's own subscription -- it doesn't know about payment at all.
        subscribe(OrderPlaced.class, e -> {
            OrderPlaced ev = (OrderPlaced) e;
            System.out.println("inventory: reserving stock for " + ev.orderId());
            publish(new StockReserved(ev.orderId()));
        });
        // Payment service's own subscription -- it doesn't know about order-placement directly.
        subscribe(StockReserved.class, e -> {
            StockReserved ev = (StockReserved) e;
            System.out.println("payment: charging card for " + ev.orderId());
            publish(new PaymentCharged(ev.orderId()));
        });
        subscribe(PaymentCharged.class, e ->
                System.out.println("order: saga complete for " + ((PaymentCharged) e).orderId()));

        publish(new OrderPlaced("order-1")); // order service kicks off the chain
    }
}
```

How to run: `java ChoreographySagaHappyPath.java`

`publish(new OrderPlaced("order-1"))` is the only line the "order service" needs to run — it has no idea inventory or payment even exist. Each subscriber reacts only to the event type it registered for, and the chain unfolds purely through publish/subscribe: `OrderPlaced` triggers inventory's handler, which publishes `StockReserved`, which triggers payment's handler, which publishes `PaymentCharged`, which triggers the final completion log.

### Level 2 — Intermediate

```java
// File: ChoreographySagaCompensation.java -- payment FAILS; inventory
// subscribes to the failure event and compensates on its OWN, with no
// coordinator telling it to.
import java.util.*;
import java.util.function.Consumer;

public class ChoreographySagaCompensation {
    interface Event {}
    record OrderPlaced(String orderId) implements Event {}
    record StockReserved(String orderId) implements Event {}
    record PaymentFailed(String orderId) implements Event {}

    static Map<Class<?>, List<Consumer<Event>>> subscribers = new HashMap<>();
    static void subscribe(Class<?> type, Consumer<Event> handler) {
        subscribers.computeIfAbsent(type, k -> new ArrayList<>()).add(handler);
    }
    static void publish(Event event) {
        subscribers.getOrDefault(event.getClass(), List.of()).forEach(h -> h.accept(event));
    }

    public static void main(String[] args) {
        subscribe(OrderPlaced.class, e -> {
            System.out.println("inventory: reserving stock for " + ((OrderPlaced) e).orderId());
            publish(new StockReserved(((OrderPlaced) e).orderId()));
        });
        subscribe(StockReserved.class, e -> {
            System.out.println("payment: attempting charge for " + ((StockReserved) e).orderId());
            System.out.println("payment: card DECLINED");
            publish(new PaymentFailed(((StockReserved) e).orderId()));
        });
        // Inventory ALSO subscribes to the failure event -- its own compensation logic, independently.
        subscribe(PaymentFailed.class, e ->
                System.out.println("inventory: reacting to PaymentFailed -- releasing stock for "
                        + ((PaymentFailed) e).orderId() + " (COMPENSATION)"));

        publish(new OrderPlaced("order-1"));
    }
}
```

How to run: `java ChoreographySagaCompensation.java`

The chain runs the same way up through `StockReserved`, but payment's handler now publishes `PaymentFailed` instead of a success event. Inventory — the very service that reserved the stock — has *also* subscribed to `PaymentFailed`, and its handler runs the compensation (releasing the stock) entirely on its own initiative. No coordinator told inventory to do this; it simply reacts to an event it chose to subscribe to, which is both choreography's strength (full decoupling) and its risk (the compensation logic lives far from the code that did the original reservation).

### Level 3 — Advanced

```java
// File: ChoreographySagaIdempotent.java -- the SAME PaymentFailed event is
// delivered TWICE (a normal at-least-once messaging occurrence); the
// inventory handler must be IDEMPOTENT so it doesn't release stock twice
// or double-log a compensation that only happened once.
import java.util.*;
import java.util.function.Consumer;

public class ChoreographySagaIdempotent {
    interface Event { String orderId(); String eventId(); }
    record PaymentFailed(String orderId, String eventId) implements Event {}

    static Map<Class<?>, List<Consumer<Event>>> subscribers = new HashMap<>();
    static Set<String> processedEventIds = new HashSet<>(); // dedupe key across ALL handlers here
    static Map<String, Boolean> stockReleased = new HashMap<>(); // per-order compensation state

    static void subscribe(Class<?> type, Consumer<Event> handler) {
        subscribers.computeIfAbsent(type, k -> new ArrayList<>()).add(handler);
    }
    static void publish(Event event) {
        subscribers.getOrDefault(event.getClass(), List.of()).forEach(h -> h.accept(event));
    }

    public static void main(String[] args) {
        subscribe(PaymentFailed.class, e -> {
            PaymentFailed ev = (PaymentFailed) e;
            if (!processedEventIds.add(ev.eventId())) { // add() returns false if ALREADY present
                System.out.println("inventory: event " + ev.eventId() + " already processed -- SKIPPING duplicate delivery");
                return;
            }
            stockReleased.merge(ev.orderId(), true, (a, b) -> a); // idempotent: released exactly once regardless
            System.out.println("inventory: releasing stock for " + ev.orderId() + " (compensation applied)");
        });

        PaymentFailed event = new PaymentFailed("order-1", "evt-77");
        publish(event); // first delivery -- applied
        publish(event); // REDELIVERY -- messaging systems guarantee at-least-once, this WILL happen

        System.out.println("stockReleased for order-1: " + stockReleased.get("order-1")
                + " -- released exactly once, despite two deliveries.");
    }
}
```

How to run: `java ChoreographySagaIdempotent.java`

The `PaymentFailed` event for `order-1` is published twice, simulating a normal at-least-once redelivery. `processedEventIds.add(ev.eventId())` returns `true` only the first time `"evt-77"` is added and `false` on the second attempt (since `Set.add` reports whether the element was newly inserted); the handler uses that to skip the redelivery entirely, printing a "SKIPPING duplicate" message instead of releasing the stock a second time. The final `stockReleased` map correctly shows the compensation applied exactly once, even though the event physically arrived twice.

## 6. Walkthrough

Trace `ChoreographySagaIdempotent.main` in order. **First**, a single `PaymentFailed` event with `eventId="evt-77"` is constructed once and reused for both `publish` calls, simulating a message broker redelivering the exact same message.

**The first `publish(event)` call** invokes the subscribed handler. Inside, `processedEventIds.add("evt-77")` succeeds (the set didn't contain it) and returns `true`, so the `if` guard is skipped; the handler proceeds to `stockReleased.merge("order-1", true, ...)`, recording the compensation, and prints that stock was released.

**The second `publish(event)` call** invokes the same handler again with the identical event. This time `processedEventIds.add("evt-77")` returns `false` because `"evt-77"` is already in the set — the `if (!processedEventIds.add(...))` condition is now true, so the handler prints the "SKIPPING duplicate" message and returns immediately, never touching `stockReleased` again.

**Finally**, `main` prints `stockReleased.get("order-1")`, which is `true` — set exactly once, during the first delivery, and left untouched by the duplicate.

```
publish(PaymentFailed, evt-77) 1st -> processedEventIds.add() = true  -> compensation APPLIED
publish(PaymentFailed, evt-77) 2nd -> processedEventIds.add() = false -> SKIPPED (duplicate)
```

## 7. Gotchas & takeaways

> As a choreography-based saga grows past a handful of steps, tracing "what happens when an order is placed" requires reading subscription code scattered across every participating service — there is no single place that shows the whole flow. This is the main reason teams migrate to an [orchestration-based saga](0322-orchestration-based-saga.md) once a saga's step count grows.

- Every participating service must independently subscribe to the failure/compensation events it cares about — compensation logic is decentralized, just like the forward flow.
- Every handler must be idempotent, exactly as in any event-driven system, since messaging systems typically guarantee at-least-once delivery.
- Choreography keeps services maximally decoupled and lets new participants join by subscribing to existing events, at the cost of no centralized view of the overall saga.
- Contrast with [orchestration-based sagas](0322-orchestration-based-saga.md), which centralize the flow logic in one orchestrator component.
