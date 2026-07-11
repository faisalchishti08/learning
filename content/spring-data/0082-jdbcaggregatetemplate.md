---
card: spring-data
gi: 82
slug: jdbcaggregatetemplate
title: "JdbcAggregateTemplate"
---

## 1. What it is

`JdbcAggregateTemplate` is the lower-level class that actually implements every `CrudRepository` method (`save`, `findById`, `delete`, ...) for Spring Data JDBC — the same relationship `JdbcTemplate` has to raw JDBC in classic Spring, or `EntityManager` has to `JpaRepository` in the JPA module. Injecting it directly gives access to aggregate-level operations that a generated repository interface doesn't expose as a method, such as `save`ing with an explicit control over insert-versus-update detection.

```java
@Autowired JdbcAggregateTemplate template;

Order saved = template.save(order);         // exactly what orderRepository.save(order) delegates to underneath
Optional<Order> found = template.findById(1L, Order.class);
```

## 2. Why & when

Every repository method used throughout this section's earlier cards — `save`, `findById`, derived queries — is, underneath, a thin call onto `JdbcAggregateTemplate`. Knowing this explains what a custom repository implementation (from the earlier custom-implementation pattern, applied here to JDBC) can inject to perform aggregate operations that no repository interface method directly exposes, and demystifies exactly what `save`/`findById` are doing under the hood.

Reach for `JdbcAggregateTemplate` directly specifically when:

- Writing a custom repository implementation fragment (the same `<Repository>Impl` pattern from the JPA custom-implementation card) that needs aggregate-level save/load operations beyond what the generated `CrudRepository` interface exposes.
- You need fine control over whether an operation is treated as an insert or an update — `JdbcAggregateTemplate` exposes this distinction more directly than the single overloaded `save` method on a repository interface.
- You're debugging or reasoning about exactly what SQL a repository's `save`/`findById` call produces — tracing through to `JdbcAggregateTemplate` (and the aggregate-mapping context from earlier cards) shows precisely what happens.

## 3. Core concept

```
 interface OrderRepository extends CrudRepository<Order, Long> { }
   -- Spring Data auto-generates an implementation...
   -- ...which internally is just a thin wrapper delegating to:

 JdbcAggregateTemplate.save(order)
   -- decides insert vs. update (based on whether the @Id field is null/new)
   -- writes the aggregate root's row
   -- deletes + re-inserts every @MappedCollection member (as covered in the aggregates-philosophy card)
   -- returns the saved aggregate

 orderRepository.save(order)  ==  jdbcAggregateTemplate.save(order)   (same operation, different entry point)
```

The generated `CrudRepository` methods and direct `JdbcAggregateTemplate` calls perform the exact same underlying operations — the repository interface is a convenience layer on top.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Both the generated repository interface and a custom implementation delegate to the same underlying JdbcAggregateTemplate">
  <rect x="20" y="20" width="240" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.save(order)</text>

  <rect x="380" y="20" width="240" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: template.save(order)</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">JdbcAggregateTemplate</text>

  <line x1="140" y1="65" x2="280" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#jt)"/>
  <line x1="500" y1="65" x2="400" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#jt)"/>
  <defs><marker id="jt" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every path — generated repository method or hand-written custom code — funnels through the same underlying `JdbcAggregateTemplate` operations.

## 5. Runnable example

The scenario: saving and loading orders, evolving from a plain generated-repository-style call, to exposing what `JdbcAggregateTemplate` actually does underneath (insert-vs-update detection), to a custom repository fragment that uses the template directly for an operation no generated method exposes.

### Level 1 — Basic

Model the generated repository call as a thin wrapper, making the delegation to an underlying template explicit.

