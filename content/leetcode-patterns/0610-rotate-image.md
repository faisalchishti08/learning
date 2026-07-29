---
card: leetcode-patterns
gi: 610
slug: rotate-image
title: Rotate Image
---

## 1. What it is

Given an `n x n` 2D matrix representing an image, rotate it 90 degrees clockwise **in place** (without allocating another matrix). Example: `[[1,2,3],[4,5,6],[7,8,9]]` rotates to `[[7,4,1],[8,5,2],[9,6,3]]` — the first column of the output, read top to bottom, is the first row of the input, read right to left.

## 2. Why & when

This is the direct application of [the Math & Geometry matrix-rotation template](0597-math-geometry-template-modular-arithmetic-in-place-matrix-mo.md): rewriting an `n x n` matrix's positions to achieve a 90-degree clockwise rotation, constrained to O(1) extra space — no second matrix allowed. The "in place" constraint is the direct signal that a naive "build a new rotated matrix" approach is disallowed by the problem, even though it would be simpler.

## 3. Core concept

**Key idea:** a 90-degree clockwise rotation decomposes into two simpler, well-understood in-place operations performed in sequence: **transpose** (reflect the matrix across its main diagonal, swapping `matrix[i][j]` with `matrix[j][i]`), then **reverse each row**.

**Steps:**
1. **Transpose:** for each `i` from `0` to `n-1`, and each `j` from `i+1` to `n-1` (only the upper triangle, to avoid swapping each pair twice), swap `matrix[i][j]` and `matrix[j][i]`.
2. **Reverse each row:** for each row in the now-transposed matrix, reverse its elements left to right (swap `row[left]` and `row[right]`, moving `left` inward and `right` inward, until they meet or cross).

**Why transpose-then-reverse-rows produces a 90-degree clockwise rotation, and not some other transformation:** transposing turns row `i` into column `i` — element `(i,j)` moves to `(j,i)`. Reversing each row afterward then flips column `i`'s vertical order into a horizontal mirror. The net effect: the original first row (top row) becomes the last column, read top to bottom — exactly matching what a physical 90-degree clockwise rotation of a square grid does. (A 90-degree counter-clockwise rotation would instead be transpose-then-reverse-each-**column**, or equivalently, reverse rows first, then transpose.)

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 3x3 matrix transposed then row-reversed to achieve a 90-degree clockwise rotation">
  <g font-family="sans-serif" font-size="11">
    <text x="90" y="20" fill="#8b949e" text-anchor="middle">original</text>
    <rect x="20" y="30" width="140" height="105" fill="none" stroke="#30363d"/>
    <text x="55" y="55" fill="#e6edf3" text-anchor="middle">1</text><text x="90" y="55" fill="#e6edf3" text-anchor="middle">2</text><text x="125" y="55" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="55" y="90" fill="#e6edf3" text-anchor="middle">4</text><text x="90" y="90" fill="#e6edf3" text-anchor="middle">5</text><text x="125" y="90" fill="#e6edf3" text-anchor="middle">6</text>
    <text x="55" y="120" fill="#e6edf3" text-anchor="middle">7</text><text x="90" y="120" fill="#e6edf3" text-anchor="middle">8</text><text x="125" y="120" fill="#e6edf3" text-anchor="middle">9</text>
    <text x="280" y="20" fill="#8b949e" text-anchor="middle">transposed</text>
    <rect x="210" y="30" width="140" height="105" fill="none" stroke="#f0883e"/>
    <text x="245" y="55" fill="#e6edf3" text-anchor="middle">1</text><text x="280" y="55" fill="#e6edf3" text-anchor="middle">4</text><text x="315" y="55" fill="#e6edf3" text-anchor="middle">7</text>
    <text x="245" y="90" fill="#e6edf3" text-anchor="middle">2</text><text x="280" y="90" fill="#e6edf3" text-anchor="middle">5</text><text x="315" y="90" fill="#e6edf3" text-anchor="middle">8</text>
    <text x="245" y="120" fill="#e6edf3" text-anchor="middle">3</text><text x="280" y="120" fill="#e6edf3" text-anchor="middle">6</text><text x="315" y="120" fill="#e6edf3" text-anchor="middle">9</text>
    <text x="480" y="20" fill="#8b949e" text-anchor="middle">rows reversed (final)</text>
    <rect x="410" y="30" width="140" height="105" fill="none" stroke="#3fb950"/>
    <text x="445" y="55" fill="#e6edf3" text-anchor="middle">7</text><text x="480" y="55" fill="#e6edf3" text-anchor="middle">4</text><text x="515" y="55" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="445" y="90" fill="#e6edf3" text-anchor="middle">8</text><text x="480" y="90" fill="#e6edf3" text-anchor="middle">5</text><text x="515" y="90" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="445" y="120" fill="#e6edf3" text-anchor="middle">9</text><text x="480" y="120" fill="#e6edf3" text-anchor="middle">6</text><text x="515" y="120" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="350" y="170" fill="#79c0ff" text-anchor="middle">two O(n^2) passes, zero extra matrix allocation</text>
  </g>
