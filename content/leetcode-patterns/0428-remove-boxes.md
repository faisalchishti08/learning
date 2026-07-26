---
card: leetcode-patterns
gi: 428
slug: remove-boxes
title: Remove Boxes
---

## 1. What it is

Given a row of colored boxes, you may remove any CONTIGUOUS group of boxes with the SAME color, scoring `k * k` points for a group of `k` boxes, repeating until every box is gone. Return the MAXIMUM total points achievable. Example: `boxes = [1,3,2,2,2,3,4,3,1]` → `23`.

## 2. Why & when

Use this shape whenever a problem's score depends on GROUPING identical adjacent items, and removing items can bring two PREVIOUSLY-SEPARATED matching items next to each other (by deleting everything between them first). This is interval DP with an EXTRA dimension: two indices alone (`dp[i][j]`) cannot capture "how many same-colored boxes are already attached to this range from further left" — a third state variable is required.

## 3. Core concept

**Key idea:** build `dp[i][j][k]` = the maximum points obtainable from the range `boxes[i..j]`, GIVEN that there are already `k` extra boxes, all the same color as `boxes[i]`, attached immediately to the LEFT of this range (from boxes that were originally further left but are now adjacent, because everything between them was removed earlier).

**Steps:**
1. First, merge any boxes at the START of the range that already match `boxes[i]`: advance `i` forward and increase `k` for each match, since they will always be removed TOGETHER with `boxes[i]` in the optimal strategy — no need to consider splitting them apart.
2. Option A — remove `boxes[i]` (and its `k` attached matches) immediately: this scores `(k+1) * (k+1)`, plus whatever the REST of the range (`boxes[i+1..j]`, with `0` attached extra boxes) can score on its own: `dp[i+1][j][0]`.
3. Option B — for every later position `m` in `(i, j]` where `boxes[m] == boxes[i]`, DELAY removing `boxes[i]`'s group: first clear out everything strictly between `i` and `m` (`dp[i+1][m-1][0]`), which brings `boxes[m]` right next to `boxes[i]`'s group; then solve the range `[m, j]`, but now WITH `k+1` extra attached boxes (since `boxes[i]`'s group has joined `boxes[m]`'s side): `dp[i+1][m-1][0] + dp[m][j][k+1]`.
4. `dp[i][j][k] = max` over Option A and every Option B choice of `m`. The answer is `dp[0][n-1][0]`.

**Why the extra dimension `k` is necessary:** the value of removing `boxes[i]`'s group depends on EXACTLY HOW MANY same-colored boxes are already attached to it from the left — that count is not fixed for a given range `[i, j]`, since it depends on choices made in a DIFFERENT part of the array, outside this range entirely. `dp[i][j]` alone cannot distinguish "3 boxes attached" from "0 boxes attached," even though those lead to very different scores (`k*k` grows quadratically).

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two options for the leftmost box group, remove it immediately, or clear the middle and merge it with a later matching group">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Option A: remove boxes[i]'s group now -- scores (k+1)^2 + dp[i+1][j][0]</text>
    <text x="10" y="45" font-weight="bold">Option B: clear (i, m) first, merge boxes[i] with boxes[m] (same color)</text>
    <rect x="10" y="60" width="60" height="26" fill="#3fb950"/><text x="40" y="78" text-anchor="middle" font-size="10" fill="#0d1117">i (+k)</text>
    <rect x="90" y="60" width="120" height="26" fill="#30363d" stroke="#8b949e"/><text x="150" y="78" text-anchor="middle" font-size="10">cleared first</text>
    <rect x="230" y="60" width="60" height="26" fill="#3fb950"/><text x="260" y="78" text-anchor="middle" font-size="10" fill="#0d1117">m (same color)</text>
    <rect x="10" y="100" width="320" height="24" fill="#3fb950"/><text x="170" y="117" fill="#0d1117" text-anchor="middle" font-size="10">i's group joins m's side, now with k+1 attached boxes</text>
  </g>
</svg>

Delaying a group's removal to merge it with a same-colored group further right can score more, since points grow quadratically with group size.

## 5. Runnable example

