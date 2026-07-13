---
card: microservices
gi: 304
slug: database-per-service-pattern
title: "Database per service pattern"
---

## 1. What it is

Database-per-service is the foundational data-management pattern for microservices: each service owns its own private database, which no other service is permitted to access directly — every interaction with that data goes exclusively through the owning service's API. This is what actually makes services independently deployable and independently scalable at the data layer, not just at the code layer.

## 2. Why & when

Microservices are meant to be developed, deployed, and scaled independently, but that independence breaks down immediately if two services share a database: a schema migration in one service's tables can silently break another service that queries them directly, one service's heavy query load can degrade another's performance by consuming the same database's shared resources, and there is no way to deploy one service without coordinating with every other service that touches its tables. Database-per-service eliminates this coupling at its root: since no other service can see inside a service's database, that service's team can change its schema, switch database technology, or scale its data tier entirely independently.

Use database-per-service as the default for any new microservices architecture — it is the pattern virtually every other topic in this Distributed Data Management section exists to work around the consequences of (no cross-service joins, eventual consistency, the need for composition and events instead of shared queries). It is a deliberate tradeoff: strong data isolation and independence, paid for with the loss of easy cross-service queries and immediate consistency, which the rest of this section addresses.

## 3. Core concept

Each service's data access layer is private; cross-service data needs are satisfied only through that service's public API, never through a direct database connection to another service's schema.

```java
// InventoryService owns its OWN database exclusively.
@Service
class InventoryService {
    private final InventoryRepository inventoryRepository; // talks ONLY to inventory_db
    InventoryService(InventoryRepository inventoryRepository) { this.inventoryRepository = inventoryRepository; }

    public StockLevel getStock(String sku) { return inventoryRepository.findBySku(sku); }
}

// OrderService needs stock info but must NOT connect to inventory_db directly --
// it goes through InventoryService's PUBLIC API instead.
@Service
class OrderService {
    private final InventoryClient inventoryClient; // HTTP/gRPC client, NOT a direct DB connection
    OrderService(InventoryClient inventoryClient) { this.inventoryClient = inventoryClient; }

    public boolean canFulfill(String sku, int quantity) {
        return inventoryClient.getStock(sku).quantity() >= quantity; // API call, not a JOIN
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each service exclusively owns its own private database; no service ever connects directly to another service's database, and any cross-service data need is satisfied only by calling the owning service's public API">
  <rect x="30" y="30" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <rect x="30" y="90" width="150" height="35" rx="5" fill="none" stroke="#6db33f" stroke-dasharray="3,3"/>
  <text x="105" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">order_db (private)</text>
  <line x1="105" y1="70" x2="105" y2="90" stroke="#6db33f"/>

  <rect x="460" y="30" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory Service</text>
  <rect x="460" y="90" width="150" height="35" rx="5" fill="none" stroke="#6db33f" stroke-dasharray="3,3"/>
  <text x="535" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory_db (private)</text>
  <line x1="535" y1="70" x2="535" y2="90" stroke="#6db33f"/>

  <line x1="180" y1="50" x2="460" y2="50" stroke="#8b949e" marker-end="url(#arr304)"/>
  <text x="320" y="40" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ALLOWED: API call</text>

  <line x1="180" y1="107" x2="460" y2="107" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="320" y="145" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">FORBIDDEN: direct database access across services</text>

  <defs><marker id="arr304" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Cross-service data access is only ever an API call; direct cross-database access is structurally forbidden.

## 5. Runnable example

Scenario: two services sharing one database and silently coupling through it, extended to give each its own private data store, forcing a proper API boundary between them, and finally showing how this isolation lets one service change its internal schema completely without breaking the other, the concrete payoff of the pattern.

### Level 1 — Basic

```java
// File: SharedDatabaseCoupling.java -- OrderService reaches directly
// into a table conceptually "owned" by InventoryService, coupling the
// two together through shared storage rather than an API.
import java.util.*;

public class SharedDatabaseCoupling {
    // ONE shared "database" -- both services read/write it directly.
    static Map<String, Integer> sharedInventoryTable = new HashMap<>(Map.of("sku-1", 10, "sku-2", 0));

