---
card: leetcode-patterns
gi: 295
slug: k-way-merge-complexity-o-n-log-k-time
title: K-way Merge — complexity: O(n log k) time
---

## 1. What it is

This page pins down the time and space cost of the K-way Merge pattern, and lists the problems that use it. Knowing the exact complexity lets you justify, in an interview, why merging with a heap beats dumping everything into one array and sorting.

## 2. Why & when

Use this page as the reference point once you recognize the signal and the template. You still need to know exactly how much cheaper a k-way merge is compared to a full re-sort, so you can defend the choice and reason about the tradeoff as `k` grows.

## 3. Core concept

**Complexity.** Let `n` be the TOTAL number of elements across all `k` sequences. Each element is pushed to the heap exactly once and popped exactly once — that is `2n` heap operations total. The heap never holds more than `k` elements at a time, so each operation costs O(log k). Total time: O(n log k). Space: O(k), for the heap (plus O(n) for the output, if you materialize it).

**Compare against a full re-sort.** Concatenating all `k` sequences into one array of size `n` and sorting it costs O(n log n). Since `k ≤ n` always, `log k ≤ log n`, so the k-way merge is never worse, and is often dramatically better when `k` is small relative to `n` — for example, merging `k = 5` sorted lists of `200` elements each (`n = 1000`) costs about `1000 * log2(5) ≈ 2,322` comparisons via k-way merge, versus about `1000 * log2(1000) ≈ 9,966` for a full sort.

**When it stops helping.** If `k` approaches `n` (many very short sequences, e.g. `k = n` sequences of length 1), `log k` approaches `log n`, and the saving shrinks toward zero — at that extreme, a k-way merge and a full sort cost about the same.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bar comparison of full sort cost n log n versus k-way merge cost n log k for n=1000">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">n = 1000 total elements</text>
    <text x="10" y="45">Full sort:        O(n log n) -&gt; log2(1000) ~ 10</text>
    <rect x="10" y="55" width="300" height="18" fill="#8b949e"/>
    <text x="10" y="90">K-way merge, k=5: O(n log k) -&gt; log2(5) ~ 2.3</text>
    <rect x="10" y="100" width="70" height="18" fill="#3fb950"/>
  </g>
</svg>

The k-way merge's cost tracks `log k`, not `log n` — smaller `k` relative to `n` means a bigger saving.

## 5. Runnable example

```java
// KWayMergeComplexity.java
import java.util.PriorityQueue;

public class KWayMergeComplexity {

    // O(n log k): n total elements, each doing one O(log k) push
    // and one O(log k) pop, since the heap never exceeds size k.
    static int[] mergeKSortedArrays(int[][] arrays) {
        int total = 0;
        for (int[] arr : arrays) total += arr.length;

        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        for (int i = 0; i < arrays.length; i++) {
            if (arrays[i].length > 0) heap.offer(new int[]{arrays[i][0], i, 0});
        }

        int[] result = new int[total];
        int idx = 0;
        while (!heap.isEmpty()) {
            int[] top = heap.poll();               // O(log k)
            result[idx++] = top[0];
            int arrIdx = top[1], elemIdx = top[2] + 1;
            if (elemIdx < arrays[arrIdx].length) {
                heap.offer(new int[]{arrays[arrIdx][elemIdx], arrIdx, elemIdx}); // O(log k)
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int k = 5, lenEach = 200;
        int[][] arrays = new int[k][lenEach];
        for (int i = 0; i < k; i++) {
            for (int j = 0; j < lenEach; j++) arrays[i][j] = j * k + i;
        }

        long start = System.nanoTime();
        int[] merged = mergeKSortedArrays(arrays);
        long elapsed = System.nanoTime() - start;

        System.out.println("first 5: " + java.util.Arrays.toString(java.util.Arrays.copyOf(merged, 5)));
        System.out.println("total merged: " + merged.length);
        System.out.println("elapsed ms: " + elapsed / 1_000_000);
    }
}
```

**How to run:** `java KWayMergeComplexity.java`

## 6. Walkthrough

1. `n = 1000` (5 arrays of 200 elements each), `k = 5`.
2. Every element is pushed to the heap exactly once (`n` pushes) and popped exactly once (`n` pops) — `2n = 2000` heap operations total.
3. The heap never grows past `k = 5` elements, so each push or pop costs O(log 5), a small constant.
4. Total work: `2n` operations times O(log k) each — O(n log k).
5. Compare to sorting all `1000` elements directly: O(n log n) with `log n = log(1000) ≈ 10`, versus `log k = log(5) ≈ 2.3` — roughly four times fewer comparisons for the same merged result.

## 7. Gotchas & takeaways

> Gotcha: the O(n log k) bound assumes the heap comparator itself runs in O(1) — if your heap entries carry a linked-list node or array reference and the comparator does extra work (like comparing whole sub-arrays instead of one value), the true cost per operation can be higher than a simple `log k` factor suggests.

- K-way merge: O(n log k) time, O(k) space for the heap.
- Full re-sort: O(n log n) time — always at least as expensive, since `k ≤ n`.
- Problems using this pattern: Merge Two Sorted Lists, Kth Smallest Element in a Sorted Matrix, Find K Pairs with Smallest Sums, Ugly Number II, Super Ugly Number, Merge k Sorted Lists, Smallest Range Covering Elements from K Lists, Find K-th Smallest Pair Distance.
