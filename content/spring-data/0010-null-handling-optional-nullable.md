---
card: spring-data
gi: 10
slug: null-handling-optional-nullable
title: "Null handling (Optional, @Nullable)"
---

## 1. What it is

Spring Data repository methods communicate whether a result can be absent through their return type and parameter annotations, not through undocumented convention: a single-result finder method returning `Optional<T>` (like `CrudRepository.findById`) makes "might not exist" explicit and forces callers to handle it; a method returning `T` directly is a promise the result will never be null (and Spring Data enforces this — see the runnable example); and `@Nullable` on a parameter documents that passing `null` for that argument is a legitimate, handled case rather than a bug.

```java
Optional<Customer> findById(Long id);          // may be absent -- caller must handle it
Customer getReferenceById(Long id);             // never null -- throws instead, if invalid
List<Customer> findByNickname(@Nullable String nickname); // null nickname is valid input
```

## 2. Why & when

"Does this method return null, or throw, or return an empty collection, when nothing matches?" is exactly the kind of question that shouldn't require reading documentation or, worse, guessing from experience — Spring Data's null-handling conventions make the answer visible directly in the method signature. This matters because getting it wrong (assuming `findById` never returns empty, or failing to handle an `Optional`) is one of the most common sources of `NullPointerException`s in real Spring Data code, entirely preventable by respecting what the type signature already promises.

Understanding this matters specifically when:

