---
card: spring-data
gi: 165
slug: cypher-queries-query
title: "Cypher queries & @Query"
---

## 1. What it is

Cypher is Neo4j's native graph query language — pattern-matching syntax like `(a)-[:KNOWS]->(b)` that reads like an ASCII drawing of the graph you want to match. `@Query` lets a Spring Data Neo4j repository method run hand-written Cypher directly, the same escape hatch `@Query` provided for MongoDB (JSON) and Cassandra (CQL) earlier in this course.

```java
interface CustomerRepository extends Neo4jRepository<Customer, String> {
    @Query("MATCH (c:Customer)-[:BOUGHT]->(:Product {name: $productName}) RETURN c")
    List<Customer> findCustomersWhoBought(String productName);
}
```

## 2. Why & when

Derived method names (two cards back) cover simple property lookups well, but Cypher's pattern-matching syntax is what makes graph traversals expressive — variable-length paths, multiple relationship hops, filtering on properties partway through a path. None of that maps cleanly onto a method name.

Reach for `@Query` with Cypher when:

- The traversal involves more than one relationship hop, or a variable-length path (`-[:KNOWS*1..3]->`).
- You need to shape the result — returning a projection, an aggregate, or a path — rather than a plain mapped entity.
- The query is clearer written as an explicit graph pattern than reverse-engineered from a long derived method name.

## 3. Core concept

```
 MATCH (c:Customer)-[:BOUGHT]->(p:Product {name: $productName})
 RETURN c

   MATCH   -- describes the graph pattern to find
   (c:Customer)             -- a node, labeled Customer, bound to variable c
   -[:BOUGHT]->              -- a directed BOUGHT relationship
   (p:Product {name: $x})    -- a Product node, filtered by property
   RETURN c                  -- what to return: the customer nodes
```

Cypher patterns read left-to-right as a mini "picture" of the graph shape being matched — this is the core mental shift from SQL's table/join thinking or MongoDB's document-filter thinking.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Cypher MATCH pattern mirrors the shape of the graph nodes and relationship it matches">
  <rect x="30" y="20" width="580" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">MATCH (c:Customer)-[:BOUGHT]-&gt;(p:Product {name: $x}) RETURN c</text>

  <rect x="40" y="100" width="150" height="50" rx="25" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="130" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">(c:Customer)</text>

  <line x1="190" y1="125" x2="380" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="285" y="115" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">:BOUGHT</text>
  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="390" y="100" width="200" height="50" rx="25" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="490" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">(p:Product {name:$x})</text>
</svg>

The query text visually mirrors the graph shape it matches, node-by-node and relationship-by-relationship.

## 5. Runnable example

The scenario: finding customers who bought a given product with hand-written Cypher, evolving from a single-hop `@Query` match, to a two-hop recommendation query, to a parameterized query returning a shaped projection instead of a full entity.

### Level 1 — Basic

Model a single-hop `@Query` lookup against an in-memory graph stand-in that interprets a Cypher-like pattern.

```java
import java.util.*;
import java.util.stream.*;

public class CypherQueryLevel1 {
    public static void main(String[] args) {
        Graph graph = new Graph();
        graph.link("c1", "Amara", "BOUGHT", "kettle");
        graph.link("c2", "Bilal", "BOUGHT", "kettle");
        graph.link("c3", "Chidi", "BOUGHT", "mug");

        CustomerRepository repo = new CustomerRepositoryImpl(graph);
        // @Query("MATCH (c:Customer)-[:BOUGHT]->(:Product {name: $productName}) RETURN c")
        List<String> buyers = repo.findCustomersWhoBought("kettle");
        System.out.println("Bought kettle: " + buyers);
    }
}

class Graph {
    record Edge(String customerId, String customerName, String relType, String productName) {}
    List<Edge> edges = new ArrayList<>();
    void link(String customerId, String customerName, String relType, String productName) {
        edges.add(new Edge(customerId, customerName, relType, productName));
    }
}

interface CustomerRepository {
    List<String> findCustomersWhoBought(String productName);
}

// Stands in for Spring Data Neo4j executing the @Query Cypher string above.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Graph graph;
    CustomerRepositoryImpl(Graph graph) { this.graph = graph; }
    public List<String> findCustomersWhoBought(String productName) {
        return graph.edges.stream()
            .filter(e -> e.relType().equals("BOUGHT") && e.productName().equals(productName))
            .map(Graph.Edge::customerName)
            .collect(Collectors.toList());
    }
}
```

