---
card: leetcode-patterns
gi: 422
slug: guess-number-higher-or-lower-ii
title: Guess Number Higher or Lower II
---

## 1. What it is

You play a guessing game against a number picked secretly from `1` to `n`. Each time you guess wrong, you pay the amount you guessed, and you are told whether the secret number is higher or lower. Return the MINIMUM amount of money needed to guarantee a win, no matter what the secret number turns out to be. Example: `n = 10` → `16`.

## 2. Why & when

Use this shape whenever a problem asks you to guarantee a WORST-CASE outcome across a range of possibilities, where each guess splits the remaining range into two smaller ranges, and you must plan for the ADVERSARY always steering you into the more expensive half.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum money needed to guarantee a win, if the secret number is known to lie somewhere in `[i, j]`.

**Steps:**
1. Base case: `dp[i][j] = 0` whenever `i >= j` (zero or one number left means no guess — hence no cost — is needed).
2. For each range `[i, j]`, try every possible guess `x` from `i` to `j`: if wrong, you pay `x`, and the adversary picks whichever remaining half (`[i, x-1]` or `[x+1, j]`) is MORE expensive for you, so the cost of guessing `x` is `x + max(dp[i][x-1], dp[x+1][j])`.
3. `dp[i][j] = min over all x of (x + max(dp[i][x-1], dp[x+1][j]))` — you pick the guess that minimizes your WORST-CASE cost.
4. The answer is `dp[1][n]`.

**Why the `max` (not `min`) belongs inside the guess's cost:** you do not control which half the secret number falls in after a wrong guess — an adversarial (worst-case) opponent always forces you into the more expensive remaining range. Planning for the `max` of the two halves is what guarantees a win regardless of where the number actually is.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="guessing x splits the range into a left half and a right half, paying x plus whichever half costs more in the worst case">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">guess x in [i, j] -- adversary picks the MORE expensive remaining half</text>
    <rect x="60" y="40" width="90" height="26" fill="#30363d" stroke="#8b949e"/><text x="105" y="58" text-anchor="middle" font-size="10">dp[i][x-1]</text>
    <rect x="170" y="40" width="90" height="26" fill="#30363d" stroke="#8b949e"/><text x="215" y="58" text-anchor="middle" font-size="10">dp[x+1][j]</text>
    <rect x="10" y="80" width="320" height="24" fill="#3fb950"/><text x="170" y="97" fill="#0d1117" text-anchor="middle" font-size="10">cost(x) = x + max(left, right); dp[i][j] = min over all x</text>
  </g>
</svg>

Every candidate guess costs itself plus whichever remaining half is worse for you.

## 5. Runnable example

```java
// GuessNumberHigherOrLowerII.java
public class GuessNumberHigherOrLowerII {

    // KEY INSIGHT: you pay the guess, then face whichever remaining
    // half the adversary steers you into -- so take the max of the
    // two halves, then minimize over every possible guess.

    static int getMoneyAmount(int n) {
        int[][] dp = new int[n + 2][n + 2];
        for (int len = 1; len < n; len++) {
            for (int i = 1; i + len <= n; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int x = i; x <= j; x++) {
                    int left = (x - 1 >= i) ? dp[i][x - 1] : 0;
                    int right = (x + 1 <= j) ? dp[x + 1][j] : 0;
                    best = Math.min(best, x + Math.max(left, right));
                }
                dp[i][j] = best;
            }
        }
        return dp[1][n];
    }

    public static void main(String[] args) {
        System.out.println(getMoneyAmount(10));
        // 16
        System.out.println(getMoneyAmount(1));
        // 0
    }
}
```

**How to run:** `java GuessNumberHigherOrLowerII.java`

## 6. Walkthrough

Trace small ranges for `n = 10` (a sample of the filled table):

| range | best guess | worst-case cost |
|---|---|---|
| [1,1] | (none needed) | 0 |
| [1,2] | guess 1 | 1 |
| [1,3] | guess 2 | 2 |
| [1,10] | guess 7 (a known optimal split) | 16 |

`dp[1][10] = 16`, matching the expected answer. Time complexity is O(n^3) (O(n^2) ranges, each trying O(n) guesses). Space is O(n^2).

## 7. Gotchas & takeaways

> Gotcha: using `min` instead of `max` for the two halves after a wrong guess computes the wrong thing entirely — that would answer "the best case if you get lucky," not "the guaranteed amount needed no matter what," which is what the problem actually asks for.

- `dp[i][j] = min over guesses x of (x + max(left, right))`: the "minimize your worst case" template for adversarial range games.
- The base case `dp[i][j] = 0` for `i >= j` reflects that a range with zero or one candidate needs no further guessing (or money) at all.
- Related problems: Predict the Winner and Stone Game (also adversarial two-outcome range games, but the choice is "take from an end," not "guess a split point," changing the transition's shape).
