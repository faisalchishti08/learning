---
card: leetcode-patterns
gi: 36
slug: find-all-anagrams-in-a-string
title: Find All Anagrams in a String
---

## 1. What it is

Given two strings `s` and `p`, return the start indices of all substrings of `s` that are anagrams of `p`. Example: `s = "cbaebabacd"`, `p = "abc"` → `[0, 6]`, since `s[0..2] = "cba"` and `s[6..8] = "bac"` are both anagrams of `"abc"`.

## 2. Why & when

This is Permutation in String, run to completion instead of stopping at the first match: same fixed-size sliding window comparing frequency counts, but collecting every matching start index instead of returning as soon as one is found.

## 3. Core concept

**Key idea:** identical to Permutation in String — a window of length `p.length()` is an anagram of `p` exactly when its character counts match `p`'s counts exactly. The only change is recording the index instead of short-circuiting.

**Steps:**
1. If `s.length() < p.length()`, return an empty list.
2. Build a frequency array `need` for `p`.
3. Build a frequency array `window` for the first `p.length()` characters of `s`.
4. If `window` matches `need`, record index `0`.
5. Slide the window across the rest of `s`: increment the entering character's count, decrement the exiting character's count, and check for a match after each slide, recording the start index whenever it matches.
6. Return the list of recorded indices.

**Why it is correct:** the same reasoning as Permutation in String applies at every window position — an exact frequency match is both necessary and sufficient for the window to be an anagram of `p`. Checking every window position (not stopping early) is what produces the complete list of matches, still in O(n) time overall since each slide is O(1) amortized (the frequency comparison itself is O(26), a constant).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Find all anagrams collecting every matching window start">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "cbaebabacd", p = "abc" (need: a=1,b=1,c=1)</text>
    <text x="20" y="55" fill="#79c0ff">index 0: "cba" -&gt; counts match -&gt; record 0</text>
    <text x="20" y="80" fill="#8b949e">index 1: "bae" -&gt; e present, no match</text>
    <text x="20" y="105" fill="#8b949e">... continues sliding ...</text>
    <text x="20" y="130" fill="#f0883e">index 6: "bac" -&gt; counts match -&gt; record 6</text>
  </g>
</svg>

Every window position is checked and recorded if it matches, instead of stopping at the first hit.

## 5. Runnable example

```java
// FindAllAnagrams.java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class FindAllAnagrams {

    // Level 1 -- Brute force: rebuild the frequency array for every window
    // from scratch. O(n * 26) time.
    static List<Integer> bruteForce(String s, String p) {
        List<Integer> result = new ArrayList<>();
        int n = p.length();
        if (s.length() < n) return result;
        int[] need = new int[26];
        for (char c : p.toCharArray()) need[c - 'a']++;

        for (int i = 0; i + n <= s.length(); i++) {
            int[] window = new int[26];
            for (int j = i; j < i + n; j++) window[s.charAt(j) - 'a']++;
            if (Arrays.equals(need, window)) result.add(i);
        }
        return result;
    }

    // KEY INSIGHT: same fixed-size sliding window as Permutation in
    // String -- update the frequency counts incrementally on each slide,
    // but now record every match instead of stopping at the first.

    // Level 2 -- Optimal: fixed-size sliding window, incremental counts.
    // O(n) time, O(1) space (26-slot arrays) plus the output list.
    public static List<Integer> findAnagrams(String s, String p) {
        List<Integer> result = new ArrayList<>();
        int n = p.length();
        if (s.length() < n) return result;

        int[] need = new int[26];
        int[] window = new int[26];
        for (int i = 0; i < n; i++) {
            need[p.charAt(i) - 'a']++;
            window[s.charAt(i) - 'a']++;
        }
        if (Arrays.equals(need, window)) result.add(0);

        for (int i = n; i < s.length(); i++) {
            window[s.charAt(i) - 'a']++;
            window[s.charAt(i - n) - 'a']--;
            if (Arrays.equals(need, window)) result.add(i - n + 1);
        }
        return result;
    }

    // Level 3 -- Hardened: p longer than s returns an empty list
    // immediately, avoiding an invalid initial window.
    static List<Integer> hardened(String s, String p) {
        if (s == null || p == null) throw new IllegalArgumentException("inputs must not be null");
        return findAnagrams(s, p);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("cbaebabacd", "abc"));
        System.out.println("optimal:     " + findAnagrams("cbaebabacd", "abc"));
        System.out.println("p too long:  " + hardened("ab", "abcd"));
    }
}
```

How to run: save as `FindAllAnagrams.java`, then run `java FindAllAnagrams.java`.

## 6. Walkthrough

Dry run of `findAnagrams("cbaebabacd", "abc")` (need: a=1, b=1, c=1):

| i (entering) | window substring | matches? | recorded start |
|---|---|---|---|
| init (0-2) | "cba" | yes | 0 |
| 3 ('e' enters, 'c' drops) | "bae" | no | — |
| 4 ('b' enters, 'a' drops) | "aeb" | no | — |
| 5 ('a' enters, 'e' drops) | "eba" | no | — |
| 6 ('b' enters, 'b' drops) | "bab" | no | — |
| 7 ('a' enters, 'a' drops) | "aba" | no | — |
| 8 ('c' enters, 'b' drops) | "bac" | yes | 6 |
| 9 ('d' enters, 'a' drops) | "acd" | no | — |

Final result: `[0, 6]`. Time complexity: O(n) — n window slides, each doing O(26) work to compare frequency arrays. Space complexity: O(1) beyond the output list.

## 7. Gotchas & takeaways

> Gotcha: recording the wrong index — using the *current* right pointer `i` instead of the window's start `i - n + 1` — offsets every result by `n - 1`.

- This problem is a strict generalization of Permutation in String: same window mechanics, different stopping behavior.
- Related problems: Permutation in String, Group Anagrams, Minimum Window Substring.
