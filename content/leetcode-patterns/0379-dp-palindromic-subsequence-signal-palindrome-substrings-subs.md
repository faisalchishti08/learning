---
card: leetcode-patterns
gi: 379
slug: dp-palindromic-subsequence-signal-palindrome-substrings-subs
title: "DP: Palindromic Subsequence — signal: palindrome substrings/subsequences or partitions"
---

## 1. What it is

Palindromic Subsequence DP is the pattern for questions about palindromes — strings that read the same forwards and backwards — WITHIN a single string. Unlike the LCS family (which compares two strings), this pattern examines ONE string against itself, checking whether some RANGE `s[i..j]` forms (or can become) a palindrome. Think of checking a string from the outside in: the first and last characters must match, then the same check repeats on what's left in the middle.

## 2. Why & when

Reach for this pattern whenever a problem's core question is about palindromes inside a SINGLE string — finding one, counting them, or figuring out the minimum changes to create one. The single-string, range-based nature is the tell: the DP state is usually `dp[i][j]`, representing a RANGE of one string, not two separate strings.

Learn to recognize these signals in a problem statement:

- **"Is this substring/string a palindrome," "longest palindromic substring/subsequence"** — the defining palindrome-range framing directly.
- **"Minimum insertions/deletions to make a string a palindrome"** — a transform-to-palindrome variant, closely related to Longest Common Subsequence between the string and its own reverse.
- **"Partition a string into palindromic pieces, minimize the number of cuts"** — a palindrome-partitioning variant, combining a "is this range a palindrome" check with a 1D DP over cut points.
- **"Count distinct palindromic subsequences"** — a counting variant over the same range-based state.

The alternative — checking every possible substring or subsequence for the palindrome property from scratch — costs at least O(n^2) just to enumerate ranges, often more to check each one naively (O(n^3) total). Dynamic programming reduces the CHECKING cost to O(1) per range by reusing whether smaller, inner ranges are already known to be palindromes.

## 3. Core concept

Every Palindromic Subsequence problem reduces to the SAME per-range decision, checked for ranges of increasing length:

**The state.** `dp[i][j]` = whether (or how much of) the range `s[i..j]` (inclusive) is a palindrome, or relates to one — a boolean for pure detection, a length or count for optimization/counting variants.

**The transition.** A range `s[i..j]` is a palindrome if its OUTER characters match (`s[i] == s[j]`) AND the INNER range `s[i+1..j-1]` is also a palindrome (or is empty/a single character, the base cases).

**Why the DP works:** the KEY property is that `dp[i][j]` depends ONLY on the smaller, STRICTLY INNER range `dp[i+1][j-1]` — so filling the table by increasing RANGE LENGTH (shortest ranges first) guarantees every dependency is ready before it is needed.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="range i to j checking outer characters match and inner range already known to be a palindrome">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">range s[i..j]: is it a palindrome?</text>
    <text x="10" y="45">check: s[i] == s[j] (outer characters match)</text>
    <text x="10" y="65">AND dp[i+1][j-1] is already known true (inner range)</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = outer match AND inner palindrome</text>
  </g>
</svg>

Each range's palindrome status is built from a strictly smaller range nested inside it.

## 5. Runnable example

```java
// PalindromicSubsequenceSignal.java
public class PalindromicSubsequenceSignal {

    // Signal check: is a range of a single string a palindrome --
    // built from increasing range lengths.
    static boolean[][] buildPalindromeTable(String s) {
        int n = s.length();
        boolean[][] dp = new boolean[n][n];

        for (int i = 0; i < n; i++) dp[i][i] = true;

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                if (s.charAt(i) != s.charAt(j)) continue;
                dp[i][j] = (len == 2) || dp[i + 1][j - 1];
            }
        }
        return dp;
    }

    public static void main(String[] args) {
        boolean[][] dp = buildPalindromeTable("aba");
        System.out.println(dp[0][2]);
        // true ("aba" is a palindrome)
    }
}
```

**How to run:** `java PalindromicSubsequenceSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Palindrome," "reads the same forwards and backwards," or "partition into palindromic pieces" is the Palindromic Subsequence signal.
2. Running `buildPalindromeTable("aba")` confirms `dp[0][2]` is `true`, since `'a' == 'a'` at the ends and the inner single character `'b'` is trivially a palindrome.
3. The table is filled by increasing LENGTH (`len`), not by row or column alone — this ordering guarantees `dp[i+1][j-1]` (a strictly shorter range) is always already computed.
4. If instead the problem asks for the MINIMUM insertions to make the whole string a palindrome, recognize it as a TRANSFORM variant: the transition changes to a minimize/count shape, but the range-based, "outer match plus inner sub-problem" structure stays the same.
5. This upfront classification (detection vs. counting vs. transforming vs. partitioning) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: filling the table row by row (increasing `i`) or column by column (increasing `j`) instead of by increasing RANGE LENGTH silently reads `dp[i+1][j-1]` before it has been computed, since a longer range can have a smaller starting row than a shorter range's inner cell.

- The state `dp[i][j]`, built from `dp[i+1][j-1]` (strictly inside): the core Palindromic Subsequence signal.
- Distinguish SUBSTRING problems (contiguous, `dp[i][j]` about the literal range `s[i..j]`) from SUBSEQUENCE problems (gaps allowed, like Longest Palindromic Subsequence) — the transition's base cases and combining step change, but the range-based state stays the same.
- Watch for problems that need the palindrome table as a SUB-ROUTINE inside a bigger DP (like Palindrome Partitioning II, which combines it with a 1D cut-counting DP).
