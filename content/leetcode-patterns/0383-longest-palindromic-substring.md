---
card: leetcode-patterns
gi: 383
slug: longest-palindromic-substring
title: Longest Palindromic Substring
---

## 1. What it is

Given a string `s`, return the LONGEST CONTIGUOUS substring of `s` that is a palindrome. Example: `s = "babad"` → `"bab"` (`"aba"` is also a valid answer, both length 3).

## 2. Why & when

This is the canonical palindrome-detection problem, solvable with either the expand-around-center technique or the full interval DP table. Use this shape whenever a problem asks for the single longest (or just ANY) palindromic substring, without needing to query many different ranges afterward.

## 3. Core concept

**Key idea:** every palindrome has a CENTER (a single character for odd length, a gap between two characters for even length). Expanding outward from every possible center, stopping at the first mismatch, finds the maximal palindrome for that center — and trying all `2n - 1` centers finds the overall longest one.

**Steps:**
1. For each `center` from `0` to `2n - 2`: compute `left = center / 2`, `right = left + center % 2` (this single formula produces both single-character and between-character centers).
2. While `left >= 0`, `right < n`, and `s.charAt(left) == s.charAt(right)`: expand, `left--`, `right++`.
3. The palindrome found has length `right - left - 1`, starting at `left + 1`. Track the longest one seen across all centers.
4. Return the substring corresponding to the longest palindrome found.

**Why it is correct:** every palindrome is symmetric around exactly one center. Trying EVERY possible center and expanding as far as possible from each one is guaranteed to discover every MAXIMAL palindrome in the string — the longest one overall must be among them, since it too has a well-defined center.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="expanding from each of the 9 possible centers of a 5 character string, keeping track of the widest palindrome found">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "babad", n = 5, centers 0..8</text>
    <text x="10" y="45">center=2 (single char 'b'): expands to "bab", length 3</text>
    <text x="10" y="65">center=4 (single char 'a'): expands to "aba", length 3</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">both length 3; either is a valid answer</text>
  </g>
</svg>

Every center is tried once; the widest successful expansion determines the final answer.

## 5. Runnable example

```java
// LongestPalindromicSubstring.java
public class LongestPalindromicSubstring {

    // KEY INSIGHT: every palindrome has one center; trying all 2n-1
    // centers and expanding outward finds the longest one in O(n^2).

    static String longestPalindrome(String s) {
        if (s.isEmpty()) return "";
        int start = 0, maxLen = 1;

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

    public static void main(String[] args) {
        System.out.println(longestPalindrome("babad"));
        // bab
        System.out.println(longestPalindrome("cbbd"));
        // bb
    }
}
```

**How to run:** `java LongestPalindromicSubstring.java`

## 6. Walkthrough

Trace key centers for `longestPalindrome("babad")`:

| center | left,right start | expands to | length |
|---|---|---|---|
| 2 (char 'b') | 2,2 | left=0,right=4 stop (mismatch 'b' vs 'd') | 3 ("bab") |
| 4 (char 'a') | 4,4 | left=2,right=5 (out of bounds) stop | 3 ("aba") |
| 3 (between 'a','d') | 3,4 | mismatch immediately | 0 |

The longest found is length `3` (`"bab"`, the first one found, since later ties do not overwrite it). Time complexity is O(n^2) (each of the `2n-1` centers can expand up to O(n) times). Space is O(1) extra.

## 7. Gotchas & takeaways

> Gotcha: using `len > maxLen` (strictly greater) instead of `>=` means the FIRST longest palindrome found is kept on ties — this matches the problem's "return any one of them" requirement, but if a SPECIFIC tie-break is required, adjust the comparison accordingly.

- The `center / 2`, `left + center % 2` formula is the compact way to generate BOTH odd-length centers (`center` even) and even-length centers (`center` odd) in a single loop.
- This problem only needs Template A (expand-around-center) from the pattern's template page — the full interval DP table (Template B) is unnecessary overhead here, since only one query (the overall longest) is needed.
- Related problems: Palindromic Substrings (counts ALL palindromic substrings, using the same expansion technique, tallying instead of tracking a max), Longest Palindromic Subsequence (allows GAPS, requiring the full interval DP instead of expand-around-center).
