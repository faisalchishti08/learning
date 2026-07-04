---
card: spring-framework
gi: 280
slug: persistence-unit-entitymanagerfactory
title: Persistence unit & EntityManagerFactory
---

## 1. What it is

A **persistence unit** is a named configuration block that groups JPA entity classes, a data source, and JPA properties together. In a plain Java EE application it is defined in `META-INF/persistence.xml`. In a Spring application it can be defined in `persistence.xml` **or** configured entirely in Java (`LocalContainerEntityManagerFactoryBean`) — no `persistence.xml` needed.

```xml
<!-- persistence.xml (optional with Spring) -->
<persistence-unit name="storePU" transaction-type="RESOURCE_LOCAL">
    <class>com.example.Item</class>
    <properties>
        <property name="hibernate.dialect" value="org.hibernate.dialect.H2Dialect"/>
    </properties>
</persistence-unit>
```

The **`EntityManagerFactory`** (EMF) is the long-lived, thread-safe object that represents the persistence unit at runtime. It creates `EntityManager` instances (one per transaction or request) and holds the entity metadata, second-level cache, and connection pool integration.

## 2. Why & when

Every JPA application has one `EntityManagerFactory` per persistence unit (one per database in typical setups). Understanding persistence units matters when:
- You have **multiple databases** (e.g., primary + audit DB) — each needs its own persistence unit and EMF.
- You mix **Spring and `persistence.xml`** configuration — Spring merges them.
- You override `persistence.xml` properties programmatically in Spring — essential for tests.
- You need to understand **EMF lifecycle** to diagnose startup errors.

## 3. Core concept

**`EntityManagerFactory` lifecycle:**

```
Application start:
  1. LocalContainerEntityManagerFactoryBean.afterPropertiesSet()
     → scan @Entity classes
     → validate schema (hbm2ddl.auto=validate) or create
     → build internal entity metamodel + proxy classes
     → return EntityManagerFactory

  2. EntityManagerFactory shared as singleton @Bean

Request / TX:
  3. EntityManager em = emf.createEntityManager()
     → open session / persistence context
     → NOT thread-safe — one per TX
  
  4. em.close()  → release connection to pool

Application stop:
  5. emf.close()  → close all open connections, release cache
```

Spring's `LocalContainerEntityManagerFactoryBean`:
- Implements `DisposableBean` → calls `emf.close()` on `ApplicationContext.close()`.
- Can be given a `persistenceUnitName` to match a `persistence.xml` unit.
- `setPersistenceXmlLocation()` — locate `persistence.xml` on classpath.
- `setMappingResources(String[])` — XML mapping files (Hibernate `.hbm.xml`).

`EntityManagerFactory.getMetamodel()` returns the JPA `Metamodel` — compile-time metadata about entity classes, useful with the Criteria API for type-safe `SingularAttribute<Entity, Type>` access.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Persistence Unit -->
  <rect x="10" y="20" width="200" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Persistence Unit config</text>
  <line x1="20" y1="48" x2="200" y2="48" stroke="#8b949e" stroke-width="0.5"/>
  <text x="110" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Entity classes (scan)</text>
  <text x="110" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">DataSource</text>
  <text x="110" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JPA properties (dialect, ddl)</text>
  <text x="110" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JpaVendorAdapter (Hibernate)</text>

  <line x1="212" y1="70" x2="255" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- EMF -->
  <rect x="257" y="40" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="347" y="65" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">EntityManagerFactory</text>
  <text x="347" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">singleton, thread-safe</text>

  <!-- Per-TX EntityManager -->
  <line x1="347" y1="102" x2="347" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="257" y="137" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="158" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EntityManager (per TX)</text>
  <text x="347" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">persistence context, NOT thread-safe</text>

  <!-- Second-level cache / Metamodel -->
  <rect x="460" y="50" width="200" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">EMF holds:</text>
  <text x="560" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">entity Metamodel</text>
  <text x="560" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2nd-level cache (optional)</text>
  <line x1="439" y1="75" x2="458" y2="75" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
</svg>

`EntityManagerFactory` is shared; `EntityManager` is per-transaction. The EMF holds the metamodel and optional second-level cache.

## 5. Runnable example

Scenario: a **catalog service** — configure a persistence unit fully in Java, inspect the `Metamodel`, and demonstrate multiple persistence units (two databases).

### Level 1 — Basic

Java-configured persistence unit — no `persistence.xml`.

