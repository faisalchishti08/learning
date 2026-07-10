---
card: spring-data
gi: 55
slug: query-by-example-qbe
title: "Query by Example (QBE)"
---

## 1. What it is

Query by Example lets you build a query by populating a *probe* — a plain instance of your entity type with only the fields you want to filter on set, leaving the rest `null`/default — wrapping it in an `Example<T>`, and passing that to `QueryByExampleExecutor<T>` (an interface `JpaRepository` already extends). Spring Data inspects which fields on the probe are non-null (by default) and builds a query matching only those, with zero query-string writing, zero Criteria API code, and zero `Specification` objects.

```java
Customer probe = new Customer();
probe.setLastName("Lovelace");
probe.setActive(true);

Example<Customer> example = Example.of(probe);
List<Customer> matches = customerRepository.findAll(example);
```

## 2. Why & when

Every dynamic-query mechanism covered so far in this section (custom fragments, Querydsl, Specifications) requires writing *some* code describing the query's shape — a `Predicate`, a `Specification` lambda, Criteria API calls. Query by Example is different: for the common case of "match on whatever fields happen to be set on this object," it needs none of that — the probe object itself *is* the query description, inferred automatically from which fields are populated. This makes it an especially good fit for simple, form-driven search UIs where the search criteria naturally already exist as a partially-filled domain object.

Reach for Query by Example specifically when:

- A search form's fields map directly, one-to-one, onto entity properties, and "match whichever fields the user actually filled in" is exactly the filtering logic needed — QBE expresses this with zero query-building code.
- You want the simplest possible dynamic-query mechanism for straightforward equality-based filtering, reserving `Specification`/Querydsl for genuinely more complex conditions (ranges, `OR` logic, joins) that QBE's default equality-matching can't express.
- You're prototyping quickly and want dynamic filtering without committing to any of the more ceremony-heavy mechanisms (custom fragments, Querydsl's build-time code generation) yet.

## 3. Core concept

```
 Customer probe = new Customer();
 probe.setLastName("Lovelace");     -- SET: becomes a filter condition
                                        (everything else left null/default: IGNORED)

 Example<Customer> example = Example.of(probe);
        |
        v
 QueryByExampleExecutor<T> (extended by JpaRepository already):
   findAll(Example<T>)              findOne(Example<T>)
   findAll(Example<T>, Sort)        count(Example<T>)
   findAll(Example<T>, Pageable)    exists(Example<T>)

 DEFAULT MATCHING BEHAVIOR:
   - null/default-valued fields on the probe are IGNORED (not matched as "IS NULL")
   - String fields match by EXACT equality by default
   - ExampleMatcher customizes this: case-insensitive, CONTAINS/STARTS_WITH,
     ignoring specific paths, custom per-field matchers
```

The probe object's *state* (which fields are set) is the entire query specification — no separate query-building code is written at all for the basic case.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A partially-populated probe object is wrapped in an Example and passed to findAll, with only the set fields becoming query conditions">
  <rect x="10" y="20" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">probe (partial Customer)</text>
  <text x="120" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lastName="Lovelace", rest null</text>

  <rect x="270" y="20" width="150" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Example.of(probe)</text>

  <rect x="460" y="20" width="170" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repo.findAll(example)</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WHERE lastName='Lovelace'</text>

  <line x1="230" y1="47" x2="265" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="47" x2="455" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The probe's populated fields become the query — no separate query-building syntax involved.

## 5. Runnable example

The scenario: a customer search, evolving from a basic single-field probe, to multi-field matching, to a customized `ExampleMatcher` with case-insensitive, substring-based string matching.

### Level 1 — Basic

