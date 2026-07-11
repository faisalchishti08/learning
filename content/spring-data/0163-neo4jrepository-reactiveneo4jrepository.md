---
card: spring-data
gi: 163
slug: neo4jrepository-reactiveneo4jrepository
title: "Neo4jRepository / ReactiveNeo4jRepository"
---

## 1. What it is

`Neo4jRepository<T, ID>` and `ReactiveNeo4jRepository<T, ID>` are the Spring Data Commons-style repository interfaces for Neo4j: extend one, declare methods by name or annotate them with `@Query`, and Spring Data generates the implementation, saving you from writing `Neo4jTemplate` calls by hand for routine graph operations.

```java
interface CustomerRepository extends Neo4jRepository<Customer, String> {
    Optional<Customer> findByName(String name);
    List<Customer> findByNameContaining(String fragment);
}
```

## 2. Why & when

`Neo4jTemplate` (previous card) is powerful but verbose for everyday operations — find-by-id, save, delete, find-by-a-property. `Neo4jRepository` is the same generated-interface pattern used by `MongoRepository`, `CrudRepository`, and `CassandraRepository` throughout this course, specialized for graph entities: it understands `@Node`-mapped classes and follows their `@Relationship` fields when saving and loading.

Reach for `Neo4jRepository`/`ReactiveNeo4jRepository` when:

- The operation is a standard CRUD call or a property-based lookup — `findById`, `save`, `deleteById`, `findByEmail`.
- You want Spring Data to derive the traversal from a method name, rather than hand-writing it against the template.
- You're choosing blocking vs. reactive for graph access, exactly as with every earlier repository interface in this course.

## 3. Core concept

```
 interface CustomerRepository extends Neo4jRepository<Customer, String> {
     Optional<Customer> findByName(String name);
 }

 findByName("Amara")
   -> Spring Data derives: MATCH (c:Customer {name: $name}) RETURN c
   -> executes via Neo4jTemplate under the hood
   -> maps result row(s) back to Customer, including mapped relationships

 ReactiveNeo4jRepository<Customer, String>
   -> same derivation, methods return Mono<Customer> / Flux<Customer>
```

Method-name derivation works the same way it did for `MongoRepository` and `JpaRepository` earlier — Spring Data parses the method name into a query, it's just compiled to Cypher (Neo4j's query language) instead of a Mongo filter or SQL.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A derived repository method name is parsed into a Cypher query and executed against the graph">
  <rect x="20" y="20" width="240" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">findByName("Amara")</text>

  <rect x="300" y="20" width="320" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="460" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">MATCH (c:Customer {name:$name}) RETURN c</text>

  <line x1="260" y1="42" x2="290" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a2)"/>

  <rect x="180" y="100" width="280" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Neo4j graph engine</text>

  <line x1="460" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a2)"/>
  <defs><marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A method name is parsed once, at startup, into a Cypher query that runs against the graph engine on every call.

## 5. Runnable example

The scenario: a `CustomerRepository` for finding customers by name, evolving from a blocking derived-method baseline, to its reactive equivalent, to a repository interface mixing generated methods with a custom fragment for a traversal derivation can't express — continuing the recommendation graph from the previous card.

### Level 1 — Basic

Model the blocking `Neo4jRepository`-style derived method, against an in-memory stand-in.

```java
import java.util.*;
import java.util.stream.*;

public class Neo4jRepositoryLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara"));
        repo.save(new Customer("c2", "Bilal"));

        Optional<Customer> found = repo.findByName("Amara");
        System.out.println("Found: " + found.map(c -> c.name).orElse("none"));
    }
}

class Customer { String id; String name; Customer(String id, String name) { this.id = id; this.name = name; } }

interface CustomerRepository {
    Customer save(Customer c);
    Optional<Customer> findByName(String name); // derived: MATCH (c:Customer {name: $name}) RETURN c
}

// Stands in for the Spring Data-generated implementation of a Neo4jRepository<Customer, String>.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public Optional<Customer> findByName(String name) {
        return nodes.values().stream().filter(c -> c.name.equals(name)).findFirst();
    }
}
```

How to run: `java Neo4jRepositoryLevel1.java`

`findByName` is never implemented by hand — the method name alone tells Spring Data to derive a Cypher `MATCH` filtering by the `name` property, matching the derived-query pattern established for `MongoRepository` and JPA earlier in this course.

### Level 2 — Intermediate

Model the reactive `ReactiveNeo4jRepository` equivalent, returning `CompletableFuture` to stand in for `Mono`/`Flux`.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class Neo4jRepositoryLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveCustomerRepository repo = new ReactiveCustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara")).get();
        repo.save(new Customer("c2", "Bilal")).get();

        CompletableFuture<List<Customer>> future = repo.findByNameContaining("a"); // returns IMMEDIATELY
        System.out.println("Call returned; not necessarily complete yet.");
        List<Customer> matches = future.get(); // wait here ONLY for demo purposes
        for (Customer c : matches) System.out.println("Matched: " + c.name);
    }
}

class Customer { String id; String name; Customer(String id, String name) { this.id = id; this.name = name; } }

interface ReactiveCustomerRepository {
    CompletableFuture<Customer> save(Customer c);
    CompletableFuture<List<Customer>> findByNameContaining(String fragment); // Flux<Customer> stand-in
}

