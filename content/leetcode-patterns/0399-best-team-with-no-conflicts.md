---
card: leetcode-patterns
gi: 399
slug: best-team-with-no-conflicts
title: Best Team With No Conflicts
---

## 1. What it is

Given `scores` and `ages` for a group of players, choose a subset to form a team that MAXIMIZES the total score, subject to one constraint: there can be NO CONFLICT, where a conflict means one player has a STRICTLY GREATER age but a STRICTLY LOWER score than another chosen player. Return the maximum possible total score. Example: `scores = [1,3,5,10,15]`, `ages = [1,2,3,4,5]` → `34` (everyone fits, since both age and score increase together).

## 2. Why & when

This is LIS with TWO criteria that must both be respected: after sorting, "compatible" means the earlier player's score does not exceed the later player's score (age compatibility is guaranteed by the sort itself). Use this shape whenever a problem selects a MAXIMUM-SCORE subset from paired attributes, where the selection must avoid a "one attribute up, the other down" conflict — sorting by one attribute reduces the problem to an LIS-style scan on the other.

## 3. Core concept

**Key idea:** pair each player's `(age, score)`, sort by age ascending (breaking ties by score ascending), then build `dp[i]` = the maximum total score of a valid team ENDING with player `i` (in sorted order), using the LIS transition with `scores[j] <= scores[i]` as the compatibility check.

**Steps:**
1. Create an array of `(age, score)` pairs; sort by `age` ascending, with ties broken by `score` ascending.
2. Create `dp[n]`, initialized to each player's own `score` (a team of one).
3. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: if `scores[j] <= scores[i]`, `dp[i] = max(dp[i], dp[j] + scores[i])`.
4. Return `max(dp)`.

**Why sorting by age (with score as tie-break) makes the scan correct:** after sorting, for any `j < i`, either `ages[j] < ages[i]` (a genuinely younger player), or `ages[j] == ages[i]` and `scores[j] <= scores[i]` (same age, so no conflict is possible regardless of score, and the tie-break just orders them consistently). In BOTH cases, checking `scores[j] <= scores[i]` correctly identifies whether including both `j` and `i` avoids a conflict — a younger player with a higher score never conflicts with an older, higher-scoring player.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sorted players by age and score showing a later player extending the best compatible earlier teams total score">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">sorted (age,score): (1,5),(1,5),(2,4),(2,6)</text>
    <text x="10" y="45">at i=3 (age2,score6): compatible j's have score &lt;= 6 -- all of them</text>
    <text x="10" y="65">best prior dp: dp[1]=10 (chain of the two age-1 players)</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[3] = 6 + 10 = 16</text>
  </g>
</svg>

Sorting by age (with score as a tie-break) turns the two-attribute conflict check into a single score comparison.

## 5. Runnable example

```java
// BestTeamWithNoConflicts.java
import java.util.Arrays;

public class BestTeamWithNoConflicts {

    // KEY INSIGHT: sort by age (score as tie-break), then run the LIS
    // transition on score alone -- the sort makes the age half of the
    // conflict check automatic.

    static int bestTeamScore(int[] scores, int[] ages) {
        int n = scores.length;
        int[][] players = new int[n][2];
        for (int i = 0; i < n; i++) players[i] = new int[]{ages[i], scores[i]};
        Arrays.sort(players, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);

        int[] dp = new int[n];
        int maxScore = 0;
        for (int i = 0; i < n; i++) {
            dp[i] = players[i][1];
            for (int j = 0; j < i; j++) {
                if (players[j][1] <= players[i][1]) {
                    dp[i] = Math.max(dp[i], dp[j] + players[i][1]);
                }
            }
            maxScore = Math.max(maxScore, dp[i]);
        }
        return maxScore;
    }

    public static void main(String[] args) {
        System.out.println(bestTeamScore(new int[]{1, 3, 5, 10, 15}, new int[]{1, 2, 3, 4, 5}));
        // 34
        System.out.println(bestTeamScore(new int[]{4, 5, 6, 5}, new int[]{2, 1, 2, 1}));
        // 16
    }
}
```

**How to run:** `java BestTeamWithNoConflicts.java`

## 6. Walkthrough

Trace `bestTeamScore([4,5,6,5], [2,1,2,1])`, sorted as `(1,5),(1,5),(2,4),(2,6)`:

| i | (age,score) | best j | dp[i] |
|---|---|---|---|
| 0 | (1,5) | - | 5 |
| 1 | (1,5) | j=0, score 5&lt;=5 | 10 |
| 2 | (2,4) | none (5,5 &gt; 4) | 4 |
| 3 | (2,6) | j=1 (best, dp=10) | 16 |

`max(dp) = 16`, matching the expected answer. Time complexity is O(n^2) for the DP, plus O(n log n) for sorting. Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: this DP MAXIMIZES the SUM of scores, not the COUNT of players — the transition adds `scores[i]` (not `1`) to the best prior sum, which is a different combining rule from the plain LIS length-counting template, even though the surrounding structure is identical.

- The tie-break (sorting by score ascending WITHIN equal ages) is essential — without it, two same-age players could be processed in an order that misses a valid, conflict-free combination.
- This is the SAME "sort by one attribute, LIS-scan on the other" technique as Russian Doll Envelopes, adapted to MAXIMIZE a sum instead of a count.
- Related problems: Longest Increasing Subsequence (the length-counting ancestor of this sum-maximizing variant), Russian Doll Envelopes (the same two-attribute sorting trick, applied to counting a chain length instead of summing scores).
