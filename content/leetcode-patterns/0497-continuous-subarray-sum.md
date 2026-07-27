---
card: leetcode-patterns
gi: 497
slug: continuous-subarray-sum
title: Continuous Subarray Sum
---

## 1. What it is

Given an array `nums` and an integer `k`, determine whether the array has a contiguous subarray of length **at least 2** whose sum is a multiple of `k` (including `0`, since `0` is a multiple of every `k`). Example: `nums = [23, 2, 4, 6, 7]`, `k = 6` → `true` (the subarray `[2, 4]` sums to `6`, a multiple of `6`).

## 2. Why & when

"Sum is a multiple of k" reframes as "two prefix sums have the same remainder mod k," from the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family. If `prefixSum[j] % k == prefixSum[i] % k`, then the subarray between `i` and `j` sums to a multiple of `k`, because the difference between two numbers with the same remainder is always divisible by `k`. Constraints: up to 100,000 elements, `k` can be any non-negative integer (including `0`, handled separately).

## 3. Core concept

**Key idea:** scan left to right, maintaining a running sum and its remainder modulo `k` (or the running sum unchanged if `k == 0`, to avoid division by zero). Use a hash map from "remainder value" to "the *first* index where it occurred." If the same remainder appears again at least 2 indices later, a qualifying subarray exists.

**Steps:**
1. Initialize `firstIndexOf = {0: -1}` (a remainder of `0` occurs "before index 0").
2. Scan the array, maintaining `runningSum`. Compute `remainder = (k == 0) ? runningSum : runningSum % k`.
3. If `remainder` has been seen before at index `i`, and the current index `j` satisfies `j - i >= 2`, return `true`.
4. If `remainder` has not been seen before, record `firstIndexOf[remainder] = j`.
5. If the scan finishes with no match, return `false`.

**Why only the *first* occurrence of each remainder should be stored:** storing the first occurrence maximizes the distance to any later matching occurrence, giving the best chance of satisfying the "length at least 2" requirement. Overwriting with later indices would only shrink that potential distance.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two indices sharing the same running sum remainder bound a subarray divisible by k">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [23, 2, 4, 6, 7], k = 6</text>
    <text x="20" y="45" fill="#8b949e">firstIndexOf = {0: -1}. runningSum=0.</text>
    <text x="20" y="65" fill="#8b949e">i=0 (23): runningSum=23, rem=23%6=5. not seen. store {5: 0}</text>
    <text x="20" y="85" fill="#8b949e">i=1 (2): runningSum=25, rem=25%6=1. not seen. store {1: 1}</text>
    <text x="20" y="105" fill="#3fb950">i=2 (4): runningSum=29, rem=29%6=5. seen at index 0! length=2-0=2 &gt;= 2 -&gt; true</text>
  </g>
</svg>

Matching remainders at indices at least 2 apart confirm a subarray of length 2 or more summing to a multiple of `k`.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray of length at least 2, sum it and check divisibility by `k`. O(n²).

**KEY INSIGHT:** two prefix sums with the same remainder modulo `k` always bound a subarray whose sum is a multiple of `k` — a hash map of first-seen remainders finds this in one pass.

**Level 2 — Optimal.** Running sum with a remainder hash map, O(n).

**Level 3 — Hardened.** Handles `k = 0` (only exact-zero-sum subarrays qualify) and a subarray of length exactly 2 as the minimum valid length.

```java
// ContinuousSubarraySum.java
import java.util.*;

public class ContinuousSubarraySum {

    // Level 1: brute force, O(n^2)
    static boolean bruteForce(int[] nums, int k) {
        for (int i = 0; i < nums.length; i++) {
            int sum = nums[i];
            for (int j = i + 1; j < nums.length; j++) {
                sum += nums[j];
                if ((k == 0 && sum == 0) || (k != 0 && sum % k == 0)) return true;
            }
        }
        return false;
    }

    // Level 2 & 3: running sum + remainder hash map, O(n)
    static boolean checkSubarraySum(int[] nums, int k) {
        Map<Integer, Integer> firstIndexOf = new HashMap<>();
        firstIndexOf.put(0, -1);
        int runningSum = 0;

        for (int i = 0; i < nums.length; i++) {
            runningSum += nums[i];
            int remainder = (k == 0) ? runningSum : runningSum % k;

            if (firstIndexOf.containsKey(remainder)) {
                if (i - firstIndexOf.get(remainder) >= 2) return true;
            } else {
                firstIndexOf.put(remainder, i);
            }
        }
        return false;
    }

    public static void main(String[] args) {
        System.out.println(bruteForce(new int[]{23, 2, 4, 6, 7}, 6));       // true
        System.out.println(checkSubarraySum(new int[]{23, 2, 4, 6, 7}, 6)); // true
        System.out.println(checkSubarraySum(new int[]{23, 2, 6, 4, 7}, 6)); // true
        System.out.println(checkSubarraySum(new int[]{0, 0}, 0));            // true (both zero)
    }
}
```

**How to run:** save as `ContinuousSubarraySum.java`, then run `java ContinuousSubarraySum.java`.

## 6. Walkthrough

Trace `checkSubarraySum({23, 2, 4, 6, 7}, 6)`:

| i | nums[i] | runningSum | remainder | seen before? | index gap | result |
|---|---|---|---|---|---|---|
| 0 | 23 | 23 | 5 | no | — | store {5:0} |
| 1 | 2 | 25 | 1 | no | — | store {1:1} |
| 2 | 4 | 29 | 5 | yes, at 0 | 2-0=2 >= 2 | **true** |

The method returns `true` at `i=2`, corresponding to the subarray `nums[1..2] = [2, 4]`, which sums to `6`, a multiple of `6`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the "length at least 2" requirement and returning `true` as soon as any remainder repeats (even at the very next index) can wrongly accept a subarray of length 1 in edge cases — always check `i - firstIndexOf.get(remainder) >= 2` before returning `true`.

- "Sum is a multiple of k" becomes "two prefix sums share a remainder mod k" — the same hash-map-of-prefixes idea as [Subarray Sum Equals K](0493-subarray-sum-equals-k.md), keyed by remainder instead of exact value.
- Handle `k = 0` separately (no modulo by zero): in that case, only an exact running-sum match (meaning a zero-sum subarray) counts.
- Time: O(n) — one pass, O(1) amortized hash map operations per step.
