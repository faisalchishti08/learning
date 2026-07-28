---
card: leetcode-patterns
gi: 549
slug: shortest-path-signal-weighted-shortest-path-or-minimum-cost
title: Shortest Path — signal: weighted shortest path or minimum-cost traversal
---

## 1. What it is

A weighted shortest-path algorithm finds the minimum total cost to travel from a start node to a target node (or to every other node) through a graph where each edge has a cost, distance, or weight. This is different from plain breadth-first search, which only handles graphs where every edge costs exactly 1.

## 2. Why & when

Reach for a shortest-path algorithm whenever a problem describes edges with different costs, times, or probabilities, and asks for the cheapest, fastest, or most likely route. Plain breadth-first search finds the shortest path in *unweighted* graphs by counting edges — it breaks the moment edges have different weights, because a path with more edges can still cost less than a path with fewer, heavier edges.

Learn to recognize these signals in a problem statement:

- **"Minimum cost/time to travel from A to B"** with edges carrying different weights — the direct definition of weighted shortest path.
- **"Network delay," "travel time between cities," "flight cost"** — real-world weighted-edge framing of the same problem.
- **"Maximum probability of success along a path"** — a variant where you multiply edge weights instead of summing them, and want the maximum product instead of the minimum sum, but the same greedy expansion idea (Dijkstra's algorithm) still applies.
- **"Grid where some cells cost more to enter" or "minimum effort path"** — a grid is just a graph where each cell is a node and each adjacent cell pair is a weighted edge.
- **"At most K stops" or "at most K edges"** — a shortest-path variant with an added constraint on path length, usually solved with a modified Bellman-Ford or a state that also tracks stops used.

The alternative is trying every possible path (exponential) or using breadth-first search, which gives a wrong answer whenever edge weights are unequal. Dijkstra's algorithm, Bellman-Ford, or 0-1 breadth-first search are the correct tools, chosen based on whether weights are non-negative, whether negative weights exist, or whether weights are limited to just 0 and 1.

## 3. Core concept

**Key idea:** maintain a running "best known distance" to every node, starting at infinity except the source (distance 0). Repeatedly pick the node with the smallest known distance that has not been finalized yet, and **relax** its outgoing edges: if going through this node offers a shorter path to a neighbor than what is currently known, update that neighbor's distance.

**Why greedily finalizing the smallest-distance node works (for non-negative weights):** once a node has the smallest tentative distance among all unfinalized nodes, no other unfinalized node's path could possibly reach it more cheaply, since every other path would have to go through an edge of weight >= 0 from an already-larger distance. This greedy guarantee is what makes Dijkstra's algorithm correct — and exactly what breaks if negative edge weights are allowed, since a longer-looking path could later become cheaper.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A weighted graph where the path with more edges but lower total weight is the true shortest path">
  <g font-family="sans-serif" font-size="13">
    <circle cx="80" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="85" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="350" cy="30" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="350" y="35" fill="#e6edf3" text-anchor="middle">B</text>
    <circle cx="350" cy="130" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="350" y="135" fill="#e6edf3" text-anchor="middle">C</text>
    <circle cx="600" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="600" y="85" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="94" y1="72" x2="336" y2="38" stroke="#f0883e" stroke-width="2"/>
    <text x="200" y="45" fill="#f0883e" font-size="11">weight 10 (direct-looking, 1 hop)</text>
    <line x1="94" y1="88" x2="336" y2="122" stroke="#3fb950" stroke-width="2"/>
    <text x="200" y="145" fill="#3fb950" font-size="11">weight 1</text>
    <line x1="365" y1="122" x2="586" y2="88" stroke="#3fb950" stroke-width="2"/>
    <text x="500" y="145" fill="#3fb950" font-size="11">weight 1</text>
    <line x1="365" y1="40" x2="586" y2="72" stroke="#8b949e"/>
    <text x="500" y="45" fill="#8b949e" font-size="11">weight 8</text>
  </g>
</svg>

The path `A -> C -> D` uses 2 edges but totals weight 2, cheaper than the 1-edge-looking `A -> B` at weight 10 alone — edge count alone does not determine the shortest path.

## 5. Runnable example

The artifact below is a reusable signal-checker: it compares plain breadth-first search (which ignores weights) against Dijkstra's algorithm (which respects them) on the same weighted graph.

### Signal-checker

```java
// ShortestPathSignal.java
import java.util.*;

public class ShortestPathSignal {

    static int bfsHopCount(Map<Integer, List<int[]>> graph, int start, int target) {
        Map<Integer, Integer> dist = new HashMap<>();
        Deque<Integer> queue = new ArrayDeque<>();
        dist.put(start, 0);
        queue.add(start);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int[] edge : graph.getOrDefault(node, Collections.emptyList())) {
                int next = edge[0];
                if (!dist.containsKey(next)) {
                    dist.put(next, dist.get(node) + 1); // counts hops, ignores weight
                    queue.add(next);
                }
            }
        }
        return dist.getOrDefault(target, -1);
    }

    static int dijkstraWeightedDistance(Map<Integer, List<int[]>> graph, int start, int target, int n) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
        pq.add(new int[]{start, 0});

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int node = cur[0], d = cur[1];
            if (d > dist[node]) continue;
            for (int[] edge : graph.getOrDefault(node, Collections.emptyList())) {
                int next = edge[0], weight = edge[1];
                if (dist[node] + weight < dist[next]) {
                    dist[next] = dist[node] + weight;
                    pq.add(new int[]{next, dist[next]});
                }
            }
        }
        return dist[target] == Integer.MAX_VALUE ? -1 : dist[target];
    }

    public static void main(String[] args) {
        Map<Integer, List<int[]>> graph = new HashMap<>();
        graph.put(0, Arrays.asList(new int[]{1, 10}, new int[]{2, 1}));
        graph.put(2, Arrays.asList(new int[]{3, 1}));

        System.out.println("bfs hop count 0->3 (ignores weight): " + bfsHopCount(graph, 0, 3));
        System.out.println("dijkstra weighted distance 0->3: " + dijkstraWeightedDistance(graph, 0, 3, 4));
    }
}
```

**How to run:** save as `ShortestPathSignal.java`, then run `java ShortestPathSignal.java`.

## 6. Walkthrough

1. You read a problem describing routes or connections with different costs, times, or weights, then asking for the cheapest way to travel between two points. That is the direct weighted shortest-path signal.
2. Plain breadth-first search from node `0` reaches node `3` via `0 -> 2 -> 3`, counting `2` hops — but it never compares this against the alternative `0 -> 1` (which does not even reach `3` here), so its "hop count" answer is not measuring cost at all.
3. Dijkstra's algorithm starts with `dist[0]=0`, relaxes `0`'s edges to get `dist[1]=10` and `dist[2]=1`, then processes node `2` (the smaller tentative distance) and relaxes its edge to get `dist[3]=2`.
4. Node `1` is processed later, but it has no outgoing edges here, so it contributes nothing further.
5. The final weighted distance to node `3` is `2`, correctly reflecting the true cheapest path `0 -> 2 -> 3` (weights `1 + 1`), which plain hop-counting could never have surfaced.

## 7. Gotchas & takeaways

> Gotcha: using plain breadth-first search on a weighted graph silently produces a wrong "shortest path," since it only tracks the number of edges, not their weights — always check whether edge weights matter before choosing breadth-first search over a real shortest-path algorithm.

- Signal words: "cost," "weight," "time," "distance," "probability," "minimum effort," "at most K stops."
- Dijkstra's algorithm requires non-negative weights; use Bellman-Ford if negative weights are possible; use 0-1 breadth-first search (a deque-based trick) if every weight is exactly 0 or 1.
- Alternative: brute-force path enumeration is exponential; plain breadth-first search is wrong whenever weights are unequal.
