---
card: leetcode-patterns
gi: 340
slug: coin-change
title: Coin Change
---

## 1. What it is

Given an array `coins` of coin denominations and an integer `amount`, return the FEWEST number of coins needed to make exactly `amount`. Each coin denomination is available in unlimited supply. If `amount` cannot be made, return `-1`. Example: `coins = [1,2,5]`, `amount = 11` → `3` (`5 + 5 + 1`).

## 2. Why & when

This is the textbook Unbounded Knapsack MINIMUM-count problem: an unlimited supply of item types (coins), a target amount, minimize the count used. Use this shape whenever a problem asks for the fewest "pieces" (coins, squares, jumps) to exactly reach a target, with each piece type reusable any number of times.

## 3. Core concept

**Key idea:** build `dp[a]` = fewest coins to make amount `a`, for every `a` from `0` to `amount`, using smaller already-solved amounts.

**Steps:**
1. Create `dp[amount + 1]`, filled with a sentinel "impossible" value (larger than any real answer, e.g. `amount + 1`). Set `dp[0] = 0` (zero coins make amount zero).
2. For `a` from `1` to `amount`, for each `coin` in `coins` with `coin <= a`: `dp[a] = min(dp[a], dp[a - coin] + 1)`.
3. Return `dp[amount]` if it is still `<= amount`, else `-1`.

**Why it is correct:** any way to make amount `a` uses SOME last coin `c`; removing that one coin leaves an optimal way to make `a - c`. Trying every possible last coin and taking the minimum over all of them is exactly what the inner loop does, so `dp[a]` ends up holding the true minimum, built from already-correct smaller answers.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for coins 1,2,5 filling amounts 0 through 11, showing dp 11 built from dp 6 plus one coin of value 5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">coins=[1,2,5], amount=11</text>
    <text x="10" y="45">dp[6]=2 (5+1)</text>
    <text x="10" y="65">dp[11] = min(dp[11], dp[11-5]+1) = min(dp[11], dp[6]+1) = 3</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[11] = 3 coins: 5+5+1</text>
  </g>
</svg>

Each `dp[a]` is one plus the best answer for some smaller amount, minimized over every coin choice.

## 5. Runnable example

```java
// CoinChange.java
public class CoinChange {

    // KEY INSIGHT: minimum coins to make an amount is unbounded
    // knapsack's MINIMIZE variant -- dp[a] = min over every coin of
    // dp[a - coin] + 1.

    static int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        java.util.Arrays.fill(dp, amount + 1);
        dp[0] = 0;

        for (int a = 1; a <= amount; a++) {
            for (int coin : coins) {
                if (coin <= a) {
                    dp[a] = Math.min(dp[a], dp[a - coin] + 1);
                }
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }

    public static void main(String[] args) {
        System.out.println(coinChange(new int[]{1, 2, 5}, 11));
        // 3
        System.out.println(coinChange(new int[]{2}, 3));
        // -1
    }
}
```

**How to run:** `java CoinChange.java`

## 6. Walkthrough

Trace `coinChange([1,2,5], 11)`:

| amount a | dp[a] before coin 5 | after considering coin 5 |
|---|---|---|
| 0 | 0 | 0 |
| 5 | 1 (one coin of 5, via 1+1+1+1+1 beaten by direct 5) | 1 |
| 6 | 2 (5+1) | 2 |
| 10 | 2 (5+5) | 2 |
| 11 | 3 (5+5+1, via coin 1) | 3 (dp[6]+1 = 2+1 = 3) |

`dp[11] = 3`, matching `5 + 5 + 1`. Time complexity is O(n · amount), where `n` is the number of coin denominations. Space is O(amount).

## 7. Gotchas & takeaways

> Gotcha: initializing `dp` with `0` instead of a large sentinel makes every amount look "already reachable with zero coins," silently producing wrong (too-small) answers — use a sentinel bigger than any valid answer, and check it at the end to detect "impossible."

- The sentinel trick (`amount + 1`) works because no valid answer can ever legitimately need more than `amount` coins (using all coin-value-`1`s in the worst case, if `1` is present).
- `dp[a] = min(dp[a], dp[a - coin] + 1)` is the general unbounded-knapsack MINIMIZE transition — swap `min`/`+1` for `+=` to get a COUNTING variant instead (see Coin Change II).
- Related problems: Coin Change II (count combinations instead of minimizing), Perfect Squares (same minimize-count shape, but "coins" are perfect squares).
