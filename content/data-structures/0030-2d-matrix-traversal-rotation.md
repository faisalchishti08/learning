---
card: data-structures
gi: 30
slug: 2d-matrix-traversal-rotation
title: 2D matrix traversal & rotation
---

## 1. What it is

A **matrix** here is a rectangular 2D array, `int[][] matrix`, where every row has the same length. **Traversal** means visiting its elements in a defined order — row by row, column by column, diagonally, or spiraling from the outside in. **Rotation** means turning the whole matrix 90 degrees, which can be done cleanly in-place using two combined steps: transpose, then reverse.

## 2. Why & when

Matrix problems appear whenever data is naturally grid-shaped — images (pixels), game boards, or adjacency matrices for graphs. Spiral traversal and 90-degree rotation are common because they force you to reason carefully about row/column index relationships, which is exactly the skill that transfers to any 2D-array problem.

## 3. Core concept

**Row-major traversal is the default.** A nested loop, outer over rows and inner over columns (`for row... for col... matrix[row][col]`), visits every element in the order they are laid out in memory (since each row is its own contiguous array) — this is the most cache-friendly traversal order.

**Spiral traversal shrinks a boundary.** Track four boundaries — `top`, `bottom`, `left`, `right`. Walk the top row left-to-right, the right column top-to-bottom, the bottom row right-to-left, and the left column bottom-to-top, then shrink each boundary inward by one and repeat, until the boundaries cross.

**90-degree rotation = transpose + reverse each row.** **Transpose** swaps `matrix[i][j]` with `matrix[j][i]` for every `i < j`, flipping the matrix across its main diagonal. Reversing each row of the transposed matrix then completes a 90-degree clockwise rotation. This works because transposing turns "row `i`" into "column `i`," and reversing that new row puts the elements in the exact order a clockwise rotation requires.

**Rotation in place needs a square matrix.** The transpose-then-reverse trick only works without extra space on a square (`n x n`) matrix, because transposing a non-square matrix changes its dimensions (`m x n` becomes `n x m`), which cannot be done by swapping values within the original array.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 3x3 matrix rotated 90 degrees clockwise via transpose then row reversal">
  <g font-family="sans-serif" font-size="11">
    <text x="110" y="18" fill="#8b949e" text-anchor="middle">original</text>
    <text x="110" y="40" fill="#e6edf3" text-anchor="middle">1 2 3</text>
    <text x="110" y="60" fill="#e6edf3" text-anchor="middle">4 5 6</text>
    <text x="110" y="80" fill="#e6edf3" text-anchor="middle">7 8 9</text>

    <text x="320" y="18" fill="#8b949e" text-anchor="middle">transposed (swap across diagonal)</text>
    <text x="320" y="40" fill="#e6edf3" text-anchor="middle">1 4 7</text>
    <text x="320" y="60" fill="#e6edf3" text-anchor="middle">2 5 8</text>
    <text x="320" y="80" fill="#e6edf3" text-anchor="middle">3 6 9</text>

    <text x="530" y="18" fill="#8b949e" text-anchor="middle">rotated (reverse each row)</text>
    <text x="530" y="40" fill="#79c0ff" text-anchor="middle">7 4 1</text>
    <text x="530" y="60" fill="#79c0ff" text-anchor="middle">8 5 2</text>
    <text x="530" y="80" fill="#79c0ff" text-anchor="middle">9 6 3</text>

    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">transpose + reverse each row = 90-degree clockwise rotation, in place</text>
  </g>
</svg>

Transposing flips across the diagonal; reversing each row of that result completes the clockwise rotation.

## 5. Runnable example

