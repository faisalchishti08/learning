---
card: spring-data
gi: 94
slug: fluent-query-api-criteria
title: "Fluent query API (Criteria)"
---

## 1. What it is

The `Criteria` class is Spring Data R2DBC's fluent, programmatic query-building API — the reactive module's answer to the same need Querydsl and the JPA Specification API address: building a query dynamically, condition by condition, as composable Java objects rather than a fixed derived method name or a raw SQL/`@Query` string.

```java
Flux<Order> orders = template.select(Order.class)
    .matching(Criteria.where("status").is("SHIPPED").and("total").greaterThan(100.0))
    .all();
```

## 2. Why & when

Every earlier R2DBC card used either a fixed derived method or raw SQL through `DatabaseClient`. `Criteria` fills the gap for dynamic queries — conditions that depend on runtime input, some of which may be absent — the same problem the JPA Specifications card solved for the blocking module, just with a different API shape suited to R2DBC's `R2dbcEntityTemplate`.

Reach for `Criteria` specifically when:

- A query's conditions vary at runtime — some filters present, some absent (a search form where any field may be blank) — building this as a fixed derived method name or a single `@Query` string is awkward or impossible.
- You want compile-time-checked composition (`.and()`, `.or()`) of conditions as Java objects, similar in spirit to Querydsl or JPA's `Specification`, adapted for the reactive `R2dbcEntityTemplate`.
- You're building a custom reactive repository fragment (from the `R2dbcEntityTemplate` card) and need a query more flexible than a single derived method or fixed `@Query`, but don't need the full generality (and extra ceremony) of raw SQL via `DatabaseClient`.

## 3. Core concept

```
 Criteria.where("status").is("SHIPPED")                     -- one condition
 Criteria.where("status").is("SHIPPED").and("total").greaterThan(100.0)  -- composed with .and()
 Criteria.where("status").is("SHIPPED").or("status").is("PENDING")        -- composed with .or()

 template.select(Order.class).matching(criteria).all()  -- Flux<Order>, criteria plugged in
 template.select(Order.class).matching(criteria).first()  -- Mono<Order>, single result
 template.select(Order.class).matching(criteria).count()  -- Mono<Long>, count instead of rows
```

`Criteria` objects compose via `.and()`/`.or()` into a single tree of conditions, then plug into `R2dbcEntityTemplate.select(...).matching(...)` to produce the actual query.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Individual Criteria conditions compose via and/or into one tree, then plug into a select-matching query">
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="43" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">where("status").is("SHIPPED")</text>

  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">and("total").gt(100.0)</text>

  <rect x="120" y="85" width="300" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="270" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">composed Criteria tree</text>

  <rect x="460" y="85" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="108" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">select(...).matching(...)</text>

  <line x1="110" y1="60" x2="200" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#fq)"/>
  <line x1="320" y1="60" x2="290" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#fq)"/>
  <line x1="420" y1="105" x2="455" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#fq)"/>
  <defs><marker id="fq" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Small, individual conditions compose into one tree, which then drives the actual reactive query.

## 5. Runnable example

The scenario: a dynamic order search, evolving from a single fixed criteria condition, to composed multi-condition criteria, to a fully dynamic builder that skips absent optional filters — the same optional-filter problem the Querydsl and Specifications cards solved for other modules.

### Level 1 — Basic

