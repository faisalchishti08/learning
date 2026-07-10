---
card: spring-data
gi: 47
slug: derived-query-methods-jpa
title: "Derived query methods (JPA)"
---

## 1. What it is

This card looks at query derivation (the general mechanism covered in depth in the Commons section) specifically through the lens of what JPA does with it: the exact JPQL a derived method compiles into, how derivation handles `@Column`-renamed fields and `@ManyToOne`/`@OneToMany` associations (producing real SQL `JOIN`s), and what happens when a derived method's generated JPQL would be genuinely inefficient — the point where understanding the generated query matters for real applications, not just for correctness.

```java
// Derives to: select o from Order o join o.customer c where c.email = ?1
List<Order> findByCustomerEmail(String email);
```

## 2. Why & when

The Commons section established the naming grammar; this card is about reading the *result* — knowing what JPQL (and therefore what SQL, what joins, what potential N+1 problems) a given derived method name actually produces. This matters because a derived method that looks simple can generate a join across several tables, and a derived method returning a collection of entities with lazy associations can trigger the classic N+1 query problem the moment calling code iterates and accesses those associations.

Understanding JPA-specific derivation behavior matters specifically when:

- You're reviewing or writing a derived method that traverses a relationship (`findByCustomerEmail`, from `Order` through `Customer`) and want to know exactly what SQL join it produces, to judge whether it's efficient for the actual table sizes involved.
- You're debugging an N+1 query problem — often traced back to a derived method returning entities whose lazily-loaded associations get accessed in a loop afterward, each access triggering its own additional query.
- You're deciding whether a derived method's generated query is efficient enough, or whether the same logical query needs a hand-written `@Query` with an explicit `JOIN FETCH` to eagerly load an association in the same round-trip.

## 3. Core concept

```
 findByCustomerEmail(String email)
        |
        v
 JPQL:  select o from Order o join o.customer c where c.email = ?1
        |
        v
 SQL (Hibernate-generated, roughly):
   SELECT o.* FROM order o
   INNER JOIN customer c ON o.customer_id = c.id
   WHERE c.email = ?

 If Order.customer is LAZY (the JPA default for @ManyToOne is actually EAGER,
 but @OneToMany/@ManyToMany default to LAZY):
   the JOIN above is only for FILTERING -- customer.* columns may or may not
   be selected/populated depending on the association's fetch type;
   accessing order.getCustomer().getName() afterward, if lazy, triggers
   a SEPARATE query PER order in a loop -- the classic N+1 problem
```

A derived method's JOIN exists to filter, not necessarily to eagerly populate the joined association — those are two separate concerns easy to conflate.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A derived query filtering through an association produces a JOIN for filtering, but accessing a lazy association afterward triggers separate N+1 queries">
  <rect x="10" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByCustomerEmail(email)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 query, JOIN used for filtering</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">for(Order o : results) o.getLineItems()</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">N extra queries if lineItems is LAZY</text>
</svg>

The filtering join and the eventual association access are two independent query concerns.

## 5. Runnable example

The scenario: an `Order`/`Customer` relationship, evolving from confirming a derived-traversal method's generated join, to observing the N+1 problem concretely via query counts, to fixing it with `JOIN FETCH` inside an explicit `@Query`.

### Level 1 — Basic

Confirm `findByCustomerEmail` correctly filters through the `customer` association, producing one query.

```java
import jakarta.persistence.*;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class JpaDerivationLevel1 {

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
        List<Order> findByCustomerEmail(String email);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpaDerivationLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:jpaderiv1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        Customer ada = new Customer("ada@example.com");
        em.persist(ada);
        em.persist(new Order(ada, 100.0));
        em.persist(new Order(ada, 50.0));
        em.getTransaction().commit();
        em.close();

        Statistics stats = ctx.getBean(EntityManagerFactory.class).unwrap(SessionFactory.class).getStatistics();
        stats.clear();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        List<Order> result = repo.findByCustomerEmail("ada@example.com");

        System.out.println("found " + result.size() + " orders, queries executed = " + stats.getQueryExecutionCount());

        if (result.size() != 2) throw new AssertionError("Expected 2 orders for ada@example.com");
        if (stats.getQueryExecutionCount() != 1) throw new AssertionError("Expected exactly 1 query for the join-filtered derived method");
        System.out.println("findByCustomerEmail used a single JOIN-based query to filter through the association -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java JpaDerivationLevel1.java` on JDK 17+.

