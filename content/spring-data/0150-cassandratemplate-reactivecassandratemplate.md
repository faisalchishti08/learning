---
card: spring-data
gi: 150
slug: cassandratemplate-reactivecassandratemplate
title: "CassandraTemplate / ReactiveCassandraTemplate"
---

## 1. What it is

`CassandraTemplate` (blocking) and `ReactiveCassandraTemplate` (returning `Mono`/`Flux`) are Spring Data Cassandra's low-level entry points for Apache Cassandra — a distributed, wide-column database built for massive write throughput and horizontal scale across many nodes, with a fundamentally different consistency and query model than anything covered so far in this course.

```java
@Autowired CassandraTemplate cassandraTemplate;

Order order = cassandraTemplate.selectOneById(orderId, Order.class);
cassandraTemplate.insert(new Order(orderId, "PENDING"));
```

## 2. Why & when

This card opens the final Spring Data section in this course: Spring Data for Apache Cassandra. Cassandra is neither relational nor document-oriented — it's a distributed wide-column store where data is deliberately partitioned and replicated across many nodes with no single point of failure, designed for write-heavy workloads at massive scale (think: sensor readings, event logs, time-series data) where a single powerful server, or even a MongoDB replica set, would eventually become a bottleneck. `CassandraTemplate`/`ReactiveCassandraTemplate` play the same architectural role every other section's template played: the low-level API every generated repository builds on.

Reach for `CassandraTemplate`/`ReactiveCassandraTemplate` directly when:

- Writing a custom repository implementation needing operations beyond a generated `CassandraRepository` method.
- Choosing between blocking and reactive access based on the rest of the application stack — mirroring the same blocking/reactive split from MongoDB and Redis.
- You need direct control over a Cassandra-specific concern (a consistency level for one particular operation, a lightweight transaction) that a generated repository method can't express.

## 3. Core concept

```
 interface OrderRepository extends CassandraRepository<Order, UUID> { }
   -- generated implementation is a thin wrapper delegating to:

 CassandraTemplate.selectOneById(id, Order.class)             -- blocking, direct value returned
 CassandraTemplate.insert(order)                                -- blocking, writes the row

 ReactiveCassandraTemplate.selectOneById(id, Order.class)       -- Mono<Order>
 ReactiveCassandraTemplate.insert(order)                        -- Mono<Order>

 orderRepository.findById(id)  ==  cassandraTemplate.selectOneById(id, Order.class)
```

The relationship mirrors exactly what `MongoTemplate`/`ReactiveMongoTemplate` were to their repositories, and what `JdbcAggregateTemplate`/`R2dbcEntityTemplate` were to theirs — a lower-level, storage-specific API that generated repositories build on.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generated CassandraRepository and a custom implementation both delegate to the same underlying CassandraTemplate">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.findById(id)</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: cassandraTemplate...</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CassandraTemplate / ReactiveCassandraTemplate</text>

  <line x1="150" y1="65" x2="290" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the generated repository and a hand-written custom fragment ultimately delegate to the same underlying template.

## 5. Runnable example

The scenario: storing and reading order events, evolving from a blocking `CassandraTemplate`-style baseline, to its reactive `ReactiveCassandraTemplate` equivalent, to a custom repository fragment combining both concepts for an operation no generated method expresses.

### Level 1 — Basic

Model the blocking `CassandraTemplate` style, against an in-memory stand-in for a Cassandra table.

