---
card: spring-data
gi: 45
slug: jparepository-jpaspecificationexecutor
title: "JpaRepository / JpaSpecificationExecutor"
---

## 1. What it is

This section turns from Spring Data's store-agnostic Commons abstractions to the specifics of Spring Data JPA — starting with `JpaRepository<T, ID>` (already used throughout the Commons section as the standard base interface for relational entities) and its sibling `JpaSpecificationExecutor<T>`, which accepts a `Specification<T>` — a functional-interface wrapper around JPA Criteria API logic — giving repositories yet another way (alongside derived queries, `@Query`, custom fragments, and Querydsl, all covered earlier) to build dynamic, composable queries.

```java
public interface CustomerRepository extends JpaRepository<Customer, Long>, JpaSpecificationExecutor<Customer> {}

Specification<Customer> isActive = (root, query, cb) -> cb.isTrue(root.get("active"));
List<Customer> active = customerRepository.findAll(isActive);
```

## 2. Why & when

The earlier custom-fragment card built dynamic Criteria API queries by hand, inside a hand-written implementation class — genuinely custom code, requiring a full fragment interface plus implementation class per repository. `JpaSpecificationExecutor` offers a lighter-weight alternative for the specific, common case of dynamic filtering: define reusable `Specification<T>` objects (each one a small, focused, independently-composable unit of filter logic), and combine them at the call site with `.and(...)`/`.or(...)`, without writing a custom fragment implementation class at all.

Reach for `JpaSpecificationExecutor` specifically when:

- You want dynamic, composable query filtering without the ceremony of a full custom-fragment interface-plus-implementation-class pair — a `Specification` is just a small functional object.
- You have several independent, reusable filter conditions (active customers, customers in a region, customers above a spend threshold) that different call sites need to combine in different combinations — `Specification.and()`/`.or()` composition is designed exactly for this.
- You're choosing between Querydsl (from the earlier card) and Specifications for type-safe-ish dynamic queries — Specifications use the standard JPA Criteria API directly (no code-generation build step required), while Querydsl offers stronger compile-time type safety at the cost of that generation step.

## 3. Core concept

```
 public interface CustomerRepository extends JpaRepository<Customer, Long>,
     JpaSpecificationExecutor<Customer> {}

 A Specification<T> is a functional interface:
   Predicate toPredicate(Root<T> root, CriteriaQuery<?> query, CriteriaBuilder cb);
        |
        v
 Written as a lambda -- the SAME Criteria API primitives the earlier
 custom-fragment card used by hand, but packaged as a small, reusable,
 independently-testable unit:

   Specification<Customer> isActive = (root, query, cb) -> cb.isTrue(root.get("active"));
   Specification<Customer> inRegion = (root, query, cb) -> cb.equal(root.get("region"), "EU");

 COMPOSITION at the call site:
   customerRepository.findAll(isActive.and(inRegion));
   customerRepository.findAll(isActive.or(inRegion));

 Inherited methods from JpaSpecificationExecutor<T>:
   findAll(Specification<T>)                    findOne(Specification<T>)
   findAll(Specification<T>, Pageable)          count(Specification<T>)
   findAll(Specification<T>, Sort)              exists(Specification<T>)
```

Each `Specification` is a small, standalone, reusable unit — the composition (`.and`/`.or`) happens at the call site, letting different combinations be assembled from the same reusable building blocks.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Individual Specifications compose via and/or into a combined predicate executed through JpaSpecificationExecutor">
  <rect x="10" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">isActive</text>

  <rect x="180" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">inRegion("EU")</text>

  <rect x="90" y="110" width="240" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">isActive.and(inRegion)</text>

  <rect x="440" y="20" width="180" height="140" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="530" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JpaSpecificationExecutor</text>
  <text x="530" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">findAll, findOne,</text>
  <text x="530" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">count, exists</text>

  <line x1="85" y1="70" x2="180" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="255" y1="70" x2="230" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="330" y1="132" x2="435" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Small, reusable `Specification` units compose freely at each call site before being executed.

## 5. Runnable example

The scenario: a `Customer` search, evolving from basic single-specification filtering, to composing two independent specifications with `.and()`, to a realistic search-form pattern building a variable specification chain from optional user input.

### Level 1 — Basic

Define one `Specification<Customer>` and execute it via `findAll(Specification)`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

