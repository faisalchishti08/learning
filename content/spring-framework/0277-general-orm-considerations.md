---
card: spring-framework
gi: 277
slug: general-orm-considerations
title: General ORM considerations
---

## 1. What it is

**General ORM considerations** are the cross-cutting concerns you must understand when using any ORM (Hibernate, JPA, EclipseLink) in a Spring application:

- **Session / EntityManager scope**: how long does a persistence context live?
- **Lazy loading**: when are related objects fetched?
- **Open-session-in-view**: extending the persistence context to the view layer.
- **N+1 problem**: unintentional loops of per-row queries.
- **Second-level cache**: shared cache across Sessions.
- **Detached entities**: managing objects outside a transaction.

These are not unique to any one ORM — they apply everywhere ORM is used and are the most common source of bugs and performance issues in Spring + JPA applications.

## 2. Why & when

Most ORM bugs fall into one of these categories:
- **`LazyInitializationException`** — accessing a lazy association outside a session.
- **N+1 queries** — loading a list then fetching a field per row.
- **Stale detached entities** — merging an old snapshot over fresh data.
- **Second-level cache staleness** — cached data diverges from the database.

Understanding these pitfalls is more valuable than memorising API signatures — the API calls are simple; the edge cases are where bugs hide.

## 3. Core concept

**Persistence context lifetime:**

```
Short context (default):
  @Transactional
  service.loadOrders()  → Session opens → entities loaded → TX commits → Session closes
  // entities are now DETACHED — no lazy loading possible

Extended context (EXTENDED scope):
  @PersistenceContext(type=EXTENDED)
  → Session lives for the bean lifecycle (stateful session bean pattern)
  // risky in stateless services; mostly used in @Stateful EJBs
```

**LazyInitializationException pattern:**
```java
// BROKEN — session closed before getItems() accesses the lazy collection
Order order = orderRepository.findById(1L);   // TX ends here
List<Item> items = order.getItems();           // LazyInitializationException!

// FIXED — load inside TX with JOIN FETCH
@Transactional
Order findWithItems(long id) {
    return em.createQuery("FROM Order o JOIN FETCH o.items WHERE o.id=:id", Order.class)
        .setParameter("id", id).getSingleResult();
}
```

**N+1 query pattern:**
```
// Loading 100 orders + fetching customer per order = 1 + 100 queries
List<Order> orders = em.createQuery("FROM Order", Order.class).getResultList();
orders.forEach(o -> System.out.println(o.getCustomer().getName()));  // N+1!

// Fix: JOIN FETCH
em.createQuery("FROM Order o JOIN FETCH o.customer", Order.class)
```

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Transaction boundary -->
  <rect x="10" y="10" width="670" height="80" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="345" y="30" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Transactional scope — EntityManager OPEN</text>
  <rect x="30" y="38" width="130" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="95" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">em.find()</text>
  <text x="95" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">MANAGED entity</text>
  <rect x="200" y="38" width="130" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="265" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">entity.setX()</text>
  <text x="265" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">dirty → auto UPDATE</text>
  <rect x="370" y="38" width="130" height="38" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="435" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">lazy.get()</text>
  <text x="435" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">OK — session open</text>
  <rect x="540" y="38" width="120" height="38" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="600" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">flush + commit</text>

  <!-- Outside TX -->
  <rect x="10" y="110" width="670" height="60" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="2,3"/>
  <text x="345" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Outside @Transactional — EntityManager CLOSED — entity is DETACHED</text>
  <rect x="30" y="140" width="200" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">entity.setX() → no effect (detached)</text>
  <rect x="280" y="140" width="220" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="390" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">entity.getLazyField() → LazyInitializationException</text>

  <!-- N+1 warning -->
  <rect x="10" y="188" width="670" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="345" y="207" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">N+1: SELECT * FROM orders [1 query] then SELECT customer WHERE id=? [N queries]</text>
  <text x="345" y="218" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">Fix: JOIN FETCH collapses to 1 query with JOIN</text>
</svg>

Entities are MANAGED inside a TX (dirty check + lazy loading work); DETACHED outside (neither works).

## 5. Runnable example

Scenario: an **order management** system — demonstrate lazy loading, the N+1 problem and its fix, and detached entity handling.

### Level 1 — Basic

Lazy loading — access association inside vs. outside a transaction.

