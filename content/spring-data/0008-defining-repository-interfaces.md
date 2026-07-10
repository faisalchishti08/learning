---
card: spring-data
gi: 8
slug: defining-repository-interfaces
title: "Defining repository interfaces"
---

## 1. What it is

"Defining a repository interface" is the practical, everyday act this whole section has been building toward: writing a Java interface that extends one of Spring Data's base interfaces, adding whatever custom finder methods a specific entity actually needs, and letting Spring Data discover and implement it. This card focuses on the mechanics and conventions of that act itself — naming, placement, generic parameters, and how Spring Data's component scanning finds these interfaces in the first place.

```java
package com.example.orders;

public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByStatus(OrderStatus status);
    Optional<Order> findByOrderNumber(String orderNumber);
}
```

## 2. Why & when

Every card so far in this section has shown repository interfaces being extended and used — this card is where the pattern gets named and its rules made explicit: what makes an interface eligible for Spring Data's proxy generation, where it needs to live for scanning to find it, and how its generic type parameters get resolved. Understanding these mechanics matters once a codebase grows past a handful of trivial examples — multi-module projects, repositories in non-default packages, and repositories with several layers of interface inheritance all depend on getting this right.

This matters specifically when:

- You're organizing a real application's repository interfaces across multiple packages or modules, and need `@EnableJpaRepositories` (or the equivalent for other stores) to actually find them — Spring Boot's auto-configuration handles the common case automatically, but explicit configuration becomes necessary once repositories live outside the main application package's subtree.
- You're debugging why a repository interface *isn't* being picked up — usually a scanning base-package mismatch, a missing store-specific starter dependency, or an interface that doesn't actually extend `Repository<T, ID>` anywhere in its hierarchy.
- You're designing a new repository interface and need to decide its generic parameters, its base interface, and which custom methods belong on it versus being pulled out into a separate custom-implementation class (a related but distinct topic from repository definition itself).

## 3. Core concept

```
 For an interface to become a Spring Data repository, it must:
   1. extend Repository<T, ID> (directly, or transitively through CrudRepository,
      JpaRepository, or a custom base interface)
   2. be found by component scanning within the configured base package(s)
   3. NOT be annotated @NoRepositoryBean (covered in the next card)

 Scanning is driven by:
   Spring Boot auto-configuration:
     scans the package of the @SpringBootApplication class and its sub-packages
     (this is why repositories "just work" when placed under the main package)

   Explicit configuration (needed for repositories outside that subtree):
     @EnableJpaRepositories(basePackages = "com.example.legacy.orders")
     (equivalent annotations exist per store: @EnableMongoRepositories, etc.)
```

The interface itself carries no annotation marking it as a repository — eligibility comes purely from what it extends, combined with where it's found during scanning.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Component scanning finds interfaces extending Repository within the base package and generates a proxy for each">
  <rect x="10" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">com.example.orders</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OrderRepository interface</text>

  <rect x="240" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repository scanning</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">base package(s) configured</text>

  <rect x="470" y="20" width="150" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generated proxy</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">registered as a bean</text>

  <line x1="190" y1="47" x2="235" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="47" x2="465" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Scanning finds every eligible interface under the configured base package(s) and generates one proxy bean per interface.

## 5. Runnable example

The scenario: proving scanning boundaries and generic-parameter resolution concretely — a repository placed where the default scan reaches it, one placed where it doesn't (requiring explicit configuration), and one whose generic parameters are resolved through several layers of interface inheritance.

### Level 1 — Basic

