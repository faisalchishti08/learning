---
card: spring-data
gi: 13
slug: query-lookup-strategies-create-use-declared-query-create-if
title: "Query lookup strategies (CREATE, USE_DECLARED_QUERY, CREATE_IF_NOT_FOUND)"
---

## 1. What it is

A query lookup strategy is the rule Spring Data follows, for each repository method, to decide *where* the actual query comes from: derive it purely from the method name (`CREATE`), require a query to already be declared somewhere — an `@Query` annotation or a named query — and fail if there isn't one (`USE_DECLARED_QUERY`), or check for a declared query first and fall back to name-derivation if none exists (`CREATE_IF_NOT_FOUND`, the default). This is the configuration knob controlling how strictly Spring Data enforces "queries should be declared explicitly" versus "queries can be inferred from naming conventions."

```java
@EnableJpaRepositories(queryLookupStrategy = QueryLookupStrategy.Key.CREATE_IF_NOT_FOUND)
public class AppConfig {}
```

## 2. Why & when

The earlier query-derivation card showed method names being turned into queries automatically — that automatic behavior isn't unconditional; it's governed by this strategy setting, which every Spring Data module reads when building each repository method's implementation. `CREATE_IF_NOT_FOUND` (the default in virtually every setup) is why both `@Query`-annotated methods and plain derived-name methods work side-by-side in the same repository without extra configuration — but understanding the other two strategies clarifies exactly what's happening, and matters when a team wants to enforce a stricter convention.

Understanding query lookup strategies matters specifically when:

- You're debugging why a method that should have used a declared `@Query` (or a named query) instead silently fell back to name-derivation (or vice versa) — the active strategy explains the precedence.
- You're enforcing a team convention that *all* queries must be explicitly declared (no "magic" name-derived queries allowed, for auditability or because a team finds long derived method names hard to review) — setting `USE_DECLARED_QUERY` makes Spring Data fail fast at startup for any method lacking an explicit query, rather than silently deriving one.
- You want to understand precisely what `CREATE_IF_NOT_FOUND`, the default, actually does — since it's silently in effect in the vast majority of Spring Data applications without ever being mentioned explicitly.

## 3. Core concept

```
 For each declared repository method, Spring Data decides how to implement it:

 CREATE
   ALWAYS derive the query from the method name via PartTree parsing.
   Any @Query annotation present is IGNORED for lookup purposes (though in practice,
   CREATE is rarely combined with @Query-annotated methods at all).
   A method name PartTree can't parse => startup failure.

 USE_DECLARED_QUERY
   ONLY use an already-declared query: an @Query annotation, or a matching
   named query (covered in the next card). NEVER derive from the method name.
   A method with no declared query and no matching named query => startup failure.

 CREATE_IF_NOT_FOUND   (the default)
   Check for a declared query (@Query, or a named query) FIRST.
   If found, use it.
   If NOT found, fall back to CREATE-style name derivation.
   This is why @Query-annotated methods and plain derived-name methods
   coexist freely in the same repository with zero extra configuration.
```

`CREATE_IF_NOT_FOUND`'s "declared query wins, else derive" precedence is exactly the behavior every earlier card in this section relied on implicitly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CREATE_IF_NOT_FOUND checks for a declared query first, falling back to name derivation only if none exists">
  <rect x="230" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repository method</text>

  <rect x="230" y="90" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Query or named query?</text>
  <text x="320" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">declared explicitly?</text>

  <rect x="30" y="150" width="180" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="120" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">yes -> use the declared query</text>

  <rect x="440" y="150" width="180" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="530" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no -> derive from method name</text>

  <line x1="320" y1="60" x2="320" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="280" y1="135" x2="150" y2="148" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="360" y1="135" x2="500" y2="148" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Under the default strategy, an explicitly declared query always takes precedence over name derivation.

## 5. Runnable example

The scenario: one repository with both a derived-name method and an `@Query`-annotated method, proving `CREATE_IF_NOT_FOUND`'s precedence — then a second repository configured with `USE_DECLARED_QUERY`, proving a method lacking a declared query fails at startup rather than silently deriving one.

### Level 1 — Basic

