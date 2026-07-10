---
card: spring-data
gi: 29
slug: custom-repository-implementations-fragments
title: "Custom repository implementations (fragments)"
---

## 1. What it is

A custom repository implementation ("fragment") is hand-written Java code plugged into an otherwise auto-generated repository proxy — used when a specific operation genuinely can't be expressed through query derivation or `@Query` (complex multi-step logic, calling an external system, building a query dynamically at runtime with the JPA Criteria API). The pattern: declare a fragment interface with the custom method(s), write a class implementing it named `<RepositoryName><Postfix>` (default postfix `Impl`, as seen in the previous card), and have the main repository interface extend both the standard Spring Data interface and the fragment interface.

```java
interface CustomerRepositoryCustom {
    List<Customer> findByComplexCriteria(SearchCriteria criteria); // hand-implemented
}

class CustomerRepositoryImpl implements CustomerRepositoryCustom {
    // real, hand-written implementation using CriteriaBuilder, an EntityManager, etc.
}

interface CustomerRepository extends JpaRepository<Customer, Long>, CustomerRepositoryCustom {}
```

## 2. Why & when

Query derivation and `@Query` cover the enormous majority of real query needs, but a genuine minority of operations need more than a declarative query can express: building a `WHERE` clause dynamically based on which of several optional search fields were actually supplied, calling multiple repository methods and combining results with business logic, or integrating a non-JPA data source into what otherwise looks like a normal repository method. Custom implementations exist to let exactly those methods live alongside the auto-generated ones, on the same repository interface, indistinguishable to calling code.

Reach for a custom implementation specifically when:

- A query's structure depends on runtime conditions in a way no fixed JPQL string or derived method name can express — a dynamic search form where any subset of several optional filters might be present.
- The operation needs the JPA Criteria API, a `TypedQuery` built up programmatically, or direct `EntityManager` access beyond what `@Query` offers.
- The "query" isn't really a query at all — it involves calling an external service, combining data from multiple sources, or other logic that belongs conceptually on the repository but can't be expressed as a single declarative query.

## 3. Core concept

```
 1. Fragment interface -- declares the custom method(s):
    interface CustomerRepositoryCustom {
        List<Customer> findByComplexCriteria(SearchCriteria criteria);
    }

 2. Implementation class -- named <RepositoryInterfaceName> + Postfix (default "Impl"):
    class CustomerRepositoryImpl implements CustomerRepositoryCustom {
        @PersistenceContext private EntityManager em;
        public List<Customer> findByComplexCriteria(SearchCriteria criteria) {
            // real, hand-written logic -- CriteriaBuilder, EntityManager, whatever's needed
        }
    }

 3. Main repository interface -- extends BOTH:
    interface CustomerRepository extends JpaRepository<Customer, Long>, CustomerRepositoryCustom {}

 At proxy-generation time, Spring Data builds a COMPOSITE proxy:
   standard methods (save, findById, derived queries) -> generated implementation
   fragment methods (findByComplexCriteria)             -> delegated to CustomerRepositoryImpl
   BOTH accessible through the SAME CustomerRepository reference
```

The naming convention (`Impl` suffix by default) is what links the fragment interface's implementation class to the main repository — no explicit wiring annotation is needed once the naming convention is followed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CustomerRepository composes generated CRUD behavior with a hand-written fragment implementation into one proxy">
  <rect x="180" y="15" width="280" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CustomerRepository (composite proxy)</text>

  <rect x="30" y="100" width="260" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">save, findById, derived queries</text>
  <text x="160" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GENERATED implementation</text>

  <rect x="350" y="100" width="260" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByComplexCriteria(...)</text>
  <text x="480" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delegates to CustomerRepositoryImpl</text>

  <line x1="270" y1="60" x2="180" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="370" y1="60" x2="460" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both call paths pass through the same `CustomerRepository` reference — callers can't tell which methods are generated and which are hand-written.

## 5. Runnable example

The scenario: a `Product` search with several optional filters, evolving from a basic custom fragment using the JPA Criteria API, to composing standard and custom methods together, to a fragment calling multiple internal helper methods — the realistic shape of non-trivial custom repository logic.

### Level 1 — Basic

