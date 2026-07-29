---
card: leetcode-patterns
gi: 612
slug: set-matrix-zeroes
title: Set Matrix Zeroes
---

## 1. What it is

Given an `m x n` matrix, if an element is `0`, set its **entire row and entire column** to `0`, doing this in place. A follow-up asks for an O(1) extra space solution (beyond the input matrix itself). Example: `[[1,1,1],[1,0,1],[1,1,1]]` → `[[1,0,1],[0,0,0],[1,0,1]]` (the single `0` at `(1,1)` zeroes out row `1` and column `1` entirely).

## 2. Why & when

The direct approach — scan for zeroes, then immediately zero out their rows and columns — has a subtle bug: zeroing cells *while scanning* can create new `0`s that get mistaken for original zeroes, cascading incorrectly to zero out far more of the matrix than intended. Recording *which* rows and columns need zeroing first, separately from actually zeroing them, avoids this; the O(1) space follow-up pushes this further by reusing the matrix's own first row and first column as that record, instead of separate arrays.

## 3. Core concept

**Key idea:** never zero a cell while still reading original values from the matrix. First pass: scan the whole matrix once to determine *which* rows and columns contain a zero, recording this in a separate structure. Second pass: use that record to zero the appropriate cells. For O(1) space, the "separate structure" is the matrix's own first row (for column markers) and first column (for row markers), with two extra booleans to remember whether the first row and first column themselves originally contained a zero (since they double as both data and markers).

**Steps (O(1) space version):**
1. Check whether the first row, and separately the first column, originally contain any zero — record each as a boolean, since these two lines are about to be reused as marker storage.
2. Scan the rest of the matrix (from `(1,1)` onward). Whenever `matrix[i][j] == 0`, set `matrix[i][0] = 0` (mark row `i`) and `matrix[0][j] = 0` (mark column `j`).
3. Scan the rest of the matrix again. For each `(i,j)` with `i >= 1, j >= 1`, if `matrix[i][0] == 0` or `matrix[0][j] == 0`, set `matrix[i][j] = 0`.
4. Finally, using the two booleans from step 1, zero the first row entirely if it originally had a zero, and zero the first column entirely if it originally had a zero.

**Why step 4 must come last, and why the two booleans are needed:** the first row and column are being used as scratch space for markers throughout steps 2–3, so their values no longer reflect the *original* matrix by the time step 3 finishes — the two booleans captured in step 1 are the only remaining record of whether those two special lines needed zeroing for their own sake, independent of the marker information they now hold.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The first row and first column reused as marker storage: a zero at (1,1) marks matrix[1][0] and matrix[0][1]">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="85" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="110" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="135" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">0(mark col1)</text>
    <rect x="60" y="80" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="85" y="102" fill="#e6edf3" text-anchor="middle" font-size="10">0(mark row1)</text>
    <rect x="110" y="80" width="50" height="35" fill="#161b22" stroke="#79c0ff"/><text x="135" y="102" fill="#e6edf3" text-anchor="middle" font-size="10">0(orig)</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">the original 0 at (1,1) writes markers into row 0 and column 0 instead of a separate set</text>
  </g>
</svg>

The matrix's own border cells double as marker storage — no separate arrays are needed, achieving true O(1) extra space.

## 5. Runnable example

**Level 1 — Brute force.** Use two separate `boolean[]` arrays (`zeroRows`, `zeroCols`) of size `m` and `n` to record which rows/columns need zeroing, then a second pass applies them. Correct and simpler to reason about, but uses O(m+n) extra space, not O(1).

**KEY INSIGHT:** the matrix's own first row and first column can serve as that same marker storage, since they will be at least partially overwritten anyway — the only extra state needed is two booleans remembering whether those two special lines originally had a zero of their own, since their true data gets overwritten by markers during the scan.

**Level 2 — Optimal (O(m+n) space).** Two boolean arrays for rows/columns to zero, O(m*n) time, O(m+n) space.

**Level 3 — Hardened (O(1) space).** Reuses the first row and column as markers, using two booleans to preserve their own original zero-status, O(m*n) time, O(1) extra space.

```java
// SetMatrixZeroes.java
import java.util.*;

public class SetMatrixZeroes {

    public static void setZeroes(int[][] matrix) {
        int m = matrix.length, n = matrix[0].length;
        boolean firstRowHasZero = false, firstColHasZero = false;

        for (int j = 0; j < n; j++) if (matrix[0][j] == 0) firstRowHasZero = true;
        for (int i = 0; i < m; i++) if (matrix[i][0] == 0) firstColHasZero = true;

        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                if (matrix[i][j] == 0) {
                    matrix[i][0] = 0;
                    matrix[0][j] = 0;
                }
            }
        }

        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                if (matrix[i][0] == 0 || matrix[0][j] == 0) {
                    matrix[i][j] = 0;
                }
            }
        }

        if (firstRowHasZero) {
            for (int j = 0; j < n; j++) matrix[0][j] = 0;
        }
        if (firstColHasZero) {
            for (int i = 0; i < m; i++) matrix[i][0] = 0;
        }
    }

    public static void main(String[] args) {
        int[][] matrix = {{1, 1, 1}, {1, 0, 1}, {1, 1, 1}};
        setZeroes(matrix);
        for (int[] row : matrix) System.out.println(Arrays.toString(row));
        // [1, 0, 1]
        // [0, 0, 0]
        // [1, 0, 1]
    }
}
```

**How to run:** save as `SetMatrixZeroes.java`, then run `java SetMatrixZeroes.java`.

## 6. Walkthrough

Trace on `[[1,1,1],[1,0,1],[1,1,1]]`:

1. Check first row `[1,1,1]`: no zero, `firstRowHasZero=false`. Check first column `1,1,1`: no zero, `firstColHasZero=false`.
2. Scan from `(1,1)` onward: `matrix[1][1]==0` found. Mark `matrix[1][0]=0` (row 1) and `matrix[0][1]=0` (column 1). Matrix now: `[[1,0,1],[0,0,1],[1,1,1]]`.
3. Second scan (using markers): `(1,2)`: `matrix[1][0]==0` -> zero it: `matrix[1][2]=0`. `(2,1)`: `matrix[0][1]==0` -> zero it: `matrix[2][1]=0`. Other cells' markers are non-zero, left unchanged.
4. `firstRowHasZero` and `firstColHasZero` are both `false`, so the first row/column are not further zeroed (they already correctly hold their marker-derived values, `matrix[1][0]=0` and `matrix[0][1]=0`, which happen to coincide with the correct final answer since row 1 and column 1 are exactly what needed zeroing).

Final: `[[1,0,1],[0,0,0],[1,0,1]]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: zeroing cells directly during the very first scan (instead of only marking rows/columns) creates new `0`s that the scan itself might later misread as original zeroes, incorrectly cascading to zero out far more of the matrix than the true input warranted — always separate "detect what needs zeroing" from "apply the zeroing" into two distinct passes.

- Signal: "if a condition holds at one cell, propagate an effect across its whole row and column" is the row/column-marker signal — mark first, apply second, never mutate mid-scan.
- The O(1) space trick reuses the matrix's own border as marker storage, at the cost of needing two extra booleans to remember the border's own original zero-status before it is overwritten.
- Related problems: Rotate Image (a different in-place matrix technique, transpose-plus-reverse instead of marker-plus-apply), Game of Life (a similar "read all original values before mutating any" constraint, solved with encoded intermediate states instead of markers).
