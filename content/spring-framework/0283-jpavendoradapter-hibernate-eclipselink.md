---
card: spring-framework
gi: 283
slug: jpavendoradapter-hibernate-eclipselink
title: "JpaVendorAdapter: Hibernate & EclipseLink"
---

## 1. What it is

`JpaVendorAdapter` is a Spring SPI that bridges between `LocalContainerEntityManagerFactoryBean` (Spring's JPA bootstrap) and a specific JPA provider (Hibernate, EclipseLink). It contributes:

- **Provider class**: the `javax.persistence.provider` property.
- **Platform properties**: dialect, DDL generation, show-SQL.
- **`PersistenceUnitInfo` customization**: vendor-specific class transformers, JPA 2.x extensions.

```java
// Hibernate
@Bean
LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
    var emf = new LocalContainerEntityManagerFactoryBean();
    emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());  // Hibernate
    // ...
}

// EclipseLink
@Bean
LocalContainerEntityManagerFactoryBean emf(DataSource ds) {
    var emf = new LocalContainerEntityManagerFactoryBean();
    emf.setJpaVendorAdapter(new EclipseLinkJpaVendorAdapter()); // EclipseLink
    // ...
}
```

## 2. Why & when

Without `JpaVendorAdapter`, you must provide all vendor-specific properties manually through `persistence.xml` or `jpaProperties`. The adapter centralises common provider setup and lets Spring's `LocalContainerEntityManagerFactoryBean` configure the provider correctly.

`HibernateJpaVendorAdapter` specifically:
- Sets `hibernate.dialect` from the `databasePlatform` property or auto-detects it from the `DataSource`.
- Sets `hibernate.hbm2ddl.auto` from `generateDdl` (true → `create-drop`).
- Registers Hibernate's `PersistenceUnitInfo` transformer so Spring handles scanning.
- Exposes Hibernate-specific SessionFactory APIs via `emf.unwrap(SessionFactory.class)`.

`EclipseLinkJpaVendorAdapter` provides the same abstraction for EclipseLink, setting `eclipselink.target-database` and wiring `EclipseLinkLoadTimeWeaver`.

Swap vendors by changing one line — the rest of the Spring + JPA code remains unchanged.

## 3. Core concept

`JpaVendorAdapter` contributes three things to `LocalContainerEntityManagerFactoryBean`:

```java
interface JpaVendorAdapter {
    PersistenceProvider getPersistenceProvider();         // which JPA provider class
    Map<String, ?> getJpaPropertyMap();                  // vendor properties
    void postProcessEntityManagerFactory(EntityManagerFactory emf, PersistenceUnitInfo pui);
}
```

Property merging order:
```
adapter.getJpaPropertyMap()             (lowest priority — adapter defaults)
  + emf.setJpaProperties(props)         (higher priority — explicit overrides)
  → merged and passed to PersistenceProvider.createContainerEntityManagerFactory()
```

`HibernateJpaVendorAdapter` property map example:
```
hibernate.dialect          = org.hibernate.dialect.H2Dialect   (from databasePlatform or auto-detected)
hibernate.show_sql         = true                              (if showSql = true)
hibernate.hbm2ddl.auto     = create-drop                      (if generateDdl = true)
```

`EclipseLinkJpaVendorAdapter` property map example:
```
eclipselink.target-database = Auto    (or H2, MySQL, PostgreSQL…)
eclipselink.ddl-generation  = create-or-extend-tables  (if generateDdl = true)
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- LCEMFB -->
  <rect x="10" y="65" width="220" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="88" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">LocalContainer</text>
  <text x="120" y="101" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EntityManagerFactoryBean</text>
  <line x1="20" y1="107" x2="220" y2="107" stroke="#8b949e" stroke-width="0.5"/>
  <text x="120" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setJpaVendorAdapter(adapter)</text>
  <text x="120" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setJpaProperties(overrides)</text>

  <!-- Arrow to adapter -->
  <line x1="232" y1="95" x2="275" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JpaVendorAdapter -->
  <rect x="277" y="30" width="160" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="357" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HibernateJpaVendorAdapter</text>
  <line x1="287" y1="58" x2="427" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="357" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">databasePlatform, generateDdl</text>
  <text x="357" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">showSql, prepareConnection</text>

  <rect x="277" y="110" width="160" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="357" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">EclipseLinkJpaVendorAdapter</text>
  <line x1="287" y1="138" x2="427" y2="138" stroke="#8b949e" stroke-width="0.5"/>
  <text x="357" y="153" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">target-database, weaving</text>

  <!-- Arrow to EMF -->
  <line x1="439" y1="62" x2="487" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="439" y1="138" x2="487" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- EntityManagerFactory -->
  <rect x="489" y="75" width="175" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="576" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">EntityManagerFactory</text>
  <text x="576" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">unwrap(SessionFactory.class)</text>
</svg>

## 5. Runnable example

Scenario: a **product catalog service** — configure `HibernateJpaVendorAdapter` at each level, then show `EclipseLinkJpaVendorAdapter` wiring as Level 3 reference.

### Level 1 — Basic

`HibernateJpaVendorAdapter` with auto-detected dialect.

```java
// JpaVendorAdapterDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.List;

@Entity @Table(name="products")
class Product {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String name; double price;
    public Product(){} public Product(String n, double p){name=n;price=p;}
    public Long getId(){return id;} public String getName(){return name;}
    public String toString(){return "Product["+id+","+name+","+price+"]";}
}

@Repository
class ProductRepository {
    @PersistenceContext EntityManager em;
    @Transactional public Product save(Product p){ em.persist(p); return p; }
    @Transactional(readOnly=true) public List<Product> findAll(){
        return em.createQuery("FROM Product", Product.class).getResultList(); }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:catalog;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds); emf.setPackagesToScan("");

        // Vendor adapter — auto-detects H2Dialect from DataSource metadata
        HibernateJpaVendorAdapter adapter = new HibernateJpaVendorAdapter();
        adapter.setGenerateDdl(true);    // equivalent to hbm2ddl.auto=create-drop for tests
        adapter.setShowSql(true);        // LOG SQL — useful during development
        emf.setJpaVendorAdapter(adapter);

        return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class JpaVendorAdapterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        ProductRepository repo = ctx.getBean(ProductRepository.class);

        repo.save(new Product("Widget",  49.99));
        repo.save(new Product("Gadget",  99.00));

        System.out.println("Products: " + repo.findAll());
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. JpaVendorAdapterDemo.java`

`adapter.setGenerateDdl(true)` instructs `HibernateJpaVendorAdapter` to contribute `hibernate.hbm2ddl.auto=create-drop`. `setShowSql(true)` adds `hibernate.show_sql=true`. These adapter properties are merged with any explicit `jpaProperties` you set — explicit properties win.

---

### Level 2 — Intermediate

Explicit dialect + `jpaProperties` overrides.

```java
// JpaVendorAdapterDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Product entity and ProductRepository same as Level 1)

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg2 {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:catalog2;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds); emf.setPackagesToScan("");

        HibernateJpaVendorAdapter adapter = new HibernateJpaVendorAdapter();
        adapter.setDatabasePlatform("org.hibernate.dialect.H2Dialect");  // explicit dialect
        adapter.setGenerateDdl(false);   // adapter sets hbm2ddl.auto=none
        adapter.setShowSql(false);
        emf.setJpaVendorAdapter(adapter);

        // Explicit jpaProperties OVERRIDE adapter defaults
        Properties props = new Properties();
        props.setProperty("hibernate.hbm2ddl.auto", "create-drop");     // override: yes DDL for tests
        props.setProperty("hibernate.format_sql", "true");               // pretty-print SQL in logs
        props.setProperty("hibernate.jdbc.batch_size", "25");            // batch DML
        props.setProperty("hibernate.order_inserts", "true");
        props.setProperty("hibernate.order_updates", "true");
        emf.setJpaProperties(props);

        return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class JpaVendorAdapterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg2.class);
        ProductRepository repo = ctx.getBean(ProductRepository.class);

        // save products — will use batch_size=25 for bulk ops
        for (int i=0; i<5; i++) repo.save(new Product("Product-"+i, 10.0+i));

        System.out.println("All: " + repo.findAll());

        // unwrap Hibernate SessionFactory for vendor-specific access
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        org.hibernate.SessionFactory sf = emf.unwrap(org.hibernate.SessionFactory.class);
        System.out.println("Hibernate stats enabled: " +
            sf.getStatistics().isStatisticsEnabled());

        ctx.close();
    }
}
```

How to run: same classpath

`adapter.setDatabasePlatform("org.hibernate.dialect.H2Dialect")` explicitly sets the dialect (useful when auto-detection is unreliable or when targeting a cloud DB not in the driver metadata). Properties in `setJpaProperties()` override the adapter's defaults — here we override `hbm2ddl.auto` back to `create-drop` even though `generateDdl=false`.

---

### Level 3 — Advanced

`EclipseLinkJpaVendorAdapter` configuration + `unwrap` for vendor API.

```java
// JpaVendorAdapterDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.EclipseLinkJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Product entity and ProductRepository same as Level 1)

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg3 {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:catalog3;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds); emf.setPackagesToScan("");

        // EclipseLink adapter — swap from Hibernate by changing one line
        EclipseLinkJpaVendorAdapter adapter = new EclipseLinkJpaVendorAdapter();
        adapter.setDatabasePlatform("org.eclipse.persistence.platform.database.H2Platform");
        adapter.setGenerateDdl(true);     // eclipselink.ddl-generation = create-or-extend-tables
        adapter.setShowSql(true);
        emf.setJpaVendorAdapter(adapter);

        Properties props = new Properties();
        // EclipseLink-specific overrides
        props.setProperty("eclipselink.weaving", "false");         // disable for non-agent environments
        props.setProperty("eclipselink.logging.level", "FINE");
        props.setProperty("eclipselink.cache.shared.default", "false"); // disable shared L2 cache
        emf.setJpaProperties(props);

        return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){return new JpaTransactionManager(emf);}
}

