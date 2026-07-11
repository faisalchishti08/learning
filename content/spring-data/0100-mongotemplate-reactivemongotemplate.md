---
card: spring-data
gi: 100
slug: mongotemplate-reactivemongotemplate
title: "MongoTemplate / ReactiveMongoTemplate"
---

## 1. What it is

`MongoTemplate` (blocking) and `ReactiveMongoTemplate` (returning `Mono`/`Flux`) are Spring Data MongoDB's lower-level template classes — the MongoDB-specific counterparts to `JdbcAggregateTemplate`/`R2dbcEntityTemplate` from the earlier relational cards — offering direct, document-oriented `find`/`insert`/`update`/`remove` operations against MongoDB collections, independent of any repository interface.

```java
@Autowired MongoTemplate mongoTemplate;

Order order = mongoTemplate.findById(1L, Order.class);
List<Order> shipped = mongoTemplate.find(
    Query.query(Criteria.where("status").is("SHIPPED")), Order.class);
```

## 2. Why & when

This card starts a new section: Spring Data MongoDB, a document-database module built on entirely different storage semantics than the relational (JPA/JDBC/R2DBC) modules covered so far — MongoDB stores JSON-like BSON documents in collections, with no fixed schema, no joins, and no SQL. `MongoTemplate`/`ReactiveMongoTemplate` are the entry points, exactly parallel in role to the relational templates: every generated `MongoRepository` method (the next card) delegates to one of these underneath.

Reach for `MongoTemplate`/`ReactiveMongoTemplate` directly specifically when:

- Writing a custom repository implementation (the same `<Repository>Impl` pattern used throughout this section) that needs document-level operations beyond what a generated repository interface method exposes.
- You want to build a query dynamically using MongoDB's `Query`/`Criteria` objects (covered in a later card) rather than a fixed derived method name or `@Query` JSON string.
- You need to choose between blocking (`MongoTemplate`) and reactive (`ReactiveMongoTemplate`) based on whether the rest of your application stack is blocking or reactive — both offer the same conceptual operations, mirroring the JDBC/R2DBC split from the relational modules.

## 3. Core concept

```
 interface OrderRepository extends MongoRepository<Order, Long> { }
   -- generated implementation is a thin wrapper delegating to:

 MongoTemplate.findById(1L, Order.class)                          -- blocking, direct value returned
 MongoTemplate.find(Query.query(Criteria.where("status").is(s)), Order.class)  -- blocking, List<Order>

 ReactiveMongoTemplate.findById(1L, Order.class)                    -- Mono<Order>
 ReactiveMongoTemplate.find(query, Order.class)                     -- Flux<Order>

 orderRepository.findById(1L)  ==  mongoTemplate.findById(1L, Order.class)  (same operation, different entry point)
```

The relationship mirrors exactly what `JdbcAggregateTemplate`/`R2dbcEntityTemplate` are to their respective repository interfaces — a lower-level, document-oriented API that generated repositories build on.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A generated MongoRepository and a custom implementation both delegate to the same underlying MongoTemplate">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.findById(1L)</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: mongoTemplate.find(...)</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">MongoTemplate / ReactiveMongoTemplate</text>

  <line x1="150" y1="65" x2="290" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mt)"/>
  <line x1="490" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mt)"/>
  <defs><marker id="mt" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the generated repository and a hand-written custom fragment ultimately delegate to the same underlying template.

## 5. Runnable example

The scenario: storing and querying orders as documents, evolving from a blocking `MongoTemplate`-style baseline, to its reactive `ReactiveMongoTemplate` equivalent, to a custom repository fragment combining both concepts for an operation no generated method expresses.

### Level 1 — Basic

Model the blocking `MongoTemplate` style directly, against an in-memory "collection" standing in for a real MongoDB collection.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for org.springframework.data.mongodb.core.MongoTemplate.
class MongoTemplate {
    private final Map<Long, Order> collection = new HashMap<>();

    Order findById(long id) {
        return collection.get(id); // blocking, direct return
    }
    List<Order> find(String statusFilter) { // simplified Query/Criteria for this level
        return collection.values().stream().filter(o -> o.status.equals(statusFilter)).collect(Collectors.toList());
    }
    Order insert(Order order) { collection.put(order.id, order); return order; }
}

