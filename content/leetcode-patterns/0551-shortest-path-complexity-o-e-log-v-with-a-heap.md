---
card: leetcode-patterns
gi: 551
slug: shortest-path-complexity-o-e-log-v-with-a-heap
title: Shortest Path — complexity: O(E log V) with a heap
---

## 1. What it is

This page explains why Dijkstra's algorithm, implemented with a binary heap (priority queue), runs in `O((V + E) log V)` time — commonly shortened to `O(E log V)` since `E >= V - 1` in any connected graph — and lists the named problems that use the pattern.

## 2. Why & when

Interviewers often ask "why the log factor?" after you propose Dijkstra's algorithm. Explaining that the log comes specifically from heap operations, not from the graph traversal itself, shows you understand the algorithm's actual cost drivers, not just the memorized complexity string.

## 3. Core concept

**Time — O((V + E) log V).** Every edge can trigger one push onto the heap (when it successfully relaxes a neighbor's distance), so there are at most `O(E)` pushes across the whole run, plus one initial push for the start node. Each heap push or pop costs `O(log V)`, since the heap holds at most `O(V)` (or in the worst case `O(E)`, if many stale duplicate entries pile up) entries at once. Multiplying the number of heap operations by their per-operation cost gives `O(E log V)` for the relaxation work, plus `O(V log V)` in the worst case for popping every node — combined, `O((V + E) log V)`.

**Space — O(V + E).** The adjacency list costs `O(E)`. The `dist[]` array costs `O(V)`. The heap can hold up to `O(E)` entries in the worst case (one per relaxation), though it never exceeds `O(E)` since each edge contributes at most one useful push.

**Why the log factor comes specifically from the heap, not the graph:** without a heap, finding "the unfinalized node with the smallest tentative distance" requires an `O(V)` linear scan every time, giving `O(V^2)` total — fine for dense graphs, worse for sparse ones. A binary heap turns that same "find the minimum" operation into `O(log V)`, which is why the heap-based version scales better on graphs where `E` is much smaller than `V^2`.

**Contrast with Bellman-Ford's O(V · E).** Bellman-Ford relaxes every edge, `V - 1` times, giving `O(V · E)` — no heap, but strictly more total relaxation passes. For dense graphs with non-negative weights, Dijkstra's heap-based `O(E log V)` is typically faster; Bellman-Ford is chosen only when negative weights force it.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Heap push and pop operations each costing O(log V), multiplied by O(E) total operations">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Each edge relaxation: at most one heap push -&gt; O(E) pushes total</text>
    <text x="20" y="50" fill="#79c0ff">Each heap push or pop: O(log V), since the heap holds up to O(V) or O(E) entries</text>
    <text x="20" y="80" fill="#3fb950">Total: O(E) operations * O(log V) per operation = O(E log V)</text>
    <text x="20" y="115" fill="#f0883e">without a heap: finding the min each round is O(V) -&gt; O(V^2) total instead</text>
  </g>
</svg>

The heap turns "find the minimum tentative distance" from an O(V) scan into an O(log V) operation, which is what produces the log factor.

## 5. Runnable example

An instrumented Dijkstra's algorithm that counts total heap push and pop operations, confirming they scale with the edge count, not the square of the node count.

```java
// ShortestPathComplexity.java
import java.util.*;

public class ShortestPathComplexity {

    static long heapOps = 0;

    static int[] dijkstra(int n, List<List<int[]>> graph, int start) {
        heapOps = 0;
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
        pq.add(new int[]{start, 0});
        heapOps++;

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            heapOps++;
            int node = cur[0], d = cur[1];
            if (d > dist[node]) continue;
            for (int[] edge : graph.get(node)) {
                int next = edge[0], weight = edge[1];
                if (dist[node] + weight < dist[next]) {
                    dist[next] = dist[node] + weight;
                    pq.add(new int[]{next, dist[next]});
                    heapOps++;
                }
            }
        }
        return dist;
    }

    static List<List<int[]>> buildDenseGraph(int n) {
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        Random rand = new Random(42);
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int w = 1 + rand.nextInt(10);
                graph.get(i).add(new int[]{j, w});
                graph.get(j).add(new int[]{i, w});
            }
        }
        return graph;
    }

    public static void main(String[] args) {
        for (int n : new int[]{10, 50, 100}) {
            List<List<int[]>> graph = buildDenseGraph(n);
            int edgeCount = n * (n - 1) / 2;
            dijkstra(n, graph, 0);
            System.out.printf("V=%-4d E=%-6d heapOps=%-6d (roughly proportional to E)%n",
                    n, edgeCount, heapOps);
        }
    }
}
```

**How to run:** save as `ShortestPathComplexity.java`, then run `java ShortestPathComplexity.java`.

## 6. Walkthrough

1. `buildDenseGraph(n)` creates a complete graph: every pair of nodes connected, giving `E = n(n-1)/2` edges.
2. For `n = 10`, `E = 45`. The measured `heapOps` count stays within a small constant multiple of `E`, confirming pushes are bounded by edge relaxations, not by `V^2` node-scan operations.
3. For `n = 50`, `E = 1225` — roughly 27x more edges than `n=10`. `heapOps` grows by a similar factor, not by the much larger factor a quadratic algorithm would show.
4. For `n = 100`, `E = 4950`. The ratio of `heapOps` to `E` stays roughly constant across all three sizes, confirming the linear-in-`E` (times a slowly growing `log V` factor) behavior predicted by the complexity bound.

## 7. Gotchas & takeaways

> Gotcha: assuming the heap never holds more than `V` entries at once is wrong — because Dijkstra pushes a new entry every time a distance improves (not just once per node), the heap can temporarily hold up to `O(E)` entries, with older, stale entries for the same node still sitting inside it until popped and skipped.

- Time: O((V + E) log V), commonly written O(E log V) for connected graphs where E dominates V.
- Space: O(V + E) for the graph and distance array, with the heap itself bounded by O(E) in the worst case.
- Reference problems that use this pattern: Network Delay Time, Cheapest Flights Within K Stops, Path with Maximum Probability, Path With Minimum Effort, Bus Routes, Minimum Cost to Make at Least One Valid Path in a Grid, Shortest Path in a Grid with Obstacles Elimination, Find the City With the Smallest Number of Neighbors at a Threshold Distance.
