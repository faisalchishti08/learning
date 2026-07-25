---
card: leetcode-patterns
gi: 372
slug: minimum-ascii-delete-sum-for-two-strings
title: Minimum ASCII Delete Sum for Two Strings
---

## 1. What it is

Given two strings `s1` and `s2`, return the MINIMUM sum of ASCII values of the characters you must DELETE so both strings become equal. Example: `s1 = "sea"`, `s2 = "eat"` → `231` (delete `'s'` from `s1`, `'t'` from `s2`; `'s'=115`, `'t'=116`, sum `231`).

## 2. Why & when

This is Delete Operation for Two Strings with WEIGHTED deletions (ASCII value instead of a flat count of `1` per deletion). Because the weights differ per character, you CANNOT just reuse the plain LCS length arithmetic — you need a dedicated DP that directly minimizes the deleted ASCII sum. Use this shape whenever a "make two strings equal via deletion" problem attaches a COST to each deletion that varies by character.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum ASCII sum deleted to make the first `i` characters of `s1` equal the first `j` characters of `s2`, for every `i, j`.

**Steps:**
1. Base cases: `dp[0][0] = 0`. `dp[i][0] = dp[i-1][0] + s1.charAt(i-1)` (deleting all of `s1`'s prefix, one character's ASCII value at a time). `dp[0][j] = dp[0][j-1] + s2.charAt(j-1)` (symmetric for `s2`).
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `s1.charAt(i-1) == s2.charAt(j-1)`, `dp[i][j] = dp[i-1][j-1]` (no deletion needed here — the matching character stays in both). Else, `dp[i][j] = min(dp[i-1][j] + s1.charAt(i-1), dp[i][j-1] + s2.charAt(j-1))` (delete this character from whichever string is cheaper to delete from, given the rest of the table).
3. Return `dp[m][n]`.

**Why it is correct:** at a MATCHING position, keeping both characters costs nothing, so the best answer simply carries forward from the diagonal, with no additions. At a MISMATCH, one of the two current characters must eventually be deleted (they cannot both remain, since the strings must become equal); trying both options (delete from `s1`, or delete from `s2`) and taking the minimum ensures the cheaper path is chosen.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table for sea and eat showing base row deletions accumulating ascii values and a mismatch cell choosing the cheaper deletion">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s1="sea", s2="eat"</text>
    <text x="10" y="45">dp[1][0] = 0 + ascii('s') = 115 (delete 's' alone)</text>
    <text x="10" y="65">dp[1][1]: 's' != 'e' -&gt; min(dp[0][1]+115, dp[1][0]+ascii('e'))</text>
    <rect x="10" y="85" width="280" height="24" fill="#3fb950"/><text x="150" y="102" fill="#0d1117" text-anchor="middle" font-size="10">each mismatch picks the cheaper deletion direction</text>
  </g>
</svg>

The base row and column accumulate the cost of deleting an entire prefix; interior cells pick the cheaper of two deletion directions.

## 5. Runnable example

```java
// MinimumAsciiDeleteSumForTwoStrings.java
public class MinimumAsciiDeleteSumForTwoStrings {

    // KEY INSIGHT: same LCS-family table shape, but the "cost" of a
    // mismatch step is the ASCII value of the deleted character, not
    // a flat 1 -- weighted edit distance instead of length arithmetic.

    static int minimumDeleteSum(String s1, String s2) {
        int m = s1.length(), n = s2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            dp[i][0] = dp[i - 1][0] + s1.charAt(i - 1);
        }
        for (int j = 1; j <= n; j++) {
            dp[0][j] = dp[0][j - 1] + s2.charAt(j - 1);
        }

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = Math.min(
                            dp[i - 1][j] + s1.charAt(i - 1),
                            dp[i][j - 1] + s2.charAt(j - 1));
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(minimumDeleteSum("sea", "eat"));
        // 231
        System.out.println(minimumDeleteSum("delete", "leet"));
        // 403
    }
}
```

**How to run:** `java MinimumAsciiDeleteSumForTwoStrings.java`

## 6. Walkthrough

Trace `minimumDeleteSum("sea", "eat")`, `m=3, n=3`:

| i,j | chars | match? | dp[i][j] |
|---|---|---|---|
| 1,0 | (base) | - | ascii('s')=115 |
| 0,1 | (base) | - | ascii('e')=101 |
| 1,1 | 's','e' | no | min(dp[0][1]+115, dp[1][0]+101) = min(216,216) = 216 |
| 3,3 | (final) | - | 231 |

`dp[3][3] = 231`, matching the expected answer (delete `'s'`=115 and `'t'`=116, total `231`). Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: reusing the PLAIN LCS-length arithmetic (`m + n - 2*lcs`) from Delete Operation for Two Strings does NOT work here — since deletion costs vary per character, the cheapest set of matches to keep is not necessarily the LONGEST one, so a dedicated weighted DP is required.

- `dp[i][j] = dp[i-1][j-1]` on match (free), `min(...)+ascii` on mismatch: the weighted variant of the LCS-family template.
- The base row and column are NOT zero here (unlike plain LCS) — they accumulate the real cost of deleting an entire prefix.
- Related problems: Delete Operation for Two Strings (the unweighted version, solvable via LCS length arithmetic directly), Edit Distance (a related but different cost model, allowing insert and replace operations too, not just delete).
