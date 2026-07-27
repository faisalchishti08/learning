---
card: leetcode-patterns
gi: 498
slug: subarray-sums-divisible-by-k
title: Subarray Sums Divisible by K
---

## 1. What it is

Given an array `nums` and an integer `k`, return the total number of contiguous subarrays whose sum is divisible by `k`. Example: `nums = [4, 5, 0, -2, -3, 1]`, `k = 5` → `7`.

## 2. Why & when

This is [Subarray Sum Equals K](0493-subarray-sum-equals-k.md), but keyed by remainder modulo `k` instead of exact sum — and it also needs to correctly handle negative remainders, which Java's `%` operator can produce. It belongs to the same [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family: two prefix sums with the same remainder mod `k` bound a subarray divisible by `k`. Constraints: up to 30,000 elements, `nums` can contain negative numbers.

## 3. Core concept

**Key idea:** scan left to right, maintaining a running sum and a hash map counting how many times each remainder (mod `k`) has appeared so far. At each step, the number of earlier prefixes with the *same* remainder as the current one is exactly the number of subarrays ending here that are divisible by `k` (since a subarray's sum is divisible by `k` exactly when its two boundary prefix sums share a remainder).

**Steps:**
1. Initialize `remainderCount = {0: 1}` (the empty prefix has remainder `0`).
2. Scan the array, maintaining `runningSum`.
3. Compute `remainder = ((runningSum % k) + k) % k` — the double-modulo trick normalizes negative remainders into the range `[0, k-1]`.
4. Add `remainderCount.getOrDefault(remainder, 0)` to the total count.
5. Increment `remainderCount[remainder]` by 1.
6. Return the total count.

**Why the double-modulo (`((x % k) + k) % k`) is necessary:** in Java, `%` returns a result with the same sign as the dividend, so a negative running sum can produce a negative remainder (e.g. `-3 % 5 == -3` in Java, not `2`). Adding `k` and taking `% k` again always normalizes the result into `[0, k-1]`, so that two sums which are mathematically congruent mod `k` map to the *same* hash map key regardless of sign.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Running sum remainders, normalized to be non-negative, counted in a hash map">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [4, 5, 0, -2, -3, 1], k = 5</text>
    <text x="20" y="45" fill="#8b949e">map={0:1}. runningSum=0, count=0.</text>
    <text x="20" y="65" fill="#8b949e">4: sum=4, rem=4. count+=map[4]=0. map={0:1,4:1}</text>
    <text x="20" y="85" fill="#8b949e">5: sum=9, rem=4. count+=map[4]=1 -&gt; count=1. map={0:1,4:2}</text>
    <text x="20" y="105" fill="#8b949e">0: sum=9, rem=4. count+=map[4]=2 -&gt; count=3. map={0:1,4:3}</text>
    <text x="20" y="130" fill="#f0883e">-2: sum=7, rem=2. count+=map[2]=0 -&gt; count=3. map={...,2:1}</text>
    <text x="20" y="150" fill="#f0883e">-3: sum=4, rem=4. count+=map[4]=3 -&gt; count=6. map={...,4:4}</text>
    <text x="20" y="170" fill="#3fb950">1: sum=5, rem=0. count+=map[0]=1 -&gt; count=7. final answer: 7</text>
  </g>
</svg>

Matching remainders accumulate a running count of subarrays divisible by `k`, negative sums included.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray, sum it directly and check divisibility by `k`. O(n²).

**KEY INSIGHT:** subarrays divisible by `k` are found by counting matching remainders among prefix sums, exactly like [Subarray Sum Equals K](0493-subarray-sum-equals-k.md) — the only new wrinkle is normalizing negative remainders before using them as hash map keys.

**Level 2 — Optimal.** Running sum with a normalized-remainder hash map, O(n).

**Level 3 — Hardened.** Handles negative numbers correctly (via the double-modulo normalization) and `k = 1` (every subarray is divisible by 1).

```java
// SubarraysDivByK.java
import java.util.*;

public class SubarraysDivByK {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums, int k) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum % k == 0) count++;
            }
        }
        return count;
    }

    // Level 2 & 3: running sum + normalized remainder hash map, O(n)
    static int subarraysDivByK(int[] nums, int k) {
        Map<Integer, Integer> remainderCount = new HashMap<>();
        remainderCount.put(0, 1);
        int runningSum = 0;
        int count = 0;

        for (int num : nums) {
            runningSum += num;
            int remainder = ((runningSum % k) + k) % k; // normalize to [0, k-1]
            count += remainderCount.getOrDefault(remainder, 0);
            remainderCount.merge(remainder, 1, Integer::sum);
        }
        return count;
    }

    public static void main(String[] args) {
        int[] nums = {4, 5, 0, -2, -3, 1};
        System.out.println("brute force: " + bruteForce(nums, 5));
        System.out.println("optimal:     " + subarraysDivByK(nums, 5));

        System.out.println("k=1 (all subarrays): " + subarraysDivByK(new int[]{1, 2, 3}, 1));
    }
}
```

**How to run:** save as `SubarraysDivByK.java`, then run `java SubarraysDivByK.java`.

## 6. Walkthrough

Trace `subarraysDivByK({4, 5, 0, -2, -3, 1}, 5)`:

| num | runningSum | raw sum%k | normalized remainder | found count | count after | map after |
|---|---|---|---|---|---|---|
| 4 | 4 | 4 | 4 | 0 | 0 | {0:1, 4:1} |
| 5 | 9 | 4 | 4 | 1 | 1 | {0:1, 4:2} |
| 0 | 9 | 4 | 4 | 2 | 3 | {0:1, 4:3} |
| -2 | 7 | 2 | 2 | 0 | 3 | {0:1, 4:3, 2:1} |
| -3 | 4 | 4 | 4 | 3 | 6 | {0:1, 4:4, 2:1} |
| 1 | 5 | 0 | 0 | 1 | 7 | {0:2, 4:4, 2:1} |

Final count: `7`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using a plain `runningSum % k` without normalization treats `-3 % 5` (which Java evaluates to `-3`) as a different key from `2 % 5` (which is `2`), even though they are mathematically the same remainder — this silently undercounts whenever the array contains negative numbers.

- Same technique as [Subarray Sum Equals K](0493-subarray-sum-equals-k.md), keyed by remainder mod `k` instead of exact sum.
- Always normalize remainders with `((x % k) + k) % k` when negative numbers are possible.
- Time: O(n) — one pass, O(1) amortized hash map operations per step.
