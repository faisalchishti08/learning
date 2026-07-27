---
card: leetcode-patterns
gi: 491
slug: find-pivot-index
title: Find Pivot Index
---

## 1. What it is

Find the leftmost index in `nums` where the sum of all elements strictly to its left equals the sum of all elements strictly to its right. Return `-1` if no such index exists. Example: `nums = [1, 7, 3, 6, 5, 6]` → `3` (left sum `1+7+3=11`, right sum `5+6=11`).

## 2. Why & when

"Sum of everything to the left" and "sum of everything to the right" are both prefix-sum-shaped quantities, part of the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family. Rather than recomputing both sides for every candidate index, track a running left sum and derive the right sum from the total. Constraints: up to 10,000 elements.

## 3. Core concept

**Key idea:** compute the total sum of the array once. Scan left to right, maintaining `leftSum` (sum of everything strictly before the current index). At each index `i`, the right sum is `total - leftSum - nums[i]` (everything except the left part and the element itself). If `leftSum` equals that right sum, `i` is the pivot.

**Steps:**
1. Compute `total = sum(nums)`.
2. Initialize `leftSum = 0`.
3. For each index `i`: compute `rightSum = total - leftSum - nums[i]`. If `leftSum == rightSum`, return `i`.
4. Otherwise, add `nums[i]` to `leftSum` and continue.
5. If the scan finishes with no match, return `-1`.

**Why deriving the right sum avoids a second pass:** the total sum is fixed; subtracting the left sum and the current element from it gives exactly the right sum, without ever summing the right side directly.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Running left sum compared against a right sum derived from the total">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 7, 3, 6, 5, 6], total = 28</text>
    <text x="20" y="45" fill="#8b949e">i=0: leftSum=0, rightSum=28-0-1=27. not equal.</text>
    <text x="20" y="65" fill="#8b949e">i=1: leftSum=1, rightSum=28-1-7=20. not equal.</text>
    <text x="20" y="85" fill="#8b949e">i=2: leftSum=8, rightSum=28-8-3=17. not equal.</text>
    <text x="20" y="105" fill="#3fb950">i=3: leftSum=11, rightSum=28-11-6=11. EQUAL -&gt; pivot index 3</text>
  </g>
</svg>

The right sum is derived from the total each step, never recomputed by scanning forward.

## 5. Runnable example

**Level 1 — Brute force.** For each index, sum everything to its left and everything to its right directly. O(n²).

**KEY INSIGHT:** the right sum at any index is always `total - leftSum - nums[i]`, so only one running variable (`leftSum`) and one precomputed constant (`total`) are needed — no repeated summation.

**Level 2 — Optimal.** Single pass with a running left sum and a derived right sum, O(n).

**Level 3 — Hardened.** Handles no valid pivot (`-1`), and a pivot at index 0 (left sum is 0).

```java
// FindPivotIndex.java
public class FindPivotIndex {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums) {
        for (int i = 0; i < nums.length; i++) {
            int left = 0, right = 0;
            for (int j = 0; j < i; j++) left += nums[j];
            for (int j = i + 1; j < nums.length; j++) right += nums[j];
            if (left == right) return i;
        }
        return -1;
    }

    // Level 2 & 3: running left sum + derived right sum, O(n)
    static int pivotIndex(int[] nums) {
        int total = 0;
        for (int num : nums) total += num;

        int leftSum = 0;
        for (int i = 0; i < nums.length; i++) {
            int rightSum = total - leftSum - nums[i];
            if (leftSum == rightSum) return i;
            leftSum += nums[i];
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(bruteForce(new int[]{1, 7, 3, 6, 5, 6})); // 3
        System.out.println(pivotIndex(new int[]{1, 7, 3, 6, 5, 6})); // 3
        System.out.println(pivotIndex(new int[]{1, 2, 3}));           // -1
        System.out.println(pivotIndex(new int[]{2, 1, -1}));          // 0 (leftSum=0, rightSum=1-1=0)
    }
}
```

**How to run:** save as `FindPivotIndex.java`, then run `java FindPivotIndex.java`.

## 6. Walkthrough

Trace `pivotIndex({1, 7, 3, 6, 5, 6})`, `total = 28`:

| i | nums[i] | leftSum before | rightSum = total-leftSum-nums[i] | match? | leftSum after |
|---|---|---|---|---|---|
| 0 | 1 | 0 | 28-0-1=27 | no | 1 |
| 1 | 7 | 1 | 28-1-7=20 | no | 8 |
| 2 | 3 | 8 | 28-8-3=17 | no | 11 |
| 3 | 6 | 11 | 28-11-6=11 | **yes** | — |

Returns `3`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: adding `nums[i]` to `leftSum` before computing `rightSum` for that same index counts the current element on both sides, always giving a wrong (too-small) right sum — compute `rightSum` first, then update `leftSum`.

- "Sum to the left equals sum to the right" is answered with one running variable and one precomputed total — no second array or nested loop needed.
- The pivot at index 0 is valid whenever `leftSum = 0` equals the derived right sum; do not special-case it.
- Time: O(n) — one pass to compute the total, one pass to scan for the pivot.