- You're writing or reviewing a repository interface and need to decide the return type for a single-result finder — `Optional<T>` when absence is a normal, expected outcome; a bare `T` only when absence should be treated as exceptional (or is genuinely impossible, as with `getReferenceById`).
- You're calling a Spring Data repository method and need to know, without checking documentation, whether to expect `null`, an empty `Optional`, or an exception for a no-match case — the return type itself answers this.
- You're deciding whether a query method's parameter can legitimately be `null` — Spring Data enforces `@NonNull`-by-default on repository parameters (via Spring's null-safety annotations), meaning passing `null` where `@Nullable` isn't declared throws immediately, before any query even runs.

## 3. Core concept

```
 Return type conventions for single-result queries:

   Optional<T> findByX(...)     -- explicit: "may not exist," caller must unwrap
   T findByX(...)                -- promise: "will not be null" -- throws
                                     EmptyResultDataAccessException (or similar) if
                                     nothing matches, rather than silently returning null

 Collection-returning queries NEVER return null:
   List<T> findByX(...)         -- returns an EMPTY list if nothing matches, never null

 Parameter null-safety (via Spring's org.springframework.lang annotations):
   findByX(String x)             -- x is NON-NULL by default; passing null throws
                                     IllegalArgumentException before the query runs
   findByX(@Nullable String x)   -- x may legitimately be null; the generated query
                                     handles it (typically translating to "IS NULL")
```

The rule of thumb: `Optional` and `@Nullable` both mean "absence is expected and handled here" — their absence means "this can never legitimately be null, and Spring Data will enforce that."

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Different return types communicate different null-handling contracts for single-result queries">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Optional&lt;Customer&gt;</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">may be empty -- caller unwraps</text>

  <rect x="230" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Customer (bare)</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">never null -- throws instead</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;Customer&gt;</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">never null -- empty list instead</text>
</svg>

Three different single/collection-result conventions, each communicating its "nothing found" behavior directly through the type.

## 5. Runnable example

The scenario: a `Customer` lookup repository, evolving from `Optional`-based safe lookups, to proving a bare-`T`-returning method throws rather than returning null, to combining `@Nullable` parameter handling with both conventions in one repository.

### Level 1 — Basic

Use `findById` (returning `Optional<Customer>`) for both a hit and a miss, showing the caller-side handling `Optional` requires and enables.

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
public class NullHandlingLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NullHandlingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:nullh1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Ada"));

        Optional<Customer> hit = repo.findById(saved.getId());
        Optional<Customer> miss = repo.findById(999_999L);

        String hitResult = hit.map(Customer::getName).orElse("NOT FOUND");
        String missResult = miss.map(Customer::getName).orElse("NOT FOUND");

        System.out.println("hit result = " + hitResult);
        System.out.println("miss result = " + missResult);

        if (!hitResult.equals("Ada")) throw new AssertionError("Expected to find Ada");
        if (!missResult.equals("NOT FOUND")) throw new AssertionError("Expected an empty Optional for a nonexistent id");
        System.out.println("Optional<Customer> correctly represented both hit and miss without any null -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java NullHandlingLevel1.java` on JDK 17+.

`repo.findById(...)` never returns `null` itself — it always returns an `Optional<Customer>`, either populated (`hit`) or empty (`miss`). `.map(...).orElse(...)` is the idiomatic way to handle both cases without ever risking a `NullPointerException` on the result — the type signature makes this handling mandatory by construction, since there's no `Customer` to accidentally dereference directly.

### Level 2 — Intermediate

Declare a custom finder method returning a bare `Customer` (not `Optional`) and confirm Spring Data throws rather than returning `null` when nothing matches — proving the "never null" promise is enforced, not just a convention.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class NullHandlingLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Customer() {}
        public Customer(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        // A BARE return type -- the "promise" convention: never null, throws if absent.
        Customer findByEmail(String email);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NullHandlingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:nullh2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com"));

        Customer found = repo.findByEmail("ada@example.com");
        System.out.println("found (bare return type) = " + found.getEmail());

        boolean threwOnMiss = false;
        try {
            Customer missing = repo.findByEmail("nobody@example.com");
            System.out.println("this line should not print -- got: " + missing);
        } catch (EmptyResultDataAccessException expected) {
            threwOnMiss = true;
            System.out.println("threw as expected: " + expected.getClass().getSimpleName());
        }

        if (found == null) throw new AssertionError("Expected a real Customer for an existing email");
        if (!threwOnMiss) throw new AssertionError("Expected findByEmail to throw, not return null, for a nonexistent email");
        System.out.println("Bare return type never silently returned null -- it threw instead -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java NullHandlingLevel2.java`.

`findByEmail(String email)` returns a bare `Customer`, not `Optional<Customer>` — this is Spring Data's "promise" convention. When the query matches, it returns the entity directly, no unwrapping needed. When nothing matches, it does *not* return `null` (which would silently defeat the "never null" promise); it throws `EmptyResultDataAccessException` instead — forcing the absence to be handled as an explicit exceptional case (via a `try`/`catch`) rather than risking an unchecked `NullPointerException` somewhere downstream if a caller forgot to null-check.

### Level 3 — Advanced

Combine `@Nullable` on a query parameter with both single-result conventions, showing how a `null` argument is treated as legitimate input (translating to `IS NULL` in the generated query) rather than triggering the parameter-validation `IllegalArgumentException` that an undeclared, implicitly non-null parameter would.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.lang.Nullable;

import java.util.List;

@SpringBootApplication
public class NullHandlingLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String referredBy; // nullable column: null means "no referrer"
        protected Customer() {}
        public Customer(String name, String referredBy) { this.name = name; this.referredBy = referredBy; }
        public String getName() { return name; }
        public String getReferredBy() { return referredBy; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        // @Nullable here means: passing null is LEGITIMATE, not a bug -- the generated
        // query correctly translates it to "referredBy IS NULL".
        List<Customer> findByReferredBy(@Nullable String referredBy);

        // No @Nullable here -- passing null throws IllegalArgumentException BEFORE any query runs.
        List<Customer> findByName(String name);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(NullHandlingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:nullh3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Grace"));
        repo.save(new Customer("Katherine", null));   // no referrer
        repo.save(new Customer("Grace", null));       // no referrer

        List<Customer> noReferrer = repo.findByReferredBy(null); // legitimate null argument
        System.out.println("customers with no referrer = " + noReferrer.size());

        boolean threwOnNullName = false;
        try {
            repo.findByName(null); // NOT declared @Nullable -- should be rejected before querying
        } catch (IllegalArgumentException expected) {
            threwOnNullName = true;
            System.out.println("findByName(null) rejected as expected: " + expected.getMessage());
        }

        if (noReferrer.size() != 2) throw new AssertionError("Expected 2 customers with no referrer, found " + noReferrer.size());
        if (!threwOnNullName) throw new AssertionError("Expected findByName(null) to be rejected since it's not @Nullable");

        System.out.println("@Nullable correctly distinguished a legitimate null from an invalid one -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java NullHandlingLevel3.java`.

`findByReferredBy(@Nullable String referredBy)` accepts `null` as a legitimate argument — Spring Data JPA translates a `null` parameter for an equality-derived query into `WHERE referredBy IS NULL` rather than `WHERE referredBy = ?` (which would never match, since SQL `NULL` isn't equal to anything, including itself). `findByName(String name)`, with no `@Nullable` annotation, is protected by Spring Data's default null-safety — passing `null` throws `IllegalArgumentException` immediately, before any query is even built, since the method's signature makes no allowance for absence.

## 6. Walkthrough

Trace Level 3's two finder calls.

1. **`repo.findByReferredBy(null)`**: Spring Data's parameter-validation layer checks the method's null-safety metadata — because the `referredBy` parameter is annotated `@Nullable`, a `null` argument passes validation and proceeds to query generation.
2. **Query generation for a null equality parameter**: Spring Data JPA's derived-query mechanism recognizes that the bound parameter value is `null` and generates `WHERE c.referredBy IS NULL` instead of the usual `WHERE c.referredBy = ?1` — a SQL-level necessity, since `= NULL` never evaluates true in standard SQL.
3. **Query execution**: the database returns the two customers (`Katherine`, `Grace`) whose `referredBy` column is genuinely `NULL`, correctly excluding `Ada` (whose `referredBy` is `"Grace"`, a non-null string).
4. **`repo.findByName(null)`**: Spring Data's parameter-validation layer checks `findByName`'s metadata — `name` has no `@Nullable` annotation, so it's treated as non-null by Spring's default null-safety convention. The validation layer throws `IllegalArgumentException` immediately, *before* any query is constructed or sent to the database.
5. **`try`/`catch` observes the rejection**: the program catches the `IllegalArgumentException`, confirming the parameter was rejected at the validation layer rather than either silently querying with a broken comparison or throwing a less specific, harder-to-diagnose error later.
6. **Verification**: the program checks both the correct count of no-referrer customers and that the null-name call was indeed rejected, printing `PASS` only if both null-handling behaviors — legitimate (`@Nullable`) and illegitimate (undeclared) — worked exactly as their annotations promised.

```
 findByReferredBy(@Nullable String referredBy)
        |
        v
 null argument ALLOWED --> query becomes "WHERE referredBy IS NULL" --> 2 matches

 findByName(String name)   -- no @Nullable
        |
        v
 null argument REJECTED --> IllegalArgumentException thrown BEFORE any query runs
```

## 7. Gotchas & takeaways

> **Gotcha:** a derived-query method built around an equality comparison (`findByReferredBy`) silently changes its generated SQL semantics based on whether the *runtime value* passed is `null`, even though the method's type signature (`String referredBy`) looks identical either way — this is easy to overlook when reading code, since nothing in the method signature itself signals "this becomes an `IS NULL` check when called with null." The `@Nullable` annotation on the parameter is the only compile-time signal that this behavior is intentional and supported.

- `Optional<T>` on a single-result finder method makes "might not exist" explicit and forces the caller to handle both cases without risking a direct null dereference.
- A bare `T` return type is a promise the method will never return `null` — Spring Data enforces this by throwing (typically `EmptyResultDataAccessException`) rather than ever silently returning `null`, so treat a bare-typed finder's "no result" case as exceptional, not as a value to null-check.
- Collection-returning methods (`List<T>`, `Iterable<T>`) never return `null` under any circumstances — an empty collection represents "nothing found," so there's no need (and no correct reason) to null-check a `List<T>` result from a repository.
- `@Nullable` on a query parameter (from `org.springframework.lang`) is what makes passing `null` a supported, intentional input rather than a validation error — without it, Spring Data rejects a `null` argument immediately, before any query executes.
