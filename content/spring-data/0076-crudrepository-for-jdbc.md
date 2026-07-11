---
card: spring-data
gi: 76
slug: crudrepository-for-jdbc
title: "CrudRepository for JDBC"
---

## 1. What it is

Spring Data JDBC repositories extend the exact same `CrudRepository<T, ID>` interface (and the same `PagingAndSortingRepository`) covered in the Spring Data Commons cards — `save`, `findById`, `findAll`, `deleteById`, and the rest — but the implementation behind them issues plain SQL directly, using `JdbcAggregateTemplate` internally, rather than going through a JPA persistence context.

```java
interface OrderRepository extends CrudRepository<Order, Long> { }

orderRepository.save(order);          // direct INSERT or UPDATE, no persistence context
orderRepository.findById(1L);         // direct SELECT, returns a detached object immediately
```

## 2. Why & when

The previous card explained *why* Spring Data JDBC treats entities as aggregates; this card is about how familiar that feels day-to-day, because the repository interface itself is identical to the one already used throughout the Spring Data Commons and JPA cards. Switching a project from Spring Data JPA to Spring Data JDBC (or vice versa) often changes very little application code — the difference is what happens *underneath* `save`/`findById`, not the method signatures themselves.

Reach for `CrudRepository` on Spring Data JDBC specifically when:

- You want the same familiar repository programming model (`save`, `findById`, derived query methods) but with the simpler, more predictable aggregate-oriented persistence explained in the previous card.
- You're evaluating a migration between Spring Data modules and want to know what stays the same — the answer is: almost the entire repository interface and derived-query-naming convention.
- You need `save`'s return value to reflect the *actual* state written to the database immediately — since there's no persistence context deferring writes, `save` executes its SQL synchronously, right there.

## 3. Core concept

```
 interface OrderRepository extends CrudRepository<Order, Long> { }
   -- IDENTICAL interface shape to a Spring Data JPA repository

 orderRepository.save(order)
   JPA:  entity becomes MANAGED; actual UPDATE/INSERT may be deferred until flush/commit
   JDBC: SQL is issued IMMEDIATELY, synchronously, no deferred flush, no persistence context at all

 orderRepository.findById(1L)
   JPA:  entity becomes MANAGED (subsequent field changes get auto-tracked)
   JDBC: entity is returned DETACHED -- mutating it does nothing until you call save() again explicitly
```

The method names and signatures are shared with JPA, but every call is a direct, synchronous SQL operation with no managed/detached distinction to reason about.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="The same CrudRepository interface is backed by a persistence context in JPA, or direct synchronous SQL in JDBC">
  <rect x="230" y="15" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CrudRepository&lt;Order,Long&gt;</text>

  <rect x="30" y="90" width="240" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring Data JPA impl</text>
  <text x="150" y="128" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">persistence context, deferred flush</text>

  <rect x="380" y="90" width="240" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring Data JDBC impl</text>
  <text x="500" y="128" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">direct SQL, synchronous, no context</text>

  <line x1="300" y1="55" x2="180" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cr)"/>
  <line x1="340" y1="55" x2="470" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cr)"/>
  <defs><marker id="cr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The exact same repository interface can be backed by two very different implementations — the calling code never changes.

## 5. Runnable example

The scenario: a repository for orders, evolving from a plain `CrudRepository`-shaped interface, to a JDBC-style implementation that issues synchronous SQL with no persistence context, to a demonstration that returned entities are detached (mutating them has no automatic effect).

### Level 1 — Basic

Model the shared `CrudRepository`-shaped interface first, with a minimal in-memory JDBC-style implementation.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

// interface OrderRepository extends CrudRepository<Order, Long> { }
interface CrudRepository {
    Order save(Order order);
    Optional<Order> findById(long id);
    void deleteById(long id);
}

class JdbcOrderRepository implements CrudRepository {
    private final Map<Long, Order> db = new HashMap<>();

    public Order save(Order order) {
        System.out.println("  SQL: INSERT/UPDATE orders ... (issued immediately, synchronously)");
        db.put(order.id, order); // no persistence context -- this IS the write
        return order;
    }

