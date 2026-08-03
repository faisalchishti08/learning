---
card: data-structures
gi: 155
slug: sparse-table-static-range-queries
title: Sparse table (static range queries)
---

## 1. What it is

A **sparse table** is a lookup table that answers range minimum, maximum, or GCD queries in `O(1)`, built once in `O(n log n)` time. It precomputes the answer for every range whose length is a power of two, then answers any query by combining just two of those precomputed ranges.

## 2. Why & when

Use a sparse table when the array **never changes** and you need many range-min or range-max queries. A [segment tree](0152-segment-tree-range-query-update.md) also answers these in `O(log n)`, but a sparse table answers in `O(1)` per query, at the cost of losing the ability to update. If your array changes even once, rebuild the whole table (`O(n log n)`) or switch to a segment tree instead.

## 3. Core concept

**The shape.** A 2D table `table[k][i]`, where `table[k][i]` holds the answer (say, the minimum) over the range starting at index `i` with length `2^k`. Row `k = 0` holds single elements. Row `k = 1` holds pairs. Row `k = 2` holds groups of four, and so on.

**The invariant.** `table[k][i] = combine(table[k-1][i], table[k-1][i + 2^(k-1)])` — a length-`2^k` range is exactly two length-`2^(k-1)` ranges glued together, so each row is built from the row below it.

**Why queries are `O(1)`.** For min/max, overlapping ranges do not corrupt the answer (`min(a, a) = a`), so any range `[l, r]` of length `len = r - l + 1` can be answered by picking `k = floor(log2(len))` and combining **two overlapping** precomputed ranges: `table[k][l]` (covering the first `2^k` elements) and `table[k][r - 2^k + 1]` (covering the last `2^k` elements). These two ranges always cover `[l, r]` completely, even though they overlap in the middle.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sparse table with rows for range lengths 1, 2, and 4, and a query answered by two overlapping precomputed ranges">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">k=0 (len 1):</text>
    <text x="10" y="60">k=1 (len 2):</text>
    <text x="10" y="100">k=2 (len 4):</text>

    <g>
      <rect x="140" y="8" width="34" height="20" fill="#0d1117" stroke="#8b949e"/><text x="157" y="22" text-anchor="middle" font-size="9">2</text>
      <rect x="174" y="8" width="34" height="20" fill="#0d1117" stroke="#8b949e"/><text x="191" y="22" text-anchor="middle" font-size="9">1</text>
      <rect x="208" y="8" width="34" height="20" fill="#0d1117" stroke="#8b949e"/><text x="225" y="22" text-anchor="middle" font-size="9">4</text>
      <rect x="242" y="8" width="34" height="20" fill="#0d1117" stroke="#8b949e"/><text x="259" y="22" text-anchor="middle" font-size="9">3</text>
      <rect x="276" y="8" width="34" height="20" fill="#0d1117" stroke="#8b949e"/><text x="293" y="22" text-anchor="middle" font-size="9">5</text>
    </g>
    <g>
      <rect x="140" y="48" width="68" height="20" fill="#161b22" stroke="#79c0ff"/><text x="174" y="62" text-anchor="middle" font-size="9">min=1</text>
      <rect x="208" y="48" width="68" height="20" fill="#161b22" stroke="#79c0ff"/><text x="242" y="62" text-anchor="middle" font-size="9">min=3</text>
      <rect x="276" y="48" width="34" height="20" fill="#161b22" stroke="#79c0ff"/>
    </g>
    <g>
      <rect x="140" y="88" width="136" height="20" fill="#21262d" stroke="#f0883e"/><text x="208" y="102" text-anchor="middle" font-size="9">min=1</text>
    </g>

    <text x="10" y="140" font-size="9" fill="#8b949e">query min[0,4] (length 5): k=floor(log2(5))=2</text>
    <text x="10" y="160" font-size="9" fill="#f0883e">= min(table[2][0], table[2][1]) = min(1, min(1,3,4,5))</text>
    <text x="10" y="180" font-size="9" fill="#8b949e">the two length-4 windows overlap at indices 1-3, but min() ignores duplicates safely</text>
  </g>
</svg>

Two overlapping precomputed windows, both size `2^k`, always cover the full query range.

## 5. Runnable example

