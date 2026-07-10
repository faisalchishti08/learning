---
card: spring-data
gi: 25
slug: open-vs-closed-projections
title: "Open vs closed projections"
---

## 1. What it is

Interface-based projections come in two flavors: "closed" projections, where every getter method's name exactly matches an underlying entity property (as used throughout the previous card), and "open" projections, where a getter is annotated with `@Value` and a SpEL expression, letting it compute a value from one or more entity properties rather than mapping to exactly one. Spring Data can optimize a closed projection's underlying SQL to select only the needed columns; an open projection, because its SpEL expression could reference anything, generally requires the full entity to be loaded first before the expression is evaluated against it.

```java
// CLOSED: every getter maps 1:1 to an entity property -- SQL can be optimized
public interface CustomerSummary {
    String getFirstName();
    String getLastName();
}

// OPEN: a getter computed via SpEL, referencing multiple properties -- needs the full entity
public interface CustomerSummary {
    @Value("#{target.firstName + ' ' + target.lastName}")
    String getFullName();
}
```

## 2. Why & when

Closed projections are more efficient (fewer columns fetched) but limited to a direct one-to-one property mapping — they can't compute a derived value like a full name from first and last name, or apply any transformation. Open projections trade that efficiency for flexibility, letting a projection method return a computed or combined value at the cost of Spring Data needing to load the full entity anyway (since the SpEL expression is evaluated against the complete loaded object, not against individual pre-fetched columns).

Choose between them specifically based on:

- **Closed** when every field a projection needs maps directly to a single entity property with no transformation — the common case, and the one that gets genuine query-optimization benefit.
- **Open** when a projection needs a computed, combined, or transformed value — concatenating fields, formatting a number, referencing a related entity's property through a short expression — accepting that the underlying query can no longer be narrowed to fewer columns.
- Mixing the two within the same interface is entirely legal — a projection interface can have some purely closed getters and some `@Value`-annotated open ones, gaining partial optimization on the closed parts.

## 3. Core concept

```
 CLOSED projection getter:
   String getFirstName();
        |
        v
   Spring Data matches "firstName" directly against the entity's property --
   for JPA, can generate: SELECT p.firstName FROM Product p ...
   (only the needed column, not the whole row)

 OPEN projection getter:
   @Value("#{target.firstName + ' ' + target.lastName}")
   String getFullName();
        |
        v
   Spring Data CANNOT know in advance what the SpEL expression needs --
   it loads the FULL entity, then evaluates the SpEL expression against it
   ("target" refers to the loaded entity instance) to produce the getter's value

 A single projection interface CAN mix both kinds of getters.
```

The `target` variable inside an open projection's SpEL expression always refers to the underlying, fully-loaded entity instance for that row.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Closed projections allow column-level query optimization; open projections require the full entity to evaluate a SpEL expression against">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CLOSED: getFirstName()</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SELECT firstName only</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-- query can be narrowed</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OPEN: @Value("#{target.first...}")</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">loads FULL entity first</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-- then evaluates SpEL against it</text>

  <rect x="150" y="115" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">both can coexist in ONE projection interface</text>
</svg>

Closed getters map straight to columns; open getters need the whole row loaded before their expression runs.

## 5. Runnable example

The scenario: a `Customer` catalog, evolving from a purely closed projection, to a purely open one computing a combined value, to a mixed interface using both kinds of getters together.

### Level 1 — Basic

