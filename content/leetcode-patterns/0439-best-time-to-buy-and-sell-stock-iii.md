---
card: leetcode-patterns
gi: 439
slug: best-time-to-buy-and-sell-stock-iii
title: Best Time to Buy and Sell Stock III
---

## 1. What it is

Same setup as the base problem, but now you may complete AT MOST TWO transactions (you must sell before buying again). Return the maximum total profit. Example: `prices = [3,3,5,0,0,3,1,4]` → `6` (buy at `0`, sell at `3`: `+3`; buy at `1`, sell at `4`: `+3`; total `6`).

## 2. Why & when

Use this shape whenever a problem caps the transaction count at a SMALL, FIXED number (here, exactly two). This is the specific `k=2` case of the general limited-transactions problem — worth its own named states, since a fixed small `k` can be written out explicitly, without needing a loop or array indexed by transaction number.

## 3. Core concept

**Key idea:** track FOUR states: `buy1` (bought during the first transaction), `sell1` (sold, completing the first transaction), `buy2` (bought during the second transaction, using profit from the first), and `sell2` (sold, completing the second transaction).

**Steps:**
1. Initialize `buy1 = -infinity`, `sell1 = 0`, `buy2 = -infinity`, `sell2 = 0`.
2. For each price: `buy1 = max(buy1, -price)`; `sell1 = max(sell1, buy1 + price)`; `buy2 = max(buy2, sell1 - price)`; `sell2 = max(sell2, buy2 + price)`.
3. The answer is `sell2`.

**Why `buy2` is computed from `sell1`, not from `0`:** the second transaction can only begin using money left over AFTER the first transaction has completed — `sell1` already represents the best possible profit from a completed first transaction, so subtracting today's price from it correctly models "use the first transaction's profit to fund the second purchase." This chaining (`buy1 -> sell1 -> buy2 -> sell2`) is what enforces that the two transactions happen in order, without overlapping.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="four states buy1 sell1 buy2 sell2 chained so each depends only on the state directly before it in the chain">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">buy1 -&gt; sell1 -&gt; buy2 -&gt; sell2, each state built from the one before it</text>
    <rect x="20" y="40" width="80" height="26" fill="#3fb950"/><text x="60" y="58" text-anchor="middle" font-size="10" fill="#0d1117">buy1</text>
    <rect x="130" y="40" width="80" height="26" fill="#30363d" stroke="#8b949e"/><text x="170" y="58" text-anchor="middle" font-size="10">sell1</text>
    <rect x="240" y="40" width="80" height="26" fill="#3fb950"/><text x="280" y="58" text-anchor="middle" font-size="10" fill="#0d1117">buy2</text>
    <rect x="350" y="40" width="80" height="26" fill="#30363d" stroke="#8b949e"/><text x="390" y="58" text-anchor="middle" font-size="10">sell2</text>
    <rect x="10" y="80" width="330" height="24" fill="#3fb950"/><text x="175" y="97" fill="#0d1117" text-anchor="middle" font-size="10">the second transaction is funded by the first one's profit</text>
  </g>
</svg>

Four states, chained in a straight line — each one is built only from the state directly before it.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStockIII.java
public class BestTimeToBuyAndSellStockIII {

    // KEY INSIGHT: buy2 is computed FROM sell1, not from scratch --
    // this chaining (buy1 -> sell1 -> buy2 -> sell2) is what enforces
    // that the two transactions happen strictly in order.

    static int maxProfit(int[] prices) {
        int buy1 = Integer.MIN_VALUE, sell1 = 0, buy2 = Integer.MIN_VALUE, sell2 = 0;
        for (int price : prices) {
            buy1 = Math.max(buy1, -price);
            sell1 = Math.max(sell1, buy1 + price);
            buy2 = Math.max(buy2, sell1 - price);
            sell2 = Math.max(sell2, buy2 + price);
        }
        return sell2;
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{3, 3, 5, 0, 0, 3, 1, 4}));
        // 6
        System.out.println(maxProfit(new int[]{1, 2, 3, 4, 5}));
        // 4
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStockIII.java`

## 6. Walkthrough

Trace key steps for `prices = [3,3,5,0,0,3,1,4]`:

| price | buy1 | sell1 | buy2 | sell2 |
|---|---|---|---|---|
| 3 | -3 | 0 | -3 | 0 |
| 5 | -3 | 2 | -3 | 2 |
| 0 | 0 | 2 | 2 | 2 |
| 3 | 0 | 3 | 2 | 5 |
| 4 | 0 | 4 | 3 | 6 |

Final `sell2 = 6`, matching the expected answer. Time complexity is O(n) (four states is a constant). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: `[1,2,3,4,5]` gives `4`, not `8` — even though the price strictly rises every day, the problem caps transactions at TWO, and there is never a mid-sequence dip to sell into and re-buy from, so the optimal strategy is one single buy-at-`1`, sell-at-`5` transaction, leaving the second transaction UNUSED (its cost simply never improves on `0`).

- Four explicit states, chained `buy1 -> sell1 -> buy2 -> sell2`: the hand-written special case of the general `k`-transaction template for exactly `k=2`.
- Writing out named variables (instead of arrays) is only practical because `k` is small and FIXED — for a general `k`, use the array-indexed template from Best Time to Buy and Sell Stock IV instead.
- Related problems: Best Time to Buy and Sell Stock IV (the general `k`-transaction version, of which this problem is the `k=2` special case), Best Time to Buy and Sell Stock (the `k=1` special case).
