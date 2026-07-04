---
card: spring-framework
gi: 285
slug: exception-translation-with-orm
title: Exception Translation with ORM
---

## 1. What it is

Spring's **exception translation** converts JPA/Hibernate vendor exceptions into its portable `DataAccessException` hierarchy, so your data-access code throws consistent Spring exceptions regardless of the underlying ORM.

The two key pieces:
1. **`@Repository`** — marks the bean as a candidate for exception translation.
2. **`PersistenceExceptionTranslationPostProcessor`** — a `BeanPostProcessor` that wraps `@Repository` beans in an AOP proxy; the proxy intercepts unchecked exceptions and routes them through registered `PersistenceExceptionTranslator`s.

```java
@Repository         // enables exception translation proxy
class OrderRepo {
    @PersistenceContext EntityManager em;

    @Transactional
    public void save(Order o) {
        em.persist(o);      // Hibernate ConstraintViolationException
                            // → Spring DataIntegrityViolationException
    }
}
```

## 2. Why & when

JPA throws `jakarta.persistence.PersistenceException` (and vendor-specific subclasses). Hibernate throws `org.hibernate.exception.ConstraintViolationException`. EclipseLink throws its own hierarchy. Without translation, every catch clause is provider-specific and every test breaks when you change ORM vendors.

Spring's `DataAccessException` hierarchy is provider-neutral:
```
DataAccessException
  ├─ DataIntegrityViolationException  (constraint, FK violation)
  ├─ OptimisticLockingFailureException
  ├─ EmptyResultDataAccessException
  ├─ TransientDataAccessResourceException
  └─ ...
```

Add `@Repository` + `PersistenceExceptionTranslationPostProcessor` and your service layer catches `DataIntegrityViolationException` regardless of whether the underlying store is Hibernate, EclipseLink, or JDBC.

## 3. Core concept

```
@Repository bean
  ↓ (AOP proxy from PersistenceExceptionTranslationPostProcessor)
  em.persist(entity)
  ↓
Hibernate throws ConstraintViolationException
  ↓
proxy.invoke() catches RuntimeException
  ↓
DataAccessUtils.translateIfNecessary(ex, translators)
  iterates registered PersistenceExceptionTranslators:
    HibernateJpaDialect.translateExceptionIfPossible(ex)
      → DataIntegrityViolationException
  ↓
throws DataIntegrityViolationException to caller
```

The `PersistenceExceptionTranslationPostProcessor` auto-discovers `PersistenceExceptionTranslator` beans in the `ApplicationContext` (both `JpaTransactionManager` and `HibernateJpaDialect` implement this interface).

Wiring: with `@Configuration + @EnableTransactionManagement`, you still need to declare the postprocessor explicitly:
```java
@Bean
PersistenceExceptionTranslationPostProcessor exTranslation() {
    return new PersistenceExceptionTranslationPostProcessor();
}
```
(Spring Boot auto-configures this for you. In plain Spring, declare it manually.)

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Service -->
  <rect x="10" y="70" width="120" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Service</text>
  <text x="70" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">catches DataAccessEx</text>
  <line x1="132" y1="95" x2="165" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr2)"/>

  <!-- Proxy -->
  <rect x="167" y="55" width="175" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="254" y="78" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Translation Proxy</text>
  <text x="254" y="92" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">(from PersistenceException-</text>
  <text x="254" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">TranslationPostProcessor)</text>
  <line x1="177" y1="109" x2="332" y2="109" stroke="#8b949e" stroke-width="0.5"/>
  <text x="254" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">catch → translateIfNecessary()</text>
  <line x1="344" y1="95" x2="387" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- @Repository -->
  <rect x="389" y="60" width="145" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="461" y="82" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Repository bean</text>
  <line x1="399" y1="88" x2="524" y2="88" stroke="#8b949e" stroke-width="0.5"/>
  <text x="461" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">em.persist(entity)</text>
  <text x="461" y="118" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">↓ ConstraintViolEx</text>

  <!-- translator -->
  <line x1="461" y1="132" x2="461" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="461" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">→ DataIntegrityViolationException</text>
</svg>

## 5. Runnable example

Scenario: an **order management service** — observe exception translation at three levels of complexity.

### Level 1 — Basic

`@Repository` + `PersistenceExceptionTranslationPostProcessor` translate constraint violations.

