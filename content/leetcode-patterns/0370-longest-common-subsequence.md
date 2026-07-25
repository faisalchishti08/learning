---
card: leetcode-patterns
gi: 370
slug: longest-common-subsequence
title: Longest Common Subsequence
---

## 1. What it is

Given two strings `text1` and `text2`, return the length of their LONGEST COMMON SUBSEQUENCE — the longest sequence of characters that appears in BOTH strings, in the same relative order, but not necessarily contiguous. If there is no common subsequence, return `0`. Example: `text1 = "abcde"`, `text2 = "ace"` → `3` (`"ace"`).

## 2. Why & when

This is the textbook LCS problem, the exact pattern this section is named after. Use this shape whenever you need to compare two sequences and measure how much of their content overlaps while preserving relative order.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the length of the LCS between the first `i` characters of `text1` and the first `j` characters of `text2`, for every `i` from `0` to `text1.length()` and `j` from `0` to `text2.length()`.

**Steps:**
1. Create `dp[m+1][n+1]`, all zeros.
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `text1.charAt(i-1) == text2.charAt(j-1)`, `dp[i][j] = dp[i-1][j-1] + 1`; else `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
3. Return `dp[m][n]`.

**Why it is correct:** if the current characters MATCH, they can always be included in an optimal common subsequence, extending whatever the best answer was for both strings WITHOUT these two characters (`dp[i-1][j-1] + 1`). If they DON'T match, the best answer must exclude at least one of the two current characters, so it equals the better of "drop this character of `text1`" (`dp[i][j-1]`) or "drop this character of `text2`" (`dp[i-1][j]`).

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table for abcde and ace showing the diagonal growth through matched characters a c e">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">text1="abcde", text2="ace"</text>
    <text x="10" y="45">dp[1][1]: 'a'=='a' -&gt; dp[0][0]+1 = 1</text>
    <text x="10" y="65">dp[3][2]: 'c'=='c' -&gt; dp[2][1]+1 = 2</text>
    <text x="10" y="85">dp[5][3]: 'e'=='e' -&gt; dp[4][2]+1 = 3</text>
    <rect x="10" y="105" width="240" height="24" fill="#3fb950"/><text x="130" y="122" fill="#0d1117" text-anchor="middle" font-size="10">dp[5][3] = 3</text>
  </g>
</svg>

Each matched character extends the diagonal by one; mismatches carry the best value forward.

## 5. Runnable example

```java
// LongestCommonSubsequence.java
public class LongestCommonSubsequence {

    // KEY INSIGHT: matched characters extend the diagonal by one;
    // mismatched characters fall back to the better of dropping one
    // character from either string.

    static int longestCommonSubsequence(String text1, String text2) {
        int m = text1.length(), n = text2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (text1.charAt(i - 1) == text2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(longestCommonSubsequence("abcde", "ace"));
        // 3
        System.out.println(longestCommonSubsequence("abc", "def"));
        // 0
    }
}
```

**How to run:** `java LongestCommonSubsequence.java`

## 6. Walkthrough

Trace key cells for `longestCommonSubsequence("abcde", "ace")`:

| i,j | chars | match? | dp[i][j] |
|---|---|---|---|
| 1,1 | 'a','a' | yes | dp[0][0]+1=1 |
| 3,2 | 'c','c' | yes | dp[2][1]+1=2 |
| 5,3 | 'e','e' | yes | dp[4][2]+1=3 |

`dp[5][3] = 3`, matching the expected `3`. Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n)) with rolling rows).

## 7. Gotchas & takeaways

> Gotcha: initializing `dp[0][j]` and `dp[i][0]` to anything other than `0` breaks the recurrence — an empty prefix of either string has a common subsequence of length `0` with anything, by definition.

- `dp[i][j] = dp[i-1][j-1]+1` on match, `max(dp[i-1][j], dp[i][j-1])` on mismatch: the exact template every other problem on this card's section builds from.
- The characters DON'T need to be contiguous — only their relative order must be preserved, which is what distinguishes "subsequence" from "substring."
- Related problems: Uncrossed Lines (the identical DP, framed as connecting lines between two arrays instead of matching string characters), Delete Operation for Two Strings (derives the answer FROM the LCS length, via `m + n - 2*lcs`).
