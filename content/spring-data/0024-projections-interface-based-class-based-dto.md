---
card: spring-data
gi: 24
slug: projections-interface-based-class-based-dto
title: "Projections (interface-based & class-based DTO)"
---

## 1. What it is

A projection is a repository query that returns something *narrower* than the full entity — just the fields a particular use case actually needs — expressed either as an interface with getter methods matching the entity's property names (an interface-based, or "closed," projection) or as a plain class/record with a matching constructor (a class-based DTO projection). Spring Data generates the implementation for interface projections automatically and, for JPA, can even optimize the underlying SQL to select only the needed columns.

```java
public interface CustomerSummary {
    String getFullName();
    String getEmail();
}

List<CustomerSummary> findByStatus(String status); // returns ONLY name + email, not the whole entity
```

## 2. Why & when

Loading a full entity when only two or three of its fields are actually needed wastes memory, network bandwidth, and (for a wide entity with many columns or expensive-to-load relationships) real query time. Projections exist to let a repository method's return shape match what a specific use case actually needs — a summary list view doesn't need every column a detail view does — without hand-writing a separate DTO-mapping layer for every such case.

Reach for projections specifically when:

- You're building a list or summary view that only displays a handful of an entity's fields — a search-results table showing name and price, not every column of the underlying `Product` entity.
- You want the database itself to select fewer columns (a real performance win for wide tables or entities with expensive lazy associations) rather than fetching the full entity and discarding most of it in application code.
- You're returning API response data that intentionally excludes certain entity fields (internal flags, audit columns) — a projection interface or DTO is a clean, declarative way to define exactly what's exposed, without a manual mapping step.

## 3. Core concept

```
 INTERFACE-BASED (closed) projection:
   public interface CustomerSummary {
       String getFullName();   -- MUST match an entity property name (or be an @Value SpEL expression)
       String getEmail();
   }
   List<CustomerSummary> findByStatus(String status);
        |
        v
   Spring Data generates a PROXY implementing CustomerSummary at query-execution time,
   backed by the query result -- for JPA, the underlying SQL can be optimized to
   SELECT only fullName, email (not every column)

 CLASS-BASED (DTO) projection:
   public record CustomerSummary(String fullName, String email) {}
   List<CustomerSummary> findByStatus(String status);   -- via @Query with a "new" JPQL constructor expression
        |
        v
   Spring Data (via JPQL's "new com.example.CustomerSummary(...)" constructor expression)
   instantiates a REAL object -- not a proxy -- directly from the query's SELECT clause

 DYNAMIC projection: same METHOD, caller chooses the return type via a Class<T> parameter
   <T> List<T> findByStatus(String status, Class<T> type);
```

Interface-based projections are proxies generated at runtime; class-based (record/DTO) projections are real, instantiated objects — both achieve the same narrowing goal through different mechanisms.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Interface projections are generated proxies; class-based DTO projections are real instantiated objects from a constructor expression">
  <rect x="10" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">interface CustomerSummary</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getters only -- Spring Data</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">generates a PROXY at query time</text>

  <rect x="350" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">record CustomerSummary(...)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">via JPQL "new ...(...)" --</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a REAL instantiated object</text>

  <rect x="150" y="115" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">both narrow the query result to only the needed fields</text>
</svg>

Two different mechanisms — runtime proxy versus real object construction — achieving the same "select only what's needed" goal.

## 5. Runnable example

The scenario: a `Product` catalog, evolving from a basic interface-based projection with derived queries, to a class-based DTO projection via a JPQL constructor expression, to a dynamic projection letting the same method serve both the full entity and a narrow summary depending on what the caller asks for.

### Level 1 — Basic

