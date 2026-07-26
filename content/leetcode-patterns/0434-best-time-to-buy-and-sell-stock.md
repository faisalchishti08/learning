---
card: leetcode-patterns
gi: 434
slug: best-time-to-buy-and-sell-stock
title: Best Time to Buy and Sell Stock
---

## 1. What it is

Given an array of daily stock prices, you may buy on ONE day and sell on a LATER day, at most ONCE. Return the MAXIMUM profit you can achieve, or `0` if no profit is possible. Example: `prices = [7,1,5,3,6,4]` → `5` (buy at `1`, sell at `6`).

## 2. Why & when

Use this shape whenever a problem allows exactly ONE buy and ONE sell. It is the simplest possible state-machine DP: just two states, "holding a share" or "not holding one," with no cooldown, no fee, and no transaction limit beyond the single implicit one.

## 3. Core concept

**Key idea:** track the MINIMUM price seen so far, and the MAXIMUM profit achievable by selling TODAY given that minimum.

**Steps:**
1. Initialize `minPrice = prices[0]` and `maxProfit = 0`.
2. For each subsequent day's price: update `maxProfit = max(maxProfit, price - minPrice)` (selling today, having bought at the best price seen so far), THEN update `minPrice = min(minPrice, price)` (today might be an even better day to have bought).
3. Return `maxProfit`.

**Why it is correct:** for any day chosen as the SELL day, the best possible BUY day is whichever earlier day had the lowest price — there is never a reason to buy at a higher earlier price when a lower one was available. Tracking the running minimum, and checking the profit of selling at every day against it, considers every valid buy/sell pair implicitly, without needing to check them all explicitly.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="prices plotted over time with the running minimum price marked and the largest gap from that minimum to a later price highlighted">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">prices = [7, 1, 5, 3, 6, 4]</text>
    <text x="10" y="45">running min after each day: 7, 1, 1, 1, 1, 1</text>
    <text x="10" y="65">profit if selling each day: -, 0, 4, 2, 5, 3</text>
    <rect x="10" y="85" width="200" height="24" fill="#3fb950"/><text x="110" y="102" fill="#0d1117" text-anchor="middle" font-size="10">max profit = 5 (buy at 1, sell at 6)</text>
  </g>
</svg>

The best profit is the largest gap between the running minimum price and any later price.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStock.java
public class BestTimeToBuyAndSellStock {

    // KEY INSIGHT: for any sell day, the best buy day is the lowest
    // price seen so far -- track that running minimum in one pass.

    static int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE;
        int maxProfit = 0;
        for (int price : prices) {
            maxProfit = Math.max(maxProfit, price - minPrice);
            minPrice = Math.min(minPrice, price);
        }
        return maxProfit;
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{7, 1, 5, 3, 6, 4}));
        // 5
        System.out.println(maxProfit(new int[]{7, 6, 4, 3, 1}));
        // 0
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStock.java`

## 6. Walkthrough

Trace `maxProfit([7,1,5,3,6,4])`:

| price | minPrice before | profit if sold today | maxProfit after | minPrice after |
|---|---|---|---|---|
| 7 | inf | -inf (ignored) | 0 | 7 |
| 1 | 7 | -6 (ignored, negative) | 0 | 1 |
| 5 | 1 | 4 | 4 | 1 |
| 3 | 1 | 2 | 4 | 1 |
| 6 | 1 | 5 | 5 | 1 |
| 4 | 1 | 3 | 5 | 1 |

Final `maxProfit = 5`, matching the expected answer. Time complexity is O(n) (a single pass). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: if prices only ever DECREASE (like `[7,6,4,3,1]`), every day's profit-if-sold is negative or zero, and `maxProfit` correctly stays at its initial value of `0` — the problem explicitly allows "do nothing" as a valid outcome, so never return a negative profit.

- Track `minPrice` and `maxProfit` together in ONE pass — this is the simplest possible state-machine DP, with only an implicit two-state shape ("bought at the best price so far" vs. "haven't bought yet").
- This is the base case that every other problem in this section generalizes: allowing MULTIPLE transactions (Buy and Sell Stock II), a COOLDOWN (with Cooldown), a FEE (with Transaction Fee), or a TRANSACTION LIMIT (III and IV).
- Related problems: Best Time to Buy and Sell Stock II (unlimited transactions instead of exactly one), Best Time to Buy and Sell Stock III (at most two transactions).
