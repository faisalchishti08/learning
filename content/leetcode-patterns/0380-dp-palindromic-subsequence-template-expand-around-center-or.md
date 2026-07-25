---
card: leetcode-patterns
gi: 380
slug: dp-palindromic-subsequence-template-expand-around-center-or
title: "DP: Palindromic Subsequence — template: expand-around-center or interval dp[i][j]"
---

## 1. What it is

This page gives the two reusable templates for palindrome-substring detection: EXPAND-AROUND-CENTER (simpler, O(1) extra space, great for substring-only problems) and INTERVAL DP with a full `dp[i][j]` table (needed when the palindrome information must be REUSED across many queries, or combined with another DP).

## 2. Why & when

Use expand-around-center when you only need to find the longest palindromic SUBSTRING (contiguous) once, since it avoids building a full O(n^2) table. Use the interval `dp[i][j]` table when you need to know, for MANY different ranges, whether each one is a palindrome — for example, inside Palindrome Partitioning II, where the palindrome check is reused repeatedly for different cut points.

## 3. Core concept

**Template A — expand around center.**
1. For each possible CENTER position (there are `2n - 1` of them: `n` single-character centers, `n-1` between-character centers for even-length palindromes), expand outward while the characters on both sides match.
2. Track the longest palindrome found across all centers.

**Template B — interval `dp[i][j]`.**
1. Create `dp[n][n]`, boolean. Base case: every `dp[i][i] = true` (single characters are palindromes).
2. For `len` from `2` to `n`, for `i` from `0` while `i + len - 1 < n`: let `j = i + len - 1`. `dp[i][j] = (s.charAt(i) == s.charAt(j))` AND (`len == 2` OR `dp[i+1][j-1]`).
3. Query any range's palindrome status in O(1) by looking up `dp[i][j]`.

**Why expand-around-center works:** a palindrome is symmetric around its center; growing outward from every possible center and stopping at the first mismatch finds every maximal palindrome in O(n) per center, O(n^2) total, without needing to store a full table.

**Why the interval DP's length-ordering is required:** `dp[i][j]` depends on `dp[i+1][j-1]`, a range strictly INSIDE it — filling by increasing `len` guarantees that inner range was already computed in an earlier iteration of the outer loop.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="expand around center growing outward from a middle position until characters stop matching">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "babad"; center at index 2 ('b')</text>
    <text x="10" y="45">expand: left=1,right=3: s[1]='a', s[3]='a' -- match, keep expanding</text>
    <text x="10" y="65">expand: left=0,right=4: s[0]='b', s[4]='d' -- mismatch, stop</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">longest palindrome centered here: "aba"</text>
  </g>
</svg>

Expansion stops the moment the two sides disagree, giving the maximal palindrome for that center.

## 5. Runnable example

```java
// PalindromicSubsequenceTemplate.java
public class PalindromicSubsequenceTemplate {

    // Template A: expand around center.
    static String longestPalindromeExpand(String s) {
        int start = 0, maxLen = 0;
        for (int center = 0; center < 2 * s.length() - 1; center++) {
            int left = center / 2;
            int right = left + center % 2;
            while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
                left--; right++;
            }
            int len = right - left - 1;
            if (len > maxLen) {
                maxLen = len;
                start = left + 1;
            }
        }
        return s.substring(start, start + maxLen);
    }

    // Template B: interval dp[i][j] table.
    static boolean[][] buildTable(String s) {
        int n = s.length();
        boolean[][] dp = new boolean[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = true;
        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = s.charAt(i) == s.charAt(j) && (len == 2 || dp[i + 1][j - 1]);
            }
        }
        return dp;
    }

    public static void main(String[] args) {
        System.out.println(longestPalindromeExpand("babad"));
        // bab (or aba, both length 3)
        boolean[][] dp = buildTable("babad");
        System.out.println(dp[0][2]);
        // true ("bab")
    }
}
```

**How to run:** `java PalindromicSubsequenceTemplate.java`

## 6. Walkthrough

1. `longestPalindromeExpand` tries every one of the `2*5-1 = 9` centers in `"babad"`, expanding each, and keeps the widest result found (`"bab"`, length `3`).
2. `buildTable` fills a `5x5` boolean table by increasing range length, so `dp[0][2]` (`"bab"`) is computed only after `dp[1][1]` (the inner single character) is already known `true`.
3. Both approaches agree that `"bab"` (or equivalently `"aba"`) is a longest palindromic substring of length `3`.
4. Tracing the center-expansion approach shows it does no wasted table storage — it only ever tracks the current best `start`/`maxLen`, which is why it needs O(1) extra space beyond the input.
5. This template applies directly to Longest Palindromic Substring (Template A is sufficient) and Palindrome Partitioning II (Template B is required, since the palindrome check is reused across many different ranges).

## 7. Gotchas & takeaways

> Gotcha: forgetting the TWO types of centers (single-character, for odd-length palindromes, and between-character, for even-length palindromes) in Template A silently misses every even-length palindrome — the `center / 2` and `left + center % 2` trick handles both in one loop.

- Expand-around-center: O(n^2) time, O(1) extra space; best for a ONE-TIME longest-substring query.
- Interval `dp[i][j]`: O(n^2) time AND space; best when the palindrome status of MANY ranges must be looked up repeatedly.
- The interval DP's `len == 2` special case avoids reading `dp[i+1][j-1]` when that would be an EMPTY range (i.e., `i+1 > j-1`), which is trivially considered a palindrome by convention.