Declare an interface-based projection and confirm a derived query returns proxy instances implementing only the narrowed getter set.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class ProjectionsLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private double price;
        private String internalSupplierCode; // deliberately NOT exposed via the projection
        protected Product() {}
        public Product(String name, double price, String internalSupplierCode) {
            this.name = name; this.price = price; this.internalSupplierCode = internalSupplierCode;
        }
    }

    // Interface-based (closed) projection -- getter names must match entity property names.
    public interface ProductSummary {
        String getName();
        double getPrice();
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        List<ProductSummary> findByPriceGreaterThan(double minPrice);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ProjectionsLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:proj1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", 9.99, "SUPP-001"));
        repo.save(new Product("Gadget", 49.99, "SUPP-002"));

        List<ProductSummary> summaries = repo.findByPriceGreaterThan(5.0);
        System.out.println("summaries: " + summaries.stream().map(s -> s.getName() + "=$" + s.getPrice()).toList());
        System.out.println("proxy implementation class = " + summaries.get(0).getClass().getSimpleName());

        if (summaries.size() != 2) throw new AssertionError("Expected 2 product summaries");
        System.out.println("Interface-based projection returned narrowed proxy instances -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ProjectionsLevel1.java` on JDK 17+.

`ProductSummary` declares only `getName()` and `getPrice()` — no `getInternalSupplierCode()` at all, so that field is never even exposed by this repository method's return type. `findByPriceGreaterThan(double minPrice)`, declared to return `List<ProductSummary>` instead of `List<Product>`, causes Spring Data to generate proxy instances implementing `ProductSummary` at query-execution time — printing the proxy's runtime class name confirms it's a generated proxy, not a real `Product` instance cast to the interface.

### Level 2 — Intermediate

Use a class-based DTO projection via a JPQL constructor expression, producing genuinely instantiated objects rather than proxies.

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
public class ProjectionsLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private double price;
        protected Product() {}
        public Product(String name, double price) { this.name = name; this.price = price; }
    }

    // Class-based (DTO) projection -- a record with a constructor matching the query's SELECT columns.
    public record ProductPriceTag(String name, double price) {}

    public interface ProductRepository extends JpaRepository<Product, Long> {
        @Query("select new ProjectionsLevel2$ProductPriceTag(p.name, p.price) from Product p where p.price > :minPrice")
        List<ProductPriceTag> findPriceTags(double minPrice);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ProjectionsLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:proj2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", 9.99));
        repo.save(new Product("Gadget", 49.99));

        List<ProductPriceTag> tags = repo.findPriceTags(5.0);
        System.out.println("price tags: " + tags);
        System.out.println("actual runtime class = " + tags.get(0).getClass().getName());

        if (tags.size() != 2) throw new AssertionError("Expected 2 price tags");
        if (!tags.get(0).getClass().getSimpleName().equals("ProductPriceTag"))
            throw new AssertionError("Expected a REAL ProductPriceTag instance, not a proxy");
        System.out.println("Class-based DTO projection produced real, instantiated record objects -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ProjectionsLevel2.java`.

`select new ProjectionsLevel2$ProductPriceTag(p.name, p.price) from Product p where p.price > :minPrice` is a JPQL constructor expression — Hibernate calls `ProductPriceTag`'s constructor directly for each result row, producing genuine, fully-instantiated `ProductPriceTag` record instances (confirmed by the printed runtime class name), not proxies. This is the class-based counterpart to Level 1's interface-based approach — same narrowing goal, different underlying mechanism, requiring an explicit `@Query` since the constructor expression syntax isn't something method-name derivation can produce automatically.

### Level 3 — Advanced

Use a dynamic projection — one repository method, generic over the return type, letting the caller choose between the full entity and a narrowed projection at each call site.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class ProjectionsLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private double price;
        private String description;
        protected Product() {}
        public Product(String name, double price, String description) {
            this.name = name; this.price = price; this.description = description;
        }
        public String getName() { return name; }
        public double getPrice() { return price; }
        public String getDescription() { return description; }
    }

    public interface ProductSummary {
        String getName();
        double getPrice();
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        // DYNAMIC projection: the SAME method, caller decides the return shape via Class<T>.
        <T> List<T> findByPriceGreaterThan(double minPrice, Class<T> type);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ProjectionsLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:proj3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", 9.99, "A basic widget, does widget things."));
        repo.save(new Product("Gadget", 49.99, "A fancier gadget with extra features."));

        // Same method, TWO different call sites, TWO different return shapes.
        List<Product> fullEntities = repo.findByPriceGreaterThan(5.0, Product.class);
        List<ProductSummary> summaries = repo.findByPriceGreaterThan(5.0, ProductSummary.class);

        System.out.println("full entities include description: " + fullEntities.get(0).getDescription());
        System.out.println("summaries only expose name+price: " + summaries.get(0).getName() + "/" + summaries.get(0).getPrice());

        if (fullEntities.get(0).getDescription() == null)
            throw new AssertionError("Expected the full entity projection to include the description");
        if (summaries.size() != fullEntities.size())
            throw new AssertionError("Expected both projections to match the same number of rows");

        System.out.println("Dynamic projection let ONE method serve two different return shapes -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java ProjectionsLevel3.java`.

`<T> List<T> findByPriceGreaterThan(double minPrice, Class<T> type)` is a single derived-query method whose return element type is generic, resolved at each call site by the `Class<T> type` argument — passing `Product.class` returns full entities (including `description`); passing `ProductSummary.class` returns narrowed proxy instances exposing only `name` and `price`. Both calls execute the same underlying filter (`price > minPrice`), but Spring Data adapts the actual query and result mapping based on which target type was requested.

## 6. Walkthrough

Trace Level 3's two calls.

1. **`repo.findByPriceGreaterThan(5.0, Product.class)`**: Spring Data recognizes `Product.class` as the repository's own managed entity type — it executes the standard derived query, `SELECT p FROM Product p WHERE p.price > ?1`, selecting every column, and maps each row to a fully-populated `Product` entity, exactly as any non-projected derived query would.
2. **`repo.findByPriceGreaterThan(5.0, ProductSummary.class)`**: Spring Data recognizes `ProductSummary.class` as an interface projection type (not the managed entity type) — for JPA, it can optimize the generated query to select only the columns `ProductSummary`'s getters need (`name`, `price`), though the exact optimization depends on the Spring Data JPA version and configuration; at minimum, it wraps each result row in a generated proxy implementing `ProductSummary`.
3. **Both calls share the same filter logic** (`price > minPrice`) — the `Class<T> type` parameter changes only the *shape* of what's returned, not which rows match.
4. **`fullEntities.get(0).getDescription()`** succeeds and returns real data, since `Product` (the full entity) carries every field, including `description`.
5. **`summaries.get(0).getName()`/`getPrice()`** succeed too, but there is no `getDescription()` method on `ProductSummary` at all — attempting to call it wouldn't even compile, since the interface's declared method set is the entire contract available to code holding a `ProductSummary` reference.
6. **Verification**: the program confirms the full-entity call includes a genuine `description` value, and that both calls returned the same number of matching rows, proving the dynamic projection correctly varied only the result *shape*, not the underlying filtering logic.

```
 findByPriceGreaterThan(5.0, Product.class)
        |
        v
 SELECT p.* FROM product p WHERE price > 5.0   --> full Product entities

 findByPriceGreaterThan(5.0, ProductSummary.class)
        |
        v
 SELECT p.name, p.price FROM product p WHERE price > 5.0   --> ProductSummary proxies (narrower)

 SAME filter, SAME rows matched -- only the returned SHAPE differs
```

## 7. Gotchas & takeaways

> **Gotcha:** interface-based projection getter names must exactly match the underlying entity's property names (following JavaBean conventions) for Spring Data to wire them up automatically — a projection interface method like `getCustomerName()` won't automatically map to an entity property called `name` just because it seems semantically related; either rename the projection method to match, or use `@Value("#{target.name}")` (a SpEL "open" projection) to bridge a mismatched name explicitly.

- Interface-based projections are generated proxies, created at query-execution time, whose getter method names must align with the entity's actual property names — the simplest, most common projection style.
- Class-based (DTO/record) projections are genuine instantiated objects, produced via a JPQL `select new ...(...)` constructor expression in an explicit `@Query` — necessary since method-name derivation alone can't express a constructor call.
- Dynamic projections (`<T> List<T> methodName(..., Class<T> type)`) let a single repository method serve multiple return shapes, chosen per call site — useful when the same filtering logic needs to back both a full-detail view and a lightweight summary view.
- Projections exist specifically to avoid loading and transferring more data than a given use case needs — for JPA in particular, this can translate into real, measurable savings on wide entities or entities with expensive-to-load relationships, on top of the simpler ergonomic win of a narrower, purpose-built return type.
