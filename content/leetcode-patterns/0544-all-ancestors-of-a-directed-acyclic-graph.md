---
card: leetcode-patterns
gi: 544
slug: all-ancestors-of-a-directed-acyclic-graph
title: All Ancestors of a Directed Acyclic Graph
---

## 1. What it is

Given a directed acyclic graph (DAG) with `n` nodes and a list of directed edges, return, for every node, the sorted list of all its **ancestors** — nodes that can reach it through one or more directed edges. Example: `n = 5`, `edges = [[0,3],[0,4],[1,3],[2,4],[2,3],[3,4]]` → node `4`'s ancestors are `[0,1,2,3]` (every node that has a path leading to `4`).

## 2. Why & when

"Which nodes can reach this node" is exactly what a [topological sort](0538-topological-sort-template-kahn-s-bfs-on-in-degrees-or-dfs-po.md) traversal order lets you compute efficiently: process nodes in topological order (every ancestor before its descendants), and propagate each node's known ancestor set forward to its direct children. Constraints: up to 1,000 nodes, up to 100,000 edges.

## 3. Core concept

**Key idea:** process nodes in topological order. When you process node `u`, every ancestor of `u` has already been fully determined (since they come earlier in the order). For each direct edge `u -> v`, add `u` itself, plus everything already known to be an ancestor of `u`, into `v`'s ancestor set.

**Steps:**
1. Build the graph and compute a topological order using Kahn's algorithm.
2. Initialize `ancestors[i]` as an empty set for every node.
3. Process nodes in topological order. For each node `u`, for each direct edge `u -> v`: add `u` to `ancestors[v]`, then add every element of `ancestors[u]` to `ancestors[v]` too (using a `Set` avoids duplicates automatically).
4. After processing all nodes, sort and return each node's ancestor set.

**Why processing in topological order guarantees correctness:** `ancestors[u]` is only read when computing `ancestors[v]` for an edge `u -> v`. Topological order guarantees `u` is fully processed (all of its own incoming edges already folded in) before that read happens — so `ancestors[u]` is complete and correct at the moment it is used.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Node 0 points to 3, which points to 4; processing in topological order propagates 0 as an ancestor of 3, then both 0 and 3 as ancestors of 4">
  <g font-family="sans-serif" font-size="13">
    <circle cx="100" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="85" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="300" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="85" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="500" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="85" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="118" y1="80" x2="282" y2="80" stroke="#8b949e" marker-end="url(#a5)"/>
    <line x1="318" y1="80" x2="482" y2="80" stroke="#8b949e" marker-end="url(#a5)"/>
    <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="200" y="65" fill="#8b949e" text-anchor="middle" font-size="11">ancestors[3] += {0}</text>
    <text x="400" y="65" fill="#8b949e" text-anchor="middle" font-size="11">ancestors[4] += {3} U ancestors[3] = {0,3}</text>
  </g>
</svg>

Processing `0` first adds it to `3`'s ancestor set. Processing `3` next adds both `3` itself and everything already in `3`'s ancestor set (`{0}`) to `4`'s ancestor set.

## 5. Runnable example

**Level 1 — Brute force.** For every node, run a depth-first search or breadth-first search backward (or forward from every other node) to check reachability. O(n · (V + E)).

**KEY INSIGHT:** propagating ancestor sets forward along a topological order computes every node's ancestors in one pass, reusing already-computed ancestor sets instead of re-searching per node.

**Level 2 — Optimal.** Topological order plus forward ancestor-set propagation, O(V + E) edges processed, with set operations costing up to O(V) each in the worst case (dense graphs), giving O(V · (V + E)) overall in the worst case but far fewer redundant searches than the brute force.

**Level 3 — Hardened.** Handles nodes with no ancestors at all (empty result) and a node reachable through multiple different paths (no duplicate ancestors, thanks to using a `Set`).

```java
// AllAncestorsOfDAG.java
import java.util.*;

public class AllAncestorsOfDAG {

    static List<List<Integer>> getAncestors(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        int[] inDegree = new int[n];
        for (int[] e : edges) {
            graph.get(e[0]).add(e[1]);
            inDegree[e[1]]++;
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (inDegree[i] == 0) queue.add(i);

        List<Set<Integer>> ancestors = new ArrayList<>();
        for (int i = 0; i < n; i++) ancestors.add(new TreeSet<>());

        while (!queue.isEmpty()) {
            int u = queue.poll();
            for (int v : graph.get(u)) {
                ancestors.get(v).add(u);
                ancestors.get(v).addAll(ancestors.get(u));
                if (--inDegree[v] == 0) queue.add(v);
            }
        }

        List<List<Integer>> result = new ArrayList<>();
        for (Set<Integer> set : ancestors) result.add(new ArrayList<>(set));
        return result;
    }

    public static void main(String[] args) {
        int[][] edges = {{0, 3}, {0, 4}, {1, 3}, {2, 4}, {2, 3}, {3, 4}};
        List<List<Integer>> result = getAncestors(5, edges);
        for (int i = 0; i < result.size(); i++) {
            System.out.println("node " + i + ": " + result.get(i));
        }
        // node 0: []
        // node 1: []
        // node 2: []
        // node 3: [0, 1, 2]
        // node 4: [0, 1, 2, 3]
    }
}
```

**How to run:** save as `AllAncestorsOfDAG.java`, then run `java AllAncestorsOfDAG.java`.

## 6. Walkthrough

Trace processing node `3` (assuming its ancestors are already fully computed as `{0, 1, 2}` from prior steps), with edge `3 -> 4`:

1. `ancestors[4].add(3)` — `3` itself becomes an ancestor of `4`.
2. `ancestors[4].addAll(ancestors[3])` — copies `{0, 1, 2}` into `ancestors[4]`.
3. `ancestors[4]` now holds `{0, 1, 2, 3}`, exactly the four nodes that can reach `4`.
4. Since `TreeSet` keeps elements sorted, converting it to a list at the end needs no separate sort step.

## 7. Gotchas & takeaways

> Gotcha: propagating ancestors in an arbitrary node order (not a valid topological order) can read an incomplete `ancestors[u]` before all of `u`'s own ancestors have been folded in, silently producing an incomplete ancestor list for its descendants.

- Signal: "which nodes can reach this node" (the reverse of "which nodes are reachable from this node") is solved by propagating sets forward along a topological order.
- Using a `TreeSet<Integer>` per node keeps results both deduplicated and sorted, satisfying the "sorted list" output requirement for free.
- Related problems: Course Schedule II (produces the topological order this problem builds on), Find Eventual Safe States.
