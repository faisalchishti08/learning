---
card: leetcode-patterns
gi: 357
slug: house-robber
title: House Robber
---

## 1. What it is

Given an array `nums` where `nums[i]` is the money in house `i`, return the MAXIMUM total money you can rob without robbing two ADJACENT houses (robbing houses `i` and `i+1` together triggers an alarm). Example: `nums = [2,7,9,3,1]` → `12` (rob houses `0`, `2`, `4`: `2+9+1=12`).

## 2. Why & when

This is the "skip or take" variant of Fibonacci/Linear DP: at each house, you either ROB it (and must have skipped the one before) or SKIP it (keeping whatever you had). Use this shape whenever a problem forbids picking two adjacent elements and asks for a maximum (or minimum) over the elements you do pick.

## 3. Core concept

**Key idea:** build `dp[i]` = the maximum money obtainable considering houses `0` through `i`, for every `i`, by choosing the better of two options at each house.

**Steps:**
1. Base cases: `dp[0] = nums[0]` (only one house, rob it), `dp[1] = max(nums[0], nums[1])` (two houses, pick the richer one, since robbing both is not allowed).
2. For `i` from `2` to `n-1`: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` (skip house `i`, keeping `dp[i-1]`; or rob house `i`, adding its money to the best answer that EXCLUDES house `i-1`, which is `dp[i-2]`).
3. Return `dp[n-1]`.

**Why it is correct:** at house `i`, there are only two choices: rob it or not. If you rob it, house `i-1` MUST be skipped, so the best you can combine with is `dp[i-2]` (the best answer using houses up to `i-2`). If you skip it, the best answer is simply `dp[i-1]` unchanged. Taking the maximum of these two covers every possibility.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for houses 2,7,9,3,1 showing dp of 4 as the max of skip and rob options">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[2,7,9,3,1]; dp[0]=2, dp[1]=7, dp[2]=11, dp[3]=11</text>
    <text x="10" y="45">dp[4] = max(dp[3], dp[2] + nums[4]) = max(11, 11+1) = 12</text>
    <rect x="10" y="65" width="260" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">dp[4] = 12: rob houses 0, 2, 4</text>
  </g>
</svg>

Each house's best answer is the max of "skip it" and "rob it plus the best answer two houses back."

## 5. Runnable example

```java
// HouseRobber.java
public class HouseRobber {

    // KEY INSIGHT: rob house i requires skipping i-1, so combine with
    // dp[i-2]; skip house i keeps dp[i-1] -- take the max of both.

    static int rob(int[] nums) {
        int n = nums.length;
        if (n == 1) return nums[0];

        int prev2 = nums[0];
        int prev1 = Math.max(nums[0], nums[1]);
        for (int i = 2; i < n; i++) {
            int curr = Math.max(prev1, prev2 + nums[i]);
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(rob(new int[]{2, 7, 9, 3, 1}));
        // 12
        System.out.println(rob(new int[]{1, 2, 3, 1}));
        // 4
    }
}
```

**How to run:** `java HouseRobber.java`

## 6. Walkthrough

Trace `rob([2,7,9,3,1])`:

| i | prev2 | prev1 | curr |
|---|---|---|---|
| start | 2 | 7 | - |
| 2 | 7 | max(7, 2+9)=11 | 11 |
| 3 | 11 | max(11, 7+3)=11 | 11 |
| 4 | 11 | max(11, 11+1)=12 | 12 |

Final `prev1 = 12`, matching the expected `12`. Time complexity is O(n). Space is O(1) with rolling variables.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `n == 1` special case makes `dp[1] = max(nums[0], nums[1])` crash on an out-of-bounds access when there is only one house — always guard the case where the array has fewer than two elements.

- `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`: the general "skip or take, adjacent forbidden" template.
- Base cases `dp[0] = nums[0]` and `dp[1] = max(nums[0], nums[1])` handle the two smallest array sizes before the general recurrence kicks in at `i = 2`.
- Related problems: House Robber II (houses arranged in a CIRCLE, so the first and last are also adjacent), Delete and Earn (the same skip-or-take recurrence, but disguised as a value-based, not index-based, adjacency rule).
