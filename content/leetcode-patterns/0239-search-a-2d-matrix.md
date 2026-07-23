---
card: leetcode-patterns
gi: 239
slug: search-a-2d-matrix
title: Search a 2D Matrix
---

## 1. What it is

Given an `m x n` matrix where each row is sorted left to right, and the first element of each row is greater than the last element of the previous row, return `true` if `target` exists in the matrix. Example: `matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]]`, `target = 3` → `true`.

## 2. Why & when

The matrix's two properties together mean it behaves exactly like ONE giant sorted array, just displayed in rows of fixed width. Use this shape whenever a 2D grid is described as sorted both across each row and down between rows, so you can search it in O(log(m·n)) time instead of the O(m + n) a row-then-column scan would need.

## 3. Core concept

**Key idea:** treat the matrix as a virtual 1D array of length `m * n`, without actually flattening it into a new array. Any virtual index `i` maps to `matrix[i / n][i % n]` (row = index divided by column count, column = index modulo column count). Run plain binary search over the virtual index range `0..m*n-1`, converting `mid` to a row/column pair each time you need to read a value.

**Steps:**
1. Let `m` and `n` be the number of rows and columns. Set `lo = 0`, `hi = m * n - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. Convert: `row = mid / n`, `col = mid % n`. Read `value = matrix[row][col]`.
4. If `value == target`, return `true`.
5. If `value < target`, set `lo = mid + 1`; otherwise set `hi = mid - 1`.
6. If the loop ends without a match, return `false`.

**Why it is correct:** because each row is sorted, and every row's first value is greater than the previous row's last value, reading the matrix in row-major order (row 0 left to right, then row 1 left to right, and so on) produces a single, fully sorted sequence. The virtual-index-to-row/column mapping just walks that sequence without allocating it, so ordinary binary search's correctness argument applies unchanged.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3x4 matrix mapped to a virtual sorted array of 12 elements, index 8 maps to row 2 col 0">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">matrix (3 rows x 4 cols), virtual index in each cell:</text>
    <rect x="10" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="25" y="47" text-anchor="middle" font-size="9">0</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="70" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="47" text-anchor="middle" font-size="9">2</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="115" y="47" text-anchor="middle" font-size="9">3</text>
    <rect x="10" y="55" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="25" y="72" text-anchor="middle" font-size="9">4</text>
    <rect x="40" y="55" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="72" text-anchor="middle" font-size="9">5</text>
    <rect x="70" y="55" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="72" text-anchor="middle" font-size="9">6</text>
    <rect x="100" y="55" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="115" y="72" text-anchor="middle" font-size="9">7</text>
    <rect x="10" y="80" width="30" height="24" fill="#3fb950"/><text x="25" y="97" fill="#0d1117" text-anchor="middle" font-size="9">8</text>
    <rect x="40" y="80" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="97" text-anchor="middle" font-size="9">9</text>
    <rect x="70" y="80" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="97" text-anchor="middle" font-size="9">10</text>
    <rect x="100" y="80" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="115" y="97" text-anchor="middle" font-size="9">11</text>
    <text x="10" y="130">virtual index 8 -&gt; row = 8/4 = 2, col = 8%4 = 0</text>
    <text x="10" y="155">binary search runs over indices 0..11 exactly as on a flat array</text>
  </g>
</svg>

The matrix is never actually flattened; only the row/column formula changes at read time, while the search loop stays identical to plain binary search.

## 5. Runnable example

```java
// SearchA2DMatrix.java
public class SearchA2DMatrix {

    // Level 1 -- Brute force: scan every row, and within a promising
    // row scan every column, comparing to target. Correct, but O(m*n)
    // -- ignores that the whole matrix is one sorted sequence.

    // KEY INSIGHT: the matrix, read row by row left to right, IS a
    // single sorted array of size m*n. Map a virtual 1D index to a
    // row/column pair, and reuse plain binary search unchanged.

    // Level 2 -- Optimal: binary search over the virtual flat index.
    static boolean searchMatrix(int[][] matrix, int target) {
        int m = matrix.length, n = matrix[0].length;
        int lo = 0, hi = m * n - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int row = mid / n, col = mid % n;
            int value = matrix[row][col];
            if (value == target) return true;
            if (value < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return false;
    }

    // Level 3 -- Hardened: works unchanged for a matrix with a single
    // row (n == m*n, degrades to plain 1D binary search) or a single
    // column (n == 1, row = mid, col always 0).

    public static void main(String[] args) {
        int[][] matrix = {{1,3,5,7},{10,11,16,20},{23,30,34,60}};
        System.out.println(searchMatrix(matrix, 3));
        // true
        System.out.println(searchMatrix(matrix, 13));
        // false
    }
}
```

**How to run:** `java SearchA2DMatrix.java`

## 6. Walkthrough

Trace `searchMatrix(matrix, 3)` on the 3x4 example, `lo=0, hi=11`:

| lo | hi | mid | row | col | value | comparison | action |
|---|---|---|---|---|---|---|---|
| 0 | 11 | 5 | 1 | 1 | 11 | 11 > 3 | hi = 4 |
| 0 | 4 | 2 | 0 | 2 | 5 | 5 > 3 | hi = 1 |
| 0 | 1 | 0 | 0 | 0 | 1 | 1 < 3 | lo = 1 |
| 1 | 1 | 1 | 0 | 1 | 3 | match | return true |

Found in 4 comparisons instead of scanning up to 12 cells. Time complexity is O(log(m·n)). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this specific matrix layout (each row sorted, and every row strictly greater than the previous row) is what allows treating it as ONE flat sorted array — a weaker guarantee (only each row and each column individually sorted, values NOT continuous between rows) needs a different algorithm (see the "II" variant, which uses a staircase search from a corner instead).

- The `row = mid / n`, `col = mid % n` conversion is the only new idea here; the search loop itself is identical to plain Binary Search.
- Always read `matrix[0].length` for `n` (assuming a non-empty matrix with at least one row) before computing the virtual index range.
- Related problems: Binary Search (the 1D base case), Search in Rotated Sorted Array (a different twist on the same core loop).
