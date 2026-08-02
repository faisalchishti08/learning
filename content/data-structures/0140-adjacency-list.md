---
card: data-structures
gi: 140
slug: adjacency-list
title: Adjacency list
---

## 1. What it is

An **adjacency list** represents a graph as a map (or array) from each vertex to a list of its neighbors. Vertex `A`'s entry directly lists every vertex `A` has an edge to, without wasting space on the vertices `A` is *not* connected to.

## 2. Why & when

An adjacency list is the default choice for most graph algorithms, because it uses memory proportional to the number of edges actually present (`O(V + E)`, for `V` vertices and `E` edges), rather than the number of *possible* edges. For a **sparse** graph — one where most vertex pairs have no edge, which describes the vast majority of real-world graphs (a social network, a road map, a dependency graph) — this is far more memory-efficient than an [adjacency matrix](0141-adjacency-matrix.md).

## 3. Core concept

**The structure's shape.** A `Map<Vertex, List<Vertex>>` (or, for a weighted graph, `Map<Vertex, List<Edge>>` where `Edge` bundles a target and a weight). Each key's list holds exactly the vertices it connects to — nothing more.

**How the invariant makes operations fast.** "Who are `A`'s neighbors?" costs `O(degree of A)` — you simply read `A`'s list directly, never touching any other vertex's data. This is the operation adjacency lists are built for, and it is the one every traversal algorithm (BFS, DFS) repeatedly performs.

**The tradeoff: checking a specific edge is slower.** "Does an edge from `A` to `B` exist?" requires scanning `A`'s entire neighbor list (`O(degree of A)`), unless that list is itself backed by a `Set` instead of a plain `List` — in which case it becomes `O(1)` average, at the cost of losing insertion order and gaining hashing overhead. An adjacency matrix answers this specific question in guaranteed `O(1)`, which is its main advantage over a list.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small graph next to its adjacency list representation, showing each vertex mapped only to its actual neighbors">
  <g font-family="sans-serif" font-size="11">
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="112" y1="50" x2="188" y2="35" stroke="#79c0ff" stroke-width="2"/>
    <line x1="112" y1="70" x2="188" y2="85" stroke="#79c0ff" stroke-width="2"/>
    <line x1="200" y1="46" x2="200" y2="74" stroke="#79c0ff" stroke-width="2"/>
    <rect x="330" y="15" width="280" height="120" fill="#0d1117" stroke="#79c0ff"/>
    <text x="470" y="35" fill="#e6edf3" text-anchor="middle" font-size="9">A -&gt; [B, C]</text>
    <text x="470" y="60" fill="#e6edf3" text-anchor="middle" font-size="9">B -&gt; [A, C]</text>
    <text x="470" y="85" fill="#e6edf3" text-anchor="middle" font-size="9">C -&gt; [A, B]</text>
    <text x="470" y="115" fill="#8b949e" text-anchor="middle" font-size="8">only actual neighbors stored -- no wasted entries</text>
  </g>
</svg>

Each vertex's list contains exactly its real neighbors, no more — `A`'s list has 2 entries, not `n` entries with mostly "no edge" markers.

## 5. Runnable example

