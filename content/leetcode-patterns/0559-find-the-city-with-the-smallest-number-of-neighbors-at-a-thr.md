---
card: leetcode-patterns
gi: 559
slug: find-the-city-with-the-smallest-number-of-neighbors-at-a-thr
title: Find the City With the Smallest Number of Neighbors at a Threshold Distance
---

## 1. What it is

Given `n` cities connected by weighted, bidirectional roads `edges[i] = [from, to, weight]`, and a `distanceThreshold`, find the city that has the **fewest** other cities reachable within `distanceThreshold` (using the shortest path, not direct edges). If a tie, return the city with the **largest** number (largest index). Example: a small road network where one city is relatively isolated compared to the others within the given distance budget.

## 2. Why & when

This needs the shortest path between **every pair** of cities, not just from one source — a direct application of [Floyd-Warshall](0550-shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs.md)-style all-pairs shortest path, since running Dijkstra's algorithm from every single city individually would also work but is more code for a graph this small. Constraints: up to 100 cities — small enough that the `O(n^3)` all-pairs approach is comfortably fast enough.

## 3. Core concept

**Key idea:** Floyd-Warshall computes the shortest distance between every pair of nodes by considering each node, in turn, as a possible "intermediate stop" that might shorten some other pair's path. After it completes, `dist[i][j]` holds the true shortest distance between every pair `(i, j)`. Then, for each city, count how many other cities are within `distanceThreshold`, and pick the city with the fewest such neighbors (breaking ties toward the largest index).

**Steps:**
1. Initialize an `n x n` distance matrix: `dist[i][i] = 0`, `dist[i][j] = weight` for each direct edge, and infinity elsewhere.
2. Floyd-Warshall's triple loop: for each candidate intermediate city `mid`, for each pair `(i, j)`, check if routing through `mid` is shorter: `dist[i][mid] + dist[mid][j] < dist[i][j]`; if so, update `dist[i][j]`.
3. For each city `i`, count `j != i` where `dist[i][j] <= distanceThreshold`.
4. Track the city with the smallest such count, breaking ties by preferring the larger city index (checking cities in increasing order and using `<=` for updates naturally keeps the largest-index tie-winner).

**Why the intermediate node must be the outermost loop:** `dist[i][mid]` and `dist[mid][j]` must both already reflect every previously considered intermediate node before they are used to potentially improve `dist[i][j]` through `mid`. Putting `mid` as the outermost loop guarantees that by the time you consider routing through it, its own shortest distances to everything else are already as good as they can be using all *earlier* intermediates — this ordering is what makes the algorithm correct.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Floyd-Warshall checking whether routing i to j through mid beats the direct known distance">
  <g font-family="sans-serif" font-size="13">
    <circle cx="100" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="85" fill="#e6edf3" text-anchor="middle">i</text>
    <circle cx="350" cy="30" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="350" y="35" fill="#e6edf3" text-anchor="middle">mid</text>
    <circle cx="600" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="600" y="85" fill="#e6edf3" text-anchor="middle">j</text>
    <line x1="114" y1="72" x2="336" y2="38" stroke="#8b949e"/>
    <line x1="365" y1="38" x2="586" y2="72" stroke="#8b949e"/>
    <line x1="114" y1="88" x2="586" y2="88" stroke="#f0883e" stroke-dasharray="4"/>
    <text x="350" y="120" fill="#79c0ff" text-anchor="middle">check: dist[i][mid] + dist[mid][j] &lt; dist[i][j]?</text>
  </g>
</svg>

For every triple `(i, mid, j)`, Floyd-Warshall checks whether routing through `mid` beats the current best-known direct-or-indirect distance from `i` to `j`.

## 5. Runnable example

**Level 1 — Brute force.** Run Dijkstra's algorithm separately from each of the `n` cities. Works, and is `O(n * E log V)`, but needs `n` separate runs.

**KEY INSIGHT:** Floyd-Warshall computes all pairs of shortest distances in one unified triple loop, which is simpler to write correctly than orchestrating `n` separate Dijkstra runs, and is fast enough for the small city counts this problem allows.

**Level 2 — Optimal.** Floyd-Warshall, O(n^3).

**Level 3 — Hardened.** Handles disconnected city pairs (distance stays infinity, correctly excluded from the threshold count) and ties in the neighbor count (resolved toward the larger city index).

```java
// FindCityWithSmallestNeighbors.java
import java.util.*;

public class FindCityWithSmallestNeighbors {

    static int findTheCity(int n, int[][] edges, int distanceThreshold) {
        int[][] dist = new int[n][n];
        for (int[] row : dist) Arrays.fill(row, Integer.MAX_VALUE / 2); // avoid overflow when summing
        for (int i = 0; i < n; i++) dist[i][i] = 0;
        for (int[] e : edges) {
            dist[e[0]][e[1]] = e[2];
            dist[e[1]][e[0]] = e[2];
        }

        for (int mid = 0; mid < n; mid++) {
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    if (dist[i][mid] + dist[mid][j] < dist[i][j]) {
                        dist[i][j] = dist[i][mid] + dist[mid][j];
                    }
                }
            }
        }

        int bestCity = -1, minNeighbors = Integer.MAX_VALUE;
        for (int i = 0; i < n; i++) {
            int count = 0;
            for (int j = 0; j < n; j++) {
                if (i != j && dist[i][j] <= distanceThreshold) count++;
            }
            if (count <= minNeighbors) { // <= keeps the larger index on ties
                minNeighbors = count;
                bestCity = i;
            }
        }
        return bestCity;
    }

    public static void main(String[] args) {
        int[][] edges = {{0, 1, 3}, {1, 2, 1}, {1, 3, 4}, {2, 3, 1}};
        System.out.println(findTheCity(4, edges, 4)); // 3
    }
}
```

**How to run:** save as `FindCityWithSmallestNeighbors.java`, then run `java FindCityWithSmallestNeighbors.java`.

## 6. Walkthrough

Trace the neighbor counting step of `findTheCity(4, [[0,1,3],[1,2,1],[1,3,4],[2,3,1]], 4)`, after Floyd-Warshall computes all-pairs distances:

| city | distances to others | count within threshold 4 |
|---|---|---|
| 0 | to 1:3, to 2:4, to 3:5 | 2 (cities 1 and 2) |
| 1 | to 0:3, to 2:1, to 3:2 | 3 |
| 2 | to 0:4, to 1:1, to 3:1 | 3 |
| 3 | to 0:5, to 1:2, to 2:1 | 2 (cities 1 and 2) |

Cities `0` and `3` tie with `2` neighbors each. Using `<=` when scanning cities in increasing order lets the later, larger index (`3`) overwrite the earlier tie — the correct tie-break, returning `3`.

## 7. Gotchas & takeaways

> Gotcha: initializing unreachable distances to `Integer.MAX_VALUE` directly (instead of a smaller safe sentinel like `MAX_VALUE / 2`) risks integer overflow when computing `dist[i][mid] + dist[mid][j]`, silently wrapping into a negative number that could corrupt the whole distance matrix.

- Signal: "shortest distance between every pair of nodes," on a graph small enough for `O(n^3)`, is a direct fit for Floyd-Warshall — simpler to write than `n` separate single-source runs.
- The intermediate node must be the *outermost* loop for the algorithm to be correct — swapping the loop order silently produces wrong distances.
- Related problems: Network Delay Time (single-source version), Cheapest Flights Within K Stops.
