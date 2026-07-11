---
card: spring-data
gi: 135
slug: elasticsearchoperations-elasticsearchtemplate
title: "ElasticsearchOperations / ElasticsearchTemplate"
---

## 1. What it is

`ElasticsearchOperations` is Spring Data Elasticsearch's central, blocking API for indexing and searching documents in Elasticsearch — a search engine built around inverted indexes and relevance scoring, rather than tables or BSON documents. `ElasticsearchTemplate` is its default implementation, playing the same architectural role `MongoTemplate` played for MongoDB or `JdbcAggregateTemplate` played for JDBC: the low-level entry point every generated repository ultimately delegates to.

```java
@Autowired ElasticsearchOperations operations;

Order order = operations.get("1", Order.class);
SearchHits<Order> hits = operations.search(
    Query.of(q -> q.match(m -> m.field("status").query("SHIPPED"))), Order.class);
```

## 2. Why & when

This card opens the final Spring Data section covered here: Spring Data Elasticsearch, backing a fundamentally different storage model than any covered so far. MongoDB matches documents by structural queries; a relational database matches rows by exact predicates and joins; Elasticsearch matches documents by **relevance** — it tokenizes text into an inverted index and ranks results by how well they match a query, which is what makes full-text search, fuzzy matching, and "did you mean" behavior possible in a way SQL's `LIKE` or MongoDB's regex queries were never designed for.

Reach for `ElasticsearchOperations` directly when:

- You need index-level or search-level control a generated repository method can't express — building a query programmatically, running a search with custom relevance tuning, or working with raw `SearchHits` metadata (score, highlighting, aggregations) alongside the results.
- You're implementing a custom repository fragment (the same `<Repository>Impl` pattern seen in earlier Spring Data modules) for a search operation too dynamic for a derived query method.
- You want the same operation to work whether it's invoked through a hand-written service or a generated `ElasticsearchRepository` (the next card) — both ultimately call through this one API.

## 3. Core concept

```
 interface OrderRepository extends ElasticsearchRepository<Order, String> { }
   -- generated implementation is a thin wrapper delegating to:

 ElasticsearchOperations.get(id, Order.class)                        -- fetch by id
 ElasticsearchOperations.search(query, Order.class)                   -- relevance-ranked search, returns SearchHits<T>
 ElasticsearchOperations.save(order)                                  -- index (write) a document

 orderRepository.findById(id)  ==  operations.get(id, Order.class)   (same operation, different entry point)
```

Exactly like the relational and document-store templates in earlier sections, generated repositories are a convenience layer built entirely on top of this one operations interface.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generated ElasticsearchRepository and a custom implementation both delegate to the same underlying ElasticsearchOperations">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.search(...)</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: operations.search(...)</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">ElasticsearchOperations</text>

  <line x1="150" y1="65" x2="290" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the generated repository and a hand-written custom fragment ultimately delegate to the same underlying operations interface.

## 5. Runnable example

The scenario: indexing and searching product-order documents by relevance, evolving from basic index/get operations, to a relevance-ranked text search over a `status`/`description` field, to a custom repository fragment combining both concepts for a search no generated method expresses.

### Level 1 — Basic

Model `ElasticsearchOperations`'s basic index/get operations against an in-memory stand-in for Elasticsearch.

```java
import java.util.*;

public class EsOperationsLevel1 {
    public static void main(String[] args) {
        ElasticsearchOperations operations = new ElasticsearchOperations();

        operations.save(new Order("1", "SHIPPED", "Wireless mouse, shipped via express courier"));
        operations.save(new Order("2", "PENDING", "Office chair, awaiting warehouse pickup"));

        Order found = operations.get("1");
        System.out.println("Found by id: status=" + found.status + ", description=" + found.description);
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

// Stands in for org.springframework.data.elasticsearch.core.ElasticsearchOperations.
class ElasticsearchOperations {
    private final Map<String, Order> index = new HashMap<>();

    String save(Order order) { index.put(order.id, order); return order.id; } // indexes (writes) the document
    Order get(String id) { return index.get(id); }                            // fetch by id, no relevance involved
}
```

How to run: `java EsOperationsLevel1.java`

