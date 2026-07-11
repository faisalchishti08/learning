---
card: spring-data
gi: 140
slug: criteria-criteriaquery
title: "Criteria & CriteriaQuery"
---

## 1. What it is

`Criteria` is Spring Data Elasticsearch's fluent, type-safe API for building queries in Java — combining conditions with `.and()`/`.or()`, without writing raw Elasticsearch JSON query syntax by hand. Wrapped in a `CriteriaQuery`, it's passed to `elasticsearchOperations.search(...)`, playing a similar programmatic-query role to `Criteria`/`Query` objects from the earlier MongoDB cards.

```java
Criteria criteria = Criteria.where("status").is("SHIPPED")
    .and(Criteria.where("description").contains("wireless"));

SearchHits<Order> hits = elasticsearchOperations.search(new CriteriaQuery(criteria), Order.class);
```

## 2. Why & when

Derived query methods (the earlier `ElasticsearchRepository` card) cover fixed, known-in-advance queries well, but they can't express a query whose shape depends on runtime conditions — "filter by status only if the user provided one, and by a date range only if both dates were given." `Criteria` fills that gap: it's built with regular Java code, so branching, loops, and conditionals can shape the final query naturally.

Reach for `Criteria`/`CriteriaQuery` when:

- The exact combination of filters isn't known until runtime — a search form where several fields are optional, and only the ones the user actually filled in should constrain the query.
- You want a type-safe, fluent Java API rather than hand-writing Elasticsearch's JSON query DSL as a string (the `@Query` card, next, covers that string-based alternative).
- You're building a query incrementally across several methods or conditions, accumulating `Criteria` objects with `.and()`/`.or()` as you go.

## 3. Core concept

```
 Criteria.where("status").is("SHIPPED")
      .and(Criteria.where("description").contains("wireless"))

      ~=  (a Java object graph, built with regular code)

 translates to Elasticsearch's bool query:
   { "bool": { "must": [
       { "term":  { "status": "SHIPPED" } },
       { "match": { "description": "wireless" } }
   ]}}
```

`Criteria` is a Java-side builder; `CriteriaQuery` wraps it into something `elasticsearchOperations.search(...)` can execute — the translation into Elasticsearch's actual JSON query syntax happens automatically underneath.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Chained Criteria conditions combine into one CriteriaQuery, which is executed as a search">
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">where("status").is(...)</text>

  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">.and(where("desc")...)</text>

  <line x1="200" y1="40" x2="225" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <rect x="460" y="20" width="150" height="40" rx="6" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CriteriaQuery</text>
  <line x1="410" y1="40" x2="455" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <rect x="380" y="100" width="230" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="495" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">operations.search(query, Order.class)</text>
  <line x1="535" y1="60" x2="495" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Fluent chaining in Java builds up the query object incrementally, which is only translated and executed at `search()` time.

## 5. Runnable example

The scenario: a search form with several optional filters, evolving from a basic `Criteria`-style AND condition, to combining `.and()`/`.or()` for a more expressive query, to building the query conditionally at runtime based on which filters were actually provided — the actual value `Criteria` has over a fixed derived query method.

### Level 1 — Basic

