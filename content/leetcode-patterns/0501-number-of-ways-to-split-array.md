---
card: leetcode-patterns
gi: 501
slug: number-of-ways-to-split-array
title: Number of Ways to Split Array
---

## 1. What it is

Given an array `nums`, count how many ways you can split it into two non-empty parts (a left part `nums[0..i]` and a right part `nums[i+1..n-1]`, for every possible split point `i`) such that the sum of the left part is greater than or equal to the sum of the right part. Example: `nums = [10, 4, -8, 7]` → `2`.

## 2. Why & when

"Sum of the left part" and "sum of the right part" at every possible split point are exactly what a running prefix sum and a total sum give you directly, from the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family — the same left/right-sum trick as [Find Pivot Index](0491-find-pivot-index.md). Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** compute the total sum once. Scan left to right, maintaining a running `leftSum`. At each split point `i` (splitting after index `i`), the right sum is `total - leftSum` (everything not yet included in `leftSum`). Check `leftSum >= total - leftSum` and count how many split points satisfy it.

**Steps:**
1. Compute `total = sum(nums)`.
2. Initialize `leftSum = 0` and `count = 0`.
3. For each index `i` from `0` to `n - 2` (the split must leave a non-empty right part): add `nums[i]` to `leftSum`.
4. Compute `rightSum = total - leftSum`. If `leftSum >= rightSum`, increment `count`.
5. Return `count` after scanning all valid split points.

**Why the loop stops at `n - 2` (not `n - 1`):** the split point `i` marks the end of the left part; the right part must contain at least one element, so `i` can be at most the second-to-last index — splitting after the very last index would leave the right part empty, which the problem disallows.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Running left sum compared against a right sum derived from the total, at every valid split point">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [10, 4, -8, 7], total = 13</text>
    <text x="20" y="45" fill="#8b949e">i=0: leftSum=10, rightSum=13-10=3. 10&gt;=3 -&gt; valid split</text>
    <text x="20" y="65" fill="#8b949e">i=1: leftSum=14, rightSum=13-14=-1. 14&gt;=-1 -&gt; valid split</text>
    <text x="20" y="85" fill="#3fb950">i=2: leftSum=6, rightSum=13-6=7. 6&gt;=7? no -&gt; not valid</text>
    <text x="20" y="110" fill="#79c0ff">total valid splits: 2</text>
  </g>
</svg>

The right sum is derived from the total minus the running left sum, needing no separate scan.

## 5. Runnable example

**Level 1 — Brute force.** For each split point, sum both halves directly. O(n²).

**KEY INSIGHT:** the right sum at any split point is always `total - leftSum`, so a single running variable and one precomputed total answer every split point in O(1) each.

**Level 2 — Optimal.** Running left sum with a derived right sum, O(n).

**Level 3 — Hardened.** Handles negative numbers and a 2-element array (only one possible split).

```java
// NumberOfWaysToSplitArray.java
public class NumberOfWaysToSplitArray {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums) {
        int n = nums.length;
        int count = 0;
        for (int i = 0; i < n - 1; i++) {
            long left = 0, right = 0;
            for (int j = 0; j <= i; j++) left += nums[j];
            for (int j = i + 1; j < n; j++) right += nums[j];
            if (left >= right) count++;
        }
        return count;
    }

    // Level 2 & 3: running left sum + derived right sum, O(n)
    static int waysToSplitArray(int[] nums) {
        long total = 0;
        for (int num : nums) total += num;

        long leftSum = 0;
        int count = 0;
        for (int i = 0; i < nums.length - 1; i++) {
            leftSum += nums[i];
            long rightSum = total - leftSum;
            if (leftSum >= rightSum) count++;
        }
        return count;
    }

    public static void main(String[] args) {
        int[] nums = {10, 4, -8, 7};
        System.out.println("brute force: " + bruteForce(nums));
        System.out.println("optimal:     " + waysToSplitArray(nums));

        System.out.println("two elements: " + waysToSplitArray(new int[]{2, 3}));
    }
}
```

**How to run:** save as `NumberOfWaysToSplitArray.java`, then run `java NumberOfWaysToSplitArray.java`.

## 6. Walkthrough

Trace `waysToSplitArray({10, 4, -8, 7})`, `total = 13`:

| i | nums[i] | leftSum after | rightSum = total-leftSum | leftSum >= rightSum? | count |
|---|---|---|---|---|---|
| 0 | 10 | 10 | 3 | yes | 1 |
| 1 | 4 | 14 | -1 | yes | 2 |
| 2 | -8 | 6 | 7 | no | 2 |

The loop stops before `i=3` (splitting there would leave no elements on the right). Final count: `2`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using `int` instead of `long` for the running sums can overflow on large arrays with large values — the constraints allow sums well beyond `int` range, so accumulate in `long`.

- The left/right-sum-from-total trick reused here is the same one used in [Find Pivot Index](0491-find-pivot-index.md), applied to an inequality instead of an equality.
- The loop must stop one index before the end, since the right part needs at least one element.
- Time: O(n) — one pass to compute the total, one pass to scan split points.
