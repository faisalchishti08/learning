---
card: leetcode-patterns
gi: 435
slug: best-time-to-buy-and-sell-stock-ii
title: Best Time to Buy and Sell Stock II
---

## 1. What it is

Same setup as Best Time to Buy and Sell Stock, but now you may complete AS MANY transactions as you like (buy, then sell, then buy again, and so on), as long as you hold at most one share at a time. Return the MAXIMUM total profit. Example: `prices = [7,1,5,3,6,4]` → `7` (buy at `1`, sell at `5`: `+4`; buy at `3`, sell at `6`: `+3`; total `7`).

## 2. Why & when

Use this shape whenever a problem allows UNLIMITED transactions. With no transaction cap, the problem simplifies dramatically: it becomes equivalent to capturing every single UPWARD price movement, since any profitable rise can always be captured by a buy-sell pair somewhere within it.

## 3. Core concept

**Key idea:** sum up every day-to-day INCREASE in price.

**Steps:**
1. Initialize `profit = 0`.
2. For each day from the second onward: if `prices[i] > prices[i-1]`, add the difference `prices[i] - prices[i-1]` to `profit`.
3. Return `profit`.

**Why capturing every upward step works, even though it looks like many tiny trades instead of a few big ones:** any single profitable stretch (buy low, sell higher later) can be decomposed into the SUM of all its individual day-to-day increases — buying and selling on every up-day inside that stretch yields the EXACT SAME total profit as one single buy-low/sell-high trade covering the whole stretch, since the intermediate "sell then immediately re-buy at the same price" steps cancel out financially. With no limit on transaction count, there is never a reason NOT to capture every available upward step this way.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="prices rising and falling with each individual upward step highlighted and summed">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">prices = [7, 1, 5, 3, 6, 4]</text>
    <text x="10" y="45">day-to-day changes: -6, +4, -2, +3, -2</text>
    <rect x="10" y="65" width="240" height="24" fill="#3fb950"/><text x="130" y="82" fill="#0d1117" text-anchor="middle" font-size="10">sum of positive changes only: 4 + 3 = 7</text>
  </g>
</svg>

Summing every individual upward price movement gives the same total as capturing each profitable stretch as one trade.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStockII.java
public class BestTimeToBuyAndSellStockII {

    // KEY INSIGHT: with unlimited transactions, capturing every single
    // upward day-to-day move sums to the same total profit as any
    // larger buy-low/sell-high trade spanning the same stretch.

    static int maxProfit(int[] prices) {
        int profit = 0;
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > prices[i - 1]) {
                profit += prices[i] - prices[i - 1];
            }
        }
        return profit;
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{7, 1, 5, 3, 6, 4}));
        // 7
        System.out.println(maxProfit(new int[]{1, 2, 3, 4, 5}));
        // 4
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStockII.java`

## 6. Walkthrough

Trace `maxProfit([7,1,5,3,6,4])`:

| i | prices[i-1] -> prices[i] | change | profit added |
|---|---|---|---|
| 1 | 7 -> 1 | -6 | 0 (ignored) |
| 2 | 1 -> 5 | +4 | 4 |
| 3 | 5 -> 3 | -2 | 0 (ignored) |
| 4 | 3 -> 6 | +3 | 3 |
| 5 | 6 -> 4 | -2 | 0 (ignored) |

Total `profit = 4 + 3 = 7`, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this greedy "sum every positive step" shortcut works ONLY because transactions are UNLIMITED — the moment a problem adds a transaction cap (Best Time to Buy and Sell Stock III or IV) or a per-transaction FEE, this simple greedy approach stops being correct, and the full state-machine DP (tracking `hold`/`sold` states) is required instead.

- Summing every positive day-to-day change is mathematically equivalent to the state-machine DP's answer for the unlimited-transaction case — it is a valid SHORTCUT specifically because of this problem's lack of any transaction limit.
- This differs from Best Time to Buy and Sell Stock (limit of exactly one transaction), where the running-minimum technique is required instead.
- Related problems: Best Time to Buy and Sell Stock with Cooldown and Best Time to Buy and Sell Stock with Transaction Fee (also unlimited transactions, but with an added restriction or cost that breaks the simple greedy shortcut, requiring the full state-machine DP).
