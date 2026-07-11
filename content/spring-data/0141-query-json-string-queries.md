---
card: spring-data
gi: 141
slug: query-json-string-queries
title: "@Query (JSON) & string queries"
---

## 1. What it is

`@Query` on a repository method lets you write Elasticsearch's native JSON query DSL directly, with `?0`, `?1` substitution markers bound to method parameters — the Elasticsearch-specific counterpart to the `@Query` annotation seen for JPQL (relational) and JSON criteria (MongoDB) in earlier sections. It's the escape hatch for queries too elaborate for `Criteria` or a derived method name to express cleanly.

```java
interface OrderRepository extends ElasticsearchRepository<Order, String> {
    @Query("""
        { "bool": { "must": [
            { "term":  { "status": "?0" } },
            { "range": { "total": { "gte": ?1 } } }
        ]}}
        """)
    List<Order> findByStatusAndMinTotal(String status, double minTotal);
}
```

## 2. Why & when

`Criteria` (the previous card) covers most everyday needs, but Elasticsearch's full query DSL includes constructs — `function_score` for custom relevance boosting, `nested` queries against nested objects, `more_like_this` for similarity search — that don't have a fluent `Criteria` equivalent, or where writing the raw JSON is simply clearer than composing it through a builder API.

Reach for `@Query` with raw JSON when:

