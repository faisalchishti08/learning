---
card: microservices
gi: 68
slug: database-decomposition-splitting-a-shared-schema
title: "Database decomposition / splitting a shared schema"
---

## 1. What it is

Database decomposition is the process of splitting a single shared database schema — typically inherited from a monolith — into separate schemas or databases, one per extracted microservice, so each service owns its own data exclusively. It is usually the hardest part of [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md): extracting application code behind a new service boundary is comparatively easy, but as long as two services still read and write the same underlying tables, they remain coupled at the data layer no matter how cleanly their code is separated.

## 2. Why & when

A microservice that shares its database with another service isn't really independent: any change to a shared table's schema risks breaking the other service, deployments have to be coordinated around shared migrations, and one service's data-access patterns can degrade performance for the other. This directly undermines the core promises of microservices — independent deployability and failure isolation — regardless of how clean the service boundary looks at the code level. A shared database is often the *real* boundary in a system, no matter what the deployment topology looks like.

Split the schema whenever two services that should be independently deployable still read or write the same tables. This is typically necessary work during [incremental monolith decomposition](0066-decomposing-a-monolith-incrementally.md), done gradually and carefully — a shared production database is exactly the kind of shared, stateful resource where a mistake is expensive and hard to reverse.

## 3. Core concept

Splitting happens in stages: first stop cross-service writes to tables you don't own (route through an API instead), then physically move the tables into a separate schema, then finally point the owning service directly at its own database — each stage independently verifiable.

```
Stage 0: shared schema, both services read/write directly       -- fully coupled
Stage 1: OrderService still reads Shipping tables, but only
         WRITES through ShippingService's API now               -- write coupling removed
Stage 2: Shipping tables physically moved to their own schema;
         OrderService now reads through ShippingService's API too -- fully decoupled
```

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A shared database used directly by two services evolves into two separate databases, each owned exclusively by one service, communicating only through APIs">
  <rect x="20" y="20" width="260" height="90" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">BEFORE: shared schema</text>
  <rect x="40" y="55" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="160" y="55" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="210" y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ShippingService</text>
  <text x="150" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">both read/write the SAME tables directly</text>

  <rect x="360" y="20" width="260" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AFTER: split schemas</text>
  <rect x="380" y="55" width="90" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="500" y="55" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ShippingService</text>
  <text x="490" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">own DB each; talk only via API calls</text>

  <line x1="425" y1="90" x2="425" y2="130" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="550" y1="90" x2="550" y2="130" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="385" y="130" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="425" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">orders_db</text>
  <rect x="510" y="130" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="550" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shipping_db</text>
  <line x1="470" y1="70" x2="500" y2="70" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,3"/>
  <text x="485" y="65" fill="#79c0ff" font-size="6.5" text-anchor="middle" font-family="sans-serif">API</text>
</svg>

Direct table access becomes an API call; each service ends up owning its own storage exclusively.

## 5. Runnable example

Scenario: `OrderService` and `ShippingService` sharing one in-memory table for shipment data, first with both writing to it directly (data-layer coupling), then fixed so only `ShippingService` writes while `OrderService` reads through an API method (write coupling removed), then fully split into two separate stores where `OrderService` can no longer touch shipment data at all.

### Level 1 — Basic

```java
// File: SharedTable.java -- BOTH OrderService and ShippingService write
// directly to the SAME shared in-memory table -- classic data-layer coupling.
import java.util.*;

public class SharedTable {
    static Map<String, String> shipmentStatusTable = new HashMap<>(); // the "shared schema"

    static class OrderService {
        void cancelOrder(String orderId) {
            shipmentStatusTable.put(orderId, "CANCELLED"); // writing DIRECTLY into Shipping's table
            System.out.println("[OrderService] wrote shipment status directly: " + orderId + " -> CANCELLED");
        }
    }

    static class ShippingService {
        void dispatch(String orderId) {
            shipmentStatusTable.put(orderId, "DISPATCHED");
            System.out.println("[ShippingService] wrote shipment status: " + orderId + " -> DISPATCHED");
        }
    }

    public static void main(String[] args) {
        new ShippingService().dispatch("ORD-1");
        new OrderService().cancelOrder("ORD-1"); // OrderService overwrites Shipping's own data
        System.out.println("Final status: " + shipmentStatusTable.get("ORD-1"));
    }
}
```

**How to run:** `javac SharedTable.java && java SharedTable` (JDK 17+).

Expected output:
```
[ShippingService] wrote shipment status: ORD-1 -> DISPATCHED
[OrderService] wrote shipment status directly: ORD-1 -> CANCELLED
Final status: CANCELLED
```

