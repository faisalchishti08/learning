---
card: spring-framework
gi: 279
slug: jpa-integration-localcontainerentitymanagerfactorybean
title: JPA integration (LocalContainerEntityManagerFactoryBean)
---

## 1. What it is

`LocalContainerEntityManagerFactoryBean` is Spring's factory bean that creates a JPA `EntityManagerFactory` (EMF) — the root of the JPA persistence layer — in a Spring-managed, "container-managed" style without requiring a Java EE application server.

```java
@Bean
public LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource ds) {
    LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
    emf.setDataSource(ds);
    emf.setPackagesToScan("com.example.domain");
    emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
    Properties props = new Properties();
    props.setProperty("hibernate.hbm2ddl.auto", "create-drop");
    emf.setJpaProperties(props);
    return emf;
}
```

The difference from the Hibernate-native path:
- `LocalContainerEntityManagerFactoryBean` → JPA standard; `EntityManagerFactory` → `EntityManager`
- `LocalSessionFactoryBean` → Hibernate-native; `SessionFactory` → `Session`

Both ultimately use Hibernate under the hood (with the default `HibernateJpaVendorAdapter`), but the JPA path is portable to EclipseLink or any other JPA provider.

## 2. Why & when

The JPA path is preferred for new Spring applications because:
- **Standard API** — your code compiles against `jakarta.persistence.*` not `org.hibernate.*`.
- **Spring Data JPA** — `JpaRepository` and `@Query` are JPA-based; they require an `EntityManagerFactory`.
- **Portability** — switching from Hibernate to EclipseLink is a config change, not a code change.
- **Testability** — JPA standard interfaces are easier to mock.

Use `LocalSessionFactoryBean` only when you need Hibernate-specific annotations or APIs that JPA doesn't expose.

## 3. Core concept

`LocalContainerEntityManagerFactoryBean` performs container-level bootstrapping:

1. Loads entity classes via `packagesToScan` (or via `persistence.xml` if present).
2. Calls `JpaVendorAdapter.postProcessEntityManagerFactory()` — vendor-specific setup.
3. Builds the `EntityManagerFactory` by calling `PersistenceProvider.createContainerEntityManagerFactory()`.
4. Exposes it as a singleton `@Bean`.

`JpaVendorAdapter` implementations:
| Class | Provider |
|---|---|
| `HibernateJpaVendorAdapter` | Hibernate ORM (default in Spring Boot) |
| `EclipseLinkJpaVendorAdapter` | EclipseLink |

`JpaTransactionManager(entityManagerFactory)` drives `@Transactional` for the JPA path — it binds an `EntityManager` to the thread-local transaction and commits/rolls back via the JPA TX API.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Config class -->
  <rect x="10" y="70" width="175" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">LocalContainerEMFBean</text>
  <text x="97" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setDataSource()</text>
  <text x="97" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setPackagesToScan()</text>

  <line x1="187" y1="100" x2="230" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- EntityManagerFactory -->
  <rect x="232" y="75" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="307" y="98" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EntityManagerFactory</text>
  <text x="307" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">thread-safe singleton</text>

  <line x1="384" y1="100" x2="427" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JpaTransactionManager -->
  <rect x="429" y="65" width="165" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="511" y="88" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JpaTransactionManager</text>
  <line x1="439" y1="94" x2="584" y2="94" stroke="#8b949e" stroke-width="0.5"/>
  <text x="511" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="511" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">begin/commit/rollback</text>

  <!-- EntityManager per TX -->
  <rect x="232" y="150" width="150" height="36" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="307" y="167" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">EntityManager (per TX)</text>
  <text x="307" y="179" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">not thread-safe</text>
  <line x1="307" y1="127" x2="307" y2="148" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>
</svg>

`LocalContainerEntityManagerFactoryBean` builds the `EntityManagerFactory`. `JpaTransactionManager` opens one `EntityManager` per transaction.

## 5. Runnable example

Scenario: an **online store** — configure JPA with `LocalContainerEntityManagerFactoryBean`, persist and query entities using standard JPA API.

### Level 1 — Basic

Configure and verify `EntityManagerFactory` + basic JPA CRUD.