`findByCustomerEmail(String email)` traverses the `customer` association purely to filter — one query, one join, confirmed directly via Hibernate's statistics counter, which reports exactly `1` query execution for the whole call.

### Level 2 — Intermediate

Add a `@OneToMany` (lazy by JPA default) association and observe the N+1 problem when iterating and accessing it after a derived query.

```java
import jakarta.persistence.*;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class JpaDerivationLevel2 {

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
        private String status;
        @OneToMany(mappedBy = "order")
        private List<LineItem> lineItems = new ArrayList<>();
        protected Order() {}
        public Order(String status) { this.status = status; }
        public String getStatus() { return status; }
        public List<LineItem> getLineItems() { return lineItems; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        List<Order> findByStatus(String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpaDerivationLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:jpaderiv2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        for (int i = 0; i < 3; i++) {
            Order o = new Order("pending");
            em.persist(o);
            em.persist(new LineItem(o, "item-" + i + "-a"));
            em.persist(new LineItem(o, "item-" + i + "-b"));
        }
        em.getTransaction().commit();
        em.close();

        Statistics stats = ctx.getBean(EntityManagerFactory.class).unwrap(SessionFactory.class).getStatistics();
        stats.clear();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        List<Order> orders = repo.findByStatus("pending"); // 1 query so far
        long afterDerivedQuery = stats.getQueryExecutionCount();

        int totalLineItems = 0;
        for (Order o : orders) {
            totalLineItems += o.getLineItems().size(); // each access, for a LAZY collection, triggers ANOTHER query
        }
        long afterAccessingLineItems = stats.getQueryExecutionCount();

        System.out.println("queries after derived findByStatus alone = " + afterDerivedQuery);
        System.out.println("queries after accessing lineItems in a loop = " + afterAccessingLineItems);
        System.out.println("total line items counted = " + totalLineItems);

        if (afterDerivedQuery != 1) throw new AssertionError("Expected exactly 1 query for the derived findByStatus call");
        if (afterAccessingLineItems - afterDerivedQuery != 3)
            throw new AssertionError("Expected exactly 3 ADDITIONAL queries (N+1), one per order's lazy lineItems access");

        System.out.println("Demonstrated the N+1 problem concretely: 1 + 3 extra queries for 3 orders -- PASS (problem confirmed)");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java JpaDerivationLevel2.java`.

`findByStatus("pending")` itself is one query, returning 3 `Order` entities with their `lineItems` collections left unloaded (JPA's default `FetchType.LAZY` for `@OneToMany`). Looping over the results and calling `o.getLineItems().size()` triggers, for each order, a separate `SELECT` to fetch that specific order's line items — the query count jumps by exactly 3 (one per order), the textbook N+1 pattern, confirmed here by directly measuring query counts rather than merely asserting it happens.

### Level 3 — Advanced

Fix the N+1 problem from Level 2 using an explicit `@Query` with `JOIN FETCH`, confirming the same data now loads in a single query.

```java
import jakarta.persistence.*;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class JpaDerivationLevel3 {

    @Entity
    public static class LineItem {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        @ManyToOne
        private Order order;
        protected LineItem() {}
        public LineItem(Order order) { this.order = order; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        @OneToMany(mappedBy = "order")
        private List<LineItem> lineItems = new ArrayList<>();
        protected Order() {}
        public Order(String status) { this.status = status; }
        public List<LineItem> getLineItems() { return lineItems; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // JOIN FETCH eagerly loads lineItems in the SAME query, avoiding N+1.
        @Query("select distinct o from Order o join fetch o.lineItems where o.status = :status")
        List<Order> findByStatusWithLineItems(@org.springframework.data.repository.query.Param("status") String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(JpaDerivationLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:jpaderiv3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--spring.jpa.properties.hibernate.generate_statistics=true");

        EntityManager em = ctx.getBean(EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        for (int i = 0; i < 3; i++) {
            Order o = new Order("pending");
            em.persist(o);
            em.persist(new LineItem(o));
            em.persist(new LineItem(o));
        }
        em.getTransaction().commit();
        em.close();

        Statistics stats = ctx.getBean(EntityManagerFactory.class).unwrap(SessionFactory.class).getStatistics();
        stats.clear();

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        List<Order> orders = repo.findByStatusWithLineItems("pending");

        int totalLineItems = 0;
        for (Order o : orders) {
            totalLineItems += o.getLineItems().size(); // already loaded -- NO additional queries
        }

        long totalQueries = stats.getQueryExecutionCount();
        System.out.println("total queries for fetch + full access = " + totalQueries);
        System.out.println("total line items counted = " + totalLineItems);

        if (totalQueries != 1) throw new AssertionError("Expected exactly 1 query total, thanks to JOIN FETCH");
        if (totalLineItems != 6) throw new AssertionError("Expected 6 total line items across 3 orders");

        System.out.println("JOIN FETCH eliminated the N+1 problem -- single query for everything -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java JpaDerivationLevel3.java`.

`join fetch o.lineItems` in the `@Query` string tells Hibernate to eagerly load each order's line items in the *same* SQL query, via a genuine SQL `JOIN`, rather than leaving them lazy. `distinct` is necessary because the join produces one result row per line item (multiplying each order's row for every line item it has), and without `distinct`, the same `Order` would appear duplicated in the returned `List`. Accessing `o.getLineItems()` afterward triggers zero additional queries — the total query count for the whole operation stays at exactly `1`, directly fixing the N+1 problem demonstrated in Level 2.