How to run: `java CypherQueryLevel1.java`

`findCustomersWhoBought` runs exactly the Cypher pattern in its `@Query` annotation: match a `Customer` connected by `BOUGHT` to a `Product` with the given name, return the customers — a single relationship hop, filtered on the far node's property.

### Level 2 — Intermediate

Extend to a two-hop Cypher pattern: "products bought by customers who also bought X" — the recommendation traversal from earlier cards, now expressed as one declarative Cypher `@Query` instead of hand-written Java traversal logic.

```java
import java.util.*;
import java.util.stream.*;

public class CypherQueryLevel2 {
    public static void main(String[] args) {
        Graph graph = new Graph();
        graph.link("c1", "kettle");
        graph.link("c1", "mug");
        graph.link("c2", "kettle");
        graph.link("c2", "teapot");

        RecommendationRepository repo = new RecommendationRepositoryImpl(graph);
        // @Query("MATCH (:Product {name:$x})<-[:BOUGHT]-(:Customer)-[:BOUGHT]->(rec:Product) " +
        //        "WHERE rec.name <> $x RETURN DISTINCT rec.name")
        List<String> recommended = repo.recommendationsFor("kettle");
        System.out.println("Recommended for kettle buyers: " + recommended);
    }
}

class Graph {
    Map<String, Set<String>> boughtByCustomer = new HashMap<>();
    void link(String customerId, String productName) {
        boughtByCustomer.computeIfAbsent(customerId, k -> new HashSet<>()).add(productName);
    }
}

interface RecommendationRepository {
    List<String> recommendationsFor(String productName);
}

// Stands in for a two-hop Cypher @Query executed by Spring Data Neo4j.
class RecommendationRepositoryImpl implements RecommendationRepository {
    private final Graph graph;
    RecommendationRepositoryImpl(Graph graph) { this.graph = graph; }
    public List<String> recommendationsFor(String productName) {
        Set<String> customers = graph.boughtByCustomer.entrySet().stream()
            .filter(e -> e.getValue().contains(productName)).map(Map.Entry::getKey).collect(Collectors.toSet());
        return customers.stream()
            .flatMap(id -> graph.boughtByCustomer.get(id).stream())
            .filter(p -> !p.equals(productName)).distinct().collect(Collectors.toList());
    }
}
```

How to run: `java CypherQueryLevel2.java`

The commented Cypher walks *out* from the target product to the customers who bought it (`<-[:BOUGHT]-`), then back *out* to those customers' other products (`-[:BOUGHT]->`) — the two-hop "also bought" pattern, now a single declarative query instead of the hand-rolled Java loops used in earlier cards.

### Level 3 — Advanced

Use `@Query` with a shaped projection (not a full entity), parameterized inputs, and a result limit — production-flavored concerns Cypher handles natively.