`OrderService` silently overwrote data `ShippingService` owns, with no validation, no event, and no way for `ShippingService` to know its own table changed underneath it — the hallmark risk of a shared schema.

### Level 2 — Intermediate

```java
// File: WriteThroughApi.java -- Stage 1: stop OrderService from writing
// directly. It must now go through ShippingService's API, which can
// validate the transition before applying it.
import java.util.*;

public class WriteThroughApi {
    static class ShippingService {
        private Map<String, String> shipmentStatusTable = new HashMap<>(); // now PRIVATE -- no direct access

        void dispatch(String orderId) {
            shipmentStatusTable.put(orderId, "DISPATCHED");
            System.out.println("[ShippingService] " + orderId + " -> DISPATCHED");
        }

        void requestCancellation(String orderId) { // the ONLY way to change shipment status now
            String current = shipmentStatusTable.get(orderId);
            if ("DISPATCHED".equals(current)) {
                System.out.println("[ShippingService] refused cancellation: " + orderId + " already dispatched");
                return;
            }
            shipmentStatusTable.put(orderId, "CANCELLED");
            System.out.println("[ShippingService] " + orderId + " -> CANCELLED");
        }
    }

    static class OrderService {
        ShippingService shipping;
        OrderService(ShippingService shipping) { this.shipping = shipping; }

        void cancelOrder(String orderId) {
            shipping.requestCancellation(orderId); // goes through the API, not a shared table
            System.out.println("[OrderService] requested cancellation for " + orderId);
        }
    }

    public static void main(String[] args) {
        ShippingService shipping = new ShippingService();
        OrderService orders = new OrderService(shipping);
        shipping.dispatch("ORD-1");
        orders.cancelOrder("ORD-1"); // now correctly refused
    }
}
```

**How to run:** `javac WriteThroughApi.java && java WriteThroughApi` (JDK 17+).

Expected output:
```
[ShippingService] ORD-1 -> DISPATCHED
[ShippingService] refused cancellation: ORD-1 already dispatched
[OrderService] requested cancellation for ORD-1
```

`shipmentStatusTable` is now `private` to `ShippingService`; `OrderService` cannot bypass it. And because `ShippingService` now sees every write request, it correctly refuses to cancel a shipment that has already dispatched — a business rule the shared-table version in Level 1 had no way to enforce.

### Level 3 — Advanced

```java
// File: FullySplitDatabases.java -- Stage 2: physically separate the
// storage too. Each service now owns its OWN store; OrderService only
// ever sees a read-only PROJECTION of shipment status, kept in sync via
// an event -- it can no longer even conceptually reach Shipping's table.
import java.util.*;

public class FullySplitDatabases {
    record ShipmentDispatched(String orderId) {}

    static class ShippingService {
        private Map<String, String> shippingDb = new HashMap<>(); // ShippingService's OWN database
        private List<ShipmentDispatched> outbox = new ArrayList<>();

        void dispatch(String orderId) {
            shippingDb.put(orderId, "DISPATCHED");
            outbox.add(new ShipmentDispatched(orderId)); // publish an event instead of a shared write
            System.out.println("[ShippingService/shipping_db] " + orderId + " -> DISPATCHED");
        }

        List<ShipmentDispatched> drainEvents() {
            List<ShipmentDispatched> events = new ArrayList<>(outbox);
            outbox.clear();
            return events;
        }
    }

    static class OrderService {
        private Map<String, String> ordersDb = new HashMap<>(); // OrderService's OWN, SEPARATE database
        private Map<String, String> shipmentStatusProjection = new HashMap<>(); // local read-only copy

        void placeOrder(String orderId) {
            ordersDb.put(orderId, "PLACED");
            System.out.println("[OrderService/orders_db] " + orderId + " -> PLACED");
        }

        void onShipmentDispatched(ShipmentDispatched event) { // reacts to Shipping's event, doesn't query its DB
            shipmentStatusProjection.put(event.orderId(), "DISPATCHED");
            System.out.println("[OrderService] projection updated from event: " + event.orderId() + " -> DISPATCHED");
        }

        void cancelOrder(String orderId) {
            if ("DISPATCHED".equals(shipmentStatusProjection.get(orderId))) {
                System.out.println("[OrderService] cannot cancel " + orderId + ": already dispatched (per local projection)");
                return;
            }
            ordersDb.put(orderId, "CANCELLED");
            System.out.println("[OrderService/orders_db] " + orderId + " -> CANCELLED");
        }
    }

    public static void main(String[] args) {
        ShippingService shipping = new ShippingService();
        OrderService orders = new OrderService();
        orders.placeOrder("ORD-1");
        shipping.dispatch("ORD-1");
        for (ShipmentDispatched event : shipping.drainEvents()) {
            orders.onShipmentDispatched(event); // event-driven sync, NO shared table anywhere
        }
        orders.cancelOrder("ORD-1");
    }
}
```

