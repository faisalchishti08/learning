---
card: leetcode-patterns
gi: 410
slug: minimum-falling-path-sum
title: Minimum Falling Path Sum
---

## 1. What it is

Given an `n x n` matrix, find the minimum sum of any "falling path" from the first row to the last. A falling path starts anywhere in the first row, and at each step moves to the cell directly below, or diagonally down-left, or diagonally down-right, in the next row. Example: `matrix = [[2,1,3],[6,5,4],[7,8,9]]` → `13` (path `1 -> 5 -> 7`).

## 2. Why & when

Use this shape whenever a grid problem allows movement into THREE cells in the row below (straight down, and both diagonals), and the path may START anywhere along the top row rather than at a fixed corner. It is closely related to Triangle, but on a full rectangular grid instead of a triangular one.

## 3. Core concept

**Key idea:** build `dp[r][c]` = the minimum sum of a falling path that ENDS exactly at `(r, c)`.

**Steps:**
1. Set `dp[0][c] = matrix[0][c]` for every column (a path can start at any cell in the first row, with no cost yet incurred).
2. For `r` from `1` to `n-1`, for `c` from `0` to `n-1`: `dp[r][c] = matrix[r][c] + min(dp[r-1][c], dp[r-1][c-1], dp[r-1][c+1])`, treating any out-of-bounds diagonal as `+infinity` (unreachable).
3. Return the MINIMUM value across the entire last row.

**Why it is correct:** any falling path arriving at `(r, c)` took its last step from one of exactly three cells in row `r-1`: directly above, or one of the two diagonals. Picking the smallest of those three (already the best possible sum to reach that neighbor) and adding this cell's own value gives the true minimum sum to reach `(r, c)`. Since the path may end at ANY column in the last row, the overall answer is the minimum over the whole final row, not just one fixed cell.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="cell r c reading three neighbors from the row above straight up and both diagonals">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[r][c] = matrix[r][c] + min(up-left, up, up-right)</text>
    <rect x="110" y="40" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="135" y="58" text-anchor="middle" font-size="10">up-left</text>
    <rect x="170" y="40" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="195" y="58" text-anchor="middle" font-size="10">up</text>
    <rect x="230" y="40" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="255" y="58" text-anchor="middle" font-size="10">up-right</text>
    <rect x="170" y="80" width="50" height="26" fill="#3fb950"/><text x="195" y="98" text-anchor="middle" font-size="10" fill="#0d1117">r,c</text>
    <rect x="10" y="120" width="320" height="24" fill="#3fb950"/><text x="170" y="137" fill="#0d1117" text-anchor="middle" font-size="10">answer = minimum value across the WHOLE final row</text>
  </g>
</svg>

Each cell reads three cells from the row above; the answer is the smallest value in the finished last row.

## 5. Runnable example

```java
// MinimumFallingPathSum.java
public class MinimumFallingPathSum {

    // KEY INSIGHT: three incoming directions (not two), and the path
    // can both START and END anywhere along its respective row.

    static int minFallingPathSum(int[][] matrix) {
        int n = matrix.length;
        int[][] dp = new int[n][n];
        for (int c = 0; c < n; c++) dp[0][c] = matrix[0][c];

        for (int r = 1; r < n; r++) {
            for (int c = 0; c < n; c++) {
                int best = dp[r - 1][c];
                if (c > 0) best = Math.min(best, dp[r - 1][c - 1]);
                if (c < n - 1) best = Math.min(best, dp[r - 1][c + 1]);
                dp[r][c] = matrix[r][c] + best;
            }
        }

        int answer = Integer.MAX_VALUE;
        for (int c = 0; c < n; c++) answer = Math.min(answer, dp[n - 1][c]);
        return answer;
    }

    public static void main(String[] args) {
        System.out.println(minFallingPathSum(new int[][]{{2, 1, 3}, {6, 5, 4}, {7, 8, 9}}));
        // 13
    }
}
```

**How to run:** `java MinimumFallingPathSum.java`

## 6. Walkthrough

Trace `minFallingPathSum([[2,1,3],[6,5,4],[7,8,9]])`:

| row | dp row values |
|---|---|
| 0 | [2, 1, 3] |
| 1 | [6+1, 5+1, 4+1] = [7, 6, 5] |
| 2 | [7+6, 8+6, 9+5] = [13, 14, 14] |

Minimum of row 2 is `13`, matching the expected answer, via path `1 (col 1) -> 5 (col 1) -> 7 (col 0)`. Time complexity is O(n^2). Space is O(n^2) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: the two diagonal neighbors need BOUNDS CHECKS (`c > 0` and `c < n - 1`) — forgetting them causes an `ArrayIndexOutOfBoundsException` at the grid's edges, since the leftmost column has no up-left diagonal and the rightmost column has no up-right diagonal.

- `dp[r][c] = matrix[r][c] + min(three neighbors above)`, answer = min of the WHOLE last row: the three-neighbor, any-start/any-end variant of the grid-DP shape.
- This differs from Triangle only in shape (rectangular vs. triangular) and neighbor count (three vs. two) — the underlying "read the row above, take the smallest option" idea is identical.
- Related problems: Triangle (two neighbors, triangular shape), Minimum Path Sum (two neighbors, fixed start and end corners), Out of Boundary Paths (a grid-traversal DP that instead counts ways to LEAVE the grid within a move budget).
