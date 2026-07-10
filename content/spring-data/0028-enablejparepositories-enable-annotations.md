---
card: spring-data
gi: 28
slug: enablejparepositories-enable-annotations
title: "@EnableJpaRepositories & enable annotations"
---

## 1. What it is

Every Spring Data store module ships its own `@Enable*Repositories` annotation — `@EnableJpaRepositories`, `@EnableMongoRepositories`, `@EnableRedisRepositories`, and others — all sharing a common family of attributes beyond the basic `basePackages` scoping covered in the previous card: `repositoryImplementationPostfix` (naming convention for custom-implementation classes, previewed in an upcoming card), `bootstrapMode` (controlling whether repository proxies are created eagerly at startup or lazily on first use), and `considerNestedRepositories` (whether to scan into nested/inner interfaces). This card is the reference for these shared, cross-cutting configuration knobs.

```java
@EnableJpaRepositories(
    basePackages = "com.example.orders",
    repositoryImplementationPostfix = "CustomImpl",
    bootstrapMode = BootstrapMode.LAZY
)
```

## 2. Why & when

The default settings for these attributes work fine for most applications, which is exactly why they're rarely mentioned explicitly — but each addresses a real, specific concern once an application grows large enough or has particular startup-time requirements. Knowing they exist (and what each controls) matters when the defaults stop being the right fit.

Reach for these attributes specifically when:

- **`bootstrapMode = BootstrapMode.LAZY`**: your application has a very large number of repository interfaces, and eager proxy generation for all of them at startup is measurably slowing down application boot — lazy bootstrap defers each repository's actual proxy creation until it's first requested from the context.
- **`repositoryImplementationPostfix`**: you're using custom repository implementations (fragments, covered in the next card) and want a naming convention other than the default `Impl` suffix — perhaps to avoid a naming collision, or to match an existing team convention.
- **`considerNestedRepositories = true`**: your repository interfaces are declared as nested/inner interfaces of another class (common in test code or in single-file examples like the ones throughout this section) rather than as top-level interfaces in their own files — by default, Spring Data's scanning only considers top-level interfaces.

## 3. Core concept

```
 @EnableJpaRepositories(
     basePackages = "...",                          -- WHERE to scan (previous card)

     bootstrapMode = BootstrapMode.DEFAULT           -- proxies created EAGERLY at startup (default)
     bootstrapMode = BootstrapMode.LAZY              -- proxies created on FIRST USE
     bootstrapMode = BootstrapMode.DEFERRED          -- creation deferred until the app is "ready"
                                                          (useful with async initialization)

     repositoryImplementationPostfix = "Impl"        -- (default) naming suffix for custom-impl classes
                                                          e.g. CustomerRepositoryImpl backs CustomerRepository

     considerNestedRepositories = false              -- (default) only top-level interfaces scanned
     considerNestedRepositories = true               -- ALSO scans nested/inner interfaces
 )
```

Every `@Enable*Repositories` annotation across every Spring Data store module shares this same attribute vocabulary, even though each is a store-specific annotation class.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DEFAULT bootstrap mode creates all repository proxies eagerly at startup; LAZY defers each one until first use">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BootstrapMode.DEFAULT</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ALL proxies built at startup --</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">slower boot, no first-use latency</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BootstrapMode.LAZY</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">each proxy built on FIRST USE --</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">faster boot, small first-call latency</text>
</svg>

Bootstrap mode trades startup time against first-call latency for each repository.

## 5. Runnable example

The scenario: a multi-repository application, evolving from confirming eager (default) bootstrap timing, to lazy bootstrap deferring proxy creation, to a nested-interface repository requiring `considerNestedRepositories`.

### Level 1 — Basic

Measure when a repository proxy is actually created under the default eager bootstrap mode, by hooking into bean creation.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.concurrent.atomic.AtomicBoolean;

