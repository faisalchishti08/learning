---
card: microservices
gi: 520
slug: shared-database
title: "Shared database"
---

## 1. What it is

**Shared database** is the anti-pattern where two or more independently deployed services read from and write to the same database (or the same tables within it) directly, instead of each service owning its own data exclusively and exposing it to others only through an API. It's one of the most common causes of a [distributed monolith](0519-distributed-monolith.md): the services *look* separate on an architecture diagram, but any schema change to a shared table can silently break every service that touches it, and no service can evolve its data model independently.

## 2. Why & when

You avoid a shared database because it recreates the exact coupling microservices are meant to remove, just one layer lower than the service boundary:

- **A shared table is an undocumented, implicit contract.** An API has a explicit, versionable shape; a raw table has whatever columns happen to exist right now, and any service reading it directly is coupled to that exact shape, with no way to signal "this is changing" before it breaks.
- **It eliminates independent deployability at the data layer.** Even if two services have separate codebases, separate pipelines, and separate release schedules, if they share a table, a migration in one is a breaking change risk for the other — deploying becomes a coordination exercise between teams again.
- **It blurs ownership and responsibility.** When multiple services write to the same table, it becomes unclear which service is actually authoritative for that data's correctness — two services can write conflicting updates with neither one "wrong" by its own logic, because neither was ever designed as the sole owner.
- **The common causes are usually pragmatic shortcuts** — reusing an existing table feels faster than building a new service and API around it, or a reporting/analytics need seems to justify a service reading another's tables directly "just for queries." Both erode the boundary the same way, regardless of the good intention behind them.

## 3. Core concept

Think of two departments in a company sharing one physical filing cabinet with no assigned drawers — Sales and Finance both file documents into it freely. It works until Sales reorganizes their folders (a schema change) without telling Finance, and Finance's clerk can no longer find what they need, or worse, misfiles something into what used to be Sales' folder. Giving each department its own cabinet, and requiring the other department to *request* documents through a front desk (an API) rather than opening the cabinet themselves, means either department can reorganize their own filing system freely — the front desk's request format is the only thing that has to stay stable.

Concretely:

1. **Each service should have exactly one team, and exactly one service, that owns a given piece of data** — meaning it's the only one with direct read/write access to the underlying storage for that data.
2. **Other services that need that data ask for it through the owning service's API**, not by querying the storage directly — the API is the stable, versioned, explicit contract; the schema underneath it is a private implementation detail the owner is free to change.
3. **This holds even for read-only access** — a service reading another's table directly for a report is still coupled to that table's exact shape, and will break the same way a writer would when the schema changes, even though it never writes anything.
4. **The fix is not always "give every service its own physical database"** — sometimes shared infrastructure (one database server) is fine, as long as each service has its own schema/tables and only accesses its own; the coupling comes from crossing ownership boundaries, not from sharing hardware.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shared database anti-pattern: multiple services read and write one table directly; the fix routes cross-service access through the owning service's API instead">
  <text x="150" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Anti-pattern</text>
  <rect x="30" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Orders</text>
  <rect x="210" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Reporting</text>
  <rect x="80" y="110" width="180" height="34" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="170" y="131" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE shared "customers" table</text>
  <line x1="75" y1="74" x2="140" y2="110" stroke="#f0883e"/>
  <line x1="255" y1="74" x2="200" y2="110" stroke="#f0883e"/>

  <text x="510" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Fixed</text>
  <rect x="420" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="465" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Orders</text>
  <rect x="420" y="90" width="90" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="465" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own table</text>

  <rect x="560" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="605" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Reporting</text>
  <line x1="465" y1="74" x2="540" y2="57" stroke="#8b949e" marker-end="url(#a2)"/>
  <text x="510" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Reporting calls Orders' API, never touches its table</text>
  <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Cross-service data access goes through the owning service's API, never directly against another service's tables.

## 5. Runnable example

