---
card: spring-data
gi: 72
slug: custom-jpa-repository-implementation
title: "Custom JPA repository implementation"
---

## 1. What it is

This card applies the custom-repository-fragment mechanism (introduced generically in an earlier Spring Data Commons card) specifically to JPA: you write a plain interface declaring the extra method(s), implement it in a class named `<RepositoryName>Impl` using `EntityManager` directly, and have your main repository interface extend both `JpaRepository` and your custom interface — Spring Data JPA stitches all three together into one bean.

```java
interface OrderRepositoryCustom { void bulkUpdateStatus(String from, String to); }

class OrderRepositoryImpl implements OrderRepositoryCustom {
    @PersistenceContext EntityManager em;
    public void bulkUpdateStatus(String from, String to) {
        em.createQuery("UPDATE Order o SET o.status = :to WHERE o.status = :from")
          .setParameter("to", to).setParameter("from", from).executeUpdate();
    }
}

interface OrderRepository extends JpaRepository<Order, Long>, OrderRepositoryCustom { }
```

## 2. Why & when

Every other JPA card so far worked within what derived queries, `@Query`, `@Procedure`, or Querydsl can express declaratively. Sometimes a repository method needs genuine imperative logic — direct `EntityManager` access, a multi-step operation, or integration with a non-Spring-Data library — that no annotation-driven approach can express. Custom implementations are the escape hatch: the method still lives on the repository interface application code already depends on, but its body is hand-written Java.

Reach for a custom implementation specifically when:

- The operation needs direct `EntityManager`/`Session` access — e.g., calling Hibernate-specific APIs (like the previous card's batching, or Envers' `AuditReader`) that have no `@Query`-expressible equivalent.
- The logic genuinely can't be one query — e.g., building a query dynamically based on complex runtime conditions beyond what a `Specification` conveniently expresses, or orchestrating multiple `EntityManager` calls as one repository method.
- You want the custom method to appear on the *same* repository interface as the generated ones, so callers never need to know or care which methods are declarative and which are hand-written.

## 3. Core concept

```
 interface OrderRepositoryCustom { void bulkUpdateStatus(String from, String to); }

 class OrderRepositoryImpl implements OrderRepositoryCustom {
     @PersistenceContext EntityManager em;
     public void bulkUpdateStatus(...) { em.createQuery(...).executeUpdate(); }  -- hand-written
 }

 interface OrderRepository extends JpaRepository<Order, Long>,   -- generated: save/findById/...
                                    OrderRepositoryCustom { }     -- custom: bulkUpdateStatus

 Spring Data detects "OrderRepositoryImpl" by NAMING CONVENTION
 (interface name + "Impl") and wires it in automatically as a fragment.
```

The naming convention (`<Repository>Impl`) is how Spring Data finds and stitches in the hand-written fragment — no explicit wiring configuration is needed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="OrderRepository extends both JpaRepository and a custom interface, backed by a hand-written Impl class found by naming convention">
  <rect x="220" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">OrderRepository</text>

  <rect x="30" y="105" width="220" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">extends JpaRepository</text>
  <text x="140" y="143" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">save, findById, ... (generated)</text>

  <rect x="390" y="105" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">extends OrderRepositoryCustom</text>
  <text x="500" y="143" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; OrderRepositoryImpl (hand-written)</text>

  <line x1="270" y1="65" x2="150" y2="100" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ci)"/>
  <line x1="370" y1="65" x2="490" y2="100" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ci)"/>
  <defs><marker id="ci" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One repository bean is stitched together from a generated fragment (`JpaRepository`) and a hand-written one (`OrderRepositoryImpl`), found automatically by its `Impl` suffix.

## 5. Runnable example

The scenario: a bulk status-update operation that a derived query or simple `@Query` can express, but which is used here to build up the custom-fragment wiring pattern, evolving from a plain custom class, to the two-interface composition, to a version that also uses direct `EntityManager`-style batching logic no declarative query could express.

### Level 1 — Basic

Model the custom implementation class in isolation first — plain Java doing the actual work.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

// interface OrderRepositoryCustom { void bulkUpdateStatus(String from, String to); }
interface OrderRepositoryCustom { void bulkUpdateStatus(String from, String to); }

// class OrderRepositoryImpl implements OrderRepositoryCustom { @PersistenceContext EntityManager em; ... }
class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final List<Order> db;
    OrderRepositoryImpl(List<Order> db) { this.db = db; }

    public void bulkUpdateStatus(String from, String to) {
        // UPDATE orders SET status = :to WHERE status = :from
        for (Order o : db) if (o.status.equals(from)) o.status = to;
    }
}

