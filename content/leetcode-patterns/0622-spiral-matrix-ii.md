---
card: leetcode-patterns
gi: 622
slug: spiral-matrix-ii
title: Spiral Matrix II
---

## 1. What it is

Given an integer `n`, generate an `n x n` matrix filled with the numbers `1` to `n^2`, placed in spiral order (starting at the top-left, moving right, then down, then left, then up, spiraling inward). Example: `n=3` → `[[1,2,3],[8,9,4],[7,6,5]]`.

## 2. Why & when

This is [Spiral Matrix](0611-spiral-matrix.md) run in reverse: instead of *reading* a matrix's elements in spiral order, this problem *writes* sequential numbers into a matrix following that same spiral path. The identical four-shrinking-boundary technique applies, just replacing "append this cell's value to the output" with "write the next sequential number into this cell."

## 3. Core concept

**Key idea:** maintain the same four boundary variables — `top`, `bottom`, `left`, `right` — as in the read version. Instead of reading `matrix[i][j]` into a result list, write an increasing counter (`1, 2, 3, ...`) into `matrix[i][j]` while walking the same spiral path: top row left-to-right, right column top-to-bottom, bottom row right-to-left, left column bottom-to-top, shrinking each boundary inward after its walk.

**Steps:**
1. Create an `n x n` matrix. Initialize `top=0, bottom=n-1, left=0, right=n-1`, and `num=1`.
2. While `top <= bottom` and `left <= right`:
3. Fill row `top` from `left` to `right` with `num, num+1, ...`, incrementing `num` after each write; then increment `top`.
4. Fill column `right` from `top` to `bottom` similarly; then decrement `right`.
5. If `top <= bottom` still holds, fill row `bottom` from `right` to `left`; then decrement `bottom`.
6. If `left <= right` still holds, fill column `left` from `bottom` to `top`; then increment `left`.

**Why this is a strict structural mirror of Spiral Matrix's reading algorithm:** both problems share the exact same geometric path definition (the spiral order itself) and the exact same shrinking-boundary bookkeeping to trace that path without a separate visited-cells structure. The only difference is the single line inside each directional walk: reading appends `matrix[i][j]` to an output list, while writing assigns `matrix[i][j] = num++` — everything else, including the boundary re-check logic before the third and fourth walks of each ring, is identical.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Filling a 3x3 matrix in spiral order with numbers 1 through 9">
  <g font-family="sans-serif" font-size="13">
    <rect x="250" y="20" width="180" height="150" fill="none" stroke="#30363d"/>
    <text x="290" y="55" fill="#3fb950">1</text><text x="335" y="55" fill="#3fb950">2</text><text x="380" y="55" fill="#3fb950">3</text>
    <text x="290" y="100" fill="#e6edf3">8</text><text x="335" y="100" fill="#e6edf3">9</text><text x="380" y="100" fill="#f0883e">4</text>
    <text x="290" y="145" fill="#79c0ff">7</text><text x="335" y="145" fill="#79c0ff">6</text><text x="380" y="145" fill="#79c0ff">5</text>
    <text x="340" y="185" fill="#8b949e" text-anchor="middle" font-size="11">1,2,3 (top row) -&gt; 4,5 (right+bottom col/row) -&gt; 6,7 (bottom/left) -&gt; 8 (left col) -&gt; 9 (center)</text>
  </g>
</svg>

The identical spiral path from Spiral Matrix is retraced here, but each visited cell receives the next sequential number instead of contributing a value to an output list.

## 5. Runnable example

**Level 1 — Brute force.** Simulate a "turtle" moving one cell at a time in a fixed direction, turning when the next cell is out of bounds or already filled, using a separate visited-check (like testing if the cell already holds a nonzero value). Correct, and reasonably simple, but the boundary-based approach below avoids per-cell out-of-bounds/visited checks entirely.

**KEY INSIGHT:** the same four shrinking boundaries used to *read* a matrix in spiral order can be reused unchanged to *write* one — the geometric path is identical in both directions; only what happens at each visited cell differs.

**Level 2 — Optimal.** Four boundary variables, filled in the fixed top-row/right-column/bottom-row/left-column order, O(n^2) time (every cell written exactly once), O(1) extra space (beyond the output matrix).

**Level 3 — Hardened.** Correctly re-checks `top <= bottom` and `left <= right` before the bottom-row and left-column fills, exactly as in the reading version, to avoid re-filling an already-completed row or column on matrices that collapse to a single row or column mid-spiral.

```java
// SpiralMatrixII.java
import java.util.*;

public class SpiralMatrixII {

    public static int[][] generateMatrix(int n) {
        int[][] matrix = new int[n][n];
        int top = 0, bottom = n - 1, left = 0, right = n - 1;
        int num = 1;

        while (top <= bottom && left <= right) {
            for (int col = left; col <= right; col++) matrix[top][col] = num++;
            top++;

            for (int row = top; row <= bottom; row++) matrix[row][right] = num++;
            right--;

            if (top <= bottom) {
                for (int col = right; col >= left; col--) matrix[bottom][col] = num++;
                bottom--;
            }

            if (left <= right) {
                for (int row = bottom; row >= top; row--) matrix[row][left] = num++;
                left++;
            }
        }

        return matrix;
    }

    public static void main(String[] args) {
        int[][] matrix = generateMatrix(3);
        for (int[] row : matrix) System.out.println(Arrays.toString(row));
        // [1, 2, 3]
        // [8, 9, 4]
        // [7, 6, 5]
    }
}
```

**How to run:** save as `SpiralMatrixII.java`, then run `java SpiralMatrixII.java`.

## 6. Walkthrough

Trace the first ring of `generateMatrix(3)`, boundaries start `top=0,bottom=2,left=0,right=2`, `num=1`:

1. Top row (`col` 0 to 2, row 0): write `1,2,3`. `num=4`. `top` becomes `1`.
2. Right column (`row` 1 to 2, col 2): write `4,5`. `num=6`. `right` becomes `1`.
3. Check `top(1) <= bottom(2)`: true. Bottom row (`col` 1 down to 0, row 2): write `6,7`. `num=8`. `bottom` becomes `1`.
4. Check `left(0) <= right(1)`: true. Left column (`row` 1 down to 1, col 0): write `8`. `num=9`. `left` becomes `1`.
5. Loop condition `top(1)<=bottom(1)` and `left(1)<=right(1)`: true. Top row (`col` 1 to 1, row 1): write `9`. `num=10`. `top` becomes `2`.
6. Loop condition `top(2)<=bottom(1)`: false, loop ends.

Final matrix: `[[1,2,3],[8,9,4],[7,6,5]]`, matching the expected spiral fill.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `if (top <= bottom)` and `if (left <= right)` guards before the bottom-row and left-column fills causes a single-row or single-column matrix's cells to be overwritten a second time with incorrect (too-large) numbers, since the first two unconditional walks (top row, right column) may have already covered every cell in a degenerate case.

- Signal: "fill/traverse a grid following a specific geometric path" reuses the same boundary-tracking technique regardless of whether the operation is reading or writing.
- The exact same four-step order (top row, right column, bottom row, left column) and the same boundary re-checks apply — only the per-cell operation changes between reading and writing.
- Related problems: Spiral Matrix (the read version of this exact same boundary-tracking technique).
