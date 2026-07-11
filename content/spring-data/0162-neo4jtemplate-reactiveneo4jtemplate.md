---
card: spring-data
gi: 162
slug: neo4jtemplate-reactiveneo4jtemplate
title: "Neo4jTemplate / ReactiveNeo4jTemplate"
---

## 1. What it is

`Neo4jTemplate` (blocking) and `ReactiveNeo4jTemplate` (returning `Mono`/`Flux`) are Spring Data Neo4j's low-level entry points for Neo4j — a graph database that stores data as nodes and relationships instead of tables or documents, and is built for traversing connected data (friend-of-friend networks, recommendation paths, org charts) far more naturally than a relational join chain ever could.

```java
@Autowired Neo4jTemplate neo4jTemplate;

Customer customer = neo4jTemplate.findById(customerId, Customer.class);
neo4jTemplate.save(new Customer("c1", "Amara"));
```

## 2. Why & when

This card opens the final Spring Data module in this course: Spring Data Neo4j. Where Cassandra optimized for write-heavy, partition-scoped access, Neo4j optimizes for the opposite problem — following relationships several hops deep, quickly, without the join explosion a relational database suffers as hop count grows. `Neo4jTemplate`/`ReactiveNeo4jTemplate` play the same architectural role every earlier template played: the low-level API every generated repository builds on.

Reach for `Neo4jTemplate`/`ReactiveNeo4jTemplate` directly when:

- Writing a custom repository implementation needing operations beyond a generated `Neo4jRepository` method.
- Choosing between blocking and reactive access based on the rest of the application stack — the same blocking/reactive split seen in every earlier Spring Data module.
- You need to save or load a graph of connected entities as a unit, letting the template handle relationship persistence rather than issuing separate calls per node.

## 3. Core concept

```
 interface CustomerRepository extends Neo4jRepository<Customer, String> { }
   -- generated implementation is a thin wrapper delegating to:

 Neo4jTemplate.findById(id, Customer.class)              -- blocking, direct value returned
 Neo4jTemplate.save(customer)                              -- blocking, writes node + relationships

 ReactiveNeo4jTemplate.findById(id, Customer.class)        -- Mono<Customer>
 ReactiveNeo4jTemplate.save(customer)                       -- Mono<Customer>

 customerRepository.findById(id)  ==  neo4jTemplate.findById(id, Customer.class)
```

The relationship mirrors what `CassandraTemplate`/`ReactiveCassandraTemplate` were to their repositories in the previous section — a lower-level, storage-specific API that generated repositories build on, this time storage-specific to a graph model instead of a wide-column one.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generated Neo4jRepository and a custom implementation both delegate to the same underlying Neo4jTemplate">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">customerRepository.findById(id)</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">custom impl: neo4jTemplate...</text>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Neo4jTemplate / ReactiveNeo4jTemplate</text>

  <line x1="150" y1="65" x2="290" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the generated repository and a hand-written custom fragment ultimately delegate to the same underlying template.

## 5. Runnable example

The scenario: storing customers and the products they bought, evolving from a blocking `Neo4jTemplate`-style baseline, to its reactive `ReactiveNeo4jTemplate` equivalent, to a custom repository fragment that walks a "customers who bought this also bought" relationship — a query graph databases handle naturally.

### Level 1 — Basic

Model the blocking `Neo4jTemplate` style, against an in-memory stand-in for a Neo4j graph.

```java
import java.util.*;

public class Neo4jTemplateLevel1 {
    public static void main(String[] args) {
        Neo4jTemplate neo4jTemplate = new Neo4jTemplate();
        neo4jTemplate.save(new Customer("c1", "Amara"));
        neo4jTemplate.save(new Customer("c2", "Bilal"));

        Customer found = neo4jTemplate.findById("c1");
        System.out.println("Found by id: name=" + found.name);

        List<Customer> all = neo4jTemplate.findAll();
        System.out.println("Total customers: " + all.size());
    }
}

class Customer { String id; String name; Customer(String id, String name) { this.id = id; this.name = name; } }

// Stands in for org.springframework.data.neo4j.core.Neo4jTemplate.
class Neo4jTemplate {
    private final Map<String, Customer> nodes = new HashMap<>();

    Customer findById(String id) { return nodes.get(id); } // blocking, direct return
    void save(Customer customer) { nodes.put(customer.id, customer); }
    List<Customer> findAll() { return new ArrayList<>(nodes.values()); }
}
```

How to run: `java Neo4jTemplateLevel1.java`

`findById`/`findAll` return values directly, exactly matching the blocking style established for every earlier template in this course — this is the pattern to reach for when the rest of the application stack is also blocking.

### Level 2 — Intermediate

Model the reactive `ReactiveNeo4jTemplate` equivalent, using `CompletableFuture` to stand in for `Mono`, matching the convention used consistently throughout this course's reactive cards.

```java
import java.util.*;
import java.util.concurrent.*;

public class Neo4jTemplateLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveNeo4jTemplate template = new ReactiveNeo4jTemplate();
        template.save(new Customer("c1", "Amara")).get(); // .get() used only for demo sequencing

        CompletableFuture<Customer> future = template.findById("c1"); // returns IMMEDIATELY
        System.out.println("Call returned; not necessarily complete yet.");
        Customer found = future.get(); // wait here ONLY for demo purposes
        System.out.println("Eventually found: name=" + found.name);
    }
}

class Customer { String id; String name; Customer(String id, String name) { this.id = id; this.name = name; } }

// Stands in for org.springframework.data.neo4j.core.ReactiveNeo4jTemplate.
class ReactiveNeo4jTemplate {
    private final Map<String, Customer> nodes = new HashMap<>();

    CompletableFuture<Customer> findById(String id) { // stands in for Mono<Customer>
        return CompletableFuture.supplyAsync(() -> nodes.get(id));
    }
    CompletableFuture<Customer> save(Customer customer) {
        return CompletableFuture.supplyAsync(() -> { nodes.put(customer.id, customer); return customer; });
    }
}
```

