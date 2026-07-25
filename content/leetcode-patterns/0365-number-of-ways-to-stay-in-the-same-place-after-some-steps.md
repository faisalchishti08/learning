---
card: leetcode-patterns
gi: 365
slug: number-of-ways-to-stay-in-the-same-place-after-some-steps
title: Number of Ways to Stay in the Same Place After Some Steps
---

## 1. What it is

A pointer starts at index `0` of an array of length `arrLen`. In each of `steps` moves, it can go LEFT, go RIGHT, or STAY, but must always remain within `[0, arrLen - 1]`. Return the number of ways to be back at index `0` after EXACTLY `steps` moves, modulo `10^9 + 7`. Example: `steps = 3`, `arrLen = 2` → `4`.

## 2. Why & when

This is the array-position sibling of Number of Dice Rolls With Target Sum: a FIXED number of moves (`steps`), each choosing from a small set of options (`-1, 0, +1`), tracked with a "how many moves used" axis alongside a "current position" axis. Use this shape whenever a problem counts walks or paths of an EXACT length over positions, where each step has a small, fixed set of moves.

## 3. Core concept

**Key idea:** build `dp[s][p]` = number of ways to be at position `p` after exactly `s` moves, for every reachable `s` and `p`, using the three possible moves at each step.

**Steps:**
1. The position can never exceed `min(steps, arrLen - 1)`, since each move changes position by at most `1`, and going further than `steps` would leave no way to return to `0` in time — cap the position range to save work.
2. Create `dp[steps + 1][maxPos + 1]`, with `dp[0][0] = 1` (zero moves, already at position `0`: one way).
3. For `s` from `1` to `steps`, for `p` from `0` to `maxPos`: `dp[s][p] = dp[s-1][p]` (stay) `+ dp[s-1][p-1]` (came from the left, if `p-1 >= 0`) `+ dp[s-1][p+1]` (came from the right, if `p+1 <= maxPos`).
4. Return `dp[steps][0]`, modulo `10^9 + 7`.

**Why it is correct:** to be at position `p` after `s` moves, the LAST move was either "stay" (from `p` at step `s-1`), "move right" (from `p-1` at step `s-1`), or "move left" (from `p+1` at step `s-1`). Summing the ways for all three valid predecessors counts every path to `(s, p)` exactly once.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table over steps and position showing dp of step 2 position 0 summing three predecessor states">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">computing dp[2][0]: predecessors at step 1</text>
    <text x="10" y="45">stay: dp[1][0]; right (came from p-1=-1, invalid): skip</text>
    <text x="10" y="65">left (came from p+1=1): dp[1][1]</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[2][0] = dp[1][0] + dp[1][1]</text>
  </g>
</svg>

Each state sums exactly the (up to three) predecessor states one move away.

## 5. Runnable example

```java
// NumberOfWaysToStayInTheSamePlaceAfterSomeSteps.java
public class NumberOfWaysToStayInTheSamePlaceAfterSomeSteps {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: fixed number of moves (steps), each from {-1,0,+1}
    // -- add a "moves used" axis to the position DP, same shape as
    // Number of Dice Rolls With Target Sum.

    static int numWays(int steps, int arrLen) {
        int maxPos = Math.min(steps, arrLen - 1);
        long[][] dp = new long[steps + 1][maxPos + 1];
        dp[0][0] = 1;

        for (int s = 1; s <= steps; s++) {
            for (int p = 0; p <= maxPos; p++) {
                long ways = dp[s - 1][p];
                if (p - 1 >= 0) ways += dp[s - 1][p - 1];
                if (p + 1 <= maxPos) ways += dp[s - 1][p + 1];
                dp[s][p] = ways % MOD;
            }
        }
        return (int) dp[steps][0];
    }

    public static void main(String[] args) {
        System.out.println(numWays(3, 2));
        // 4
        System.out.println(numWays(2, 4));
        // 2
    }
}
```

**How to run:** `java NumberOfWaysToStayInTheSamePlaceAfterSomeSteps.java`

## 6. Walkthrough

Trace `numWays(3, 2)`, `maxPos = min(3, 1) = 1`:

| s | dp[s][0] | dp[s][1] |
|---|---|---|
| 0 | 1 | 0 |
| 1 | 1 (stay) | 1 (from p=0, right) |
| 2 | 2 (dp[1][0]+dp[1][1]) | 1 (dp[1][1]+dp[1][0]) |
| 3 | 4 (dp[2][0]+dp[2][1]) | - |

`dp[3][0] = 4`, matching the expected answer. Time complexity is O(steps · maxPos), where `maxPos <= steps`, so effectively O(steps^2). Space is O(steps · maxPos) (reducible to O(maxPos) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: using `arrLen` directly as the position bound instead of `min(steps, arrLen - 1)` wastes massive time and memory when `arrLen` is huge (up to `10^6`) but `steps` is small (up to `500`) — the pointer physically cannot travel farther than `steps` positions away from `0`.

- Bounding the state space by the SMALLEST relevant limit (here, `min(steps, arrLen-1)`), not just the input's raw size, is a common and important DP optimization.
- The three-way sum (`stay`, `came from left`, `came from right`) at each state, with bounds checks, is the general template for "small fixed move set" position-counting DP.
- Related problems: Number of Dice Rolls With Target Sum (the same "moves used" axis idea, summing over face values instead of `{-1,0,+1}`), Climbing Stairs (a simpler single-axis version without the position dimension).