    public Optional<Order> findById(long id) {
        System.out.println("  SQL: SELECT * FROM orders WHERE id = " + id);
        return Optional.ofNullable(db.get(id));
    }

    public void deleteById(long id) {
        System.out.println("  SQL: DELETE FROM orders WHERE id = " + id);
        db.remove(id);
    }
}

public class CrudJdbcLevel1 {
    public static void main(String[] args) {
        CrudRepository repo = new JdbcOrderRepository();

        repo.save(new Order(1, "PENDING"));
        Order found = repo.findById(1L).orElseThrow();
        System.out.println("Found: status=" + found.status);
    }
}
```

How to run: `java CrudJdbcLevel1.java`

Every call to `save`/`findById` prints its simulated SQL immediately, with no deferred-flush step anywhere — this is the entire point of contrast with the JPA-backed implementation from earlier cards, where `save` might only mark an entity managed, deferring the actual `INSERT`/`UPDATE` until a later flush or commit.

### Level 2 — Intermediate

Add derived query methods (matching the naming-convention mechanism from Spring Data Commons), showing that this JDBC-specific repository still supports the same query-derivation conventions used throughout the rest of Spring Data.

```java
import java.util.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

interface OrderRepository {
    Order save(Order order);
    Optional<Order> findById(long id);
    List<Order> findByStatus(String status);          // derived query, same convention as JPA
    List<Order> findByStatusAndTotalGreaterThan(String status, double total); // combined condition
}

class JdbcOrderRepository implements OrderRepository {
    private final Map<Long, Order> db = new HashMap<>();

    public Order save(Order order) {
        System.out.println("  SQL: INSERT/UPDATE orders (id=" + order.id + ")");
        db.put(order.id, order);
        return order;
    }
    public Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }

    public List<Order> findByStatus(String status) {
        System.out.println("  SQL: SELECT * FROM orders WHERE status = '" + status + "'");
        return db.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    public List<Order> findByStatusAndTotalGreaterThan(String status, double total) {
        System.out.println("  SQL: SELECT * FROM orders WHERE status = '" + status + "' AND total > " + total);
        return db.values().stream()
            .filter(o -> o.status.equals(status) && o.total > total)
            .collect(Collectors.toList());
    }
}

public class CrudJdbcLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new JdbcOrderRepository();
        repo.save(new Order(1, "SHIPPED", 50));
        repo.save(new Order(2, "SHIPPED", 150));
        repo.save(new Order(3, "PENDING", 200));

        System.out.println("Shipped orders: " + repo.findByStatus("SHIPPED").size());
        System.out.println("Shipped over 100: " + repo.findByStatusAndTotalGreaterThan("SHIPPED", 100).size());
    }
}
```

How to run: `java CrudJdbcLevel2.java`

`findByStatus` and `findByStatusAndTotalGreaterThan` follow exactly the same derived-query naming convention introduced generically in the Spring Data Commons cards — Spring Data JDBC parses the method name into a `WHERE` clause the same way the JPA module does; only the underlying SQL execution mechanism (direct, no persistence context) differs.

### Level 3 — Advanced

Demonstrate the detached-entity behavior directly: an object returned by `findById` is a plain, unmanaged Java object — mutating it has zero effect on the database until `save` is called again explicitly.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

interface OrderRepository {
    Order save(Order order);
    Optional<Order> findById(long id);
}

class JdbcOrderRepository implements OrderRepository {
    private final Map<Long, Order> db = new HashMap<>();
    public Order save(Order order) {
        System.out.println("  SQL: INSERT/UPDATE orders SET status='" + order.status + "' WHERE id=" + order.id);
        db.put(order.id, new Order(order.id, order.status)); // store an independent copy -- no shared reference
        return order;
    }
    public Optional<Order> findById(long id) {
        Order stored = db.get(id);
        return stored == null ? Optional.empty() : Optional.of(new Order(stored.id, stored.status)); // fresh, detached copy
    }
}

public class CrudJdbcLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new JdbcOrderRepository();
        repo.save(new Order(1, "PENDING"));

        Order fetched = repo.findById(1L).orElseThrow();
        System.out.println("Fetched: " + fetched.status);

        fetched.status = "SHIPPED"; // mutate the DETACHED object -- no persistence context tracking this
        System.out.println("Mutated in memory: " + fetched.status);

        Order reFetched = repo.findById(1L).orElseThrow(); // re-query the "database"
        System.out.println("Still in DB (unaffected by the mutation above): " + reFetched.status);

        repo.save(fetched); // must EXPLICITLY save to persist the mutation
        Order afterSave = repo.findById(1L).orElseThrow();
        System.out.println("After explicit save: " + afterSave.status);
    }
}
```

