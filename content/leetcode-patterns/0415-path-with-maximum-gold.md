---
card: leetcode-patterns
gi: 415
slug: path-with-maximum-gold
title: Path with Maximum Gold
---

## 1. What it is

Given a grid where each cell holds an amount of gold (`0` means no gold, and you cannot step on a `0` cell), find the maximum gold you can collect by starting at any cell, moving up/down/left/right, and never visiting the same cell twice. Example: `grid = [[0,6,0],[5,8,7],[0,9,0]]` → `24` (path `9 -> 8 -> 7`, or `9 -> 8 -> 5`... the best is `1,1 -> 2,1 -> nowhere better`; actual best path sums to `24`).

## 2. Why & when

Use this shape whenever a grid problem allows movement in ALL FOUR directions, forbids revisiting a cell, and there is no simple ordering rule (like Longest Increasing Path's strict increase) to guarantee acyclic exploration. Since gold values are not ordered, a classic memoized `dp[r][c]` table is not safe — the same cell could be reached along many different partial paths, each with a DIFFERENT set of already-collected cells. BACKTRACKING (explore, then un-mark and try elsewhere) is the correct tool here, not table-based DP.

## 3. Core concept

**Key idea:** try starting the path from EVERY cell that has gold. From each start, explore outward with depth-first search, marking cells visited so they are not reused, and un-marking them on the way back out ("backtrack") so other paths can still use them.

**Steps:**
1. For every cell `(r, c)` with `grid[r][c] > 0`, run a DFS starting there, and track the best total found across ALL starting cells.
2. In the DFS: temporarily set the current cell's gold to `0` (mark visited), add its ORIGINAL value to the running total, and recurse into each of the four neighbors that still has gold `> 0`.
3. After exploring all four directions, RESTORE the current cell's original gold value (backtrack), since a different path (from a different starting cell, or a different order) might need to walk through this same cell again.
4. The answer is the maximum total found across every DFS call, from every starting cell.

**Why backtracking (not memoized DP) is required:** the set of gold ALREADY collected differs for every distinct path that reaches a given cell, so `dp[r][c]` alone cannot capture "the best answer from here" — the answer depends on the FULL history of the path, not just the current position. Restoring the cell's value after exploring it is what allows a sibling branch (a path that does not go through this cell) to still collect its gold.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dfs exploring a path, temporarily zeroing a visited cell, then restoring it after backtracking so other paths can use it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">grid = [[0,6,0],[5,8,7],[0,9,0]]</text>
    <text x="10" y="45">DFS from (1,1)=8: mark 0, total=8, explore (1,2)=7 -&gt; total=15</text>
    <text x="10" y="65">after exploring, RESTORE grid[1][1]=8 -- other starts may still use it</text>
    <rect x="10" y="85" width="300" height="24" fill="#3fb950"/><text x="160" y="102" fill="#0d1117" text-anchor="middle" font-size="10">best path overall: 9 -&gt; 8 -&gt; 7 = 24</text>
  </g>
</svg>

Marking a cell visited, then restoring it after exploring, lets every other path still reach it.

## 5. Runnable example

```java
// PathWithMaximumGold.java
public class PathWithMaximumGold {

    static int[][] dirs = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

    // KEY INSIGHT: gold values have no ordering, so no memoized dp[r][c]
    // is safe -- backtracking (mark, explore, restore) is required.
    static int getMaximumGold(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int best = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] > 0) {
                    best = Math.max(best, dfs(grid, r, c));
                }
            }
        }
        return best;
    }

    static int dfs(int[][] grid, int r, int c) {
        int rows = grid.length, cols = grid[0].length;
        if (r < 0 || r >= rows || c < 0 || c >= cols || grid[r][c] == 0) return 0;

        int original = grid[r][c];
        grid[r][c] = 0; // mark visited
        int best = 0;
        for (int[] d : dirs) {
            best = Math.max(best, dfs(grid, r + d[0], c + d[1]));
        }
        grid[r][c] = original; // backtrack: restore for other paths
        return original + best;
    }

    public static void main(String[] args) {
        int[][] grid = {{0, 6, 0}, {5, 8, 7}, {0, 9, 0}};
        System.out.println(getMaximumGold(grid));
        // 24
    }
}
```

**How to run:** `java PathWithMaximumGold.java`

## 6. Walkthrough

Trace `dfs` starting from `(2, 1)` (value `9`):

| call | cell | value | marked (temp) | best neighbor sum | returns |
|---|---|---|---|---|---|
| dfs(2,1) | (2,1) | 9 | grid[2][1]=0 | dfs(1,1) explored next | 9 + 15 = 24 |
| dfs(1,1) | (1,1) | 8 | grid[1][1]=0 | dfs(1,2) explored next | 8 + 7 = 15 |
| dfs(1,2) | (1,2) | 7 | grid[1][2]=0 | no gold neighbors left | 7 |

After each call returns, the grid is restored to its original values, so starting from `(1,0)=5` or `(0,1)=6` later still sees the full grid. The overall maximum across all starts is `24`. Time complexity is O(m·n · 4^(number of gold cells)) in the worst case (bounded in practice since the problem caps total gold cells at 25), reflecting genuine path enumeration, not a polynomial DP. Space is O(number of gold cells) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting to RESTORE `grid[r][c]` after exploring it (skipping the backtrack step) permanently destroys gold values for every SUBSEQUENT starting cell tried in the outer loop — the grid must return to its original state after each full DFS call completes.

- Backtracking (mark, explore all directions, then un-mark) is required here specifically because there is no ordering rule (unlike Longest Increasing Path) to make memoization safe.
- Trying every possible STARTING cell with gold is necessary, since the best path is not guaranteed to start at any particular corner or edge.
- Related problems: Longest Increasing Path in a Matrix (also explores four directions, but the STRICT increase rule allows memoized DP instead of full backtracking), Unique Paths III (backtracking with an explicit visited set, counting complete paths that cover every empty cell).
