---
card: spring-framework
gi: 256
slug: persistenceexceptiontranslationpostprocessor
title: PersistenceExceptionTranslationPostProcessor
---

## 1. What it is

`PersistenceExceptionTranslationPostProcessor` (PETPP) is a `BeanPostProcessor` that scans all beans in the application context for the `@Repository` annotation. For each matching bean it wraps the bean in a `PersistenceExceptionTranslationAdvisor`-backed proxy — a proxy that intercepts thrown `RuntimeException`s from the bean's methods and delegates to registered `PersistenceExceptionTranslator` beans for mapping to `DataAccessException`.

```java
// Declare once — then all @Repository beans get the proxy automatically
@Bean
public PersistenceExceptionTranslationPostProcessor persistenceExceptionTranslationPostProcessor() {
    return new PersistenceExceptionTranslationPostProcessor();
}
```

In Spring Boot applications with `spring-data-jpa` on the classpath, this bean is auto-configured.

## 2. Why & when

Without PETPP, annotating a class `@Repository` does nothing at runtime — it's just a marker. PETPP is the mechanism that activates exception translation for all `@Repository`-annotated beans in a single registration.

Register PETPP explicitly when:
- Using plain Spring (not Spring Boot) with JPA, Hibernate, or raw JDBC DAOs.
- You have hand-written DAOs that use `EntityManager` or `Connection` directly and you want portable exceptions.

In Spring Boot: `JpaRepositoriesAutoConfiguration` registers PETPP for you.

## 3. Core concept

PETPP implements `BeanPostProcessor`. In `postProcessAfterInitialization`:
1. It checks whether the bean class or any superclass/interface is annotated `@Repository`.
2. If so, it creates a `PersistenceExceptionTranslationAdvisor` wrapping a `PersistenceExceptionTranslationInterceptor`.
3. It uses `ProxyFactory` to wrap the bean (JDK proxy if interface available, CGLIB subclass otherwise).

The interceptor's `invoke()`:
1. Calls the target method.
2. If any `RuntimeException` escapes, calls `DataAccessUtils.translateIfNecessary(ex, translator)`.
3. The translator chain: all `PersistenceExceptionTranslator` beans in the context. For each: `translator.translateExceptionIfPossible(ex)`. First non-null wins.
4. Throws translated exception or rethrows original if no translation found.

PETPP is configured with one property: `repositoryAnnotationType` (default: `@Repository`). Overridable to a custom annotation.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- App Context startup -->
  <rect x="10" y="10" width="300" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="155" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ApplicationContext startup</text>
  <line x1="20" y1="40" x2="300" y2="40" stroke="#8b949e" stroke-width="0.5"/>
  <text x="155" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PETPP.postProcessAfterInitialization(bean)</text>
  <text x="155" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ if @Repository → wrap in proxy</text>
  <text x="155" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ else → return bean unchanged</text>

  <!-- Translators -->
  <rect x="330" y="10" width="360" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="32" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">PersistenceExceptionTranslator chain</text>
  <line x1="340" y1="40" x2="680" y2="40" stroke="#8b949e" stroke-width="0.5"/>
  <text x="510" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">HibernateExceptionTranslator</text>
  <text x="510" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">JpaDialect (EclipseLink, etc.)</text>
  <text x="510" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">CustomTranslator (your @Bean)</text>

  <!-- Runtime interception -->
  <rect x="10" y="130" width="680" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="150" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Runtime: method call on @Repository proxy</text>
  <line x1="20" y1="158" x2="680" y2="158" stroke="#8b949e" stroke-width="0.5"/>
  <text x="350" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">target throws RuntimeException → translator.translateExceptionIfPossible(ex) → DataAccessException</text>
  <text x="350" y="198" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">no translation found → original RuntimeException rethrown</text>
</svg>

PETPP wraps every `@Repository` bean at context startup; the proxy translates exceptions at runtime.

## 5. Runnable example

Scenario: a **`InventoryDao`** using JPA — showing PETPP effect, custom repository annotation, and lazy initialization with a Spring Boot context.

### Level 1 — Basic

