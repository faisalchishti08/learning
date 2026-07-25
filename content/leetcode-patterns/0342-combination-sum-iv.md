---
card: leetcode-patterns
gi: 342
slug: combination-sum-iv
title: Combination Sum IV
---

## 1. What it is

Given an array of DISTINCT positive integers `nums` and an integer `target`, return the number of possible COMBINATIONS that add up to `target`, where different ORDERS of the same numbers count as DIFFERENT combinations (despite the name, this problem counts permutations). Example: `nums = [1,2,3]`, `target = 4` → `7` (including both `[1,3]` and `[3,1]` separately).

## 2. Why & when

Despite sharing a name with the "Combination Sum" backtracking problems, this is Unbounded Knapsack's PERMUTATION-counting variant: each number is reusable, and order matters. Use this shape whenever a problem explicitly counts different orderings of the same multiset as distinct answers — the tell is usually an example showing `[1,3]` and `[3,1]` both counted.

## 3. Core concept

**Key idea:** build `dp[a]` = number of ORDERED sequences of numbers from `nums` that sum to `a`, by looping the amount on the OUTSIDE so every amount reconsiders every number fresh — the ordering is generated automatically by which number gets appended LAST.

**Steps:**
1. Create `dp[target + 1]`, all zeros, with `dp[0] = 1` (one way to reach `0`: the empty sequence).
2. For `a` from `1` to `target`, for each `num` in `nums` with `num <= a`: `dp[a] += dp[a - num]`.
3. Return `dp[target]`.

**Why amount-outer produces permutations:** at each amount `a`, the algorithm asks "what could the LAST number in the sequence be?" and sums the ways to reach `a - num` for every candidate last number. Since a sequence ending in `1` (built from a sequence summing to `a-1`) and a sequence ending in `3` (built from a sequence summing to `a-3`) are tracked as separate cases at the SAME amount, sequences that use the same numbers in different orders end up counted separately — exactly the permutation behavior this problem wants.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for nums 1,2,3 reaching target 4, amount outer loop reconsidering every number at each amount">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[1,2,3], target=4</text>
    <text x="10" y="45">dp[4] = dp[3] (last num=1) + dp[2] (last num=2) + dp[1] (last num=3)</text>
    <text x="10" y="65">dp[3]=4, dp[2]=2, dp[1]=1 -&gt; dp[4] = 4+2+1 = 7</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[4] = 7 ordered sequences</text>
  </g>
</svg>

Every amount asks "what was the last number placed," which naturally distinguishes orderings.

## 5. Runnable example

```java
// CombinationSumIV.java
public class CombinationSumIV {

    // KEY INSIGHT: counting PERMUTATIONS (order matters) requires the
    // amount loop OUTER, numbers loop INNER -- the opposite order of
    // Coin Change II, which counts order-independent combinations.

    static int combinationSum4(int[] nums, int target) {
        int[] dp = new int[target + 1];
        dp[0] = 1;

        for (int a = 1; a <= target; a++) {
            for (int num : nums) {
                if (num <= a) {
                    dp[a] += dp[a - num];
                }
            }
        }
        return dp[target];
    }

    public static void main(String[] args) {
        System.out.println(combinationSum4(new int[]{1, 2, 3}, 4));
        // 7
        System.out.println(combinationSum4(new int[]{9}, 3));
        // 0
    }
}
```

**How to run:** `java CombinationSumIV.java`

## 6. Walkthrough

Trace `combinationSum4([1,2,3], 4)`:

| amount a | contributions (num: dp[a-num]) | dp[a] |
|---|---|---|
| 0 | (base case) | 1 |
| 1 | 1: dp[0]=1 | 1 |
| 2 | 1: dp[1]=1; 2: dp[0]=1 | 2 |
| 3 | 1: dp[2]=2; 2: dp[1]=1; 3: dp[0]=1 | 4 |
| 4 | 1: dp[3]=4; 2: dp[2]=2; 3: dp[1]=1 | 7 |

`dp[4] = 7`, matching all ordered sequences: `(1,1,1,1)`, `(1,1,2)`, `(1,2,1)`, `(2,1,1)`, `(2,2)`, `(1,3)`, `(3,1)`. Time complexity is O(target · n). Space is O(target).

## 7. Gotchas & takeaways

> Gotcha: LeetCode's name "Combination Sum IV" is misleading — despite the name, this problem counts PERMUTATIONS. Always check the problem's own example (does `[1,3]` and `[3,1]` count as one or two?) rather than trusting the title.

- Amount outer, items inner, `dp[a] += dp[a - num]`: the general template for order-dependent counting over reusable items.
- If `target` can be reached but individual `dp[a]` values could overflow a 32-bit integer for large inputs, LeetCode's constraints keep results within `int` range — but watch for this risk in similar problems with larger bounds.
- Related problems: Coin Change II (the order-independent sibling — swap to items outer), Word Break (a similar "what came last" DP, but over string positions instead of numeric amounts).
