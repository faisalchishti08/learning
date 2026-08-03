---
card: data-structures
gi: 167
slug: applications-connectivity-kruskal-s-mst-cycle-detection
title: Applications (connectivity, Kruskal's MST, cycle detection)
---

## 1. What it is

This page ties [disjoint-set](0162-disjoint-set-data-structure.md) operations to the three problems they solve most often: checking **connectivity** between nodes, detecting a **cycle** while building a graph edge by edge, and building a **minimum spanning tree (MST)** with Kruskal's algorithm. All three reduce to the same pattern: process edges one at a time, and use `union`/`find` to track which nodes are already connected.

## 2. Why & when

These three uses share one insight: **union-find answers "would adding this edge create a cycle?" in near-constant time**, without ever building or traversing the graph as an adjacency list. That single question is the core of cycle detection, and it is also exactly what Kruskal's algorithm needs to decide whether to keep or skip each candidate edge while building an MST.

## 3. Core concept

**Connectivity check.** Given a graph built up from a list of edges, "are nodes `A` and `B` connected?" is answered by `find(A) == find(B)` after processing every edge with `union`. This avoids re-running BFS/DFS from scratch for every query.

**Cycle detection while building a graph.** Process edges one at a time. Before adding edge `(u, v)`, check `find(u) == find(v)`. If they are already in the same group, adding this edge would connect two nodes that are already connected through some other path — a cycle. Otherwise, add the edge and call `union(u, v)`.

**Kruskal's minimum spanning tree.** An MST connects every node with the minimum total edge weight, using no cycles. Kruskal's algorithm: sort all edges by weight ascending; process them in that order; for each edge `(u, v, weight)`, if `find(u) != find(v)`, include the edge in the MST and call `union(u, v)`; otherwise skip it (including it would form a cycle). Stop once `n-1` edges have been added, for `n` nodes.

**Why union-find is the right tool for all three.** Each problem needs the same repeated question — "are these two nodes already connected?" — asked once per edge, with the answer changing as edges are added. A graph traversal (BFS/DFS) answers this for a fixed, finished graph; union-find answers it incrementally, which is exactly the shape of Kruskal's edge-by-edge processing.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kruskal's algorithm processing sorted edges, using union-find to skip an edge that would form a cycle">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Sorted edges: (A,B,1) (B,C,2) (A,C,3) (C,D,4)</text>

    <circle cx="80" cy="80" r="16" fill="#161b22" stroke="#79c0ff"/><text x="80" y="84" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="64" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="140" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="144" text-anchor="middle" font-size="9">C</text>
    <circle cx="320" cy="100" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="104" text-anchor="middle" font-size="9">D</text>

    <line x1="94" y1="76" x2="186" y2="62" stroke="#3fb950" stroke-width="2"/><text x="140" y="60" font-size="8" fill="#3fb950">1 (added)</text>
    <line x1="200" y1="76" x2="200" y2="124" stroke="#3fb950" stroke-width="2"/><text x="210" y="105" font-size="8" fill="#3fb950">2 (added)</text>
    <line x1="90" y1="90" x2="190" y2="135" stroke="#f44336" stroke-dasharray="4,4"/><text x="110" y="130" font-size="8" fill="#f44336">3 (skip: cycle)</text>
    <line x1="216" y1="145" x2="308" y2="105" stroke="#3fb950" stroke-width="2"/><text x="260" y="140" font-size="8" fill="#3fb950">4 (added)</text>

    <text x="320" y="190" text-anchor="middle" font-size="9" fill="#8b949e">edge (A,C,3) skipped: find(A)==find(C) already, via A-B-C</text>
  </g>
</svg>

Each accepted edge merges two groups; each skipped edge would connect nodes already in the same group.

## 5. Runnable example

```java
// UnionFindApplications.java
import java.util.*;

public class UnionFindApplications {

    static class DSU {
        int[] parent, rank;

        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        boolean union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return false; // already connected -- this edge would be a cycle
            if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
            else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
            else { parent[rootY] = rootX; rank[rootX]++; }
            return true;
        }
    }

    // Basic: cycle detection while adding edges one at a time to an undirected graph.
    static boolean hasCycle(int n, int[][] edges) {
        DSU dsu = new DSU(n);
        for (int[] edge : edges) {
            if (!dsu.union(edge[0], edge[1])) return true; // union returned false -> already connected -> cycle
        }
        return false;
    }

    static void basicLevel() {
        int[][] noCycle = {{0, 1}, {1, 2}, {2, 3}};
        int[][] withCycle = {{0, 1}, {1, 2}, {2, 0}};

        System.out.println("basic: hasCycle(no cycle) -> " + hasCycle(4, noCycle));
        System.out.println("basic: hasCycle(with cycle) -> " + hasCycle(3, withCycle));
    }

    // Intermediate: connectivity queries after building the graph from a list of edges.
    static void intermediateLevel() {
        DSU dsu = new DSU(6);
        int[][] edges = {{0, 1}, {1, 2}, {3, 4}};
        for (int[] e : edges) dsu.union(e[0], e[1]);

        System.out.println("intermediate: connected(0,2) -> " + (dsu.find(0) == dsu.find(2)));
        System.out.println("intermediate: connected(0,4) -> " + (dsu.find(0) == dsu.find(4)));
        System.out.println("intermediate: connected(5,5) -> " + (dsu.find(5) == dsu.find(5)));
    }

    // Advanced: Kruskal's minimum spanning tree, using union-find to skip cycle-forming edges.
    record Edge(int u, int v, int weight) {}

    static List<Edge> kruskalMST(int n, List<Edge> edges) {
        List<Edge> sorted = new ArrayList<>(edges);
        sorted.sort(Comparator.comparingInt(Edge::weight));

        DSU dsu = new DSU(n);
        List<Edge> mst = new ArrayList<>();
        for (Edge e : sorted) {
            if (dsu.union(e.u(), e.v())) {
                mst.add(e);
                if (mst.size() == n - 1) break; // MST complete
            }
        }
        return mst;
    }

    static void advancedLevel() {
        List<Edge> edges = List.of(
            new Edge(0, 1, 1), new Edge(1, 2, 2), new Edge(0, 2, 3), new Edge(2, 3, 4));
        List<Edge> mst = kruskalMST(4, edges);

        int totalWeight = mst.stream().mapToInt(Edge::weight).sum();
        System.out.println("advanced: MST edges -> " + mst);
        System.out.println("advanced: MST total weight -> " + totalWeight);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java UnionFindApplications.java`

## 6. Walkthrough

Trace `kruskalMST` on edges `(A,B,1), (B,C,2), (A,C,3), (C,D,4)` (using `0=A, 1=B, 2=C, 3=D`), already sorted by weight. Start with 4 singleton groups.

Process `(A,B,1)`: `find(A) != find(B)`, so `union` succeeds — add this edge to the MST, merging `{A,B}`.

Process `(B,C,2)`: `find(B) != find(C)`, `union` succeeds — add it, merging into `{A,B,C}`.

Process `(A,C,3)`: `find(A) == find(C)` now (both are in `{A,B,C}`), so `union` returns `false` — this edge is **skipped**, because `A` and `C` are already connected via `B`, and adding it would form a cycle.

Process `(C,D,4)`: `find(C) != find(D)`, `union` succeeds — add it, merging into `{A,B,C,D}`. Now the MST has `3` edges for `4` nodes (`n-1`), so it stops.

The final MST has total weight `1 + 2 + 4 = 7`, and correctly excludes the redundant, more expensive `(A,C,3)` edge.

**Complexity.** Kruskal's algorithm: sorting `E` edges costs `O(E log E)`; the union-find loop over all edges costs `O(E * α(V))` (near-constant per edge, per [inverse Ackermann bound](0166-near-constant-amortized-complexity-inverse-ackermann.md)). Total: `O(E log E)`, dominated by the sort. Cycle detection alone (no sorting needed): `O(E * α(V))`.

## 7. Gotchas & takeaways

> The order edges are processed in matters for Kruskal's algorithm (must be sorted by weight ascending) but does **not** matter for plain cycle detection — any edge order correctly detects a cycle, because the question "are these two nodes already connected?" does not depend on processing order.

- Kruskal's algorithm assumes an **undirected** graph. Cycle detection in a **directed** graph needs a different technique (DFS with a recursion-stack check), because union-find has no notion of edge direction.
- `union` returning `false` is the cycle signal — many implementations return a `boolean` from `union` specifically so callers can reuse it for cycle detection without a separate `find` call.
- These patterns generalize beyond graphs: "accounts that share an email" or "pixels of the same color touching each other" are the same union-find pattern applied to a different notion of "edge."
