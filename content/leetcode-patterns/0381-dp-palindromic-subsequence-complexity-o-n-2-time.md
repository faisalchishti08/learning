---
card: leetcode-patterns
gi: 381
slug: dp-palindromic-subsequence-complexity-o-n-2-time
title: "DP: Palindromic Subsequence — complexity: O(n^2) time"
---

## 1. What it is

This page states and justifies the complexity of the Palindromic Subsequence pattern, and lists the problems that use it, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. If a string can be up to `1000` characters, an O(n^2) solution runs about `10^6` operations — comfortably fast. A brute-force approach checking every substring for the palindrome property from scratch is O(n^3), and checking every SUBSEQUENCE is exponential.

## 3. Core concept

**Time complexity: O(n^2).** Both templates examine each of the O(n^2) possible ranges `(i, j)` a constant number of times: expand-around-center does O(n) work for each of the `2n-1` centers (O(n^2) total); interval DP fills a table of O(n^2) cells, each in O(1) time using an already-computed inner value.

**Space complexity: O(1)** for expand-around-center (only tracking the current best range). **O(n^2)** for the interval `dp[i][j]` table, needed whenever many range queries must be answered, or when the palindrome table feeds into a larger DP.

**Why it is NOT O(n^3) like naive substring checking:** checking whether ONE substring `s[i..j]` is a palindrome directly takes O(j - i) time (comparing characters from both ends inward). Doing this NAIVELY for all O(n^2) substrings costs O(n^3) total. The DP instead REUSES the fact that `s[i..j]` is a palindrome exactly when `s[i] == s[j]` AND the already-known answer for `s[i+1..j-1]` is true — collapsing each check from O(n) down to O(1).

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="comparison of naive per substring checking costing n cubed versus dp reuse costing n squared">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">naive: O(n^2) substrings, each checked in O(n) -&gt; O(n^3)</text>
    <text x="10" y="45" font-weight="bold">DP: O(n^2) ranges, each checked in O(1) using dp[i+1][j-1] -&gt; O(n^2)</text>
    <rect x="10" y="65" width="260" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">reusing inner ranges drops one full factor of n</text>
  </g>
</svg>

Reusing the inner range's already-known answer collapses the per-range check from linear to constant time.

## 5. Runnable example

```java
// PalindromicSubsequenceComplexity.java
public class PalindromicSubsequenceComplexity {

    // Confirms O(n^2): counts cell computations done.
    static boolean[][] buildTableWithCounter(String s, long[] ops) {
        int n = s.length();
        boolean[][] dp = new boolean[n][n];
        for (int i = 0; i < n; i++) { dp[i][i] = true; ops[0]++; }

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = s.charAt(i) == s.charAt(j) && (len == 2 || dp[i + 1][j - 1]);
                ops[0]++;
            }
        }
        return dp;
    }

    public static void main(String[] args) {
        String s = "babad";
        long[] ops = {0};
        buildTableWithCounter(s, ops);
        System.out.println("n=" + s.length() + " ops=" + ops[0]);
        // ops is on the order of n^2 = 25 (exact count depends on triangular fill)
    }
}
```

**How to run:** `java PalindromicSubsequenceComplexity.java`

## 6. Walkthrough

1. `buildTableWithCounter` runs the standard interval DP template while counting every cell computation in `ops`.
2. For `s="babad"` (`n=5`), the printed `ops` count is `15` (`5` single-character base cases plus `10` two-or-more-character ranges) — on the order of `n^2`, not `n^3`.
3. Each cell computation does constant work (one or two character comparisons, one array read), so total work scales with the number of `(i, j)` pairs, which is O(n^2).
4. Compare this to checking every substring naively: even at `n=5`, this already does noticeably more character comparisons than the DP, and the gap grows fast as `n` increases.
5. This confirms the pattern is efficient enough for typical constraints (strings up to `1000`–`5000` characters), which is the check you should run before committing to this approach on a new problem.

## 7. Gotchas & takeaways

> Gotcha: some problems in this family (like Count Different Palindromic Subsequences) need a MORE careful transition to avoid double-counting distinct subsequences, which can push the per-cell work above O(1) — always re-derive the exact transition for counting variants rather than assuming the plain detection template's O(1)-per-cell bound automatically applies.

- Time: O(n^2); space: O(1) for expand-around-center, O(n^2) for the interval table.
- This is the same asymptotic shape as the LCS family (O(m·n), which becomes O(n^2) when comparing a string to itself) — both fill a 2D table where each cell reuses a smaller, already-computed sub-answer.
- Problems that use this pattern: Valid Palindrome II, Longest Palindromic Substring, Longest Palindromic Subsequence, Palindromic Substrings, Palindrome Partitioning II, Minimum Insertion Steps to Make a String Palindrome, Count Different Palindromic Subsequences, Longest Chunked Palindrome Decomposition.
