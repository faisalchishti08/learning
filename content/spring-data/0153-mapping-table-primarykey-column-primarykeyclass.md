---
card: spring-data
gi: 153
slug: mapping-table-primarykey-column-primarykeyclass
title: "Mapping (@Table, @PrimaryKey, @Column, @PrimaryKeyClass)"
---

## 1. What it is

`@Table` maps a Java class to a Cassandra table; `@PrimaryKey` marks a simple single-field key; `@Column` controls individual field-to-column mapping (name, type); and `@PrimaryKeyClass` (with `@PrimaryKeyColumn`) is used when the primary key has multiple parts — a composite key of partition and clustering columns, which the next card covers in depth.

```java
@Table("orders")
class Order {
    @PrimaryKey String orderId;
    @Column("order_status") String status;
    double total;
}
```

## 2. Why & when

Every earlier card in this section assumed a table's structure already existed and matched a Java class's fields. `@Table`/`@PrimaryKey`/`@Column` are the annotations that actually establish that mapping — the Cassandra-specific counterparts to `@Document`/`@Id`/`@Field` from the MongoDB and Elasticsearch sections, adapted to Cassandra's table-and-column model, which is structurally closer to a relational table than a MongoDB document, but with the "model around your queries" key-design discipline from the previous two cards layered on top.

Reach for explicit mapping annotations when:

- Defining any entity that will be persisted to Cassandra — `@Table` and `@PrimaryKey` (or `@PrimaryKeyClass` for composite keys) are the minimum required mapping.
- A Java field's name doesn't match the desired Cassandra column name — Cassandra convention is typically `snake_case` column names, while Java convention is `camelCase` field names, and `@Column("order_status")` bridges that gap explicitly.
- Building an entity with a composite primary key — a partition key plus one or more clustering columns — which requires `@PrimaryKeyClass` to represent the combined key as its own type.

## 3. Core concept

```
 @Table("orders")
 class Order {
     @PrimaryKey String orderId;        -- maps to Cassandra's PRIMARY KEY column
     @Column("order_status") String status;  -- maps to a column named "order_status", NOT "status"
     double total;                       -- maps to a column named "total" (Java field name, unless overridden)
 }

 CREATE TABLE orders (
     orderid       text PRIMARY KEY,
     order_status  text,
     total         double
 );
```

Field names, table names, and column names can all be mapped independently — Java naming conventions and Cassandra naming conventions don't have to match, as long as the mapping is explicit where they diverge.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Java class's fields map to Cassandra table columns, with @Column overriding the default name mapping for one field">
  <rect x="20" y="20" width="220" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">class Order</text>
  <text x="130" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orderId</text>
  <text x="130" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">status</text>
  <text x="130" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total</text>

  <rect x="360" y="20" width="260" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">table orders</text>
  <text x="490" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orderid (PRIMARY KEY)</text>
  <text x="490" y="80" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">order_status (renamed!)</text>
  <text x="490" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total</text>

  <line x1="240" y1="60" x2="355" y2="60" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="240" y1="80" x2="355" y2="80" stroke="#3fb950" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="240" y1="98" x2="355" y2="98" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Most fields map by default naming convention; `@Column` explicitly overrides the mapping wherever the Java and Cassandra names diverge.

## 5. Runnable example

The scenario: mapping an `Order` entity to a Cassandra table, evolving from a basic `@Table`/`@PrimaryKey` mapping, to `@Column` renaming individual fields, to a composite-key entity using `@PrimaryKeyClass` — setting up the deeper composite-key card that follows.

### Level 1 — Basic

Model the basic `@Table`/`@PrimaryKey` mapping: a Java class mapped to a table with a simple single-column key.

```java
import java.util.*;

public class MappingLevel1 {
    public static void main(String[] args) {
        OrdersTable table = new OrdersTable();
        table.insert(new Order("1", "PENDING", 50.0));

        Order found = table.selectByPrimaryKey("1");
        System.out.println("Found via primary key: status=" + found.status + ", total=" + found.total);
    }
}

// Mirrors: @Table("orders") class Order { @PrimaryKey String orderId; String status; double total; }
class Order {
    String orderId; // the PRIMARY KEY field
    String status;
    double total;
    Order(String orderId, String status, double total) { this.orderId = orderId; this.status = status; this.total = total; }
}

// Stands in for the table structure @Table("orders") + @PrimaryKey together describe.
class OrdersTable {
    Map<String, Order> rowsByPrimaryKey = new HashMap<>();
    void insert(Order order) { rowsByPrimaryKey.put(order.orderId, order); } // keyed by the @PrimaryKey field
    Order selectByPrimaryKey(String orderId) { return rowsByPrimaryKey.get(orderId); }
}
```