@SpringBootApplication
public class SpecExecutorLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean active;
        protected Customer() {}
        public Customer(String name, boolean active) { this.name = name; this.active = active; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long>, JpaSpecificationExecutor<Customer> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecExecutorLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:specexec1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", true));
        repo.save(new Customer("Grace", false));
        repo.save(new Customer("Katherine", true));

        Specification<Customer> isActive = (root, query, cb) -> cb.isTrue(root.get("active"));
        List<Customer> active = repo.findAll(isActive);

        System.out.println("active customers = " + active.stream().map(Customer::getName).toList());

        if (active.size() != 2) throw new AssertionError("Expected 2 active customers");
        System.out.println("Basic Specification executed via JpaSpecificationExecutor -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java SpecExecutorLevel1.java` on JDK 17+.

`CustomerRepository extends JpaRepository<Customer, Long>, JpaSpecificationExecutor<Customer>` inherits `findAll(Specification<Customer>)`. `isActive` is a plain lambda implementing `Specification`'s single method, using the same `Root`/`CriteriaBuilder` primitives the earlier custom-fragment card used by hand — but here, no custom implementation class is needed at all; the lambda is passed directly to the inherited method.

### Level 2 — Intermediate

Compose two independent `Specification` objects with `.and()`, showing reusable filter units combined at the call site.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

@SpringBootApplication
public class SpecExecutorLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean active;
        private String region;
        protected Customer() {}
        public Customer(String name, boolean active, String region) { this.name = name; this.active = active; this.region = region; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long>, JpaSpecificationExecutor<Customer> {}

    // Reusable, independently-defined specifications.
    static class CustomerSpecs {
        static Specification<Customer> isActive() {
            return (root, query, cb) -> cb.isTrue(root.get("active"));
        }
        static Specification<Customer> inRegion(String region) {
            return (root, query, cb) -> cb.equal(root.get("region"), region);
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecExecutorLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:specexec2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", true, "EU"));
        repo.save(new Customer("Grace", true, "US"));
        repo.save(new Customer("Katherine", false, "EU"));

        Specification<Customer> activeInEU = CustomerSpecs.isActive().and(CustomerSpecs.inRegion("EU"));
        List<Customer> result = repo.findAll(activeInEU);

        System.out.println("active EU customers = " + result.stream().map(Customer::getName).toList());

        if (result.size() != 1 || !result.get(0).getName().equals("Ada"))
            throw new AssertionError("Expected only Ada to match both isActive AND inRegion(EU)");
        System.out.println("Two independent Specifications composed via .and() at the call site -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java SpecExecutorLevel2.java`.

`CustomerSpecs.isActive()` and `CustomerSpecs.inRegion("EU")` are independent, reusable static factory methods, each returning a small `Specification`. `.and(...)` — a default method on the `Specification` interface — combines them into a single composed specification, translated into one `WHERE active = true AND region = 'EU'` query, without either individual specification needing to know about the other.

### Level 3 — Advanced

Build a variable-length specification chain from optional search-form input — the realistic "combine whichever filters were actually supplied" pattern, mirroring the earlier custom-fragment and Querydsl cards' dynamic-filter examples, but using `Specification.and()` chaining instead.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

@SpringBootApplication
public class SpecExecutorLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String category;
        private double price;
        protected Product() {}
        public Product(String category, double price) { this.category = category; this.price = price; }
        public String getCategory() { return category; }
        public double getPrice() { return price; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long>, JpaSpecificationExecutor<Product> {}

    public record SearchCriteria(String category, Double minPrice, Double maxPrice) {}

    static Specification<Product> buildSpecification(SearchCriteria criteria) {
        Specification<Product> spec = Specification.where(null); // a no-op starting point
        if (criteria.category() != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("category"), criteria.category()));
        }
        if (criteria.minPrice() != null) {
            spec = spec.and((root, query, cb) -> cb.greaterThanOrEqualTo(root.get("price"), criteria.minPrice()));
        }
        if (criteria.maxPrice() != null) {
            spec = spec.and((root, query, cb) -> cb.lessThanOrEqualTo(root.get("price"), criteria.maxPrice()));
        }
        return spec;
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecExecutorLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:specexec3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("tools", 15.0));
        repo.save(new Product("tools", 45.0));
        repo.save(new Product("electronics", 25.0));

        // Only category + minPrice supplied -- maxPrice omitted entirely.
        Specification<Product> spec = buildSpecification(new SearchCriteria("tools", 20.0, null));
        List<Product> result = repo.findAll(spec);

        System.out.println("tools priced >=20: " + result.stream().map(Product::getPrice).toList());

        if (result.size() != 1 || result.get(0).getPrice() != 45.0)
            throw new AssertionError("Expected only the 45.0-priced tools product to match the 2-of-3 supplied filters");
        System.out.println("Variable-length Specification chain handled optional search criteria correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java SpecExecutorLevel3.java`.

`Specification.where(null)` provides a genuinely no-op starting specification (matching everything), which the loop then progressively `.and()`s additional conditions onto, only for the criteria fields that were actually supplied — exactly two of the three possible filters here (`category`, `minPrice`), with `maxPrice` entirely omitted from the resulting query since it was `null` in the input `SearchCriteria`. This mirrors the dynamic-filtering pattern from the earlier custom-fragment and Querydsl cards, using `Specification` composition instead of `List<Predicate>` or `BooleanBuilder`.

## 6. Walkthrough

Trace `buildSpecification(new SearchCriteria("tools", 20.0, null))`.

1. **`Specification.where(null)`** creates a starting specification whose `toPredicate` effectively contributes no condition at all — a safe, neutral starting point for the chain.
2. **`criteria.category() != null`** is `true` (`"tools"`), so `spec = spec.and((root, query, cb) -> cb.equal(root.get("category"), "tools"))` — the specification now represents `category = 'tools'`.
3. **`criteria.minPrice() != null`** is `true` (`20.0`), so `spec = spec.and((root, query, cb) -> cb.greaterThanOrEqualTo(root.get("price"), 20.0))` — the specification now represents `category = 'tools' AND price >= 20.0`.
4. **`criteria.maxPrice() != null`** is `false` (it's `null` in this call), so this branch is skipped entirely — no third condition is ever added to the chain.
5. **`repo.findAll(spec)`**: Spring Data JPA's Specification support translates the final composed `Specification` into an actual JPA `CriteriaQuery`, producing SQL equivalent to `WHERE category = 'tools' AND price >= 20.0` — genuinely just the two conditions that were actually supplied.
6. **Execution**: among the three seeded products, only the `"tools"`-category product priced `45.0` satisfies both conditions (`15.0` fails the `>= 20.0` check; the `"electronics"` product fails the category check).
7. **Verification**: the program checks exactly one result was returned, and that it's the expected `45.0`-priced product, confirming the dynamic specification chain correctly reflected only the criteria fields that were actually non-null.

```
 SearchCriteria(category="tools", minPrice=20.0, maxPrice=null)
        |
        v
 Specification.where(null)
        .and(category = 'tools')       <- criteria.category() != null
        .and(price >= 20.0)             <- criteria.minPrice() != null
        (maxPrice skipped entirely -- criteria.maxPrice() == null)
        |
        v
 WHERE category = 'tools' AND price >= 20.0   -- exactly 2 conditions, not 3
```

## 7. Gotchas & takeaways

> **Gotcha:** the `query` parameter available inside a `Specification`'s lambda (`(root, query, cb) -> ...`) gives access to the full `CriteriaQuery`, which can be used to add `DISTINCT`, ordering, or even subqueries — but modifying `query` from within a `Specification` that gets composed with `.and()`/`.or()` alongside other specifications can produce surprising interactions, since multiple specifications in a chain might each try to configure the same shared `CriteriaQuery`. Keep individual specifications focused purely on contributing their own `Predicate`, and handle query-wide concerns (distinct, ordering) separately, outside the composed specification chain, when possible.

- `JpaSpecificationExecutor<T>` lets a repository accept `Specification<T>` objects directly — a lighter-weight alternative to a full custom fragment (from an earlier card) for the common case of dynamic, composable filtering.
- `Specification` is a functional interface wrapping standard JPA Criteria API logic (`Root`, `CriteriaQuery`, `CriteriaBuilder`) — the same primitives used in hand-written custom fragments, just packaged as small, independently-reusable units.
- `.and(...)`/`.or(...)` (default methods on `Specification`) compose independently-defined specifications at the call site — `Specification.where(null)` is the standard, safe starting point for building a variable-length chain from optional criteria.
- Choosing between `JpaSpecificationExecutor` (Criteria API-based, no build-time code generation needed) and `QuerydslPredicateExecutor` (stronger compile-time type safety, requires an annotation-processing build step) is a genuine tradeoff — both solve the same fundamental "dynamic, composable query filtering" problem from different angles.
