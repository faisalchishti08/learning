---
card: microservices
gi: 16
slug: loose-coupling-high-cohesion
title: Loose coupling & high cohesion
---

## 1. What it is

**Coupling** measures how much one service's code depends on another's internal details — its data structures, its private logic — rather than just its public contract. **Cohesion** measures how strongly the responsibilities inside a single service belong together — whether everything in it exists to serve one clear purpose, or whether it's a grab-bag of unrelated concerns. The goal in a well-designed microservices system is **loose coupling** (services barely need to know anything about each other's internals) combined with **high cohesion** (everything inside one service genuinely belongs together).

These two properties reinforce each other: a service with low cohesion — handling orders, sending emails, and generating reports all at once — tends to force other services into tight coupling with it, because callers end up depending on several unrelated pieces of its behavior rather than one clean concern.

## 2. Why & when

Tight coupling defeats independent deployability before it even gets a chance: if `OrderService` reaches directly into `InventoryService`'s internal data structure, then any change to that structure — even one that doesn't affect `InventoryService`'s public behavior at all — can break `OrderService`. Low cohesion compounds the problem: a service doing five unrelated things has five unrelated reasons to change, and each change risks breaking whichever of those five things some other service happens to depend on.

Actively design for both properties from the start of splitting a system into services — they don't happen by accident. Loose coupling means depending only on a stable, minimal public contract. High cohesion means drawing a service's boundary around one genuine responsibility, resisting the temptation to fold in "just one more small thing" that doesn't actually belong.

## 3. Core concept

Two axes, evaluated independently:

- **Coupling (between services):** low = depends only on a public contract; high = reaches into internal fields, shared mutable state, or private implementation details.
- **Cohesion (within a service):** high = every piece of functionality serves one clear responsibility; low = unrelated responsibilities bundled together because it was convenient, not because they belong together.

The ideal combination is **loose coupling, high cohesion**: services that barely need each other's internals, and each one focused tightly on a single, coherent purpose.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tight coupling reaches into another service's internal fields; loose coupling depends only on a public interface. Low cohesion bundles unrelated responsibilities; high cohesion keeps one clear purpose">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Tight coupling</text>
  <rect x="30" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="85" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="180" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="235" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory</text>
  <text x="235" y="68" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.stock (PRIVATE field, reached into)</text>
  <line x1="140" y1="57" x2="180" y2="57" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a16)"/>

  <text x="480" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Loose coupling</text>
  <rect x="380" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="435" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="530" y="35" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory</text>
  <text x="575" y="68" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">reserve()</text>
  <line x1="490" y1="57" x2="530" y2="57" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a16b)"/>
  <defs>
    <marker id="a16" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="a16b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Tight coupling reaches into another service's internals; loose coupling depends only on a stable public method.

## 5. Runnable example

Scenario: `OrderService` depending on `InventoryService`, first tightly coupled to its internal data and bundled with unrelated low-cohesion responsibilities, then refactored to loose coupling and high cohesion.

### Level 1 — Basic

```java
// File: TightCouplingLowCohesion.java -- reaches into internals, bundles unrelated concerns
import java.util.*;

public class TightCouplingLowCohesion {
    static class InventoryService {
        Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5)); // PUBLIC field -- an internal detail exposed
    }

    // LOW COHESION: order placement, email formatting, and report generation, all bundled together
    static class OrderAndEverythingElseService {
        InventoryService inventory;
        OrderAndEverythingElseService(InventoryService inventory) { this.inventory = inventory; }

        void placeOrder(String item) {
            // TIGHT COUPLING: reaches straight into inventory's internal map, not through any method
            Integer count = inventory.stock.get(item);
            if (count != null && count > 0) inventory.stock.put(item, count - 1);
        }

        String formatConfirmationEmail(String item) { return "Subject: Your order for " + item; } // unrelated concern #1
        String generateMonthlyReport() { return "Report: N/A"; } // unrelated concern #2
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        OrderAndEverythingElseService svc = new OrderAndEverythingElseService(inventory);
        svc.placeOrder("widget");
        System.out.println("stock after order: " + inventory.stock.get("widget"));
        System.out.println(svc.formatConfirmationEmail("widget"));
    }
}
```

**How to run:** `javac TightCouplingLowCohesion.java && java TightCouplingLowCohesion` (JDK 17+).

Expected output:
```
stock after order: 4
Subject: Your order for widget
```

`placeOrder` reaches directly into `inventory.stock`, a public `Map` — any future change to how `InventoryService` stores its data breaks this code. And `OrderAndEverythingElseService` bundles ordering, email formatting, and reporting — three unrelated responsibilities with three unrelated reasons to change.

### Level 2 — Intermediate

```java
// File: LooseCouplingHighCohesion.java -- InventoryService exposes only a
// method; OrderService does ONLY ordering, nothing else.
import java.util.*;

public class LooseCouplingHighCohesion {
    static class InventoryService {
        private final Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5)); // PRIVATE now

        boolean reserve(String item) { // the ONLY way in -- a stable public contract
            Integer count = stock.get(item);
            if (count != null && count > 0) { stock.put(item, count - 1); return true; }
            return false;
        }
        int stockLevel(String item) { return stock.getOrDefault(item, 0); }
    }

    // HIGH COHESION: this class does exactly one thing -- placing orders
    static class OrderService {
        InventoryService inventory;
        OrderService(InventoryService inventory) { this.inventory = inventory; }

        void placeOrder(String item) {
            if (inventory.reserve(item)) System.out.println("Order placed for " + item); // LOOSE COUPLING: only calls a method
            else System.out.println("Out of stock: " + item);
        }
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        OrderService orders = new OrderService(inventory);
        orders.placeOrder("widget");
        System.out.println("stock after order: " + inventory.stockLevel("widget"));
    }
}
```

