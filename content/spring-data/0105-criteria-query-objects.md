---
card: spring-data
gi: 105
slug: criteria-query-objects
title: "Criteria & Query objects"
---

## 1. What it is

`Criteria` and `Query` are Spring Data MongoDB's fluent, programmatic query-building API — the document-store counterpart to R2DBC's `Criteria` (and, conceptually, to JPA's `Specification`) — letting a query be assembled dynamically from composable Java objects instead of a fixed derived method name or a raw `@Query` JSON string.

```java
Query query = Query.query(
    Criteria.where("status").is("SHIPPED").and("total").gte(100.0));
List<Order> orders = mongoTemplate.find(query, Order.class);
```

## 2. Why & when

The `@Query` JSON card handled operator-rich but *fixed* conditions well; `Criteria`/`Query` are for the same dynamic-condition problem the R2DBC `Criteria` card and JPA `Specification` card both solved for their respective modules — conditions that vary at runtime, some present, some absent, composed programmatically rather than baked into a fixed query string.

Reach for `Criteria`/`Query` specifically when:

- A query's conditions vary at runtime — a search form where any combination of filters might be supplied — the same optional-filter problem covered for every other Spring Data module in this series.
- You want compile-time-checked, composable query building as Java objects (`.and()`, `.or()`), rather than string-concatenating a `@Query` JSON template.
- You're building custom repository fragments using `MongoTemplate` directly and need to construct the actual query object it expects (`mongoTemplate.find(query, EntityClass.class)`).

## 3. Core concept

```
 Criteria.where("status").is("SHIPPED")                          -- one condition
 Criteria.where("status").is("SHIPPED").and("total").gte(100.0)   -- composed with .and()
 Criteria.where("status").is("SHIPPED").orOperator(
     Criteria.where("total").gte(500.0), Criteria.where("priority").is(true))  -- composed with .or()

 Query.query(criteria)                    -- wraps a Criteria into a Query
       .with(Sort.by("total").descending())  -- adds sorting
       .limit(20)                             -- adds paging

 mongoTemplate.find(query, Order.class)   -- executes it, List<Order> (or Flux<Order> reactively)
```

`Criteria` objects compose into a tree of conditions; `Query` wraps that tree together with sorting/paging/other query-shaping options, ready to execute against `MongoTemplate`.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Composed Criteria conditions are wrapped in a Query with sorting and limits, then executed via MongoTemplate">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">composed Criteria</text>

  <rect x="260" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Query.query(criteria)</text>
  <text x="360" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.with(sort).limit(n)</text>

  <rect x="500" y="20" width="120" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">mongoTemplate.find</text>

  <line x1="220" y1="42" x2="255" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cq)"/>
  <line x1="460" y1="42" x2="495" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#cq)"/>
  <defs><marker id="cq" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Criteria` builds the condition tree; `Query` wraps it with shaping options; `MongoTemplate` executes the assembled query.

## 5. Runnable example

The scenario: a dynamic order search, evolving from a single-condition `Criteria`, to composed multi-condition criteria wrapped in a `Query` with sorting, to a fully dynamic search builder skipping absent optional filters — deliberately mirroring the R2DBC `Criteria` card's structure, adapted to documents.

### Level 1 — Basic

Model a single `Criteria`-style condition and apply it via a simulated `Query`/`MongoTemplate` pair.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for org.springframework.data.mongodb.core.query.Criteria
class Criteria {
    private final Predicate<Order> predicate;
    Criteria(Predicate<Order> predicate) { this.predicate = predicate; }
    static Criteria where(String field) { throw new UnsupportedOperationException("use statusIs/totalGte helpers below"); }
    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGte(double min) { return new Criteria(o -> o.total >= min); }
    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

class Query {
    final Criteria criteria;
    Query(Criteria criteria) { this.criteria = criteria; }
    static Query query(Criteria criteria) { return new Query(criteria); }
}

class MongoTemplate {
    List<Order> find(Query query, List<Order> collection) {
        return collection.stream().filter(query.criteria.asPredicate()).collect(Collectors.toList());
    }
}

public class CriteriaQueryLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(new Order("1", "SHIPPED", 50), new Order("2", "PENDING", 150));
        MongoTemplate mongoTemplate = new MongoTemplate();

        Query query = Query.query(Criteria.statusIs("SHIPPED")); // Query.query(Criteria.where("status").is("SHIPPED"))
        List<Order> found = mongoTemplate.find(query, orders);
        System.out.println("Found: " + found.size() + " matching order(s)");
    }
}
```

