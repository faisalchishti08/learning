---
card: spring-data
gi: 53
slug: modifying-queries-modifying
title: "Modifying queries (@Modifying)"
---

## 1. What it is

This card goes deeper on `@Modifying` (introduced briefly in an earlier Commons-section card) — specifically its return-type options (`void`, or `int`/`long` reporting the affected-row count), the mandatory `@Transactional` requirement, and its two companion flush-management attributes, `flushAutomatically` and `clearAutomatically`, examined together rather than in isolation.

```java
@Modifying
@Transactional
@Query("update Order o set o.status = :status where o.id = :id")
int updateStatus(@Param("id") Long id, @Param("status") String status);
```

## 2. Why & when

The earlier card established that `@Modifying` is required for any `@Query` performing `UPDATE`/`DELETE`, and that `clearAutomatically` clears the persistence context afterward. This card fills in the surrounding practical details: `@Modifying` methods genuinely need an active transaction (unlike read-only queries, which Spring Data wraps in a default read-only transaction automatically), and choosing the right combination of `flushAutomatically`/`clearAutomatically` prevents two distinct, easy-to-hit consistency bugs — reading stale data from the persistence context after a bulk update, and a bulk update silently missing changes still pending in the persistence context.

Understanding `@Modifying`'s full attribute surface matters specifically when:

- You're writing a bulk update/delete and need to decide whether the caller's subsequent reads (within the same transaction) should see fresh data (`clearAutomatically = true`) or whether performance matters more than that immediate consistency.
- You're combining a bulk `@Modifying` update with prior, still-unflushed entity changes in the same transaction and need `flushAutomatically = true` to ensure those pending changes are written to the database *before* the bulk update runs (since the bulk update bypasses the persistence context and could otherwise miss or conflict with pending in-memory changes).
- You're deciding whether a `@Modifying` method should return `void` or an `int`/`long` — the affected-row count is often valuable for confirming how many rows an operation actually touched, especially useful in tests or audit logging.

## 3. Core concept

```
 @Modifying                              -- REQUIRED for @Query UPDATE/DELETE
 @Transactional                          -- REQUIRED -- a modifying query needs
                                             a genuine (non-read-only) transaction
 @Query("update Order o set ...")
 int bulkUpdate(...);                     -- int/long return = rows affected;
                                              void is also valid if the count
                                              genuinely isn't needed

 flushAutomatically = true   (default: false)
   -- flushes PENDING, unflushed entity changes to the DATABASE
      BEFORE the bulk update/delete statement runs
   -- prevents the bulk operation from missing/conflicting with
      changes still sitting in the persistence context

 clearAutomatically = true   (default: false)
   -- clears the persistence context's first-level cache AFTER the
      bulk update/delete runs
   -- prevents SUBSEQUENT reads (in the same transaction) from
      returning STALE, pre-update cached entity data
```

`flushAutomatically` addresses consistency *before* the bulk operation; `clearAutomatically` addresses consistency *after* it — two independent concerns, both defaulting to `false`, both worth setting deliberately based on what a given bulk operation actually needs.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="flushAutomatically writes pending changes before the bulk update runs, clearAutomatically clears stale cached data after it runs">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">flushAutomatically</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BEFORE the bulk op</text>

  <rect x="230" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bulk UPDATE/DELETE</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bypasses persistence context</text>

  <rect x="450" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">clearAutomatically</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AFTER the bulk op</text>

  <line x1="200" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="47" x2="445" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two independent flush-management knobs, bracketing the bulk operation on either side.

## 5. Runnable example

The scenario: an order-status bulk update, evolving from confirming `@Modifying` requires `@Transactional` to even function, to `flushAutomatically` preventing a missed pending change, to `clearAutomatically` preventing a stale read afterward.

### Level 1 — Basic

Confirm a `@Modifying` method's return value correctly reports the number of affected rows.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