```java
// SparseTable.java
public class SparseTable {

    // Basic: build a min sparse table and answer one query.
    static class MinSparseTable {
        int[][] table;
        int n;
        int[] log;

        MinSparseTable(int[] arr) {
            n = arr.length;
            log = new int[n + 1];
            for (int i = 2; i <= n; i++) log[i] = log[i / 2] + 1;

            int maxK = log[n] + 1;
            table = new int[maxK][n];
            table[0] = arr.clone();

            for (int k = 1; k < maxK; k++) {
                int len = 1 << k;
                for (int i = 0; i + len <= n; i++) {
                    table[k][i] = Math.min(table[k - 1][i], table[k - 1][i + len / 2]);
                }
            }
        }

        int queryMin(int l, int r) {
            int k = log[r - l + 1];
            return Math.min(table[k][l], table[k][r - (1 << k) + 1]);
        }
    }

    static void basicLevel() {
        MinSparseTable st = new MinSparseTable(new int[]{2, 1, 4, 3, 5});
        System.out.println("basic: min[0,4] -> " + st.queryMin(0, 4));
    }

    // Intermediate: reuse the same table shape for range MAX, showing the technique generalizes.
    static class MaxSparseTable {
        int[][] table;
        int[] log;

        MaxSparseTable(int[] arr) {
            int n = arr.length;
            log = new int[n + 1];
            for (int i = 2; i <= n; i++) log[i] = log[i / 2] + 1;

            int maxK = log[n] + 1;
            table = new int[maxK][n];
            table[0] = arr.clone();

            for (int k = 1; k < maxK; k++) {
                int len = 1 << k;
                for (int i = 0; i + len <= n; i++) {
                    table[k][i] = Math.max(table[k - 1][i], table[k - 1][i + len / 2]);
                }
            }
        }

        int queryMax(int l, int r) {
            int k = log[r - l + 1];
            return Math.max(table[k][l], table[k][r - (1 << k) + 1]);
        }
    }

    static void intermediateLevel() {
        MaxSparseTable st = new MaxSparseTable(new int[]{2, 1, 4, 3, 5});
        System.out.println("intermediate: max[1,3] -> " + st.queryMax(1, 3));
    }

    // Advanced: multiple queries against the same table, showing true O(1) per query after one O(n log n) build.
    static void advancedLevel() {
        int[] data = {7, 2, 9, 4, 1, 8, 3, 6, 5};
        MinSparseTable st = new MinSparseTable(data);

        int[][] queries = {{0, 8}, {2, 5}, {4, 4}, {1, 7}};
        for (int[] q : queries) {
            System.out.println("advanced: min[" + q[0] + "," + q[1] + "] -> " + st.queryMin(q[0], q[1]));
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java SparseTable.java`

## 6. Walkthrough

Build a min sparse table over `[2, 1, 4, 3, 5]`. Row `k=0` is the array itself. Row `k=1` (length-2 windows): `table[1][0] = min(2,1) = 1`, `table[1][1] = min(1,4) = 1`, `table[1][2] = min(4,3) = 3`, `table[1][3] = min(3,5) = 3`. Row `k=2` (length-4 windows): `table[2][0] = min(table[1][0], table[1][2]) = min(1, 3) = 1`.

Now query `min[0, 4]`. The range length is `5`, so `k = floor(log2(5)) = 2`, meaning window size `4`. Take `table[2][0]` (covers indices `0-3`) and `table[2][4 - 4 + 1] = table[2][1]` (covers indices `1-4`). Combine: `min(table[2][0], table[2][1]) = min(1, min(table[1][1], table[1][3])) = min(1, min(1,3)) = 1`. The two windows overlap on indices `1-3`, but since `min` is idempotent, the overlap causes no error.

**Complexity.** Build: `O(n log n)` time and space (one row per power of two, up to `log n` rows). Query: `O(1)`, since it is just two array lookups and one `min`/`max` call, after an `O(1)` lookup of `k` from the precomputed `log` array.

## 7. Gotchas & takeaways

> A sparse table only works for **idempotent** combine operations — `min`, `max`, `gcd`, bitwise AND/OR — where overlapping the same element twice does not change the answer. It does **not** work for sum, because summing an overlapping region double-counts those elements.

- The table is immutable after construction. Any update to the source array requires a full `O(n log n)` rebuild — unlike a [segment tree](0152-segment-tree-range-query-update.md), which updates in `O(log n)`.
- Precompute the `log` array once up front (`O(n)`), rather than calling `Math.log` per query, to keep queries genuinely `O(1)`.
- Choose a sparse table over a segment tree only when the array is truly static and you expect far more queries than any conceivable update.
