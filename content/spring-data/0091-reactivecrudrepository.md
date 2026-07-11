---
card: spring-data
gi: 91
slug: reactivecrudrepository
title: "ReactiveCrudRepository"
---

## 1. What it is

`ReactiveCrudRepository<T, ID>` is the reactive counterpart to `CrudRepository<T, ID>` — the same `save`, `findById`, `findAll`, `deleteById` operations, but every method returns `Mono<T>` (for single results) or `Flux<T>` (for multiple results) instead of returning values directly, and derived query methods use the exact same naming convention covered throughout every earlier Spring Data card.

```java
interface OrderRepository extends ReactiveCrudRepository<Order, Long> {
    Mono<Order> findById(Long id);            // zero-or-one
    Flux<Order> findByStatus(String status);   // zero-or-many
    Mono<Long> countByStatus(String status);   // a single aggregate value
}
```

## 2. Why & when

The reactive-overview card established *why* R2DBC exists; this card is about the concrete repository programming model built on top of it, and how closely it mirrors the familiar `CrudRepository` shape already used throughout the JPA and JDBC sections — the derived-query-method convention, the annotation-driven customization, all carry over. The only fundamental difference is the return type: `Mono`/`Flux` instead of a direct value.

Reach for `ReactiveCrudRepository` specifically when:

- You're building a Spring Data R2DBC repository and want the same familiar `save`/`findById`/derived-query programming model used across every other Spring Data module.
- You need to compose multiple repository calls into one non-blocking pipeline — `Mono`/`Flux`'s `.flatMap()`/`.map()` operators are how that composition happens, replacing the sequential blocking calls you'd write against a `CrudRepository`.
- You're translating an existing blocking repository interface to its reactive equivalent — the translation is mostly mechanical: wrap each return type in `Mono`/`Flux`, and change calling code from direct value access to reactive operator chains.

## 3. Core concept

```
 CrudRepository<Order, Long>            ReactiveCrudRepository<Order, Long>
   Order save(Order order)                Mono<Order> save(Order order)
   Optional<Order> findById(Long id)       Mono<Order> findById(Long id)
   Iterable<Order> findAll()               Flux<Order> findAll()
   void deleteById(Long id)                 Mono<Void> deleteById(Long id)

 Derived methods work IDENTICALLY:
   List<Order> findByStatus(String s)  -->  Flux<Order> findByStatus(String s)
```

Every method's meaning stays the same — only the return type changes, wrapping the result in a reactive publisher instead of exposing it directly.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="CrudRepository and ReactiveCrudRepository expose the same operations, differing only in whether results are direct values or reactive publishers">
  <rect x="20" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CrudRepository</text>
  <text x="35" y="65" fill="#8b949e" font-size="8.5" font-family="monospace">Order save(Order)</text>
  <text x="35" y="82" fill="#8b949e" font-size="8.5" font-family="monospace">Optional&lt;Order&gt; findById(id)</text>
  <text x="35" y="99" fill="#8b949e" font-size="8.5" font-family="monospace">List&lt;Order&gt; findByStatus(s)</text>

  <rect x="350" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ReactiveCrudRepository</text>
  <text x="365" y="65" fill="#8b949e" font-size="8.5" font-family="monospace">Mono&lt;Order&gt; save(Order)</text>
  <text x="365" y="82" fill="#8b949e" font-size="8.5" font-family="monospace">Mono&lt;Order&gt; findById(id)</text>
  <text x="365" y="99" fill="#8b949e" font-size="8.5" font-family="monospace">Flux&lt;Order&gt; findByStatus(s)</text>

  <line x1="290" y1="70" x2="345" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rc)"/>
  <defs><marker id="rc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same method names, same query-derivation rules — every return type is simply wrapped in `Mono`/`Flux`.

## 5. Runnable example

The scenario: an order repository, evolving from a blocking `CrudRepository`-style baseline, to its `Mono`/`Flux`-returning reactive equivalent (modeled with `CompletableFuture`/`Stream` since a real reactive type needs a reactive library), to composing multiple reactive repository calls in one non-blocking chain.

### Level 1 — Basic

Model the blocking `CrudRepository`-style baseline first, for direct comparison.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

interface OrderRepository {
    Order save(Order order);
    Optional<Order> findById(long id);
    List<Order> findByStatus(String status);
}

