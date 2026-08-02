---
card: data-structures
gi: 147
slug: shortest-path-overview-dijkstra-bellman-ford
title: Shortest path overview (Dijkstra / Bellman-Ford)
---

## 1. What it is

**Dijkstra's algorithm** and **Bellman-Ford** both find the shortest (lowest total weight) path from a start vertex to every other vertex in a weighted graph. They differ in what weights they can handle correctly: Dijkstra's is faster but requires all edge weights to be non-negative; Bellman-Ford is slower but works even with negative weights, and can also detect a **negative cycle** (a loop whose total weight is negative, which would make "shortest path" undefined).

## 2. Why & when

Use Dijkstra's whenever weights are guaranteed non-negative (distances, times, most real-world costs) — it is the faster, standard choice for road networks, network routing, and most graph-based shortest-path problems. Use Bellman-Ford only when negative weights are possible (e.g. financial arbitrage graphs, where an edge can represent a *gain*), or when you specifically need to detect whether a negative cycle exists at all.

## 3. Core concept

**Dijkstra's algorithm.** Maintain a min-heap of `(vertex, distance-so-far)`, seeded with the start vertex at distance `0`. Repeatedly pop the vertex with the smallest known distance; if it has already been finalized, skip it. Otherwise, finalize it, and **relax** each outgoing edge: if going through the current vertex gives a neighbor a shorter distance than previously known, update it and push the improved distance onto the heap. Because the heap always processes the currently-cheapest unfinalized vertex next, once a vertex is popped and finalized, its distance is guaranteed final — no cheaper path to it can be found later.

**Why Dijkstra's fails with negative weights.** The "once finalized, never revisited" guarantee relies on every subsequent path only being able to get *more* expensive by adding edges. A negative edge can make a path found *later* actually cheaper than one already finalized — breaking the algorithm's core assumption.

**Bellman-Ford.** Relax *every* edge in the graph, `V - 1` times total (for `V` vertices) — after `V - 1` rounds, every shortest path (which can use at most `V - 1` edges, since a simple path never repeats a vertex) is guaranteed found, regardless of edge weight sign. A **`V`-th round** that still finds an improvement proves a negative cycle exists, since a normal shortest path could never need more than `V - 1` edges.

**Complexity comparison.** Dijkstra's with a binary heap: `O((V + E) log V)`. Bellman-Ford: `O(V * E)` — noticeably slower, but tolerant of negative weights and able to detect negative cycles, which Dijkstra's cannot do at all.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A graph with a negative edge from B to C of weight negative 5, showing Dijkstra finalizing B too early and missing the cheaper path through the negative edge, while Bellman-Ford correctly relaxes every edge repeatedly">
  <g font-family="sans-serif" font-size="11">
    <circle cx="100" cy="100" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="300" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="300" cy="150" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="115" y1="90" x2="285" y2="65" stroke="#79c0ff" stroke-width="2"/>
    <text x="200" y="65" fill="#79c0ff" font-size="9">weight 4</text>
    <line x1="115" y1="110" x2="285" y2="145" stroke="#8b949e" stroke-width="2"/>
    <text x="200" y="145" fill="#8b949e" font-size="9">weight 10</text>
    <line x1="300" y1="78" x2="300" y2="132" stroke="#f0883e" stroke-width="2"/>
    <text x="330" y="105" fill="#f0883e" font-size="9">weight -5</text>
    <text x="300" y="185" fill="#f0883e" text-anchor="middle" font-size="10">A-&gt;B-&gt;C costs 4+(-5)=-1, cheaper than direct A-&gt;C (10) -- Dijkstra's could miss this</text>
  </g>
</svg>

`A -> B -> C` costs `4 + (-5) = -1`, cheaper than the direct `A -> C` edge (`10`). Dijkstra's, which finalizes vertices greedily by currently-known distance, can finalize `C` via the direct edge before ever exploring the cheaper negative-weight path through `B` — Bellman-Ford avoids this by relaxing every edge repeatedly, regardless of order.

## 5. Runnable example

