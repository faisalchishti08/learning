---
card: spring-data
gi: 101
slug: mongorepository-reactivemongorepository
title: "MongoRepository / ReactiveMongoRepository"
---

## 1. What it is

`MongoRepository<T, ID>` (blocking) and `ReactiveMongoRepository<T, ID>` (returning `Mono`/`Flux`) are the generated repository interfaces for Spring Data MongoDB — extending the same `CrudRepository`/`ReactiveCrudRepository` base interfaces from Spring Data Commons, so `save`, `findById`, and the entire derived-query-method naming convention already familiar from every earlier card in this series carry over unchanged, now generating MongoDB queries instead of SQL.

```java
interface OrderRepository extends MongoRepository<Order, Long> {
    List<Order> findByStatus(String status); // derived, SAME convention as every other module
}
interface ReactiveOrderRepository extends ReactiveMongoRepository<Order, Long> {
    Flux<Order> findByStatus(String status); // derived, reactive-returning
}
```

## 2. Why & when

The `MongoTemplate` card showed the lower-level entry point; this card is the everyday, repository-interface programming model built on top of it — deliberately unsurprising, since it's the same `CrudRepository`/`ReactiveCrudRepository` shape (and the same query-derivation mechanism) used throughout the JPA, JDBC, and R2DBC sections, just targeting a document store instead of a relational database.

Reach for `MongoRepository`/`ReactiveMongoRepository` specifically when:

- You want the familiar, minimal-boilerplate repository interface pattern for MongoDB, exactly as you would for any other Spring Data module.
- Your application needs blocking (`MongoRepository`) or reactive (`ReactiveMongoRepository`) data access, mirroring the same blocking/reactive choice covered for relational data — MongoDB's native driver supports both models natively.
- You need `@Query` with MongoDB's JSON query syntax (covered in a later card) for conditions a derived method name can't express — this works on both repository flavors identically.

## 3. Core concept

```
 CrudRepository<T, ID>  (Commons)          ReactiveCrudRepository<T, ID>  (Commons)
        |                                          |
 MongoRepository<T, ID>                    ReactiveMongoRepository<T, ID>
   save(T) -> T                                Mono<T> save(T)
   findById(ID) -> Optional<T>                  Mono<T> findById(ID)
   findByStatus(String) -> List<T>              Flux<T> findByStatus(String)  -- SAME derivation rules

 Underneath: MongoTemplate                Underneath: ReactiveMongoTemplate
```

Both repository interfaces build on the exact same Spring Data Commons base interfaces and query-derivation infrastructure already covered for every prior module — only the underlying template (and therefore the actual database queries produced) differs.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="MongoRepository and ReactiveMongoRepository both extend Spring Data Commons base interfaces and delegate to their respective templates">
  <rect x="180" y="10" width="280" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="32" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring Data Commons (Crud/ReactiveCrud)</text>

  <rect x="30" y="70" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="97" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">MongoRepository -&gt; MongoTemplate</text>

  <rect x="350" y="70" width="260" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="97" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">ReactiveMongoRepository -&gt; ReactiveMongoTemplate</text>

  <line x1="270" y1="45" x2="180" y2="65" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mr)"/>
  <line x1="370" y1="45" x2="450" y2="65" stroke="#8b949e" stroke-width="1.3" marker-end="url(#mr)"/>
  <defs><marker id="mr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both repository flavors share the same base contracts and query-derivation rules — the fork happens only at the underlying template layer.

## 5. Runnable example

The scenario: an order repository, evolving from a blocking `MongoRepository`-style baseline using derived queries, to its reactive equivalent, to a repository combining derived methods with a MongoDB-specific `@Query` JSON string for a condition derivation can't express.

### Level 1 — Basic

Model the blocking `MongoRepository` style with a derived query method.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// interface OrderRepository extends MongoRepository<Order, Long> { List<Order> findByStatus(String status); }
interface OrderRepository {
    Order save(Order order);
    List<Order> findByStatus(String status);
}

class MongoOrderRepository implements OrderRepository {
    Map<Long, Order> collection = new HashMap<>();
    public Order save(Order order) { collection.put(order.id, order); return order; }
    public List<Order> findByStatus(String status) {
        return collection.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }
}

public class MongoRepoLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new MongoOrderRepository();
        repo.save(new Order(1, "SHIPPED", 50));
        repo.save(new Order(2, "PENDING", 150));

        List<Order> shipped = repo.findByStatus("SHIPPED");
        System.out.println("Found (blocking): " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java MongoRepoLevel1.java`

`findByStatus` is derived from the method name exactly like every earlier module's repository — underneath, `MongoRepository`'s generated implementation translates this into a MongoDB `find({status: "SHIPPED"})` query rather than SQL, but the Java-facing method signature and naming convention are identical.

### Level 2 — Intermediate

Model the reactive equivalent, using `CompletableFuture` to stand in for `Mono`/`Flux`, matching the same reactive-repository pattern from the R2DBC section.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// interface ReactiveOrderRepository extends ReactiveMongoRepository<Order, Long> { Flux<Order> findByStatus(String status); }
interface ReactiveOrderRepository {
    CompletableFuture<Order> save(Order order);              // stands in for Mono<Order>
    CompletableFuture<List<Order>> findByStatus(String status); // stands in for Flux<Order>
}

class ReactiveMongoOrderRepository implements ReactiveOrderRepository {
    Map<Long, Order> collection = new HashMap<>();
    public CompletableFuture<Order> save(Order order) {
        return CompletableFuture.supplyAsync(() -> { collection.put(order.id, order); return order; });
    }
    public CompletableFuture<List<Order>> findByStatus(String status) {
        return CompletableFuture.supplyAsync(() ->
            collection.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList()));
    }
}

public class MongoRepoLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveOrderRepository repo = new ReactiveMongoOrderRepository();
        repo.save(new Order(1, "SHIPPED", 50)).get(); // .get() only for demo sequencing
        repo.save(new Order(2, "PENDING", 150)).get();

        CompletableFuture<List<Order>> future = repo.findByStatus("SHIPPED"); // returns IMMEDIATELY
        List<Order> shipped = future.get(); // wait here only for demo purposes
        System.out.println("Found (reactive): " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java MongoRepoLevel2.java`

Same derived-method name, same conceptual behavior, but `findByStatus` now returns immediately with a `CompletableFuture` (standing in for `Flux<Order>`) — exactly mirroring the blocking-to-reactive transition already covered for relational repositories, just for MongoDB's `ReactiveMongoRepository` instead.

### Level 3 — Advanced

Add a method backed by MongoDB's JSON `@Query` syntax for a condition a derived method name can't cleanly express, alongside the existing derived methods on the same repository.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; List<String> tags; Order(long id, String status, double total, List<String> tags) { this.id = id; this.status = status; this.total = total; this.tags = tags; } }

