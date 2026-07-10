---
card: spring-data
gi: 49
slug: query-with-native-sql-nativequery-true
title: "@Query with native SQL (nativeQuery=true)"
---

## 1. What it is

`@Query(value = "...", nativeQuery = true)` sends the query string directly to the database as raw SQL, bypassing JPQL translation entirely — necessary for database-specific functions (window functions, full-text search, JSON column operators), performance-tuning hints, or any SQL construct JPQL simply has no equivalent for. This card covers native queries' specific mechanics: result mapping (automatic for entity types, requiring `@SqlResultSetMapping` for arbitrary shapes), pagination support, and the portability tradeoff this escape hatch always carries.

```java
@Query(value = "SELECT * FROM orders WHERE EXTRACT(DOW FROM placed_at) = 0", nativeQuery = true)
List<Order> findSundayOrders(); // PostgreSQL-specific EXTRACT(DOW ...) -- no JPQL equivalent
```

## 2. Why & when

The previous card demonstrated JPQL's real depth — subqueries, `CASE`, aggregates — covering far more than simple property filters. Native SQL exists for the genuine remainder: constructs tied to a specific database's SQL dialect that JPQL, being database-agnostic by design, deliberately doesn't support. Reaching for it is a real tradeoff: full access to the database's actual capabilities, at the cost of the query no longer being portable to a different database vendor.

Reach for `nativeQuery = true` specifically when:

- You need a database-specific function or operator — PostgreSQL's JSON operators, a database-specific date/time function, a full-text search construct — that has no JPQL equivalent.
- You're tuning a specific query's performance using database-specific hints or query plan directives that only make sense in raw SQL.
- You're working with an existing, complex piece of hand-tuned SQL (perhaps migrated from a legacy system) and want to expose it through a Spring Data repository method without rewriting it in JPQL, when a rewrite is impractical or would lose database-specific optimizations.

## 3. Core concept

```
 @Query(value = "SELECT * FROM orders WHERE total > ?1", nativeQuery = true)
 List<Order> findLargeOrders(double minTotal);
        |
        v
 sent DIRECTLY to the database -- no JPQL parsing/translation at all

 RESULT MAPPING:
   "SELECT * FROM orders ..." (matches the entity's columns exactly)
        -> automatically mapped to Order entities

   "SELECT status, COUNT(*) FROM orders GROUP BY status" (arbitrary shape)
        -> requires either:
             a) an interface/DTO projection (works for native queries too), or
             b) an explicit @SqlResultSetMapping for complex custom mapping

 PAGINATION: native queries support Pageable, but require a SEPARATE,
   explicit countQuery attribute, since Spring Data cannot automatically
   derive a count query from arbitrary native SQL the way it can for JPQL:

   @Query(value = "SELECT * FROM orders WHERE total > ?1",
          countQuery = "SELECT COUNT(*) FROM orders WHERE total > ?1",
          nativeQuery = true)
   Page<Order> findLargeOrders(double minTotal, Pageable pageable);
```

Native queries lose JPQL's automatic query-derivation conveniences (automatic count-query generation for paging, in particular) exactly because Spring Data can't parse arbitrary SQL the way it can parse its own JPQL.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="nativeQuery=true sends SQL directly to the database, bypassing JPQL translation, at the cost of losing automatic pagination count-query derivation">
  <rect x="10" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Query("select o from Order o...")</text>
  <text x="145" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JPQL -- portable, auto count-query</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Query(nativeQuery=true)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">raw SQL -- DB-specific, needs countQuery</text>
</svg>

Native queries trade portability and automatic conveniences for full access to the database's real SQL dialect.

## 5. Runnable example

The scenario: an order-analytics repository, evolving from a basic native query with automatic entity mapping, to a projection-mapped aggregate native query, to native-query pagination with an explicit `countQuery`.

### Level 1 — Basic

