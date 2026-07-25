---
card: leetcode-patterns
gi: 344
slug: minimum-cost-for-tickets
title: Minimum Cost For Tickets
---

## 1. What it is

Given a sorted array `days` (the days within a year you need to travel) and `costs = [cost1, cost7, cost30]` (the price of a 1-day, 7-day, or 30-day pass), return the MINIMUM total cost to cover every day in `days`. Passes bought on day `d` cover a rolling window of consecutive days starting at `d`. Example: `days = [1,4,6,7,8,20]`, `costs = [2,7,15]` → `11`.

## 2. Why & when

This is Unbounded Knapsack in disguise, over the TIMELINE instead of an amount: each "item" is a pass TYPE (1-day, 7-day, 30-day), reusable any number of times, and the "capacity" being filled is the set of travel days. Recognize this shape whenever a problem gives several reusable "duration" or "batch" options with different costs, and asks for the minimum cost to cover a sequence of required days or events.

## 3. Core concept

**Key idea:** build `dp[d]` = minimum cost to cover all travel days up to calendar day `d`, but only compute it for days you actually need — on days with no travel, the cost does not change from the day before.

**Steps:**
1. Let `lastDay` be the final entry in `days`. Create `dp[lastDay + 1]`, with `dp[0] = 0`.
2. For `d` from `1` to `lastDay`: if `d` is NOT in `days`, `dp[d] = dp[d - 1]` (nothing to buy, cost carries over unchanged).
3. If `d` IS in `days`, `dp[d] = min(dp[d-1] + cost1, dp[max(0, d-7)] + cost7, dp[max(0, d-30)] + cost30)` (try each pass type, ending exactly on day `d`, and take the cheapest).
4. Return `dp[lastDay]`.

**Why it is correct:** for a travel day `d`, the LAST pass bought must cover `d` — it started somewhere between `d-29` and `d` (for the 30-day pass), `d-6` and `d` (7-day), or exactly `d` (1-day). Rather than trying every start day, the trick is to always attribute the pass's cost to its LAST covered day and look back to the state BEFORE that pass's window began — `dp[d-1]`, `dp[d-7]`, or `dp[d-30]` — since everything before the window is unaffected by this pass.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array over calendar days with three ticket options each looking back a different window length">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">travel day d=8; costs=[2,7,15]</text>
    <text x="10" y="45">1-day: dp[7] + 2</text>
    <text x="10" y="65">7-day: dp[max(0,8-7)] + 7 = dp[1] + 7</text>
    <text x="10" y="85">30-day: dp[max(0,8-30)] + 15 = dp[0] + 15</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">dp[8] = min of the three options</text>
  </g>
</svg>

Each pass type looks back by its own window length, from the day right before that pass would need to start.

## 5. Runnable example

```java
// MinimumCostForTickets.java
public class MinimumCostForTickets {

    // KEY INSIGHT: unbounded knapsack over the calendar -- pass types
    // are reusable items; non-travel days simply copy the previous
    // day's cost forward.

    static int mincostTickets(int[] days, int[] costs) {
        int lastDay = days[days.length - 1];
        boolean[] isTravelDay = new boolean[lastDay + 1];
        for (int d : days) isTravelDay[d] = true;

        int[] dp = new int[lastDay + 1];
        for (int d = 1; d <= lastDay; d++) {
            if (!isTravelDay[d]) {
                dp[d] = dp[d - 1];
                continue;
            }
            int oneDay = dp[d - 1] + costs[0];
            int sevenDay = dp[Math.max(0, d - 7)] + costs[1];
            int thirtyDay = dp[Math.max(0, d - 30)] + costs[2];
            dp[d] = Math.min(oneDay, Math.min(sevenDay, thirtyDay));
        }
        return dp[lastDay];
    }

    public static void main(String[] args) {
        int[] days = {1, 4, 6, 7, 8, 20};
        int[] costs = {2, 7, 15};
        System.out.println(mincostTickets(days, costs));
        // 11
    }
}
```

**How to run:** `java MinimumCostForTickets.java`

## 6. Walkthrough

Trace `mincostTickets([1,4,6,7,8,20], [2,7,15])`:

| day d | travel? | dp[d] | best option |
|---|---|---|---|
| 1 | yes | 2 | dp[0]+2 (1-day pass) |
| 4 | yes | 4 | dp[3]+2 (1-day pass) |
| 6 | yes | 6 | dp[5]+2 (1-day pass) |
| 7 | yes | 7 | dp[0]+7 (7-day pass, cheaper than dp[6]+2=8) |
| 8 | yes | 9 | dp[7]+2 or dp[1]+7, both give 9 |
| 20 | yes | 11 | dp[19]+2 (1-day pass, cheapest here) |

`dp[20] = 11`, matching the expected answer: a 7-day pass on day 7 covers days 7–13, and 1-day passes cover the rest. Time complexity is O(lastDay). Space is O(lastDay).

## 7. Gotchas & takeaways

> Gotcha: using `days.length` (number of travel days) as the array size instead of `lastDay` (the calendar span) is a common mix-up — the DP must iterate over EVERY calendar day, including non-travel days, so the array must be sized by the calendar, not by the count of travel days.

- `Math.max(0, d - windowLength)` guards against negative indices when a pass's window would reach before day `1`.
- This problem shows Unbounded Knapsack applied to a TIMELINE rather than a numeric amount — the "items" are pass durations, and the "amount" is calendar days, with non-travel days simply skipped (`dp[d] = dp[d-1]`).
- Related problems: Coin Change (same minimize-count shape over a plain numeric amount), House Robber (a simpler "skip or take" DP also indexed by position, though not knapsack).