interface OrderRepository {
    Order save(Order order);
    List<Order> findByStatus(String status); // derived
    List<Order> findHighValueTaggedOrders(String tag, double minTotal); // backed by @Query
}

class MongoOrderRepository implements OrderRepository {
    Map<Long, Order> collection = new HashMap<>();
    public Order save(Order order) { collection.put(order.id, order); return order; }
    public List<Order> findByStatus(String status) {
        return collection.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    // @Query("{ 'tags': ?0, 'total': { $gt: ?1 } }")
    public List<Order> findHighValueTaggedOrders(String tag, double minTotal) {
        System.out.println("  MongoDB query: { tags: '" + tag + "', total: { $gt: " + minTotal + " } }");
        return collection.values().stream()
            .filter(o -> o.tags.contains(tag) && o.total > minTotal)
            .collect(Collectors.toList());
    }
}

public class MongoRepoLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new MongoOrderRepository();
        repo.save(new Order(1, "SHIPPED", 50, List.of("gift")));
        repo.save(new Order(2, "SHIPPED", 200, List.of("gift", "urgent")));
        repo.save(new Order(3, "PENDING", 300, List.of("urgent")));

        List<Order> result = repo.findHighValueTaggedOrders("gift", 100.0);
        System.out.println("High-value gift orders: " + result.size());
    }
}
```

How to run: `java MongoRepoLevel3.java`

`findHighValueTaggedOrders` uses MongoDB's JSON query syntax (`{ 'tags': ?0, 'total': { $gt: ?1 } }`) via `@Query`, matching an array-containment condition (`tags` includes `"gift"`) combined with a numeric comparison — a condition that would produce an awkward derived method name (`findByTagsContainingAndTotalGreaterThan`) at best; the `@Query` form is clearer for this specific shape.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, three orders are saved: order 1 (`SHIPPED`, `total=50`, tags `["gift"]`), order 2 (`SHIPPED`, `total=200`, tags `["gift", "urgent"]`), and order 3 (`PENDING`, `total=300`, tags `["urgent"]`).

`repo.findHighValueTaggedOrders("gift", 100.0)` is called. Inside, the simulated MongoDB query is printed: `{ tags: 'gift', total: { $gt: 100.0 } }`. The stream filter then checks each order against both conditions: order 1 has tag `"gift"` but `total=50`, which fails `total > 100.0`, so it's excluded. Order 2 has tag `"gift"` and `total=200`, satisfying both conditions, so it's included. Order 3 doesn't have tag `"gift"` at all (only `"urgent"`), so it's excluded regardless of its total.

The resulting list contains just order 2, and "High-value gift orders: 1" is printed, confirming only the order satisfying *both* the tag-containment and the total-threshold conditions survived the filter.

```
findHighValueTaggedOrders("gift", 100.0):
  order1: tags=[gift], total=50    -> tag OK, total FAILS (50 not > 100)  -> excluded
  order2: tags=[gift,urgent], total=200 -> tag OK, total OK (200 > 100)   -> INCLUDED
  order3: tags=[urgent], total=300 -> tag FAILS (no "gift")                -> excluded
  result: [order2]
```

In a real Spring Data MongoDB application, `@Query("{ 'tags': ?0, 'total': { $gt: ?1 } }")` on `findHighValueTaggedOrders(String tag, double minTotal)` sends exactly that JSON filter document to MongoDB's `find` command, with `?0`/`?1` bound positionally to the method's arguments — MongoDB executes the filter server-side (using any index on `tags`/`total` if one exists) and returns only matching documents, which Spring Data MongoDB then maps back into `Order` objects, identically to how a derived method's generated query would be executed, just expressed as hand-written JSON instead of parsed from a method name.

## 7. Gotchas & takeaways

> Gotcha: MongoDB's `@Query` JSON syntax uses positional parameter placeholders (`?0`, `?1`, ...) by default, which — unlike named parameters — are easy to get out of order when a method has several arguments; a swapped parameter order compiles and runs without error, but silently queries the wrong fields.

- `MongoRepository`/`ReactiveMongoRepository` extend the same `CrudRepository`/`ReactiveCrudRepository` base interfaces (and derived-query-naming convention) shared across every Spring Data module.
- The blocking/reactive choice mirrors the relational modules exactly — same conceptual repository shape, different return types and underlying template.
- `@Query` on Spring Data MongoDB takes MongoDB's own JSON query syntax, not SQL or JPQL — reach for it when a condition (especially array/nested-document matching) doesn't translate cleanly into a derived method name.
- Both derived methods and `@Query` methods coexist naturally on the same repository interface, exactly as in every other Spring Data module covered so far.
