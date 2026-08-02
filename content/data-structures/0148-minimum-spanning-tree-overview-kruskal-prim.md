---
card: data-structures
gi: 148
slug: minimum-spanning-tree-overview-kruskal-prim
title: Minimum spanning tree overview (Kruskal / Prim)
---

## 1. What it is

A **minimum spanning tree (MST)** of a connected, undirected, weighted graph is a subset of its edges that connects all vertices together, contains no cycle, and has the smallest possible total edge weight among all such subsets. **Kruskal's** and **Prim's** algorithms are the two standard ways to build one; both are greedy, but they grow the tree in different ways.

## 2. Why & when

An MST answers "what is the cheapest way to connect everything?" — laying network cable to connect every building using the least total cable, or connecting cities with roads at minimum total construction cost. Use Kruskal's when your graph is given (or naturally available) as an edge list and is relatively sparse; use Prim's when the graph is dense or already represented as an adjacency list/matrix, since Prim's grows from a single starting point and never needs the whole edge set sorted upfront.

## 3. Core concept

**Kruskal's algorithm.** Sort *all* edges by weight, ascending. Process them one at a time, adding an edge to the MST only if it connects two vertices that are not already connected through previously-added edges (checked with **Union-Find**) — skipping any edge that would create a cycle. Stop once `V - 1` edges have been added (a tree connecting `V` vertices always has exactly `V - 1` edges).

**Prim's algorithm.** Start from any single vertex, and grow the tree one vertex at a time: at each step, add the cheapest edge that connects a vertex already in the tree to a vertex not yet in the tree (using a min-heap of candidate edges, similar to Dijkstra's, but keyed by the edge's own weight, not by cumulative distance). Repeat until every vertex is included.

**Why both are greedy but still correct.** Both algorithms make the locally cheapest choice at every step (Kruskal's: cheapest edge overall that avoids a cycle; Prim's: cheapest edge that grows the current tree) and never reconsider that choice. This greedy strategy is provably correct for MST specifically, due to the "cut property": for any way of splitting the vertices into two groups, the cheapest edge crossing that split must be part of *some* MST — which is exactly the edge either algorithm picks at each step.

**Kruskal's versus Prim's, practically.** Kruskal's needs Union-Find to detect cycles efficiently and works naturally from an edge list. Prim's needs a min-heap of candidate edges and works naturally from an adjacency list, growing outward like a heap-based BFS. Both reach `O(E log E)` or `O(E log V)` complexity, depending on implementation details — neither is universally faster; the choice usually follows which representation the graph is already in.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A four vertex graph with several weighted edges, highlighting the three cheapest edges that form the minimum spanning tree while skipping a more expensive edge that would create a cycle">
  <g font-family="sans-serif" font-size="11">
    <circle cx="120" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="120" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="280" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="280" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="280" cy="120" r="16" fill="#161b22" stroke="#79c0ff"/><text x="280" y="124" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="440" cy="70" r="16" fill="#161b22" stroke="#79c0ff"/><text x="440" y="74" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="134" y1="52" x2="266" y2="34" stroke="#79c0ff" stroke-width="3"/><text x="200" y="30" fill="#79c0ff" font-size="9">1</text>
    <line x1="134" y1="70" x2="266" y2="112" stroke="#79c0ff" stroke-width="3"/><text x="200" y="105" fill="#79c0ff" font-size="9">2</text>
    <line x1="294" y1="40" x2="428" y2="65" stroke="#79c0ff" stroke-width="3"/><text x="365" y="40" fill="#79c0ff" font-size="9">3</text>
    <line x1="294" y1="110" x2="426" y2="78" stroke="#f0883e" stroke-width="1" stroke-dasharray="4,3"/><text x="365" y="115" fill="#f0883e" font-size="9">7 (skipped)</text>
    <text x="300" y="170" fill="#79c0ff" text-anchor="middle" font-size="10">MST total weight = 1+2+3 = 6; the weight-7 edge is skipped -- it would create a cycle</text>
  </g>
</svg>

Kruskal's processes edges in weight order (`1, 2, 3, 7, ...`), accepting the first three (they connect new vertices) and rejecting the weight-`7` edge (`C-D`), since `C` and `D` are already connected through cheaper edges — accepting it would create a cycle.

## 5. Runnable example

