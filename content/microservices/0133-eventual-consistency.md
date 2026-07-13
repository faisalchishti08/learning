---
card: microservices
gi: 133
slug: eventual-consistency
title: "Eventual consistency"
---

## 1. What it is

Eventual consistency is the guarantee that, given no new updates, all parts of a distributed system will *eventually* converge on the same state — but at any given moment in between, different services or replicas may be observing different, temporarily-inconsistent views of that state. It is the consistency model that [asynchronous messaging](0111-asynchronous-messaging-model.md) and [event-carried state transfer](0129-event-carried-state-transfer.md) naturally produce, since a consumer's local copy is only ever as fresh as the last event it has processed.

## 2. Why & when

Strong consistency — every reader seeing the same, immediately up-to-date value everywhere, always — requires synchronous coordination between every party involved, which is exactly the kind of tight coupling and availability chaining that asynchronous, event-driven microservices are designed to avoid. Eventual consistency is the trade-off accepted in exchange: services stay independently deployable, available, and decoupled, at the cost of a real, sometimes user-visible window where different parts of the system briefly disagree.

Eventual consistency is the default and expected model for data that crosses service boundaries via events — an inventory count updated by an order in `order-service` will not be instantly visible in `catalog-service`'s copy, and that gap is a design decision, not a bug. Strong consistency remains appropriate *within* a single service's own transactional boundary (a single database transaction should still be atomic and immediately consistent) — the trade-off specifically concerns state that has to cross an asynchronous boundary between independently deployed services.

## 3. Core concept

A write to the owning service is immediately consistent there; other services holding a copy of that data only become consistent with it after they receive and apply the corresponding event, meaning there is a real, measurable time window during which querying two different services about the "same" fact can yield two different answers.

```java
// order-service, the source of truth: immediately consistent with itself
inventoryService.reserveStock(orderId, sku, quantity); // committed NOW, in order-service's own transaction

// catalog-service, holding a COPY: only becomes consistent once it processes the resulting event
// -- there is a real window where catalog-service still shows the OLD stock count
channel.publish("stock-reserved", new StockReservedEvent(sku, quantity)); // catalog-service hasn't seen this yet
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline: order-service's stock count updates immediately at t=0; catalog-service's copy remains stale until it processes the corresponding event at t=200ms, after which both views agree" >
  <line x1="40" y1="90" x2="600" y2="90" stroke="#8b949e"/>
  <circle cx="100" cy="90" r="4" fill="#6db33f"/>
  <text x="100" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">t=0: order-service updates</text>
  <text x="100" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">stock=8 (immediately consistent)</text>

  <rect x="130" y="130" width="300" height="24" rx="3" fill="#79c0ff" opacity="0.35"/>
  <text x="280" y="147" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inconsistency window -- catalog-service still shows stock=10</text>

  <circle cx="430" cy="90" r="4" fill="#6db33f"/>
  <text x="430" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">t=200ms: catalog-service</text>
  <text x="430" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">processes event, stock=8 (converged)</text>
</svg>

Between the two marked points, order-service and catalog-service genuinely disagree; after the event is processed, they converge.

## 5. Runnable example

Scenario: a stock count kept in two places, `order-service` (source of truth) and `catalog-service` (a replicated copy), that starts with a strongly-consistent shared variable (the alternative being contrasted), moves to two genuinely separate stores connected by an asynchronous event with a visible lag, and finally adds a "read your own writes" pattern so a specific, common inconsistency case is handled deliberately rather than surprising users.

### Level 1 — Basic

```java
// File: StronglyConsistentBaseline.java -- one shared variable: always instantly consistent, for comparison.
public class StronglyConsistentBaseline {
    static int stock = 10;

    public static void main(String[] args) {
        System.out.println("Before: stock = " + stock);
        stock -= 2; // one single write, one single read location -- inherently consistent
        System.out.println("After: stock = " + stock + " (both 'order-service' and 'catalog-service' are really just this one variable)");
    }
}
```

**How to run:** `javac StronglyConsistentBaseline.java && java StronglyConsistentBaseline` (JDK 17+).

With a single shared piece of state, there is no possibility of disagreement — but this only works because there is no real service boundary here at all.

### Level 2 — Intermediate

```java
// File: EventuallyConsistentServices.java -- TWO separate stores, connected by an
// asynchronous event; a real, measurable window exists where they disagree.
import java.util.concurrent.*;