```java
import java.util.*;

class Order { Long id; String status; Order(Long id, String status) { this.id = id; this.status = status; } }

// Stands in for JdbcAggregateTemplate.
class JdbcAggregateTemplate {
    Map<Long, Order> db = new HashMap<>();
    private long nextId = 1;

    Order save(Order order) {
        if (order.id == null) {
            order.id = nextId++; // insert path: assign a new id
            System.out.println("  [template] INSERT: assigned new id=" + order.id);
        } else {
            System.out.println("  [template] UPDATE: id=" + order.id + " already exists");
        }
        db.put(order.id, order);
        return order;
    }

    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

// interface OrderRepository extends CrudRepository<Order, Long> { }
// -- generated implementation is just a thin wrapper around the template above.
class OrderRepository {
    private final JdbcAggregateTemplate template;
    OrderRepository(JdbcAggregateTemplate template) { this.template = template; }
    Order save(Order order) { return template.save(order); } // pure delegation
    Optional<Order> findById(long id) { return template.findById(id); }
}

public class TemplateLevel1 {
    public static void main(String[] args) {
        JdbcAggregateTemplate template = new JdbcAggregateTemplate();
        OrderRepository repo = new OrderRepository(template);

        Order saved = repo.save(new Order(null, "PENDING")); // new -- id is null
        System.out.println("Saved with id=" + saved.id);
    }
}
```

How to run: `java TemplateLevel1.java`

`OrderRepository.save` does nothing but forward to `template.save(order)` — this is exactly the relationship between a generated Spring Data JDBC repository and the underlying `JdbcAggregateTemplate`: the repository interface is a thin, convenient facade, but every actual operation happens in the template.

### Level 2 — Intermediate

Make the insert-vs-update decision explicit and observable — a genuinely new aggregate (`id == null`) is inserted with a freshly assigned ID; an aggregate with an existing ID is updated instead.

```java
import java.util.*;

class Order { Long id; String status; Order(Long id, String status) { this.id = id; this.status = status; } }

class JdbcAggregateTemplate {
    Map<Long, Order> db = new HashMap<>();
    private long nextId = 1;

    Order save(Order order) {
        boolean isNew = order.id == null;
        if (isNew) {
            order.id = nextId++;
            System.out.println("  [template] treating as NEW -> INSERT INTO orders (id, status) VALUES (" + order.id + ", '" + order.status + "')");
        } else {
            System.out.println("  [template] treating as EXISTING -> UPDATE orders SET status='" + order.status + "' WHERE id=" + order.id);
        }
        db.put(order.id, order);
        return order;
    }
    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

public class TemplateLevel2 {
    public static void main(String[] args) {
        JdbcAggregateTemplate template = new JdbcAggregateTemplate();

        Order created = template.save(new Order(null, "PENDING")); // INSERT path
        System.out.println("Assigned id: " + created.id);

        created.status = "SHIPPED"; // mutate the already-saved (detached) object
        Order updated = template.save(created); // id is now non-null -> UPDATE path
        System.out.println("Status after update: " + template.findById(created.id).orElseThrow().status);
    }
}
```

How to run: `java TemplateLevel2.java`

The first `save` call sees `order.id == null`, treats it as an insert, and assigns a fresh ID (`1`). The second `save` call, using the same `created` object (now with `id=1` and a mutated `status`), sees a non-null `id` and treats it as an update instead — exactly the insert-vs-update decision `JdbcAggregateTemplate` makes for every call, regardless of whether it's reached via a generated repository method or invoked directly.

### Level 3 — Advanced

Add a custom repository fragment (matching the JPA custom-implementation pattern) that uses `JdbcAggregateTemplate` directly for an operation the generated `CrudRepository` interface doesn't expose: an explicit "insert-only" save that fails loudly if the aggregate already has an ID, guarding against accidental overwrites.

```java
import java.util.*;

class Order { Long id; String status; Order(Long id, String status) { this.id = id; this.status = status; } }

class JdbcAggregateTemplate {
    Map<Long, Order> db = new HashMap<>();
    private long nextId = 1;

    Order save(Order order) {
        boolean isNew = order.id == null;
        if (isNew) order.id = nextId++;
        db.put(order.id, order);
        return order;
    }
    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

// interface OrderRepositoryCustom { Order insertOnly(Order order); }
interface OrderRepositoryCustom { Order insertOnly(Order order); }

// class OrderRepositoryImpl implements OrderRepositoryCustom { @Autowired JdbcAggregateTemplate template; ... }
class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final JdbcAggregateTemplate template;
    OrderRepositoryImpl(JdbcAggregateTemplate template) { this.template = template; }

    // No generated CrudRepository method expresses "insert only, fail if this would be an update" --
    // this needs direct template access plus custom guard logic.
    public Order insertOnly(Order order) {
        if (order.id != null) {
            throw new IllegalStateException("insertOnly() called with an existing id=" + order.id + " -- refusing to update");
        }
        return template.save(order);
    }
}

class OrderRepository implements OrderRepositoryCustom {
    private final JdbcAggregateTemplate template;
    private final OrderRepositoryCustom custom;
    OrderRepository(JdbcAggregateTemplate template) {
        this.template = template;
        this.custom = new OrderRepositoryImpl(template);
    }
    Order save(Order order) { return template.save(order); } // generated-style method
    public Order insertOnly(Order order) { return custom.insertOnly(order); } // custom fragment
}

public class TemplateLevel3 {
    public static void main(String[] args) {
        JdbcAggregateTemplate template = new JdbcAggregateTemplate();
        OrderRepository repo = new OrderRepository(template);

        Order created = repo.insertOnly(new Order(null, "PENDING")); // succeeds -- genuinely new
        System.out.println("Inserted with id=" + created.id);

        try {
            repo.insertOnly(created); // created.id is now non-null -- this should be refused
        } catch (IllegalStateException e) {
            System.out.println("Correctly refused: " + e.getMessage());
        }
    }
}
```

