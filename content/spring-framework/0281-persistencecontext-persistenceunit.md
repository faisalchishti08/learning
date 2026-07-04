---
card: spring-framework
gi: 281
slug: persistencecontext-persistenceunit
title: "@PersistenceContext / @PersistenceUnit"
---

## 1. What it is

`@PersistenceContext` and `@PersistenceUnit` are standard JPA annotations for injecting persistence infrastructure into Spring beans:

- **`@PersistenceContext EntityManager em`** — injects a **transactional proxy** of the `EntityManager`. The proxy delegates to the transaction-bound `EntityManager` — safe to use as a field in a singleton bean.
- **`@PersistenceUnit EntityManagerFactory emf`** — injects the `EntityManagerFactory` directly. Use when you need to create `EntityManager` instances manually.

```java
@Repository
public class ProductRepository {
    @PersistenceContext   // injects a thread-safe proxy
    private EntityManager em;

    @PersistenceUnit      // injects the raw factory
    private EntityManagerFactory emf;

    public Product findById(long id) {
        return em.find(Product.class, id);  // em routes to the current TX's EM
    }
}
```

## 2. Why & when

The naive approach to inject an `EntityManager` is `@Autowired EntityManager em` — but `EntityManager` is **not thread-safe**. A single `EntityManager` shared across threads would be a concurrency bug.

`@PersistenceContext` solves this by injecting a **shared thread-safe proxy** instead of a real `EntityManager`. When you call `em.find(...)`, the proxy looks up the `EntityManager` bound to the current transaction (stored in thread-local by `JpaTransactionManager`) and delegates to it.

Use `@PersistenceUnit` when:
- You need to create an `EntityManager` yourself (stateful patterns, bulk import).
- You inspect the `EntityManagerFactory`'s `Metamodel` or properties.
- You need to call `emf.unwrap()` to access vendor-specific extensions.

## 3. Core concept

Spring's `PersistenceAnnotationBeanPostProcessor` processes `@PersistenceContext` and `@PersistenceUnit` — it scans beans for these annotations and injects the appropriate proxy/factory.

```java
@PersistenceContext
EntityManager em;
// injected: SharedEntityManagerCreator.createSharedEntityManager(emf)
// — a JDK Proxy that delegates all EM calls to the TX-bound EM

@PersistenceUnit
EntityManagerFactory emf;
// injected: the raw EMF bean directly (thread-safe — factory, not connection)
```

`@PersistenceContext` type attribute:
- `PersistenceContextType.TRANSACTION` (default) — per-TX EM; proxy finds the thread-local EM.
- `PersistenceContextType.EXTENDED` — long-lived EM; survives beyond a single TX; mainly for stateful session beans.

Multiple persistence units: use `unitName` to disambiguate:
```java
@PersistenceContext(unitName = "catalogPU")
EntityManager catalogEm;

@PersistenceContext(unitName = "auditPU")
EntityManager auditEm;
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Repository -->
  <rect x="10" y="75" width="140" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Repository</text>
  <text x="80" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@PersistenceContext em</text>
  <text x="80" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">em.find(…)</text>

  <line x1="152" y1="105" x2="195" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- EM Proxy -->
  <rect x="197" y="55" width="185" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="289" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EM Proxy (shared)</text>
  <line x1="207" y1="84" x2="372" y2="84" stroke="#8b949e" stroke-width="0.5"/>
  <text x="289" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">thread-safe JDK proxy</text>
  <text x="289" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">em.find() →</text>
  <text x="289" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">look up TX-bound EM</text>

  <line x1="384" y1="105" x2="427" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- TX manager / ThreadLocal -->
  <rect x="429" y="65" width="175" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="516" y="88" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JpaTransactionManager</text>
  <line x1="439" y1="94" x2="594" y2="94" stroke="#8b949e" stroke-width="0.5"/>
  <text x="516" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">thread-local EM binding</text>
  <text x="516" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">→ real EntityManager</text>
</svg>

`@PersistenceContext` injects a shared proxy; the proxy delegates to the real TX-bound `EntityManager` at call time.

## 5. Runnable example

Scenario: an **order service** — use `@PersistenceContext` in a `@Repository` and `@Service`, query and update via the injected proxy.

### Level 1 — Basic

`@PersistenceContext` in a `@Repository` class.

```java
// PersistenceContextDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name = "orders")
class Order {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String product; double total; String status;
    public Order(){} public Order(String p, double t, String s){product=p;total=t;status=s;}
    public Long getId(){return id;} public String getProduct(){return product;}
    public double getTotal(){return total;} public String getStatus(){return status;}
    public void setStatus(String s){status=s;}
    public String toString(){return "Order["+id+","+product+","+status+"]";}
}