## 6. Walkthrough

Trace Level 3's single query and its downstream effect.

1. **`repo.findByStatusWithLineItems("pending")`** executes the declared JPQL: `select distinct o from Order o join fetch o.lineItems where o.status = :status`.
2. **SQL generation**: Hibernate translates this into a single SQL query with a genuine `INNER JOIN` between `order` and `line_item`, selecting columns from *both* tables in one round-trip — unlike Level 1's join (used purely for filtering), this join's purpose is to populate `lineItems` too.
3. **Result set shape**: because of the join, the raw SQL result has one row per `(order, lineItem)` pair — for 3 orders with 2 line items each, that's 6 raw rows.
4. **Hibernate's row-to-object mapping**: as it processes these 6 rows, Hibernate recognizes repeated `order` data (the same order's columns appearing twice, once per line item) and correctly assembles it into just 3 distinct `Order` objects, each with its `lineItems` collection *already fully populated* from the join results — no separate query needed for this.
5. **`distinct` in the JPQL**: ensures the `List<Order>` returned to the caller contains exactly 3 entries, not 6 duplicated ones, even though the underlying SQL result set had 6 rows.
6. **Loop over `orders`**: `o.getLineItems().size()` for each order reads directly from the already-populated in-memory collection — no lazy-loading trigger, no additional query, since the data arrived already attached during step 4.
7. **Verification**: `stats.getQueryExecutionCount()` confirms exactly `1` query total for the entire operation — the derived-method fetch and every subsequent line-item access combined — a stark contrast to Level 2's `1 + 3` query total for the equivalent (unfetched) data access pattern.

```
 Level 2 (lazy, no fetch):     1 query (orders) + 3 queries (lineItems, one per order) = 4 total
 Level 3 (JOIN FETCH):          1 query (orders AND lineItems together)                = 1 total
```

## 7. Gotchas & takeaways

> **Gotcha:** `JOIN FETCH` on a `@OneToMany`/`@ManyToMany` collection, combined with `Pageable`-based pagination, produces a well-known Hibernate warning/limitation — pagination applied *in memory* after the join (since `LIMIT`/`OFFSET` on the raw, multiplied SQL rows would incorrectly cut off an order's line items partway through) can be a serious, silent performance problem for large result sets. `JOIN FETCH` and pagination don't combine safely without extra care (such as a two-query approach: paginate ids first, then fetch with the join for just those ids).

- Query derivation traversing a JPA association (`findByCustomerEmail`, reaching `Order` through `Customer`) produces a real SQL `JOIN` used purely for filtering — it does not automatically mean the joined association's data is eagerly loaded into the result.
- Lazy associations (`@OneToMany`/`@ManyToMany`, JPA's default fetch type for these) accessed after a query returns trigger a separate query *per entity* in a loop — the classic N+1 problem, directly measurable via Hibernate statistics as this card's examples demonstrated.
- `JOIN FETCH` inside an explicit `@Query` (with `distinct` to avoid row-multiplication duplicates in the returned list) is the standard fix, loading an association eagerly in the same query as the main entity fetch.
- Understanding what SQL a derived method actually produces — not just trusting that "it returns the right data" — is essential for catching N+1 problems and other efficiency issues before they surface as production performance incidents.
