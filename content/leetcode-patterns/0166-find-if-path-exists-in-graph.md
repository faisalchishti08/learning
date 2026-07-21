---
card: leetcode-patterns
gi: 166
slug: find-if-path-exists-in-graph
title: Find if Path Exists in Graph
---

## 1. What it is

Given `n` vertices labeled `0` to `n-1`, a list of undirected `edges`, and two nodes `source` and `destination`, return `true` if there is a valid path from `source` to `destination` (through zero or more intermediate vertices). Example: `n = 3`, `edges = [[0,1],[1,2],[2,0]]`, `source = 0`, `destination = 2` → `true`.

## 2. Why & when

This is the simplest possible Graph BFS/DFS question: "are these two specific nodes connected." It belongs in this section as the baseline case that Keys and Rooms, Number of Provinces, and Is Graph Bipartite all build on — a single traversal from `source`, checking if `destination` is ever visited.

## 3. Core concept

**Key idea:** build an adjacency list from the edge list, then run BFS or DFS starting from `source`. If `destination` is ever visited (or equals `source` itself), a path exists.

**Steps:**
1. Build an adjacency list: for each edge `[a, b]`, add `b` to `a`'s neighbor list AND `a` to `b`'s neighbor list (undirected).
2. If `source == destination`, return `true` immediately (a path of length zero always exists from a node to itself).
3. BFS (or DFS) from `source`, marking visited nodes.
4. If `destination` is dequeued/visited at any point, return `true`.
5. If the traversal completes without visiting `destination`, return `false`.

**Why it is correct:** a traversal starting at `source` visits every node reachable from it, following any sequence of edges; `destination` is reachable if and only if it appears among those visited nodes, which the traversal is guaranteed to discover if a path exists (and guaranteed NOT to discover if no path exists, since it explores every possible connection).

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS/DFS from source checks whether destination is ever reached">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="80" y="94" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="200" cy="50" r="16" fill="#161b22" stroke="#3fb950"/><text x="200" y="54" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="200" cy="130" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="94" y1="80" x2="186" y2="58" stroke="#8b949e"/>
    <line x1="200" y1="66" x2="200" y2="114" stroke="#8b949e"/>
    <line x1="94" y1="100" x2="186" y2="122" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">source=0 (green), destination=2 (blue). BFS from 0 reaches 1, then 2 -- path exists, return true</text>
  </g>
</svg>

Starting BFS at `0` reaches `1` first, then `2`, confirming a valid path from `source` to `destination`.

## 5. Runnable example

```java
// FindIfPathExistsInGraph.java
import java.util.*;

public class FindIfPathExistsInGraph {

    // Level 1 -- Brute force: Union-Find (disjoint set), unioning every
    // edge, then checking if source and destination share the same
    // root. Correct and actually efficient (near O(E * alpha(n))), but
    // requires a separate data structure instead of the simpler direct
    // BFS/DFS this problem's small scale doesn't really need.
    static boolean bruteForce(int n, int[][] edges, int source, int destination) {
        int[] parent = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;
        for (int[] edge : edges) union(parent, edge[0], edge[1]);
        return find(parent, source) == find(parent, destination);
    }

    static int find(int[] parent, int x) {
        while (parent[x] != x) x = parent[x];
        return x;
    }

    static void union(int[] parent, int a, int b) {
        int rootA = find(parent, a), rootB = find(parent, b);
        if (rootA != rootB) parent[rootA] = rootB;
    }

    // KEY INSIGHT: since we only need to answer ONE reachability
    // question (source to destination), a single BFS/DFS from source is
    // simpler than building a full Union-Find structure -- just stop
    // early the moment destination is found.

    // Level 2 -- Optimal: build adjacency list, BFS from source,
    // stop early if destination is reached. O(V + E) time, O(V + E) space.
    public static boolean validPath(int n, int[][] edges, int source, int destination) {
        if (source == destination) return true;

        List<List<Integer>> adjacency = new ArrayList<>();
        for (int i = 0; i < n; i++) adjacency.add(new ArrayList<>());
        for (int[] edge : edges) {
            adjacency.get(edge[0]).add(edge[1]);
            adjacency.get(edge[1]).add(edge[0]);
        }

        boolean[] visited = new boolean[n];
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(source);
        visited[source] = true;

        while (!queue.isEmpty()) {
            int node = queue.poll();
            if (node == destination) return true;
            for (int neighbor : adjacency.get(node)) {
                if (!visited[neighbor]) {
                    visited[neighbor] = true;
                    queue.offer(neighbor);
                }
            }
        }
        return false;
    }

    // Level 3 -- Hardened: source equal to destination must return true
    // immediately, even with zero edges in the graph, and a destination
    // in a completely separate disconnected component must return false.
    static boolean hardened(int n, int[][] edges, int source, int destination) {
        return validPath(n, edges, source, destination);
    }

    public static void main(String[] args) {
        int n = 3;
        int[][] edges = {{0,1},{1,2},{2,0}};

        System.out.println(bruteForce(n, edges, 0, 2));
        System.out.println(validPath(n, edges, 0, 2));

        int[][] disconnected = {{0,1}};
        System.out.println(hardened(3, disconnected, 0, 2));
    }
}
```

How to run: save as `FindIfPathExistsInGraph.java`, then run `java FindIfPathExistsInGraph.java`.

## 6. Walkthrough

Dry run of `validPath(n=3, edges=[[0,1],[1,2],[2,0]], source=0, destination=2)`:

| step | queue | dequeue | check | neighbors enqueued |
|---|---|---|---|---|
| start | [0] | - | `source != destination`, start BFS | - |
| 1 | [0] | 0 | `0 != 2` | 1 (unvisited) |
| 2 | [1] | 1 | `1 != 2` | 2 (unvisited) |
| 3 | [2] | 2 | `2 == 2` | return true |

The BFS finds `destination` on its third dequeue. Time complexity: O(V + E), building the adjacency list plus the traversal. Space complexity: O(V + E) for the adjacency list, plus O(V) for the visited array and queue.

## 7. Gotchas & takeaways

> Gotcha: forgetting to add BOTH directions of each edge to the adjacency list (`edge[0] -> edge[1]` AND `edge[1] -> edge[0]`) silently turns the undirected graph into a directed one, potentially reporting `false` for a path that actually exists in the reverse direction.

- Checking `source == destination` as a special case up front handles the (easily overlooked) valid path of length zero from a node to itself, which the general BFS loop would also find correctly, but only after unnecessarily building the adjacency list first.
- Related problems: Keys and Rooms (a directed-graph version of reachability, checking if EVERY node is reachable from one fixed start, rather than one specific destination), Number of Provinces (extends this same reachability idea to count how many separate groups the whole graph splits into).
