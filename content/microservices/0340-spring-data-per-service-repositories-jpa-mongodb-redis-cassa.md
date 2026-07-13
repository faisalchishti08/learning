---
card: microservices
gi: 340
slug: spring-data-per-service-repositories-jpa-mongodb-redis-cassa
title: "Spring Data per-service repositories (JPA, MongoDB, Redis, Cassandra, etc.)"
---

## 1. What it is

**Spring Data** is a family of modules (Spring Data JPA, Spring Data MongoDB, Spring Data Redis, Spring Data Cassandra, and more) that each provide the same repository abstraction — an interface with methods like `findById` or `save` that Spring implements for you at runtime — over a different underlying storage technology. In microservices, this means each service can declare a `Repository` interface backed by whichever database fits its own needs, giving [polyglot persistence](0307-polyglot-persistence.md) and [database per service](0304-database-per-service-pattern.md) a concrete, idiomatic Spring implementation: the order service might use Spring Data JPA over Postgres while the catalog service uses Spring Data MongoDB, with no shared code between them beyond the common repository interface style.

## 2. Why & when

Once each service genuinely owns its own private database ([database per service](0304-database-per-service-pattern.md)), the natural next question is how each service's Spring code should actually talk to its chosen store. Spring Data answers this uniformly: regardless of whether a service's database is relational (JPA), document-oriented (MongoDB), key-value (Redis), or wide-column (Cassandra), the application code writes a repository interface in the same style, and Spring generates the implementation for that specific store. This means a team can standardize on "how we write data access code" across every service, even while each service is free to choose the storage technology that best fits its own data shape and access patterns — exactly the flexibility [polyglot persistence](0307-polyglot-persistence.md) calls for.

Use the Spring Data module matching each service's chosen database, and resist the temptation to force every service onto the same store just because "we already have Spring Data JPA set up" — the whole point of per-service repositories is that each service's storage choice is independent, and Spring Data is what makes that independence cheap to implement consistently.

## 3. Core concept

Every Spring Data module follows the same shape: define an interface extending a module-specific base (`JpaRepository`, `MongoRepository`, `CrudRepository` for Redis, `CassandraRepository`), declare query methods by name (`findByStatus`, `findByRegion`) or with `@Query`, and Spring generates a working implementation at startup — no hand-written SQL or driver code needed for common cases, regardless of which store is behind the interface.

```java
interface OrderRepository extends JpaRepository<Order, String> { List<Order> findByStatus(String status); } // order-service: relational
interface ProductRepository extends MongoRepository<Product, String> { List<Product> findByCategory(String category); } // catalog-service: document
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service uses Spring Data JPA over Postgres, catalog service uses Spring Data MongoDB over MongoDB, session service uses Spring Data Redis over Redis -- each independent, same repository style">
  <rect x="20" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="110" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Data JPA</text>
  <text x="110" y="72" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; Postgres</text>

  <rect x="230" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">catalog-service</text>
  <text x="320" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Data MongoDB</text>
  <text x="320" y="72" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; MongoDB</text>

  <rect x="440" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">session-service</text>
  <text x="530" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Data Redis</text>
  <text x="530" y="72" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; Redis</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Same repository interface style everywhere; each service's storage choice is fully independent.</text>
</svg>

Each service picks the Spring Data module matching its own storage technology, while sharing the same repository interface programming model.

## 5. Runnable example

Scenario: an order-service repository, first modeled with hand-written data access, then converted to a Spring Data-style repository interface pattern (simulated without a real database, since this is a conceptual, runnable illustration), and finally extended to show a second, independent service using a completely different Spring Data module for its own store.

### Level 1 — Basic

```java
// File: HandWrittenDataAccess.java -- data access written by hand, no
// repository abstraction; every query is manually coded.
import java.util.*;

public class HandWrittenDataAccess {
    record Order(String id, String status) {}
    static Map<String, Order> table = new HashMap<>(); // stands in for a real database table

    static Order findById(String id) { return table.get(id); } // hand-written, one method per query need
    static List<Order> findByStatus(String status) {
        List<Order> results = new ArrayList<>();
        for (Order o : table.values()) if (o.status().equals(status)) results.add(o);
        return results;
    }
    static void save(Order order) { table.put(order.id(), order); }

