---
card: spring-data
gi: 142
slug: native-queries-nativequery
title: "Native queries (NativeQuery)"
---

## 1. What it is

`NativeQuery` builds an Elasticsearch query programmatically using Spring Data Elasticsearch's Java client wrapper types, rather than either a fluent `Criteria` chain or a raw JSON string — it's the option that gives full access to Elasticsearch's entire query DSL (anything `Criteria` doesn't cover) while still being ordinary, type-checked Java code (unlike `@Query`'s fixed string template).

```java
NativeQuery query = NativeQuery.builder()
    .withQuery(q -> q.bool(b -> b
        .must(m -> m.term(t -> t.field("status").value("SHIPPED")))
        .must(m -> m.range(r -> r.field("total").gte(JsonData.of(100.0))))))
    .build();

SearchHits<Order> hits = elasticsearchOperations.search(query, Order.class);
```

## 2. Why & when

The previous two cards each had a real limitation: `Criteria` doesn't expose every Elasticsearch query type fluently, and `@Query`'s raw JSON template is fixed text that can't easily express "this clause only appears under some runtime condition" (as the previous card's Level 3 demonstrated with its imperfect wildcard workaround). `NativeQuery` resolves both: it's built with real Java — conditionals, loops, helper methods — while still expressing any query construct Elasticsearch's full DSL supports, because it's a structured object model, not a template string.

Reach for `NativeQuery` when:

- You need an Elasticsearch query feature that `Criteria` doesn't have a fluent method for, but the query's *structure* genuinely needs to vary at runtime — the exact combination `@Query`'s fixed template couldn't handle cleanly.
- You want compile-time type checking on your query construction, rather than string concatenation or template placeholders that only fail at runtime if something doesn't line up.
- You're building a query with a genuinely complex or deeply nested structure (aggregations combined with filters combined with sorting, for instance) where a builder API keeps things more manageable than either alternative.

## 3. Core concept

```
 Criteria             -- fluent Java API, covers common cases, doesn't expose every DSL feature
 @Query (raw JSON)     -- covers everything, but FIXED TEXT -- can't easily vary its structure at runtime
 NativeQuery            -- covers everything AND is regular Java -- conditionals, loops, full type safety

 NativeQuery.builder()
     .withQuery(q -> q.bool(b -> {
         var builder = b.must(...);
         if (optionalCondition) builder = builder.must(...);  // a REAL Java if-statement, not a template hack
         return builder;
     }))
     .build();
```

`NativeQuery` sits at the intersection of `Criteria`'s type safety and `@Query`'s full expressive power — genuine Java code building a genuine full-DSL query object.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three approaches trade off expressiveness and flexibility differently: Criteria, raw-JSON Query, and NativeQuery">
  <rect x="20" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Criteria</text>
  <text x="110" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fluent, limited coverage</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@Query (raw JSON)</text>
  <text x="320" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">full coverage, fixed text</text>

  <rect x="440" y="20" width="180" height="55" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">NativeQuery</text>
  <text x="530" y="58" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">full coverage AND type-safe Java</text>

  <text x="320" y="115" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">NativeQuery trades a bit of verbosity for combining both other options' strengths</text>
</svg>

Each approach trades expressiveness against flexibility differently; `NativeQuery` gives up some conciseness for both full coverage and real code.

## 5. Runnable example

