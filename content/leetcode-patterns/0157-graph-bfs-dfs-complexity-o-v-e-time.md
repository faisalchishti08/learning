---
card: leetcode-patterns
gi: 157
slug: graph-bfs-dfs-complexity-o-v-e-time
title: Graph BFS/DFS — complexity: O(V + E) time
---

## 1. What it is

Both BFS and DFS over a graph cost O(V + E) time, where `V` is the number of vertices (nodes) and `E` is the number of edges. Space is O(V) for the `visited` set plus O(V) for the queue (BFS) or the recursion/stack depth (DFS) in the worst case.

## 2. Why & when

Understanding WHY it is `V + E`, not just `V` or just `E`, matters because grid-based problems (where nodes are cells and edges are implicit adjacency) often need this translated into grid terms: `V` becomes the number of cells (`rows * cols`), and `E` becomes a small constant times `V` (each cell has at most 4 neighbors), so the bound simplifies to O(rows * cols) for typical grid traversal problems.

## 3. Core concept

**Key idea:** every node is visited (and marked) exactly once — that accounts for the `O(V)` term. But visiting a node also means examining ALL of its outgoing edges to find unvisited neighbors — summed across every node, the total number of edge-examinations equals the total number of edges in the graph (or twice that, for an undirected graph, since each edge is stored in both endpoints' adjacency lists) — that accounts for the `O(E)` term.

**Why O(V) for visiting nodes:** the `visited` check guarantees each node is enqueued/recursed into at most once, and each node is dequeued/processed at most once, so the total "node work" summed across the whole traversal is exactly `V` units of O(1) work each.

**Why O(E) for examining edges:** every node's adjacency list is scanned exactly once (when that node is processed), and the total length of ALL adjacency lists combined equals the number of edges (or `2 * E` for an undirected graph, since each edge appears in two lists) — so the total "edge work" summed across the whole traversal is `O(E)`.

**Why space is O(V):** the `visited` set holds at most `V` entries; the BFS queue or the DFS stack/recursion depth holds at most `V` nodes in the worst case (e.g. a graph that is one long path, where every node is "in flight" at some point).

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Total work splits into visiting each node once and examining each edge once">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="40" r="15" fill="#161b22" stroke="#79c0ff"/><text x="100" y="44" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="200" cy="40" r="15" fill="#161b22" stroke="#79c0ff"/><text x="200" y="44" fill="#e6edf3" text-anchor="middle">B</text>
    <circle cx="150" cy="110" r="15" fill="#161b22" stroke="#79c0ff"/><text x="150" y="114" fill="#e6edf3" text-anchor="middle">C</text>
    <circle cx="280" cy="110" r="15" fill="#161b22" stroke="#79c0ff"/><text x="280" y="114" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="115" y1="40" x2="185" y2="40" stroke="#3fb950"/>
    <line x1="108" y1="53" x2="142" y2="97" stroke="#3fb950"/>
    <line x1="208" y1="53" x2="222" y2="97" stroke="#3fb950"/>
    <line x1="165" y1="110" x2="265" y2="110" stroke="#3fb950"/>
    <text x="10" y="15" fill="#e6edf3">V = 4 nodes, E = 4 edges. Visiting each node: 4 units. Examining each edge (both directions, undirected): 8 checks.</text>
    <text x="10" y="175" fill="#e6edf3">Total work = O(V) + O(E) = O(4 + 4) = O(V + E), never more, since each edge is only ever traversed from its two endpoints.</text>
  </g>
</svg>

Each of the 4 edges is examined from both of its endpoints during the traversal, contributing a bounded, fixed amount of extra work per edge.

## 5. Runnable example

```java
// GraphComplexityDemo.java
import java.util.*;

public class GraphComplexityDemo {

    static int nodeVisits = 0;
    static int edgeExaminations = 0;

    static void bfs(Map<Integer, List<Integer>> graph, int start) {
        nodeVisits = 0;
        edgeExaminations = 0;
        Set<Integer> visited = new HashSet<>();
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(start);
        visited.add(start);

        while (!queue.isEmpty()) {
            int node = queue.poll();
            nodeVisits++;
            for (int neighbor : graph.getOrDefault(node, List.of())) {
                edgeExaminations++;
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
    }

    public static void main(String[] args) {
        // 4 nodes, 4 undirected edges (8 directed entries in adjacency lists)
        Map<Integer, List<Integer>> graph = new HashMap<>();
        graph.put(0, List.of(1, 2));
        graph.put(1, List.of(0, 2));
        graph.put(2, List.of(0, 1, 3));
        graph.put(3, List.of(2));

        bfs(graph, 0);
        System.out.println("nodeVisits=" + nodeVisits + " edgeExaminations=" + edgeExaminations);

        int totalAdjacencyEntries = graph.values().stream().mapToInt(List::size).sum();
        System.out.println("totalAdjacencyEntries=" + totalAdjacencyEntries);
    }
}
```

How to run: save as `GraphComplexityDemo.java`, then run `java GraphComplexityDemo.java`.

## 6. Walkthrough

For the graph `0-1, 0-2, 1-2, 2-3` (4 undirected edges, so `V=4`, `E=4`):

- `nodeVisits` ends at `4` — exactly `V`, since every node is dequeued and processed exactly once.
- `edgeExaminations` ends at `8` — exactly `2 * E`, since each undirected edge is stored once in each of its two endpoints' adjacency lists, and BFS scans every node's full adjacency list once.
- `totalAdjacencyEntries` also equals `8`, confirming that the sum of all adjacency list lengths is exactly `2 * E` for an undirected graph.

So total work is `nodeVisits + edgeExaminations = 4 + 8 = 12`, matching the `O(V + E)` bound (here written as `O(V + 2E)`, which is the same complexity class since constants are dropped).

## 7. Gotchas & takeaways

> Gotcha: for a DIRECTED graph, each edge appears in only ONE node's adjacency list (not two), so `edgeExaminations` would total exactly `E`, not `2E` — the complexity is still O(V + E) either way, but the exact constant differs between directed and undirected representations.

- For grid problems, translate directly: `V = rows * cols` (one node per cell), and `E` is bounded by `4 * V` (each cell has at most 4 neighbors), so the whole traversal is O(rows * cols) — no need to separately reason about "edges" in a grid, since the 4-neighbor check is already baked into the per-cell work.
- This is the standard cost for every problem in this section: Clone Graph, Number of Provinces, Pacific Atlantic Water Flow, Rotting Oranges, Snakes and Ladders, Minimum Genetic Mutation, Keys and Rooms, Is Graph Bipartite?, Find if Path Exists in Graph.
