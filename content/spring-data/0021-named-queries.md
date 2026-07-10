---
card: spring-data
gi: 21
slug: named-queries
title: "Named queries"
---

## 1. What it is

Named queries are queries declared *on the entity class itself*, via `@NamedQuery` (JPQL) or `@NamedNativeQuery` (SQL), identified by a string name following the convention `EntityName.methodName` — a repository method with no `@Query` annotation and no derivable name match will automatically be backed by a named query of that exact name, if one exists. This is the third leg of the `CREATE_IF_NOT_FOUND` lookup strategy from an earlier card: check for `@Query` first, then a named query, then fall back to derivation.

```java
@Entity
@NamedQuery(name = "Customer.findByEmailDomain",
    query = "select c from Customer c where c.email like concat('%@', :domain)")
public class Customer { ... }

public interface CustomerRepository extends JpaRepository<Customer, Long> {
    List<Customer> findByEmailDomain(@Param("domain") String domain); // matches the named query above
}
```

## 2. Why & when

Named queries predate Spring Data — they're a core JPA feature, useful because the JPA provider (Hibernate) validates and can pre-compile them once at startup, and because keeping a query's text on the entity class itself (rather than scattered across every repository interface that might use it) centralizes query definitions for a given entity in one place. Spring Data's contribution is purely the naming convention that lets a repository method be backed by one automatically, with no `@Query` annotation needed on the repository interface at all.

Reach for named queries specifically when:

- You're working in a codebase or team convention that prefers keeping query definitions on the entity class rather than scattered across repository interfaces — named queries centralize a given entity's queries in one file.
- You're integrating with existing JPA code (perhaps a codebase that predates Spring Data, or one shared with non-Spring JPA code) that already declares named queries this way, and want a Spring Data repository method to pick them up without duplicating the query text into an `@Query` annotation.
- You want JPA-level, provider-validated queries checked at `EntityManagerFactory` bootstrap time — named queries are parsed and validated by Hibernate as part of building the `EntityManagerFactory`, independent of and prior to Spring Data's own repository proxy generation.

In most modern Spring Data codebases, `@Query` directly on the repository method (from the previous card) is more common and more discoverable — named queries are reached for specifically when centralizing query definitions on the entity, or JPA-native tooling compatibility, is the priority.

## 3. Core concept

```
 @Entity
 @NamedQuery(name = "Customer.findByEmailDomain", query = "...")
 @NamedQuery(name = "Customer.countByActive", query = "...")
 public class Customer { ... }
        |
        v
 Hibernate parses and registers these under the EntityManagerFactory
 at APPLICATION STARTUP (not repository-proxy-creation time specifically,
 though both happen during overall context refresh)
        |
        v
 CustomerRepository method "findByEmailDomain(...)"
        |
        v
 Spring Data checks: is there a named query called "Customer.findByEmailDomain"?
   YES -- under CREATE_IF_NOT_FOUND (the default), this takes precedence
          over name-derivation, exactly like an @Query annotation would
```

The naming convention `EntityName.methodName` is what links a repository method to its named query — no annotation on the repository interface itself is needed once that convention is followed.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A NamedQuery declared on the entity is matched to a repository method by the EntityName.methodName naming convention">
  <rect x="10" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@NamedQuery on Customer entity</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">name = "Customer.findByEmailDomain"</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">registered at EMF bootstrap</text>

  <rect x="350" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CustomerRepository</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">findByEmailDomain(String domain)</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NO @Query annotation needed</text>

  <line x1="290" y1="52" x2="345" y2="52" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="45" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">matched by name</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The connection between a repository method and its named query is purely by string-name convention — no explicit reference is written on either side.

## 5. Runnable example

The scenario: a `Customer` entity with named queries, evolving from a basic named-query-backed finder, to a named native query, to a demonstration that a matching named query genuinely takes precedence over what name-derivation would otherwise produce for that same method name.

### Level 1 — Basic

Declare a `@NamedQuery` on `Customer` and a repository method whose name matches it, with no `@Query` annotation on the repository at all.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;

import java.util.List;

@SpringBootApplication
public class NamedQueryLevel1 {