</svg>

Transpose reflects across the main diagonal; reversing each row then completes the clockwise turn — together they touch every cell exactly twice, never allocating a second matrix.

## 5. Runnable example

**Level 1 — Brute force.** Allocate a new `n x n` matrix, and for each `(i,j)` in the original, write `new[j][n-1-i] = original[i][j]` directly (the closed-form position for a 90-degree clockwise rotation). Correct and arguably simpler to reason about in one step, but violates the "in place" constraint by using O(n^2) extra space.

**KEY INSIGHT:** the same rotation the closed-form index formula describes in one step can be achieved with zero extra matrix allocation, by decomposing it into two simple, separately well-known in-place operations: transpose, then reverse each row.

**Level 2 — Optimal.** Transpose (swap upper triangle with lower triangle) followed by per-row reversal, O(n^2) time (unavoidable — every cell must move), O(1) extra space.

**Level 3 — Hardened.** The transpose loop's inner bound (`j` starts at `i+1`, not `0`) avoids swapping each pair of symmetric cells twice (which would undo the transpose), and row reversal correctly handles both even and odd row lengths.

```java
// RotateImage.java
import java.util.*;

public class RotateImage {

    public static void rotate(int[][] matrix) {
        int n = matrix.length;

        // Step 1: transpose in place.
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        }

        // Step 2: reverse each row in place.
        for (int[] row : matrix) {
            int left = 0, right = row.length - 1;
            while (left < right) {
                int tmp = row[left];
                row[left] = row[right];
                row[right] = tmp;
                left++;
                right--;
            }
        }
    }

    public static void main(String[] args) {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        rotate(matrix);
        for (int[] row : matrix) {
            System.out.println(Arrays.toString(row));
        }
        // [7, 4, 1]
        // [8, 5, 2]
        // [9, 6, 3]
    }
}
```

**How to run:** save as `RotateImage.java`, then run `java RotateImage.java`.

## 6. Walkthrough

Trace the transpose step on `[[1,2,3],[4,5,6],[7,8,9]]` (only upper-triangle swaps, `j > i`):

| swap | positions | before | after |
|---|---|---|---|
| 1 | (0,1) <-> (1,0) | 2, 4 | 4, 2 |
| 2 | (0,2) <-> (2,0) | 3, 7 | 7, 3 |
| 3 | (1,2) <-> (2,1) | 6, 8 | 8, 6 |

After transpose: `[[1,4,7],[2,5,8],[3,6,9]]`. Reversing each row: row `[1,4,7]` becomes `[7,4,1]`; row `[2,5,8]` becomes `[8,5,2]`; row `[3,6,9]` becomes `[9,6,3]` — matching the expected final rotated matrix.

## 7. Gotchas & takeaways

> Gotcha: starting the transpose's inner loop at `j = 0` instead of `j = i + 1` swaps every off-diagonal pair **twice** (once as `(i,j)`, once again later as `(j,i)`), which undoes the transpose entirely and leaves the matrix unchanged — the inner loop must only visit each symmetric pair once.

- Signal: "rotate/transform a matrix in place" is the transpose-plus-reflect decomposition signal — break the transform into simpler, well-known steps rather than deriving one combined index formula.
- O(n^2) is optimal here: every cell must be visited at least once, so no algorithm can do less work.
- Related problems: Spiral Matrix (a different matrix-traversal shape, reading in a spiral rather than transforming positions), Set Matrix Zeroes (a different in-place matrix technique, using the matrix's own borders as scratch space).