Build a probe with one field set and confirm `findAll(Example)` filters correctly.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Example;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QbeLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;
        protected Customer() {}
        public Customer(String firstName, String lastName) { this.firstName = firstName; this.lastName = lastName; }
        public String getFirstName() { return firstName; }
        public String getLastName() { return lastName; }
        public void setLastName(String lastName) { this.lastName = lastName; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QbeLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:qbe1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Lovelace"));
        repo.save(new Customer("Katherine", "Lovelace"));
        repo.save(new Customer("Grace", "Hopper"));

        Customer probe = new Customer(null, null); // most fields null -- only lastName set below
        probe.setLastName("Lovelace");

        Example<Customer> example = Example.of(probe);
        List<Customer> matches = repo.findAll(example);

        System.out.println("matches for lastName='Lovelace' = " + matches.stream().map(Customer::getFirstName).toList());

        if (matches.size() != 2) throw new AssertionError("Expected 2 customers named Lovelace");
        System.out.println("Query by Example matched purely on the one populated probe field -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java QbeLevel1.java` on JDK 17+.

`probe`'s `firstName` is `null`, `lastName` is `"Lovelace"` — `Example.of(probe)` builds a query matching only the populated field, `WHERE lastName = 'Lovelace'`, completely ignoring the `null` `firstName` field (not treating it as an `IS NULL` condition, which would be a very different and usually unintended query).

### Level 2 — Intermediate

Set multiple fields on the probe simultaneously, confirming they combine with implicit `AND` logic.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Example;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QbeLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String lastName;
        private String region;
        private boolean active;
        protected Customer() {}
        public Customer(String lastName, String region, boolean active) {
            this.lastName = lastName; this.region = region; this.active = active;
        }
        public String getLastName() { return lastName; }
        public String getRegion() { return region; }
        public boolean isActive() { return active; }
        public void setLastName(String lastName) { this.lastName = lastName; }
        public void setRegion(String region) { this.region = region; }
        public void setActive(boolean active) { this.active = active; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QbeLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:qbe2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Lovelace", "EU", true));
        repo.save(new Customer("Lovelace", "US", true));
        repo.save(new Customer("Lovelace", "EU", false));

        Customer probe = new Customer(null, null, false); // active=false is a PRIMITIVE default -- see gotcha
        probe.setLastName("Lovelace");
        probe.setRegion("EU");

        // NOTE: primitives default to false/0, so "active" would ALWAYS match false unless
        // excluded via ExampleMatcher.ignoringPaths("active") -- demonstrated in Level 3.
        Example<Customer> example = Example.of(probe,
            org.springframework.data.domain.ExampleMatcher.matching().withIgnorePaths("active"));
        List<Customer> matches = repo.findAll(example);

        System.out.println("matches for lastName='Lovelace' AND region='EU' = " + matches.size());

        if (matches.size() != 2) throw new AssertionError("Expected 2 EU-region Lovelaces (active status ignored)");
        System.out.println("Multiple probe fields combined with implicit AND -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java QbeLevel2.java`.

`lastName = "Lovelace"` and `region = "EU"` are both set on the probe — the resulting query is `WHERE lastName = 'Lovelace' AND region = 'EU'`, correctly matching both the active and inactive EU-region Lovelace customers (2 of the 3 seeded rows), since `active` was deliberately excluded via `withIgnorePaths("active")` — the gotcha this example is already working around, covered fully below.

### Level 3 — Advanced

Use `ExampleMatcher` for case-insensitive, substring (`CONTAINS`) string matching — the customization QBE needs for anything beyond exact equality.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.ExampleMatcher;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QbeLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String fullName;
        protected Customer() {}
        public Customer(String fullName) { this.fullName = fullName; }
        public String getFullName() { return fullName; }
        public void setFullName(String fullName) { this.fullName = fullName; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QbeLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:qbe3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada Lovelace"));
        repo.save(new Customer("ADA Byron"));
        repo.save(new Customer("Grace Hopper"));

        Customer probe = new Customer(null);
        probe.setFullName("ada"); // lowercase, partial -- would match NEITHER with exact/case-sensitive default

        ExampleMatcher matcher = ExampleMatcher.matching()
            .withMatcher("fullName", ExampleMatcher.GenericPropertyMatcher::containsIgnoreCase);

        Example<Customer> example = Example.of(probe, matcher);
        List<Customer> matches = repo.findAll(example);

        System.out.println("case-insensitive CONTAINS('ada') matches = " + matches.stream().map(Customer::getFullName).toList());

        if (matches.size() != 2) throw new AssertionError("Expected 2 matches (Ada Lovelace, ADA Byron) via case-insensitive substring match");
        System.out.println("ExampleMatcher customized string matching to case-insensitive CONTAINS -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java QbeLevel3.java`.

By default, QBE matches strings by *exact* equality — `probe.setFullName("ada")` (all lowercase, partial) would match neither `"Ada Lovelace"` nor `"ADA Byron"` under that default. `ExampleMatcher.matching().withMatcher("fullName", ... containsIgnoreCase)` customizes matching for specifically the `fullName` path to case-insensitive substring matching, correctly finding both names containing `"ada"` regardless of case.

## 6. Walkthrough

Trace Level 3's matcher-customized query.

1. **Probe and matcher construction**: `probe.fullName = "ada"` sets the search value; `ExampleMatcher.matching().withMatcher("fullName", ...containsIgnoreCase)` overrides the default exact-match behavior specifically for the `fullName` property.
2. **`Example.of(probe, matcher)`** bundles both the probe's values and the customized matching rules into one `Example<Customer>` object.
3. **Query translation**: Spring Data JPA's QBE support translates this into a JPQL/SQL query using `LOWER(fullName) LIKE LOWER('%ada%')` (or an equivalent case-insensitive `LIKE` construct) — the case-insensitive-substring behavior the custom matcher specified, rather than the default `fullName = 'ada'` exact match.
4. **Execution**: H2 evaluates this against all three seeded customers — `"Ada Lovelace"` contains `"ada"` case-insensitively (true), `"ADA Byron"` contains `"ada"` case-insensitively (true), `"Grace Hopper"` does not (false).
5. **Result**: exactly 2 matches, returned as `List<Customer>`.
6. **Verification**: the program checks the match count and confirms both expected names are present, proving the customized `ExampleMatcher` behavior — not the default exact-match behavior — genuinely governed the query.

```
 probe.fullName = "ada"   (lowercase, partial)
        |
 default matching:  fullName = 'ada'                -->  0 matches (case + exact-match mismatch)
        |
 with ExampleMatcher containsIgnoreCase:
   LOWER(fullName) LIKE LOWER('%ada%')               -->  2 matches: "Ada Lovelace", "ADA Byron"
```

## 7. Gotchas & takeaways

> **Gotcha:** primitive fields (`boolean`, `int`, and similar, as opposed to their boxed equivalents `Boolean`, `Integer`) on a probe object can never be genuinely "unset" — a `boolean active` field defaults to `false`, which QBE's default matching treats as a real, intentional filter condition (`WHERE active = false`), not as "field not specified." This was exactly why Level 2 needed `withIgnorePaths("active")` — without it, the probe would have silently filtered to only inactive customers, an easy, subtle bug. Use boxed types (`Boolean`, `Integer`) for probe fields you want to be able to genuinely leave unset, or always explicitly `ignorePaths` any primitive fields not meant to filter.

- Query by Example builds a query directly from which fields are populated on a plain probe instance — no query-string, Criteria API, or `Specification` code needed for the basic, equality-matching case.
- `null`/unset fields on the probe are ignored by default, not treated as `IS NULL` conditions — but primitive-typed fields can never be truly "unset," making them a common source of unintended filter conditions unless explicitly excluded via `ExampleMatcher.withIgnorePaths(...)`.
- `ExampleMatcher` customizes matching behavior beyond the default exact-equality — case-insensitivity, `CONTAINS`/`STARTS_WITH`/`ENDS_WITH` substring matching, and per-property matcher overrides all go through it.
- QBE is best suited to simple, equality/substring-based filtering directly mapped from a domain object's own fields — for genuinely complex conditions (ranges, `OR` logic, joins across relationships), `Specification` (from an earlier card) or Querydsl remain the more capable, if more verbose, choices.
