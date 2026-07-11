---
card: spring-data
gi: 164
slug: node-relationship-mapping-node-relationship-id
title: "Node & relationship mapping (@Node, @Relationship, @Id)"
---

## 1. What it is

`@Node`, `@Relationship`, and `@Id` are the mapping annotations that tell Spring Data Neo4j how a Java class corresponds to a graph node, and how a field referencing another entity corresponds to a graph relationship — the graph-database equivalent of `@Document` and `@Entity` from earlier sections.

```java
@Node
class Customer {
    @Id String id;
    String name;

    @Relationship(type = "BOUGHT", direction = Relationship.Direction.OUTGOING)
    List<Product> products = new ArrayList<>();
}
```

## 2. Why & when

Every earlier mapping annotation in this course (`@Document`, `@Table`, `@Entity`) described how a class maps onto a *record* — a row, a document. `@Node` and `@Relationship` are different in kind: `@Node` still maps a class to a record-like thing (a graph node with properties), but `@Relationship` maps a *field* to an edge connecting two nodes, which has no equivalent in a document or wide-column model.

Reach for these annotations when:

- Defining any entity Spring Data Neo4j should persist as a node — every `@Node`-annotated class needs an `@Id` field, exactly like every other Spring Data module.
- Modeling a connection between two entities as a first-class graph relationship, rather than an embedded reference or foreign key.
- Controlling the relationship's direction and type — `BOUGHT`, `FRIEND_OF`, `MANAGES` — since Neo4j relationships are directed and named.

## 3. Core concept

```
 @Node
 class Customer {
     @Id String id;                                  -- node identity
     String name;                                      -- node property

     @Relationship(type = "BOUGHT",
                   direction = OUTGOING)
     List<Product> products;                            -- outgoing edges to other nodes
 }

 Graph shape:
   (:Customer {id, name}) -[:BOUGHT]-> (:Product {id, name})
```

An `@Node` class becomes a labeled node with its non-relationship fields as properties; an `@Relationship` field becomes a directed, typed edge to another `@Node`-mapped class, which becomes the node at the other end.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Customer node connects via an outgoing BOUGHT relationship to a Product node">
  <rect x="40" y="55" width="180" height="55" rx="27" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">(:Customer)</text>
  <text x="130" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">id, name</text>

  <line x1="220" y1="82" x2="400" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a3)"/>
  <text x="310" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">:BOUGHT</text>
  <defs><marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="410" y="55" width="180" height="55" rx="27" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="500" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">(:Product)</text>
  <text x="500" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">id, name</text>
</svg>

An `@Relationship` field is a directed, typed edge between two `@Node`-mapped classes.

## 5. Runnable example

The scenario: mapping `Customer` and `Product` as graph nodes connected by a `BOUGHT` relationship, evolving from a plain-property node, to a node with an outgoing relationship field, to a relationship carrying its own properties (a purchase date and quantity) via a dedicated relationship-entity class.

### Level 1 — Basic

Define a bare `@Node` with an `@Id`, and show it round-tripping through a stand-in mapper.

```java
import java.util.*;

public class NodeMappingLevel1 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.saveNode(new Customer("c1", "Amara"));

        Customer found = store.findNode("c1", Customer.class);
        System.out.println("Found node: id=" + found.id + " name=" + found.name);
    }
}

// @Node
class Customer {
    // @Id
    String id;
    String name;
    Customer(String id, String name) { this.id = id; this.name = name; }
}

// Stands in for how Spring Data Neo4j stores an @Node-mapped class: a labeled node with properties.
class GraphStore {
    private final Map<String, Object> nodesById = new HashMap<>();
    void saveNode(Customer c) { nodesById.put(c.id, c); }
    @SuppressWarnings("unchecked")
    <T> T findNode(String id, Class<T> type) { return (T) nodesById.get(id); }
}
```

How to run: `java NodeMappingLevel1.java`

`@Id` marks `id` as the node's identity, and every other field (`name`) becomes a node property — the direct graph analogue of `@Id`/`@Field` on `@Document` classes from the MongoDB section.

### Level 2 — Intermediate

Add an `@Relationship`-mapped field so a `Customer` node carries outgoing edges to `Product` nodes.

```java
import java.util.*;

public class NodeMappingLevel2 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        Customer amara = new Customer("c1", "Amara");
        amara.products.add(new Product("p1", "Kettle"));
        amara.products.add(new Product("p2", "Mug"));
        store.saveNode(amara);

        Customer found = store.findNode("c1", Customer.class);
        System.out.println("Customer " + found.name + " bought:");
        for (Product p : found.products) System.out.println("  -> " + p.name);
    }
}

// @Node
class Customer {
    // @Id
    String id;
    String name;

    // @Relationship(type = "BOUGHT", direction = Relationship.Direction.OUTGOING)
    List<Product> products = new ArrayList<>();

    Customer(String id, String name) { this.id = id; this.name = name; }
}

// @Node
class Product {
    // @Id
    String id;
    String name;
    Product(String id, String name) { this.id = id; this.name = name; }
}

class GraphStore {
    private final Map<String, Object> nodesById = new HashMap<>();
    void saveNode(Customer c) { nodesById.put(c.id, c); } // cascades: saves the Customer node AND its BOUGHT edges
    @SuppressWarnings("unchecked")
    <T> T findNode(String id, Class<T> type) { return (T) nodesById.get(id); }
}
```

