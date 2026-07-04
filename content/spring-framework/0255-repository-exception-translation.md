---
card: spring-framework
gi: 255
slug: repository-exception-translation
title: "@Repository & exception translation"
---

## 1. What it is

`@Repository` is a Spring stereotype annotation (alongside `@Service`, `@Controller`, `@Component`) that marks a class as a data-access object (DAO). Beyond marking, it enables **automatic exception translation**: when `PersistenceExceptionTranslationPostProcessor` is present in the application context, Spring wraps the DAO in a proxy that intercepts any thrown persistence exception and translates it to a `DataAccessException` subclass.

```java
@Repository
public class UserJpaDao {
    @PersistenceContext EntityManager em;

    public User findById(Long id) {
        return em.find(User.class, id);   // PersistenceException → DataAccessException
    }
}
```

Without `@Repository`, exceptions from direct JPA/Hibernate/JDBC calls escape as raw vendor exceptions.

## 2. Why & when

`@Transactional` handles transaction boundaries. `@Repository` handles **exception translation** for code that lives outside Spring-managed templates.

Use `@Repository` when:
- Writing JPA/Hibernate DAOs that call `EntityManager` directly.
- Writing JDBC DAOs with raw `Connection` or `PreparedStatement`.
- Using Spring Data repositories (they inherit this behavior automatically).

You do NOT need `@Repository` when using `JdbcTemplate`, `NamedParameterJdbcTemplate`, or `JpaRepository` — these templates translate internally already.

## 3. Core concept

Spring's post-processor `PersistenceExceptionTranslationPostProcessor` (PETPP) scans every bean annotated with `@Repository` and wraps it in a `PersistenceExceptionTranslationInterceptor`. This interceptor:

1. Calls the target method.
2. Catches any `RuntimeException`.
3. Delegates to the registered `PersistenceExceptionTranslator` (e.g., `HibernateExceptionTranslator`, `JpaDialect`, or `SQLErrorCodeSQLExceptionTranslator`).
4. If a translation is found, throws the `DataAccessException` subclass. Otherwise rethrows the original.

Translation happens per-exception-translator. Spring auto-detects translators registered in the context (one per persistence provider).

```
@Repository bean method throws HibernateException
  → PersistenceExceptionTranslationInterceptor catches it
  → PersistenceExceptionTranslator.translateExceptionIfPossible(ex)
     HibernateExceptionTranslator:
       ConstraintViolationException → DataIntegrityViolationException
       ObjectNotFoundException → EmptyResultDataAccessException
       ...
  → DataAccessException thrown to caller
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="80" width="110" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Service</text>
  <line x1="122" y1="105" x2="178" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Proxy -->
  <rect x="178" y="60" width="170" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="263" y="84" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Repository Proxy</text>
  <line x1="188" y1="92" x2="338" y2="92" stroke="#8b949e" stroke-width="0.5"/>
  <text x="263" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">ExceptionTranslationInterceptor</text>
  <text x="263" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">catch → translate → rethrow</text>
  <line x1="350" y1="105" x2="406" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DAO -->
  <rect x="406" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="466" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">DAO impl</text>
  <text x="466" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">EntityManager</text>

  <!-- Translator -->
  <line x1="263" y1="152" x2="263" y2="190" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="165" y="188" width="200" height="16" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="265" y="200" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">PersistenceExceptionTranslator</text>

  <!-- JPA exception -->
  <rect x="538" y="60" width="150" height="90" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="613" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JPA Exceptions</text>
  <line x1="548" y1="88" x2="678" y2="88" stroke="#8b949e" stroke-width="0.5"/>
  <text x="613" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">ConstraintViolation →</text>
  <text x="613" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">DataIntegrityViolation</text>
  <text x="613" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">ObjectNotFound →</text>
  <text x="613" y="148" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">EmptyResultDataAccess</text>
</svg>

`@Repository` proxy intercepts thrown exceptions and delegates to the registered translator before re-throwing.

## 5. Runnable example

Scenario: a **`ProductDao`** using JPA `EntityManager` directly — demonstrating that `@Repository` translates JPA exceptions while a plain POJO DAO does not.

### Level 1 — Basic

`@Repository` DAO with `EntityManager` — `PersistenceException` becomes `DataAccessException`.

```java
// RepositoryExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;