`save` mirrors indexing a document into Elasticsearch — writing it so it becomes both retrievable by id and searchable by its field contents. `get` is a direct, non-relevance id lookup, exactly like `findById` on any other Spring Data repository — Elasticsearch's real value only shows up once you search by content rather than by exact id, which the next level demonstrates.

### Level 2 — Intermediate

Model a relevance-ranked text search: documents are scored by how well their content matches the query, and results come back ordered by that score — the behavior that sets Elasticsearch apart from an exact-match `find`.

```java
import java.util.*;
import java.util.stream.*;

public class EsOperationsLevel2 {
    public static void main(String[] args) {
        ElasticsearchOperations operations = new ElasticsearchOperations();
        operations.save(new Order("1", "SHIPPED", "Wireless mouse, shipped via express courier"));
        operations.save(new Order("2", "PENDING", "Wireless keyboard, awaiting warehouse pickup"));
        operations.save(new Order("3", "SHIPPED", "Office chair, express delivery requested"));

        List<SearchHit> hits = operations.search("wireless express");
        System.out.println("Search results, ranked by relevance:");
        for (SearchHit hit : hits) System.out.println("  " + hit.order.id + " (score=" + hit.score + "): " + hit.order.description);
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class SearchHit { Order order; double score; SearchHit(Order order, double score) { this.order = order; this.score = score; } }

class ElasticsearchOperations {
    private final Map<String, Order> index = new HashMap<>();
    String save(Order order) { index.put(order.id, order); return order.id; }
    Order get(String id) { return index.get(id); }

    // Simplified relevance scoring: count how many query terms appear in the description, case-insensitively.
    List<SearchHit> search(String queryText) {
        String[] terms = queryText.toLowerCase().split("\\s+");
        List<SearchHit> hits = new ArrayList<>();
        for (Order order : index.values()) {
            String haystack = order.description.toLowerCase();
            long matchingTerms = Arrays.stream(terms).filter(haystack::contains).count();
            if (matchingTerms > 0) hits.add(new SearchHit(order, (double) matchingTerms / terms.length));
        }
        hits.sort((a, b) -> Double.compare(b.score, a.score)); // HIGHEST relevance first
        return hits;
    }
}
```

How to run: `java EsOperationsLevel2.java`

`search` scores each document by the fraction of query terms it contains, standing in for Elasticsearch's real relevance scoring (which uses far more sophisticated term-frequency/inverse-document-frequency math, but the *shape* of the behavior — more matching, more relevant terms score higher — is the same). Order `1` matches both `"wireless"` and `"express"` and scores highest; orders `2` and `3` each match only one term and tie below it — results come back sorted by relevance, not insertion order or id.

### Level 3 — Advanced

Build a custom repository fragment using `ElasticsearchOperations` directly for a search no generated `ElasticsearchRepository` method expresses: filtering by exact `status` *and* ranking by text relevance together, in one call.

```java
import java.util.*;
import java.util.stream.*;

public class EsOperationsLevel3 {
    public static void main(String[] args) {
        ElasticsearchOperations operations = new ElasticsearchOperations();
        operations.save(new Order("1", "SHIPPED", "Wireless mouse, shipped via express courier"));
        operations.save(new Order("2", "PENDING", "Wireless keyboard, awaiting warehouse pickup")); // matches text, WRONG status
        operations.save(new Order("3", "SHIPPED", "Office chair, express delivery requested"));

        OrderRepositoryCustom repo = new OrderRepositoryImpl(operations);
        List<SearchHit> results = repo.searchShippedByRelevance("wireless express");

        System.out.println("Shipped orders matching 'wireless express', by relevance:");
        for (SearchHit hit : results) System.out.println("  " + hit.order.id + " (score=" + hit.score + "): " + hit.order.description);
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class SearchHit { Order order; double score; SearchHit(Order order, double score) { this.order = order; this.score = score; } }

class ElasticsearchOperations {
    Map<String, Order> index = new HashMap<>();
    String save(Order order) { index.put(order.id, order); return order.id; }

    List<SearchHit> search(String queryText, String statusFilter) {
        String[] terms = queryText.toLowerCase().split("\\s+");
        List<SearchHit> hits = new ArrayList<>();
        for (Order order : index.values()) {
            if (statusFilter != null && !order.status.equals(statusFilter)) continue; // exact FILTER, not scored
            String haystack = order.description.toLowerCase();
            long matchingTerms = Arrays.stream(terms).filter(haystack::contains).count();
            if (matchingTerms > 0) hits.add(new SearchHit(order, (double) matchingTerms / terms.length));
        }
        hits.sort((a, b) -> Double.compare(b.score, a.score));
        return hits;
    }
}

// interface OrderRepositoryCustom { List<SearchHit> searchShippedByRelevance(String text); }
interface OrderRepositoryCustom { List<SearchHit> searchShippedByRelevance(String text); }

class OrderRepositoryImpl implements OrderRepositoryCustom {
    private final ElasticsearchOperations operations;
    OrderRepositoryImpl(ElasticsearchOperations operations) { this.operations = operations; }

    // No generated ElasticsearchRepository method expresses "filter by exact status AND rank by text relevance" together.
    public List<SearchHit> searchShippedByRelevance(String text) {
        return operations.search(text, "SHIPPED");
    }
}
```