Write a native query whose `SELECT *` matches the entity's columns, confirming automatic entity mapping still works.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class NativeQueryLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query(value = "SELECT * FROM \"order\" WHERE total > ?1", nativeQuery = true)
        List<Order> findLargeOrders(double minTotal);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NativeQueryLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:native1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(10.0));
        repo.save(new Order(100.0));
        repo.save(new Order(200.0));

        List<Order> large = repo.findLargeOrders(50.0);
        System.out.println("large orders (native SQL) = " + large.stream().map(Order::getTotal).toList());

        if (large.size() != 2) throw new AssertionError("Expected 2 orders over 50.0");
        System.out.println("Native SQL with automatic entity mapping worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java NativeQueryLevel1.java` on JDK 17+.

`@Query(value = "SELECT * FROM \"order\" WHERE total > ?1", nativeQuery = true)` sends genuine SQL to H2, referencing the actual table name (`"order"`, quoted since it's a SQL reserved word) rather than the JPQL entity name — since the `SELECT *` returns exactly the columns `Order` maps to, Hibernate automatically maps each row back into a full `Order` entity, no explicit result mapping needed.

### Level 2 — Intermediate

Write a native aggregate query and map its results to a DTO projection — the same projection technique from earlier cards, working identically for native queries.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class NativeQueryLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
    }

    // An interface projection -- works for native query result mapping too.
    public interface StatusSummary {
        String getStatus();
        Long getOrderCount();
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query(value = "SELECT status AS status, COUNT(*) AS order_count FROM \"order\" GROUP BY status",
               nativeQuery = true)
        List<StatusSummary> summarizeByStatus();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NativeQueryLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:native2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 100.0));
        repo.save(new Order("shipped", 50.0));
        repo.save(new Order("pending", 30.0));

        List<StatusSummary> summaries = repo.summarizeByStatus();
        summaries.forEach(s -> System.out.println(s.getStatus() + ": " + s.getOrderCount()));

        boolean shippedCorrect = summaries.stream().anyMatch(s -> s.getStatus().equals("shipped") && s.getOrderCount() == 2);
        if (!shippedCorrect) throw new AssertionError("Expected shipped count = 2");
        System.out.println("Native SQL aggregate mapped correctly to an interface projection -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java NativeQueryLevel2.java`.

`AS status` and `AS order_count` in the raw SQL alias the result columns to match `StatusSummary`'s getter-derived property names (`getStatus`/`getOrderCount`) — Spring Data's projection mapping works identically for native query results as it does for JPQL ones, matching result column labels against the projection interface's expected property names.

### Level 3 — Advanced

Add `Pageable`-based pagination to a native query, with the required explicit `countQuery`, confirming both the content and count queries execute correctly.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

@SpringBootApplication
public class NativeQueryLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query(value = "SELECT * FROM \"order\" WHERE total > ?1 ORDER BY total DESC",
               countQuery = "SELECT COUNT(*) FROM \"order\" WHERE total > ?1",
               nativeQuery = true)
        Page<Order> findLargeOrdersPaged(double minTotal, org.springframework.data.domain.Pageable pageable);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NativeQueryLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:native3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        for (int i = 1; i <= 10; i++) repo.save(new Order(i * 20.0));

        Page<Order> page = repo.findLargeOrdersPaged(50.0, PageRequest.of(0, 3));
        System.out.println("page content = " + page.getContent().stream().map(Order::getTotal).toList());
        System.out.println("total elements (from explicit countQuery) = " + page.getTotalElements());

        if (page.getContent().size() != 3) throw new AssertionError("Expected a page of 3");
        if (page.getTotalElements() != 8) throw new AssertionError("Expected 8 total orders over 50.0 (60,80,...,200)");

        System.out.println("Native query pagination with explicit countQuery worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java NativeQueryLevel3.java`.

The `countQuery` attribute supplies the SQL Spring Data uses to compute `getTotalElements()` — since it can't automatically derive a `COUNT` query from arbitrary native SQL the way it can from JPQL, this is mandatory for a paginated native query. Both queries share the same `?1` parameter binding (`minTotal`), and the content query's `ORDER BY total DESC` plus the page size/offset (handled automatically by Spring Data appending the appropriate `LIMIT`/`OFFSET` to the native SQL) together produce the correctly paginated, sorted result.

## 6. Walkthrough

Trace `repo.findLargeOrdersPaged(50.0, PageRequest.of(0, 3))`.

1. **Content query execution**: Spring Data takes the native SQL `SELECT * FROM "order" WHERE total > ?1 ORDER BY total DESC`, binds `50.0`, and appends pagination (`LIMIT 3 OFFSET 0`, H2's syntax) to fetch just page 0's 3 rows — the 3 highest-total orders among those exceeding 50.0.
2. **Count query execution**: separately, Spring Data executes the explicit `countQuery`, `SELECT COUNT(*) FROM "order" WHERE total > ?1`, with the same `50.0` binding, returning the total count of matching rows regardless of pagination — `8` (orders totaling 60 through 200, in steps of 20).
3. **`Page<Order>` assembly**: the 3 fetched rows plus the `8` total count are combined into the returned `Page<Order>`.
4. **Verification**: the program checks the page's content size (3, matching the requested page size) and the total element count (8, matching the explicit count query's independent computation), confirming both native queries — content and count — executed correctly and consistently with each other.

```
 findLargeOrdersPaged(50.0, page 0, size 3)
        |
        +-- content query:  SELECT * FROM "order" WHERE total>50.0 ORDER BY total DESC LIMIT 3
        |        -> 3 rows (the 3 highest)
        |
        +-- countQuery:     SELECT COUNT(*) FROM "order" WHERE total>50.0
        |        -> 8  (independently computed, same WHERE clause)
        |
        v
 Page<Order> { content: [3 rows], totalElements: 8 }
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting `countQuery` on a `Pageable`-accepting native query doesn't necessarily fail loudly at startup in every Spring Data version — behavior has varied (some versions throw immediately, others attempt an automatic, often-incorrect count-query derivation from the native SQL) — but relying on the automatic behavior for anything beyond the simplest native query is fragile. Always supply `countQuery` explicitly for any paginated native query, rather than hoping the automatic fallback happens to work.

- `nativeQuery = true` sends the query string directly to the database, unmediated by JPQL — full access to database-specific SQL, at the cost of losing portability to a different database vendor.
- Automatic entity-result mapping works for native queries whose `SELECT` shape matches the target entity's columns exactly — for any other shape (aggregates, computed values), use a projection interface/DTO (with column aliases matching the projection's expected property names) or an explicit `@SqlResultSetMapping`.
- Paginated native queries require an explicit `countQuery` attribute, since Spring Data cannot reliably derive a count query from arbitrary SQL the way it automatically does for JPQL.
- Reach for native SQL specifically for genuinely database-specific constructs — the previous card demonstrated JPQL alone covers subqueries, `CASE` expressions, and aggregate reporting, meaning many queries that seem to need native SQL don't actually require it.
