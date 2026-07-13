---
card: microservices
gi: 308
slug: data-duplication-denormalization-across-services
title: "Data duplication & denormalization across services"
---

## 1. What it is

Data duplication across services means the same piece of information — a product's name and price, a customer's shipping address — is deliberately stored in more than one service's private database, rather than living in exactly one place and being fetched on demand. Denormalization is the closely related technique of storing derived or redundant data (a pre-computed total, a copy of a related record's fields) to avoid expensive lookups or joins at read time. In a microservices architecture with [database per service](0304-database-per-service-pattern.md), some amount of both is not just acceptable but often necessary, since cross-service joins aren't possible.

## 2. Why & when

Without duplication, every time `OrderService` needs to display a product's name alongside an order line item, it would need a synchronous API call to `ProductCatalogService` — for every single order line, on every single read. This couples `OrderService`'s availability and latency to `ProductCatalogService`'s availability and latency, for data (a product name) that changes far less often than orders are read. Duplicating a *local, read-only copy* of just the fields actually needed (product name, not the full catalog record) into `OrderService`'s own database, kept in sync via [events](0315-keeping-read-models-in-sync-via-events.md), lets `OrderService` serve reads entirely from its own data, independent of `ProductCatalogService`'s availability, at the cost of that copy being slightly stale between sync events.

Use deliberate, scoped duplication when a service frequently needs a small, relatively stable subset of another service's data for its own reads, and synchronous coupling for every read is unacceptable for latency or availability reasons. Duplicate only the specific fields actually needed, not entire records, and always let exactly one service remain the [system of record](0311-data-ownership-system-of-record.md) — the duplicated copy is a read-optimized cache of that source of truth, never a second place where the data can be independently written.

## 3. Core concept

A service holds its own local, denormalized copy of just the fields it needs from another service's data, refreshed via an event whenever the source changes — reads never leave the service's own boundary.

```java
// OrderService's OWN local copy -- only the fields IT needs, kept in sync
// via events from ProductCatalogService, never fetched synchronously per read.
@Entity
class OrderLineItem {
    @Id Long id;
    String productSku;
    String productNameSnapshot; // DUPLICATED from ProductCatalogService, may be slightly stale
    BigDecimal priceSnapshot;   // DENORMALIZED: the price AT ORDER TIME, deliberately never updated later
    int quantity;
}

// Kept fresh (for NEW orders, not existing ones -- see below) via an event listener:
@EventListener
void onProductRenamed(ProductRenamedEvent event) {
    // Only affects a LOCAL cache used for lookups when CREATING new orders,
    // never retroactively rewrites priceSnapshot/productNameSnapshot on past orders.
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ProductCatalogService is the single system of record for product data; OrderService holds a locally duplicated, denormalized copy of just the fields it needs, kept approximately in sync via events, so OrderService's reads never require a synchronous call back to ProductCatalogService">
  <rect x="30" y="30" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ProductCatalogService</text>
  <text x="130" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">system of record</text>

  <line x1="230" y1="55" x2="380" y2="55" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr308)"/>
  <text x="305" y="45" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">event: ProductRenamed</text>

  <rect x="390" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="500" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">local denormalized copy (product name only)</text>

  <text x="320" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderService reads its OWN copy -- never a synchronous call for every read</text>
</svg>

The catalog service owns the truth; the order service keeps a small, event-synced local copy for fast, independent reads.

## 5. Runnable example

Scenario: a synchronous per-read dependency where every order display requires a live call to the product catalog, extended to a locally duplicated snapshot that removes that dependency for reads, and finally showing the deliberate, correct behavior of a price snapshot that must NOT update when the source product's price later changes, since an order should reflect the price at the time it was placed.

### Level 1 — Basic

```java
// File: SynchronousCoupledReads.java -- every order display requires a
// LIVE call to ProductCatalogService, coupling OrderService's read
// availability and latency to a completely different service.
import java.util.*;

public class SynchronousCoupledReads {
    static class ProductCatalogService {
        Map<String, String> productNames = new HashMap<>(Map.of("sku-1", "Wireless Mouse"));
        boolean isDown = false;
        String getProductName(String sku) {
            if (isDown) throw new RuntimeException("ProductCatalogService UNAVAILABLE");
            return productNames.get(sku);
        }
    }

    record OrderLine(String sku, int quantity) {}

    static class OrderService {
        ProductCatalogService catalogService;
        OrderService(ProductCatalogService catalogService) { this.catalogService = catalogService; }
        String displayOrderLine(OrderLine line) {
            String name = catalogService.getProductName(line.sku()); // SYNCHRONOUS call, EVERY read
            return line.quantity() + "x " + name;
        }
    }

