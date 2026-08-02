---
card: data-structures
gi: 142
slug: edge-list
title: Edge list
---

## 1. What it is

An **edge list** represents a graph as a flat collection of edges — each one simply a pair (or triple, if weighted) `(from, to)` or `(from, to, weight)`. There is no per-vertex structure at all; the graph is just "here is every edge that exists."

## 2. Why & when

An edge list is the simplest possible representation, and the most compact for storage or transmission — reading a graph from a file often naturally produces a list of edges (one per line). It is also the natural input format for algorithms that process edges independently of vertex structure, most notably **Kruskal's minimum spanning tree algorithm**, which sorts all edges by weight and processes them one at a time using Union-Find. It is a poor fit, however, for anything that needs to repeatedly ask "who are this vertex's neighbors?"

## 3. Core concept

**The structure's shape.** A plain list of edges: `List<Edge>` where `Edge` bundles `from`, `to`, and (optionally) `weight`. No vertex has its own dedicated storage — the same vertex name can appear in many different edge entries scattered throughout the list.

**Why this is ideal for edge-centric algorithms.** Kruskal's algorithm needs to consider edges **in weight order**, globally, regardless of which vertices they touch — sorting a flat edge list by weight is exactly the operation it needs, and no other representation makes this as direct.

**Why this is a poor fit for vertex-centric algorithms.** "Who are vertex `A`'s neighbors?" requires scanning the *entire* edge list, checking every single edge for whether it touches `A` — `O(E)` for `E` total edges, regardless of `A`'s actual degree. Both an [adjacency list](0140-adjacency-list.md) (`O(degree)`) and an [adjacency matrix](0141-adjacency-matrix.md) (`O(V)`) answer this faster.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small weighted graph next to its edge list representation, a flat list of from, to, weight triples with no per vertex grouping">
  <g font-family="sans-serif" font-size="11">
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="112" y1="50" x2="188" y2="35" stroke="#79c0ff" stroke-width="2"/>
    <line x1="112" y1="70" x2="188" y2="85" stroke="#79c0ff" stroke-width="2"/>
    <text x="150" y="20" fill="#79c0ff" font-size="9">3</text>
    <text x="150" y="95" fill="#79c0ff" font-size="9">7</text>

    <rect x="330" y="15" width="280" height="90" fill="#0d1117" stroke="#79c0ff"/>
    <text x="470" y="35" fill="#e6edf3" text-anchor="middle" font-size="9">(A, B, 3)</text>
    <text x="470" y="60" fill="#e6edf3" text-anchor="middle" font-size="9">(A, C, 7)</text>
    <text x="470" y="90" fill="#8b949e" text-anchor="middle" font-size="8">flat list -- no per-vertex grouping at all</text>
  </g>
</svg>

The whole graph is just two edge entries, `(A, B, 3)` and `(A, C, 7)` — no vertex has any dedicated storage; `A`'s connections only become visible by scanning every entry.

## 5. Runnable example

```java
// EdgeList.java
import java.util.*;

public class EdgeList {

    record Edge(String from, String to, int weight) {}

    // Basic: the entire graph is just a flat list.
    static void basicLevel() {
        List<Edge> edges = new ArrayList<>(List.of(
            new Edge("A", "B", 3),
            new Edge("A", "C", 7),
            new Edge("B", "C", 1)));

        System.out.println("basic: edge list -> " + edges);
    }

    // Intermediate: Kruskal's algorithm needs edges sorted by weight -- trivial on a flat list, awkward on other representations.
    static void intermediateLevel() {
        List<Edge> edges = new ArrayList<>(List.of(
            new Edge("A", "B", 3),
            new Edge("A", "C", 7),
            new Edge("B", "C", 1),
            new Edge("C", "D", 5)));

        edges.sort(Comparator.comparingInt(Edge::weight)); // exactly what Kruskal's needs -- process cheapest edges first
        System.out.println("intermediate: edges sorted by weight -> " + edges);
    }

    // Advanced: confirm "find A's neighbors" costs O(E) on an edge list -- scanning every entry, unlike an adjacency list.
    static List<String> neighborsOfWithCount(List<Edge> edges, String vertex, int[] comparisons) {
        List<String> neighbors = new ArrayList<>();
        for (Edge edge : edges) {
            comparisons[0]++;
            if (edge.from().equals(vertex)) neighbors.add(edge.to());
            else if (edge.to().equals(vertex)) neighbors.add(edge.from()); // undirected: check both sides
        }
        return neighbors;
    }

    static void advancedLevel() {
        List<Edge> edges = List.of(
            new Edge("A", "B", 1), new Edge("C", "D", 1), new Edge("D", "E", 1),
            new Edge("E", "F", 1), new Edge("A", "F", 1)); // A's real edges are scattered: entries 0 and 4

        int[] comparisons = {0};
        List<String> neighbors = neighborsOfWithCount(edges, "A", comparisons);
        System.out.println("advanced: neighbors of A -> " + neighbors + ", entries scanned -> " + comparisons[0]
            + " (had to check ALL " + edges.size() + " edges, even though A has only 2 real connections)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `EdgeList.java`, then run `java EdgeList.java`.

## 6. Walkthrough

1. `basicLevel()` represents the whole graph as three plain `Edge` records — no per-vertex map or array exists anywhere.
2. `intermediateLevel()` sorts the edge list by weight, exactly the preprocessing step Kruskal's minimum spanning tree algorithm needs: process the cheapest edge first, then the next cheapest, and so on, using Union-Find to skip any edge that would form a cycle. This sort is a single, direct operation on a flat list — no other graph representation makes "all edges, globally ordered by weight" this straightforward.
3. `advancedLevel()` searches for vertex `A`'s neighbors by scanning every single edge in the list, checking both `from` and `to` (since the graph is undirected), and counting the comparisons made. Even though `A` has only 2 real edges, the scan must check all 5 entries in the list before it can be sure it found every one — the `O(E)` cost that makes an edge list a poor fit whenever neighbor lookups are frequent.

## 7. Gotchas & takeaways

> Gotcha: using an edge list as the primary representation for a traversal-heavy algorithm (BFS, DFS, which repeatedly ask "who are this vertex's neighbors?") is a common performance mistake — convert to an adjacency list first if your algorithm needs frequent neighbor lookups; keep the edge list only for algorithms that are naturally edge-centric.

- An edge list is the simplest, most compact representation — just a flat collection of `(from, to[, weight])` entries.
- It is the natural fit for edge-centric algorithms like Kruskal's minimum spanning tree, which needs all edges globally sorted by weight.
- Finding a specific vertex's neighbors costs `O(E)` — scanning every edge — far worse than an adjacency list's `O(degree)`.
- Related concepts: [Adjacency list](0140-adjacency-list.md), [Adjacency matrix](0141-adjacency-matrix.md).
