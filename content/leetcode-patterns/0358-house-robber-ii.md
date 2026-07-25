---
card: leetcode-patterns
gi: 358
slug: house-robber-ii
title: House Robber II
---

## 1. What it is

Same rules as House Robber, but the houses are arranged in a CIRCLE: house `0` and house `n-1` are now also ADJACENT to each other, so robbing both together is forbidden. Return the maximum money obtainable. Example: `nums = [2,3,2]` → `3` (robbing houses `0` and `2` is forbidden since they are now adjacent; the best is just house `1`).

## 2. Why & when

This extends House Robber by turning the LINE of houses into a CIRCLE. Use this shape whenever a "skip or take, adjacent forbidden" problem is arranged circularly — the fix is to reduce the circular problem into two LINEAR sub-problems, each excluding one of the two houses that create the wraparound adjacency.

## 3. Core concept

**Key idea:** since houses `0` and `n-1` cannot BOTH be robbed, the answer is the maximum of two independent linear House Robber runs: one that EXCLUDES house `0` (so `n-1` is free to be robbed), and one that EXCLUDES house `n-1` (so `0` is free to be robbed).

**Steps:**
1. If `n == 1`, return `nums[0]` (a single house has no wraparound conflict).
2. Run the standard House Robber DP on `nums[0 .. n-2]` (excluding the last house).
3. Run the standard House Robber DP on `nums[1 .. n-1]` (excluding the first house).
4. Return the maximum of the two results.

**Why it is correct:** any valid selection either excludes house `0`, excludes house `n-1`, or excludes BOTH — but never includes both (that would violate the wraparound adjacency). Since "excludes both" can never beat "excludes just one" (having more choices available), checking only the two "exclude exactly one end" cases is guaranteed to include the true optimum among them.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="circular houses split into two linear ranges, one excluding the first house and one excluding the last house">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[2,3,2]; houses 0 and 2 are adjacent (circle)</text>
    <text x="10" y="45">range A: nums[0..1] = [2,3] -&gt; rob() = 3</text>
    <text x="10" y="65">range B: nums[1..2] = [3,2] -&gt; rob() = 3</text>
    <rect x="10" y="85" width="220" height="24" fill="#3fb950"/><text x="120" y="102" fill="#0d1117" text-anchor="middle" font-size="10">max(3, 3) = 3</text>
  </g>
</svg>

Two linear sub-problems, each dropping one end house, cover every valid circular selection.

## 5. Runnable example

```java
// HouseRobberII.java
public class HouseRobberII {

    // KEY INSIGHT: a valid selection never robs both end houses, so
    // solve two LINEAR House Robber sub-problems -- one excluding
    // house 0, one excluding house n-1 -- and take the max.

    static int rob(int[] nums) {
        int n = nums.length;
        if (n == 1) return nums[0];

        int excludeLast = robLinear(nums, 0, n - 2);
        int excludeFirst = robLinear(nums, 1, n - 1);
        return Math.max(excludeLast, excludeFirst);
    }

    static int robLinear(int[] nums, int start, int end) {
        int prev2 = 0, prev1 = 0;
        for (int i = start; i <= end; i++) {
            int curr = Math.max(prev1, prev2 + nums[i]);
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(rob(new int[]{2, 3, 2}));
        // 3
        System.out.println(rob(new int[]{1, 2, 3, 1}));
        // 4
    }
}
```

**How to run:** `java HouseRobberII.java`

## 6. Walkthrough

Trace `rob([2,3,2])`, `n=3`:

| sub-problem | range | robLinear result |
|---|---|---|
| excludeLast | indices 0..1 = [2,3] | 3 |
| excludeFirst | indices 1..2 = [3,2] | 3 |

`max(3, 3) = 3`, matching the expected answer. Time complexity is O(n) (two linear passes, each O(n/2) to O(n)). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: reusing a single `robLinear` helper with explicit `start`/`end` bounds (instead of copying sub-arrays) avoids allocating extra arrays and keeps both ranges' logic identical — always factor out the shared linear logic rather than duplicating it with subtly different code for each range.

- Reducing a circular constraint to two linear sub-problems, each dropping one conflicting end, is a general technique — it applies to any "first and last are also adjacent" variant of a linear DP.
- The `n == 1` guard is essential: with only one house, `robLinear(nums, 0, -1)` would run zero iterations and wrongly return `0` instead of `nums[0]`.
- Related problems: House Robber (the linear version this problem reduces to), Delete and Earn (a different disguise of the same skip-or-take recurrence, based on value equality rather than array position).