    public static void main(String[] args) {
        ProductCatalogService catalog = new ProductCatalogService();
        OrderService orderService = new OrderService(catalog);
        System.out.println(orderService.displayOrderLine(new OrderLine("sku-1", 2)));

        catalog.isDown = true; // catalog service has an outage
        try {
            orderService.displayOrderLine(new OrderLine("sku-1", 2));
        } catch (Exception e) {
            System.out.println("Order display FAILED because of an UNRELATED service's outage: " + e.getMessage());
        }
    }
}
```

How to run: `java SynchronousCoupledReads.java`

The first order line displays correctly. Once `ProductCatalogService` is simulated as down, `OrderService` cannot even display an *existing* order's line item — a read of `OrderService`'s own data (the order itself) is blocked entirely by an outage in a completely different service, purely because the product name was never stored locally.

### Level 2 — Intermediate

```java
// File: LocalDenormalizedSnapshot.java -- OrderService stores its OWN
// local copy of the product name at order-creation time; displaying an
// existing order NEVER requires calling ProductCatalogService again.
import java.util.*;

public class LocalDenormalizedSnapshot {
    static class ProductCatalogService {
        Map<String, String> productNames = new HashMap<>(Map.of("sku-1", "Wireless Mouse"));
        boolean isDown = false;
        String getProductName(String sku) {
            if (isDown) throw new RuntimeException("ProductCatalogService UNAVAILABLE");
            return productNames.get(sku);
        }
    }

    // OrderService's OWN table -- productNameSnapshot is DUPLICATED data,
    // captured once, at order creation time.
    record OrderLine(String sku, int quantity, String productNameSnapshot) {}

    static class OrderService {
        ProductCatalogService catalogService;
        List<OrderLine> savedOrderLines = new ArrayList<>();
        OrderService(ProductCatalogService catalogService) { this.catalogService = catalogService; }

        void createOrderLine(String sku, int quantity) {
            String name = catalogService.getProductName(sku); // called ONCE, at CREATION time only
            savedOrderLines.add(new OrderLine(sku, quantity, name));
        }
        String displayOrderLine(OrderLine line) {
            return line.quantity() + "x " + line.productNameSnapshot(); // reads OrderService's OWN data, NO external call
        }
    }

    public static void main(String[] args) {
        ProductCatalogService catalog = new ProductCatalogService();
        OrderService orderService = new OrderService(catalog);
        orderService.createOrderLine("sku-1", 2); // catalog IS up at creation time

        catalog.isDown = true; // catalog service has an outage LATER
        System.out.println(orderService.displayOrderLine(orderService.savedOrderLines.get(0))
                + " -- displayed successfully DESPITE ProductCatalogService being down, because this read never touches it.");
    }
}
```

How to run: `java LocalDenormalizedSnapshot.java`

`createOrderLine` calls the catalog exactly once, at creation time, and stores the result locally as `productNameSnapshot`. Later, even with `ProductCatalogService` simulated as fully down, `displayOrderLine` succeeds — it reads only `OrderService`'s own locally duplicated data, with zero dependency on the catalog service's availability for this read.

### Level 3 — Advanced

```java
// File: PriceSnapshotMustNotUpdate.java -- demonstrates the CORRECT,
// deliberate behavior for denormalized data that represents a POINT IN
// TIME fact: an order's price snapshot must stay FROZEN at order-creation
// time even after the product's CURRENT price later changes, because an
// order legitimately reflects "the price when this order was placed," not
// "the product's current price."
import java.util.*;
import java.math.BigDecimal;

public class PriceSnapshotMustNotUpdate {
    static class ProductCatalogService {
        Map<String, BigDecimal> currentPrices = new HashMap<>(Map.of("sku-1", new BigDecimal("29.99")));
        BigDecimal getCurrentPrice(String sku) { return currentPrices.get(sku); }
        void changePrice(String sku, BigDecimal newPrice) {
            System.out.println("  ProductCatalogService: price for " + sku + " changed to $" + newPrice);
            currentPrices.put(sku, newPrice);
        }
    }

    // priceSnapshot is DENORMALIZED and DELIBERATELY IMMUTABLE once set --
    // this is NOT staleness to be "fixed" by re-syncing; it is correct,
    // permanent historical data.
    record Order(String id, String sku, BigDecimal priceSnapshot) {}

    static class OrderService {
        ProductCatalogService catalogService;
        List<Order> orders = new ArrayList<>();
        OrderService(ProductCatalogService catalogService) { this.catalogService = catalogService; }

        Order placeOrder(String orderId, String sku) {
            BigDecimal priceAtOrderTime = catalogService.getCurrentPrice(sku); // captured ONCE
            Order order = new Order(orderId, sku, priceAtOrderTime);
            orders.add(order);
            return order;
        }
    }

