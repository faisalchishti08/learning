---
card: leetcode-patterns
gi: 385
slug: palindromic-substrings
title: Palindromic Substrings
---

## 1. What it is

Given a string `s`, return the TOTAL NUMBER of palindromic substrings it contains, counting different OCCURRENCES at different positions separately (so `"aaa"` has `6`: `"a","a","a","aa","aa","aaa"`). Example: `s = "abc"` → `3` (each single character). Example: `s = "aaa"` → `6`.

## 2. Why & when

This is the COUNTING variant of palindrome-substring detection: instead of finding just the LONGEST one, tally EVERY palindromic substring found. Use this shape whenever a problem asks "how many" palindromic substrings exist, rather than asking for just the longest or a boolean check.

## 3. Core concept

**Key idea:** every palindrome has exactly one center; counting how many times expansion SUCCEEDS (produces a valid, in-bounds, matching palindrome) across all centers gives the total count, since each successful expansion step corresponds to exactly one distinct palindromic substring.

**Steps:**
1. Initialize `count = 0`.
2. For each of the `2n - 1` centers (`center` from `0` to `2n-2`, using the same `left = center/2`, `right = left + center%2` formula as Longest Palindromic Substring): expand outward while `left >= 0`, `right < n`, and `s.charAt(left) == s.charAt(right)`.
3. Each successful expansion step (before failing) represents one valid palindrome — increment `count` once per successful step, then continue expanding.
4. Return `count`.

**Why it is correct:** at a given center, the expansion visits palindromes of increasing length, one at a time (length `1`, then `3`, then `5`, ... for an odd center; or length `0`, `2`, `4`, ... for an even center) — EVERY one of these intermediate palindromes is itself a valid, distinct palindromic substring occurrence, so counting each successful expansion step (not just the final, longest one) tallies them all.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="expansion from the center of aaa counting three successful steps corresponding to palindromes of length one three and five">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "aaa"; center at index 1 (single char)</text>
    <text x="10" y="45">step 1: left=1,right=1 "a" -- count 1</text>
    <text x="10" y="65">step 2: left=0,right=2 "aaa" -- count 1 more</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">each successful expansion = one palindrome counted</text>
  </g>
</svg>

Every step of a successful expansion is itself a distinct palindromic substring, not just the final longest one.

## 5. Runnable example

```java
// PalindromicSubstrings.java
public class PalindromicSubstrings {

    // KEY INSIGHT: count EVERY successful expansion step at every
    // center, not just the final longest one -- each step is a
    // distinct palindromic substring occurrence.

    static int countSubstrings(String s) {
        int n = s.length();
        int count = 0;

        for (int center = 0; center < 2 * n - 1; center++) {
            int left = center / 2;
            int right = left + center % 2;
            while (left >= 0 && right < n && s.charAt(left) == s.charAt(right)) {
                count++;
                left--; right++;
            }
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(countSubstrings("abc"));
        // 3
        System.out.println(countSubstrings("aaa"));
        // 6
    }
}
```

**How to run:** `java PalindromicSubstrings.java`

## 6. Walkthrough

Trace `countSubstrings("aaa")`, `n=3`, `5` centers:

| center | expansions (each counted) | subtotal |
|---|---|---|
| 0 (char 'a', idx0) | "a" | 1 |
| 1 (between 0,1) | "aa" | 1 |
| 2 (char 'a', idx1) | "a", "aaa" | 2 |
| 3 (between 1,2) | "aa" | 1 |
| 4 (char 'a', idx2) | "a" | 1 |

Total: `1+1+2+1+1 = 6`, matching the expected answer. Time complexity is O(n^2) (each of the `2n-1` centers can expand up to O(n) times). Space is O(1) extra.

## 7. Gotchas & takeaways

> Gotcha: counting only the FINAL, longest palindrome found at each center (instead of every intermediate successful step) undercounts badly — every step of a successful expansion is its own distinct palindrome, and all of them must be tallied.

- This is the exact same expand-around-center mechanics as Longest Palindromic Substring, with the accumulation changed from "track the maximum" to "count every success."
- Repeated characters (like `"aaa"`) produce MULTIPLE overlapping palindromes centered at different positions — the total count grows quadratically with the length of a run of identical characters.
- Related problems: Longest Palindromic Substring (tracks the max instead of counting), Count Different Palindromic Subsequences (counts DISTINCT subsequences, not substring occurrences — a much harder counting variant, since it must avoid double-counting identical subsequences formed different ways).
