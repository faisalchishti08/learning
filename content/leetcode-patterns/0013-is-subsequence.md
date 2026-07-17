---
card: leetcode-patterns
gi: 13
slug: is-subsequence
title: Is Subsequence
---

## 1. What it is

Given two strings `s` and `t`, return `true` if `s` is a subsequence of `t` — meaning you can delete some (or no) characters from `t` without changing the order of the rest, and get `s`. Example: `s = "abc"`, `t = "ahbgdc"` → `true`, because `a`, `b`, `c` appear in `t` in that order (with other characters between them).

## 2. Why & when

A subsequence check needs to confirm every character of `s` shows up in `t` in the right relative order. Two pointers over two different strings, both moving forward, is the natural fit: one pointer tracks "which character of `s` we still need to find," the other scans `t` looking for it.

## 3. Core concept

**Key idea:** you only need to advance the `s` pointer when you find a match; the `t` pointer always advances, since you are allowed to skip characters in `t` freely.

**Steps:**
1. Set `i = 0` (index into `s`), `j = 0` (index into `t`).
2. While `i < s.length()` and `j < t.length()`:
   - If `s.charAt(i) == t.charAt(j)`, that character of `s` is found — advance `i`.
   - Always advance `j`, whether or not it matched.
3. After the loop, `s` is a subsequence of `t` exactly when `i == s.length()` — every character of `s` was matched.

**Why it is correct:** greedily matching each character of `s` to the *earliest* possible position in `t` never hurts — using an earlier match leaves more of `t` available for the remaining characters of `s`, so there is never a benefit to skipping a valid match and waiting for a later one.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Is subsequence two pointers over s and t">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "abc"</text>
    <text x="20" y="60" fill="#e6edf3">t = "a h b g d c"</text>
    <text x="20" y="90" fill="#79c0ff">i=0 'a' matches t[0]='a' -&gt; i++, j++</text>
    <text x="20" y="112" fill="#f0883e">i=1 'b' vs t[1]='h' no match -&gt; j++ only</text>
    <text x="20" y="134" fill="#8b949e">i=1 'b' vs t[2]='b' matches -&gt; i++, j++ ... continues to i=3=s.length -&gt; true</text>
  </g>
</svg>

`i` only advances on a match; `j` always advances, scanning `t` for the next needed character.

## 5. Runnable example

```java
// IsSubsequence.java
public class IsSubsequence {

    // Level 1 -- Brute force: for each character of s, search t starting
    // from where the last search ended, using indexOf. O(n * m) worst case
    // if indexOf rescans -- and it obscures the two-pointer structure.
    static boolean bruteForce(String s, String t) {
        int fromIndex = 0;
        for (char c : s.toCharArray()) {
            int found = t.indexOf(c, fromIndex);
            if (found == -1) return false;
            fromIndex = found + 1;
        }
        return true;
    }

    // KEY INSIGHT: matching each character of s to the EARLIEST available
    // position in t is always at least as good as matching it later, so a
    // single forward pass through both strings with two pointers suffices.

    // Level 2 -- Optimal: two pointers, one pass. O(n + m) time, O(1) space.
    public static boolean isSubsequence(String s, String t) {
        int i = 0, j = 0;
        while (i < s.length() && j < t.length()) {
            if (s.charAt(i) == t.charAt(j)) {
                i++;
            }
            j++;
        }
        return i == s.length();
    }

    // Level 3 -- Hardened: an empty s is trivially a subsequence of
    // anything (loop never runs, i stays 0 == s.length()); s longer than t
    // correctly returns false once j exhausts t first.
    static boolean hardened(String s, String t) {
        if (s == null || t == null) throw new IllegalArgumentException("s and t must not be null");
        return isSubsequence(s, t);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("abc", "ahbgdc"));
        System.out.println("optimal:     " + isSubsequence("abc", "ahbgdc"));
        System.out.println("not a subsequence: " + isSubsequence("axc", "ahbgdc"));
        System.out.println("empty s: " + hardened("", "anything"));
    }
}
```

How to run: save as `IsSubsequence.java`, then run `java IsSubsequence.java`.

## 6. Walkthrough

Dry run of `isSubsequence("abc", "ahbgdc")`:

| step | i | j | s[i] | t[j] | match? | i after | j after |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 0 | a | a | yes | 1 | 1 |
| 2 | 1 | 1 | b | h | no | 1 | 2 |
| 3 | 1 | 2 | b | b | yes | 2 | 3 |
| 4 | 2 | 3 | c | g | no | 2 | 4 |
| 5 | 2 | 4 | c | d | no | 2 | 5 |
| 6 | 2 | 5 | c | c | yes | 3 | 6 |

Loop ends (`i == 3 == s.length()`), so return `true`. Time complexity: O(n + m). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: this simple O(n + m) approach is the right one for a single query, but if the interviewer asks a follow-up — "what if you have to answer this for thousands of different `s` strings against the same `t`?" — the two-pointer scan repeats wasted work; a precomputed "next occurrence of each character" table for `t` (binary search per character) answers each query in O(n log m) instead.

- Only the `s` pointer's advance is conditional; the `t` pointer always advances — that asymmetry is what makes this different from opposite-ends two pointers.
- Related problems: Number of Matching Subsequences, Longest Common Subsequence (a different pattern — dynamic programming), Edit Distance.