public class MongoTemplateLevel1 {
    public static void main(String[] args) {
        MongoTemplate mongoTemplate = new MongoTemplate();
        mongoTemplate.insert(new Order(1, "SHIPPED", 50));
        mongoTemplate.insert(new Order(2, "PENDING", 150));

        Order found = mongoTemplate.findById(1L); // blocking -- value returned directly
        System.out.println("Found by id: status=" + found.status);

        List<Order> shipped = mongoTemplate.find("SHIPPED");
        System.out.println("Found by status: " + shipped.size() + " order(s)");
    }
}
```

How to run: `java MongoTemplateLevel1.java`

`findById`/`find` return values directly, exactly like `JdbcAggregateTemplate` from the earlier relational cards — this is the blocking `MongoTemplate` style, appropriate when the rest of the application stack is also blocking.

### Level 2 — Intermediate

Model the reactive `ReactiveMongoTemplate` equivalent, using `CompletableFuture` to stand in for `Mono`/`Flux` (mirroring the R2DBC section's convention), returning handles immediately instead of direct values.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for org.springframework.data.mongodb.core.ReactiveMongoTemplate.
class ReactiveMongoTemplate {
    private final Map<Long, Order> collection = new HashMap<>();

    CompletableFuture<Order> findById(long id) { // stands in for Mono<Order>
        return CompletableFuture.supplyAsync(() -> collection.get(id));
    }
    CompletableFuture<List<Order>> find(String statusFilter) { // stands in for Flux<Order>
        return CompletableFuture.supplyAsync(() ->
            collection.values().stream().filter(o -> o.status.equals(statusFilter)).collect(Collectors.toList()));
    }
    CompletableFuture<Order> insert(Order order) {
        return CompletableFuture.supplyAsync(() -> { collection.put(order.id, order); return order; });
    }
}

public class MongoTemplateLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveMongoTemplate template = new ReactiveMongoTemplate();
        template.insert(new Order(1, "SHIPPED", 50)).get(); // .get() used only for demo sequencing
        template.insert(new Order(2, "PENDING", 150)).get();

        CompletableFuture<Order> future = template.findById(1L); // returns IMMEDIATELY
        System.out.println("Call returned; not necessarily complete yet.");
        Order found = future.get(); // wait here ONLY for demo purposes
        System.out.println("Eventually found: status=" + found.status);
    }
}
```

How to run: `java MongoTemplateLevel2.java`

`findById` returns its `CompletableFuture` (standing in for `Mono<Order>`) immediately — mirroring exactly the same non-blocking behavior the R2DBC section's `ReactiveCrudRepository` card demonstrated for relational data, just applied to document storage instead.

### Level 3 — Advanced

Build a custom repository fragment using `MongoTemplate` directly for an operation no generated `MongoRepository` method expresses: an atomic "increment a counter field" update, matching how MongoDB's native update operators (like `$inc`) are typically accessed through the template layer.

```java
import java.util.*;

class Order { long id; String status; int viewCount; Order(long id, String status, int viewCount) { this.id = id; this.status = status; this.viewCount = viewCount; } }

class MongoTemplate {
    Map<Long, Order> collection = new HashMap<>();
    Order findById(long id) { return collection.get(id); }
}

// interface OrderRepositoryCustom { void incrementViewCount(long orderId); }
interface OrderRepositoryCustom { void incrementViewCount(long orderId); }

// class OrderRepositoryImpl implements OrderRepositoryCustom { @Autowired MongoTemplate mongoTemplate; ... }
class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final MongoTemplate mongoTemplate;
    OrderRepositoryImpl(MongoTemplate mongoTemplate) { this.mongoTemplate = mongoTemplate; }

    // No generated MongoRepository method expresses an ATOMIC field increment --
    // this needs direct template access using MongoDB's native $inc update operator.
    public void incrementViewCount(long orderId) {
        Order order = mongoTemplate.findById(orderId);
        // mongoTemplate.updateFirst(Query.query(Criteria.where("id").is(orderId)),
        //                           new Update().inc("viewCount", 1), Order.class);
        System.out.println("  db.orders.updateOne({id: " + orderId + "}, {$inc: {viewCount: 1}})");
        order.viewCount += 1; // simulates the atomic $inc happening server-side
    }
}

class OrderRepository implements OrderRepositoryCustom {
    private final MongoTemplate mongoTemplate;
    private final OrderRepositoryCustom custom;
    OrderRepository(MongoTemplate mongoTemplate) { this.mongoTemplate = mongoTemplate; this.custom = new OrderRepositoryImpl(mongoTemplate); }
    Order findById(long id) { return mongoTemplate.findById(id); }
    public void incrementViewCount(long orderId) { custom.incrementViewCount(orderId); }
}

public class MongoTemplateLevel3 {
    public static void main(String[] args) {
        MongoTemplate mongoTemplate = new MongoTemplate();
        mongoTemplate.collection.put(1L, new Order(1, "SHIPPED", 0));
        OrderRepository repo = new OrderRepository(mongoTemplate);

        repo.incrementViewCount(1L);
        repo.incrementViewCount(1L);
        repo.incrementViewCount(1L);

        System.out.println("Final view count: " + repo.findById(1L).viewCount);
    }
}
```

