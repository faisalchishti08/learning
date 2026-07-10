---
card: spring-data
gi: 38
slug: querydsl-integration-querydslpredicateexecutor
title: "Querydsl integration (QuerydslPredicateExecutor)"
---

## 1. What it is

Querydsl is a library that generates type-safe, fluent query classes (`QCustomer`, `QOrder`, and so on) from annotated entity classes at compile time — `QuerydslPredicateExecutor<T>` is the Spring Data interface that lets a repository accept a Querydsl `Predicate` directly, executing it as a query, giving repositories an additional way to build dynamic, type-safe queries beyond derived methods, `@Query`, and hand-written Criteria API fragments (covered earlier in this section).

```java
QCustomer customer = QCustomer.customer;
Predicate predicate = customer.lastName.eq("Lovelace").and(customer.active.isTrue());

List<Customer> results = customerRepository.findAll(predicate); // via QuerydslPredicateExecutor
```

## 2. Why & when

Building dynamic queries with the JPA Criteria API (as the earlier custom-fragment card demonstrated) works, but its verbose, string-based-property-reference style (`root.get("category")`) has no compile-time type safety — a typo in a property name fails only at runtime. Querydsl solves this by generating a `Q`-prefixed metamodel class per entity, with a strongly-typed field for every property, letting predicates be built with full IDE autocomplete and compiler verification. `QuerydslPredicateExecutor` is the bridge that lets Spring Data repositories accept these predicates directly, without needing a hand-written custom fragment (from the earlier card) just to execute one.

Reach for Querydsl integration specifically when:

- You need dynamic, type-safe query construction — the same "combine an arbitrary subset of optional filters" need the custom-fragment card addressed with the Criteria API, but with compile-time safety for property references instead of Criteria's string-based ones.
- You want IDE autocomplete and refactoring support for query construction — renaming an entity field and having every Querydsl predicate referencing it either update automatically or fail to compile, rather than silently breaking at runtime.
- You're already using Querydsl elsewhere in a codebase (for other query-building needs) and want the same predicate style to work directly against Spring Data repositories, without a separate custom-implementation layer.

## 3. Core concept

```
 Annotated entity:
   @Entity
   public class Customer {
       private String lastName;
       private boolean active;
   }
        |
        v
 Querydsl's annotation processor generates, AT COMPILE TIME:
   QCustomer.customer.lastName   -- a typed StringPath
   QCustomer.customer.active     -- a typed BooleanPath

 Repository interface:
   interface CustomerRepository extends JpaRepository<Customer, Long>,
       QuerydslPredicateExecutor<Customer> {}
        |
        v
 Predicate predicate = QCustomer.customer.lastName.eq("Lovelace")
     .and(QCustomer.customer.active.isTrue());
        |
        v
 customerRepository.findAll(predicate)   -- inherited from QuerydslPredicateExecutor
   customerRepository.findOne(predicate)
   customerRepository.count(predicate)
   customerRepository.exists(predicate)
```

Every predicate is built from strongly-typed, generated fields (`QCustomer.customer.lastName`) — a typo like `.lastNaem` simply doesn't compile, since no such field exists on the generated `QCustomer` class.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Querydsl's annotation processor generates a typed Q-class from the entity, used to build compile-time-checked predicates executed via QuerydslPredicateExecutor">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Entity Customer</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compile-time annotation processing</text>

  <rect x="230" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">QCustomer (generated)</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">typed fields: lastName, active</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repo.findAll(predicate)</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">QuerydslPredicateExecutor</text>

  <line x1="200" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="47" x2="445" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A compile-time-generated metamodel class is what makes every predicate reference type-checked.

## 5. Runnable example

The scenario: a `Customer` search using Querydsl, evolving from a basic predicate query, to combining predicates dynamically based on optional filters, to Querydsl's paging/sorting integration alongside `Predicate`-based filtering.

### Level 1 — Basic

Build a simple `Predicate` using a generated `Q`-class and execute it via `QuerydslPredicateExecutor.findAll(Predicate)`.

