---
card: spring-data
gi: 9
slug: fine-tuning-repository-definition-repositorydefinition-norep
title: "Fine-tuning repository definition (@RepositoryDefinition, @NoRepositoryBean)"
---

## 1. What it is

Two annotations give finer control over exactly how and whether a repository interface gets a generated implementation: `@RepositoryDefinition` lets an interface become a full Spring Data repository *without* extending any of the `Repository`/`CrudRepository` hierarchy at all — you specify the entity and ID types directly on the annotation instead — and `@NoRepositoryBean` (used already in earlier cards' custom base interfaces) tells Spring Data to skip proxy generation for an interface entirely, even though it does extend `Repository<T, ID>`.

```java
@RepositoryDefinition(domainClass = Customer.class, idClass = Long.class)
public interface CustomerRepository {
    Optional<Customer> findById(Long id); // works, despite extending nothing
}

@NoRepositoryBean
public interface BaseRepository<T, ID> extends CrudRepository<T, ID> {
    // a template for other interfaces to extend -- never gets its own proxy
}
```

## 2. Why & when

`@NoRepositoryBean` has already appeared in this section's custom-base-interface examples because it solves a real, common problem: a generic intermediate interface (`MinimalRepository<T, ID>`, `AuditableRepository<T, ID>`) with unbound type parameters cannot itself become a working repository — there's no concrete entity type to generate queries against — but Spring Data's scanning would still try, and fail, without this annotation telling it to skip that interface specifically. `@RepositoryDefinition` solves a different, rarer problem: building a repository-like interface that intentionally shares nothing with the `Repository` hierarchy, useful when you want Spring Data's method-implementing machinery without inheriting any of the standard CRUD method set at all.

Reach for these annotations specifically when:

- You're defining a reusable, generic base interface meant to be extended by several concrete repositories (as in earlier cards) — always mark it `@NoRepositoryBean`, or Spring Data will attempt (and fail) to generate a proxy for the generic template itself.
- You want a repository-style interface with an entirely custom method set, sharing no methods with `CrudRepository` at all, and don't want to extend `Repository<T, ID>` just to get scanning eligibility — `@RepositoryDefinition` grants that eligibility directly via annotation instead of inheritance.
- You're debugging a startup failure mentioning an inability to resolve domain type or ID type for an interface with unbound generics — the fix is almost always adding `@NoRepositoryBean` to that specific interface.

## 3. Core concept

```
 Normal path to eligibility:
   interface extends Repository<T, ID> (with T, ID bound to concrete types)
        |
        v
   eligible for proxy generation

 @NoRepositoryBean:
   interface DOES extend Repository<T, ID> (or CrudRepository, etc.)
   BUT is marked @NoRepositoryBean
        |
        v
   Spring Data SKIPS this interface during proxy generation
   (used for generic templates with unbound T/ID -- see earlier cards)

 @RepositoryDefinition:
   interface extends NOTHING from Spring Data
   BUT is annotated @RepositoryDefinition(domainClass=..., idClass=...)
        |
        v
   eligible for proxy generation anyway -- the annotation supplies
   what the Repository<T,ID> supertype would normally have supplied
```

Both annotations exist to decouple "is this interface eligible for a generated implementation" from the default rule of "does it extend `Repository<T, ID>`" — one to opt an interface *out* despite extending it, the other to opt an interface *in* despite not extending it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="NoRepositoryBean excludes a template interface from proxy generation; RepositoryDefinition includes an interface that extends nothing">
  <rect x="10" y="20" width="260" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@NoRepositoryBean interface</text>
  <text x="140" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends CrudRepository&lt;T,ID&gt;</text>
  <text x="140" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SKIPPED by proxy generation</text>

  <rect x="370" y="20" width="260" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@RepositoryDefinition interface</text>
  <text x="500" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends NOTHING from Spring Data</text>
  <text x="500" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">INCLUDED by proxy generation</text>

  <rect x="150" y="130" width="340" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="157" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Both override the default "extends Repository" rule</text>

  <line x1="140" y1="85" x2="250" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="500" y1="85" x2="400" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both annotations are exceptions to the default "extends `Repository`" eligibility rule, pulling in opposite directions.

## 5. Runnable example

The scenario: proving both annotations' effects concretely — a `@NoRepositoryBean` template that genuinely produces no bean of its own, and a `@RepositoryDefinition` interface that becomes a working repository despite extending nothing.

### Level 1 — Basic

Confirm a `@NoRepositoryBean`-marked generic interface produces no bean, while a concrete interface extending it does.

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

@SpringBootApplication
public class FineTuningLevel1 {

    @Entity
    public static class Widget {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Widget() {}
        public Widget(String name) { this.name = name; }
    }

    @NoRepositoryBean
    public interface BaseRepository<T, ID> extends JpaRepository<T, ID> {}

    public interface WidgetRepository extends BaseRepository<Widget, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FineTuningLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:finetune1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean widgetRepoFound = ctx.getBeanNamesForType(WidgetRepository.class).length > 0;
        boolean baseRepoDirectBeanFound = java.util.Arrays.stream(ctx.getBeanDefinitionNames())
            .anyMatch(name -> name.toLowerCase().contains("baserepository") && !name.toLowerCase().contains("widget"));

        System.out.println("WidgetRepository bean found? " + widgetRepoFound);
        System.out.println("A separate bean literally FOR BaseRepository (not Widget) found? " + baseRepoDirectBeanFound);

        WidgetRepository repo = ctx.getBean(WidgetRepository.class);
        repo.save(new Widget("Gizmo"));
        System.out.println("count = " + repo.count());

        if (!widgetRepoFound) throw new AssertionError("Expected WidgetRepository to be registered");
        if (baseRepoDirectBeanFound) throw new AssertionError("BaseRepository itself should NOT get its own bean");
        System.out.println("@NoRepositoryBean correctly excluded the generic template from proxy generation -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java FineTuningLevel1.java` on JDK 17+.

`BaseRepository<T, ID>`, marked `@NoRepositoryBean`, produces no bean of its own — only `WidgetRepository`, the concrete interface with `T`/`ID` bound to `Widget`/`Long`, gets a generated proxy. Without the `@NoRepositoryBean` annotation, Spring Data would attempt to generate a proxy for `BaseRepository` itself too, and fail at startup since it has no concrete domain type to build queries against.

### Level 2 — Intermediate

Use `@RepositoryDefinition` to build a repository interface that extends nothing from Spring Data at all, proving the annotation alone is sufficient for eligibility.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.RepositoryDefinition;

import java.util.List;
import java.util.Optional;

@SpringBootApplication
public class FineTuningLevel2 {

    @Entity
    public static class Widget {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Widget() {}
        public Widget(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    // Extends NOTHING from Spring Data -- eligibility comes purely from the annotation.
    @RepositoryDefinition(domainClass = Widget.class, idClass = Long.class)
    public interface WidgetFinder {
        Widget save(Widget widget);
        Optional<Widget> findById(Long id);
        List<Widget> findByName(String name); // derived query still works here too
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FineTuningLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:finetune2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        boolean isRepositorySubtype = org.springframework.data.repository.Repository.class
            .isAssignableFrom(WidgetFinder.class);
        System.out.println("Does WidgetFinder extend Repository<T,ID>? " + isRepositorySubtype);

        WidgetFinder repo = ctx.getBean(WidgetFinder.class);
        repo.save(new Widget("Gizmo"));
        repo.save(new Widget("Gadget"));

        List<Widget> found = repo.findByName("Gizmo");
        System.out.println("findByName(Gizmo) = " + found.size());

        if (isRepositorySubtype) throw new AssertionError("WidgetFinder deliberately does NOT extend Repository");
        if (found.size() != 1) throw new AssertionError("Expected exactly 1 widget named Gizmo");
        System.out.println("@RepositoryDefinition granted eligibility without extending Repository -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java FineTuningLevel2.java`.

`WidgetFinder` has no `extends` clause at all — `org.springframework.data.repository.Repository.class.isAssignableFrom(WidgetFinder.class)` confirms this is genuinely `false`, not just a naming coincidence. Yet `@RepositoryDefinition(domainClass = Widget.class, idClass = Long.class)` alone is enough for Spring Data to generate a working proxy, implementing `save`, `findById`, and even the derived query `findByName` — the annotation supplies exactly the two pieces of information (`domainClass`, `idClass`) that `Repository<T, ID>`'s type parameters would otherwise have provided.

### Level 3 — Advanced

Combine both annotations in one application: a `@NoRepositoryBean` base interface shared by two concrete repositories, alongside a completely separate `@RepositoryDefinition`-based interface for a read-model type — showing both mechanisms coexisting for genuinely different purposes in the same codebase.

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
import org.springframework.data.repository.RepositoryDefinition;

import java.util.List;
import java.util.Optional;

@SpringBootApplication
public class FineTuningLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String sku;
        protected Product() {}
        public Product(String sku) { this.sku = sku; }
        public String getSku() { return sku; }
    }

    @Entity
    public static class Warehouse {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String location;
        protected Warehouse() {}
        public Warehouse(String location) { this.location = location; }
        public String getLocation() { return location; }
    }

    @NoRepositoryBean
    public interface CommonBase<T, ID> extends JpaRepository<T, ID> {
        default String describe() { return getClass().getSimpleName() + " with " + count() + " rows"; }
    }

    public interface ProductRepository extends CommonBase<Product, Long> {}
    public interface WarehouseRepository extends CommonBase<Warehouse, Long> {}

    // A completely independent, RepositoryDefinition-based interface for a read-model query.
    @RepositoryDefinition(domainClass = Product.class, idClass = Long.class)
    public interface ProductSkuLookup {
        Optional<Product> findBySku(String sku);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FineTuningLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:finetune3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository productRepo = ctx.getBean(ProductRepository.class);
        WarehouseRepository warehouseRepo = ctx.getBean(WarehouseRepository.class);
        ProductSkuLookup skuLookup = ctx.getBean(ProductSkuLookup.class);

        productRepo.save(new Product("SKU-100"));
        productRepo.save(new Product("SKU-200"));
        warehouseRepo.save(new Warehouse("EU-West"));

        System.out.println(productRepo.describe());   // inherited default method from CommonBase
        System.out.println(warehouseRepo.describe());  // same default method, different entity

        Optional<Product> lookedUp = skuLookup.findBySku("SKU-200");
        System.out.println("skuLookup found = " + lookedUp.map(Product::getSku).orElse("MISSING"));

        if (!productRepo.describe().contains("2")) throw new AssertionError("Expected productRepo to report 2 rows");
        if (!warehouseRepo.describe().contains("1")) throw new AssertionError("Expected warehouseRepo to report 1 row");
        if (lookedUp.isEmpty()) throw new AssertionError("Expected the SKU lookup to find SKU-200");

        System.out.println("@NoRepositoryBean template + @RepositoryDefinition interface coexisted correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java FineTuningLevel3.java`.

`CommonBase<T, ID>`, marked `@NoRepositoryBean`, is shared by both `ProductRepository` and `WarehouseRepository` — each gets its own proxy with its own bound entity type, but both inherit the same `describe()` default method, demonstrating code reuse across repositories via a shared, non-instantiated template. `ProductSkuLookup`, entirely unrelated to that hierarchy and built via `@RepositoryDefinition` instead, coexists in the same application, proving these two mechanisms address different needs (shared behavior across repositories vs. eligibility without inheritance) without interfering with each other.

## 6. Walkthrough

Trace Level 3's startup scanning phase.

1. **Scanning finds three interfaces**: `ProductRepository` (extends `CommonBase<Product, Long>`), `WarehouseRepository` (extends `CommonBase<Warehouse, Long>`), and `ProductSkuLookup` (extends nothing, annotated `@RepositoryDefinition`).
2. **`CommonBase<T, ID>` itself is also encountered** during scanning (it does extend `JpaRepository`, making it structurally eligible), but its `@NoRepositoryBean` annotation causes Spring Data to skip generating a proxy for it — no `CommonBase` bean is ever created.
3. **`ProductRepository` and `WarehouseRepository` each get their own proxy**, generated independently, each resolving `T`/`ID` from their own `extends CommonBase<Product, Long>` / `extends CommonBase<Warehouse, Long>` declaration — both proxies include the inherited `describe()` default method, but each computes it against its own entity's `count()`.
4. **`ProductSkuLookup` is handled through an entirely separate code path**: since it doesn't extend `Repository`, Spring Data's `@RepositoryDefinition` support reads the annotation's `domainClass`/`idClass` attributes directly to determine what entity type and ID type to build query-derivation logic against, then generates a proxy the same way it would for any other repository.
5. **Data seeding**: `main` saves two products and one warehouse through their respective repositories.
6. **`productRepo.describe()` and `warehouseRepo.describe()`**: both invoke the same inherited default method body, but each calls `count()` on itself — `this.count()` resolves polymorphically to each proxy's own entity-scoped count, producing `"2"` for products and `"1"` for warehouses.
7. **`skuLookup.findBySku("SKU-200")`**: `ProductSkuLookup`'s generated proxy executes a derived query against `Product` (resolved from the `@RepositoryDefinition` annotation's `domainClass`), finding the matching row.
8. **Verification**: the program checks both `describe()` outputs contain the expected counts and that the SKU lookup succeeded, confirming all three interfaces — two sharing a `@NoRepositoryBean` template, one built via `@RepositoryDefinition` — worked correctly and independently.

```
 CommonBase<T,ID> @NoRepositoryBean  -- NO bean generated for this interface itself
        ^                    ^
        |                    |
 ProductRepository    WarehouseRepository   -- each gets its OWN proxy + inherited describe()

 ProductSkuLookup @RepositoryDefinition(domainClass=Product.class, idClass=Long.class)
        |
        v
 its own INDEPENDENT proxy, unrelated to the CommonBase hierarchy above
```

## 7. Gotchas & takeaways

> **Gotcha:** `@RepositoryDefinition` interfaces don't automatically inherit any standard method behavior the way extending `CrudRepository` would — every method you want (even `save` or `findById`) must be declared explicitly on the interface, and each one must be either a valid derived-query pattern or annotated with `@Query`. There's no shortcut to "give me the standard CRUD set" without extending the actual `Repository` hierarchy; `@RepositoryDefinition` trades that convenience for the freedom to build an arbitrary, from-scratch method contract.

- `@NoRepositoryBean` excludes an interface that *does* extend `Repository<T, ID>` from getting its own generated proxy — essential on any generic, reusable base interface with unbound type parameters, as used throughout this section's custom-base-interface examples.
- `@RepositoryDefinition(domainClass = ..., idClass = ...)` grants Spring Data eligibility to an interface that extends *nothing* from Spring Data at all — useful for building a repository-shaped interface with a completely custom, hand-picked method set and no inherited baggage.
- Both annotations exist to override the default "extends `Repository`" eligibility rule, in opposite directions — one opts an eligible interface *out*, the other opts an ineligible interface *in*.
- These two annotations round out the mechanics of repository definition covered across this section's cards — the remaining cards shift focus to specific method behaviors: null handling, reactive return types, and query derivation from method names.