How to run: `java NodeMappingLevel2.java`

`products` is annotated `@Relationship(type = "BOUGHT", direction = OUTGOING)` — saving `amara` persists the `Customer` node, both `Product` nodes, and two `BOUGHT` edges connecting them, all from one `save()` call, because Spring Data Neo4j walks the mapped object graph and persists everything it finds.

### Level 3 — Advanced

Give the `BOUGHT` relationship its own properties (`purchasedOn`, `quantity`) using a dedicated relationship-entity class — something a plain `List<Product>` field can't express, since a relationship property belongs to the *edge*, not either node.

```java
import java.util.*;
import java.time.*;

public class NodeMappingLevel3 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        Customer amara = new Customer("c1", "Amara");
        amara.purchases.add(new Purchase(new Product("p1", "Kettle"), LocalDate.of(2026, 1, 5), 1));
        amara.purchases.add(new Purchase(new Product("p2", "Mug"), LocalDate.of(2026, 2, 12), 2));
        store.saveNode(amara);

        Customer found = store.findNode("c1", Customer.class);
        System.out.println("Purchase history for " + found.name + ":");
        for (Purchase purchase : found.purchases) {
            System.out.println("  " + purchase.product.name + " x" + purchase.quantity + " on " + purchase.purchasedOn);
        }
    }
}

// @Node
class Customer {
    // @Id
    String id;
    String name;

    // @Relationship(type = "BOUGHT", direction = Relationship.Direction.OUTGOING)
    List<Purchase> purchases = new ArrayList<>(); // relationship WITH properties, not a plain node list

    Customer(String id, String name) { this.id = id; this.name = name; }
}

// @RelationshipProperties -- maps to the edge itself, not to either endpoint node.
class Purchase {
    // @TargetNode
    Product product;
    LocalDate purchasedOn; // property stored ON the BOUGHT relationship
    int quantity;          // property stored ON the BOUGHT relationship

    Purchase(Product product, LocalDate purchasedOn, int quantity) {
        this.product = product; this.purchasedOn = purchasedOn; this.quantity = quantity;
    }
}

// @Node
class Product {
    // @Id
    String id;
    String name;
    Product(String id, String name) { this.id = id; this.name = name; }
}

class GraphStore {
    private final Map<String, Object> nodesById = new HashMap<>();
    void saveNode(Customer c) { nodesById.put(c.id, c); }
    @SuppressWarnings("unchecked")
    <T> T findNode(String id, Class<T> type) { return (T) nodesById.get(id); }
}
```

How to run: `java NodeMappingLevel3.java`

`Purchase` is a relationship-entity: `purchasedOn` and `quantity` are stored as properties *on the `BOUGHT` edge itself*, not on `Customer` or `Product`. `@TargetNode` marks which field the relationship points to. This is a genuinely graph-specific concept — a relational join table could fake it with an associative table, but here it's a native part of the graph model.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two `Purchase` objects are built, each pairing a `Product` with a date and quantity, and added to `amara.purchases`. `store.saveNode(amara)` is called once.

In a real Spring Data Neo4j save, this single call triggers a Cypher write that creates the `Customer` node, both `Product` nodes (if not already present), and two `BOUGHT` relationships — each carrying its own `purchasedOn` and `quantity` properties directly on the edge:

```
CREATE (c:Customer {id:'c1', name:'Amara'})
CREATE (p1:Product {id:'p1', name:'Kettle'})
CREATE (p2:Product {id:'p2', name:'Mug'})
CREATE (c)-[:BOUGHT {purchasedOn: date('2026-01-05'), quantity: 1}]->(p1)
CREATE (c)-[:BOUGHT {purchasedOn: date('2026-02-12'), quantity: 2}]->(p2)
```

`store.findNode("c1", Customer.class)` reconstructs `amara` with both `Purchase` relationship-entities re-hydrated, and the loop prints each one:

```
Purchase history for Amara:
  Kettle x1 on 2026-01-05
  Mug x2 on 2026-02-12
```

Every layer of this round trip — Java object graph in, Cypher write, Cypher read, Java object graph out — preserves the fact that `purchasedOn`/`quantity` live on the relationship, not on either node, exactly the way a real `(:Customer)-[:BOUGHT]->(:Product)` graph stores them.

## 7. Gotchas & takeaways

> Gotcha: relationship-entity classes (`@RelationshipProperties`) require exactly one field annotated `@TargetNode` pointing at the other end of the edge — omit it, and Spring Data Neo4j can't tell which mapped field is the relationship's endpoint versus just another property.

> Gotcha: `@Relationship` direction matters for both querying and saving. An `OUTGOING` relationship on `Customer` pointing to `Product` is the *same* underlying edge as an `INCOMING` relationship declared on `Product` pointing back to `Customer` — get the direction backwards on one side and traversals silently return nothing instead of erroring.

- `@Node` maps a class to a graph node; `@Id` marks its identity, exactly like every other Spring Data module's identifier annotation.
- `@Relationship` maps a field to a directed, typed edge — the concept with no equivalent in document or wide-column mapping covered earlier in this course.
- A relationship can carry its own properties via a dedicated `@RelationshipProperties` class with a `@TargetNode` field, when the connection itself has data (a date, a weight, a role).
- Saving a mapped entity cascades through its `@Relationship` fields, persisting connected nodes and edges in one call — powerful, but worth scoping carefully on deeply connected graphs.