```java
// RemoveBoxes.java
public class RemoveBoxes {

    static int[][][] memo;
    static int[] boxes;

    // KEY INSIGHT: dp[i][j][k] needs a THIRD dimension -- k, the count
    // of same-colored boxes already attached from the left -- since
    // that count depends on choices made outside this very range.

    static int removeBoxes(int[] b) {
        boxes = b;
        int n = b.length;
        memo = new int[n][n][n];
        return dp(0, n - 1, 0);
    }

    static int dp(int i, int j, int k) {
        if (i > j) return 0;
        if (memo[i][j][k] > 0) return memo[i][j][k];

        int origI = i, origK = k;
        while (i + 1 <= j && boxes[i + 1] == boxes[i]) { i++; k++; } // merge leading matches

        int best = (k + 1) * (k + 1) + dp(i + 1, j, 0); // Option A
        for (int m = i + 1; m <= j; m++) {
            if (boxes[m] == boxes[i]) {
                best = Math.max(best, dp(i + 1, m - 1, 0) + dp(m, j, k + 1)); // Option B
            }
        }
        memo[origI][j][origK] = best;
        return best;
    }

    public static void main(String[] args) {
        System.out.println(removeBoxes(new int[]{1, 3, 2, 2, 2, 3, 4, 3, 1}));
        // 23
        System.out.println(removeBoxes(new int[]{1, 1, 1}));
        // 9
    }
}
```

**How to run:** `java RemoveBoxes.java`

## 6. Walkthrough

Trace the key calls for `boxes = [1, 3, 2, 2, 2, 3, 4, 3, 1]` (indices `0..8`):

| call | best choice | result |
|---|---|---|
| dp(2,4,0) | leading merge: boxes[2..4] all '2' (k becomes 2); Option A removes all three together | (2+1)^2 = 9 |
| dp(6,6,0) | single box '4', no attachments | 1 |
| dp(7,7,2) | box '3' at index 7, with k=2 already attached (from indices 1 and 5, merged in by the caller) | (2+1)^2 = 9 |
| dp(5,7,1) | Option B: merge boxes[5]='3' (k=1 incoming) with boxes[7]='3'; clear (6,6) first | dp(6,6,0) + dp(7,7,2) = 1 + 9 = 10 |
| dp(1,7,0) | Option B: merge boxes[1]='3' with boxes[5]='3'; clear (2,4) first | dp(2,4,0) + dp(5,7,1) = 9 + 10 = 19 |
| dp(8,8,1) | box '1' at index 8, with k=1 attached (from index 0) | (1+1)^2 = 4 |
| dp(0,8,0) | Option B: merge boxes[0]='1' with boxes[8]='1'; clear (1,7) first | dp(1,7,0) + dp(8,8,1) = 19 + 4 = 23 |

The optimal strategy removes the middle `2,2,2` for `9`, then the lone `4` for `1`, then merges all three `3`s (indices `1, 5, 7`) for `9`, then merges both `1`s (indices `0, 8`) for `4`: total `9 + 1 + 9 + 4 = 23`, matching the expected answer. Time complexity is O(n^4) (O(n^3) states for `dp[i][j][k]`, each trying O(n) merge points `m`). Space is O(n^3) for the memo table.

## 7. Gotchas & takeaways

> Gotcha: forgetting to merge leading matching boxes into `i` and `k` FIRST (the `while` loop at the top of `dp`) misses the fact that consecutive same-colored boxes should always be treated as ONE unit from the start — without this step, the algorithm would need extra, more complicated case analysis to reach the same answer.

- `dp[i][j][k]`, with `k` tracking same-colored boxes already attached from the left: the signature example of an interval-DP problem needing a THIRD state dimension.
- Points grow QUADRATICALLY with group size (`k*k`), which is WHY delaying a removal to merge two same-colored groups (Option B) can beat removing them separately (two smaller squares sum to less than one larger square, for the same total count).
- Related problems: Strange Printer (a related "match now vs. match later" idea, but for print turns, not squared group sizes), Minimum Cost to Merge Stones (also merges groups, but under a fixed group-size constraint `K`, not a free choice of match position).
