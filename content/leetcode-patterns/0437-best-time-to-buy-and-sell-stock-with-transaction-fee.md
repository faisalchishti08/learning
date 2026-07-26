---
card: leetcode-patterns
gi: 437
slug: best-time-to-buy-and-sell-stock-with-transaction-fee
title: Best Time to Buy and Sell Stock with Transaction Fee
---

## 1. What it is

Same setup as unlimited transactions, but each SALE costs a fixed transaction `fee`, deducted from that sale's proceeds. Return the maximum total profit after fees. Example: `prices = [1,3,2,8,4,9]`, `fee = 2` → `8`.

## 2. Why & when

Use this shape whenever unlimited transactions come with a flat COST per trade. The fee changes the state-machine DP only in ONE place: subtract the fee at the moment of selling. It does not need a third state (unlike Cooldown), since there is no restriction on WHEN you can buy again — only a cost attached to selling.

## 3. Core concept

**Key idea:** track TWO states: `hold` (currently holding a share) and `cash` (not holding, holding money instead).

**Steps:**
1. Initialize `hold = -prices[0]`, `cash = 0`.
2. For each subsequent day, using YESTERDAY's values: `hold = max(prevHold, prevCash - price)` (keep holding, or buy today); `cash = max(prevCash, prevHold + price - fee)` (keep resting, or sell today and pay the fee).
3. The answer is `cash` after the last day.

**Why the fee is subtracted at the SELL step, not the buy step:** the problem charges the fee per completed transaction, and a transaction is only "completed" at the moment of sale — subtracting it earlier (at buy time) would double-count it if the same share is never sold, and subtracting it anywhere else would not correctly attribute the cost to the specific sale that incurred it.

## 4. Diagram

<svg viewBox="0 0 480 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two states hold and cash with the fee subtracted specifically at the moment of transitioning from hold to cash">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">hold(today) = max(hold(yst), cash(yst) - price)</text>
    <text x="10" y="45" font-weight="bold">cash(today) = max(cash(yst), hold(yst) + price - fee)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">fee subtracted exactly once, at the sell transition</text>
  </g>
</svg>

The transaction fee is charged exactly once, at the point of selling — nowhere else in the update.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStockWithTransactionFee.java
public class BestTimeToBuyAndSellStockWithTransactionFee {

    // KEY INSIGHT: the fee is charged exactly once, at the sell
    // transition -- no third state (like cooldown's "rest") is needed,
    // since there is no restriction on when you can buy again.

    static int maxProfit(int[] prices, int fee) {
        int hold = -prices[0], cash = 0;
        for (int i = 1; i < prices.length; i++) {
            int prevHold = hold, prevCash = cash;
            hold = Math.max(prevHold, prevCash - prices[i]);
            cash = Math.max(prevCash, prevHold + prices[i] - fee);
        }
        return cash;
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{1, 3, 2, 8, 4, 9}, 2));
        // 8
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStockWithTransactionFee.java`

## 6. Walkthrough

Trace `maxProfit([1,3,2,8,4,9], fee=2)`:

| day | price | hold | cash |
|---|---|---|---|
| 0 | 1 | -1 | 0 |
| 1 | 3 | max(-1, 0-3)=-1 | max(0, -1+3-2)=0 |
| 2 | 2 | max(-1, 0-2)=-1 | max(0, -1+2-2)=0 |
| 3 | 8 | max(-1, 0-8)=-1 | max(0, -1+8-2)=5 |
| 4 | 4 | max(-1, 5-4)=1 | max(5, -1+4-2)=5 |
| 5 | 9 | max(1, 5-9)=1 | max(5, 1+9-2)=8 |

Final `cash = 8`, matching the expected answer: buy at `1`, sell at `8` (profit `7 - 2 = 5`), buy at `4`, sell at `9` (profit `5 - 2 = 3`), total `8`. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: subtracting the fee at BUY time instead of SELL time gives the same FINAL answer mathematically (the fee is paid once per round trip either way), but it changes what intermediate values MEAN — pick one convention and apply it consistently; mixing both would double- or never-charge the fee.

- Only TWO states are needed here (`hold`, `cash`) — the fee changes the ARITHMETIC of one transition, but not the STRUCTURE of the state machine, unlike Cooldown, which needs a genuinely new third state.
- `cash = max(prevCash, prevHold + price - fee)`: the fee applies exactly once, at the point of selling.
- Related problems: Best Time to Buy and Sell Stock with Cooldown (a different kind of restriction — a forced wait — needing an actual new state, not just an arithmetic tweak), Best Time to Buy and Sell Stock II (the fee-free, restriction-free base case).