@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = EnableLoadTimeWeaving.AspectJWeaving.AUTODETECT)
public class RepositoryExceptionDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        LocalContainerEntityManagerFactoryBean b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds);
        b.setPackagesToScan("com.example");
        HibernateJpaVendorAdapter va = new HibernateJpaVendorAdapter();
        va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va);
        return b;
    }
    @Bean public PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }
    @Bean public ProductDao productDao(EntityManagerFactory emf) {
        return new ProductDao(emf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RepositoryExceptionDemo.class);
        ProductDao dao = ctx.getBean(ProductDao.class);
        dao.save(new Product(null, "Widget"));
        // Attempt duplicate — PersistenceException → DataIntegrityViolationException
        try {
            dao.save(new Product(1L, "Duplicate Widget"));   // same id=1
        } catch (DataAccessException e) {
            System.out.println("Caught DataAccessException: " + e.getClass().getSimpleName());
            System.out.println("Translation worked — no JPA-specific catch needed");
        }
        ctx.close();
    }
}

@Repository
class ProductDao {
    @PersistenceContext EntityManager em;
    ProductDao(EntityManagerFactory emf) { this.em = emf.createEntityManager(); }

    @org.springframework.transaction.annotation.Transactional
    public void save(Product p) { em.persist(p); }
}

@Entity class Product {
    @Id Long id; String name;
    Product() {} Product(Long id, String n) { this.id=id; this.name=n; }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:hibernate-core.jar:h2.jar:. RepositoryExceptionDemo.java`

`ProductDao` is annotated `@Repository` and `PersistenceExceptionTranslationPostProcessor` is registered. When `em.persist()` throws `EntityExistsException` (a JPA `PersistenceException`), the proxy intercepts it, `HibernateExceptionTranslator` maps it to `DataIntegrityViolationException`, and that is what the caller sees.

---

### Level 2 — Intermediate

Compare `@Repository` DAO (translated) vs plain `@Component` DAO (raw exception) for the same operation.

```java
// RepositoryExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;

@Configuration
public class RepositoryExceptionDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        var b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds); b.setPackagesToScan("com.example");
        var va = new HibernateJpaVendorAdapter(); va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va); return b;
    }
    @Bean public PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RepositoryExceptionDemo.class);

        // @Repository bean — exception is translated
        var repoDao = ctx.getBean(AnnotatedProductDao.class);
        try { repoDao.saveDuplicate(); }
        catch (DataAccessException e) {
            System.out.println("@Repository throws: " + e.getClass().getSimpleName());
        }

        // @Component bean — raw JPA exception escapes
        var plainDao = ctx.getBean(PlainProductDao.class);
        try { plainDao.saveDuplicate(); }
        catch (PersistenceException e) {
            System.out.println("@Component throws raw: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}

@Repository
class AnnotatedProductDao {
    @PersistenceContext EntityManager em;
    @org.springframework.transaction.annotation.Transactional
    public void saveDuplicate() { em.persist(new Product(1L,"A")); em.persist(new Product(1L,"B")); }
}

@Component
class PlainProductDao {
    @PersistenceContext EntityManager em;
    @org.springframework.transaction.annotation.Transactional
    public void saveDuplicate() { em.persist(new Product(2L,"C")); em.persist(new Product(2L,"D")); }
}

@Entity class Product {
    @Id Long id; String name;
    Product() {} Product(Long id, String n) { this.id=id; this.name=n; }
}
```

How to run: same classpath

`@Repository` gets the translation proxy; `@Component` does not. The `@Component` DAO throws raw `EntityExistsException` which the caller must catch as `PersistenceException` — vendor-specific, not portable.

---

### Level 3 — Advanced

Custom `PersistenceExceptionTranslator` — translate a domain-specific `ProductNotFoundException` to `EmptyResultDataAccessException`.

```java
// RepositoryExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.dao.support.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.embedded.*;

@Configuration
public class RepositoryExceptionDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }
    @Bean public LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
        var b = new LocalContainerEntityManagerFactoryBean();
        b.setDataSource(ds); b.setPackagesToScan("com.example");
        var va = new HibernateJpaVendorAdapter(); va.setGenerateDdl(true);
        b.setJpaVendorAdapter(va); return b;
    }
    // Custom translator — registered as a bean, auto-detected by PETPP
    @Bean public PersistenceExceptionTranslator customTranslator() {
        return ex -> {
            if (ex instanceof ProductNotFoundException pnfe)
                return new EmptyResultDataAccessException("Product not found: " + pnfe.getMessage(), 1);
            return null;   // return null = cannot translate, try next translator
        };
    }
    @Bean public PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RepositoryExceptionDemo.class);
        var dao = ctx.getBean(CatalogDao.class);

        // Domain exception → custom translator → EmptyResultDataAccessException
        try { dao.findBySku("UNKNOWN-SKU"); }
        catch (EmptyResultDataAccessException e) {
            System.out.println("Translated: " + e.getClass().getSimpleName() + " — " + e.getMessage());
        }
        ctx.close();
    }
}

