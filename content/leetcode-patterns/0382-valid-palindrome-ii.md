---
card: leetcode-patterns
gi: 382
slug: valid-palindrome-ii
title: Valid Palindrome II
---

## 1. What it is

Given a string `s`, return `true` if `s` can become a palindrome by removing AT MOST ONE character. Example: `s = "abca"` → `true` (remove `'b'` or `'c'` to get `"aca"` or `"aba"`).

## 2. Why & when

This is the simplest member of the palindrome family: a two-pointer check, with ONE allowed "skip" when a mismatch is found. Use this shape whenever a problem asks whether a string is "almost" a palindrome, allowing a small, fixed number of corrections.

## 3. Core concept

**Key idea:** walk two pointers inward from both ends. As long as characters match, keep moving inward. The FIRST time a mismatch occurs, there are only two possible fixes: skip the LEFT character, or skip the RIGHT character — check whether the remaining range is a palindrome under EITHER choice.

**Steps:**
1. Set `left = 0`, `right = s.length() - 1`.
2. While `left < right` and `s.charAt(left) == s.charAt(right)`: advance `left++`, `right--`.
3. If the loop finishes with `left >= right`, the whole string is already a palindrome — return `true`.
4. Otherwise, a mismatch occurred at `(left, right)`. Return `true` if EITHER `s.substring(left+1, right+1)` is a plain palindrome (skipping the left character) OR `s.substring(left, right)` is a plain palindrome (skipping the right character).

**Why it is correct:** the first mismatch found by the two-pointer walk is the FIRST point where a deletion becomes unavoidable — everything before it already matches. Since only one deletion is allowed, it must be used at this exact mismatch, on EITHER the left or right character; checking both remaining ranges with a plain (no-skip-allowed) palindrome check covers both possibilities.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two pointers converging until a mismatch, then branching into two checks skipping either the left or right character">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "abca"; left=0('a'), right=3('a') match, move inward</text>
    <text x="10" y="45">left=1('b'), right=2('c') -- MISMATCH</text>
    <text x="10" y="65">check skip left: s[2..2]="c" (palindrome) OR skip right: s[1..1]="b" (palindrome)</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">either check succeeds -&gt; true</text>
  </g>
</svg>

At the first mismatch, exactly one character must be dropped from either side — both options are tried.

## 5. Runnable example

```java
// ValidPalindromeII.java
public class ValidPalindromeII {

    // KEY INSIGHT: the first mismatch found by two pointers is where
    // the single allowed deletion must happen -- try skipping either
    // side and check the rest with a plain palindrome check.

    static boolean validPalindrome(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right && s.charAt(left) == s.charAt(right)) {
            left++; right--;
        }
        if (left >= right) return true;

        return isPalindrome(s, left + 1, right) || isPalindrome(s, left, right - 1);
    }

    static boolean isPalindrome(String s, int left, int right) {
        while (left < right) {
            if (s.charAt(left) != s.charAt(right)) return false;
            left++; right--;
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(validPalindrome("abca"));
        // true
        System.out.println(validPalindrome("abc"));
        // false
    }
}
```

**How to run:** `java ValidPalindromeII.java`

## 6. Walkthrough

Trace `validPalindrome("abca")`:

| step | left | right | chars | result |
|---|---|---|---|---|
| 1 | 0 | 3 | 'a','a' | match, move inward |
| 2 | 1 | 2 | 'b','c' | mismatch, branch |
| 3a | skip left | isPalindrome(s,2,2) | single char | true |

Since branch 3a already returns `true`, `validPalindrome` returns `true`. Time complexity is O(n): the outer walk is O(n), and each branch's plain palindrome check is also O(n), but they run at most once each. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: calling the general-purpose skip-checking function RECURSIVELY (allowing more than one skip inside `isPalindrome`) would silently allow MORE than one deletion — `isPalindrome` here must be a PLAIN palindrome check with zero skips allowed, since the one allowed deletion is already used at the branch point.

- Two pointers converging, with EXACTLY one branch point on first mismatch: the simplest palindrome-family shape, not requiring a full DP table.
- The two candidate checks (`skip left`, `skip right`) are independent and both cheap (O(n) each); no memoization is needed since there is only ever one mismatch point to branch from.
- Related problems: Longest Palindromic Substring (a full DP or expand-around-center problem, not a simple two-pointer check), Palindrome Partitioning II (uses a full palindrome table, since it needs to check MANY ranges, not just one).
