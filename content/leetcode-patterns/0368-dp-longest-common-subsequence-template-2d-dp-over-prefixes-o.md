---
card: leetcode-patterns
gi: 368
slug: dp-longest-common-subsequence-template-2d-dp-over-prefixes-o
title: "DP: Longest Common Subsequence — template: 2D dp over prefixes of both strings"
---

## 1. What it is

This page gives the reusable template for LCS-family problems: a 2D table `dp[i][j]` filled row by row over prefixes of string A, and column by column over prefixes of string B, plus how to reconstruct the actual subsequence from the filled table.

## 2. Why & when

Use the LENGTH-ONLY template when a problem just asks "how long" or "how many." Use the RECONSTRUCTION extension when a problem asks for the actual common subsequence itself, not just its length — this requires walking the table backwards after filling it forward.

## 3. Core concept

**Template A — length only.**
1. Create `dp[m+1][n+1]`, all zeros (`dp[0][j] = 0` and `dp[i][0] = 0` for all `i, j`: an empty prefix has no common subsequence with anything).
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `a.charAt(i-1) == b.charAt(j-1)`, `dp[i][j] = dp[i-1][j-1] + 1`; else `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
3. The answer is `dp[m][n]`.

**Template B — reconstruct the actual subsequence.**
1. Fill `dp` exactly as in Template A.
2. Starting at `(i, j) = (m, n)`, walk BACKWARDS: if `a.charAt(i-1) == b.charAt(j-1)`, this character is part of the LCS — prepend it, then move to `(i-1, j-1)`. Otherwise, move toward whichever neighbor (`dp[i-1][j]` or `dp[i][j-1]`) has the LARGER value (that is the direction the optimal answer came from).
3. Stop when `i == 0` or `j == 0`.

**Why reconstruction works:** the filled table already encodes, at every cell, WHICH transition produced its value. Walking backwards simply retraces that same decision in reverse — a character is only ever added to the LCS at a cell where the characters matched, since that is the only transition that grows the subsequence.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="backward walk through the dp table from the bottom right corner tracing which cells contributed matched characters">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">a="abcde", b="ace"; walking backward from dp[5][3]</text>
    <text x="10" y="45">'e'=='e' match -&gt; prepend 'e', move to dp[4][2]</text>
    <text x="10" y="65">'d' != 'c' mismatch -&gt; move toward larger neighbor, dp[3][2]</text>
    <text x="10" y="85">'c'=='c' match -&gt; prepend 'c', move to dp[2][1]</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">continuing gives "ace"</text>
  </g>
</svg>

Each backward step either consumes a matched character or follows the direction the maximum came from.

## 5. Runnable example

```java
// LongestCommonSubsequenceTemplate.java
public class LongestCommonSubsequenceTemplate {

    // Template A: length only.
    static int lcsLength(String a, String b) {
        int m = a.length(), n = b.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = (a.charAt(i - 1) == b.charAt(j - 1))
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[m][n];
    }

    // Template B: reconstruct the actual LCS string.
    static String lcsString(String a, String b) {
        int m = a.length(), n = b.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = (a.charAt(i - 1) == b.charAt(j - 1))
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }

        StringBuilder sb = new StringBuilder();
        int i = m, j = n;
        while (i > 0 && j > 0) {
            if (a.charAt(i - 1) == b.charAt(j - 1)) {
                sb.append(a.charAt(i - 1));
                i--; j--;
            } else if (dp[i - 1][j] >= dp[i][j - 1]) {
                i--;
            } else {
                j--;
            }
        }
        return sb.reverse().toString();
    }

    public static void main(String[] args) {
        System.out.println(lcsLength("abcde", "ace"));
        // 3
        System.out.println(lcsString("abcde", "ace"));
        // ace
    }
}
```

**How to run:** `java LongestCommonSubsequenceTemplate.java`

## 6. Walkthrough

1. `lcsLength` fills a `6 x 4` table (`m+1` rows, `n+1` columns), each cell built from at most three neighbors.
2. `lcsString` fills the SAME table, then walks backward from `(5,3)`, appending matched characters and following the larger neighbor on mismatches, producing `"ace"` once reversed.
3. Both agree: the length is `3` and the actual subsequence is `"ace"`.
4. Tracing the backward walk confirms every appended character corresponds to a MATCH cell — `'e'` at `(5,3)`, `'c'` at `(3,2)`, `'a'` at `(1,1)` — while mismatched cells only redirect the walk without adding anything.
5. This template applies directly to Longest Common Subsequence, Uncrossed Lines, and Delete Operation for Two Strings — only the combining rule and what gets reconstructed change per problem.

## 7. Gotchas & takeaways

> Gotcha: when walking backward on a mismatch, choosing the WRONG neighbor (the smaller one instead of the larger one) silently reconstructs a shorter, non-optimal subsequence — always move toward `max(dp[i-1][j], dp[i][j-1])`.

- Length-only: simpler, and sufficient whenever only a count or length is needed.
- Reconstruction: needed when the actual matched sequence (or a downstream ADAPTATION of it, like the actual edit operations) must be reported.
- The transition itself (`dp[i-1][j-1]+1` on match, `max` of two neighbors on mismatch) is the general LCS shape — other problems in this family swap `max` for `min`, `+=`, or a boolean `OR`.
