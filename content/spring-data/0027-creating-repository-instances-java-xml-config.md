---
card: spring-data
gi: 27
slug: creating-repository-instances-java-xml-config
title: "Creating repository instances (Java/XML config)"
---

## 1. What it is

Behind the "Spring Boot automatically finds and wires up your repositories" convenience this whole section has relied on is an explicit, configurable mechanism: repository-instance creation, controllable either through Java `@Configuration` (`@EnableJpaRepositories` and its store-specific siblings) or through XML (a `<jpa:repositories base-package="..."/>` element, mirroring the XML namespaces covered in this guide's Appendix section). This card makes that underlying mechanism explicit, since Spring Boot's auto-configuration is really just a convenient default on top of it.

```java
@Configuration
@EnableJpaRepositories(basePackages = "com.example.orders.repository")
public class RepositoryConfig {}
```
```xml
<jpa:repositories base-package="com.example.orders.repository"/>
```

## 2. Why & when

Spring Boot applications rarely need to think about this explicitly — `@SpringBootApplication`'s auto-configuration wires up `@EnableJpaRepositories` (or the equivalent for other stores) implicitly, scoped to the application's own package tree, as covered in an earlier card on defining repository interfaces. But plain Spring Framework applications (no Spring Boot), multi-module projects with repositories outside the default scan boundary, or applications needing fine control over exactly which packages get scanned all need this mechanism made explicit.

Understanding explicit repository-instance creation matters specifically when:

- You're working in a plain Spring Framework application (not Spring Boot) and need to bootstrap Spring Data repositories yourself — there's no auto-configuration doing this implicitly.
- You're integrating Spring Data into a legacy, XML-configured application (the kind covered throughout this guide's Appendix section) and need the XML equivalent of `@EnableJpaRepositories`.
- You need fine-grained control over repository scanning — multiple base packages, exclusion filters, or a non-default `entityManagerFactoryRef`/`transactionManagerRef` for an application with more than one data source.

## 3. Core concept

```
 JAVA CONFIGURATION:
   @Configuration
   @EnableJpaRepositories(
       basePackages = "com.example.orders.repository",
       entityManagerFactoryRef = "ordersEntityManagerFactory",
       transactionManagerRef = "ordersTransactionManager"
   )
   public class OrdersRepositoryConfig {}

 XML CONFIGURATION (mirrors the jpa XML namespace covered in this guide's Appendix):
   <jpa:repositories base-package="com.example.orders.repository"
       entity-manager-factory-ref="ordersEntityManagerFactory"
       transaction-manager-ref="ordersTransactionManager"/>

 BOTH ultimately do the same thing:
   1. scan the given base package(s) for interfaces extending Repository<T,ID>
   2. for each one found, generate a proxy bean
   3. wire that proxy to the given EntityManagerFactory/TransactionManager
      (or the default ones, if not explicitly specified)

 Spring Boot's auto-configuration is EQUIVALENT to an implicit
 @EnableJpaRepositories scoped to the @SpringBootApplication class's own package.
```

Every store module (`@EnableMongoRepositories`, `@EnableRedisRepositories`, and so on) follows this exact same pattern — only the annotation name and store-specific reference attributes differ.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java config, XML config, and Spring Boot auto-configuration all funnel into the same repository-scanning and proxy-generation mechanism">
  <rect x="10" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@EnableJpaRepositories</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java config</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;jpa:repositories&gt;</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">XML config</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot auto-config</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implicit equivalent</text>

  <rect x="150" y="110" width="340" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="135" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">SAME underlying scan + proxy-generation mechanism</text>

  <line x1="100" y1="75" x2="250" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="320" y1="75" x2="320" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="540" y1="75" x2="390" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Three configuration entry points, one underlying mechanism.

## 5. Runnable example

The scenario: proving all three configuration paths — Spring Boot auto-configuration, explicit `@EnableJpaRepositories`, and XML — produce an identically-functioning repository bean.

### Level 1 — Basic