    public static void main(String[] args) {
        save(new Order("order-1", "PENDING"));
        save(new Order("order-2", "SHIPPED"));
        System.out.println("findById: " + findById("order-1"));
        System.out.println("findByStatus(PENDING): " + findByStatus("PENDING"));
    }
}
```

How to run: `java HandWrittenDataAccess.java`

Every query — `findById`, `findByStatus` — is written by hand, with its own loop or lookup logic. This works, but every new query need means writing a new method from scratch, and this exact pattern would need to be reimplemented differently for every different storage technology a service might use.

### Level 2 — Intermediate

```java
// File: SpringDataStyleRepository.java -- a Spring Data JPA-STYLE
// repository interface; in real Spring Boot, only the interface below is
// written -- Spring generates the implementation. Here we simulate that
// generated behavior with a small proxy, to show the SHAPE of what
// Spring Data provides for free.
import java.util.*;
import java.lang.reflect.*;

public class SpringDataStyleRepository {
    record Order(String id, String status) {}

    interface OrderRepository { // this is ALL you write in real Spring Data JPA
        Order findById(String id);
        List<Order> findByStatus(String status);
        void save(Order order);
    }

    // Simulates what Spring Data generates automatically at startup -- normally invisible to you.
    static OrderRepository createGeneratedRepository() {
        Map<String, Order> table = new HashMap<>();
        return (OrderRepository) Proxy.newProxyInstance(OrderRepository.class.getClassLoader(),
                new Class<?>[]{OrderRepository.class}, (proxy, method, args) -> {
                    switch (method.getName()) {
                        case "findById": return table.get((String) args[0]);
                        case "findByStatus": {
                            List<Order> results = new ArrayList<>();
                            for (Order o : table.values()) if (o.status().equals(args[0])) results.add(o);
                            return results;
                        }
                        case "save": table.put(((Order) args[0]).id(), (Order) args[0]); return null;
                        default: return null;
                    }
                });
    }

    public static void main(String[] args) {
        OrderRepository orderRepository = createGeneratedRepository(); // in real Spring, @Autowired gives you this

        orderRepository.save(new Order("order-1", "PENDING"));
        orderRepository.save(new Order("order-2", "SHIPPED"));

        System.out.println("findById: " + orderRepository.findById("order-1"));
        System.out.println("findByStatus(PENDING): " + orderRepository.findByStatus("PENDING"));
        System.out.println("(In real Spring Data JPA, YOU only wrote the interface -- Spring generated this implementation.)");
    }
}
```

How to run: `java SpringDataStyleRepository.java`

The application code only ever refers to the `OrderRepository` interface — `findById`, `findByStatus`, `save` — exactly the same method names as Level 1's hand-written version, but with no hand-written implementation at all in real Spring Data JPA (the `Proxy` here simulates Spring's runtime-generated implementation, just to keep this example runnable standalone). This is the core value proposition: declare the interface, get a working implementation, in the same style regardless of what's actually behind it.

### Level 3 — Advanced

```java
// File: TwoServicesTwoStores.java -- TWO independent services, each with
// its own repository interface in the SAME style, but backed by
// COMPLETELY different simulated stores -- illustrating polyglot
// persistence with a consistent Spring Data programming model.
import java.util.*;
import java.lang.reflect.*;

public class TwoServicesTwoStores {
    // order-service's own types and repository -- would be Spring Data JPA over Postgres in reality.
    record Order(String id, String status) {}
    interface OrderRepository { Order findById(String id); void save(Order o); }

    // catalog-service's own types and repository -- would be Spring Data MongoDB over MongoDB in reality.
    record Product(String id, String category) {}
    interface ProductRepository { List<Product> findByCategory(String category); void save(Product p); }

    static OrderRepository buildOrderRepository() {
        Map<String, Order> relationalStyleTable = new HashMap<>(); // "Postgres" simulation
        return (OrderRepository) Proxy.newProxyInstance(OrderRepository.class.getClassLoader(),
                new Class<?>[]{OrderRepository.class}, (proxy, method, args) -> {
                    if (method.getName().equals("findById")) return relationalStyleTable.get((String) args[0]);
                    relationalStyleTable.put(((Order) args[0]).id(), (Order) args[0]); return null;
                });
    }

