---
card: spring-data
gi: 1
slug: spring-data-mission-umbrella-overview
title: "Spring Data mission & umbrella overview"
---

## 1. What it is

Spring Data is an umbrella project — not one library, but a family of them (Spring Data JPA, Spring Data MongoDB, Spring Data Redis, Spring Data Elasticsearch, Spring Data Cassandra, and more) that all share one mission: let application code express data access as an interface with method names like `findByLastName`, and have the actual query — SQL, a Mongo document filter, a Redis key lookup — generated automatically, regardless of which underlying store that interface talks to.

```java
public interface CustomerRepository extends CrudRepository<Customer, Long> {
    List<Customer> findByLastName(String lastName); // no implementation -- Spring Data writes it
}
```

## 2. Why & when

Every data-access layer, regardless of the underlying store, ends up needing the same handful of operations — save an entity, find it by ID, find it by some other field, delete it, page through a large result set — and hand-writing that boilerplate (a DAO class with a `Connection`, a `PreparedStatement`, manual `ResultSet` mapping) repeats itself across every entity in an application and again across every project that uses the same store. Spring Data's mission is to eliminate exactly that repetition: define an interface describing *what* data operations you need, and let the framework generate the *how*.

Reach for a Spring Data module specifically when:

- You're building a Spring application (Boot or plain Spring Framework) that talks to a relational database, a document store, a key-value store, a graph database, or a search index, and want the standard CRUD and query operations without hand-writing them.
- You want consistent data-access idioms across an application that might use more than one store — a relational database for orders and a document store for product catalogs, for instance — since `Repository<T, ID>`, `CrudRepository`, and the query-derivation naming convention (covered later in this section) work almost identically across every Spring Data module.
- You need custom queries beyond basic CRUD — Spring Data's query-derivation-from-method-names mechanism (covered in a later card) and its `@Query` annotation cover the vast majority of real-world query needs without dropping to raw SQL or store-specific query APIs.

## 3. Core concept

```
                    Spring Data Commons
              (shared abstractions: Repository<T,ID>,
               CrudRepository, query derivation, Pageable, Sort)
                            |
        -------------------+-------------------+------------------
        |                  |                   |                 |
        v                  v                   v                 v
  Spring Data JPA   Spring Data MongoDB   Spring Data Redis   Spring Data ...
  (relational DBs)   (MongoDB documents)   (key-value store)   (Cassandra, Neo4j,
                                                                 Elasticsearch, etc.)
        |                  |                   |                 |
        v                  v                   v                 v
     JpaRepository     MongoRepository    RedisRepository     store-specific
     (adds JPA-        (adds Mongo-        (adds Redis-        repository
      specific ops)     specific ops)       specific ops)        interfaces
```

Every store-specific module implements the same Commons abstractions, then layers on store-specific extensions where the underlying technology needs them.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Data Commons provides shared abstractions that every store-specific module implements and extends">
  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data Commons</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Repository, CrudRepository, query derivation</text>

  <rect x="20" y="130" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data JPA</text>
  <text x="95" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">relational</text>

  <rect x="245" y="130" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data MongoDB</text>
  <text x="320" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">documents</text>

  <rect x="470" y="130" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data Redis</text>
  <text x="545" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">key-value</text>

  <line x1="280" y1="70" x2="120" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="320" y1="70" x2="320" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="360" y1="70" x2="520" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One shared abstraction layer, many store-specific implementations underneath.

## 5. Runnable example

Since illustrating "one mission across many stores" concretely needs a real store, the example uses Spring Data JPA against an in-memory H2 database — the most common entry point into Spring Data. The scenario: a `Customer` repository, evolving from a bare `CrudRepository` performing basic saves and lookups, to a derived-name query, to a full setup mixing derived queries with pagination — a preview of the mechanisms this whole section covers in depth.

### Level 1 — Basic

Define a minimal JPA entity and a `CrudRepository` extension with zero method implementations, and confirm `save`/`findById` work out of the box.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

