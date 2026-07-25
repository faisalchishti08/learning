---
card: leetcode-patterns
gi: 337
slug: dp-unbounded-knapsack-signal-items-reusable-an-unlimited-num
title: DP: Unbounded Knapsack — signal: items reusable an unlimited number of times
---

## 1. What it is

Unbounded Knapsack is the sibling of 0/1 Knapsack. You still choose items to fill a capacity while maximizing or counting some outcome. The difference is reuse: each item type can be picked as many times as you want. Think of an unlimited supply of coins, not a fixed backpack of one-off objects.

## 2. Why & when

Reach for this pattern when a problem gives you a set of item TYPES (coins, rods, squares) with a capacity or target amount, and each type can be used ZERO, ONE, or MANY times. The alternative — 0/1 knapsack — forbids reuse; confusing the two produces the wrong transition and the wrong answer.

Learn to recognize these signals in a problem statement:

- **"You have an unlimited supply of coins/rods/items"** — the defining unbounded constraint.
- **"Minimum number of coins/squares/steps to reach a total"** — a minimize-count variant of unbounded knapsack.
- **"Number of ways to make an amount"** — a counting variant, where order may or may not matter.
- **"Break a string into dictionary words," "climb stairs with variable step sizes"** — the "items" are reused choices (a word, a step size) applied repeatedly along a sequence.

The alternative — trying every combination of repeated picks directly — explodes combinatorially. Dynamic programming reduces it to O(amount · types), by reusing the answer to "best result for a smaller amount" across every larger amount that includes it.

## 3. Core concept

Every unbounded knapsack problem reduces to the SAME per-amount decision, repeated for each item type against each possible amount:

**The state.** `dp[a]` = the best result (minimum count, number of ways, or reachability) using item types considered so far, for amount exactly `a`.

**The transition.** For an item of weight `wt` and value `val`, at amount `a` (with `wt <= a`): `dp[a] = combine(dp[a], dp[a - wt] + val)`.

**Why reuse works:** unlike 0/1 knapsack, `dp[a - wt]` is allowed to ALREADY include this same item type, because `dp[a - wt]` was computed in the SAME pass over this item, not a previous one. That single indexing difference — same row, not row `i-1` — is what lets one item be picked again and again.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array update where dp of amount minus weight can already include the current item, allowing reuse">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">coin value=3; dp array so far (min coins): [0,INF,INF,1,INF,INF,INF]</text>
    <text x="10" y="45">amount=6: dp[6] = min(dp[6], dp[6-3] + 1) = min(INF, dp[3]+1)</text>
    <text x="10" y="65">dp[3] already used this SAME coin once, so dp[3]=1 reflects coin=3 already placed</text>
    <rect x="10" y="85" width="300" height="24" fill="#3fb950"/><text x="160" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[6] = dp[3] + 1 = 2 -- coin 3 used twice</text>
  </g>
</svg>

Reading `dp[a - weight]` from the SAME pass, not an earlier one, is exactly what lets one item type repeat.

## 5. Runnable example

```java
// UnboundedKnapsackSignal.java
public class UnboundedKnapsackSignal {

    // Signal check: minimum coins to make an amount, coins reusable
    // any number of times.
    static int minCoins(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        java.util.Arrays.fill(dp, Integer.MAX_VALUE - 1);
        dp[0] = 0;

        for (int a = 1; a <= amount; a++) {
            for (int coin : coins) {
                if (coin <= a) {
                    dp[a] = Math.min(dp[a], dp[a - coin] + 1);
                }
            }
        }
        return dp[amount] >= Integer.MAX_VALUE - 1 ? -1 : dp[amount];
    }

    public static void main(String[] args) {
        int[] coins = {1, 3, 4};
        System.out.println(minCoins(coins, 6));
        // 2 (3 + 3)
    }
}
```

**How to run:** `java UnboundedKnapsackSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Unlimited supply," "any number of times," or "minimum/count over a repeated choice" is the unbounded knapsack signal.
2. Running `minCoins` on coins `[1,3,4]`, amount `6` gives `2`, using the coin `3` twice.
3. At every amount `a`, the loop checks each coin and reads `dp[a - coin]`, a SMALLER amount that may already have used this same coin — that is what allows reuse.
4. If instead the problem forbids reuse ("each coin used at most once"), recognize it as 0/1 knapsack instead, and switch the transition to read from a previous row or a descending 1D pass.
5. This upfront classification (reusable vs. one-off items) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: writing the inner loop the same way as 0/1 knapsack's 1D form (descending over amount) silently turns unbounded knapsack back into 0/1 knapsack — the ascending-over-amount order is what lets a smaller `dp[a - weight]` already reflect the current item.

- The state `dp[a]`, built from `dp[a - weight]` in the SAME pass: the core unbounded knapsack signal.
- Distinguish MINIMIZE-count problems from COUNT-ways problems — the combining step (`min` vs `+=`) changes, but the state structure stays the same.
- Watch for problems where item order matters (permutations, like Combination Sum IV) versus does not (combinations, like Coin Change II) — this changes which loop goes on the outside.
