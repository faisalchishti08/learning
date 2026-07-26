---
card: leetcode-patterns
gi: 431
slug: dp-state-machine-stocks-signal-sequential-decisions-with-a-f
title: "DP: State Machine (Stocks) — signal: sequential decisions with a few discrete states"
---

## 1. What it is

State-machine DP is the pattern for problems where you move through a sequence (usually days, or positions in a row) making a small, fixed set of DECISIONS at each step — buy, sell, hold, rest, or "paint this color" — and the best choice today depends only on which STATE you were in yesterday. Think of a light switch with a few named positions (holding a stock, just sold, resting) — at each day, you either stay in your current position or flip to an allowed neighboring one.

## 2. Why & when

Reach for this pattern whenever a problem describes a sequence of steps where, at each step, you pick from a SMALL, NAMED set of actions or states, and a RULE restricts which state can follow which (you cannot sell without already holding, you cannot buy again the day right after selling, you cannot paint a house the same color as the house before it). The number of states stays constant (it does not grow with the array), which is what makes this different from grid or interval DP, where the state itself scales with position.

Learn to recognize these signals in a problem statement:

- **"Buy one share, then sell it later, to maximize profit"** — the base two-state pattern: holding a stock, or not.
- **"You may complete as many transactions as you like"** or **"at most k transactions"** — a variant that adds a TRANSACTION COUNT as part of the state.
- **"After selling, you must wait one day before buying again"** (cooldown) — an extra RESTING state, forbidding an immediate re-buy.
- **"Paint each house one of k colors, no two adjacent houses the same color"** — a different domain, but the same shape: a fixed set of states (colors) per step, with a transition rule (never repeat the previous step's state).

The alternative — trying every combination of buy/sell days with plain recursion — costs exponential time, since the number of possible action sequences grows exponentially with the number of days. Tracking only the BEST value for each state, updated one step at a time, reduces this to a single linear (or near-linear) pass.

## 3. Core concept

Every state-machine DP problem reduces to the SAME per-step update, across a small fixed set of named states:

**The state.** One `dp` value PER NAMED STATE (e.g. `hold`, `sold`, `rest`), representing the best possible outcome achievable if you are in that state after processing today.

**The transition.** For each step, recompute every state's new value from the ALLOWED PREVIOUS states, according to the problem's rules — e.g. `hold` today can come from `hold` yesterday (do nothing) or from `rest`/`cash` yesterday minus today's price (just bought); `sold` today can only come from `hold` yesterday plus today's price (just sold).

**Why the DP works:** the KEY property is that each state's best value depends only on a FEW other states from the PREVIOUS step, never on the full history — this is exactly what makes a state machine a valid abstraction: today's best outcome is fully determined by yesterday's state values, not by which exact sequence of actions produced them.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three named states hold sold and rest with arrows showing which previous state each can transition from">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">states: hold, sold, rest -- each day, recompute from ALLOWED previous states</text>
    <rect x="30" y="40" width="80" height="30" fill="#3fb950"/><text x="70" y="60" text-anchor="middle" font-size="10" fill="#0d1117">hold</text>
    <rect x="180" y="40" width="80" height="30" fill="#30363d" stroke="#8b949e"/><text x="220" y="60" text-anchor="middle" font-size="10">sold</text>
    <rect x="330" y="40" width="80" height="30" fill="#30363d" stroke="#8b949e"/><text x="370" y="60" text-anchor="middle" font-size="10">rest</text>
    <text x="10" y="95">hold(today) = max(hold(yst), rest(yst) - price)</text>
    <text x="10" y="115">sold(today) = hold(yst) + price</text>
    <text x="10" y="135">rest(today) = max(rest(yst), sold(yst))</text>
  </g>
</svg>

Each named state's value each day is recomputed only from the specific previous states the problem's rules allow.

## 5. Runnable example

```java
// StateMachineStocksSignal.java
public class StateMachineStocksSignal {

    // Signal check: cooldown after selling -- three named states
    // (hold, sold, rest), each updated from its allowed predecessors.
    static int maxProfit(int[] prices) {
        int hold = Integer.MIN_VALUE, sold = 0, rest = 0;
        for (int price : prices) {
            int prevHold = hold, prevSold = sold, prevRest = rest;
            hold = Math.max(prevHold, prevRest - price);
            sold = prevHold + price;
            rest = Math.max(prevRest, prevSold);
        }
        return Math.max(sold, rest);
    }

    public static void main(String[] args) {
        System.out.println(maxProfit(new int[]{1, 2, 3, 0, 2}));
        // 3
    }
}
```

**How to run:** `java StateMachineStocksSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Buy and sell a stock," "at most k transactions," "cooldown after selling," or "paint houses with no repeated adjacent color" are all state-machine DP signals.
2. Running `maxProfit([1,2,3,0,2])` confirms the cooldown-constrained best profit is `3`: buy at price `1`, sell at price `2` (profit `1`), a forced cooldown day, then buy at price `0` and sell at price `2` (profit `2`), for a total of `3`.
3. Each of the three states (`hold`, `sold`, `rest`) is updated using ONLY the previous day's values — no state ever looks further back than one step.
4. If the problem instead capped the number of transactions at some `k`, the state would need an EXTRA dimension (which transaction number you are on), but the per-step update rule would stay the same shape.
5. This upfront classification (how many states, and which transitions are allowed between them) tells you exactly which state variables to declare on the next page's template.

## 7. Gotchas & takeaways

> Gotcha: updating a state variable IN PLACE before other states have read its PREVIOUS value corrupts the transition — always read every state's OLD value into local variables first (as `prevHold`, `prevSold`, `prevRest` above), then compute all the new values from those saved copies.

- The state is a SMALL, FIXED set of named variables per step, not an array indexed by position — this is what separates state-machine DP from grid or interval DP.
- The transition rules (which state can follow which) come directly from the problem's real-world constraints — reading the problem statement carefully for phrases like "cannot," "must first," or "after" reveals exactly which states are reachable from which.
- Some variants (limited transaction count, k colors) add an extra dimension to the state, but the core idea — recompute every state from its allowed predecessors, one step at a time — stays identical.