How to run: `java MappingLevel1.java`

`OrdersTable.rowsByPrimaryKey` is keyed by `orderId`, mirroring `@PrimaryKey` marking that field as the table's `PRIMARY KEY` — every row is located by this single value, exactly like `CREATE TABLE orders (orderid text PRIMARY KEY, status text, total double)`.

### Level 2 — Intermediate

Add `@Column` renaming, matching a Java field name that diverges from its Cassandra column name.

```java
import java.util.*;

public class MappingLevel2 {
    public static void main(String[] args) {
        OrdersTable table = new OrdersTable();
        table.insert(new Order("1", "PENDING", 50.0));
        table.printRawSchema();
    }
}

// Mirrors: @Table("orders") class Order { @PrimaryKey String orderId; @Column("order_status") String status; double total; }
class Order {
    String orderId;
    String status; // Java field name; the CASSANDRA COLUMN is named "order_status", per @Column("order_status")
    double total;
    Order(String orderId, String status, double total) { this.orderId = orderId; this.status = status; this.total = total; }
}

class OrdersTable {
    // Simulates the actual Cassandra column names used internally -- "order_status", NOT "status".
    List<Map<String, Object>> rawRows = new ArrayList<>();

    void insert(Order order) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("orderid", order.orderId);
        row.put("order_status", order.status); // the @Column-mapped name, used in the ACTUAL storage layer
        row.put("total", order.total);
        rawRows.add(row);
    }

    void printRawSchema() {
        System.out.println("Actual Cassandra columns (note: 'order_status', not 'status'):");
        for (String col : rawRows.get(0).keySet()) System.out.println("  " + col);
    }
}
```

How to run: `java MappingLevel2.java`

`insert` writes the Java field `order.status` into a raw column explicitly named `"order_status"`, mirroring what `@Column("order_status")` instructs Spring Data Cassandra to do at the storage layer — the Java-side field name (`status`) and the actual Cassandra column name (`order_status`) are two independent names, bridged by the annotation.

### Level 3 — Advanced

Model a composite primary key with `@PrimaryKeyClass`: a dedicated key type combining a partition key and a clustering column, matching Cassandra's requirement that composite keys be represented as their own type.

```java
import java.util.*;

public class MappingLevel3 {
    public static void main(String[] args) {
        OrderEventsTable table = new OrderEventsTable();
        table.insert(new OrderEvent(new OrderEventKey("1", 3), "SHIPPED"));
        table.insert(new OrderEvent(new OrderEventKey("1", 1), "CREATED"));
        table.insert(new OrderEvent(new OrderEventKey("1", 2), "PACKED"));

        List<OrderEvent> events = table.selectPartition("1");
        System.out.println("Order 1's events, automatically in CLUSTERING order (by timestamp):");
        for (OrderEvent e : events) System.out.println("  t=" + e.key.timestamp + ": " + e.eventType);
    }
}

// Mirrors @PrimaryKeyClass -- a dedicated class representing a COMPOSITE key (partition + clustering column).
class OrderEventKey {
    String orderId;   // @PrimaryKeyColumn(type = PARTITIONED) -- determines which node owns this data
    long timestamp;    // @PrimaryKeyColumn(type = CLUSTERED)   -- determines ORDER within the partition
    OrderEventKey(String orderId, long timestamp) { this.orderId = orderId; this.timestamp = timestamp; }

    public boolean equals(Object o) {
        if (!(o instanceof OrderEventKey)) return false;
        OrderEventKey other = (OrderEventKey) o;
        return orderId.equals(other.orderId) && timestamp == other.timestamp;
    }
    public int hashCode() { return Objects.hash(orderId, timestamp); }
}

// Mirrors: @Table("order_events") class OrderEvent { @PrimaryKey OrderEventKey key; String eventType; }
class OrderEvent {
    OrderEventKey key;
    String eventType;
    OrderEvent(OrderEventKey key, String eventType) { this.key = key; this.eventType = eventType; }
}

class OrderEventsTable {
    // Grouped by PARTITION key (orderId); within each partition, rows are naturally ordered by CLUSTERING key (timestamp).
    Map<String, TreeMap<Long, OrderEvent>> partitions = new HashMap<>();

    void insert(OrderEvent event) {
        partitions.computeIfAbsent(event.key.orderId, k -> new TreeMap<>()).put(event.key.timestamp, event);
    }

    List<OrderEvent> selectPartition(String orderId) {
        return new ArrayList<>(partitions.getOrDefault(orderId, new TreeMap<>()).values());
    }
}
```

