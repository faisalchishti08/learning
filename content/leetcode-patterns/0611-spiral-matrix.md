---
card: leetcode-patterns
gi: 611
slug: spiral-matrix
title: Spiral Matrix
---

## 1. What it is

Given an `m x n` matrix, return all its elements in **spiral order**: starting at the top-left, moving right across the top row, then down the right column, then left across the bottom row, then up the left column, and repeating this pattern inward until every element has been visited. Example: `[[1,2,3],[4,5,6],[7,8,9]]` → `[1,2,3,6,9,8,7,4,5]`.

## 2. Why & when

This is a coordinate-geometry traversal problem: the spiral order is defined by four shrinking boundaries (top, bottom, left, right) that close inward after each full pass around the current ring. Recognize the signal whenever a problem asks for a non-standard reading order over a 2D grid defined by a geometric pattern (spiral, diagonal, zigzag) rather than plain row-by-row scanning.

## 3. Core concept

**Key idea:** maintain four boundary variables — `top`, `bottom`, `left`, `right` — representing the current unvisited rectangle. Traverse the current top row left to right, then the current right column top to bottom, then (if a bottom row remains) the current bottom row right to left, then (if a left column remains) the current left column bottom to top. After each of the four directional walks, shrink the corresponding boundary inward by one, and repeat until the boundaries cross.

**Steps:**
1. Initialize `top=0, bottom=m-1, left=0, right=n-1`.
2. While `top <= bottom` and `left <= right`:
3. Walk `left` to `right` along row `top`; then increment `top`.
4. Walk `top` to `bottom` along column `right`; then decrement `right`.
5. **If `top <= bottom` still holds** (a bottom row remains after step 3's increment), walk `right` to `left` along row `bottom`; then decrement `bottom`.
6. **If `left <= right` still holds** (a left column remains after step 4's decrement), walk `bottom` to `top` along column `left`; then increment `left`.

**Why steps 5 and 6 need their own boundary re-checks, not just steps 3 and 4:** after completing the top-row and right-column walks, the remaining rectangle may have collapsed to a single row or a single column. Re-checking `top <= bottom` before walking the bottom row (and `left <= right` before walking the left column) prevents re-visiting a row or column that was already fully covered by an earlier step — a common source of duplicate output for non-square matrices, especially ones with a single row or single column.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four shrinking boundaries defining a spiral traversal path around a 3x3 grid">
  <g font-family="sans-serif" font-size="12">
    <rect x="220" y="20" width="180" height="150" fill="none" stroke="#30363d"/>
    <line x1="220" y1="20" x2="400" y2="20" stroke="#3fb950" stroke-width="3" marker-end="url(#a16)"/>
    <line x1="400" y1="20" x2="400" y2="170" stroke="#f0883e" stroke-width="3" marker-end="url(#a16)"/>
    <line x1="400" y1="170" x2="220" y2="170" stroke="#79c0ff" stroke-width="3" marker-end="url(#a16)"/>
    <line x1="220" y1="170" x2="220" y2="70" stroke="#e6edf3" stroke-width="3" marker-end="url(#a16)"/>
    <defs><marker id="a16" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker></defs>
    <text x="310" y="185" fill="#8b949e" text-anchor="middle" font-size="11">top row -&gt; right col -&gt; bottom row -&gt; left col, boundaries shrink each pass</text>
  </g>
</svg>

Each of the four sides is walked once per outer ring, then its boundary shrinks inward — the loop continues until the shrinking boundaries cross, meaning no cells remain unvisited.

## 5. Runnable example

**Level 1 — Brute force.** Simulate a "turtle" walking one cell at a time, using a fixed direction-cycling order (right, down, left, up), and a separate `visited` boolean matrix to detect when to turn. Correct, but uses O(m*n) extra space for the visited matrix, unnecessary given the boundary-tracking approach.

**KEY INSIGHT:** the four shrinking boundaries (`top`, `bottom`, `left`, `right`) implicitly encode "have I visited this cell yet" — there is no need for a separate visited matrix, since each boundary only ever moves inward, never revisiting the same row or column twice.

**Level 2 — Optimal.** Four boundary variables, walked and shrunk in the fixed order top-row, right-column, bottom-row, left-column, O(m*n) time (every cell visited exactly once), O(1) extra space (beyond the output list).

**Level 3 — Hardened.** Correctly re-checks `top <= bottom` and `left <= right` before the bottom-row and left-column walks respectively, avoiding duplicate output on single-row or single-column matrices.

```java
// SpiralMatrix.java
import java.util.*;

public class SpiralMatrix {

    public static List<Integer> spiralOrder(int[][] matrix) {
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

    public static void main(String[] args) {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        System.out.println(spiralOrder(matrix)); // [1, 2, 3, 6, 9, 8, 7, 4, 5]
    }
}
```

**How to run:** save as `SpiralMatrix.java`, then run `java SpiralMatrix.java`.

## 6. Walkthrough

Trace the first full ring on the `3x3` example, boundaries start at `top=0,bottom=2,left=0,right=2`:

1. Top row (`col` 0 to 2, row `top=0`): append `1,2,3`. `top` becomes `1`.
2. Right column (`row` 1 to 2, col `right=2`): append `6,9`. `right` becomes `1`.
3. Check `top(1) <= bottom(2)`: true. Bottom row (`col` 1 down to 0, row `bottom=2`): append `8,7`. `bottom` becomes `1`.
4. Check `left(0) <= right(1)`: true. Left column (`row` 1 down to 1, col `left=0`): append `4`. `left` becomes `1`.
5. Loop condition: `top(1) <= bottom(1)` and `left(1) <= right(1)`: true, continue. Top row (`col` 1 to 1, row `top=1`): append `5`. `top` becomes `2`.
6. Right column (`row` 2 to 1, `right=1`): range is empty (`2 > 1`), nothing appended. `right` becomes `0`.
7. Loop condition: `top(2) <= bottom(1)`: false, loop ends.

Final result: `1,2,3,6,9,8,7,4,5` — matching the expected spiral order.

## 7. Gotchas & takeaways

> Gotcha: omitting the `if (top <= bottom)` guard before the bottom-row walk causes a single-row matrix (like `[[1,2,3]]`) to have its one row appended twice — once as the "top row" walk, and again as the "bottom row" walk, since both `top` and `bottom` still reference the same row before any boundary shrinks.

- Signal: non-standard 2D traversal orders (spiral, diagonal, boustrophedon/zigzag) are usually solved by tracking shrinking or advancing boundaries, not a visited-cells matrix.
- The four walks happen in a fixed order every ring: top row, right column, bottom row, left column — each boundary shrinks immediately after its walk, before the next walk begins.
- Related problems: Rotate Image (a different matrix in-place transform, using transpose-plus-reverse instead of boundary traversal), Spiral Matrix II (generates a spiral-filled matrix instead of reading one, using the same boundary-tracking technique in reverse).