    static ProductRepository buildProductRepository() {
        List<Product> documentStyleCollection = new ArrayList<>(); // "MongoDB" simulation
        return (ProductRepository) Proxy.newProxyInstance(ProductRepository.class.getClassLoader(),
                new Class<?>[]{ProductRepository.class}, (proxy, method, args) -> {
                    if (method.getName().equals("findByCategory")) {
                        List<Product> results = new ArrayList<>();
                        for (Product p : documentStyleCollection) if (p.category().equals(args[0])) results.add(p);
                        return results;
                    }
                    documentStyleCollection.add((Product) args[0]); return null;
                });
    }

    public static void main(String[] args) {
        OrderRepository orderRepository = buildOrderRepository();      // order-service's own store, independent
        ProductRepository productRepository = buildProductRepository(); // catalog-service's own store, independent

        orderRepository.save(new Order("order-1", "PENDING"));
        productRepository.save(new Product("p1", "electronics"));
        productRepository.save(new Product("p2", "electronics"));

        System.out.println("order-service found: " + orderRepository.findById("order-1"));
        System.out.println("catalog-service found: " + productRepository.findByCategory("electronics"));
        System.out.println("Two independent stores, TWO independent Spring Data modules, ONE consistent repository style.");
    }
}
```

How to run: `java TwoServicesTwoStores.java`

`buildOrderRepository` and `buildProductRepository` construct completely independent, differently-shaped backing stores (one keyed by ID for direct lookup, standing in for a relational table; one an unindexed list scanned by category, standing in for a MongoDB collection query) — yet both are consumed through a repository interface in the identical Spring Data style. Neither service's code has any dependency on the other's storage technology; `order-service` never needs to know `catalog-service` uses a document store, and vice versa.

## 6. Walkthrough

Trace `TwoServicesTwoStores.main` in order. **First**, `buildOrderRepository()` and `buildProductRepository()` each construct their own independent backing store and proxy — `orderRepository` is bound to a `HashMap` keyed by order ID, while `productRepository` is bound to an `ArrayList` that must be scanned linearly for category matches, mirroring the real structural difference between a relational table (indexed lookups) and a MongoDB collection query (filter over documents).

**Next**, `orderRepository.save(new Order("order-1", "PENDING"))` runs: the proxy's invocation handler matches on the method name `"save"` (the `else` branch, since it's not `"findById"`), and stores the order in `relationalStyleTable` keyed by its ID.

**Then**, two `productRepository.save(...)` calls run, each appending a `Product` to `documentStyleCollection` — no key-based indexing here, just an append, mirroring how a MongoDB insert doesn't require the same kind of primary-key-first design a relational table does.

**After that**, `orderRepository.findById("order-1")` runs: the proxy matches `"findById"` and returns `relationalStyleTable.get("order-1")` directly — an O(1)-style keyed lookup.

**Finally**, `productRepository.findByCategory("electronics")` runs: the proxy matches `"findByCategory"`, and since this isn't a keyed lookup, it iterates the entire `documentStyleCollection`, collecting every `Product` whose `category()` equals `"electronics"` — both `p1` and `p2` match, and both are returned.

```
order-service:    save(order-1) -> relationalStyleTable{order-1: PENDING}
catalog-service:  save(p1, electronics), save(p2, electronics) -> documentStyleCollection[p1, p2]
order-service:    findById(order-1)          -> direct keyed lookup       -> Order(order-1, PENDING)
catalog-service:  findByCategory(electronics) -> linear scan over collection -> [p1, p2]
```

## 7. Gotchas & takeaways

> Spring Data's uniform repository style can create a false sense that every store behaves identically underneath — a `findByCategory` query that's an efficient indexed lookup in one database might be a full collection scan in another, depending on whether you've defined the right index for that specific store. The interface hides the implementation, not the performance characteristics; still design queries and indexes for the actual technology behind each repository.

- Every Spring Data module (JPA, MongoDB, Redis, Cassandra, and more) provides the same repository-interface programming model over a different storage technology.
- This lets each microservice choose its own database independently ([polyglot persistence](0307-polyglot-persistence.md)) while every service's data-access code still looks and feels the same to developers moving between services.
- Query methods are typically declared by name (`findByStatus`) or with `@Query`, and Spring generates the implementation at startup — no hand-written boilerplate for common access patterns.
- A shared repository *style* does not imply shared repository *behavior* — understand and design for the real performance characteristics of whatever store sits behind each service's chosen Spring Data module.
