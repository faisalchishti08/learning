---
card: data-structures
gi: 40
slug: palindrome-checking
title: Palindrome checking
---

## 1. What it is

A **palindrome** is a string that reads the same forwards and backwards, like `"level"` or `"racecar"`. Checking whether a string is a palindrome means comparing characters from both ends moving inward, and confirming every matching pair is equal.

## 2. Why & when

Palindrome checking is a small, self-contained problem that teaches the two-pointer technique in its clearest form — no sorting, no auxiliary structure needed, just two indices converging. Variants (ignoring case and punctuation, checking the longest palindromic sub-string) are common building blocks for text-processing and interview-style problems.

## 3. Core concept

**Two-pointer comparison from both ends.** Start `left` at index 0 and `right` at the last index. Compare `s.charAt(left)` and `s.charAt(right)`. If they differ, the string is not a palindrome — stop immediately. If they match, move `left` forward and `right` backward, and repeat until they meet or cross.

**Why this is O(n) with O(1) extra space.** Each comparison eliminates one pair of positions permanently — the pointers only ever move toward each other, never backward, so the total number of comparisons is at most `n/2`. No extra array or reversed copy is needed, unlike an approach that builds a reversed string and compares it to the original (which costs O(n) extra space).

**Real-world palindrome checks usually need normalization first.** `"A man, a plan, a canal: Panama"` is a palindrome only after removing punctuation/spaces and ignoring case. Normalize first (build a cleaned version, or skip non-alphanumeric characters and compare case-insensitively during the scan), then apply the same two-pointer logic.

**Expand-around-center finds the longest palindromic sub-string.** Instead of checking one fixed string, treat every position (and every position-pair, for even-length palindromes) as a potential center, and expand outward while both sides keep matching — tracking the longest expansion seen.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointers starting at opposite ends of racecar and moving inward, each pair matching, converging at the center r">
  <g font-family="sans-serif" font-size="11">
    <rect x="60" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="80" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">r</text>
    <rect x="100" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="120" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">a</text>
    <rect x="140" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="160" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">c</text>
    <rect x="180" y="30" width="40" height="28" fill="#161b22" stroke="#79c0ff"/><text x="200" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">e</text>
    <rect x="220" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="240" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">c</text>
    <rect x="260" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="280" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">a</text>
    <rect x="300" y="30" width="40" height="28" fill="#0d1117" stroke="#3fb950"/><text x="320" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">r</text>
    <text x="320" y="90" fill="#79c0ff" text-anchor="middle">left and right match at every step -- palindrome confirmed once they meet at "e"</text>
  </g>
</svg>

Comparing matching pairs from both ends of `"racecar"`, moving inward, confirms the palindrome once the two pointers meet at the center.

## 5. Runnable example

```java
// PalindromeChecking.java
public class PalindromeChecking {

    // Basic: classic two-pointer palindrome check.
    static boolean isPalindrome(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right) {
            if (s.charAt(left) != s.charAt(right)) return false;
            left++;
            right--;
        }
        return true;
    }

    static void basicLevel() {
        System.out.println("basic: \"racecar\" -> " + isPalindrome("racecar"));
        System.out.println("basic: \"hello\" -> " + isPalindrome("hello"));
    }

    // Intermediate: normalize first -- ignore case and skip non-alphanumeric characters.
    static boolean isPalindromeNormalized(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right) {
            while (left < right && !Character.isLetterOrDigit(s.charAt(left))) left++;
            while (left < right && !Character.isLetterOrDigit(s.charAt(right))) right--;
            if (Character.toLowerCase(s.charAt(left)) != Character.toLowerCase(s.charAt(right))) return false;
            left++;
            right--;
        }
        return true;
    }

    static void intermediateLevel() {
        String phrase = "A man, a plan, a canal: Panama";
        System.out.println("intermediate: \"" + phrase + "\" -> " + isPalindromeNormalized(phrase));
    }

    // Advanced: expand-around-center to find the longest palindromic sub-string.
    static String longestPalindrome(String s) {
        String best = "";
        for (int center = 0; center < s.length(); center++) {
            String odd = expandAroundCenter(s, center, center);         // odd-length, single center
            String even = expandAroundCenter(s, center, center + 1);    // even-length, center pair
            if (odd.length() > best.length()) best = odd;
            if (even.length() > best.length()) best = even;
        }
        return best;
    }

    static String expandAroundCenter(String s, int left, int right) {
        while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
            left--;
            right++;
        }
        return s.substring(left + 1, right); // left/right overshot by one on the last failed check
    }

    static void advancedLevel() {
        String s = "babad";
        System.out.println("advanced: longest palindromic sub-string of \"" + s + "\" -> " + longestPalindrome(s));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PalindromeChecking.java`, then run `java PalindromeChecking.java`.

## 6. Walkthrough

1. `basicLevel()` checks `"racecar"`: `left=0`(`r`) vs `right=6`(`r`) match, then `left=1`(`a`) vs `right=5`(`a`) match, then `left=2`(`c`) vs `right=4`(`c`) match, then `left=3` meets `right=3` — loop ends, returns `true`. `"hello"` fails at the very first comparison (`h` vs `o`), returning `false` immediately.
2. `intermediateLevel()`'s `isPalindromeNormalized` skips over punctuation and spaces with the two inner `while` loops before comparing, and lower-cases both characters before comparing — this lets `"A man, a plan, a canal: Panama"` correctly evaluate to `true` despite its mixed case and punctuation.
3. `advancedLevel()`'s `longestPalindrome` tries every index as a potential center, checking both an odd-length palindrome (single character center) and an even-length one (a center pair) at each position.
4. `expandAroundCenter(s, 1, 1)` on `"babad"` (center at index 1, `'a'`) expands to `left=0, right=2` (`'b'`==`'b'`), then tries `left=-1` and stops — returning `s.substring(0, 3)` = `"bab"`. A later center around index 2 similarly finds `"aba"`. Both have length 3; the first one found (`"bab"`) is kept as `best`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check both odd-length *and* even-length centers in `longestPalindrome` misses half of all possible palindromes — an even-length palindrome like `"abba"` has no single center character, only a center *pair*, so `expandAroundCenter(s, center, center + 1)` is required in addition to `expandAroundCenter(s, center, center)`.

- Two-pointer comparison from both ends checks a palindrome in O(n) time and O(1) extra space.
- Real-world text needs normalization (skip punctuation, ignore case) before the same two-pointer logic applies correctly.
- Expand-around-center checks every possible palindrome center (both single-character and paired) to find the longest palindromic sub-string in O(n²) overall.
- Related concepts: [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md), [Anagram & frequency-count problems](0039-anagram-frequency-count-problems.md).