```java
// JpaIntegrationDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name = "items")
class Item {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) Long id;
    String name; double price; String status;
    public Item(){}
    public Item(String n, double p, String s){name=n; price=p; status=s;}
    public Long getId(){return id;} public String getName(){return name;}
    public double getPrice(){return price;} public String getStatus(){return status;}
    public String toString(){return "Item["+id+","+name+","+price+","+status+"]";}
}

@Configuration @EnableTransactionManagement
class JpaCfg {
    @Bean DataSource ds(){
        var d = new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:store;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource ds) {
        var emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds);
        emf.setPackagesToScan("");  // scan default package
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p = new Properties();
        p.setProperty("hibernate.hbm2ddl.auto", "create-drop");
        p.setProperty("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        emf.setJpaProperties(p);
        return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }
}

public class JpaIntegrationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JpaCfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // EMF metadata
        System.out.println("JPA provider: " + emf.getProperties().get("hibernate.dialect"));

        // Persist items
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            em.persist(new Item("Widget",  9.99,  "AVAILABLE"));
            em.persist(new Item("Gadget",  24.99, "AVAILABLE"));
            em.persist(new Item("Sensor",  49.99, "OUT_OF_STOCK"));
            em.close(); return null;
        });

        // Query via JPQL
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            List<Item> available = em.createQuery(
                "SELECT i FROM Item i WHERE i.status = 'AVAILABLE' ORDER BY i.price", Item.class)
                .getResultList();
            System.out.println("Available items:");
            available.forEach(i -> System.out.printf("  %-10s $%.2f%n", i.getName(), i.getPrice()));
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. JpaIntegrationDemo.java`

`LocalContainerEntityManagerFactoryBean.afterPropertiesSet()` builds the `EntityManagerFactory` — it scans `""` (default package) for `@Entity` classes, applies the Hibernate dialect, and creates the schema via `hbm2ddl.auto=create-drop`. `em.joinTransaction()` attaches the `EntityManager` to the active TX bound by `JpaTransactionManager`.

---

### Level 2 — Intermediate

`Criteria API` — type-safe programmatic queries.

```java
// JpaIntegrationDemo.java
import jakarta.persistence.*;
import jakarta.persistence.criteria.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

// (Item entity and JpaCfg same as Level 1)

public class JpaIntegrationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JpaCfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            for (String[] row : new String[][]{
                {"Widget","9.99","AVAILABLE"},{"Gadget","24.99","AVAILABLE"},
                {"Sensor","49.99","OUT_OF_STOCK"},{"Relay","4.99","AVAILABLE"},
                {"Timer","14.99","AVAILABLE"}
            }) em.persist(new Item(row[0], Double.parseDouble(row[1]), row[2]));
            em.close(); return null;
        });

        // Criteria API — type-safe dynamic query
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            CriteriaBuilder cb = em.getCriteriaBuilder();
            CriteriaQuery<Item> cq = cb.createQuery(Item.class);
            Root<Item> root = cq.from(Item.class);

            // WHERE status='AVAILABLE' AND price < 20
            cq.select(root)
                .where(cb.and(
                    cb.equal(root.get("status"), "AVAILABLE"),
                    cb.lessThan(root.get("price"), 20.0)))
                .orderBy(cb.asc(root.get("price")));

            List<Item> cheap = em.createQuery(cq).getResultList();
            System.out.println("Available < $20:");
            cheap.forEach(i -> System.out.printf("  %-10s $%.2f%n", i.getName(), i.getPrice()));

            // Typed count
            CriteriaQuery<Long> countCq = cb.createQuery(Long.class);
            Root<Item> countRoot = countCq.from(Item.class);
            countCq.select(cb.count(countRoot));
            Long total = em.createQuery(countCq).getSingleResult();
            System.out.println("Total items: " + total);
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

The `Criteria API` builds queries programmatically with type-safe `CriteriaBuilder` calls — useful when query conditions are dynamic (differ at runtime). `cb.equal()`, `cb.lessThan()`, `cb.and()` correspond to `=`, `<`, `AND` in JPQL. The `CriteriaQuery` is compiled to SQL by the JPA provider.

---

### Level 3 — Advanced

`TypedQuery` with named queries + `EntityManager.createNamedQuery()` + merge and remove.

```java
// JpaIntegrationDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@NamedQuery(name = "Item.findByStatus",
    query = "SELECT i FROM Item i WHERE i.status = :status ORDER BY i.price")
@Entity @Table(name = "items")
class Item {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String name; double price; String status;
    public Item(){}
    public Item(String n, double p, String s){name=n;price=p;status=s;}
    public Long getId(){return id;} public String getName(){return name;}
    public double getPrice(){return price;} public String getStatus(){return status;}
    public void setPrice(double p){price=p;} public void setStatus(String s){status=s;}
    public String toString(){return "Item["+id+","+name+","+status+"]";}
}

