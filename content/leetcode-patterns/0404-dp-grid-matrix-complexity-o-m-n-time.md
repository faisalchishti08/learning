---
card: leetcode-patterns
gi: 404
slug: dp-grid-matrix-complexity-o-m-n-time
title: "DP: Grid / Matrix — complexity: O(m*n) time"
---

## 1. What it is

This page states and justifies the complexity of grid-DP problems, and lists the problems that use this pattern, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. Grid dimensions in these problems are usually bounded by around `200 x 200`, so an O(m·n) pass (at most `40,000` cells) comfortably fits typical time limits, and there is rarely a need to look for anything asymptotically faster.

## 3. Core concept

**Time complexity: O(m · n).** Every grid-DP template visits each of the `m x n` cells exactly once, doing a constant amount of work per cell (reading two or three neighbor values, combining them, writing the result).

**Space complexity: O(m · n)** for a full 2D `dp` array, but this REDUCES to O(n) (or O(m), whichever is smaller) with a ROLLING array, since a cell's value only ever depends on the row directly above it (or, for triangle problems, the row directly below).

**Why the rolling-array reduction is valid:** once row `r` is fully computed, row `r-2` and everything above it is never read again — only row `r-1` matters for computing row `r`. Reusing a single 1D array (updating it in place, or with two alternating arrays) drops the memory footprint from `O(m·n)` to `O(n)` without changing the answer.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="full grid versus a single rolling row that gets overwritten as the algorithm moves down the grid">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">full dp grid: O(m*n) space -- every row kept</text>
    <text x="10" y="45" font-weight="bold">rolling 1D array: O(n) space -- only the row above is kept</text>
    <rect x="10" y="65" width="300" height="24" fill="#3fb950"/><text x="160" y="82" fill="#0d1117" text-anchor="middle" font-size="10">each row only ever reads the row directly above it</text>
  </g>
</svg>

Only the most recent row is ever needed, so older rows can be safely discarded or overwritten.

## 5. Runnable example

```java
// GridMatrixComplexity.java
public class GridMatrixComplexity {

    // Confirms O(m*n): counts exactly one operation per cell.
    static int minPathCostCountingOps(int[][] grid, long[] ops) {
        int rows = grid.length, cols = grid[0].length;
        int[][] dp = new int[rows][cols];
        dp[0][0] = grid[0][0];
        ops[0]++;
        for (int c = 1; c < cols; c++) {
            dp[0][c] = dp[0][c - 1] + grid[0][c];
            ops[0]++;
        }
        for (int r = 1; r < rows; r++) {
            dp[r][0] = dp[r - 1][0] + grid[r][0];
            ops[0]++;
            for (int c = 1; c < cols; c++) {
                dp[r][c] = grid[r][c] + Math.min(dp[r - 1][c], dp[r][c - 1]);
                ops[0]++;
            }
        }
        return dp[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        int[][] grid = {{1, 3, 1}, {1, 5, 1}, {4, 2, 1}};
        long[] ops = {0};
        int result = minPathCostCountingOps(grid, ops);
        System.out.println("result=" + result + " ops=" + ops[0]);
        // ops == 9, exactly rows * cols == 3 * 3
    }
}
```

**How to run:** `java GridMatrixComplexity.java`

## 6. Walkthrough

1. `minPathCostCountingOps` runs the standard path-cost template while counting every cell visited in `ops`.
2. For a `3x3` grid, the printed `ops` count is exactly `9`, confirming one constant-time operation per cell, matching `rows * cols`.
3. No cell is ever visited twice, and no cell does more than a fixed amount of work (two comparisons and an addition, at most), which is what makes the bound O(m·n) rather than something larger.
4. If this grid were doubled to `6x6`, `ops` would grow to `36` — exactly four times as many, confirming the bound scales with the PRODUCT of the dimensions, not their sum.
5. Swapping the full `dp[][]` array for a single rolling row of length `cols` would not change `ops` at all, only the memory used to hold the answer along the way.

## 7. Gotchas & takeaways

> Gotcha: reducing space to O(n) with a rolling array is only safe once you have confirmed the transition reads ONLY from the row directly above (or, for triangles, directly below) — a transition that reads two rows back (rare, but possible in some variants) needs two alternating arrays, not one.

- Time: O(m·n) for every problem in this section; space: O(m·n) naively, reducible to O(n) with a rolling array.
- The O(m·n) bound is tight — every cell must be visited at least once, since each one can be the corner of a different valid path.
- Problems that use this pattern: Unique Paths, Unique Paths II, Minimum Path Sum, Triangle, Maximal Square, Minimum Falling Path Sum, Count Square Submatrices with All Ones, Where Will the Ball Fall, Out of Boundary Paths.