Model a single `Criteria`-style condition and apply it, standing in for `Criteria.where("status").is(status)`.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for org.springframework.data.relational.core.query.Criteria
class Criteria {
    private final Predicate<Order> predicate;
    private Criteria(Predicate<Order> predicate) { this.predicate = predicate; }

    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGreaterThan(double min) { return new Criteria(o -> o.total > min); }

    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Criteria or(Criteria other) { return new Criteria(o -> this.predicate.test(o) || other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

public class CriteriaLevel1 {
    // Simulates: template.select(Order.class).matching(criteria).all()
    static CompletableFuture<List<Order>> select(List<Order> data, Criteria criteria) {
        return CompletableFuture.supplyAsync(() ->
            data.stream().filter(criteria.asPredicate()).collect(Collectors.toList()));
    }

    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(new Order(1, "SHIPPED", 50), new Order(2, "PENDING", 150));

        Criteria criteria = Criteria.statusIs("SHIPPED"); // Criteria.where("status").is("SHIPPED")
        List<Order> found = select(orders, criteria).get();
        System.out.println("Found: " + found.size() + " matching order(s)");
    }
}
```

How to run: `java CriteriaLevel1.java`

`Criteria.statusIs("SHIPPED")` wraps a single condition as a composable object — standing in for `Criteria.where("status").is("SHIPPED")` — and `select` applies it as a filter predicate, matching how `R2dbcEntityTemplate.select(Order.class).matching(criteria)` uses the `Criteria` object to filter query results.

### Level 2 — Intermediate

Compose two conditions with `.and()`, matching `Criteria.where("status").is(...).and("total").greaterThan(...)`.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class Criteria {
    private final Predicate<Order> predicate;
    private Criteria(Predicate<Order> predicate) { this.predicate = predicate; }
    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGreaterThan(double min) { return new Criteria(o -> o.total > min); }
    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Criteria or(Criteria other) { return new Criteria(o -> this.predicate.test(o) || other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

public class CriteriaLevel2 {
    static CompletableFuture<List<Order>> select(List<Order> data, Criteria criteria) {
        return CompletableFuture.supplyAsync(() -> data.stream().filter(criteria.asPredicate()).collect(Collectors.toList()));
    }

    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 150), new Order(3, "PENDING", 200)
        );

        // Criteria.where("status").is("SHIPPED").and("total").greaterThan(100.0)
        Criteria criteria = Criteria.statusIs("SHIPPED").and(Criteria.totalGreaterThan(100.0));
        List<Order> found = select(orders, criteria).get();
        System.out.println("Shipped AND total > 100: " + found.size() + " order(s)");
    }
}
```

How to run: `java CriteriaLevel2.java`

`Criteria.statusIs("SHIPPED").and(Criteria.totalGreaterThan(100.0))` composes two independent conditions into one — only order 2 (`SHIPPED`, `total=150`) satisfies both; order 1 fails the total check, order 3 fails the status check — matching exactly how a real `Criteria.where(...).and(...)` chain builds a compound `WHERE` clause.

### Level 3 — Advanced

Build a dynamic search that conditionally composes criteria based on which optional filter fields are actually supplied, skipping absent ones — the same optional-filter problem the Querydsl and Specifications cards solved for other Spring Data modules.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class Criteria {
    private final Predicate<Order> predicate;
    private Criteria(Predicate<Order> predicate) { this.predicate = predicate; }
    static Criteria empty() { return new Criteria(o -> true); } // Criteria.empty() -- identity, matches everything
    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGreaterThan(double min) { return new Criteria(o -> o.total > min); }
    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

public class CriteriaLevel3 {
    // Builds Criteria dynamically, skipping any filter argument that's null -- exactly like a real search form.
    static Criteria buildSearchCriteria(String status, Double minTotal) {
        Criteria criteria = Criteria.empty();
        if (status != null) criteria = criteria.and(Criteria.statusIs(status));
        if (minTotal != null) criteria = criteria.and(Criteria.totalGreaterThan(minTotal));
        return criteria;
    }

    static CompletableFuture<List<Order>> select(List<Order> data, Criteria criteria) {
        return CompletableFuture.supplyAsync(() -> data.stream().filter(criteria.asPredicate()).collect(Collectors.toList()));
    }

    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 150), new Order(3, "PENDING", 200)
        );

        // Simulates a search form where the user only filled in "status".
        Criteria statusOnly = buildSearchCriteria("SHIPPED", null);
        System.out.println("Status only: " + select(orders, statusOnly).get().size() + " order(s)");

        // Simulates a search form where the user filled in both fields.
        Criteria both = buildSearchCriteria("SHIPPED", 100.0);
        System.out.println("Both filters: " + select(orders, both).get().size() + " order(s)");

        // Simulates a search form where the user filled in NOTHING.
        Criteria none = buildSearchCriteria(null, null);
        System.out.println("No filters: " + select(orders, none).get().size() + " order(s)");
    }
}
```

How to run: `java CriteriaLevel3.java`

`buildSearchCriteria` starts from `Criteria.empty()` (matching everything) and conditionally `.and()`s in each supplied filter, skipping `null` ones entirely — `statusOnly` matches both `SHIPPED` orders, `both` narrows to just order 2, and `none` (no filters at all) matches all three orders, exactly mirroring the optional-filter pattern from the earlier Querydsl and Specifications cards, adapted to R2DBC's reactive `Criteria` API.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `buildSearchCriteria("SHIPPED", null)` runs: `criteria` starts as `Criteria.empty()` (a predicate that's always `true`); since `status` is non-null, `criteria` becomes `empty.and(statusIs("SHIPPED"))`; since `minTotal` is `null`, the second `if` is skipped entirely — the final `criteria` only enforces the status check. `select(orders, statusOnly)` then filters all three orders through this predicate, matching orders 1 and 2 (both `SHIPPED`) and excluding order 3 (`PENDING`) — printed as "Status only: 2 order(s)".

Next, `buildSearchCriteria("SHIPPED", 100.0)` runs: both conditions are added this time, producing `empty.and(statusIs("SHIPPED")).and(totalGreaterThan(100.0))`. Filtering the same three orders, only order 2 (`SHIPPED`, `total=150`) satisfies both — printed as "Both filters: 1 order(s)".

Finally, `buildSearchCriteria(null, null)` runs: neither `if` branch executes, so `criteria` remains exactly `Criteria.empty()` — its predicate always returns `true`. Filtering the three orders against this identity criteria matches all of them — printed as "No filters: 3 order(s)".

```
buildSearchCriteria("SHIPPED", null):    empty.and(status==SHIPPED)                       -> matches [order1, order2]
buildSearchCriteria("SHIPPED", 100.0):   empty.and(status==SHIPPED).and(total>100.0)        -> matches [order2]
buildSearchCriteria(null, null):         empty (no conditions added)                        -> matches [order1, order2, order3]
```

In a real Spring Data R2DBC application, `buildSearchCriteria` would return a genuine `org.springframework.data.relational.core.query.Criteria` object, and the calling code would pass it to `template.select(Order.class).matching(criteria).all()`, producing a `Flux<Order>` filtered by whatever combination of conditions the search form actually supplied — the database receives a single, dynamically-assembled `WHERE` clause reflecting exactly the non-null filters, with no conditional branching needed in the SQL itself; all of that logic lives in how the `Criteria` object was built in Java.

## 7. Gotchas & takeaways

> Gotcha: `Criteria.empty()` combined with `.and(...)` conditions works cleanly for "match everything unless a filter narrows it," but building the equivalent "match nothing unless a filter is present" logic (common for search screens that shouldn't return every row when no filter is given) requires different composition — starting from a criteria that matches nothing and using `.or()` instead, which is easy to get backwards.

- `Criteria` is Spring Data R2DBC's fluent, composable query-building API, filling the same role Querydsl and JPA's `Specification` fill for other modules.
- Individual conditions compose via `.and()`/`.or()` into a single tree, which then plugs into `R2dbcEntityTemplate.select(...).matching(...)`.
- The standard pattern for optional/dynamic filters is starting from an identity criteria (`Criteria.empty()`, matching everything) and conditionally `.and()`-ing in only the filters actually supplied.
- Reach for `Criteria` when a query's conditions vary at runtime and a fixed derived method or `@Query` string can't express that variability cleanly.
