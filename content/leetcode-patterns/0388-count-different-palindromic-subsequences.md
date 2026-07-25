---
card: leetcode-patterns
gi: 388
slug: count-different-palindromic-subsequences
title: Count Different Palindromic Subsequences
---

## 1. What it is

Given a string `s`, return the number of DIFFERENT (distinct) non-empty palindromic subsequences it contains, modulo `10^9 + 7`. Two subsequences with the same characters in the same order count only ONCE, even if they can be formed by picking different positions. Example: `s = "bccb"` → `6` (`"b"`, `"c"`, `"bb"`, `"cc"`, `"bcb"`, `"bccb"`).

## 2. Why & when

This is the hardest counting variant in the palindrome family: unlike Palindromic Substrings (which counts every OCCURRENCE, even duplicates), this problem must count each DISTINCT subsequence exactly once, requiring careful handling of repeated characters to avoid double-counting. Use this shape whenever a problem counts distinct palindromic subsequences (not occurrences) within a single string.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the number of distinct non-empty palindromic subsequences within `s[i..j]`, using, for the MATCHING character at both ends, the NEAREST occurrences of that character inside the range to avoid recounting the same subsequence twice.

**Steps:**
1. Precompute `next[i][c]` = the leftmost position `>= i` in the whole string where character `c` occurs (or a sentinel if none), and `prev[j][c]` = the rightmost position `<= j` where `c` occurs (or a sentinel if none), for every position and every character.
2. Base case: `dp[i][i] = 1` (a single character is one distinct palindrome).
3. For each range `[i, j]` (increasing length), for each character `c` present in the range: let `l = next[i][c]`, `r = prev[j][c]` (both bounded within `[i, j]`).
   - If `c` does not occur in `[i, j]` (`l > j`), contribute `0`.
   - If `l == r` (`c` occurs EXACTLY once in the range), contribute `1` (just the single character `c` itself).
   - If `l < r` (`c` occurs two or more times), contribute `2` (the character `c` alone, AND the pair `cc`) PLUS `dp[l+1][r-1]` (every distinct palindrome strictly between the nearest two occurrences, since wrapping `c` around any of THOSE also forms a new distinct palindrome).
4. Sum the contributions over all characters present, modulo `10^9 + 7`. Return `dp[0][n-1]`.

**Why it is correct:** for a fixed character `c`, every palindrome starting and ending with `c` is uniquely determined by choosing the OUTER pair of `c`s to be the NEAREST pair (`l` and `r`) — any wider matching pair would just reproduce the same distinct subsequence surrounded by extra ignored `c`s. This is why using the nearest occurrences, rather than every possible pair, avoids double-counting the same distinct subsequence.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="range bccb showing character b occurring at the nearest positions 0 and 3 contributing b bb and the inner range cc plus wrapped bb">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s="bccb"; range [0,3]; character 'b': nearest occurrences at 0 and 3</text>
    <text x="10" y="45">l=0, r=3, l&lt;r -&gt; contribute 2 ("b", "bb") + dp[1][2] (inner "cc" range)</text>
    <text x="10" y="65">dp[1][2] = 2 ("c", "cc") -&gt; total from 'b': 2 + 2 = 4</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">plus character 'c' contributes 2 more -&gt; 6 total</text>
  </g>
</svg>

The nearest matching pair of a character wraps every distinct palindrome found strictly inside it, without re-deriving them.

## 5. Runnable example

```java
// CountDifferentPalindromicSubsequences.java
public class CountDifferentPalindromicSubsequences {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: for each character, use only its NEAREST occurrence
    // pair inside the range as the outer wrap -- this is the unique
    // way to avoid counting the same distinct subsequence twice.

    static int countPalindromicSubsequences(String s) {
        int n = s.length();
        int[][] next = new int[n + 1][26];
        int[][] prev = new int[n][26];

        for (int c = 0; c < 26; c++) next[n][c] = n;
        for (int i = n - 1; i >= 0; i--) {
            for (int c = 0; c < 26; c++) next[i][c] = next[i + 1][c];
            next[i][s.charAt(i) - 'a'] = i;
        }
        for (int c = 0; c < 26; c++) prev[0][c] = (s.charAt(0) - 'a' == c) ? 0 : -1;
        for (int j = 1; j < n; j++) {
            for (int c = 0; c < 26; c++) prev[j][c] = prev[j - 1][c];
            prev[j][s.charAt(j) - 'a'] = j;
        }

        long[][] dp = new long[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = 1;

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                long total = 0;
                for (int c = 0; c < 26; c++) {
                    int l = next[i][c];
                    int r = prev[j][c];
                    if (l > j || r < i || l > r) continue;
                    if (l == r) {
                        total += 1;
                    } else {
                        total += 2;
                        if (l + 1 <= r - 1) {
                            total += dp[l + 1][r - 1];
                        }
                    }
                }
                dp[i][j] = ((total % MOD) + MOD) % MOD;
            }
        }
        return (int) dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(countPalindromicSubsequences("bccb"));
        // 6
    }
}
```

**How to run:** `java CountDifferentPalindromicSubsequences.java`

## 6. Walkthrough

Trace `countPalindromicSubsequences("bccb")`, `n=4` (indices: `0='b', 1='c', 2='c', 3='b'`):

| range | character | l, r | contribution |
|---|---|---|---|
| [1,2] "cc" | 'c' | l=1, r=2 | 2 (dp[2][1] invalid, skip) |
| [0,2] "bcc" | 'b' | l=0, r=0 | 1 (single occurrence) |
| [0,2] "bcc" | 'c' | l=1, r=2 | 2 |
| [0,3] "bccb" | 'b' | l=0, r=3 | 2 + dp[1][2] = 2 + 2 = 4 |
| [0,3] "bccb" | 'c' | l=1, r=2 | 2 |

`dp[0][3] = 4 + 2 = 6`, matching the expected `6`. Time complexity is O(26 · n^2) (26 characters checked per cell). Space is O(n^2) for `dp`, plus O(26n) for the `next`/`prev` tables.

## 7. Gotchas & takeaways

> Gotcha: using EVERY pair of matching characters (not just the nearest one) inside the range would count the same distinct subsequence multiple times — for example, in `"aaa"`, using the outer pair `(0,2)` and separately the pair `(0,1)` both wrapped around the middle would double-count `"a"` itself; the nearest-pair rule is what makes each distinct subsequence counted exactly once.

- The `next`/`prev` lookup tables, precomputed once in O(26n), turn "find the nearest occurrence of character `c`" from an O(n) scan into an O(1) lookup — essential for keeping the overall algorithm at O(26n^2) instead of O(26n^3).
- Modulo arithmetic must handle the case where a subtraction (not present in this version, but common in ALTERNATIVE formulations) could go negative — this template avoids subtraction entirely by using the nearest-pair method, so only addition and modulo are needed.
- Related problems: Palindromic Substrings (counts OCCURRENCES, not distinct subsequences — a much simpler problem), Longest Palindromic Subsequence (measures LENGTH, not the count of distinct palindromic subsequences).