class ReactiveCustomerRepositoryImpl implements ReactiveCustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public CompletableFuture<Customer> save(Customer c) {
        return CompletableFuture.supplyAsync(() -> { nodes.put(c.id, c); return c; });
    }
    public CompletableFuture<List<Customer>> findByNameContaining(String fragment) {
        return CompletableFuture.supplyAsync(() ->
            nodes.values().stream().filter(c -> c.name.contains(fragment)).collect(Collectors.toList()));
    }
}
```

How to run: `java Neo4jRepositoryLevel2.java`

`findByNameContaining` derives a `CONTAINS` filter instead of an exact match — Spring Data reads the `Containing` keyword from the method name the same way it did for MongoDB and JPA repositories, just compiling it to Cypher's `CONTAINS` operator here.

### Level 3 — Advanced

Combine generated derived methods with a custom fragment for the two-hop recommendation traversal from the previous card — something a method name alone can't express.

```java
import java.util.*;
import java.util.stream.*;

public class Neo4jRepositoryLevel3 {
    public static void main(String[] args) {
        Graph graph = new Graph();
        graph.link("c1", "kettle");
        graph.link("c1", "mug");
        graph.link("c2", "kettle");
        graph.link("c2", "teapot");

        CustomerRepository repo = new CustomerRepositoryImpl(graph);
        repo.save(new Customer("c1", "Amara"));
        repo.save(new Customer("c2", "Bilal"));

        System.out.println("By name: " + repo.findByName("Amara").map(c -> c.name).orElse("none"));
        System.out.println("Recommended for kettle buyers: " + repo.alsoBoughtByCustomersOf("kettle"));
    }
}

class Customer { String id; String name; Customer(String id, String name) { this.id = id; this.name = name; } }

class Graph {
    Map<String, Set<String>> boughtByCustomer = new HashMap<>();
    void link(String customerId, String productId) {
        boughtByCustomer.computeIfAbsent(customerId, k -> new HashSet<>()).add(productId);
    }
}

// Base repository interface: generated methods.
interface CustomerRepositoryBase {
    Customer save(Customer c);
    Optional<Customer> findByName(String name); // derived
}
// Custom fragment: hand-written traversal no derivation can express.
interface CustomerRepositoryCustom {
    List<String> alsoBoughtByCustomersOf(String productId);
}
interface CustomerRepository extends CustomerRepositoryBase, CustomerRepositoryCustom { }

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    private final Graph graph;
    CustomerRepositoryImpl(Graph graph) { this.graph = graph; }

    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public Optional<Customer> findByName(String name) {
        return nodes.values().stream().filter(c -> c.name.equals(name)).findFirst();
    }
    // Not derivable from a method name -- a genuine two-hop graph traversal.
    public List<String> alsoBoughtByCustomersOf(String productId) {
        Set<String> customersOfProduct = graph.boughtByCustomer.entrySet().stream()
            .filter(e -> e.getValue().contains(productId)).map(Map.Entry::getKey).collect(Collectors.toSet());
        return customersOfProduct.stream()
            .flatMap(id -> graph.boughtByCustomer.get(id).stream())
            .filter(p -> !p.equals(productId)).distinct().collect(Collectors.toList());
    }
}
```

How to run: `java Neo4jRepositoryLevel3.java`

`CustomerRepository` now blends a generated interface (`findByName`, derived automatically) with a custom fragment (`alsoBoughtByCustomersOf`, hand-implemented against the graph) — the same base-plus-custom-fragment composition pattern used for `CassandraRepository` earlier, so one repository interface can expose both routine lookups and bespoke traversals.

## 6. Walkthrough

Execution starts in `main` for Level 3. `graph.link` calls build the same purchase graph as the previous card: `c1` bought `kettle` and `mug`, `c2` bought `kettle` and `teapot`. Two `Customer` nodes are then saved through `repo.save`.

`repo.findByName("Amara")` runs the derived lookup, scanning saved customers for a `name` match and returning `Amara`. `repo.alsoBoughtByCustomersOf("kettle")` runs the custom fragment: it finds customers who bought `kettle` (`c1`, `c2`), then collects their other products (`mug`, `teapot`).

```
By name: Amara
Recommended for kettle buyers: [mug, teapot]
```

In a real Spring Data Neo4j application, `findByName` would be entirely generated at startup from the interface method signature — no implementation class written by hand — while `alsoBoughtByCustomersOf` would live in a `CustomerRepositoryImpl` class that Spring Data automatically detects and wires in as the custom fragment, exactly the composition modeled here.

## 7. Gotchas & takeaways

> Gotcha: a custom fragment interface's implementing class must be named `<RepositoryName>Impl` by default (e.g. `CustomerRepositoryImpl` for `CustomerRepository`) for Spring Data to auto-detect and wire it in — get the suffix wrong and the custom methods silently fail to resolve at startup with a bean-definition error.

> Gotcha: derived query methods that traverse relationships (e.g. `findByOrdersProductName`) can generate deep, expensive Cypher patterns if the mapped entity graph is large — unlike a flat document or row, a graph entity's "shape" can pull in far more nodes than the method name suggests at a glance.

- `Neo4jRepository`/`ReactiveNeo4jRepository` extend the same Spring Data Commons repository abstraction as `MongoRepository`, `JpaRepository`, and `CassandraRepository` — derive-by-method-name works the same way, just compiled to Cypher.
- Reach for the template directly, or a custom fragment, when a traversal is too irregular for name-based derivation to express cleanly.
- Custom fragments compose with generated repository interfaces via a `Base` + `Custom` interface split, exactly as with `CassandraRepository` earlier in this course.
- The blocking/reactive split is consistent with every other Spring Data module covered so far.
