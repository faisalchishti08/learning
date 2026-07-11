---
card: spring-data
gi: 137
slug: elasticsearchrepository
title: "ElasticsearchRepository"
---

## 1. What it is

`ElasticsearchRepository<T, ID>` is the generated-implementation repository interface for Elasticsearch, following the exact same pattern as `JpaRepository`, `MongoRepository`, and `ReactiveCrudRepository` from earlier sections: extend it, and Spring Data generates `save`/`findById`/`delete`/`findAll` plus derived query methods from method names, all backed by `ElasticsearchOperations` underneath.

```java
interface OrderRepository extends ElasticsearchRepository<Order, String> {
    List<Order> findByStatus(String status);
    List<Order> findByDescriptionContaining(String keyword);
}
```

## 2. Why & when

Earlier cards in this section used `ElasticsearchOperations` directly, which is powerful but requires building query objects by hand for every search. `ElasticsearchRepository` brings the same convenience already familiar from every other Spring Data module: derived query methods generated from a method's name, without writing a single query object — while still supporting `@Query` (a later card) and custom implementations for anything a derived method name can't express.

Reach for `ElasticsearchRepository` when:

- You want standard CRUD plus simple derived searches (`findByStatus`, `findByDescriptionContaining`) without hand-building `Query` objects for every method — the same convenience `JpaRepository`/`MongoRepository` provide for their respective stores.
- Your team is already comfortable with the Spring Data repository pattern from other modules and wants the same programming model applied to Elasticsearch.
- You want repository method names to double as self-documenting queries — `findByStatusAndDescriptionContaining(status, keyword)` reads as exactly what it does.

## 3. Core concept

```
 interface OrderRepository extends ElasticsearchRepository<Order, String> {
     List<Order> findByStatus(String status);
     List<Order> findByDescriptionContaining(String keyword);
 }

 orderRepository.findByStatus("SHIPPED")
        |
        v
 generates: term query on "status" field, exact match  (status fields are typically NOT analyzed)

 orderRepository.findByDescriptionContaining("mouse")
        |
        v
 generates: match query on "description" field, ANALYZED, relevance-scored  (this IS full-text search)
```

The same derived-method-name mechanism from JPA/MongoDB repositories applies here, but the *underlying query type* it generates differs by field: exact term matching for keyword-like fields, analyzed relevance matching for full-text fields.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two derived query methods generate different underlying Elasticsearch query types depending on the field they target">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus("SHIPPED")</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByDescriptionContaining("x")</text>

  <rect x="20" y="100" width="260" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="150" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">term query -- exact match</text>

  <rect x="360" y="100" width="260" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="490" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">match query -- relevance ranked</text>

  <line x1="150" y1="65" x2="150" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="490" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same method-name-to-query mechanism as other Spring Data modules, producing exact-match or relevance-ranked queries depending on the targeted field.

## 5. Runnable example

The scenario: a generated `OrderRepository`, evolving from a basic derived `findByStatus` (exact match), to `findByDescriptionContaining` (relevance-ranked text search), to combining both in one derived method — mirroring `findByStatusAndDescriptionContaining`.

### Level 1 — Basic

Model a derived `findByStatus` method: exact-match filtering, generated from the method name.

```java
import java.util.*;
import java.util.stream.*;

public class EsRepositoryLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "SHIPPED", "Wireless mouse"));
        repo.save(new Order("2", "PENDING", "Wireless keyboard"));
        repo.save(new Order("3", "SHIPPED", "Office chair"));

        List<Order> shipped = repo.findByStatus("SHIPPED");
        System.out.println("Shipped orders: " + shipped.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

// Stands in for a generated implementation of: interface OrderRepository extends ElasticsearchRepository<Order, String> { findByStatus(...) }
class OrderRepository {
    private final Map<String, Order> index = new HashMap<>();
    void save(Order order) { index.put(order.id, order); }

    // Derived from the method name "findByStatus" -- generates an EXACT term match on the status field.
    List<Order> findByStatus(String status) {
        return index.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }
}
```

How to run: `java EsRepositoryLevel1.java`

`findByStatus` is derived purely from the method name — Spring Data would generate a term query on the `status` field from this signature alone, with no query body written by hand. `status` fields are typically mapped as `keyword` type in Elasticsearch (not analyzed into tokens), which is exactly why this is an exact match rather than a relevance search.

### Level 2 — Intermediate

Add `findByDescriptionContaining`: a derived method targeting a full-text field, matching Elasticsearch's analyzed, relevance-scored search rather than an exact comparison.

```java
import java.util.*;
import java.util.stream.*;

public class EsRepositoryLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "SHIPPED", "Wireless mouse, ergonomic design"));
        repo.save(new Order("2", "PENDING", "Wireless keyboard, mechanical switches"));
        repo.save(new Order("3", "SHIPPED", "Office chair, adjustable height"));

        List<Order> wirelessMatches = repo.findByDescriptionContaining("wireless");
        System.out.println("Descriptions containing 'wireless': " + wirelessMatches.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class OrderRepository {
    private final Map<String, Order> index = new HashMap<>();
    void save(Order order) { index.put(order.id, order); }

    List<Order> findByStatus(String status) {
        return index.values().stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    // Derived from "findByDescriptionContaining" -- generates a MATCH query: analyzed, case-insensitive, relevance-scored.
    List<Order> findByDescriptionContaining(String keyword) {
        String needle = keyword.toLowerCase();
        return index.values().stream()
            .filter(o -> o.description.toLowerCase().contains(needle))
            .collect(Collectors.toList());
    }
}
```

