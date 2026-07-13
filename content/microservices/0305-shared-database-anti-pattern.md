---
card: microservices
gi: 305
slug: shared-database-anti-pattern
title: "Shared database anti-pattern"
---

## 1. What it is

The shared database anti-pattern is the direct opposite of [database per service](0304-database-per-service-pattern.md): multiple services connecting to and directly reading/writing the same physical database and tables. It is called an anti-pattern rather than just an alternative design because it undermines the core promises of a microservices architecture while offering, at first glance, an appealing shortcut — one database is simpler to set up, and joining across "services'" data is trivial when it's all just one schema.

## 2. Why & when

The appeal is real and worth naming honestly: a shared database avoids the need for [API composition](0312-api-composition-pattern.md), event-driven synchronization, or accepting eventual consistency — a single SQL query can join across what would otherwise be several services' worth of data instantly and consistently. This is exactly why teams under time pressure often reach for it, especially early in a migration from a monolith, where the data already lives in one shared schema and splitting it out feels like unnecessary extra work.

The cost, though, compounds over time in ways that erode the actual benefits of having "microservices" at all: any service can be broken by another service's schema migration, since there's no enforced boundary; independent deployability disappears because a schema change now potentially requires coordinating every service touching the affected tables; and independent scaling is compromised because all services compete for the same database's connections, locks, and I/O capacity. Teams often adopt this anti-pattern as a deliberate, temporary bridge during a monolith-to-microservices migration (the "strangler fig" approach touches this) — that can be a reasonable transitional state, but it should be explicitly tracked as technical debt with a plan to split the data, not treated as the end state.

## 3. Core concept

The anti-pattern is structural: multiple independently-deployed services each hold a direct connection/repository pointed at the same schema, with no service-owned boundary between them.

```java
// ANTI-PATTERN: both services connect DIRECTLY to the same schema and
// even the same tables, with no owning service and no API boundary.
@Repository
interface OrderJpaRepository extends JpaRepository<OrderEntity, Long> {}   // in the ORDER service
@Repository
interface OrderJpaRepositoryFromShipping extends JpaRepository<OrderEntity, Long> {} // in the SHIPPING service, SAME table

// Both services can independently read AND WRITE 'orders' -- neither
// "owns" it, so neither can safely change its schema alone.
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three separately deployed services all connect directly to the same shared database and the same tables, with no service owning any boundary, so a schema change made for one service's benefit can silently break the others, and none of them can be deployed, scaled, or evolved independently">
  <rect x="30" y="20" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Order Service</text>

  <rect x="260" y="20" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Shipping Service</text>

  <rect x="490" y="20" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Billing Service</text>

  <line x1="90" y1="60" x2="320" y2="110" stroke="#8b949e" marker-end="url(#arr305)"/>
  <line x1="320" y1="60" x2="320" y2="110" stroke="#8b949e" marker-end="url(#arr305)"/>
  <line x1="550" y1="60" x2="320" y2="110" stroke="#8b949e" marker-end="url(#arr305)"/>

  <rect x="230" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ONE shared schema, no owner</text>

  <defs><marker id="arr305" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every service reads and writes the same tables directly; none of them can safely change the schema alone.

## 5. Runnable example

Scenario: two services sharing one `orders` table where a schema change made for one service's needs silently breaks the other, extended to show the same scenario with a proper API boundary (database-per-service) where the identical schema change is fully isolated, and finally a realistic incident timeline showing exactly how a shared-database change ships successfully in one service's tests but breaks a completely different, seemingly unrelated service in production.

### Level 1 — Basic

```java
// File: SharedTableBreaksSilently.java -- OrderService renames a column
// (a normal, "internal" refactor from its own point of view), and
// ShippingService -- which ALSO reads the same table directly -- breaks
// immediately, with no warning at compile time.
import java.util.*;

public class SharedTableBreaksSilently {
    // The SHARED table, represented as rows of column-name -> value.
    static List<Map<String, Object>> ordersTable = new ArrayList<>(List.of(
            new HashMap<>(Map.of("id", 1, "status", "PLACED")) // OrderService's original column name
    ));

    static class OrderService {
        // OrderService decides to rename 'status' to 'order_status' -- seems like
        // a purely internal, harmless refactor from ITS perspective.
        void renameStatusColumn() {
            for (Map<String, Object> row : ordersTable) {
                row.put("order_status", row.remove("status"));
            }
            System.out.println("OrderService: renamed 'status' -> 'order_status' (looks like a safe internal change)");
        }
    }

    static class ShippingService {
        // ShippingService reads the SAME table directly, using the OLD column name.
        String checkOrderStatus(int orderId) {
            for (Map<String, Object> row : ordersTable) {
                if ((int) row.get("id") == orderId) {
                    return (String) row.get("status"); // still expects the OLD name
                }
            }
            return "NOT FOUND";
        }
    }

