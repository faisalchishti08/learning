---
card: leetcode-patterns
gi: 408
slug: triangle
title: Triangle
---

## 1. What it is

Given a triangle of numbers, find the minimum path sum from the top to the bottom row. At each step, you may move to an adjacent number in the row directly below (index `i` or index `i + 1`). Example: `triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]` → `11` (path `2 -> 3 -> 5 -> 1`).

## 2. Why & when

Use this shape whenever a problem gives you a TRIANGULAR grid instead of a rectangular one, with movement restricted to two adjacent cells in the row below. It is the same min-cost pattern as Minimum Path Sum, just working BOTTOM-UP instead of top-down, since bottom-up avoids needing a separate `min` over two DIFFERENT neighbor sets depending on direction.

## 3. Core concept

**Key idea:** work from the BOTTOM row upward. Let `dp[j]` = the minimum path sum from row `i`, position `j`, down to the triangle's bottom. Update it in place, one row at a time, moving up.

**Steps:**
1. Initialize `dp` as a copy of the triangle's LAST row (from the bottom, each single cell's minimum sum to the bottom is just itself).
2. For each row `i` from the second-to-last up to the top, for each position `j` in that row: `dp[j] = triangle[i][j] + min(dp[j], dp[j+1])` (using the still-OLD values of `dp[j]` and `dp[j+1]` from the row below, before this row overwrites them).
3. After processing the top row, `dp[0]` holds the answer.

**Why it is correct:** from any cell `(i, j)`, the best path downward either goes to `(i+1, j)` or `(i+1, j+1)` — both of whose best sums TO THE BOTTOM are already known, since the algorithm works bottom-up. Adding this cell's own value to the smaller of the two gives the true minimum sum from `(i, j)` all the way down.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="triangle collapsing upward, each cell adding its value to the smaller of the two cells below it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]</text>
    <text x="10" y="45">bottom row dp = [4,1,8,3]</text>
    <text x="10" y="65">row [6,5,7] -&gt; dp = [6+min(4,1), 5+min(1,8), 7+min(8,3)] = [7,6,10]</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp collapses upward until only dp[0] remains: 11</text>
  </g>
</svg>

Each row's minimum sums fold into a smaller row above it, until only one cell — the answer — remains.

## 5. Runnable example

```java
// Triangle.java
import java.util.*;

public class Triangle {

    // KEY INSIGHT: work bottom-up so both neighbors' best sums to the
    // bottom are already known -- no need for a separate top-down
    // "which direction did I come from" case split.

    static int minimumTotal(List<List<Integer>> triangle) {
        int n = triangle.size();
        int[] dp = new int[n + 1];
        for (int j = 0; j < n; j++) dp[j] = triangle.get(n - 1).get(j);

        for (int i = n - 2; i >= 0; i--) {
            for (int j = 0; j <= i; j++) {
                dp[j] = triangle.get(i).get(j) + Math.min(dp[j], dp[j + 1]);
            }
        }
        return dp[0];
    }

    public static void main(String[] args) {
        List<List<Integer>> triangle = new ArrayList<>();
        triangle.add(List.of(2));
        triangle.add(List.of(3, 4));
        triangle.add(List.of(6, 5, 7));
        triangle.add(List.of(4, 1, 8, 3));
        System.out.println(minimumTotal(triangle));
        // 11
    }
}
```

**How to run:** `java Triangle.java`

## 6. Walkthrough

Trace `minimumTotal` bottom-up, `dp` after each row:

| row processed | dp values |
|---|---|
| bottom `[4,1,8,3]` | [4, 1, 8, 3] |
| `[6,5,7]` | [7, 6, 10] |
| `[3,4]` | [9, 10] |
| `[2]` | [11] |

`dp[0] = 11`, matching the expected answer, via path `2 -> 3 -> 5 -> 1`. Time complexity is O(n^2) for a triangle with `n` rows (total cells across all rows). Space is O(n) with the rolling array shown above.

## 7. Gotchas & takeaways

> Gotcha: updating `dp[j]` for row `i` MUST use the OLD `dp[j]` and `dp[j+1]` values (from row `i+1`, still sitting in the array) — since the loop overwrites `dp[j]` in place, always read `dp[j]` and `dp[j+1]` BEFORE the assignment on that same iteration, never after.

- Bottom-up folding avoids the two-neighbor-set complication of a top-down approach, where each cell in the middle of a row can be reached from ONE of two different cells above it (not simply "left" and "up").
- The rolling 1D array works here specifically because processing `j` left to right on row `i` only reads `dp[j]` and `dp[j+1]`, both still holding row `i+1`'s values at the moment they are read.
- Related problems: Minimum Path Sum (the same min-cost idea over a rectangular grid), Minimum Falling Path Sum (a rectangular grid, but reading three neighbors instead of two, like a "double-wide" triangle transition).
