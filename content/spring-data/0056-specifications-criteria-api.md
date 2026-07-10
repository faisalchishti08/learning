---
card: spring-data
gi: 56
slug: specifications-criteria-api
title: "Specifications (Criteria API)"
---

## 1. What it is

This card goes deeper into the JPA Criteria API mechanics underlying `Specification<T>` (introduced earlier in this section) — specifically joins (`Root.join(...)`, producing a real SQL `JOIN` from within a `Specification`), subqueries (`CriteriaQuery.subquery(...)`, embedding a nested query), and the `CriteriaBuilder`'s full function surface (aggregate functions, `CASE` expressions, and more) — the same capabilities the earlier JPQL card demonstrated as raw query strings, expressed instead as type-checked (if verbosely so) Java method calls.

```java
Specification<Order> hasLineItemDescribing = (root, query, cb) -> {
    Join<Order, LineItem> items = root.join("lineItems");
    return cb.like(items.get("description"), "%urgent%");
};
```

## 2. Why & when

The earlier `Specification` card focused on composition (`.and()`/`.or()`) using simple, single-entity predicates — this card addresses the more advanced Criteria API constructs needed once a `Specification` needs to reach across relationships or express something beyond a flat property comparison. Understanding `Root.join(...)` and Criteria subqueries specifically closes the gap between "what a `Specification` can express" and "what a hand-written JPQL query string can express" (from the earlier JPQL card) — with the tradeoff that Criteria API code is generally more verbose, in exchange for it being ordinary, refactorable, composable Java rather than a string.

Reach for join- and subquery-capable Specifications specifically when:

- A dynamic filter needs to reach through a relationship — filtering orders by a property of their line items, or customers by a property of their orders — the same kind of traversal a JPQL `JOIN` clause would express, but built programmatically and composably.
- A dynamic filter needs to compare against an aggregate or a computed subquery result — mirroring the JPQL subquery card's "above average" example, but as a reusable `Specification` object rather than a fixed query string.
- You're building a genuinely complex, multi-condition dynamic search where some conditions involve joins and others don't, and want each condition as an independently composable `Specification` unit rather than one large, hard-to-read query string.

## 3. Core concept

```
 JOIN within a Specification:
   Specification<Order> hasLineItemDescribing(String keyword) {
       return (root, query, cb) -> {
           Join<Order, LineItem> items = root.join("lineItems");  -- real SQL JOIN
           return cb.like(items.get("description"), "%" + keyword + "%");
       };
   }

 SUBQUERY within a Specification:
   Specification<Order> aboveAverageTotal() {
       return (root, query, cb) -> {
           Subquery<Double> avgSubquery = query.subquery(Double.class);
           Root<Order> subRoot = avgSubquery.from(Order.class);
           avgSubquery.select(cb.avg(subRoot.get("total")));
           return cb.greaterThan(root.get("total"), avgSubquery);
       };
   }

 BOTH compose with .and()/.or() exactly like any other Specification:
   repo.findAll(hasLineItemDescribing("urgent").and(aboveAverageTotal()));
```

Join and subquery logic, once wrapped in a `Specification`, compose with every other specification the same way — the internal complexity doesn't leak into how the specification is used at the call site.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Specifications built with joins or subqueries compose identically to simple ones via and/or">
  <rect x="10" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">hasLineItemDescribing("urgent")</text>
  <text x="145" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">uses root.join(...)</text>

  <rect x="350" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">aboveAverageTotal()</text>
  <text x="485" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">uses query.subquery(...)</text>

  <rect x="150" y="100" width="340" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="125" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">both .and()-composable identically -- complexity stays internal</text>

  <line x1="145" y1="75" x2="250" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="485" y1="75" x2="390" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Advanced Criteria API constructs stay encapsulated within a `Specification`, composing identically with simpler ones.

## 5. Runnable example

The scenario: an order/line-item search, evolving from a join-based specification, to a subquery-based one comparing against a computed average, to composing both together in one query.

### Level 1 — Basic

Build a `Specification` using `Root.join(...)` to filter orders based on a property of their related line items.

```java
import jakarta.persistence.*;
import jakarta.persistence.criteria.Join;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class SpecCriteriaLevel1 {

    @Entity
    public static class LineItem {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String description;
        @ManyToOne
        private Order order;
        protected LineItem() {}
        public LineItem(Order order, String description) { this.order = order; this.description = description; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        @OneToMany(mappedBy = "order")
        private List<LineItem> lineItems = new ArrayList<>();
        protected Order() {}
        public Order(double total) { this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {}

    static Specification<Order> hasLineItemDescribing(String keyword) {
        return (root, query, cb) -> {
            Join<Order, LineItem> items = root.join("lineItems");
            query.distinct(true); // avoid row-multiplication duplicates from the join
            return cb.like(items.get("description"), "%" + keyword + "%");
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecCriteriaLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:speccrit1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        Order urgent = new Order(100.0);
        Order normal = new Order(50.0);
        em.persist(urgent);
        em.persist(normal);
        em.persist(new LineItem(urgent, "urgent restock needed"));
        em.persist(new LineItem(normal, "routine order"));
        em.getTransaction().commit();
        em.close();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        List<Order> matches = repo.findAll(hasLineItemDescribing("urgent"));
        System.out.println("orders with an urgent line item = " + matches.stream().map(Order::getTotal).toList());

        if (matches.size() != 1 || matches.get(0).getTotal() != 100.0)
            throw new AssertionError("Expected only the order with the 'urgent' line item to match");
        System.out.println("Specification with root.join() correctly filtered through the relationship -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java SpecCriteriaLevel1.java` on JDK 17+.