public class CustomRepoLevel1 {
    public static void main(String[] args) {
        List<Order> db = new ArrayList<>(List.of(new Order(1, "PENDING"), new Order(2, "PENDING"), new Order(3, "SHIPPED")));
        OrderRepositoryCustom custom = new OrderRepositoryImpl(db);

        custom.bulkUpdateStatus("PENDING", "PROCESSING");
        for (Order o : db) System.out.println("Order " + o.id + ": " + o.status);
    }
}
```

How to run: `java CustomRepoLevel1.java`

`OrderRepositoryImpl` is plain, hand-written Java — no derived-query mechanism could express "update every row matching X to Y" as a single named method the way `bulkUpdateStatus` reads here; a real implementation would issue this as one `UPDATE` statement via `EntityManager`.

### Level 2 — Intermediate

Compose the custom fragment with a generated-style repository interface, matching the real `JpaRepository` + `OrderRepositoryCustom` combination.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

interface OrderRepositoryCustom { void bulkUpdateStatus(String from, String to); }

class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final List<Order> db;
    OrderRepositoryImpl(List<Order> db) { this.db = db; }
    public void bulkUpdateStatus(String from, String to) {
        for (Order o : db) if (o.status.equals(from)) o.status = to;
    }
}

// interface OrderRepository extends JpaRepository<Order, Long>, OrderRepositoryCustom { }
// Simulated "generated" half (save/findById) plus the custom half, composed into one class.
class OrderRepository implements OrderRepositoryCustom {
    private final List<Order> db;
    private final OrderRepositoryCustom custom;
    OrderRepository(List<Order> db) { this.db = db; this.custom = new OrderRepositoryImpl(db); }

    // "generated" method
    Optional<Order> findById(long id) { return db.stream().filter(o -> o.id == id).findFirst(); }

    // delegates to the custom fragment -- callers see ONE repository, not two
    public void bulkUpdateStatus(String from, String to) { custom.bulkUpdateStatus(from, to); }
}

public class CustomRepoLevel2 {
    public static void main(String[] args) {
        List<Order> db = new ArrayList<>(List.of(new Order(1, "PENDING"), new Order(2, "PENDING"), new Order(3, "SHIPPED")));
        OrderRepository repo = new OrderRepository(db);

        System.out.println("Before: " + repo.findById(1L).orElseThrow().status);
        repo.bulkUpdateStatus("PENDING", "PROCESSING"); // custom fragment method, called on the SAME repo
        System.out.println("After: " + repo.findById(1L).orElseThrow().status);
    }
}
```

How to run: `java CustomRepoLevel2.java`

`repo.findById(...)` (standing in for a `JpaRepository`-generated method) and `repo.bulkUpdateStatus(...)` (the hand-written custom fragment) are both called on the *same* `repo` object — application code never needs to know that one is generated and the other is hand-implemented; Spring Data's real composition (via the `Impl`-suffix naming convention) hides that distinction the same way.

### Level 3 — Advanced

Add a custom method that genuinely needs imperative logic no declarative query could express: a batched bulk update that processes orders in chunks and reports progress, matching how a custom implementation might use direct `EntityManager` control (flush/clear per batch) to avoid loading everything into memory at once.

```java
import java.util.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

interface OrderRepositoryCustom {
    void bulkUpdateStatus(String from, String to);
    int bulkUpdateStatusBatched(String from, String to, int batchSize, IntConsumer onBatchDone);
}

class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final List<Order> db;
    OrderRepositoryImpl(List<Order> db) { this.db = db; }

    public void bulkUpdateStatus(String from, String to) {
        for (Order o : db) if (o.status.equals(from)) o.status = to;
    }

    // No single JPQL/derived query can express "process in batches of N, flushing/reporting after each" --
    // this needs imperative control, which is exactly what a custom implementation is for.
    public int bulkUpdateStatusBatched(String from, String to, int batchSize, IntConsumer onBatchDone) {
        List<Order> matching = db.stream().filter(o -> o.status.equals(from)).toList();
        int updated = 0;
        for (int i = 0; i < matching.size(); i += batchSize) {
            List<Order> batch = matching.subList(i, Math.min(i + batchSize, matching.size()));
            for (Order o : batch) o.status = to;
            updated += batch.size();
            onBatchDone.accept(updated); // e.g., report progress, or em.flush()+em.clear() in a real impl
        }
        return updated;
    }
}

class OrderRepository implements OrderRepositoryCustom {
    private final OrderRepositoryCustom custom;
    private final List<Order> db;
    OrderRepository(List<Order> db) { this.db = db; this.custom = new OrderRepositoryImpl(db); }

    public void bulkUpdateStatus(String from, String to) { custom.bulkUpdateStatus(from, to); }
    public int bulkUpdateStatusBatched(String from, String to, int batchSize, IntConsumer onBatchDone) {
        return custom.bulkUpdateStatusBatched(from, to, batchSize, onBatchDone);
    }
}

public class CustomRepoLevel3 {
    public static void main(String[] args) {
        List<Order> db = new ArrayList<>();
        for (int i = 1; i <= 25; i++) db.add(new Order(i, "PENDING"));
        OrderRepository repo = new OrderRepository(db);

        int total = repo.bulkUpdateStatusBatched("PENDING", "PROCESSING", 10,
            progress -> System.out.println("  ...batch done, " + progress + " orders updated so far"));

        System.out.println("Total updated: " + total);
    }
}
```