public class JpaVendorAdapterDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg3.class);
        ProductRepository repo = ctx.getBean(ProductRepository.class);

        repo.save(new Product("Widget", 49.99));
        repo.save(new Product("Gadget", 99.00));
        System.out.println("Products: " + repo.findAll());

        // unwrap EclipseLink-specific API
        EntityManagerFactory emf = ctx.getBean(EntityManagerFactory.class);
        // For EclipseLink: emf.unwrap(org.eclipse.persistence.jpa.JpaEntityManagerFactory.class)
        // (ClassCast if Hibernate is on classpath instead — adapter controls what you can unwrap)
        System.out.println("Provider: " + emf.getProperties().get("eclipselink.target-database"));

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:eclipselink.jar:jakarta.persistence-api.jar:h2.jar:. JpaVendorAdapterDemo.java`

Switching providers: change `HibernateJpaVendorAdapter` → `EclipseLinkJpaVendorAdapter` and update `setDatabasePlatform()`. Vendor-specific `jpaProperties` keys differ (e.g., `eclipselink.weaving` vs `hibernate.bytecode.provider`). The rest of your `@Repository`, `@Transactional`, and `@PersistenceContext` code does not change.

## 6. Walkthrough

**Level 2 — property resolution order during EMF creation:**

1. **`emf.afterPropertiesSet()` called**: `LocalContainerEntityManagerFactoryBean` begins JPA bootstrap.
2. **Adapter properties collected**: `adapter.getJpaPropertyMap()` returns:
   ```
   {hibernate.dialect = org.hibernate.dialect.H2Dialect,
    hibernate.show_sql = false,
    hibernate.hbm2ddl.auto = none}    ← from generateDdl=false
   ```
3. **Explicit `jpaProperties` merged**: `hibernate.hbm2ddl.auto = create-drop` OVERRIDES the adapter value; `hibernate.format_sql`, `hibernate.jdbc.batch_size`, etc. ADDED to the merged map.
4. **`PersistenceProvider.createContainerEntityManagerFactory(pui, mergedProps)`**: Hibernate receives the final merged map, configures the SessionFactory.
5. **EMF registered as Spring singleton**: ready for `@PersistenceContext` injection.

**Dialect auto-detection** (when `databasePlatform` not set):
```
adapter.setDatabasePlatform → null
→ HibernateJpaVendorAdapter.determineDatabasePlatform(DataSource)
  → DataSource.getConnection().getMetaData().getDatabaseProductName()
  → "H2" → org.hibernate.dialect.H2Dialect
  → contributes: hibernate.dialect = org.hibernate.dialect.H2Dialect
