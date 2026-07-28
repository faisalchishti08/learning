---
card: leetcode-patterns
gi: 554
slug: path-with-maximum-probability
title: Path with Maximum Probability
---

## 1. What it is

Given `n` nodes connected by undirected edges, each with a success probability `succProb[i]` (between 0 and 1), find the path from `start` to `end` that **maximizes** the product of probabilities along the way. Return that maximum probability, or `0` if no path exists. Example: `edges = [[0,1],[1,2],[0,2]]`, `succProb = [0.5,0.5,0.2]`, `start=0`, `end=2` → `0.25` (path `0->1->2`: `0.5 * 0.5 = 0.25`, better than the direct edge's `0.2`).

## 2. Why & when

This is [Dijkstra's algorithm](0550-shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs.md) with two flips: multiply instead of add (since probabilities along a path combine multiplicatively, not additively), and maximize instead of minimize (since higher probability is "better," the opposite of "shorter"). Everything else about the algorithm — greedy expansion from the best-known frontier, relaxation, a priority queue — stays the same. Constraints: up to 10,000 nodes, 20,000 edges.

## 3. Core concept

**Key idea:** track `prob[node]`, the best known probability of successfully reaching that node, initialized to `0` everywhere except `start` (probability `1`, since you are already there). Use a **max-heap** (ordered by probability, largest first) instead of Dijkstra's usual min-heap. Relax an edge `(u, v, p)` by checking if `prob[u] * p > prob[v]`; if so, update and push.

**Steps:**
1. Build an undirected weighted graph where edge weights are success probabilities.
2. Initialize `prob[start] = 1`, everything else `0`. Push `(start, 1.0)` onto a max-heap.
3. Repeatedly pop the highest-probability entry. If it is stale (its stored probability is less than the current known `prob[]` for that node), skip it.
4. For every edge `(node, neighbor, p)`: if `prob[node] * p > prob[neighbor]`, update `prob[neighbor]` and push it.
5. Return `prob[end]` (which is `0` if `end` was never reached).

**Why maximizing a product still fits Dijkstra's greedy guarantee:** since every probability is between 0 and 1, multiplying by any edge's probability can only keep the running product the same or shrink it — never grow it. That means the node with the currently-highest known probability can never be improved further by a path through a lower-probability node, mirroring exactly why Dijkstra's minimum-distance greedy choice is safe for non-negative weights.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two paths from 0 to 2: a direct low-probability edge versus a two-hop path with higher combined probability">
  <g font-family="sans-serif" font-size="13">
    <circle cx="100" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="85" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="350" cy="30" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="350" y="35" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="600" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="600" y="85" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="114" y1="72" x2="336" y2="38" stroke="#3fb950" stroke-width="2"/>
    <text x="220" y="45" fill="#3fb950" font-size="11">p=0.5</text>
    <line x1="365" y1="38" x2="586" y2="72" stroke="#3fb950" stroke-width="2"/>
    <text x="480" y="45" fill="#3fb950" font-size="11">p=0.5</text>
    <line x1="114" y1="88" x2="586" y2="88" stroke="#f0883e"/>
    <text x="350" y="105" fill="#f0883e" font-size="11">direct p=0.2</text>
    <text x="350" y="135" fill="#79c0ff" text-anchor="middle">0-&gt;1-&gt;2: 0.5*0.5=0.25 &gt; direct 0.2</text>
  </g>
</svg>

The two-hop path's combined probability (`0.5 * 0.5 = 0.25`) beats the direct edge's `0.2`, even though it uses more edges.

## 5. Runnable example

**Level 1 — Brute force.** Enumerate every path from `start` to `end`, computing each path's product and tracking the maximum. Exponential.

**KEY INSIGHT:** flipping Dijkstra's min-heap to a max-heap and its addition to multiplication handles "maximize a product along a path" with the exact same greedy correctness argument as ordinary shortest path.

**Level 2 — Optimal.** Dijkstra's algorithm with a max-heap and multiplicative relaxation, O(E log V).

**Level 3 — Hardened.** Handles no path existing between `start` and `end` (returns `0`), and `start == end` (probability `1`, no edges needed).

```java
// PathWithMaxProbability.java
import java.util.*;

public class PathWithMaxProbability {

    static double maxProbability(int n, int[][] edges, double[] succProb, int start, int end) {
        List<List<double[]>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (int i = 0; i < edges.length; i++) {
            int u = edges[i][0], v = edges[i][1];
            graph.get(u).add(new double[]{v, succProb[i]});
            graph.get(v).add(new double[]{u, succProb[i]});
        }

        double[] prob = new double[n];
        prob[start] = 1.0;
        PriorityQueue<double[]> pq = new PriorityQueue<>((a, b) -> Double.compare(b[1], a[1])); // max-heap
        pq.add(new double[]{start, 1.0});

        while (!pq.isEmpty()) {
            double[] cur = pq.poll();
            int node = (int) cur[0];
            double p = cur[1];
            if (p < prob[node]) continue; // stale entry
            if (node == end) return p;
            for (double[] edge : graph.get(node)) {
                int next = (int) edge[0];
                double edgeProb = edge[1];
                if (prob[node] * edgeProb > prob[next]) {
                    prob[next] = prob[node] * edgeProb;
                    pq.add(new double[]{next, prob[next]});
                }
            }
        }
        return prob[end];
    }

    public static void main(String[] args) {
        int[][] edges = {{0, 1}, {1, 2}, {0, 2}};
        double[] succProb = {0.5, 0.5, 0.2};
        System.out.println(maxProbability(3, edges, succProb, 0, 2)); // 0.25

        int[][] noPathEdges = {{0, 1}};
        double[] noPathProb = {0.5};
        System.out.println(maxProbability(3, noPathEdges, noPathProb, 0, 2)); // 0.0
    }
}
```

**How to run:** save as `PathWithMaxProbability.java`, then run `java PathWithMaxProbability.java`.

## 6. Walkthrough

Trace `maxProbability(3, [[0,1],[1,2],[0,2]], [0.5,0.5,0.2], 0, 2)`:

| step | popped | prob array (0,1,2) |
|---|---|---|
| start | — | [1.0, 0, 0] |
| pop (0, 1.0) | node 0 | relax 0->1: `1.0*0.5=0.5 > 0` → prob[1]=0.5. relax 0->2: `1.0*0.2=0.2 > 0` → prob[2]=0.2. → [1.0, 0.5, 0.2] |
| pop (1, 0.5) | node 1 | relax 1->2: `0.5*0.5=0.25 > 0.2` → prob[2]=0.25 → [1.0, 0.5, 0.25] |
| pop (2, 0.25) | node 2 | this is `end`, return `0.25` immediately |

## 7. Gotchas & takeaways

> Gotcha: forgetting to flip the priority queue comparator (leaving Dijkstra's default min-heap in place) silently explores the *lowest*-probability frontier first, producing a wrong, usually too-small answer for a maximization problem.

- Signal: "maximize a product of edge weights along a path" is Dijkstra's algorithm with a max-heap and multiplication in place of addition — the same greedy correctness argument applies since probabilities never exceed 1.
- Returning as soon as `end` is popped from the max-heap is a valid early exit, exactly like Dijkstra's early exit when the target is finalized.
- Related problems: Network Delay Time, Path With Minimum Effort (a different combining rule: max instead of sum).