```java
import java.util.*;
import java.util.stream.*;

public class CassandraTemplateLevel1 {
    public static void main(String[] args) {
        CassandraTemplate cassandraTemplate = new CassandraTemplate();
        cassandraTemplate.insert(new Order("1", "PENDING"));
        cassandraTemplate.insert(new Order("2", "SHIPPED"));

        Order found = cassandraTemplate.selectOneById("1");
        System.out.println("Found by id: status=" + found.status);

        List<Order> shipped = cassandraTemplate.select("SHIPPED");
        System.out.println("Found by status: " + shipped.size() + " order(s)");
    }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

// Stands in for org.springframework.data.cassandra.core.CassandraTemplate.
class CassandraTemplate {
    private final Map<String, Order> table = new HashMap<>();

    Order selectOneById(String id) { return table.get(id); } // blocking, direct return
    void insert(Order order) { table.put(order.id, order); }
    List<Order> select(String statusFilter) {
        return table.values().stream().filter(o -> o.status.equals(statusFilter)).collect(Collectors.toList());
    }
}
```

How to run: `java CassandraTemplateLevel1.java`

`selectOneById`/`select` return values directly, exactly matching the blocking style already established for `MongoTemplate` and JDBC's templates in earlier sections — this is the pattern to reach for when the rest of the application stack is also blocking.

### Level 2 — Intermediate

Model the reactive `ReactiveCassandraTemplate` equivalent, using `CompletableFuture` to stand in for `Mono`, matching the convention used consistently throughout this course's reactive cards.

```java
import java.util.*;
import java.util.concurrent.*;

public class CassandraTemplateLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveCassandraTemplate template = new ReactiveCassandraTemplate();
        template.insert(new Order("1", "PENDING")).get(); // .get() used only for demo sequencing

        CompletableFuture<Order> future = template.selectOneById("1"); // returns IMMEDIATELY
        System.out.println("Call returned; not necessarily complete yet.");
        Order found = future.get(); // wait here ONLY for demo purposes
        System.out.println("Eventually found: status=" + found.status);
    }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

// Stands in for org.springframework.data.cassandra.core.ReactiveCassandraTemplate.
class ReactiveCassandraTemplate {
    private final Map<String, Order> table = new HashMap<>();

    CompletableFuture<Order> selectOneById(String id) { // stands in for Mono<Order>
        return CompletableFuture.supplyAsync(() -> table.get(id));
    }
    CompletableFuture<Order> insert(Order order) {
        return CompletableFuture.supplyAsync(() -> { table.put(order.id, order); return order; });
    }
}
```

How to run: `java CassandraTemplateLevel2.java`

`selectOneById` returns its `CompletableFuture` (standing in for `Mono<Order>`) immediately — mirroring exactly the non-blocking behavior established for `ReactiveMongoTemplate`, `ReactiveRedisTemplate`, and `ReactiveElasticsearchOperations` earlier in this course, just applied to Cassandra now.

### Level 3 — Advanced

Build a custom repository fragment using `CassandraTemplate` directly for an operation no generated `CassandraRepository` method expresses cleanly: appending an event to a per-order event log stored as a wide row, the kind of write pattern Cassandra is specifically optimized for.

```java
import java.util.*;

public class CassandraTemplateLevel3 {
    public static void main(String[] args) {
        CassandraTemplate cassandraTemplate = new CassandraTemplate();
        OrderEventRepositoryCustom repo = new OrderEventRepositoryImpl(cassandraTemplate);

        repo.appendEvent("1", "CREATED");
        repo.appendEvent("1", "PACKED");
        repo.appendEvent("1", "SHIPPED");

        List<OrderEvent> events = cassandraTemplate.selectEventsForOrder("1");
        System.out.println("Event log for order 1 (" + events.size() + " events):");
        for (OrderEvent e : events) System.out.println("  " + e.eventType);
    }
}

class OrderEvent { String orderId; long timestamp; String eventType; OrderEvent(String orderId, long timestamp, String eventType) { this.orderId = orderId; this.timestamp = timestamp; this.eventType = eventType; } }

class CassandraTemplate {
    Map<String, List<OrderEvent>> eventsByOrder = new HashMap<>(); // one "wide row" per orderId
    void insertEvent(OrderEvent event) {
        eventsByOrder.computeIfAbsent(event.orderId, k -> new ArrayList<>()).add(event);
    }
    List<OrderEvent> selectEventsForOrder(String orderId) {
        return eventsByOrder.getOrDefault(orderId, List.of());
    }
}

// interface OrderEventRepositoryCustom { void appendEvent(String orderId, String eventType); }
interface OrderEventRepositoryCustom { void appendEvent(String orderId, String eventType); }

class OrderEventRepositoryImpl implements OrderEventRepositoryCustom {
    private final CassandraTemplate cassandraTemplate;
    OrderEventRepositoryImpl(CassandraTemplate cassandraTemplate) { this.cassandraTemplate = cassandraTemplate; }

    // No generated CassandraRepository method expresses "append to this order's wide-row event log" --
    // this needs direct template access, matching Cassandra's write-optimized wide-row modeling.
    public void appendEvent(String orderId, String eventType) {
        cassandraTemplate.insertEvent(new OrderEvent(orderId, System.nanoTime(), eventType));
    }
}
```

