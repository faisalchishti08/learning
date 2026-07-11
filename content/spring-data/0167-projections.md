---
card: spring-data
gi: 167
slug: projections
title: "Projections"
---

## 1. What it is

Projections in Spring Data Neo4j let a repository method return a shaped subset of a node's data — an interface or record covering only the fields actually needed — instead of always hydrating the full mapped entity and its relationships. This is the same projection concept from the MongoDB and JPA sections earlier, applied to graph nodes.

```java
interface CustomerNameOnly {
    String getName();
}

interface CustomerRepository extends Neo4jRepository<Customer, String> {
    List<CustomerNameOnly> findByCity(String city);
}
```

## 2. Why & when

A full `Customer` entity, if it has `@Relationship` fields, can pull in connected `Product` nodes, `Purchase` relationship-entities, and whatever *those* connect to — a much larger fetch than a caller who just wants a list of names actually needs. Projections let the query return only the requested shape, which for a graph entity often means skipping relationship traversal entirely.

Reach for projections when:

- A view or API endpoint only needs a few fields, and pulling the full connected entity graph would be wasteful.
- Returning data across a relationship without materializing the related side as a full mapped entity — e.g., a customer's name plus just the *count* of products they bought, not the products themselves.
- Composing `@Query` results into a shape that doesn't match any `@Node` entity, using a DTO/record projection.

## 3. Core concept

```
 Full entity fetch:                    Projection fetch:

 Customer                               CustomerSummary
  id, name,                              name,
  [BOUGHT]-> Product...                  productCount
  (walks relationships)                  (no relationship walk needed)

 findByCity(city) -> List<Customer>     findByCity(city) -> List<CustomerSummary>
   pulls full graph per match             pulls only requested fields
```

The query only fetches what the projection's interface or record actually declares — fewer fields and no unnecessary relationship traversal.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A full entity fetch walks relationships while a projection fetch returns only requested fields">
  <rect x="20" y="20" width="270" height="110" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="40" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Full entity</text>
  <text x="155" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">id, name</text>
  <text x="155" y="85" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">[BOUGHT]-&gt; Product, Product...</text>
  <text x="155" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">walks relationships</text>

  <rect x="350" y="20" width="270" height="110" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Projection</text>
  <text x="485" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">name, productCount</text>
  <text x="485" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no relationship walk needed</text>
</svg>

A projection declares only the fields it needs, letting the query skip unnecessary relationship traversal.

## 5. Runnable example

The scenario: exposing customer data through progressively leaner projection shapes, evolving from a full entity fetch, to an interface-based name-only projection, to a record-based DTO projection that aggregates across a relationship without materializing the related nodes.

### Level 1 — Basic

Model fetching the full `Customer` entity, including its connected products, to establish the baseline being optimized away.

```java
import java.util.*;

public class ProjectionsLevel1 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        Customer amara = new Customer("c1", "Amara", "Lagos");
        amara.products = List.of("kettle", "mug");
        store.save(amara);

        Customer found = store.findById("c1");
        System.out.println("Full fetch: name=" + found.name + " city=" + found.city + " products=" + found.products);
    }
}

class Customer {
    String id, name, city;
    List<String> products = new ArrayList<>();
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java ProjectionsLevel1.java`

`findById` returns the entire `Customer`, including its `products` relationship list — fine here, but wasteful if a caller only ever needed the name.

### Level 2 — Intermediate

Add an interface-based projection that returns only the customer's name, and a repository method that returns the projection type directly instead of the full entity.

```java
import java.util.*;
import java.util.stream.*;

public class ProjectionsLevel2 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", "Lagos"));
        store.save(new Customer("c2", "Bilal", "Lagos"));
        store.save(new Customer("c3", "Chidi", "Abuja"));

        CustomerRepository repo = new CustomerRepositoryImpl(store);
        List<CustomerNameOnly> names = repo.findByCity("Lagos");
        for (CustomerNameOnly n : names) System.out.println("Name only: " + n.getName());
    }
}

class Customer {
    String id, name, city;
    Customer(String id, String name, String city) { this.id = id; this.name = name; this.city = city; }
}

interface CustomerNameOnly { String getName(); } // projection: only the name field is fetched

class CustomerNameOnlyImpl implements CustomerNameOnly {
    private final String name;
    CustomerNameOnlyImpl(String name) { this.name = name; }
    public String getName() { return name; }
}

interface CustomerRepository { List<CustomerNameOnly> findByCity(String city); }

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    List<Customer> allByCity(String city) {
        return nodes.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final GraphStore store;
    CustomerRepositoryImpl(GraphStore store) { this.store = store; }
    public List<CustomerNameOnly> findByCity(String city) {
        // Only projects "name" out of each matched node -- no product relationship walked.
        return store.allByCity(city).stream()
            .map(c -> (CustomerNameOnly) new CustomerNameOnlyImpl(c.name))
            .collect(Collectors.toList());
    }
}
```