Declare a purely closed projection and confirm each getter maps directly to an entity property.

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
public class OpenClosedLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;
        protected Customer() {}
        public Customer(String firstName, String lastName) { this.firstName = firstName; this.lastName = lastName; }
    }

    // CLOSED: getter names map 1:1 to entity properties.
    public interface NameOnly {
        String getFirstName();
        String getLastName();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<NameOnly> findAllProjectedBy();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(OpenClosedLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:openclosed1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Lovelace"));
        repo.save(new Customer("Grace", "Hopper"));

        List<NameOnly> names = repo.findAllProjectedBy();
        System.out.println("closed projections: " + names.stream().map(n -> n.getFirstName() + " " + n.getLastName()).toList());

        if (names.size() != 2) throw new AssertionError("Expected 2 projected customers");
        System.out.println("Closed projection getters mapped 1:1 to entity properties -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java OpenClosedLevel1.java` on JDK 17+.

`findAllProjectedBy()` (a Spring Data naming convention: `findAllProjectedBy` retrieves all entities, projected into whatever type the method's declared return element is) returns `List<NameOnly>` — every getter (`getFirstName`, `getLastName`) maps directly to an identically-named `Customer` property, making this a purely closed projection.

### Level 2 — Intermediate

Declare a purely open projection using `@Value` and SpEL to compute a combined value from two entity properties.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class OpenClosedLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;
        protected Customer() {}
        public Customer(String firstName, String lastName) { this.firstName = firstName; this.lastName = lastName; }
    }

    // OPEN: a getter computed via SpEL, combining two properties into one.
    public interface FullNameView {
        @Value("#{target.firstName + ' ' + target.lastName}")
        String getFullName();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<FullNameView> findAllProjectedBy();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(OpenClosedLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:openclosed2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Lovelace"));
        repo.save(new Customer("Grace", "Hopper"));

        List<FullNameView> views = repo.findAllProjectedBy();
        System.out.println("open projections (computed fullName): " + views.stream().map(FullNameView::getFullName).toList());

        if (!views.get(0).getFullName().equals("Ada Lovelace"))
            throw new AssertionError("Expected the SpEL expression to compute 'Ada Lovelace'");
        System.out.println("Open projection computed a combined value via SpEL against the loaded entity -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java OpenClosedLevel2.java`.

`@Value("#{target.firstName + ' ' + target.lastName}")` is a SpEL expression evaluated against `target` — the full, loaded `Customer` entity instance for each row — computing a combined `"firstName lastName"` string that has no direct one-to-one entity property equivalent. Because the expression could reference anything about the entity, Spring Data must load the complete `Customer` row first before it can evaluate this getter, unlike Level 1's closed projection.

### Level 3 — Advanced

Mix closed and open getters in one projection interface, and confirm both kinds of getters work correctly together — the realistic shape of a projection that's mostly efficient (closed) but needs one computed field (open).

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class OpenClosedLevel3 {

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
    }

    // MIXED: closed getters (direct mapping) alongside an open one (SpEL-computed).
    public interface CustomerCard {
        String getFirstName();    // CLOSED -- maps directly to the property
        int getLoyaltyPoints();   // CLOSED -- maps directly to the property

        @Value("#{target.firstName + ' ' + target.lastName}")
        String getFullName();     // OPEN -- computed from two properties

        @Value("#{target.loyaltyPoints >= 100 ? 'GOLD' : 'STANDARD'}")
        String getTier();          // OPEN -- computed with conditional logic
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<CustomerCard> findAllProjectedBy();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(OpenClosedLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:openclosed3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", "Lovelace", 150));
        repo.save(new Customer("Grace", "Hopper", 40));

        List<CustomerCard> cards = repo.findAllProjectedBy();
        for (CustomerCard card : cards) {
            System.out.println(card.getFirstName() + " | " + card.getFullName() + " | "
                + card.getLoyaltyPoints() + "pts | " + card.getTier());
        }

        CustomerCard ada = cards.stream().filter(c -> c.getFirstName().equals("Ada")).findFirst().orElseThrow();
        CustomerCard grace = cards.stream().filter(c -> c.getFirstName().equals("Grace")).findFirst().orElseThrow();

        if (!ada.getFullName().equals("Ada Lovelace")) throw new AssertionError("Expected computed full name for Ada");
        if (!ada.getTier().equals("GOLD")) throw new AssertionError("Expected Ada (150pts) to be GOLD tier");
        if (!grace.getTier().equals("STANDARD")) throw new AssertionError("Expected Grace (40pts) to be STANDARD tier");

        System.out.println("Mixed closed + open projection getters all resolved correctly together -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java OpenClosedLevel3.java`.

`CustomerCard` mixes two closed getters (`getFirstName`, `getLoyaltyPoints`, mapping directly to properties) with two open getters (`getFullName`, combining two properties; `getTier`, applying conditional SpEL logic based on a threshold) — all four resolve correctly against the same underlying `Customer` rows. Because at least one open getter is present, Spring Data loads the full entity for each row (the closed getters' potential optimization is effectively moot once any open getter is in the mix), then evaluates every getter — closed or open — against that loaded instance.

## 6. Walkthrough

Trace how `CustomerCard`'s getters resolve for the `Ada` row.

1. **Query execution**: `findAllProjectedBy()` executes a query retrieving `Customer` rows — because `CustomerCard` contains at least one `@Value`-annotated (open) getter, Spring Data loads full `Customer` entities rather than attempting a narrowed, columns-only `SELECT`.
2. **Proxy creation**: for each loaded `Customer` row, Spring Data creates a proxy implementing `CustomerCard`, internally holding a reference to that specific loaded `Customer` instance as its `target`.
3. **`ada.getFirstName()`** (closed getter): the proxy recognizes this getter name matches a property directly on the target entity, and simply returns `target.getFirstName()` — no SpEL evaluation involved.
4. **`ada.getLoyaltyPoints()`** (closed getter): resolves the same direct way, returning `150`.
5. **`ada.getFullName()`** (open getter): the proxy recognizes this getter is `@Value`-annotated, and evaluates the SpEL expression `#{target.firstName + ' ' + target.lastName}` against the held `target` (Ada's `Customer` instance), producing `"Ada Lovelace"`.
6. **`ada.getTier()`** (open getter): evaluates `#{target.loyaltyPoints >= 100 ? 'GOLD' : 'STANDARD'}` against the same target — `150 >= 100` is `true`, so the SpEL ternary produces `"GOLD"`.
7. **The same process repeats for Grace's row**, independently — her proxy holds *her* `Customer` instance as `target`, so `getTier()` evaluates `40 >= 100` as `false`, producing `"STANDARD"`.
8. **Verification**: the program checks Ada's computed full name and tier, and Grace's tier, confirming both closed and open getters resolved correctly and independently for each row.

```
 Customer row (Ada, Lovelace, 150) loaded FULLY (because an open getter exists)
        |
        v
 CustomerCard proxy, target = this Customer instance
        |
        +-- getFirstName()    [closed] --> target.getFirstName()          --> "Ada"
        +-- getLoyaltyPoints() [closed] --> target.getLoyaltyPoints()       --> 150
        +-- getFullName()     [open]   --> SpEL: target.firstName + ' ' + target.lastName --> "Ada Lovelace"
        +-- getTier()          [open]   --> SpEL: target.loyaltyPoints >= 100 ? 'GOLD' : ... --> "GOLD"
```

## 7. Gotchas & takeaways

> **Gotcha:** the presence of even one open (`@Value`-annotated) getter in a projection interface generally prevents Spring Data from optimizing the underlying query to fewer columns for the *entire* interface — since the full entity must be loaded for the SpEL expression to have something to evaluate against, the closed getters in the same interface don't get their usual column-narrowing benefit either. If query-level optimization genuinely matters, keep purely closed projections in a separate interface from any that need computed values.

- Closed projections (every getter mapping 1:1 to an entity property) allow Spring Data to potentially optimize the underlying query to select only the needed columns — the more efficient option when applicable.
- Open projections (`@Value` with a SpEL expression, referencing `target`) can compute, combine, or transform values, at the cost of requiring the full entity to be loaded first — the more flexible option when a direct property mapping isn't enough.
- A single projection interface can freely mix closed and open getters — useful for a projection that's mostly simple property access with one or two computed fields layered on top.
- `target` inside an open projection's SpEL expression always refers to the specific, fully-loaded entity instance backing that particular projected row — the same SpEL syntax and capabilities available elsewhere in Spring (property access, arithmetic, conditionals, method calls) are available here too.
