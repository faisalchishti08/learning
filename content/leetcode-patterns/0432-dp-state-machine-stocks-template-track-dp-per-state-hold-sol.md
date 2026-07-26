---
card: leetcode-patterns
gi: 432
slug: dp-state-machine-stocks-template-track-dp-per-state-hold-sol
title: "DP: State Machine (Stocks) — template: track dp per state (hold/sold/rest) across time"
---

## 1. What it is

This page gives the general recipe for building a state-machine DP: name every reachable state, draw the ALLOWED transitions between them, then write one update line per state, re-evaluated once per step of the sequence.

## 2. Why & when

Use this template as the STARTING POINT for any stock (or stock-like) problem: identify the states the problem actually needs, work out which state can transition into which, then translate that directly into code. The states needed range from as few as two (a simple "holding or not") to as many as `2k + 1` (limited transactions) or `k` (painting with `k` colors).

## 3. Core concept

**Step 1 — enumerate the states.** For the basic stock problem: `hold` (currently holding a share) and `cash`/`sold` (not holding). For cooldown: add `rest` (not holding, and eligible to buy). For a transaction limit `k`: `buy[t]` and `sell[t]` for each transaction number `t` from `1` to `k`.

**Step 2 — draw the allowed transitions.** Write out, in plain words, which state can come from which: "you can only enter `hold` from `rest`/`cash` (by buying) or by staying in `hold`"; "you can only enter `sold` from `hold` (by selling)"; "a cooldown-driven `rest` can come from `rest` or from `sold`, but never directly from `hold`."

**Step 3 — write one update per state, per step.** For each state, its NEW value is the BEST (`max`, usually) of every allowed transition into it, using the PREVIOUS step's values (never the just-updated ones, unless the transition legitimately allows staying in the same state without external input).

**Step 4 — initialize the base case.** Typically, `hold`-type states start at `-price[0]` or `-infinity` (impossible before any purchase), and `cash`/`rest`-type states start at `0`.

**Step 5 — read the final answer from whichever "not holding" state is best at the end** (you would never want to end the sequence still holding a share, if selling costs nothing extra).

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="general recipe boxes enumerate states then draw transitions then write update equations then initialize then read the answer">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">1. enumerate states -&gt; 2. draw allowed transitions -&gt; 3. write per-state updates</text>
    <text x="10" y="45" font-weight="bold">4. initialize base case -&gt; 5. read answer from the best "not holding" state</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">the same 5-step recipe scales from 2 states up to 2k+1 states</text>
  </g>
</svg>

The same five-step recipe applies whether the problem needs two states or dozens.

## 5. Runnable example

```java
// StateMachineStocksTemplate.java
public class StateMachineStocksTemplate {

    // General template applied to "at most k transactions": states are
    // buy[t] (bought during transaction t) and sell[t] (sold during
    // transaction t), for t = 1..k.
    static int maxProfitKTransactions(int k, int[] prices) {
        int n = prices.length;
        if (n == 0 || k == 0) return 0;

        int[] buy = new int[k + 1];
        int[] sell = new int[k + 1];
        java.util.Arrays.fill(buy, Integer.MIN_VALUE);

        for (int price : prices) {
            for (int t = 1; t <= k; t++) {
                buy[t] = Math.max(buy[t], sell[t - 1] - price);   // enter hold for transaction t
                sell[t] = Math.max(sell[t], buy[t] + price);      // exit hold, completing transaction t
            }
        }
        return sell[k];
    }

    public static void main(String[] args) {
        System.out.println(maxProfitKTransactions(2, new int[]{3, 2, 6, 5, 0, 3}));
        // 7
    }
}
```

**How to run:** `java StateMachineStocksTemplate.java`

## 6. Walkthrough

1. States: `buy[t]` (best profit having just bought shares for the `t`-th transaction) and `sell[t]` (best profit having just sold, completing the `t`-th transaction), for each `t` from `1` to `k`.
2. Allowed transitions: `buy[t]` can only follow `sell[t-1]` (you must complete transaction `t-1` before starting transaction `t`) or stay in `buy[t]` (do nothing today); `sell[t]` can only follow `buy[t]`.
3. Base case: every `buy[t]` starts at `-infinity` (`Integer.MIN_VALUE`), since no transaction has begun; every `sell[t]` starts at `0` implicitly (the default array value).
4. Running the template on `prices = [3,2,6,5,0,3]` with `k=2` gives `sell[2] = 7`, matching the known best two-transaction profit (buy at `2`, sell at `6`: `+4`; buy at `0`, sell at `3`: `+3`; total `7`).
5. This same five-step process, with different state names and transition rules, produces every other problem's solution in this section.

## 7. Gotchas & takeaways

> Gotcha: updating `sell[t]` using the ALREADY-UPDATED `buy[t]` from the SAME day is intentional here (both loops run within the same price iteration) — this correctly allows a same-day buy-then-sell combination when that is profitable, matching how the problem is meant to be interpreted (profit is evaluated per price point, not per literal calendar transaction restriction).

- The five-step recipe (enumerate states, draw transitions, write updates, initialize, read the answer) applies to every problem in this section, no matter how many states it needs.
- `Integer.MIN_VALUE` as the initial value for an impossible/unreached "hold" state correctly prevents that branch from ever winning a `max`, without needing a separate boolean "is this state reachable yet" flag.
- When `k` is large enough (`k >= n / 2`), every possible profitable trade can be taken, and the limited-transaction template degenerates to the same answer as the unlimited-transaction problem — some solutions special-case this to avoid unnecessary O(n·k) work.
