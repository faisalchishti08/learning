---
card: spring-data
gi: 104
slug: derived-query-json-queries
title: "Derived & @Query (JSON) queries"
---

## 1. What it is

This card deepens the `@Query` introduction from the `MongoRepository` card: MongoDB's JSON query syntax supports the full range of MongoDB query operators (`$gt`, `$in`, `$regex`, `$exists`, nested-field dot notation, array-element matching) inside a `@Query` string, giving `@Query` methods access to far more expressive conditions than derived method names can practically encode, while derived methods remain the right choice for simple, common conditions.

```java
interface OrderRepository extends MongoRepository<Order, String> {
    List<Order> findByStatus(String status); // derived: simple equality

    @Query("{ 'total': { $gte: ?0, $lte: ?1 } }")
    List<Order> findByTotalBetween(double min, double max); // JSON operators: range condition

    @Query("{ 'tags': { $in: ?0 } }")
    List<Order> findByAnyTag(List<String> tags); // JSON operators: array membership
}
```

## 2. Why & when

The derived-query-naming convention (shared across every Spring Data module in this series) handles simple, common conditions well — equality, comparison, basic combinations with `And`/`Or`. MongoDB's query language, though, has operators with no clean derived-method-name equivalent at all: `$in` (value is one of several), `$regex` (pattern matching), `$exists` (field is present/absent), and deeply nested document/array queries. `@Query` with MongoDB's JSON syntax is where those live.

Reach for `@Query` with MongoDB operators specifically when:

- A condition needs an operator with no derived-method vocabulary — array membership (`$in`), regex matching (`$regex`), field presence (`$exists`), or a range expressed with both bounds in one condition.
- You're querying nested documents or arrays with MongoDB's dot notation (`"address.city"`) or array-element operators (`$elemMatch`) — these read far more naturally as JSON than as an English-like method name.
- A derived method name would become unreasonably long or ambiguous trying to express a condition MongoDB's query language expresses concisely.

## 3. Core concept

```
 Derived (simple, common conditions):
   findByStatus(status)                    -> { status: ?0 }
   findByStatusAndTotalGreaterThan(s, t)     -> { status: ?0, total: { $gt: ?1 } }

 @Query (MongoDB operators, no derived equivalent):
   @Query("{ 'total': { $gte: ?0, $lte: ?1 } }")       -- range with both bounds
   @Query("{ 'tags': { $in: ?0 } }")                    -- array membership
   @Query("{ 'notes': { $regex: ?0 } }")                 -- pattern matching
   @Query("{ 'discountCode': { $exists: true } }")        -- field presence check
```

Simple conditions stay derived for readability; anything needing a genuine MongoDB operator moves to `@Query`.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Simple conditions use derived method names while operator-heavy conditions use at-Query JSON syntax">
  <rect x="20" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Derived methods</text>
  <text x="35" y="65" fill="#8b949e" font-size="8.5" font-family="sans-serif">findByStatus(status)</text>
  <text x="35" y="83" fill="#8b949e" font-size="8.5" font-family="sans-serif">findByStatusAndTotalGreaterThan</text>
  <text x="35" y="101" fill="#8b949e" font-size="8" font-family="sans-serif">-- simple, common conditions</text>

  <rect x="350" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Query (JSON)</text>
  <text x="365" y="65" fill="#8b949e" font-size="8.5" font-family="monospace">{ tags: { $in: ?0 } }</text>
  <text x="365" y="83" fill="#8b949e" font-size="8.5" font-family="monospace">{ notes: { $regex: ?0 } }</text>
  <text x="365" y="101" fill="#8b949e" font-size="8" font-family="sans-serif">-- MongoDB operators, no derived form</text>
</svg>

Simple conditions stay readable as derived method names; operator-rich conditions are clearer and more direct as JSON.

## 5. Runnable example

The scenario: querying orders with increasingly operator-rich conditions, evolving from a plain derived-query baseline, to a range condition using `$gte`/`$lte`, to array-membership and regex conditions combined.

### Level 1 — Basic

Model the derived-query baseline for simple equality, as a point of comparison.

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

public class JsonQueryLevel1 {
    // findByStatus(String status) -- derived
    static List<Order> findByStatus(List<Order> collection, String status) {
        return collection.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(new Order("1", "SHIPPED", 50), new Order("2", "PENDING", 150));
        List<Order> shipped = findByStatus(orders, "SHIPPED");
        System.out.println("Derived query result: " + shipped.size() + " shipped order(s)");
    }
}
```

How to run: `java JsonQueryLevel1.java`

Plain equality is the sweet spot for a derived method name — clear, short, and self-documenting; no `@Query` is needed here.

### Level 2 — Intermediate

Add a range condition using `$gte`/`$lte` via `@Query`, a condition awkward to express as a derived method name (`findByTotalGreaterThanEqualAndTotalLessThanEqual` is technically valid but unwieldy).

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

public class JsonQueryLevel2 {
    // @Query("{ 'total': { $gte: ?0, $lte: ?1 } }")
    static List<Order> findByTotalBetween(List<Order> collection, double min, double max) {
        System.out.println("  MongoDB query: { total: { $gte: " + min + ", $lte: " + max + " } }");
        return collection.stream().filter(o -> o.total >= min && o.total <= max).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50), new Order("2", "SHIPPED", 150), new Order("3", "PENDING", 300)
        );
        List<Order> midRange = findByTotalBetween(orders, 100.0, 200.0);
        System.out.println("In range [100, 200]: " + midRange.size() + " order(s)");
    }
}
```

How to run: `java JsonQueryLevel2.java`