**How to run:** `javac LooseCouplingHighCohesion.java && java LooseCouplingHighCohesion` (JDK 17+).

Expected output:
```
Order placed for widget
stock after order: 4
```

`OrderService` never touches `InventoryService`'s internal map — it calls `reserve(...)`, a stable public method. `OrderService` also does exactly one thing: place orders. Email formatting and reporting have been removed entirely (they'd belong in their own, separately cohesive services).

### Level 3 — Advanced

```java
// File: SwapInventoryImplementation.java -- prove loose coupling by swapping
// InventoryService's ENTIRE internal storage; OrderService needs ZERO changes.
import java.util.*;

public class SwapInventoryImplementation {
    interface Inventory { // the stable contract OrderService depends on
        boolean reserve(String item);
        int stockLevel(String item);
    }

    // v1: simple HashMap-backed implementation
    static class HashMapInventory implements Inventory {
        private final Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5));
        public boolean reserve(String item) {
            Integer count = stock.get(item);
            if (count != null && count > 0) { stock.put(item, count - 1); return true; }
            return false;
        }
        public int stockLevel(String item) { return stock.getOrDefault(item, 0); }
    }

    // v2: a COMPLETELY different implementation -- thread-safe, tracks reservation history too
    static class ConcurrentInventoryWithHistory implements Inventory {
        private final Map<String, Integer> stock = new java.util.concurrent.ConcurrentHashMap<>(Map.of("widget", 5));
        private final List<String> reservationHistory = new ArrayList<>();
        public boolean reserve(String item) {
            Integer count = stock.get(item);
            if (count != null && count > 0) { stock.put(item, count - 1); reservationHistory.add(item); return true; }
            return false;
        }
        public int stockLevel(String item) { return stock.getOrDefault(item, 0); }
    }

    // OrderService, UNCHANGED, depends ONLY on the Inventory interface -- never a concrete class
    static class OrderService {
        Inventory inventory;
        OrderService(Inventory inventory) { this.inventory = inventory; }
        void placeOrder(String item) {
            if (inventory.reserve(item)) System.out.println("Order placed for " + item);
            else System.out.println("Out of stock: " + item);
        }
    }

    public static void main(String[] args) {
        OrderService ordersV1 = new OrderService(new HashMapInventory());
        ordersV1.placeOrder("widget");

        OrderService ordersV2 = new OrderService(new ConcurrentInventoryWithHistory()); // ENTIRELY different internals
        ordersV2.placeOrder("widget"); // OrderService's code did NOT change at all
    }
}
```

**How to run:** `javac SwapInventoryImplementation.java && java SwapInventoryImplementation` (JDK 17+).

Expected output:
```
Order placed for widget
Order placed for widget
```

The production-flavored proof: `OrderService`'s source is identical whether it's wired to `HashMapInventory` or `ConcurrentInventoryWithHistory` — a genuinely different implementation, with a different backing map type and an entirely new capability (reservation history) `HashMapInventory` never had. Loose coupling means `OrderService` never needed to know or care about that difference.

## 6. Walkthrough

1. `new OrderService(new HashMapInventory())` constructs `OrderService` with the simpler v1 implementation, referenced only through the `Inventory` interface type.
2. `ordersV1.placeOrder("widget")` calls `inventory.reserve("widget")` — resolved at run time to `HashMapInventory.reserve`, which decrements a plain `HashMap` entry and returns `true`.
3. `new OrderService(new ConcurrentInventoryWithHistory())` constructs a second `OrderService`, wired to a completely different implementation — a `ConcurrentHashMap` internally, plus an entirely new `reservationHistory` list `HashMapInventory` never had.
4. `ordersV2.placeOrder("widget")` runs the exact same `OrderService.placeOrder` method body as step 2 — the same compiled bytecode — but this time `inventory.reserve(...)` resolves to `ConcurrentInventoryWithHistory.reserve`, which also decrements stock, but additionally appends to `reservationHistory`.
5. Both calls print the same success message, and neither required `OrderService`'s source code to be aware of which concrete implementation it was talking to — proof that coupling exists only between `OrderService` and the `Inventory` *interface*, never between `OrderService` and either concrete class's internals.

```
OrderService.placeOrder(item)
        |
   inventory.reserve(item)   <- interface call, resolved at RUN TIME
        |
   +---------------------+---------------------------------+
   HashMapInventory        ConcurrentInventoryWithHistory
   (v1: simple map)        (v2: concurrent map + history)
```

## 7. Gotchas & takeaways

> **Gotcha:** cohesion problems often creep in gradually, not all at once — a service that starts perfectly focused can accumulate "just one small unrelated thing" repeatedly over time (a notification helper here, a reporting endpoint there) until it's quietly become a low-cohesion grab-bag. Periodically ask, of every method in a service, "does this genuinely belong to the one responsibility this service owns?"

- Loose coupling means depending only on another service's stable public contract, never its internal data or implementation details.
- High cohesion means every responsibility inside a service genuinely belongs to one coherent purpose — not several unrelated concerns bundled together for convenience.
- The proof of loose coupling: can a service's entire internal implementation be swapped for something completely different, with zero changes required to any caller's code?
- Low cohesion in one service tends to force tight coupling onto its callers, since they end up depending on several unrelated pieces of its behavior rather than one clean concern — the two properties are linked, not independent.
