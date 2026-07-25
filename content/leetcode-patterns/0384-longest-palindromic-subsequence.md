---
card: leetcode-patterns
gi: 384
slug: longest-palindromic-subsequence
title: Longest Palindromic Subsequence
---

## 1. What it is

Given a string `s`, return the length of the LONGEST palindromic SUBSEQUENCE — characters can be skipped (gaps allowed), but the remaining characters, read in order, must form a palindrome. Example: `s = "bbbab"` → `4` (`"bbbb"`).

## 2. Why & when

Unlike Longest Palindromic Substring (contiguous), this problem allows GAPS, which means expand-around-center no longer works — you need the full interval DP. Use this shape whenever a problem allows characters to be SKIPPED while still requiring the remaining ones to form a palindrome.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the length of the longest palindromic subsequence within the range `s[i..j]`, for every range, filled by increasing range length.

**Steps:**
1. Base case: `dp[i][i] = 1` for every `i` (a single character is a palindrome of length 1).
2. For `len` from `2` to `n`, for `i` from `0` while `i + len - 1 < n`: let `j = i + len - 1`. If `s.charAt(i) == s.charAt(j)`, `dp[i][j] = dp[i+1][j-1] + 2` (both outer characters are usable, wrapping around the inner best answer; treat `dp[i+1][j-1]` as `0` when `i+1 > j-1`). Else, `dp[i][j] = max(dp[i+1][j], dp[i][j-1])` (drop one end, keep the better of the two).
3. Return `dp[0][n-1]`.

**Why it is correct:** if the outer characters MATCH, they can always be included as the OUTERMOST pair of some optimal palindromic subsequence, adding `2` to whatever the best answer is for the strictly inner range. If they DON'T match, at least one of them cannot be part of the answer, so the best is whichever remains after dropping ONE end — trying both and taking the max covers both cases.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table cell for matching outer characters adding 2 to the inner range versus mismatched outer characters taking the max of two smaller ranges">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s[i]==s[j] (match): dp[i][j] = dp[i+1][j-1] + 2</text>
    <text x="10" y="45">s[i]!=s[j] (mismatch): dp[i][j] = max(dp[i+1][j], dp[i][j-1])</text>
    <rect x="10" y="65" width="260" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">outer match wraps the inner best; mismatch drops one end</text>
  </g>
</svg>

Matching ends always extend the answer by two; mismatched ends fall back to the better of two smaller ranges.

## 5. Runnable example

```java
// LongestPalindromicSubsequence.java
public class LongestPalindromicSubsequence {

    // KEY INSIGHT: unlike the substring version, characters can be
    // skipped -- matching ends wrap the inner range's answer with +2,
    // mismatched ends fall back to the better of dropping one side.

    static int longestPalindromeSubseq(String s) {
        int n = s.length();
        int[][] dp = new int[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = 1;

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                if (s.charAt(i) == s.charAt(j)) {
                    int inner = (i + 1 <= j - 1) ? dp[i + 1][j - 1] : 0;
                    dp[i][j] = inner + 2;
                } else {
                    dp[i][j] = Math.max(dp[i + 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(longestPalindromeSubseq("bbbab"));
        // 4
        System.out.println(longestPalindromeSubseq("cbbd"));
        // 2
    }
}
```

**How to run:** `java LongestPalindromicSubsequence.java`

## 6. Walkthrough

Trace key cells for `longestPalindromeSubseq("bbbab")`, `n=5`:

| i,j | range | match? | dp[i][j] |
|---|---|---|---|
| 0,4 | "bbbab" | 'b'=='b', match | dp[1][3] + 2 |
| 1,3 | "bba" | 'b'!='a', mismatch | max(dp[2][3], dp[1][2]) |
| 2,3 | "ba" | 'b'!='a', mismatch | max(dp[3][3], dp[2][2]) = max(1,1)=1 |
| 1,2 | "bb" | 'b'=='b', match | dp[2][1]... treated as 0 (empty) + 2 = 2 |

Working back up: `dp[1][3] = max(1, 2) = 2`, so `dp[0][4] = 2 + 2 = 4`, matching the expected `4` (`"bbbb"`). Time complexity is O(n^2). Space is O(n^2) (reducible to O(n) with careful rolling-row management, since each `len` only needs the previous two diagonals).

## 7. Gotchas & takeaways

> Gotcha: forgetting to treat `dp[i+1][j-1]` as `0` when `i+1 > j-1` (an empty or invalid inner range) causes an array-index error or reads a stale value — always guard this case explicitly, since it occurs whenever the matching outer pair has zero or one character between them.

- `dp[i][j] = dp[i+1][j-1] + 2` on match, `max(dp[i+1][j], dp[i][j-1])` on mismatch: the subsequence variant of the palindrome-family template — contrast with the SUBSTRING version (Longest Palindromic Substring), which cannot skip characters and so never falls back to `max` of two ranges.
- This problem is ALSO solvable as: `n - (length of LCS between s and its own reverse)` gives the minimum deletions, but computing `dp[0][n-1]` directly (as shown here) gives the length itself without the extra reversal step.
- Related problems: Longest Palindromic Substring (the no-gaps, contiguous version), Minimum Insertion Steps to Make a String Palindrome (uses this exact `dp[i][j]` shape, then computes `n - dp[0][n-1]`).
