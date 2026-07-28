---
card: leetcode-patterns
gi: 527
slug: number-of-connected-components-in-an-undirected-graph
title: Number of Connected Components in an Undirected Graph
---

## 1. What it is

Given `n` nodes labeled `0` to `n - 1` and a list of undirected edges, return the number of connected components — groups of nodes that are all reachable from each other, with no edges crossing between groups. Example: `n = 5`, `edges = [[0,1],[1,2],[3,4]]` → `2` (component `{0,1,2}` and component `{3,4}`).

## 2. Why & when

"Count the groups formed by these connections" is a direct [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md). Breadth-first search or depth-first search also solves this (count how many times you start a fresh search from an unvisited node), and is equally valid here since the graph is static. Union-find is preferred when edges arrive incrementally or when you also need fast "are these two connected" queries later. Constraints: up to 2,000 nodes and edges.

## 3. Core concept

**Key idea:** start with `n` separate groups, one per node. Each edge either merges two different groups into one (reducing the group count by 1) or connects two nodes already in the same group (no change). After processing every edge, the number of remaining groups is the answer.

**Steps:**
1. Initialize union-find over nodes `0..n-1`, with `groupCount = n`.
2. For each edge `(u, v)`: if `find(u) != find(v)`, union them and decrement `groupCount`.
3. Return `groupCount` after all edges are processed.

**Why decrementing only on a real merge works:** every successful `union` strictly reduces the number of distinct groups by exactly one, since it combines two previously separate groups into one. An edge between two nodes already in the same group changes nothing, so it correctly contributes no decrement.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five nodes starting as five groups, merging down to two groups after edges 0-1, 1-2, and 3-4">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">n=5, edges=[[0,1],[1,2],[3,4]]</text>
    <circle cx="60" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="60" y="85" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="140" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="140" y="85" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="220" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="220" y="85" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="76" y1="80" x2="124" y2="80" stroke="#8b949e"/>
    <line x1="156" y1="80" x2="204" y2="80" stroke="#8b949e"/>
    <circle cx="380" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="380" y="85" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="460" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="460" y="85" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="396" y1="80" x2="444" y2="80" stroke="#8b949e"/>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">2 components: {0,1,2} and {3,4}</text>
  </g>
</svg>

Nodes `0`, `1`, `2` merge into one group; nodes `3`, `4` merge into another — 2 components remain.

## 5. Runnable example

**Level 1 — Brute force.** Build an adjacency list, then run depth-first search from every unvisited node, counting how many times a fresh search starts. O(n + e).

**KEY INSIGHT:** counting groups is exactly what union-find's group counter tracks as edges are unioned — no separate traversal pass is needed.

**Level 2 — Optimal.** Union-find with a running group counter, O((n + e) · α(n)), effectively O(n + e).

**Level 3 — Hardened.** Handles nodes with no edges at all (each stays its own component) and duplicate edges (no double-decrement).

```java
// CountComponents.java
public class CountComponents {

    static class DSU {
        int[] parent;
        int[] rank;
        int groupCount;
        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            groupCount = n;
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        void union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return; // already same group; no decrement
            if (rank[rootA] < rank[rootB]) {
                parent[rootA] = rootB;
            } else if (rank[rootA] > rank[rootB]) {
                parent[rootB] = rootA;
            } else {
                parent[rootB] = rootA;
                rank[rootA]++;
            }
            groupCount--;
        }
    }

    static int countComponents(int n, int[][] edges) {
        DSU dsu = new DSU(n);
        for (int[] edge : edges) {
            dsu.union(edge[0], edge[1]);
        }
        return dsu.groupCount;
    }

    public static void main(String[] args) {
        System.out.println(countComponents(5, new int[][]{{0, 1}, {1, 2}, {3, 4}})); // 2
        System.out.println(countComponents(5, new int[][]{{0, 1}, {1, 2}, {2, 3}, {3, 4}})); // 1
        System.out.println(countComponents(4, new int[][]{})); // 4, no edges at all
        System.out.println(countComponents(3, new int[][]{{0, 1}, {0, 1}})); // 2, duplicate edge
    }
}
```

**How to run:** save as `CountComponents.java`, then run `java CountComponents.java`.

## 6. Walkthrough

Trace `countComponents(5, [[0,1],[1,2],[3,4]])`:

| edge | groupCount before | rootA vs rootB | action | groupCount after |
|---|---|---|---|---|
| start | — | — | — | 5 |
| (0,1) | 5 | 0 vs 1, different | union | 4 |
| (1,2) | 4 | 0 vs 2, different | union | 3 |
| (3,4) | 3 | 3 vs 4, different | union | 2 |

Final `groupCount` is `2`, matching the two components `{0,1,2}` and `{3,4}`.

## 7. Gotchas & takeaways

> Gotcha: decrementing `groupCount` unconditionally on every edge (instead of only when the union actually merges two different roots) overcounts when the input has duplicate edges or an edge between nodes already connected through other edges.

- Signal: "count the groups/components formed by these edges" is answered directly by a union-find group counter.
- A node with no edges at all still counts as its own component — initialize `groupCount = n`, not 0.
- Related problems: Redundant Connection, Graph Valid Tree, Accounts Merge, Most Stones Removed with Same Row or Column.
