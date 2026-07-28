---
card: leetcode-patterns
gi: 558
slug: shortest-path-in-a-grid-with-obstacles-elimination
title: Shortest Path in a Grid with Obstacles Elimination
---

## 1. What it is

Given an `m x n` grid of `0`s (empty) and `1`s (obstacles), and a budget `k` of obstacles you are allowed to eliminate (walk through), find the minimum number of moves from the top-left cell to the bottom-right cell. Return `-1` if it is impossible even using the full budget. Example: `k = 1` lets you pass through one obstacle cell along your path, if doing so shortens it.

## 2. Why & when

Every move here costs exactly `1` (unweighted), so this looks like plain breadth-first search — but the twist is that "the same cell" can be reached in genuinely different, non-interchangeable situations depending on **how many obstacles you have already eliminated to get there**. The graph's real nodes are not grid cells alone, but **(cell, obstacles-eliminated-so-far)** pairs — a state-augmented breadth-first search. Constraints: up to 40x40 grid, `k` up to `m + n`.

## 3. Core concept

**Key idea:** track visited states as `(row, col, obstaclesUsed)`, not just `(row, col)`. Two paths reaching the same cell with a *different* number of obstacles eliminated so far are genuinely different situations — one might have budget left to eliminate more obstacles later, the other might not. A cell should only be marked "visited" for a specific obstacle-count, or (as an optimization) only when a new path reaches it using **fewer or equal** eliminations than any previous visit.

**Steps:**
1. Breadth-first search from `(0,0,0)` (0 obstacles eliminated so far), tracking moves as the breadth-first search layer count.
2. For each of the 4 neighbors: if the neighbor is empty (`0`), the new state is `(neighborRow, neighborCol, obstaclesUsed)` — same budget spent. If it is an obstacle (`1`), the new state is `(neighborRow, neighborCol, obstaclesUsed + 1)` — only valid if `obstaclesUsed + 1 <= k`.
3. Track visited states in a 2D array `minObstaclesUsed[row][col]`, storing the *fewest* obstacles used to reach that cell so far; only enqueue a new arrival at a cell if it uses strictly fewer obstacles than the best previously recorded for that cell (a larger-or-equal obstacle count can never lead to a better future than an earlier, cheaper arrival already explored).
4. The first time `(m-1, n-1, *)` is reached, in breadth-first search's move-count order, that move count is the answer. If the queue empties first, return `-1`.

**Why tracking obstacles-used per cell (not just visited/unvisited) is required:** breadth-first search's usual "mark visited once" shortcut assumes reaching a cell earlier is always at least as good as reaching it later. Here, an earlier arrival that used *more* of the obstacle budget could be strictly worse than a later arrival at the same cell that used *fewer* obstacles, since the cheaper arrival leaves more budget for later obstacles — so both must be considered unless the ordering of "used" values is checked.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two different paths reaching the same cell with different obstacle budgets remaining are tracked as different states">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">reaching cell (2,2):</text>
    <text x="20" y="50" fill="#79c0ff">path A: 6 moves, 0 obstacles used (went around)</text>
    <text x="20" y="80" fill="#f0883e">path B: 4 moves, 2 obstacles used (went through)</text>
    <text x="20" y="115" fill="#3fb950">both are worth keeping: A has more budget left, B is fewer moves so far</text>
  </g>
</svg>

Two arrivals at the same cell, with different move counts and different remaining obstacle budgets, are genuinely different states — neither strictly dominates the other unless both its moves and its obstacle usage are worse.

## 5. Runnable example

**Level 1 — Brute force.** Depth-first search every possible path, tracking obstacles used, and keep the minimum move count among all that finish within budget. Exponential.

**KEY INSIGHT:** augmenting each breadth-first search state with "obstacles eliminated so far" turns a single 2D grid search into a 3D state search, correctly distinguishing paths that would otherwise collide at the same cell.

**Level 2 — Optimal.** Breadth-first search over `(row, col, obstaclesUsed)` states, O(m · n · k).

**Level 3 — Hardened.** Handles `k` large enough to eliminate every obstacle in the grid (behaves like an empty grid), and the start or end cell itself being an obstacle (still enterable, consuming budget).

```java
// ShortestPathObstacles.java
import java.util.*;

public class ShortestPathObstacles {

    static int shortestPath(int[][] grid, int k) {
        int rows = grid.length, cols = grid[0].length;
        k = Math.min(k, rows + cols); // more budget than the longest possible path is wasted

        int[][] minObstaclesUsed = new int[rows][cols];
        for (int[] row : minObstaclesUsed) Arrays.fill(row, Integer.MAX_VALUE);
        minObstaclesUsed[0][0] = 0;

        Deque<int[]> queue = new ArrayDeque<>();
        queue.add(new int[]{0, 0, 0}); // row, col, obstaclesUsed
        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
        int moves = 0;

        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int[] cur = queue.poll();
                int r = cur[0], c = cur[1], used = cur[2];
                if (r == rows - 1 && c == cols - 1) return moves;

                for (int[] d : directions) {
                    int nr = r + d[0], nc = c + d[1];
                    if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                    int newUsed = used + grid[nr][nc]; // grid value is 0 or 1
                    if (newUsed > k) continue;
                    if (newUsed < minObstaclesUsed[nr][nc]) {
                        minObstaclesUsed[nr][nc] = newUsed;
                        queue.add(new int[]{nr, nc, newUsed});
                    }
                }
            }
            moves++;
        }
        return -1;
    }

    public static void main(String[] args) {
        int[][] grid1 = {{0, 0, 0}, {1, 1, 0}, {0, 0, 0}, {0, 1, 1}, {0, 0, 0}};
        System.out.println(shortestPath(grid1, 1)); // 6

        int[][] grid2 = {{0, 1, 1}, {1, 1, 1}, {1, 0, 0}};
        System.out.println(shortestPath(grid2, 1)); // -1, not enough budget
    }
}
```

**How to run:** save as `ShortestPathObstacles.java`, then run `java ShortestPathObstacles.java`.

## 6. Walkthrough

Trace the state check for cell `(1,0)` in `grid1`, an obstacle (`1`):

1. Reaching `(1,0)` from `(0,0)` requires eliminating this obstacle: `newUsed = 0 + 1 = 1`.
2. Check `newUsed (1) <= k (1)` — allowed.
3. Check `newUsed (1) < minObstaclesUsed[1][0]` (initially infinity) — true, so update `minObstaclesUsed[1][0] = 1` and enqueue `(1, 0, 1)`.
4. If some other path later reached `(1,0)` also using exactly `1` obstacle, it would be skipped (not strictly fewer), since the first arrival already explored every move from that state at the same or earlier breadth-first search layer.
5. The overall breadth-first search continues layer by layer until `(4,2)` (bottom-right) is popped, returning the move count at that layer, `6`.

## 7. Gotchas & takeaways

> Gotcha: using a plain 2D `visited[row][col]` array (ignoring obstacle count) incorrectly blocks a later path that reaches the same cell with *fewer* obstacles used but *more* moves — that later path could still be the one that ultimately succeeds within budget, while the first (fewer-moves) arrival exhausts its budget before reaching the end.

- Signal: "shortest path with a limited resource/budget that can be spent along the way" needs the resource amount folded into the search state, not just position — turning a 2D search into a 3D one.
- Capping `k` at `rows + cols` (the longest possible shortest path) avoids wasted work when the budget is far larger than could ever be useful.
- Related problems: Minimum Cost to Make at Least One Valid Path in a Grid, Cheapest Flights Within K Stops (also a budget-bounded shortest path).