`root.join("lineItems")` produces a real SQL `JOIN` between `order` and `line_item`, letting the specification filter on `items.get("description")` — a property of the *joined* entity, not `Order` itself. `query.distinct(true)` prevents the join from producing duplicate `Order` rows in the result (the same row-multiplication concern the JPQL `JOIN FETCH` card addressed with an explicit `distinct` keyword).

### Level 2 — Intermediate

Build a `Specification` using a Criteria API subquery, comparing each order's total against the computed average — the programmatic equivalent of the earlier JPQL subquery card's example.

```java
import jakarta.persistence.*;
import jakarta.persistence.criteria.Root;
import jakarta.persistence.criteria.Subquery;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

@SpringBootApplication
public class SpecCriteriaLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        protected Order() {}
        public Order(double total) { this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {}

    static Specification<Order> aboveAverageTotal() {
        return (root, query, cb) -> {
            Subquery<Double> avgSubquery = query.subquery(Double.class);
            Root<Order> subRoot = avgSubquery.from(Order.class);
            avgSubquery.select(cb.avg(subRoot.get("total")));
            return cb.greaterThan(root.get("total"), avgSubquery);
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecCriteriaLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:speccrit2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(10.0));
        repo.save(new Order(20.0));
        repo.save(new Order(90.0)); // average = 40.0 -- only this exceeds it

        List<Order> aboveAverage = repo.findAll(aboveAverageTotal());
        System.out.println("above-average orders (via Specification subquery) = " + aboveAverage.stream().map(Order::getTotal).toList());

        if (aboveAverage.size() != 1 || aboveAverage.get(0).getTotal() != 90.0)
            throw new AssertionError("Expected only the 90.0 order to exceed the computed average");
        System.out.println("Specification with a Criteria API subquery matched the earlier JPQL example's result -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java SpecCriteriaLevel2.java`.

`query.subquery(Double.class)` creates a nested `Subquery`, independently `from`-ing `Order` again (as `subRoot`, distinct from the outer `root`), computing `cb.avg(subRoot.get("total"))` — this whole subquery becomes the right-hand side of `cb.greaterThan(root.get("total"), avgSubquery)`, producing the exact same logical query as the earlier JPQL card's `where o.total > (select avg(o2.total) from Order o2)`, expressed here as composable Java code instead of a query string.

### Level 3 — Advanced

Compose the join-based and subquery-based specifications from Levels 1 and 2 together with `.and()`, confirming advanced Criteria API constructs combine seamlessly, exactly like the simpler specifications from the earlier card.

```java
import jakarta.persistence.*;
import jakarta.persistence.criteria.Join;
import jakarta.persistence.criteria.Root;
import jakarta.persistence.criteria.Subquery;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class SpecCriteriaLevel3 {

    @Entity
    public static class LineItem {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String description;
        @ManyToOne
        private Order order;
        protected LineItem() {}
        public LineItem(Order order, String description) { this.order = order; this.description = description; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;
        @OneToMany(mappedBy = "order")
        private List<LineItem> lineItems = new ArrayList<>();
        protected Order() {}
        public Order(double total) { this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {}

    static Specification<Order> hasLineItemDescribing(String keyword) {
        return (root, query, cb) -> {
            Join<Order, LineItem> items = root.join("lineItems");
            query.distinct(true);
            return cb.like(items.get("description"), "%" + keyword + "%");
        };
    }

    static Specification<Order> aboveAverageTotal() {
        return (root, query, cb) -> {
            Subquery<Double> avgSubquery = query.subquery(Double.class);
            Root<Order> subRoot = avgSubquery.from(Order.class);
            avgSubquery.select(cb.avg(subRoot.get("total")));
            return cb.greaterThan(root.get("total"), avgSubquery);
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecCriteriaLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:speccrit3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        Order bigUrgent = new Order(90.0);   // above average AND has an urgent item
        Order smallUrgent = new Order(10.0); // has an urgent item, but NOT above average
        Order bigNormal = new Order(80.0);   // above average, but NO urgent item
        em.persist(bigUrgent); em.persist(smallUrgent); em.persist(bigNormal);
        em.persist(new LineItem(bigUrgent, "urgent restock"));
        em.persist(new LineItem(smallUrgent, "urgent but small"));
        em.persist(new LineItem(bigNormal, "routine restock"));
        em.getTransaction().commit();
        em.close();
        // average of 90, 10, 80 = 60.0

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Specification<Order> combined = hasLineItemDescribing("urgent").and(aboveAverageTotal());
        List<Order> matches = repo.findAll(combined);

        System.out.println("matches (urgent AND above-average) = " + matches.stream().map(Order::getTotal).toList());

        if (matches.size() != 1 || matches.get(0).getTotal() != 90.0)
            throw new AssertionError("Expected ONLY the 90.0 order to satisfy BOTH conditions");
        System.out.println("Join-based and subquery-based Specifications composed correctly via .and() -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java SpecCriteriaLevel3.java`.

