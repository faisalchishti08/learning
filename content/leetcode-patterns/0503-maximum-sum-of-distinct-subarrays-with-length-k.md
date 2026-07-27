---
card: leetcode-patterns
gi: 503
slug: maximum-sum-of-distinct-subarrays-with-length-k
title: Maximum Sum of Distinct Subarrays With Length K
---

## 1. What it is

Given an integer array `nums` and an integer `k`, find the maximum sum of any subarray of exactly length `k` whose elements are all **distinct** (no repeated value within that window). Return `0` if no such subarray exists. Example: `nums = [1, 5, 4, 2, 9, 9, 9]`, `k = 3` → `15` (the subarray `[4, 2, 9]` is distinct and sums to `15`, the best among all distinct length-3 windows).

## 2. Why & when

A fixed-length window's sum is a direct prefix-sum-style computation: `windowSum = runningSum - runningSum from k steps ago`, from the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family. Layer a frequency map on top to track distinctness inside the window, and you get a sliding window that maintains both a running sum and a running "all distinct" check in O(1) amortized per step. Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** slide a window of exactly `k` elements across the array. Maintain `windowSum` (the current window's total) and a frequency map of elements currently inside the window. When the window is full (`k` elements) and every element inside has frequency `1` (all distinct), check whether `windowSum` beats the best sum seen so far.

**Steps:**
1. Maintain `windowSum = 0`, a frequency map, and `maxSum = 0`.
2. Scan `nums` with index `i`: add `nums[i]` to `windowSum` and increment its frequency in the map.
3. If the window exceeds size `k` (i.e. `i >= k`), remove the element leaving the window (`nums[i - k]`): subtract it from `windowSum` and decrement its frequency (removing the entry if it drops to `0`).
4. Once the window has exactly `k` elements, check if the frequency map's size equals `k` (meaning every element inside is distinct — no repeats). If so, update `maxSum = max(maxSum, windowSum)`.
5. Return `maxSum`.

**Why checking `map.size() == k` (not scanning the whole window) detects distinctness in O(1):** the frequency map only ever contains entries for elements currently in the window. If every element appears exactly once, the number of distinct keys equals the window size `k` — no repeated element can exist without shrinking that count below `k`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sliding window of fixed length k tracking both a running sum and element distinctness">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 5, 4, 2, 9, 9, 9], k = 3</text>
    <text x="20" y="45" fill="#8b949e">window [1,5,4]: sum=10, distinct (3 unique) -&gt; candidate 10</text>
    <text x="20" y="65" fill="#8b949e">window [5,4,2]: sum=11, distinct -&gt; candidate 11</text>
    <text x="20" y="85" fill="#3fb950">window [4,2,9]: sum=15, distinct -&gt; candidate 15 (new max)</text>
    <text x="20" y="110" fill="#f0883e">window [2,9,9]: sum=20, but map.size()=2 &lt; 3 (9 repeats) -&gt; skip</text>
    <text x="20" y="135" fill="#8b949e">window [9,9,9]: sum=27, map.size()=1 &lt; 3 -&gt; skip</text>
    <text x="20" y="155" fill="#3fb950">final answer: 15</text>
  </g>
</svg>

Each window's sum updates in O(1); a frequency map's size check confirms distinctness without rescanning the window.

## 5. Runnable example

**Level 1 — Brute force.** For each window of length `k`, sum it and check distinctness with a fresh set. O(n·k).

**KEY INSIGHT:** sliding the window one step at a time updates both the sum and the frequency map in O(1) amortized, instead of rebuilding them from scratch for every window.

**Level 2 — Optimal.** Sliding window with a running sum and a frequency map, O(n).

**Level 3 — Hardened.** Handles no valid window (all windows have repeats, answer `0`) and `k` equal to the array length.

```java
// MaximumSumOfDistinctSubarrays.java
import java.util.*;

public class MaximumSumOfDistinctSubarrays {

    // Level 1: brute force, O(n * k)
    static long bruteForce(int[] nums, int k) {
        long maxSum = 0;
        for (int i = 0; i + k <= nums.length; i++) {
            Set<Integer> seen = new HashSet<>();
            long sum = 0;
            boolean allDistinct = true;
            for (int j = i; j < i + k; j++) {
                if (!seen.add(nums[j])) { allDistinct = false; break; }
                sum += nums[j];
            }
            if (allDistinct) maxSum = Math.max(maxSum, sum);
        }
        return maxSum;
    }

    // Level 2 & 3: sliding window with running sum + frequency map, O(n)
    static long maximumSubarraySum(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        long windowSum = 0;
        long maxSum = 0;

        for (int i = 0; i < nums.length; i++) {
            windowSum += nums[i];
            freq.merge(nums[i], 1, Integer::sum);

            if (i >= k) {
                int leaving = nums[i - k];
                windowSum -= leaving;
                freq.merge(leaving, -1, Integer::sum);
                if (freq.get(leaving) == 0) freq.remove(leaving);
            }

            if (i >= k - 1 && freq.size() == k) {
                maxSum = Math.max(maxSum, windowSum);
            }
        }
        return maxSum;
    }

    public static void main(String[] args) {
        int[] nums = {1, 5, 4, 2, 9, 9, 9};
        System.out.println("brute force: " + bruteForce(nums, 3));
        System.out.println("optimal:     " + maximumSubarraySum(nums, 3));

        int[] allSame = {1, 1, 1, 1};
        System.out.println("all same, k=2: " + maximumSubarraySum(allSame, 2));
    }
}
```

**How to run:** save as `MaximumSumOfDistinctSubarrays.java`, then run `java MaximumSumOfDistinctSubarrays.java`.

## 6. Walkthrough

Trace `maximumSubarraySum({1, 5, 4, 2, 9, 9, 9}, 3)`:

| i | nums[i] | windowSum after | leaving | freq.size() | complete? distinct? | maxSum |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | — | 1 | no | 0 |
| 1 | 5 | 6 | — | 2 | no | 0 |
| 2 | 4 | 10 | — | 3 | yes, distinct | 10 |
| 3 | 2 | 11 | 1 | 3 | yes, distinct | 11 |
| 4 | 9 | 15 | 5 | 3 | yes, distinct | 15 |
| 5 | 9 | 20 | 4 | 2 (9 repeats) | no | 15 |
| 6 | 9 | 27 | 2 | 1 (only 9 left) | no | 15 |

Final `maxSum = 15`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: checking distinctness by comparing `freq.size()` to `k` only works once the window has reached its full size — checking too early (before `i >= k - 1`) would wrongly accept a partially filled window.

- A fixed-length window's sum updates in O(1) by adding the entering element and subtracting the one leaving — no need to re-sum the whole window.
- `freq.size() == k` is an O(1) proxy for "every element in the window is distinct," maintained incrementally as the window slides.
- Time: O(n) — one pass, O(1) amortized map operations per step.
