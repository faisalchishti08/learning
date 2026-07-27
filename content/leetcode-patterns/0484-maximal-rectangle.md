---
card: leetcode-patterns
gi: 484
slug: maximal-rectangle
title: Maximal Rectangle
---

## 1. What it is

Given a 2D binary matrix filled with `'0'` and `'1'`, find the area of the largest rectangle made up entirely of `'1'`s. Example: a 4×5 grid with a mix of `'0'`s and `'1'`s → `6` (a 2-row-by-3-column block of `'1'`s).

## 2. Why & when

Treat each row as the "ground" of a histogram: for every cell, its histogram height is how many consecutive `'1'`s stack up above it (including itself), reset to `0` at any `'0'`. Once you have that height array for a row, the largest all-`'1'` rectangle ending at that row is exactly the [Largest Rectangle in Histogram](0483-largest-rectangle-in-histogram.md) problem on those heights. Constraints: up to 200×200 grid.

## 3. Core concept

**Key idea:** build a running "heights" array, one row at a time. For row `r`, column `c`: if the cell is `'1'`, `heights[c] += 1` (extends the bar from the row above); if it is `'0'`, `heights[c] = 0` (the bar breaks). After updating `heights` for row `r`, run the histogram algorithm on it — the resulting largest-rectangle area is the best all-`'1'` rectangle whose bottom edge is row `r`. Track the maximum across all rows.

**Steps:**
1. Initialize `heights[]` of size `columns`, all zero.
2. For each row, top to bottom: update `heights[c]` for every column (add 1 for `'1'`, reset to 0 for `'0'`).
3. Run the O(columns) monotonic-stack histogram algorithm on the updated `heights` array.
4. Track the maximum area returned across all rows.
5. Return the overall maximum.

**Why reusing the histogram function is valid:** a rectangle of all `'1'`s with its bottom edge on row `r` is fully determined by, for each column, how many consecutive `'1'`s reach up to row `r` without a break — which is exactly what `heights[c]` measures at that point in the scan. The largest rectangle in that "skyline" is the best all-`'1'` rectangle bottoming out at row `r`.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each grid row turned into a histogram of consecutive ones stacked above it">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">grid rows, turned into running column heights</text>
    <text x="20" y="45" fill="#8b949e">row0: 1 0 1 0 0  -&gt; heights: [1,0,1,0,0]</text>
    <text x="20" y="65" fill="#8b949e">row1: 1 0 1 1 1  -&gt; heights: [2,0,2,1,1]</text>
    <text x="20" y="85" fill="#8b949e">row2: 1 1 1 1 1  -&gt; heights: [3,1,3,2,2]</text>
    <text x="20" y="105" fill="#8b949e">row3: 1 0 0 1 0  -&gt; heights: [4,0,0,3,0]</text>
    <text x="20" y="135" fill="#79c0ff">row2's heights [3,1,3,2,2] fed into the histogram algorithm</text>
    <text x="20" y="155" fill="#3fb950">gives the largest all-1s rectangle bottoming at row2: area 6 (columns 2-4, 2 rows tall, or similar)</text>
  </g>
</svg>

Each row's running heights array becomes a histogram; the biggest rectangle across all rows is the answer.

## 5. Runnable example

**Level 1 — Brute force.** For every pair of top-left and bottom-right corners, check whether the enclosed rectangle is all `'1'`s. O(rows² · columns² · rows · columns) in the worst case — extremely slow.

**KEY INSIGHT:** turning each row into a histogram of "consecutive ones above this cell" reduces the whole 2D problem to running the already-solved 1D [Largest Rectangle in Histogram](0483-largest-rectangle-in-histogram.md) once per row.

**Level 2 — Optimal.** Running heights array + histogram algorithm per row, O(rows × columns).

**Level 3 — Hardened.** Handles an all-`'0'` grid (answer `0`) and a single row or single column.

```java
// MaximalRectangle.java
import java.util.*;

public class MaximalRectangle {

    // Reused from Largest Rectangle in Histogram
    static int largestRectangleArea(int[] heights) {
        Deque<Integer> stack = new ArrayDeque<>();
        int maxArea = 0;
        int n = heights.length;
        for (int i = 0; i <= n; i++) {
            int currentHeight = (i == n) ? 0 : heights[i];
            while (!stack.isEmpty() && heights[stack.peek()] > currentHeight) {
                int height = heights[stack.pop()];
                int leftBoundary = stack.isEmpty() ? -1 : stack.peek();
                int width = i - leftBoundary - 1;
                maxArea = Math.max(maxArea, height * width);
            }
            stack.push(i);
        }
        return maxArea;
    }

    // Level 2 & 3: running heights per row + histogram, O(rows * columns)
    static int maximalRectangle(char[][] matrix) {
        if (matrix.length == 0 || matrix[0].length == 0) return 0;
        int columns = matrix[0].length;
        int[] heights = new int[columns];
        int maxArea = 0;

        for (char[] row : matrix) {
            for (int c = 0; c < columns; c++) {
                heights[c] = (row[c] == '1') ? heights[c] + 1 : 0;
            }
            maxArea = Math.max(maxArea, largestRectangleArea(heights));
        }
        return maxArea;
    }

    public static void main(String[] args) {
        char[][] grid = {
            {'1', '0', '1', '0', '0'},
            {'1', '0', '1', '1', '1'},
            {'1', '1', '1', '1', '1'},
            {'1', '0', '0', '1', '0'}
        };
        System.out.println("optimal: " + maximalRectangle(grid));

        char[][] allZeros = {{'0', '0'}, {'0', '0'}};
        System.out.println("all zeros: " + maximalRectangle(allZeros));

        char[][] single = {{'1'}};
        System.out.println("single cell: " + maximalRectangle(single));
    }
}
```

**How to run:** save as `MaximalRectangle.java`, then run `java MaximalRectangle.java`.

## 6. Walkthrough

For the sample grid, the running `heights` array evolves row by row:

| row | grid row | heights after update | histogram result for this row |
|---|---|---|---|
| 0 | 1 0 1 0 0 | [1, 0, 1, 0, 0] | 1 |
| 1 | 1 0 1 1 1 | [2, 0, 2, 1, 1] | 3 (columns 2-4, height >= 1, width 3) |
| 2 | 1 1 1 1 1 | [3, 1, 3, 2, 2] | 6 (columns 2-4, height >= 2, width 3, area 6) |
| 3 | 1 0 0 1 0 | [4, 0, 0, 3, 0] | 4 |

The maximum across all rows is `6`, reached at row 2, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting to reset `heights[c]` to `0` on a `'0'` cell (instead of just not incrementing it) keeps stale height data from rows above a break, producing a rectangle that is not actually all `'1'`s.

- This problem is exactly [Largest Rectangle in Histogram](0483-largest-rectangle-in-histogram.md), run once per row on a running "consecutive ones" heights array.
- Reuse the histogram function unchanged — the only new work is building and updating `heights` row by row.
- Time: O(rows × columns) — each row does O(columns) work to update heights, plus one O(columns) histogram pass.