class ProductNotFoundException extends RuntimeException {
    ProductNotFoundException(String msg) { super(msg); }
}

@Repository
class CatalogDao {
    @PersistenceContext EntityManager em;
    public Product findBySku(String sku) {
        // Domain-level not-found exception — translated by customTranslator
        throw new ProductNotFoundException(sku);
    }
}

@Entity class Product { @Id Long id; String name; Product() {} }
```

How to run: same classpath

Custom `PersistenceExceptionTranslator` beans are automatically discovered by `PersistenceExceptionTranslationPostProcessor` alongside the built-in ones. Returning `null` from `translateExceptionIfPossible` defers to the next translator in chain.

## 6. Walkthrough

**Level 1 — `@Repository` proxy interception flow:**

```
Service calls ProductDao.save(product)
  → Spring proxy (PersistenceExceptionTranslationInterceptor) intercepts

  → target ProductDao.save(product) called
      em.persist(product)
        → Hibernate: ConstraintViolationException (PersistenceException)
        ← exception propagates out of target method

  ← PersistenceExceptionTranslationInterceptor.invoke() catches RuntimeException

  → translateIfNecessary(ex):
      for each PersistenceExceptionTranslator in context:
        HibernateExceptionTranslator.translateExceptionIfPossible(ex)
          ConstraintViolationException → DataIntegrityViolationException
          return DataIntegrityViolationException (not null)

  ← throw DataIntegrityViolationException (DataAccessException subclass)

Service sees DataAccessException — no JPA imports needed
```

## 7. Gotchas & takeaways

> **`@Repository` alone is NOT enough.** Exception translation only works if `PersistenceExceptionTranslationPostProcessor` is registered in the context. Without it, `@Repository` is just a stereotype marker. In Spring Boot, `@SpringBootApplication` auto-configures the PETPP when JPA is on the classpath.

> **Translation requires the exception to propagate from the target method, not be caught inside it.** If the DAO catches and handles the JPA exception internally, the proxy has nothing to intercept.

> **Spring Data `JpaRepository` beans already get translation** — they extend `SimpleJpaRepository` which is itself annotated `@Repository`. You only need to add `@Repository` to your own hand-written DAO classes.

- `@Repository` — marks DAO beans; enables exception translation via proxy when PETPP is present.
- `PersistenceExceptionTranslationPostProcessor` — the post-processor that creates the proxy for `@Repository` beans.
- Translation chain: all `PersistenceExceptionTranslator` beans in context are tried in order; first non-null result wins.
- Custom translator: implement `PersistenceExceptionTranslator`, register as `@Bean` — auto-discovered.
- Spring Boot: PETPP is auto-configured when spring-data-jpa is on classpath — no explicit declaration needed.
