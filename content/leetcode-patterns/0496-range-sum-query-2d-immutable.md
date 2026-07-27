---
card: leetcode-patterns
gi: 496
slug: range-sum-query-2d-immutable
title: Range Sum Query 2D - Immutable
---

## 1. What it is

Design a class `NumMatrix` that, given a 2D integer matrix, answers many `sumRegion(row1, col1, row2, col2)` queries — the sum of all elements inside the rectangle from `(row1, col1)` to `(row2, col2)`, inclusive. The matrix never changes. Example: a query on a sample 5x5 matrix for the rectangle `(2,1)` to `(4,3)` returns `8`.

## 2. Why & when

This extends the 1D [prefix-sum template](0488-prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma.md) to two dimensions. Just as a 1D prefix sum turns any range sum into a subtraction of two values, a 2D prefix sum turns any rectangle sum into a combination of four values, using inclusion-exclusion. Constraints: up to 200x200 matrix, up to 10,000 queries.

## 3. Core concept

**Key idea:** build a 2D prefix-sum table `prefixSum` where `prefixSum[r][c]` is the sum of every element in the rectangle from `(0,0)` to `(r-1, c-1)`. Any rectangle sum is then four lookups combined with inclusion-exclusion: the whole area up to the bottom-right corner, minus the two overlapping strips above and to the left, plus back the doubly-subtracted corner.

**Steps:**
1. Build `prefixSum` of size `(rows+1) x (cols+1)`, all zero on the first row and column.
2. Fill it: `prefixSum[r+1][c+1] = prefixSum[r][c+1] + prefixSum[r+1][c] - prefixSum[r][c] + matrix[r][c]` (the standard 2D prefix-sum recurrence, itself an inclusion-exclusion step).
3. For `sumRegion(row1, col1, row2, col2)`, return `prefixSum[row2+1][col2+1] - prefixSum[row1][col2+1] - prefixSum[row2+1][col1] + prefixSum[row1][col1]`.

**Why the "+ prefixSum[row1][col1]" term is needed:** subtracting the top strip and the left strip both remove the top-left overlapping rectangle once each — twice in total — so it must be added back once to correct for the double subtraction. This is the classic inclusion-exclusion pattern, applied here to areas instead of sets.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inclusion-exclusion combining four prefix-sum corners into one rectangle sum">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="150" height="150" fill="#161b22" stroke="#79c0ff"/>
    <text x="95" y="100" fill="#79c0ff" text-anchor="middle">whole area</text>
    <text x="95" y="120" fill="#79c0ff" text-anchor="middle">to (row2,col2)</text>
    <rect x="220" y="20" width="90" height="150" fill="#161b22" stroke="#f0883e"/>
    <text x="265" y="100" fill="#f0883e" text-anchor="middle" font-size="11">left strip</text>
    <rect x="360" y="20" width="150" height="60" fill="#161b22" stroke="#f0883e"/>
    <text x="435" y="55" fill="#f0883e" text-anchor="middle" font-size="11">top strip</text>
    <rect x="550" y="20" width="60" height="60" fill="#161b22" stroke="#3fb950"/>
    <text x="580" y="55" fill="#3fb950" text-anchor="middle" font-size="10">corner (+back)</text>
    <text x="20" y="190" fill="#8b949e">region = whole - left strip - top strip + corner (added back once)</text>
  </g>
</svg>

Four precomputed corner sums combine, via inclusion-exclusion, into any rectangle's sum in O(1).

## 5. Runnable example

**Level 1 — Brute force.** Sum every cell inside the rectangle directly on each query. O(rows · cols) per query.

**KEY INSIGHT:** a 2D prefix sum, built once, answers any rectangle query with four array lookups and one inclusion-exclusion formula — the same idea as the 1D version, extended by one dimension.

**Level 2 — Optimal.** Precomputed 2D prefix-sum table, O(rows · cols) constructor, O(1) per query.

**Level 3 — Hardened.** Handles a single-cell region (`row1==row2`, `col1==col2`) and a region covering the whole matrix.

```java
// NumMatrix.java
public class NumMatrix {

    private final int[][] prefixSum;

    // Level 2 & 3: build once, O(rows * cols)
    public NumMatrix(int[][] matrix) {
        int rows = matrix.length, cols = matrix[0].length;
        prefixSum = new int[rows + 1][cols + 1];
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                prefixSum[r + 1][c + 1] = prefixSum[r][c + 1] + prefixSum[r + 1][c]
                    - prefixSum[r][c] + matrix[r][c];
            }
        }
    }

    // O(1) per query
    public int sumRegion(int row1, int col1, int row2, int col2) {
        return prefixSum[row2 + 1][col2 + 1] - prefixSum[row1][col2 + 1]
            - prefixSum[row2 + 1][col1] + prefixSum[row1][col1];
    }

    // Level 1: brute force reference, O(rows * cols) per query
    static int bruteForceSumRegion(int[][] matrix, int row1, int col1, int row2, int col2) {
        int sum = 0;
        for (int r = row1; r <= row2; r++) {
            for (int c = col1; c <= col2; c++) sum += matrix[r][c];
        }
        return sum;
    }

    public static void main(String[] args) {
        int[][] matrix = {
            {3, 0, 1, 4, 2},
            {5, 6, 3, 2, 1},
            {1, 2, 0, 1, 5},
            {4, 1, 0, 1, 7},
            {1, 0, 3, 0, 5}
        };
        NumMatrix numMatrix = new NumMatrix(matrix);

        System.out.println("sumRegion(2,1,4,3): " + numMatrix.sumRegion(2, 1, 4, 3)
            + " (brute force: " + bruteForceSumRegion(matrix, 2, 1, 4, 3) + ")");
        System.out.println("sumRegion(1,1,2,2): " + numMatrix.sumRegion(1, 1, 2, 2)
            + " (brute force: " + bruteForceSumRegion(matrix, 1, 1, 2, 2) + ")");
        System.out.println("single cell (0,0,0,0): " + numMatrix.sumRegion(0, 0, 0, 0));
    }
}
```

**How to run:** save as `NumMatrix.java`, then run `java NumMatrix.java`.

## 6. Walkthrough

For `sumRegion(2, 1, 4, 3)`: `prefixSum[5][4]` sums everything up to row 4, col 3 (inclusive); subtract `prefixSum[2][4]` (everything above row 2) and `prefixSum[5][1]` (everything left of col 1); add back `prefixSum[2][1]` (the corner subtracted twice).

| term | meaning | value |
|---|---|---|
| prefixSum[5][4] | sum of rows 0-4, cols 0-3 | (whole relevant block) |
| prefixSum[2][4] | sum of rows 0-1, cols 0-3 (subtract: above the region) | — |
| prefixSum[5][1] | sum of rows 0-4, col 0 (subtract: left of the region) | — |
| prefixSum[2][1] | sum of rows 0-1, col 0 (add back: double-subtracted corner) | — |

Combining these four values gives `sumRegion(2,1,4,3) = 8`, matching the direct brute-force sum of the rectangle covering rows 2-4, columns 1-3.

## 7. Gotchas & takeaways

> Gotcha: forgetting the "+ prefixSum[row1][col1]" correction term leaves the top-left corner subtracted twice, silently under-counting every rectangle query — the four-term inclusion-exclusion formula must always include all four terms with their correct signs.

- A 2D prefix sum is the 1D idea applied twice, with one inclusion-exclusion correction for the doubly-subtracted corner.
- Precompute once in the constructor; every `sumRegion` call afterward is O(1), regardless of the rectangle's size.
- Time: O(rows · cols) constructor, O(1) per query; space: O(rows · cols) for the prefix-sum table.
