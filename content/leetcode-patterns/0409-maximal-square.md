---
card: leetcode-patterns
gi: 409
slug: maximal-square
title: Maximal Square
---

## 1. What it is

Given a 2D binary matrix filled with `0`s and `1`s, find the largest SQUARE containing only `1`s, and return its area. Example: `matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]]` → `4` (a 2-by-2 square of `1`s).

## 2. Why & when

Use this shape whenever a grid problem asks for the largest SQUARE (or, closely related, wants to COUNT square sub-regions) made entirely of a target value. Unlike path problems, the transition here reads THREE neighbors, not two, because a square's size is limited by all three directions at once.

## 3. Core concept

**Key idea:** build `dp[r][c]` = the SIDE LENGTH of the largest square of `1`s whose BOTTOM-RIGHT corner is exactly `(r, c)`.

**Steps:**
1. If `matrix[r][c]` is `'0'`, then `dp[r][c] = 0` (no square of `1`s can end here).
2. If `(r, c)` is in the first row or first column and `matrix[r][c]` is `'1'`, then `dp[r][c] = 1` (a single cell is itself a valid 1-by-1 square).
3. Otherwise, `dp[r][c] = 1 + min(dp[r-1][c], dp[r][c-1], dp[r-1][c-1])`.
4. Track the MAXIMUM `dp[r][c]` seen across the whole grid; the answer is that maximum, SQUARED (side length to area).

**Why it is correct:** a square of side `s` ending at `(r, c)` requires the cell directly above, the cell directly to the left, AND the cell diagonally above-left to ALL support at least a square of side `s - 1` — if any one of those three is smaller, the square ending at `(r, c)` is limited by the SMALLEST of the three, plus the one row/column that `(r, c)` itself adds.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="cell r c reading three neighbors top left and top left diagonal to determine the largest square ending there">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[r][c] = 1 + min(top, left, top-left diagonal)</text>
    <rect x="120" y="40" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="145" y="58" text-anchor="middle" font-size="10">diag</text>
    <rect x="180" y="40" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="205" y="58" text-anchor="middle" font-size="10">top</text>
    <rect x="120" y="76" width="50" height="26" fill="#30363d" stroke="#8b949e"/><text x="145" y="94" text-anchor="middle" font-size="10">left</text>
    <rect x="180" y="76" width="50" height="26" fill="#3fb950"/><text x="205" y="94" text-anchor="middle" font-size="10" fill="#0d1117">r,c</text>
    <rect x="10" y="115" width="300" height="24" fill="#3fb950"/><text x="160" y="132" fill="#0d1117" text-anchor="middle" font-size="10">square size limited by the SMALLEST of the three neighbors</text>
  </g>
</svg>

The square growing into a cell is only as big as the smallest of the three squares feeding it.

## 5. Runnable example

```java
// MaximalSquare.java
public class MaximalSquare {

    // KEY INSIGHT: a square of side s ending at (r,c) needs all three
    // neighbors (top, left, top-left) to already support side s-1 --
    // the weakest of the three caps the size.

    static int maximalSquare(char[][] matrix) {
        int rows = matrix.length, cols = matrix[0].length;
        int[][] dp = new int[rows][cols];
        int maxSide = 0;

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (matrix[r][c] == '0') {
                    dp[r][c] = 0;
                } else if (r == 0 || c == 0) {
                    dp[r][c] = 1;
                } else {
                    dp[r][c] = 1 + Math.min(dp[r - 1][c], Math.min(dp[r][c - 1], dp[r - 1][c - 1]));
                }
                maxSide = Math.max(maxSide, dp[r][c]);
            }
        }
        return maxSide * maxSide;
    }

    public static void main(String[] args) {
        char[][] matrix = {
            {'1', '0', '1', '0', '0'},
            {'1', '0', '1', '1', '1'},
            {'1', '1', '1', '1', '1'},
            {'1', '0', '0', '1', '0'}
        };
        System.out.println(maximalSquare(matrix));
        // 4
    }
}
```

**How to run:** `java MaximalSquare.java`

## 6. Walkthrough

Trace key cells for the example matrix (`dp[r][c]`, side length):

| r,c | matrix value | neighbors (top, left, diag) | dp[r][c] |
|---|---|---|---|
| 1,2 | '1' | (dp[0][2]=1, dp[1][1]=0, dp[0][1]=0) | 1 |
| 2,3 | '1' | (dp[1][3]=1, dp[2][2]=1, dp[1][2]=1) | 2 |
| 2,4 | '1' | (dp[1][4]=1, dp[2][3]=2, dp[1][3]=1) | 2 |

The largest `dp` value reached is `2` (at `(2,3)` or `(2,4)`), so the answer is `2^2 = 4`. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: the final answer is the AREA (`maxSide * maxSide`), not the side length itself — returning `maxSide` directly is a common off-by-transformation mistake, since the problem asks for area, not side.

- `dp[r][c] = 1 + min(top, left, diagonal)` on a `'1'`, else `0`: the three-neighbor extension of the two-neighbor path templates earlier in this section.
- The diagonal neighbor (`dp[r-1][c-1]`) is the detail that makes this a SQUARE-growing problem rather than a path problem — omitting it (using only top and left) would compute something else entirely, not a valid square side length.
- Related problems: Count Square Submatrices with All Ones (the exact same `dp[r][c]` transition, but SUMS every `dp` value instead of tracking only the maximum).