How to run: `java Neo4jTemplateLevel2.java`

`findById` returns its `CompletableFuture` (standing in for `Mono<Customer>`) immediately — mirroring the same non-blocking behavior established for `ReactiveCassandraTemplate` and every earlier reactive template, just applied to a graph store now.

### Level 3 — Advanced

Build a custom repository fragment using `Neo4jTemplate` directly for an operation no generated `Neo4jRepository` method expresses cleanly: finding "customers who bought this product also bought" recommendations by walking `BOUGHT` relationships two hops out.

```java
import java.util.*;
import java.util.stream.*;

public class Neo4jTemplateLevel3 {
    public static void main(String[] args) {
        Neo4jTemplate neo4jTemplate = new Neo4jTemplate();
        neo4jTemplate.link("c1", "kettle");
        neo4jTemplate.link("c1", "mug");
        neo4jTemplate.link("c2", "kettle");
        neo4jTemplate.link("c2", "teapot");
        neo4jTemplate.link("c3", "mug");

        RecommendationRepositoryCustom repo = new RecommendationRepositoryImpl(neo4jTemplate);
        List<String> recommended = repo.alsoBoughtByCustomersOf("kettle");
        System.out.println("Customers of 'kettle' also bought: " + recommended);
    }
}

class Neo4jTemplate {
    // BOUGHT relationships: customerId -> set of productIds
    Map<String, Set<String>> boughtByCustomer = new HashMap<>();

    void link(String customerId, String productId) {
        boughtByCustomer.computeIfAbsent(customerId, k -> new HashSet<>()).add(productId);
    }
    Map<String, Set<String>> allLinks() { return boughtByCustomer; }
}

interface RecommendationRepositoryCustom { List<String> alsoBoughtByCustomersOf(String productId); }

class RecommendationRepositoryImpl implements RecommendationRepositoryCustom {
    private final Neo4jTemplate neo4jTemplate;
    RecommendationRepositoryImpl(Neo4jTemplate neo4jTemplate) { this.neo4jTemplate = neo4jTemplate; }

    // No generated Neo4jRepository method walks "product -> customers who bought it -> their other products".
    // A two-hop traversal like this needs direct template/graph access.
    public List<String> alsoBoughtByCustomersOf(String productId) {
        Set<String> customersOfProduct = neo4jTemplate.allLinks().entrySet().stream()
            .filter(e -> e.getValue().contains(productId))
            .map(Map.Entry::getKey)
            .collect(Collectors.toSet());

        return customersOfProduct.stream()
            .flatMap(customerId -> neo4jTemplate.allLinks().get(customerId).stream())
            .filter(p -> !p.equals(productId))
            .distinct()
            .collect(Collectors.toList());
    }
}
```

How to run: `java Neo4jTemplateLevel3.java`

`alsoBoughtByCustomersOf` is a method no generated `Neo4jRepository<Customer, ...>` interface exposes on its own — it hops from a product, to the customers who bought it, to those customers' *other* products, which is exactly the kind of multi-hop traversal graph databases are built to answer efficiently, unlike a relational schema where each extra hop means another join.

## 6. Walkthrough

Execution starts in `main` for Level 3. Five `link` calls build the graph: `c1` bought `kettle` and `mug`, `c2` bought `kettle` and `teapot`, `c3` bought `mug`. This is the `(:Customer)-[:BOUGHT]->(:Product)` shape a real Neo4j graph would store as actual nodes and relationships rather than a `Map`.

`repo.alsoBoughtByCustomersOf("kettle")` runs the two-hop traversal: first it finds every customer connected to `kettle` (`c1`, `c2`), then it follows *their* `BOUGHT` edges out to every other product they've touched (`mug` from `c1`, `teapot` from `c2`), excluding `kettle` itself and de-duplicating.

```
Customers of 'kettle' also bought: [mug, teapot]
```

In a real Neo4j deployment this same traversal would be a single Cypher query — `MATCH (:Product {id:$productId})<-[:BOUGHT]-(c:Customer)-[:BOUGHT]->(rec:Product) WHERE rec.id <> $productId RETURN DISTINCT rec` — evaluated by Neo4j's graph engine by walking relationship pointers directly, not by scanning and joining tables. The next few cards cover writing and mapping queries like that.

## 7. Gotchas & takeaways

> Gotcha: `Neo4jTemplate`/`ReactiveNeo4jTemplate` model data as a graph of nodes and relationships from the start — trying to force a graph-shaped problem (recommendations, hierarchies, path-finding) into a relational or document model usually means simulating relationships with foreign keys or embedded arrays, which is exactly the friction Neo4j exists to remove.

> Gotcha: saving an entity with `save()` can cascade and save its related entities too, depending on how deep the mapped object graph goes — this is convenient for small connected graphs but can trigger far more writes than expected if an entity's relationships aren't scoped carefully, unlike a single-row JDBC insert.

- `Neo4jTemplate`/`ReactiveNeo4jTemplate` are the low-level entry points every generated `Neo4jRepository`/`ReactiveNeo4jRepository` method delegates to, mirroring the template pattern from every other Spring Data module in this course.
- The blocking/reactive split matches the pattern established for MongoDB, Redis, Elasticsearch, and Cassandra earlier — same conceptual operations, different execution model.
- Neo4j's strength is multi-hop traversal — following relationships several steps deep without the join cost that grows with hop count in a relational database.
- Custom repository fragments using the template directly are how graph traversals that don't map to a simple derived query get expressed.
