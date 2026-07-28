---
card: leetcode-patterns
gi: 555
slug: path-with-minimum-effort
title: Path With Minimum Effort
---

## 1. What it is

Given an `m x n` grid of elevations, you travel from the top-left cell to the bottom-right cell, moving only up, down, left, or right. The "effort" of a path is the **maximum absolute elevation difference** between any two adjacent cells along it (not the sum). Return the minimum possible effort. Example: `heights = [[1,2,2],[3,8,2],[5,3,5]]` → `2` (a path exists where the largest single step is only `2`).

## 2. Why & when

A grid where each cell is a node and each adjacent pair is a weighted edge is a graph — this is [Dijkstra's algorithm](0550-shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs.md) again, but the "distance" being minimized is not a **sum** of edge weights, it is the **maximum** edge weight along the path (a bottleneck metric, like the weakest link in a chain). Constraints: up to 100x100 grid.

## 3. Core concept

**Key idea:** define `effort[cell]` as the smallest possible "largest single step" needed to reach that cell from the start. Relax an edge `(u, v)` with step cost `w = |height[u] - height[v]|` by checking if `max(effort[u], w) < effort[v]` — the candidate route's effort is the *larger* of what it already cost to reach `u` and this new step, not their sum.

**Steps:**
1. Treat each grid cell as a node; each of its up-to-4 neighbors is connected by an edge weighted by the absolute height difference.
2. Initialize `effort[start] = 0`, everything else infinity. Push `(start, 0)` onto a min-heap.
3. Repeatedly pop the smallest-effort entry (skip if stale). If it is the destination, return its effort immediately.
4. For each neighbor: compute `candidateEffort = max(effort[node], |height[node] - height[neighbor]|)`. If this is less than `effort[neighbor]`, update and push.
5. Return `effort[destination]`.

**Why `max` instead of `sum` still allows a Dijkstra-style greedy approach:** the same core guarantee holds — once a node's tentative effort is the smallest among all unfinalized nodes, no alternate path through a currently-larger-effort node could ever produce a smaller `max(...)` result, since `max` can only stay the same or grow as more steps are added, never shrink. This mirrors exactly why non-negative summed weights make Dijkstra's greedy choice safe.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 3x3 height grid where the minimum-effort path avoids the largest single step by routing around it">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">heights = [[1,2,2],[3,8,2],[5,3,5]]</text>
    <rect x="20" y="30" width="50" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="45" y="55" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="70" y="30" width="50" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="95" y="55" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="120" y="30" width="50" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="145" y="55" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="20" y="70" width="50" height="40" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="70" y="70" width="50" height="40" fill="#161b22" stroke="#f0883e"/>
    <text x="95" y="95" fill="#e6edf3" text-anchor="middle">8</text>
    <rect x="120" y="70" width="50" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="145" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="20" y="110" width="50" height="40" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="135" fill="#e6edf3" text-anchor="middle">5</text>
    <rect x="70" y="110" width="50" height="40" fill="#161b22" stroke="#30363d"/>
    <text x="95" y="135" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="120" y="110" width="50" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="145" y="135" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="350" y="80" fill="#79c0ff">route (0,0)-&gt;(0,1)-&gt;(0,2)-&gt;(1,2)-&gt;(2,2): steps 1,0,0,3 -&gt; max=3</text>
    <text x="350" y="110" fill="#3fb950">better route around the 8: max step = 2</text>
  </g>
</svg>

The path avoids stepping into or out of the cell with height `8`, keeping every single step's difference at `2` or less.

## 5. Runnable example

**Level 1 — Brute force.** Depth-first search every path from start to destination, tracking the maximum step seen, and keep the smallest such maximum across all paths. Exponential.

**KEY INSIGHT:** replacing Dijkstra's "add the edge weight" relaxation with "take the max of the running effort and the new step" correctly extends the same greedy shortest-path idea to a bottleneck (minimax) metric.

**Level 2 — Optimal.** Dijkstra's algorithm with a max-based relaxation rule, O(E log V) where E is roughly `4 * m * n`.

**Level 3 — Hardened.** Handles a 1x1 grid (effort `0`, start equals destination) and a grid where the optimal path revisits no cell but still requires zig-zagging around a high-elevation obstacle.

```java
// PathWithMinimumEffort.java
import java.util.*;

public class PathWithMinimumEffort {

    static int minimumEffortPath(int[][] heights) {
        int rows = heights.length, cols = heights[0].length;
        if (rows == 1 && cols == 1) return 0;

        int[][] effort = new int[rows][cols];
        for (int[] row : effort) Arrays.fill(row, Integer.MAX_VALUE);
        effort[0][0] = 0;

        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[2] - b[2]); // [row, col, effort]
        pq.add(new int[]{0, 0, 0});
        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int r = cur[0], c = cur[1], e = cur[2];
            if (e > effort[r][c]) continue;
            if (r == rows - 1 && c == cols - 1) return e;

            for (int[] d : directions) {
                int nr = r + d[0], nc = c + d[1];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                int step = Math.abs(heights[r][c] - heights[nr][nc]);
                int candidate = Math.max(e, step);
                if (candidate < effort[nr][nc]) {
                    effort[nr][nc] = candidate;
                    pq.add(new int[]{nr, nc, candidate});
                }
            }
        }
        return effort[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        int[][] heights1 = {{1, 2, 2}, {3, 8, 2}, {5, 3, 5}};
        System.out.println(minimumEffortPath(heights1)); // 2

        int[][] heights2 = {{1}};
        System.out.println(minimumEffortPath(heights2)); // 0
    }
}
```

**How to run:** save as `PathWithMinimumEffort.java`, then run `java PathWithMinimumEffort.java`.

## 6. Walkthrough

Trace the key portion of `minimumEffortPath([[1,2,2],[3,8,2],[5,3,5]])`:

1. Start `(0,0)`, effort `0`. Relax to `(0,1)`: step `|1-2|=1`, candidate `max(0,1)=1` — better than infinity, update.
2. From `(0,1)`, relax to `(0,2)`: step `|2-2|=0`, candidate `max(1,0)=1` — update.
3. From `(0,2)`, relax to `(1,2)`: step `|2-2|=0`, candidate `max(1,0)=1` — update.
4. From `(1,2)`, relax to `(2,2)`: step `|2-5|=3`, candidate `max(1,3)=3` — update, but this is not yet optimal.
5. A different route eventually finds `(2,2)` with effort `2` (avoiding a step through the `8`), and since `2 < 3`, that lower effort wins and gets popped first from the min-heap.
6. When `(2,2)` (the destination) is finally popped with effort `2`, the function returns `2` immediately.

## 7. Gotchas & takeaways

> Gotcha: relaxing with `effort[node] + step` (summing, as in ordinary Dijkstra) instead of `max(effort[node], step)` answers a completely different question — the total elevation change along the path, not the single hardest step, which is what "effort" means here.

- Signal: "minimize the worst single step along a path" (a bottleneck/minimax metric) is Dijkstra's algorithm with `max` in place of `+` during relaxation.
- The greedy correctness argument still holds for `max`-based relaxation, since `max` never decreases as more steps are appended to a path.
- Related problems: Path with Maximum Probability (multiplication instead of `max`), Network Delay Time (the standard summed version).