How to run: `java TemplateLevel3.java`

`insertOnly` is a method that exists on *no* generated `CrudRepository` interface — it's a custom fragment (following the same `<Repository>Impl` pattern from the JPA custom-implementation card) built directly on `JdbcAggregateTemplate`, adding a guard the generated `save` method doesn't have. The first call succeeds because `created.id` starts `null`; the second call, reusing the now-saved (non-null-`id`) `created` object, correctly throws rather than silently performing an update.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.insertOnly(new Order(null, "PENDING"))` is called, delegating to `custom.insertOnly(order)` on the `OrderRepositoryImpl` fragment. Inside, `order.id` is `null`, so the guard condition (`order.id != null`) is false, and execution proceeds to `template.save(order)` — which assigns a fresh `id` (`1`) and stores the order. `created` now holds `id=1, status="PENDING"`. "Inserted with id=1" is printed.

Next, `repo.insertOnly(created)` is called again, this time passing the *same* `created` object from the previous step — which now has `id=1`, not `null`. Inside `insertOnly`, the guard condition `order.id != null` is now `true`, so the method throws `IllegalStateException` immediately, *before* ever reaching `template.save(...)` — no update is silently performed. The `catch` block in `main` catches this and prints "Correctly refused: insertOnly() called with an existing id=1 -- refusing to update".

```
insertOnly(Order(id=null, "PENDING"))
   -> guard passes (id is null) -> template.save(...) -> id assigned=1 -> returns Order(id=1,...)

insertOnly(created)  // created.id == 1 now
   -> guard FAILS (id != null) -> throws IllegalStateException, template.save(...) never called
```

In a real Spring Data JDBC application, `OrderRepositoryImpl` would have `JdbcAggregateTemplate` injected via `@Autowired` (or constructor injection), and `insertOnly` would appear as a method on the composed `OrderRepository` interface (extending both `CrudRepository<Order, Long>` and `OrderRepositoryCustom`) — application code calling `orderRepository.insertOnly(newOrder)` gets the safety guard, while `orderRepository.save(existingOrder)` (the generated method) continues to perform ordinary insert-or-update behavior via the same underlying `JdbcAggregateTemplate`, just without the extra guard.

## 7. Gotchas & takeaways

> Gotcha: `JdbcAggregateTemplate`'s insert-vs-update decision is based purely on whether the `@Id` field is `null` (or, for primitive/wrapper ID types, a database default) — manually setting an ID on a genuinely new object before saving (e.g., to pre-generate an ID client-side) causes it to be treated as an update against a row that doesn't exist, typically resulting in zero rows affected rather than the expected insert.

- `JdbcAggregateTemplate` is the underlying implementation every generated `CrudRepository` method for Spring Data JDBC delegates to — it's not a separate, alternative API, but the actual mechanism.
- It decides insert-versus-update purely based on whether the aggregate root's `@Id` field is currently `null`.
- Custom repository implementations (the `<Repository>Impl` pattern) inject `JdbcAggregateTemplate` directly to build operations the generated interface doesn't expose.
- Understanding `JdbcAggregateTemplate` demystifies exactly what SQL a plain `save()`/`findById()` call produces, since there is no additional persistence-context layer hiding further behavior underneath it.
