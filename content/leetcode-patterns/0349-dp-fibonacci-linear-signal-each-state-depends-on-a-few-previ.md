---
card: leetcode-patterns
gi: 349
slug: dp-fibonacci-linear-signal-each-state-depends-on-a-few-previ
title: "DP: Fibonacci / Linear — signal: each state depends on a few previous states"
---

## 1. What it is

Fibonacci/Linear DP is the simplest dynamic programming shape: each answer `dp[i]` depends on only a FEW nearby previous answers (usually `dp[i-1]` and `dp[i-2]`), not on a whole range or a second dimension. Think of climbing stairs one or two steps at a time: the number of ways to reach step `i` is built directly from the ways to reach the one or two steps just before it.

## 2. Why & when

Reach for this pattern when a problem describes a sequence of steps, days, or positions, where the choice at each position is limited to a SMALL, FIXED set of "look-back" options (take 1 or 2 stairs; rob this house or skip it; decode 1 or 2 digits). The state space is one-dimensional and small, so the DP is a single array (or even just a few rolling variables), computed in one pass.

Learn to recognize these signals in a problem statement:

- **"Each step, you can move 1 or 2 positions"** — the defining Fibonacci-style recurrence (`dp[i]` from `dp[i-1]` and `dp[i-2]`).
- **"You cannot pick two adjacent items"** — a "take or skip" recurrence, common to House Robber-style problems.
- **"Decode a string where each digit or pair of digits maps to something"** — a look-back-1-or-2 recurrence over string positions instead of array indices.
- **A small, fixed number of previous states matters, and nothing further back ever matters again.**

The alternative — full recursion without memoization — recomputes the same sub-answers exponentially (this is literally why naive recursive Fibonacci is O(2^n)). Reusing just the last one or two computed values turns the same problem into O(n) time and, often, O(1) space.

## 3. Core concept

Every Fibonacci/Linear DP problem reduces to the SAME small recurrence, applied once per position:

**The state.** `dp[i]` = the answer (count, max value, or boolean) considering everything UP TO position `i`.

**The transition.** `dp[i]` is built from a SMALL, FIXED number of earlier states — typically `dp[i-1]` and `dp[i-2]` — combined with a simple rule specific to the problem (`+`, `max`, or a conditional check).

**Why the DP works:** the KEY property is that `dp[i]` never needs anything from more than 1 or 2 positions back. Once `dp[i-1]` and `dp[i-2]` are known, EVERYTHING before them becomes irrelevant — this is what allows the space optimization from a full array down to two rolling variables.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="chain of dp values where each value depends only on the two immediately preceding values">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[i] depends only on dp[i-1] and dp[i-2]</text>
    <rect x="10" y="40" width="60" height="30" fill="none" stroke="#8b949e"/><text x="40" y="60" text-anchor="middle" font-size="10">dp[i-2]</text>
    <rect x="90" y="40" width="60" height="30" fill="none" stroke="#8b949e"/><text x="120" y="60" text-anchor="middle" font-size="10">dp[i-1]</text>
    <rect x="170" y="40" width="60" height="30" fill="#3fb950"/><text x="200" y="60" text-anchor="middle" font-size="10" fill="#0d1117">dp[i]</text>
    <text x="10" y="95">everything before dp[i-2] is never looked at again</text>
  </g>
</svg>

Each new value slides a small window forward, discarding everything except the last one or two entries.

## 5. Runnable example

```java
// FibonacciLinearSignal.java
public class FibonacciLinearSignal {

    // Signal check: climbing stairs 1 or 2 at a time -- each dp[i]
    // depends only on dp[i-1] and dp[i-2].
    static int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;
        for (int i = 3; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(climbStairs(5));
        // 8
    }
}
```

**How to run:** `java FibonacciLinearSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Move 1 or 2 steps," "cannot pick two adjacent items," or "decode using 1 or 2 characters" is the Fibonacci/Linear signal.
2. Running `climbStairs(5)` gives `8`, matching the count of distinct 1-and-2 step sequences that sum to `5`.
3. At every step `i`, the algorithm only reads `prev1` (`dp[i-1]`) and `prev2` (`dp[i-2]`) — no array is even needed, since nothing further back ever matters again.
4. If instead the problem needs THREE previous states (like Tribonacci), the same idea extends to three rolling variables instead of two.
5. This upfront classification (how many previous states does each answer depend on) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: forgetting to handle the small base cases (`n = 0`, `n = 1`, `n = 2`) explicitly before the loop starts is the most common bug in this pattern — the recurrence `dp[i] = dp[i-1] + dp[i-2]` is meaningless until at least two prior values exist.

- The state `dp[i]`, built from only `dp[i-1]` (and maybe `dp[i-2]`): the core Fibonacci/Linear signal.
- Distinguish COUNTING problems (`dp[i] = dp[i-1] + dp[i-2]`) from OPTIMIZATION problems (`dp[i] = max(dp[i-1], dp[i-2] + value[i])`, as in House Robber) — the combining step changes, but the "look back 1 or 2" structure stays the same.
- Once you see this pattern, always ask: can the full array be replaced with 2–3 rolling variables? Almost always yes, dropping space from O(n) to O(1).