public class EventuallyConsistentServices {
    static class OrderService {
        int stock = 10; // ITS OWN store, the source of truth
        BlockingQueue<Integer> events = new LinkedBlockingQueue<>();

        void reserveStock(int quantity) {
            stock -= quantity; // immediately consistent WITHIN order-service
            events.offer(quantity); // published asynchronously -- catalog-service hasn't seen it yet
            System.out.println("[order-service] stock now " + stock + " (immediately, locally consistent)");
        }
    }

    static class CatalogService {
        volatile int stockCopy = 10; // ITS OWN, SEPARATE copy
        void consumeEventsFrom(OrderService orderService) {
            new Thread(() -> {
                try {
                    Integer quantity = orderService.events.take();
                    Thread.sleep(200); // simulated network + processing lag -- the REAL inconsistency window
                    stockCopy -= quantity;
                    System.out.println("[catalog-service] processed event, stockCopy now " + stockCopy + " (converged, 200ms later)");
                } catch (InterruptedException ignored) { }
            }).start();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        OrderService orderService = new OrderService();
        CatalogService catalogService = new CatalogService();
        catalogService.consumeEventsFrom(orderService);

        orderService.reserveStock(2);
        System.out.println("[catalog-service] queried IMMEDIATELY after: stockCopy = " + catalogService.stockCopy + " (STALE -- still 10, not yet 8)");

        Thread.sleep(300); // wait past the processing lag
        System.out.println("[catalog-service] queried after waiting: stockCopy = " + catalogService.stockCopy + " (now converged)");
    }
}
```

**How to run:** `javac EventuallyConsistentServices.java && java EventuallyConsistentServices` (JDK 17+).

Expected output (timing approximate):
```
[order-service] stock now 8 (immediately, locally consistent)
[catalog-service] queried IMMEDIATELY after: stockCopy = 10 (STALE -- still 10, not yet 8)
[catalog-service] processed event, stockCopy now 8 (converged, 200ms later)
[catalog-service] queried after waiting: stockCopy = 8 (now converged)
```

The two services genuinely disagree about the stock count for roughly 200ms, a real and measurable inconsistency window, before converging.

### Level 3 — Advanced

```java
// File: ReadYourOwnWrites.java -- a common, deliberate mitigation: the SERVICE that
// just wrote can always answer immediately-consistent queries about ITS OWN write,
// even while other services are still catching up.
import java.util.concurrent.*;

public class ReadYourOwnWrites {
    static class OrderService {
        int stock = 10;
        BlockingQueue<Integer> events = new LinkedBlockingQueue<>();

        int reserveStockAndReturnNewCount(int quantity) {
            stock -= quantity;
            events.offer(quantity);
            return stock; // the CALLER gets the immediately-consistent result directly from the source of truth
        }
    }

