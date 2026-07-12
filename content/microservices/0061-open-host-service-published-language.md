---
card: microservices
gi: 61
slug: open-host-service-published-language
title: "Open host service & published language"
---

## 1. What it is

An **Open Host Service** is a relationship pattern for an upstream context serving *many* independent downstream consumers: instead of negotiating a custom integration with each one individually, the upstream exposes one well-designed, general-purpose protocol — its **Published Language** — documented and stable, intended for any consumer to integrate against. A public REST API with an OpenAPI specification, or a well-documented event schema published for any interested service to subscribe to, are both concrete examples: one interface, designed deliberately for broad reuse, rather than a bespoke integration per consumer.

## 2. Why & when

When an upstream context has one or two consumers, a bespoke integration per consumer (potentially even a [Customer-Supplier](0059-customersupplier-relationship.md) relationship with each) is manageable. Once an upstream context needs to serve many independent consumers — a dozen different services, possibly across different teams or even different organizations — negotiating and maintaining a separate bespoke contract with each one becomes an unsustainable coordination burden for the upstream team. An Open Host Service solves this by designing one general-purpose interface well, once, and publishing it as the single contract every consumer integrates against.

Adopt this pattern once a context has enough independent consumers that bespoke, per-consumer contracts would genuinely become a coordination bottleneck — a single, well-documented, versioned public interface, with a formal, published language describing its request/response shapes, replaces what would otherwise be many separate, individually-negotiated relationships.

## 3. Core concept

The key discipline: the published language must be genuinely general-purpose, not shaped around any one specific consumer's needs — designing it well enough that it serves many different, unrelated consumers without needing per-consumer customization is what makes the pattern actually work.

```
InventoryService (Open Host Service)
        |
   Published Language: GET /inventory/{sku} -> { sku, quantityAvailable, lastUpdated }
        |
   +----------+----------+----------+
   OrderService  RecommendationService  AnalyticsService   <- ALL consumers use the SAME published contract
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InventoryService publishes one general-purpose language that many independent consumer services all integrate against, rather than negotiating a bespoke contract with each">
  <rect x="230" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">InventoryService</text>
  <text x="320" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Open Host Service</text>

  <rect x="30" y="120" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="255" y="120" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">RecommendationService</text>
  <rect x="480" y="120" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AnalyticsService</text>

  <line x1="95" y1="120" x2="280" y2="80" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="120" x2="320" y2="80" stroke="#8b949e" stroke-width="1"/>
  <line x1="545" y1="120" x2="360" y2="80" stroke="#8b949e" stroke-width="1"/>
</svg>

One published, general-purpose language; many independent consumers integrate against the same stable contract.

## 5. Runnable example

Scenario: `InventoryService` serving multiple consumers, first with bespoke per-consumer contracts (an unsustainable pattern), then unified into one published language, then extended to show a new consumer integrating with zero negotiation needed.

### Level 1 — Basic

```java
// File: BespokePerConsumer.java -- a DIFFERENT contract negotiated for
// EACH consumer -- unsustainable as consumers grow.
public class BespokePerConsumer {
    static class InventoryService {
        // a DIFFERENT method, a DIFFERENT shape, for EACH consumer -- negotiated bespoke, one at a time
        int getStockForOrderService(String sku) { return 5; }
        String getStockLevelForRecommendationService(String sku) { return "5 units"; } // different RETURN TYPE entirely
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        System.out.println("OrderService sees: " + inventory.getStockForOrderService("widget"));
        System.out.println("RecommendationService sees: " + inventory.getStockLevelForRecommendationService("widget"));
    }
}
```

**How to run:** `javac BespokePerConsumer.java && java BespokePerConsumer` (JDK 17+).

Expected output:
```
OrderService sees: 5
RecommendationService sees: 5 units
```

Two consumers, two entirely separate methods with different shapes — `InventoryTeam` has to design, document, and maintain a distinct bespoke contract for each one. A third consumer would mean a third bespoke method, and so on, each one its own negotiation and maintenance burden.

### Level 2 — Intermediate

```java
// File: OpenHostService.java -- ONE published, general-purpose contract
// ALL consumers use identically.
import java.util.*;

public class OpenHostService {
    // the PUBLISHED LANGUAGE -- one general-purpose response shape, designed for BROAD reuse
    record InventoryStatus(String sku, int quantityAvailable, String lastUpdated) { }

    static class InventoryService { // the OPEN HOST SERVICE
        InventoryStatus getInventoryStatus(String sku) { // ONE method, serving ANY consumer
            return new InventoryStatus(sku, 5, "2026-07-12");
        }
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();

        InventoryStatus forOrders = inventory.getInventoryStatus("widget");
        InventoryStatus forRecommendations = inventory.getInventoryStatus("widget");

