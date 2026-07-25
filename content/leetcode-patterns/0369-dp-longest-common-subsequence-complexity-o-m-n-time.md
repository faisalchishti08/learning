---
card: leetcode-patterns
gi: 369
slug: dp-longest-common-subsequence-complexity-o-m-n-time
title: "DP: Longest Common Subsequence — complexity: O(m*n) time"
---

## 1. What it is

This page states and justifies the complexity of the LCS-family pattern, and lists the problems that use it, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. If both strings can be up to `1000` characters, an O(m · n) solution runs about `10^6` operations — comfortably fast. A brute-force approach trying every subsequence of one string against the other is exponential and will time out on the same input.

## 3. Core concept

**Time complexity: O(m · n).** The DP fills a table of size `(m+1) x (n+1)`, where `m` and `n` are the two input lengths. Each cell does O(1) work (comparing two characters and reading up to three neighbors), giving O(m · n) total.

**Space complexity: O(m · n)** for the full 2D table, or **O(min(m, n))** if space-optimized to two rolling rows (since `dp[i][j]` only ever needs the CURRENT row and the PREVIOUS row, never anything further back).

**Why it is NOT exponential like brute force:** trying every subsequence of string A (there are `2^m` of them) and checking each against B directly costs O(2^m · n). The DP instead computes each `(i, j)` prefix-pair's answer EXACTLY ONCE, and reuses it for every larger prefix pair that needs it — collapsing the exponential subsequence enumeration into a polynomial table fill.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="grid of m by n cells showing total work as their product">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">m rows (prefixes of A) x n columns (prefixes of B)</text>
    <rect x="10" y="35" width="200" height="90" fill="none" stroke="#8b949e"/>
    <text x="110" y="85" text-anchor="middle">m x n cells</text>
    <text x="230" y="85">each cell: O(1) work</text>
    <rect x="10" y="135" width="260" height="20" fill="#3fb950"/><text x="140" y="150" fill="#0d1117" text-anchor="middle" font-size="10">total time = O(m * n)</text>
  </g>
</svg>

Every `(i, j)` prefix pair is visited once, each doing constant comparison-and-lookup work.

## 5. Runnable example

```java
// LongestCommonSubsequenceComplexity.java
public class LongestCommonSubsequenceComplexity {

    // Confirms O(m*n): counts cell computations done.
    static int lcsLengthWithCounter(String a, String b, long[] ops) {
        int m = a.length(), n = b.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = (a.charAt(i - 1) == b.charAt(j - 1))
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
                ops[0]++;
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        String a = "abcde", b = "ace";
        long[] ops = {0};
        int len = lcsLengthWithCounter(a, b, ops);
        System.out.println("len=" + len + " ops=" + ops[0]);
        // len=3, ops = m * n = 5 * 3 = 15
    }
}
```

**How to run:** `java LongestCommonSubsequenceComplexity.java`

## 6. Walkthrough

1. `lcsLengthWithCounter` runs the standard LCS template while counting every cell computation in `ops`.
2. For `a="abcde"` (`m=5`), `b="ace"` (`n=3`), the printed `ops` count is exactly `m * n = 15`, confirming the loop structure matches the claimed O(m · n) bound.
3. Each cell computation does constant work (one character comparison, one or two array reads, one write), so total work scales exactly with the number of `(i, j)` pairs.
4. Compare this to enumerating every subsequence of `a` (there are `2^5 = 32` of them) and checking each against `b`: even at this tiny size, the exponential approach already does more comparisons than the DP, and the gap widens fast as `m` grows.
5. This confirms the pattern is efficient enough for typical constraints (strings up to `1000`–`5000` characters), which is the check you should run before committing to this approach on a new problem.

## 7. Gotchas & takeaways

> Gotcha: reconstructing the actual subsequence (not just its length) requires keeping the FULL 2D table for the backward walk — the space-optimized two-row version only works when the final answer is a number, not when you need to trace back the actual matched characters.

- Time: O(m · n); space: O(m · n) for the full table, O(min(m, n)) if only the final numeric answer is needed.
- Compare against Unbounded/0-1 Knapsack, which also fills an O(n · capacity) table — the SAME "2D table, each cell O(1)" shape, just with different axes (two strings here, instead of items and capacity).
- Problems that use this pattern: Longest Common Subsequence, Delete Operation for Two Strings, Minimum ASCII Delete Sum for Two Strings, Uncrossed Lines, Interleaving String, Maximum Length of Repeated Subarray, Edit Distance, Distinct Subsequences, Shortest Common Supersequence.
