---
card: spring-data
gi: 20
slug: query-annotated-queries
title: "@Query annotated queries"
---

## 1. What it is

`@Query` lets a repository method declare its query explicitly — a JPQL string by default, or raw SQL with `nativeQuery = true` — rather than relying on name-derivation. It's the escape hatch every earlier card in this section has referenced: whenever a query needs a join, a subquery, an aggregate function, a computed value, or is simply too complex to name cleanly, `@Query` is where it goes, using the same method-parameter binding (positional `?1`, `?2`, or named `:paramName`) as derived queries.

```java
@Query("select o from Order o join o.customer c where c.email = :email and o.total > :minTotal")
List<Order> findLargeOrdersForCustomer(@Param("email") String email, @Param("minTotal") double minTotal);
```

## 2. Why & when

Query derivation covers the common case well, but plenty of real queries genuinely need more than property comparisons and `And`/`Or` combination — a join across three tables, a `GROUP BY` with `HAVING`, a computed expression, a database-specific function. `@Query` exists to express exactly these without abandoning the repository pattern — the method still looks like every other repository method to calling code, it just carries its query explicitly instead of having one derived.

Reach for `@Query` specifically when:

- A query needs a join, subquery, aggregate function (`COUNT`, `SUM`, `AVG` with `GROUP BY`), or any SQL/JPQL construct query derivation can't express through property-name naming alone.
- A derived method name would become long and hard to read — once a name accumulates more than two or three conditions, an explicit query, even if longer in raw character count, is usually easier to actually understand at a glance.
- You need a store-specific feature only expressible in native SQL (`nativeQuery = true`) — a database function, a hint, a construct with no JPQL equivalent.
- A query needs to modify data directly (`UPDATE`/`DELETE`) rather than select it — paired with `@Modifying`, `@Query` is how a repository method executes a bulk update or delete.

## 3. Core concept

```
 @Query("select o from Order o where o.status = :status")   -- JPQL (default)
 List<Order> findByStatusExplicit(@Param("status") String status);

 @Query(value = "SELECT * FROM orders WHERE total > ?1", nativeQuery = true)  -- raw SQL
 List<Order> findLargeOrdersNative(double minTotal);

 @Modifying                                                  -- REQUIRED for UPDATE/DELETE
 @Query("update Order o set o.status = :newStatus where o.status = :oldStatus")
 int bulkUpdateStatus(@Param("oldStatus") String oldStatus, @Param("newStatus") String newStatus);

 PARAMETER BINDING:
   Positional: ?1, ?2, ...      matches parameter DECLARATION ORDER
   Named:      :paramName        matches a @Param("paramName") annotation
                                  (or, with -parameters compiler flag, the
                                   actual parameter name -- named binding is
                                   generally preferred for readability)
```

`@Modifying` is mandatory alongside any `@Query` that performs an `UPDATE` or `DELETE` — without it, Spring Data assumes every `@Query` is a `SELECT` and will reject (or mishandle) a data-modifying statement.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Query derivation and @Query both implement the same repository method contract, differing in where the query comes from">
  <rect x="10" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByStatus(status)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">query DERIVED from the name</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Query("select o from ...")</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">query DECLARED explicitly</text>

  <rect x="150" y="110" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">both are called identically -- repo.methodName(args)</text>
</svg>

Callers can't tell whether a repository method's query was derived or declared — both look and behave identically from the outside.

## 5. Runnable example

The scenario: an order-analytics repository, evolving from a basic JPQL `@Query` with a join, to a native-SQL aggregate query, to a `@Modifying` bulk update — the three most common `@Query` use cases.

### Level 1 — Basic

Write a `@Query` with a join and named parameters, expressing something query derivation alone couldn't cleanly reach across two related entities.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