        System.out.println("OrderService sees: " + forOrders.quantityAvailable() + " units");
        System.out.println("RecommendationService sees: " + forRecommendations.quantityAvailable() + " units");
        System.out.println("SAME published contract, SAME method, used by BOTH consumers");
    }
}
```

**How to run:** `javac OpenHostService.java && java OpenHostService` (JDK 17+).

Expected output:
```
OrderService sees: 5 units
RecommendationService sees: 5 units
SAME published contract, SAME method, used by BOTH consumers
```

Both consumers now call the exact same `getInventoryStatus` method, receiving the exact same `InventoryStatus` shape — one well-designed, general-purpose contract instead of two bespoke ones.

### Level 3 — Advanced

```java
// File: NewConsumerZeroNegotiation.java -- a BRAND-NEW THIRD consumer
// integrates with ZERO negotiation, using the ALREADY-PUBLISHED contract.
import java.util.*;

public class NewConsumerZeroNegotiation {
    record InventoryStatus(String sku, int quantityAvailable, String lastUpdated) { } // UNCHANGED published language

    static class InventoryService { // UNCHANGED Open Host Service
        InventoryStatus getInventoryStatus(String sku) { return new InventoryStatus(sku, 5, "2026-07-12"); }
    }

    // a BRAND-NEW consumer, AnalyticsService -- never mentioned to InventoryTeam beforehand
    static class AnalyticsService {
        InventoryService inventory;
        AnalyticsService(InventoryService inventory) { this.inventory = inventory; }

        void recordInventorySnapshot(String sku) {
            InventoryStatus status = inventory.getInventoryStatus(sku); // uses the ALREADY-PUBLISHED contract directly
            System.out.println("[Analytics] recorded snapshot: " + status.sku() + " = " + status.quantityAvailable() + " units at " + status.lastUpdated());
        }
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();

        // the ORIGINAL two consumers, UNCHANGED
        System.out.println("OrderService sees: " + inventory.getInventoryStatus("widget").quantityAvailable() + " units");
        System.out.println("RecommendationService sees: " + inventory.getInventoryStatus("widget").quantityAvailable() + " units");

        // the NEW third consumer, integrated with ZERO changes to InventoryService or negotiation with InventoryTeam
        new AnalyticsService(inventory).recordInventorySnapshot("widget");
    }
}
```

**How to run:** `javac NewConsumerZeroNegotiation.java && java NewConsumerZeroNegotiation` (JDK 17+).

Expected output:
```
OrderService sees: 5 units
RecommendationService sees: 5 units
[Analytics] recorded snapshot: widget = 5 units at 2026-07-12
```

The production-flavored payoff: `AnalyticsService`, a brand-new consumer, integrates directly against `InventoryService.getInventoryStatus` — the same published contract `OrderService` and `RecommendationService` already use — with zero changes to `InventoryService` itself and zero bespoke negotiation with `InventoryTeam`. This is exactly the scalability an Open Host Service is designed to provide: adding the Nth consumer costs the same (near-zero, on the upstream side) as adding the second.

## 6. Walkthrough

1. `inventory.getInventoryStatus("widget")` is called first for `OrderService`'s benefit, returning `InventoryStatus("widget", 5, "2026-07-12")` — exactly the same method that will be reused below.
2. The identical call is made again for `RecommendationService` — same method, same published contract, same result.
3. `new AnalyticsService(inventory)` constructs the new consumer, wiring it to the *same* `InventoryService` instance the other two consumers already use.
4. `recordInventorySnapshot("widget")` calls `inventory.getInventoryStatus(sku)` — the exact same method signature `OrderService` and `RecommendationService` already call — and receives the exact same `InventoryStatus` shape, with no special-casing or new method needed on `InventoryService`'s side.
5. `AnalyticsService` then formats and prints its own snapshot using the data from the published contract — proof that a genuinely new, previously-unknown consumer could integrate successfully using only the already-published, general-purpose language, without `InventoryService`'s code changing at all to accommodate it.

```
InventoryService.getInventoryStatus(sku)   <- ONE published method, UNCHANGED throughout
        |
   +--------------+--------------------+------------------------+
   OrderService     RecommendationService     AnalyticsService (NEW, zero negotiation needed)
```

## 7. Gotchas & takeaways

> **Gotcha:** designing a genuinely general-purpose published language is harder than it looks — a naive attempt often ends up shaped subtly around whichever consumer happened to be built first, making it awkward for later, differently-shaped consumers. Invest real design effort in making the published language's shape reflect the upstream's own domain concepts cleanly, rather than any one consumer's specific preferences, so it genuinely serves many different, unanticipated future consumers well.

- An Open Host Service publishes one well-designed, general-purpose contract for an upstream context to serve many independent consumers, replacing what would otherwise be a bespoke, individually-negotiated integration per consumer.
- The published language must be genuinely general-purpose — designed around the upstream's own domain concepts, not shaped around any one specific consumer's preferences — for the pattern to actually scale to many different consumers well.
- The concrete payoff: a brand-new consumer can integrate against an already-published contract with zero changes to the upstream service and zero bespoke negotiation, unlike a bespoke-per-consumer approach where every new consumer adds real coordination cost.
- Adopt this pattern once an upstream context has, or expects to have, enough independent consumers that maintaining separate bespoke contracts would become an unsustainable coordination burden for the upstream team.