```java
// OrmConsiderationsDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="customers")
class Customer {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String name;
    @OneToMany(mappedBy="customer", fetch=FetchType.LAZY)
    List<Order> orders;
    public Customer(){}
    public Customer(String n){name=n;}
    public Long getId(){return id;}
    public String getName(){return name;}
    public List<Order> getOrders(){return orders;}
}

@Entity @Table(name="orders")
class Order {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    double total;
    @ManyToOne Customer customer;
    public Order(){}
    public Order(double t, Customer c){total=t; customer=c;}
    public Long getId(){return id;}
    public double getTotal(){return total;}
}

@Configuration @EnableTransactionManagement
class Cfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:shop;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var f=new LocalContainerEntityManagerFactoryBean(); f.setDataSource(ds); f.setPackagesToScan("");
        f.setJpaVendorAdapter(new org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); f.setJpaProperties(p); return f;
    }
    @Bean JpaTransactionManager tx(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class OrmConsiderationsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Cfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(ctx.getBean(PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer alice = new Customer("Alice");
            em.persist(alice);
            em.persist(new Order(99.0, alice)); em.persist(new Order(49.0, alice));
            em.close(); return null;
        });

        // Lazy loading INSIDE transaction — OK
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer c = em.find(Customer.class, 1L);
            System.out.println("Orders inside TX: " + c.getOrders().size()); // 2 — OK
            em.close(); return null;
        });

        // Lazy loading OUTSIDE transaction — fails
        EntityManager em = emf.createEntityManager();
        Customer detached = em.find(Customer.class, 1L);
        em.close();
        try {
            detached.getOrders().size();  // LazyInitializationException
        } catch (org.hibernate.LazyInitializationException e) {
            System.out.println("Expected: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. OrmConsiderationsDemo.java`

`FetchType.LAZY` tells the ORM not to load `orders` until accessed. Inside a TX the session is open — `getOrders()` triggers a SELECT for the collection. Outside the TX the session is closed and the entity is **detached** — accessing a lazy collection throws `LazyInitializationException`.

---

### Level 2 — Intermediate

N+1 problem — 1 SELECT + N SELECT queries; fix with JOIN FETCH.

```java
// OrmConsiderationsDemo.java
import jakarta.persistence.*;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.support.TransactionTemplate;
import java.util.*;

// (same entity and config classes as Level 1)

public class OrmConsiderationsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Cfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(ctx.getBean(
            org.springframework.transaction.PlatformTransactionManager.class));

        // Seed 3 customers with 2 orders each
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            for (String name : List.of("Alice","Bob","Carol")) {
                Customer c = new Customer(name);
                em.persist(c);
                em.persist(new Order(50.0 + name.length(), c));
                em.persist(new Order(25.0 + name.length(), c));
            }
            em.close(); return null;
        });

        // N+1: load all customers, access orders for each → 1 + 3 queries
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            System.out.println("--- N+1 ---");
            List<Customer> customers = em.createQuery("FROM Customer", Customer.class).getResultList();
            // Each customer.getOrders() fires a separate SELECT
            customers.forEach(c -> System.out.printf("  %s: %d orders%n",
                c.getName(), c.getOrders().size()));  // 1 + N queries
            em.close(); return null;
        });

        // FIX: JOIN FETCH — 1 query with JOIN
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            System.out.println("--- JOIN FETCH (1 query) ---");
            List<Customer> customers = em.createQuery(
                "SELECT DISTINCT c FROM Customer c JOIN FETCH c.orders", Customer.class)
                .getResultList();
            customers.forEach(c -> System.out.printf("  %s: %d orders%n",
                c.getName(), c.getOrders().size()));
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

The N+1 problem: `FROM Customer` fires 1 SELECT for customers, then each `customer.getOrders()` fires 1 SELECT for that customer's orders — 1 + N queries. `JOIN FETCH` tells Hibernate to eagerly load orders in the same query via a SQL JOIN — 1 query total. `SELECT DISTINCT` prevents duplicate customer rows from the JOIN.

---

### Level 3 — Advanced

Detached entity reattachment + `em.merge()` vs. `em.refresh()`.

```java
// OrmConsiderationsDemo.java
import jakarta.persistence.*;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.support.TransactionTemplate;
import java.util.*;

// (same entity and config as Level 1)