The scenario: a search combining an exact filter, a text match, and conditional clauses, evolving from a basic `NativeQuery`-style builder, to a query built with real Java conditionals for optional filters (fixing the previous card's workaround), to nesting a sub-query inside a builder for a more elaborate structure.

### Level 1 — Basic

Model a basic `NativeQuery`-style builder combining a term filter and a range filter.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class NativeQueryLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50.0),
            new Order("2", "SHIPPED", 150.0),
            new Order("3", "PENDING", 200.0)
        );

        Predicate<Order> query = new NativeQueryBuilder()
            .term("status", "SHIPPED")
            .rangeGte("total", 100.0)
            .build();

        List<Order> results = orders.stream().filter(query).collect(Collectors.toList());
        System.out.println("SHIPPED and total >= 100: " + results.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for org.springframework.data.elasticsearch.client.elc.NativeQuery's builder.
class NativeQueryBuilder {
    private final List<Predicate<Order>> mustClauses = new ArrayList<>();
    NativeQueryBuilder term(String field, String value) { mustClauses.add(o -> fieldStr(o, field).equals(value)); return this; }
    NativeQueryBuilder rangeGte(String field, double min) { mustClauses.add(o -> fieldNum(o, field) >= min); return this; }
    Predicate<Order> build() { return o -> mustClauses.stream().allMatch(c -> c.test(o)); }

    private static String fieldStr(Order o, String field) { return field.equals("status") ? o.status : ""; }
    private static double fieldNum(Order o, String field) { return field.equals("total") ? o.total : 0; }
}
```

How to run: `java NativeQueryLevel1.java`

`NativeQueryBuilder` accumulates clauses via genuine method calls, matching `NativeQuery.builder().withQuery(q -> q.bool(b -> b.must(...).must(...)))`'s structural shape. `build()` produces the final combined predicate — order `2` (`SHIPPED`, `total=150`) satisfies both clauses; orders `1` and `3` each fail one.

### Level 2 — Intermediate

Add optional clauses using real Java conditionals — fixing the previous card's limitation where a fixed JSON template couldn't cleanly omit a clause.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class NativeQueryLevel2 {
    // A REAL if-statement decides whether to add a clause -- no wildcard workaround needed, unlike the raw-JSON @Query card.
    static Predicate<Order> buildQuery(SearchForm form) {
        NativeQueryBuilder builder = new NativeQueryBuilder();
        if (form.status != null) builder.term("status", form.status);
        if (form.minTotal != null) builder.rangeGte("total", form.minTotal);
        return builder.build();
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50.0),
            new Order("2", "SHIPPED", 150.0),
            new Order("3", "PENDING", 200.0)
        );

        SearchForm onlyStatus = new SearchForm(); onlyStatus.status = "SHIPPED";
        System.out.println("Only status filter: " +
            orders.stream().filter(buildQuery(onlyStatus)).map(o -> o.id).collect(Collectors.toList()));

        SearchForm onlyMinTotal = new SearchForm(); onlyMinTotal.minTotal = 100.0;
        System.out.println("Only minTotal filter: " +
            orders.stream().filter(buildQuery(onlyMinTotal)).map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class SearchForm { String status; Double minTotal; }

 // both optional

class NativeQueryBuilder {
    private final List<Predicate<Order>> mustClauses = new ArrayList<>();
    NativeQueryBuilder term(String field, String value) { mustClauses.add(o -> o.status.equals(value)); return this; }
    NativeQueryBuilder rangeGte(String field, double min) { mustClauses.add(o -> o.total >= min); return this; }
    Predicate<Order> build() { return o -> mustClauses.stream().allMatch(c -> c.test(o)); }
}
```

How to run: `java NativeQueryLevel2.java`

`buildQuery` adds a clause to the builder only when the corresponding `SearchForm` field is non-null — a genuine `if` statement, not a wildcard substitution hack. This is precisely the flexibility `NativeQuery` offers that a raw `@Query` string template struggles with: the *set* of clauses in the final query, not just their values, can vary based on runtime conditions.

### Level 3 — Advanced

Nest a sub-condition inside the builder — an OR group within an overall AND query — matching how real `NativeQuery` builders let you compose `bool` queries with nested `should` clauses inside a `must` clause.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class NativeQueryLevel3 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", "Electronics", 50.0),
            new Order("2", "SHIPPED", "Books", 150.0),
            new Order("3", "SHIPPED", "Furniture", 200.0),
            new Order("4", "PENDING", "Electronics", 300.0)
        );

        // status = SHIPPED  AND  total >= 100  AND  category IN (Electronics, Books) -- a nested OR inside the outer AND
        Predicate<Order> query = new NativeQueryBuilder()
            .term("status", "SHIPPED")
            .rangeGte(100.0)
            .shouldAnyOf("category", List.of("Electronics", "Books"))
            .build();

        List<Order> results = orders.stream().filter(query).collect(Collectors.toList());
        System.out.println("SHIPPED, total>=100, category IN (Electronics, Books): "
            + results.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String category; double total; Order(String id, String status, String category, double total) { this.id = id; this.status = status; this.category = category; this.total = total; } }

class NativeQueryBuilder {
    private final List<Predicate<Order>> mustClauses = new ArrayList<>();
    NativeQueryBuilder term(String field, String value) { mustClauses.add(o -> o.status.equals(value)); return this; }
    NativeQueryBuilder rangeGte(double min) { mustClauses.add(o -> o.total >= min); return this; }

