---
card: leetcode-patterns
gi: 377
slug: distinct-subsequences
title: Distinct Subsequences
---

## 1. What it is

Given two strings `s` and `t`, return the NUMBER OF DISTINCT SUBSEQUENCES of `s` that equal `t`. Example: `s = "rabbbit"`, `t = "rabbit"` → `3` (three different ways to pick out the letters of `"rabbit"` from `"rabbbit"`, by choosing which of the three `'b'`s to skip).

## 2. Why & when

This is the COUNTING variant of the LCS-family pattern, asked in only ONE direction: instead of measuring how much two strings overlap symmetrically, you count how many ways `s` can be "thinned out" (by deleting characters) to become exactly `t`. Use this shape whenever a problem counts the number of ways one sequence can be reduced to match another via deletions only.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the number of distinct subsequences of the first `i` characters of `s` that equal the first `j` characters of `t`, for every `i, j`.

**Steps:**
1. Base cases: `dp[i][0] = 1` for every `i` (there is exactly one way to form an empty target: delete everything). `dp[0][j] = 0` for every `j > 0` (an empty source can never form a non-empty target).
2. For `i` from `1` to `m` (`m = s.length()`), for `j` from `1` to `n` (`n = t.length()`): `dp[i][j] = dp[i-1][j]` (always: skip `s`'s current character, keeping whatever count already existed). If `s.charAt(i-1) == t.charAt(j-1)`, ALSO add `dp[i-1][j-1]` (additionally use `s`'s current character to match `t`'s current character).
3. Return `dp[m][n]`.

**Why it is correct:** for each character of `s`, there are always two choices: SKIP it (contributing `dp[i-1][j]` ways, unchanged), or, if it matches `t`'s current character, USE it to extend a match (contributing `dp[i-1][j-1]` ways). These two contributions never overlap (one explicitly discards `s.charAt(i-1)`, the other explicitly consumes it), so summing them counts every distinct subsequence exactly once.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp cell showing two contributions, skip s character always, plus use it when characters match">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s[i-1]='b', t[j-1]='b' -- MATCH</text>
    <text x="10" y="45">skip s[i-1]: contributes dp[i-1][j]</text>
    <text x="10" y="65">use s[i-1] to match t[j-1]: contributes dp[i-1][j-1]</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = dp[i-1][j] + dp[i-1][j-1]</text>
  </g>
</svg>

Every character of `s` is either skipped or, when it matches, optionally consumed — both paths are summed, never double-applied.

## 5. Runnable example

```java
// DistinctSubsequences.java
public class DistinctSubsequences {

    // KEY INSIGHT: each character of s is either skipped (always
    // possible) or, on a match, additionally consumed to extend a
    // match with t -- sum both contributions.

    static int numDistinct(String s, String t) {
        int m = s.length(), n = t.length();
        long[][] dp = new long[m + 1][n + 1];
        for (int i = 0; i <= m; i++) dp[i][0] = 1;

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = dp[i - 1][j];
                if (s.charAt(i - 1) == t.charAt(j - 1)) {
                    dp[i][j] += dp[i - 1][j - 1];
                }
            }
        }
        return (int) dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(numDistinct("rabbbit", "rabbit"));
        // 3
        System.out.println(numDistinct("babgbag", "bag"));
        // 5
    }
}
```

**How to run:** `java DistinctSubsequences.java`

## 6. Walkthrough

Trace a portion of `numDistinct("rabbbit", "rabbit")` focusing on the three `'b'`s versus `t`'s two `'b'`s (positions where `s = "...bbb..."`, `t = "...bb..."`):

| after s character | dp count for matching "bb" so far |
|---|---|
| 1st 'b' | 1 way (use it) |
| 2nd 'b' | 2 ways (skip 1st+use 2nd, or use both) |
| 3rd 'b' | 3 ways (each 'b' can be the one skipped) |

This matches the final answer of `3`: the three ways correspond to which of the three `'b'`s in `"rabbbit"` gets left out. Time complexity is O(m · n). Space is O(m · n) (reducible to O(n) with a single rolling row, processing `j` in DESCENDING order to avoid overwriting values still needed).

## 7. Gotchas & takeaways

> Gotcha: using `int` instead of `long` for `dp` risks overflow on inputs where `s` has many repeated characters matching `t` — LeetCode's stated constraints keep the final answer within `int` range, but intermediate `long` arithmetic avoids any risk during accumulation.

- `dp[i][j] = dp[i-1][j] + (match ? dp[i-1][j-1] : 0)`: the counting variant of the LCS-family template, directional (only `s` can be "thinned," not `t`).
- Base case `dp[i][0] = 1` (not `0`) is easy to get backwards — matching an EMPTY target is always possible, exactly one way, by deleting everything.
- Related problems: Longest Common Subsequence (the length-measuring, symmetric sibling of this counting, directional problem), Word Break (also builds a 1D reachability count from a dictionary, a simpler single-string version of this two-string counting idea).
