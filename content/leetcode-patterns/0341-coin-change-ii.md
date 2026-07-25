---
card: leetcode-patterns
gi: 341
slug: coin-change-ii
title: Coin Change II
---

## 1. What it is

Given an array `coins` of coin denominations and an integer `amount`, return the NUMBER OF DIFFERENT COMBINATIONS of coins that make up `amount`. Each coin has unlimited supply, and the ORDER of coins within a combination does not matter (`[1,2]` and `[2,1]` are the SAME combination). Example: `coins = [1,2,5]`, `amount = 5` → `4` (`5`; `2+2+1`; `2+1+1+1`; `1+1+1+1+1`).

## 2. Why & when

This is Unbounded Knapsack's COUNTING variant, with the added twist that order must NOT be double-counted. Use this shape whenever a problem asks "how many combinations" (not permutations) of reusable items reach a target — the "combinations, not permutations" wording is the signal to loop item types on the OUTSIDE.

## 3. Core concept

**Key idea:** build `dp[a]` = number of combinations of coins (processed so far) that sum to `a`, adding one coin denomination at a time to avoid counting the same multiset of coins in more than one order.

**Steps:**
1. Create `dp[amount + 1]`, all zeros, with `dp[0] = 1` (there is exactly one way to make amount `0`: use no coins).
2. For each `coin` in `coins`, for `a` from `coin` UP TO `amount` (ascending, and this coin's loop must finish before moving to the next coin): `dp[a] += dp[a - coin]`.
3. Return `dp[amount]`.

**Why the coin-outer order is correct:** processing one coin denomination completely (across all amounts) before moving to the next means every combination gets built by adding coins in a FIXED canonical order (smallest-first, in the order `coins` lists them) — so `{1,2}` is only ever counted once, never once as `1,2` and once as `2,1`. Looping amount on the outside instead would recount those as different permutations.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array building combinations for coins 1,2,5 reaching amount 5, coin 1 fully processed before coin 2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">coins=[1,2,5], amount=5</text>
    <text x="10" y="45">after coin 1 fully processed: dp=[1,1,1,1,1,1] (only all-1s combos)</text>
    <text x="10" y="65">after coin 2 fully processed: dp[5] += dp[3] -&gt; adds combos using at least one 2</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">final dp[5] = 4 combinations</text>
  </g>
</svg>

Each coin is fully "locked in" across all amounts before the next coin is considered, which is what prevents order from being double-counted.

## 5. Runnable example

```java
// CoinChangeII.java
public class CoinChangeII {

    // KEY INSIGHT: "combinations" (order-independent) means the coin
    // loop must be OUTER, fully processed for one coin before moving
    // to the next -- otherwise the same multiset gets counted once
    // per ordering.

    static int change(int amount, int[] coins) {
        int[] dp = new int[amount + 1];
        dp[0] = 1;

        for (int coin : coins) {
            for (int a = coin; a <= amount; a++) {
                dp[a] += dp[a - coin];
            }
        }
        return dp[amount];
    }

    public static void main(String[] args) {
        System.out.println(change(5, new int[]{1, 2, 5}));
        // 4
        System.out.println(change(3, new int[]{2}));
        // 0
    }
}
```

**How to run:** `java CoinChangeII.java`

## 6. Walkthrough

Trace `change(5, [1,2,5])`:

| after coin | dp array (indices 0..5) |
|---|---|
| start | [1,0,0,0,0,0] |
| coin 1 | [1,1,1,1,1,1] |
| coin 2 | [1,1,2,2,3,3] |
| coin 5 | [1,1,2,2,3,4] |

`dp[5] = 4`, matching the four combinations: `5`; `2+2+1`; `2+1+1+1`; `1+1+1+1+1`. Time complexity is O(n · amount). Space is O(amount).

## 7. Gotchas & takeaways

> Gotcha: swapping the loop order (amount outer, coins inner) silently changes this into a PERMUTATION count, over-counting combinations that use the same coins in different orders — coin-outer is not a style choice here, it changes correctness.

- `dp[a] += dp[a - coin]`, with the coin loop OUTER: the general template for order-independent counting over reusable items.
- Contrast with Combination Sum IV, which wants PERMUTATIONS (order matters) and therefore needs amount outer, items inner.
- Related problems: Coin Change (minimize count instead of counting combinations, same unbounded shape), Combination Sum IV (the permutation-counting sibling of this exact problem).
