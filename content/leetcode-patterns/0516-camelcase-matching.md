---
card: leetcode-patterns
gi: 516
slug: camelcase-matching
title: Camelcase Matching
---

## 1. What it is

Given an array of `queries` and a `pattern` (a string of uppercase and lowercase letters), for each query determine whether you can insert lowercase letters into `pattern` (at any positions, including none) to make it equal to the query. Example: `pattern = "FB"`, query `"FooBar"` → `true` (insert "oo" after "F" and "ar" after "B"), query `"FootBall"` → `true`, query `"FrameBuffer"` → `true`, query `"ForceFeedBack"` → `false`.

## 2. Why & when

Although this problem is not usually solved with an explicit trie data structure, it belongs conceptually to the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family: matching a query against a pattern by "skipping" extra lowercase letters is the same two-pointer idea used when walking a trie path that allows optional detours. Constraints: up to 100 queries, pattern and queries up to 100 characters.

## 3. Core concept

**Key idea:** use two pointers, one on `pattern` and one on the current `query`. Walk through `query` character by character: if the current query character matches the current pattern character, advance both pointers. If it does not match, it must be a lowercase letter that was "inserted" — advance only the query pointer, but only if the character is lowercase (an uppercase character that does not match the pattern can never be a valid insertion, since insertions are restricted to lowercase letters). At the end, the match succeeds only if every pattern character was consumed (the pattern pointer reached its end).

**Steps:**
1. For each query, initialize `patternIndex = 0`.
2. Scan the query character by character: if `patternIndex < pattern.length()` and the current query character equals `pattern.charAt(patternIndex)`, increment `patternIndex`.
3. Otherwise, if the current query character is uppercase, the match fails immediately (an unmatched uppercase letter can never be a valid insertion).
4. If the current query character is lowercase and did not match, simply skip it (it represents an inserted letter) — do not advance `patternIndex`.
5. After scanning the whole query, the match succeeds only if `patternIndex == pattern.length()` (every pattern character was matched, in order).

**Why an unmatched uppercase letter always fails the match:** the problem only allows *lowercase* letters to be inserted into the pattern. If a query has an uppercase letter that does not line up with the next expected pattern character, there is no legal way to produce it — the query and pattern's uppercase letters must appear in the exact same relative order with nothing else possible in between them.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointers walking pattern and query, skipping lowercase insertions">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">pattern = "FB", query = "FooBar"</text>
    <text x="20" y="45" fill="#8b949e">F: matches pattern[0]='F' -&gt; advance both. patternIndex=1</text>
    <text x="20" y="65" fill="#8b949e">o,o: lowercase, don't match 'B' -&gt; skip (inserted letters)</text>
    <text x="20" y="85" fill="#8b949e">B: matches pattern[1]='B' -&gt; advance both. patternIndex=2</text>
    <text x="20" y="105" fill="#8b949e">a,r: lowercase, patternIndex already at end -&gt; skip</text>
    <text x="20" y="130" fill="#3fb950">patternIndex reached pattern.length() (2) -&gt; match succeeds</text>
  </g>
</svg>

Matching characters advance both pointers; unmatched lowercase letters are silently skipped as insertions.

## 5. Runnable example

```java
// CamelcaseMatching.java
import java.util.*;

public class CamelcaseMatching {

    static boolean matches(String query, String pattern) {
        int patternIndex = 0;
        for (char c : query.toCharArray()) {
            if (patternIndex < pattern.length() && c == pattern.charAt(patternIndex)) {
                patternIndex++;
            } else if (Character.isUpperCase(c)) {
                return false; // an unmatched uppercase letter can never be a valid insertion
            }
            // unmatched lowercase letters are simply skipped (treated as inserted)
        }
        return patternIndex == pattern.length();
    }

    static List<Boolean> camelMatch(String[] queries, String pattern) {
        List<Boolean> result = new ArrayList<>();
        for (String query : queries) {
            result.add(matches(query, pattern));
        }
        return result;
    }

    public static void main(String[] args) {
        String[] queries = {"FooBar", "FootBall", "FrameBuffer", "ForceFeedBack"};
        System.out.println(camelMatch(queries, "FB"));
        // [true, true, true, false]
    }
}
```

**How to run:** save as `CamelcaseMatching.java`, then run `java CamelcaseMatching.java`.

## 6. Walkthrough

Trace `matches("ForceFeedBack", "FB")`:

| char | patternIndex before | matches pattern[patternIndex]? | uppercase? | action | patternIndex after |
|---|---|---|---|---|---|
| F | 0 | yes ('F') | — | advance | 1 |
| o,r,c,e | 1 | no | no (lowercase) | skip | 1 |
| F | 1 | no ('B' expected) | **yes** | **fail** | — |

The second uppercase `F` in `"ForceFeedBack"` does not match the expected pattern character `'B'` at that point, and since it is uppercase, it cannot be treated as an inserted letter — the match fails immediately, returning `false`.

## 7. Gotchas & takeaways

> Gotcha: skipping unmatched uppercase letters the same way as lowercase ones (instead of failing immediately) would incorrectly accept queries with extra, unaccounted-for uppercase letters — only lowercase letters may be "inserted."

- The check must be asymmetric: matching characters always advance both pointers; unmatched lowercase letters are silently skipped; unmatched uppercase letters immediately fail the match.
- The match only succeeds if the *entire* pattern was consumed by the end of the query — reaching the end of the query with `patternIndex` short of `pattern.length()` is also a failure.
- Time: O(query length) per query — a single linear scan with two pointers, no backtracking needed.
