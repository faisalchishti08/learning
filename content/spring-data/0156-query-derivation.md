---
card: spring-data
gi: 156
slug: query-derivation
title: "Query derivation"
---

## 1. What it is

Query derivation generates CQL automatically from a repository method's name — the same mechanism seen throughout this course for JPA, MongoDB, and Elasticsearch — but for Cassandra, the derivation is far more constrained: a derived method can only filter on fields that satisfy the table's partition/clustering key structure from the previous cards, or Spring Data Cassandra refuses to generate it at all, catching the mismatch at application startup rather than letting it fail (or silently full-scan) at runtime.

```java
interface OrderRepository extends CassandraRepository<Order, OrderKey> {
    List<Order> findByCustomerId(String customerId);                          // OK: partition key
    List<Order> findByCustomerIdAndOrderDateGreaterThan(String c, Instant d);  // OK: partition key + clustering range
    List<Order> findByStatus(String status);                                  // FAILS at startup -- not a key field
}
```

## 2. Why & when

Every other Spring Data module covered in this course lets you write essentially any derived method name and generates a working (if not always efficient) query for it. Cassandra's query derivation is deliberately stricter: because an inefficient or impossible query in Cassandra isn't just slow, it's often outright disallowed by the database itself, Spring Data Cassandra validates a derived method's field references against the entity's declared primary key structure *when the application starts*, failing fast with a clear error rather than deploying a repository method that would blow up (or silently full-scan) the first time it's actually called.

Reach for query derivation on Cassandra when:

- The query filters only on the partition key (equality) and, optionally, clustering columns (equality or range, in their declared order) — exactly the queries CQL itself can execute efficiently.
- You want the same startup-time validation as a compile-time check: catching a query that doesn't match the table's key design during development, not after a production deploy.
- The derived method name maps cleanly to the exact `WHERE`/`ORDER BY`/`LIMIT` structure you'd otherwise write by hand in `@Query` — for those cases, derivation is simply less code with the same result.

## 3. Core concept

```
 Table: PRIMARY KEY ((customer_id), order_date, order_id)

 findByCustomerId(String customerId)
        -> WHERE customer_id = ?               -- equality on the FULL partition key -- ALWAYS valid

 findByCustomerIdAndOrderDateGreaterThan(String customerId, Instant orderDate)
        -> WHERE customer_id = ? AND order_date > ?   -- partition key + clustering RANGE, in declared order -- VALID

 findByStatus(String status)
        -> status is NEITHER the partition key NOR a clustering column
        -> Spring Data Cassandra REFUSES to create this repository bean at STARTUP, with a clear error
```

Unlike other Spring Data modules, an invalid derived method here is caught immediately when the application context starts, not discovered later when the method is actually called.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A derived method matching the key structure is validated successfully at startup, while one referencing a non-key field fails validation">
  <rect x="20" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">findByCustomerId(...)</text>

  <rect x="340" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">findByStatus(...)</text>

  <rect x="20" y="90" width="280" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="160" y="114" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">startup: VALID, bean created</text>

  <rect x="340" y="90" width="280" height="40" rx="6" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="480" y="114" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">startup: FAILS, application won't start</text>

  <line x1="160" y1="65" x2="160" y2="85" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="480" y1="65" x2="480" y2="85" stroke="#f85149" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Cassandra's stricter derived-query validation happens once, at application startup, rather than being discovered later during normal operation.

## 5. Runnable example

The scenario: a repository for the orders-by-customer table, evolving from basic valid derived methods, to startup-time validation catching an invalid derived method, to a valid multi-condition derived method combining partition and clustering filters — mirroring the exact CQL from the previous card, now generated from method names alone.

### Level 1 — Basic

Model a basic, valid derived method — equality on the partition key.

