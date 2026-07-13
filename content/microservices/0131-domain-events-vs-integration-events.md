---
card: microservices
gi: 131
slug: domain-events-vs-integration-events
title: "Domain events vs integration events"
---

## 1. What it is

A domain event is something meaningful that happened inside a single service's own domain model, published in-process to other parts of that same service (see [Spring application events](0074-spring-application-events-applicationeventpublisher-for-in-process-domain-events.md)). An integration event is a deliberately separate, more stable message published *across* service boundaries, onto a shared [message channel](0115-message-channels.md), for other services to consume. Conflating the two — publishing a service's internal domain event directly onto the broker — is a common and costly mistake.

## 2. Why & when

A domain model evolves quickly and often: fields get renamed, new event types get added for internal use, internal invariants shift as the service's own logic matures — and none of that should be anyone else's problem. If a service's *internal* event structure is published directly to other services, every one of those routine internal refactorings becomes a breaking change for every external consumer, coupling the pace of one team's internal cleanup to the release schedules of every team downstream. Keeping domain events and integration events as two explicitly separate concepts — with a translation step between them — lets the internal model evolve freely while the external contract changes deliberately and rarely.

Always translate before crossing a service boundary. Publish domain events freely and internally for any change worth reacting to within the service (see [Spring Modulith domain events between modules](0073-spring-modulith-domain-events-between-modules.md) for the same idea applied to modules within one deployable). Only a curated, intentionally-designed subset of those, reshaped into a stable schema, should ever become an integration event.

## 3. Core concept

An internal handler listens for the rich, frequently-changing domain event and, only when appropriate, constructs and publishes a separate, deliberately stable integration event with its own schema, decoupling the two lifecycles entirely.

```java
// domain event: rich, internal, can change freely as the domain model evolves
record OrderDomainEvent(Order order, String triggeredByUserId, Instant occurredAt, Map<String, Object> internalMetadata) {}

// integration event: a DELIBERATE, separate, stable public contract
record OrderPlacedIntegrationEvent(int orderId, double total, String status) {}

// the translation step -- this is the actual design decision
void onOrderDomainEvent(OrderDomainEvent domainEvent) {
    if (domainEvent.order().status() == OrderStatus.PLACED) {
        publishToBroker(new OrderPlacedIntegrationEvent(
            domainEvent.order().id(), domainEvent.order().total(), "PLACED")); // only what's intended to be public
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inside order-service, a rich domain event fires in-process; a translation handler listens for it and publishes a separate, stable integration event onto the broker for other services to consume, keeping the internal domain model decoupled from the external contract">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="35" y="40" fill="#8b949e" font-size="8.5" font-family="sans-serif">order-service (internal)</text>

  <rect x="40" y="60" width="110" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Domain event</text>

  <rect x="170" y="60" width="110" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="225" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Translation</text>
  <text x="225" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">handler</text>

  <line x1="150" y1="82" x2="168" y2="82" stroke="#8b949e" marker-end="url(#arr17)"/>

  <rect x="370" y="60" width="220" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Integration event (broker)</text>
  <text x="480" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">stable, external contract</text>

  <line x1="300" y1="82" x2="368" y2="82" stroke="#8b949e" marker-end="url(#arr17)"/>

  <defs>
    <marker id="arr17" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The translation handler is the deliberate boundary between an internal model that can change freely and an external contract that shouldn't.

## 5. Runnable example

Scenario: an order service that starts by publishing its internal domain event directly to other services (showing the coupling problem), adds a translation layer producing a separate stable integration event, and finally demonstrates the payoff — the internal domain model changes substantially while the integration event's schema, and therefore every external consumer, remains completely unaffected.

### Level 1 — Basic

```java
// File: LeakedDomainEvent.java -- publishing the internal event directly: the mistake.
import java.time.*;
import java.util.*;

public class LeakedDomainEvent {
    record Order(int id, double total, String status, String internalWarehouseCode) {} // internal detail leaks
    record OrderDomainEvent(Order order, String triggeredByUserId, Instant occurredAt) {}

    public static void main(String[] args) {
        OrderDomainEvent domainEvent = new OrderDomainEvent(
            new Order(42, 99.90, "PLACED", "WH-INTERNAL-7"), "user-alice", Instant.now());

        // BAD: publishing the raw internal event straight to the broker
        publishToBroker(domainEvent);
        System.out.println("Every external consumer now depends on 'internalWarehouseCode' and 'triggeredByUserId' -- fields that were only ever meant for internal use.");
    }

