---
card: spring-data
gi: 92
slug: r2dbcentitytemplate
title: "R2dbcEntityTemplate"
---

## 1. What it is

`R2dbcEntityTemplate` is the reactive equivalent of `JdbcAggregateTemplate` (from the Spring Data JDBC section) — the lower-level class that every generated `ReactiveCrudRepository` method actually delegates to, offering direct, `Mono`/`Flux`-returning access to select/insert/update/delete operations for entities not necessarily reached through a repository interface at all.

```java
@Autowired R2dbcEntityTemplate template;

Mono<Order> saved = template.insert(order);
Flux<Order> found = template.select(Order.class)
    .matching(Criteria.where("status").is("SHIPPED"))
    .all();
```

## 2. Why & when

The `ReactiveCrudRepository` card showed the familiar repository-interface programming model; `R2dbcEntityTemplate` is what's underneath it, in exactly the same relationship `JdbcAggregateTemplate` has to `CrudRepository` on the JDBC side. Understanding it matters for the same two reasons: writing custom repository implementations that need reactive, template-level access, and building queries with the fluent Criteria API (covered fully in the next card) that a generated repository method can't express directly.

Reach for `R2dbcEntityTemplate` directly specifically when:

- Writing a custom reactive repository fragment (the same `<Repository>Impl` pattern from earlier cards, adapted to R2DBC) that needs entity-level operations beyond what a generated interface method exposes.
- You want to build a query dynamically at runtime using the fluent Criteria API rather than a fixed derived method name or `@Query` string — `template.select(...).matching(...)` is the entry point for that.
- You're working with an entity that isn't wired into a repository interface at all, but still needs reactive persistence operations — `R2dbcEntityTemplate` works directly against any mapped entity class.

## 3. Core concept

```
 interface OrderRepository extends ReactiveCrudRepository<Order, Long> { }
   -- generated implementation is a thin wrapper delegating to:

 R2dbcEntityTemplate.insert(order)   -- Mono<Order>, non-blocking INSERT
 R2dbcEntityTemplate.select(Order.class).matching(criteria).all()  -- Flux<Order>, non-blocking SELECT

 orderRepository.save(order)  ==  template.insert(order) / template.update(order)  (same operation, different entry point)
```

Exactly like `JdbcAggregateTemplate` for the blocking JDBC module, every generated reactive repository method is a convenience wrapper around `R2dbcEntityTemplate`.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Both the generated reactive repository and a custom implementation delegate to the same underlying R2dbcEntityTemplate">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.save(order)</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: template.insert(order)</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">R2dbcEntityTemplate</text>

  <line x1="150" y1="65" x2="290" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rt)"/>
  <line x1="490" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rt)"/>
  <defs><marker id="rt" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the generated repository and a hand-written custom fragment ultimately delegate to the same underlying `R2dbcEntityTemplate`.

## 5. Runnable example

The scenario: saving and querying orders, evolving from a generated-repository-style call, to exposing what `R2dbcEntityTemplate` does underneath directly, to a custom fragment using the template's fluent select API for a query no generated method expresses.

### Level 1 — Basic

Model the generated repository call as a thin wrapper, making the delegation to the underlying reactive template explicit.

```java
import java.util.*;
import java.util.concurrent.*;

class Order { Long id; String status; Order(Long id, String status) { this.id = id; this.status = status; } }

// Stands in for R2dbcEntityTemplate.
class R2dbcEntityTemplate {
    Map<Long, Order> db = new HashMap<>();
    private long nextId = 1;

    CompletableFuture<Order> insert(Order order) {
        return CompletableFuture.supplyAsync(() -> {
            order.id = nextId++;
            db.put(order.id, order);
            System.out.println("  [template] INSERT -> assigned id=" + order.id);
            return order;
        });
    }
}

// interface OrderRepository extends ReactiveCrudRepository<Order, Long> { }
// -- generated implementation is a thin wrapper around the template above.
class OrderRepository {
    private final R2dbcEntityTemplate template;
    OrderRepository(R2dbcEntityTemplate template) { this.template = template; }
    CompletableFuture<Order> save(Order order) { return template.insert(order); } // pure delegation
}

public class R2dbcTemplateLevel1 {
    public static void main(String[] args) throws Exception {
        R2dbcEntityTemplate template = new R2dbcEntityTemplate();
        OrderRepository repo = new OrderRepository(template);

        Order saved = repo.save(new Order(null, "PENDING")).get(); // .get() only for demo sequencing
        System.out.println("Saved with id=" + saved.id);
    }
}
```

