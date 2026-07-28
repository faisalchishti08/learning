---
card: leetcode-patterns
gi: 539
slug: topological-sort-complexity-o-v-e-time
title: Topological Sort — complexity: O(V + E) time
---

## 1. What it is

This page explains why both topological sort templates (Kahn's algorithm and depth-first search post-order) run in `O(V + E)` time, where `V` is the number of nodes (vertices) and `E` is the number of edges — and lists the named problems that use the pattern.

## 2. Why & when

Interviewers often ask "why is this linear, and not something worse, given it's a graph algorithm?" Explaining that every node and every edge is touched a small, fixed number of times demonstrates you understand the algorithm's mechanics, not just that "topological sort is O(V + E)."

## 3. Core concept

**Time — O(V + E) for Kahn's algorithm.** Building the graph and the `inDegree[]` array costs `O(E)` (one increment per edge). Every node is pushed onto the queue exactly once (when its in-degree first hits zero) and popped exactly once — `O(V)` total for queue operations. Processing a popped node's outgoing edges to decrement neighbors' in-degrees touches each edge exactly once across the whole algorithm — `O(E)` total. Summing: `O(V + E)`.

**Time — O(V + E) for DFS post-order.** Each node is visited (and marked DONE) exactly once, and from each node, every outgoing edge is examined exactly once to decide whether to recurse — `O(V)` for the node visits, `O(E)` for the edge examinations. Reversing the final order costs `O(V)`. Total: `O(V + E)`.

**Space — O(V + E).** The adjacency list itself stores `O(E)` entries. The in-degree array, visited/state array, queue, and output list are all `O(V)`. The recursion stack for DFS can also reach `O(V)` in the worst case (a long chain).

**Why neither approach depends on anything worse than V and E:** both algorithms visit each node a constant number of times (Kahn's: pushed once, popped once; DFS: visited once) and examine each directed edge a constant number of times (Kahn's: to decrement its target's in-degree; DFS: to decide whether to recurse into it). No node or edge is ever revisited, so the total work scales linearly with the graph's size, not with something like the number of possible orderings (which would be exponential).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each node visited once and each edge examined once, giving O(V+E) total work">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Every node: pushed/visited exactly once -&gt; O(V)</text>
    <text x="20" y="45" fill="#79c0ff">Every edge: examined exactly once (decrement or recurse) -&gt; O(E)</text>
    <text x="20" y="75" fill="#3fb950">no node or edge is ever revisited -&gt; total work = O(V) + O(E) = O(V + E)</text>
    <text x="20" y="110" fill="#f0883e">contrast: trying every permutation of V nodes -&gt; O(V!) -&gt; infeasible beyond ~12 nodes</text>
  </g>
</svg>

Linear work per node and per edge, with no revisits, is what keeps the total at `O(V + E)` instead of something exponential.

## 5. Runnable example

An instrumented Kahn's algorithm that counts total node-pops and edge-examinations, confirming both scale linearly with graph size.

```java
// TopoSortComplexity.java
import java.util.*;

public class TopoSortComplexity {

    static int nodeOps = 0;
    static int edgeOps = 0;

    static List<Integer> kahnTopoSort(int n, List<List<Integer>> graph) {
        nodeOps = 0;
        edgeOps = 0;
        int[] inDegree = new int[n];
        for (List<Integer> neighbors : graph) {
            for (int next : neighbors) {
                inDegree[next]++;
                edgeOps++;
            }
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (inDegree[i] == 0) queue.add(i);

        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int node = queue.poll();
            nodeOps++;
            order.add(node);
            for (int next : graph.get(node)) {
                edgeOps++;
                if (--inDegree[next] == 0) queue.add(next);
            }
        }
        return order;
    }

    static List<List<Integer>> buildChain(int n) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (int i = 0; i < n - 1; i++) graph.get(i).add(i + 1);
        return graph;
    }

    public static void main(String[] args) {
        for (int n : new int[]{10, 100, 1000, 10000}) {
            List<List<Integer>> graph = buildChain(n); // n nodes, n-1 edges
            kahnTopoSort(n, graph);
            System.out.printf("n=%-6d nodeOps=%-6d edgeOps=%-6d (V=%d, E=%d)%n",
                    n, nodeOps, edgeOps, n, n - 1);
        }
    }
}
```

**How to run:** save as `TopoSortComplexity.java`, then run `java TopoSortComplexity.java`.

## 6. Walkthrough

1. `buildChain(n)` creates a straight-line dependency chain: `0 -> 1 -> 2 -> ... -> n-1`, with exactly `n` nodes and `n - 1` edges.
2. For `n = 10`: `nodeOps` reaches exactly `10` (every node popped once) and `edgeOps` reaches exactly `9` (every edge examined once, during the in-degree build) plus `9` more (during the decrement loop) — the instrumented counts confirm both grow in direct proportion to `V` and `E`.
3. Doubling `n` from `1000` to `10000` roughly multiplies both `nodeOps` and `edgeOps` by ten, matching linear growth — not the quadratic or worse growth you would see from repeated re-scans.
4. This confirms the O(V + E) bound holds regardless of graph size, for this straight-chain worst-case shape.

## 7. Gotchas & takeaways

> Gotcha: assuming a sparse-looking adjacency *matrix* representation is just as fast is wrong — scanning an `n x n` matrix to find each node's neighbors costs `O(V²)` regardless of how few edges actually exist. Use an adjacency list to keep the cost at `O(V + E)`, proportional to the actual edge count.

- Time: O(V + E) for both Kahn's algorithm and DFS post-order — every node and every edge is touched a constant number of times.
- Space: O(V + E) for the adjacency list, plus O(V) for auxiliary arrays (in-degree, visited state, queue, output).
- Reference problems that use this pattern: Course Schedule, Course Schedule II, Minimum Height Trees, Find Eventual Safe States, All Ancestors of a Directed Acyclic Graph, Alien Dictionary, Parallel Courses III, Sort Items by Groups Respecting Dependencies, Sequence Reconstruction.
