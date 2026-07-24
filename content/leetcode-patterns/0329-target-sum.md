---
card: leetcode-patterns
gi: 329
slug: target-sum
title: Target Sum
---

## 1. What it is

Given an integer array `nums` and an integer `target`, assign either a `+` or `-` sign in front of EACH number, then sum them all. Return the number of DIFFERENT ways to assign signs so the sum equals `target`. Example: `nums = [1,1,1,1,1]`, `target = 3` → `5`.

## 2. Why & when

This looks like a sign-assignment problem, but a small algebraic rewrite turns it into subset-sum counting: split `nums` into a POSITIVE subset `P` and a NEGATIVE subset `N`. Then `sum(P) - sum(N) = target`, and since `sum(P) + sum(N) = total` (the sum of all numbers), solving these two equations gives `sum(P) = (total + target) / 2`. Use this shape whenever a problem's "choice" (here, a `+`/`-` sign) can be reframed as "which subset does this element belong to," turning it into a 0/1 knapsack COUNTING problem.

## 3. Core concept

**Key idea:** count how many subsets of `nums` sum to exactly `subsetTarget = (total + target) / 2`. This is 0/1 knapsack, but counting the NUMBER OF WAYS to reach a sum, not just whether it is reachable.

**Steps:**
1. Compute `total = sum(nums)`. If `(total + target)` is odd, or `target` exceeds `total` in absolute value, return `0` (no valid split exists).
2. Compute `subsetTarget = (total + target) / 2`. If `subsetTarget < 0`, return `0`.
3. Create `dp[subsetTarget + 1]`, an integer array, with `dp[0] = 1` (there is exactly 1 way to reach sum `0`: choose nothing).
4. For each number `num` in `nums`, loop `w` from `subsetTarget` DOWN TO `num`: `dp[w] += dp[w - num]` (every existing way to reach `w - num` becomes a new way to reach `w`, by adding `num` to the positive subset).
5. Return `dp[subsetTarget]`.

**Why it is correct:** the algebraic rewrite (`sum(P) = (total + target) / 2`) is an exact, reversible transformation — every valid sign assignment corresponds to exactly one subset `P` summing to `subsetTarget`, and vice versa, so COUNTING subsets that sum to `subsetTarget` is the same as counting valid sign assignments. Using `dp[w] += dp[w - num]` (instead of `dp[w] = dp[w] || dp[w-num]`) accumulates the NUMBER of distinct ways, since each way to reach `w - num` extends into exactly one distinct way to reach `w` by including `num`.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Counting ways array for 5 ones, targeting subset sum 4, showing counts accumulate as each one is processed">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[1,1,1,1,1], target=3, total=5, subsetTarget=(5+3)/2=4</text>
    <text x="10" y="45">dp[0]=1 initially</text>
    <text x="10" y="65">after 1st '1': dp[1] += dp[0] -&gt; dp[1]=1</text>
    <text x="10" y="85">after 2nd '1': dp[2] += dp[1]=1, dp[1] += dp[0]=1 -&gt; dp[1]=2,dp[2]=1</text>
    <text x="10" y="105">... continuing for all 5 ones ...</text>
    <rect x="10" y="120" width="150" height="24" fill="#3fb950"/><text x="85" y="137" fill="#0d1117" text-anchor="middle" font-size="10">dp[4] = 5 ways</text>
  </g>
</svg>

Each number processed adds its own contribution to every reachable sum, accumulating the count of distinct ways.

## 5. Runnable example

```java
// TargetSum.java
public class TargetSum {

    // KEY INSIGHT: "+/- sign for each number, sum equals target" is
    // algebraically the same as "count subsets summing to
    // (total+target)/2" -- a 0/1 knapsack COUNTING problem.

    static int findTargetSumWays(int[] nums, int target) {
        int total = 0;
        for (int num : nums) total += num;

        if (Math.abs(target) > total || (total + target) % 2 != 0) return 0;

        int subsetTarget = (total + target) / 2;
        int[] dp = new int[subsetTarget + 1];
        dp[0] = 1;

        for (int num : nums) {
            for (int w = subsetTarget; w >= num; w--) {
                dp[w] += dp[w - num];
            }
        }
        return dp[subsetTarget];
    }

    public static void main(String[] args) {
        System.out.println(findTargetSumWays(new int[]{1, 1, 1, 1, 1}, 3));
        // 5
        System.out.println(findTargetSumWays(new int[]{1}, 1));
        // 1
    }
}
```

**How to run:** `java TargetSum.java`

## 6. Walkthrough

Trace `findTargetSumWays([1,1,1,1,1], 3)`: `total = 5`, `subsetTarget = (5+3)/2 = 4`.

| after processing | dp array (indices 0..4) |
|---|---|
| start | [1,0,0,0,0] |
| 1st '1' | [1,1,0,0,0] |
| 2nd '1' | [1,2,1,0,0] |
| 3rd '1' | [1,3,3,1,0] |
| 4th '1' | [1,4,6,4,1] |
| 5th '1' | [1,5,10,10,5] |

`dp[4] = 5`, matching the expected `5` ways (choosing which one or two of the five `1`s get a `-` sign, among the valid combinations that sum to `3`). Time complexity is O(n · subsetTarget). Space is O(subsetTarget), for the 1D array.

## 7. Gotchas & takeaways

> Gotcha: `(total + target)` must be checked for being EVEN before dividing by 2 — an odd sum here means no integer subset sum can satisfy the equation, and proceeding with integer division would silently compute the wrong (rounded-down) target.

- The algebraic rewrite from "sign assignment" to "subset sum" is the key insight — once seen, the rest is a direct application of the 0/1 knapsack counting template.
- `dp[w] += dp[w - num]` (accumulate counts) versus `dp[w] = dp[w] || dp[w-num]` (reachability only) is the general distinction between COUNTING and CHECKING variants of knapsack DP.
- Related problems: Partition Equal Subset Sum (the reachability-only version of a similar subset-sum idea), Coin Change 2 (a counting-ways knapsack problem, but UNBOUNDED — coins can repeat, using an ascending loop instead of descending).