    public static void main(String[] args) {
        ShippingService shippingService = new ShippingService();
        System.out.println("Before OrderService's change: " + shippingService.checkOrderStatus(1));

        new OrderService().renameStatusColumn();

        System.out.println("After OrderService's change: " + shippingService.checkOrderStatus(1)
                + " -- ShippingService is now BROKEN, with no compile-time or deploy-time warning.");
    }
}
```

How to run: `java SharedTableBreaksSilently.java`

Before the change, `ShippingService.checkOrderStatus` correctly returns `"PLACED"`. After `OrderService` renames the `status` column — a change its own team reasonably considered internal and low-risk — `ShippingService`'s identical code now returns `null` (the `"status"` key no longer exists in the row), silently breaking a completely different team's service with no compiler error, no failed test in `OrderService`'s own test suite, and no deployment-time signal that anything is wrong.

### Level 2 — Intermediate

```java
// File: DatabasePerServiceIsolatesTheChange.java -- the SAME rename,
// but now OrderService owns its data exclusively and ShippingService
// only calls its API; the internal rename is fully absorbed and
// invisible to ShippingService.
import java.util.*;

public class DatabasePerServiceIsolatesTheChange {
    static class OrderService {
        // PRIVATE storage -- OrderService alone decides its column names.
        private final Map<Integer, Map<String, Object>> ordersDb = new HashMap<>();
        { ordersDb.put(1, new HashMap<>(Map.of("id", 1, "status", "PLACED"))); }

        void renameStatusColumn() {
            for (Map<String, Object> row : ordersDb.values()) row.put("order_status", row.remove("status"));
            System.out.println("OrderService: renamed internal column 'status' -> 'order_status' (private change)");
        }

        // PUBLIC API contract -- stable, regardless of the internal column name.
        public String getOrderStatus(int orderId) {
            Map<String, Object> row = ordersDb.get(orderId);
            if (row == null) return "NOT FOUND";
            // OrderService adapts INTERNALLY so the public contract never changes.
            return row.containsKey("order_status") ? (String) row.get("order_status") : (String) row.get("status");
        }
    }

    static class ShippingService {
        private final OrderService orderServiceApi;
        ShippingService(OrderService orderServiceApi) { this.orderServiceApi = orderServiceApi; }
        String checkOrderStatus(int orderId) { return orderServiceApi.getOrderStatus(orderId); } // via API, not direct storage
    }

    public static void main(String[] args) {
        OrderService orderService = new OrderService();
        ShippingService shippingService = new ShippingService(orderService);

        System.out.println("Before OrderService's change: " + shippingService.checkOrderStatus(1));
        orderService.renameStatusColumn();
        System.out.println("After OrderService's change: " + shippingService.checkOrderStatus(1)
                + " -- ShippingService is UNAFFECTED, because it never depended on the internal column name.");
    }
}
```

How to run: `java DatabasePerServiceIsolatesTheChange.java`

The identical internal rename happens, but this time `ShippingService` only ever calls `orderServiceApi.getOrderStatus(orderId)` — a stable public contract `OrderService` maintains regardless of its internal storage. `OrderService`'s `getOrderStatus` method adapts to read from whichever internal key currently holds the data, so the exact same rename that broke `ShippingService` in Level 1 is now completely invisible to it — `checkOrderStatus` returns `"PLACED"` both before and after.

### Level 3 — Advanced

```java
// File: RealisticIncidentTimeline.java -- simulates a realistic
// shared-database incident: OrderService's team makes a schema change,
// runs and passes THEIR OWN full test suite (which only tests
// OrderService's own code paths), deploys successfully, and only THEN
// does an unrelated, seemingly unconnected BillingService start failing
// in production -- because it too was silently reading the shared table.
import java.util.*;

public class RealisticIncidentTimeline {
    static List<Map<String, Object>> ordersTable = new ArrayList<>(List.of(
            new HashMap<>(Map.of("id", 1, "total_cents", 4999))
    ));

    static class OrderService {
        boolean runOwnTestSuite() {
            // OrderService's tests only exercise ITS OWN read/write paths --
            // they have no way to know BillingService also reads this table.
            renameTotalColumn();
            boolean pass = ordersTable.get(0).containsKey("amount_cents");
            System.out.println("OrderService test suite: " + (pass ? "PASSED" : "FAILED") + " (only checks OrderService's own expectations)");
            return pass;
        }
        void renameTotalColumn() {
            ordersTable.get(0).put("amount_cents", ordersTable.get(0).remove("total_cents"));
        }
    }

    static class BillingService {
        // BillingService ALSO reads 'orders' directly -- OrderService's team
        // has no visibility into this dependency AT ALL.
        int getOrderTotalCents(int orderId) {
            for (Map<String, Object> row : ordersTable) {
                if ((int) row.get("id") == orderId) return (int) row.get("total_cents"); // OLD column name
            }
            throw new NoSuchElementException("order not found");
        }
    }