How to run: `java CriteriaQueryLevel1.java`

`Query.query(Criteria.statusIs("SHIPPED"))` wraps a single condition into an executable query object, and `mongoTemplate.find(query, ...)` applies it — standing in exactly for `mongoTemplate.find(Query.query(Criteria.where("status").is("SHIPPED")), Order.class)` in a real Spring Data MongoDB application.

### Level 2 — Intermediate

Compose two conditions with `.and()` and add sorting to the `Query`.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class Criteria {
    private final Predicate<Order> predicate;
    Criteria(Predicate<Order> predicate) { this.predicate = predicate; }
    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGte(double min) { return new Criteria(o -> o.total >= min); }
    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

class Query {
    final Criteria criteria;
    Comparator<Order> sort = null;
    Query(Criteria criteria) { this.criteria = criteria; }
    static Query query(Criteria criteria) { return new Query(criteria); }
    Query withSortByTotalDescending() { this.sort = Comparator.comparingDouble((Order o) -> o.total).reversed(); return this; }
}

class MongoTemplate {
    List<Order> find(Query query, List<Order> collection) {
        var stream = collection.stream().filter(query.criteria.asPredicate());
        if (query.sort != null) stream = stream.sorted(query.sort);
        return stream.collect(Collectors.toList());
    }
}

public class CriteriaQueryLevel2 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50), new Order("2", "SHIPPED", 300), new Order("3", "SHIPPED", 150)
        );
        MongoTemplate mongoTemplate = new MongoTemplate();

        // Query.query(Criteria.where("status").is("SHIPPED").and("total").gte(100.0)).with(Sort.by("total").descending())
        Query query = Query.query(Criteria.statusIs("SHIPPED").and(Criteria.totalGte(100.0))).withSortByTotalDescending();
        List<Order> found = mongoTemplate.find(query, orders);

        for (Order o : found) System.out.println("Order " + o.id + ": total=" + o.total);
    }
}
```

How to run: `java CriteriaQueryLevel2.java`

Two conditions compose via `.and()` (status is `SHIPPED` and total is at least `100.0`), filtering out order 1 (`total=50`), and the query's sort orders the remaining two descending by total — order 2 (`300`) prints before order 3 (`150`), matching how `Query.with(Sort.by(...))` shapes the result ordering alongside the filter.

### Level 3 — Advanced

Build a fully dynamic search that skips absent optional filters — the same optional-filter pattern from the R2DBC `Criteria` card, now for MongoDB documents.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class Criteria {
    private final Predicate<Order> predicate;
    Criteria(Predicate<Order> predicate) { this.predicate = predicate; }
    static Criteria empty() { return new Criteria(o -> true); }
    static Criteria statusIs(String status) { return new Criteria(o -> o.status.equals(status)); }
    static Criteria totalGte(double min) { return new Criteria(o -> o.total >= min); }
    Criteria and(Criteria other) { return new Criteria(o -> this.predicate.test(o) && other.predicate.test(o)); }
    Predicate<Order> asPredicate() { return predicate; }
}

class Query {
    final Criteria criteria;
    Query(Criteria criteria) { this.criteria = criteria; }
    static Query query(Criteria criteria) { return new Query(criteria); }
}

class MongoTemplate {
    List<Order> find(Query query, List<Order> collection) {
        return collection.stream().filter(query.criteria.asPredicate()).collect(Collectors.toList());
    }
}

public class CriteriaQueryLevel3 {
    // Builds Criteria dynamically, one .and() per SUPPLIED filter, skipping absent (null) ones.
    static Criteria buildSearchCriteria(String status, Double minTotal) {
        Criteria criteria = Criteria.empty();
        if (status != null) criteria = criteria.and(Criteria.statusIs(status));
        if (minTotal != null) criteria = criteria.and(Criteria.totalGte(minTotal));
        return criteria;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50), new Order("2", "SHIPPED", 300), new Order("3", "PENDING", 150)
        );
        MongoTemplate mongoTemplate = new MongoTemplate();

        // Search form: only "status" filled in.
        Query statusOnly = Query.query(buildSearchCriteria("SHIPPED", null));
        System.out.println("Status only: " + mongoTemplate.find(statusOnly, orders).size() + " order(s)");

        // Search form: both fields filled in.
        Query both = Query.query(buildSearchCriteria("SHIPPED", 100.0));
        System.out.println("Both filters: " + mongoTemplate.find(both, orders).size() + " order(s)");

        // Search form: nothing filled in.
        Query none = Query.query(buildSearchCriteria(null, null));
        System.out.println("No filters: " + mongoTemplate.find(none, orders).size() + " order(s)");
    }
}
```