How to run: `java ProjectionsLevel2.java`

`findByCity` now returns `List<CustomerNameOnly>` — Spring Data Neo4j generates a Cypher query that returns only `c.name` per matched node, never touching any `BOUGHT` relationships, because the projection interface never asked for `products`.

### Level 3 — Advanced

Use a record-based DTO projection that aggregates a *count* across a relationship, without materializing the related `Product` nodes at all — a shape no full entity fetch could produce directly.

```java
import java.util.*;
import java.util.stream.*;

public class ProjectionsLevel3 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", "Lagos", List.of("kettle", "mug")));
        store.save(new Customer("c2", "Bilal", "Lagos", List.of("kettle")));
        store.save(new Customer("c3", "Chidi", "Abuja", List.of()));

        CustomerRepository repo = new CustomerRepositoryImpl(store);
        // @Query("MATCH (c:Customer {city:$city})-[:BOUGHT]->(p:Product) " +
        //        "RETURN c.name AS name, count(p) AS productCount")
        List<CustomerSummary> summaries = repo.summariesByCity("Lagos");
        for (CustomerSummary s : summaries) System.out.println(s.name() + " bought " + s.productCount() + " product(s)");
    }
}

class Customer {
    String id, name, city;
    List<String> products;
    Customer(String id, String name, String city, List<String> products) {
        this.id = id; this.name = name; this.city = city; this.products = products;
    }
}

record CustomerSummary(String name, int productCount) {} // DTO projection aggregating across a relationship

interface CustomerRepository { List<CustomerSummary> summariesByCity(String city); }

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    List<Customer> allByCity(String city) {
        return nodes.values().stream().filter(c -> c.city.equals(city)).collect(Collectors.toList());
    }
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final GraphStore store;
    CustomerRepositoryImpl(GraphStore store) { this.store = store; }
    public List<CustomerSummary> summariesByCity(String city) {
        // Cypher's count(p) aggregates BOUGHT relationships server-side; individual Product nodes never materialize.
        return store.allByCity(city).stream()
            .map(c -> new CustomerSummary(c.name, c.products.size()))
            .collect(Collectors.toList());
    }
}
```

How to run: `java ProjectionsLevel3.java`

`CustomerSummary` pairs `name` with `productCount`, computed by Cypher's `count(p)` aggregation directly in the query — the individual `Product` nodes are traversed to be counted but never returned or mapped into Java objects, which is cheaper than fetching a full `List<Product>` just to call `.size()` on it in application code.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `Customer` nodes are saved, two in `Lagos`, one with two products and one with one. `repo.summariesByCity("Lagos")` runs the (simulated) aggregating Cypher query.

In a real Spring Data Neo4j deployment, the request is the Cypher query with `city: "Lagos"` bound, and Neo4j's engine matches each `Customer` node in Lagos, follows its `BOUGHT` edges only far enough to count them, and returns two scalar columns per row — `name` and `productCount` — never materializing the `Product` nodes on the other end:

```
Amara bought 2 product(s)
Bilal bought 1 product(s)
```

Compare this to Level 1's full fetch: there, `found.products` held the entire list of product names, fetched and transferred in full even if the caller only needed the count. The projection collapses "fetch relationship, then count in Java" into "count during the graph traversal, return only the number" — less data moved, less mapping work on the way back.

## 7. Gotchas & takeaways

> Gotcha: interface-based *closed* projections (declaring only getters, like `CustomerNameOnly`) are the safe default, but an *open* projection using `@Value("#{target.name + ' from ' + target.city}")` SpEL expressions still forces the full entity to be fetched underneath before the expression evaluates — it doesn't save any traversal work, only reshapes the output.

> Gotcha: record-based DTO projections used with `@Query` require the query's `RETURN` column aliases to exactly match the record's component names (`AS productCount` must match `productCount()`), or Spring Data can't bind the aggregated values into the record.

- Projections return a shaped subset of a node's fields, skipping relationship traversal the shape doesn't ask for — cheaper than fetching the full entity and discarding parts of it in application code.
- DTO/record projections combined with `@Query` aggregations (like `count(p)`) let a relationship be summarized server-side without materializing the related nodes at all.
- Closed interface projections (getters only) are safest and most efficient; open (SpEL) projections still fetch the full entity underneath.
- The same projection concept from MongoDB and JPA applies here — Spring Data Neo4j just fetches less of the graph instead of fewer document fields or table columns.
