---
card: data-structures
gi: 139
slug: degree-path-cycle
title: Degree, path & cycle
---

## 1. What it is

This is the shared vocabulary for describing a graph's local and global shape. A vertex's **degree** is how many edges touch it. A **path** is a sequence of vertices connected by edges, with no repeated vertex. A **cycle** is a path that returns to its starting vertex. These three terms underpin almost every graph algorithm's description.

## 2. Why & when

Precise terms prevent ambiguity when reasoning about or discussing graph algorithms. "Degree" distinguishes a hub vertex (many connections) from a leaf-like vertex (one connection). "Path" versus "walk" (a walk may repeat vertices; a path may not) matters for correctness in shortest-path algorithms. Getting "cycle" right (a path back to the start) is the foundation for cycle detection, covered separately.

## 3. Core concept

**Degree, in-degree, out-degree.** In an undirected graph, a vertex's **degree** is simply the number of edges touching it. In a directed graph, this splits into **in-degree** (number of edges pointing *into* the vertex) and **out-degree** (number of edges pointing *out of* it) — a vertex can have very different in- and out-degrees (e.g. a popular social media account: huge in-degree from followers, small out-degree from who it follows).

**Path vs walk.** A **walk** is any sequence of vertices connected by edges, allowing repeats. A **path** additionally requires no vertex to repeat. This distinction matters because many algorithms (like finding the shortest path) implicitly assume paths, not arbitrary walks — a shortest "path" would never usefully repeat a vertex anyway, since that would only add length.

**Cycle, precisely.** A cycle is a path of length at least 1 (at least one edge) that starts and ends at the same vertex, with no other repeated vertex along the way. A single self-loop (an edge from a vertex to itself) is the simplest possible cycle, of length 1.

**Why degree matters for algorithm design.** The **sum of all vertices' degrees equals twice the number of edges** in an undirected graph (the "handshake" identity), since each edge contributes to exactly two vertices' degree counts. This identity is a quick sanity check when building or debugging a graph's adjacency structure.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A graph with vertex B having degree 3 connected to A, C, and D, illustrating degree, and a path A to D via B distinct from a cycle A to B to C back to A">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="100" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <text x="300" y="130" fill="#f0883e" text-anchor="middle" font-size="9">degree(B) = 3</text>
    <circle cx="150" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="150" cy="150" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="450" cy="100" r="16" fill="#161b22" stroke="#8b949e"/><text x="450" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="284" y1="88" x2="166" y2="70" stroke="#79c0ff" stroke-width="2"/>
    <line x1="284" y1="112" x2="166" y2="140" stroke="#79c0ff" stroke-width="2"/>
    <line x1="318" y1="100" x2="434" y2="100" stroke="#8b949e" stroke-width="2"/>
    <line x1="150" y1="76" x2="150" y2="134" stroke="#f0883e" stroke-width="2"/>
    <text x="180" y="175" fill="#f0883e" text-anchor="middle" font-size="9">A-B-C-A: a cycle (returns to start)</text>
    <text x="380" y="175" fill="#8b949e" text-anchor="middle" font-size="9">A-B-D: a path (no repeats, no return)</text>
  </g>
</svg>

`B` has degree `3` (edges to `A`, `C`, `D`). `A -> B -> C -> A` is a cycle (returns to `A`). `A -> B -> D` is a path (visits distinct vertices, does not return to its start).

## 5. Runnable example