How to run: `java EsOperationsLevel3.java`

`searchShippedByRelevance` combines an exact filter (`status = "SHIPPED"`) with relevance-ranked text search in a single custom method built directly on `ElasticsearchOperations` — order `2` matches the search text well but is excluded entirely for having the wrong status, something a plain relevance search (Level 2) alone couldn't express, and something a generated repository method's fixed naming convention also can't easily combine with free-text relevance ranking.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are saved, including order `2`, which matches the search text (`"wireless"`) well but has `status = "PENDING"` rather than `"SHIPPED"`.

`repo.searchShippedByRelevance("wireless express")` calls `operations.search("wireless express", "SHIPPED")`. Inside `search`, the loop iterates every indexed order. For order `1` (`SHIPPED`), the `statusFilter` check passes, and its description matches both `"wireless"` and `"express"`, giving it a score of `1.0`. For order `2` (`PENDING`), the check `!order.status.equals(statusFilter)` is `true` (its status doesn't match `"SHIPPED"`), so `continue` skips it entirely — it never even gets scored, regardless of how well its text matches. For order `3` (`SHIPPED`), the filter passes, and its description matches only `"express"` (not `"wireless"`), giving it a score of `0.5`.

The two surviving hits (orders `1` and `3`) are sorted by score, descending, and returned. The final loop prints them.

```
Shipped orders matching 'wireless express', by relevance:
  1 (score=1.0): Wireless mouse, shipped via express courier
  3 (score=0.5): Office chair, express delivery requested
```

In real Spring Data Elasticsearch, this combined filter-plus-relevance query would be built with a `Query` object combining a `bool` query's `must` (or `filter`) clause for the exact `status` match with a `match` clause for the free-text relevance search, executed via `operations.search(query, Order.class)` — the same underlying method a generated `ElasticsearchRepository`'s derived query methods use, but composed here by hand for a combination no single derived method name can express as naturally.

## 7. Gotchas & takeaways

> Gotcha: `ElasticsearchOperations.get(id, Type.class)` is an exact id lookup, unrelated to relevance scoring — don't confuse it with `search`, which tokenizes and ranks. Reaching for `get` when you actually want fuzzy/relevance matching (or vice versa) produces confusing, seemingly "wrong" results that are actually both working exactly as designed.

> Gotcha: unlike MongoDB's `MongoTemplate` or JDBC's templates, indexing a document into Elasticsearch isn't instantly reflected in search results by default — Elasticsearch refreshes its search index periodically (roughly once per second by default), so a document saved and immediately searched for might not appear yet unless you explicitly wait for a refresh (relevant for tests especially).

- `ElasticsearchOperations` (implemented by `ElasticsearchTemplate`) is the low-level API every `ElasticsearchRepository` (the next card) is built on, exactly like `MongoTemplate` or `JdbcAggregateTemplate` played that role for their respective modules.
- `get`/`save` are exact, non-scored id-based operations; `search` is Elasticsearch's core value proposition — relevance-ranked matching over document content.
- Custom repository fragments injecting `ElasticsearchOperations` directly are the way to express searches (combined filters plus relevance ranking, for instance) that a generated repository's derived-method naming convention can't capture cleanly.
- Elasticsearch's search index refreshes on an interval, not instantly on write — a just-indexed document may not appear in search results immediately.