public class OrmConsiderationsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Cfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(ctx.getBean(
            org.springframework.transaction.PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer alice = new Customer("Alice");
            em.persist(alice);
            em.persist(new Order(99.0, alice));
            em.close(); return null;
        });

        // Load and detach Alice
        EntityManager em1 = emf.createEntityManager();
        Customer alice = em1.find(Customer.class, 1L);
        em1.close();  // em closed — alice is DETACHED
        System.out.println("Detached name: " + alice.getName());

        // Modify detached entity
        alice.name = "Alice Updated";

        // Another TX updates Alice's name in the DB
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer db = em.find(Customer.class, 1L);
            db.name = "Alice (DB version)";
            em.close(); return null;
        });

        // merge() — reattaches detached entity, OVERWRITES db version
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer merged = em.merge(alice);  // alice's state wins over DB
            System.out.println("After merge: " + merged.getName()); // "Alice Updated"
            em.close(); return null;
        });

        // refresh() — discards in-memory changes, reloads from DB
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Customer c = em.find(Customer.class, 1L);
            c.name = "Pending Change";
            em.refresh(c);  // reload from DB — discard "Pending Change"
            System.out.println("After refresh: " + c.getName()); // "Alice Updated"
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

`em.merge(detachedEntity)` copies the detached entity's state into the persistence context — it overwrites whatever is currently in the database. This is correct when the detached entity is the source of truth. `em.refresh(entity)` is the opposite — it reloads the entity from the database, discarding any pending in-memory changes. Use `refresh()` when you want to discard local changes and synchronise with DB reality.

## 6. Walkthrough

**Level 2 — N+1 vs. JOIN FETCH (execution order):**

**N+1 path:**
1. `em.createQuery("FROM Customer").getResultList()` → `SELECT * FROM customers` — 3 rows loaded.
2. `alice.getOrders().size()`: lazy proxy fires → `SELECT * FROM orders WHERE customer_id=1` — 2 rows.
3. `bob.getOrders().size()`: lazy proxy fires → `SELECT * FROM orders WHERE customer_id=2` — 2 rows.
4. `carol.getOrders().size()` → same. Total: **4 SQL queries** for 3 customers.

**JOIN FETCH path:**
1. `SELECT DISTINCT c FROM Customer c JOIN FETCH c.orders` → Hibernate generates:
   `SELECT DISTINCT c.*, o.* FROM customers c JOIN orders o ON o.customer_id=c.id`
   — 1 query returns all rows.
2. Hibernate assembles `Customer` objects from the flat result, building the `orders` list from the joined rows. No additional queries fired.
3. `alice.getOrders().size()` → collection already populated. **0 additional queries**.

```
N+1:
  SELECT * FROM customers           -- 1 query
  SELECT * FROM orders WHERE cid=1  -- per customer
  SELECT * FROM orders WHERE cid=2  -- per customer
  SELECT * FROM orders WHERE cid=3  -- per customer
  Total: 4 queries for 3 customers

JOIN FETCH:
  SELECT c.*,o.* FROM customers c JOIN orders o ON o.customer_id=c.id
  Total: 1 query
```

## 7. Gotchas & takeaways

> **Never use `FetchType.EAGER` globally.** Eager loading forces JOINs on every query, even when you don't need the related data. Use `LAZY` by default and `JOIN FETCH` in queries where you specifically need the relationship.

> **`em.merge()` creates a NEW managed instance — the passed-in detached object is NOT made managed.** `Customer managed = em.merge(detached)` — use `managed`, not `detached`, after the merge call. The detached reference is still detached.

> **Open-Session-in-View (OSIV) extends the session to the view layer** — it "fixes" `LazyInitializationException` by keeping the session open until the HTTP response is written. It appears to work but causes N+1 queries silently in views. Disable OSIV (`spring.jpa.open-in-view=false`) and load everything inside `@Transactional` service methods.

- `FetchType.LAZY` (default for collections): defer loading until accessed — but only while session is open.
- `JOIN FETCH`: collapse N+1 into 1 query — use when you know you'll access the association.
- `em.merge(detached)` — reattach and overwrites DB; `em.refresh(managed)` ��� reload from DB.
- Detached entities outside `@Transactional` can't lazy-load — plan fetching inside the TX.
- Disable OSIV in production; load associations explicitly in service methods.