Registering PETPP in a plain Spring context — enable translation for all `@Repository` DAOs.

```java
// PetppDemo.java
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;

@Configuration
public class PetppDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        var b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds); b.setPackagesToScan("demo");
        var va = new HibernateJpaVendorAdapter(); va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va); return b;
    }
    @Bean public JpaTransactionManager transactionManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }

    // THE KEY DECLARATION — enables @Repository proxy wrapping
    @Bean
    public PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }

    @Bean public InventoryDao inventoryDao(EntityManagerFactory emf) { return new InventoryDao(emf); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PetppDemo.class);
        InventoryDao dao = ctx.getBean(InventoryDao.class);

        dao.save(new Item(1L, "Wrench"));
        System.out.println("Saved item 1");

        try {
            dao.save(new Item(1L, "Duplicate Wrench"));   // same id=1 → exception
        } catch (DataAccessException e) {
            System.out.println("PETPP translated: " + e.getClass().getSimpleName());
            System.out.println("Caller sees DataAccessException, not PersistenceException");
        }
        ctx.close();
    }
}

@Repository
class InventoryDao {
    @PersistenceContext EntityManager em;
    InventoryDao(EntityManagerFactory emf) { this.em = emf.createEntityManager(); }
    @org.springframework.transaction.annotation.Transactional
    public void save(Item item) { em.persist(item); }
}

@Entity class Item { @Id Long id; String name; Item() {} Item(Long id, String n){this.id=id;this.name=n;} }
```

How to run: `java -cp spring-context.jar:spring-orm.jar:hibernate-core.jar:h2.jar:. PetppDemo.java`

`PersistenceExceptionTranslationPostProcessor` is registered as a `@Bean`. At context startup, it wraps `InventoryDao` (which has `@Repository`) in a proxy. When the DAO throws `EntityExistsException`, the proxy translates it to `DataIntegrityViolationException`.

---

### Level 2 — Intermediate

Verifying the proxy exists at runtime using `AopUtils`, and inspecting the advisors applied.

```java
// PetppDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;

@Configuration
public class PetppDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        var b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds); b.setPackagesToScan("demo");
        var va = new HibernateJpaVendorAdapter(); va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va); return b;
    }
    @Bean public PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }
    @Bean public InventoryDao inventoryDao(EntityManagerFactory emf) { return new InventoryDao(emf); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PetppDemo.class);
        InventoryDao dao = ctx.getBean(InventoryDao.class);

        System.out.println("Is AOP proxy: " + AopUtils.isAopProxy(dao));
        System.out.println("Is CGLIB proxy: " + AopUtils.isCglibProxy(dao));
        System.out.println("Target class: " + AopUtils.getTargetClass(dao).getSimpleName());

        if (dao instanceof Advised advised) {
            System.out.println("Advisors:");
            for (var advisor : advised.getAdvisors()) {
                System.out.println("  " + advisor.getClass().getSimpleName());
            }
        }
        ctx.close();
    }
}

@Repository
class InventoryDao {
    @PersistenceContext EntityManager em;
    InventoryDao(EntityManagerFactory emf) { this.em = emf.createEntityManager(); }
    public void save(Item item) { em.persist(item); }
}

@Entity class Item { @Id Long id; String name; Item() {} Item(Long id, String n){this.id=id;this.name=n;} }
```

How to run: same classpath

`AopUtils.isAopProxy(dao)` returns `true` — PETPP added a CGLIB proxy. The `Advised` cast reveals the advisor list, which includes `PersistenceExceptionTranslationAdvisor`. Without PETPP, `isAopProxy()` returns `false`.

---

### Level 3 — Advanced

Override `repositoryAnnotationType` to use a custom `@Dao` annotation instead of `@Repository`.

