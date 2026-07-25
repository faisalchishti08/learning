---
card: leetcode-patterns
gi: 338
slug: dp-unbounded-knapsack-template-dp-over-amount-iterate-coins
title: "DP: Unbounded Knapsack — template: dp over amount, iterate coins/items in the inner loop"
---

## 1. What it is

This page gives the reusable template for Unbounded Knapsack problems: a 1D array `dp[amount]`, filled by looping amounts on the outside and item types on the inside (or vice versa, depending on whether order matters).

## 2. Why & when

Use "amount outer, items inner" when the problem counts COMBINATIONS (order does not matter, like Coin Change II) or computes a MINIMUM/reachability (order is irrelevant either way). Use "items outer, amount inner" when the problem counts PERMUTATIONS (order matters, like Combination Sum IV), since that ordering lets the same total be reached through different item sequences.

## 3. Core concept

**Template A — combinations / minimum (items outer or either order works for min).**
1. Create `dp[amount+1]`. Set `dp[0]` to the identity value (`0` ways becomes `1`, or `0` cost, or `true`).
2. For each item type, for `a` from the item's weight UP TO `amount` (ascending order is required): `dp[a] = combine(dp[a], dp[a - weight] + value)`.
3. The answer is `dp[amount]`.

**Template B — permutations (amount outer, items inner).**
1. Create `dp[amount+1]`, `dp[0] = 1` (one way to make zero: pick nothing).
2. For `a` from `1` to `amount`, for each item type with `weight <= a`: `dp[a] += dp[a - weight]`.
3. The answer is `dp[amount]`.

**Why the loop order changes the answer:** in Template A, each item type is fully processed (all amounts) before moving to the next type, so a coin sequence like `[1,3]` and `[3,1]` collapse into ONE combination. In Template B, every amount considers ALL item types at every step, so `[1,3]` and `[3,1]` count as TWO separate permutations, because the outer loop revisits every coin choice at every amount independently of order already fixed.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two loop orders producing combinations versus permutations for coins one and three reaching amount four">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">coins=[1,3], amount=4</text>
    <text x="10" y="45">Template A (coin outer): coin=1 fills dp fully, then coin=3 adds on top</text>
    <text x="10" y="65">-&gt; counts {1,1,1,1} and {1,3} as ONE way each = 2 combinations</text>
    <text x="10" y="95">Template B (amount outer): each amount re-checks BOTH coins every time</text>
    <text x="10" y="115">-&gt; counts {1,3} and {3,1} separately = permutations, not combinations</text>
    <rect x="10" y="135" width="300" height="24" fill="#3fb950"/><text x="160" y="152" fill="#0d1117" text-anchor="middle" font-size="10">loop order decides combination vs permutation</text>
  </g>
</svg>

The outer loop is the one that "locks in" an ordering rule; put items outer to forbid reordering, amount outer to allow it.

## 5. Runnable example

```java
// UnboundedKnapsackTemplate.java
public class UnboundedKnapsackTemplate {

    // Template A: combinations (coin outer) -- Coin Change II style.
    static int countCombinations(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        dp[0] = 1;
        for (int coin : coins) {
            for (int a = coin; a <= amount; a++) {
                dp[a] += dp[a - coin];
            }
        }
        return dp[amount];
    }

    // Template B: permutations (amount outer) -- Combination Sum IV style.
    static int countPermutations(int[] nums, int target) {
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
        int[] coins = {1, 2};
        System.out.println(countCombinations(coins, 4));
        // 3: {1,1,1,1}, {1,1,2}, {2,2}
        System.out.println(countPermutations(coins, 4));
        // 5: also counts {1,2,1} and {2,1,1} as distinct
    }
}
```

**How to run:** `java UnboundedKnapsackTemplate.java`

## 6. Walkthrough

1. `countCombinations` loops coin `1` first, filling every `dp[a]` using only `1`s, THEN loops coin `2`, adding ways that use at least one `2` — each combination counted exactly once regardless of the order coins would be picked in.
2. `countPermutations` loops amount `1` to `4`, and at EACH amount checks both coins fresh — so a sequence ending in `1` and a sequence ending in `2` are tracked as different paths even if they use the same multiset of coins.
3. Both return an answer for `coins=[1,2]`, `amount=4`: `3` combinations versus `5` permutations, confirming the loop order changes what is being counted, not just performance.
4. Tracing `countCombinations`'s array after processing coin `1` alone shows `dp = [1,1,1,1,1]` (only one way to make any amount using just `1`s); processing coin `2` next updates `dp[2..4]` by adding `dp[a-2]`, folding in the new combinations.
5. This template applies directly to Coin Change, Coin Change II, Combination Sum IV, and Perfect Squares — only the combining step (`min`, `+=`, or `OR`) and which loop is outer change per problem.

## 7. Gotchas & takeaways

> Gotcha: using "items outer" (Template A) for a problem that actually wants PERMUTATIONS silently undercounts the answer, since it never revisits an item order once the outer loop has moved past that item type.

- Combinations (order does not matter): items outer, amount inner, ascending.
- Permutations (order matters): amount outer, items inner, ascending.
- Minimum/reachability problems: either loop order works, since `min`/`OR` do not care how many times a state was reached — only the descending-vs-ascending rule from 0/1 knapsack does not apply here at all, since unbounded knapsack is always ascending.