How to run: `java R2dbcTemplateLevel1.java`

`OrderRepository.save` does nothing but forward to `template.insert(order)` — exactly the relationship between a generated Spring Data R2DBC repository and `R2dbcEntityTemplate`, mirroring `JdbcAggregateTemplate`'s role on the blocking JDBC side.

### Level 2 — Intermediate

Add a `select` operation on the template directly, showing the fluent query-building entry point (`template.select(Order.class).matching(...)`) that generated repository interfaces don't expose in raw form.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { Long id; String status; double total; Order(Long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class SelectSpec {
    private final List<Order> data;
    private String statusFilter;
    SelectSpec(List<Order> data) { this.data = data; }

    // Simulates R2dbcEntityTemplate.select(Order.class).matching(Criteria.where("status").is(status))
    SelectSpec matching(String status) { this.statusFilter = status; return this; }

    CompletableFuture<List<Order>> all() {
        return CompletableFuture.supplyAsync(() ->
            data.stream().filter(o -> statusFilter == null || o.status.equals(statusFilter)).collect(Collectors.toList()));
    }
}

class R2dbcEntityTemplate {
    List<Order> db = new ArrayList<>();
    SelectSpec select() { return new SelectSpec(db); } // select(Order.class) simplified for this example
}

public class R2dbcTemplateLevel2 {
    public static void main(String[] args) throws Exception {
        R2dbcEntityTemplate template = new R2dbcEntityTemplate();
        template.db.addAll(List.of(new Order(1L, "SHIPPED", 50), new Order(2L, "PENDING", 150)));

        List<Order> shipped = template.select().matching("SHIPPED").all().get(); // demo-only .get()
        System.out.println("Found via fluent template query: " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java R2dbcTemplateLevel2.java`

`template.select().matching("SHIPPED").all()` builds and executes a query fluently at the template level, entirely independent of any repository interface method — this is exactly the entry point a custom repository fragment or ad hoc service-layer query would use when a generated repository method isn't the right fit.

### Level 3 — Advanced

Combine both into a custom repository fragment using `R2dbcEntityTemplate` directly for an operation no generated interface exposes: an upsert-style "insert or update by natural key" operation.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { Long id; String externalRef; String status; Order(Long id, String externalRef, String status) { this.id = id; this.externalRef = externalRef; this.status = status; } }

class R2dbcEntityTemplate {
    List<Order> db = new ArrayList<>();
    private long nextId = 1;

    CompletableFuture<List<Order>> selectByExternalRef(String ref) {
        return CompletableFuture.supplyAsync(() ->
            db.stream().filter(o -> o.externalRef.equals(ref)).collect(Collectors.toList()));
    }
    CompletableFuture<Order> insert(Order order) {
        return CompletableFuture.supplyAsync(() -> { order.id = nextId++; db.add(order); return order; });
    }
    CompletableFuture<Order> update(Order order) {
        return CompletableFuture.supplyAsync(() -> {
            db.removeIf(o -> Objects.equals(o.id, order.id));
            db.add(order);
            return order;
        });
    }
}

// interface OrderRepositoryCustom { Mono<Order> upsertByExternalRef(Order order); }
interface OrderRepositoryCustom { CompletableFuture<Order> upsertByExternalRef(Order order); }

// class OrderRepositoryImpl implements OrderRepositoryCustom { @Autowired R2dbcEntityTemplate template; ... }
class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final R2dbcEntityTemplate template;
    OrderRepositoryImpl(R2dbcEntityTemplate template) { this.template = template; }

    // No generated ReactiveCrudRepository method expresses "insert if new, else update by external reference" --
    // this needs direct template access plus custom lookup logic.
    public CompletableFuture<Order> upsertByExternalRef(Order order) {
        return template.selectByExternalRef(order.externalRef).thenCompose(existing -> {
            if (existing.isEmpty()) {
                System.out.println("  No existing order for ref=" + order.externalRef + " -> INSERT");
                return template.insert(order);
            } else {
                Order match = existing.get(0);
                order.id = match.id;
                System.out.println("  Found existing order id=" + match.id + " for ref=" + order.externalRef + " -> UPDATE");
                return template.update(order);
            }
        });
    }
}

public class R2dbcTemplateLevel3 {
    public static void main(String[] args) throws Exception {
        R2dbcEntityTemplate template = new R2dbcEntityTemplate();
        OrderRepositoryCustom repo = new OrderRepositoryImpl(template);

        Order first = repo.upsertByExternalRef(new Order(null, "EXT-100", "PENDING")).get(); // INSERT path
        System.out.println("First upsert -> id=" + first.id + ", status=" + first.status);

        Order second = repo.upsertByExternalRef(new Order(null, "EXT-100", "SHIPPED")).get(); // UPDATE path, same ref
        System.out.println("Second upsert -> id=" + second.id + ", status=" + second.status);
    }
}
```

How to run: `java R2dbcTemplateLevel3.java`

`upsertByExternalRef` is a method no `ReactiveCrudRepository` interface exposes on its own — it's a custom fragment built directly on `R2dbcEntityTemplate`, first querying by `externalRef` to decide insert-vs-update, then delegating to the appropriate template operation. The first call inserts (no existing row for `"EXT-100"`); the second call, using the same `externalRef`, correctly finds and updates the row created by the first call instead of creating a duplicate.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.upsertByExternalRef(new Order(null, "EXT-100", "PENDING"))` is called. Inside `OrderRepositoryImpl.upsertByExternalRef`, `template.selectByExternalRef("EXT-100")` runs first, returning an empty list (nothing in `db` yet). `.thenCompose(existing -> ...)` sees `existing.isEmpty()` is `true`, prints "No existing order ... -> INSERT", and calls `template.insert(order)`, which assigns `id=1` and adds the order to `db`. The result, `first`, has `id=1, status="PENDING"`.

Next, `repo.upsertByExternalRef(new Order(null, "EXT-100", "SHIPPED"))` is called with the *same* `externalRef`. This time, `template.selectByExternalRef("EXT-100")` finds the previously-inserted order (`id=1`) in `db`. `.thenCompose` sees `existing` is non-empty, takes `match = existing.get(0)` (the order with `id=1`), sets the *new* order's `id` to match it (`order.id = 1`), prints "Found existing order id=1 ... -> UPDATE", and calls `template.update(order)` — which removes the old entry for `id=1` and adds the new one (`status="SHIPPED"`) in its place.

The final printed lines confirm: the first upsert produced `id=1, status=PENDING` (a genuine insert), and the second upsert produced `id=1, status=SHIPPED` (the *same* ID, confirming it updated the existing row rather than creating a second one).

```
upsertByExternalRef(ref="EXT-100", status=PENDING):
  selectByExternalRef -> [] (empty)  -> INSERT -> id=1, status=PENDING

upsertByExternalRef(ref="EXT-100", status=SHIPPED):
  selectByExternalRef -> [order{id=1}] (found) -> UPDATE (same id=1) -> id=1, status=SHIPPED
```

In a real Spring Data R2DBC application, `OrderRepositoryImpl` would have `R2dbcEntityTemplate` injected, and `upsertByExternalRef` would compose `template.select(Order.class).matching(Criteria.where("externalRef").is(ref)).first()` with `template.insert(...)`/`template.update(...)`, all chained through `Mono`'s `.flatMap()` — the whole operation runs as one non-blocking reactive pipeline, and application code calling `orderRepository.upsertByExternalRef(order)` (via the composed repository interface) never needs to know whether the underlying operation resulted in an insert or an update.

## 7. Gotchas & takeaways

> Gotcha: because `R2dbcEntityTemplate` operations are non-blocking and return `Mono`/`Flux`, chaining a lookup-then-write sequence like `upsertByExternalRef` has an inherent race condition under real concurrency — two simultaneous calls with the same `externalRef` could both see "no existing row" and both attempt an insert, unless the database enforces a unique constraint on `externalRef` as a backstop (which any correct implementation of this pattern needs regardless of blocking or reactive style).

- `R2dbcEntityTemplate` is the underlying implementation every generated `ReactiveCrudRepository` method delegates to — the reactive counterpart to `JdbcAggregateTemplate`.
- It exposes both simple entity operations (`insert`, `update`) and a fluent query-building API (`select(...).matching(...)`) for queries a generated interface method can't express directly.
- Custom reactive repository fragments inject `R2dbcEntityTemplate` directly, chaining its `Mono`/`Flux`-returning operations via `.flatMap()`/`.thenCompose()` to build multi-step, still-non-blocking operations.
- Lookup-then-write patterns built this way remain subject to race conditions under concurrency — a database-level uniqueness constraint is still the real safeguard, reactive or not.