```java
import java.util.*;
import java.util.stream.*;

public class QueryDerivationLevel1 {
    public static void main(String[] args) {
        List<Order> table = List.of(
            new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"),
            new Order("customer-B", "2026-02-10", "order-3", "PENDING")
        );
        OrderRepository repo = new OrderRepository(table);

        List<Order> results = repo.findByCustomerId("customer-A");
        System.out.println("findByCustomerId(\"customer-A\"): " + results.stream().map(o -> o.orderId).collect(Collectors.toList()));
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }

// Stands in for a generated implementation of: List<Order> findByCustomerId(String customerId);
class OrderRepository {
    private final List<Order> table;
    OrderRepository(List<Order> table) { this.table = table; }

    // customerId IS the partition key -- equality is always a valid, efficient derived query.
    List<Order> findByCustomerId(String customerId) {
        return table.stream().filter(o -> o.customerId.equals(customerId)).collect(Collectors.toList());
    }
}
```

How to run: `java QueryDerivationLevel1.java`

`findByCustomerId` is derived purely from its method name and works correctly because `customerId` is the table's partition key — the simplest, always-valid Cassandra derived query shape, requiring no additional validation concern.

### Level 2 — Intermediate

Model Spring Data Cassandra's startup-time validation catching an invalid derived method — one referencing a field that isn't part of the key.

```java
import java.util.*;
import java.util.stream.*;

public class QueryDerivationLevel2 {
    // Mirrors the SET of columns that make up the table's primary key -- what Spring Data Cassandra validates against.
    static final Set<String> KEY_FIELDS = Set.of("customerId", "orderDate", "orderId");

    // Mirrors Spring Data Cassandra's startup-time repository bean creation, validating EVERY derived method name.
    static void validateDerivedMethod(String methodName, List<String> referencedFields) {
        for (String field : referencedFields) {
            if (!KEY_FIELDS.contains(field)) {
                throw new InvalidDerivedQueryException(
                    "Cannot derive query for method '" + methodName + "': field '" + field
                        + "' is not part of the primary key (partition or clustering column).");
            }
        }
    }

    public static void main(String[] args) {
        // VALID: customerId is the partition key.
        validateDerivedMethod("findByCustomerId", List.of("customerId"));
        System.out.println("findByCustomerId: validated OK, repository bean created.");

        // INVALID: status is not part of the key at all.
        try {
            validateDerivedMethod("findByStatus", List.of("status"));
        } catch (InvalidDerivedQueryException e) {
            System.out.println("findByStatus: FAILED validation -- " + e.getMessage());
            System.out.println("(in a real application, this would prevent the application context from starting up at all)");
        }
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }

class InvalidDerivedQueryException extends RuntimeException { InvalidDerivedQueryException(String msg) { super(msg); } }
```

How to run: `java QueryDerivationLevel2.java`

`validateDerivedMethod` mirrors what Spring Data Cassandra does internally when scanning repository interfaces at startup: for each derived method, it checks every referenced field against the entity's known key fields. `findByCustomerId` passes because `customerId` is in `KEY_FIELDS`; `findByStatus` fails immediately, because `status` was never declared as part of the primary key — in a real application, this exact mismatch prevents the Spring application context from starting at all, rather than deploying successfully and failing (or silently misbehaving) only when the method is actually invoked.

### Level 3 — Advanced

Model a valid multi-condition derived method combining an equality condition on the partition key with a range condition on a clustering column — matching the previous card's `findRecentOrders`, but generated purely from the method name.

```java
import java.util.*;
import java.util.stream.*;

public class QueryDerivationLevel3 {
    public static void main(String[] args) {
        List<Order> table = List.of(
            new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"),
            new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"),
            new Order("customer-A", "2026-06-02", "order-9", "PENDING")
        );
        OrderRepository repo = new OrderRepository(table);

        List<Order> results = repo.findByCustomerIdAndOrderDateGreaterThanEqual("customer-A", "2026-03-01");
        System.out.println("Derived query results: " + results.stream().map(o -> o.orderId).collect(Collectors.toList()));
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }

// Stands in for: List<Order> findByCustomerIdAndOrderDateGreaterThanEqual(String customerId, String orderDate);
class OrderRepository {
    private final List<Order> table;
    OrderRepository(List<Order> table) { this.table = table; }

    // Derived from the method name: equality on customerId (partition key), range on orderDate (clustering column).
    // Spring Data Cassandra parses "CustomerId" + "OrderDateGreaterThanEqual" and validates BOTH against the key.
    List<Order> findByCustomerIdAndOrderDateGreaterThanEqual(String customerId, String orderDate) {
        return table.stream()
            .filter(o -> o.customerId.equals(customerId))     // equality on partition key
            .filter(o -> o.orderDate.compareTo(orderDate) >= 0) // range on clustering column
            .collect(Collectors.toList());
    }
}
```