```java
// PetppDemo.java
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;
import java.lang.annotation.*;

@Configuration
public class PetppDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        var b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds); b.setPackagesToScan("demo");
        var va = new HibernateJpaVendorAdapter(); va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va); return b;
    }

    // PETPP configured to translate @Dao annotated beans (instead of @Repository)
    @Bean
    public PersistenceExceptionTranslationPostProcessor petpp() {
        var p = new PersistenceExceptionTranslationPostProcessor();
        p.setRepositoryAnnotationType(Dao.class);   // custom annotation
        return p;
    }

    @Bean public WarehouseDao warehouseDao(EntityManagerFactory emf) { return new WarehouseDao(emf); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PetppDemo.class);
        WarehouseDao dao = ctx.getBean(WarehouseDao.class);
        dao.save(new Item(10L, "Pallet Jack"));
        try {
            dao.save(new Item(10L, "Duplicate"));
        } catch (DataAccessException e) {
            System.out.println("Custom @Dao translated: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}

// Custom DAO annotation — replaces @Repository for translation purposes
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@interface Dao {}

@Dao   // NOT @Repository — but PETPP is configured to recognize @Dao
class WarehouseDao {
    @PersistenceContext EntityManager em;
    WarehouseDao(EntityManagerFactory emf) { this.em = emf.createEntityManager(); }
    @org.springframework.transaction.annotation.Transactional
    public void save(Item item) { em.persist(item); }
}

@Entity class Item { @Id Long id; String name; Item() {} Item(Long id, String n){this.id=id;this.name=n;} }
```

How to run: same classpath

`setRepositoryAnnotationType(Dao.class)` instructs PETPP to proxy beans annotated `@Dao` instead of `@Repository`. This is useful when your project has a naming convention different from Spring's default, or when you need to exclude some `@Repository` beans from translation.

## 6. Walkthrough

**Level 1 — PETPP lifecycle (context startup to runtime):**

```
ApplicationContext.refresh()
  → BeanPostProcessor registration phase:
      PETPP registered as BeanPostProcessor

  → Bean instantiation phase:
      InventoryDao instance created (target)
      PETPP.postProcessAfterInitialization(inventoryDao, "inventoryDao"):
        → check: is InventoryDao annotated @Repository? YES
        → collect PersistenceExceptionTranslator beans from context:
             [HibernateExceptionTranslator (via JpaVendorAdapter)]
        → ProxyFactory.getProxy():
             InventoryDao has no interfaces → CGLIB subclass
             add PersistenceExceptionTranslationAdvisor
             return CGLIB proxy
      → replace bean "inventoryDao" with proxy in context

Runtime: dao.save(new Item(1L, "Duplicate"))
  → CGLIB proxy.save()
  → PersistenceExceptionTranslationInterceptor.invoke()
  → target.save()
       → em.persist() → Hibernate throws EntityExistsException
  ← exception caught by interceptor
  → HibernateExceptionTranslator.translateExceptionIfPossible(EntityExistsException)
       → return DataIntegrityViolationException
  ← throw DataIntegrityViolationException
```

## 7. Gotchas & takeaways

> **PETPP and `@Transactional` proxies stack.** When a DAO is both `@Repository` and `@Transactional`, it gets TWO proxies: one from PETPP (exception translation) and one from `@EnableTransactionManagement` (transaction management). Spring's AOP merges these into a single CGLIB proxy with both advisors in most cases, but the ordering matters: exception translation runs inside the transaction boundary so that rollback occurs before translation.

> **PETPP does NOT translate checked exceptions.** Only `RuntimeException` subclasses are intercepted. If your DAO throws a checked `IOException`, it escapes unmodified.

> **In Spring Boot, you do not need to declare PETPP.** `JpaRepositoriesAutoConfiguration` registers it when `spring-data-jpa` is on the classpath. Declaring it twice causes no harm — Spring deduplicates `BeanPostProcessor` implementations by type.

- PETPP is a `BeanPostProcessor` — wraps `@Repository` beans in exception-translating proxies at startup.
- One PETPP declaration enables exception translation for ALL `@Repository`-annotated beans in the context.
- `setRepositoryAnnotationType()` — customize which annotation triggers translation.
- Spring Boot auto-configures PETPP — no explicit declaration needed with spring-data-jpa.
- Only `RuntimeException`s are intercepted; checked exceptions pass through unchanged.
