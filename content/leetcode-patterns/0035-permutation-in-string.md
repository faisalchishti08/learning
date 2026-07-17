---
card: leetcode-patterns
gi: 35
slug: permutation-in-string
title: Permutation in String
---

## 1. What it is

Given two strings `s1` and `s2`, return `true` if `s2` contains a contiguous substring that is a permutation (any reordering) of `s1`. Example: `s1 = "ab"`, `s2 = "eidbaooo"` → `true`, because `"ba"` (a permutation of `"ab"`) appears in `s2`.

## 2. Why & when

A permutation of `s1` has exactly the same character counts as `s1`, just reordered — so this reduces to "does any fixed-size window of `s2` (size `s1.length()`) have the same character-count signature as `s1`?" That is a fixed-size sliding window, comparing frequency maps.

## 3. Core concept

**Key idea:** a window of length `s1.length()` is a permutation of `s1` exactly when its character counts match `s1`'s character counts exactly — no more, no less, for every character.

**Steps:**
1. If `s2.length() < s1.length()`, return `false` immediately.
2. Build a frequency array `need` for `s1` (26 slots for lowercase letters).
3. Build a frequency array `window` for the first `s1.length()` characters of `s2`.
4. If `window` equals `need`, return `true`.
5. Slide the window across the rest of `s2`: for each new position, increment the count for the entering character, decrement the count for the character leaving the window (the one `s1.length()` positions behind), and compare `window` to `need` again after each slide.
6. If no window ever matches, return `false`.

**Why it is correct:** because the window size is fixed at `s1.length()`, comparing two 26-slot frequency arrays for exact equality after every slide is a direct, complete test of "is this window a permutation of `s1`" — a permutation by definition uses every character the same number of times as the original, in any order, which is exactly what matching frequency counts captures.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Permutation in string fixed window comparing frequency counts">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s1 = "ab" (need: a=1,b=1)   s2 = "eidbaooo"</text>
    <rect x="20" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="50" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="80" y="40" width="30" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="110" y="40" width="30" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="35" y="60" fill="#e6edf3" text-anchor="middle">e</text>
    <text x="65" y="60" fill="#e6edf3" text-anchor="middle">i</text>
    <text x="95" y="60" fill="#e6edf3" text-anchor="middle">d</text>
    <text x="125" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="20" y="95" fill="#8b949e">window "db": counts d=1,b=1 -- does not match need (a=1,b=1)</text>
    <text x="20" y="118" fill="#8b949e">slide one more: window "ba": counts a=1,b=1 -- matches! return true</text>
  </g>
</svg>

Each fixed-size window's exact character-count signature is compared against `s1`'s signature.

## 5. Runnable example

```java
// PermutationInString.java
import java.util.Arrays;

public class PermutationInString {

    // Level 1 -- Brute force: for each window position, rebuild the
    // frequency array from scratch and compare. O(n * 26) time -- correct,
    // but redoes counting work that could be updated incrementally.
    static boolean bruteForce(String s1, String s2) {
        int n = s1.length();
        if (s2.length() < n) return false;
        int[] need = new int[26];
        for (char c : s1.toCharArray()) need[c - 'a']++;

        for (int i = 0; i + n <= s2.length(); i++) {
            int[] window = new int[26];
            for (int j = i; j < i + n; j++) window[s2.charAt(j) - 'a']++;
            if (Arrays.equals(need, window)) return true;
        }
        return false;
    }

    // KEY INSIGHT: since the window size is fixed, sliding it by one only
    // changes two characters' counts (one enters, one exits) -- updating
    // incrementally avoids rebuilding the frequency array every time.

    // Level 2 -- Optimal: fixed-size sliding window with incremental
    // counts. O(n) time, O(1) space (26-slot arrays).
    public static boolean checkInclusion(String s1, String s2) {
        int n = s1.length();
        if (s2.length() < n) return false;

        int[] need = new int[26];
        int[] window = new int[26];
        for (int i = 0; i < n; i++) {
            need[s1.charAt(i) - 'a']++;
            window[s2.charAt(i) - 'a']++;
        }
        if (Arrays.equals(need, window)) return true;

        for (int i = n; i < s2.length(); i++) {
            window[s2.charAt(i) - 'a']++;
            window[s2.charAt(i - n) - 'a']--;
            if (Arrays.equals(need, window)) return true;
        }
        return false;
    }

    // Level 3 -- Hardened: s1 longer than s2 returns false immediately,
    // avoiding an out-of-bounds window construction.
    static boolean hardened(String s1, String s2) {
        if (s1 == null || s2 == null) throw new IllegalArgumentException("inputs must not be null");
        return checkInclusion(s1, s2);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("ab", "eidbaooo"));
        System.out.println("optimal:     " + checkInclusion("ab", "eidbaooo"));
        System.out.println("s1 too long: " + hardened("abcde", "ab"));
    }
}
```

How to run: save as `PermutationInString.java`, then run `java PermutationInString.java`.

## 6. Walkthrough

Dry run of `checkInclusion("ab", "eidbaooo")`:

| step | window chars | window counts | matches need (a=1,b=1)? |
|---|---|---|---|
| init | "ei" | e=1,i=1 | no |
| i=2 | "id" (drop e, add d) | i=1,d=1 | no |
| i=3 | "db" (drop i, add b) | d=1,b=1 | no |
| i=4 | "ba" (drop d, add a) | b=1,a=1 | yes! |

Return `true`. Time complexity: O(n), each window slide is O(1) amortized plus an O(26) array comparison. Space complexity: O(1), fixed-size arrays.

## 7. Gotchas & takeaways

> Gotcha: comparing frequency arrays with `==` instead of `Arrays.equals` compares array references, not contents, and always returns `false` — a classic Java pitfall when working with arrays as value-like data.

- Comparing two fixed-size frequency arrays for equality is the reusable trick for "is this window an anagram/permutation of a target."
- Related problems: Find All Anagrams in a String (same idea, but collects every matching start index instead of stopping at the first), Minimum Window Substring, Group Anagrams.
