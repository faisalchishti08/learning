---
card: leetcode-patterns
gi: 526
slug: redundant-connection
title: Redundant Connection
---

## 1. What it is

You are given a list of edges for a graph that started as a tree with `n` nodes, then had exactly one extra edge added, creating a cycle. Return the extra edge — the one that, if removed, turns the graph back into a tree. If several edges could be removed to break the cycle, return the one that appears last in the input list. Example: `edges = [[1,2],[1,3],[2,3]]` → `[2,3]` (adding `2-3` closes the cycle `1-2-3-1`).

## 2. Why & when

A tree with `n` nodes has exactly `n - 1` edges and no cycles. This input has exactly `n` edges — one too many — so exactly one edge must close a cycle. The problem asks you to find that edge as the edges are added one at a time, which is the direct [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md): "will adding this edge create a cycle?" Constraints: up to 1,000 nodes, edges given as `[u, v]` pairs with `1 <= u, v <= n`.

## 3. Core concept

**Key idea:** process edges in the given order. Before adding an edge `(u, v)`, check whether `u` and `v` are already in the same union-find group. If they are, this edge connects two nodes already reachable from each other — adding it closes a cycle, so it is the redundant edge. If they are not, union them and continue.

**Steps:**
1. Initialize a union-find structure over nodes `1..n`.
2. For each edge `(u, v)`, in order: if `find(u) == find(v)`, return `(u, v)` immediately.
3. Otherwise, `union(u, v)` and move to the next edge.

**Why the last such edge is always correct:** every edge before the true redundant one is part of the original tree, so it always connects two different groups (a tree has no cycles). The first edge that connects two nodes already in the same group must be the extra one — and since exactly one extra edge exists, it is also necessarily the last one that could possibly cause this.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding edges 1-2 and 1-3 build a tree; adding 2-3 closes a cycle and is the redundant edge">
  <g font-family="sans-serif" font-size="13">
    <circle cx="350" cy="30" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="35" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="335" y1="42" x2="270" y2="90" stroke="#8b949e"/>
    <circle cx="255" cy="100" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="255" y="105" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="365" y1="42" x2="430" y2="90" stroke="#8b949e"/>
    <circle cx="445" cy="100" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="445" y="105" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="270" y1="105" x2="430" y2="105" stroke="#f0883e" stroke-width="2" stroke-dasharray="5"/>
    <text x="350" y="140" fill="#f0883e" text-anchor="middle">edge 2-3: find(2) == find(3) already -&gt; redundant</text>
  </g>
</svg>

Edges `1-2` and `1-3` build a tree over three nodes. Edge `2-3` connects two nodes already in the same group, closing a cycle — it is the redundant edge.

## 5. Runnable example

**Level 1 — Brute force.** For each candidate edge to remove (trying the last one first), check whether the remaining graph is still a valid tree using breadth-first search. O(n²) or worse.

**KEY INSIGHT:** you do not need to try removing edges after the fact — process edges in order and union-find tells you the moment a cycle first closes.

**Level 2 — Optimal.** Union-find with path compression and union by rank, O(n · α(n)), effectively O(n).

**Level 3 — Hardened.** Works when the redundant edge is not the very last one listed, and when nodes are 1-indexed.

```java
// RedundantConnection.java
public class RedundantConnection {

    static class DSU {
        int[] parent;
        int[] rank;
        DSU(int n) {
            parent = new int[n + 1];
            rank = new int[n + 1];
            for (int i = 0; i <= n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        // returns false if a and b were already connected (cycle)
        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false;
            if (rank[rootA] < rank[rootB]) {
                parent[rootA] = rootB;
            } else if (rank[rootA] > rank[rootB]) {
                parent[rootB] = rootA;
            } else {
                parent[rootB] = rootA;
                rank[rootA]++;
            }
            return true;
        }
    }

    static int[] findRedundantConnection(int[][] edges) {
        int n = edges.length; // n nodes, n edges (one extra beyond a tree)
        DSU dsu = new DSU(n);
        for (int[] edge : edges) {
            if (!dsu.union(edge[0], edge[1])) {
                return edge; // this edge closes a cycle
            }
        }
        return new int[0]; // never reached on valid input
    }

    public static void main(String[] args) {
        int[][] edges1 = {{1, 2}, {1, 3}, {2, 3}};
        System.out.println(java.util.Arrays.toString(findRedundantConnection(edges1))); // [2, 3]

        int[][] edges2 = {{1, 2}, {2, 3}, {3, 4}, {1, 4}, {1, 5}};
        System.out.println(java.util.Arrays.toString(findRedundantConnection(edges2))); // [1, 4]
    }
}
```

**How to run:** save as `RedundantConnection.java`, then run `java RedundantConnection.java`.

## 6. Walkthrough

Trace `findRedundantConnection([[1,2],[1,3],[2,3]])`:

| edge | find(u) | find(v) | same group? | action | result |
|---|---|---|---|---|---|
| (1,2) | 1 | 2 | no | union(1,2) | groups: {1,2}, {3} |
| (1,3) | 1 | 3 | no | union(1,3) | groups: {1,2,3} |
| (2,3) | 1 | 1 | **yes** | return edge | `[2, 3]` |

The third edge is the first one where both endpoints already share a representative, so it is returned immediately.

## 7. Gotchas & takeaways

> Gotcha: running breadth-first search or depth-first search from scratch to check for a cycle after adding each edge also works, but costs O(n) per edge (O(n²) total) — union-find answers the same question in near O(1) per edge.

- Signal: "one extra edge added to a tree, find it" is a direct cycle-detection-while-building signal for union-find.
- Process edges in input order; the first cycle-closing edge found is guaranteed to be the answer, since exactly one extra edge exists.
- Related problems: Redundant Connection II (directed version, harder), Graph Valid Tree, Number of Connected Components in an Undirected Graph.