    // A nested OR group: matches if ANY of the given category values match -- itself one clause within the outer AND.
    NativeQueryBuilder shouldAnyOf(String field, List<String> values) {
        mustClauses.add(o -> values.stream().anyMatch(v -> v.equals(o.category)));
        return this;
    }

    Predicate<Order> build() { return o -> mustClauses.stream().allMatch(c -> c.test(o)); }
}
```

How to run: `java NativeQueryLevel3.java`

`shouldAnyOf` adds one clause to the outer AND (`mustClauses`) that itself succeeds if *any* of several category values match — a nested OR group living inside an overall AND, exactly mirroring a `bool` query's `must` clause containing a nested `bool` query with a `should` list. Order `1` (`SHIPPED`, `total=50`) fails the total check; order `2` (`SHIPPED`, `total=150`, `Books`) passes all three; order `3` (`SHIPPED`, `total=200`, `Furniture`) fails the category check since `"Furniture"` isn't in the allowed list; order `4` fails the status check.

## 6. Walkthrough

Execution starts in `main` for Level 3. The `NativeQueryBuilder` is built up with three clauses: `term("status", "SHIPPED")`, `rangeGte(100.0)`, and `shouldAnyOf("category", List.of("Electronics", "Books"))`. `build()` combines all three into one predicate requiring every clause to hold.

For order `1` (`SHIPPED`, `Electronics`, `total=50.0`): the status clause passes (`"SHIPPED".equals("SHIPPED")`), but the range clause fails (`50.0 >= 100.0` is `false`) — since `mustClauses.stream().allMatch(...)` short-circuits on the first failing predicate, order `1` is excluded regardless of its category.

For order `2` (`SHIPPED`, `Books`, `total=150.0`): the status clause passes, the range clause passes (`150.0 >= 100.0`), and the `shouldAnyOf` clause checks whether `"Books"` appears in `["Electronics", "Books"]` — it does, so this clause passes too. All three hold, so order `2` is included.

For order `3` (`SHIPPED`, `Furniture`, `total=200.0`): status and range both pass, but `shouldAnyOf` checks whether `"Furniture"` appears in `["Electronics", "Books"]` — it doesn't, so this clause fails, and order `3` is excluded.

For order `4` (`PENDING`, `Electronics`, `total=300.0`): the status clause fails immediately (`"PENDING".equals("SHIPPED")` is `false`), excluding it regardless of the rest.

```
SHIPPED, total>=100, category IN (Electronics, Books): [2]
```

In real Spring Data Elasticsearch, this nested structure is expressed as `q.bool(b -> b.must(m -> m.term(t -> t.field("status").value("SHIPPED"))).must(m -> m.range(r -> r.field("total").gte(JsonData.of(100.0)))).must(m -> m.bool(inner -> inner.should(s -> s.term(t -> t.field("category").value("Electronics"))).should(s -> s.term(t -> t.field("category").value("Books"))))))` — an outer `bool` query's `must` clauses combined with a nested `bool` query (itself using `should` for the OR semantics) as one of those `must` clauses, exactly the AND-containing-an-OR structure this example models in plain Java.

## 7. Gotchas & takeaways

> Gotcha: `should` clauses inside a `bool` query behave differently depending on whether the `bool` query also has `must`/`filter` clauses — with at least one `must`/`filter` present, `should` clauses become optional (contributing to relevance score but not required to match), whereas in a `bool` query with *only* `should` clauses, at least one must match by default. This example's `shouldAnyOf` models the "required OR group" version by placing it inside the outer AND explicitly — get this nesting wrong in a real query and clauses you intended as required become merely score-boosting, or vice versa.

> Gotcha: `NativeQuery` gives you full DSL access, which also means full responsibility for getting Elasticsearch's `bool` query semantics right — unlike `Criteria`'s guardrails, there's nothing stopping you from building a structurally valid but logically incorrect query (like accidentally putting a required filter inside a `should` clause where it becomes optional).

- `NativeQuery` builds Elasticsearch's full query DSL programmatically in Java, combining `Criteria`'s type safety with `@Query`'s complete feature coverage.
- Because it's real Java code, it supports conditionals and loops for building queries whose structure — not just whose values — needs to vary at runtime, which a fixed `@Query` template struggles with.
- Nested `bool` queries (an OR group living inside an overall AND, or vice versa) are how compound conditions with mixed logic are expressed.
- With full DSL access comes full responsibility for `bool` query semantics — `must`/`filter`/`should`/`must_not` each behave differently, and getting the nesting wrong produces a structurally valid but logically incorrect query.
