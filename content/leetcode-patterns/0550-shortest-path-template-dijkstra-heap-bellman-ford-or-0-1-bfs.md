---
card: leetcode-patterns
gi: 550
slug: shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs
title: "Shortest Path — template: Dijkstra (heap), Bellman-Ford, or 0-1 BFS"
---

## 1. What it is

Three standard templates cover almost every weighted shortest-path problem: **Dijkstra's algorithm** (a priority queue, for non-negative weights), **Bellman-Ford** (repeated relaxation, handles negative weights and detects negative cycles), and **0-1 breadth-first search** (a deque, for graphs where every edge weighs exactly 0 or 1).

## 2. Why & when

Choose based on the graph's weights: all non-negative and no special structure → Dijkstra. Negative weights possible, or you need to detect a negative cycle, or the path length is bounded (like "at most K edges") → Bellman-Ford. Every weight is exactly 0 or 1 → 0-1 breadth-first search, which is simpler and faster than a full Dijkstra for that special case.

## 3. Core concept

**Dijkstra's algorithm (priority queue).**
1. Initialize `dist[start] = 0`, everything else infinity. Push `(start, 0)` onto a min-heap ordered by distance.
2. Repeatedly pop the smallest-distance entry. If its stored distance is greater than the current known `dist[]` for that node, skip it (a stale entry from an earlier, worse relaxation).
3. Otherwise, relax every outgoing edge: if `dist[node] + weight < dist[neighbor]`, update `dist[neighbor]` and push the new `(neighbor, newDist)`.
4. Stop when the heap is empty; `dist[]` holds the shortest distance to every reachable node.

**Bellman-Ford (repeated relaxation).**
1. Initialize `dist[start] = 0`, everything else infinity.
2. Repeat `V - 1` times (V = node count): relax every edge in the graph once. After `V - 1` full passes, all shortest paths are guaranteed found (a shortest path visits at most `V - 1` edges, since a DAG-like acyclic path cannot exceed that).
3. Optional extra pass: if any edge can still be relaxed on a `V`th pass, a negative-weight cycle exists.

**0-1 breadth-first search (deque).**
1. Initialize `dist[start] = 0`, everything else infinity. Push `start` onto a double-ended queue (deque).
2. Repeatedly pop from the **front**. For each edge: if it has weight `0`, push the neighbor to the **front** of the deque (it is just as close as the current node); if weight `1`, push it to the **back** (it is one step farther).
3. This keeps the deque implicitly sorted by distance, without needing a full priority queue.

**Why the "skip stale entries" check matters in Dijkstra:** a node can be pushed onto the heap multiple times, once per relaxation that improved its distance. Only the most recent (smallest) push is still valid; older, larger entries are stale leftovers, and processing them again would waste work without changing any final answer, so skipping them is a pure efficiency guard, not a correctness requirement.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three shortest path templates and when to pick each">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="60" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="45" fill="#e6edf3" text-anchor="middle">Dijkstra: priority queue</text>
    <text x="120" y="65" fill="#8b949e" text-anchor="middle" font-size="11">non-negative weights</text>
    <rect x="250" y="20" width="200" height="60" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="350" y="45" fill="#e6edf3" text-anchor="middle">Bellman-Ford: relax V-1 times</text>
    <text x="350" y="65" fill="#8b949e" text-anchor="middle" font-size="11">negative weights OK; detects neg cycles</text>
    <rect x="480" y="20" width="200" height="60" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="580" y="45" fill="#e6edf3" text-anchor="middle">0-1 BFS: deque</text>
    <text x="580" y="65" fill="#8b949e" text-anchor="middle" font-size="11">weights only 0 or 1</text>
  </g>
</svg>

Pick the template based on the graph's weight properties: general non-negative, possibly-negative, or the special 0/1 case.

## 5. Runnable example

All three templates on comparable graphs.

