---
card: leetcode-patterns
gi: 325
slug: dp-0-1-knapsack-signal-pick-skip-items-with-a-capacity-const
title: DP: 0/1 Knapsack — signal: pick/skip items with a capacity constraint (each item once)
---

## 1. What it is

The 0/1 Knapsack pattern solves problems where you choose a SUBSET of items, each usable AT MOST ONCE, to fit within some CAPACITY, while maximizing (or matching) a value. "0/1" means each item is either fully taken (`1`) or fully skipped (`0`) — never split or reused. Think of packing a backpack with a fixed weight limit: for each item, you either put it in or leave it out.

## 2. Why & when

Reach for this pattern whenever a problem gives you a set of items (each with a "weight" or "cost" and a "value"), a capacity or target limit, and asks for the best (or any) way to select a subset, with EACH ITEM USABLE ONLY ONCE. Trying every subset directly costs O(2^n), since there are `2^n` possible subsets; dynamic programming reduces this to O(n · capacity), by reusing overlapping sub-decisions instead of recomputing them.

Learn to recognize these signals in a problem statement:

- **"Each element/coin/item can be used at most once"** — the defining 0/1 constraint (contrast with Unbounded Knapsack, where items can repeat).
- **"Partition into two subsets with equal sum," "can you reach exactly this target sum"** — a capacity-matching variant, where "value" is implicit (every included item contributes its own weight to a running sum).
- **"Maximize value within a weight limit"** — the classic knapsack framing directly.
- **"Choose a subset of piles/coins to maximize count K,"** or **"choose items to fit two independent capacity constraints (zeros and ones)"** — 0/1 knapsack generalized to 2 (or more) capacity dimensions.

The alternative — backtracking over every subset — is correct but exponential; 0/1 knapsack's dynamic programming formulation reuses the answer to "best value using the first `i` items with capacity `w`" across many different decision paths that happen to reach the same `(i, w)` state.

## 3. Core concept

Every 0/1 knapsack problem reduces to the SAME per-item decision, repeated for each item against each possible remaining capacity:

**The state.** `dp[i][w]` = the best achievable value (or `true`/`false` for reachability problems) using only the FIRST `i` items, with capacity exactly (or at most) `w`.

**The transition.** For item `i` (weight `wt[i]`, value `val[i]`), there are exactly two choices at capacity `w`:
- **Skip item `i`:** `dp[i][w] = dp[i-1][w]` (the best value stays whatever it was without this item).
- **Take item `i`** (only possible if `wt[i] <= w`): `dp[i][w] = dp[i-1][w - wt[i]] + val[i]` (use up `wt[i]` of the capacity, gaining `val[i]`, from the best answer using one fewer item and less remaining capacity).
- `dp[i][w] = max(skip, take)` (or `OR` for reachability problems).

**Why the DP works:** the KEY property that makes memoization valid is that `dp[i][w]` depends ONLY on `dp[i-1][...]` — decisions about item `i` never need to be reconsidered once made, and every state `(i, w)` has a well-defined, reusable answer regardless of WHICH earlier items were chosen to reach that particular remaining capacity `w`.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decision tree for one item showing the skip branch reusing dp at row i-1 same capacity, and the take branch reusing dp at row i-1 reduced capacity plus this item's value">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">item i: weight=3, value=5; current capacity w=7</text>
    <text x="10" y="45">skip item i: dp[i][7] candidate = dp[i-1][7]</text>
    <text x="10" y="65">take item i (3&lt;=7): dp[i][7] candidate = dp[i-1][7-3] + 5 = dp[i-1][4] + 5</text>
    <rect x="10" y="80" width="280" height="24" fill="#3fb950"/><text x="150" y="97" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][7] = max(skip candidate, take candidate)</text>
  </g>
</svg>

Every cell's answer is built from exactly two smaller sub-answers: one row up (skip), one row up and shifted left by the item's weight (take).

## 5. Runnable example

```java
// Knapsack01Signal.java
public class Knapsack01Signal {

    // Signal check: classic 0/1 knapsack, maximize value within a
    // weight limit, each item usable at most once.
    static int knapsack(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];

        for (int i = 1; i <= n; i++) {
            for (int w = 0; w <= capacity; w++) {
                int skip = dp[i - 1][w];
                int take = (weights[i - 1] <= w)
                        ? dp[i - 1][w - weights[i - 1]] + values[i - 1]
                        : Integer.MIN_VALUE;
                dp[i][w] = Math.max(skip, take);
            }
        }
        return dp[n][capacity];
    }

    public static void main(String[] args) {
        int[] weights = {1, 3, 4, 5};
        int[] values = {1, 4, 5, 7};
        System.out.println(knapsack(weights, values, 7));
        // 9 (items with weight 3 and 4, values 4+5=9)
    }
}
```

**How to run:** `java Knapsack01Signal.java`

## 6. Walkthrough

1. You read a problem statement. "Each item used at most once, fit within a capacity" is the 0/1 knapsack signal.
2. Running `knapsack` on weights `[1,3,4,5]`, values `[1,4,5,7]`, capacity `7` confirms the best achievable value is `9`, by taking the weight-3 and weight-4 items (`4 + 5 = 9`, total weight `7`).
3. At every `(i, w)` cell, the algorithm only ever looks at row `i-1` — this row-by-row dependency is exactly what lets 0/1 knapsack be computed bottom-up, filling the table once, instead of exploring every subset separately.
4. If instead the problem says "can you partition into two equal-sum subsets," recognize it as a capacity-MATCHING variant: capacity = `sum/2`, values are irrelevant (every item's "value" equals its own weight), and the question becomes "is `dp[n][capacity]` reachable" rather than "what is the max value."
5. This upfront classification (maximize value vs. check reachability vs. multi-dimensional capacity) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: confusing 0/1 Knapsack with UNBOUNDED Knapsack (where items can be reused any number of times, like Coin Change) leads to using the wrong transition — unbounded knapsack's "take" case reuses `dp[i][w - wt[i]]` (same row `i`, since the item can be picked again), while 0/1 knapsack's "take" case must use `dp[i-1][w - wt[i]]` (previous row, since the item is now used up).

- The state `dp[i][w]`, built from exactly `dp[i-1][w]` (skip) and `dp[i-1][w - weight]` (take): the core 0/1 knapsack signal.
- Distinguish MAXIMIZE-value problems from REACHABILITY (`true`/`false`) problems — the transition's combining step (`max` vs `OR`) changes, but the state structure stays the same.
- Watch for MULTI-DIMENSIONAL capacity variants (two independent limits, like counting 0s and 1s), which extend the state to `dp[i][cap1][cap2]`.
