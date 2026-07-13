---
card: microservices
gi: 306
slug: private-tables-schema-per-service
title: "Private tables / schema per service"
---

## 1. What it is

Schema-per-service (also called private-tables) is a middle ground between full [database-per-service](0304-database-per-service-pattern.md) (a fully separate database instance per service) and the [shared database anti-pattern](0305-shared-database-anti-pattern.md): all services' data lives in the same physical database server, but each service gets its own schema (or namespace/prefix) with access controls that prevent any other service from touching it. Logical isolation is enforced through database permissions rather than through physically separate server instances.

## 2. Why & when

Running a fully separate database server per service has real operational cost: more instances to provision, patch, back up, and monitor, and for a system with many small services, this overhead can be disproportionate to any single service's actual load. Schema-per-service keeps that isolation — the crucial property that no service can accidentally or deliberately reach into another's tables — while sharing the underlying database engine, its connection infrastructure, and its operational tooling, at the cost of some resource contention between services (they still compete for the same server's CPU, memory, and I/O) and a shared blast radius if the physical database server itself goes down.

Use schema-per-service when the operational overhead of fully separate database instances isn't justified — for a set of small, low-traffic services, or during an incremental migration where physically separating databases can happen later once the pattern's value is proven. It preserves the core discipline of database-per-service (services never touch each other's data directly) while being cheaper to operate; reach for fully separate instances specifically when a service's scaling, availability, or technology needs genuinely diverge from the rest (e.g., one service needs a different database engine, or needs to scale its data tier independently of everyone else).

## 3. Core concept

Each service connects with credentials scoped only to its own schema; the database's own permission system — not application code discipline alone — enforces the boundary.

```sql
-- One physical database SERVER, multiple SCHEMAS, one per service.
CREATE SCHEMA order_service;
CREATE SCHEMA inventory_service;

CREATE TABLE order_service.orders (id BIGINT PRIMARY KEY, status VARCHAR(20));
CREATE TABLE inventory_service.stock (sku VARCHAR(50) PRIMARY KEY, quantity INT);

-- Each service's DB USER can only see and touch its OWN schema.
CREATE USER order_service_user WITH PASSWORD '...';
GRANT ALL ON SCHEMA order_service TO order_service_user;
REVOKE ALL ON SCHEMA inventory_service FROM order_service_user; -- enforced by the DATABASE, not just convention
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One physical database server hosts multiple separate schemas, one per service; each service connects with credentials scoped only to its own schema, so the database's own permission system enforces isolation even though all data lives on the same physical server">
  <rect x="20" y="20" width="600" height="130" rx="8" fill="none" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="38" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ONE physical database server</text>

  <rect x="50" y="55" width="170" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order_service schema</text>
  <text x="135" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">accessible ONLY by</text>
  <text x="135" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">order_service_user</text>

  <rect x="420" y="55" width="170" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="505" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory_service schema</text>
  <text x="505" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">accessible ONLY by</text>
  <text x="505" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">inventory_service_user</text>

  <line x1="220" y1="90" x2="420" y2="90" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="320" y="145" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">REVOKED: cross-schema access blocked by the database's own permission system</text>
</svg>

Shared server, separate schemas, isolation enforced by database credentials rather than application discipline alone.

## 5. Runnable example

Scenario: services sharing one namespace with no real access boundary, extended to model per-service credentials that enforce schema isolation the way a real database permission system does, and finally simulating an actual permission-denied error when a service attempts to reach outside its granted schema, showing the boundary is enforced mechanically rather than by convention.

### Level 1 — Basic

```java
// File: NoSchemaIsolation.java -- all "services" share ONE namespace
// with no access control at all -- any service can read or write any
// other service's tables freely.
import java.util.*;

public class NoSchemaIsolation {
    static Map<String, Map<String, Object>> allTables = new HashMap<>();
    static { allTables.put("orders", new HashMap<>(Map.of("count", 5))); allTables.put("stock", new HashMap<>(Map.of("count", 100))); }

    static Object read(String table, String field) { return allTables.get(table).get(field); } // NO access check

    public static void main(String[] args) {
        // "InventoryService" can freely read (or WRITE) "orders", which it does not own.
        System.out.println("InventoryService reading OrderService's table directly: " + read("orders", "count")
                + " -- nothing stops this, there is no concept of ownership at all.");
    }
}
```

How to run: `java NoSchemaIsolation.java`

`read` has no notion of which "service" is asking or which table it's permitted to touch — any caller can read (or, with a symmetric `write` method, modify) any table. This is the shared-database anti-pattern in its rawest form: total absence of an enforced boundary.

### Level 2 — Intermediate

```java
// File: SchemaScopedCredentials.java -- models real database permission
// enforcement: each "connection" is scoped to exactly one schema, and
// any attempt to reach outside that schema is REJECTED by the access
// layer itself, not just discouraged by convention.
import java.util.*;

public class SchemaScopedCredentials {
    static Map<String, Map<String, Object>> schemas = new HashMap<>();
    static {
        schemas.put("order_service", new HashMap<>(Map.of("orders_count", 5)));
        schemas.put("inventory_service", new HashMap<>(Map.of("stock_count", 100)));
    }

    // A "connection" scoped to exactly ONE schema -- mirrors a real DB user
    // whose GRANTs only cover their own schema.
    static class ScopedConnection {
        final String allowedSchema;
        ScopedConnection(String allowedSchema) { this.allowedSchema = allowedSchema; }

        Object read(String schema, String field) {
            if (!schema.equals(allowedSchema)) {
                throw new SecurityException("permission denied: '" + allowedSchema
                        + "' user cannot access schema '" + schema + "'");
            }
            return schemas.get(schema).get(field);
        }
    }

    public static void main(String[] args) {
        ScopedConnection orderServiceConn = new ScopedConnection("order_service");

        System.out.println("OrderService reading its OWN schema: " + orderServiceConn.read("order_service", "orders_count"));
        try {
            orderServiceConn.read("inventory_service", "stock_count"); // attempting to reach OUTSIDE its schema
        } catch (SecurityException e) {
            System.out.println("OrderService attempting to read inventory_service's schema: BLOCKED -- " + e.getMessage());
        }
    }
}
```

How to run: `java SchemaScopedCredentials.java`

`orderServiceConn` is scoped to only the `"order_service"` schema, mirroring a real database user whose GRANTs cover only that schema. Reading its own schema succeeds normally. Attempting to read `"inventory_service"` — even though the data technically lives in the same `schemas` map, the same physical process — is rejected with a `SecurityException`, exactly as a real database engine would reject a query from a user lacking `SELECT` privilege on another schema, regardless of how "close" the data physically is.

### Level 3 — Advanced

```java
// File: MultiServiceGrantMatrix.java -- models a realistic set of
// several services with a full grant matrix (who can access what),
// demonstrating that the enforcement is purely mechanical: it depends
// ENTIRELY on the granted permissions, not on which "service" is asking
// or its intentions -- exactly how a real database's GRANT/REVOKE system works.
import java.util.*;

public class MultiServiceGrantMatrix {
    static Map<String, Map<String, Object>> schemas = Map.of(
            "order_service", Map.of("orders_count", 5),
            "inventory_service", Map.of("stock_count", 100),
            "billing_service", Map.of("invoices_count", 3)
    );

    // GRANT matrix: which DB user may access which schema(s).
    // Mirrors real GRANT statements a DBA would run.
    static Map<String, Set<String>> grants = Map.of(
            "order_service_user", Set.of("order_service"),
            "inventory_service_user", Set.of("inventory_service"),
            "billing_service_user", Set.of("billing_service", "order_service") // billing legitimately needs BOTH
    );

    static class ScopedConnection {
        final String dbUser;
        ScopedConnection(String dbUser) { this.dbUser = dbUser; }
        Object read(String schema, String field) {
            if (!grants.getOrDefault(dbUser, Set.of()).contains(schema)) {
                throw new SecurityException("permission denied: '" + dbUser + "' has no GRANT on schema '" + schema + "'");
            }
            return schemas.get(schema).get(field);
        }
    }

    public static void main(String[] args) {
        ScopedConnection billing = new ScopedConnection("billing_service_user");
        ScopedConnection inventory = new ScopedConnection("inventory_service_user");

        System.out.println("billing_service_user reading order_service (GRANTED, needed for invoicing): "
                + billing.read("order_service", "orders_count"));
        System.out.println("billing_service_user reading billing_service (own schema): "
                + billing.read("billing_service", "invoices_count"));
        try {
            billing.read("inventory_service", "stock_count"); // billing has NO legitimate need for this
        } catch (SecurityException e) {
            System.out.println("billing_service_user reading inventory_service (NOT granted): BLOCKED -- " + e.getMessage());
        }
        try {
            inventory.read("order_service", "orders_count"); // inventory has no need for order data either
        } catch (SecurityException e) {
            System.out.println("inventory_service_user reading order_service (NOT granted): BLOCKED -- " + e.getMessage());
        }
    }
}
```

How to run: `java MultiServiceGrantMatrix.java`

Three services' schemas exist, with a grant matrix reflecting real, deliberate access decisions: `billing_service_user` is granted access to both its own schema *and* `order_service`'s schema (a legitimate, explicit exception — billing genuinely needs order data to generate invoices), while `inventory_service_user` has no such grant to `order_service` at all. The `billing` connection successfully reads both `order_service` and `billing_service`; the `inventory` connection is blocked from reading `order_service`, even though nothing about `inventory_service_user`'s "intentions" differ conceptually from `billing_service_user`'s — the enforcement is purely mechanical, based entirely on what was explicitly granted, exactly matching how a real database's `GRANT`/`REVOKE` permission system works, and exactly how a deliberate, reviewed cross-schema access exception (billing needing order data) should be modeled: an explicit grant, not an ambient shared connection everyone happens to use.

## 6. Walkthrough

Trace `MultiServiceGrantMatrix.main`'s final blocked call. **First**, `inventory` is constructed as a `ScopedConnection` with `dbUser = "inventory_service_user"`.

**`inventory.read("order_service", "orders_count")` is called.** Inside `read`, the first line is `grants.getOrDefault(dbUser, Set.of()).contains(schema)`. `grants.get("inventory_service_user")` retrieves `Set.of("inventory_service")` — the set of schemas this user is explicitly granted access to. The check `.contains("order_service")` evaluates against this set: `"order_service"` is not a member of `{"inventory_service"}`, so the check returns `false`.

**Since the permission check failed** (`!contains(...)` is `true`), the method immediately throws a `SecurityException` with a message naming both the denied user and the schema it attempted to access — the method never reaches the line that would actually retrieve data from `schemas.get(schema)`; the rejection happens purely at the permission-check layer, before any data access is attempted.

**Back in `main`**, this exception is caught and printed as a "BLOCKED" message.

**Contrast with `billing.read("order_service", "orders_count")`**, traced earlier in the same run: `grants.get("billing_service_user")` retrieves `Set.of("billing_service", "order_service")`. The check `.contains("order_service")` this time evaluates `true`, since `billing_service_user` has an explicit, deliberate grant covering that schema — the method proceeds past the permission check and returns `schemas.get("order_service").get("orders_count")`, which is `5`.

**The structural point**: both `billing` and `inventory` are running the exact same `read` method against the exact same underlying `schemas` data structure — the only thing that differs between "billing can read order_service" and "inventory cannot" is a single entry in the `grants` map, configured explicitly and deliberately ahead of time, precisely mirroring how a real database administrator would run `GRANT SELECT ON SCHEMA order_service TO billing_service_user;` as an explicit, reviewed decision, while leaving `inventory_service_user` with no such grant.

```
billing.read("order_service", ...)   -> grants["billing_service_user"] contains "order_service"?    YES -> data returned
inventory.read("order_service", ...) -> grants["inventory_service_user"] contains "order_service"?  NO  -> SecurityException
```

## 7. Gotchas & takeaways

> A schema-per-service boundary is only as strong as the actual database grants behind it — if every service's connection string uses the same superuser or admin credentials "for convenience," the schema separation exists in name only, and any service can still read or write any other service's tables, silently reintroducing the shared-database anti-pattern despite the schemas being logically separate.

- Schema-per-service delivers the core isolation benefit of database-per-service (no service can touch another's data directly) at lower operational cost than fully separate database server instances, at the price of shared physical resource contention and a shared server-level blast radius.
- Enforce isolation with real, minimal-privilege database credentials per service — each service's connection should be granted access to only its own schema, with any deliberate cross-schema exception (like billing needing order data) modeled as an explicit, reviewed grant, not an ambient shared superuser connection.
- This pattern is a reasonable default for smaller services or during incremental migration; move to fully separate database instances specifically when a service's scaling, availability, or database-technology needs genuinely diverge from its neighbors.
- Even with correct grants, remember that schema-per-service does not provide full physical isolation — a database server outage, a noisy-neighbor resource contention issue, or a maintenance window still affects every co-located service simultaneously, unlike fully separate database instances.