Scenario: a Reporting component that needs customer data owned by an Orders service. We start with the anti-pattern (Reporting reads the shared table directly), extend it to show how an Orders-side schema change silently breaks Reporting, then handle the fix: Reporting goes through Orders' API, which stays stable even as the underlying storage changes.

### Level 1 — Basic

```java
// File: SharedTableAntiPattern.java -- Reporting reads Orders' table
// DIRECTLY, with no API in between: an anti-pattern shortcut.
import java.util.*;

public class SharedTableAntiPattern {
    // the "database": a table Orders considers its own, but Reporting also reads directly
    static List<Map<String, Object>> customersTable = new ArrayList<>(List.of(
        Map.of("id", 1, "name", "Alice", "totalSpent", 250.00)
    ));

    static class ReportingComponent {
        void printTopCustomer() {
            Map<String, Object> row = customersTable.get(0); // reaches directly into Orders' table
            System.out.println("[Reporting] Top customer: " + row.get("name") + ", spent $" + row.get("totalSpent"));
        }
    }

    public static void main(String[] args) {
        new ReportingComponent().printTopCustomer();
    }
}
```

How to run: `java SharedTableAntiPattern.java`

`ReportingComponent` reads `customersTable` — a structure Orders considers its own internal data — directly by field name (`"totalSpent"`). This works today, but Reporting now has an implicit dependency on Orders' exact internal column names, with no contract protecting it.

### Level 2 — Intermediate

```java
// File: SchemaChangeBreaksReporting.java -- Orders makes a perfectly
// reasonable internal change (splitting "totalSpent" into finer-grained
// fields) and Reporting BREAKS, because it depended on the raw schema.
import java.util.*;

public class SchemaChangeBreaksReporting {
    // Orders evolves its own table: "totalSpent" is now split into two more precise fields
    static List<Map<String, Object>> customersTable = new ArrayList<>(List.of(
        Map.of("id", 1, "name", "Alice", "lifetimeSpentCents", 25000, "currency", "USD")
    ));

    static class ReportingComponent {
        void printTopCustomer() {
            Map<String, Object> row = customersTable.get(0);
            Object totalSpent = row.get("totalSpent"); // this key no longer exists!
            System.out.println("[Reporting] Top customer: " + row.get("name") + ", spent $" + totalSpent);
        }
    }

    public static void main(String[] args) {
        new ReportingComponent().printTopCustomer(); // prints "spent $null" -- silently wrong, no error at all
    }
}
```

How to run: `java SchemaChangeBreaksReporting.java`

Orders' team renamed and restructured `totalSpent` into `lifetimeSpentCents` + `currency` — a completely reasonable internal improvement from Orders' point of view. But `Reporting` still looks up the old key `"totalSpent"`, which now silently returns `null` from the map rather than throwing a compile error, producing a wrong report (`spent $null`) with no warning at all. This is the specific danger of a shared table: the break is silent and semantic, not a loud compile-time or even runtime failure.

### Level 3 — Advanced

```java
// File: ApiOwnedFix.java -- the FIX: Orders exposes a stable API;
// Reporting calls the API, never the table. Orders is now free to
// restructure its internal storage without breaking Reporting.
import java.util.*;

public class ApiOwnedFix {
    static class OrdersService {
        // internal storage -- private, can change shape freely
        private List<Map<String, Object>> customersTable = new ArrayList<>(List.of(
            Map.of("id", 1, "name", "Alice", "lifetimeSpentCents", 25000, "currency", "USD")
        ));

        // the STABLE API contract: a dedicated method with an explicit, versioned return shape
        static class CustomerSpendSummary {
            String name; double totalSpentDollars;
            CustomerSpendSummary(String name, double totalSpentDollars) { this.name = name; this.totalSpentDollars = totalSpentDollars; }
        }

        CustomerSpendSummary getCustomerSpendSummary(int customerId) {
            Map<String, Object> row = customersTable.get(0); // internal lookup, private detail
            int cents = (int) row.get("lifetimeSpentCents");
            return new CustomerSpendSummary((String) row.get("name"), cents / 100.0); // API translates internal shape -> stable contract
        }
    }

    static class ReportingComponent {
        OrdersService orders;
        ReportingComponent(OrdersService orders) { this.orders = orders; }

        void printTopCustomer() {
            OrdersService.CustomerSpendSummary summary = orders.getCustomerSpendSummary(1); // calls the API, never the table
            System.out.println("[Reporting] Top customer: " + summary.name + ", spent $" + summary.totalSpentDollars);
        }
    }

    public static void main(String[] args) {
        OrdersService orders = new OrdersService();
        new ReportingComponent(orders).printTopCustomer();
        System.out.println("Fix: Orders can rename/restructure customersTable freely -- getCustomerSpendSummary's contract absorbs the change.");
    }
}
```

