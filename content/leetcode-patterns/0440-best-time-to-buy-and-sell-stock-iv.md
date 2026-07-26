---
card: leetcode-patterns
gi: 440
slug: best-time-to-buy-and-sell-stock-iv
title: Best Time to Buy and Sell Stock IV
---

## 1. What it is

Same setup as before, but now you may complete AT MOST `k` transactions, for an arbitrary given `k`. Return the maximum total profit. Example: `k = 2`, `prices = [3,2,6,5,0,3]` → `7` (buy at `2`, sell at `6`: `+4`; buy at `0`, sell at `3`: `+3`; total `7`).

## 2. Why & when

Use this shape whenever the transaction limit `k` is a VARIABLE, not a fixed small constant — this generalizes Best Time to Buy and Sell Stock III (`k=2` specifically) into the fully general form, using ARRAYS of states indexed by transaction number instead of individually named variables.

## 3. Core concept

**Key idea:** track `buy[t]` and `sell[t]` for every transaction number `t` from `1` to `k`, where `buy[t]` = best profit having just bought for the `t`-th transaction, and `sell[t]` = best profit having just completed the `t`-th transaction.

**Steps:**
1. If `k >= n / 2` (where `n` is the number of days), there is no meaningful limit — enough transactions are allowed to capture every profitable day-to-day rise, so fall back to the unlimited-transactions greedy sum (Best Time to Buy and Sell Stock II's approach).
2. Otherwise, initialize `buy[t] = -infinity` for every `t`, and `sell[t] = 0` for every `t`.
3. For each price, for `t` from `1` to `k`: `buy[t] = max(buy[t], sell[t-1] - price)`; `sell[t] = max(sell[t], buy[t] + price)`.
4. The answer is `sell[k]`.

**Why the `k >= n/2` shortcut is valid:** the maximum number of NON-OVERLAPPING transactions possible in `n` days is at most `n/2` (each transaction needs at least a buy day and a sell day). Once `k` reaches or exceeds that ceiling, the transaction limit no longer constrains anything — the problem becomes identical to the unlimited case, which the simple greedy sum solves directly, avoiding unnecessary O(n*k) work for large `k`.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an array of buy and sell states indexed by transaction number, each transaction chained to the one before it exactly like the fixed two transaction case">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">buy[1] -&gt; sell[1] -&gt; buy[2] -&gt; sell[2] -&gt; ... -&gt; buy[k] -&gt; sell[k]</text>
    <rect x="10" y="40" width="330" height="24" fill="#3fb950"/><text x="175" y="57" fill="#0d1117" text-anchor="middle" font-size="10">same chain as Best Time III, generalized to k links instead of 2</text>
    <text x="10" y="80">if k &gt;= n/2: skip the DP entirely, sum every positive price step instead</text>
  </g>
</svg>

The same chained state idea from the fixed two-transaction problem, generalized to an array of length `k`.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStockIV.java
public class BestTimeToBuyAndSellStockIV {

    // KEY INSIGHT: this is Best Time III's chained buy/sell idea,
    // generalized to k links -- with a shortcut when k is so large
    // the limit stops mattering at all.

    static int maxProfit(int k, int[] prices) {
        int n = prices.length;
        if (n == 0 || k == 0) return 0;

        if (k >= n / 2) {
            int profit = 0;
            for (int i = 1; i < n; i++) {
                if (prices[i] > prices[i - 1]) profit += prices[i] - prices[i - 1];
            }
            return profit;
        }

        int[] buy = new int[k + 1];
        int[] sell = new int[k + 1];
        java.util.Arrays.fill(buy, Integer.MIN_VALUE);

        for (int price : prices) {
            for (int t = 1; t <= k; t++) {
                buy[t] = Math.max(buy[t], sell[t - 1] - price);
                sell[t] = Math.max(sell[t], buy[t] + price);
            }
        }
        return sell[k];
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(2, new int[]{2, 4, 1}));
        // 2
        System.out.println(maxProfit(2, new int[]{3, 2, 6, 5, 0, 3}));
        // 7
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStockIV.java`

## 6. Walkthrough

Trace `maxProfit(2, [3,2,6,5,0,3])` (`k=2`, `n=6`, so `k < n/2 = 3`, the full DP runs):

| price | buy[1] | sell[1] | buy[2] | sell[2] |
|---|---|---|---|---|
| 3 | -3 | 0 | -3 | 0 |
| 2 | -2 | 0 | -2 | 0 |
| 6 | -2 | 4 | -2 | 4 |
| 5 | -2 | 4 | -1 | 4 |
| 0 | 0 | 4 | 4 | 4 |
| 3 | 0 | 4 | 4 | 7 |

Final `sell[2] = 7`, matching the expected answer — buy at `2`, sell at `6` for `4`; buy at `0`, sell at `3` for `3`; total `7`. Time complexity is O(n*k) (or O(n) when the shortcut applies). Space is O(k).

## 7. Gotchas & takeaways

> Gotcha: skipping the `k >= n/2` shortcut is not a CORRECTNESS bug (the full DP still gives the right answer for any `k`), but for large `k` it wastes time and memory needlessly — always include the shortcut when `k` can be large relative to `n`.

- `buy[t]` and `sell[t]` arrays, chained exactly like Best Time III's four named variables, generalized to `k` transaction slots: the fully general limited-transactions template.
- The `k >= n/2` shortcut connects this problem directly back to Best Time II's simple greedy sum, once the transaction limit becomes non-binding.
- Related problems: Best Time to Buy and Sell Stock III (the hand-written `k=2` special case of this exact template), Best Time to Buy and Sell Stock II (the unlimited-transactions case this problem's shortcut falls back to).