How to run: `java CriteriaQueryLevel3.java`

`buildSearchCriteria` starts from `Criteria.empty()` and conditionally `.and()`s in each supplied filter — `statusOnly` matches the two `SHIPPED` orders, `both` narrows to just order 2, and `none` matches all three orders, exactly the same dynamic-filter pattern demonstrated for R2DBC's `Criteria` API, now applied to MongoDB documents through `Query`/`MongoTemplate`.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `buildSearchCriteria("SHIPPED", null)` runs: `criteria` starts as `Criteria.empty()`; since `status` is non-null, it becomes `empty.and(statusIs("SHIPPED"))`; since `minTotal` is `null`, the second condition is skipped. `Query.query(...)` wraps this, and `mongoTemplate.find(statusOnly, orders)` filters all three orders through it, matching orders 1 and 2 (both `SHIPPED`) and excluding order 3 (`PENDING`) — printed as "Status only: 2 order(s)".

Next, `buildSearchCriteria("SHIPPED", 100.0)` runs with both filters supplied, producing `empty.and(statusIs("SHIPPED")).and(totalGte(100.0))`. Filtering the same three orders, only order 2 (`SHIPPED`, `total=300`) satisfies both conditions — order 1 fails the total check (`50 < 100.0`) — printed as "Both filters: 1 order(s)".

Finally, `buildSearchCriteria(null, null)` runs with neither filter supplied: `criteria` remains exactly `Criteria.empty()`, matching all three orders unconditionally — printed as "No filters: 3 order(s)".

```
buildSearchCriteria("SHIPPED", null):    empty.and(status==SHIPPED)                    -> [order1, order2]
buildSearchCriteria("SHIPPED", 100.0):   empty.and(status==SHIPPED).and(total>=100.0)   -> [order2]
buildSearchCriteria(null, null):         empty (no conditions)                           -> [order1, order2, order3]
```

In a real Spring Data MongoDB application, `buildSearchCriteria` would return a genuine `org.springframework.data.mongodb.core.query.Criteria` object, and the calling code would wrap it in `Query.query(criteria)` before passing it to `mongoTemplate.find(query, Order.class)` (or `reactiveMongoTemplate.find(query, Order.class)` for the reactive variant) — MongoDB receives a single, dynamically-assembled filter document reflecting exactly the non-null search-form fields, with all the conditional logic living in how the Java `Criteria` object was constructed rather than in the query executed against the database.

## 7. Gotchas & takeaways

> Gotcha: `Criteria`'s `.orOperator(...)` takes an explicit list of criteria to OR together, structurally different from `.and()`'s chained style — mixing up the two composition styles (e.g., expecting `.or()` to chain the same way `.and()` does) is a common source of subtly wrong dynamic queries.

- `Criteria`/`Query` are Spring Data MongoDB's fluent, composable query-building API, filling the same role as R2DBC's `Criteria` and JPA's `Specification` for their respective modules.
- `Criteria` conditions compose via `.and()`/`.orOperator()` into a tree; `Query` wraps that tree together with sorting, paging, and other query-shaping options.
- The standard optional-filter pattern is identical across every Spring Data module covered in this series: start from an identity/empty criteria, conditionally `.and()` in only the filters actually supplied.
- Reach for `Criteria`/`Query` when conditions vary at runtime; reach for `@Query` JSON strings when the condition is fixed but needs an operator a derived method can't express.