@SpringBootApplication
public class SpringDataMissionLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;

        protected Customer() {}
        public Customer(String firstName, String lastName) {
            this.firstName = firstName; this.lastName = lastName;
        }
        public Long getId() { return id; }
        public String getFirstName() { return firstName; }
        public String getLastName() { return lastName; }
        @Override public String toString() { return firstName + " " + lastName; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpringDataMissionLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:testdb",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);

        Customer saved = repo.save(new Customer("Ada", "Lovelace"));
        System.out.println("saved with generated id = " + saved.getId());

        Optional<Customer> found = repo.findById(saved.getId());
        System.out.println("found = " + found.orElse(null));

        if (found.isEmpty() || !found.get().getLastName().equals("Lovelace"))
            throw new AssertionError("Expected to find the saved customer by generated id");
        System.out.println("CrudRepository save/findById worked with zero implementation code -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java SpringDataMissionLevel1.java` on JDK 17+ (Spring Boot's single-file launcher support) or run inside a minimal Maven/Gradle project with those two dependencies.

`CustomerRepository extends JpaRepository<Customer, Long>` declares no methods at all, yet `repo.save(...)` and `repo.findById(...)` both work — Spring Data generates a real implementation class at startup (a JDK dynamic proxy backed by `SimpleJpaRepository`) that translates these calls into actual JPA `EntityManager` operations, entirely from the interface declaration.

### Level 2 — Intermediate

Add a derived-name query method — `findByLastName` — with no query written anywhere, previewing the query-derivation mechanism covered in depth later in this section.

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
public class SpringDataMissionLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;

        protected Customer() {}
        public Customer(String firstName, String lastName) {
            this.firstName = firstName; this.lastName = lastName;
        }
        public String getFirstName() { return firstName; }
        public String getLastName() { return lastName; }
        @Override public String toString() { return firstName + " " + lastName; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<Customer> findByLastName(String lastName);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpringDataMissionLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:testdb2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Lovelace"));
        repo.save(new Customer("Grace", "Hopper"));
        repo.save(new Customer("Katherine", "Lovelace")); // shares a last name with Ada

        List<Customer> lovelaces = repo.findByLastName("Lovelace");
        System.out.println("Lovelaces found = " + lovelaces);

        if (lovelaces.size() != 2)
            throw new AssertionError("Expected exactly 2 customers named Lovelace, found " + lovelaces.size());
        System.out.println("Derived query findByLastName generated correct SQL from the method name -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java SpringDataMissionLevel2.java`.

`findByLastName(String lastName)` has no method body and no `@Query` annotation — Spring Data parses the method name at startup (`findBy` + `LastName`), matches `LastName` against the `Customer` entity's `lastName` property, and builds a JPQL query (`select c from Customer c where c.lastName = ?1`) automatically. Two customers share the last name `"Lovelace"`, so the query correctly returns both.

### Level 3 — Advanced

Combine derived queries with pagination via `PagingAndSortingRepository`'s inherited `findAll(Pageable)`, and add a custom `@Query` for a case not expressible by method-name derivation alone — the production-flavored combination of "let Spring Data write the easy queries, write the hard ones by hand."

```java
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
import org.springframework.data.jpa.repository.Query;

import java.util.List;

@SpringBootApplication
public class SpringDataMissionLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;
        private int loyaltyPoints;

        protected Customer() {}
        public Customer(String firstName, String lastName, int loyaltyPoints) {
            this.firstName = firstName; this.lastName = lastName; this.loyaltyPoints = loyaltyPoints;
        }
        public String getFirstName() { return firstName; }
        public String getLastName() { return lastName; }
        public int getLoyaltyPoints() { return loyaltyPoints; }
        @Override public String toString() { return firstName + " " + lastName + " (" + loyaltyPoints + "pts)"; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<Customer> findByLastName(String lastName);

        @Query("select c from Customer c where c.loyaltyPoints >= :threshold order by c.loyaltyPoints desc")
        List<Customer> findVips(int threshold);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpringDataMissionLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:testdb3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        for (int i = 1; i <= 25; i++) {
            repo.save(new Customer("Customer" + i, "LastName" + (i % 3), i * 10));
        }

        Page<Customer> firstPage = repo.findAll(PageRequest.of(0, 10, Sort.by("loyaltyPoints").descending()));
        System.out.println("page 1 of " + firstPage.getTotalPages() + ", total elements = " + firstPage.getTotalElements());
        System.out.println("top of page 1 = " + firstPage.getContent().get(0));

        List<Customer> vips = repo.findVips(200);
        System.out.println("VIPs (>=200 points) = " + vips.size());

        if (firstPage.getTotalElements() != 25) throw new AssertionError("Expected 25 total customers");
        if (firstPage.getContent().get(0).getLoyaltyPoints() != 250) throw new AssertionError("Expected highest-points customer first");
        if (vips.size() != 6) throw new AssertionError("Expected 6 customers with >=200 points (210..250 by 10s), got " + vips.size());

        System.out.println("Pagination + derived query + custom @Query all worked together -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java SpringDataMissionLevel3.java`.

`repo.findAll(PageRequest.of(0, 10, Sort.by("loyaltyPoints").descending()))` uses `PagingAndSortingRepository`'s inherited method (covered in a later card) to fetch page 1 of 10, sorted by points descending — no query written by hand. `findVips` needs a threshold comparison and custom ordering that method-name derivation can't cleanly express, so it uses `@Query` with a JPQL string and a named parameter (`:threshold`) instead — the same repository interface freely mixes both approaches, choosing whichever fits each specific query.

## 6. Walkthrough

Trace Level 3's startup and the `findVips` call specifically, since it shows Spring Data's layered abstraction most clearly.

1. **Application startup**: `SpringApplication.run(...)` boots a Spring context. Spring Data JPA's auto-configuration scans for interfaces extending `Repository` (the root interface, covered in the next card) — it finds `CustomerRepository`.
2. **Proxy generation**: for `CustomerRepository`, Spring Data creates a runtime proxy implementing the interface. Standard methods (`save`, `findAll`, `findById`) are backed by `SimpleJpaRepository`, the shared JPA implementation of the Commons `CrudRepository`/`PagingAndSortingRepository` contracts.
3. **Custom method resolution**: for `findByLastName`, Spring Data's `PartTree` query-derivation parser breaks the method name into `FindBy` + `LastName`, matches `LastName` against the `Customer` entity metadata, and pre-builds a JPQL query template at startup — not on every call, but once, when the proxy is created.
4. **`@Query` method resolution**: for `findVips`, Spring Data instead uses the literal JPQL string from the `@Query` annotation directly, substituting `:threshold` with the method's `threshold` parameter at call time.
5. **Data seeding**: `main` saves 25 customers with varying `loyaltyPoints` (10, 20, 30, ..., 250), each insert going through the proxy's `save` method into the real H2 database via Hibernate.
6. **`findAll(PageRequest...)`** call: the proxy translates the `Pageable` into a JPQL query with `ORDER BY loyaltyPoints DESC` plus a `LIMIT`/`OFFSET` equivalent for page 0, size 10 — H2 executes it and returns rows 1–10 by descending points, wrapped in a `Page<Customer>` that also carries the total count (25) via a second `COUNT` query Spring Data issues automatically.
7. **`findVips(200)`** call: the proxy substitutes `200` for `:threshold` in the stored JPQL string, executes `select c from Customer c where c.loyaltyPoints >= 200 order by c.loyaltyPoints desc`, and returns the 6 matching customers (points 210 through 250, in steps of 10).
8. **Verification**: the program checks the total element count, confirms the highest-points customer appears first on page 1, and confirms exactly 6 VIPs were found, printing `PASS` only if every check holds.

```
 CustomerRepository (interface, zero implementation code)
        |
        v
 Spring Data proxy, generated at startup
        |
        +-- save/findAll/findById  --> SimpleJpaRepository (shared JPA implementation)
        +-- findByLastName(...)    --> PartTree-derived JPQL, built from the method name
        +-- findVips(...)          --> literal JPQL from @Query, params substituted at call time
        |
        v
 real SQL sent to H2 via Hibernate's EntityManager
```

## 7. Gotchas & takeaways

> **Gotcha:** the mission of "write an interface, get an implementation" is genuinely store-agnostic at the Commons level (`Repository<T,ID>`, `CrudRepository`, query derivation), but the actual query language and capabilities differ by store — a derived-name query that works against Spring Data JPA (translated to JPQL/SQL) and one that works against Spring Data MongoDB (translated to a Mongo query document) look identical in the Java interface, but the underlying store determines what's actually expressible; not every JPA capability has a MongoDB equivalent, and vice versa.

- Every Spring Data module (JPA, MongoDB, Redis, and the rest) builds on the same Commons foundation — learning `Repository<T,ID>`, `CrudRepository`, and query derivation once transfers directly to every store-specific module this guide covers.
- A repository interface needs zero implementation code for standard CRUD and derived queries — Spring Data generates a working implementation entirely from the interface declaration and, for derived methods, the method's name.
- `@Query` remains available for anything method-name derivation can't cleanly express — the two approaches coexist freely in the same repository interface, as shown by `CustomerRepository` in Level 3.
- The rest of this section works through each of these mechanisms — the base interfaces, defining repositories, null handling, reactive return types, and query derivation itself — in the depth this overview only previews.
