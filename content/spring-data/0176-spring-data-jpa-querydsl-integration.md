---
card: spring-data
gi: 176
slug: spring-data-jpa-querydsl-integration
title: "Spring Data JPA + QueryDSL integration"
---

## 1. What it is

QueryDSL is a framework for building type-safe queries as Java code instead of strings, using generated "Q-classes" (e.g. `QCustomer` for a `Customer` entity). Spring Data JPA integrates with it through `QuerydslPredicateExecutor`, letting a repository accept a QueryDSL `Predicate` built up from composable, compiler-checked conditions.

```java
interface CustomerRepository extends JpaRepository<Customer, String>,
        QuerydslPredicateExecutor<Customer> {
}

QCustomer customer = QCustomer.customer;
Predicate predicate = customer.city.eq("Lagos").and(customer.lifetimeSpend.gt(100));
List<Customer> matches = (List<Customer>) customerRepository.findAll(predicate);
```

## 2. Why & when

Derived method names work well for fixed, known-in-advance query shapes, but a search form with several optional filters — city, name, minimum spend, any combination present or absent — would need one derived method per combination, or a hand-built JPQL string with the same fragility the Cypher-DSL card addressed for Neo4j. QueryDSL's `Predicate` objects compose the same way that DSL's `Statement` did, but for JPA/relational queries, with the added benefit of compile-time checking against the entity's actual fields.

Reach for QueryDSL with Spring Data JPA when:

- A query's conditions are dynamic and optional, and you want to compose them as Java objects rather than concatenate JPQL or SQL strings.
- You want compile-time safety — referencing `customer.city` through `QCustomer` fails to compile if the `city` field is ever renamed or removed, unlike a string-based query that only fails at runtime.
- The repository should stay a normal `JpaRepository`, gaining predicate-based querying as an additional capability rather than replacing derived methods and `@Query` entirely.

## 3. Core concept

```
 @Entity class Customer { String id, name, city; BigDecimal lifetimeSpend; }
   -> annotation processor generates QCustomer at build time

 QCustomer customer = QCustomer.customer;
 Predicate p = customer.city.eq("Lagos")
                 .and(customer.lifetimeSpend.gt(100));

 customerRepository.findAll(p)
   -> compiles the Predicate into: SELECT c FROM Customer c WHERE c.city = ?1 AND c.lifetimeSpend > ?2
```

`QCustomer` is generated from `Customer`'s actual fields — every predicate built against it is checked by the compiler, unlike a JPQL string that only fails when it runs.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Composable predicate conditions combine into one Predicate object which is translated to a JPQL WHERE clause">
  <rect x="20" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">customer.city.eq("Lagos")</text>

  <rect x="230" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">customer.lifetimeSpend.gt(100)</text>

  <line x1="110" y1="55" x2="260" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a11)"/>
  <line x1="340" y1="55" x2="290" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a11)"/>

  <rect x="180" y="95" width="200" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="117" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">combined Predicate</text>

  <defs><marker id="a11" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Individual predicate conditions compose with `.and()`/`.or()` into a single object, translated to a JPQL `WHERE` clause at execution time.

## 5. Runnable example

The scenario: a customer search endpoint with several optional filters, evolving from a hardcoded fixed query, to a QueryDSL-style `Predicate` built conditionally, to a `BooleanBuilder` composing an arbitrary number of optional filters from a search-form-shaped input — production-flavored dynamic search.

### Level 1 — Basic

Model the fixed-query baseline: one hardcoded filter, to establish the problem being solved.

