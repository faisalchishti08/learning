---
card: spring-boot
gi: 163
slug: couchbase
title: Couchbase
---

## 1. What it is

**Couchbase** is a distributed NoSQL document database combining the flexibility of JSON documents with memory-first performance. Spring Boot auto-configures it via `spring-boot-starter-data-couchbase`, providing a `Cluster`, `CouchbaseTemplate`, and Spring Data Couchbase repositories. Connection is configured with `spring.couchbase.connection-string`, `spring.couchbase.username`, and `spring.couchbase.password`. Data lives in **buckets** (analogous to databases) and **collections** (analogous to tables).

## 2. Why & when

Use Couchbase when:

- **High-performance caching + persistence** — Couchbase was designed around a built-in managed cache layer.
- **Session storage at scale** — sub-millisecond get/set for session documents.
- **Mobile synchronisation** — Couchbase Lite (mobile SDK) syncs with Couchbase Server.
- **Flexible schema JSON documents** — product catalogues, user profiles, content management.

Couchbase differs from MongoDB in emphasising memory-first access and built-in cross-datacenter replication (XDCR). Avoid it for heavy relational joins or aggregate analytics.

## 3. Core concept

```java
@Document                          // maps class to Couchbase document
@Scope("inventory")                // optional: N1QL scope
@Collection("products")            // optional: N1QL collection
class Product {
    @Id String id;                 // document key
    String name;
    double price;
    @Version long version;         // optimistic locking (CAS)
}
```

Couchbase uses **N1QL** (SQL-like query language for JSON) or **Key-Value** operations (get/set by document key):

```java
interface ProductRepo extends CouchbaseRepository<Product, String> {
    List<Product> findByPriceLessThan(double max);  // → N1QL query
}
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="75" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="102" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">CouchbaseRepository</text>
  <text x="97" y="119" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">N1QL / KV ops</text>
  <rect x="245" y="55" width="170" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">CouchbaseTemplate</text>
  <rect x="245" y="115" width="170" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">Cluster / Collection</text>
  <rect x="490" y="75" width="165" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="102" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Couchbase</text>
  <text x="572" y="119" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">bucket / collection</text>
  <line x1="177" y1="105" x2="241" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cb)"/>
  <line x1="330" y1="97" x2="330" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cb2)"/>
  <line x1="417" y1="135" x2="486" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cb3)"/>
  <defs>
    <marker id="cb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cb2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="cb3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Repository uses K-V operations for single-document access (sub-millisecond) and N1QL for indexed queries.

## 5. Runnable example

```java
// CouchbaseApp.java — Spring Boot project with spring-boot-starter-data-couchbase
// application.properties:
//   spring.couchbase.connection-string=localhost
//   spring.couchbase.username=Administrator
//   spring.couchbase.password=password
//   spring.data.couchbase.bucket-name=demo
//   spring.data.couchbase.auto-index=true
// Start Couchbase: docker run -p 8091-8097:8091-8097 -p 11210:11210 couchbase:7.6
// Then set up via http://localhost:8091 (cluster, bucket "demo", user Administrator/password)

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Version;
import org.springframework.data.couchbase.core.mapping.Document;
import org.springframework.data.couchbase.repository.CouchbaseRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@SpringBootApplication
public class CouchbaseApp {
    public static void main(String[] args) {
        SpringApplication.run(CouchbaseApp.class, args);
    }
}

@Document
class Item {
    @Id String id = UUID.randomUUID().toString();
    String name;
    double price;
    @Version long version;
    Item() {}
    Item(String name, double price) { this.name = name; this.price = price; }
    public String getId() { return id; }
    public String getName() { return name; }
    public double getPrice() { return price; }
}

interface ItemRepo extends CouchbaseRepository<Item, String> {
    List<Item> findByName(String name);
    List<Item> findByPriceLessThan(double max);
}

@RestController
@RequestMapping("/items")
class ItemController {

    private final ItemRepo repo;

    ItemController(ItemRepo repo) { this.repo = repo; }

    @PostMapping
    public Item create(@RequestBody Item item) { return repo.save(item); }

    @GetMapping
    public Iterable<Item> all() { return repo.findAll(); }

    @GetMapping("/cheap")
    public List<Item> cheap(@RequestParam double maxPrice) {
        return repo.findByPriceLessThan(maxPrice);
    }
}
```

**How to run:**
1. Start Couchbase: `docker run -p 8091-8097:8091-8097 -p 11210:11210 couchbase:7.6`
2. Set up cluster, bucket `demo`, user `Administrator`/`password` at `http://localhost:8091`.
3. Add `spring-boot-starter-data-couchbase` to `pom.xml`, start the app.
4. `curl -X POST http://localhost:8080/items -H 'Content-Type: application/json' -d '{"name":"Widget","price":9.99}'`
5. `curl "http://localhost:8080/items/cheap?maxPrice=15"` → items under $15.

## 6. Walkthrough

- `CouchbaseAutoConfiguration` creates a `Cluster` from `spring.couchbase.connection-string`, username, and password. `CouchbaseDataAutoConfiguration` opens the bucket specified by `spring.data.couchbase.bucket-name` and registers `CouchbaseTemplate`.
- `@Document` marks the class as a Couchbase document. Each saved instance gets a document key equal to the `@Id` field.
- `@Version long version` enables **optimistic locking** via Couchbase's CAS (Compare-And-Swap) mechanism. If two threads modify the same document simultaneously, the second write fails with `OptimisticLockingFailureException`.
- `spring.data.couchbase.auto-index=true` creates N1QL indexes for `@Indexed` fields at startup — necessary for N1QL queries to perform well.
- `findByPriceLessThan(max)` generates `SELECT ... WHERE price < $max` N1QL — requires an index on `price`. Without the index the query falls back to a primary-index scan, which is slow.
- `repo.findAll()` uses a primary index `SELECT * FROM demo` — create a primary index (`CREATE PRIMARY INDEX ON demo`) in development.

## 7. Gotchas & takeaways

> Couchbase requires a **primary index** for `findAll()` and queries without a covered index. In production, use targeted secondary indexes and avoid primary index scans.

> `@Version` is strongly recommended for any update-heavy document. Without it, concurrent writes silently overwrite each other — the last write wins.

- `spring.data.couchbase.type-key=_class` is the field Couchbase uses to store the Java class name — useful if you store multiple entity types in one bucket.
- K-V operations (`collection.get(key)`) are sub-millisecond; N1QL queries are milliseconds to tens of milliseconds. Design entity IDs for K-V lookups where performance matters most.
- For reactive access (WebFlux), use `ReactiveCouchbaseRepository` — the Couchbase Java SDK is fully reactive.
- Couchbase Community Edition (free) lacks XDCR and some enterprise features; use Enterprise for production multi-DC setups.