    static void publishToBroker(Object event) { System.out.println("[broker] published: " + event); }
}
```

**How to run:** `javac LeakedDomainEvent.java && java LeakedDomainEvent` (JDK 17+).

The raw `OrderDomainEvent`, including `internalWarehouseCode` (a detail no external consumer should ever need to know exists), is now part of the public contract the moment any external service starts depending on it.

### Level 2 — Intermediate

```java
// File: TranslatedIntegrationEvent.java -- a translation handler produces a
// SEPARATE, stable integration event, decoupled from the internal domain model.
import java.time.*;
import java.util.*;
import java.util.function.*;

public class TranslatedIntegrationEvent {
    record Order(int id, double total, String status, String internalWarehouseCode) {}
    record OrderDomainEvent(Order order, String triggeredByUserId, Instant occurredAt) {}
    record OrderPlacedIntegrationEvent(int orderId, double total, String status) {} // deliberately minimal, public

    static class InProcessEventBus { // models a domain event published in-process
        List<Consumer<OrderDomainEvent>> handlers = new ArrayList<>();
        void subscribe(Consumer<OrderDomainEvent> h) { handlers.add(h); }
        void publish(OrderDomainEvent e) { handlers.forEach(h -> h.accept(e)); }
    }

    public static void main(String[] args) {
        InProcessEventBus internalBus = new InProcessEventBus();

        // the translation handler: the ONLY place that knows both the internal AND external shapes
        internalBus.subscribe(domainEvent -> {
            if (domainEvent.order().status().equals("PLACED")) {
                OrderPlacedIntegrationEvent integrationEvent = new OrderPlacedIntegrationEvent(
                    domainEvent.order().id(), domainEvent.order().total(), domainEvent.order().status());
                publishToBroker(integrationEvent); // internalWarehouseCode and triggeredByUserId never leave this service
            }
        });

        internalBus.publish(new OrderDomainEvent(
            new Order(42, 99.90, "PLACED", "WH-INTERNAL-7"), "user-alice", Instant.now()));
    }

    static void publishToBroker(Object event) { System.out.println("[broker] published: " + event); }
}
```

**How to run:** `javac TranslatedIntegrationEvent.java && java TranslatedIntegrationEvent` (JDK 17+).

Expected output:
```
[broker] published: OrderPlacedIntegrationEvent[orderId=42, total=99.9, status=PLACED]
```

Only the minimal, deliberate `OrderPlacedIntegrationEvent` reaches the broker; `internalWarehouseCode` and `triggeredByUserId` never leave `order-service`'s process.

### Level 3 — Advanced

```java
// File: InternalModelChangesFreelyOutsideUnaffected.java -- the domain model is
// substantially refactored; the integration event's schema, and its consumers, don't notice.
import java.time.*;
import java.util.*;
import java.util.function.*;

public class InternalModelChangesFreelyOutsideUnaffected {
    // REFACTORED internal domain model: 'status' is now a richer enum with more states,
    // 'internalWarehouseCode' was renamed AND a new 'fulfillmentPriority' field was added --
    // none of this should be an external consumer's problem
    enum OrderStatus { DRAFT, VALIDATED, PLACED, FULFILLING }
    record Order(int id, double total, OrderStatus status, String warehouseRoutingKey, int fulfillmentPriority) {}
    record OrderDomainEvent(Order order, Instant occurredAt) {}

    // the integration event's SCHEMA IS UNCHANGED from the previous version -- this is the whole point
    record OrderPlacedIntegrationEvent(int orderId, double total, String status) {}

    static class InProcessEventBus {
        List<Consumer<OrderDomainEvent>> handlers = new ArrayList<>();
        void subscribe(Consumer<OrderDomainEvent> h) { handlers.add(h); }
        void publish(OrderDomainEvent e) { handlers.forEach(h -> h.accept(e)); }
    }

    // this is an UNCHANGED external consumer -- written against the integration event schema,
    // has NO knowledge of the internal refactoring that just happened
    static void externalEmailServiceConsumer(OrderPlacedIntegrationEvent event) {
        System.out.println("[email-service, external, UNCHANGED] confirming order " + event.orderId() + ", total=" + event.total());
    }