How to run: `java MongoTemplateLevel3.java`

`incrementViewCount` is a method no generated `MongoRepository<Order, Long>` interface exposes on its own — it's a custom fragment built directly on `MongoTemplate`, simulating MongoDB's native `$inc` update operator (which atomically increments a field server-side, avoiding a read-modify-write race under concurrency). After three calls, `viewCount` correctly reaches `3`.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `mongoTemplate.collection` is seeded with one order (`id=1, viewCount=0`), and `repo` wraps both the template and a custom `OrderRepositoryImpl` fragment built on it.

`repo.incrementViewCount(1L)` is called three times in a row. Each call delegates to `custom.incrementViewCount(orderId)`, which calls `mongoTemplate.findById(orderId)` to fetch the current order, prints the simulated `$inc` update command, and then increments `order.viewCount` by `1` directly on the fetched object (standing in for the atomic server-side increment a real `Update().inc("viewCount", 1)` would perform).

After the first call, `viewCount` becomes `1`; after the second, `2`; after the third, `3`. Each call operates on the same underlying `Order` object stored in `mongoTemplate.collection`, so the increments accumulate correctly across all three calls.

`repo.findById(1L).viewCount` is checked at the end and confirmed to be `3`, matching three successful increments.

```
incrementViewCount(1L) call #1: viewCount 0 -> 1
incrementViewCount(1L) call #2: viewCount 1 -> 2
incrementViewCount(1L) call #3: viewCount 2 -> 3
final viewCount: 3
```

In a real Spring Data MongoDB application, `OrderRepositoryImpl.incrementViewCount` would call `mongoTemplate.updateFirst(Query.query(Criteria.where("id").is(orderId)), new Update().inc("viewCount", 1), Order.class)` — this generates a native MongoDB `updateOne` command using the `$inc` operator, which increments the field *atomically on the database server itself*, without ever fetching the document into application memory first. This avoids a subtle race condition that a naive "fetch, increment in Java, save" sequence would have under concurrent requests — exactly the kind of document-native operation that requires dropping down to `MongoTemplate` rather than relying on a generated repository method.

## 7. Gotchas & takeaways

> Gotcha: fetching a document, mutating a field in application memory, and saving it back (as this example's simplified `incrementViewCount` does for illustration) is *not* atomic — under real concurrent load, two simultaneous "increment" calls could both read the same starting value and both write back the same incremented result, losing one of the increments; the real fix is MongoDB's native `$inc` operator applied server-side via `Update().inc(...)`, never a read-modify-write round trip through the application.

- `MongoTemplate`/`ReactiveMongoTemplate` are the document-oriented, lower-level template classes every generated `MongoRepository`/`ReactiveMongoRepository` method delegates to.
- The blocking/reactive split mirrors the relational modules' `JdbcAggregateTemplate`/`R2dbcEntityTemplate` split exactly — same conceptual operations, different execution model.
- Custom repository fragments inject the template directly for document-native operations (atomic field updates, aggregation pipelines) that generated repository methods can't express.
- Prefer MongoDB's native atomic update operators (`$inc`, `$push`, etc.) via `Update()` over a manual fetch-mutate-save sequence whenever the operation needs to be safe under concurrent access.
