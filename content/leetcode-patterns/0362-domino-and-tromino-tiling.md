---
card: leetcode-patterns
gi: 362
slug: domino-and-tromino-tiling
title: Domino and Tromino Tiling
---

## 1. What it is

You have a `2 x n` board. You can tile it using `2 x 1` dominoes (placed horizontally or vertically) and L-shaped trominoes (covering 3 cells, in any of 4 rotations). Return the NUMBER OF WAYS to fully tile the board, modulo `10^9 + 7`. Example: `n = 3` → `5`.

## 2. Why & when

This is a Fibonacci-style recurrence hiding behind a geometry problem: once you work out the tiling cases, `dp[n]` depends only on `dp[n-1]`, `dp[n-2]`, and `dp[n-3]` — a fixed, small look-back, just like Tribonacci. Use this shape whenever a tiling or arrangement problem, after careful case analysis, collapses into a recurrence over a small constant number of previous states.

## 3. Core concept

**Key idea:** let `dp[i]` = the number of ways to FULLY tile a `2 x i` board. Careful case analysis (fully filling column `i`, or filling it using an L-shape that also touches column `i-1`) gives the recurrence `dp[i] = 2*dp[i-1] + dp[i-3]`, for `i >= 3`.

**Steps:**
1. Base cases: `dp[0] = 1` (one way to tile nothing: do nothing), `dp[1] = 1` (one vertical domino), `dp[2] = 2` (two vertical dominoes, or two horizontal dominoes stacked).
2. For `i` from `3` to `n`: `dp[i] = (2 * dp[i-1] + dp[i-3]) % MOD`.
3. Return `dp[n]`.

**Why the formula works:** to reach a fully-tiled `2 x i` board, the last column can be completed in two symmetric ways using an L-tromino that reaches back into a `2 x (i-1)` fully-tiled board (contributing `2 * dp[i-1]`, one for each mirror orientation), or the last THREE columns form a specific tromino-plus-domino combination that reaches back to a fully-tiled `2 x (i-3)` board (contributing `dp[i-3]`). This case analysis is a known result for this specific tiling problem, derived by enumerating how the rightmost columns can be completed.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array showing dp of 5 built from twice dp of 4 plus dp of 2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dp[0]=1, dp[1]=1, dp[2]=2</text>
    <text x="10" y="45">dp[3] = 2*dp[2] + dp[0] = 2*2 + 1 = 5</text>
    <text x="10" y="65">dp[4] = 2*dp[3] + dp[1] = 2*5 + 1 = 11</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[3] = 5 ways to tile 2x3</text>
  </g>
</svg>

Each width's tiling count combines twice the previous width's count with the count three columns back.

## 5. Runnable example

```java
// DominoAndTrominoTiling.java
public class DominoAndTrominoTiling {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: after case analysis of how the last column(s) can
    // be completed, the tiling count reduces to dp[i] = 2*dp[i-1] +
    // dp[i-3] -- a small, fixed look-back, like Tribonacci.

    static int numTilings(int n) {
        if (n == 1) return 1;
        if (n == 2) return 2;

        long[] dp = new long[n + 1];
        dp[0] = 1;
        dp[1] = 1;
        dp[2] = 2;
        for (int i = 3; i <= n; i++) {
            dp[i] = (2 * dp[i - 1] % MOD + dp[i - 3]) % MOD;
        }
        return (int) dp[n];
    }

    public static void main(String[] args) {
        System.out.println(numTilings(3));
        // 5
        System.out.println(numTilings(1));
        // 1
    }
}
```

**How to run:** `java DominoAndTrominoTiling.java`

## 6. Walkthrough

Trace `numTilings(3)`:

| i | dp[i-1] | dp[i-3] | dp[i] |
|---|---|---|---|
| 3 | dp[2]=2 | dp[0]=1 | 2*2+1 = 5 |

`dp[3] = 5`, matching the expected `5` distinct tilings. Time complexity is O(n). Space is O(n) as written (could be reduced to O(1) with three rolling variables, following the Tribonacci template).

## 7. Gotchas & takeaways

> Gotcha: deriving `dp[i] = 2*dp[i-1] + dp[i-3]` requires careful enumeration of tiling cases by hand — attempting to guess the recurrence from small examples alone (without the case analysis) risks missing a term or a coefficient; verify any guessed recurrence against several small `n` by brute force before trusting it.

- Once a tiling or arrangement problem's recurrence is worked out, it often reduces to the exact SAME rolling-variable technique as Tribonacci, just with different coefficients.
- The modulo operation must be applied after every addition and multiplication that could overflow, not just at the end.
- Related problems: N-th Tribonacci Number (the same "look back 3, sum with coefficients" structure, with simpler coefficients), Climbing Stairs (a simpler 2-term tiling-style recurrence, without needing case analysis to derive).
