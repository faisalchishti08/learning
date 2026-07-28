---
card: leetcode-patterns
gi: 523
slug: union-find-signal-dynamic-connectivity-or-grouping-by-equiva
title: Union-Find — signal: dynamic connectivity or grouping by equivalence
---

## 1. What it is

Union-Find (also called a disjoint-set union, or DSU) is a data structure that tracks a collection of items split into non-overlapping groups. It answers one question fast: "are these two items in the same group?" It also supports merging two groups into one.

## 2. Why & when

Reach for union-find whenever a problem describes connections being added one at a time, and asks about groups or connectivity as a result. A graph traversal (breadth-first search or depth-first search) can also answer "are these connected," but it must re-scan the whole graph for every query. Union-find instead updates its groups incrementally, in near-constant time per connection.

Learn to recognize these signals in a problem statement:

- **"Are these two nodes connected?"**, repeated across many pairs — each check is a `find` and comparison.
- **"Merge accounts/emails/groups if they share something"** — each shared item triggers a `union` of the two groups.
- **"Count the number of connected components"** — the final number of distinct groups after all unions.
- **"Will adding this edge create a cycle?"** — if the edge's two endpoints are already in the same group, adding it closes a cycle.
- **"Equations are given as equalities and inequalities; are they consistent?"** — union all the equal pairs first, then check the inequal pairs against the resulting groups.

The alternative is building an adjacency list and running breadth-first search or depth-first search from scratch for every query, which costs O(V + E) per query (V vertices, E edges). Union-find answers each query in near O(1) time after the structure is built, because it does not need to re-walk the graph.

## 3. Core concept

**Key idea:** each item points to a "parent." Following parent pointers upward always ends at a special item called the group's **representative** (or root), where an item is its own parent. Two items are in the same group exactly when following their parent chains reaches the same representative.

- **`find(x)`** follows parent pointers from `x` until it reaches the representative, and returns that representative.
- **`union(x, y)`** finds the representatives of `x` and `y`. If they differ, it attaches one representative under the other, merging the two groups into one.

Two optimizations make this fast: **path compression** (during `find`, point every visited node directly at the representative, flattening future lookups) and **union by rank/size** (attach the smaller group under the larger group's root, keeping trees shallow). Together they make `find` and `union` run in near O(1) amortized time.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two disjoint groups before a union, and one merged group after">
  <g font-family="sans-serif" font-size="13">
    <text x="150" y="20" fill="#e6edf3" text-anchor="middle">before union(B, D)</text>
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="65" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="100" cy="120" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="100" y="125" fill="#e6edf3" text-anchor="middle">B</text>
    <line x1="100" y1="76" x2="100" y2="104" stroke="#8b949e"/>
    <circle cx="220" cy="60" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="220" y="65" fill="#e6edf3" text-anchor="middle">C</text>
    <circle cx="220" cy="120" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="220" y="125" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="220" y1="76" x2="220" y2="104" stroke="#8b949e"/>
    <text x="500" y="20" fill="#e6edf3" text-anchor="middle">after union(B, D)</text>
    <circle cx="500" cy="40" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="500" y="45" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="440" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="440" y="105" fill="#e6edf3" text-anchor="middle">B</text>
    <line x1="490" y1="52" x2="450" y2="88" stroke="#8b949e"/>
    <circle cx="560" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="560" y="105" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="510" y1="52" x2="550" y2="88" stroke="#8b949e"/>
    <circle cx="500" cy="160" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="500" y="165" fill="#e6edf3" text-anchor="middle">C</text>
    <line x1="500" y1="56" x2="500" y2="144" stroke="#8b949e" stroke-dasharray="4"/>
  </g>
</svg>

Before the union, `{A, B}` and `{C, D}` are two separate groups. `union(B, D)` attaches one root under the other, merging everything into one group with a single representative, `A`.

## 5. Runnable example

The artifact below is a reusable signal-checker: it compares repeated breadth-first search connectivity checks against union-find, on a small set of connections.

### Signal-checker

```java
// UnionFindSignal.java
import java.util.*;

public class UnionFindSignal {

    static boolean bfsConnected(Map<Integer, List<Integer>> graph, int start, int target) {
        Set<Integer> visited = new HashSet<>();
        Deque<Integer> queue = new ArrayDeque<>();
        queue.add(start);
        visited.add(start);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            if (node == target) return true;
            for (int next : graph.getOrDefault(node, Collections.emptyList())) {
                if (visited.add(next)) queue.add(next);
            }
        }
        return false;
    }

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
        void union(int a, int b) {
            parent[find(a)] = find(b);
        }
    }

    public static void main(String[] args) {
        Map<Integer, List<Integer>> graph = new HashMap<>();
        int[][] edges = {{0, 1}, {1, 2}, {3, 4}};

        DSU dsu = new DSU(5);
        for (int[] e : edges) {
            graph.computeIfAbsent(e[0], k -> new ArrayList<>()).add(e[1]);
            graph.computeIfAbsent(e[1], k -> new ArrayList<>()).add(e[0]);
            dsu.union(e[0], e[1]);
        }

        System.out.println("bfs        0 and 2 connected: " + bfsConnected(graph, 0, 2));
        System.out.println("union-find 0 and 2 connected: " + (dsu.find(0) == dsu.find(2)));
        System.out.println("bfs        0 and 3 connected: " + bfsConnected(graph, 0, 3));
        System.out.println("union-find 0 and 3 connected: " + (dsu.find(0) == dsu.find(3)));
    }
}
```

**How to run:** save as `UnionFindSignal.java`, then run `java UnionFindSignal.java`.

## 6. Walkthrough

1. You read a problem describing connections (edges, shared accounts, equal variables) added one by one, then asking whether two items end up connected. That is the direct union-find signal.
2. Both approaches build the same graph from edges `(0,1)`, `(1,2)`, `(3,4)`, and union-find also merges `0` and `1`, then `1` and `2`, into one group.
3. Checking whether `0` and `2` are connected: breadth-first search walks `0 -> 1 -> 2`, exploring every edge along the way; union-find just compares `find(0)` and `find(2)`, both already pointing at the same representative.
4. Checking whether `0` and `3` are connected: breadth-first search explores the whole reachable component from `0` before concluding "no"; union-find compares two representatives directly, since `3` was only ever unioned with `4`.
5. Both approaches agree on every answer. The difference is speed on repeated queries: union-find pays the graph-walk cost once, during the unions, not on every query.

## 7. Gotchas & takeaways

> Gotcha: mistaking union-find for a tool that finds paths or shortest distances — it only answers "same group or not," and cannot tell you the path between two connected items. Use breadth-first search or depth-first search when you need the actual path.

- Signal words: "connected," "merge if shared," "count groups/components," "would creating this edge cause a cycle," "are these equations consistent."
- Union-find shines when connections arrive incrementally and you need many connectivity queries; a single one-off connectivity check is simpler with plain breadth-first search or depth-first search.
- Alternative: an adjacency list with repeated breadth-first search/depth-first search answers the same questions but re-walks the graph every time, costing O(V + E) per query instead of near O(1).