```java
// MinimumSpanningTree.java
import java.util.*;

public class MinimumSpanningTree {

    record Edge(String from, String to, int weight) {}

    // Basic: Union-Find, the data structure Kruskal's uses to detect "would this edge create a cycle?"
    static class UnionFind {
        Map<String, String> parent = new HashMap<>();

        void makeSet(String v) { parent.put(v, v); }

        String find(String v) {
            if (!parent.get(v).equals(v)) parent.put(v, find(parent.get(v))); // path compression
            return parent.get(v);
        }

        boolean union(String a, String b) {
            String rootA = find(a), rootB = find(b);
            if (rootA.equals(rootB)) return false; // already connected -- adding this edge would create a cycle
            parent.put(rootA, rootB);
            return true;
        }
    }

    static void basicLevel() {
        UnionFind uf = new UnionFind();
        for (String v : List.of("A", "B", "C")) uf.makeSet(v);

        System.out.println("basic: union(A, B) -> " + uf.union("A", "B") + " (new connection)");
        System.out.println("basic: union(A, B) again -> " + uf.union("A", "B") + " (already connected -- would be a cycle)");
    }

    // Intermediate: Kruskal's algorithm -- sort edges, greedily accept ones that don't create a cycle.
    static List<Edge> kruskalMST(List<String> vertices, List<Edge> edges) {
        List<Edge> sorted = new ArrayList<>(edges);
        sorted.sort(Comparator.comparingInt(Edge::weight));

        UnionFind uf = new UnionFind();
        for (String v : vertices) uf.makeSet(v);

        List<Edge> mst = new ArrayList<>();
        for (Edge edge : sorted) {
            if (uf.union(edge.from(), edge.to())) { // returns true only if this edge connects two previously-separate groups
                mst.add(edge);
                if (mst.size() == vertices.size() - 1) break; // a tree over V vertices has exactly V-1 edges
            }
        }
        return mst;
    }

    static void intermediateLevel() {
        List<String> vertices = List.of("A", "B", "C", "D");
        List<Edge> edges = List.of(
            new Edge("A", "B", 1),
            new Edge("A", "C", 2),
            new Edge("B", "D", 3),
            new Edge("C", "D", 7)); // more expensive than the alternative path -- should be skipped

        List<Edge> mst = kruskalMST(vertices, edges);
        int totalWeight = mst.stream().mapToInt(Edge::weight).sum();
        System.out.println("intermediate: Kruskal's MST edges -> " + mst + ", total weight -> " + totalWeight);
    }

    // Advanced: Prim's algorithm -- grow from one vertex, always adding the cheapest edge that reaches a NEW vertex.
    static List<Edge> primMST(Map<String, List<Edge>> adjacency, String start) {
        Set<String> inTree = new HashSet<>();
        PriorityQueue<Edge> candidates = new PriorityQueue<>(Comparator.comparingInt(Edge::weight));
        List<Edge> mst = new ArrayList<>();

        inTree.add(start);
        candidates.addAll(adjacency.getOrDefault(start, List.of()));

        while (!candidates.isEmpty() && inTree.size() < adjacency.size()) {
            Edge cheapest = candidates.poll();
            if (inTree.contains(cheapest.to())) continue; // both endpoints already in the tree -- would create a cycle

            inTree.add(cheapest.to());
            mst.add(cheapest);
            candidates.addAll(adjacency.getOrDefault(cheapest.to(), List.of()));
        }
        return mst;
    }

    static void advancedLevel() {
        Map<String, List<Edge>> adjacency = new HashMap<>();
        adjacency.put("A", List.of(new Edge("A", "B", 1), new Edge("A", "C", 2)));
        adjacency.put("B", List.of(new Edge("B", "A", 1), new Edge("B", "D", 3)));
        adjacency.put("C", List.of(new Edge("C", "A", 2), new Edge("C", "D", 7)));
        adjacency.put("D", List.of(new Edge("D", "B", 3), new Edge("D", "C", 7)));

        List<Edge> mst = primMST(adjacency, "A");
        int totalWeight = mst.stream().mapToInt(Edge::weight).sum();
        System.out.println("advanced: Prim's MST edges -> " + mst + ", total weight -> " + totalWeight
            + " (same total as Kruskal's -- both find A VALID minimum spanning tree)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MinimumSpanningTree.java`, then run `java MinimumSpanningTree.java`.

## 6. Walkthrough

1. `basicLevel()` demonstrates Union-Find in isolation. `union("A", "B")` merges their groups and returns `true`, since they started in separate groups. Calling `union("A", "B")` again returns `false` — they now share the same root, so merging them again would create a cycle rather than a new connection.
2. `intermediateLevel()` sorts all four edges by weight (`1, 2, 3, 7`), then processes them in order. `A-B` (weight `1`) connects two new groups — accepted. `A-C` (weight `2`) connects `C` to the growing group — accepted. `B-D` (weight `3`) connects `D` — accepted, reaching `V - 1 = 3` edges, so the loop stops before even considering `C-D` (weight `7`), which would have created a cycle anyway. Total MST weight: `1 + 2 + 3 = 6`.
3. `advancedLevel()` runs Prim's from `A` on the same graph, represented as an adjacency list instead of a flat edge list. Starting with `A` in the tree, its candidate edges (`A-B` weight `1`, `A-C` weight `2`) are queued. The cheapest, `A-B`, is taken first, adding `B`'s edges to the candidate queue. The next cheapest overall is `A-C` (weight `2`), then `B-D` (weight `3`) — reaching all four vertices with the same total weight, `6`, as Kruskal's found — confirming both algorithms correctly find a minimum spanning tree, even though they build it in a different order.

## 7. Gotchas & takeaways

> Gotcha: an MST is not necessarily unique — if multiple edges share the same weight, different tie-breaking choices can produce different (but equally minimal-weight) spanning trees; do not assume there is exactly one correct MST to compare your algorithm's output against.

- Kruskal's sorts all edges and greedily accepts ones that do not create a cycle (checked via Union-Find); Prim's grows a single tree from one vertex, always adding the cheapest edge that reaches a new vertex.
- Both are greedy algorithms, and both are provably correct for MST specifically, due to the "cut property."
- Kruskal's fits an edge-list representation naturally; Prim's fits an adjacency-list representation naturally — pick based on what your graph data already looks like.
- Related concepts: [Edge list](0142-edge-list.md), [Shortest path overview (Dijkstra / Bellman-Ford)](0147-shortest-path-overview-dijkstra-bellman-ford.md).