@SpringBootApplication
public class EnableAnnotationsLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    static final AtomicBoolean repositoryProxyCreatedDuringStartup = new AtomicBoolean(false);

    @Bean
    public static BeanPostProcessor repositoryCreationWatcher() {
        return new BeanPostProcessor() {
            @Override
            public Object postProcessAfterInitialization(Object bean, String beanName) {
                if (bean instanceof ProductRepository) {
                    repositoryProxyCreatedDuringStartup.set(true);
                    System.out.println("[watcher] ProductRepository proxy created for bean: " + beanName);
                }
                return bean;
            }
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableAnnotationsLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:enableann1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        // By the time run() returns, startup (including eager bootstrap) is fully complete.
        System.out.println("was the proxy created DURING startup (eager/default mode)? "
            + repositoryProxyCreatedDuringStartup.get());

        if (!repositoryProxyCreatedDuringStartup.get())
            throw new AssertionError("Expected DEFAULT (eager) bootstrap mode to create the proxy during startup");
        System.out.println("Default BootstrapMode created the repository proxy eagerly at startup -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java EnableAnnotationsLevel1.java` on JDK 17+.

The `BeanPostProcessor` observes every bean as it's initialized during context startup — under `BootstrapMode.DEFAULT` (the implicit default, requiring no explicit `@EnableJpaRepositories` mention), `ProductRepository`'s proxy bean is created and observed by the watcher *before* `SpringApplication.run(...)` even returns, confirming eager creation.

### Level 2 — Intermediate

Configure `bootstrapMode = BootstrapMode.LAZY` and observe the repository proxy is *not* created during startup, only once actually requested from the context.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.repository.config.BootstrapMode;

import java.util.concurrent.atomic.AtomicBoolean;

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = EnableAnnotationsLevel2.class, bootstrapMode = BootstrapMode.LAZY)
public class EnableAnnotationsLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    static final AtomicBoolean repositoryProxyCreated = new AtomicBoolean(false);

    @Bean
    public static BeanPostProcessor repositoryCreationWatcher() {
        return new BeanPostProcessor() {
            @Override
            public Object postProcessAfterInitialization(Object bean, String beanName) {
                if (bean instanceof ProductRepository) {
                    repositoryProxyCreated.set(true);
                    System.out.println("[watcher] ProductRepository proxy created for bean: " + beanName);
                }
                return bean;
            }
        };
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableAnnotationsLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:enableann2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean createdDuringStartup = repositoryProxyCreated.get();
        System.out.println("was the proxy created DURING startup (LAZY mode)? " + createdDuringStartup);

        // NOW actually request it -- this is when a lazily-bootstrapped repository's proxy is built.
        ProductRepository repo = ctx.getBean(ProductRepository.class);
        boolean createdAfterFirstUse = repositoryProxyCreated.get();
        System.out.println("was the proxy created AFTER first getBean() call? " + createdAfterFirstUse);

        if (createdDuringStartup) throw new AssertionError("Expected LAZY mode to NOT create the proxy during startup");
        if (!createdAfterFirstUse) throw new AssertionError("Expected the proxy to exist once actually requested");
        System.out.println("LAZY BootstrapMode deferred proxy creation until first actual use -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java EnableAnnotationsLevel2.java`.

`bootstrapMode = BootstrapMode.LAZY` changes the timing entirely: the watcher confirms `ProductRepository`'s proxy is *not* yet created when `SpringApplication.run(...)` returns, but *is* created the moment `ctx.getBean(ProductRepository.class)` is actually called — the underlying bean definition exists from startup, but its actual instantiation (and the accompanying query-derivation validation work) is deferred until genuinely needed.

### Level 3 — Advanced

Declare a repository as a *nested* interface (as every example throughout this section technically has, for single-file convenience) and confirm `considerNestedRepositories = true` is required for it to be found in a genuinely separate top-level scanning root — contrasted with the default behavior.

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

// A separate top-level "container" class holding a NESTED repository interface,
// simulating a common real-world layout: a test-support class or a grouping class
// with repository interfaces declared inside it, rather than as top-level files.
class RepositoryContainer {
    @Entity
    static class InternalNote {
        @jakarta.persistence.Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String text;
        protected InternalNote() {}
        public InternalNote(String text) { this.text = text; }
    }

    interface InternalNoteRepository extends JpaRepository<InternalNote, Long> {}
}

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = RepositoryContainer.class, considerNestedRepositories = true)
public class EnableAnnotationsLevel3 {

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableAnnotationsLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:enableann3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean found = ctx.getBeanNamesForType(RepositoryContainer.InternalNoteRepository.class).length > 0;
        System.out.println("nested InternalNoteRepository found with considerNestedRepositories=true? " + found);

        RepositoryContainer.InternalNoteRepository repo = ctx.getBean(RepositoryContainer.InternalNoteRepository.class);
        repo.save(new RepositoryContainer.InternalNote("test note"));
        System.out.println("count = " + repo.count());

        if (!found) throw new AssertionError("Expected the nested repository interface to be found");
        if (repo.count() != 1) throw new AssertionError("Expected 1 saved note");
        System.out.println("considerNestedRepositories=true found a repository nested inside another class -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java EnableAnnotationsLevel3.java` on JDK 17+.

`InternalNoteRepository` is declared as a nested interface *inside* `RepositoryContainer`, a separate top-level class — not itself a top-level interface. Without `considerNestedRepositories = true`, Spring Data's default scanning behavior only considers top-level interfaces and would not find it at all; with it explicitly set, the scan also looks inside classes for nested repository interfaces, correctly discovering and creating a proxy for `InternalNoteRepository`.

## 6. Walkthrough

Trace Level 3's scanning behavior.

1. **`@EnableJpaRepositories(basePackageClasses = RepositoryContainer.class, considerNestedRepositories = true)`** configures scanning to start from `RepositoryContainer`'s package, with nested-interface consideration explicitly turned on.
2. **Scanning walks the package**: it finds `RepositoryContainer` itself (a plain class, not a repository), and — because `considerNestedRepositories = true` — also looks *inside* `RepositoryContainer` for nested interfaces extending `Repository<T, ID>`.
3. **`InternalNoteRepository` is found** as a nested interface inside `RepositoryContainer`, extending `JpaRepository<InternalNote, Long>` — it's added to the set of interfaces eligible for proxy generation.
4. **Proxy generation**: exactly as with any top-level repository interface throughout this section, Spring Data generates a proxy for `InternalNoteRepository`, registered as a bean.
5. **`ctx.getBeanNamesForType(...)`** confirms this bean genuinely exists — the concrete, checkable proof that the nested-interface scanning actually worked, not just that the code compiled.
6. **`repo.save(...)` and `repo.count()`** exercise the generated proxy, confirming it's fully functional.
7. **Verification**: the program checks both the bean's presence and its functional behavior, printing `PASS` only if `considerNestedRepositories = true` genuinely enabled discovery of this otherwise-invisible-to-default-scanning repository interface.

```
 @EnableJpaRepositories(considerNestedRepositories = true)
        |
        v
 scan finds: RepositoryContainer (plain class)
        |
        +-- considerNestedRepositories=true --> ALSO look INSIDE it
        |
        v
 finds: RepositoryContainer.InternalNoteRepository (nested interface)
        |
        v
 generates a proxy for it, exactly like any top-level repository interface
```

## 7. Gotchas & takeaways

> **Gotcha:** `BootstrapMode.LAZY` defers proxy *creation*, not query-derivation *validation* — a repository method with an unresolvable derived-query name will still eventually fail, just at first-use time instead of at application-startup time. This trades an earlier, more predictable failure point (at boot, before any traffic is served) for faster startup — a tradeoff worth making deliberately, not by accident, since a broken repository under `LAZY` mode might not surface until the first real request that happens to use it, potentially in production.

- `@Enable*Repositories` annotations across every Spring Data store module share a common attribute vocabulary — `bootstrapMode`, `repositoryImplementationPostfix`, `considerNestedRepositories` — beyond the basic package-scoping covered in the previous card.
- `BootstrapMode.LAZY` trades startup speed for a small amount of first-call latency per repository, and — critically — defers query-derivation validation failures from startup time to first-use time.
- `considerNestedRepositories = true` is specifically needed when repository interfaces are declared as nested/inner interfaces of another class rather than as top-level interfaces — a layout more common in test code and compact examples than in typical production package structures.
- `repositoryImplementationPostfix` (covered further in the next card on custom repository implementations) changes the naming convention Spring Data looks for when pairing a repository interface with a hand-written custom implementation class.