- You need an Elasticsearch query feature `Criteria` doesn't expose a fluent method for — a specialized query type, a boosting function, or fine-grained control over how `bool` clauses (`must`/`should`/`filter`/`must_not`) are structured.
- You're translating a query you've already prototyped and tuned directly against Elasticsearch (via its REST API or Kibana's Dev Tools) into your application, and want to keep it as close to that verified, working JSON as possible.
- The query is complex enough that a fluent `Criteria` chain would be harder to read than the equivalent JSON — readability, not just capability, is a valid reason to reach for this.

## 3. Core concept

```
 @Query("""
     { "bool": { "must": [
         { "term":  { "status": "?0" } },
         { "range": { "total": { "gte": ?1 } } }
     ]}}
     """)
 List<Order> findByStatusAndMinTotal(String status, double minTotal);

 findByStatusAndMinTotal("SHIPPED", 100.0)
        |
        v
 ?0 -> "SHIPPED", ?1 -> 100.0   (positional substitution, by parameter index)
        |
        v
 { "bool": { "must": [
     { "term":  { "status": "SHIPPED" } },
     { "range": { "total": { "gte": 100.0 } } }
 ]}}
```

Substitution markers are substituted positionally, by parameter index — `?0` is always the method's first parameter, `?1` the second, and so on, regardless of parameter name.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Method call arguments are substituted positionally into substitution markers inside the raw JSON query string">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">findByX("SHIPPED", 100.0)</text>

  <rect x="330" y="20" width="290" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">?0 -&gt; "SHIPPED", ?1 -&gt; 100.0</text>

  <line x1="280" y1="42" x2="325" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="80" y="90" width="480" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="117" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">{ "term": {"status":"SHIPPED"}}, {"range": {"total": {"gte": 100.0}}}</text>
  <line x1="475" y1="65" x2="380" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Parameters are substituted purely by position — the method's argument order must match the substitution marker order in the JSON.

## 5. Runnable example

The scenario: a raw-JSON `@Query` method for filtering orders, evolving from basic positional marker substitution, to a query with multiple conditions combined, to a query with a conditionally-included clause — showing where a hand-built string query starts needing the same care `Criteria`'s conditional building required.

### Level 1 — Basic

Model positional marker substitution into a raw query template.

```java
import java.util.*;

public class QueryJsonLevel1 {
    public static void main(String[] args) {
        // Mirrors @Query("{ \"term\": { \"status\": \"?0\" } }") List<Order> findByStatusRaw(String status);
        String template = "{ \"term\": { \"status\": \"?0\" } }";

        String resolved = substituteMarkers(template, "SHIPPED");
        System.out.println("Resolved query: " + resolved);
    }

    // Mirrors how Spring Data Elasticsearch resolves ?0, ?1, ... against the method's actual argument values.
    static String substituteMarkers(String template, Object... args) {
        String result = template;
        for (int i = 0; i < args.length; i++) {
            result = result.replace("?" + i, String.valueOf(args[i]));
        }
        return result;
    }
}
```

How to run: `java QueryJsonLevel1.java`

`substituteMarkers` mirrors exactly what Spring Data Elasticsearch does when resolving a `@Query` annotation's substitution markers: `?0` is replaced by the method's first argument (`"SHIPPED"`), by simple positional index, with no name matching involved at all.

### Level 2 — Intermediate

Substitute multiple substitution markers in a query with combined conditions, matching the intro snippet's `findByStatusAndMinTotal`.

```java
import java.util.*;

public class QueryJsonLevel2 {
    public static void main(String[] args) {
        String template = """
            { "bool": { "must": [
                { "term":  { "status": "?0" } },
                { "range": { "total": { "gte": ?1 } } }
            ]}}
            """;

        String resolved = substituteMarkers(template, "SHIPPED", 100.0);
        System.out.println("Resolved query:\n" + resolved);
    }

    static String substituteMarkers(String template, Object... args) {
        String result = template;
        for (int i = 0; i < args.length; i++) {
            result = result.replace("?" + i, String.valueOf(args[i]));
        }
        return result;
    }
}
```

How to run: `java QueryJsonLevel2.java`

Both `?0` and `?1` are substituted from the method call's two arguments, in order — `status="SHIPPED"` becomes `?0`'s replacement, `minTotal=100.0` becomes `?1`'s. Note that `?1` is *not* quoted in the template (`"gte": ?1`, not `"gte": "?1"`), because `total` is a numeric field — quoting it would send Elasticsearch a string where it expects a number, causing a type error at query time.

### Level 3 — Advanced

Show why a raw-string `@Query` struggles with the same conditional-filter problem `Criteria` solved cleanly in the previous card — and the common workaround of accepting a `null`-safe wildcard rather than truly omitting a clause.

```java
import java.util.*;

public class QueryJsonLevel3 {
    public static void main(String[] args) {
        // Mirrors a @Query method where "status" is OPTIONAL -- a naive template can't just OMIT the clause.
        String template = """
            { "bool": { "must": [
                { "term":  { "status": "?0" } },
                { "range": { "total": { "gte": ?1 } } }
            ]}}
            """;

        // Workaround: pass a wildcard that matches ANY status when the caller didn't provide a real filter.
        String noStatusFilter = resolveWithOptionalStatus(template, null, 100.0);
        System.out.println("No status filter provided:\n" + noStatusFilter);

        String withStatusFilter = resolveWithOptionalStatus(template, "SHIPPED", 100.0);
        System.out.println("Status filter provided:\n" + withStatusFilter);
    }

    // A raw JSON template CANNOT skip a clause the way a dynamically-built Criteria object can (previous card) --
    // the common workaround is substituting a value that matches everything, e.g. "*" for a wildcard query.
    static String resolveWithOptionalStatus(String template, String status, double minTotal) {
        String effectiveStatus = (status != null) ? status : "*"; // "*" as a wildcard term is a common, imperfect workaround
        return template.replace("?0", effectiveStatus).replace("?1", String.valueOf(minTotal));
    }
}
```

How to run: `java QueryJsonLevel3.java`

Because the JSON template's structure is fixed text, it can't conditionally omit the `status` clause the way `Criteria.where(...)` could skip adding a condition entirely — the workaround shown here substitutes a wildcard value (`"*"`) so the clause is always present but effectively matches anything when no real filter value was given. This is a real limitation of string-based `@Query`: expressing "this clause is optional" cleanly usually means switching to `Criteria`, a `NativeQuery` built with conditional Java logic (the next card), or restructuring the query itself — a plain positional-substitution template doesn't have a native way to omit a clause.

## 6. Walkthrough

Execution starts in `main` for Level 3. `resolveWithOptionalStatus(template, null, 100.0)` is called first. Inside, `status` is `null`, so `effectiveStatus` is set to `"*"`. `template.replace("?0", "*")` substitutes the wildcard into the `status` term clause, and `.replace("?1", "100.0")` substitutes the numeric threshold. The result still contains a `status` term clause — just one matching `"*"` rather than a specific value.

`resolveWithOptionalStatus(template, "SHIPPED", 100.0)` is called second, with a real status value. `effectiveStatus` is set to `"SHIPPED"` directly, and the same substitution produces a query with a genuine, specific `status` filter.

```
No status filter provided:
{ "bool": { "must": [
    { "term":  { "status": "*" } },
    { "range": { "total": { "gte": 100.0 } } }
]}}

Status filter provided:
{ "bool": { "must": [
    { "term":  { "status": "SHIPPED" } },
    { "range": { "total": { "gte": 100.0 } } }
]}}
```

In practice, a `"*"` wildcard against a `term` query (which targets an exact, unanalyzed value) doesn't actually behave as a true "match anything" the way this simplified example implies — `term` queries generally don't support wildcard matching at all; achieving genuinely optional clauses in real Elasticsearch usually means using a `wildcard` query type specifically, restructuring the query to omit the clause via a conditionally-built `NativeQuery` (the next card lets you build a query object with real Java conditionals), or falling back to `Criteria`'s clean conditional composition from the previous card — which is precisely why `@Query`'s fixed-template nature is best suited to queries whose structure doesn't need to vary at runtime.

## 7. Gotchas & takeaways

> Gotcha: substitution markers are purely positional (`?0`, `?1`, ...) — reordering a method's parameters without updating the `@Query` string's substitution marker numbers silently substitutes the wrong values into the wrong places, with no compile-time check catching the mismatch.

> Gotcha: string values must be explicitly quoted in the template (`"?0"`) while numeric values must not be (`?1`, unquoted) — getting this wrong sends Elasticsearch a JSON type it doesn't expect for that field (a string where a number was mapped, or vice versa), producing a runtime query error rather than a silent wrong answer, but only once the query actually executes.

- `@Query` with raw JSON is the escape hatch for Elasticsearch query features `Criteria` doesn't expose fluently, or for keeping a query close to JSON already prototyped and verified outside the application.
- Substitution markers (`?0`, `?1`, ...) substitute positionally from method arguments — quoting matters and must match each field's actual mapped type (string vs. numeric).
- A fixed JSON template can't conditionally omit a clause the way a dynamically-built `Criteria` object can — queries whose structure genuinely varies at runtime are usually better expressed with `Criteria` or a conditionally-built `NativeQuery`.
- Reach for `@Query` when the query's shape is fixed and known ahead of time; reach for `Criteria` or `NativeQuery` when the shape needs to vary based on runtime conditions.