    static class CatalogService {
        volatile int stockCopy = 10;
        void consumeEventsFrom(OrderService orderService) {
            new Thread(() -> {
                try {
                    Integer quantity = orderService.events.take();
                    Thread.sleep(200);
                    stockCopy -= quantity;
                    System.out.println("[catalog-service] eventually converged: stockCopy = " + stockCopy);
                } catch (InterruptedException ignored) { }
            }).start();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        OrderService orderService = new OrderService();
        CatalogService catalogService = new CatalogService();
        catalogService.consumeEventsFrom(orderService);

        // the CHECKOUT FLOW needs an immediately-correct number for the confirmation page --
        // it reads directly from order-service (read-your-own-writes), NOT from catalog-service's lagging copy
        int authoritativeStockAfterReservation = orderService.reserveStockAndReturnNewCount(2);
        System.out.println("[checkout confirmation page] shows authoritative stock = " + authoritativeStockAfterReservation + " (correct immediately, read from the source of truth)");

        // meanwhile, the PRODUCT LISTING PAGE reads from catalog-service, which is fine being eventually consistent
        System.out.println("[product listing page] shows catalog-service's stock = " + catalogService.stockCopy + " (briefly stale, acceptable for this use case)");

        Thread.sleep(300);
        System.out.println("[product listing page, later] shows catalog-service's stock = " + catalogService.stockCopy + " (now converged too)");
    }
}
```

**How to run:** `javac ReadYourOwnWrites.java && java ReadYourOwnWrites` (JDK 17+).

Expected output (timing approximate):
```
[checkout confirmation page] shows authoritative stock = 8 (correct immediately, read from the source of truth)
[product listing page] shows catalog-service's stock = 10 (briefly stale, acceptable for this use case)
[catalog-service] eventually converged: stockCopy = 8
[product listing page, later] shows catalog-service's stock = 8 (now converged too)
```

## 6. Walkthrough

1. **Level 1** — `stock` is a single variable read and written from one place; there is only ever one value to observe, so "consistency" isn't even a meaningful question here — this is the baseline strong-consistency case eventual consistency is contrasted against.
2. **Level 2, two genuinely separate stores** — `OrderService.stock` and `CatalogService.stockCopy` are two distinct fields on two distinct objects; `reserveStock` updates only the first, immediately, and separately calls `events.offer(quantity)` to notify the second, asynchronously.
3. **Level 2, the lag made concrete** — `CatalogService.consumeEventsFrom` spins up a background thread that calls `Thread.sleep(200)` after receiving the event but before applying it, deliberately modeling the real network and processing delay that exists in any actual asynchronous system.
4. **Level 2, catching the inconsistency in the act** — `main` queries `catalogService.stockCopy` *immediately* after calling `orderService.reserveStock(2)`, before the 200ms delay has elapsed, and genuinely observes the stale value `10` — this isn't a hypothetical risk, it's directly demonstrated by running the program.
5. **Level 2, convergence** — after `Thread.sleep(300)` (deliberately longer than the simulated 200ms lag), querying `catalogService.stockCopy` again shows `8`, matching `order-service`'s value — the "eventual" part of eventual consistency has now occurred.
6. **Level 3, the read-your-own-writes pattern** — `reserveStockAndReturnNewCount` returns the *new* stock value directly to its caller, from the source of truth itself, rather than requiring the caller to separately query `catalog-service` and potentially observe a stale value for a write it just made.
7. **Level 3, matching each read to its consistency need** — the checkout confirmation page's requirement (show the customer an immediately-correct number for the reservation they *just* made) is served by reading directly from `order-service`, while the product listing page's requirement (show a generally-accurate stock count to browsing customers) is served perfectly well by `catalog-service`'s eventually-consistent copy — this is the practical resolution to eventual consistency: matching each specific read to the consistency guarantee it actually needs, rather than treating every read the same way.

## 7. Gotchas & takeaways

> **Gotcha:** eventual consistency has no built-in bound on *how long* "eventual" takes — a healthy system converges in milliseconds, but a backed-up consumer, a broker outage, or a downstream failure can stretch that window to minutes or hours with nothing in the basic guarantee preventing it; systems with real requirements around staleness need an explicit, monitored freshness target, not just faith that "eventual" will be fast enough in practice.

- Eventual consistency guarantees convergence given no further updates, but allows a real, observable window during which different services disagree about the same underlying fact.
- It is the natural consequence of asynchronous, event-driven communication between independently deployed services, and the trade-off accepted for their decoupling and availability.
- Consistency remains strong and immediate *within* a single service's own transactional boundary — the trade-off specifically applies to state that crosses an asynchronous service boundary.
- The read-your-own-writes pattern — routing a caller back to the source of truth for data it just wrote — resolves the most common, most user-visible instance of this problem without giving up eventual consistency elsewhere.
- Different reads have different consistency needs; matching each read to the guarantee it actually requires (source of truth vs. an eventually-consistent local copy) is the practical way to live with this trade-off rather than fight it everywhere uniformly.
