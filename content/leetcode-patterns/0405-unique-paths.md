---
card: leetcode-patterns
gi: 405
slug: unique-paths
title: Unique Paths
---

## 1. What it is

A robot sits at the top-left corner of an `m x n` grid. It can only move DOWN or RIGHT at each step. Return the number of unique paths to reach the bottom-right corner. Example: `m = 3, n = 7` → `28`.

## 2. Why & when

This is the textbook grid-DP counting problem, the exact pattern this section is named after. Use this shape whenever you need to count paths across a grid where movement is restricted to two directions and there are no obstacles.

## 3. Core concept

**Key idea:** build `dp[r][c]` = the number of ways to reach cell `(r, c)` from the top-left corner, for every `r, c`.

**Steps:**
1. Set `dp[r][0] = 1` for every row (only one way along the left edge: keep moving down) and `dp[0][c] = 1` for every column (only one way along the top edge: keep moving right).
2. For `r` from `1` to `m-1`, for `c` from `1` to `n-1`: `dp[r][c] = dp[r-1][c] + dp[r][c-1]`.
3. Return `dp[m-1][n-1]`.

**Why it is correct:** any path reaching `(r, c)` must have taken its LAST step either from directly above (`(r-1, c)`, moving down) or directly to the left (`(r, c-1)`, moving right) — there are no other options. Summing the path counts from both gives every distinct path exactly once, since the two cases never overlap.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3 by 3 grid filled with path counts, each cell the sum of the cell above and the cell to its left">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">grid, 3 rows x 3 cols</text>
    <text x="10" y="45">dp = [[1,1,1], [1,2,3], [1,3,6]]</text>
    <rect x="10" y="65" width="240" height="24" fill="#3fb950"/><text x="130" y="82" fill="#0d1117" text-anchor="middle" font-size="10">dp[2][2] = dp[1][2] + dp[2][1] = 3 + 3 = 6</text>
  </g>
</svg>

Every cell's count is the sum of the ways to reach it from above and from the left.

## 5. Runnable example

```java
// UniquePaths.java
public class UniquePaths {

    // KEY INSIGHT: the last step into (r, c) came from either directly
    // above or directly to the left -- sum both counts.

    static int uniquePaths(int m, int n) {
        int[][] dp = new int[m][n];
        for (int r = 0; r < m; r++) dp[r][0] = 1;
        for (int c = 0; c < n; c++) dp[0][c] = 1;

        for (int r = 1; r < m; r++) {
            for (int c = 1; c < n; c++) {
                dp[r][c] = dp[r - 1][c] + dp[r][c - 1];
            }
        }
        return dp[m - 1][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(uniquePaths(3, 7));
        // 28
        System.out.println(uniquePaths(3, 3));
        // 6
    }
}
```

**How to run:** `java UniquePaths.java`

## 6. Walkthrough

Trace `uniquePaths(3, 3)`:

| row | dp row values |
|---|---|
| 0 | [1, 1, 1] |
| 1 | [1, 2, 3] |
| 2 | [1, 3, 6] |

`dp[2][2] = 6`, matching the expected answer. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: the answer grows FAST — for larger `m` and `n`, `dp[m-1][n-1]` can exceed the range of a 32-bit `int` in problems with bigger constraints. LeetCode's own constraints keep this specific problem safe, but always check the bounds before reusing this code elsewhere.

- `dp[r][c] = dp[r-1][c] + dp[r][c-1]`, with the first row and column both set to `1`: the exact template every other counting problem in this section builds from.
- This is a special case of the combinatorial formula `C(m+n-2, m-1)` (choosing which `m-1` of the `m+n-2` total moves are "down") — the DP table is usually simpler and safer to write correctly than the combinatorics formula.
- Related problems: Unique Paths II (adds obstacles that block certain cells), Minimum Path Sum (same shape, but optimizing a cost instead of counting paths).
