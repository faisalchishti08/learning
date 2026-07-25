---
card: leetcode-patterns
gi: 367
slug: dp-longest-common-subsequence-signal-matching-aligning-two-s
title: "DP: Longest Common Subsequence — signal: matching/aligning two sequences"
---

## 1. What it is

Longest Common Subsequence (LCS) is the pattern for comparing TWO sequences (strings or arrays) character by character or element by element, building up an answer about how they RELATE — how similar they are, how to transform one into the other, or how to interleave them. A subsequence keeps relative order but can skip elements; think of finding the longest "thread" of matching characters you can pull out of both strings without reordering either one.

## 2. Why & when

Reach for this pattern whenever a problem gives you TWO strings or arrays and asks a question about matching, aligning, transforming, or interleaving them — not just examining one sequence alone. The two-sequence nature is the tell: one axis of the DP table walks one string, the other axis walks the second string.

Learn to recognize these signals in a problem statement:

- **"Longest common subsequence/substring between two strings"** — the defining LCS framing directly.
- **"Minimum number of deletions/insertions to transform one string into another"** — an edit-distance variant, closely related to LCS (the characters NOT deleted form a common subsequence).
- **"Can string C be formed by interleaving strings A and B"** — a 2D reachability variant, walking through A and B in parallel.
- **"Number of distinct ways one string appears as a subsequence of another"** — a 2D counting variant.

The alternative — trying every possible subsequence or alignment directly — costs exponential time (`O(2^m)` or worse). Dynamic programming reduces it to `O(m * n)`, where `m` and `n` are the two sequences' lengths, by reusing the answer to "how do prefixes of length `i` and `j` relate" across every larger pair of prefixes.

## 3. Core concept

Every LCS-family problem reduces to the SAME per-cell decision, repeated for each pair of prefix lengths:

**The state.** `dp[i][j]` = the answer (length, count, cost, or reachability) considering the FIRST `i` characters of string A and the FIRST `j` characters of string B.

**The transition.** At each cell `(i, j)`, compare the current characters `A[i-1]` and `B[j-1]`:
- **If they MATCH:** the answer usually extends diagonally: `dp[i][j] = dp[i-1][j-1] + 1` (or similar, depending on the exact problem).
- **If they DON'T match:** the answer usually comes from skipping a character in ONE of the two strings: `dp[i][j] = combine(dp[i-1][j], dp[i][j-1])`.

**Why the DP works:** the KEY property is that `dp[i][j]` depends ONLY on cells with a smaller `i` or a smaller `j` (never larger) — specifically `dp[i-1][j-1]`, `dp[i-1][j]`, and `dp[i][j-1]`. Filling the table row by row (or column by column) guarantees every dependency is ready before it is needed.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp cell for two strings showing the match case reading diagonally and the mismatch case reading left or above">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">A[i-1]='c', B[j-1]='c' -- MATCH</text>
    <text x="10" y="45">dp[i][j] = dp[i-1][j-1] + 1 (extend the diagonal)</text>
    <text x="10" y="75" font-weight="bold">A[i-1]='c', B[j-1]='d' -- MISMATCH</text>
    <text x="10" y="95">dp[i][j] = max(dp[i-1][j], dp[i][j-1]) (skip one character)</text>
    <rect x="10" y="115" width="280" height="24" fill="#3fb950"/><text x="150" y="132" fill="#0d1117" text-anchor="middle" font-size="10">every cell reads only up/left/diagonal neighbors</text>
  </g>
</svg>

Matches extend the diagonal; mismatches fall back to the best of skipping a character from either string.

## 5. Runnable example

```java
// LongestCommonSubsequenceSignal.java
public class LongestCommonSubsequenceSignal {

    // Signal check: two strings, asking how they relate -- classic
    // LCS length computation.
    static int lcsLength(String a, String b) {
        int m = a.length(), n = b.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(lcsLength("abcde", "ace"));
        // 3 ("ace")
    }
}
```

**How to run:** `java LongestCommonSubsequenceSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Two strings," "transform one into another," or "interleave two strings" is the LCS-family signal.
2. Running `lcsLength` on `"abcde"` and `"ace"` confirms the longest common subsequence has length `3` (`"ace"`).
3. At every cell `(i, j)`, the algorithm only ever looks at cells with a smaller row or column index — this dependency structure is exactly what lets LCS-family problems be computed with a simple nested loop, filling the table once.
4. If instead the problem asks for minimum EDITS to transform one string into the other, recognize it as the DISTANCE variant: the transition changes to account for insert/delete/replace operations, but the two-string, 2D-table structure stays the same.
5. This upfront classification (matching vs. transforming vs. interleaving) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: confusing "subsequence" (elements can be skipped, order preserved) with "substring" (elements must be CONTIGUOUS) leads to using the wrong transition — a substring/subarray variant resets to `0` on a mismatch instead of falling back to `max(dp[i-1][j], dp[i][j-1])`.

- The state `dp[i][j]`, built from `dp[i-1][j-1]` (match) and `dp[i-1][j]`/`dp[i][j-1]` (mismatch): the core LCS-family signal.
- Distinguish LENGTH/COUNT problems (numeric `dp` values) from REACHABILITY problems (boolean `dp` values, like Interleaving String) — the combining step changes, but the 2D-prefix state structure stays the same.
- Watch for CONTIGUOUS variants (Maximum Length of Repeated Subarray), which reset on mismatch instead of falling back to a neighbor.