class BlockingOrderRepository implements OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    public Order save(Order order) { db.put(order.id, order); return order; }
    public Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
    public List<Order> findByStatus(String status) {
        return db.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }
}

public class ReactiveCrudLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new BlockingOrderRepository();
        repo.save(new Order(1, "SHIPPED"));
        repo.save(new Order(2, "PENDING"));

        List<Order> shipped = repo.findByStatus("SHIPPED"); // returns a direct, already-complete List
        System.out.println("Found (blocking): " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java ReactiveCrudLevel1.java`

`findByStatus` returns a fully-materialized `List<Order>` — by the time the method call returns, all the work (however it happens underneath) is already done; the calling thread has no choice but to have waited for it.

### Level 2 — Intermediate

Introduce the reactive equivalent, using `CompletableFuture<List<Order>>` to stand in for `Flux<Order>` (since a genuine `Flux` requires Project Reactor as a dependency) — the method returns immediately, with results delivered asynchronously.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

// interface OrderRepository extends ReactiveCrudRepository<Order, Long> { Flux<Order> findByStatus(String status); }
interface ReactiveOrderRepository {
    CompletableFuture<Order> save(Order order);              // stands in for Mono<Order>
    CompletableFuture<Optional<Order>> findById(long id);      // stands in for Mono<Order>
    CompletableFuture<List<Order>> findByStatus(String status); // stands in for Flux<Order>
}

class R2dbcOrderRepository implements ReactiveOrderRepository {
    Map<Long, Order> db = new HashMap<>();
    public CompletableFuture<Order> save(Order order) {
        return CompletableFuture.supplyAsync(() -> { db.put(order.id, order); return order; });
    }
    public CompletableFuture<Optional<Order>> findById(long id) {
        return CompletableFuture.supplyAsync(() -> Optional.ofNullable(db.get(id)));
    }
    public CompletableFuture<List<Order>> findByStatus(String status) {
        return CompletableFuture.supplyAsync(() ->
            db.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList()));
    }
}

public class ReactiveCrudLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveOrderRepository repo = new R2dbcOrderRepository();

        repo.save(new Order(1, "SHIPPED")).join(); // .join() used only for this demo's sequencing
        repo.save(new Order(2, "PENDING")).join();

        CompletableFuture<List<Order>> future = repo.findByStatus("SHIPPED"); // returns IMMEDIATELY
        System.out.println("Call returned; result not yet necessarily available.");

        List<Order> shipped = future.get(); // wait here ONLY for demo purposes
        System.out.println("Found (reactive): " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java ReactiveCrudLevel2.java`

`findByStatus` now returns a `CompletableFuture` (standing in for `Flux<Order>`) immediately — the "Call returned" message prints before we've necessarily waited for any actual query to complete, mirroring how a real `Flux<Order>` is a description of future emissions, not the data itself, until something subscribes to it.

### Level 3 — Advanced

Compose two repository calls together reactively: fetch orders by status, then for each one, fetch its full details — chained via `.thenCompose()`, matching how a real reactive pipeline chains `.flatMap()` calls across `Mono`/`Flux` without ever blocking in between.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
class OrderDetail { long orderId; String status; double total; int lineItemCount; OrderDetail(long orderId, String status, double total, int lineItemCount) { this.orderId = orderId; this.status = status; this.total = total; this.lineItemCount = lineItemCount; } }

class R2dbcOrderRepository {
    Map<Long, Order> db = new HashMap<>();
    Map<Long, Integer> lineItemCounts = new HashMap<>();

    CompletableFuture<List<Order>> findByStatus(String status) {
        return CompletableFuture.supplyAsync(() ->
            db.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList()));
    }

    CompletableFuture<Integer> countLineItems(long orderId) {
        return CompletableFuture.supplyAsync(() -> lineItemCounts.getOrDefault(orderId, 0));
    }

    // findByStatus(...).flatMap(order -> countLineItems(order.id).map(count -> new OrderDetail(...)))
    CompletableFuture<List<OrderDetail>> findDetailsByStatus(String status) {
        return findByStatus(status).thenCompose(orders -> {
            List<CompletableFuture<OrderDetail>> detailFutures = orders.stream()
                .map(o -> countLineItems(o.id).thenApply(count -> new OrderDetail(o.id, o.status, o.total, count)))
                .collect(Collectors.toList());
            return CompletableFuture.allOf(detailFutures.toArray(new CompletableFuture[0]))
                .thenApply(v -> detailFutures.stream().map(CompletableFuture::join).collect(Collectors.toList()));
        });
    }
}

