---
card: system-design
gi: 78
slug: graph-databases
title: Graph databases
---

## 1. What it is

A **graph database** stores data as **nodes** (entities) and **edges** (relationships between them), both of which can carry their own properties. Unlike a relational database, where a relationship between rows requires a join at query time, a graph database stores each relationship as a direct, traversable pointer, making it fast to answer questions about how entities connect, even across many hops. Neo4j is the most widely used example.

## 2. Why & when

A relational join gets more expensive the more tables (or hops) it has to cross — finding "friends of friends of friends" means chaining several joins together, each one scanning and matching rows. A graph database stores the relationship itself as a first-class, directly-followable pointer, so traversing multiple hops is close to a constant-time pointer-following operation per hop, regardless of how large the overall dataset is. Use one whenever the core value of your data is in the connections themselves: social networks, recommendation engines ("people who bought X also bought Y"), fraud detection (finding rings of related accounts), or dependency graphs.

## 3. Core concept

**Nodes, edges, and properties:** a node might represent a `Person` with properties `name` and `age`; an edge might represent a `FOLLOWS` relationship between two `Person` nodes, itself optionally carrying properties like `since`. Both nodes and edges are typed and can hold arbitrary key-value properties.

**Why traversal is fast — direct pointers, not re-computed joins:** in a relational database, "find this person's friends" means a join matching a foreign key; "find friends of friends" means joining again, against a growing intermediate result. In a graph database, each node already directly references its connected edges, so following a relationship is just walking a pointer — the cost of one more hop does not depend on the size of the whole graph, only on how many edges that specific node has.

**Index-free adjacency:** the term for this direct-pointer traversal is "index-free adjacency" — a node's relationships are stored physically alongside it, so the database does not need a secondary index lookup to find them, unlike following a foreign key in a relational table.

**Where a graph database is a poor fit:** aggregating over the whole dataset (sum, average, group-by across millions of unrelated rows) is not what a graph database is optimized for — that is squarely a relational or analytical database's strength. Graph databases specialize in relationship-heavy traversal queries, not bulk aggregation.

## 4. Diagram

```
Nodes and edges, with index-free adjacency:

  (Alice) --FOLLOWS--> (Bob) --FOLLOWS--> (Cid) --FOLLOWS--> (Dee)
     |                                                          
     +--FOLLOWS--> (Eve)

  "friends of friends of Alice" (2 hops):
    Alice -> Bob (hop 1) -> Cid (hop 2)     result: Cid
    Alice -> Eve (hop 1) -> (no further edges)

  Each hop follows a DIRECT pointer already attached to the current node -
  no join, no secondary lookup, regardless of how many total nodes exist in the graph.
```
*Caption: each traversal hop follows a pointer already stored on the node, so cost depends on that node's own connections, not the size of the whole graph.*

## 5. Runnable example

**Level 1 — Basic.** Model nodes and directed edges as an adjacency list, mirroring index-free adjacency.

**Level 2 — Multi-hop traversal.** Follow relationships two hops deep (breadth-first), the way "friends of friends" is answered.

**Level 3 — Edge properties.** Attach a property to each edge (`since`) and filter a traversal by it.

```java
// GraphDatabases.java
import java.util.*;

public class GraphDatabases {

    record Edge(String to, String relationship, int since) {}

    // Level 1: index-free adjacency - each node's outgoing edges are stored directly WITH it.
    static final Map<String, List<Edge>> graph = new HashMap<>();

    static void addEdge(String from, String to, String relationship, int since) {
        graph.computeIfAbsent(from, n -> new ArrayList<>()).add(new Edge(to, relationship, since));
    }

    public static void main(String[] args) {
        addEdge("Alice", "Bob", "FOLLOWS", 2021);
        addEdge("Alice", "Eve", "FOLLOWS", 2023);
        addEdge("Bob", "Cid", "FOLLOWS", 2019);
        addEdge("Cid", "Dee", "FOLLOWS", 2020);

        // Level 1: one hop - direct pointer-follow, no join.
        System.out.println("Alice directly follows: " + graph.get("Alice").stream().map(Edge::to).toList());

        // Level 2: two-hop traversal ("friends of friends"), breadth-first.
        String start = "Alice";
        int hops = 2;
        Set<String> visited = new LinkedHashSet<>();
        Queue<String> frontier = new LinkedList<>();
        frontier.add(start);
        visited.add(start);

        for (int hop = 1; hop <= hops; hop++) {
            Queue<String> nextFrontier = new LinkedList<>();
            for (String node : frontier) {
                for (Edge edge : graph.getOrDefault(node, List.of())) {
                    if (visited.add(edge.to())) { // each hop just follows the pointer already on this node
                        nextFrontier.add(edge.to());
                    }
                }
            }
            frontier = nextFrontier;
        }
        visited.remove(start);
        System.out.println("within " + hops + " hops of Alice: " + visited);

        // Level 3: filter a traversal by an edge property - "who has Alice followed since before 2022?".
        System.out.println("Alice's follows established before 2022 (filtering by edge property 'since'):");
        for (Edge e : graph.get("Alice")) {
            if (e.since() < 2022) {
                System.out.println("  " + e.to() + " (since " + e.since() + ")");
            }
        }
    }
}
```

**How to run:** save as `GraphDatabases.java`, then run `java GraphDatabases.java`.

## 6. Walkthrough

1. `graph` stores each node's outgoing edges directly alongside it — `graph.get("Alice")` returns Alice's edges with no separate lookup, mirroring index-free adjacency.
2. The one-hop query, `graph.get("Alice").stream().map(Edge::to)`, returns `[Bob, Eve]` directly, in constant work relative to the size of the whole graph.
3. The breadth-first loop expands one hop at a time: hop 1 visits `Bob` and `Eve` (Alice's direct edges); hop 2 expands from `Bob` and `Eve`, finding `Cid` (via `Bob`'s edge) — `Eve` has no outgoing edges in this graph, so that branch adds nothing.
4. The final `visited` set (with `Alice` removed) is `{Bob, Eve, Cid}` — everyone reachable within two hops — found by following pointers already attached to each node visited, never by re-scanning the whole graph.
5. The edge-property filter iterates only Alice's own edges and checks each one's `since` field, printing only `Bob (since 2021)` — `Eve`'s edge, `since 2023`, is correctly excluded.

## 7. Gotchas & takeaways

> Gotcha: a graph database's traversal speed advantage only applies to relationship-following queries; asking it to aggregate across the entire dataset (e.g. "average number of followers across all users") generally performs worse than a relational or analytical database purpose-built for bulk scans — pick the tool for the query shape you actually need.

- Graph databases make multi-hop relationship traversal fast and roughly constant-cost per hop, by storing each relationship as a direct, pre-linked pointer instead of requiring a join at query time.
- This specialization is a trade-off, not a universal upgrade: they are a poor fit for bulk aggregation across unrelated rows.
- Related concepts: [Tables, rows, keys & relationships](0062-tables-rows-keys-relationships.md) (the relational alternative, where the same relationships require a join at query time), [When to choose SQL vs NoSQL](0083-when-to-choose-sql-vs-nosql.md) (the broader decision graph databases are one option within).