```java
// ShortestPathOverview.java
import java.util.*;

public class ShortestPathOverview {

    record Edge(String to, int weight) {}

    // Basic: Dijkstra's algorithm -- correct and fast for non-negative weights.
    static Map<String, Integer> dijkstra(Map<String, List<Edge>> graph, String start) {
        Map<String, Integer> distances = new HashMap<>();
        PriorityQueue<Edge> minHeap = new PriorityQueue<>(Comparator.comparingInt(Edge::weight));
        minHeap.offer(new Edge(start, 0));

        while (!minHeap.isEmpty()) {
            Edge current = minHeap.poll();
            if (distances.containsKey(current.to())) continue; // already finalized -- skip
            distances.put(current.to(), current.weight());

            for (Edge edge : graph.getOrDefault(current.to(), List.of())) {
                if (!distances.containsKey(edge.to())) {
                    minHeap.offer(new Edge(edge.to(), current.weight() + edge.weight()));
                }
            }
        }
        return distances;
    }

    static void basicLevel() {
        Map<String, List<Edge>> graph = Map.of(
            "A", List.of(new Edge("B", 4), new Edge("C", 10)),
            "B", List.of(new Edge("C", 3))); // all non-negative -- Dijkstra's is correct here

        System.out.println("basic: Dijkstra's distances from A -> " + dijkstra(graph, "A"));
    }

    // Intermediate: Bellman-Ford -- relax every edge V-1 times, handling negative weights correctly.
    static Map<String, Integer> bellmanFord(List<String> vertices, List<Object[]> edges, String start) {
        Map<String, Integer> distance = new HashMap<>();
        for (String v : vertices) distance.put(v, Integer.MAX_VALUE);
        distance.put(start, 0);

        for (int round = 0; round < vertices.size() - 1; round++) { // V-1 rounds is always enough for a simple path
            for (Object[] edge : edges) {
                String from = (String) edge[0], to = (String) edge[1];
                int weight = (int) edge[2];
                if (distance.get(from) != Integer.MAX_VALUE && distance.get(from) + weight < distance.get(to)) {
                    distance.put(to, distance.get(from) + weight);
                }
            }
        }
        return distance;
    }

    static void intermediateLevel() {
        List<String> vertices = List.of("A", "B", "C");
        List<Object[]> edges = List.of(
            new Object[]{"A", "B", 4},
            new Object[]{"A", "C", 10},
            new Object[]{"B", "C", -5}); // negative edge -- Dijkstra's could get this wrong

        Map<String, Integer> distances = bellmanFord(vertices, edges, "A");
        System.out.println("intermediate: Bellman-Ford distances from A -> " + distances
            + " (correctly finds A->B->C = 4+(-5) = -1, cheaper than the direct edge's 10)");
    }

    // Advanced: detect a negative cycle -- a V-th round that STILL finds an improvement proves one exists.
    static boolean hasNegativeCycle(List<String> vertices, List<Object[]> edges, String start) {
        Map<String, Integer> distance = bellmanFord(vertices, edges, start);

        for (Object[] edge : edges) { // one more round, beyond the normal V-1
            String from = (String) edge[0], to = (String) edge[1];
            int weight = (int) edge[2];
            if (distance.get(from) != Integer.MAX_VALUE && distance.get(from) + weight < distance.get(to)) {
                return true; // still improving after V-1 rounds -- only possible if a negative cycle exists
            }
        }
        return false;
    }

    static void advancedLevel() {
        List<String> vertices = List.of("A", "B", "C");
        List<Object[]> negativeCycleEdges = List.of(
            new Object[]{"A", "B", 1},
            new Object[]{"B", "C", -3},
            new Object[]{"C", "B", 1}); // B->C->B costs -3+1=-2, a negative cycle

        System.out.println("advanced: graph with a B<->C negative cycle -> hasNegativeCycle -> "
            + hasNegativeCycle(vertices, negativeCycleEdges, "A"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ShortestPathOverview.java`, then run `java ShortestPathOverview.java`.

## 6. Walkthrough

1. `basicLevel()` runs Dijkstra's on a graph with only non-negative weights. `A` starts at distance `0`; its neighbors `B` (weight `4`) and `C` (weight `10`) are pushed. Popping `B` first (smaller distance) finalizes it at `4`, then relaxes `C` through `B`: `4 + 3 = 7`, cheaper than `10`, so `C`'s eventual finalized distance becomes `7` — correctly finding the cheapest path.
2. `intermediateLevel()` runs Bellman-Ford on the graph from the diagram, which includes a negative edge `B -> C` (weight `-5`). After relaxing every edge across `V - 1 = 2` rounds, `C`'s distance correctly settles at `-1` (via `A -> B -> C`), cheaper than the direct edge's `10` — a result Dijkstra's could get wrong on this same input, since it might finalize `C` via the direct edge before ever discovering the cheaper path through `B`.
3. `advancedLevel()` builds a graph with a genuine negative cycle (`B -> C -> B` costs `-3 + 1 = -2`). Running one extra relaxation round beyond the normal `V - 1` still finds an improvement — proof that "shortest path" is not even well-defined here, since you could loop around the negative cycle indefinitely to make the path arbitrarily cheap.

## 7. Gotchas & takeaways

> Gotcha: running Dijkstra's on a graph with any negative edge can silently produce a wrong (too large) shortest-distance answer, with no error or warning — Dijkstra's algorithm has no way to detect that its core assumption (distances only ever increase as you add edges) has been violated.

- Dijkstra's is faster (`O((V+E) log V)`) but requires non-negative weights; Bellman-Ford is slower (`O(V*E)`) but handles negative weights correctly.
- Bellman-Ford relaxes every edge `V - 1` times; a `V`-th round that still improves any distance proves a negative cycle exists.
- A negative cycle makes "shortest path" undefined for any vertex reachable through it, since the path could be made arbitrarily cheap by looping.
- Related concepts: [Weighted vs unweighted graphs](0136-weighted-vs-unweighted-graphs.md), [Minimum spanning tree overview (Kruskal / Prim)](0148-minimum-spanning-tree-overview-kruskal-prim.md).