```java
import java.math.*;
import java.util.*;
import java.util.stream.*;

public class QueryDslLevel1 {
    public static void main(String[] args) {
        List<Customer> customers = List.of(
            new Customer("c1", "Amara", "Lagos", new BigDecimal("250")),
            new Customer("c2", "Bilal", "Lagos", new BigDecimal("50")),
            new Customer("c3", "Chidi", "Abuja", new BigDecimal("400"))
        );

        // Fixed, hardcoded filter -- works, but a new filter combination needs new code.
        List<Customer> lagosCustomers = customers.stream()
            .filter(c -> c.city.equals("Lagos"))
            .collect(Collectors.toList());

        for (Customer c : lagosCustomers) System.out.println("In Lagos: " + c.name);
    }
}

class Customer {
    String id, name, city; BigDecimal lifetimeSpend;
    Customer(String id, String name, String city, BigDecimal lifetimeSpend) {
        this.id = id; this.name = name; this.city = city; this.lifetimeSpend = lifetimeSpend;
    }
}
```

How to run: `java QueryDslLevel1.java`

A hardcoded filter is fine for one fixed query, but every new filter combination (city + minimum spend, name only, spend only) would need its own hand-written method — this is exactly the combinatorial-explosion problem QueryDSL's composable predicates solve.

### Level 2 — Intermediate

Model a QueryDSL-style `Predicate` built from composable conditions, combined conditionally based on which search inputs are present.

```java
import java.math.*;
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class QueryDslLevel2 {
    public static void main(String[] args) {
        List<Customer> customers = List.of(
            new Customer("c1", "Amara", "Lagos", new BigDecimal("250")),
            new Customer("c2", "Bilal", "Lagos", new BigDecimal("50")),
            new Customer("c3", "Chidi", "Abuja", new BigDecimal("400"))
        );

        Predicate<Customer> cityAndMinSpend = search(customers, "Lagos", new BigDecimal("100"));
        for (Customer c : customers) if (cityAndMinSpend.test(c)) System.out.println("Matched: " + c.name);
    }

    // Stands in for building a QueryDSL Predicate: customer.city.eq(city).and(customer.lifetimeSpend.gt(minSpend))
    static Predicate<Customer> search(List<Customer> all, String city, BigDecimal minSpend) {
        Predicate<Customer> cityPredicate = c -> c.city.equals(city);            // customer.city.eq(city)
        Predicate<Customer> spendPredicate = c -> c.lifetimeSpend.compareTo(minSpend) > 0; // customer.lifetimeSpend.gt(minSpend)
        return cityPredicate.and(spendPredicate); // .and() composes them, mirroring QueryDSL's Predicate.and()
    }
}

class Customer {
    String id, name, city; BigDecimal lifetimeSpend;
    Customer(String id, String name, String city, BigDecimal lifetimeSpend) {
        this.id = id; this.name = name; this.city = city; this.lifetimeSpend = lifetimeSpend;
    }
}
```

How to run: `java QueryDslLevel2.java`

`cityPredicate.and(spendPredicate)` mirrors exactly how real QueryDSL code composes `BooleanExpression`s from `QCustomer` fields — each condition is an independent, reusable, compiler-checked object, combined with `.and()`/`.or()` rather than string concatenation.

### Level 3 — Advanced

Build a `BooleanBuilder`-style composer that adds conditions only when the corresponding search input is present — an arbitrary number of optional filters from one method, the realistic shape of a search-form backend.