@SpringBootApplication
public class ModifyingLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Modifying
        @Transactional
        @Query("update Order o set o.status = :newStatus where o.status = :oldStatus")
        int bulkUpdateStatus(@Param("oldStatus") String oldStatus, @Param("newStatus") String newStatus);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ModifyingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:modifying1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("pending"));
        repo.save(new Order("pending"));
        repo.save(new Order("shipped"));

        int affected = repo.bulkUpdateStatus("pending", "processing");
        System.out.println("rows affected = " + affected);

        if (affected != 2) throw new AssertionError("Expected exactly 2 rows to be affected");
        System.out.println("@Modifying's int return value correctly reported the affected-row count -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ModifyingLevel1.java` on JDK 17+.

`bulkUpdateStatus` returns `int`, and the returned value correctly reports `2` — the exact number of rows matching `WHERE status = 'pending'`, which is exactly what the underlying JDBC `executeUpdate()` call (which Hibernate's bulk-update execution delegates to) reports.

### Level 2 — Intermediate

Demonstrate `flushAutomatically`'s purpose: without it, a pending (unflushed) entity change in the same transaction can be missed by a subsequent bulk update.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@SpringBootApplication
public class ModifyingLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // flushAutomatically = true: flush pending changes BEFORE this bulk update runs.
        @Modifying(flushAutomatically = true)
        @Transactional
        @Query("update Order o set o.status = 'archived' where o.status = 'pending'")
        int archivePendingOrders();
    }

    @Component
    public static class OrderService {
        private final OrderRepository repo;
        public OrderService(OrderRepository repo) { this.repo = repo; }

        @Transactional
        public int changeStatusThenArchive(Long orderId) {
            Order order = repo.findById(orderId).orElseThrow();
            order.setStatus("pending"); // a PENDING, unflushed change within this transaction
            // NOTE: repo.save(order) is not even called here -- Hibernate's dirty-checking
            // will pick up this change automatically at the next flush point.
            return repo.archivePendingOrders(); // flushAutomatically=true ensures the change above is seen
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ModifyingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:modifying2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order("shipped")); // starts as "shipped", not "pending"

        OrderService service = ctx.getBean(OrderService.class);
        int archivedCount = service.changeStatusThenArchive(saved.getId());

        System.out.println("archived count = " + archivedCount);

        if (archivedCount != 1)
            throw new AssertionError("Expected flushAutomatically to make the bulk update see the pending in-memory status change");
        System.out.println("flushAutomatically ensured the pending change was visible to the bulk update -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ModifyingLevel2.java`.

`order.setStatus("pending")` modifies the entity in memory, but this change hasn't been flushed to the database yet — Hibernate's dirty-checking would normally write it at the next natural flush point (often transaction commit). Without `flushAutomatically`, `archivePendingOrders()`'s bulk `UPDATE ... WHERE status = 'pending'` (which bypasses the persistence context entirely, querying the database's *current* state) could run *before* that pending change is actually written, missing this order entirely. `flushAutomatically = true` forces the pending change to be flushed first, ensuring the bulk update genuinely sees it.

### Level 3 — Advanced

Demonstrate `clearAutomatically`'s purpose: without it, a subsequent read within the same transaction can return stale, pre-update cached data instead of the bulk update's actual effect.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@SpringBootApplication
public class ModifyingLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
        public String getStatus() { return status; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Modifying(clearAutomatically = true) // clears the persistence context AFTER the bulk update
        @Transactional
        @Query("update Order o set o.status = 'processing' where o.id = :id")
        int markProcessing(@Param("id") Long id);
    }

    @Component
    public static class OrderService {
        private final OrderRepository repo;
        public OrderService(OrderRepository repo) { this.repo = repo; }

        @Transactional
        public String loadUpdateThenReload(Long orderId) {
            Order beforeUpdate = repo.findById(orderId).orElseThrow(); // loads + caches "pending" in the persistence context
            repo.markProcessing(orderId); // bulk update bypasses the cache; clearAutomatically clears it afterward
            Order afterUpdate = repo.findById(orderId).orElseThrow(); // WITHOUT clearAutomatically, this could return the STALE cached "pending" instance
            return "before=" + beforeUpdate.getStatus() + ", after=" + afterUpdate.getStatus();
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ModifyingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:modifying3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order("pending"));

        OrderService service = ctx.getBean(OrderService.class);
        String result = service.loadUpdateThenReload(saved.getId());

        System.out.println(result);

        if (!result.equals("before=pending, after=processing"))
            throw new AssertionError("Expected clearAutomatically to make the second read see the FRESH, updated status");
        System.out.println("clearAutomatically ensured the subsequent read saw fresh data, not a stale cached entity -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java ModifyingLevel3.java`.

The first `findById` loads and caches the `Order` (status `"pending"`) into the persistence context's first-level cache. `markProcessing`'s bulk `UPDATE` runs directly against the database, bypassing that cache — without `clearAutomatically`, a second `findById` for the *same id, within the same transaction/persistence context* would typically return the same cached Java object from the first load (still showing `"pending"`), rather than reflecting the database's actual, now-updated `"processing"` state. `clearAutomatically = true` clears that cache immediately after the bulk update, forcing the second `findById` to issue a genuinely fresh `SELECT`, correctly returning `"processing"`.

## 6. Walkthrough

Trace Level 3's `loadUpdateThenReload` call.

1. **`repo.findById(orderId)` (first call)**: loads the `Order` row, status `"pending"`, into a managed entity instance — the persistence context's first-level cache now holds this exact instance, keyed by its id.
2. **`repo.markProcessing(orderId)`**: executes the declared JPQL `UPDATE Order o SET o.status = 'processing' WHERE o.id = :id` directly against the database — this SQL statement has no awareness of, and doesn't touch, the cached Java `Order` instance from step 1 at all.
3. **`clearAutomatically = true` takes effect**: immediately after the bulk update executes, Spring Data calls `EntityManager.clear()`, detaching every entity the persistence context was tracking — including the `"pending"`-status instance from step 1.
4. **`repo.findById(orderId)` (second call)**: because the persistence context was just cleared, there's no cached instance to return — this genuinely issues a fresh `SELECT` against the database, correctly retrieving the row with its now-updated `"processing"` status.
5. **Result assembly**: `beforeUpdate.getStatus()` still reports `"pending"` (that specific, separate Java object was never mutated — it simply reflects the state at the moment it was loaded), while `afterUpdate.getStatus()` correctly reports `"processing"`, since it's a freshly-loaded instance reflecting the database's current state.
6. **Verification**: the program checks the combined "before=pending, after=processing" string, confirming both objects show the correct, expected states — the first frozen at its load time, the second freshly reflecting the bulk update's actual effect.

```
 findById(id)   -->  cached Order{status="pending"}   (persistence context now holds this)
        |
 markProcessing(id)  -->  UPDATE bypasses the cache -->  database now has status="processing"
        |
 clearAutomatically=true  -->  persistence context CLEARED
        |
        v
 findById(id)   -->  NO cache hit -->  FRESH SELECT  -->  Order{status="processing"}
```

## 7. Gotchas & takeaways

> **Gotcha:** `@Modifying` methods genuinely require an active, non-read-only transaction — Spring Data's default behavior for plain query methods wraps them in an implicit read-only transaction (an optimization), but a read-only transaction cannot execute an `UPDATE`/`DELETE`. This is exactly why `@Transactional` (without `readOnly = true`) is mandatory on every `@Modifying` method — omitting it typically produces a runtime error about attempting to modify data in a read-only transaction, or in some configurations, simply fails to execute the modification at all.

- `@Modifying` methods can return `void`, or `int`/`long` reporting the number of affected rows — the count is genuinely useful for confirming an operation's actual scope, especially in tests, audit logs, or conditional logic based on whether anything was actually changed.
- `@Transactional` (a real, writable transaction, not read-only) is mandatory on every `@Modifying` method — this is a hard requirement, not merely a best practice, since the underlying bulk SQL statement cannot execute within a read-only transaction.
- `flushAutomatically = true` flushes any pending, unflushed entity changes to the database *before* the bulk operation runs, preventing the bulk operation from missing changes still sitting only in the persistence context.
- `clearAutomatically = true` clears the persistence context's cache *after* the bulk operation runs, preventing subsequent reads within the same transaction from returning stale, pre-update cached entity data — both attributes default to `false` and should be set deliberately based on what each specific bulk operation's surrounding code actually needs.
