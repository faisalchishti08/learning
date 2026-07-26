---
card: leetcode-patterns
gi: 403
slug: dp-grid-matrix-template-dp-r-c-from-top-and-left-neighbors
title: "DP: Grid / Matrix — template: dp[r][c] from top and left neighbors"
---

## 1. What it is

This page gives the two reusable templates for grid-DP problems: the PATH-COUNTING template (sums the neighbors), and the PATH-COST template (takes the minimum or maximum of the neighbors, plus the current cell's own value).

## 2. Why & when

Use the path-counting template when a problem asks "how many ways," moving only right and down (or the equivalent triangle/falling-path shape). Use the path-cost template when a problem asks for the MINIMUM or MAXIMUM total along a path, since a single best path — not a count of all of them — is what matters.

## 3. Core concept

**Template A — path counting.**
1. Set `dp[r][0] = 1` for every row `r` and `dp[0][c] = 1` for every column `c` (exactly one way to reach any edge cell: keep moving in the one available direction), unless an obstacle blocks that cell, in which case it stays `0`.
2. For `r` from `1` to `rows-1`, for `c` from `1` to `cols-1`: `dp[r][c] = dp[r-1][c] + dp[r][c-1]` (skip cells that are obstacles — leave them `0`).
3. The answer is `dp[rows-1][cols-1]`.

**Template B — path cost.**
1. Set `dp[0][0] = grid[0][0]`. Fill the first row and first column by ACCUMULATING (`dp[0][c] = dp[0][c-1] + grid[0][c]`; `dp[r][0] = dp[r-1][0] + grid[r][0]`), since there is only one way to reach an edge cell.
2. For `r` from `1` to `rows-1`, for `c` from `1` to `cols-1`: `dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])` (or `max`, depending on the problem).
3. The answer is `dp[rows-1][cols-1]`.

**Why both templates are correct:** any path reaching cell `(r, c)` must have arrived from exactly one of two places — directly above, or directly to the left — since the only allowed moves are right and down. Template A sums the WAYS from each of those two places (every path is counted exactly once). Template B picks the CHEAPEST (or costliest) of the two incoming paths, then adds this cell's own cost, since a path's total cost is fixed once its route is fixed.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two grids side by side showing the sum transition for counting paths and the min transition for path cost">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Template A (count): dp[r][c] = dp[r-1][c] + dp[r][c-1]</text>
    <text x="10" y="45" font-weight="bold">Template B (cost): dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])</text>
    <rect x="10" y="65" width="300" height="24" fill="#3fb950"/><text x="160" y="82" fill="#0d1117" text-anchor="middle" font-size="10">same two neighbors, different combining rule (sum vs. min-plus-cost)</text>
  </g>
</svg>

Both templates read the same two neighbor cells; only the combining operation changes.

## 5. Runnable example

```java
// GridMatrixTemplate.java
public class GridMatrixTemplate {

    // Template A: count paths, with optional obstacles (1 = blocked).
    static int countPaths(int[][] obstacleGrid) {
        int rows = obstacleGrid.length, cols = obstacleGrid[0].length;
        int[][] dp = new int[rows][cols];
        for (int r = 0; r < rows && obstacleGrid[r][0] == 0; r++) dp[r][0] = 1;
        for (int c = 0; c < cols && obstacleGrid[0][c] == 0; c++) dp[0][c] = 1;

        for (int r = 1; r < rows; r++) {
            for (int c = 1; c < cols; c++) {
                if (obstacleGrid[r][c] == 1) continue; // stays 0
                dp[r][c] = dp[r - 1][c] + dp[r][c - 1];
            }
        }
        return dp[rows - 1][cols - 1];
    }

    // Template B: minimum path cost.
    static int minPathCost(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int[][] dp = new int[rows][cols];
        dp[0][0] = grid[0][0];
        for (int c = 1; c < cols; c++) dp[0][c] = dp[0][c - 1] + grid[0][c];
        for (int r = 1; r < rows; r++) dp[r][0] = dp[r - 1][0] + grid[r][0];

        for (int r = 1; r < rows; r++) {
            for (int c = 1; c < cols; c++) {
                dp[r][c] = grid[r][c] + Math.min(dp[r - 1][c], dp[r][c - 1]);
            }
        }
        return dp[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        System.out.println(countPaths(new int[][]{{0, 0, 0}, {0, 1, 0}, {0, 0, 0}}));
        // 2
        System.out.println(minPathCost(new int[][]{{1, 3, 1}, {1, 5, 1}, {4, 2, 1}}));
        // 7
    }
}
```

**How to run:** `java GridMatrixTemplate.java`

## 6. Walkthrough

1. `countPaths` fills a `3x3` grid where the center cell is an obstacle. Every cell it touches stays `0`, so no path through the center is ever counted.
2. Both remaining routes (all the way right then down, or all the way down then right) survive, giving `dp[2][2] = 2`.
3. `minPathCost` accumulates the first row (`1, 4, 5`) and first column (`1, 2, 6`) directly, then fills the interior: `dp[1][1] = 5 + min(4, 2) = 7`, `dp[1][2] = 1 + min(5, 7) = 6`, `dp[2][1] = 2 + min(7, 6) = 8`, `dp[2][2] = 1 + min(6, 8) = 7`.
4. The final answer `7` matches the path `1 -> 3 -> 1 -> 1 -> 1` down the middle-right route.
5. Both templates apply directly to Unique Paths, Unique Paths II, and Minimum Path Sum; Triangle and Minimum Falling Path Sum use a small variation reading from the row above instead.

## 7. Gotchas & takeaways

> Gotcha: in Template A, once an obstacle sets a cell to `0` and you `continue`, you must NOT overwrite it later — a `0`-count cell correctly propagates "no paths reach here" to every cell that depends on it.

- Template A sums two neighbors (counting); Template B takes the min or max of two neighbors plus the current cost (optimizing) — the same shape, a different combining rule.
- The first row and first column need SPECIAL handling in both templates, since they have only one incoming direction, not two.
- Triangle and Minimum Falling Path Sum read from the row ABOVE at up to three positions (same column, and one diagonal each side) instead of "top and left" — check the exact neighbor set before reusing this template blindly.
