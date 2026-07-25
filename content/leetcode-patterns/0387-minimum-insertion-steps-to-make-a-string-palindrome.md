---
card: leetcode-patterns
gi: 387
slug: minimum-insertion-steps-to-make-a-string-palindrome
title: Minimum Insertion Steps to Make a String Palindrome
---

## 1. What it is

Given a string `s`, return the MINIMUM number of characters you must INSERT anywhere in `s` to make the whole string a palindrome. Example: `s = "mbadm"` → `2` (insert to get `"mbdadbm"` or `"mdbabdm"`, both palindromes, using 2 insertions).

## 2. Why & when

This is the MINIMIZE variant of interval palindrome DP: instead of checking whether a range IS a palindrome, compute how many insertions it would take to MAKE it one. Use this shape whenever a problem asks for the minimum edits (specifically insertions) to transform a string into a palindrome.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum insertions needed to make the range `s[i..j]` a palindrome, for every range, filled by increasing range length.

**Steps:**
1. Base case: `dp[i][i] = 0` for every `i` (a single character is already a palindrome).
2. For `len` from `2` to `n`, for `i` from `0` while `i + len - 1 < n`: let `j = i + len - 1`. If `s.charAt(i) == s.charAt(j)`, `dp[i][j] = dp[i+1][j-1]` (treated as `0` when `i+1 > j-1`) — the matching ends need no extra insertion. Else, `dp[i][j] = 1 + min(dp[i+1][j], dp[i][j-1])`.
3. Return `dp[0][n-1]`.

**Why it is correct:** if the outer characters ALREADY match, no insertion is needed at this level — the answer is exactly the cost for the strictly inner range. If they DON'T match, ONE insertion is required to create a matching partner for whichever character is "harder" to fix, and the two candidate moves (insert a copy of `s[j]` at the front, reducing to `dp[i][j-1]`; or insert a copy of `s[i]` at the back, reducing to `dp[i+1][j]`) both make exactly one unit of progress — taking the minimum finds the cheaper path.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp cell showing matching ends needing zero extra insertions versus mismatched ends needing one insertion plus the better of two smaller ranges">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s[i]==s[j] (match): dp[i][j] = dp[i+1][j-1] (free)</text>
    <text x="10" y="45">s[i]!=s[j] (mismatch): dp[i][j] = 1 + min(dp[i+1][j], dp[i][j-1])</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="150" y="82" fill="#0d1117" text-anchor="middle" font-size="10">matching ends cost nothing; mismatches cost exactly 1 plus the cheaper sub-problem</text>
  </g>
</svg>

Matching ends propagate the inner cost unchanged; mismatched ends pay one insertion and pick the cheaper remaining sub-problem.

## 5. Runnable example

```java
// MinimumInsertionStepsToMakeAStringPalindrome.java
public class MinimumInsertionStepsToMakeAStringPalindrome {

    // KEY INSIGHT: matching outer characters cost nothing; mismatched
    // ones cost exactly one insertion plus the cheaper of two smaller
    // ranges -- the minimize variant of the interval palindrome DP.

    static int minInsertions(String s) {
        int n = s.length();
        int[][] dp = new int[n][n];

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                if (s.charAt(i) == s.charAt(j)) {
                    dp[i][j] = (i + 1 <= j - 1) ? dp[i + 1][j - 1] : 0;
                } else {
                    dp[i][j] = 1 + Math.min(dp[i + 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(minInsertions("mbadm"));
        // 2
        System.out.println(minInsertions("leetcode"));
        // 5
    }
}
```

**How to run:** `java MinimumInsertionStepsToMakeAStringPalindrome.java`

## 6. Walkthrough

Trace key cells for `minInsertions("mbadm")`, `n=5`:

| i,j | range | match? | dp[i][j] |
|---|---|---|---|
| 0,4 | "mbadm" | 'm'=='m', match | dp[1][3] |
| 1,3 | "bad" | 'b'!='d', mismatch | 1 + min(dp[2][3], dp[1][2]) |
| 2,3 | "ad" | 'a'!='d', mismatch | 1 + min(dp[3][3], dp[2][2]) = 1+0 = 1 |
| 1,2 | "ba" | 'b'!='a', mismatch | 1 + min(dp[2][2], dp[1][1]) = 1+0 = 1 |

`dp[1][3] = 1 + min(1, 1) = 2`, so `dp[0][4] = 2`, matching the expected `2`. Time complexity is O(n^2). Space is O(n^2) (reducible to O(n) with rolling diagonals).

## 7. Gotchas & takeaways

> Gotcha: this problem is MATHEMATICALLY EQUIVALENT to `n - (Longest Palindromic Subsequence length)`, but computing `dp[i][j]` DIRECTLY as the minimum-insertions DP (as shown here) avoids the extra step of computing the LPS length and subtracting — both are correct, and either is acceptable, but mixing them up mid-solution risks an off-by-one error.

- `dp[i][j] = dp[i+1][j-1]` on match (free), `1 + min(...)` on mismatch: the minimize variant of the interval palindrome template — contrast with Longest Palindromic Subsequence, which ADDS `2` on match and takes `max` on mismatch (an optimization problem, not a cost-minimization problem).
- Every insertion made is always exactly `1` unit of "progress," which is why the mismatch case always adds exactly `1`, never more.
- Related problems: Longest Palindromic Subsequence (the equivalent problem via `n - LPS`), Edit Distance (a similar minimize-cost interval DP, but between TWO different strings instead of a string and its own mirror).