    static class InventoryService {
        int getStock(String sku) { return sharedInventoryTable.getOrDefault(sku, 0); }
    }
    static class OrderService {
        // Reaches DIRECTLY into inventory's table -- no API boundary at all.
        boolean canFulfill(String sku, int quantity) {
            return sharedInventoryTable.getOrDefault(sku, 0) >= quantity;
        }
    }

    public static void main(String[] args) {
        OrderService orderService = new OrderService();
        System.out.println("Can fulfill 5 of sku-1? " + orderService.canFulfill("sku-1", 5));
        System.out.println("OrderService reached DIRECTLY into inventory's storage -- "
                + "if InventoryService renames this table or changes its structure, OrderService breaks with NO warning.");
    }
}
```

How to run: `java SharedDatabaseCoupling.java`

`OrderService.canFulfill` reads `sharedInventoryTable` directly, the same structure `InventoryService` uses internally. This works today, but it means `InventoryService`'s team cannot change how stock is stored — split it into multiple tables, rename a field, switch database technology — without also, silently, potentially breaking `OrderService`, which has no formal contract with `InventoryService` at all; it simply assumes the shared structure's shape.

### Level 2 — Intermediate

```java
// File: DatabasePerServiceWithApi.java -- InventoryService now owns its
// data EXCLUSIVELY; OrderService can only reach it through a defined
// API method, never through direct storage access.
import java.util.*;

public class DatabasePerServiceWithApi {
    static class InventoryService {
        // PRIVATE to this service -- nothing outside this class touches it directly.
        private final Map<String, Integer> inventoryDb = new HashMap<>(Map.of("sku-1", 10, "sku-2", 0));

        // The ONLY way anything outside this class can learn about stock.
        public int getStock(String sku) { return inventoryDb.getOrDefault(sku, 0); }
    }

    static class OrderService {
        private final InventoryService inventoryServiceApi; // stands in for an HTTP/gRPC client
        OrderService(InventoryService inventoryServiceApi) { this.inventoryServiceApi = inventoryServiceApi; }

        boolean canFulfill(String sku, int quantity) {
            return inventoryServiceApi.getStock(sku) >= quantity; // goes through the API, NOT direct storage
        }
    }

    public static void main(String[] args) {
        InventoryService inventoryService = new InventoryService();
        OrderService orderService = new OrderService(inventoryService);
        System.out.println("Can fulfill 5 of sku-1? " + orderService.canFulfill("sku-1", 5));
        System.out.println("OrderService has NO knowledge of inventoryDb's internal structure -- "
                + "it only knows the public getStock(sku) contract.");
    }
}
```

How to run: `java DatabasePerServiceWithApi.java`

`InventoryService.inventoryDb` is now `private`, and the only way `OrderService` can learn about stock is through the public `getStock` method — a real API boundary. `OrderService` has no idea whether stock is stored in a `HashMap`, a relational table, or something else entirely; it only depends on the stable contract `getStock(sku) -> int`.

### Level 3 — Advanced

```java
// File: SchemaChangeIsolation.java -- demonstrates the CONCRETE payoff:
// InventoryService completely REWRITES its internal storage (splitting a
// single quantity into reserved + available stock, a common real-world
// schema evolution) WITHOUT requiring any change to OrderService at all,
// because OrderService only ever depended on the public API contract.
import java.util.*;

public class SchemaChangeIsolation {
    record StockRecord(int reserved, int available) {}

    static class InventoryServiceV2 {
        // COMPLETELY DIFFERENT internal structure from the V1 example --
        // this is now split into reserved/available, a realistic schema evolution.
        private final Map<String, StockRecord> inventoryDb = new HashMap<>(Map.of(
                "sku-1", new StockRecord(2, 8),   // 2 reserved, 8 available (total was 10)
                "sku-2", new StockRecord(0, 0)
        ));

        // The PUBLIC API CONTRACT stays the same shape as before --
        // getStock(sku) -> int -- even though the internal storage changed completely.
        public int getStock(String sku) {
            StockRecord record = inventoryDb.getOrDefault(sku, new StockRecord(0, 0));
            return record.available(); // internal detail: only AVAILABLE (not reserved) counts as fulfillable
        }
    }

    // UNCHANGED from the previous version -- OrderService's code is
    // IDENTICAL, because it never depended on inventory's internal schema.
    static class OrderService {
        private final InventoryServiceV2 inventoryServiceApi;
        OrderService(InventoryServiceV2 inventoryServiceApi) { this.inventoryServiceApi = inventoryServiceApi; }
        boolean canFulfill(String sku, int quantity) { return inventoryServiceApi.getStock(sku) >= quantity; }
    }

