---
card: leetcode-patterns
gi: 5
slug: valid-palindrome
title: Valid Palindrome
---

## 1. What it is

Given a string `s`, return `true` if it reads the same forward and backward after two transforms: convert all letters to lowercase, and remove every character that is not a letter or a digit. Example: `s = "A man, a plan, a canal: Panama"` → after cleaning, `"amanaplanacanalpanama"`, which is a palindrome, so the answer is `true`.

## 2. Why & when

The naive approach builds a cleaned copy of the string, then compares it to its reverse — that costs extra space for the reversed copy. The two-pointers pattern (opposite-ends) checks the palindrome property directly, in place, without building any extra string: compare the outermost characters, skip non-alphanumeric ones, and move inward.

## 3. Core concept

**Key idea:** a string is a palindrome exactly when its first character equals its last, its second equals its second-to-last, and so on — a direct match for opposite-ends pointers.

**Steps:**
1. Set `left = 0` and `right = s.length() - 1`.
2. While `left < right`:
   - If `s.charAt(left)` is not a letter or digit, skip it: `left++`, continue.
   - If `s.charAt(right)` is not a letter or digit, skip it: `right--`, continue.
   - Otherwise compare the lowercase forms of both characters. If they differ, the string is not a palindrome — return `false`. If they match, move both pointers inward: `left++`, `right--`.
3. If the loop finishes without a mismatch, the string is a palindrome — return `true`.

**Why it is correct:** skipping non-alphanumeric characters before comparing is equivalent to first building the cleaned string and then comparing ends inward — but it does so without allocating that cleaned string. Each character is visited at most once by each pointer, so the check is still linear.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Valid palindrome pointers skipping punctuation">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="30" fill="#e6edf3">"A man, a plan, a canal: Panama"</text>
    <text x="20" y="60" fill="#79c0ff">left -&gt;  A</text>
    <text x="500" y="60" fill="#f0883e">&lt;- right  a  (from "Panama")</text>
    <text x="20" y="90" fill="#8b949e">skip ',' ':' ' ' on either side; compare lowercase letters only</text>
    <text x="20" y="120" fill="#8b949e">'a' == 'a' -&gt; keep moving inward until pointers meet</text>
  </g>
</svg>

Pointers skip punctuation and spaces, then compare lowercase letters from both ends inward.

## 5. Runnable example

```java
// ValidPalindrome.java
public class ValidPalindrome {

    // Level 1 -- Brute force: build a cleaned string, then compare it to
    // its reverse. O(n) time but O(n) extra space for two new strings.
    static boolean bruteForce(String s) {
        StringBuilder cleaned = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (Character.isLetterOrDigit(c)) {
                cleaned.append(Character.toLowerCase(c));
            }
        }
        String forward = cleaned.toString();
        String backward = cleaned.reverse().toString();
        return forward.equals(backward);
    }

    // KEY INSIGHT: you never need the cleaned string as a whole -- you only
    // need to compare matching positions from both ends, so two pointers
    // can skip junk characters and compare in place, with no allocation.

    // Level 2 -- Optimal: two pointers, O(n) time, O(1) space.
    public static boolean isPalindrome(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right) {
            char cl = s.charAt(left);
            char cr = s.charAt(right);
            if (!Character.isLetterOrDigit(cl)) { left++; continue; }
            if (!Character.isLetterOrDigit(cr)) { right--; continue; }
            if (Character.toLowerCase(cl) != Character.toLowerCase(cr)) {
                return false;
            }
            left++;
            right--;
        }
        return true;
    }

    // Level 3 -- Hardened: empty string and single-character strings are
    // palindromes by definition; the loop condition (left < right) already
    // handles both without a special case.
    static boolean hardened(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        return isPalindrome(s);
    }

    public static void main(String[] args) {
        String s1 = "A man, a plan, a canal: Panama";
        String s2 = "race a car";

        System.out.println("brute force s1: " + bruteForce(s1));
        System.out.println("optimal s1:     " + isPalindrome(s1));
        System.out.println("optimal s2:     " + isPalindrome(s2));
        System.out.println("empty string:   " + hardened(""));
    }
}
```

How to run: save as `ValidPalindrome.java`, then run `java ValidPalindrome.java`.

## 6. Walkthrough

Dry run of `isPalindrome("race a car")` (spaces are skipped, not letters/digits):

| step | left char | right char | action |
|---|---|---|---|
| 1 | 'r' | 'r' | match, left++, right-- |
| 2 | 'a' | 'a' | match, left++, right-- |
| 3 | 'c' | 'c' | match, left++, right-- |
| 4 | 'e' | ' ' (skip) | right-- (space is not alphanumeric) |
| 5 | 'e' | 'a' | mismatch -> return false |

`race a car` cleans to `raceacar`, which is not a palindrome, so the method correctly returns `false` as soon as it finds the first mismatch — it does not need to scan the rest of the string. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: comparing `s.charAt(left) != s.charAt(right)` without lowercasing both sides fails on inputs with mixed case, like `"Aa"`, which should count as a palindrome once case is ignored.

- Skip non-alphanumeric characters on *each* pointer independently — do not assume punctuation lines up symmetrically.
- The empty string and single-character strings are trivially palindromes; the `left < right` loop condition handles them for free.
- Related problems: Valid Palindrome II (allows deleting one character), Palindrome Linked List, Longest Palindromic Substring (a different pattern — expand around center).