@Configuration @EnableTransactionManagement
class JpaCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:store;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource ds) {
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean JpaTransactionManager tm(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class JpaIntegrationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JpaCfg.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            em.persist(new Item("Widget",9.99,"AVAILABLE")); em.persist(new Item("Gadget",24.99,"AVAILABLE"));
            em.persist(new Item("Sensor",49.99,"OUT_OF_STOCK")); em.persist(new Item("Relay",4.99,"AVAILABLE"));
            em.close(); return null;
        });

        // Named query
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            List<Item> avail = em.createNamedQuery("Item.findByStatus", Item.class)
                .setParameter("status","AVAILABLE").getResultList();
            System.out.println("Available: " + avail.size());
            avail.forEach(i -> System.out.printf("  %s $%.2f%n", i.getName(), i.getPrice()));
            em.close(); return null;
        });

        // Merge detached entity
        Item detached = tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Item i = em.find(Item.class, 1L); em.close(); return i;
        });
        detached.setPrice(12.99);  // modify detached

        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Item merged = em.merge(detached);  // reattach with new price
            System.out.println("Merged Widget price: $" + merged.getPrice());
            em.close(); return null;
        });

        // Remove (delete)
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Item sensor = em.find(Item.class, 3L);
            em.remove(sensor);  // DELETE FROM items WHERE id=3
            em.close(); return null;
        });

        Long remaining = tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            Long n = em.createQuery("SELECT COUNT(i) FROM Item i", Long.class).getSingleResult();
            em.close(); return n;
        });
        System.out.println("Remaining items: " + remaining);
        ctx.close();
    }
}
```

How to run: same classpath

`@NamedQuery` defines a pre-compiled JPQL query on the entity class — compiled at EMF startup (syntax errors fail at boot, not at runtime). `em.createNamedQuery("Item.findByStatus", Item.class)` retrieves and runs it. `em.merge(detached)` re-attaches the detached entity — the provider issues `UPDATE items SET price=12.99 WHERE id=1`. `em.remove(entity)` must receive a managed entity — it generates `DELETE FROM items WHERE id=?`.

## 6. Walkthrough

**Level 1 — `LocalContainerEntityManagerFactoryBean` startup + first persist (execution order):**

1. **`AnnotationConfigApplicationContext(JpaCfg.class)`**: Spring creates beans in dependency order.
2. **`ds()` bean**: `DriverManagerDataSource` created.
3. **`entityManagerFactory(ds)` bean**: `LocalContainerEntityManagerFactoryBean` built; `afterPropertiesSet()` runs:
   - Scans `""` package → finds `Item.class` annotated `@Entity`.
   - `HibernateJpaVendorAdapter` configures Hibernate as the JPA provider.
   - `hbm2ddl.auto=create-drop` → Hibernate generates `CREATE TABLE items (...)`.
   - `PersistenceProvider.createContainerEntityManagerFactory()` builds the EMF.
4. **`transactionManager(emf)` bean**: `JpaTransactionManager` wraps the EMF.
5. **`tx.execute()`**: `JpaTransactionManager.getTransaction()` → `emf.createEntityManager()` → `em.getTransaction().begin()` → binds EM to thread-local.
6. **`em.persist(new Item("Widget",9.99,"AVAILABLE"))`**: entity state set to MANAGED; snapshot taken. No SQL yet.
7. **TX commit**: `JpaTransactionManager.commit()` → `em.flush()` → Hibernate dirty-checks: new entity → `INSERT INTO items (name,price,status) VALUES (?,?,?)` → `["Widget",9.99,"AVAILABLE"]`.
8. **`em.getTransaction().commit()`** → H2 commits. `em.close()`.

```
Startup:
  Scan → find Item.class (@Entity)
  CREATE TABLE items (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR, price DOUBLE, status VARCHAR)

TX execute:
  BEGIN
  em.persist(widget) → MANAGED (INSERT queued)
  em.persist(gadget) → MANAGED (INSERT queued)
  em.persist(sensor) → MANAGED (INSERT queued)
  FLUSH: INSERT × 3
  COMMIT
```

## 7. Gotchas & takeaways

> **`setPackagesToScan("")` scans the default (unnamed) package — fine for demos, wrong for production.** Always specify a real package: `emf.setPackagesToScan("com.example.domain")`. Scanning `""` can load random `@Entity`-annotated classes from third-party jars.

> **`em.joinTransaction()` is required when you create an `EntityManager` from an `EntityManagerFactory` inside a Spring TX.** Without it, the EM operates outside the TX — changes are auto-committed immediately and won't roll back. In Spring Data JPA, this is handled automatically.

> **`@NamedQuery` validation at startup is a benefit.** If the JPQL has a typo, Hibernate throws at startup — not in a production request. Prefer named queries over ad-hoc JPQL strings in production code.

- `LocalContainerEntityManagerFactoryBean` → JPA standard EMF; scans `@Entity` classes.
- `HibernateJpaVendorAdapter` ��� Hibernate as JPA provider; `EclipseLinkJpaVendorAdapter` for EclipseLink.
- `em.joinTransaction()` — attach EM to Spring TX when created from EMF directly.
- `@NamedQuery` — compiled at startup; typos caught early.
- Prefer `setPackagesToScan("com.yourpackage")` over `""` in production.
