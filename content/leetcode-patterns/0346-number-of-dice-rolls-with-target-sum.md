---
card: leetcode-patterns
gi: 346
slug: number-of-dice-rolls-with-target-sum
title: Number of Dice Rolls With Target Sum
---

## 1. What it is

Given `d` dice, each with `f` faces (showing `1` to `f`), and an integer `target`, return the NUMBER OF WAYS to roll all `d` dice so the face values sum to exactly `target`. Since the answer can be huge, return it MODULO `10^9 + 7`. Example: `d = 2`, `f = 6`, `target = 7` → `6` (the classic "sum of two dice equals 7" count).

## 2. Why & when

This is a COUNTING knapsack problem with a twist: instead of an unbounded supply of "items," you have EXACTLY `d` dice, each contributing ONE face value between `1` and `f`. Recognize this shape whenever a problem counts ways to reach a target using a FIXED NUMBER of draws, each draw picked from the same fixed range — the "how many draws" dimension becomes an explicit second axis in the DP state, distinguishing it from plain unbounded knapsack.

## 3. Core concept

**Key idea:** build `dp[i][t]` = number of ways to reach sum `t` using exactly `i` dice, by trying every possible face value for the `i`-th die and summing the ways to reach the remaining target with `i - 1` dice.

**Steps:**
1. Create `dp[d + 1][target + 1]`, all zeros, with `dp[0][0] = 1` (one way to reach sum `0` using `0` dice: roll nothing).
2. For `i` from `1` to `d`, for `t` from `1` to `target`, for each `face` from `1` to `f` (with `face <= t`): `dp[i][t] += dp[i - 1][t - face]`.
3. Return `dp[d][target]`, taken modulo `10^9 + 7`.

**Why it is correct:** the sum after `i` dice is the sum after `i - 1` dice plus THIS die's face value. Trying every face `1..f` for the current die and adding up the ways `dp[i-1][t - face]` counts every valid roll sequence exactly once, since each sequence is uniquely determined by its ordered list of face values, and the DP builds sequences one die at a time in order.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table indexed by dice count and target sum, showing dp of 2 dice 7 summing over six face choices for the second die">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">d=2, f=6, target=7; computing dp[2][7]</text>
    <text x="10" y="45">dp[2][7] = sum over face=1..6 of dp[1][7-face]</text>
    <text x="10" y="65">= dp[1][6]+dp[1][5]+dp[1][4]+dp[1][3]+dp[1][2]+dp[1][1]</text>
    <text x="10" y="85">= 1+1+1+1+1+1 = 6</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">dp[2][7] = 6 ways</text>
  </g>
</svg>

Each die adds one more axis choice, summed over every face value into the previous die's row.

## 5. Runnable example

```java
// NumberOfDiceRollsWithTargetSum.java
public class NumberOfDiceRollsWithTargetSum {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: a fixed number of draws (dice), each from the same
    // range (1..f), summing to a target -- add a "how many drawn so
    // far" axis to the counting-knapsack state.

    static int numRollsToTarget(int d, int f, int target) {
        int[][] dp = new int[d + 1][target + 1];
        dp[0][0] = 1;

        for (int i = 1; i <= d; i++) {
            for (int t = 1; t <= target; t++) {
                long ways = 0;
                for (int face = 1; face <= f && face <= t; face++) {
                    ways += dp[i - 1][t - face];
                }
                dp[i][t] = (int) (ways % MOD);
            }
        }
        return dp[d][target];
    }

    public static void main(String[] args) {
        System.out.println(numRollsToTarget(2, 6, 7));
        // 6
        System.out.println(numRollsToTarget(1, 6, 3));
        // 1
    }
}
```

**How to run:** `java NumberOfDiceRollsWithTargetSum.java`

## 6. Walkthrough

Trace `numRollsToTarget(2, 6, 7)`:

| i (dice used) | t (target so far) | dp[i][t] |
|---|---|---|
| 1 | 1..6 | 1 each (single die: exactly one way to show any face 1-6) |
| 1 | 7 | 0 (one die cannot show 7) |
| 2 | 7 | sum of dp[1][1..6] = 6 |

`dp[2][7] = 6`, matching the six ways: `(1,6),(2,5),(3,4),(4,3),(5,2),(6,1)`. Time complexity is O(d · target · f). Space is O(d · target).

## 7. Gotchas & takeaways

> Gotcha: forgetting the modulo operation, or applying it inconsistently, causes silent integer overflow for large `d` and `f` — always take the result modulo `10^9 + 7` after EVERY accumulation into a running sum, not just at the very end.

- Adding an explicit "count of draws used" axis (`i`) to the DP state is the general fix when a problem has a FIXED number of picks, instead of an unbounded supply — contrast with Coin Change II, which has no such limit on how many coins you use.
- The inner `face` loop bounds itself with `face <= t`, avoiding negative indices into `dp[i-1][t-face]`.
- Related problems: Coin Change II (unbounded, no draw-count limit), Combination Sum IV (also counts ordered sequences, but with an unbounded number of picks, not exactly `d`).
