---
card: system-design
gi: 164
slug: spring-data-elasticsearch
title: Spring Data Elasticsearch
---

## 1. What it is

**Spring Data Elasticsearch** lets a Spring Boot application talk to an Elasticsearch cluster using the same familiar repository pattern as Spring Data JPA — you define an entity class with `@Document`, a repository interface extending `ElasticsearchRepository`, and Spring generates the search queries for you, instead of you hand-writing raw Elasticsearch JSON queries and HTTP calls.

## 2. Why & when

Talking to Elasticsearch's REST API directly means building and parsing JSON query bodies by hand for every search you need — full-text queries, filters, pagination — which is verbose and easy to get wrong. Spring Data Elasticsearch maps this onto the same repository-method-naming conventions Spring Data uses elsewhere (`findByTitleContaining`, `findByPriceLessThan`), and maps your Java objects to and from Elasticsearch documents automatically. Use it in any Spring Boot service that needs full-text search, using [relevance ranking](0161-relevance-ranking-tf-idf-bm25.md) and an [inverted index](0159-inverted-index.md) under the hood, backed by a real Elasticsearch cluster.

## 3. Core concept

- **`@Document(indexName = "...")`:** marks a Java class as mapping to a specific Elasticsearch index (Elasticsearch's equivalent of a database table).
- **`@Field`:** configures how a Java field maps to an Elasticsearch field, including its type (`text` for full-text-searchable, `keyword` for exact-match-only) and which [analyzer](0160-tokenization-stemming-analyzers.md) to apply.
- **`ElasticsearchRepository<T, ID>`:** the base repository interface; extending it and declaring methods like `List<Product> findByNameContaining(String keyword)` gets you a working full-text search method with zero query code written.
- **`ElasticsearchOperations` / `ElasticsearchRestTemplate`:** a lower-level API for building more complex queries (boolean combinations, filters, sorting by relevance score) than the repository method-naming convention alone can express.
- **Automatic index management:** Spring Data Elasticsearch can create the index and its mapping automatically from your `@Document`-annotated class on startup, keeping the Java model and the Elasticsearch mapping in sync.

## 4. Diagram

```
   @Document(indexName = "products")
   class Product {
       @Id String id;
       @Field(type = FieldType.Text) String name;
       @Field(type = FieldType.Keyword) String category;
   }

   interface ProductRepository extends ElasticsearchRepository<Product, String> {
       List<Product> findByNameContaining(String keyword);
   }

   caller -> productRepository.findByNameContaining("laptop")
                |
                v
   Spring Data Elasticsearch builds a match query:
   { "query": { "match": { "name": "laptop" } } }
                |
                v
   sent to Elasticsearch over HTTP -> ranked results mapped back to List<Product>
```
*Caption: a repository method name is translated into a real Elasticsearch query body automatically, and the JSON response is mapped back into Java objects.*

## 5. Runnable example

This models the repository-to-query translation in-process; the "How to run" note shows the real Spring Data Elasticsearch dependency and annotations.

**Level 1 — Basic.** A document class and an in-memory index, modeling `@Document` and index storage.

**Level 2 — Repository-style query method.** A method name like `findByNameContaining` is translated into an actual search over indexed terms.

**Level 3 — Relevance-based result ordering.** Results come back sorted by a match score, the way a real Elasticsearch query would order them.

```java
// SpringDataElasticsearchDemo.java
import java.util.*;
import java.util.stream.*;

public class SpringDataElasticsearchDemo {

    // Level 1: models a @Document-annotated entity.
    static class Product {
        String id, name, category;
        Product(String id, String name, String category) { this.id = id; this.name = name; this.category = category; }
        public String toString() { return name + " (" + category + ")"; }
    }

    // Level 1: models the Elasticsearch index Spring Data Elasticsearch talks to.
    static List<Product> productsIndex = new ArrayList<>();

    // Level 2: models a repository method like "findByNameContaining(String keyword)".
    static List<Product> findByNameContaining(String keyword) {
        String lowerKeyword = keyword.toLowerCase();
        return productsIndex.stream()
            .filter(p -> Arrays.stream(p.name.toLowerCase().split("\\s+")).anyMatch(term -> term.contains(lowerKeyword)))
            .collect(Collectors.toList());
    }

    // Level 3: same search, but scored and sorted by relevance instead of returned in insertion order.
    static List<Product> findByNameContainingRankedByRelevance(String keyword) {
        String lowerKeyword = keyword.toLowerCase();
        return productsIndex.stream()
            .map(p -> Map.entry(p, scoreMatch(p.name.toLowerCase(), lowerKeyword)))
            .filter(entry -> entry.getValue() > 0)
            .sorted((a, b) -> Double.compare(b.getValue(), a.getValue()))
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());
    }

    // A tiny relevance score: exact term match scores higher than a partial (substring) match.
    static double scoreMatch(String name, String keyword) {
        String[] terms = name.split("\\s+");
        double score = 0;
        for (String term : terms) {
            if (term.equals(keyword)) score += 2.0;
            else if (term.contains(keyword)) score += 1.0;
        }
        return score;
    }

    public static void main(String[] args) {
        productsIndex.add(new Product("1", "gaming laptop pro", "electronics"));
        productsIndex.add(new Product("2", "laptop sleeve case", "accessories"));
        productsIndex.add(new Product("3", "laptop", "electronics"));
        productsIndex.add(new Product("4", "wireless mouse", "accessories"));

        System.out.println("findByNameContaining(\"laptop\"): " + findByNameContaining("laptop"));
        System.out.println("relevance-ranked: " + findByNameContainingRankedByRelevance("laptop"));
    }
}
```

**How to run:** save as `SpringDataElasticsearchDemo.java`, then run `java SpringDataElasticsearchDemo.java`. (Real Spring Data Elasticsearch: add `spring-boot-starter-data-elasticsearch`, annotate `Product` with `@Document(indexName = "products")`, extend `ElasticsearchRepository<Product, String>` with `List<Product> findByNameContaining(String keyword)`, and Spring generates and sends the real Elasticsearch `match` query against a running Elasticsearch cluster.)

## 6. Walkthrough

1. Four `Product` objects are added to the in-memory `productsIndex`, modeling documents already indexed into a real Elasticsearch index.
2. `findByNameContaining("laptop")` filters `productsIndex` by checking whether any whitespace-split term in a product's `name` contains `"laptop"`; products 1, 2, and 3 all have a term containing "laptop" ("laptop" itself, in each case), so all three are returned, in their original insertion order — this models the plain repository-method query with no relevance ordering.
3. `findByNameContainingRankedByRelevance("laptop")` instead computes a `scoreMatch` for every product: product 3's single term "laptop" is an *exact* match (`term.equals(keyword)`), scoring `2.0`; product 1's "laptop" term inside "gaming laptop pro" is also an exact term match, scoring `2.0`; product 2's "laptop" inside "laptop sleeve case" is likewise an exact term match, scoring `2.0` as well, since the term itself is "laptop" exactly.
4. Since products 1, 2, and 3 all score identically in this simplified model, the stable sort keeps their relative order from the stream, showing that a real relevance score (as computed by actual Elasticsearch/BM25 scoring, accounting for document length and term frequency) would differentiate these results more finely than this simplified `scoreMatch` does.
5. Product 4 ("wireless mouse") never appears in either result list, since `scoreMatch` returns `0` for it (no term matches "laptop" at all) — the `.filter(entry -> entry.getValue() > 0)` step in the ranked version explicitly excludes it, and the plain `findByNameContaining` version's `anyMatch` check also naturally excludes it.

## 7. Gotchas & takeaways

> Gotcha: `@Field(type = FieldType.Keyword)` and `@Field(type = FieldType.Text)` behave very differently — a `Keyword` field is only ever matched exactly (no analysis, no partial matching), while a `Text` field goes through the full analyzer pipeline and supports partial and fuzzy matching. Mapping a field intended for full-text search as `Keyword` (or vice versa) is a common mistake that silently breaks either exact filtering or full-text search on that field.

- Spring Data Elasticsearch maps the familiar Spring Data repository pattern onto Elasticsearch, translating method names into real search queries automatically.
- `@Document` and `@Field` control how your Java model maps onto the underlying Elasticsearch index and its field types.
- Whether a field supports full-text (partial, analyzed) matching or only exact matching depends entirely on its mapped field type, not on the Java type alone.
- Related concepts: [Inverted index](0159-inverted-index.md) and [Relevance ranking (TF-IDF / BM25)](0161-relevance-ranking-tf-idf-bm25.md) (what Elasticsearch itself implements under this API), [Elasticsearch cluster basics (shards & replicas)](0165-elasticsearch-cluster-basics-shards-replicas.md) (how the index this repository talks to is actually distributed), [Tokenization, stemming & analyzers](0160-tokenization-stemming-analyzers.md) (what a `Text`-typed field applies before indexing).
