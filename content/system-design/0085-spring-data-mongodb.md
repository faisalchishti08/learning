---
card: system-design
gi: 85
slug: spring-data-mongodb
title: Spring Data MongoDB
---

## 1. What it is

**Spring Data MongoDB** extends the same repository pattern used by Spring Data JPA — declare an interface, get a working implementation — to MongoDB, a document store. `@Document` marks a Java class as mapping to a MongoDB collection, and a repository extending `MongoRepository<T, ID>` provides `save`, `findById`, and derived query methods, backed by MongoDB's document queries instead of SQL.

## 2. Why & when

Just as Spring Data JPA removes relational DAO boilerplate, Spring Data MongoDB removes the boilerplate of hand-writing MongoDB driver calls (building query documents, converting between BSON and Java objects). The programming model is deliberately similar to JPA's, so a team already familiar with Spring Data repositories can pick up MongoDB with very little new syntax to learn. Use it whenever a Spring application needs a document store — the catalog and flexible-schema use cases covered earlier in this section.

## 3. Core concept

**`@Document` and a repository interface:**

```java
@Document(collection = "products")
public class Product {
    @Id
    private String id;
    private String name;
    private double price;
    private List<String> tags; // nested, flexible fields - no fixed column list
}

public interface ProductRepository extends MongoRepository<Product, String> {
    List<Product> findByTagsContaining(String tag); // derived query, no code needed
    List<Product> findByPriceLessThan(double maxPrice);
}
```

**Derived queries map to MongoDB query documents, not SQL:** `findByPriceLessThan(50.0)` generates a MongoDB query equivalent to `{ price: { $lt: 50.0 } }`, the same derived-method-name mechanism from Spring Data JPA, but translated into MongoDB's own query language instead of JPQL/SQL.

**`MongoTemplate` for anything derived methods cannot express:** for aggregation pipelines or more complex nested-document queries, `MongoTemplate` gives direct, lower-level access — the MongoDB equivalent of `@Query` / native SQL in the JPA world.

**No schema migrations, but no schema enforcement either:** because MongoDB documents are schema-flexible, adding a new field to `Product` needs no database migration — existing documents simply do not have that field until they are next written. This is convenient for iteration but means your Java class's shape and what is actually stored can silently drift apart over time if not disciplined about it.

## 4. Diagram

```
public interface ProductRepository extends MongoRepository<Product, String> {
    List<Product> findByPriceLessThan(double maxPrice);
}
              |
              | at startup: Spring generates a proxy implementation
              v
   productRepository.findByPriceLessThan(50.0)
              |
              v
   Spring Data MongoDB parses the method name "findByPriceLessThan"
              |
              v
   builds a MongoDB query document: { price: { $lt: 50.0 } }
              |
              v
   MongoDB executes it, returns matching documents mapped back to List<Product>
```
*Caption: the same derived-method-name mechanism as Spring Data JPA, but generating a MongoDB query document instead of SQL.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling how a derived MongoDB query method is parsed and executed

```java
import java.util.*;
import java.util.function.Predicate;

public class SpringDataMongoSim {

    record Product(String id, String name, double price, List<String> tags) {}

    // Simulates the MongoDB collection underneath the generated repository proxy.
    static final List<Product> collection = new ArrayList<>();

    // Simulates what Spring Data MongoDB generates for each derived method name.
    static List<Product> queryCollection(Predicate<Product> filter) {
        return collection.stream().filter(filter).toList();
    }

    static List<Product> findByPriceLessThan(double maxPrice) {
        return queryCollection(p -> p.price() < maxPrice); // parsed from "findBy" + "Price" + "LessThan"
    }

    static List<Product> findByTagsContaining(String tag) {
        return queryCollection(p -> p.tags().contains(tag)); // parsed from "findBy" + "Tags" + "Containing"
    }

    public static void main(String[] args) {
        collection.add(new Product("1", "Wireless Mouse", 25.99, List.of("electronics", "accessories")));
        collection.add(new Product("2", "Mechanical Keyboard", 89.99, List.of("electronics", "accessories")));
        collection.add(new Product("3", "Desk Lamp", 34.50, List.of("home", "lighting")));

        System.out.println("findByPriceLessThan(50.0):");
        for (Product p : findByPriceLessThan(50.0)) {
            System.out.println("  " + p.name() + " ($" + p.price() + ")");
        }

        System.out.println("findByTagsContaining(\"electronics\"):");
        for (Product p : findByTagsContaining("electronics")) {
            System.out.println("  " + p.name());
        }
    }
}
```

**How to run:** save as `SpringDataMongoSim.java`, run `java SpringDataMongoSim.java` (JDK 17+). A real Spring Boot app needs the `spring-boot-starter-data-mongodb` dependency, a running MongoDB instance, and `@Document`-annotated classes as shown above; the repository interface itself needs no implementation code.

## 6. Walkthrough

1. `findByPriceLessThan(50.0)` filters `collection` for products with `price < 50.0`, returning the Wireless Mouse (`$25.99`) and Desk Lamp (`$34.50`) but not the Mechanical Keyboard (`$89.99`) — mirroring `{ price: { $lt: 50.0 } }` on a real MongoDB collection.
2. `findByTagsContaining("electronics")` filters for products whose `tags` list contains `"electronics"`, returning the Wireless Mouse and Mechanical Keyboard — mirroring `{ tags: "electronics" }`, MongoDB's array-containment query, generated from the `Containing` keyword in the method name.
3. Both methods needed zero implementation code beyond their signature — Spring Data MongoDB parses the method name and generates the equivalent query, the exact same derived-query mechanism as Spring Data JPA, applied to a document store's query language instead of SQL.

## 7. Gotchas & takeaways

> **Gotcha:** because MongoDB enforces no schema, adding a field to the `@Document` class does not retroactively add it to documents already stored — code reading an older document must handle that field being absent (usually deserializing to `null` or a default), which is easy to forget and can cause `NullPointerException`s on data written before a schema change.

- Spring Data MongoDB mirrors Spring Data JPA's repository and derived-query-method model, making the transition between relational and document stores mostly a matter of learning MongoDB's query semantics, not a new programming model.
- `MongoTemplate` provides an escape hatch for aggregation pipelines and queries too complex for the method-naming convention to express.
- Related concepts: [Document stores](0076-document-stores.md) (the underlying store this integration wraps), [Spring Data JPA & repositories](0072-spring-data-jpa-repositories.md) (the relational equivalent this API is intentionally modeled after).
