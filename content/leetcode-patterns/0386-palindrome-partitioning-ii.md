---
card: leetcode-patterns
gi: 386
slug: palindrome-partitioning-ii
title: Palindrome Partitioning II
---

## 1. What it is

Given a string `s`, partition it into pieces so that EVERY piece is a palindrome, using the MINIMUM number of cuts. Return that minimum cut count. Example: `s = "aab"` → `1` (cut into `"aa"` and `"b"`, both palindromes, using 1 cut).

## 2. Why & when

This problem COMBINES two DP layers: the interval `dp[i][j]` palindrome-detection table (is THIS range a palindrome), and a 1D `cuts[i]` DP over cut positions (minimum cuts for the prefix ending at position `i`). Use this shape whenever a problem partitions a string into palindromic pieces and asks for a MINIMUM (or count) over the partitioning, since the palindrome table becomes a fast O(1) sub-routine feeding a separate 1D optimization.

## 3. Core concept

**Key idea:** first build the full interval palindrome table `isPal[i][j]`. Then build `cuts[i]` = the minimum number of cuts needed to partition the prefix `s[0..i)` into palindromic pieces, trying every possible LAST piece.

**Steps:**
1. Build `isPal[i][j]` using the standard interval-DP template (increasing range length).
2. `cuts[0] = -1` (an empty prefix needs zero pieces, which is conventionally represented as `-1` cuts so the `+1` in the next step works out to `0` cuts for a single whole-string palindrome).
3. For `i` from `1` to `n`, for `j` from `0` to `i - 1`: if `isPal[j][i-1]` is `true` (the piece `s[j..i-1]` is a palindrome), `cuts[i] = min(cuts[i], cuts[j] + 1)`.
4. Return `cuts[n]`.

**Why it is correct:** the LAST palindromic piece in an optimal partition of `s[0..i)` starts at SOME position `j` and covers `s[j..i-1]`. Trying every possible `j` where that final piece is a valid palindrome, and combining with the best cut count for the prefix BEFORE that piece (`cuts[j]`), covers every possible partition — taking the minimum over all valid `j` finds the true optimum.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="cuts array built by trying every possible last palindromic piece ending at position i using the precomputed palindrome table">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s="aab"; isPal table confirms "aa" (0..1) and "b" (2..2) are palindromes</text>
    <text x="10" y="45">cuts[0]=-1</text>
    <text x="10" y="65">cuts[2]: isPal[0][1]="aa" true -&gt; cuts[2]=min(_, cuts[0]+1)=0</text>
    <text x="10" y="85">cuts[3]: isPal[2][2]="b" true -&gt; cuts[3]=min(_, cuts[2]+1)=1</text>
    <rect x="10" y="105" width="240" height="24" fill="#3fb950"/><text x="130" y="122" fill="#0d1117" text-anchor="middle" font-size="10">cuts[3] = 1</text>
  </g>
</svg>

The palindrome table answers "is this piece valid" in O(1); the cuts array combines valid pieces optimally.

## 5. Runnable example

```java
// PalindromePartitioningII.java
public class PalindromePartitioningII {

    // KEY INSIGHT: precompute the interval palindrome table once,
    // then run a separate 1D DP over cut positions, using the table
    // as an O(1) "is this piece a palindrome" check.

    static int minCut(String s) {
        int n = s.length();
        boolean[][] isPal = new boolean[n][n];
        for (int i = 0; i < n; i++) isPal[i][i] = true;
        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                isPal[i][j] = s.charAt(i) == s.charAt(j) && (len == 2 || isPal[i + 1][j - 1]);
            }
        }

        int[] cuts = new int[n + 1];
        cuts[0] = -1;
        for (int i = 1; i <= n; i++) {
            cuts[i] = Integer.MAX_VALUE;
            for (int j = 0; j < i; j++) {
                if (isPal[j][i - 1]) {
                    cuts[i] = Math.min(cuts[i], cuts[j] + 1);
                }
            }
        }
        return cuts[n];
    }

    public static void main(String[] args) {
        System.out.println(minCut("aab"));
        // 1
        System.out.println(minCut("a"));
        // 0
    }
}
```

**How to run:** `java PalindromePartitioningII.java`

## 6. Walkthrough

Trace `minCut("aab")`, `n=3`, using `isPal` (from the table: `[0][1]="aa"` true, `[2][2]="b"` true, `[0][2]="aab"` false):

| i | best j | cuts[i] |
|---|---|---|
| 1 | j=0, "a" | cuts[0]+1 = 0 |
| 2 | j=0, "aa" | cuts[0]+1 = 0 |
| 3 | j=2, "b" (needs cuts[2]) | cuts[2]+1 = 1 |

`cuts[3] = 1`, matching the expected `1` cut. Time complexity is O(n^2) for the palindrome table, plus O(n^2) for the cuts DP (each `i` tries up to `n` values of `j`) — O(n^2) total. Space is O(n^2) for the table, O(n) for `cuts`.

## 7. Gotchas & takeaways

> Gotcha: setting `cuts[0] = 0` instead of `-1` is a common off-by-one mistake — since `cuts[i]` represents CUTS (not pieces), and a single whole-string palindrome needs `0` cuts, the base case must be `-1` so that `cuts[j] + 1` correctly evaluates to `0` when the very first piece spans the entire prefix.

- Precomputing the full palindrome table FIRST, then treating it as a fast lookup inside a separate DP, is a general technique whenever a palindrome-partitioning problem needs to check MANY different piece boundaries.
- This problem's 1D `cuts` DP has the same shape as Word Break's `dp[i]` — "try every split point `j`, combine with a precomputed check on `s[j..i)`" — but MINIMIZING count instead of checking reachability.
- Related problems: Palindrome Partitioning (the backtracking version, returning EVERY valid partition instead of just the minimum cut count), Word Break (the same 1D split-point DP shape, checking a dictionary instead of the palindrome property).