```java
// PersistenceUnitDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name = "catalog_items")
class CatalogItem {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) Long id;
    String name; double price;
    public CatalogItem(){}
    public CatalogItem(String n, double p){name=n; price=p;}
    public Long getId(){return id;} public String getName(){return name;}
    public double getPrice(){return price;}
    public String toString(){return "CatalogItem["+id+","+name+","+price+"]";}
}

@Configuration @EnableTransactionManagement
class CatalogConfig {
    @Bean DataSource ds(){
        var d = new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:catalog;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource ds) {
        var emf = new LocalContainerEntityManagerFactoryBean();
        emf.setPersistenceUnitName("catalogPU");   // explicit name
        emf.setDataSource(ds);
        emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p = new Properties();
        p.setProperty("hibernate.hbm2ddl.auto", "create-drop");
        p.setProperty("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        emf.setJpaProperties(p);
        return emf;
    }
    @Bean JpaTransactionManager tx(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class PersistenceUnitDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CatalogConfig.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Print EMF metadata
        System.out.println("Persistence unit: catalogPU");
        System.out.println("Entities in metamodel: " +
            emf.getMetamodel().getEntities().stream().map(e -> e.getName()).toList());

        // Persist and query
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            em.persist(new CatalogItem("Widget", 9.99));
            em.persist(new CatalogItem("Gadget", 24.99));
            em.close(); return null;
        });

        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            List<CatalogItem> all = em.createQuery("FROM CatalogItem ORDER BY price", CatalogItem.class)
                .getResultList();
            all.forEach(System.out::println);
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. PersistenceUnitDemo.java`

`setPersistenceUnitName("catalogPU")` gives the persistence unit an explicit name — useful when multiple EMFs coexist. `emf.getMetamodel().getEntities()` returns the set of entity types known to this persistence unit at runtime.

---

### Level 2 — Intermediate

`Metamodel` access + `SingularAttribute` for type-safe Criteria queries.

```java
// PersistenceUnitDemo.java
import jakarta.persistence.*;
import jakarta.persistence.criteria.*;
import jakarta.persistence.metamodel.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.context.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (CatalogItem entity and CatalogConfig same as Level 1)

public class PersistenceUnitDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CatalogConfig.class);
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            em.persist(new CatalogItem("Widget",9.99));
            em.persist(new CatalogItem("Gadget",24.99));
            em.persist(new CatalogItem("Sensor",49.99));
            em.close(); return null;
        });

        // Metamodel introspection
        Metamodel meta = emf.getMetamodel();
        EntityType<CatalogItem> itemType = meta.entity(CatalogItem.class);
        System.out.println("Entity: " + itemType.getName());
        itemType.getAttributes().forEach(a ->
            System.out.printf("  Attribute: %-10s type=%s%n", a.getName(), a.getJavaType().getSimpleName()));

        // Type-safe Criteria using Metamodel attributes
        tx.execute(s -> {
            EntityManager em = emf.createEntityManager(); em.joinTransaction();
            CriteriaBuilder cb = em.getCriteriaBuilder();
            CriteriaQuery<CatalogItem> cq = cb.createQuery(CatalogItem.class);
            Root<CatalogItem> root = cq.from(CatalogItem.class);

            // Access attribute via Metamodel (compile-time safe)
            SingularAttribute<? super CatalogItem, Double> priceAttr =
                (SingularAttribute<? super CatalogItem, Double>) itemType.getSingularAttribute("price");

            cq.select(root)
                .where(cb.greaterThan(root.get(priceAttr), 15.0))
                .orderBy(cb.desc(root.get(priceAttr)));

            List<CatalogItem> expensive = em.createQuery(cq).getResultList();
            System.out.println("Price > $15:");
            expensive.forEach(i -> System.out.printf("  %-10s $%.2f%n", i.getName(), i.getPrice()));
            em.close(); return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

`emf.getMetamodel().entity(CatalogItem.class)` returns the `EntityType<CatalogItem>` — an in-memory representation of the entity's attributes and their types. `itemType.getSingularAttribute("price")` retrieves the price attribute as a `SingularAttribute` — the `root.get(priceAttr)` call in the Criteria query is then type-safe (not a string `"price"`).

---

### Level 3 — Advanced

Two persistence units — primary catalog DB + audit DB, each with its own EMF.

```java
// PersistenceUnitDemo.java
import jakarta.persistence.*;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name = "catalog_items")
class CatalogItem {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String name; double price;
    public CatalogItem(){} public CatalogItem(String n, double p){name=n;price=p;}
    public Long getId(){return id;} public String getName(){return name;}
    public double getPrice(){return price;}
}

@Entity @Table(name = "audit_log")
class AuditLog {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String action; String detail;
    public AuditLog(){} public AuditLog(String a, String d){action=a;detail=d;}
    public Long getId(){return id;}
    public String toString(){return "Audit["+action+": "+detail+"]";}
}