`hasLineItemDescribing("urgent").and(aboveAverageTotal())` combines a join-based specification with a subquery-based one into a single composed `Specification`, translated into one SQL query containing both the `JOIN` and the subquery together. Only `bigUrgent` (total 90.0, above the average of 60.0, and has an "urgent" line item) satisfies both conditions simultaneously — `smallUrgent` fails the average check, `bigNormal` fails the line-item-description check.

## 6. Walkthrough

Trace `repo.findAll(hasLineItemDescribing("urgent").and(aboveAverageTotal()))`.

1. **Composition**: `.and(...)` (a default method on `Specification`) returns a new, combined `Specification` whose `toPredicate` calls *both* underlying specifications' `toPredicate` methods against the same `root`/`query`/`cb`, then combines their two resulting `Predicate`s with `cb.and(...)`.
2. **`hasLineItemDescribing("urgent")`'s contribution**: calls `root.join("lineItems")`, adding a `JOIN` to the query, and returns a `Predicate` checking `items.description LIKE '%urgent%'`.
3. **`aboveAverageTotal()`'s contribution**: calls `query.subquery(Double.class)`, adding a nested subquery computing the average total, and returns a `Predicate` checking `root.total > (that subquery)`.
4. **Final combined predicate**: `cb.and(...)` combines both predicates, producing the logical equivalent of `WHERE items.description LIKE '%urgent%' AND total > (SELECT AVG(total) FROM order)`.
5. **SQL generation**: Hibernate translates this combined Criteria structure into one SQL query with both the `JOIN` and the subquery present together.
6. **Execution against the 3 seeded orders**: `bigUrgent` (90.0, has an "urgent" item) satisfies both conditions; `smallUrgent` (10.0, has an "urgent" item but fails `10.0 > 60.0`) fails the average check; `bigNormal` (80.0, satisfies the average check but its line item says "routine," not "urgent") fails the join-based condition.
7. **Verification**: exactly one order — `bigUrgent` — satisfies both, confirming the composed specification correctly combined a join-based and a subquery-based condition into one coherent query.

```
 hasLineItemDescribing("urgent")  .and(  aboveAverageTotal()  )
        |                                    |
   JOIN + LIKE predicate              SUBQUERY + comparison predicate
        |                                    |
        +------------- cb.and(...) ----------+
                        |
                        v
        WHERE (JOIN ... description LIKE '%urgent%')
          AND (total > (SELECT AVG(total) FROM order))
                        |
                        v
        bigUrgent(90.0) matches BOTH -- only result
```

## 7. Gotchas & takeaways

> **Gotcha:** `query.distinct(true)`, called inside one specification in a composed chain, applies to the *entire* combined query, not just that one specification's contribution — if a different specification later in the same composition also needs distinct-suppressing behavior (rare, but possible), setting `distinct` from within any single specification affects the whole query globally. Be mindful that certain Criteria API calls on `query` (as opposed to calls scoped to `root`/`cb`) have chain-wide effects when specifications are composed together.

- `Root.join(...)` inside a `Specification` produces a genuine SQL `JOIN`, letting a dynamic filter reach through a relationship — combined with `query.distinct(true)` to avoid row-multiplication duplicates in the result, the same concern the JPQL `JOIN FETCH` card addressed.
- `CriteriaQuery.subquery(...)` embeds a nested query within a `Specification`, expressing the same "compare against a computed aggregate" pattern the JPQL subquery card demonstrated as a raw query string — as composable, type-checked Java code instead.
- Both advanced constructs compose with `.and()`/`.or()` exactly like the simplest property-comparison specifications from the earlier card — internal Criteria API complexity stays encapsulated within each specification, invisible at the composition call site.
- Choosing between JPQL (a query string, potentially more concise for a single fixed query) and Criteria-API-based Specifications (more verbose, but composable and reusable as independent Java objects) is the same portable-versus-flexible tradeoff every dynamic-query mechanism in this section has presented, just at this card's more advanced level of join and subquery capability.
