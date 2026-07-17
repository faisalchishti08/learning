---
card: leetcode-patterns
gi: 14
slug: merge-strings-alternately
title: Merge Strings Alternately
---

## 1. What it is

Given two strings `word1` and `word2`, merge them by adding letters in alternating order, starting with `word1`. If one string is longer, append its remaining letters at the end. Example: `word1 = "abc"`, `word2 = "pqr"` → `"apbqcr"`. Example with different lengths: `word1 = "ab"`, `word2 = "pqrs"` → `"apbqrs"`.

## 2. Why & when

Two independent pointers, one per string, both walking forward and interleaving their output — the same-direction, two-array shape used in Intersection of Two Arrays II, but here every element is included (no filtering condition), and order alternates instead of matching.

## 3. Core concept

**Key idea:** alternate taking one character from `word1`, then one from `word2`, advancing each string's own pointer only when you take from it; once one string runs out, drain the rest of the other.

**Steps:**
1. Set `i = 0`, `j = 0`, and an empty result builder.
2. While `i < word1.length()` or `j < word2.length()`:
   - If `i < word1.length()`, append `word1.charAt(i)`, then `i++`.
   - If `j < word2.length()`, append `word2.charAt(j)`, then `j++`.
3. Return the built string.

**Why it is correct:** the loop condition uses **or**, not **and**, so it keeps running as long as either string has characters left — once one string is exhausted, its `if` check is simply skipped every iteration, which is exactly the "append remaining letters" behavior the problem asks for, with no special-case branch needed.

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merge strings alternately interleaving two pointers">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">word1 = "ab"   word2 = "pqrs"</text>
    <text x="20" y="55" fill="#79c0ff">i=0 'a'</text>
    <text x="120" y="55" fill="#f0883e">j=0 'p'</text>
    <text x="220" y="55" fill="#79c0ff">i=1 'b'</text>
    <text x="320" y="55" fill="#f0883e">j=1 'q'</text>
    <text x="420" y="55" fill="#8b949e">i exhausted -&gt; drain word2: 'r', 's'</text>
    <text x="20" y="95" fill="#e6edf3">result: a p b q r s</text>
  </g>
</svg>

Once `word1` runs out at `i = 2`, the loop keeps draining `word2` alone until `j` also reaches the end.

## 5. Runnable example

```java
// MergeAlternately.java
public class MergeAlternately {

    // Level 1 -- Brute force: loop by the max length, using conditional
    // charAt calls guarded by bounds checks written inline each time --
    // functionally similar to the optimal version but less clearly
    // expresses the "drain the rest" step as its own idea.
    static String bruteForce(String word1, String word2) {
        StringBuilder sb = new StringBuilder();
        int max = Math.max(word1.length(), word2.length());
        for (int k = 0; k < max; k++) {
            if (k < word1.length()) sb.append(word1.charAt(k));
            if (k < word2.length()) sb.append(word2.charAt(k));
        }
        return sb.toString();
    }

    // KEY INSIGHT: using "or" as the loop condition, with two independent
    // bounds checks inside, naturally drains whichever string is longer --
    // no separate cleanup loop is needed.

    // Level 2 -- Optimal: two pointers, one pass. O(n + m) time, O(n + m)
    // space for the required output string.
    public static String mergeAlternately(String word1, String word2) {
        StringBuilder sb = new StringBuilder();
        int i = 0, j = 0;
        while (i < word1.length() || j < word2.length()) {
            if (i < word1.length()) {
                sb.append(word1.charAt(i));
                i++;
            }
            if (j < word2.length()) {
                sb.append(word2.charAt(j));
                j++;
            }
        }
        return sb.toString();
    }

    // Level 3 -- Hardened: an empty word1 or word2 just means one side of
    // the "if" never fires -- the loop still correctly returns the other
    // string unchanged.
    static String hardened(String word1, String word2) {
        if (word1 == null || word2 == null) throw new IllegalArgumentException("inputs must not be null");
        return mergeAlternately(word1, word2);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("abc", "pqr"));
        System.out.println("optimal:     " + mergeAlternately("ab", "pqrs"));
        System.out.println("one empty:   " + hardened("", "xyz"));
    }
}
```

How to run: save as `MergeAlternately.java`, then run `java MergeAlternately.java`.

## 6. Walkthrough

Dry run of `mergeAlternately("ab", "pqrs")`:

| step | i | j | append from word1? | append from word2? | result so far |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 'a', i=1 | 'p', j=1 | "ap" |
| 2 | 1 | 1 | 'b', i=2 | 'q', j=2 | "apbq" |
| 3 | 2 | 2 | skip (i out of bounds) | 'r', j=3 | "apbqr" |
| 4 | 2 | 3 | skip | 's', j=4 | "apbqrs" |
| 5 | 2 | 4 | loop condition false (both exhausted) | — | "apbqrs" |

Final result: `"apbqrs"`. Time complexity: O(n + m). Space complexity: O(n + m) for the output.

## 7. Gotchas & takeaways

> Gotcha: using `else if` instead of two independent `if` statements would only append from one string per iteration, breaking the alternating pattern — the two appends must be independent checks, both able to fire in the same loop iteration.

- The "or" loop condition combined with two independent bounds checks is a reusable trick any time you need to interleave two sequences of different lengths.
- Related problems: Merge Sorted Array, Zigzag Conversion, Add Strings.