Build a custom fragment implementing a dynamic search using `CriteriaBuilder`, handling an arbitrary combination of optional filters.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class FragmentLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String category;
        private Double minPrice;
        private String name;
        private double price;
        protected Product() {}
        public Product(String name, String category, double price) { this.name = name; this.category = category; this.price = price; }
        public String getName() { return name; }
    }

    public record SearchCriteria(String category, Double minPrice) {}

    public interface ProductRepositoryCustom {
        List<Product> search(SearchCriteria criteria);
    }

    public static class ProductRepositoryImpl implements ProductRepositoryCustom {
        @PersistenceContext
        private EntityManager em;

        @Override
        public List<Product> search(SearchCriteria criteria) {
            CriteriaBuilder cb = em.getCriteriaBuilder();
            CriteriaQuery<Product> query = cb.createQuery(Product.class);
            Root<Product> root = query.from(Product.class);

            List<Predicate> predicates = new ArrayList<>();
            if (criteria.category() != null) {
                predicates.add(cb.equal(root.get("category"), criteria.category()));
            }
            if (criteria.minPrice() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("price"), criteria.minPrice()));
            }
            query.where(predicates.toArray(new Predicate[0]));
            return em.createQuery(query).getResultList();
        }
    }

    public interface ProductRepository extends JpaRepository<Product, Long>, ProductRepositoryCustom {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FragmentLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:fragment1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", "tools", 25.0));
        repo.save(new Product("Cheap Widget", "tools", 5.0));
        repo.save(new Product("Gadget", "electronics", 50.0));

        List<Product> result = repo.search(new SearchCriteria("tools", 10.0));
        System.out.println("search(category=tools, minPrice=10.0) = " + result.stream().map(Product::getName).toList());

        if (result.size() != 1 || !result.get(0).getName().equals("Widget"))
            throw new AssertionError("Expected only 'Widget' to match both filters");
        System.out.println("Custom fragment with CriteriaBuilder handled dynamic optional filters -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java FragmentLevel1.java` on JDK 17+.

`ProductRepositoryImpl` (matching `ProductRepository` + the default `Impl` postfix) hand-builds a `CriteriaQuery`, adding a `Predicate` only for each non-null field of `SearchCriteria` — this dynamic predicate-list construction is exactly what neither query derivation nor a single fixed `@Query` string can express, since the actual `WHERE` clause shape varies based on which filters were supplied at runtime.

### Level 2 — Intermediate

Combine standard, generated repository methods (`save`, a derived query) with the custom fragment method on the same `ProductRepository` reference, confirming both live together seamlessly.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PersistenceContext;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class FragmentLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String category;
        private double price;
        protected Product() {}
        public Product(String category, double price) { this.category = category; this.price = price; }
        public String getCategory() { return category; }
    }

    public interface ProductRepositoryCustom {
        long countMatchingLegacyRule(); // a hand-written "custom" business rule
    }

    public static class ProductRepositoryImpl implements ProductRepositoryCustom {
        @PersistenceContext
        private EntityManager em;

        @Override
        public long countMatchingLegacyRule() {
            // Deliberately non-trivial "legacy business rule" logic that doesn't map to a simple query.
            List<Product> all = em.createQuery("select p from Product p", Product.class).getResultList();
            return all.stream().filter(p -> p.getCategory().equals("tools") && p.price > 10.0).count();
        }
    }

    public interface ProductRepository extends JpaRepository<Product, Long>, ProductRepositoryCustom {
        List<Product> findByCategory(String category); // ordinary derived query
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FragmentLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:fragment2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("tools", 25.0));   // matches the rule
        repo.save(new Product("tools", 5.0));    // fails price threshold
        repo.save(new Product("electronics", 50.0)); // fails category

        List<Product> tools = repo.findByCategory("tools"); // GENERATED derived query
        long legacyCount = repo.countMatchingLegacyRule();   // CUSTOM fragment method

        System.out.println("tools category count (derived) = " + tools.size());
        System.out.println("legacy rule count (custom) = " + legacyCount);

        if (tools.size() != 2) throw new AssertionError("Expected 2 tools products via derived query");
        if (legacyCount != 1) throw new AssertionError("Expected exactly 1 product matching the custom legacy rule");
        System.out.println("Generated and custom fragment methods coexisted on one repository interface -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java FragmentLevel2.java`.

`findByCategory` is an entirely ordinary derived query, generated automatically. `countMatchingLegacyRule` is entirely hand-written, delegating to `ProductRepositoryImpl`. Both are called through the identical `ProductRepository` reference — the composite proxy Spring Data builds at startup routes each method call to the correct underlying implementation transparently, with no visible seam from the caller's perspective.

### Level 3 — Advanced

Write a fragment method that internally calls *other* repository methods (both generated and custom) to compose a more complex operation — showing custom implementations can freely use the rest of the repository's own capabilities, not just raw `EntityManager` access.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PersistenceContext;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.core.support.RepositoryFactoryBeanSupport;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@SpringBootApplication
public class FragmentLevel3 {

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

    public interface ProductRepositoryCustom {
        Map<String, Double> averagePriceByCategory();
    }

    // Note: implementation classes CAN have @Autowired constructors to access the
    // EntityManager (or other Spring beans) needed for genuinely custom logic.
    public static class ProductRepositoryImpl implements ProductRepositoryCustom {
        @PersistenceContext
        private EntityManager em;

        @Override
        public Map<String, Double> averagePriceByCategory() {
            // Composes logic across the full result set -- something no single derived
            // query or simple @Query aggregate cleanly expresses in one line.
            List<Product> all = em.createQuery("select p from Product p", Product.class).getResultList();
            return all.stream()
                .collect(Collectors.groupingBy(Product::getCategory, Collectors.averagingDouble(Product::getPrice)));
        }
    }

    public interface ProductRepository extends JpaRepository<Product, Long>, ProductRepositoryCustom {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(FragmentLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:fragment3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("tools", 10.0));
        repo.save(new Product("tools", 30.0)); // tools avg: 20.0
        repo.save(new Product("electronics", 100.0));
        repo.save(new Product("electronics", 50.0)); // electronics avg: 75.0

        Map<String, Double> averages = repo.averagePriceByCategory();
        System.out.println("average price by category: " + averages);

        if (averages.get("tools") != 20.0) throw new AssertionError("Expected tools average of 20.0");
        if (averages.get("electronics") != 75.0) throw new AssertionError("Expected electronics average of 75.0");
        System.out.println("Custom fragment composed a grouped aggregate not expressible as a single derived query -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java FragmentLevel3.java`.

`averagePriceByCategory()` computes a per-category average using Java's `Stream`/`Collectors.groupingBy` after loading the full result set — while a real production version might prefer a JPQL `GROUP BY` query for efficiency at scale, this demonstrates that custom fragment methods have complete freedom to combine data loading with arbitrary Java logic, unconstrained by what any declarative query mechanism (derived or `@Query`) can express in a single statement.

## 6. Walkthrough

Trace how `repo.averagePriceByCategory()` resolves and executes.

1. **Proxy generation at startup**: Spring Data recognizes `ProductRepository` extends both `JpaRepository<Product, Long>` (the standard contract) and `ProductRepositoryCustom` (a fragment interface). It looks for an implementation class named `ProductRepositoryImpl` (the main interface's simple name, `ProductRepository`, plus the default `Impl` postfix) — finds it, and registers it as a *fragment* backing this repository, alongside the generated `SimpleJpaRepository`-based implementation for the standard methods.
2. **Composite proxy assembly**: the final `ProductRepository` proxy is built as a composite — method calls matching `ProductRepositoryCustom`'s declared methods (`averagePriceByCategory`) are routed to the `ProductRepositoryImpl` instance; every other method call (`save`, `findById`, and so on) is routed to the standard generated implementation.
3. **Dependency injection into the fragment**: `ProductRepositoryImpl` is itself treated somewhat like a Spring-managed component during this wiring — its `@PersistenceContext`-annotated `EntityManager` field is populated, giving the hand-written code direct database access.
4. **`repo.averagePriceByCategory()` call**: the composite proxy recognizes this method belongs to the custom fragment, and delegates the call directly to `ProductRepositoryImpl.averagePriceByCategory()`.
5. **Inside the fragment method**: `em.createQuery("select p from Product p", Product.class).getResultList()` loads every `Product` row as fully-materialized entities.
6. **Java-side aggregation**: `Collectors.groupingBy(Product::getCategory, Collectors.averagingDouble(Product::getPrice))` groups the loaded products by category and computes each group's average price — pure Java `Stream` logic, entirely outside any query language.
7. **Return value**: a `Map<String, Double>` (`{"tools": 20.0, "electronics": 75.0}`) is returned directly to the caller, exactly as if it had come from any other repository method — the caller has no way to tell, just from the call site, that this method's implementation was hand-written rather than generated.
8. **Verification**: the program checks both computed averages against the expected values, confirming the custom fragment's logic executed correctly end-to-end.

```
 ProductRepository (composite proxy)
        |
        +-- save(), findById(), ...        --> generated SimpleJpaRepository implementation
        |
        +-- averagePriceByCategory()        --> delegates to ProductRepositoryImpl
                                                        |
                                                        v
                                            EntityManager query --> Stream groupingBy/averagingDouble
                                                        |
                                                        v
                                            Map<String, Double> returned to caller
```

## 7. Gotchas & takeaways

> **Gotcha:** the naming convention linking a fragment interface's implementation to the main repository (`<RepositoryInterfaceName><Postfix>`, default `Impl`) is based on the *main repository interface's* simple name, not the fragment interface's name — a common mistake is naming the implementation class after the fragment interface (`ProductRepositoryCustomImpl`) instead of the main repository (`ProductRepositoryImpl`), which silently fails to wire up, since Spring Data won't find a matching implementation and either ignores the fragment method or fails at startup, depending on the exact configuration.

- Custom repository implementations ("fragments") let hand-written Java code — using the Criteria API, direct `EntityManager` access, or arbitrary business logic — live alongside auto-generated repository methods on the exact same interface, invisible to calling code.
- The linking mechanism is a naming convention: an implementation class named `<MainRepositoryInterfaceName><Postfix>` (default postfix `Impl`, configurable via `@EnableJpaRepositories`'s `repositoryImplementationPostfix` from the previous card) automatically backs the fragment interface's methods.
- Fragment implementation classes get full Spring dependency injection (`@PersistenceContext`, `@Autowired`, and so on) — they're wired into the repository infrastructure, not instantiated as plain, disconnected Java objects.
- Reach for a custom fragment specifically when an operation's logic genuinely can't be expressed as a single declarative query — dynamic optional filtering, multi-step business logic, or integration with something beyond a single JPQL/native query.
