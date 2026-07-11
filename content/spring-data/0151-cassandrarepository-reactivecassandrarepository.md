---
card: spring-data
gi: 151
slug: cassandrarepository-reactivecassandrarepository
title: "CassandraRepository / ReactiveCassandraRepository"
---

## 1. What it is

`CassandraRepository<T, ID>` and `ReactiveCassandraRepository<T, ID>` are the generated-implementation repository interfaces for Cassandra, following the exact pattern established across every Spring Data module in this course: extend the interface, and Spring Data generates `save`/`findById`/`delete` plus derived query methods, backed by `CassandraTemplate`/`ReactiveCassandraTemplate` underneath.

```java
interface OrderRepository extends CassandraRepository<Order, String> {
    List<Order> findByStatus(String status); // status must be part of the primary key, or this needs a secondary index
}

interface ReactiveOrderRepository extends ReactiveCassandraRepository<Order, String> {
    Flux<Order> findByStatus(String status);
}
```

## 2. Why & when

Just as with every other Spring Data module, `CassandraTemplate` (the previous card) is powerful but requires explicit calls for every operation. `CassandraRepository`/`ReactiveCassandraRepository` bring the same familiar CRUD-plus-derived-methods convenience to Cassandra — with one crucial difference from every prior module: **which** derived query methods are even possible depends heavily on the table's primary key structure, because Cassandra fundamentally cannot filter arbitrarily the way a relational database's `WHERE` clause or MongoDB's flexible query engine can.

Reach for `CassandraRepository`/`ReactiveCassandraRepository` when:

- You want standard CRUD without hand-building queries — the same reason to reach for any Spring Data repository.
- Your derived query methods filter only on fields that are part of the table's primary key (partition key or clustering columns) — Cassandra can efficiently answer these without scanning the whole table.
- You've deliberately designed the table's primary key around the queries you need (Cassandra's "query-first" modeling discipline from the previous card) — the repository's derived methods are a direct reflection of that design, not a substitute for it.

## 3. Core concept

```
 CREATE TABLE orders (
     order_id  text,
     status    text,
     PRIMARY KEY (order_id)
 );

 orderRepository.findById(orderId)     -- WORKS: order_id is the partition key, always efficient
 orderRepository.findByStatus(status)  -- FAILS or requires ALLOW FILTERING: status is NOT part of the primary key

 -- Cassandra needs the primary key (or a secondary index) to locate rows WITHOUT scanning every partition --
 -- unlike JPA/MongoDB, a derived method on a non-key field isn't automatically efficient (or sometimes even possible)
```

Whether a derived query method works efficiently — or works at all without an explicit secondary index — depends entirely on the underlying table's key design, not on Spring Data's query-generation logic.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A query on the partition key resolves directly to one partition, while a query on a non-key field requires scanning every partition">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="150" y="47" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">findById(orderId) -- direct partition lookup</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="490" y="47" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus(s) -- scans ALL partitions</text>

  <text x="320" y="110" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">the SAME repository pattern, but very different cost depending on the field queried</text>
</svg>

The repository programming model is identical to every other Spring Data module; the cost characteristics of the queries it generates are not.

## 5. Runnable example

The scenario: a generated `OrderRepository`, evolving from a basic derived `findById` (efficient, partition-key-based), to demonstrating why `findByStatus` on a non-key field is fundamentally different in cost, to a properly key-designed table where a second derived method becomes efficient because the key was designed for it.

### Level 1 — Basic

Model an efficient `findById` lookup: a direct partition-key access.

```java
import java.util.*;

public class CassandraRepoLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "PENDING"));
        repo.save(new Order("2", "SHIPPED"));

        Order found = repo.findById("1");
        System.out.println("findById(\"1\"): status=" + found.status + " -- direct partition access, no scan needed");
    }
}

class Order { String orderId; String status; Order(String orderId, String status) { this.orderId = orderId; this.status = status; } }

// Stands in for a generated implementation of: interface OrderRepository extends CassandraRepository<Order, String> { }
class OrderRepository {
    private final Map<String, Order> table = new HashMap<>(); // keyed by orderId -- the PARTITION KEY
    void save(Order order) { table.put(order.orderId, order); }
    Order findById(String orderId) { return table.get(orderId); } // O(1) -- goes DIRECTLY to the right partition
}
```

How to run: `java CassandraRepoLevel1.java`

`findById` maps directly to `table.get(orderId)` — an O(1) lookup, matching how Cassandra resolves a partition-key query directly to the node(s) owning that partition, with no need to inspect any other partition's data at all.

### Level 2 — Intermediate

Demonstrate why `findByStatus` on a non-key field is a fundamentally different, more expensive operation: it must inspect every partition, since `status` isn't part of the key that determines where a row physically lives.

```java
import java.util.*;
import java.util.stream.*;

public class CassandraRepoLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        for (int i = 1; i <= 1000; i++) repo.save(new Order("order-" + i, i % 3 == 0 ? "SHIPPED" : "PENDING"));

        List<Order> shipped = repo.findByStatus("SHIPPED");
        System.out.println("findByStatus(\"SHIPPED\"): found " + shipped.size() + " orders");
    }
}

class Order { String orderId; String status; Order(String orderId, String status) { this.orderId = orderId; this.status = status; } }

class OrderRepository {
    private final Map<String, Order> table = new HashMap<>();
    void save(Order order) { table.put(order.orderId, order); }

    // Derived from "findByStatus" on a NON-key field -- Cassandra CANNOT jump directly to matching rows.
    // In real Cassandra, this either requires a secondary index (with its own caveats) or ALLOW FILTERING
    // (a full-cluster scan across every partition), which is exactly what this method models.
    List<Order> findByStatus(String status) {
        int partitionsScanned = table.size(); // EVERY partition must be checked -- there's no shortcut
        System.out.println("  (had to scan all " + partitionsScanned + " partitions to answer this query)");
        return table.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }
}
```

How to run: `java CassandraRepoLevel2.java`

`findByStatus` has to inspect all 1000 partitions to find the ones matching `"SHIPPED"`, regardless of how few or many actually match — unlike `findById`'s direct O(1) lookup, this cost scales with the *entire* table size, not the result size. In real Cassandra, this exact query either requires a secondary index (which itself has significant limitations and performance caveats for high-cardinality fields) or Cassandra outright refuses to run it without an explicit `ALLOW FILTERING` clause acknowledging the full-cluster scan.

### Level 3 — Advanced

Redesign the table so `status` becomes queryable efficiently, by including it in the primary key structure — the correct fix, matching Cassandra's "model around your queries" discipline, rather than reaching for a secondary index or `ALLOW FILTERING`.

```java
import java.util.*;
import java.util.stream.*;

public class CassandraRepoLevel3 {
    public static void main(String[] args) {
        OrderByStatusRepository repo = new OrderByStatusRepository();
        for (int i = 1; i <= 1000; i++) repo.save(new Order(i % 3 == 0 ? "SHIPPED" : "PENDING", "order-" + i, i * 1.0));

        List<Order> shipped = repo.findByStatus("SHIPPED");
        System.out.println("findByStatus(\"SHIPPED\"): found " + shipped.size() + " orders");
    }
}

class Order { String status; String orderId; double total; Order(String status, String orderId, double total) { this.status = status; this.orderId = orderId; this.total = total; } }

// PRIMARY KEY ((status), order_id) -- status is now the PARTITION KEY, order_id is a CLUSTERING column.
// This models a table DESIGNED for "give me all orders with this status" as its primary access pattern.
class OrderByStatusRepository {
    private final Map<String, List<Order>> table = new HashMap<>(); // keyed by status -- the NEW partition key

    void save(Order order) {
        table.computeIfAbsent(order.status, k -> new ArrayList<>()).add(order);
    }

    // NOW efficient: status IS the partition key, so this resolves directly to one partition, just like findById did.
    List<Order> findByStatus(String status) {
        System.out.println("  (direct partition access for status=" + status + " -- no scan needed)");
        return table.getOrDefault(status, List.of());
    }
}
```

How to run: `java CassandraRepoLevel3.java`

By redesigning the table's primary key so `status` is the **partition key** (with `order_id` as a clustering column organizing rows *within* each status partition), `findByStatus` becomes just as efficient as `findById` was in Level 1 — a direct lookup, not a scan. This is the actual solution Cassandra expects: don't add a query capability after the fact via a secondary index bolted onto a mismatched key design; model the table's key structure around the query from the start, even if it means maintaining a second, differently-keyed table for a different access pattern on the same logical data.

## 6. Walkthrough

Execution starts in `main` for Level 3. A thousand orders are saved via `repo.save(...)`, each landing in `table` keyed by `status` — since only two distinct status values (`"PENDING"`, `"SHIPPED"`) are used, `table` ends up with exactly two entries, each holding a list of several hundred orders.

`repo.findByStatus("SHIPPED")` calls `table.getOrDefault("SHIPPED", List.of())` — a direct, single-key map lookup that returns the entire pre-grouped list of shipped orders immediately, without touching the `"PENDING"` partition at all. This is structurally identical to Level 1's `findById` lookup: both are O(1) accesses into a map keyed by exactly the field being queried.

```
  (direct partition access for status=SHIPPED -- no scan needed)
findByStatus("SHIPPED"): found 333 orders
```

In real Cassandra, this table would be declared as `CREATE TABLE orders_by_status (status text, order_id text, total double, PRIMARY KEY ((status), order_id))` — `status` in the outer parentheses marks it as the partition key, and Cassandra physically groups every row sharing a `status` value together on the same replica set, making `SELECT * FROM orders_by_status WHERE status = 'SHIPPED'` a direct, efficient partition read. This often means maintaining a **second table**, `orders_by_id`, keyed by `order_id` for the `findById` access pattern — intentional denormalization across multiple tables, one per query pattern, is standard Cassandra practice, not a workaround.

## 7. Gotchas & takeaways

> Gotcha: unlike a relational database, adding an index to make an existing table "queryable by another field" is not the primary Cassandra solution — secondary indexes exist but perform poorly at scale for high-cardinality fields and don't help with cross-partition consistency the way a redesigned partition key does. The default, expected fix for "I need to query by a new field efficiently" is usually a **second table** (or materialized view) keyed appropriately for that query.

> Gotcha: `CassandraRepository` will happily let you *declare* a derived method like `findByStatus` on a table where `status` isn't part of the key — Spring Data doesn't prevent this at compile time. It only surfaces as a problem at runtime, either as Cassandra rejecting the query outright or requiring an explicit (and generally discouraged) `@AllowFiltering` annotation acknowledging the full-cluster scan.

- `CassandraRepository`/`ReactiveCassandraRepository` provide the same generated CRUD-plus-derived-methods convenience as every other Spring Data module, layered on `CassandraTemplate`/`ReactiveCassandraTemplate`.
- Unlike other modules, whether a derived query method is even efficient (or possible without extra configuration) depends entirely on whether the queried field is part of the table's primary key.
- The idiomatic Cassandra fix for "I need to query by a different field efficiently" is usually a separate table keyed appropriately for that access pattern, not a secondary index or `ALLOW FILTERING`.
- Designing a table's partition key and clustering columns around the exact queries the application needs is the central discipline of effective Cassandra data modeling.