    public static void main(String[] args) {
        InventoryServiceV2 inventoryService = new InventoryServiceV2();
        OrderService orderService = new OrderService(inventoryService);

        System.out.println("InventoryService's internal schema was COMPLETELY rewritten (single quantity -> reserved+available).");
        System.out.println("OrderService's code did not change AT ALL. Can fulfill 8 of sku-1? " + orderService.canFulfill("sku-1", 8));
        System.out.println("Can fulfill 9 of sku-1 (would need to dip into reserved stock)? " + orderService.canFulfill("sku-1", 9));
    }
}
```

How to run: `java SchemaChangeIsolation.java`

`InventoryServiceV2` completely restructures its internal storage — splitting a single `quantity` field into `reserved` and `available` — a realistic, non-trivial schema change a real inventory system might make to support order reservations. `OrderService`'s code is copied verbatim from Level 2, entirely unchanged, and still works correctly, because it only ever called `getStock(sku)` and never depended on how that number was computed or stored internally. This is the concrete, demonstrable payoff of database-per-service: a service's internal schema can evolve freely as long as its public API contract stays stable, without requiring coordinated changes across every consumer.

## 6. Walkthrough

Trace `SchemaChangeIsolation.main` in order. **First**, `InventoryServiceV2` is constructed, initializing its private `inventoryDb` with `"sku-1"` mapped to `StockRecord(reserved=2, available=8)` — internal detail entirely invisible outside this class.

**`orderService.canFulfill("sku-1", 8)` is called.** Inside, this delegates to `inventoryServiceApi.getStock("sku-1")`. Inside `getStock`, `inventoryDb.getOrDefault("sku-1", ...)` retrieves the `StockRecord(2, 8)`, and the method returns `record.available()`, which is `8` — the internal `reserved` field is deliberately not exposed or considered part of "fulfillable" stock; that business rule lives entirely inside `InventoryServiceV2`.

**Back in `canFulfill`**, the returned `8` is compared against the requested `quantity` of `8`: `8 >= 8` is `true`, so the method returns `true` — this order can be fulfilled.

**`orderService.canFulfill("sku-1", 9)` is called next.** The same path executes: `getStock` again returns `8` (the `available` figure, unaffected by the different quantity being asked about). Back in `canFulfill`, `8 >= 9` is `false`, so the method returns `false` — this order, which would require dipping into the 2 reserved units, cannot be fulfilled through this API's contract.

**The key structural point**: at no point does `OrderService`'s code, or this trace of its execution, ever need to know that `reserved` and `available` exist as separate concepts inside `InventoryServiceV2` — from `OrderService`'s perspective, it called a method named `getStock` and got back a number, exactly as it did against the completely different, single-field storage in the Level 2 version. The schema change happened entirely within the boundary of `InventoryServiceV2`, with zero required changes on the consuming side.

```
OrderService.canFulfill(sku, qty)
        |
        v
inventoryServiceApi.getStock(sku)   <- the ONLY point of contact, a stable PUBLIC contract
        |
        v
[private inventoryDb: whatever internal shape InventoryService currently uses]
        |
        v
returns an int -- OrderService never sees or depends on the internal shape
```

## 7. Gotchas & takeaways

> Database-per-service is a discipline, not an automatic property of running services in separate processes — if two services' database connection strings both point at the same physical database instance and schema, nothing technically prevents a shortcut direct query, and that shortcut silently reintroduces the exact coupling this pattern exists to eliminate. Enforce the boundary through actual access controls (separate database credentials per service, network-level isolation) wherever possible, not just convention.

- Database-per-service is the foundational pattern that makes independent service deployability real at the data layer, not just the code layer.
- It trades away easy cross-service queries (joins, ad hoc reporting across tables) for genuine team and deployment independence — the rest of this Distributed Data Management section covers the patterns (composition, events, CQRS) that compensate for this tradeoff.
- A service's public API is the *only* stable contract other services should depend on; internal schema is free to evolve as long as that contract holds, exactly as demonstrated in Level 3.
- Enforce the boundary technically where possible (separate database instances or at minimum separate credentials/schemas with restricted grants), since a "logical" boundary that's only a team convention is easy to accidentally violate under time pressure.
