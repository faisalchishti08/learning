---
card: leetcode-patterns
gi: 407
slug: minimum-path-sum
title: Minimum Path Sum
---

## 1. What it is

Given an `m x n` grid filled with non-negative numbers, find a path from the top-left to the bottom-right corner that MINIMIZES the sum of all numbers along it. You may only move down or right. Example: `grid = [[1,3,1],[1,5,1],[4,2,1]]` → `7` (path `1 -> 3 -> 1 -> 1 -> 1`).

## 2. Why & when

Use this shape whenever a grid problem asks for the MINIMUM (or maximum) total cost of a single path, rather than a count of all paths. It is the direct cost-optimizing counterpart to Unique Paths.

## 3. Core concept

**Key idea:** build `dp[r][c]` = the minimum sum needed to reach `(r, c)` from the top-left corner, for every `r, c`.

**Steps:**
1. Set `dp[0][0] = grid[0][0]`.
2. Fill the first row by ACCUMULATING: `dp[0][c] = dp[0][c-1] + grid[0][c]` (only one way in: from the left). Fill the first column the same way: `dp[r][0] = dp[r-1][0] + grid[r][0]`.
3. For `r` from `1` to `m-1`, for `c` from `1` to `n-1`: `dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])`.
4. Return `dp[m-1][n-1]`.

**Why it is correct:** any path reaching `(r, c)` arrived either from above or from the left. Since the cost of the rest of the path (from the start up to that neighbor) is already the MINIMUM possible for that neighbor, picking the smaller of the two neighbor sums and adding this cell's own cost always produces the true minimum sum to reach `(r, c)`.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3 by 3 cost grid filled with running minimum sums, each cell adding its own cost to the smaller neighbor">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">grid = [[1,3,1], [1,5,1], [4,2,1]]</text>
    <text x="10" y="45">dp = [[1,4,5], [2,7,6], [6,8,7]]</text>
    <rect x="10" y="65" width="240" height="24" fill="#3fb950"/><text x="130" y="82" fill="#0d1117" text-anchor="middle" font-size="10">dp[2][2] = 1 + min(dp[1][2], dp[2][1]) = 1 + 6 = 7</text>
  </g>
</svg>

Each cell adds its own cost to the CHEAPER of the two possible ways to arrive.

## 5. Runnable example

```java
// MinimumPathSum.java
public class MinimumPathSum {

    // KEY INSIGHT: dp[r][c] = this cell's cost, plus the smaller of the
    // two already-minimal neighbor sums (from above or from the left).

    static int minPathSum(int[][] grid) {
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
        System.out.println(minPathSum(new int[][]{{1, 3, 1}, {1, 5, 1}, {4, 2, 1}}));
        // 7
        System.out.println(minPathSum(new int[][]{{1, 2, 3}, {4, 5, 6}}));
        // 12
    }
}
```

**How to run:** `java MinimumPathSum.java`

## 6. Walkthrough

Trace `minPathSum([[1,3,1],[1,5,1],[4,2,1]])`:

| row | dp row values |
|---|---|
| 0 | [1, 4, 5] |
| 1 | [2, 7, 6] |
| 2 | [6, 8, 7] |

`dp[2][2] = 1 + min(dp[1][2], dp[2][1]) = 1 + min(6, 8) = 7`, matching the expected answer. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: the first row and first column must be filled by ACCUMULATING costs (a running sum), not by copying `grid` values directly — there is exactly one way to reach any edge cell, so its minimum sum is simply "everything along that edge so far," never a `min` of two options.

- `dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])`: the min-cost analogue of Unique Paths' sum-of-counts transition.
- The values in `grid` are non-negative here, which guarantees a locally optimal choice at each cell also leads to a globally optimal path — this greedy-looking `min` step is only safe to trust because DP explores every cell, not just one route.
- Related problems: Unique Paths (the same shape, counting instead of optimizing), Triangle (a min-cost path shape over a triangular grid instead of a rectangle), Minimum Falling Path Sum (reads three neighbors from the row above instead of two).