Model a basic two-condition `Criteria` combined with `.and()`.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class CriteriaLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", "Wireless mouse"),
            new Order("2", "PENDING", "Wireless keyboard"),
            new Order("3", "SHIPPED", "Office chair")
        );

        Criteria criteria = Criteria.where("status").is("status", "SHIPPED")
            .and(Criteria.where("description").contains("description", "wireless"));

        List<Order> matches = orders.stream().filter(criteria::matches).collect(Collectors.toList());
        System.out.println("Matches (SHIPPED and contains 'wireless'): " + matches.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

// Stands in for org.springframework.data.elasticsearch.core.query.Criteria.
class Criteria {
    private final List<Predicate<Order>> conditions = new ArrayList<>();

    static Criteria where(String field) { return new Criteria(); } // simplified: condition built via is()/contains() below

    Criteria is(String field, String value) { conditions.add(o -> fieldValue(o, field).equals(value)); return this; }
    Criteria contains(String field, String substring) { conditions.add(o -> fieldValue(o, field).toLowerCase().contains(substring.toLowerCase())); return this; }
    Criteria and(Criteria other) { conditions.addAll(other.conditions); return this; }

    private static String fieldValue(Order o, String field) { return field.equals("status") ? o.status : o.description; }
    boolean matches(Order o) { return conditions.stream().allMatch(c -> c.test(o)); }
}
```

How to run: `java CriteriaLevel1.java`

`Criteria` accumulates `Predicate<Order>` conditions as methods are chained, mirroring how the real `Criteria` class builds up an internal representation that later translates into Elasticsearch's `bool` query. `matches` (standing in for what happens at search time) checks that *every* accumulated condition holds — an AND combination — exactly like `.and(...)` chaining in the real API.

### Level 2 — Intermediate

Add `.or()`, combining two independent condition groups where matching *either* is sufficient.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class CriteriaLevel2 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", "Wireless mouse"),
            new Order("2", "PENDING", "Wireless keyboard"),
            new Order("3", "DELIVERED", "Office chair"),
            new Order("4", "CANCELLED", "Desk lamp")
        );

        // status is SHIPPED OR status is DELIVERED -- either satisfies the query.
        Criteria criteria = Criteria.where("status").is("status", "SHIPPED")
            .or(Criteria.where("status").is("status", "DELIVERED"));

        List<Order> matches = orders.stream().filter(criteria::matches).collect(Collectors.toList());
        System.out.println("Matches (SHIPPED or DELIVERED): " + matches.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class Criteria {
    private final List<List<Predicate<Order>>> orGroups = new ArrayList<>(); // OUTER list = OR groups, inner = AND within a group
    Criteria() { orGroups.add(new ArrayList<>()); }

    static Criteria where(String field) { return new Criteria(); }

    Criteria is(String field, String value) { orGroups.get(orGroups.size() - 1).add(o -> fieldValue(o, field).equals(value)); return this; }
    Criteria contains(String field, String substring) { orGroups.get(orGroups.size() - 1).add(o -> fieldValue(o, field).toLowerCase().contains(substring.toLowerCase())); return this; }
    Criteria and(Criteria other) { orGroups.get(orGroups.size() - 1).addAll(other.orGroups.get(0)); return this; }
    Criteria or(Criteria other) { orGroups.addAll(other.orGroups); return this; } // adds a NEW alternative group

    private static String fieldValue(Order o, String field) { return field.equals("status") ? o.status : o.description; }
    boolean matches(Order o) { return orGroups.stream().anyMatch(group -> group.stream().allMatch(c -> c.test(o))); }
}
```

How to run: `java CriteriaLevel2.java`

`orGroups` is a list of AND-groups, where matching *any one* group is sufficient — `.and()` adds to the current group, `.or()` starts a fresh alternative group. Orders `1` (`SHIPPED`) and `3` (`DELIVERED`) both satisfy at least one group, while orders `2` (`PENDING`) and `4` (`CANCELLED`) satisfy neither — exactly the semantics `Criteria.where(...).is(...).or(Criteria.where(...).is(...))` expresses in real Spring Data Elasticsearch.

### Level 3 — Advanced

Build the query conditionally at runtime, adding filters only for the parameters a caller actually provided — the real advantage `Criteria` has over a fixed derived query method, which can't skip a condition based on whether an argument was supplied.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

 // ALL fields optional -- may be null

public class CriteriaLevel3 {
    // Mirrors building a Criteria object incrementally, adding a condition ONLY when the corresponding form field was provided.
    static Predicate<Order> buildCriteria(SearchForm form) {
        List<Predicate<Order>> conditions = new ArrayList<>();
        if (form.status != null) conditions.add(o -> o.status.equals(form.status));
        if (form.descriptionKeyword != null) conditions.add(o -> o.description.toLowerCase().contains(form.descriptionKeyword.toLowerCase()));
        if (form.minTotal != null) conditions.add(o -> o.total >= form.minTotal);
        return o -> conditions.stream().allMatch(c -> c.test(o)); // AND of only the conditions that were actually built
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", "Wireless mouse", 25.0),
            new Order("2", "PENDING", "Wireless keyboard", 60.0),
            new Order("3", "SHIPPED", "Office chair", 150.0)
        );

        SearchForm onlyStatusProvided = new SearchForm();
        onlyStatusProvided.status = "SHIPPED"; // description and minTotal left null -- NOT filtered on

        List<Order> result1 = orders.stream().filter(buildCriteria(onlyStatusProvided)).collect(Collectors.toList());
        System.out.println("Only status='SHIPPED' provided: " + result1.stream().map(o -> o.id).collect(Collectors.toList()));

        SearchForm statusAndMinTotal = new SearchForm();
        statusAndMinTotal.status = "SHIPPED";
        statusAndMinTotal.minTotal = 100.0;

        List<Order> result2 = orders.stream().filter(buildCriteria(statusAndMinTotal)).collect(Collectors.toList());
        System.out.println("status='SHIPPED' and minTotal=100: " + result2.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; double total; Order(String id, String status, String description, double total) { this.id = id; this.status = status; this.description = description; this.total = total; } }

class SearchForm { String status; String descriptionKeyword; Double minTotal; }
```

How to run: `java CriteriaLevel3.java`

`buildCriteria` only adds a condition for each `SearchForm` field that's actually non-null — a form with only `status` set produces a query filtering on status alone; a form with `status` and `minTotal` both set produces a query filtering on both. This is precisely what a fixed derived query method (`findByStatus`, or even `findByStatusAndMinTotal`) can't do on its own: it can't skip a parameter at call time the way a dynamically built `Criteria` object can.

## 6. Walkthrough

Execution starts in `main` for Level 3. `onlyStatusProvided` has `status = "SHIPPED"` set, with `descriptionKeyword` and `minTotal` left `null` (Java's default for object fields).

`buildCriteria(onlyStatusProvided)` checks each field: `form.status != null` is `true`, so a status-equality condition is added; `form.descriptionKeyword != null` is `false`, so no description condition is added at all; `form.minTotal != null` is `false`, so no total condition is added either. The returned predicate only checks the one condition that was actually built. Filtering `orders` with it keeps orders `1` and `3` (both `SHIPPED`), regardless of their description or total.

`statusAndMinTotal` has both `status = "SHIPPED"` and `minTotal = 100.0` set. `buildCriteria` this time adds two conditions: status equality and `total >= 100.0`. Filtering `orders` with this predicate requires both conditions to hold — order `1` (`total = 25.0`) fails the total check even though its status matches, and order `3` (`total = 150.0`) satisfies both, so only order `3` survives.

```
Only status='SHIPPED' provided: [1, 3]
status='SHIPPED' and minTotal=100: [3]
```

In real Spring Data Elasticsearch, the equivalent code builds an actual `Criteria` object conditionally: `Criteria criteria = Criteria.where("status").is(form.status); if (form.descriptionKeyword != null) criteria = criteria.and(Criteria.where("description").contains(form.descriptionKeyword)); if (form.minTotal != null) criteria = criteria.and(Criteria.where("total").greaterThanEqual(form.minTotal));` — the resulting `CriteriaQuery`, when executed, contains only the `bool` clauses that were actually added, exactly matching this example's behavior of skipping unset filters entirely rather than treating them as some default value.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check for `null` before adding a `Criteria` condition (adding `Criteria.where("status").is(form.status)` unconditionally when `form.status` might be `null`) typically produces a query that matches nothing, or errors, rather than "no filter on this field" — always guard optional filter conditions explicitly, as this example's `if (form.status != null)` checks do.

> Gotcha: `Criteria`'s `.and()`/`.or()` combine differently depending on how they're chained — `a.and(b).or(c)` groups differently than `a.and(b.or(c))` in terms of the resulting boolean logic, exactly the same operator-precedence subtlety that applies to `&&`/`||` in plain Java. When mixing `.and()` and `.or()`, be deliberate about grouping, or the generated query may not match the intended logic.

- `Criteria`/`CriteriaQuery` build Elasticsearch queries with a fluent, type-safe Java API, translated automatically into the underlying `bool` query at search time.
- `.and()`/`.or()` combine conditions, matching the same boolean-logic composition seen in the earlier MongoDB `Criteria` card.
- The real advantage over a fixed derived query method is conditional query construction — adding filters at runtime only for the parameters a caller actually provided.
- Be deliberate about how `.and()`/`.or()` chains group, since mixing them without care can produce a query with different boolean logic than intended.
