---
card: leetcode-patterns
gi: 492
slug: range-sum-query-immutable
title: Range Sum Query - Immutable
---

## 1. What it is

Design a class `NumArray` that, given an integer array, answers many `sumRange(left, right)` queries — the sum of elements from index `left` to `right`, inclusive — efficiently. The array itself never changes ("immutable"). Example: `nums = [-2, 0, 3, -5, 2, -1]`, `sumRange(0, 2)` → `1`, `sumRange(2, 5)` → `-1`.

## 2. Why & when

This is the textbook use case for the [prefix-sum template](0488-prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma.md), array variant: precompute once in the constructor, then answer every `sumRange` call in O(1). Constraints: up to 10,000 elements, up to 10,000 queries.

## 3. Core concept

**Key idea:** in the constructor, build a prefix-sum array `prefixSum` where `prefixSum[i]` is the sum of `nums[0..i-1]`. Each `sumRange(left, right)` call then computes `prefixSum[right + 1] - prefixSum[left]`, a single subtraction.

**Steps:**
1. In the constructor, allocate `prefixSum` of size `n + 1`, with `prefixSum[0] = 0`.
2. Fill it: `prefixSum[i + 1] = prefixSum[i] + nums[i]`.
3. In `sumRange(left, right)`, return `prefixSum[right + 1] - prefixSum[left]`.

**Why this beats summing the range directly on every call:** without precomputing, each `sumRange` call costs O(range width), and repeated calls on overlapping ranges redo the same additions over and over. Precomputing once means every call, regardless of range width, costs the same O(1).

## 4. Diagram

<svg viewBox="0 0 700 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Prefix sum array built once in the constructor, queried repeatedly">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [-2, 0, 3, -5, 2, -1]</text>
    <text x="20" y="45" fill="#8b949e">prefixSum = [0, -2, -2, 1, -4, -2, -3]</text>
    <text x="20" y="70" fill="#79c0ff">sumRange(0,2) = prefixSum[3]-prefixSum[0] = 1-0 = 1</text>
    <text x="20" y="95" fill="#3fb950">sumRange(2,5) = prefixSum[6]-prefixSum[2] = -3-(-2) = -1</text>
  </g>
</svg>

Each query is a single subtraction against the array built once in the constructor.

## 5. Runnable example

**Level 1 — Brute force.** Recompute each `sumRange` by scanning the array directly. O(range width) per query.

**KEY INSIGHT:** since the array is immutable, the same prefix-sum array can be reused for every query — build it once in the constructor instead of rescanning on every call.

**Level 2 — Optimal.** Precomputed prefix-sum array, O(n) constructor, O(1) per query.

**Level 3 — Hardened.** Handles queries where `left == right` (single element) and a query spanning the whole array.

```java
// NumArray.java
public class NumArray {

    private final int[] prefixSum;

    // Level 2 & 3: build once, O(n)
    public NumArray(int[] nums) {
        prefixSum = new int[nums.length + 1];
        for (int i = 0; i < nums.length; i++) {
            prefixSum[i + 1] = prefixSum[i] + nums[i];
        }
    }

    // O(1) per query
    public int sumRange(int left, int right) {
        return prefixSum[right + 1] - prefixSum[left];
    }

    // Level 1: brute force reference, O(range width) per query
    static int bruteForceSumRange(int[] nums, int left, int right) {
        int sum = 0;
        for (int i = left; i <= right; i++) sum += nums[i];
        return sum;
    }

    public static void main(String[] args) {
        int[] nums = {-2, 0, 3, -5, 2, -1};
        NumArray numArray = new NumArray(nums);

        System.out.println("sumRange(0,2): " + numArray.sumRange(0, 2)
            + " (brute force: " + bruteForceSumRange(nums, 0, 2) + ")");
        System.out.println("sumRange(2,5): " + numArray.sumRange(2, 5)
            + " (brute force: " + bruteForceSumRange(nums, 2, 5) + ")");
        System.out.println("sumRange(0,5): " + numArray.sumRange(0, 5));
        System.out.println("sumRange(3,3): " + numArray.sumRange(3, 3));
    }
}
```

**How to run:** save as `NumArray.java`, then run `java NumArray.java`.

## 6. Walkthrough

`prefixSum` for `{-2, 0, 3, -5, 2, -1}`: `[0, -2, -2, 1, -4, -2, -3]` (each entry adds the next `nums` value to the previous entry).

| query | formula | result |
|---|---|---|
| sumRange(0, 2) | prefixSum[3] - prefixSum[0] = 1 - 0 | 1 |
| sumRange(2, 5) | prefixSum[6] - prefixSum[2] = -3 - (-2) | -1 |
| sumRange(0, 5) | prefixSum[6] - prefixSum[0] = -3 - 0 | -3 |
| sumRange(3, 3) | prefixSum[4] - prefixSum[3] = -4 - 1 | -5 |

Every query matches the direct brute-force sum, but each costs only one subtraction.

## 7. Gotchas & takeaways

> Gotcha: rebuilding the prefix-sum array inside `sumRange` instead of the constructor throws away the whole benefit of precomputing — the array is immutable, so building it once and reusing it for every query is both correct and necessary for O(1) queries.

- The "Immutable" in the problem name is the signal: since the array never changes, one upfront O(n) build pays for unlimited O(1) queries.
- `sumRange(i, i)` (a single element) still uses the same formula — no special case needed.
- Time: O(n) constructor, O(1) per query; space: O(n) for the prefix-sum array.