```java
import java.math.*;
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class QueryDslLevel3 {
    public static void main(String[] args) {
        List<Customer> customers = List.of(
            new Customer("c1", "Amara", "Lagos", new BigDecimal("250")),
            new Customer("c2", "Bilal", "Lagos", new BigDecimal("50")),
            new Customer("c3", "Chidi", "Abuja", new BigDecimal("400"))
        );

        // Only city supplied.
        System.out.println("City=Lagos only: " + search(customers, "Lagos", null, null).size());
        // City + minimum spend supplied.
        System.out.println("City=Lagos, minSpend=100: " + search(customers, "Lagos", new BigDecimal("100"), null).size());
        // Name fragment only.
        System.out.println("Name contains 'Chi': " + search(customers, null, null, "Chi").size());
    }

    // Stands in for building a QueryDSL BooleanBuilder from a search-form's optional fields.
    static List<Customer> search(List<Customer> all, String city, BigDecimal minSpend, String nameFragment) {
        BooleanBuilder<Customer> builder = new BooleanBuilder<>();
        if (city != null) builder.and(c -> c.city.equals(city));
        if (minSpend != null) builder.and(c -> c.lifetimeSpend.compareTo(minSpend) > 0);
        if (nameFragment != null) builder.and(c -> c.name.contains(nameFragment));

        return all.stream().filter(builder.build()).collect(Collectors.toList());
    }
}

class Customer {
    String id, name, city; BigDecimal lifetimeSpend;
    Customer(String id, String name, String city, BigDecimal lifetimeSpend) {
        this.id = id; this.name = name; this.city = city; this.lifetimeSpend = lifetimeSpend;
    }
}

// Stands in for com.querydsl.core.BooleanBuilder: accumulates conditions, ANDed together, only when added.
class BooleanBuilder<T> {
    private Predicate<T> combined = null;
    BooleanBuilder<T> and(Predicate<T> condition) {
        combined = (combined == null) ? condition : combined.and(condition);
        return this;
    }
    Predicate<T> build() { return combined == null ? (t -> true) : combined; } // no conditions -> match everything
}
```

How to run: `java QueryDslLevel3.java`

`BooleanBuilder.and(...)` is only called for filters whose input was actually supplied — with zero conditions added, `build()` returns a predicate matching everything, mirroring `BooleanBuilder`'s real behavior of producing an unrestricted query when nothing was ever added to it, rather than throwing or matching nothing.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `search` calls exercise three different filter combinations against the same three customers.

The first call, `search(customers, "Lagos", null, null)`, adds only the city condition to the builder — `minSpend` and `nameFragment` are both `null`, so neither `and(...)` call happens — and matches `Amara` and `Bilal`, both in Lagos:

```
City=Lagos only: 2
```

The second call adds both a city condition and a spend condition — `combined` becomes `cityPredicate.and(spendPredicate)` — narrowing to just `Amara` (Lagos, spend 250 > 100); `Bilal`'s spend of 50 fails the second condition:

```
City=Lagos, minSpend=100: 1
```

The third call adds only a name-fragment condition, matching `Chidi` regardless of city or spend:

```
Name contains 'Chi': 1
```

In a real Spring Data JPA application, this same `BooleanBuilder` pattern builds a QueryDSL `Predicate`, and `customerRepository.findAll(predicate)` translates it into a single JPQL `WHERE` clause with exactly the conditions that were actually added — Hibernate then compiles that to SQL and executes it against the database in one round trip, regardless of how many or how few filters the original search form supplied.

## 7. Gotchas & takeaways

> Gotcha: an empty `BooleanBuilder` (no conditions ever added) produces a predicate matching *everything*, not nothing — if a search form's "no filters selected" state is supposed to mean "return no results" rather than "return all results," that has to be handled explicitly, since `BooleanBuilder`'s default behavior is the opposite.

> Gotcha: QueryDSL's `Q`-classes are generated by an annotation processor at build time — if the build is misconfigured (annotation processing disabled, or the generated-sources directory not on the classpath), `QCustomer` and friends simply won't exist, and the failure surfaces as a compile error far from the actual misconfiguration.

- QueryDSL's `Predicate` composition solves the same "avoid string concatenation for dynamic queries" problem as the Cypher-DSL did for Neo4j, applied to JPA/relational entities via generated, compiler-checked `Q`-classes.
- `QuerydslPredicateExecutor` lets a `JpaRepository` accept a `Predicate` directly, alongside its normal derived methods and `@Query` — it's additive, not a replacement.
- `BooleanBuilder` accumulates optional conditions and is the standard pattern for search-form-shaped queries with any combination of filters present or absent.
- An empty `BooleanBuilder` matches everything by default — worth handling explicitly if "no filters" should mean "no results" instead.
