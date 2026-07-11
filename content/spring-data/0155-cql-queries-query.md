---
card: spring-data
gi: 155
slug: cql-queries-query
title: "CQL queries & @Query"
---

## 1. What it is

CQL (Cassandra Query Language) is Cassandra's SQL-like query language — deliberately similar in syntax to SQL, but backed by fundamentally different execution semantics tied to the partition/clustering key model from the previous cards. `@Query` on a repository method lets you write CQL directly, with `?0`, `?1` markers bound to method parameters, the same positional-substitution mechanism already seen for JPQL and Elasticsearch's raw-JSON `@Query` earlier in this course.

```java
interface OrderRepository extends CassandraRepository<Order, OrderKey> {
    @Query("SELECT * FROM orders_by_customer WHERE customer_id = ?0 AND order_date >= ?1")
    List<Order> findRecentOrders(String customerId, Instant since);
}
```

## 2. Why & when

CQL looks like SQL — `SELECT`, `WHERE`, `AND` — which makes it approachable, but it is not a general-purpose query language the way SQL is: every `WHERE` clause must be satisfiable using the partition key (and, for range conditions, the clustering columns) established by the table's design, exactly as the earlier composite-key card explained. `@Query` is where you write CQL directly, for queries too specific or elaborate for a derived method name (the next card) to express as cleanly.

Reach for `@Query` with raw CQL when:

- You need a query with a specific `WHERE` clause structure — a clustering-column range condition, an `ORDER BY` (only ever on clustering columns, matching their declared order), or a `LIMIT` — that's clearer as CQL than as a derived method name.
- You're translating a query you've already tested directly against `cqlsh` (Cassandra's CLI) into your application, keeping the exact CQL you validated.
- You want explicit control over Cassandra-specific query options — consistency level, or `ALLOW FILTERING` when you've made a deliberate, informed decision to accept a full-partition scan.

## 3. Core concept

```
 @Query("SELECT * FROM orders_by_customer WHERE customer_id = ?0 AND order_date >= ?1")
 List<Order> findRecentOrders(String customerId, Instant since);

 findRecentOrders("customer-A", Instant.parse("2026-01-01T00:00:00Z"))
        |
        v
 ?0 -> "customer-A", ?1 -> 2026-01-01T00:00:00Z
        |
        v
 SELECT * FROM orders_by_customer WHERE customer_id = 'customer-A' AND order_date >= '2026-01-01T00:00:00Z'
        |
        v
 EFFICIENT because: customer_id is the PARTITION key (equality match, required)
                     order_date is a CLUSTERING column (range condition, allowed on clustering columns)
```

The query is only efficient because its `WHERE` clause structure matches the table's key design exactly — an equality condition on the full partition key, followed by a range condition on a clustering column.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Query parameters are substituted positionally into a CQL template, which is efficient because it filters by partition key equality and clustering column range">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">findRecentOrders("A", date)</text>

  <rect x="330" y="20" width="290" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">WHERE customer_id=?0 AND order_date&gt;=?1</text>

  <line x1="280" y1="42" x2="325" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <text x="150" y="90" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">?0 -&gt; partition key (equality)</text>
  <text x="475" y="90" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">?1 -&gt; clustering column (range)</text>

  <text x="320" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">this specific combination is what makes the query efficient in Cassandra</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Positional substitution works exactly like every other `@Query` mechanism in this course — the query's efficiency depends on matching the table's key structure, not on the substitution mechanism itself.

## 5. Runnable example

The scenario: querying an orders-by-customer table with raw CQL, evolving from a basic equality-on-partition-key query, to a range condition on a clustering column, to an `ORDER BY`/`LIMIT` combination — the standard shape of an efficient, well-formed Cassandra query.

### Level 1 — Basic

Model a basic CQL query template with positional substitution — equality on the partition key.

```java
import java.util.*;
import java.util.stream.*;

public class CqlQueryLevel1 {
    public static void main(String[] args) {
        List<Order> table = List.of(
            new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"),
            new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"),
            new Order("customer-B", "2026-02-10", "order-3", "PENDING")
        );

        // Mirrors: @Query("SELECT * FROM orders_by_customer WHERE customer_id = ?0")
        List<Order> matches = executeQuery(table, "customer-A");
        System.out.println("Orders for customer-A: " + matches.stream().map(o -> o.orderId).collect(Collectors.toList()));
    }

    // Equality on the PARTITION key -- efficient, resolves to exactly one partition.
    static List<Order> executeQuery(List<Order> table, String customerId) {
        return table.stream().filter(o -> o.customerId.equals(customerId)).collect(Collectors.toList());
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }
```

How to run: `java CqlQueryLevel1.java`

`executeQuery` filters purely by `customerId` equality, mirroring `SELECT * FROM orders_by_customer WHERE customer_id = ?0` — an equality condition on the full partition key, the simplest and always-efficient CQL query shape.

### Level 2 — Intermediate

Add a range condition on a clustering column, matching the intro snippet's `findRecentOrders`.

```java
import java.util.*;
import java.util.stream.*;

public class CqlQueryLevel2 {
    public static void main(String[] args) {
        List<Order> table = List.of(
            new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"),
            new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"),
            new Order("customer-A", "2026-06-02", "order-9", "PENDING")
        );

        // Mirrors: @Query("SELECT * FROM orders_by_customer WHERE customer_id = ?0 AND order_date >= ?1")
        List<Order> recentOrders = findRecentOrders(table, "customer-A", "2026-03-01");
        System.out.println("customer-A's orders since 2026-03-01: " + recentOrders.stream().map(o -> o.orderId).collect(Collectors.toList()));
    }

    // Equality on the PARTITION key, PLUS a range condition on a CLUSTERING column -- still efficient.
    static List<Order> findRecentOrders(List<Order> table, String customerId, String sinceDate) {
        return table.stream()
            .filter(o -> o.customerId.equals(customerId))
            .filter(o -> o.orderDate.compareTo(sinceDate) >= 0)
            .collect(Collectors.toList());
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }
```

How to run: `java CqlQueryLevel2.java`

`findRecentOrders` filters by `customerId` equality first (locating the partition), then applies a range condition on `orderDate` (a clustering column) — this exact combination is what CQL allows to remain efficient: an equality match on the partition key, followed by range conditions on clustering columns in their declared order, resolved directly against the sorted, co-located rows within that one partition.

### Level 3 — Advanced

Add `ORDER BY` and `LIMIT`, matching CQL's constraint that `ORDER BY` is only valid on clustering columns, in an order consistent with (or the reverse of) how they're declared.

```java
import java.util.*;
import java.util.stream.*;

public class CqlQueryLevel3 {
    public static void main(String[] args) {
        List<Order> table = List.of(
            new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"),
            new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"),
            new Order("customer-A", "2026-06-02", "order-9", "PENDING")
        );

        // Mirrors: @Query("SELECT * FROM orders_by_customer WHERE customer_id = ?0 ORDER BY order_date DESC LIMIT ?1")
        List<Order> mostRecentTwo = findMostRecent(table, "customer-A", 2);
        System.out.println("customer-A's 2 most recent orders: " + mostRecentTwo.stream().map(o -> o.orderId + "@" + o.orderDate).collect(Collectors.toList()));
    }

    // ORDER BY on a CLUSTERING column (reversing its natural ascending order), plus LIMIT -- both CQL-legal
    // ONLY because order_date is a clustering column, not an arbitrary field.
    static List<Order> findMostRecent(List<Order> table, String customerId, int limit) {
        return table.stream()
            .filter(o -> o.customerId.equals(customerId))
            .sorted(Comparator.comparing((Order o) -> o.orderDate).reversed()) // ORDER BY order_date DESC
            .limit(limit)                                                      // LIMIT ?1
            .collect(Collectors.toList());
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }
```

How to run: `java CqlQueryLevel3.java`

`findMostRecent` sorts by `orderDate` in reverse (descending) order and takes only the first `limit` results, mirroring `ORDER BY order_date DESC LIMIT ?1`. This is only a legal, efficient CQL query because `order_date` is a clustering column — since Cassandra already maintains rows within a partition sorted by clustering columns on disk, reversing that order (or reading it in its natural order) and limiting the result requires no additional sorting work at query time, just reading in the opposite physical direction.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders for `customer-A` are defined with dates `2026-01-01`, `2026-03-15`, `2026-06-02`.

`findMostRecent(table, "customer-A", 2)` filters to only `customer-A`'s orders (all three, in this case), then calls `.sorted(Comparator.comparing((Order o) -> o.orderDate).reversed())`, which sorts them by `orderDate` descending — `2026-06-02` (order-9) first, then `2026-03-15` (order-5), then `2026-01-01` (order-1). `.limit(2)` then keeps only the first two results from that sorted stream, discarding `order-1`.

```
customer-A's 2 most recent orders: [order-9@2026-06-02, order-5@2026-03-15]
```

In real Cassandra, `SELECT * FROM orders_by_customer WHERE customer_id = 'customer-A' ORDER BY order_date DESC LIMIT 2` is executed by reading `customer-A`'s partition from the *end* (since clustering order is maintained physically, reading in reverse is just as efficient as reading forward) and stopping after two rows — no in-memory sort of the whole partition is needed at query time, because the sort order was already established when the data was written, exactly as this Java example's `Comparator`-based sort conceptually mirrors but Cassandra achieves "for free" from its storage layout.

## 7. Gotchas & takeaways

> Gotcha: `ORDER BY` in CQL can *only* reference clustering columns, and only in an order consistent with how they were declared (or their exact reverse) — you cannot `ORDER BY` an arbitrary non-clustering-column field, and attempting to do so is rejected by Cassandra outright, not silently slow.

> Gotcha: a `WHERE` clause missing an equality condition on the *full* partition key (for a composite partition key spanning multiple columns) generally isn't allowed without `ALLOW FILTERING` — CQL requires you to fully specify the partition before applying any clustering-column conditions, since that's what lets Cassandra locate the right node(s) before it even starts reading rows.

- CQL resembles SQL syntactically but is fundamentally constrained by the table's partition/clustering key structure — a `WHERE` clause is only efficient (and often only legal) when it matches that structure.
- `@Query` with raw CQL uses the same `?0`, `?1` positional marker substitution seen for `@Query` in the JPA and Elasticsearch sections earlier in this course.
- `ORDER BY` and range conditions are valid only on clustering columns, in their declared order (or exact reverse) — this isn't a performance suggestion, it's a hard constraint CQL enforces.
- Because clustering order is maintained physically on disk, `ORDER BY`/`LIMIT` queries on clustering columns require no runtime sorting at all, unlike the equivalent query against an arbitrary field in a relational database.