**How to run:** `javac FullySplitDatabases.java && java FullySplitDatabases` (JDK 17+).

Expected output:
```
[OrderService/orders_db] ORD-1 -> PLACED
[ShippingService/shipping_db] ORD-1 -> DISPATCHED
[OrderService] projection updated from event: ORD-1 -> DISPATCHED
[OrderService/orders_db] ORD-1 -> CANCELLED
[OrderService] cannot cancel ORD-1: already dispatched (per local projection)
```

`OrderService`'s constructor needs no argument, since it owns `ordersDb` itself — the two services only ever interact through `dispatch` producing events and `onShipmentDispatched` consuming them, never through shared storage.

## 6. Walkthrough

1. **Level 1** — a single `shipmentStatusTable` map stands in for a shared database table. `ShippingService.dispatch` writes `DISPATCHED`, then `OrderService.cancelOrder` writes `CANCELLED` directly into the *same* map — `main` prints both writes and shows the final status silently flipped to `CANCELLED`, with `ShippingService` having no say in, or even awareness of, that change. This is data-layer coupling: two services, two sets of code, but one shared mutable resource underneath.
2. **Level 2 — Stage 1, remove write coupling** — `shipmentStatusTable` becomes a private field of `ShippingService`; `OrderService` can no longer reach it directly and must call `shipping.requestCancellation(orderId)` instead. Tracing `main`: `shipping.dispatch("ORD-1")` sets status to `DISPATCHED` and prints it; `orders.cancelOrder("ORD-1")` calls `shipping.requestCancellation`, which checks the current status, sees `DISPATCHED`, and *refuses* the cancellation, printing a refusal message — a business rule Level 1's raw shared-table write could never enforce, because nothing was checking anything.
3. **Level 3 — Stage 2, remove read coupling too, via events** — each service now owns a fully separate map (`shippingDb` vs `ordersDb`), and `OrderService` keeps its own local `shipmentStatusProjection` instead of ever querying `ShippingService`'s storage. Tracing `main`: `orders.placeOrder("ORD-1")` writes only to `ordersDb` and prints. `shipping.dispatch("ORD-1")` writes to `shippingDb` *and* appends a `ShipmentDispatched` event to its outbox, printing the dispatch line. `shipping.drainEvents()` returns that event, and the loop passes it to `orders.onShipmentDispatched`, which updates `OrderService`'s own local `shipmentStatusProjection` — printing the projection-update line. Only *after* that event has been consumed does `orders.cancelOrder("ORD-1")` check `shipmentStatusProjection` (its own local copy, not a live query into Shipping's database) and correctly refuse, printing the final refusal line.
4. **What changed structurally between Level 2 and Level 3** — in Level 2, `OrderService` still made a *synchronous call* into `ShippingService` to check status — the services were separate at the storage layer but still directly, synchronously coupled at the call layer. In Level 3, `OrderService` reacts to a *published event* and keeps its own local copy of the information it needs, so it never has to call into `ShippingService` at all to answer "is this shipment dispatched?" — a fuller decoupling appropriate once both services are meant to be genuinely independently deployable.

## 7. Gotchas & takeaways

> **Gotcha:** splitting the storage (Stage 2) before removing cross-service writes (Stage 1) is backwards and far riskier — you'd be physically separating tables that code elsewhere in the system is still actively writing to across the split, guaranteeing broken writes the moment the split happens. Always remove the coupling at the code/API level first, verify it, and only then move the underlying storage.
- A shared database is a hidden coupling point that undermines independent deployability even when the application code looks cleanly separated into services.
- Split in stages: stop cross-service writes first (route through an API), verify, then physically separate the storage, then finally remove any remaining synchronous cross-service reads if full decoupling is the goal.
- Moving from synchronous "call the other service to check its state" (Level 2) to "react to its published events and keep a local read projection" (Level 3) is a common final step toward true independence — see [domain events](0054-domain-events.md).
- This is usually the hardest and riskiest step of [incremental monolith decomposition](0066-decomposing-a-monolith-incrementally.md) — treat schema changes to shared production tables with the same caution as any other hard-to-reverse, shared-state change.
- Related: an [anti-corruption layer](0067-anti-corruption-layer-between-monolith-and-new-service.md) is often layered on top of this same seam to translate legacy data shapes while the schema split is happening.
