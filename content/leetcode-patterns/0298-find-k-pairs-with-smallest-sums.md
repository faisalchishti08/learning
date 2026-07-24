---
card: leetcode-patterns
gi: 298
slug: find-k-pairs-with-smallest-sums
title: Find K Pairs with Smallest Sums
---

## 1. What it is

Given two integer arrays `nums1` and `nums2`, both sorted ascending, and an integer `k`, return the `k` pairs `(nums1[i], nums2[j])` with the smallest sums. Example: `nums1 = [1,7,11]`, `nums2 = [2,4,6]`, `k = 3` → `[[1,2],[1,4],[1,6]]`.

## 2. Why & when

This problem hides a K-way Merge inside a pair-generation task: fix each index `i` in `nums1`, and the sequence of sums `nums1[i] + nums2[0], nums1[i] + nums2[1], ...` is itself sorted ascending, since `nums2` is sorted. That gives you up to `nums1.length` sorted sequences to merge. Use this shape whenever pairing two sorted arrays creates many IMPLICIT sorted sequences that would be wasteful to generate in full.

## 3. Core concept

**Key idea:** treat each starting index `i` in `nums1` as the head of a sorted sequence of pair-sums (pairing `nums1[i]` with `nums2[0], nums2[1], ...`). Merge across these sequences with a min-heap, generating pairs LAZILY, and stop after `k` pairs.

**Steps:**
1. Create a min-heap of `(sum, i, j)` triples, ordered by `sum`.
2. Seed the heap with pairs `(nums1[i], nums2[0])` for `i` from `0` up to `min(k, nums1.length) - 1` — you never need more than `k` starting sequences, since you will only ever pop `k` values total.
3. Pop the heap up to `k` times. Each pop yields the next-smallest pair. After popping `(i, j)`, push `(i, j+1)` if `j+1 < nums2.length`.
4. Collect each popped pair into the result.

**Why it is correct:** fixing `i` and increasing `j` always increases the sum, since `nums2` is sorted — so each `i` truly generates a sorted sequence of sums. The heap invariant from K-way Merge applies directly: the smallest sum not yet produced is always among the current heads of these sequences. Capping the seed at `min(k, nums1.length)` starting sequences is safe because you can never need a pair starting at `nums1[i]` for `i >= k` before exhausting `k` smaller-index pairs first (since `nums1` is sorted too, larger `i` means a larger base value).

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap merging sum sequences seeded from nums1 = 1,7,11 paired with nums2 index 0, popping the 3 smallest sums">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums1=[1,7,11], nums2=[2,4,6], k=3</text>
    <text x="10" y="45">seed heap: (1+2,0,0)=3, (7+2,1,0)=9, (11+2,2,0)=13</text>
    <text x="10" y="65">pop (1,2) sum=3 -&gt; push (1,4) sum=5</text>
    <text x="10" y="85">pop (1,4) sum=5 -&gt; push (1,6) sum=7</text>
    <text x="10" y="105">pop (1,6) sum=7 -&gt; k=3 pairs collected, stop</text>
    <rect x="10" y="120" width="220" height="24" fill="#3fb950"/><text x="120" y="137" fill="#0d1117" text-anchor="middle" font-size="10">[[1,2],[1,4],[1,6]]</text>
  </g>
</svg>

Each `i` seeds a sorted sum sequence (fixed `nums1[i]`, increasing `nums2[j]`); the heap merges across them.

## 5. Runnable example

```java
// KPairsWithSmallestSums.java
import java.util.*;

public class KPairsWithSmallestSums {

    // KEY INSIGHT: fixing i and increasing j produces a sorted sum
    // sequence, since nums2 is sorted -- merge across at most k such
    // sequences instead of generating all nums1.length * nums2.length
    // pairs and sorting them.

    static List<List<Integer>> kSmallestPairs(int[] nums1, int[] nums2, int k) {
        List<List<Integer>> result = new ArrayList<>();
        if (nums1.length == 0 || nums2.length == 0 || k == 0) return result;

        PriorityQueue<int[]> heap = new PriorityQueue<>(
            (a, b) -> (nums1[a[0]] + nums2[a[1]]) - (nums1[b[0]] + nums2[b[1]])
        );
        int seeds = Math.min(k, nums1.length);
        for (int i = 0; i < seeds; i++) {
            heap.offer(new int[]{i, 0});
        }

        while (k-- > 0 && !heap.isEmpty()) {
            int[] top = heap.poll();
            int i = top[0], j = top[1];
            result.add(Arrays.asList(nums1[i], nums2[j]));
            if (j + 1 < nums2.length) {
                heap.offer(new int[]{i, j + 1});
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(kSmallestPairs(new int[]{1, 7, 11}, new int[]{2, 4, 6}, 3));
        // [[1, 2], [1, 4], [1, 6]]
    }
}
```

**How to run:** `java KPairsWithSmallestSums.java`

## 6. Walkthrough

Trace `kSmallestPairs([1,7,11], [2,4,6], 3)`:

| pop # | popped (i,j) | sum | result so far | pushed next |
|---|---|---|---|---|
| 1 | (0,0) | 3 | [[1,2]] | (0,1) sum=5 |
| 2 | (0,1) | 5 | [[1,2],[1,4]] | (0,2) sum=7 |
| 3 | (0,2) | 7 | [[1,2],[1,4],[1,6]] | none, `k` reached, loop stops |

Final result: `[[1,2],[1,4],[1,6]]`. Time complexity is O(k log k): at most `k` seed sequences, and `k` pops each costing O(log k). Space is O(k), for the heap.

## 7. Gotchas & takeaways

> Gotcha: seeding the heap with ALL `nums1.length` starting sequences instead of capping at `min(k, nums1.length)` still gives a correct answer, but wastes memory and initial heap-build time when `nums1` is much longer than `k` — you can never need more than `k` distinct starting sequences to produce `k` pairs.

- This problem shows K-way Merge applied to an IMPLICIT set of sequences (generated lazily from two sorted arrays), not an explicit list of pre-built sequences.
- Only advancing `j` (never `i`) when pushing a replacement is deliberate: it guarantees each of the `k` (or fewer) seeded sequences stays independently sorted and never re-seeds a duplicate starting pair.
- Related problems: Kth Smallest Element in a Sorted Matrix (rows are the sequences instead of generated pair sums), Merge k Sorted Lists (explicit sequences instead of generated ones).
