---
card: leetcode-patterns
gi: 411
slug: count-square-submatrices-with-all-ones
title: Count Square Submatrices with All Ones
---

## 1. What it is

Given a matrix of `0`s and `1`s, count the total number of square SUBMATRICES that contain only `1`s (squares of every possible size, not just the largest one). Example: `matrix = [[0,1,1,1],[1,1,1,1],[0,1,1,1]]` → `15`.

## 2. Why & when

Use this shape whenever a problem asks you to COUNT every square sub-region of `1`s, not just find the single LARGEST one. It reuses the exact same `dp[r][c]` transition as Maximal Square, but changes what you do with the results: sum them all, instead of tracking only the maximum.

## 3. Core concept

**Key idea:** build the same `dp[r][c]` = the SIDE LENGTH of the largest square of `1`s ending at `(r, c)`, as in Maximal Square. Then SUM every `dp[r][c]` value across the whole grid.

**Steps:**
1. If `matrix[r][c]` is `0`, `dp[r][c] = 0`.
2. If `(r, c)` is on the first row or first column and `matrix[r][c]` is `1`, `dp[r][c] = 1`.
3. Otherwise, `dp[r][c] = 1 + min(dp[r-1][c], dp[r][c-1], dp[r-1][c-1])`.
4. The answer is the SUM of every `dp[r][c]` in the grid.

**Why summing works:** `dp[r][c] = k` means there are exactly `k` DISTINCT squares of `1`s ending at `(r, c)` — one of side `1`, one of side `2`, ..., up to one of side `k` (every smaller square nested inside the largest one ending at that same corner is also entirely `1`s, since the largest one is). Summing `dp[r][c]` over every cell therefore counts every square of every size, with no double-counting, since each square has exactly ONE bottom-right corner.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a dp value of 3 at one cell representing three nested squares of side 1 2 and 3 all ending at that same corner">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[r][c] = 3 means 3 distinct squares end here: side 1, side 2, side 3</text>
    <rect x="10" y="35" width="90" height="90" fill="none" stroke="#3fb950" stroke-width="2"/>
    <rect x="40" y="65" width="60" height="60" fill="none" stroke="#58a6ff" stroke-width="2"/>
    <rect x="70" y="95" width="30" height="30" fill="none" stroke="#f0883e" stroke-width="2"/>
    <text x="110" y="105" font-size="10">3 nested squares, same bottom-right corner</text>
  </g>
</svg>

Every value of `dp[r][c]` counts that many distinct squares, all sharing the same bottom-right corner.

## 5. Runnable example

```java
// CountSquareSubmatricesWithAllOnes.java
public class CountSquareSubmatricesWithAllOnes {

    // KEY INSIGHT: dp[r][c] = k means k nested squares (sides 1..k) all
    // end at (r,c) -- summing dp over the grid counts every square,
    // of every size, exactly once each.

    static int countSquares(int[][] matrix) {
        int rows = matrix.length, cols = matrix[0].length;
        int[][] dp = new int[rows][cols];
        int total = 0;

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (matrix[r][c] == 0) {
                    dp[r][c] = 0;
                } else if (r == 0 || c == 0) {
                    dp[r][c] = 1;
                } else {
                    dp[r][c] = 1 + Math.min(dp[r - 1][c], Math.min(dp[r][c - 1], dp[r - 1][c - 1]));
                }
                total += dp[r][c];
            }
        }
        return total;
    }

    public static void main(String[] args) {
        int[][] matrix = {
            {0, 1, 1, 1},
            {1, 1, 1, 1},
            {0, 1, 1, 1}
        };
        System.out.println(countSquares(matrix));
        // 15
    }
}
```

**How to run:** `java CountSquareSubmatricesWithAllOnes.java`

## 6. Walkthrough

Trace `dp` for the example matrix (row by row):

| row | dp row values | row sum |
|---|---|---|
| 0 | [0, 1, 1, 1] | 3 |
| 1 | [1, 1, 2, 2] | 6 |
| 2 | [0, 1, 2, 3] | 6 |

Total `= 3 + 6 + 6 = 15`, matching the expected answer. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: reusing Maximal Square's code but forgetting to change "track the max" into "sum everything" silently answers the WRONG question — the two problems share an identical `dp` table, but need a completely different final reduction over it.

- Same transition as Maximal Square (`dp[r][c] = 1 + min(top, left, diagonal)`); different final step (sum vs. max).
- The insight that `dp[r][c] = k` represents exactly `k` nested squares (not just "the biggest one has side `k`") is what justifies summing rather than something more complex like combinatorics on `k`.
- Related problems: Maximal Square (identical `dp` table, asks for the largest square's area instead of a total count).