How to run: `java CustomRepoLevel3.java`

`bulkUpdateStatusBatched` processes the 25 matching orders in 3 batches of 10, 10, and 5, invoking `onBatchDone` after each — logic no single derived query or `@Query` string could express, because it requires imperative control over batch boundaries and per-batch side effects (in a real implementation, typically `entityManager.flush()` + `entityManager.clear()` between batches to keep the persistence context from growing unbounded during a large bulk operation).

## 6. Walkthrough

Execution starts in `main` for Level 3. First, 25 `Order` objects (IDs 1–25) are created, all with `status="PENDING"`, and wrapped in `repo`.

`repo.bulkUpdateStatusBatched("PENDING", "PROCESSING", 10, progress -> ...)` is called, delegating to `custom.bulkUpdateStatusBatched(...)` on the underlying `OrderRepositoryImpl`. Inside, `matching` collects all 25 `PENDING` orders. The loop then steps through in strides of 10: the first iteration takes `matching.subList(0, 10)`, flips those 10 orders' status to `"PROCESSING"`, adds 10 to `updated` (now 10), and calls `onBatchDone.accept(10)` — printing "...batch done, 10 orders updated so far". The second iteration handles orders 11–20 the same way, `updated` becomes 20, printing the progress. The third iteration handles the remaining 5 orders (21–25), `updated` becomes 25, printing the final progress line.

The loop ends (`i` now exceeds `matching.size()`), and `bulkUpdateStatusBatched` returns `25`. Back in `main`, "Total updated: 25" is printed.

```
matching = [order1..order25] (all PENDING)
batch 1: orders[0..10)  -> status=PROCESSING, updated=10 -> onBatchDone(10)
batch 2: orders[10..20) -> status=PROCESSING, updated=20 -> onBatchDone(20)
batch 3: orders[20..25) -> status=PROCESSING, updated=25 -> onBatchDone(25)
return 25
```

In a real Spring Data JPA application, `OrderRepositoryImpl.bulkUpdateStatusBatched` would use an injected `EntityManager` directly: fetch matching orders in pages (e.g., via `entityManager.createQuery(...).setFirstResult(...).setMaxResults(batchSize)`), mutate each batch's managed entities (relying on dirty checking from the persistence-context card to generate the `UPDATE`s), then call `entityManager.flush()` followed by `entityManager.clear()` after each batch — flushing pending changes to the database and detaching the batch's entities so the persistence context doesn't accumulate 25 (or 25 million) managed entities in memory over the course of one large operation. Application code calling `orderRepository.bulkUpdateStatusBatched(...)` never needs to know any of this happens — it's just another method on the same `OrderRepository` it already injects.

## 7. Gotchas & takeaways

> Gotcha: the custom implementation class must be named exactly `<RepositoryInterfaceName>Impl` (matching Spring Data's default naming convention) or it won't be found automatically — a typo in the suffix, or forgetting it entirely, causes a startup failure complaining that no bean implements the custom interface's methods.

- Custom implementations are the escape hatch for logic that no derived query, `@Query`, or `@Procedure` can express declaratively.
- The pattern is always three pieces: a plain custom interface, an `Impl`-suffixed class implementing it (with direct `EntityManager` access if needed), and the main repository interface extending both `JpaRepository` and the custom interface.
- Spring Data finds the implementation purely by naming convention — no explicit registration is required, but the suffix must match exactly.
- Callers never see the seam between generated and hand-written methods — both live on the same injected repository bean.