Show `@Query` taking precedence over what would otherwise be name-derivation, even when the method name would itself parse into a valid (but different) query.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class QueryLookupLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean discontinued;
        protected Product() {}
        public Product(String name, boolean discontinued) { this.name = name; this.discontinued = discontinued; }
        public String getName() { return name; }
        public boolean isDiscontinued() { return discontinued; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        // The method name would normally derive: WHERE discontinued = ?1
        // But @Query OVERRIDES that -- it always deliberately returns the OPPOSITE.
        @Query("select p from Product p where p.discontinued = false")
        List<Product> findByDiscontinued(boolean discontinued);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryLookupLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:qlookup1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", false));
        repo.save(new Product("Old Gadget", true));

        // Calling with `true` -- if name-derivation were used, this would find the
        // discontinued product. Because @Query is declared, it ALWAYS returns
        // non-discontinued products instead, regardless of the argument passed.
        List<Product> result = repo.findByDiscontinued(true);
        System.out.println("findByDiscontinued(true) returned: " + result.stream().map(Product::getName).toList());

        if (result.size() != 1 || !result.get(0).getName().equals("Widget"))
            throw new AssertionError("Expected @Query to override derivation and return the non-discontinued product");
        System.out.println("@Query took precedence over name-derivation under CREATE_IF_NOT_FOUND -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java QueryLookupLevel1.java` on JDK 17+.

`findByDiscontinued(boolean discontinued)`'s name would, under pure `CREATE`, derive `WHERE discontinued = ?1` — calling it with `true` would return the discontinued product. But because `@Query` is present, `CREATE_IF_NOT_FOUND` finds the declared query first and uses it exclusively, deliberately ignoring what the method name would otherwise have meant — the query always returns non-discontinued products, regardless of the boolean argument (which is bound to nothing in the fixed query string). This demonstrates the precedence concretely, not just by assertion.

### Level 2 — Intermediate

Show name-derivation still working normally for a method with no declared query, in the very same repository as the `@Query`-overridden one from Level 1 — confirming `CREATE_IF_NOT_FOUND` genuinely evaluates each method independently.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class QueryLookupLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean discontinued;
        private String category;
        protected Product() {}
        public Product(String name, boolean discontinued, String category) {
            this.name = name; this.discontinued = discontinued; this.category = category;
        }
        public String getName() { return name; }
        public String getCategory() { return category; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        // Method 1: declared @Query -- always non-discontinued products.
        @Query("select p from Product p where p.discontinued = false")
        List<Product> findActiveProducts();

        // Method 2: NO @Query -- falls back to normal name-derivation.
        List<Product> findByCategory(String category);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryLookupLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:qlookup2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", false, "tools"));
        repo.save(new Product("Old Gadget", true, "tools"));
        repo.save(new Product("Gizmo", false, "electronics"));

        List<Product> active = repo.findActiveProducts();          // via @Query
        List<Product> tools = repo.findByCategory("tools");         // via name-derivation

        System.out.println("active products (via @Query) = " + active.stream().map(Product::getName).toList());
        System.out.println("tools category (via derivation) = " + tools.stream().map(Product::getName).toList());

        if (active.size() != 2) throw new AssertionError("Expected 2 active (non-discontinued) products");
        if (tools.size() != 2) throw new AssertionError("Expected 2 products in the tools category");
        System.out.println("Declared @Query and derived-name methods coexisted in one repository -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java QueryLookupLevel2.java`.

`findActiveProducts()` has an `@Query`, so `CREATE_IF_NOT_FOUND` uses it directly. `findByCategory(String category)` has no declared query, so the same strategy falls back to `PartTree`-based name derivation for it — both methods live on the identical `ProductRepository` interface, each independently resolved according to whether a declared query was present for that specific method.

### Level 3 — Advanced

Configure `USE_DECLARED_QUERY` explicitly via `@EnableJpaRepositories`, and show a method with no declared query and no matching named query failing at *application startup*, rather than silently falling back to derivation the way `CREATE_IF_NOT_FOUND` would.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.BeanCreationException;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.repository.query.QueryLookupStrategy;

import java.util.List;

@SpringBootApplication
@EnableJpaRepositories(queryLookupStrategy = QueryLookupStrategy.Key.USE_DECLARED_QUERY)
public class QueryLookupLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
        public String getName() { return name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        // Has a declared @Query -- fine under USE_DECLARED_QUERY.
        @Query("select p from Product p")
        List<Product> findAllExplicit();

        // NO @Query and NO matching named query -- USE_DECLARED_QUERY REQUIRES one to exist.
        // This method will fail at STARTUP, not at first call.
        List<Product> findByName(String name);
    }

    public static void main(String[] args) {
        boolean startupFailed = false;
        String failureMessage = "";
        try {
            ConfigurableApplicationContext ctx = SpringApplication.run(QueryLookupLevel3.class,
                "--spring.datasource.url=jdbc:h2:mem:qlookup3",
                "--spring.jpa.hibernate.ddl-auto=create-drop");
            ctx.close(); // should not be reached
        } catch (BeanCreationException | IllegalStateException ex) {
            startupFailed = true;
            failureMessage = ex.getMessage() != null ? ex.getMessage() : ex.getClass().getSimpleName();
            System.out.println("startup failed as expected: " + ex.getClass().getSimpleName());
            System.out.println("failure mentions the offending method? "
                + (String.valueOf(ex).contains("findByName") || (ex.getCause() != null && String.valueOf(ex.getCause()).contains("findByName"))));
        }

        if (!startupFailed)
            throw new AssertionError("Expected USE_DECLARED_QUERY to fail startup for findByName, which has no declared query");
        System.out.println("USE_DECLARED_QUERY correctly rejected a method with no declared query, at startup -- PASS");
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java QueryLookupLevel3.java` on JDK 17+. Expect this program to print a caught startup failure and then `PASS` — the failure itself is the correct, intended outcome.

`@EnableJpaRepositories(queryLookupStrategy = QueryLookupStrategy.Key.USE_DECLARED_QUERY)` forces every repository method in scope to have an explicitly declared query — `findAllExplicit()` satisfies this via `@Query`, but `findByName(String name)` has neither an `@Query` annotation nor a matching named query, so under `USE_DECLARED_QUERY` (unlike the default `CREATE_IF_NOT_FOUND`), Spring Data does *not* fall back to deriving a query from the method name — it fails immediately while building the repository proxy, which happens during `SpringApplication.run(...)`, well before any method is ever called.

## 6. Walkthrough

Trace Level 3's startup failure.

1. **`SpringApplication.run(...)` begins**, and as part of context refresh, Spring Data JPA's repository factory attempts to build a proxy for `ProductRepository`.
2. **Method-by-method resolution**: for each declared method, the factory consults the configured `QueryLookupStrategy` — here, `USE_DECLARED_QUERY`, set explicitly via `@EnableJpaRepositories`.
3. **`findAllExplicit()` resolves successfully**: it has an `@Query` annotation, satisfying `USE_DECLARED_QUERY`'s requirement, so the factory builds this method's implementation from the annotation's JPQL string.
4. **`findByName(String name)` fails resolution**: it has no `@Query` annotation and (since none was defined) no matching named query either. Under `USE_DECLARED_QUERY`, the factory does not fall back to `PartTree`-based derivation the way `CREATE_IF_NOT_FOUND` would — instead, it raises an exception describing exactly which method lacks a resolvable query.
5. **Exception propagation**: this failure occurs while Spring is still constructing the `ProductRepository` bean, so it propagates up through `SpringApplication.run(...)` as a `BeanCreationException` (or a related `IllegalStateException`, depending on the exact Spring Data version), preventing the application from starting at all.
6. **`main`'s `try`/`catch`** catches this startup exception, confirming both that it occurred and (via string inspection) that it references the specific failing method, `findByName`.
7. **Verification**: the program asserts a startup failure genuinely occurred, printing `PASS` for this specific test only because the *expected* behavior is a hard failure — the whole point of `USE_DECLARED_QUERY` is to make an undeclared query a build-breaking problem, not a silently-accepted one.

```
 @EnableJpaRepositories(queryLookupStrategy = USE_DECLARED_QUERY)
        |
        v
 building ProductRepository proxy...
        |
        +-- findAllExplicit()  -- has @Query --> OK, resolved
        |
        +-- findByName(String) -- NO @Query, NO named query
                    |
                    v
              USE_DECLARED_QUERY does NOT fall back to derivation
                    |
                    v
              startup FAILS here, before the app finishes booting
```

## 7. Gotchas & takeaways

> **Gotcha:** switching an existing application's `queryLookupStrategy` from the default `CREATE_IF_NOT_FOUND` to `USE_DECLARED_QUERY` is a breaking change for every repository method that currently relies on name-derivation with no declared query — every one of those methods will fail at the next startup. This is a deliberate, one-time migration decision (typically made to enforce "no magic derived queries" as a team convention), not something to change casually on an existing codebase without auditing every repository first.

- `CREATE_IF_NOT_FOUND` is Spring Data's default strategy, and it's why declared `@Query` methods and plain derived-name methods have coexisted freely in every repository interface used throughout this entire section — a declared query, when present, always wins.
- `CREATE` always derives from the method name and effectively ignores declared queries for lookup purposes — rarely used deliberately, since it defeats the point of writing `@Query` at all.
- `USE_DECLARED_QUERY` requires every repository method to have an explicit query (via `@Query` or a named query) and fails at startup for any method that doesn't — a strict, opt-in convention for codebases that want to forbid name-derivation entirely.
- All query-resolution failures under any strategy happen at *repository-proxy-creation time* (application startup), not at the first call to the failing method — this fail-fast behavior is consistent across all three strategies, only the specific failure conditions differ.
