---
card: leetcode-patterns
gi: 433
slug: dp-state-machine-stocks-complexity-o-n-or-o-n-k-time
title: "DP: State Machine (Stocks) — complexity: O(n) or O(n*k) time"
---

## 1. What it is

This page states and justifies the complexity of state-machine DP, and lists the problems that use this pattern, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. State-machine DP is exceptionally cheap compared to grid or interval DP — the number of states is FIXED (or scales only with a small parameter `k`), so the total work stays LINEAR, or close to it, in the length of the sequence.

## 3. Core concept

**Time complexity: O(n)** for a FIXED, small number of states (2 or 3 states — plain buy/sell, or buy/sell with cooldown/fee). Each of the `n` steps does a CONSTANT amount of work: one update per state.

**Time complexity: O(n * k)** when the state includes a transaction count `k` (Buy and Sell Stock IV) or a color count `k` (Paint House II) — each of the `n` steps now updates `O(k)` state variables instead of a fixed constant number.

**Space complexity: O(1)** for the fixed-state variants (only the previous step's few state values need to be kept). **O(k)** for the `k`-dependent variants (one value per transaction number or per color).

**Why this is so much cheaper than grid or interval DP:** the state does not scale with POSITION (like a grid's `r, c` or an interval's `i, j`) — it only scales with a small, problem-specific PARAMETER (`k`), which is often a small constant, or even just `2` or `3` for the simplest variants. This is the entire reason this pattern is worth recognizing separately: recognizing "this is a state machine, not a full grid/interval DP" turns what might look like a harder problem into a much cheaper one.

## 4. Diagram

<svg viewBox="0 0 480 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="fixed number of states means constant work per step giving linear total time versus k dependent states giving n times k time">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">fixed states (2-3): O(1) work per step -&gt; O(n) total</text>
    <text x="10" y="45" font-weight="bold">k-dependent states: O(k) work per step -&gt; O(n*k) total</text>
    <rect x="10" y="65" width="320" height="24" fill="#3fb950"/><text x="170" y="82" fill="#0d1117" text-anchor="middle" font-size="10">state count, not position, drives the complexity here</text>
  </g>
</svg>

The number of named states — not the sequence length itself — is what determines how much work each step costs.

## 5. Runnable example

```java
// StateMachineStocksComplexity.java
public class StateMachineStocksComplexity {

    // Confirms O(n*k): counts every buy/sell update performed.
    static int maxProfitKCountingOps(int k, int[] prices, long[] ops) {
        int n = prices.length;
        if (n == 0 || k == 0) return 0;
        int[] buy = new int[k + 1], sell = new int[k + 1];
        java.util.Arrays.fill(buy, Integer.MIN_VALUE);

        for (int price : prices) {
            for (int t = 1; t <= k; t++) {
                buy[t] = Math.max(buy[t], sell[t - 1] - price);
                sell[t] = Math.max(sell[t], buy[t] + price);
                ops[0]++;
            }
        }
        return sell[k];
    }

    public static void main(String[] args) {
        int[] prices = {3, 2, 6, 5, 0, 3};
        long[] ops = {0};
        int result = maxProfitKCountingOps(2, prices, ops);
        System.out.println("result=" + result + " ops=" + ops[0]);
        // ops == n * k == 6 * 2 == 12
    }
}
```

**How to run:** `java StateMachineStocksComplexity.java`

## 6. Walkthrough

1. `maxProfitKCountingOps` runs the standard `k`-transaction template while counting every `(buy, sell)` update pair in `ops`.
2. For `prices` of length `6` and `k=2`, the printed `ops` count is exactly `12`, confirming `n * k` work, not more.
3. If `k` were fixed at a small CONSTANT (like the plain 2-state buy/sell problem, effectively `k=1` with no outer loop), this same reasoning collapses to plain O(n).
4. Doubling `k` to `4` would double `ops` to `24` — a direct, linear relationship with `k`, confirming the O(n*k) bound is tight, not a loose over-estimate.
5. Compare this to interval DP's O(n^3): state-machine DP is fundamentally cheaper, specifically because its state does not multiply with the SQUARE (or cube) of the position count.

## 7. Gotchas & takeaways

> Gotcha: when `k` is very large (specifically `k >= n / 2`), continuing to run the O(n*k) template WASTES time and space for no added benefit — beyond that point, every profitable single-day trade can already be taken without hitting the transaction limit, so the problem reduces exactly to the UNLIMITED-transactions case, solvable in plain O(n).

- Time: O(n) for fixed small state counts; O(n*k) when the state scales with a parameter `k`. Space: O(1) or O(k), respectively.
- The complexity is driven by the NUMBER OF NAMED STATES, not by the sequence length alone — always count your states before estimating.
- Problems that use this pattern: Best Time to Buy and Sell Stock, Best Time to Buy and Sell Stock II, Best Time to Buy and Sell Stock with Cooldown, Best Time to Buy and Sell Stock with Transaction Fee, Paint House, Best Time to Buy and Sell Stock III, Best Time to Buy and Sell Stock IV, Maximum Profit in Job Scheduling, Paint House II.
