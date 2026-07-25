---
card: leetcode-patterns
gi: 371
slug: delete-operation-for-two-strings
title: Delete Operation for Two Strings
---

## 1. What it is

Given two strings `word1` and `word2`, return the MINIMUM number of DELETE operations needed so both strings become EQUAL, where each operation deletes exactly one character from EITHER string. Example: `word1 = "sea"`, `word2 = "eat"` → `2` (delete `'s'` from `"sea"`, delete `'t'` from `"eat"`, both become `"ea"`).

## 2. Why & when

This is the Longest Common Subsequence pattern with an algebraic twist: the characters that stay (and end up equal in both strings) form exactly their LCS — every character NOT in the LCS must be deleted from whichever string it came from. Use this shape whenever a problem asks for the minimum deletions to make two strings equal, since "keep the longest common part, delete the rest" is always optimal.

## 3. Core concept

**Key idea:** compute `lcs = length of the longest common subsequence of word1 and word2`. The characters outside the LCS in `word1` (`word1.length() - lcs` of them) and outside the LCS in `word2` (`word2.length() - lcs` of them) must all be deleted.

**Steps:**
1. Run the standard LCS DP on `word1` and `word2` to get `lcs = dp[m][n]`.
2. Return `(m - lcs) + (n - lcs)`, which simplifies to `m + n - 2 * lcs`.

**Why it is correct:** the LCS is the LARGEST set of characters that can remain identical (in relative order) in both strings without deleting them. Any characters NOT part of this common subsequence must be deleted from whichever string they belong to, since they have no matching counterpart to preserve — and keeping any smaller common subsequence would only require MORE deletions, never fewer.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="word sea and eat with common subsequence ea highlighted, showing one deletion from each word">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">word1="sea", word2="eat"; LCS = "ea", length 2</text>
    <text x="10" y="45">word1 deletions: 3 - 2 = 1 ('s')</text>
    <text x="10" y="65">word2 deletions: 3 - 2 = 1 ('t')</text>
    <rect x="10" y="85" width="220" height="24" fill="#3fb950"/><text x="120" y="102" fill="#0d1117" text-anchor="middle" font-size="10">total deletions = 1 + 1 = 2</text>
  </g>
</svg>

Everything outside the shared "ea" backbone must be deleted from whichever word it sits in.

## 5. Runnable example

```java
// DeleteOperationForTwoStrings.java
public class DeleteOperationForTwoStrings {

    // KEY INSIGHT: keeping the LCS and deleting everything else is
    // always optimal -- reduce this problem to computing the LCS
    // length, then apply m + n - 2*lcs.

    static int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                dp[i][j] = (word1.charAt(i - 1) == word2.charAt(j - 1))
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        int lcs = dp[m][n];
        return (m - lcs) + (n - lcs);
    }

    public static void main(String[] args) {
        System.out.println(minDistance("sea", "eat"));
        // 2
        System.out.println(minDistance("leetcode", "etco"));
        // 4
    }
}
```

**How to run:** `java DeleteOperationForTwoStrings.java`

## 6. Walkthrough

Trace `minDistance("sea", "eat")`:

1. Run the LCS DP: `dp[3][3] = 2`, matching common subsequence `"ea"`.
2. `word1` deletions needed: `m - lcs = 3 - 2 = 1`.
3. `word2` deletions needed: `n - lcs = 3 - 2 = 1`.
4. Total: `1 + 1 = 2`, matching the expected answer.

Time complexity is O(m · n), dominated by the LCS computation. Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: computing `m + n - lcs` (forgetting the factor of `2`) is a common off-by-one-style mistake — BOTH strings independently lose their non-LCS characters, so the LCS length must be subtracted from EACH string's length separately, then those two deletion counts are added together.

- This problem is a direct APPLICATION of the LCS length, not a new DP shape — always check whether a "minimum operations to make two strings related" problem reduces to LCS arithmetic before writing a new recurrence.
- The two strings do NOT need to become any specific target string — only equal to EACH OTHER, which is exactly what the shared LCS represents once non-matching characters are removed.
- Related problems: Longest Common Subsequence (the exact sub-routine this problem is built on), Minimum ASCII Delete Sum for Two Strings (the same idea, but MINIMIZING the sum of ASCII values deleted instead of the count of deletions).
