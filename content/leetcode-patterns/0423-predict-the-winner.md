---
card: leetcode-patterns
gi: 423
slug: predict-the-winner
title: Predict the Winner
---

## 1. What it is

Two players take turns picking a number from either END of an array, adding it to their own score. Both players play OPTIMALLY. Return `true` if Player 1 can end up with a score greater than or equal to Player 2's. Example: `nums = [1, 5, 233, 7]` → `true`.

## 2. Why & when

Use this shape whenever a problem describes two players ALTERNATING turns, each choosing from either end of a shrinking range, both trying to maximize their own outcome. This is a special case of interval DP where the "split point" is not a free choice of `k` — it collapses to exactly two options: take the LEFT end, or take the RIGHT end.

## 3. Core concept

**Key idea:** rather than tracking each player's score separately, build `dp[i][j]` = the maximum SCORE DIFFERENCE (current player's total minus opponent's total) that the player whose turn it is can guarantee, for the remaining range `[i, j]`.

**Steps:**
1. Base case: `dp[i][i] = nums[i]` (only one number left: the current player takes it, gaining exactly that value over the opponent).
2. For each range `[i, j]` (processed by increasing length): `dp[i][j] = max(nums[i] - dp[i+1][j], nums[j] - dp[i][j-1])`.
3. Player 1 wins (or ties) if and only if `dp[0][n-1] >= 0`.

**Why the transition subtracts the recursive value:** if the current player takes `nums[i]`, the OPPONENT then plays optimally on `[i+1, j]`, achieving a difference of `dp[i+1][j]` IN THEIR OWN FAVOR — from the current player's perspective, that is a SUBTRACTION. So the current player's best guaranteed difference from taking the left end is `nums[i] - dp[i+1][j]`; taking the right end is symmetric. The current player picks whichever of the two choices leaves them better off.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="current player choosing the left end or the right end, then subtracting the opponent's best resulting difference on the remaining range">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[i][j] = max(nums[i] - dp[i+1][j], nums[j] - dp[i][j-1])</text>
    <rect x="60" y="40" width="100" height="26" fill="#3fb950"/><text x="110" y="58" text-anchor="middle" font-size="10" fill="#0d1117">take left: nums[i]</text>
    <rect x="200" y="40" width="100" height="26" fill="#3fb950"/><text x="250" y="58" text-anchor="middle" font-size="10" fill="#0d1117">take right: nums[j]</text>
    <rect x="10" y="80" width="320" height="24" fill="#3fb950"/><text x="170" y="97" fill="#0d1117" text-anchor="middle" font-size="10">then SUBTRACT the opponent's best result on what remains</text>
  </g>
</svg>

Each choice's value is what you gain now, minus the opponent's best outcome on the remaining range.

## 5. Runnable example

```java
// PredictTheWinner.java
public class PredictTheWinner {

    // KEY INSIGHT: track the SCORE DIFFERENCE, not each player's total
    // score separately -- taking a number gains it, then subtracts the
    // opponent's best resulting difference on what's left.

    static boolean predictTheWinner(int[] nums) {
        int n = nums.length;
        int[][] dp = new int[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = nums[i];

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = Math.max(nums[i] - dp[i + 1][j], nums[j] - dp[i][j - 1]);
            }
        }
        return dp[0][n - 1] >= 0;
    }

    public static void main(String[] args) {
        System.out.println(predictTheWinner(new int[]{1, 5, 2}));
        // false
        System.out.println(predictTheWinner(new int[]{1, 5, 233, 7}));
        // true
    }
}
```

**How to run:** `java PredictTheWinner.java`

## 6. Walkthrough

Trace `dp` for `nums = [1, 5, 2]`:

| range | dp value | reasoning |
|---|---|---|
| [0,0] | 1 | single element |
| [1,1] | 5 | single element |
| [2,2] | 2 | single element |
| [0,1] | max(1-5, 5-1) = 4 | take right (5) is better |
| [1,2] | max(5-2, 2-5) = 3 | take left (5) is better |
| [0,2] | max(1-3, 2-4) = -2 | both choices leave Player 1 behind |

`dp[0][2] = -2 < 0`, so `predictTheWinner` returns `false`: Player 1 cannot guarantee a tie or win against optimal play. Time complexity is O(n^2) (only two choices per range, not a full scan over `k`). Space is O(n^2) (reducible to O(n) with a rolling diagonal).

## 7. Gotchas & takeaways

> Gotcha: the DP computes a SCORE DIFFERENCE, not either player's actual total — do not try to recover individual scores from `dp[i][j]` directly; the sign (and only the sign) of `dp[0][n-1]` answers the question asked.

- This is the two-choice special case of interval DP: the split point is not a free variable `k`, but always either "take the left end" or "take the right end."
- The subtraction (`nums[i] - dp[i+1][j]`), not addition, is what correctly accounts for the OPPONENT also playing optimally on the remaining range.
- Related problems: Stone Game (the exact same DP, phrased as "does Alice win," where the array length is always even), Guess Number Higher or Lower II (a different adversarial range game, where the choice is a full scan over guesses, not just two ends).