```java
// AdjacencyList.java
import java.util.*;

public class AdjacencyList {

    // Basic: build an undirected adjacency list, adding both directions per edge.
    static Map<String, List<String>> buildUndirected(List<String[]> edges) {
        Map<String, List<String>> graph = new HashMap<>();
        for (String[] edge : edges) {
            graph.computeIfAbsent(edge[0], key -> new ArrayList<>()).add(edge[1]);
            graph.computeIfAbsent(edge[1], key -> new ArrayList<>()).add(edge[0]);
        }
        return graph;
    }

    static void basicLevel() {
        Map<String, List<String>> graph = buildUndirected(List.of(
            new String[]{"A", "B"}, new String[]{"A", "C"}, new String[]{"B", "C"}));

        System.out.println("basic: A's neighbors -> " + graph.get("A"));
        System.out.println("basic: B's neighbors -> " + graph.get("B"));
    }

    // Intermediate: a weighted adjacency list -- each entry pairs a neighbor with the edge's weight.
    record WeightedEdge(String to, int weight) {}

    static Map<String, List<WeightedEdge>> buildWeighted(List<Object[]> edges) {
        Map<String, List<WeightedEdge>> graph = new HashMap<>();
        for (Object[] edge : edges) {
            String from = (String) edge[0], to = (String) edge[1];
            int weight = (int) edge[2];
            graph.computeIfAbsent(from, key -> new ArrayList<>()).add(new WeightedEdge(to, weight));
        }
        return graph;
    }

    static void intermediateLevel() {
        Map<String, List<WeightedEdge>> graph = buildWeighted(List.of(
            new Object[]{"A", "B", 5}, new Object[]{"A", "C", 2}));

        System.out.println("intermediate: A's weighted edges -> " + graph.get("A"));
    }

    // Advanced: checking "does an edge exist" costs O(degree) with a List -- confirm the cost by counting comparisons.
    static boolean hasEdgeWithCount(Map<String, List<String>> graph, String from, String to, int[] comparisons) {
        for (String neighbor : graph.getOrDefault(from, List.of())) {
            comparisons[0]++;
            if (neighbor.equals(to)) return true;
        }
        return false;
    }

    static void advancedLevel() {
        Map<String, List<String>> graph = buildUndirected(List.of(
            new String[]{"A", "B"}, new String[]{"A", "C"}, new String[]{"A", "D"}, new String[]{"A", "E"}));

        int[] comparisons = {0};
        boolean found = hasEdgeWithCount(graph, "A", "E", comparisons);
        System.out.println("advanced: hasEdge(A, E) -> " + found + ", comparisons needed -> " + comparisons[0]
            + " (had to scan through A's whole neighbor list -- O(degree), not O(1))");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AdjacencyList.java`, then run `java AdjacencyList.java`.

## 6. Walkthrough

1. `basicLevel()` builds an undirected graph from three edges. Each `computeIfAbsent` call creates a vertex's list on first use; each edge appends to both endpoints' lists, since the graph is undirected. `A`'s neighbor list correctly comes out as `[B, C]`.
2. `intermediateLevel()` builds a weighted version, where each list entry is a small `WeightedEdge` record instead of a bare vertex name — the same list-based structure, carrying one extra field per entry.
3. `advancedLevel()` checks whether an edge from `A` to `E` exists by scanning `A`'s neighbor list linearly, counting comparisons along the way. Since `E` happens to be the last entry added, the scan needs to check all `4` entries before confirming the edge exists — concretely demonstrating the `O(degree)` cost of an edge-existence check on a list-backed representation, in contrast to an adjacency matrix's guaranteed `O(1)`.

## 7. Gotchas & takeaways

> Gotcha: using a plain `List` for neighbors is fine for traversal-heavy algorithms (BFS, DFS), but if your algorithm frequently checks "does this specific edge exist," a `Set` per vertex (trading away insertion order) turns that check from `O(degree)` into `O(1)` average — pick based on which operation your algorithm actually needs most.

- An adjacency list uses `O(V + E)` memory — proportional to the edges actually present, ideal for sparse graphs.
- Listing a vertex's neighbors costs `O(degree of that vertex)` — the operation this representation is optimized for.
- Checking whether a specific edge exists costs `O(degree)` with a list-backed representation (or `O(1)` if you swap in a `Set` per vertex) — worse than an adjacency matrix's guaranteed `O(1)`.
- Related concepts: [Adjacency matrix](0141-adjacency-matrix.md), [Edge list](0142-edge-list.md), [Modeling a graph in Java (Map<V, List<V>>)](0143-modeling-a-graph-in-java-map-v-list-v.md).
