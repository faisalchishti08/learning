---
card: leetcode-patterns
gi: 155
slug: graph-bfs-dfs-signal-traversing-or-exploring-a-general-graph
title: Graph BFS/DFS — signal: traversing or exploring a general graph
---

## 1. What it is

Graph BFS/DFS is the pattern of visiting every reachable node in a general graph — not necessarily a tree — using either breadth-first search (level by level, via a queue) or depth-first search (as deep as possible, via recursion or a stack). Unlike a tree, a general graph can have cycles, multiple paths between two nodes, and nodes with more than one "parent", so a `visited` set becomes mandatory to avoid infinite loops.

## 2. Why & when

Recognise this pattern from wording like: "grid" or "matrix" where you move between adjacent cells, "graph" with explicit nodes and edges (an adjacency list or matrix), "islands", "provinces", "connected components", "clone/copy this structure", or "can you reach node B from node A". These all describe exploring connections between entities where a node can be revisited via a different route — the defining feature that separates general graphs from trees.

Use Graph BFS/DFS instead of Tree BFS/DFS whenever the input is NOT guaranteed to be a tree: a grid of cells, a list of edges, an adjacency list/matrix, or any structure where cycles are possible. If the input is explicitly a binary tree (each node has at most one parent, no cycles), the tree-specific patterns are simpler and sufficient.

Use BFS when the problem asks for the SHORTEST path/number of steps in an unweighted graph, or naturally processes things in "rounds" (like rotting oranges spreading one step per minute). Use DFS when you need to explore an entire connected component, check reachability, or naturally express the solution as "visit this node, then recursively visit its unvisited neighbors."

## 3. Core concept

**Key idea:** a graph node can be reached through more than one path, so without tracking which nodes have already been visited, a traversal can loop forever (or waste huge amounts of time revisiting the same nodes). The `visited` set (or a boolean array, or a mutated "visited" marker on the grid itself) is what makes graph traversal terminate correctly.

**General steps (either BFS or DFS):**
1. Pick a starting node (or, for "explore everything" problems, loop over every node as a possible start).
2. Mark the starting node visited BEFORE (or immediately as) it is added to the queue/stack/recursion — marking early, not late, is what prevents the same node from being queued twice.
3. Process a node: do whatever work the problem requires (count it, compare it, copy it).
4. For each neighbor of the current node: if it has not been visited, mark it visited and add it to the queue (BFS) or recurse into it (DFS).
5. Repeat until the queue/stack is empty (or the recursion bottoms out).

**Why it works:** marking a node visited the moment it is discovered (not the moment it is processed) guarantees it is only ever added to the queue/stack once, so every node is visited exactly once and the traversal is guaranteed to terminate, even in a graph full of cycles.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A visited set prevents infinite loops in a graph with a cycle">
  <g font-family="sans-serif" font-size="12">
    <circle cx="120" cy="40" r="16" fill="#161b22" stroke="#3fb950"/><text x="120" y="44" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="220" cy="40" r="16" fill="#161b22" stroke="#3fb950"/><text x="220" y="44" fill="#e6edf3" text-anchor="middle">B</text>
    <circle cx="170" cy="120" r="16" fill="#161b22" stroke="#3fb950"/><text x="170" y="124" fill="#e6edf3" text-anchor="middle">C</text>
    <line x1="136" y1="40" x2="204" y2="40" stroke="#8b949e"/>
    <line x1="128" y1="54" x2="162" y2="106" stroke="#8b949e"/>
    <line x1="212" y1="54" x2="178" y2="106" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">A-B-C-A forms a cycle. Without tracking "visited", A -&gt; B -&gt; C -&gt; A -&gt; B... loops forever.</text>
    <text x="10" y="175" fill="#e6edf3">Marking each node visited the moment it is discovered stops the traversal after exactly 3 visits.</text>
  </g>
</svg>

Without a `visited` set, the cycle `A -> B -> C -> A` would be walked endlessly; with one, each node is processed exactly once.

## 5. Runnable example

```java
// GraphTraversalTemplate.java
import java.util.*;

public class GraphTraversalTemplate {

    // BFS over an adjacency list, using a visited set to handle cycles.
    static List<Integer> bfs(Map<Integer, List<Integer>> graph, int start) {
        List<Integer> visitOrder = new ArrayList<>();
        Set<Integer> visited = new HashSet<>();
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(start);
        visited.add(start);

        while (!queue.isEmpty()) {
            int node = queue.poll();
            visitOrder.add(node);
            for (int neighbor : graph.getOrDefault(node, List.of())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
        return visitOrder;
    }

    // DFS over the same adjacency list, using recursion plus a visited set.
    static List<Integer> dfs(Map<Integer, List<Integer>> graph, int start) {
        List<Integer> visitOrder = new ArrayList<>();
        Set<Integer> visited = new HashSet<>();
        dfsHelper(graph, start, visited, visitOrder);
        return visitOrder;
    }

    static void dfsHelper(Map<Integer, List<Integer>> graph, int node, Set<Integer> visited, List<Integer> visitOrder) {
        visited.add(node);
        visitOrder.add(node);
        for (int neighbor : graph.getOrDefault(node, List.of())) {
            if (!visited.contains(neighbor)) {
                dfsHelper(graph, neighbor, visited, visitOrder);
            }
        }
    }

    public static void main(String[] args) {
        // Graph with a cycle: A(0) -> B(1) -> C(2) -> A(0)
        Map<Integer, List<Integer>> graph = new HashMap<>();
        graph.put(0, List.of(1));
        graph.put(1, List.of(2));
        graph.put(2, List.of(0));

        System.out.println(bfs(graph, 0));
        System.out.println(dfs(graph, 0));
    }
}
```

How to run: save as `GraphTraversalTemplate.java`, then run `java GraphTraversalTemplate.java`.

## 6. Walkthrough

Trace of `bfs(graph, 0)` on the cycle `0 -> 1 -> 2 -> 0`:

1. Start: `visited = {0}`, `queue = [0]`.
2. Dequeue `0`, record it. Its neighbor is `1`, unvisited: mark visited, enqueue. `queue = [1]`.
3. Dequeue `1`, record it. Its neighbor is `2`, unvisited: mark visited, enqueue. `queue = [2]`.
4. Dequeue `2`, record it. Its neighbor is `0`, but `0` is ALREADY visited — skip it. `queue = []`.
5. Queue empty, traversal ends. Result: `[0, 1, 2]` — each node visited exactly once, despite the cycle.

Without the `visited` check in step 4, `0` would be enqueued again, and the traversal would never terminate.

## 7. Gotchas & takeaways

> Gotcha: marking a node as visited when it is DEQUEUED/processed (instead of when it is first DISCOVERED and enqueued) allows the same node to be added to the queue multiple times before it is ever processed, wasting work and — in the worst case — still risking incorrect results if the problem cares about visit order or count.

- Grid-based graph problems (islands, rotting oranges, water flow) treat each cell as a node and its four (or eight) adjacent cells as neighbors — the same visited-set discipline applies, just using a 2D boolean array or by mutating the grid itself instead of a `HashSet`.
- The next two pages cover the two concrete templates (BFS with a queue, DFS with recursion or an explicit stack) and the shared O(V + E) complexity, where `V` is the number of nodes (vertices) and `E` is the number of edges.