@Configuration @EnableTransactionManagement
class MultiPUConfig {
    @Bean @Qualifier("catalogDS") DataSource catalogDs(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:catalog;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean @Qualifier("auditDS") DataSource auditDs(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:audit;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean @Primary @Qualifier("catalogEMF")
    LocalContainerEntityManagerFactoryBean catalogEmf(@Qualifier("catalogDS") DataSource ds) {
        var emf=new LocalContainerEntityManagerFactoryBean();
        emf.setPersistenceUnitName("catalogPU"); emf.setDataSource(ds);
        emf.setPackagesToScan(""); emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean @Qualifier("auditEMF")
    LocalContainerEntityManagerFactoryBean auditEmf(@Qualifier("auditDS") DataSource ds) {
        var emf=new LocalContainerEntityManagerFactoryBean();
        emf.setPersistenceUnitName("auditPU"); emf.setDataSource(ds);
        emf.setPackagesToScan(""); emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean @Primary JpaTransactionManager tx(@Qualifier("catalogEMF") EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class PersistenceUnitDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiPUConfig.class);
        var emfs = ctx.getBeansOfType(EntityManagerFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        System.out.println("Persistence units: " + emfs.keySet());

        // Catalog operations
        EntityManagerFactory catalogEmf = (EntityManagerFactory) emfs.values().toArray()[0];
        tx.execute(s -> {
            EntityManager em = catalogEmf.createEntityManager(); em.joinTransaction();
            em.persist(new CatalogItem("Widget",9.99));
            em.close(); return null;
        });

        // Audit operations (separate DB)
        EntityManagerFactory auditEmf = (EntityManagerFactory) emfs.values().toArray()[1];
        EntityManager auditEm = auditEmf.createEntityManager();
        auditEm.getTransaction().begin();
        auditEm.persist(new AuditLog("INSERT","Widget added to catalog"));
        auditEm.getTransaction().commit(); auditEm.close();

        // Verify both DBs
        tx.execute(s -> {
            EntityManager em = catalogEmf.createEntityManager(); em.joinTransaction();
            System.out.println("Catalog items: " + em.createQuery("FROM CatalogItem",CatalogItem.class).getResultList().size());
            em.close(); return null;
        });
        auditEm = auditEmf.createEntityManager();
        System.out.println("Audit logs: " + auditEm.createQuery("FROM AuditLog",AuditLog.class).getResultList());
        auditEm.close();

        ctx.close();
    }
}
```

How to run: same classpath

Two separate `LocalContainerEntityManagerFactoryBean` beans with `setPersistenceUnitName("catalogPU")` / `"auditPU"` configure two independent persistence units against two different H2 in-memory databases. `@Primary` marks the default `EntityManagerFactory` for injection when no qualifier is specified. Both persistence units scan the same package — each finds only its own entities because the `@Table` names don't conflict.

## 6. Walkthrough

**Level 1 ��� EMF startup and first query (execution order):**

1. **`AnnotationConfigApplicationContext`** processes `CatalogConfig.class`.
2. **`entityManagerFactory(ds)` bean**: `LocalContainerEntityManagerFactoryBean.afterPropertiesSet()`:
   - `setPersistenceUnitName("catalogPU")` → names this unit.
   - `setPackagesToScan("")` → `PersistenceUnitReader` finds `CatalogItem.class` (annotated `@Entity`).
   - `HibernateJpaVendorAdapter` → Hibernate `PersistenceProvider`.
   - `hbm2ddl.auto=create-drop` → `CREATE TABLE catalog_items (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR, price DOUBLE)`.
   - `EntityManagerFactory` built → stored in Spring context.
3. **`emf.getMetamodel().getEntities()`**: returns `{EntityType<CatalogItem>}` — one entity.
4. **First TX**: `em.persist(new CatalogItem("Widget",9.99))` → entity enters MANAGED state. At commit, Hibernate flushes → `INSERT INTO catalog_items (name,price) VALUES ('Widget',9.99)`.
5. **Second TX**: `FROM CatalogItem ORDER BY price` → `SELECT ci.id,ci.name,ci.price FROM catalog_items ci ORDER BY ci.price ASC` → 2 rows returned → 2 `CatalogItem` objects.

```
Metamodel: {CatalogItem → TABLE catalog_items → attributes [id:Long, name:String, price:Double]}

TX 1:
  BEGIN
  MANAGED: [CatalogItem(null,"Widget",9.99), CatalogItem(null,"Gadget",24.99)]
  FLUSH:   INSERT × 2
  COMMIT

TX 2:
  SELECT ci.* FROM catalog_items ci ORDER BY ci.price ASC
  Results: [CatalogItem(1,"Widget",9.99), CatalogItem(2,"Gadget",24.99)]
```

## 7. Gotchas & takeaways

> **`EntityManagerFactory.close()` is called automatically by Spring** via `LocalContainerEntityManagerFactoryBean`'s `DisposableBean` implementation on `ApplicationContext.close()`. Do not close it manually — double-close causes errors.

> **Multiple EMFs require `@Primary` on one of them** unless all injection points use `@Qualifier`. Without `@Primary`, Spring can't decide which `EntityManagerFactory` to inject when the bean type is `EntityManagerFactory`.

> **`persistence.xml` and Java config can coexist.** `LocalContainerEntityManagerFactoryBean` reads a matching `persistence.xml` unit and merges/overrides its settings with Spring-provided properties. This allows gradual migration from XML-only to Java config.

- One `EntityManagerFactory` per persistence unit (per database in typical setups).
- `setPersistenceUnitName("myPU")` names the unit — useful for multiple EMFs.
- `emf.getMetamodel()` — runtime entity metadata; useful for Criteria API.
- Spring calls `emf.close()` automatically on context close.
- Multiple EMFs need `@Primary` on the default, or `@Qualifier` on all injection points.
