---
card: leetcode-patterns
gi: 374
slug: interleaving-string
title: Interleaving String
---

## 1. What it is

Given three strings `s1`, `s2`, and `s3`, return `true` if `s3` can be formed by INTERLEAVING `s1` and `s2` — merging their characters together while preserving each string's own internal character order. Example: `s1 = "aabcc"`, `s2 = "dbbca"`, `s3 = "aadbbcbcac"` → `true`.

## 2. Why & when

This is the REACHABILITY variant of the LCS-family pattern: instead of matching two strings against EACH OTHER, you walk through `s1` and `s2` IN PARALLEL, checking whether their combined characters can be arranged to exactly build `s3`. Use this shape whenever a problem asks whether two sequences can be MERGED (preserving each one's internal order) to produce a third target sequence.

## 3. Core concept

**Key idea:** build `dp[i][j]` = `true` if the first `i` characters of `s1` and the first `j` characters of `s2` can interleave to form the first `i + j` characters of `s3`, for every `i` from `0` to `s1.length()` and `j` from `0` to `s2.length()`.

**Steps:**
1. If `s1.length() + s2.length() != s3.length()`, return `false` immediately (an interleaving must use every character from both source strings exactly once).
2. Create `dp[m+1][n+1]`, with `dp[0][0] = true`.
3. Fill the first row and column: `dp[i][0] = dp[i-1][0] && s1.charAt(i-1) == s3.charAt(i-1)`; `dp[0][j] = dp[0][j-1] && s2.charAt(j-1) == s3.charAt(j-1)`.
4. For `i` from `1` to `m`, for `j` from `1` to `n`: `dp[i][j] = (dp[i-1][j] && s1.charAt(i-1) == s3.charAt(i+j-1)) || (dp[i][j-1] && s2.charAt(j-1) == s3.charAt(i+j-1))`.
5. Return `dp[m][n]`.

**Why it is correct:** the character at position `i+j-1` of `s3` (the LAST character consumed so far) must have come from EITHER `s1`'s `i`-th character or `s2`'s `j`-th character — there is no third option. `dp[i][j]` is reachable if EITHER path (taking this character from `s1`, given `dp[i-1][j]` was already reachable, or from `s2`, given `dp[i][j-1]` was already reachable) matches `s3`'s actual character at that position.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp cell for interleaving showing two possible sources for the current character of s3, from s1 or from s2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">computing dp[i][j], checking s3[i+j-1]</text>
    <text x="10" y="45">from s1: dp[i-1][j] is true AND s1[i-1] == s3[i+j-1]</text>
    <text x="10" y="65">from s2: dp[i][j-1] is true AND s2[j-1] == s3[i+j-1]</text>
    <rect x="10" y="85" width="280" height="24" fill="#3fb950"/><text x="150" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = either path succeeding (OR)</text>
  </g>
</svg>

Each cell checks two possible sources for the current character — reachable if at least one of them works.

## 5. Runnable example

```java
// InterleavingString.java
public class InterleavingString {

    // KEY INSIGHT: the last character consumed in s3 came from EITHER
    // s1 or s2 -- reachability OR's the two possible sources, each
    // requiring both a character match and a reachable prior state.

    static boolean isInterleave(String s1, String s2, String s3) {
        int m = s1.length(), n = s2.length();
        if (m + n != s3.length()) return false;

        boolean[][] dp = new boolean[m + 1][n + 1];
        dp[0][0] = true;

        for (int i = 1; i <= m; i++) {
            dp[i][0] = dp[i - 1][0] && s1.charAt(i - 1) == s3.charAt(i - 1);
        }
        for (int j = 1; j <= n; j++) {
            dp[0][j] = dp[0][j - 1] && s2.charAt(j - 1) == s3.charAt(j - 1);
        }

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                boolean fromS1 = dp[i - 1][j] && s1.charAt(i - 1) == s3.charAt(i + j - 1);
                boolean fromS2 = dp[i][j - 1] && s2.charAt(j - 1) == s3.charAt(i + j - 1);
                dp[i][j] = fromS1 || fromS2;
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(isInterleave("aabcc", "dbbca", "aadbbcbcac"));
        // true
        System.out.println(isInterleave("aabcc", "dbbca", "aadbbbaccc"));
        // false
    }
}
```

**How to run:** `java InterleavingString.java`

## 6. Walkthrough

Trace a few cells for `isInterleave("aa", "bb", "abab")` (a smaller example), `m=2, n=2`:

| i,j | s3 char checked | fromS1 | fromS2 | dp[i][j] |
|---|---|---|---|---|
| 1,0 | s3[0]='a' | dp[0][0]&&'a'=='a' = true | - | true |
| 1,1 | s3[1]='b' | dp[0][1]&&'a'=='b' = false | dp[1][0]&&'b'=='b' = true | true |
| 2,2 | s3[3]='b' | dp[1][2]&&'a'=='b' = false | dp[2][1]&&'b'=='b' = true | true |

`dp[2][2] = true`, confirming `"abab"` is a valid interleaving of `"aa"` and `"bb"`. Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: forgetting the upfront length check (`m + n != s3.length()`) can still produce a wrong `false`-vs-crash outcome depending on implementation, but more importantly it wastes an O(m·n) computation on an input that is trivially impossible — always check total length first.

- `dp[i][j] = (dp[i-1][j] && match with s1) || (dp[i][j-1] && match with s2)`: the reachability variant of the LCS-family template, checking two possible SOURCES instead of one match/mismatch branch.
- This is NOT the same as checking whether `s1` and `s2` are both subsequences of `s3` independently — the characters must interleave to form `s3` EXACTLY, using every character from both exactly once.
- Related problems: Word Break (a similar 1D reachability DP, checking dictionary words instead of two parallel source strings), Distinct Subsequences (also 2D over two strings, but COUNTING ways instead of checking reachability).