```java
// MatrixTraversalRotation.java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MatrixTraversalRotation {

    // Basic: standard row-major traversal.
    static void basicLevel() {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        StringBuilder sb = new StringBuilder();
        for (int row = 0; row < matrix.length; row++) {
            for (int col = 0; col < matrix[row].length; col++) {
                sb.append(matrix[row][col]).append(' ');
            }
        }
        System.out.println("basic: row-major order -> " + sb.toString().trim());
    }

    // Intermediate: spiral traversal, shrinking four boundaries.
    static List<Integer> spiralOrder(int[][] matrix) {
        List<Integer> result = new ArrayList<>();
        int top = 0, bottom = matrix.length - 1;
        int left = 0, right = matrix[0].length - 1;
        while (top <= bottom && left <= right) {
            for (int col = left; col <= right; col++) result.add(matrix[top][col]);
            top++;
            for (int row = top; row <= bottom; row++) result.add(matrix[row][right]);
            right--;
            if (top <= bottom) {
                for (int col = right; col >= left; col--) result.add(matrix[bottom][col]);
                bottom--;
            }
            if (left <= right) {
                for (int row = bottom; row >= top; row--) result.add(matrix[row][left]);
                left++;
            }
        }
        return result;
    }

    static void intermediateLevel() {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        System.out.println("intermediate: spiral order -> " + spiralOrder(matrix));
    }

    // Advanced: rotate a square matrix 90 degrees clockwise, in place.
    static void rotate90Clockwise(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++) {           // transpose: swap across the main diagonal
            for (int j = i + 1; j < n; j++) {
                int temp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = temp;
            }
        }
        for (int[] row : matrix) {              // reverse each row
            for (int left = 0, right = row.length - 1; left < right; left++, right--) {
                int temp = row[left];
                row[left] = row[right];
                row[right] = temp;
            }
        }
    }

    static void advancedLevel() {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        rotate90Clockwise(matrix);
        System.out.println("advanced: rotated 90 clockwise -> " + Arrays.deepToString(matrix));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MatrixTraversalRotation.java`, then run `java MatrixTraversalRotation.java`.

## 6. Walkthrough

1. `basicLevel()` visits `{{1,2,3},{4,5,6},{7,8,9}}` row by row: `1 2 3 4 5 6 7 8 9` — the outer loop advances rows, the inner loop advances columns within each row.
2. `intermediateLevel()`'s `spiralOrder` starts with `top=0, bottom=2, left=0, right=2`. It walks the top row (`1,2,3`), then `top` becomes 1; walks the right column from row 1 down (`6,9`), then `right` becomes 1; walks the bottom row right-to-left (`8,7`), then `bottom` becomes 1; walks the left column bottom-to-top from row 1 (`4`), then `left` becomes 1.
3. Now `top=1, bottom=1, left=1, right=1` — one cell remains. The loop runs once more, adding `5` from the shrunk top row, and the boundaries cross, ending the traversal — final order `1,2,3,6,9,8,7,4,5`.
4. `advancedLevel()`'s `rotate90Clockwise` first transposes: `matrix[0][1]` (`2`) swaps with `matrix[1][0]` (`4`), and so on for every `i < j` pair, turning `{{1,2,3},{4,5,6},{7,8,9}}` into `{{1,4,7},{2,5,8},{3,6,9}}`.
5. Reversing each row of the transposed matrix (`{1,4,7}` becomes `{7,4,1}`, and so on) produces the final rotated matrix `{{7,4,1},{8,5,2},{9,6,3}}` — matching a 90-degree clockwise turn of the original grid.

## 7. Gotchas & takeaways

> Gotcha: the transpose-then-reverse rotation trick only works in place for a **square** matrix — attempting it on a non-square `m x n` matrix corrupts the data, since transposing changes the shape to `n x m`, which does not fit back into the original array's dimensions. For non-square rotation, build a new result matrix instead.

- Row-major traversal (`for row... for col...`) matches how a 2D array is actually laid out in memory, one contiguous row array at a time.
- Spiral traversal walks four shrinking boundaries (top, right, bottom, left) in order, adjusting each after its side is walked.
- In-place 90-degree rotation is transpose (swap across the diagonal) followed by reversing each row — valid only for square matrices.
- Related concepts: [Multi-dimensional & jagged arrays](0016-multi-dimensional-jagged-arrays.md), [In-place rotation & reversal](0023-in-place-rotation-reversal.md).
