---
card: spring-data
gi: 154
slug: composite-partition-clustering-keys
title: "Composite & partition/clustering keys"
---

## 1. What it is

A Cassandra table's primary key can have two distinct parts, playing entirely different roles: the **partition key** (one or more columns) determines *which node(s)* physically store a row, while **clustering columns** (zero or more) determine the *sort order of rows within* a partition. Together they form a composite key, but they are not interchangeable — this is the deepest, most consequential concept in Cassandra data modeling, building directly on the previous card's `@PrimaryKeyClass` mechanics.

```java
// PRIMARY KEY ((customer_id), order_date, order_id)
//              ^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^
//              partition key    clustering columns (sorted, in this order)
@PrimaryKeyClass
class OrderKey {
    @PrimaryKeyColumn(type = PrimaryKeyType.PARTITIONED) String customerId;
    @PrimaryKeyColumn(type = PrimaryKeyType.CLUSTERED, ordinal = 0) Instant orderDate;
    @PrimaryKeyColumn(type = PrimaryKeyType.CLUSTERED, ordinal = 1) String orderId;
}
```

## 2. Why & when

The partition key answers "where does this data physically live" — Cassandra hashes it to determine which node(s) in the cluster own the data, and *all* rows sharing the same partition key value live together, physically co-located. Clustering columns answer a completely different question: "in what order do I want to read the rows *within* one partition." Getting this split right is what makes Cassandra fast for the queries you actually run, and getting it wrong is the single most common cause of both poor performance and outright inability to run a needed query.

Reach for deliberate partition/clustering key design when:

- You know your dominant access pattern in advance (Cassandra's query-first modeling philosophy, established in earlier cards) — design the partition key to match "the one thing I'll always filter by," and clustering columns to match "the order I'll always want results in."
- You need range queries within a group — "all of this customer's orders from the last 30 days, most recent first" needs `customer_id` as the partition key and `order_date` (descending) as a clustering column.
- You're evaluating whether a partition key choice will create "hot partitions" — if one partition key value (say, a single extremely active customer) accumulates a disproportionate share of all data, that partition's node(s) bear disproportionate load, which is exactly the failure mode good partition key design avoids.

## 3. Core concept

```
 PRIMARY KEY ((customer_id), order_date, order_id)

 Partition key: customer_id
   -- ALL rows for one customer_id live on the SAME node(s), physically together
   -- Cassandra hashes customer_id to decide WHICH node(s)

 Clustering columns: order_date, order_id (in that order)
   -- WITHIN one customer's partition, rows are sorted by order_date, then by order_id as a tie-breaker
   -- this sort order is maintained ON DISK -- reading it back requires NO extra sorting step

 customer-A's partition (co-located, sorted by order_date):
   2026-01-01 | order-1
   2026-03-15 | order-5
   2026-06-02 | order-9
```

The partition key groups and locates data; the clustering columns order it — two different jobs, both encoded in one composite primary key.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rows sharing a partition key are co-located on one node and stored sorted by clustering column within that partition">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PRIMARY KEY ((customer_id), order_date, order_id)</text>

  <rect x="60" y="80" width="220" height="90" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="100" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">partition: customer-A</text>
  <text x="170" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2026-01-01 | order-1</text>
  <text x="170" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2026-03-15 | order-5</text>
  <text x="170" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2026-06-02 | order-9</text>

  <rect x="360" y="80" width="220" height="90" rx="8" fill="#79c0ff22" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="100" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">partition: customer-B</text>
  <text x="470" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2026-02-10 | order-3</text>

  <text x="320" y="185" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">each partition is co-located and internally sorted by clustering column(s)</text>
</svg>

Each customer's rows are grouped into one physically co-located partition, internally sorted by clustering column — two distinct structural roles within a single key.

## 5. Runnable example

The scenario: an orders-by-customer table, evolving from a basic partition-only key, to adding a clustering column for chronological ordering, to a multi-column clustering key with a tie-breaker — demonstrating exactly how each part of the composite key contributes.

### Level 1 — Basic

Model a partition-key-only table: rows grouped by customer, with no defined order within a partition.

```java
import java.util.*;

public class KeysLevel1 {
    public static void main(String[] args) {
        OrdersByCustomerTable table = new OrdersByCustomerTable();
        table.insert(new Order("customer-A", "order-5", "SHIPPED"));
        table.insert(new Order("customer-A", "order-1", "DELIVERED"));
        table.insert(new Order("customer-A", "order-9", "PENDING"));

        List<Order> customerAOrders = table.selectPartition("customer-A");
        System.out.println("customer-A's orders, in INSERTION order (no clustering defined):");
        for (Order o : customerAOrders) System.out.println("  " + o.orderId);
    }
}

class Order { String customerId; String orderId; String status; Order(String customerId, String orderId, String status) { this.customerId = customerId; this.orderId = orderId; this.status = status; } }

// PRIMARY KEY (customer_id, order_id) -- customer_id is the partition key; order_id, without CLUSTERED designation
// in a single-column key list, is ALSO part of the key but here we model the simplest "grouped, unordered" case.
class OrdersByCustomerTable {
    Map<String, List<Order>> partitions = new HashMap<>();
    void insert(Order order) { partitions.computeIfAbsent(order.customerId, k -> new ArrayList<>()).add(order); }
    List<Order> selectPartition(String customerId) { return partitions.getOrDefault(customerId, List.of()); }
}
```

How to run: `java KeysLevel1.java`

All three orders share the `customer-A` partition and are physically co-located, but without a clustering column, they come back in whatever order they were inserted — `order-5`, `order-1`, `order-9` — not in any meaningful business order. This is the gap clustering columns exist to close.

### Level 2 — Intermediate

Add `orderDate` as a clustering column, matching `PRIMARY KEY ((customer_id), order_date)` — rows within each partition are now maintained in chronological order automatically.

```java
import java.util.*;

public class KeysLevel2 {
    public static void main(String[] args) {
        OrdersByCustomerTable table = new OrdersByCustomerTable();
        table.insert(new Order("customer-A", "2026-06-02", "order-9", "PENDING"));
        table.insert(new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"));
        table.insert(new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"));

        List<Order> customerAOrders = table.selectPartition("customer-A");
        System.out.println("customer-A's orders, in CLUSTERING order (by order_date):");
        for (Order o : customerAOrders) System.out.println("  " + o.orderDate + ": " + o.orderId);
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }

// PRIMARY KEY ((customer_id), order_date) -- customer_id partitions, order_date CLUSTERS (sorts) within each partition.
class OrdersByCustomerTable {
    Map<String, TreeMap<String, Order>> partitions = new HashMap<>();
    void insert(Order order) {
        partitions.computeIfAbsent(order.customerId, k -> new TreeMap<>()).put(order.orderDate, order);
    }
    List<Order> selectPartition(String customerId) {
        return new ArrayList<>(partitions.getOrDefault(customerId, new TreeMap<>()).values());
    }
}
```

How to run: `java KeysLevel2.java`

Even though the three orders were inserted with dates out of order (`2026-06-02`, then `2026-01-01`, then `2026-03-15`), `partitions.get("customer-A")` is a `TreeMap` keyed by `orderDate`, so `selectPartition` returns them chronologically — exactly what `order_date` as a clustering column guarantees in real Cassandra, maintained on disk, with no runtime sort needed.

### Level 3 — Advanced

Add `orderId` as a second clustering column — a tie-breaker for rows sharing the same `orderDate` — matching `PRIMARY KEY ((customer_id), order_date, order_id)`, the intro snippet's full composite key.

```java
import java.util.*;

public class KeysLevel3 {
    public static void main(String[] args) {
        OrdersByCustomerTable table = new OrdersByCustomerTable();
        // TWO orders placed on the SAME date -- orderId breaks the tie.
        table.insert(new Order("customer-A", "2026-03-15", "order-9", "PENDING"));
        table.insert(new Order("customer-A", "2026-03-15", "order-5", "SHIPPED"));
        table.insert(new Order("customer-A", "2026-01-01", "order-1", "DELIVERED"));

        List<Order> customerAOrders = table.selectPartition("customer-A");
        System.out.println("customer-A's orders, clustered by (order_date, order_id):");
        for (Order o : customerAOrders) System.out.println("  " + o.orderDate + " / " + o.orderId);
    }
}

class Order { String customerId; String orderDate; String orderId; String status; Order(String customerId, String orderDate, String orderId, String status) { this.customerId = customerId; this.orderDate = orderDate; this.orderId = orderId; this.status = status; } }

class OrderClusterKey implements Comparable<OrderClusterKey> {
    String orderDate; String orderId;
    OrderClusterKey(String orderDate, String orderId) { this.orderDate = orderDate; this.orderId = orderId; }
    // Sort by orderDate FIRST; orderId is only the TIE-BREAKER when orderDate values are equal.
    public int compareTo(OrderClusterKey other) {
        int dateCompare = this.orderDate.compareTo(other.orderDate);
        return dateCompare != 0 ? dateCompare : this.orderId.compareTo(other.orderId);
    }
}

// PRIMARY KEY ((customer_id), order_date, order_id) -- TWO clustering columns, applied in order.
class OrdersByCustomerTable {
    Map<String, TreeMap<OrderClusterKey, Order>> partitions = new HashMap<>();
    void insert(Order order) {
        partitions.computeIfAbsent(order.customerId, k -> new TreeMap<>())
            .put(new OrderClusterKey(order.orderDate, order.orderId), order);
    }
    List<Order> selectPartition(String customerId) {
        return new ArrayList<>(partitions.getOrDefault(customerId, new TreeMap<>()).values());
    }
}
```

How to run: `java KeysLevel3.java`

`OrderClusterKey.compareTo` sorts by `orderDate` first, falling back to `orderId` only when two rows share the exact same date — mirroring `PRIMARY KEY ((customer_id), order_date, order_id)`'s two-clustering-column behavior. The two `2026-03-15` orders (`order-9` inserted first, `order-5` second) come back sorted as `order-5` before `order-9` by their id, since their dates tie and `orderId` breaks that tie alphabetically — exactly matching how Cassandra applies clustering columns left to right, each one only resolving ties left unresolved by the columns before it.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are inserted for `customer-A`: two sharing the date `2026-03-15` (`order-9` first, then `order-5`), and one on `2026-01-01` (`order-1`).

Each `insert` call constructs an `OrderClusterKey(orderDate, orderId)` and places the order into the `TreeMap` under that composite key. `TreeMap` uses `OrderClusterKey.compareTo` to maintain sort order internally as entries are added — so regardless of insertion order, the map's internal ordering is always kept consistent with `compareTo`'s logic.

`table.selectPartition("customer-A")` returns `values()` in the `TreeMap`'s sorted order. `compareTo` first compares `orderDate` strings: `"2026-01-01"` sorts before `"2026-03-15"`, so `order-1` comes first. For the two entries sharing `"2026-03-15"`, `dateCompare` is `0`, so the comparison falls through to `this.orderId.compareTo(other.orderId)` — `"order-5"` sorts before `"order-9"` alphabetically, so `order-5` is placed ahead of `order-9` in the final order, even though `order-9` was inserted first.

```
customer-A's orders, clustered by (order_date, order_id):
  2026-01-01 / order-1
  2026-03-15 / order-5
  2026-03-15 / order-9
```

In real Cassandra, `PRIMARY KEY ((customer_id), order_date, order_id)` produces exactly this ordering behavior, maintained physically on disk within each partition — no application-side sorting is ever needed to read a customer's orders in this order, because Cassandra's storage engine keeps rows within a partition sorted by the full clustering key at all times, applying each clustering column left to right as a tie-breaker for the ones before it, exactly as `OrderClusterKey.compareTo` models here.

## 7. Gotchas & takeaways

> Gotcha: the order clustering columns are declared in matters — `PRIMARY KEY ((customer_id), order_date, order_id)` and `PRIMARY KEY ((customer_id), order_id, order_date)` produce genuinely different physical sort orders (and different efficient query capabilities), even though they use the exact same set of columns. Declare clustering columns in the order that matches your actual "sort by this, then that" requirement.

> Gotcha: a partition key that's too coarse (too few distinct values relative to data volume — imagine partitioning by `status`, which only has a handful of possible values across millions of orders) creates a small number of enormous partitions, each overloading whichever node(s) own it. A partition key that's too fine (unique per row, like the row's own id) prevents any meaningful grouping or range query within a partition at all. Good partition key choice sits between these extremes, driven by the actual query pattern.

- The partition key determines *where* data physically lives (which node(s) own it); clustering columns determine the *sort order* of rows *within* a partition — two structurally different jobs combined into one composite key.
- Cassandra maintains clustering order automatically at the storage layer — reading a partition back never requires an application-side or even query-time sort.
- The declared order of multiple clustering columns matters: each one is a tie-breaker for the columns declared before it, and reordering them changes both the physical sort order and which queries can be answered efficiently.
- Partition key design directly determines data distribution across the cluster — choosing a key that's too coarse creates overloaded "hot" partitions; choosing one that's too fine prevents useful grouping.