@SpringBootApplication
public class QueryAnnotationLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Customer() {}
        public Customer(String email) { this.email = email; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        @ManyToOne
        private Customer customer;
        private double total;
        protected Order() {}
        public Order(Customer customer, double total) { this.customer = customer; this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query("select o from Order o join o.customer c where c.email = :email and o.total > :minTotal")
        List<Order> findLargeOrdersForCustomer(@Param("email") String email, @Param("minTotal") double minTotal);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryAnnotationLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:queryann1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        Customer ada = new Customer("ada@example.com");
        Customer grace = new Customer("grace@example.com");
        em.persist(ada); em.persist(grace);
        em.persist(new Order(ada, 150.0));
        em.persist(new Order(ada, 25.0)); // below threshold
        em.persist(new Order(grace, 200.0)); // different customer
        em.getTransaction().commit();
        em.close();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        List<Order> result = repo.findLargeOrdersForCustomer("ada@example.com", 50.0);
        System.out.println("Ada's orders over 50.0 = " + result.stream().map(Order::getTotal).toList());

        if (result.size() != 1 || result.get(0).getTotal() != 150.0)
            throw new AssertionError("Expected exactly Ada's one order over 50.0");
        System.out.println("@Query with a join and named parameters worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java QueryAnnotationLevel1.java` on JDK 17+.

`@Query("select o from Order o join o.customer c where c.email = :email and o.total > :minTotal")` explicitly joins `Order` to `Customer` and filters on both — a query derivation method name for this (`findByCustomerEmailAndTotalGreaterThan`) would actually work here too (it's not *that* complex), but this establishes the `@Query` mechanics before more genuinely derivation-resistant queries follow. `:email`/`:minTotal` named parameters, bound via `@Param`, map directly to the method's arguments regardless of their declaration order.

### Level 2 — Intermediate

Use `nativeQuery = true` for a raw SQL aggregate query — a `GROUP BY`/`HAVING` combination genuinely outside what query derivation can express.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class QueryAnnotationLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String customerEmail;
        private double total;
        protected Order() {}
        public Order(String customerEmail, double total) { this.customerEmail = customerEmail; this.total = total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // Native SQL: aggregate customers whose TOTAL spend exceeds a threshold.
        @Query(value = "SELECT customer_email FROM orders GROUP BY customer_email HAVING SUM(total) > ?1", nativeQuery = true)
        List<String> findBigSpenders(double totalThreshold);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryAnnotationLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:queryann2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("ada@example.com", 100.0));
        repo.save(new Order("ada@example.com", 150.0));   // Ada total: 250.0
        repo.save(new Order("grace@example.com", 50.0));  // Grace total: 50.0

        List<String> bigSpenders = repo.findBigSpenders(200.0);
        System.out.println("big spenders (total > 200): " + bigSpenders);

        if (bigSpenders.size() != 1 || !bigSpenders.get(0).equals("ada@example.com"))
            throw new AssertionError("Expected only ada@example.com to exceed the 200.0 total threshold");
        System.out.println("Native SQL @Query with GROUP BY/HAVING worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java QueryAnnotationLevel2.java`.

`nativeQuery = true` tells Spring Data to send `value` directly to the database as raw SQL, bypassing JPQL translation entirely — `GROUP BY customer_email HAVING SUM(total) > ?1` is a genuinely aggregate query, something query derivation's per-row property matching has no way to express. The positional `?1` binds to the method's single `totalThreshold` parameter.

### Level 3 — Advanced

Use `@Modifying` with `@Query` to perform a bulk `UPDATE`, and combine it with `clearAutomatically`/`flushAutomatically` to keep the persistence context consistent with the database after a bulk change — a realistic production concern with bulk JPA updates.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@SpringBootApplication
public class QueryAnnotationLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
        public Long getId() { return id; }
        public String getStatus() { return status; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Modifying(clearAutomatically = true) // clears the persistence context after the bulk update
        @Query("update Order o set o.status = :newStatus where o.status = :oldStatus")
        int bulkUpdateStatus(@Param("oldStatus") String oldStatus, @Param("newStatus") String newStatus);
    }

    @Component
    public static class OrderMigrationService {
        private final OrderRepository repo;
        public OrderMigrationService(OrderRepository repo) { this.repo = repo; }

        @Transactional
        public int migratePendingToProcessing() {
            int updatedCount = repo.bulkUpdateStatus("pending", "processing");
            // clearAutomatically=true means a fresh findById here reflects the bulk update,
            // rather than returning a stale, cached "pending" entity from before the bulk change.
            Order reloaded = repo.findById(1L).orElseThrow();
            System.out.println("first order's status immediately after bulk update, reloaded: " + reloaded.getStatus());
            return updatedCount;
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryAnnotationLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:queryann3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("pending"));
        repo.save(new Order("pending"));
        repo.save(new Order("shipped"));

        OrderMigrationService service = ctx.getBean(OrderMigrationService.class);
        int updated = service.migratePendingToProcessing();

        List<Order> stillPending = repo.findAll().stream().filter(o -> o.getStatus().equals("pending")).toList();
        System.out.println("bulk update affected " + updated + " rows; remaining 'pending' orders = " + stillPending.size());

        if (updated != 2) throw new AssertionError("Expected exactly 2 orders updated from pending to processing");
        if (!stillPending.isEmpty()) throw new AssertionError("Expected no orders left in 'pending' status");
        System.out.println("@Modifying bulk update + clearAutomatically kept the persistence context consistent -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java QueryAnnotationLevel3.java`.

`@Modifying` is required for `@Query`-annotated `UPDATE`/`DELETE` statements — without it, Spring Data would reject this method or attempt to treat it as a `SELECT`. The method returns `int`, the count of rows affected, exactly like JDBC's `executeUpdate()`. `clearAutomatically = true` clears Hibernate's first-level cache (persistence context) immediately after the bulk update executes — critical because a bulk JPQL `UPDATE` bypasses the persistence context entirely (it goes straight to the database), so without clearing, a subsequent `findById` could return a stale, cached entity still showing the old `"pending"` status even though the database itself was already updated.

## 6. Walkthrough

Trace Level 3's `migratePendingToProcessing()` call.

1. **`@Transactional` begins**: `OrderMigrationService.migratePendingToProcessing()` starts a database transaction, within which both the bulk update and the reload will occur.
2. **`repo.bulkUpdateStatus("pending", "processing")`**: Spring Data executes the declared JPQL `UPDATE Order o SET o.status = 'processing' WHERE o.status = 'pending'` directly against the database — this is a bulk statement operating on rows, not on any in-memory `Order` objects; Hibernate's persistence context (which might be holding onto earlier-loaded `Order` entities with their old `status` values) is completely bypassed by this operation.
3. **`clearAutomatically = true` takes effect**: immediately after the bulk update executes, Spring Data calls `EntityManager.clear()`, detaching every entity the persistence context was tracking — this is what prevents the next read from returning stale, cached data.
4. **`repo.findById(1L)`**: because the persistence context was just cleared, this issues a genuinely fresh `SELECT` against the database (rather than returning a cached, pre-update `Order` instance), correctly retrieving the row with its now-updated `"processing"` status.
5. **Method returns**: `bulkUpdateStatus` returned `2` (the count of rows the `UPDATE` actually affected — the two `"pending"` orders; the `"shipped"` one was untouched, since it didn't match the `WHERE` clause).
6. **`main` verification**: filters the full order list for any remaining `"pending"` status orders — finding none, confirming the bulk update actually took effect at the database level (not just returned a count) — and checks the returned count matches the expected `2`.

```
 bulkUpdateStatus("pending", "processing")
        |
        v
 UPDATE order SET status='processing' WHERE status='pending'   (bypasses persistence context entirely)
        |
        v
 clearAutomatically=true --> EntityManager.clear()  (drops any stale cached entities)
        |
        v
 findById(1L)  --> FRESH SELECT --> sees status='processing', not stale 'pending'
```

## 7. Gotchas & takeaways

> **Gotcha:** a bulk `@Modifying` `UPDATE`/`DELETE` operates directly against the database and does *not* trigger JPA entity lifecycle callbacks (`@PreUpdate`, `@PostUpdate`, and similar) or cascade to related entities the way saving individual entities through the persistence context would — if application logic depends on those callbacks firing (auditing, cache invalidation tied to entity events), a bulk `@Modifying` query silently skips them, which can be a subtle and hard-to-diagnose correctness gap.

- `@Query` is the explicit-query escape hatch for anything query derivation can't cleanly express — joins, aggregates, native SQL, and bulk modifications all go through it.
- Named parameters (`:paramName` with `@Param`) are generally preferable to positional ones (`?1`, `?2`) for readability, especially as a query's parameter count grows — the binding is explicit and doesn't depend on remembering declaration order.
- `nativeQuery = true` sends the query string straight to the database, unmediated by JPQL — necessary for database-specific functions or constructs, at the cost of losing JPQL's portability across different relational databases.
- `@Modifying` is mandatory for any `@Query` performing `UPDATE`/`DELETE`, and `clearAutomatically`/`flushAutomatically` are important companions for keeping the persistence context consistent with a database state that was changed in bulk, bypassing normal entity-tracking.