@Repository
class OrderRepository {
    @PersistenceContext       // Spring injects a TX-aware proxy — not a raw EntityManager
    private EntityManager em;

    @Transactional
    public Order save(Order order) { em.persist(order); return order; }

    @Transactional(readOnly = true)
    public Optional<Order> findById(Long id) {
        return Optional.ofNullable(em.find(Order.class, id));
    }

    @Transactional(readOnly = true)
    public List<Order> findByStatus(String status) {
        return em.createQuery("FROM Order WHERE status=:s ORDER BY total DESC", Order.class)
            .setParameter("s",status).getResultList();
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:orders;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean JpaTransactionManager tx(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class PersistenceContextDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        OrderRepository repo = ctx.getBean(OrderRepository.class);

        // save() — each call is a separate TX
        repo.save(new Order("Widget",  49.99, "OPEN"));
        repo.save(new Order("Gadget",  99.00, "OPEN"));
        repo.save(new Order("Sensor", 199.99, "SHIPPED"));

        // findByStatus — separate read TX
        List<Order> open = repo.findByStatus("OPEN");
        System.out.println("Open orders: " + open);

        // findById
        Optional<Order> order = repo.findById(1L);
        order.ifPresent(o -> System.out.println("Found: " + o));

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. PersistenceContextDemo.java`

`@PersistenceContext EntityManager em` injects a proxy. The proxy is safe to use as a field in a singleton `@Repository` bean — it does NOT hold a real connection. On each `em.find()` call, the proxy delegates to whatever real `EntityManager` is bound to the current transaction thread-local.

---

### Level 2 — Intermediate

`@PersistenceUnit` for manual `EntityManager` creation + `@PersistenceContext` in a service.

```java
// PersistenceContextDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.*;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Order entity and AppCfg same as Level 1)

@Service
class OrderService {
    @PersistenceContext          // TX-bound proxy
    private EntityManager em;

    @PersistenceUnit             // raw factory — useful for manual EM creation
    private EntityManagerFactory emf;

    @Transactional
    public void placeOrder(String product, double total) {
        Order order = new Order(product, total, "OPEN");
        em.persist(order);  // via TX-bound proxy
        System.out.println("Order placed: " + order.getId());
    }

    @Transactional
    public void shipOrder(Long id) {
        Order order = em.find(Order.class, id);
        if (order != null) { order.setStatus("SHIPPED"); }
        // dirty check → UPDATE at commit
    }

    // Manual EM for a bulk stat operation outside normal TX flow
    public Map<String,Long> countByStatus() {
        EntityManager manualEm = emf.createEntityManager();  // fresh EM
        try {
            List<Object[]> rows = manualEm.createQuery(
                "SELECT o.status, COUNT(o) FROM Order o GROUP BY o.status", Object[].class)
                .getResultList();
            Map<String,Long> result = new LinkedHashMap<>();
            rows.forEach(r -> result.put((String)r[0], (Long)r[1]));
            return result;
        } finally {
            manualEm.close();  // always close manually-created EMs
        }
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:orders;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean JpaTransactionManager tx(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class PersistenceContextDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        OrderService svc = ctx.getBean(OrderService.class);

        svc.placeOrder("Widget",49.99);
        svc.placeOrder("Gadget",99.00);
        svc.shipOrder(1L);

        Map<String,Long> stats = svc.countByStatus();
        System.out.println("Order stats: " + stats);  // {OPEN=1, SHIPPED=1}

        ctx.close();
    }
}
```

How to run: same classpath

`@PersistenceUnit emf` gets the raw `EntityManagerFactory`. `emf.createEntityManager()` returns a real (non-proxy) `EntityManager` — you own its lifecycle; always close it in a `finally` block. This pattern is appropriate for batch/bulk operations that don't need Spring TX management.

---

### Level 3 — Advanced

Multi-unit `@PersistenceContext(unitName = "…")` — two EntityManagers in one bean.

```java
// PersistenceContextDemo.java
import jakarta.persistence.*;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.*;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="orders")  class Order {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String product; double total;
    public Order(){} public Order(String p,double t){product=p;total=t;}
    public Long getId(){return id;} public String toString(){return "Order["+id+","+product+"]";}
}
@Entity @Table(name="audit_log")  class AuditEntry {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String msg;
    public AuditEntry(){} public AuditEntry(String m){msg=m;}
    public String toString(){return "Audit["+msg+"]";}
}

@Service
class OrderAuditService {
    @PersistenceContext(unitName = "ordersPU")
    private EntityManager ordersEm;

    @PersistenceContext(unitName = "auditPU")
    private EntityManager auditEm;

    // Note: both EMs — only ordersEm is in an @Transactional TX here
    @Transactional("ordersTx")
    public void placeOrderWithAudit(String product, double total) {
        Order order = new Order(product, total);
        ordersEm.persist(order);
        System.out.println("Placed: " + order);

        // Write audit entry directly (own transaction)
        EntityManager auditDirect = auditEm.getEntityManagerFactory().createEntityManager();
        auditDirect.getTransaction().begin();
        auditDirect.persist(new AuditEntry("ORDER_PLACED: " + product + " $" + total));
        auditDirect.getTransaction().commit(); auditDirect.close();
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class MultiPUAppCfg {
    @Bean @Qualifier("ordersDS") DataSource ordersDs(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:orders2;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean @Qualifier("auditDS") DataSource auditDs(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:audit2;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean @Primary
    LocalContainerEntityManagerFactoryBean ordersEmf(@Qualifier("ordersDS") DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setPersistenceUnitName("ordersPU");
        emf.setDataSource(ds); emf.setPackagesToScan(""); emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean
    LocalContainerEntityManagerFactoryBean auditEmf(@Qualifier("auditDS") DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setPersistenceUnitName("auditPU");
        emf.setDataSource(ds); emf.setPackagesToScan(""); emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean("ordersTx") @Primary JpaTransactionManager ordersTx(EntityManagerFactory ordersEmf){return new JpaTransactionManager(ordersEmf);}
}

public class PersistenceContextDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiPUAppCfg.class);
        OrderAuditService svc = ctx.getBean(OrderAuditService.class);
        svc.placeOrderWithAudit("Widget", 49.99);
        svc.placeOrderWithAudit("Gadget", 99.00);
        System.out.println("Done");
        ctx.close();
    }
}
```

How to run: same classpath

`@PersistenceContext(unitName = "ordersPU")` selects which persistence unit's proxy to inject. With two `LocalContainerEntityManagerFactoryBean` beans, Spring matches each `@PersistenceContext` by unit name. The `@Transactional("ordersTx")` qualifier ensures the right transaction manager drives the orders TX.

## 6. Walkthrough

**Level 1 — `@PersistenceContext` proxy delegation (execution order):**

1. **Application starts**: `PersistenceAnnotationBeanPostProcessor` scans `OrderRepository`. Finds `@PersistenceContext EntityManager em`. Creates a `SharedEntityManagerProxy` wrapping the `EntityManagerFactory` bean. Injects this proxy into the `em` field.
2. **`repo.save(new Order(...))` called**: Spring AOP (`@Transactional`) intercepts → `JpaTransactionManager.getTransaction()` → `emf.createEntityManager()` → `em.getTransaction().begin()` → binds real EM to `TransactionSynchronizationManager` thread-local.
3. **`em.persist(order)` called inside `save()`**: the proxy's `invoke()` method runs → `TransactionSynchronizationManager.getResource(emf)` → returns the bound real `EntityManager` → delegates `persist(order)` to it.
4. **TX commit**: `JpaTransactionManager` flushes the real EM → INSERT executed → TX committed → real EM closed → thread-local binding removed.
5. **Next `repo.save()` call**: new TX → new real EM bound to thread-local. The proxy field `em` still points to the same proxy object, but now delegates to the new real EM.

```
proxy field em = SharedEntityManagerProxy (singleton, shared, thread-safe)

Call em.find() during TX:
  proxy.invoke() → TransactionSynchronizationManager.getResource(emf) → real EM
  → real EM.find(Order.class, id) → SELECT FROM orders WHERE id=?

Call em.find() outside TX:
  proxy.invoke() → no binding found → create temporary EM → query → close
  (auto-close mode — no TX context)
```

## 7. Gotchas & takeaways

> **Never use `@Autowired EntityManager em`** in a singleton bean. `@Autowired` injects the raw `EntityManager` directly — shared across all threads → concurrency bug and stale persistence context. Always use `@PersistenceContext`.

> **`@PersistenceContext` outside a `@Transactional` method works**, but the proxy creates a temporary `EntityManager`, executes the operation, and closes it immediately. Lazy loading won't work after the method returns since the context is closed. Always wrap queries in `@Transactional`.

> **When using multiple persistence units**, annotate with `@Transactional("specificTxManagerBeanName")` — the default `@Transactional` uses the primary `PlatformTransactionManager` bean. Mixing units in one TX requires JTA (XA transactions); otherwise keep them separate.

- `@PersistenceContext EntityManager em` — inject a thread-safe TX-aware proxy, not a raw EM.
- `@PersistenceUnit EntityManagerFactory emf` — inject the raw factory; create/close EMs manually.
- `unitName` attribute — disambiguation when multiple persistence units exist.
- Never `@Autowired EntityManager` in a singleton — use `@PersistenceContext` only.
- Manually created EMs (`emf.createEntityManager()`) must always be closed in `finally`.
