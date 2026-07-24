---
card: leetcode-patterns
gi: 297
slug: kth-smallest-element-in-a-sorted-matrix
title: Kth Smallest Element in a Sorted Matrix
---

## 1. What it is

Given an `n x n` matrix where every ROW and every COLUMN is sorted ascending, and an integer `k`, return the `k`-th smallest element in the matrix. Example: `matrix = [[1,5,9],[10,11,13],[12,13,15]]`, `k = 8` → `13`.

## 2. Why & when

Each row of the matrix is itself a sorted sequence, which makes this a direct K-way Merge, with `k` here meaning "number of rows" (do not confuse this with the problem's OWN `k`, the desired rank). Use this shape whenever a 2D structure has each row (or column) individually sorted, and you need a rank across the whole structure.

## 3. Core concept

**Key idea:** treat each row as one sequence in a k-way merge. Seed a min-heap with the first element of every row, then pop `k` times — the `k`-th pop is the answer.

**Steps:**
1. Create a min-heap of `(value, row, col)` triples.
2. Push `matrix[row][0]` for every row (the first column holds the smallest value in each row, since rows are sorted).
3. Pop the heap `k` times. On each pop, if the popped cell has a next column (`col + 1 < n`), push `matrix[row][col+1]`.
4. The value from the `k`-th pop is the answer.

**Why it is correct:** rows are sorted, so a row's un-popped elements are always at least as large as its current head — exactly the K-way Merge invariant, with `n` rows playing the role of `n` sorted sequences. Popping the heap's minimum `k` times, in order, produces the `k` smallest values across the whole matrix in increasing order; the `k`-th one popped is, by definition, the `k`-th smallest overall.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap merging 3 sorted matrix rows, popping 8 times to find the 8th smallest value">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">matrix rows: [1,5,9], [10,11,13], [12,13,15], k=8</text>
    <text x="10" y="45">seed heap with column-0 values: [1, 10, 12]</text>
    <text x="10" y="65">pop 1(row0) push 5 -&gt; pop 5(row0) push 9 -&gt; pop 9(row0), row0 exhausted</text>
    <text x="10" y="85">pop 10(row1) push 11 -&gt; pop 11(row1) push 13a -&gt; pop 12(row2) push 13b</text>
    <text x="10" y="105">pops so far: 1,5,9,10,11,12  (6 pops) -&gt; pop 7: 13a -&gt; pop 8: 13b</text>
    <rect x="10" y="120" width="180" height="24" fill="#3fb950"/><text x="100" y="137" fill="#0d1117" text-anchor="middle" font-size="10">8th smallest = 13</text>
  </g>
</svg>

Each row supplies its next element only after its current head has been popped, exactly like a k-way merge across `n` sequences.

## 5. Runnable example

```java
// KthSmallestInSortedMatrix.java
import java.util.PriorityQueue;

public class KthSmallestInSortedMatrix {

    // Level 1 -- Brute force: flatten the matrix into an array, sort
    // it, return index k-1. Correct, but O(n^2 log(n^2)), ignoring
    // that every row already arrives sorted.

    // KEY INSIGHT: each row is a sorted sequence -- merge across rows
    // with a min-heap, popping exactly k times, instead of sorting
    // every element in the matrix.

    // Level 2 -- Optimal: k-way merge across rows, O(k log n).
    static int kthSmallest(int[][] matrix, int k) {
        int n = matrix.length;
        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        for (int row = 0; row < n; row++) {
            heap.offer(new int[]{matrix[row][0], row, 0});
        }

        int result = -1;
        for (int i = 0; i < k; i++) {
            int[] top = heap.poll();
            result = top[0];
            int row = top[1], col = top[2] + 1;
            if (col < n) {
                heap.offer(new int[]{matrix[row][col], row, col});
            }
        }
        return result;
    }

    // Level 3 -- Hardened: works when k == 1 (returns matrix[0][0]
    // immediately, the smallest possible value) and when k equals
    // n*n (returns the matrix's overall largest value, the last pop).

    public static void main(String[] args) {
        int[][] matrix = {{1, 5, 9}, {10, 11, 13}, {12, 13, 15}};
        System.out.println(kthSmallest(matrix, 8));
        // 13
    }
}
```

**How to run:** `java KthSmallestInSortedMatrix.java`

## 6. Walkthrough

Trace `kthSmallest(matrix, 8)` with `matrix = [[1,5,9],[10,11,13],[12,13,15]]`:

| pop # | popped value | row | pushed next |
|---|---|---|---|
| 1 | 1 | 0 | 5 |
| 2 | 5 | 0 | 9 |
| 3 | 9 | 0 | (row 0 exhausted) |
| 4 | 10 | 1 | 11 |
| 5 | 11 | 1 | 13 (row 1) |
| 6 | 12 | 2 | 13 (row 2) |
| 7 | 13 (row 1) | 1 | (row 1 exhausted) |
| 8 | 13 (row 2) | 2 | (row 2 exhausted) |

The 8th pop is `13`, the answer. Time complexity is O(k log n): `k` pops, each an O(log n) heap operation, since the heap never exceeds `n` entries (one per row). Space is O(n), for the heap.

## 7. Gotchas & takeaways

> Gotcha: only column advancement matters here — the matrix being sorted by COLUMN too (not just by row) is NOT used by this algorithm at all; it is extra information the problem provides but the row-based k-way merge does not need.

- This problem's `k` (the desired rank) is unrelated to the K-way Merge pattern's `k` (the number of sequences, here `n` rows) — do not conflate the two.
- A binary-search-on-value alternative also solves this in O(n log(max-min)), useful when `k` is very large relative to `n`; the heap approach is simpler to derive and reason about correctly.
- Related problems: Merge k Sorted Lists (the same row-as-sequence idea, applied to linked lists), Kth Largest Element in an Array (a flat, non-matrix version of a rank query).
