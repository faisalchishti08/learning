---
card: leetcode-patterns
gi: 339
slug: dp-unbounded-knapsack-complexity-o-n-amount-time
title: "DP: Unbounded Knapsack — complexity: O(n*amount) time"
---

## 1. What it is

This page states and justifies the complexity of the Unbounded Knapsack pattern, and lists the problems that use it, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. If `amount` can be up to `10^4` and the number of item types `n` up to `100`, an O(n · amount) solution runs about `10^6` operations — comfortably fast. A brute-force recursive solution without memoization is exponential and will time out on the same input.

## 3. Core concept

**Time complexity: O(n · amount).** The DP fills a table (or array) of size `amount + 1`. For every amount from `1` to `amount`, the algorithm checks each of the `n` item types once. That is `n` units of work per amount, times `amount` amounts, giving O(n · amount).

**Space complexity: O(amount).** The 1D array holds one entry per possible amount; item types are only read, never stored per-item, so space does not depend on `n`.

**Why it is NOT exponential like brute force:** brute-force recursion without memoization re-solves the same sub-amount many times (e.g. reaching amount `5` via `1+1+3` and via `3+1+1` re-triggers identical recursive calls for "make amount `1`" over and over). The DP array caches each sub-amount's answer exactly once, so every `dp[a]` is computed a single time and then reused for every larger amount that needs it.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="grid of amount by item type showing total work as their product">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">n item types x amount possible totals = grid of work</text>
    <rect x="10" y="35" width="200" height="90" fill="none" stroke="#8b949e"/>
    <text x="110" y="85" text-anchor="middle">n x amount cells</text>
    <text x="230" y="85">each cell: O(1) work</text>
    <rect x="10" y="135" width="300" height="20" fill="#3fb950"/><text x="160" y="150" fill="#0d1117" text-anchor="middle" font-size="10">total time = O(n * amount)</text>
  </g>
</svg>

Every `(item, amount)` pair is visited once, each doing constant work: `n` types times `amount` totals.

## 5. Runnable example

```java
// UnboundedKnapsackComplexity.java
public class UnboundedKnapsackComplexity {

    // Confirms O(n * amount): counts array accesses done.
    static int countWaysWithCounter(int[] coins, int amount, long[] ops) {
        int[] dp = new int[amount + 1];
        dp[0] = 1;
        for (int coin : coins) {
            for (int a = coin; a <= amount; a++) {
                dp[a] += dp[a - coin];
                ops[0]++;
            }
        }
        return dp[amount];
    }

    public static void main(String[] args) {
        int[] coins = {1, 2, 5};
        int amount = 11;
        long[] ops = {0};
        int ways = countWaysWithCounter(coins, amount, ops);
        System.out.println("ways=" + ways + " ops=" + ops[0]);
        // ways=11, ops is bounded by n * amount = 3 * 11 = 33
    }
}
```

**How to run:** `java UnboundedKnapsackComplexity.java`

## 6. Walkthrough

1. `countWaysWithCounter` runs the standard unbounded-knapsack template while counting every inner-loop iteration in `ops`.
2. For `coins=[1,2,5]`, `amount=11`, the printed `ops` count stays at or below `n * amount = 33`, confirming the loop structure matches the claimed O(n · amount) bound.
3. Each inner-loop step does constant work (one array read, one add, one write), so total work scales linearly with the number of `(item, amount)` pairs — no hidden nested loop or repeated recomputation.
4. Compare this to a naive recursive solution with no memo table: it would re-explore the same `amount` value from many different call paths, multiplying work exponentially instead of linearly.
5. This confirms the pattern is efficient enough for typical constraints (`amount` up to `10^4`, `n` up to a few hundred), which is the check you should run before committing to this approach on a new problem.

## 7. Gotchas & takeaways

> Gotcha: forgetting to bound the inner loop correctly (e.g. starting at `0` instead of the item's weight) does not change the asymptotic bound much, but wastes real time and risks negative-index bugs — always start the amount loop at the item's own weight.

- Time: O(n · amount); space: O(amount) for the 1D form, O(n · amount) if you keep a 2D table for reconstruction.
- Compare against 0/1 Knapsack, which has the SAME O(n · capacity) time bound; the difference is only in loop direction and what gets reused, not in complexity.
- Problems that use this pattern: Coin Change, Coin Change II, Combination Sum IV, Perfect Squares, Minimum Cost For Tickets, Integer Break, Number of Dice Rolls With Target Sum, Word Break, Word Break II.