```

## 7. Gotchas & takeaways

> **`setGenerateDdl(true)` maps to `create-drop` in Hibernate** — this drops schema on shutdown. Never use `generateDdl=true` in production. For production DDL, use `hibernate.hbm2ddl.auto=validate` (or `none` + Flyway/Liquibase).

> **`setJpaProperties()` values override adapter values for the same key.** The adapter provides sensible defaults; `jpaProperties` gives you explicit control. Adapter keys are Hibernate-prefixed (`hibernate.*`); EclipseLink uses `eclipselink.*`. Don't mix vendor prefixes when switching adapters.

> **`emf.unwrap()` returns a vendor-specific type** — `SessionFactory` (Hibernate), `JpaEntityManagerFactory` (EclipseLink). This is the escape hatch for vendor APIs (L2 cache stats, Hibernate filters, EclipseLink query hints). It couples your code to the provider — isolate it in a helper or repository.

> **`EclipseLinkJpaVendorAdapter` requires `eclipselink.weaving=false`** unless a JVM `-javaagent` is configured. Weaving enhances bytecode at load time; without the agent, EclipseLink falls back to no-weaving mode automatically, but the explicit property prevents warning noise.

- `HibernateJpaVendorAdapter`: `setDatabasePlatform`, `setGenerateDdl`, `setShowSql` are the key three properties.
- `setJpaProperties()` always wins over adapter defaults for the same key.
- `generateDdl=true` → `create-drop` — safe for tests, dangerous in production.
- Switch providers by changing one adapter class; all `@Repository`/`@Transactional` code stays the same.
- `emf.unwrap(SessionFactory.class)` unlocks Hibernate-specific APIs.
