---
card: spring-data
gi: 3
slug: repository-t-id-base-interface
title: "Repository<T,ID> base interface"
---

## 1. What it is

`Repository<T, ID>` is the actual root Java interface at the top of every Spring Data repository hierarchy — a generic, empty interface with two type parameters: `T`, the entity/domain type this repository manages, and `ID`, the type of that entity's identifier. It declares no methods whatsoever; its entire purpose is to be a type-safe, generically-parameterized marker that Spring Data's classpath scanning recognizes as "generate a repository proxy for this."

```java
package org.springframework.data.repository;

public interface Repository<T, ID> {
    // deliberately empty -- a pure marker interface
}
```

## 2. Why & when

Every richer Spring Data interface — `CrudRepository<T, ID>`, `PagingAndSortingRepository<T, ID>`, and every store-specific interface like `JpaRepository<T, ID>` — ultimately extends `Repository<T, ID>`. Understanding this base interface specifically (rather than just using `CrudRepository` and never thinking about what's underneath) matters because it clarifies exactly what Spring Data's scanning mechanism looks for, and it's the interface to extend directly when you want a fully custom, hand-picked method set rather than inheriting a large predefined contract.

Reach for `Repository<T, ID>` directly (rather than `CrudRepository` or similar) specifically when:

- You want precise control over exactly which operations a given repository interface exposes — as the previous card demonstrated with a read-only repository — and don't want to inherit (and then have to hide or deprecate) methods you don't want callers to have.
- You're building a repository around a projection or a read-model type that doesn't need full CRUD, just a handful of specific finder methods.
- You're documenting or reasoning about the Spring Data hierarchy itself and want to be precise about what's guaranteed by the framework (the two generic type parameters, recognized by scanning) versus what's added by a richer interface (specific method signatures).

For the overwhelming majority of everyday repositories, extending `CrudRepository` or a store-specific interface like `JpaRepository` (covered in upcoming cards) is simpler and more common — `Repository<T, ID>` itself is reached for specifically when the default full-CRUD surface isn't what you want.

## 3. Core concept

```
 public interface Repository<T, ID> {}
                    |
        T = entity/domain type (e.g. Customer)
        ID = type of that entity's identifier (e.g. Long)

 Spring Data's scanning infrastructure looks for:
   "any interface, directly or transitively extending Repository<?, ?>,
    found under the configured base package(s)"
                    |
                    v
        for each one found, generate a proxy bean
                    |
        the proxy's behavior comes ENTIRELY from:
          - declared methods matching CrudRepository-style base signatures (if extended)
          - declared methods Spring Data can derive a query for (by name)
          - declared methods annotated with @Query
          - custom implementation classes (covered in a later card)
```

`Repository<T, ID>` supplies zero behavior on its own — it is purely the signal that makes an interface eligible for Spring Data's proxy generation.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repository is the root of the hierarchy; richer interfaces like CrudRepository and JpaRepository extend it, adding declared methods">
  <rect x="230" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Repository&lt;T, ID&gt;</text>

  <rect x="90" y="110" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="180" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CrudRepository&lt;T, ID&gt;</text>

  <rect x="370" y="110" width="230" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">your custom Repository&lt;T,ID&gt; extension</text>

  <rect x="90" y="175" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="180" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JpaRepository, MongoRepository, ...</text>

  <line x1="290" y1="65" x2="200" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="330" y1="65" x2="460" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="180" y1="155" x2="180" y2="170" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Everything richer in Spring Data traces back to this one empty, generically-typed root interface.

## 5. Runnable example

The scenario: prove `Repository<T, ID>`'s two type parameters are what Spring Data uses to know the entity type and ID type, by building a repository whose declared methods deliberately mismatch what `CrudRepository` would offer — then confirm that reflection over the interface hierarchy shows exactly this structure.

### Level 1 — Basic

Extend `Repository<Product, String>` directly (a `String` ID, not the more common `Long`) with one custom method, and confirm the generated proxy correctly infers both type parameters.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.Repository;

import java.util.Optional;

@SpringBootApplication
public class RepositoryBaseLevel1 {

    @Entity
    public static class Product {
        @Id
        private String sku; // String ID, not the more common generated Long
        private String name;
        protected Product() {}
        public Product(String sku, String name) { this.sku = sku; this.name = name; }
        public String getSku() { return sku; }
        public String getName() { return name; }
    }

    public interface ProductRepository extends Repository<Product, String> {
        Product save(Product product);
        Optional<Product> findById(String sku);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(RepositoryBaseLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:repobase1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("SKU-001", "Widget"));

        Optional<Product> found = repo.findById("SKU-001");
        System.out.println("found = " + found.map(Product::getName).orElse("MISSING"));

        if (found.isEmpty() || !found.get().getName().equals("Widget"))
            throw new AssertionError("Expected to find the product by its String SKU");
        System.out.println("Repository<Product, String> correctly used a String identifier -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java RepositoryBaseLevel1.java` on JDK 17+.

`Repository<Product, String>`'s second type parameter, `String`, tells Spring Data the identifier type is a `String` (the `sku` field), not the more commonly seen generated `Long`. The generated proxy's `findById(String sku)` correctly uses `String` equality against the `sku` primary key column — the type parameters aren't just documentation, they drive the actual generated query's parameter type.

### Level 2 — Intermediate

Inspect the interface hierarchy reflectively to show `CrudRepository` and `JpaRepository` genuinely extend `Repository<T, ID>` transitively, making the "everything traces back to this root" claim concrete rather than asserted.

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.CrudRepository;
import org.springframework.data.repository.Repository;

import java.util.ArrayList;
import java.util.List;

public class RepositoryBaseLevel2 {

    static boolean isAssignableTransitively(Class<?> subtype, Class<?> supertype) {
        return supertype.isAssignableFrom(subtype);
    }

    static List<Class<?>> collectInterfaceChain(Class<?> start, Class<?> stopAt) {
        List<Class<?>> chain = new ArrayList<>();
        collectRecursive(start, stopAt, chain);
        return chain;
    }

    static void collectRecursive(Class<?> current, Class<?> stopAt, List<Class<?>> chain) {
        if (chain.contains(current)) return;
        chain.add(current);
        if (current.equals(stopAt)) return;
        for (Class<?> iface : current.getInterfaces()) {
            if (Repository.class.isAssignableFrom(iface)) {
                collectRecursive(iface, stopAt, chain);
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("Is CrudRepository a Repository? " + isAssignableTransitively(CrudRepository.class, Repository.class));
        System.out.println("Is JpaRepository a Repository?  " + isAssignableTransitively(JpaRepository.class, Repository.class));
        System.out.println("Is JpaRepository a CrudRepository? " + isAssignableTransitively(JpaRepository.class, CrudRepository.class));

        List<Class<?>> chain = collectInterfaceChain(JpaRepository.class, Repository.class);
        System.out.println("interface chain from JpaRepository up to Repository: ");
        chain.forEach(c -> System.out.println("  " + c.getSimpleName()));

        if (!isAssignableTransitively(CrudRepository.class, Repository.class))
            throw new AssertionError("CrudRepository must extend Repository");
        if (!isAssignableTransitively(JpaRepository.class, Repository.class))
            throw new AssertionError("JpaRepository must transitively extend Repository");
        if (!chain.contains(Repository.class))
            throw new AssertionError("Expected the chain to reach the Repository root");

        System.out.println("Confirmed the full hierarchy traces back to Repository<T,ID> -- PASS");
    }
}
```

How to run: put `spring-data-commons` and `spring-data-jpa` on the classpath, then `java RepositoryBaseLevel2.java` on JDK 17+. No database needed — this is pure reflection over interface types.

`Repository.class.isAssignableFrom(JpaRepository.class)` returning `true` proves `JpaRepository` genuinely implements `Repository` in the Java type system, not merely "behaves similarly" — Java interface inheritance is transitive, so `JpaRepository extends PagingAndSortingRepository extends CrudRepository extends Repository` (or a similar chain, depending on the exact Spring Data version) is verifiable directly through the JDK's own reflection API, without needing any Spring context at all.

### Level 3 — Advanced

Build a custom base interface that extends `Repository<T, ID>` directly with a hand-picked, reusable method set — the pattern real codebases use to define an organization-wide "base repository" with exactly the operations they want every entity's repository to have, no more and no less.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.NoRepositoryBean;
import org.springframework.data.repository.Repository;

import java.util.Optional;

@SpringBootApplication
public class RepositoryBaseLevel3 {

    // A custom organization-wide base contract: only save + findById + existsById,
    // deliberately omitting delete and findAll to keep every entity's repository minimal.
    @NoRepositoryBean
    public interface MinimalRepository<T, ID> extends Repository<T, ID> {
        T save(T entity);
        Optional<T> findById(ID id);
        boolean existsById(ID id);
    }

    @Entity
    public static class Invoice {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double amount;
        protected Invoice() {}
        public Invoice(double amount) { this.amount = amount; }
        public Long getId() { return id; }
        public double getAmount() { return amount; }
    }

    public interface InvoiceRepository extends MinimalRepository<Invoice, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(RepositoryBaseLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:repobase3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        InvoiceRepository repo = ctx.getBean(InvoiceRepository.class);
        Invoice saved = repo.save(new Invoice(499.99));

        boolean exists = repo.existsById(saved.getId());
        Optional<Invoice> found = repo.findById(saved.getId());

        System.out.println("exists = " + exists + ", found amount = " + found.map(Invoice::getAmount).orElse(null));

        if (!exists) throw new AssertionError("Expected existsById to return true for a saved invoice");
        if (found.isEmpty() || found.get().getAmount() != 499.99)
            throw new AssertionError("Expected findById to return the saved invoice");

        System.out.println("Custom @NoRepositoryBean base interface propagated to InvoiceRepository -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java RepositoryBaseLevel3.java`.

`MinimalRepository<T, ID>` is a reusable, organization-defined base interface extending `Repository<T, ID>` directly, with exactly three methods — deliberately no `delete`, no `findAll`. `@NoRepositoryBean` (covered fully in a later card) tells Spring Data *not* to generate a proxy for `MinimalRepository` itself, only for concrete interfaces that extend it, like `InvoiceRepository` — without it, Spring Data would try (and fail, since `T`/`ID` aren't bound to real types yet) to create a bean for the generic template interface itself.

## 6. Walkthrough

Trace Level 3's setup and first call.

1. **Scanning phase**: Spring Data JPA's component scan finds `InvoiceRepository`. It also encounters `MinimalRepository`, but because `MinimalRepository` is annotated `@NoRepositoryBean`, Spring Data skips generating a proxy for it directly — it's a template, not a concrete repository.
2. **Type resolution**: for `InvoiceRepository extends MinimalRepository<Invoice, Long>`, Spring Data resolves the generic type parameters up the hierarchy — `T = Invoice`, `ID = Long` — the same resolution process used for any `Repository<T, ID>` extension, regardless of how many custom interfaces sit in between.
3. **Proxy generation**: a single proxy bean is created for `InvoiceRepository`, implementing the three methods declared on `MinimalRepository` (`save`, `findById`, `existsById`) using generic JPA infrastructure — the same `SimpleJpaRepository`-style backing used for `CrudRepository`, just exposing a narrower method surface because that's all the interface chain declares.
4. **`repo.save(new Invoice(499.99))`**: the proxy's `save` implementation persists a new `Invoice` row via the `EntityManager`, returning the entity with its generated `id` populated.
5. **`repo.existsById(saved.getId())`**: the proxy's `existsById` implementation issues an efficient existence check (typically a `SELECT COUNT` or similar, rather than fetching the full row) against the invoice table using the generated id.
6. **`repo.findById(saved.getId())`**: the proxy's `findById` implementation fetches the full row and maps it back into an `Invoice` instance wrapped in `Optional`.
7. **Verification**: the program checks both `exists` is `true` and `found` contains the correct amount, confirming the custom base interface's narrow, hand-picked contract works end-to-end exactly like a normal Spring Data repository, just without the methods it deliberately excludes.

```
 Repository<T, ID>                        (root, empty)
        ^
        |
 MinimalRepository<T, ID>  @NoRepositoryBean   (custom base: save, findById, existsById only)
        ^
        |
 InvoiceRepository extends MinimalRepository<Invoice, Long>
        |
        v
   ONE generated proxy bean, exposing exactly 3 methods
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting `@NoRepositoryBean` on a custom intermediate interface like `MinimalRepository<T, ID>` causes Spring Data to attempt generating a proxy bean for it too, at startup — since its generic type parameters `T`/`ID` aren't bound to concrete types, this typically fails with a confusing startup error about being unable to resolve the domain type. Any custom interface meant purely as a reusable template, not a concrete repository, needs this annotation.

- `Repository<T, ID>` is the true root of every Spring Data repository interface — its two type parameters (entity type, ID type) are what the framework's scanning and proxy-generation infrastructure resolves for every interface in the hierarchy, no matter how many custom interfaces sit in between.
- Java's own reflection API (`Class.isAssignableFrom`) is enough to verify the hierarchy directly — no Spring context is needed to confirm that `CrudRepository` and `JpaRepository` genuinely extend `Repository`.
- Defining a custom, organization-wide base interface extending `Repository<T, ID>` (marked `@NoRepositoryBean`) is the standard pattern for enforcing a consistent, restricted method contract across many entities' repositories.
- The next cards in this section cover the specific richer interfaces Spring Data itself provides — `CrudRepository`, `ListCrudRepository`, `PagingAndSortingRepository` — as the more commonly used alternatives to defining a custom base interface from scratch.