```java
// ExceptionTranslationDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="orders",
    uniqueConstraints=@UniqueConstraint(columnNames="order_ref"))
class Order {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(name="order_ref") String ref; double total;
    public Order(){} public Order(String r,double t){ref=r;total=t;}
    public Long getId(){return id;} public String getRef(){return ref;}
    public String toString(){return "Order["+id+","+ref+","+total+"]";}
}

@Repository     // ← required for exception translation proxy
class OrderRepo {
    @PersistenceContext EntityManager em;

    @Transactional
    public Order save(Order order){ em.persist(order); return order; }

    @Transactional(readOnly=true)
    public List<Order> findAll(){
        return em.createQuery("FROM Order", Order.class).getResultList(); }
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
        var a=new HibernateJpaVendorAdapter(); a.setGenerateDdl(true); emf.setJpaVendorAdapter(a); return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
    @Bean PersistenceExceptionTranslationPostProcessor exTranslation(){
        return new PersistenceExceptionTranslationPostProcessor();  // installs translation AOP proxy
    }
}

public class ExceptionTranslationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        OrderRepo repo = ctx.getBean(OrderRepo.class);

        repo.save(new Order("ORD-001", 100.00));

        // duplicate ref → Hibernate ConstraintViolationException
        // → translated to Spring DataIntegrityViolationException
        try {
            repo.save(new Order("ORD-001", 200.00));
        } catch (DataIntegrityViolationException e) {
            System.out.println("Translated: " + e.getClass().getSimpleName());
        }

        System.out.println("Orders: " + repo.findAll());
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. ExceptionTranslationDemo.java`

Without `@Repository`, Hibernate's `ConstraintViolationException` would propagate untranslated. With `@Repository` + `PersistenceExceptionTranslationPostProcessor`, the proxy catches it and calls the registered `PersistenceExceptionTranslator`s to produce a `DataIntegrityViolationException`.

---

### Level 2 — Intermediate

Distinguish `DataIntegrityViolationException` vs `OptimisticLockingFailureException`.

```java
// ExceptionTranslationDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.*;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="products",
    uniqueConstraints=@UniqueConstraint(columnNames="sku"))
class Product {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String sku; double price;
    @Version int version;  // optimistic locking
    public Product(){} public Product(String s,double p){sku=s;price=p;}
    public Long getId(){return id;} public void setPrice(double p){price=p;}
    public String toString(){return "Product["+sku+","+price+",v"+version+"]";}
}

@Repository
class ProductRepo {
    @PersistenceContext EntityManager em;
    @Transactional public Product save(Product p){ em.persist(p); return p; }
    @Transactional(readOnly=true) public Product findById(Long id){ return em.find(Product.class, id); }
    @Transactional public void updatePrice(Long id, double price){
        Product p=em.find(Product.class,id);
        if(p!=null) p.setPrice(price);
    }
}

@Service
class ProductService {
    private final ProductRepo repo;
    ProductService(ProductRepo r){ repo=r; }

    public void demonstrateTranslation(Long id) {
        // simulate stale-state optimistic locking conflict
        Product p = repo.findById(id);
        // In a real race: another TX updates + increments version
        // We simulate by detaching and re-persisting with stale version
        try {
            repo.updatePrice(id, 99.99);  // normal update
            System.out.println("Price updated successfully");
        } catch (OptimisticLockingFailureException e) {
            System.out.println("Optimistic lock: " + e.getClass().getSimpleName());
        } catch (DataIntegrityViolationException e) {
            System.out.println("Integrity: " + e.getClass().getSimpleName());
        } catch (DataAccessException e) {
            System.out.println("Other DAE: " + e.getClass().getSimpleName());
        }
    }
}

// (AppCfg same as Level 1 but scan includes Product)

public class ExceptionTranslationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        ProductRepo repo = ctx.getBean(ProductRepo.class);
        ProductService svc = ctx.getBean(ProductService.class);

        Product p = repo.save(new Product("SKU-001", 49.99));

        // duplicate SKU → DataIntegrityViolationException
        try {
            repo.save(new Product("SKU-001", 99.99));
        } catch (DataIntegrityViolationException e) {
            System.out.println("Duplicate SKU caught as: " + e.getClass().getSimpleName());
        }

        svc.demonstrateTranslation(p.getId());
        ctx.close();
    }
}
```

How to run: same classpath

`@Version` field enables optimistic locking. When a stale entity conflicts, Hibernate throws `StaleObjectStateException` which `HibernateJpaDialect` translates to `OptimisticLockingFailureException`. Each Spring `DataAccessException` subclass corresponds to a specific failure mode — catch the right level.

---

### Level 3 — Advanced

Custom `PersistenceExceptionTranslator` for domain-specific exceptions.