Rely on Spring Boot's implicit auto-configuration (as every earlier card in this section has done) and confirm exactly what bean it produces.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class CreatingRepoLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CreatingRepoLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:creatrepo1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        String beanClassName = repo.getClass().getName();
        System.out.println("bean class implementing ProductRepository = " + beanClassName);

        repo.save(new Product("Widget"));
        System.out.println("count = " + repo.count());

        if (repo.count() != 1) throw new AssertionError("Expected 1 saved product");
        System.out.println("Spring Boot auto-configuration produced a working repository proxy implicitly -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java CreatingRepoLevel1.java` on JDK 17+.

No `@EnableJpaRepositories` annotation appears anywhere in this file — Spring Boot's `JpaRepositoriesAutoConfiguration` adds it implicitly, scoped to `CreatingRepoLevel1`'s own package (and sub-packages), which is exactly why `ProductRepository`, nested inside it, gets found and turned into a working bean with no explicit configuration.

### Level 2 — Intermediate

Add `@EnableJpaRepositories` explicitly, with a `basePackageClasses` scoping it precisely — the Java-config equivalent that Spring Boot's auto-configuration implicitly performs, made visible.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = CreatingRepoLevel2.class) // explicit, matching what auto-config does implicitly
public class CreatingRepoLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CreatingRepoLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:creatrepo2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget"));
        System.out.println("count = " + repo.count());

        if (repo.count() != 1) throw new AssertionError("Expected 1 saved product");
        System.out.println("Explicit @EnableJpaRepositories worked identically to implicit auto-configuration -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java CreatingRepoLevel2.java`.

`@EnableJpaRepositories(basePackageClasses = CreatingRepoLevel2.class)` makes the scanning scope explicit rather than relying on Spring Boot to infer it — the resulting bean and its behavior are identical to Level 1's implicit version, since Spring Boot's auto-configuration is doing precisely this underneath, just without requiring the annotation to be written out.

### Level 3 — Advanced

Bootstrap a repository in a **plain Spring Framework context** (no `@SpringBootApplication`, no Spring Boot auto-configuration at all) using `@EnableJpaRepositories` alongside manually-configured `DataSource`/`EntityManagerFactory`/`TransactionManager` beans — proving the mechanism works entirely independently of Spring Boot.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.hibernate.jpa.HibernatePersistenceProvider;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.JpaVendorAdapter;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;

public class CreatingRepoLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    // A PLAIN Spring Framework configuration -- no Spring Boot involved AT ALL.
    @Configuration
    @EnableJpaRepositories(basePackageClasses = ProductRepository.class)
    public static class PlainSpringConfig {

        @Bean
        public DataSource dataSource() {
            DriverManagerDataSource ds = new DriverManagerDataSource();
            ds.setDriverClassName("org.h2.Driver");
            ds.setUrl("jdbc:h2:mem:creatrepo3;DB_CLOSE_DELAY=-1");
            return ds;
        }

        @Bean
        public LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource dataSource) {
            LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
            emf.setDataSource(dataSource);
            emf.setPackagesToScan(CreatingRepoLevel3.class.getName());
            JpaVendorAdapter adapter = new HibernateJpaVendorAdapter();
            emf.setJpaVendorAdapter(adapter);
            emf.setPersistenceProvider(new HibernatePersistenceProvider());
            java.util.Properties props = new java.util.Properties();
            props.setProperty("hibernate.hbm2ddl.auto", "create-drop");
            emf.setJpaProperties(props);
            return emf;
        }

        @Bean
        public PlatformTransactionManager transactionManager(jakarta.persistence.EntityManagerFactory emf) {
            return new JpaTransactionManager(emf);
        }
    }

    public static void main(String[] args) {
        AnnotationConfigApplicationContext ctx = new AnnotationConfigApplicationContext(PlainSpringConfig.class);

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget"));
        System.out.println("count in a PLAIN Spring Framework context (no Spring Boot) = " + repo.count());

        if (repo.count() != 1) throw new AssertionError("Expected 1 saved product");
        System.out.println("@EnableJpaRepositories worked in a Spring Boot-free context -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context`, `spring-orm`, `spring-tx`, `spring-data-jpa`, `hibernate-core`, and `com.h2database:h2` on the classpath (no `spring-boot-starter` dependencies at all), then `java CreatingRepoLevel3.java` on JDK 17+.

`PlainSpringConfig` manually declares `DataSource`, `LocalContainerEntityManagerFactoryBean`, and `JpaTransactionManager` beans — the infrastructure Spring Boot's auto-configuration normally provides implicitly — before `@EnableJpaRepositories` does its scanning-and-proxy-generation work exactly as it did in Levels 1 and 2. This confirms `@EnableJpaRepositories` is a genuine Spring Framework feature, entirely usable (if more manually wired) without Spring Boot's convenience layer at all.

## 6. Walkthrough

Trace Level 3's manual bootstrap.

1. **`new AnnotationConfigApplicationContext(PlainSpringConfig.class)`** begins building a plain Spring context from the given `@Configuration` class — no `SpringApplication.run(...)`, no Spring Boot auto-configuration classes involved anywhere.
2. **Infrastructure beans are created first** (in dependency order): `dataSource()` builds a `DriverManagerDataSource` pointed at an in-memory H2 database; `entityManagerFactory(dataSource)` builds a `LocalContainerEntityManagerFactoryBean` wired to that data source, configured to scan `CreatingRepoLevel3`'s package for `@Entity` classes, using Hibernate as the JPA provider; `transactionManager(emf)` builds a `JpaTransactionManager` wrapping that `EntityManagerFactory`.
3. **`@EnableJpaRepositories(basePackageClasses = ProductRepository.class)`** processing begins — this is the exact same mechanism from Levels 1 and 2, just triggered by an explicit annotation in a Spring Boot-free context rather than implicitly by Spring Boot's auto-configuration machinery.
4. **Scanning**: it finds `ProductRepository` (extending `JpaRepository<Product, Long>`) and generates a proxy for it, wiring that proxy to the `entityManagerFactory` and `transactionManager` beans defined in the same configuration class (since no explicit `entityManagerFactoryRef`/`transactionManagerRef` was given, it uses the ones present by default type-matching in the context).
5. **`ctx.getBean(ProductRepository.class)`** retrieves this generated proxy — functionally identical in every way to the proxies produced in Levels 1 and 2.
6. **`repo.save(...)` and `repo.count()`** exercise it exactly as any other repository from this entire section — confirming the bean is genuinely functional, not merely present.
7. **Verification**: the program checks `count()` equals `1`, confirming a repository bootstrapped entirely through plain Spring Framework configuration — with zero Spring Boot involvement — works identically to the Spring Boot-convenience versions from Levels 1 and 2.

```
 AnnotationConfigApplicationContext(PlainSpringConfig.class)
        |
        +-- dataSource()              (manual, no Spring Boot auto-config)
        +-- entityManagerFactory(...)  (manual)
        +-- transactionManager(...)    (manual)
        |
        v
 @EnableJpaRepositories scans, finds ProductRepository, generates proxy
        |
        v
 SAME repository proxy behavior as Spring Boot's implicit auto-configuration
```

## 7. Gotchas & takeaways

> **Gotcha:** when an application has more than one `DataSource`/`EntityManagerFactory` (a genuinely multi-database application), `@EnableJpaRepositories`'s `entityManagerFactoryRef` and `transactionManagerRef` attributes become mandatory, not optional — without them, Spring Data can't determine which of several candidate beans a given repository group should wire to, and scanning multiple `@EnableJpaRepositories`-annotated configuration classes (one per data source, each scoped to its own base package with its own explicit refs) is the standard pattern for that scenario.

- Spring Boot's "repositories just work" convenience is an implicit application of `@EnableJpaRepositories` (or the equivalent for other stores), scoped to the `@SpringBootApplication` class's own package — not a fundamentally different mechanism.
- `@EnableJpaRepositories` and XML's `<jpa:repositories>` element are equivalent entry points into the identical underlying scan-and-generate-proxy mechanism — the choice between them follows whatever configuration style (Java or XML) the rest of an application already uses.
- This mechanism works entirely independently of Spring Boot — a plain Spring Framework application can bootstrap Spring Data repositories with manually-configured infrastructure beans, as Level 3 demonstrated.
- `basePackages`/`basePackageClasses` on `@EnableJpaRepositories` (and `entityManagerFactoryRef`/`transactionManagerRef` for multi-datasource setups) are the explicit controls to reach for whenever Spring Boot's default scanning scope doesn't match an application's actual package layout.