How to run: `java CrudJdbcLevel3.java`

Mutating `fetched.status` to `"SHIPPED"` has no effect on the underlying `db` at all — `reFetched.status` still prints `"PENDING"`, because `findById` returned a detached copy with no ongoing connection back to the "database." Only the explicit `repo.save(fetched)` call actually writes the change, after which `afterSave.status` finally shows `"SHIPPED"` — there is no dirty-checking or automatic persistence anywhere in this model.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.save(new Order(1, "PENDING"))` runs, printing the simulated `INSERT`/`UPDATE` and storing an independent copy of the order (`status="PENDING"`) in `db`.

Next, `repo.findById(1L)` runs, returning a *new*, independent `Order` object (`fetched`) copied from what's stored — not a reference to the same object stored in `db`. "Fetched: PENDING" is printed.

Then `fetched.status = "SHIPPED"` mutates this detached copy in memory only. "Mutated in memory: SHIPPED" is printed, but critically, nothing has been written back to `db` — this mutation exists purely in `fetched`'s own memory.

`repo.findById(1L)` is called again, producing `reFetched` — another fresh copy from `db`, which still holds `"PENDING"` (the mutation on `fetched` never touched it). "Still in DB ...: PENDING" confirms this.

Finally, `repo.save(fetched)` is called explicitly, passing the mutated `fetched` object — this overwrites `db`'s stored copy with `fetched`'s current state (`"SHIPPED"`). A final `repo.findById(1L)` now returns `"SHIPPED"`, confirming the change only took effect once `save` was explicitly called.

```
save(Order(1,"PENDING"))     -> db = {1: PENDING}
findById(1) -> fetched{PENDING}   (independent copy)
fetched.status = "SHIPPED"        (mutates ONLY the copy, db untouched)
findById(1) -> reFetched{PENDING} (db still shows the old value)
save(fetched)                     -> db = {1: SHIPPED}   (explicit write)
findById(1) -> {SHIPPED}          (now reflects the mutation)
```

In a real Spring Data JDBC application, `orderRepository.findById(1L)` returns a plain Java object with absolutely no framework-managed state attached to it — there is no persistence context to later ask "did anything change." A controller or service that fetches an order, mutates a field, and forgets to call `orderRepository.save(order)` again will simply see no change persisted at all — unlike JPA, where the equivalent mutation inside a `@Transactional` method would be picked up automatically by dirty checking at commit time.

## 7. Gotchas & takeaways

> Gotcha: because there is no dirty checking, a common migration bug when moving from JPA to Spring Data JDBC is forgetting that a mutation on a fetched entity now requires an explicit `save()` call — code that worked correctly under JPA (relying on automatic flush) silently does nothing under JDBC.

- Spring Data JDBC repositories extend the identical `CrudRepository`/`PagingAndSortingRepository` interfaces used by every other Spring Data module — the programming model is shared.
- Every repository call issues SQL synchronously and immediately — there is no deferred flush, no persistence context, no managed-entity state.
- Objects returned by `findById`/`findAll` are fully detached — mutating them has no effect until `save()` is called again explicitly.
- Derived query method naming (`findByStatus`, `findByStatusAndTotalGreaterThan`, ...) works identically to the JPA module, since it's implemented by the shared Spring Data Commons query-derivation mechanism.