```java
import java.util.*;
import java.util.stream.*;

public class CypherQueryLevel3 {
    public static void main(String[] args) {
        Graph graph = new Graph();
        graph.link("c1", "kettle", 3);
        graph.link("c1", "mug", 1);
        graph.link("c2", "kettle", 5);
        graph.link("c2", "teapot", 2);
        graph.link("c3", "kettle", 1);

        TopBuyerRepository repo = new TopBuyerRepositoryImpl(graph);
        // @Query("MATCH (c:Customer)-[b:BOUGHT]->(:Product {name:$productName}) " +
        //        "RETURN c.name AS customerName, b.quantity AS quantity " +
        //        "ORDER BY b.quantity DESC LIMIT $limit")
        List<TopBuyer> topBuyers = repo.topBuyersOf("kettle", 2);
        for (TopBuyer tb : topBuyers) System.out.println(tb.customerName() + " bought " + tb.quantity());
    }
}

class Graph {
    record Edge(String customerId, String productName, int quantity) {}
    List<Edge> edges = new ArrayList<>();
    void link(String customerId, String productName, int quantity) {
        edges.add(new Edge(customerId, productName, quantity));
    }
}

record TopBuyer(String customerName, int quantity) {} // shaped projection, not a full @Node entity

interface TopBuyerRepository {
    List<TopBuyer> topBuyersOf(String productName, int limit);
}

// Stands in for a Cypher @Query returning a projection, ordered and limited server-side.
class TopBuyerRepositoryImpl implements TopBuyerRepository {
    private final Graph graph;
    TopBuyerRepositoryImpl(Graph graph) { this.graph = graph; }
    public List<TopBuyer> topBuyersOf(String productName, int limit) {
        return graph.edges.stream()
            .filter(e -> e.productName().equals(productName))
            .sorted((a, b) -> Integer.compare(b.quantity(), a.quantity()))
            .limit(limit)
            .map(e -> new TopBuyer(e.customerId(), e.quantity()))
            .collect(Collectors.toList());
    }
}
```

How to run: `java CypherQueryLevel3.java`

The `@Query` binds two parameters (`$productName`, `$limit`), returns a shaped `TopBuyer` projection instead of a full `Customer` node, and sorts/limits in the query itself rather than in application code — Neo4j's engine does the ordering and truncation before any data leaves the database, exactly like `LIMIT` in SQL or `.limit()` in a MongoDB aggregation pipeline.

## 6. Walkthrough

Execution starts in `main` for Level 3. Five purchase edges are recorded, three of them for `kettle` with quantities 3, 5, and 1. `repo.topBuyersOf("kettle", 2)` runs the Cypher-equivalent query.

The (simulated) Cypher engine matches every `(c:Customer)-[b:BOUGHT]->(:Product {name:'kettle'})` pattern, projects out `c.name` and `b.quantity` (note: `quantity` comes from the *relationship*, matching the relationship-property mapping from the previous card), sorts by `quantity` descending, and returns only the top 2 rows:

```
c2 bought 5
c1 bought 3
```

The request/response shape here is: input parameters `{productName: "kettle", limit: 2}` in, a list of `{customerName, quantity}` projection rows out — no full `Customer` or `Product` entity is ever materialized, because the query explicitly asked for only two scalar fields per row. This is the same "shape only what you need" discipline that projections (a later card in this section) formalize further.

## 7. Gotchas & takeaways

> Gotcha: Cypher relationship patterns are direction-sensitive by default — `(a)-[:BOUGHT]->(b)` and `(a)<-[:BOUGHT]-(b)` match different edges. Omitting the arrow, `(a)-[:BOUGHT]-(b)`, matches the relationship in *either* direction, which is sometimes exactly what's wanted and sometimes a silent bug that returns more rows than intended.

> Gotcha: `@Query` methods bypass Spring Data's automatic result-shape inference in some cases — returning a projection type (like `TopBuyer` above) requires the query's `RETURN` clause to alias its columns to match the projection's property or record-component names, or the mapping silently fails to populate them.

- Cypher's `MATCH` pattern syntax mirrors the graph shape being matched, node-by-node and relationship-by-relationship, which is what makes multi-hop traversals readable compared to nested joins.
- `@Query` is the escape hatch for traversals too irregular for method-name derivation — multi-hop paths, variable-length paths, shaped projections, or explicit ordering/limiting.
- A query can return full mapped entities, records/DTOs as projections, or scalar aggregates, exactly like `@Query` in the MongoDB and Cassandra sections earlier.
- Relationship direction in a pattern is meaningful — get it backwards and a query returns zero rows instead of erroring.