```java
import com.querydsl.core.types.Predicate;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.querydsl.QuerydslPredicateExecutor;

import java.util.List;

@SpringBootApplication
public class QuerydslLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String lastName;
        private boolean active;
        protected Customer() {}
        public Customer(String lastName, boolean active) { this.lastName = lastName; this.active = active; }
        public String getLastName() { return lastName; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long>, QuerydslPredicateExecutor<Customer> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QuerydslLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:querydsl1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Lovelace", true));
        repo.save(new Customer("Hopper", true));
        repo.save(new Customer("Lovelace", false)); // same last name, inactive

        // QCustomer is generated at compile time from the Customer entity by Querydsl's
        // annotation processor -- strongly-typed fields, no string property names.
        QCustomer customer = QCustomer.customer;
        Predicate predicate = customer.lastName.eq("Lovelace").and(customer.active.isTrue());

        List<Customer> results = (List<Customer>) repo.findAll(predicate);
        System.out.println("active Lovelaces = " + results.size());

        if (results.size() != 1) throw new AssertionError("Expected exactly 1 active customer named Lovelace");
        System.out.println("QuerydslPredicateExecutor.findAll(Predicate) worked with a type-safe predicate -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `com.h2database:h2`, `com.querydsl:querydsl-jpa` (classifier `jakarta`), and `com.querydsl:querydsl-apt` (annotation processor, classifier `jakarta`) on the classpath, configured to run Querydsl's annotation processor during compilation so `QCustomer` is generated, then `java QuerydslLevel1.java` on JDK 17+ (or run inside a Maven/Gradle build that wires up the Querydsl APT step).

`QCustomer.customer` is the generated metamodel instance; `.lastName.eq("Lovelace")` and `.active.isTrue()` are strongly-typed predicate builders — combined via `.and(...)` into one `Predicate`, then passed directly to `repo.findAll(predicate)`, a method `CustomerRepository` inherits purely from extending `QuerydslPredicateExecutor<Customer>`.

### Level 2 — Intermediate

Build a `Predicate` dynamically from a set of optional filters using `BooleanBuilder`, mirroring the earlier custom-fragment card's dynamic-filter scenario, but with Querydsl's type-safe API instead of the Criteria API.

```java
import com.querydsl.core.BooleanBuilder;
import com.querydsl.core.types.Predicate;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.querydsl.QuerydslPredicateExecutor;

import java.util.List;

@SpringBootApplication
public class QuerydslLevel2 {

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

    public interface ProductRepository extends JpaRepository<Product, Long>, QuerydslPredicateExecutor<Product> {}

    public record SearchCriteria(String category, Double minPrice) {}

    static Predicate buildPredicate(SearchCriteria criteria) {
        QProduct product = QProduct.product;
        BooleanBuilder builder = new BooleanBuilder();
        if (criteria.category() != null) {
            builder.and(product.category.eq(criteria.category()));
        }
        if (criteria.minPrice() != null) {
            builder.and(product.price.goe(criteria.minPrice()));
        }
        return builder;
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QuerydslLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:querydsl2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("tools", 25.0));
        repo.save(new Product("tools", 5.0));
        repo.save(new Product("electronics", 50.0));

        Predicate predicate = buildPredicate(new SearchCriteria("tools", 10.0));
        List<Product> result = (List<Product>) repo.findAll(predicate);

        System.out.println("dynamic predicate result count = " + result.size());