public class ReactiveCrudLevel3 {
    public static void main(String[] args) throws Exception {
        R2dbcOrderRepository repo = new R2dbcOrderRepository();
        repo.db.put(1L, new Order(1, "SHIPPED", 50));
        repo.db.put(2L, new Order(2, "SHIPPED", 150));
        repo.lineItemCounts.put(1L, 2);
        repo.lineItemCounts.put(2L, 1);

        List<OrderDetail> details = repo.findDetailsByStatus("SHIPPED").get(); // wait only for demo purposes
        for (OrderDetail d : details) {
            System.out.println("Order " + d.orderId + ": total=" + d.total + ", lineItems=" + d.lineItemCount);
        }
    }
}
```

How to run: `java ReactiveCrudLevel3.java`

`findDetailsByStatus` chains `findByStatus` into a per-order `countLineItems` lookup via `.thenCompose()`/`.thenApply()` — exactly mirroring how a real reactive pipeline would write `orderRepository.findByStatus(status).flatMap(order -> lineItemRepository.countByOrderId(order.id).map(count -> new OrderDetail(...)))`, composing two reactive repository calls into one pipeline with no blocking step anywhere in between.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo` is seeded with two `SHIPPED` orders and their line-item counts.

`repo.findDetailsByStatus("SHIPPED")` is called, which internally calls `findByStatus("SHIPPED")` — this returns a `CompletableFuture<List<Order>>` immediately, without the calling thread waiting. `.thenCompose(orders -> ...)` registers a continuation that will run once that list becomes available.

When the continuation runs, `orders` holds the two matching orders. The `.map(o -> countLineItems(o.id).thenApply(...))` step calls `countLineItems` once per order — both calls are independent `CompletableFuture`s kicked off essentially simultaneously, each eventually producing an `OrderDetail` combining the order's own fields with its line-item count via `.thenApply(...)`.

`CompletableFuture.allOf(...)` then waits for both of these per-order futures to complete, and `.thenApply(v -> ...)` collects their results (via `.join()`, safe here because `allOf` already guarantees both are done) into the final `List<OrderDetail>`.

Back in `main`, `.get()` blocks only for this demo program's own purposes, and the resulting two `OrderDetail` objects are printed: order 1 with `total=50, lineItems=2`, and order 2 with `total=150, lineItems=1`.

```
findByStatus("SHIPPED")  -> [order1, order2]   (async, non-blocking)
  .thenCompose: for EACH order, countLineItems(id) -> combine into OrderDetail  (both run concurrently)
  allOf(...).thenApply(...) -> [OrderDetail(1,...,2), OrderDetail(2,...,1)]
```

In a real Spring Data R2DBC application, `orderRepository.findByStatus("SHIPPED")` returns a `Flux<Order>` immediately, and `.flatMap(order -> lineItemRepository.countByOrderId(order.id).map(count -> new OrderDetail(order, count)))` composes a per-order reactive lookup for each emitted `Order`, running these lookups concurrently (up to Reactor's configured concurrency) rather than one-at-a-time — the entire pipeline, from `findByStatus` through the final `OrderDetail` stream, executes without a single thread ever blocking on database I/O, whether it's handling one request or ten thousand concurrently.

## 7. Gotchas & takeaways

> Gotcha: calling `.block()` on a `Mono`/`Flux` (the real equivalent of this example's demo-only `.get()`/`.join()` calls) inside application code that's meant to stay reactive reintroduces blocking — it's occasionally acceptable in tests or at the very outermost edge of an application, but doing it inside a reactive pipeline (e.g., inside a `.flatMap()`) is a common and serious anti-pattern that can deadlock the reactive runtime's limited thread pool.

- `ReactiveCrudRepository<T, ID>` mirrors `CrudRepository<T, ID>` method-for-method — the same derived-query-naming convention, wrapped in `Mono`/`Flux` return types.
- The fundamental shift is compositional: instead of sequential blocking calls with direct return values, reactive code chains operators (`.flatMap()`, `.map()`) that describe what should happen once data becomes available.
- Reach for `ReactiveCrudRepository` as the natural repository layer for a Spring Data R2DBC-backed, fully reactive application.
- Never call `.block()` (or its blocking equivalents) inside a reactive pipeline itself — reserve it for tests or the outermost boundary of the application, if at all.
