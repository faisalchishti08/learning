---
card: spring-boot
gi: 161
slug: elasticsearch
title: Elasticsearch
---

## 1. What it is

**Elasticsearch** is a distributed search and analytics engine built on Apache Lucene. Spring Boot auto-configures it via `spring-boot-starter-data-elasticsearch`, registering an `ElasticsearchClient` (Java API client, the current default) and Spring Data Elasticsearch repositories. Connection is configured with `spring.elasticsearch.uris`. Data is stored in **indices** (analogous to database tables) and searched using JSON query DSL.

## 2. Why & when

Use Elasticsearch when:

- **Full-text search** — tokenised, scored, language-analysed search across large text fields.
- **Log/metrics aggregation** — part of the ELK stack (Elasticsearch + Logstash + Kibana).
- **Faceted search** — filtering products by brand, price range, rating simultaneously.
- **Geospatial search** — find all locations within X km of a point.

Elasticsearch is not a primary datastore — it lacks ACID transactions and strong consistency. Use it alongside a relational or document database: write to the primary store, index to Elasticsearch for search.

## 3. Core concept

```java
@Document(indexName = "articles")   // maps class → Elasticsearch index
class Article {
    @Id String id;
    @Field(type = FieldType.Text, analyzer = "english")
    String content;
    @Field(type = FieldType.Keyword)
    String author;
}

interface ArticleRepo extends ElasticsearchRepository<Article, String> {
    List<Article> findByAuthor(String author);  // term query on keyword field
    List<Article> findByContentContaining(String word);  // full-text match
}
```

Spring Data Elasticsearch translates method names into Elasticsearch query DSL at application startup.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">ElasticsearchRepo</text>
  <rect x="240" y="55" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ElasticsearchTemplate</text>
  <rect x="240" y="115" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="327" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">ElasticsearchClient</text>
  <rect x="490" y="75" width="170" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="100" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Elasticsearch</text>
  <text x="575" y="117" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">port 9200 (HTTP)</text>
  <line x1="172" y1="105" x2="236" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#es)"/>
  <line x1="327" y1="97" x2="327" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#es2)"/>
  <line x1="417" y1="135" x2="486" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#es3)"/>
  <defs>
    <marker id="es" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="es2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="es3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Repository delegates to `ElasticsearchTemplate`, which serialises queries to JSON and sends them to Elasticsearch over HTTP.

## 5. Runnable example

```java
// ElasticsearchApp.java — Spring Boot project with spring-boot-starter-data-elasticsearch
// application.properties:
//   spring.elasticsearch.uris=http://localhost:9200
// Start Elasticsearch: docker run -p 9200:9200 -e "discovery.type=single-node"
//                       -e "xpack.security.enabled=false" elasticsearch:8.13.4

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.*;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@SpringBootApplication
public class ElasticsearchApp {
    public static void main(String[] args) {
        SpringApplication.run(ElasticsearchApp.class, args);
    }
}

@Document(indexName = "articles")
class Article {
    @Id String id;
    @Field(type = FieldType.Text, analyzer = "english") String title;
    @Field(type = FieldType.Keyword) String author;
    Article() {}
    Article(String title, String author) { this.title = title; this.author = author; }
    public String getId() { return id; }
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
}

interface ArticleRepo extends ElasticsearchRepository<Article, String> {
    List<Article> findByAuthor(String author);
    List<Article> findByTitleContaining(String keyword);
}

@RestController
@RequestMapping("/articles")
class ArticleController {

    private final ArticleRepo repo;

    ArticleController(ArticleRepo repo) { this.repo = repo; }

    @PostMapping
    public Article create(@RequestBody Article a) { return repo.save(a); }

    @GetMapping("/search")
    public List<Article> search(@RequestParam String keyword) {
        return repo.findByTitleContaining(keyword);
    }

    @GetMapping("/author/{name}")
    public List<Article> byAuthor(@PathVariable String name) {
        return repo.findByAuthor(name);
    }
}
```

**How to run:**
1. Start Elasticsearch: `docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.13.4`
2. Add `spring-boot-starter-data-elasticsearch` to `pom.xml`, start the app.
3. `curl -X POST http://localhost:8080/articles -H 'Content-Type: application/json' -d '{"title":"Spring Boot Tips","author":"alice"}'`
4. `curl "http://localhost:8080/articles/search?keyword=Spring"` → matching articles.

## 6. Walkthrough

- `spring-boot-starter-data-elasticsearch` adds the Elasticsearch Java API client and Spring Data Elasticsearch. `ElasticsearchAutoConfiguration` creates `ElasticsearchClient` from `spring.elasticsearch.uris`. `ElasticsearchDataAutoConfiguration` registers `ElasticsearchTemplate` and enables repository scanning.
- `@Document(indexName = "articles")` maps the class to the `articles` Elasticsearch index. Spring Data Elasticsearch creates the index and mapping at application startup if it does not exist.
- `@Field(type = FieldType.Text, analyzer = "english")` maps `title` as a full-text field with English language analysis (stemming, stop-words). `FieldType.Keyword` for `author` maps it as an exact-match field (no tokenisation).
- `findByTitleContaining(keyword)` generates a `match` query against the `title` field — Elasticsearch scores documents by relevance (TF-IDF / BM25).
- `findByAuthor(name)` generates a `term` query against the keyword field `author` — exact match, no analysis.
- `repo.save(a)` calls Elasticsearch's `index` API, which upserts a document.

## 7. Gotchas & takeaways

> `FieldType.Text` fields are analysed (tokenised, lowercased) — you cannot sort or aggregate on them directly. Use `@MultiField` to add a `.keyword` sub-field for sorting/aggregation alongside the analysed text field.

> Elasticsearch index mappings are immutable once created. Changing a field type requires reindexing — create a new index, migrate data, then swap the alias. Plan your mapping carefully before going to production.

- `spring.elasticsearch.socket-timeout` and `spring.elasticsearch.connection-timeout` tune the HTTP client.
- `ElasticsearchTemplate.search(NativeQuery, Class)` allows building arbitrary native Elasticsearch queries for cases where derived query methods fall short.
- For secured Elasticsearch (default in ES 8+), set `spring.elasticsearch.username` and `spring.elasticsearch.password` or use an API key.
- Spring Boot 3.x uses Elasticsearch Java API client (co.elastic.clients) by default; the legacy `RestHighLevelClient` is removed.