How to run: `java QueryDerivationLevel3.java`

`findByCustomerIdAndOrderDateGreaterThanEqual`'s method name is parsed into two conditions — `CustomerId` (equality) and `OrderDateGreaterThanEqual` (a range operator on `orderDate`) — exactly matching the previous card's hand-written `@Query`, but expressed entirely through the method name's naming convention. Spring Data Cassandra validates both `customerId` and `orderDate` against the table's key structure at startup, confirms both are legal (partition key and clustering column, respectively, in the correct relative roles), and generates the equivalent CQL automatically.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders for `customer-A` are defined, spanning dates `2026-01-01`, `2026-03-15`, `2026-06-02`.

`repo.findByCustomerIdAndOrderDateGreaterThanEqual("customer-A", "2026-03-01")` runs `table.stream()` through two chained filters. The first, `o.customerId.equals("customer-A")`, keeps all three orders (they all belong to `customer-A`). The second, `o.orderDate.compareTo("2026-03-01") >= 0`, compares each order's date string against `"2026-03-01"`: `"2026-01-01".compareTo("2026-03-01")` is negative (excluded), `"2026-03-15".compareTo("2026-03-01")` is positive (included), `"2026-06-02".compareTo("2026-03-01")` is positive (included).

```
Derived query results: [order-5, order-9]
```

In real Spring Data Cassandra, this exact method — declared purely as `List<Order> findByCustomerIdAndOrderDateGreaterThanEqual(String customerId, Instant orderDate);` on the repository interface — is parsed at startup: `CustomerId` becomes an equality condition, `OrderDateGreaterThanEqual` becomes a `>=` range condition, both validated against `Order`'s declared `@PrimaryKeyColumn` structure, and the framework generates `SELECT * FROM orders_by_customer WHERE customer_id = ? AND order_date >= ?` automatically — identical CQL to what the previous card's hand-written `@Query` produced, with less code and the added safety of startup-time validation.

## 7. Gotchas & takeaways

> Gotcha: query derivation validates *structure* (which fields are referenced, and whether they're key fields) but does not validate that the *combination* makes semantic sense for Cassandra's ordering rules — a derived method combining range conditions on two different clustering columns in the wrong relative order (skipping over an earlier clustering column entirely) can still fail at startup or produce a query CQL itself rejects, even though every individual field referenced is technically part of the key.

> Gotcha: because Cassandra's derived-query validation is so much stricter than other Spring Data modules, it's tempting to reach for `@Query` with `ALLOW FILTERING` (or a secondary index) to "just make it work" the first time a derived method fails validation — resist that instinct as a default. The failing validation is usually correctly telling you the table's key design doesn't match this new access pattern, and the earlier "model a second table per query pattern" guidance is almost always the better fix.

- Query derivation for Cassandra generates CQL from method names exactly like every other Spring Data module in this course, but validates every referenced field against the entity's declared primary key structure.
- An invalid derived method (referencing a non-key field) is caught at application startup, not discovered later when the method is called — a meaningful safety improvement over how this failure mode surfaces in other, less constrained Spring Data modules.
- Valid derived methods combine equality on the partition key with equality or range conditions on clustering columns, in their declared order — the same query shapes the previous `@Query` card covered by hand.
- A derived method that fails validation is a strong signal the table's key design doesn't match the intended access pattern — reach for a redesigned or additional table before reaching for `ALLOW FILTERING`.
