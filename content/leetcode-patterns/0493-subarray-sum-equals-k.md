---
card: leetcode-patterns
gi: 493
slug: subarray-sum-equals-k
title: Subarray Sum Equals K
---

## 1. What it is

Given an array `nums` and an integer `k`, return the total number of contiguous subarrays whose sum equals `k`. The array can contain negative numbers, so a sliding window will not work directly. Example: `nums = [1, 1, 1]`, `k = 2` → `2` (subarrays `[1,1]` at positions 0-1 and 1-2).

## 2. Why & when

"Count subarrays with a given sum" is the flagship use case for the hash-map half of the [prefix-sum template](0488-prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma.md). Because negative numbers are allowed, a sliding window (which relies on shrinking or growing monotonically) cannot be used — prefix sums with a hash map work regardless of sign. Constraints: up to 20,000 elements.

## 3. Core concept

**Key idea:** a subarray `nums[i+1..j]` sums to `k` exactly when `prefixSum[j] - prefixSum[i] = k`, i.e. `prefixSum[i] = prefixSum[j] - k`. Scan left to right, maintaining a running sum and a hash map counting how many times each prefix sum value has appeared so far. At each step, look up `runningSum - k` in the map — that count is exactly the number of earlier prefixes that complete a subarray summing to `k` ending here.

**Steps:**
1. Initialize `seenCount = {0: 1}` (the empty prefix, for subarrays starting at index 0) and `runningSum = 0`, `count = 0`.
2. For each element: add it to `runningSum`.
3. Add `seenCount.getOrDefault(runningSum - k, 0)` to `count`.
4. Increment `seenCount[runningSum]` by 1.
5. Return `count` after the full scan.

**Why the order (lookup before update) matters:** you must check for `runningSum - k` *before* recording the current `runningSum` in the map, otherwise a subarray of length 0 (a prefix matching itself, when `k = 0`) would be miscounted as matching against itself.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Running sum checked against a hash map of previously seen prefix sums">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 1, 1], k = 2</text>
    <text x="20" y="45" fill="#8b949e">map={0:1}. i=0 (1): runningSum=1. lookup 1-2=-1: 0. count=0. map={0:1,1:1}</text>
    <text x="20" y="65" fill="#8b949e">i=1 (1): runningSum=2. lookup 2-2=0: found count=1 -&gt; count=1. map={0:1,1:1,2:1}</text>
    <text x="20" y="90" fill="#3fb950">i=2 (1): runningSum=3. lookup 3-2=1: found count=1 -&gt; count=2. map={...,3:1}</text>
    <text x="20" y="120" fill="#79c0ff">final count = 2 (subarrays [1,1] at positions 0-1 and 1-2)</text>
  </g>
</svg>

Each new prefix sum is checked against the map before being recorded, finding every earlier prefix that completes a sum-to-`k` subarray.

## 5. Runnable example

**Level 1 — Brute force.** For every pair of start and end indices, sum the subarray directly and check against `k`. O(n²).

**KEY INSIGHT:** rewriting "subarray sums to k" as "does an earlier prefix sum equal the current prefix sum minus k" turns the search into a single hash map lookup per element.

**Level 2 — Optimal.** Running prefix sum + hash map of counts, O(n).

**Level 3 — Hardened.** Handles negative numbers and `k = 0` (counting subarrays that sum to zero).

```java
// SubarraySumEqualsK.java
import java.util.*;

public class SubarraySumEqualsK {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums, int k) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum == k) count++;
            }
        }
        return count;
    }

    // Level 2 & 3: prefix sum + hash map, O(n)
    static int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> seenCount = new HashMap<>();
        seenCount.put(0, 1);
        int runningSum = 0;
        int count = 0;

        for (int num : nums) {
            runningSum += num;
            count += seenCount.getOrDefault(runningSum - k, 0);
            seenCount.merge(runningSum, 1, Integer::sum);
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(bruteForce(new int[]{1, 1, 1}, 2));        // 2
        System.out.println(subarraySum(new int[]{1, 1, 1}, 2));       // 2
        System.out.println(subarraySum(new int[]{1, -1, 0}, 0));      // 3 (negatives handled)
        System.out.println(subarraySum(new int[]{1, 2, 3}, 100));     // 0
    }
}
```

**How to run:** save as `SubarraySumEqualsK.java`, then run `java SubarraySumEqualsK.java`.

## 6. Walkthrough

Trace `subarraySum({1, 1, 1}, 2)`:

| num | runningSum before | runningSum after | lookup (runningSum-k) | found count | count after | map after |
|---|---|---|---|---|---|---|
| 1 | 0 | 1 | 1-2=-1 | 0 | 0 | {0:1, 1:1} |
| 1 | 1 | 2 | 2-2=0 | 1 | 1 | {0:1, 1:1, 2:1} |
| 1 | 2 | 3 | 3-2=1 | 1 | 2 | {0:1, 1:1, 2:1, 3:1} |

Final count: `2`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using this problem's technique but trying to also track sliding-window boundaries (like the two-pointer pattern) fails whenever `nums` contains negative numbers — growing or shrinking a window is not monotonic when values can be negative, so the hash-map prefix-sum approach is required instead.

- "Count subarrays with sum k" (negatives allowed) is solved by hashing prefix sums, not by a sliding window.
- Always seed the map with `{0: 1}` and look up before updating, in that order.
- Time: O(n) — one pass, O(1) amortized hash map operations per step.