```java
// GraphTerminology.java
import java.util.*;

public class GraphTerminology {

    // Basic: compute degree (undirected) for every vertex.
    static Map<String, Integer> computeDegrees(Map<String, List<String>> undirectedGraph) {
        Map<String, Integer> degrees = new HashMap<>();
        for (String vertex : undirectedGraph.keySet()) {
            degrees.put(vertex, undirectedGraph.get(vertex).size());
        }
        return degrees;
    }

    static void basicLevel() {
        Map<String, List<String>> graph = new HashMap<>();
        graph.put("A", List.of("B", "C"));
        graph.put("B", List.of("A", "C", "D"));
        graph.put("C", List.of("A", "B"));
        graph.put("D", List.of("B"));

        System.out.println("basic: degrees -> " + computeDegrees(graph));
    }

    // Intermediate: in-degree and out-degree, separately, for a directed graph.
    static Map<String, Integer> computeInDegrees(Map<String, List<String>> directedGraph) {
        Map<String, Integer> inDegrees = new HashMap<>();
        for (String vertex : directedGraph.keySet()) inDegrees.putIfAbsent(vertex, 0);
        for (List<String> targets : directedGraph.values()) {
            for (String target : targets) inDegrees.merge(target, 1, Integer::sum);
        }
        return inDegrees;
    }

    static void intermediateLevel() {
        Map<String, List<String>> directedGraph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("C"),
            "C", List.of());

        Map<String, Integer> outDegrees = new HashMap<>();
        for (String vertex : directedGraph.keySet()) outDegrees.put(vertex, directedGraph.get(vertex).size());

        System.out.println("intermediate: out-degrees -> " + outDegrees);
        System.out.println("intermediate: in-degrees  -> " + computeInDegrees(directedGraph)
            + " (C has in-degree 2 -- both A and B point to it)");
    }

    // Advanced: distinguish a path from a cycle by checking whether the walk returns to its own starting vertex.
    static boolean isPath(List<String> walk) {
        return new HashSet<>(walk).size() == walk.size(); // no repeated vertex anywhere
    }

    static boolean isCycle(List<String> walk) {
        return walk.size() > 1
            && walk.get(0).equals(walk.get(walk.size() - 1))
            && new HashSet<>(walk.subList(0, walk.size() - 1)).size() == walk.size() - 1; // no OTHER repeats besides start==end
    }

    static void advancedLevel() {
        List<String> candidatePath = List.of("A", "B", "D");
        List<String> candidateCycle = List.of("A", "B", "C", "A");

        System.out.println("advanced: [A,B,D] is a path? -> " + isPath(candidatePath) + ", is a cycle? -> " + isCycle(candidatePath));
        System.out.println("advanced: [A,B,C,A] is a path? -> " + isPath(candidateCycle) + ", is a cycle? -> " + isCycle(candidateCycle));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `GraphTerminology.java`, then run `java GraphTerminology.java`.

## 6. Walkthrough

1. `basicLevel()` computes each vertex's degree by counting its adjacency-list entries directly. `B` has degree `3` (connected to `A`, `C`, `D`); `D` has degree `1` (connected only to `B`) — matching the diagram.
2. `intermediateLevel()` separately computes out-degree (how many entries each vertex's own adjacency list has) and in-degree (how many times each vertex appears as *someone else's* target). `C` has out-degree `0` (points to nothing) but in-degree `2` (both `A` and `B` point to it) — a clear illustration of how directed degree splits into two independent numbers.
3. `advancedLevel()` checks `[A, B, D]` (no repeated vertex, does not return to `A`) — correctly a path, not a cycle. `[A, B, C, A]` (starts and ends at `A`, with no *other* repeats along the way) — correctly a cycle, not a plain path, since `isPath` treats the repeated `A` at both ends as disqualifying it from being a path, while `isCycle` specifically expects exactly that repetition at the ends.

## 7. Gotchas & takeaways

> Gotcha: confusing "walk" and "path" is a common source of off-by-one or logically-incorrect graph code — a walk may revisit vertices freely, but a path (and therefore most "shortest path" algorithms) must not; treating every walk as if it were automatically a path can hide bugs where a supposed "shortest path" secretly loops.

- Degree counts edges touching a vertex; directed graphs split this into in-degree and out-degree, which can differ greatly for the same vertex.
- A path never repeats a vertex; a cycle is a path that returns to its own start, with no other repeats along the way.
- The sum of all degrees in an undirected graph equals twice the edge count — a quick sanity check for a correctly built adjacency structure.
- Related concepts: [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md), [Connectivity & components](0138-connectivity-components.md).