```java
// ExceptionTranslationDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.dao.support.PersistenceExceptionTranslator;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;

// Domain exception (not a Spring class)
class DuplicateOrderException extends DataIntegrityViolationException {
    DuplicateOrderException(String msg){ super(msg); }
}

// Custom translator for order-specific exceptions
class OrderExceptionTranslator implements PersistenceExceptionTranslator {
    @Override
    public DataAccessException translateExceptionIfPossible(RuntimeException ex) {
        // intercept only ConstraintViolationException with our constraint name
        if (ex.getMessage() != null &&
            ex.getMessage().contains("ORDERS") &&
            ex.getMessage().contains("ORDER_REF")) {
            return new DuplicateOrderException("Duplicate order reference: " + extractRef(ex));
        }
        return null;  // null = not handled by this translator → next translator tries
    }
    private String extractRef(RuntimeException ex){
        String msg = ex.getMessage();
        int i = msg.indexOf("'"); int j = msg.lastIndexOf("'");
        return (i>=0 && j>i) ? msg.substring(i+1,j) : "unknown";
    }
}

@Entity @Table(name="orders",
    uniqueConstraints=@UniqueConstraint(name="ORDER_REF",columnNames="order_ref"))
class Order {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(name="order_ref") String ref; double total;
    public Order(){} public Order(String r,double t){ref=r;total=t;}
}

@Repository
class OrderRepo2 {
    @PersistenceContext EntityManager em;
    @Transactional public void save(Order o){ em.persist(o); }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfgCustom {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:ordersadv;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        var a=new HibernateJpaVendorAdapter(); a.setGenerateDdl(true); emf.setJpaVendorAdapter(a); return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
    @Bean PersistenceExceptionTranslationPostProcessor exTranslation(){
        return new PersistenceExceptionTranslationPostProcessor();
    }
    @Bean PersistenceExceptionTranslator orderTranslator(){
        return new OrderExceptionTranslator();  // registered as a PET bean → auto-discovered
    }
}

public class ExceptionTranslationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfgCustom.class);
        OrderRepo2 repo = ctx.getBean(OrderRepo2.class);

        repo.save(new Order("ORD-001", 100.00));
        try {
            repo.save(new Order("ORD-001", 200.00));
        } catch (DuplicateOrderException e) {
            System.out.println("Custom exception: " + e.getClass().getSimpleName() + " — " + e.getMessage());
        } catch (DataIntegrityViolationException e) {
            System.out.println("Fallback: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}
```

How to run: same classpath

Any bean implementing `PersistenceExceptionTranslator` is auto-discovered by `PersistenceExceptionTranslationPostProcessor`. The custom translator runs first; returning `null` defers to the next translator. Returning a non-null `DataAccessException` short-circuits — the returned exception is thrown to the caller.

## 6. Walkthrough

**Level 1 — duplicate save, full translation flow:**

1. `repo.save(new Order("ORD-001", 200.00))` → AOP proxy intercepts (two proxies layered: `@Transactional` proxy + translation proxy).
2. `@Transactional` proxy begins TX, delegates to real `OrderRepo.save()`.
3. `em.persist(order)` enqueues in persistence context.
4. TX commit → `em.flush()` → Hibernate issues `INSERT` → H2 raises `UNIQUE constraint violation`.
5. Hibernate wraps in `org.hibernate.exception.ConstraintViolationException`.
6. Unchecked exception exits `@Transactional` proxy → proxy rolls back TX, re-throws exception.
7. Translation proxy (from `PersistenceExceptionTranslationPostProcessor`) catches the `RuntimeException`.
8. Iterates `PersistenceExceptionTranslator` beans: `HibernateJpaDialect.translateExceptionIfPossible()` matches → returns `DataIntegrityViolationException`.
9. Translation proxy throws `DataIntegrityViolationException` → reaches caller's `catch` block.

## 7. Gotchas & takeaways

> **`@Repository` is necessary but not sufficient.** You also need `PersistenceExceptionTranslationPostProcessor` in the `ApplicationContext`. Without the postprocessor, `@Repository` is just a stereotype marker — no translation proxy is installed. Spring Boot configures the postprocessor automatically; plain Spring does not.

> **Translation only catches unchecked exceptions** that escape the `@Repository` method. Exceptions swallowed inside the method are never seen by the proxy.

> **`EmptyResultDataAccessException` is NOT produced automatically.** `em.getSingleResult()` throws `NoResultException` (JPA checked), which the translation proxy converts to `EmptyResultDataAccessException`. `em.find()` returns `null` — not an exception.

- `@Repository` + `PersistenceExceptionTranslationPostProcessor` = translation pair.
- Standard translations: `ConstraintViolationException` → `DataIntegrityViolationException`, `StaleObjectStateException` → `OptimisticLockingFailureException`.
- Custom translator: implement `PersistenceExceptionTranslator`, declare as `@Bean`, return `null` to defer.
- Spring Boot auto-configures the postprocessor; plain Spring requires explicit `@Bean`.
