---
card: leetcode-patterns
gi: 538
slug: topological-sort-template-kahn-s-bfs-on-in-degrees-or-dfs-po
title: Topological Sort — template: Kahn's BFS on in-degrees, or DFS post-order
---

## 1. What it is

There are two standard templates for topological sort. **Kahn's algorithm** repeatedly removes nodes with zero remaining in-degree (breadth-first search-style, using a queue). The **depth-first search post-order** approach visits every node fully, then reverses the order nodes finished in. Both produce a valid order; each has different strengths.

## 2. Why & when

Use Kahn's algorithm when you need to detect a cycle as a clean side effect (the queue empties before all nodes are processed) and when you like iterative, queue-based code. Use the depth-first search approach when you are already writing a depth-first search-based solution for the same problem (like Alien Dictionary) and want to avoid building a separate in-degree array, or when you also need explicit cycle detection via a "currently visiting" state.

## 3. Core concept

**Kahn's algorithm (BFS on in-degrees).**
1. Build the graph and an `inDegree[]` array by counting incoming edges per node.
2. Push every node with `inDegree == 0` into a queue.
3. Repeatedly pop a node, append it to the result, and decrement the in-degree of each of its neighbors; push any neighbor whose in-degree just hit `0`.
4. If the result contains fewer than `n` nodes when the queue empties, a cycle exists.

**DFS post-order.**
1. Build the graph. Track each node's state: unvisited, visiting (on the current recursion stack), or done.
2. For every unvisited node, run a depth-first search. If it reaches a node marked "visiting," a cycle exists (a back-edge).
3. After a node's neighbors are all fully explored, push that node onto a stack (its post-order position).
4. Reverse the stack at the end — that reversed order is a valid topological order.

**Why the DFS order must be reversed:** a node is pushed onto the stack only after *all* of its dependents (things reachable from it) have already finished and been pushed. That means dependents end up lower in the stack than their dependencies. Reversing puts dependencies first, dependents after — the order the problem actually wants.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kahn's algorithm processing zero-in-degree nodes from a queue versus DFS pushing nodes onto a stack in post-order then reversing">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="280" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="160" y="45" fill="#e6edf3" text-anchor="middle">Kahn: queue nodes with inDegree==0,</text>
    <text x="160" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">pop, decrement neighbors, repeat</text>
    <rect x="400" y="20" width="280" height="50" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="540" y="45" fill="#e6edf3" text-anchor="middle">DFS: visit deepest first,</text>
    <text x="540" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">push on finish, then reverse the stack</text>
    <text x="350" y="130" fill="#8b949e" text-anchor="middle">both produce a valid order; Kahn detects cycles via leftover unprocessed nodes,</text>
    <text x="350" y="150" fill="#8b949e" text-anchor="middle">DFS detects cycles via a back-edge to a "visiting" node</text>
  </g>
</svg>

Two different traversal strategies reach the same kind of valid ordering, with different natural cycle-detection mechanics.

## 5. Runnable example

Both templates implemented side by side on the same graph.

```java
// TopoSortTemplate.java
import java.util.*;

public class TopoSortTemplate {

    // Kahn's algorithm: returns empty list if a cycle exists
    static List<Integer> kahnTopoSort(int n, List<List<Integer>> graph) {
        int[] inDegree = new int[n];
        for (List<Integer> neighbors : graph) {
            for (int next : neighbors) inDegree[next]++;
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (inDegree[i] == 0) queue.add(i);

        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int node = queue.poll();
            order.add(node);
            for (int next : graph.get(node)) {
                if (--inDegree[next] == 0) queue.add(next);
            }
        }
        return order.size() == n ? order : new ArrayList<>();
    }

    // DFS post-order: returns empty list if a cycle exists
    static final int UNVISITED = 0, VISITING = 1, DONE = 2;

    static List<Integer> dfsTopoSort(int n, List<List<Integer>> graph) {
        int[] state = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();
        boolean[] hasCycle = {false};

        for (int i = 0; i < n; i++) {
            if (state[i] == UNVISITED) {
                dfsVisit(i, graph, state, stack, hasCycle);
            }
        }
        if (hasCycle[0]) return new ArrayList<>();

        List<Integer> order = new ArrayList<>(stack);
        return order; // ArrayDeque as a stack pops in insertion-reversed order already
    }

    static void dfsVisit(int node, List<List<Integer>> graph, int[] state,
                          Deque<Integer> stack, boolean[] hasCycle) {
        state[node] = VISITING;
        for (int next : graph.get(node)) {
            if (state[next] == VISITING) {
                hasCycle[0] = true;
                return;
            }
            if (state[next] == UNVISITED) {
                dfsVisit(next, graph, state, stack, hasCycle);
            }
        }
        state[node] = DONE;
        stack.push(node); // push in post-order; ArrayDeque.push adds to the front
    }

    public static void main(String[] args) {
        int n = 4;
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        graph.get(0).add(1);
        graph.get(0).add(2);
        graph.get(1).add(3);
        graph.get(2).add(3);

        System.out.println("Kahn: " + kahnTopoSort(n, graph));
        System.out.println("DFS:  " + dfsTopoSort(n, graph));
    }
}
```

**How to run:** save as `TopoSortTemplate.java`, then run `java TopoSortTemplate.java`.

## 6. Walkthrough

Trace both on `0->1, 0->2, 1->3, 2->3`:

**Kahn's:** `inDegree = [0,1,1,2]`. Queue starts with `[0]`. Pop `0`, output `[0]`, decrement `1` and `2` to `[0,0]`, both join the queue. Pop `1` (or `2`), output grows, decrement `3`. Pop the other of `1`/`2`, decrement `3` again to `0`, `3` joins the queue. Pop `3`. Final order: `[0,1,2,3]` (or `[0,2,1,3]`).

**DFS:** starting at `0`: visit `1`, visit `3` (no neighbors, mark DONE, push `3`), back to `1` (mark DONE, push `1`), back to `0`, visit `2` (its neighbor `3` is already DONE, skip), mark `2` DONE, push `2`, mark `0` DONE, push `0`. Stack (top to bottom, since `ArrayDeque.push` adds to front): `[0, 2, 1, 3]` — read front-to-back, this is already `[0, 2, 1, 3]`, a valid order.

## 7. Gotchas & takeaways

> Gotcha: in the DFS approach, checking only a simple `visited` boolean (instead of the three-state `UNVISITED`/`VISITING`/`DONE`) cannot distinguish "this node is an ancestor on the current path" (a real cycle) from "this node was already fully explored on a different branch" (not a cycle) — always use the three-state version for correct cycle detection.

- Kahn's algorithm is iterative and naturally reports "how many nodes were successfully ordered," making cycle detection a simple count comparison.
- The DFS approach needs an explicit reverse (or a stack, which reverses naturally via push/pop) and a three-state visited marker for correct cycle detection.
- Both run in O(V + E) time and O(V + E) space for the graph representation.