How to run: `java ApiOwnedFix.java`

`OrdersService.customersTable` is now a private field — `ReportingComponent` has no access to it at all. Instead, `ReportingComponent` calls `orders.getCustomerSpendSummary(1)`, a method with an explicit, stable return type (`CustomerSpendSummary`) that Orders' team controls. When Orders' internal storage changes shape (as it already has here, using `lifetimeSpentCents` internally), `getCustomerSpendSummary` is the one place that translates the internal representation into the stable API shape — Reporting never notices the internal change happened at all.

## 6. Walkthrough

Trace `ApiOwnedFix.main` end to end:

1. **`OrdersService` is constructed**, initializing its private `customersTable` with the restructured internal fields (`lifetimeSpentCents`, `currency`) — exactly the same "evolved" schema that broke Reporting in Level 2.
2. **`ReportingComponent` is constructed with a reference to `orders`**, but critically, it has no way to reach `orders.customersTable` — that field isn't exposed, by language-level access control, not just convention.
3. **`printTopCustomer()` calls `orders.getCustomerSpendSummary(1)`.** This is the only entry point Reporting has into Orders' data.
4. **Inside `getCustomerSpendSummary`, Orders reads its own private table** (`row.get("lifetimeSpentCents")`, `row.get("name")`) — this is the one piece of code that's allowed to know the table's actual current shape.
5. **Orders translates the internal representation into the API's stable contract**: `cents / 100.0` converts internal cents into the dollar figure the API promises, and a new `CustomerSpendSummary` object is constructed and returned.
6. **`ReportingComponent` receives a `CustomerSpendSummary`** with fields `name` and `totalSpentDollars` — a shape Orders has committed to keeping stable, regardless of what `customersTable` looks like internally next month.
7. **`printTopCustomer` prints the summary** using only the stable API fields, producing the correct output — unlike Level 2's silent `null`.

The key structural difference from Level 2: if Orders' team later renames `lifetimeSpentCents` yet again, or splits it further, only `getCustomerSpendSummary`'s implementation needs to change — its signature and return type are the contract, and Reporting's code doesn't change at all. That's the entire value of routing cross-service access through an API instead of a shared table: the coupling surface becomes an explicit, stable contract instead of an implicit, fragile schema.

## 7. Gotchas & takeaways

> **Gotcha:** a read-only reporting or analytics job querying another service's tables directly still creates the same coupling as a writer would — "we're only reading, not writing" doesn't protect against the owning service changing its schema out from under you; the break is just as silent and just as real.

- Every piece of data should have exactly one owning service with direct storage access; everyone else goes through that service's API, including for read-only access.
- A shared database *server* (shared hardware) is fine; a shared *table* crossing a service ownership boundary is the actual anti-pattern.
- The API is the stable, explicit contract; the schema underneath it is a private implementation detail the owning service should be free to change without notice.
- If you catch yourself reaching for a table another service owns because standing up a proper API "feels like overhead," that shortcut is exactly how distributed monoliths form — the coupling costs more later than the API would have cost now.
