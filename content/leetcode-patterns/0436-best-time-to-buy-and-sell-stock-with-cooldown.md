---
card: leetcode-patterns
gi: 436
slug: best-time-to-buy-and-sell-stock-with-cooldown
title: Best Time to Buy and Sell Stock with Cooldown
---

## 1. What it is

Same setup as unlimited transactions, but after SELLING, you must wait one full day (a "cooldown") before you are allowed to buy again. Return the maximum total profit. Example: `prices = [1,2,3,0,2]` → `3`.

## 2. Why & when

Use this shape whenever unlimited transactions come with a WAITING PERIOD after selling. The cooldown rule breaks the simple "sum every positive step" greedy shortcut from the plain unlimited-transactions problem, since a cooldown day can force you to miss capturing a small upward move right after selling.

## 3. Core concept

**Key idea:** track THREE states across the days: `hold` (currently holding a share), `sold` (just sold TODAY — cannot buy tomorrow), and `rest` (not holding, and ELIGIBLE to buy).

**Steps:**
1. Initialize `hold = -prices[0]` (bought on day 0), `sold = 0`, `rest = 0`.
2. For each subsequent day, using YESTERDAY's values: `hold = max(prevHold, prevRest - price)` (either keep holding, or buy today — only allowed from `rest`, never from `sold`); `sold = prevHold + price` (sell today, having held from before); `rest = max(prevRest, prevSold)` (either was already resting, or the cooldown from yesterday's sale has now passed).
3. The answer is `max(sold, rest)` after the last day (you would never want to end while still holding a share).

**Why `hold` can only transition from `rest`, never from `sold`:** the cooldown rule specifically forbids buying the day immediately after selling — so a purchase today is only valid if you were ALREADY eligible to buy (in `rest`) yesterday, not if you had JUST sold yesterday (`sold`). This one restriction is the entire difference between this problem and the unlimited-transactions version.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three states hold sold and rest with hold only reachable from rest or itself, sold only from hold, and rest from either rest or sold">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">hold(today) = max(hold(yst), rest(yst) - price) -- NEVER from sold(yst)</text>
    <text x="10" y="45" font-weight="bold">sold(today) = hold(yst) + price</text>
    <text x="10" y="70" font-weight="bold">rest(today) = max(rest(yst), sold(yst))</text>
    <rect x="10" y="90" width="330" height="24" fill="#3fb950"/><text x="175" y="107" fill="#0d1117" text-anchor="middle" font-size="10">the missing hold-from-sold arrow IS the cooldown rule</text>
  </g>
</svg>

The cooldown rule is encoded entirely by which transitions are absent from the state diagram, not by any extra check in the code.

## 5. Runnable example

```java
// BestTimeToBuyAndSellStockWithCooldown.java
public class BestTimeToBuyAndSellStockWithCooldown {

    // KEY INSIGHT: "hold" can only be entered from "rest," never from
    // "sold" -- that missing transition IS the cooldown rule.

    static int maxProfit(int[] prices) {
        int n = prices.length;
        if (n == 0) return 0;
        int hold = -prices[0], sold = 0, rest = 0;

        for (int i = 1; i < n; i++) {
            int prevHold = hold, prevSold = sold, prevRest = rest;
            hold = Math.max(prevHold, prevRest - prices[i]);
            sold = prevHold + prices[i];
            rest = Math.max(prevRest, prevSold);
        }
        return Math.max(sold, rest);
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{1, 2, 3, 0, 2}));
        // 3
        System.out.println(maxProfit(new int[]{1}));
        // 0
    }
}
```

**How to run:** `java BestTimeToBuyAndSellStockWithCooldown.java`

## 6. Walkthrough

Trace `maxProfit([1,2,3,0,2])`:

| day | price | hold | sold | rest |
|---|---|---|---|---|
| 0 | 1 | -1 | 0 | 0 |
| 1 | 2 | max(-1, 0-2)=-1 | -1+2=1 | max(0,0)=0 |
| 2 | 3 | max(-1, 0-3)=-1 | -1+3=2 | max(0,1)=1 |
| 3 | 0 | max(-1, 1-0)=1 | -1+0=-1 | max(1,2)=2 |
| 4 | 2 | max(1, 2-2)=1 | 1+2=3 | max(2,-1)=2 |

Final `max(sold=3, rest=2) = 3`, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing `hold`, `sold`, and `rest` for a NEW day must all read the PREVIOUS day's values — updating `hold` in place and then using the NEW `hold` to compute `sold` on the SAME day would be wrong here, since `sold` should reflect "I held from some earlier day, and I am selling right now," not "I just bought today and am selling today" (a same-day round trip the problem does not intend).

- Three named states (`hold`, `sold`, `rest`), with `hold` reachable ONLY from `rest`: this single missing transition is the entire cooldown mechanism.
- The final answer is `max(sold, rest)`, never `hold` — ending the sequence while still holding a share can never be optimal, since selling on the last day (or having already sold) is always at least as good.
- Related problems: Best Time to Buy and Sell Stock II (the same unlimited-transactions idea, without the cooldown restriction — collapses to two states instead of three), Best Time to Buy and Sell Stock with Transaction Fee (a different restriction — a cost per sale — added to the same base problem).