Define a straightforward repository interface within the default scan reach (the same top-level class as the `@SpringBootApplication`-annotated class) and confirm it's found automatically, with zero extra configuration.

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
public class DefiningRepoLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
        public String getStatus() { return status; }
    }

    // Nested under DefiningRepoLevel1 -- within the default scan base package.
    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DefiningRepoLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:defrepo1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean found = ctx.getBeanNamesForType(OrderRepository.class).length > 0;
        System.out.println("OrderRepository bean found automatically? " + found);

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("NEW"));
        System.out.println("count = " + repo.count());

        if (!found) throw new AssertionError("Expected OrderRepository to be found by default scanning");
        if (repo.count() != 1) throw new AssertionError("Expected 1 saved order");
        System.out.println("Default scanning found the repository interface automatically -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java DefiningRepoLevel1.java` on JDK 17+.

`OrderRepository`, nested inside `DefiningRepoLevel1` (the `@SpringBootApplication` class), sits within the package Spring Boot's default component scan covers — `@SpringBootApplication` implies scanning the annotated class's package and everything beneath it. No extra `@EnableJpaRepositories` annotation is needed; `ctx.getBeanNamesForType(...)` confirms a bean was actually registered, not just that the interface compiles.

### Level 2 — Intermediate

Show what happens when a repository interface's generic type parameters are resolved through an intermediate custom interface — the same "custom base interface" pattern from an earlier card, this time focused on confirming Spring Data correctly resolves `T` and `ID` across multiple hops.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@SpringBootApplication
public class DefiningRepoLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        protected Order() {}
        public Order(String status) { this.status = status; }
        public Long getId() { return id; }
        public String getStatus() { return status; }
    }

    // An intermediate, generic base interface -- T and ID are still unbound here.
    @NoRepositoryBean
    public interface AuditableRepository<T, ID> extends JpaRepository<T, ID> {
        // A method every "auditable" entity's repository should have.
        default long countAll() { return count(); }
    }

    // T and ID become concrete (Order, Long) ONLY at this final level.
    public interface OrderRepository extends AuditableRepository<Order, Long> {
        List<Order> findByStatus(String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DefiningRepoLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:defrepo2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("NEW"));
        repo.save(new Order("SHIPPED"));
        repo.save(new Order("NEW"));

        long total = repo.countAll(); // inherited default method from AuditableRepository
        List<Order> newOrders = repo.findByStatus("NEW"); // declared directly on OrderRepository

        System.out.println("countAll() = " + total + ", findByStatus(NEW) = " + newOrders.size());

        if (total != 3) throw new AssertionError("Expected countAll() to report 3");
        if (newOrders.size() != 2) throw new AssertionError("Expected 2 orders with status NEW");
        System.out.println("Generic parameters resolved correctly through an intermediate interface -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java DefiningRepoLevel2.java`.

`AuditableRepository<T, ID>` is a generic, `@NoRepositoryBean`-marked intermediate interface — its own `T`/`ID` are unbound type variables, so Spring Data correctly skips generating a proxy for it directly. `OrderRepository extends AuditableRepository<Order, Long>` is where `T` finally resolves to `Order` and `ID` to `Long` — Spring Data's generic-type resolution walks up the full interface chain to find this binding, regardless of how many `@NoRepositoryBean` interfaces sit in between. `countAll()`, a default method defined on the intermediate interface, is inherited and callable directly on `OrderRepository`.

### Level 3 — Advanced

Define two entities and two repositories in genuinely separate top-level classes (simulating separate packages), one within default scan reach and one deliberately registered via explicit `@EnableJpaRepositories`-style bean configuration — showing what it takes to make a repository outside the default scan boundary discoverable.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Entity
class LegacyAuditLog {
    @jakarta.persistence.Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String message;
    protected LegacyAuditLog() {}
    public LegacyAuditLog(String message) { this.message = message; }
    public String getMessage() { return message; }
}

// This repository interface deliberately lives OUTSIDE DefiningRepoLevel3's package tree
// in this single-file example (top-level, not nested) to illustrate the scanning boundary.
interface LegacyAuditLogRepository extends JpaRepository<LegacyAuditLog, Long> {}

@SpringBootApplication
@EntityScan(basePackageClasses = LegacyAuditLog.class)
@EnableJpaRepositories(basePackageClasses = LegacyAuditLogRepository.class)
public class DefiningRepoLevel3 {

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DefiningRepoLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:defrepo3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean found = ctx.getBeanNamesForType(LegacyAuditLogRepository.class).length > 0;
        System.out.println("LegacyAuditLogRepository found via explicit @EnableJpaRepositories? " + found);

        LegacyAuditLogRepository repo = ctx.getBean(LegacyAuditLogRepository.class);
        repo.save(new LegacyAuditLog("system started"));
        System.out.println("count = " + repo.count());

        if (!found) throw new AssertionError("Expected explicit @EnableJpaRepositories to register the repository");
        if (repo.count() != 1) throw new AssertionError("Expected 1 saved audit log entry");
        System.out.println("Explicit basePackageClasses configuration reached an out-of-tree repository -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java DefiningRepoLevel3.java`. Because top-level classes in a single file are all in the same (default, unnamed) package here, this example uses `@EntityScan`/`@EnableJpaRepositories` with `basePackageClasses` explicitly to demonstrate the *mechanism*, even though in this particular single-file layout default scanning would technically also reach them — in a real multi-package project, this same annotation is what's required when a repository genuinely sits outside the default scan boundary.

`@EnableJpaRepositories(basePackageClasses = LegacyAuditLogRepository.class)` tells Spring Data JPA explicitly which package (identified via a marker class in it) to scan for repository interfaces, independent of where the `@SpringBootApplication` class itself lives. `@EntityScan` does the equivalent for `@Entity` classes. This is the exact mechanism a real multi-module application reaches for when its repositories and entities live in a package Spring Boot's default single-package scan wouldn't otherwise cover — for example, a shared `data-access` module imported by several `@SpringBootApplication`-annotated services.

## 6. Walkthrough

Trace Level 3's startup, since it demonstrates the scanning mechanism most explicitly.

1. **`SpringApplication.run(DefiningRepoLevel3.class, ...)`** begins Spring Boot's auto-configuration process, which normally would only scan `DefiningRepoLevel3`'s own package for `@Entity` classes and repository interfaces.
2. **`@EntityScan(basePackageClasses = LegacyAuditLog.class)`** explicitly extends entity scanning to include the package containing `LegacyAuditLog` — in a real multi-package application, this is how JPA finds entity classes living outside the main application package.
3. **`@EnableJpaRepositories(basePackageClasses = LegacyAuditLogRepository.class)`** explicitly extends *repository* scanning the same way, pointing Spring Data JPA at the package containing `LegacyAuditLogRepository`.
4. **Scanning executes**: Spring Data JPA's repository factory bean post-processor walks the configured base packages, finds `LegacyAuditLogRepository` (an interface extending `JpaRepository<LegacyAuditLog, Long>`), and generates a proxy for it — exactly the same generation process as any other repository in this section, just triggered by explicit rather than default configuration.
5. **`ctx.getBeanNamesForType(LegacyAuditLogRepository.class)`** confirms the proxy bean actually exists in the context — this is the concrete, checkable proof that scanning genuinely found and registered the interface, not just that the code compiled.
6. **`repo.save(...)` and `repo.count()`** exercise the generated proxy exactly as any other repository from earlier cards in this section would, confirming it's fully functional, not merely present as an empty bean registration.
7. **Verification**: the program asserts both the bean's presence and its functional behavior, printing `PASS` only if the explicit scanning configuration produced a genuinely working repository.

```
 @SpringBootApplication default scan
        |
        +-- (normally) only DefiningRepoLevel3's own package
        |
 @EntityScan(basePackageClasses = LegacyAuditLog.class)
        |
        +-- extends ENTITY scanning to LegacyAuditLog's package
        |
 @EnableJpaRepositories(basePackageClasses = LegacyAuditLogRepository.class)
        |
        +-- extends REPOSITORY scanning to LegacyAuditLogRepository's package
        |
        v
 LegacyAuditLogRepository proxy generated and registered, exactly like any in-tree repository
```

## 7. Gotchas & takeaways

> **Gotcha:** `@EntityScan` and `@EnableJpaRepositories` are two *separate* scanning mechanisms configured independently — extending one without the other (for instance, adding `@EnableJpaRepositories` for a package but forgetting the matching `@EntityScan`) produces a startup failure when Spring Data tries to build a repository proxy for an entity type Hibernate doesn't know about yet. When repositories and their entities live outside the default scan boundary, both annotations are usually needed together.

- A repository interface needs no annotation of its own to be discovered — eligibility comes entirely from extending `Repository<T, ID>` (directly or transitively) and being found by scanning, which for Spring Boot defaults to the `@SpringBootApplication` class's package and sub-packages.
- Generic type parameters (`T`, `ID`) resolve correctly no matter how many `@NoRepositoryBean`-marked intermediate interfaces sit between the concrete repository and the Commons hierarchy — Spring Data walks the full inheritance chain to find the binding.
- `@EnableJpaRepositories(basePackages = "...")` (or `basePackageClasses`, generally preferred since it's refactor-safe) is the explicit escape hatch for repositories living outside the default scan boundary — every store module has its own equivalent annotation (`@EnableMongoRepositories`, and so on).
- Checking `ctx.getBeanNamesForType(...)` (or simply attempting `ctx.getBean(...)` and catching the failure) is a reliable way to confirm scanning actually found a repository, rather than assuming from source code alone that it did.
