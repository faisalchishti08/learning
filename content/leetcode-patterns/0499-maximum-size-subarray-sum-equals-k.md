---
card: leetcode-patterns
gi: 499
slug: maximum-size-subarray-sum-equals-k
title: Maximum Size Subarray Sum Equals k
---

## 1. What it is

Given an array `nums` and a target `k`, find the length of the **longest** contiguous subarray that sums to exactly `k`. Return `0` if no such subarray exists. Example: `nums = [1, -1, 5, -2, 3]`, `k = 3` → `4` (the subarray `[1, -1, 5, -2]` sums to `3`).

## 2. Why & when

This is [Subarray Sum Equals K](0493-subarray-sum-equals-k.md), but asking for the longest match instead of counting all matches — the same distinction as between [Contiguous Array](0494-contiguous-array.md) (longest span) and [Subarray Sum Equals K](0493-subarray-sum-equals-k.md) (count). It belongs to the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family, using a hash map of the *first* index for each prefix sum. Constraints: up to 200,000 elements, values can be negative.

## 3. Core concept

**Key idea:** scan left to right, maintaining a running sum and a hash map from "prefix sum value" to "the first index where it occurred." A subarray `nums[i+1..j]` sums to `k` exactly when `prefixSum[j] - prefixSum[i] = k`, i.e. `prefixSum[i] = prefixSum[j] - k`. For the longest such subarray, always use the *earliest* index with that value, maximizing `j - i`.

**Steps:**
1. Initialize `firstIndexOf = {0: -1}` (the empty prefix, so subarrays starting at index 0 are measured correctly).
2. Scan the array, maintaining `runningSum`.
3. At each index `j`: if `firstIndexOf` contains `runningSum - k`, this subarray's length is `j - firstIndexOf.get(runningSum - k)`. Update the maximum length if this is longer.
4. Only record `firstIndexOf[runningSum] = j` if `runningSum` has not been seen before (preserving the earliest occurrence).
5. Return the maximum length found (or `0` if none).

**Why only recording the first occurrence is essential for the "maximum size" variant:** a later occurrence of the same prefix sum value would only produce a shorter subarray when matched against future indices — the first occurrence always gives the widest possible span.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Matching a target-shifted prefix sum against the earliest occurrence for the longest span">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, -1, 5, -2, 3], k = 3</text>
    <text x="20" y="45" fill="#8b949e">firstIndexOf = {0: -1}. runningSum=0.</text>
    <text x="20" y="65" fill="#8b949e">j=0 (1): sum=1. lookup 1-3=-2: absent. store {1:0}</text>
    <text x="20" y="85" fill="#8b949e">j=1 (-1): sum=0. lookup 0-3=-3: absent. sum=0 already in map, do not overwrite.</text>
    <text x="20" y="105" fill="#8b949e">j=2 (5): sum=5. lookup 5-3=2: absent. store {5:2}</text>
    <text x="20" y="130" fill="#3fb950">j=3 (-2): sum=3. lookup 3-3=0: found at index -1! length=3-(-1)=4. maxLen=4</text>
  </g>
</svg>

The earliest occurrence of `runningSum - k` gives the longest possible span ending at the current index.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray, sum it directly and check against `k`, tracking the longest match. O(n²).

**KEY INSIGHT:** the widest subarray summing to `k` ending at any index always pairs with the *earliest* matching prefix — so the hash map must never overwrite an existing entry.

**Level 2 — Optimal.** Running sum with a first-occurrence hash map, O(n).

**Level 3 — Hardened.** Handles no valid subarray (`0`) and negative numbers throughout.

```java
// MaximumSizeSubarraySumEqualsK.java
import java.util.*;

public class MaximumSizeSubarraySumEqualsK {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums, int k) {
        int maxLen = 0;
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum == k) maxLen = Math.max(maxLen, j - i + 1);
            }
        }
        return maxLen;
    }

    // Level 2 & 3: running sum + first-occurrence hash map, O(n)
    static int maxSubArrayLen(int[] nums, int k) {
        Map<Integer, Integer> firstIndexOf = new HashMap<>();
        firstIndexOf.put(0, -1);
        int runningSum = 0;
        int maxLen = 0;

        for (int j = 0; j < nums.length; j++) {
            runningSum += nums[j];
            if (firstIndexOf.containsKey(runningSum - k)) {
                maxLen = Math.max(maxLen, j - firstIndexOf.get(runningSum - k));
            }
            firstIndexOf.putIfAbsent(runningSum, j);
        }
        return maxLen;
    }

    public static void main(String[] args) {
        int[] nums = {1, -1, 5, -2, 3};
        System.out.println("brute force: " + bruteForce(nums, 3));
        System.out.println("optimal:     " + maxSubArrayLen(nums, 3));

        System.out.println("no match: " + maxSubArrayLen(new int[]{1, 2, 3}, 100));
        System.out.println("negatives: " + maxSubArrayLen(new int[]{-2, -1, 2, 1}, 1));
    }
}
```

**How to run:** save as `MaximumSizeSubarraySumEqualsK.java`, then run `java MaximumSizeSubarraySumEqualsK.java`.

## 6. Walkthrough

Trace `maxSubArrayLen({1, -1, 5, -2, 3}, 3)`, `firstIndexOf = {0: -1}` initially:

| j | nums[j] | runningSum | lookup (sum-k) | found? | maxLen | firstIndexOf update |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | -2 | no | 0 | put 1→0 |
| 1 | -1 | 0 | -3 | no | 0 | 0 already present, skip |
| 2 | 5 | 5 | 2 | no | 0 | put 5→2 |
| 3 | -2 | 3 | 0 | yes, at -1 | 3-(-1)=4 | 3 not present, put 3→3 |
| 4 | 3 | 6 | 3 | yes, at 3 | max(4, 4-3=1)=4 | put 6→4 |

Final `maxLen = 4`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using `put` instead of `putIfAbsent` overwrites an earlier, more useful index with a later one, shrinking future matches — always preserve the first occurrence when the goal is maximum length.

- This is the "longest match" sibling of [Subarray Sum Equals K](0493-subarray-sum-equals-k.md): same lookup logic, but store first-seen index instead of a running count.
- Seed the map with `{0: -1}` so subarrays starting at index 0 are measured correctly.
- Time: O(n) — one pass, O(1) amortized hash map operations per step.