```java
// ShortestPathTemplate.java
import java.util.*;

public class ShortestPathTemplate {

    // Dijkstra: graph as adjacency list of [neighbor, weight]
    static int[] dijkstra(int n, List<List<int[]>> graph, int start) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
        pq.add(new int[]{start, 0});

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int node = cur[0], d = cur[1];
            if (d > dist[node]) continue; // stale entry
            for (int[] edge : graph.get(node)) {
                int next = edge[0], weight = edge[1];
                if (dist[node] + weight < dist[next]) {
                    dist[next] = dist[node] + weight;
                    pq.add(new int[]{next, dist[next]});
                }
            }
        }
        return dist;
    }

    // Bellman-Ford: edges as [u, v, weight]
    static int[] bellmanFord(int n, int[][] edges, int start) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;

        for (int i = 0; i < n - 1; i++) {
            for (int[] edge : edges) {
                int u = edge[0], v = edge[1], w = edge[2];
                if (dist[u] != Integer.MAX_VALUE && dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                }
            }
        }
        return dist;
    }

    // 0-1 BFS: graph as adjacency list of [neighbor, weight(0 or 1)]
    static int[] zeroOneBfs(int n, List<List<int[]>> graph, int start) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        Deque<Integer> deque = new ArrayDeque<>();
        deque.add(start);

        while (!deque.isEmpty()) {
            int node = deque.pollFirst();
            for (int[] edge : graph.get(node)) {
                int next = edge[0], weight = edge[1];
                if (dist[node] + weight < dist[next]) {
                    dist[next] = dist[node] + weight;
                    if (weight == 0) deque.addFirst(next);
                    else deque.addLast(next);
                }
            }
        }
        return dist;
    }

    public static void main(String[] args) {
        int n = 4;
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        graph.get(0).add(new int[]{1, 4});
        graph.get(0).add(new int[]{2, 1});
        graph.get(2).add(new int[]{1, 1});
        graph.get(1).add(new int[]{3, 1});

        System.out.println("Dijkstra: " + Arrays.toString(dijkstra(n, graph, 0)));

        int[][] edges = {{0, 1, 4}, {0, 2, 1}, {2, 1, 1}, {1, 3, 1}};
        System.out.println("Bellman-Ford: " + Arrays.toString(bellmanFord(n, edges, 0)));

        List<List<int[]>> zeroOneGraph = new ArrayList<>();
        for (int i = 0; i < n; i++) zeroOneGraph.add(new ArrayList<>());
        zeroOneGraph.get(0).add(new int[]{1, 1});
        zeroOneGraph.get(0).add(new int[]{2, 0});
        zeroOneGraph.get(2).add(new int[]{1, 0});
        zeroOneGraph.get(1).add(new int[]{3, 1});
        System.out.println("0-1 BFS: " + Arrays.toString(zeroOneBfs(n, zeroOneGraph, 0)));
    }
}
```

**How to run:** save as `ShortestPathTemplate.java`, then run `java ShortestPathTemplate.java`.

## 6. Walkthrough

Trace Dijkstra on `0->1(4), 0->2(1), 2->1(1), 1->3(1)`:

1. Start: `dist=[0,inf,inf,inf]`. Push `(0,0)`.
2. Pop `(0,0)`. Relax `0->1`: `dist[1]=4`, push `(1,4)`. Relax `0->2`: `dist[2]=1`, push `(2,1)`.
3. Pop `(2,1)` (smallest in heap). Relax edge `2->1`: `dist[2]+1=2 < dist[1]=4`, update `dist[1]=2`, push `(1,2)`.
4. Pop `(1,2)` (smaller than the stale `(1,4)` still in the heap). Relax `1->3`: `dist[1]+1=3 < dist[3]=inf`, update `dist[3]=3`, push `(3,3)`.
5. Pop `(3,3)`. No outgoing edges. Pop the stale `(1,4)`: since `4 > dist[1] (2)`, skip it.
6. Final: `dist=[0,2,1,3]`.

## 7. Gotchas & takeaways

> Gotcha: running Dijkstra's algorithm on a graph with a negative edge weight produces silently wrong answers, since the greedy "finalize the smallest tentative distance" step assumes no future edge can make an already-processed node's distance even smaller — negative weights break that assumption. Use Bellman-Ford instead.

- Dijkstra: O((V + E) log V) with a binary heap; requires non-negative weights.
- Bellman-Ford: O(V · E), slower but handles negative weights and detects negative cycles via an extra relaxation pass.
- 0-1 breadth-first search: O(V + E), the fastest option, but only valid when every edge weight is exactly 0 or 1.
