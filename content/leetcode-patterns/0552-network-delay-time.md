---
card: leetcode-patterns
gi: 552
slug: network-delay-time
title: Network Delay Time
---

## 1. What it is

A signal is sent from node `k` across a network of `n` nodes, connected by directed, weighted edges `times[i] = [u, v, w]` (a signal from `u` reaches `v` in `w` time units). Return the minimum time for the signal to reach **every** node, or `-1` if some node is unreachable. Example: `times = [[2,1,1],[2,3,1],[3,4,1]]`, `n = 4`, `k = 2` → `2` (node `4` is the farthest, reached in `2` time units via `2->3->4`).

## 2. Why & when

This is the textbook [Dijkstra's algorithm](0550-shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs.md) application: a single source, non-negative weighted edges, and you need the shortest distance to every other node, then the maximum among them. Constraints: up to 100 nodes, 6,000 edges, weights up to 100 (non-negative).

## 3. Core concept

**Key idea:** run Dijkstra's algorithm from source `k`, computing the shortest time to reach every node. The signal has "reached everyone" exactly when the *slowest* of those shortest times finishes — so the answer is the maximum value in the final `dist[]` array (or `-1` if any node's distance is still infinity, meaning unreachable).

**Steps:**
1. Build a directed weighted adjacency list from `times`.
2. Run Dijkstra's algorithm from `k`, filling `dist[1..n]`.
3. If any `dist[i]` is still infinity, return `-1` — that node never receives the signal.
4. Otherwise, return `max(dist[1..n])`.

**Why the maximum (not the sum or the average) is the right answer:** all signals propagate in parallel through the network, not one after another — the whole network "finishes" receiving the signal only once its single slowest node has received it, exactly like the last runner finishing a race determines when the race is over.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Signal from node 2 reaching nodes 1, 3, and 4 with the maximum delay determining the answer">
  <g font-family="sans-serif" font-size="13">
    <circle cx="300" cy="30" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="35" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="150" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="105" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="450" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="450" y="105" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="600" cy="30" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="600" y="35" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="288" y1="42" x2="162" y2="88" stroke="#8b949e" marker-end="url(#a9)"/>
    <line x1="312" y1="42" x2="438" y2="88" stroke="#8b949e" marker-end="url(#a9)"/>
    <line x1="465" y1="90" x2="586" y2="42" stroke="#8b949e" marker-end="url(#a9)"/>
    <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="400" y="140" fill="#3fb950" text-anchor="middle">dist=[1,0,1,2] (nodes 1..4) -&gt; answer = max = 2</text>
  </g>
</svg>

Node `4` receives the signal last, at time `2` — the maximum across all shortest distances is the answer.

## 5. Runnable example

**Level 1 — Brute force.** Enumerate all paths from `k` to every node and take the minimum per node, then the maximum across nodes. Exponential.

**KEY INSIGHT:** Dijkstra's algorithm computes the shortest distance from one source to every node in a single run — no need to search per-destination separately.

**Level 2 — Optimal.** Dijkstra's algorithm with a priority queue, O(E log V).

**Level 3 — Hardened.** Handles unreachable nodes (`-1`), and a source node that has no outgoing edges at all when `n == 1`.

```java
// NetworkDelayTime.java
import java.util.*;

public class NetworkDelayTime {

    static int networkDelayTime(int[][] times, int n, int k) {
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i <= n; i++) graph.add(new ArrayList<>());
        for (int[] t : times) {
            graph.get(t[0]).add(new int[]{t[1], t[2]});
        }

        int[] dist = new int[n + 1];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[k] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
        pq.add(new int[]{k, 0});

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int node = cur[0], d = cur[1];
            if (d > dist[node]) continue;
            for (int[] edge : graph.get(node)) {
                int next = edge[0], weight = edge[1];
                if (dist[node] + weight < dist[next]) {
                    dist[next] = dist[node] + weight;
                    pq.add(new int[]{next, dist[next]});
                }
            }
        }

        int maxDist = 0;
        for (int i = 1; i <= n; i++) {
            if (dist[i] == Integer.MAX_VALUE) return -1;
            maxDist = Math.max(maxDist, dist[i]);
        }
        return maxDist;
    }

    public static void main(String[] args) {
        int[][] times1 = {{2, 1, 1}, {2, 3, 1}, {3, 4, 1}};
        System.out.println(networkDelayTime(times1, 4, 2)); // 2

        int[][] times2 = {{1, 2, 1}};
        System.out.println(networkDelayTime(times2, 2, 2)); // -1, node 1 unreachable from 2
    }
}
```

**How to run:** save as `NetworkDelayTime.java`, then run `java NetworkDelayTime.java`.

## 6. Walkthrough

Trace `networkDelayTime([[2,1,1],[2,3,1],[3,4,1]], 4, 2)`:

| step | popped | dist array (1..4) |
|---|---|---|
| start | — | [inf, 0, inf, inf] |
| pop (2,0) | node 2 | relax 2->1: dist[1]=1; relax 2->3: dist[3]=1 → [1,0,1,inf] |
| pop (1,1) or (3,1) | node 1 (no outgoing edges) | unchanged |
| pop (3,1) | node 3 | relax 3->4: dist[4]=2 → [1,0,1,2] |
| pop (4,2) | node 4 (no outgoing edges) | unchanged |

Final `dist = [1,0,1,2]` for nodes `1..4`. No infinities remain, so return `max(1,0,1,2) = 2`.

## 7. Gotchas & takeaways

> Gotcha: returning the sum of all distances instead of the maximum answers a different (and usually much larger, wrong) question — the network is fully informed the moment its slowest node receives the signal, not after every node has cumulatively received it one after another.

- Signal: "minimum time for a signal/message to reach every node from one source" is single-source shortest path, answered by Dijkstra's algorithm plus a final max.
- Always check for any remaining `Integer.MAX_VALUE` (or equivalent infinity) in `dist[]` before taking the max — an unreachable node must produce `-1`, not a wrong finite maximum.
- Related problems: Cheapest Flights Within K Stops, Path with Maximum Probability, Find the City With the Smallest Number of Neighbors at a Threshold Distance.