    public static void main(String[] args) {
        System.out.println("Day 1: OrderService team plans a column rename for their own internal clarity.");
        System.out.println("Day 2: OrderService's CI pipeline runs...");
        boolean ciPassed = new OrderService().runOwnTestSuite();
        System.out.println("Day 2: OrderService deploys to production. CI was green: " + ciPassed);

        System.out.println("Day 2, 15 minutes later: BillingService starts throwing errors in production...");
        try {
            int total = new BillingService().getOrderTotalCents(1);
            System.out.println("BillingService: order total = " + total);
        } catch (Exception e) {
            System.out.println("BillingService: PRODUCTION INCIDENT -- " + e.getClass().getSimpleName()
                    + ": " + e.getMessage() + " (a service NOBODY on the OrderService team knew existed just broke)");
        }
    }
}
```

How to run: `java RealisticIncidentTimeline.java`

`OrderService`'s own CI pipeline passes cleanly — its tests only check what `OrderService` itself expects after the rename, and correctly report success. The deployment goes out. Fifteen simulated minutes later, `BillingService`, a service that was never mentioned in `OrderService`'s change review, its tests, or its deployment checklist, starts throwing a `NoSuchElementException`-style failure in production, because it was independently reading the exact same shared table using the old column name. This is the realistic shape a shared-database incident takes: the team that caused the break has no signal anything is wrong, and the team whose service actually broke often has no idea why, since nothing in their own codebase changed.

## 6. Walkthrough

Trace `RealisticIncidentTimeline.main` in order. **First**, `ordersTable` is initialized with one row containing `"total_cents": 4999`.

**`new OrderService().runOwnTestSuite()` is called.** Inside, it calls `renameTotalColumn()`, which mutates the shared `ordersTable`: it removes the `"total_cents"` key and re-inserts the same value under `"amount_cents"`. The test then checks `ordersTable.get(0).containsKey("amount_cents")`, which is now `true`, so `pass` is `true` and the method prints "PASSED." From `OrderService`'s isolated point of view, this is a fully successful, verified change.

**The "deploy" is simulated** by simply printing a success message — in a real system, this represents `OrderService`'s CI/CD pipeline shipping the schema migration and the new code to production, having seen nothing but green checks along the way.

**Fifteen simulated minutes later**, `new BillingService().getOrderTotalCents(1)` is called — representing a completely independent code path in a completely different service, deployed separately, that has been running unmodified this whole time. Inside, it iterates `ordersTable`, finds the row with `id == 1`, and executes `(int) row.get("total_cents")`. But `"total_cents"` no longer exists in that row — it was removed by `OrderService`'s rename a moment earlier, in the *same shared table* — so `row.get("total_cents")` returns `null`, and the subsequent unboxing cast `(int) null` throws a `NullPointerException` (represented here via the illustrative catch block showing a `NoSuchElementException`-style production incident).

**Back in `main`**, this exception is caught and printed as a "PRODUCTION INCIDENT" — precisely the moment an on-call engineer for `BillingService` would be paged, with no context connecting the failure to `OrderService`'s earlier, successfully-tested, successfully-deployed change, since the two services share no code, no repository, and no deployment pipeline — only, invisibly, the same database table.

```
Day 1-2: OrderService plans + tests + deploys a column rename
              |
              v  (OrderService's OWN tests: 100% green, no visibility into BillingService)
         DEPLOYED successfully
              |
              v  (shared table now has NO 'total_cents' column)
    BillingService (unrelated, unmodified, deployed separately) reads the SAME table
              |
              v
    PRODUCTION INCIDENT -- with no obvious link back to the actual root cause
```

## 7. Gotchas & takeaways

> A shared database's blast radius is invisible by construction: there is no dependency graph, no compiler, and often no monitoring that connects "OrderService changed a column" to "BillingService broke" — the two facts only ever get connected by a human during incident investigation, after the fact.

- The shared database anti-pattern trades away independent deployability, independent scaling, and safe schema evolution for the short-term convenience of trivial cross-service joins.
- It is sometimes a reasonable *temporary* bridge during a monolith-to-microservices migration, but should be tracked explicitly as debt with a concrete plan to split the data — not left as a permanent architecture.
- The actual danger is not the sharing itself but its invisibility: a proper API boundary (database-per-service) makes the *contract* between services explicit and testable, while a shared table makes the coupling implicit and discoverable only by reading every consumer's source code — or, in practice, by a production incident.
- If a shared database is truly unavoidable in the short term, at minimum enforce read-only access for all but the owning service and treat any write from a non-owning service as an emergency-level violation to be removed as soon as possible.