    public static void main(String[] args) {
        InProcessEventBus internalBus = new InProcessEventBus();

        // the translation handler is updated to match the NEW internal model...
        internalBus.subscribe(domainEvent -> {
            if (domainEvent.order().status() == OrderStatus.PLACED) {
                OrderPlacedIntegrationEvent integrationEvent = new OrderPlacedIntegrationEvent(
                    domainEvent.order().id(), domainEvent.order().total(), domainEvent.order().status().name());
                publishToBroker(integrationEvent, InternalModelChangesFreelyOutsideUnaffected::externalEmailServiceConsumer);
            }
        });

        // ...but the PUBLIC SCHEMA it produces is byte-for-byte identical to before the refactor
        internalBus.publish(new OrderDomainEvent(
            new Order(42, 99.90, OrderStatus.PLACED, "ROUTE-KEY-B7", 3), Instant.now()));

        System.out.println("Internal model gained new fields (warehouseRoutingKey, fulfillmentPriority) and a richer enum.");
        System.out.println("externalEmailServiceConsumer required ZERO changes -- the integration contract never moved.");
    }

    static void publishToBroker(Object event, Consumer<OrderPlacedIntegrationEvent> deliverTo) {
        System.out.println("[broker] published: " + event);
        deliverTo.accept((OrderPlacedIntegrationEvent) event);
    }
}
```

**How to run:** `javac InternalModelChangesFreelyOutsideUnaffected.java && java InternalModelChangesFreelyOutsideUnaffected` (JDK 17+).

Expected output:
```
[broker] published: OrderPlacedIntegrationEvent[orderId=42, total=99.9, status=PLACED]
[email-service, external, UNCHANGED] confirming order 42, total=99.9
Internal model gained new fields (warehouseRoutingKey, fulfillmentPriority) and a richer enum.
externalEmailServiceConsumer required ZERO changes -- the integration contract never moved.
```

## 6. Walkthrough

1. **Level 1** — `LeakedDomainEvent.main` calls `publishToBroker(domainEvent)` directly on the raw `OrderDomainEvent`, which includes `internalWarehouseCode`; any external service subscribing to this now has a dependency on a field that was never meant to be part of any contract, and any future rename of that field becomes a breaking change for every subscriber.
2. **Level 2, the translation handler as an explicit boundary** — `internalBus.subscribe(domainEvent -> {...})` registers a handler whose entire job is to read fields off the rich `OrderDomainEvent` and construct a *new*, separate `OrderPlacedIntegrationEvent` containing only `orderId`, `total`, and `status` — nothing else crosses this boundary.
3. **Level 2, what actually reaches the broker** — the printed output shows only the minimal `OrderPlacedIntegrationEvent`; `internalWarehouseCode` and `triggeredByUserId`, both present on the domain event that triggered this, never appear anywhere in what gets published externally.
4. **Level 3, a substantial internal refactor** — `Order`'s `status` field changes from a plain string to a four-value `OrderStatus` enum, `internalWarehouseCode` is renamed to `warehouseRoutingKey`, and an entirely new `fulfillmentPriority` field is added — a realistic, non-trivial set of internal changes a domain model might undergo over time.
5. **Level 3, the translation handler absorbs the change** — the updated handler still reads `domainEvent.order().status() == OrderStatus.PLACED` (adapted for the new enum) and still constructs an `OrderPlacedIntegrationEvent` with exactly the same three fields, `orderId`, `total`, `status` (converted via `.name()`) — the *internal* logic changed, but the *output shape* did not.
6. **Level 3, the unchanged external consumer** — `externalEmailServiceConsumer` is written entirely against `OrderPlacedIntegrationEvent`'s fields and contains no reference to `OrderStatus`, `warehouseRoutingKey`, or `fulfillmentPriority`; it is passed the freshly published integration event and runs exactly as it did before the internal refactor, needing zero source changes.
7. **Level 3, why the output proves the point** — the published integration event line is identical in shape to Level 2's, despite a substantially different internal domain model producing it; this is the concrete, observable payoff of the domain/integration event split: internal evolution and external contract stability become two independent concerns, each changing on its own schedule.

## 7. Gotchas & takeaways

> **Gotcha:** the translation handler itself becomes a piece of code that must be kept in sync with the internal model on every refactor — skipping this discipline "just this once" because a change seems small is exactly how integration events quietly start leaking internal details again; treat the translation step as a mandatory checkpoint, not an optional nicety.

- A domain event is internal, rich, and free to change as a service's own model evolves; an integration event is a deliberately separate, stable, minimal contract published across service boundaries.
- Publishing a domain event directly onto a shared broker couples every external consumer's stability to the pace of one team's internal refactoring — a mistake that's easy to make and expensive to unwind later.
- A translation handler, listening for the domain event and constructing a separate integration event, is the deliberate boundary that keeps the two lifecycles independent.
- This split allows the internal domain model to be refactored substantially — renamed fields, richer types, new fields — without external consumers needing any changes at all, as long as the translation handler preserves the integration event's schema.
- The translation handler needs the same discipline and review attention as any other public API boundary, since it's the one place responsible for not leaking internal details outward.
