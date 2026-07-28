---
card: leetcode-patterns
gi: 531
slug: graph-valid-tree
title: Graph Valid Tree
---

## 1. What it is

Given `n` nodes labeled `0` to `n - 1` and a list of undirected edges, determine whether the edges form a valid tree — meaning the graph is fully connected (every node reachable from every other) and has no cycles. Example: `n = 5`, `edges = [[0,1],[0,2],[0,3],[1,4]]` → `true`. `n = 5`, `edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]` → `false` (edge `1-3` closes a cycle).

## 2. Why & when

A valid tree with `n` nodes has exactly two properties, both directly testable with [union-find](0524-union-find-template-disjoint-sets-with-union-by-rank-path-co.md): exactly `n - 1` edges, and no edge ever connects two nodes already in the same group (which would mean a cycle). This is the union-find cycle-detection signal combined with a simple edge-count check. Constraints: up to 2,000 nodes.

## 3. Core concept

**Key idea:** a graph with `n` nodes is a tree exactly when it is connected and acyclic. Checking "no cycles" is a `union` that always succeeds (never finds two endpoints already in the same group). Checking "connected" after that just means the final group count is 1.

**Steps:**
1. Quick reject: if the number of edges is not exactly `n - 1`, return `false` immediately — a tree on `n` nodes has exactly `n - 1` edges, no more, no less.
2. Otherwise, initialize union-find over `n` nodes.
3. For each edge `(u, v)`: if `find(u) == find(v)`, a cycle exists — return `false`.
4. Otherwise, `union(u, v)`.
5. If every edge unions successfully, the graph has exactly `n - 1` edges and no cycle, which guarantees it is also fully connected — return `true`.

**Why the edge-count check makes the connectivity check free:** a graph with `n - 1` edges and zero cycles must be connected, because every union strictly merges two previously separate groups; starting from `n` groups, exactly `n - 1` successful unions can only bring the group count down to 1. There is no way to use up all `n - 1` edges without cycles and still have more than one group left over.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A valid tree with 5 nodes and 4 edges vs an invalid graph where an extra edge closes a cycle">
  <g font-family="sans-serif" font-size="13">
    <text x="150" y="20" fill="#3fb950" text-anchor="middle">valid tree: n=5, edges=4</text>
    <circle cx="150" cy="60" r="14" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <circle cx="80" cy="110" r="14" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="115" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="150" cy="150" r="14" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="155" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="220" cy="110" r="14" fill="#161b22" stroke="#3fb950"/>
    <text x="220" y="115" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <line x1="140" y1="72" x2="90" y2="100" stroke="#8b949e"/>
    <line x1="150" y1="74" x2="150" y2="136" stroke="#8b949e"/>
    <line x1="160" y1="72" x2="210" y2="100" stroke="#8b949e"/>
    <text x="500" y="20" fill="#f0883e" text-anchor="middle">invalid: extra edge closes a cycle</text>
    <circle cx="450" cy="60" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="450" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <circle cx="410" cy="120" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="410" y="125" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="500" cy="120" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="125" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <line x1="440" y1="70" x2="418" y2="108" stroke="#8b949e"/>
    <line x1="460" y1="70" x2="492" y2="108" stroke="#8b949e"/>
    <line x1="424" y1="120" x2="486" y2="120" stroke="#f0883e" stroke-width="2" stroke-dasharray="4"/>
  </g>
</svg>

Left: 5 nodes, 4 edges, no cycle — a valid tree. Right: node `1`-`2` is an extra edge closing a cycle with `0`-`1` and `0`-`2`.

## 5. Runnable example

**Level 1 — Brute force.** Run breadth-first search or depth-first search from node 0, counting visited nodes to check connectivity, and separately track "visited via a back-edge" to detect a cycle. Works, but needs two separate traversal concerns.

**KEY INSIGHT:** the edge-count pre-check plus a single cycle-free union pass proves both properties (connected and acyclic) at once, without a separate traversal.

**Level 2 — Optimal.** Union-find with an edge-count pre-check, O(n · α(n)).

**Level 3 — Hardened.** Handles `n = 1` with zero edges (a single node is trivially a valid tree) and duplicate/self-loop edges (both immediately signal an invalid tree).

```java
// GraphValidTree.java
public class GraphValidTree {

    static class DSU {
        int[] parent;
        DSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false; // would close a cycle
            parent[rootA] = rootB;
            return true;
        }
    }

    static boolean validTree(int n, int[][] edges) {
        if (edges.length != n - 1) return false; // wrong edge count, cannot be a tree

        DSU dsu = new DSU(n);
        for (int[] edge : edges) {
            if (!dsu.union(edge[0], edge[1])) {
                return false; // cycle detected
            }
        }
        return true; // n-1 edges, no cycle -> connected and acyclic
    }

    public static void main(String[] args) {
        System.out.println(validTree(5, new int[][]{{0, 1}, {0, 2}, {0, 3}, {1, 4}})); // true
        System.out.println(validTree(5, new int[][]{{0, 1}, {1, 2}, {2, 3}, {1, 3}, {1, 4}})); // false, cycle
        System.out.println(validTree(1, new int[][]{})); // true, single node
        System.out.println(validTree(4, new int[][]{{0, 1}, {2, 3}})); // false, wrong edge count (disconnected)
    }
}
```

**How to run:** save as `GraphValidTree.java`, then run `java GraphValidTree.java`.

## 6. Walkthrough

Trace `validTree(5, [[0,1],[1,2],[2,3],[1,3],[1,4]])`:

1. Edge count check: 5 edges given, but a valid tree on 5 nodes needs exactly 4 — the function could already return `false` here, but tracing the union pass shows why it would fail anyway.
2. `union(0,1)`: different roots, merge succeeds.
3. `union(1,2)`: different roots, merge succeeds.
4. `union(2,3)`: different roots, merge succeeds. Groups: `{0,1,2,3}`, `{4}`.
5. `union(1,3)`: `find(1)` and `find(3)` are now the same representative — union fails, cycle detected, return `false`.

## 7. Gotchas & takeaways

> Gotcha: skipping the `edges.length != n - 1` pre-check and relying only on the cycle check misses the case where the graph has too few edges (disconnected, but acyclic) — a forest of two separate trees has no cycles at all, yet is not one connected tree.

- Signal: "is this graph a valid tree" combines a cycle-free union pass with an edge-count check — both properties, not just one.
- `n - 1` successful, cycle-free unions on `n` nodes automatically guarantee full connectivity — no separate connectivity pass needed.
- Related problems: Redundant Connection, Number of Connected Components in an Undirected Graph.