The `$gte`/`$lte` combination reads clearly as JSON — `{ total: { $gte: 100.0, $lte: 200.0 } }` — versus the equivalent derived method name, which would be both longer and less immediately obvious about which bound is inclusive.

### Level 3 — Advanced

Combine array-membership (`$in`) and pattern-matching (`$regex`) conditions in one `@Query`, a shape with no reasonable derived-method equivalent at all.

```java
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

class Order { String id; String status; List<String> tags; String notes; Order(String id, String status, List<String> tags, String notes) { this.id = id; this.status = status; this.tags = tags; this.notes = notes; } }

public class JsonQueryLevel3 {
    // @Query("{ 'tags': { $in: ?0 }, 'notes': { $regex: ?1 } }")
    static List<Order> findByAnyTagAndNotesMatching(List<Order> collection, List<String> tags, String regexPattern) {
        System.out.println("  MongoDB query: { tags: { $in: " + tags + " }, notes: { $regex: '" + regexPattern + "' } }");
        Pattern pattern = Pattern.compile(regexPattern);
        return collection.stream()
            .filter(o -> o.tags.stream().anyMatch(tags::contains)) // $in: at least one tag matches
            .filter(o -> pattern.matcher(o.notes).find())            // $regex: notes match the pattern
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", List.of("gift", "fragile"), "Handle with care, urgent delivery"),
            new Order("2", "SHIPPED", List.of("bulk"), "Standard delivery, no rush"),
            new Order("3", "PENDING", List.of("gift"), "Urgent gift wrap requested")
        );

        List<Order> result = findByAnyTagAndNotesMatching(orders, List.of("gift", "fragile"), "(?i)urgent");
        System.out.println("Matching orders: " + result.size());
        for (Order o : result) System.out.println("  " + o.id + ": tags=" + o.tags + ", notes=\"" + o.notes + "\"");
    }
}
```

How to run: `java JsonQueryLevel3.java`

`{ tags: { $in: [gift, fragile] }, notes: { $regex: '(?i)urgent' } }` combines an array-membership check with a case-insensitive pattern match — no derived method name could reasonably express "any of these tags AND notes matching this pattern" this concisely; order 1 matches both conditions (has `"fragile"` tag, notes contain "urgent"), order 3 matches both (has `"gift"` tag, notes contain "Urgent"), while order 2 fails both conditions.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, three orders are built with varying tags and notes text.

`findByAnyTagAndNotesMatching(orders, List.of("gift", "fragile"), "(?i)urgent")` runs. The simulated MongoDB query is printed first, showing both operators together. Then `Pattern.compile("(?i)urgent")` compiles a case-insensitive regex matching the word "urgent" anywhere in a string.

The first filter, `o.tags.stream().anyMatch(tags::contains)`, checks each order's tags against the requested list `["gift", "fragile"]`: order 1 has tags `["gift", "fragile"]` — both match, so `anyMatch` is `true`; order 2 has only `["bulk"]` — no match, `anyMatch` is `false`, so order 2 is filtered out immediately and never reaches the regex check; order 3 has `["gift"]` — matches, `anyMatch` is `true`.

The second filter, `pattern.matcher(o.notes).find()`, then runs only on the surviving orders (1 and 3). Order 1's notes, "Handle with care, urgent delivery", contain "urgent" — the pattern matches. Order 3's notes, "Urgent gift wrap requested", contain "Urgent" — the case-insensitive pattern also matches (thanks to the `(?i)` flag).

Both orders 1 and 3 survive both filters, producing a final result of 2 matching orders, printed with their tags and notes.

```
findByAnyTagAndNotesMatching(tags=[gift,fragile], pattern="(?i)urgent"):
  order1: tags=[gift,fragile] -> $in MATCH; notes contain "urgent" -> $regex MATCH -> INCLUDED
  order2: tags=[bulk]          -> $in NO MATCH -> excluded (regex never checked)
  order3: tags=[gift]           -> $in MATCH; notes contain "Urgent" -> $regex MATCH (case-insensitive) -> INCLUDED
  result: [order1, order3]
```

In a real Spring Data MongoDB application, `@Query("{ 'tags': { $in: ?0 }, 'notes': { $regex: ?1 } }")` sends exactly that filter document to MongoDB's `find` command — MongoDB's query engine evaluates both conditions server-side (using any relevant index on `tags` if one exists, though `$regex` conditions generally can't use an index efficiently unless anchored at the start of the string), returning only matching documents, which Spring Data MongoDB maps back into `Order` objects — the same two-condition logic this simulated example implements with Java streams, just executed inside the database instead of in application memory.

## 7. Gotchas & takeaways

> Gotcha: an unanchored `$regex` condition (like `"(?i)urgent"`, matching "urgent" anywhere in the string) generally cannot use an index efficiently even if one exists on that field — MongoDB typically has to examine the full text of every candidate document; an anchored pattern (starting with `^`) can sometimes use an index, but general substring matching is inherently a scan-heavy operation regardless of database.

- Derived method names remain the right choice for simple, common conditions (equality, basic comparisons) — clear and self-documenting.
- `@Query` with MongoDB's JSON syntax is for conditions needing operators with no derived-method equivalent: `$in` (membership), `$regex` (pattern matching), `$exists` (field presence), range conditions with both bounds, and nested-document/array queries.
- Both query styles coexist naturally on the same repository interface, chosen per-method based on which condition is actually needed.
- Unanchored regex conditions are inherently expensive (can't efficiently use most indexes) — be mindful of this cost on large collections, regardless of how concise the `@Query` syntax makes them look.
