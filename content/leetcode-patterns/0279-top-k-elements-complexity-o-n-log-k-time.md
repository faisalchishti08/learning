---
card: leetcode-patterns
gi: 279
slug: top-k-elements-complexity-o-n-log-k-time
title: Top-K Elements — complexity: O(n log k) time
---

## 1. What it is

This page pins down the time and space cost of the Top-K Elements pattern, and lists the problems that use it. Knowing the exact complexity lets you justify, in an interview, why a heap beats a full sort.

## 2. Why & when

Use this page as the reference point once you already recognize the signal and the template. You still need to know exactly how much cheaper the size-k heap or bucket-sort approach is compared to sorting everything, so you can defend the choice and spot when `k` is large enough that the saving disappears.

## 3. Core concept

**Size-k heap complexity.** Each of the `n` elements is offered to the heap once. A heap of size `k` performs each insert or removal in O(log k) time. Total time: O(n log k). Space: O(k), for the heap itself.

**Bucket-sort-by-frequency complexity.** Counting occurrences is one O(n) pass over the input. Placing each of the up-to-`n` distinct values into its bucket is O(n). Reading buckets from high to low, until `k` values are collected, visits at most `n` bucket slots. Total time: O(n). Space: O(n), for the count map and the bucket array.

**Compare against sorting.** Sorting the whole array costs O(n log n) and then slicing the last `k` is O(1). When `k` is small (say, `k = 10` out of `n = 1,000,000`), O(n log k) is dramatically cheaper than O(n log n), since `log k` is tiny next to `log n`. When `k` approaches `n`, the saving shrinks — `log k` approaches `log n`, and a plain sort becomes just as good, and simpler to write.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bar comparison of sorting cost n log n versus heap cost n log k, showing the heap approach shrinking as k gets smaller">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">n = 1,000,000 elements</text>
    <text x="10" y="45">Full sort:      O(n log n)  -&gt; log2(1,000,000) ~ 20</text>
    <rect x="10" y="55" width="300" height="18" fill="#8b949e"/>
    <text x="10" y="90">Heap, k=10:     O(n log k)  -&gt; log2(10) ~ 3.3</text>
    <rect x="10" y="100" width="50" height="18" fill="#3fb950"/>
    <text x="10" y="135">Bucket sort:    O(n)        -&gt; no log factor at all</text>
    <rect x="10" y="145" width="15" height="18" fill="#58a6ff"/>
  </g>
</svg>

The heap's cost tracks `log k`, not `log n` — the smaller `k` is relative to `n`, the bigger the saving over a full sort.

## 5. Runnable example

```java
// TopKComplexity.java
import java.util.PriorityQueue;

public class TopKComplexity {

    // O(n log k): each of n elements does one O(log k) heap operation.
    static int[] kLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int num : nums) {
            heap.offer(num);           // O(log k)
            if (heap.size() > k) {
                heap.poll();            // O(log k)
            }
        }
        int[] out = new int[heap.size()];
        for (int i = out.length - 1; i >= 0; i--) out[i] = heap.poll();
        return out;
    }

    public static void main(String[] args) {
        int[] nums = new int[100_000];
        for (int i = 0; i < nums.length; i++) nums[i] = (i * 37) % 100_000;

        long start = System.nanoTime();
        int[] top5 = kLargest(nums, 5);
        long elapsed = System.nanoTime() - start;

        System.out.println(java.util.Arrays.toString(top5));
        // [99995, 99996, 99997, 99998, 99999]
        System.out.println("elapsed ms: " + elapsed / 1_000_000);
    }
}
```

**How to run:** `java TopKComplexity.java`

## 6. Walkthrough

1. The loop runs `n = 100,000` times, once per element.
2. Each iteration does at most two heap operations (`offer`, and sometimes `poll`), and the heap never grows past `k = 5`, so each operation costs O(log 5), a small constant.
3. Total work is `n` iterations times a constant-ish O(log k) cost per iteration: O(n log k).
4. Compare this to sorting all `100,000` numbers first: that would cost O(n log n), with `log n = log(100,000) ≈ 17` instead of `log k = log 5 ≈ 2.3` — roughly seven times more comparisons for no extra benefit, since only the top 5 values were ever needed.
5. Draining the heap at the end costs O(k log k), negligible next to the O(n log k) scan.

## 7. Gotchas & takeaways

> Gotcha: if `k` is close to `n` (for example, `k = n / 2`), the O(n log k) heap approach offers almost no saving over an O(n log n) sort, and the sort is simpler code with less room for off-by-one heap bugs. Reach for the heap specifically when `k` is small relative to `n`.

- Size-k heap: O(n log k) time, O(k) space.
- Frequency bucket sort: O(n) time, O(n) space — faster than any heap when ranking by count.
- Problems using this pattern: Top K Frequent Elements, Kth Largest Element in an Array, K Closest Points to Origin, Sort Characters By Frequency, Kth Largest Element in a Stream, Task Scheduler, Reorganize String, Least Number of Unique Integers after K Removals, Top K Frequent Words.
