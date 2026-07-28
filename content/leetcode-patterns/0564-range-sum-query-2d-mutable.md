---
card: leetcode-patterns
gi: 564
slug: range-sum-query-2d-mutable
title: Range Sum Query 2D - Mutable
---

## 1. What it is

Like [Range Sum Query - Mutable](0563-range-sum-query-mutable.md), but on a 2D matrix: `update(row, col, value)` changes one cell, and `sumRegion(row1, col1, row2, col2)` returns the sum of the rectangular region between those two corners, inclusive. Both operations are called repeatedly, in any order.

## 2. Why & when

The 1D Fenwick tree extends naturally to 2D: instead of a single array of partial sums, use a 2D array of partial sums, where each cell's update or query walks two nested "lowest set bit" loops instead of one. Constraints: up to 200x200 matrix, up to 10,000 calls.

## 3. Core concept

**Key idea:** a 2D Fenwick tree is an `n x m` grid, where `tree[i][j]` accumulates a partial sum over a 2D rectangle determined by both `i`'s and `j`'s lowest set bits. Updating a cell walks the outer loop over rows (by row's lowest set bit) and, for each row step, an inner loop over columns (by column's lowest set bit) — touching `O(log n * log m)` cells total. A prefix-sum query to `(row, col)` does the same nested walk in reverse.

**Steps:**
1. Store the current matrix values (needed to compute update deltas), and a `tree[n+1][m+1]` 2D Fenwick array.
2. `update(row, col, value)`: compute `delta = value - matrix[row][col]`, then for `i = row+1` stepping by `i & (-i)` while `i <= n`, for `j = col+1` stepping by `j & (-j)` while `j <= m`, add `delta` to `tree[i][j]`.
3. `prefixSum(row, col)` (sum of the rectangle from `(0,0)` to `(row,col)` inclusive): for `i = row+1` stepping *down* by `i & (-i)` while `i > 0`, for `j = col+1` stepping *down* by `j & (-j)` while `j > 0`, add `tree[i][j]`.
4. `sumRegion(row1, col1, row2, col2)`: use 2D inclusion-exclusion, exactly like a 2D prefix-sum array: `prefixSum(row2,col2) - prefixSum(row1-1,col2) - prefixSum(row2,col1-1) + prefixSum(row1-1,col1-1)`.

**Why the same inclusion-exclusion formula from static 2D prefix sums still applies here:** the 2D Fenwick tree's `prefixSum(row, col)` plays exactly the same role as a static 2D prefix-sum array's precomputed corner value — it answers "sum of everything from the top-left corner to this point." The formula for combining four such corner sums into an arbitrary rectangle is unchanged; only how each corner sum is *computed* (O(log n * log m) via Fenwick, instead of O(1) lookup) differs.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="2D inclusion-exclusion: the target rectangle equals the big corner sum minus the two overlapping strips plus back the double-subtracted corner">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="100" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="70" width="90" height="50" fill="#3fb950" opacity="0.5"/>
    <text x="165" y="100" fill="#0d1117" text-anchor="middle" font-size="11">target region</text>
    <text x="280" y="70" fill="#e6edf3">= prefixSum(row2,col2)</text>
    <text x="280" y="90" fill="#e6edf3">- prefixSum(row1-1,col2) - prefixSum(row2,col1-1)</text>
    <text x="280" y="110" fill="#e6edf3">+ prefixSum(row1-1,col1-1)</text>
  </g>
</svg>

The same 2D inclusion-exclusion identity from static prefix sums applies directly, using Fenwick-computed corner sums instead of precomputed array lookups.

## 5. Runnable example

**Level 1 — Brute force.** `sumRegion` scans the requested rectangle directly, O(rows * cols) per query; `update` is O(1). Fast updates, slow queries on large regions.

**KEY INSIGHT:** nesting the same lowest-set-bit trick along both dimensions extends the 1D Fenwick tree's O(log n) guarantee to 2D as O(log n * log m).

**Level 2 — Optimal.** 2D Fenwick tree, O(log n * log m) per update and per query.

**Level 3 — Hardened.** Handles a `sumRegion` call covering the entire matrix, and repeated updates to the same cell.

```java
// NumMatrix.java
public class NumMatrix {

    int[][] matrix;
    int[][] tree;
    int rows, cols;

    public NumMatrix(int[][] matrix) {
        this.rows = matrix.length;
        this.cols = matrix[0].length;
        this.matrix = new int[rows][cols];
        this.tree = new int[rows + 1][cols + 1];
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                update(r, c, matrix[r][c]);
            }
        }
    }

    void fenwickAdd(int row, int col, int delta) {
        for (int i = row + 1; i <= rows; i += i & (-i)) {
            for (int j = col + 1; j <= cols; j += j & (-j)) {
                tree[i][j] += delta;
            }
        }
    }

    int prefixSum(int row, int col) {
        int sum = 0;
        for (int i = row + 1; i > 0; i -= i & (-i)) {
            for (int j = col + 1; j > 0; j -= j & (-j)) {
                sum += tree[i][j];
            }
        }
        return sum;
    }

    public void update(int row, int col, int value) {
        int delta = value - matrix[row][col];
        matrix[row][col] = value;
        fenwickAdd(row, col, delta);
    }

    public int sumRegion(int row1, int col1, int row2, int col2) {
        return prefixSum(row2, col2)
             - prefixSum(row1 - 1, col2)
             - prefixSum(row2, col1 - 1)
             + prefixSum(row1 - 1, col1 - 1);
    }

    public static void main(String[] args) {
        int[][] matrix = {{3, 0, 1}, {5, 6, 3}, {1, 2, 0}};
        NumMatrix nm = new NumMatrix(matrix);
        System.out.println(nm.sumRegion(0, 0, 2, 2)); // 21
        nm.update(1, 1, 10); // 6 -> 10
        System.out.println(nm.sumRegion(0, 0, 2, 2)); // 25
    }
}
```

**How to run:** save as `NumMatrix.java`, then run `java NumMatrix.java`.

## 6. Walkthrough

Trace `sumRegion(0,0,2,2)` after `update(1,1,10)` on the 3x3 example matrix (now `[[3,0,1],[5,10,3],[1,2,0]]`):

1. `prefixSum(2,2)` sums the entire matrix: `3+0+1+5+10+3+1+2+0 = 25`.
2. `prefixSum(-1,2)` and `prefixSum(2,-1)`: both handle an out-of-range index (`row1-1 = -1` or `col1-1 = -1`) by returning `0`, since a negative index means "the empty prefix."
3. `prefixSum(-1,-1)` also returns `0` for the same reason.
4. Combining: `25 - 0 - 0 + 0 = 25`, matching the direct full-matrix sum.

## 7. Gotchas & takeaways

> Gotcha: the `-1` cases in `sumRegion` (when `row1` or `col1` is `0`) must be handled gracefully — calling `prefixSum(-1, ...)` should return `0`, not throw or loop incorrectly; the `for (int i = row + 1; i > 0; ...)` loop condition naturally handles `row = -1` (making `i = 0`, so the loop body never executes) as long as the code is written exactly this way.

- Signal: a mutable 2D range-sum problem extends the same Fenwick-tree idea to two dimensions, using nested lowest-set-bit loops.
- The same four-term inclusion-exclusion formula from static 2D prefix sums still applies — only the corner-sum computation changes.
- Related problems: Range Sum Query - Mutable (the 1D version this builds on), Falling Squares (a different 2D-flavored range-update problem).
