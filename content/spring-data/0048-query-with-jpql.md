---
card: spring-data
gi: 48
slug: query-with-jpql
title: "@Query with JPQL"
---

## 1. What it is

This card goes deeper on JPQL itself — the query language `@Query` uses by default (covered generally in the Commons section) — specifically its object-oriented character: JPQL queries entities and their properties, not tables and columns, supports polymorphic queries across an inheritance hierarchy, and includes aggregate functions, subqueries, and `CASE` expressions with syntax deliberately close to SQL but operating on the entity object graph rather than raw relational structure.

```java
@Query("select o from Order o where o.total > (select avg(o2.total) from Order o2)")
List<Order> findAboveAverageOrders();
```

## 2. Why & when

Earlier cards used `@Query` for joins and simple filters — this card covers JPQL's more advanced capabilities: subqueries (a query embedded inside another, as above), `CASE` expressions for computed categorization, and aggregate functions with `GROUP BY`/`HAVING`. Knowing JPQL's actual capability surface changes the earlier query-derivation-versus-`@Query` decision: many queries that seem to require dropping to native SQL are actually expressible in portable, object-oriented JPQL.

Reach for these deeper JPQL features specifically when:

- A query needs to compare against an aggregate of the same or a related table (above-average, below-median) — a JPQL subquery expresses this directly, without needing two separate queries in application code.
- A query needs computed categorization based on a value's range or condition — a `CASE` expression inside the `SELECT` clause handles this in the database, rather than fetching raw values and categorizing them in Java.
- You want aggregate reporting (counts, sums, averages grouped by a category) expressed portably — JPQL's `GROUP BY`/`HAVING` work the same way across any JPA-supported database, unlike native SQL's occasionally database-specific aggregate syntax.

## 3. Core concept

```
 SUBQUERY:
   select o from Order o where o.total > (select avg(o2.total) from Order o2)
   -- the parenthesized subquery computes ONE value (the average),
      compared against each outer row's total

 CASE expression:
   select o.id, case when o.total > 100 then 'LARGE' else 'SMALL' end
   from Order o
   -- computed classification, done in the database, not in Java after fetching

 GROUP BY / HAVING (aggregate reporting):
   select o.status, count(o), sum(o.total) from Order o
   group by o.status having count(o) > 5
   -- portable aggregate reporting across ANY JPA-supported database
```

Every one of these constructs operates on entities and their properties (`o.total`, `o.status`) — JPQL never mentions a table or column name directly, keeping the query portable and abstracted from the underlying schema.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="JPQL supports subqueries, CASE expressions, and GROUP BY/HAVING, all operating on entities rather than raw tables">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Subquery</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compare against an aggregate</text>

  <rect x="230" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CASE expression</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">computed classification</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GROUP BY / HAVING</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">portable aggregate reports</text>
</svg>

Three JPQL capabilities that push far beyond simple property comparisons.

## 5. Runnable example

The scenario: order analytics, evolving from a subquery comparing against an average, to a `CASE`-based classification, to a full aggregate report with `GROUP BY`/`HAVING`.

### Level 1 — Basic