        if (result.size() != 1 || result.get(0).getPrice() != 25.0)
            throw new AssertionError("Expected only the 25.0-priced tools product to match");
        System.out.println("BooleanBuilder composed an optional-filter predicate dynamically, type-safely -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath and build configuration as Level 1, `java QuerydslLevel2.java`.

`BooleanBuilder` accumulates `AND`-combined conditions conditionally, exactly like the earlier Criteria-based custom fragment's `List<Predicate>` — but every condition (`product.category.eq(...)`, `product.price.goe(...)`) references a strongly-typed generated field, so a typo or type mismatch would be a compile error, not a runtime surprise.

### Level 3 — Advanced

Combine `Predicate`-based filtering with `Pageable`/`Sort`, since `QuerydslPredicateExecutor` also has an overload accepting both — the realistic shape of a fully dynamic, paginated, sorted search endpoint.

```java
import com.querydsl.core.types.Predicate;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.querydsl.QuerydslPredicateExecutor;

@SpringBootApplication
public class QuerydslLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String category;
        private double price;
        protected Product() {}
        public Product(String category, double price) { this.category = category; this.price = price; }
        public double getPrice() { return price; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long>, QuerydslPredicateExecutor<Product> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QuerydslLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:querydsl3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 20; i++) {
            repo.save(new Product(i % 2 == 0 ? "tools" : "electronics", i * 5.0));
        }

        QProduct product = QProduct.product;
        Predicate predicate = product.category.eq("tools");

        // QuerydslPredicateExecutor.findAll(predicate, pageable) combines type-safe
        // filtering with the SAME Page/Pageable/Sort machinery from earlier cards.
        Page<Product> page = repo.findAll(predicate, PageRequest.of(0, 3, Sort.by("price").descending()));

        System.out.println("page 1 of tools, by price desc: " + page.getContent().stream().map(Product::getPrice).toList());
        System.out.println("total tools matching = " + page.getTotalElements());

        if (page.getTotalElements() != 10) throw new AssertionError("Expected 10 tools products total");
        if (page.getContent().size() != 3) throw new AssertionError("Expected a page of 3");
        if (page.getContent().get(0).getPrice() != 100.0) throw new AssertionError("Expected the highest-priced tools product first");

        System.out.println("Predicate + Pageable combined via QuerydslPredicateExecutor -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath and build configuration as Level 1 and 2, `java QuerydslLevel3.java`.

`repo.findAll(predicate, pageable)` — a `QuerydslPredicateExecutor` overload — combines the type-safe `Predicate` filter with the exact same `Pageable`/`Sort` mechanism from the earlier paging cards in this section, returning a genuine `Page<Product>` complete with count metadata scoped to the filtered `"tools"` category (10 total), not the whole unfiltered table (20 total).

## 6. Walkthrough

Trace Level 3's `repo.findAll(predicate, pageable)` call.

1. **Predicate construction**: `product.category.eq("tools")` builds a `Predicate` object entirely in Java, using the generated `QProduct` metamodel — no database interaction has happened yet.
2. **`Pageable` construction**: `PageRequest.of(0, 3, Sort.by("price").descending())` builds a `Pageable` describing page 0, size 3, sorted by `price` descending — the same object type used throughout this section's earlier pagination cards.
3. **`repo.findAll(predicate, pageable)` call**: Spring Data's Querydsl integration translates the `Predicate` into a JPA `Predicate`/JPQL `WHERE` clause equivalent, combines it with the `Pageable`'s `ORDER BY`/`LIMIT`/`OFFSET`, and executes the resulting query against H2 — conceptually `SELECT p FROM Product p WHERE p.category = 'tools' ORDER BY p.price DESC LIMIT 3 OFFSET 0`.
4. **Count query**: exactly as with the `Pageable`-based `findAll` methods from earlier cards, a second query computes the total count *scoped to the same predicate* — `SELECT COUNT(p) FROM Product p WHERE p.category = 'tools'`, correctly returning `10` (only tools products), not `20` (the full table).
5. **`Page<Product>` assembly**: the 3 returned rows (the 3 highest-priced tools products) plus the scoped total count (10) are assembled into the returned `Page<Product>`.
6. **Verification**: the program checks the total element count reflects the filtered scope, the page content size matches the requested page size, and the first item is indeed the highest-priced match — confirming type-safe predicate filtering and pagination composed correctly together.

```
 predicate = QProduct.product.category.eq("tools")
 pageable  = PageRequest.of(0, 3, Sort.by("price").descending())
        |
        v
 repo.findAll(predicate, pageable)
        |
        +-- content query: WHERE category='tools' ORDER BY price DESC LIMIT 3
        +-- count query:   WHERE category='tools'  (scoped to the SAME predicate)
        |
        v
 Page<Product> { content: [3 highest-priced tools], totalElements: 10 }
```

## 7. Gotchas & takeaways

> **Gotcha:** `QuerydslPredicateExecutor` requires Querydsl's annotation processor to run during the build, generating `Q`-prefixed classes for every `@Entity` — this is a build-configuration step (a Maven/Gradle annotation-processing setup), not something that happens automatically just by adding the Querydsl JPA dependency to the classpath. A missing or misconfigured annotation-processing step produces "cannot find symbol: QCustomer" compile errors, which can be confusing if the underlying cause (the code generation step never ran) isn't obvious.

- `QuerydslPredicateExecutor<T>` lets a repository accept a Querydsl `Predicate` directly — an alternative to derived queries, `@Query`, and hand-written custom fragments (from an earlier card) for building dynamic queries, with full compile-time type safety on property references.
- Querydsl's generated `Q`-classes (`QCustomer`, `QProduct`) are produced by an annotation processor at compile time from `@Entity`-annotated classes — a build-time code-generation step that must be correctly wired into the project's build configuration.
- `BooleanBuilder` is the standard way to compose a `Predicate` from a variable set of optional conditions — the type-safe counterpart to the Criteria API's `List<Predicate>` approach from the earlier custom-fragment card.
- `QuerydslPredicateExecutor` methods compose with `Pageable`/`Sort` exactly like the rest of Spring Data's pagination machinery, letting type-safe dynamic filtering and pagination work together in a single call.