    @Entity
    @NamedQuery(name = "Customer.findByEmailDomain",
        query = "select c from Customer c where c.email like concat('%@', :domain)")
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Customer() {}
        public Customer(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        // NO @Query here -- resolved via the named query "Customer.findByEmailDomain".
        List<Customer> findByEmailDomain(@Param("domain") String domain);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NamedQueryLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:namedq1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com"));
        repo.save(new Customer("grace@other.org"));
        repo.save(new Customer("katherine@example.com"));

        List<Customer> exampleDotCom = repo.findByEmailDomain("example.com");
        System.out.println("customers at example.com = " + exampleDotCom.stream().map(Customer::getEmail).toList());

        if (exampleDotCom.size() != 2) throw new AssertionError("Expected 2 customers at example.com");
        System.out.println("Named query resolved a repository method with zero @Query annotation -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java NamedQueryLevel1.java` on JDK 17+.

`@NamedQuery(name = "Customer.findByEmailDomain", ...)` is registered on the `Customer` entity itself, parsed and validated by Hibernate when the `EntityManagerFactory` is built. `CustomerRepository.findByEmailDomain(...)` has no `@Query` annotation and would not naturally derive from its own name either (`EmailDomain` isn't a real property on `Customer`) — Spring Data resolves it purely by matching the naming convention `Customer.findByEmailDomain` against the registered named queries.

### Level 2 — Intermediate

Use `@NamedNativeQuery` for a raw-SQL named query, paired with a repository method the same way.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;

@SpringBootApplication
public class NamedQueryLevel2 {

    @Entity
    @Table(name = "customer")
    @NamedNativeQuery(name = "Customer.findHighValue",
        query = "SELECT * FROM customer WHERE lifetime_value > ?1",
        resultClass = NamedQueryLevel2.Customer.class)
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        @Column(name = "lifetime_value")
        private BigDecimal lifetimeValue;
        protected Customer() {}
        public Customer(String email, BigDecimal lifetimeValue) { this.email = email; this.lifetimeValue = lifetimeValue; }
        public String getEmail() { return email; }
        public BigDecimal getLifetimeValue() { return lifetimeValue; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<Customer> findHighValue(BigDecimal threshold); // matches Customer.findHighValue
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NamedQueryLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:namedq2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com", new BigDecimal("500.00")));
        repo.save(new Customer("grace@example.com", new BigDecimal("5000.00")));

        List<Customer> highValue = repo.findHighValue(new BigDecimal("1000.00"));
        System.out.println("high-value customers = " + highValue.stream().map(Customer::getEmail).toList());

        if (highValue.size() != 1 || !highValue.get(0).getEmail().equals("grace@example.com"))
            throw new AssertionError("Expected only Grace to exceed the 1000.00 threshold");
        System.out.println("Named native query resolved via the same naming convention -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java NamedQueryLevel2.java`.

`@NamedNativeQuery` works the same way as `@NamedQuery`, just with raw SQL (`SELECT * FROM customer WHERE lifetime_value > ?1`) instead of JPQL, and an explicit `resultClass` telling Hibernate how to map the raw result set columns back into `Customer` entities. `findHighValue(BigDecimal threshold)` on the repository is matched against `Customer.findHighValue` by the same naming convention as Level 1.

### Level 3 — Advanced

Demonstrate precedence concretely: declare a named query whose logic *contradicts* what the method name would otherwise derive, proving the named query genuinely wins under the default `CREATE_IF_NOT_FOUND` strategy from the earlier query-lookup-strategies card.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;

import java.util.List;

@SpringBootApplication
public class NamedQueryLevel3 {

    @Entity
    @NamedQuery(name = "Customer.findByActive",
        // Deliberately the OPPOSITE of what "findByActive" would derive:
        // this named query ALWAYS returns INACTIVE customers, ignoring the argument.
        query = "select c from Customer c where c.active = false")
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        private boolean active;
        protected Customer() {}
        public Customer(String email, boolean active) { this.email = email; this.active = active; }
        public String getEmail() { return email; }
        public boolean isActive() { return active; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        // If this were resolved by DERIVATION, findByActive(true) would return ACTIVE customers.
        // Because a matching NAMED QUERY exists, it is used instead, and always returns inactive ones.
        List<Customer> findByActive(@Param("active") boolean active);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NamedQueryLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:namedq3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com", true));
        repo.save(new Customer("grace@example.com", false));

        // Calling with `true` -- under pure derivation this would return active customers.
        List<Customer> result = repo.findByActive(true);
        System.out.println("findByActive(true) actually returned: " + result.stream()
            .map(c -> c.getEmail() + " active=" + c.isActive()).toList());

        if (result.size() != 1 || result.get(0).isActive())
            throw new AssertionError("Expected the named query to override derivation and return the INACTIVE customer");
        System.out.println("Named query correctly took precedence over what derivation would have produced -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java NamedQueryLevel3.java`.

`findByActive(boolean active)`'s name alone would, under pure derivation, produce `WHERE active = ?1` — calling it with `true` should return active customers. But because a named query `Customer.findByActive` exists, `CREATE_IF_NOT_FOUND` finds it first and uses it exclusively — its JPQL deliberately always filters `WHERE active = false`, completely ignoring the method's `active` argument (there's no `:active` binding anywhere in the query text). The result — `findByActive(true)` returning the *inactive* customer — is the clearest possible proof that a matching named query wins over derivation, mirroring the same precedence the `@Query` annotation demonstrated in an earlier card.

## 6. Walkthrough

Trace Level 3's startup and call.

1. **`EntityManagerFactory` bootstrap**: as Hibernate builds the `EntityManagerFactory`, it scans `@Entity` classes for `@NamedQuery`/`@NamedNativeQuery` annotations, parses and validates each one's JPQL/SQL, and registers it in the `EntityManagerFactory`'s named-query registry under its declared `name` — here, `"Customer.findByActive"`.
2. **Repository proxy generation**: separately, Spring Data JPA builds the `CustomerRepository` proxy. For the `findByActive(boolean active)` method, under the default `CREATE_IF_NOT_FOUND` strategy, it first checks whether a declared query exists — no `@Query` annotation is present, so it next checks the `EntityManagerFactory`'s named-query registry for an entry matching `Customer.findByActive` (the convention: the managed entity's simple name, plus the method name).
3. **Match found**: `Customer.findByActive` exists in the registry, so Spring Data wires this repository method to execute that named query — the check for derivability never even happens, since a declared query (in the broad sense that includes named queries) was already found.
4. **Call**: `repo.findByActive(true)` invokes the named query, which is `select c from Customer c where c.active = false` — this JPQL string never references the method's `active` parameter at all (no `:active` binding exists in it), so the `true` argument is effectively ignored, and every call to this method, regardless of the argument passed, returns the same inactive-customers result.
5. **Execution**: H2 evaluates `WHERE active = false`, returning `grace@example.com` (the customer saved with `active = false`).
6. **Verification**: the program checks the returned customer's `isActive()` is indeed `false`, confirming the named query's fixed logic — not the method's argument, and not what name-derivation would have produced — determined the actual result.

```
 EntityManagerFactory bootstrap:
   @NamedQuery(name="Customer.findByActive", query="...active=false...") registered
        |
        v
 CustomerRepository proxy generation:
   findByActive(boolean) -- no @Query --> check named-query registry --> MATCH FOUND
        |
        v
 repo.findByActive(true) executes the NAMED QUERY, not a derived one
        |
        v
 result: the INACTIVE customer -- argument "true" was never even used
```

## 7. Gotchas & takeaways

> **Gotcha:** the naming-convention link between a repository method and a named query is purely string-based and entirely silent — there is no compiler check, no IDE warning by default, and no visible annotation on the repository method connecting it to its named query. A typo in either the `@NamedQuery`'s `name` attribute or a coincidental repository method name matching an *unrelated* named query can produce confusing, hard-to-trace behavior, exactly as demonstrated deliberately in Level 3. When possible, prefer an explicit `@Query` annotation directly on the repository method — it keeps the query text visible right where it's used, rather than requiring a separate lookup on the entity class to understand what a method actually does.

- Named queries are declared on the `@Entity` class via `@NamedQuery` (JPQL) or `@NamedNativeQuery` (SQL), and matched to a repository method purely by the naming convention `EntityName.methodName` — no annotation is needed on the repository method itself.
- Under the default `CREATE_IF_NOT_FOUND` lookup strategy, a matching named query takes precedence over name-derivation for that method, exactly like an `@Query` annotation would — this precedence is silent and worth knowing about when a method's behavior doesn't match what its name would suggest.
- Named queries are validated by Hibernate at `EntityManagerFactory` bootstrap time, independent of Spring Data's own repository-proxy generation — a broken named query fails startup just as reliably as any other query-resolution problem covered in this section.
- In most modern Spring Data code, `@Query` directly on the repository interface (from the previous card) is preferred for its visibility and locality — named queries remain most useful for centralizing an entity's query definitions in one place, or for compatibility with existing, non-Spring-Data JPA code.