How to run: `java CassandraTemplateLevel3.java`

`appendEvent` is a method no generated `CassandraRepository<OrderEvent, ...>` interface exposes on its own — it's a custom fragment built directly on `CassandraTemplate`, modeling Cassandra's characteristic "wide row" pattern: all events for one order live under a single partition key (`orderId`), letting Cassandra write and read an order's entire event history extremely efficiently, since it's all co-located on the same node(s) that own that partition.

## 6. Walkthrough

Execution starts in `main` for Level 3. `repo.appendEvent("1", "CREATED")`, `appendEvent("1", "PACKED")`, and `appendEvent("1", "SHIPPED")` each call `cassandraTemplate.insertEvent(...)`, which appends a new `OrderEvent` onto the list stored under key `"1"` in `eventsByOrder` — all three events accumulate under the same partition, in the order they were written.

`cassandraTemplate.selectEventsForOrder("1")` retrieves the entire list for that partition in one call, and the final loop prints each event's type in insertion order.

```
Event log for order 1 (3 events):
  CREATED
  PACKED
  SHIPPED
```

In a real Cassandra deployment, this table would be modeled with `orderId` as the **partition key** and `timestamp` as a **clustering column** (the next section's cards cover this modeling in depth) — Cassandra physically stores all rows sharing a partition key together, sorted by the clustering column, which is exactly why appending and reading an order's full event history is a single, efficient operation regardless of how large the overall dataset across all orders grows.

## 7. Gotchas & takeaways

> Gotcha: unlike JPA or MongoDB, Cassandra has no concept of ad-hoc joins or arbitrary secondary-field queries by default — data modeling in Cassandra starts from "what queries will I run" and shapes the table structure (partition key, clustering columns) around that access pattern, rather than modeling the data's natural relationships first and querying flexibly later. This is a genuinely different design discipline from every other section in this course.

> Gotcha: `CassandraTemplate`/`ReactiveCassandraTemplate` require a properly configured `CqlSession` (the next card) pointing at a Cassandra cluster — Cassandra's wire protocol and cluster topology awareness are meaningfully different from a single-server connection, and misconfigured contact points or replication settings surface as connection failures that can be confusing without understanding Cassandra's cluster model first.

- `CassandraTemplate`/`ReactiveCassandraTemplate` are the low-level entry points every generated `CassandraRepository`/`ReactiveCassandraRepository` method delegates to, mirroring the template pattern from every other Spring Data module in this course.
- The blocking/reactive split matches the same pattern established for MongoDB, Redis, and Elasticsearch earlier — same conceptual operations, different execution model.
- Cassandra's wide-row modeling (many related rows co-located under one partition key) is fundamentally different from relational or document modeling, and custom repository fragments using the template directly are how operations exploiting that structure get expressed.
- Cassandra tables are designed around specific query patterns from the start — this "query-first" modeling discipline is a genuinely different mindset from the sections earlier in this course.
