---
card: leetcode-patterns
gi: 378
slug: shortest-common-supersequence
title: Shortest Common Supersequence
---

## 1. What it is

Given two strings `str1` and `str2`, return the SHORTEST string that has BOTH `str1` and `str2` as subsequences. If multiple shortest answers exist, return any one of them. Example: `str1 = "abac"`, `str2 = "cab"` → `"cabac"` (length 5; `"cabac"` contains `"abac"` and `"cab"` as subsequences).

## 2. Why & when

This is the RECONSTRUCTION extension of LCS taken to its natural conclusion: the shortest supersequence is built by taking the LCS as a shared "backbone," then interleaving in every character that is NOT part of the LCS from both strings, in their original relative order. Use this shape whenever a problem asks for the shortest sequence that CONTAINS two given sequences as subsequences.

## 3. Core concept

**Key idea:** first compute the LCS table for `str1` and `str2`. Then walk the table BACKWARDS from `(m, n)`, building the supersequence: on a MATCH, the shared character is added ONCE; on a MISMATCH, the character from whichever string did NOT contribute to the larger neighbor is added (since that character must appear in the result, but is not part of the shared backbone).

**Steps:**
1. Fill `dp[i][j]` = LCS length of `str1[0..i)` and `str2[0..j)`, exactly as in the standard LCS template.
2. Walk backward from `(i, j) = (m, n)`, building a result (to be reversed at the end):
   - If `str1.charAt(i-1) == str2.charAt(j-1)`: prepend this character ONCE, move to `(i-1, j-1)`.
   - Else if `dp[i-1][j] >= dp[i][j-1]`: prepend `str1.charAt(i-1)`, move to `(i-1, j)`.
   - Else: prepend `str2.charAt(j-1)`, move to `(i, j-1)`.
3. When `i == 0` or `j == 0`, prepend any REMAINING characters from whichever string still has unconsumed prefix (`str1[0..i)` or `str2[0..j)`, in order).
4. Reverse the built result and return it.

**Why it is correct:** every character in the final answer is either part of the LCS (appearing exactly once, since both strings need it there) or is UNIQUE to one string at that position (appearing exactly once, since only one string needs it, and skipping it there would make that string's subsequence property fail). This is the minimum possible length: any shorter string would have to drop either a needed unique character or double-count a shared one, breaking the subsequence requirement for one of the two inputs.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="backward walk merging characters from both strings, matched characters added once and unmatched characters added from whichever side did not contribute to the larger neighbor">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">str1="abac", str2="cab"; LCS="ab"</text>
    <text x="10" y="45">backward: 'c' (str2 only) -&gt; 'a','b' (shared) -&gt; 'a','c' (str1 only)</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="150" y="82" fill="#0d1117" text-anchor="middle" font-size="10">merged (reversed): "cabac"</text>
  </g>
</svg>

The LCS backbone is kept once; every other character is folded in from whichever string it came from.

## 5. Runnable example

```java
// ShortestCommonSupersequence.java
public class ShortestCommonSupersequence {

    // KEY INSIGHT: build the LCS table first, then walk it backward,
    // keeping shared characters once and folding in every non-shared
    // character from whichever string it belongs to.

    static String shortestCommonSupersequence(String str1, String str2) {
        int m = str1.length(), n = str2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = (str1.charAt(i - 1) == str2.charAt(j - 1))
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }

        StringBuilder sb = new StringBuilder();
        int i = m, j = n;
        while (i > 0 && j > 0) {
            if (str1.charAt(i - 1) == str2.charAt(j - 1)) {
                sb.append(str1.charAt(i - 1));
                i--; j--;
            } else if (dp[i - 1][j] >= dp[i][j - 1]) {
                sb.append(str1.charAt(i - 1));
                i--;
            } else {
                sb.append(str2.charAt(j - 1));
                j--;
            }
        }
        while (i > 0) { sb.append(str1.charAt(i - 1)); i--; }
        while (j > 0) { sb.append(str2.charAt(j - 1)); j--; }

        return sb.reverse().toString();
    }

    public static void main(String[] args) {
        System.out.println(shortestCommonSupersequence("abac", "cab"));
        // cabac
    }
}
```

**How to run:** `java ShortestCommonSupersequence.java`

## 6. Walkthrough

Trace the backward walk for `shortestCommonSupersequence("abac", "cab")`, `dp` filled first (`dp[4][3] = 2`, LCS `"ab"`):

| step | i,j | comparison | appended |
|---|---|---|---|
| 1 | 4,3 | 'c' != 'b'; dp[3][3]=2 &gt;= dp[4][2]=1 | 'c' (from str1), move to i=3 |
| 2 | 3,3 | 'a' != 'b'; dp[2][3]=2 &gt;= dp[3][2]=1 | 'a' (from str1), move to i=2 |
| 3 | 2,3 | 'b' == 'b', match | 'b' (shared), move to i=1, j=2 |
| 4 | 1,2 | 'a' == 'a', match | 'a' (shared), move to i=0, j=1 |
| 5 | 0,1 | i=0, remaining str2 prefix | 'c' (from str2), move to j=0 |

Appended in order: `c, a, b, a, c`. Reversed, this gives `"cabac"`, length `5`, matching the expected answer. Time complexity is O(m · n) for the DP fill, plus O(m + n) for the backward walk. Space is O(m · n) for the table (needed in full for reconstruction, unlike the length-only LCS variant).

## 7. Gotchas & takeaways

> Gotcha: the reconstruction walk needs the FULL 2D `dp` table, not a space-optimized rolling-row version — reconstructing a path requires looking at values from potentially any earlier row, which a rolling optimization would have already discarded.

- The shortest supersequence's length is exactly `m + n - lcs`, the SAME arithmetic as Delete Operation for Two Strings — but here you also need the ACTUAL merged string, requiring the full reconstruction walk.
- The trailing `while` loops after the main backward walk are essential: once either `i` or `j` reaches `0`, any REMAINING prefix of the other string must be appended in full, since it has no more shared characters left to align with.
- Related problems: Longest Common Subsequence (the sub-routine this problem builds on), Delete Operation for Two Strings (the same underlying arithmetic, without needing to reconstruct the actual merged string).