Find orders whose total exceeds the average total across all orders, using a JPQL subquery.

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
public class JpqlLevel1 {

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
        @Query("select o from Order o where o.total > (select avg(o2.total) from Order o2)")
        List<Order> findAboveAverageOrders();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpqlLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:jpql1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(10.0));
        repo.save(new Order(20.0));
        repo.save(new Order(90.0)); // average = (10+20+90)/3 = 40 -- only this one exceeds it

        List<Order> aboveAverage = repo.findAboveAverageOrders();
        System.out.println("above-average orders = " + aboveAverage.stream().map(Order::getTotal).toList());

        if (aboveAverage.size() != 1 || aboveAverage.get(0).getTotal() != 90.0)
            throw new AssertionError("Expected only the 90.0 order to exceed the average of 40.0");
        System.out.println("JPQL subquery correctly compared against a computed average -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java JpqlLevel1.java` on JDK 17+.

`(select avg(o2.total) from Order o2)` is a genuine subquery, computed once by the database and compared against each outer `o.total` — the average of `10.0`, `20.0`, `90.0` is `40.0`, so only the `90.0` order satisfies `o.total > 40.0`.

### Level 2 — Intermediate

Use a `CASE` expression to classify orders by size directly in the query, avoiding a separate Java-side classification step.

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
public class JpqlLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query("select case when o.total > 100 then 'LARGE' when o.total > 20 then 'MEDIUM' else 'SMALL' end "
             + "from Order o where o.id = :id")
        String classifyOrder(@org.springframework.data.repository.query.Param("id") Long id);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpqlLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:jpql2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order small = repo.save(new Order(10.0));
        Order medium = repo.save(new Order(50.0));
        Order large = repo.save(new Order(150.0));

        System.out.println("small=" + repo.classifyOrder(small.getId())
            + ", medium=" + repo.classifyOrder(medium.getId())
            + ", large=" + repo.classifyOrder(large.getId()));

        if (!"SMALL".equals(repo.classifyOrder(small.getId()))) throw new AssertionError("Expected SMALL for 10.0");
        if (!"MEDIUM".equals(repo.classifyOrder(medium.getId()))) throw new AssertionError("Expected MEDIUM for 50.0");
        if (!"LARGE".equals(repo.classifyOrder(large.getId()))) throw new AssertionError("Expected LARGE for 150.0");

        System.out.println("CASE expression classified orders directly in the database -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java JpqlLevel2.java`.

The `CASE WHEN ... THEN ... END` expression evaluates entirely within the query, returning a plain `String` classification — no raw `total` value is fetched into Java only to be classified afterward with `if`/`else` logic; the database itself computes and returns the final classification.

### Level 3 — Advanced

Build an aggregate report using `GROUP BY`/`HAVING`, combined with a constructor-expression DTO projection (from the earlier projections card) to return a clean, typed result.

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
public class JpqlLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
    }

    public record StatusReport(String status, long orderCount, double totalRevenue) {}

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query("select new JpqlLevel3$StatusReport(o.status, count(o), sum(o.total)) "
             + "from Order o group by o.status having count(o) >= 2")
        List<StatusReport> reportByStatus();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpqlLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:jpql3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 100.0));
        repo.save(new Order("shipped", 50.0));
        repo.save(new Order("cancelled", 20.0)); // only 1 cancelled -- excluded by HAVING count(o) >= 2
        repo.save(new Order("pending", 30.0));
        repo.save(new Order("pending", 70.0));

        List<StatusReport> report = repo.reportByStatus();
        report.forEach(r -> System.out.println(r.status() + ": " + r.orderCount() + " orders, $" + r.totalRevenue()));

        if (report.size() != 2) throw new AssertionError("Expected only 'shipped' and 'pending' (count>=2), excluding 'cancelled'");
        boolean shippedCorrect = report.stream().anyMatch(r -> r.status().equals("shipped") && r.orderCount() == 2 && r.totalRevenue() == 150.0);
        if (!shippedCorrect) throw new AssertionError("Expected shipped: 2 orders, $150.0 total");

        System.out.println("GROUP BY/HAVING aggregate report, mapped directly to a DTO -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java JpqlLevel3.java`.

`group by o.status having count(o) >= 2` computes per-status counts and sums, excluding any status group with fewer than 2 orders (here, `"cancelled"`, with only one) — and `select new JpqlLevel3$StatusReport(...)`, the constructor-expression projection technique from the earlier projections card, maps each aggregate row directly into a `StatusReport` record, avoiding any manual `Object[]` row unpacking in application code.

## 6. Walkthrough

Trace `repo.reportByStatus()`.

1. **Query execution**: Hibernate translates the JPQL into SQL with a `GROUP BY status HAVING COUNT(*) >= 2`, aggregating all 5 seeded orders by their `status` column.
2. **Grouping**: three groups form initially — `"shipped"` (2 orders, totals 100.0+50.0), `"cancelled"` (1 order, total 20.0), `"pending"` (2 orders, totals 30.0+70.0).
3. **`HAVING` filter**: applied *after* grouping (unlike `WHERE`, which would filter individual rows before grouping), it excludes the `"cancelled"` group since its count (1) is below the required 2 — leaving only `"shipped"` and `"pending"`.
4. **Constructor-expression mapping**: for each remaining group, `new JpqlLevel3$StatusReport(o.status, count(o), sum(o.total))` is evaluated, producing a real `StatusReport` instance directly — `("shipped", 2, 150.0)` and `("pending", 2, 100.0)`.
5. **Return value**: `List<StatusReport>`, exactly 2 entries, each already a fully-typed, ready-to-use record.
6. **Verification**: the program checks the report contains exactly 2 groups (confirming `HAVING` correctly excluded `"cancelled"`), and that the `"shipped"` group's count and revenue sum match the expected aggregated values.

```
 5 orders: shipped(100), shipped(50), cancelled(20), pending(30), pending(70)
        |
        v
 GROUP BY status: shipped{count=2,sum=150}, cancelled{count=1,sum=20}, pending{count=2,sum=100}
        |
        v
 HAVING count(o) >= 2  -->  cancelled EXCLUDED (count=1)
        |
        v
 List<StatusReport>: [("shipped",2,150.0), ("pending",2,100.0)]
```

## 7. Gotchas & takeaways

> **Gotcha:** `HAVING` filters *groups* (after aggregation), while `WHERE` filters individual *rows* (before aggregation) — mixing them up (using `WHERE count(o) >= 2`, for instance) produces a JPQL syntax or semantic error, since aggregate functions like `count(...)` are only meaningful in a context where grouping has already happened. When a condition depends on an aggregate value, it belongs in `HAVING`; when it depends on a raw row property, it belongs in `WHERE`.

- JPQL subqueries let a query compare against a computed aggregate (an average, a max, a count) without a separate round-trip or Java-side computation — the whole comparison happens in one database query.
- `CASE` expressions compute classifications or derived values directly within the query's `SELECT` clause, avoiding the need to fetch raw data and post-process it in application code.
- `GROUP BY`/`HAVING` provide portable aggregate reporting, working identically across every JPA-supported database — combined with constructor-expression DTO projections, an aggregate query can return clean, typed results directly.
- Many queries that seem to require native SQL are actually expressible in JPQL's object-oriented, portable syntax — reach for `nativeQuery = true` (covered in the next card) specifically for genuinely database-specific functions or constructs JPQL has no equivalent for.
