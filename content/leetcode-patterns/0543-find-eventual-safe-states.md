---
card: leetcode-patterns
gi: 543
slug: find-eventual-safe-states
title: Find Eventual Safe States
---

## 1. What it is

Given a directed graph as an adjacency list `graph[i]` (the nodes reachable from node `i`), a node is **terminal** if it has no outgoing edges, and **safe** if every possible path starting from it eventually reaches a terminal node (never gets stuck in a cycle forever). Return all safe nodes, sorted ascending. Example: `graph = [[1,2],[2,3],[5],[0],[5],[],[]]` → `[2,4,5,6]`.

## 2. Why & when

"Every path from this node eventually terminates" is the mirror image of the [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md): instead of "this node has no remaining prerequisites," you want "this node has no remaining ways to reach a cycle." Reversing all the edges and running Kahn's algorithm from the terminal nodes (which have zero *outgoing* edges in the original graph, meaning zero *incoming* edges in the reversed graph structure used for this check) turns "detect unsafe nodes" into the same peeling process as topological sort. Constraints: up to 10,000 nodes.

## 3. Core concept

**Key idea:** a node is unsafe exactly when it lies on a cycle, or has a path leading into one. Reverse every edge, then run Kahn's algorithm using **out-degree in the original graph** as the "in-degree" to track: start from nodes with out-degree `0` (the terminal nodes — trivially safe), and repeatedly mark a node safe once every node it originally pointed to has already been confirmed safe.

**Steps:**
1. Build the reverse graph: for every original edge `u -> v`, add a reverse edge `v -> u`. Also track each node's original `outDegree[u]` (its count of outgoing edges in the *original* graph).
2. Push every node with `outDegree == 0` into a queue — these are terminal nodes, safe by definition.
3. Repeatedly pop a node, mark it safe, and for every node `p` that originally pointed to it (found via the reverse graph), decrement `outDegree[p]`. If `outDegree[p]` reaches `0`, push `p` — every node it pointed to is now confirmed safe.
4. Return all nodes marked safe, sorted.

**Why decrementing out-degree (not in-degree) is the trick here:** a node is safe only once *all* of its outgoing paths lead to safety. Tracking how many of its original outgoing edges still point to an unconfirmed node — and only marking it safe when that count hits zero — is exactly Kahn's in-degree logic, just applied to the reversed graph's structure.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Terminal node 5 (no outgoing edges) marked safe first, then node 2 becomes safe once its only outgoing edge target 5 is safe">
  <g font-family="sans-serif" font-size="13">
    <circle cx="150" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="150" y="85" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="350" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="85" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="166" y1="80" x2="334" y2="80" stroke="#8b949e" marker-end="url(#a4)"/>
    <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="250" y="65" fill="#8b949e" text-anchor="middle" font-size="11">2 -&gt; 5</text>
    <text x="350" y="120" fill="#3fb950" text-anchor="middle">5 has no outgoing edges: safe immediately</text>
    <text x="150" y="150" fill="#3fb950" text-anchor="middle">2's only target (5) is safe -&gt; 2 becomes safe</text>
  </g>
</svg>

Node `5` is terminal (no outgoing edges), so it is safe immediately. Node `2` only points to `5`, so once `5` is confirmed safe, `2` becomes safe too.

## 5. Runnable example

**Level 1 — Brute force.** For each node, run a depth-first search tracking the current path, marking a node unsafe as soon as a cycle is detected along any path from it. Repeated work across overlapping paths makes this O(V · (V + E)) without memoization.

**KEY INSIGHT:** reversing the graph and peeling from the terminal (zero out-degree) nodes inward turns "confirm safety" into the same layer-by-layer process as topological sort, without re-exploring paths.

**Level 2 — Optimal.** Reverse graph plus Kahn's-style peeling from terminal nodes, O(V + E).

**Level 3 — Hardened.** Handles a node with a self-loop (`graph[i]` contains `i`, always unsafe) and nodes that are already terminal.

```java
// FindEventualSafeStates.java
import java.util.*;

public class FindEventualSafeStates {

    static List<Integer> eventualSafeNodes(int[][] graph) {
        int n = graph.length;
        List<List<Integer>> reverseGraph = new ArrayList<>();
        for (int i = 0; i < n; i++) reverseGraph.add(new ArrayList<>());
        int[] outDegree = new int[n];

        for (int u = 0; u < n; u++) {
            outDegree[u] = graph[u].length;
            for (int v : graph[u]) {
                reverseGraph.get(v).add(u);
            }
        }

        Deque<Integer> queue = new ArrayDeque<>();
        boolean[] safe = new boolean[n];
        for (int i = 0; i < n; i++) {
            if (outDegree[i] == 0) queue.add(i);
        }

        while (!queue.isEmpty()) {
            int node = queue.poll();
            safe[node] = true;
            for (int predecessor : reverseGraph.get(node)) {
                if (--outDegree[predecessor] == 0) queue.add(predecessor);
            }
        }

        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            if (safe[i]) result.add(i);
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] graph = {{1, 2}, {2, 3}, {5}, {0}, {5}, {}, {}};
        System.out.println(eventualSafeNodes(graph)); // [2, 4, 5, 6]

        int[][] selfLoop = {{1}, {1}}; // node 1 points to itself
        System.out.println(eventualSafeNodes(selfLoop)); // []
    }
}
```

**How to run:** save as `FindEventualSafeStates.java`, then run `java FindEventualSafeStates.java`.

## 6. Walkthrough

Trace `eventualSafeNodes([[1,2],[2,3],[5],[0],[5],[],[]])`:

1. Out-degrees in the original graph: node `0`→2, `1`→1, `2`→1, `3`→1, `4`→1, `5`→0, `6`→0. Terminal nodes `5` and `6` start the queue.
2. Pop `5`, mark safe. In the reverse graph, `5`'s predecessors (nodes with an original edge into `5`) are `2` and `4`. Decrement their out-degrees: `2`→0, `4`→0. Both join the queue.
3. Pop `6`, mark safe. No node has an original edge into `6`, so nothing else changes.
4. Pop `2`, mark safe. `2`'s only predecessor is `1` (edge `1 -> 2`). Decrement `1`'s out-degree from `1` to `0`. `1` joins the queue.
5. Pop `4`, mark safe. No node has an original edge into `4`, so nothing else changes.
6. Pop `1`, mark safe. `1`'s only predecessor is `0` (edge `0 -> 1`). Decrement `0`'s out-degree from `2` to `1` — not yet zero, since the `0 -> 2` edge is still unresolved, so `0` does not join the queue.
7. The queue empties. Node `0` is never marked safe: its path `0 -> 1 -> 3 -> 0` cycles back to itself. Node `3` is never marked safe for the same reason, since it lies on that same cycle.
8. Safe nodes: `2, 4, 5, 6` — sorted, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: running plain Kahn's algorithm on the *original* graph's in-degrees answers a different question (which nodes have no unresolved prerequisites) — this problem needs out-degree on the original graph, tracked through the *reversed* adjacency list, to correctly propagate "safety" backward from terminal nodes.

- Signal: "every path from this node eventually reaches a terminal/base state" reframes as "peel safety inward from terminal nodes on the reversed graph," the mirror of topological sort.
- A node with a self-loop can never reach a terminal state through that edge, so its out-degree can never fully resolve to zero.
- Related problems: Course Schedule (same peeling idea, forward direction), Minimum Height Trees.
