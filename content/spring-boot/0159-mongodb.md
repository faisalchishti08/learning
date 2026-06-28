---
card: spring-boot
gi: 159
slug: mongodb
title: MongoDB
---

## 1. What it is

**MongoDB** is a document-oriented NoSQL database that stores data as BSON (Binary JSON) documents in collections. Spring Boot auto-configures MongoDB via `spring-boot-starter-data-mongodb`, registering a `MongoClient`, `MongoTemplate`, and Spring Data MongoDB repositories. Connection is specified with `spring.data.mongodb.uri`. Spring Data MongoDB maps Java classes to MongoDB documents using `@Document`.

## 2. Why & when

Use MongoDB when:

- Your data is **document-shaped** — nested, variable-schema, or hierarchical (e.g., product catalogues with varying attributes per category).
- You need **horizontal sharding** — MongoDB scales out natively.
- Schema evolution is frequent — adding/removing fields in documents requires no migrations.
- You want **rich queries** on nested fields (unlike relational joins across tables).

Avoid MongoDB when referential integrity (foreign keys), ACID multi-document transactions across collections, or complex aggregations across many entities are central to your application.

## 3. Core concept

`MongoAutoConfiguration` reads `spring.data.mongodb.uri` and creates a `MongoClient`. `MongoDataAutoConfiguration` creates a `MongoTemplate` (low-level CRUD) and enables Spring Data repositories.

```java
@Document(collection = "orders")   // maps class → MongoDB collection
public class Order {
    @Id private String id;          // MongoDB _id field (ObjectId)
    private String product;
    private int quantity;
}

interface OrderRepo extends MongoRepository<Order, String> {
    List<Order> findByProduct(String product);  // derived query → MongoDB filter
}
```

MongoDB query `{ product: "Widget" }` is generated from method name `findByProduct`.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">MongoRepository</text>
  <rect x="235" y="55" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="322" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">MongoTemplate</text>
  <rect x="235" y="115" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="322" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">MongoClient</text>
  <rect x="490" y="80" width="165" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">MongoDB</text>
  <line x1="162" y1="105" x2="231" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mg)"/>
  <line x1="322" y1="97" x2="322" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#mg2)"/>
  <line x1="412" y1="135" x2="486" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#mg3)"/>
  <defs>
    <marker id="mg" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mg2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="mg3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Repository delegates to `MongoTemplate`, which uses `MongoClient` to communicate with MongoDB over the wire protocol.

## 5. Runnable example

```java
// MongoApp.java — Spring Boot project with spring-boot-starter-data-mongodb
// application.properties:
//   spring.data.mongodb.uri=mongodb://localhost:27017/shopdb
// Start MongoDB: docker run -p 27017:27017 mongo:7

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@SpringBootApplication
public class MongoApp {
    public static void main(String[] args) {
        SpringApplication.run(MongoApp.class, args);
    }
}

@Document(collection = "products")
class Product {
    @Id String id;
    String name;
    double price;
    Product() {}
    Product(String name, double price) { this.name = name; this.price = price; }
    public String getId() { return id; }
    public String getName() { return name; }
    public double getPrice() { return price; }
}

interface ProductRepo extends MongoRepository<Product, String> {
    List<Product> findByPriceLessThan(double maxPrice);
}

@RestController
@RequestMapping("/products")
class ProductController {

    private final ProductRepo repo;

    ProductController(ProductRepo repo) { this.repo = repo; }

    @GetMapping
    public List<Product> all() { return repo.findAll(); }

    @PostMapping
    public Product create(@RequestBody Product p) { return repo.save(p); }

    @GetMapping("/cheap")
    public List<Product> cheap(@RequestParam double maxPrice) {
        return repo.findByPriceLessThan(maxPrice);
    }
}
```

**How to run:**
1. Start MongoDB: `docker run -p 27017:27017 mongo:7`
2. Add `spring-boot-starter-data-mongodb` to `pom.xml`, start the app.
3. `curl -X POST http://localhost:8080/products -H 'Content-Type: application/json' -d '{"name":"Widget","price":9.99}'`
4. `curl "http://localhost:8080/products/cheap?maxPrice=15"` → products under $15.

## 6. Walkthrough

- `spring-boot-starter-data-mongodb` pulls in the MongoDB Java driver and Spring Data MongoDB. `MongoAutoConfiguration` creates `MongoClient` from `spring.data.mongodb.uri`. `MongoDataAutoConfiguration` registers `MongoTemplate` and enables `@EnableMongoRepositories` scanning.
- `@Document(collection = "products")` tells Spring Data to map this class to the `products` collection. Without the annotation, the class name (lowercased) is used as the collection name.
- `@Id String id` maps to MongoDB's `_id` field. MongoDB auto-generates an `ObjectId` hex string if the field is null when the document is inserted.
- `MongoRepository<Product, String>` extends `CrudRepository` with MongoDB-specific methods like `findAll(Sort)`. The second type parameter is the `@Id` type.
- `findByPriceLessThan(double maxPrice)` generates `{ price: { $lt: maxPrice } }` — Spring Data translates the method name into a MongoDB query at application startup.
- `repo.save(p)` calls MongoDB's `insertOne` (if `id` is null) or `replaceOne` (if `id` is set).

## 7. Gotchas & takeaways

> MongoDB's `@Id` field is of type `String` (ObjectId hex) or `ObjectId`, not `Long`. Using `Long` generates sequential IDs that are not collision-safe across replicas.

> Spring Data MongoDB derived queries scan index-less collections in O(n). Always add `@Indexed` or create indexes via `@CompoundIndex` on `@Document` for query fields; without indexes, queries degrade at scale.

- `MongoTemplate.updateFirst()` and `updateMulti()` update documents in-place using MongoDB `$set` — no full document replacement needed.
- `spring.data.mongodb.auto-index-creation=true` creates `@Indexed` / `@CompoundIndex` annotations at startup — convenient for dev, disable for production.
- For reactive MongoDB access (WebFlux), use `spring-boot-starter-data-mongodb-reactive` and inject `ReactiveMongoTemplate` or extend `ReactiveMongoRepository`.
- `@Transactional` on MongoDB requires a replica set or sharded cluster — single-node standalone does not support multi-document transactions.
