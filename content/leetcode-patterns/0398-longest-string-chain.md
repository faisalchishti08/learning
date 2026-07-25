---
card: leetcode-patterns
gi: 398
slug: longest-string-chain
title: Longest String Chain
---

## 1. What it is

Given an array of words, a word `B` is a PREDECESSOR of word `A` if you can insert exactly one letter into `B`, anywhere, without reordering the other letters, to get `A`. A "word chain" is a sequence `word1 -> word2 -> ... -> wordK`, where each word is a predecessor of the next. Return the length of the LONGEST possible word chain. Example: `words = ["a","b","ba","bca","bda","bdca"]` → `4` (`"a" -> "ba" -> "bda" -> "bdca"`).

## 2. Why & when

This is LIS applied to WORDS instead of numbers, using LENGTH as the natural ordering (a predecessor is always exactly one letter SHORTER) and "is a predecessor of" as the compatibility rule. Use this shape whenever a problem chains strings together under an insertion/deletion relationship, since sorting by length plays the same role sorting by value plays in numeric LIS variants.

## 3. Core concept

**Key idea:** sort words by LENGTH (ascending). Build `dp[word]` = the length of the longest chain ENDING at `word`, using a hash map keyed by the word itself (not an array index), since chains can be looked up by generating each word's possible PREDECESSORS directly.

**Steps:**
1. Sort `words` by length, ascending.
2. Create an empty map `dp`.
3. For each `word` in sorted order: for each position `i` in `word`, form `predecessor = word` with the character at position `i` REMOVED. If `predecessor` exists in `dp`, candidate `= dp[predecessor] + 1`; track the best candidate across all `i`.
4. Set `dp[word] = max(1, best candidate found)`. Track the overall maximum across all words.
5. Return the overall maximum.

**Why it is correct:** since a predecessor is always exactly ONE character shorter, sorting by length guarantees every possible predecessor of `word` has ALREADY been fully processed (and is in `dp`) by the time `word` itself is processed. Checking every way to remove ONE character from `word` (rather than searching the word list for matches) directly generates every CANDIDATE predecessor, an O(word length) operation per word.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="word bda generating three candidate predecessors by removing one character at a time, checking each against the dp map">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">word = "bda"; remove each position: "da", "ba", "bd"</text>
    <text x="10" y="45">dp map so far: {"ba": 2, ...}</text>
    <text x="10" y="65">"ba" found in dp -&gt; candidate = dp["ba"] + 1 = 3</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp["bda"] = 3</text>
  </g>
</svg>

Removing one character at a time generates every candidate predecessor to check against the map.

## 5. Runnable example

```java
// LongestStringChain.java
import java.util.*;

public class LongestStringChain {

    // KEY INSIGHT: sort by LENGTH (the natural ordering here), then
    // for each word, generate every candidate predecessor by removing
    // one character, and look each up in a map -- same "extend the
    // best compatible chain" idea as numeric LIS.

    static int longestStrChain(String[] words) {
        Arrays.sort(words, Comparator.comparingInt(String::length));
        Map<String, Integer> dp = new HashMap<>();
        int maxLen = 1;

        for (String word : words) {
            int best = 1;
            for (int i = 0; i < word.length(); i++) {
                String predecessor = word.substring(0, i) + word.substring(i + 1);
                if (dp.containsKey(predecessor)) {
                    best = Math.max(best, dp.get(predecessor) + 1);
                }
            }
            dp.put(word, best);
            maxLen = Math.max(maxLen, best);
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(longestStrChain(new String[]{"a", "b", "ba", "bca", "bda", "bdca"}));
        // 4
    }
}
```

**How to run:** `java LongestStringChain.java`

## 6. Walkthrough

Trace `longestStrChain(["a","b","ba","bca","bda","bdca"])` (already sorted by length):

| word | candidate predecessors checked | best | dp[word] |
|---|---|---|---|
| "a" | (none, length 1) | 1 | 1 |
| "ba" | "a" (in dp, len 1) | 2 | 2 |
| "bda" | "da", "ba" (in dp, len 2), "bd" | 3 | 3 |
| "bdca" | "dca", "bca", "bda" (in dp, len 3), "bdc" | 4 | 4 |

`maxLen = 4`, matching the expected chain `"a" -> "ba" -> "bda" -> "bdca"`. Time complexity is O(sum of word lengths squared) — each word of length `L` generates `L` candidates, each substring construction costing O(L), giving O(L^2) per word. Space is O(total characters across all words).

## 7. Gotchas & takeaways

> Gotcha: sorting words ALPHABETICALLY instead of by LENGTH breaks the algorithm — a predecessor's chain value must already be computed before its successor is processed, which requires the STRICT length ordering, not lexicographic order.

- Generating candidate predecessors DIRECTLY (by removing each character) instead of scanning the word list for matches is what keeps this efficient — it turns "find compatible words" from an O(n) search into an O(word length) generation.
- Multiple words can tie for the SAME length, and the sort must not break their relative independence — words of equal length never chain into each other, since a predecessor must be strictly SHORTER.
- Related problems: Longest Increasing Subsequence (the numeric-ordering ancestor of this chain-building idea), Longest Arithmetic Subsequence (also uses a lookup-based extension, keyed by a computed property, here the removed-character result instead of a numeric difference).