How to run: `java MappingLevel3.java`

`OrderEventKey` combines `orderId` (the partition key) and `timestamp` (a clustering column) into one dedicated key type, exactly what `@PrimaryKeyClass` requires — Cassandra's composite keys can't be expressed as a single scalar field. `TreeMap<Long, OrderEvent>` models how Cassandra automatically maintains clustering order *within* each partition: even though the three events were inserted out of timestamp order (`3`, then `1`, then `2`), reading back the partition returns them correctly ordered by `timestamp`.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `OrderEvent`s are inserted, all sharing `orderId = "1"` but with timestamps `3`, `1`, and `2`, inserted in that (out-of-order) sequence.

Each `table.insert(event)` call does `partitions.computeIfAbsent("1", k -> new TreeMap<>()).put(event.key.timestamp, event)` — all three events land in the *same* `TreeMap` (since they share the partition key `"1"`), but a `TreeMap` automatically keeps its entries sorted by key (`timestamp`) regardless of insertion order. So after all three inserts, the map internally holds timestamps in the order `1, 2, 3`, even though they were inserted as `3, 1, 2`.

`table.selectPartition("1")` retrieves `partitions.get("1")`'s values in the `TreeMap`'s natural (sorted) iteration order — `values()` on a `TreeMap` always iterates in key order, so the returned list is `[timestamp=1 (CREATED), timestamp=2 (PACKED), timestamp=3 (SHIPPED)]`, correctly reflecting the event history in chronological order despite the insertion order being scrambled.

```
Order 1's events, automatically in CLUSTERING order (by timestamp):
  t=1: CREATED
  t=2: PACKED
  t=3: SHIPPED
```

In real Cassandra, `CREATE TABLE order_events (order_id text, timestamp bigint, event_type text, PRIMARY KEY ((order_id), timestamp))` declares exactly this structure: `order_id` as the partition key (determining which node(s) store the data), `timestamp` as a clustering column (determining the physical, on-disk sort order *within* that partition). Cassandra maintains this sort order automatically and efficiently at the storage layer — reading a partition back always yields clustering-ordered results, with no explicit `ORDER BY` or in-memory sort required, which is exactly the behavior `TreeMap` models here.

## 7. Gotchas & takeaways

> Gotcha: a `@PrimaryKeyClass` must correctly implement `equals()`/`hashCode()` based on all its key fields (as `OrderEventKey` does here) — without this, Spring Data Cassandra can't correctly compare or look up entities by their composite key, leading to subtle bugs where `findById` with an apparently-correct key fails to find an existing row.

> Gotcha: which field becomes the partition key versus a clustering column is a deliberate design decision with major performance consequences, not an arbitrary ordering choice — the partition key determines physical data distribution across the cluster (get it wrong, and you create "hot partitions" that overload specific nodes), while clustering columns only determine sort order *within* an already-located partition.

- `@Table`, `@PrimaryKey`, and `@Column` map a Java entity to a Cassandra table, its primary key, and individual column names — bridging Java naming conventions and Cassandra's typical `snake_case` column naming explicitly where they diverge.
- `@PrimaryKeyClass` (with `@PrimaryKeyColumn`) represents a composite key — partition key plus one or more clustering columns — as its own dedicated type, required whenever the key has more than one part.
- Clustering columns determine the physical sort order of rows *within* a partition, maintained automatically by Cassandra with no explicit sort needed on read.
- A correctly implemented `equals()`/`hashCode()` on any `@PrimaryKeyClass` is required for Spring Data Cassandra to reliably look up entities by their composite key.
