---
card: data-structures
gi: 143
slug: modeling-a-graph-in-java-map-v-list-v
title: 'Modeling a graph in Java (Map<V, List<V>>)'
---

## 1. What it is

Java has no built-in `Graph` class in `java.util`. The standard, idiomatic way to model one is `Map<V, List<V>>` — a map from each vertex to a list of its neighbors — built entirely out of ordinary collection types you already know: `HashMap`, `ArrayList`, and (for weighted graphs) a small record.

## 2. Why & when

Every graph algorithm you write in Java (BFS, DFS, Dijkstra's, topological sort) needs some concrete Java type to operate on. `Map<V, List<V>>` is the practical, idiomatic answer — it directly implements the adjacency-list concept using stock collections, requires no external library, and every method you need (`get`, `computeIfAbsent`, iteration) is already familiar.

## 3. Core concept

**Building it.** `Map<String, List<String>> graph = new HashMap<>();` Adding an edge uses `computeIfAbsent` to create a vertex's list on first use, then appends: `graph.computeIfAbsent(from, key -> new ArrayList<>()).add(to);`. For an undirected graph, add both directions; for directed, only one.

**Querying it.** `graph.getOrDefault(vertex, List.of())` is the standard defensive pattern for "give me this vertex's neighbors, or an empty list if it has none" — this avoids a `NullPointerException` for vertices that were never added as a key (e.g. a vertex with in-edges only, never itself used as a `from`).

**Extending to weighted graphs.** Swap `List<String>` for `List<Edge>`, where `record Edge(String to, int weight) {}` bundles a neighbor with its edge weight. Everything else about the structure (the outer map, `computeIfAbsent`, `getOrDefault`) stays exactly the same — only the list's element type changes.

**Choosing the vertex type.** Using `String` vertex names (as in most of these examples) is simplest for small demos. For a graph with many vertices where identity matters (not just equal names), a dedicated class with proper `equals`/`hashCode`, or plain integer indices into an array, often performs better and avoids accidental key collisions.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap of String to ArrayList of String representing a graph, with keys A, B, C each mapping to their own neighbor list">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">Map&lt;String, List&lt;String&gt;&gt; graph</text>
    <rect x="20" y="30" width="580" height="100" fill="#0d1117" stroke="#79c0ff"/>
    <text x="60" y="55" fill="#79c0ff" font-size="10">"A"</text>
    <text x="150" y="55" fill="#e6edf3" font-size="10">-&gt; ["B", "C"]</text>
    <text x="60" y="80" fill="#79c0ff" font-size="10">"B"</text>
    <text x="150" y="80" fill="#e6edf3" font-size="10">-&gt; ["A", "C"]</text>
    <text x="60" y="105" fill="#79c0ff" font-size="10">"C"</text>
    <text x="150" y="105" fill="#e6edf3" font-size="10">-&gt; ["A", "B"]</text>
    <text x="300" y="160" fill="#8b949e" text-anchor="middle" font-size="9">HashMap keys = vertices; each value is a plain ArrayList of neighbor names</text>
  </g>
</svg>

The whole graph lives in one `HashMap`: each vertex is a key, and its value is an `ArrayList` of its neighbors — no custom `Graph` class required.

## 5. Runnable example

```java
// GraphInJava.java
import java.util.*;

public class GraphInJava {

    // Basic: build and query an unweighted, undirected graph using Map<String, List<String>>.
    static void basicLevel() {
        Map<String, List<String>> graph = new HashMap<>();
        graph.computeIfAbsent("A", key -> new ArrayList<>()).add("B");
        graph.computeIfAbsent("B", key -> new ArrayList<>()).add("A"); // undirected: add both directions
        graph.computeIfAbsent("A", key -> new ArrayList<>()).add("C");
        graph.computeIfAbsent("C", key -> new ArrayList<>()).add("A");

        System.out.println("basic: A's neighbors -> " + graph.get("A"));
        System.out.println("basic: getOrDefault for a vertex never added as a key -> " + graph.getOrDefault("Z", List.of()));
    }

    // Intermediate: a small helper class wrapping the Map, for a cleaner API than raw computeIfAbsent calls everywhere.
    static class Graph {
        Map<String, List<String>> adjacency = new HashMap<>();

        void addEdge(String from, String to, boolean undirected) {
            adjacency.computeIfAbsent(from, key -> new ArrayList<>()).add(to);
            if (undirected) adjacency.computeIfAbsent(to, key -> new ArrayList<>()).add(from);
        }

        List<String> neighborsOf(String vertex) {
            return adjacency.getOrDefault(vertex, List.of()); // defensive default -- never throws for an unknown vertex
        }
    }

    static void intermediateLevel() {
        Graph graph = new Graph();
        graph.addEdge("A", "B", true);
        graph.addEdge("B", "C", true);

        System.out.println("intermediate: neighborsOf(B) -> " + graph.neighborsOf("B"));
        System.out.println("intermediate: neighborsOf(unknownVertex) -> " + graph.neighborsOf("unknownVertex") + " (empty, not an exception)");
    }

    // Advanced: a weighted, directed graph, using a small record for each adjacency entry.
    record WeightedEdge(String to, int weight) {}

    static class WeightedGraph {
        Map<String, List<WeightedEdge>> adjacency = new HashMap<>();

        void addEdge(String from, String to, int weight) {
            adjacency.computeIfAbsent(from, key -> new ArrayList<>()).add(new WeightedEdge(to, weight));
        }

        List<WeightedEdge> neighborsOf(String vertex) {
            return adjacency.getOrDefault(vertex, List.of());
        }
    }

    static void advancedLevel() {
        WeightedGraph graph = new WeightedGraph();
        graph.addEdge("A", "B", 5);
        graph.addEdge("A", "C", 2);

        System.out.println("advanced: A's weighted neighbors -> " + graph.neighborsOf("A"));
        int totalOutgoingWeight = graph.neighborsOf("A").stream().mapToInt(WeightedEdge::weight).sum();
        System.out.println("advanced: total weight of A's outgoing edges -> " + totalOutgoingWeight);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `GraphInJava.java`, then run `java GraphInJava.java`.

## 6. Walkthrough

1. `basicLevel()` builds a small undirected graph directly with `computeIfAbsent` calls, adding both directions for each edge. `graph.get("A")` returns `["B", "C"]`. `graph.getOrDefault("Z", List.of())` demonstrates the defensive pattern: `"Z"` was never added as a key, so a plain `graph.get("Z")` would return `null`, but `getOrDefault` returns a safe empty list instead.
2. `intermediateLevel()` wraps the same `Map`-based storage in a small `Graph` class with an `addEdge` method (handling the undirected-vs-directed choice explicitly) and a `neighborsOf` method that always uses `getOrDefault` internally, so callers never need to worry about `null`.
3. `advancedLevel()` extends the pattern to a weighted, directed graph by swapping `List<String>` for `List<WeightedEdge>`. `neighborsOf("A")` returns the list of `WeightedEdge` records, and a simple stream sums their weights — showing how naturally the same `Map`-based structure extends once each adjacency entry carries more than just a name.

## 7. Gotchas & takeaways

> Gotcha: using `graph.get(vertex)` directly, without `getOrDefault`, throws a `NullPointerException` the moment you query a vertex that was never added as a map key — this commonly happens for a vertex that only ever appears as someone else's *target*, never as a `from`. Always default to an empty list for vertices that might not be present as a key.

- `Map<V, List<V>>` (built from `HashMap` and `ArrayList`) is the idiomatic, no-dependency way to model a graph in Java.
- `computeIfAbsent` is the standard pattern for adding an edge, lazily creating each vertex's list on first use.
- `getOrDefault(vertex, List.of())` avoids `NullPointerException` for vertices that exist only as edge targets, never as a map key.
- Related concepts: [Adjacency list](0140-adjacency-list.md), [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md).