    public static void main(String[] args) {
        ProductCatalogService catalog = new ProductCatalogService();
        OrderService orderService = new OrderService(catalog);

        Order order1 = orderService.placeOrder("order-1", "sku-1");
        System.out.println("order-1 placed at price snapshot: $" + order1.priceSnapshot());

        catalog.changePrice("sku-1", new BigDecimal("34.99")); // price goes UP later

        Order order2 = orderService.placeOrder("order-2", "sku-1"); // a NEW order, AFTER the price change
        System.out.println("order-2 placed at price snapshot: $" + order2.priceSnapshot());

        System.out.println("order-1's snapshot is STILL: $" + order1.priceSnapshot()
                + " (correctly UNCHANGED -- this order was placed before the price increase, and must reflect THAT price forever)");
    }
}
```

How to run: `java PriceSnapshotMustNotUpdate.java`

`order1` captures `priceSnapshot=$29.99` at creation. The catalog's price is then changed to `$34.99`. `order2`, created *after* the change, correctly captures the new price, `$34.99`. Crucially, `order1.priceSnapshot()` remains `$29.99` — it was never re-read or re-synced from the catalog, because it represents a historical fact ("what this customer agreed to pay"), not a live mirror of the product's current price. This is the essential distinction between denormalized data that should be kept approximately fresh via events (like a display name, where staleness for a few seconds is a minor UX issue) and denormalized data that is fundamentally a point-in-time snapshot that must never be overwritten (like a price at time of purchase, where "updating" it would actually be a correctness bug).

## 6. Walkthrough

Trace `PriceSnapshotMustNotUpdate.main` in order. **First**, `catalog.currentPrices` starts with `"sku-1" -> $29.99`.

**`orderService.placeOrder("order-1", "sku-1")` is called.** Inside, `catalogService.getCurrentPrice("sku-1")` reads the catalog's *current* price at this exact moment, `$29.99`, and this value is captured into a new immutable `Order` record's `priceSnapshot` field. The order is appended to `orders` and returned as `order1`. From this point forward, `order1.priceSnapshot()` is a fixed value baked into that specific `Order` object — there is no code path in this program that ever mutates it.

**`catalog.changePrice("sku-1", $34.99)` is called**, mutating `catalog.currentPrices` — the *catalog's* view of the current price changes. Critically, this method has no awareness of, and no reference to, any previously placed orders; it only updates the catalog's own internal state.

**`orderService.placeOrder("order-2", "sku-1")` is called next.** This independently calls `catalogService.getCurrentPrice("sku-1")` again — but now, since `catalog.currentPrices` was just mutated, this read returns `$34.99`. A *new* `Order` record is created with `priceSnapshot=$34.99` and stored as `order2`.

**Finally**, `order1.priceSnapshot()` is read one more time and printed. Since `order1` is an immutable record created before the price change, and nothing in this program's execution path ever touches `order1` again after its creation, its `priceSnapshot` field still holds exactly `$29.99` — the value captured at the moment it was created, entirely unaffected by the later catalog change.

**The essential data-flow distinction**: `order1` and `order2` each independently captured a *copy* of the catalog's price at their own respective creation times — they are two separate snapshots of a value that changed in between, and both are simultaneously "correct" for what they represent (the price at the time each order was placed), even though they now permanently disagree with each other and with the catalog's current price.

```
t1: catalog price = $29.99 -> order1.priceSnapshot = $29.99 (frozen forever)
t2: catalog.changePrice($34.99)  -- catalog's CURRENT price changes, order1 is UNTOUCHED
t3: catalog price = $34.99 -> order2.priceSnapshot = $34.99 (frozen forever, different value)
t4: order1.priceSnapshot still reads $29.99 -- correct, NOT a sync bug
```

## 7. Gotchas & takeaways

> Not all duplicated data should be kept "in sync" — some denormalized fields are deliberately point-in-time snapshots (a price at purchase, an address at shipment) that must remain frozen even as the source data changes later, while others (a display name, a category label) genuinely should be refreshed via events to avoid becoming stale. Conflating these two cases — either freezing data that should update, or updating data that should stay frozen — is a common and consequential mistake.

- Duplicate only the specific fields a consuming service actually needs, not entire records, to keep the sync surface area and staleness window as small as possible.
- Explicitly decide, per duplicated field, whether it should be refreshed via events over time (a display-only convenience copy) or frozen permanently at creation time (a historical fact) — this decision should be deliberate and documented, not accidental.
- Duplication trades read-time independence and lower latency for the acceptance of some staleness window for the fields that *are* meant to refresh — this tradeoff should be made consciously per use case, weighing how sensitive that specific read is to staleness.
- Exactly one service remains the [system of record](0311-data-ownership-system-of-record.md) for any given fact; duplicated copies elsewhere are always derived, read-optimized views of that source of truth, never independently authoritative or independently writable.