How to run: `java EsRepositoryLevel2.java`

`findByDescriptionContaining` searches within free text, case-insensitively — matching Elasticsearch's `match` query behavior against an analyzed `text`-type field, in contrast to `findByStatus`'s exact `keyword`-type comparison. Both are derived purely from their method names, but Spring Data Elasticsearch generates a structurally different query for each, based on which field type each targets.

### Level 3 — Advanced

Combine both into `findByStatusAndDescriptionContaining`, matching Spring Data's compound derived-method naming convention — an exact filter and a relevance-ranked text match in one generated method.

```java
import java.util.*;
import java.util.stream.*;

public class EsRepositoryLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "SHIPPED", "Wireless mouse, ergonomic design"));
        repo.save(new Order("2", "PENDING", "Wireless keyboard, mechanical switches")); // matches text, WRONG status
        repo.save(new Order("3", "SHIPPED", "Office chair, adjustable height"));         // matches status, WRONG text

        List<Order> results = repo.findByStatusAndDescriptionContaining("SHIPPED", "wireless");
        System.out.println("Shipped AND containing 'wireless': " + results.stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class OrderRepository {
    private final Map<String, Order> index = new HashMap<>();
    void save(Order order) { index.put(order.id, order); }

    // Derived from "findByStatusAndDescriptionContaining" -- combines an EXACT filter with an ANALYZED text match.
    List<Order> findByStatusAndDescriptionContaining(String status, String keyword) {
        String needle = keyword.toLowerCase();
        return index.values().stream()
            .filter(o -> o.status.equals(status))                      // exact term match, like findByStatus
            .filter(o -> o.description.toLowerCase().contains(needle)) // analyzed match, like findByDescriptionContaining
            .collect(Collectors.toList());
    }
}
```

How to run: `java EsRepositoryLevel3.java`

`findByStatusAndDescriptionContaining` applies both filters in sequence: order `2` matches the text but has the wrong status, so it's excluded by the first `filter`; order `3` matches the status but not the text, so it's excluded by the second. Only order `1`, satisfying both conditions, survives — the compound method name `And`-joins an exact term condition with an analyzed text condition, exactly matching Spring Data's general derived-query naming rules already seen for JPA and MongoDB repositories.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are saved: order `2` has matching text (`"wireless"` in its description) but the wrong status (`PENDING`); order `3` has matching status (`SHIPPED`) but the wrong text.

`repo.findByStatusAndDescriptionContaining("SHIPPED", "wireless")` runs `index.values().stream()` through two chained `filter` calls. The first filter, `o.status.equals("SHIPPED")`, keeps orders `1` and `3` (both `SHIPPED`) and drops order `2` (`PENDING`). The second filter, checking whether the lowercased description contains `"wireless"`, is applied only to the orders that survived the first filter: order `1`'s description contains `"wireless"` and passes; order `3`'s description (`"Office chair, adjustable height"`) does not, and it's dropped.

Only order `1` survives both filters and is collected into `results`.

```
Shipped AND containing 'wireless': [1]
```

In real Spring Data Elasticsearch, this method name generates a `bool` query combining a `term` (or `match`) clause on `status` inside a `filter` context (exact, not scored) with a `match` clause on `description` inside a `must` context (analyzed, contributing to relevance score) — Elasticsearch's `bool` query is precisely what lets exact filtering and relevance-scored matching compose within a single query, which is what makes this compound derived method possible at all.

## 7. Gotchas & takeaways

> Gotcha: whether a field supports exact (`findByX`) versus analyzed (`findByXContaining`) matching depends entirely on how that field is mapped — a `status` field mapped as `text` instead of `keyword` would actually get tokenized and support fuzzy matching too, and a `description` field mapped as `keyword` would require an exact full-string match instead of substring search. The mapping (the next card, "Document mapping") determines what a derived method can actually do, not just the method name.

> Gotcha: `findByDescriptionContaining` and similar "Containing"/"Like" derived methods on Elasticsearch repositories are not simple substring checks the way this example's simplified Java model implements them — a real Elasticsearch `match` query analyzes the query text into tokens the same way the indexed field was analyzed, so results can include documents where the words appear in a different order, are stemmed differently, or are otherwise not a literal substring match.

- `ElasticsearchRepository<T, ID>` extends the same generated-implementation pattern as every other Spring Data repository, producing CRUD plus derived query methods from interface method names.
- Which Elasticsearch query type a derived method generates (exact `term` vs. analyzed `match`) depends on the mapped type of the field it targets, not just the method name's own wording.
- Compound derived methods (`findByXAndYContaining`) combine exact filtering with relevance-scored text matching in a single generated `bool` query.
- Field mapping (covered next) governs what kind of matching is even possible on a given field — get the mapping right before relying on a derived method's behavior.
