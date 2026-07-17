---
card: leetcode-patterns
gi: 51
slug: substring-with-concatenation-of-all-words
title: Substring with Concatenation of All Words
---

## 1. What it is

Given a string `s` and an array `words` of same-length words, find all starting indices of substrings in `s` that are a concatenation of every word in `words` exactly once, in any order. Example: `s = "barfoothefoobarman"`, `words = ["foo", "bar"]` → answer `[0, 9]` (`"barfoo"` at index 0, `"foobar"` at index 9).

## 2. Why & when

The total substring length is fixed (`words.length * wordLength`), and it must decompose exactly into a multiset match of `words` — this is Permutation in String's frequency-matching idea, but operating on whole words instead of single characters, checked at multiple staggered starting offsets to cover every possible word-alignment.

## 3. Core concept

**Key idea:** a valid substring is fixed-length and must contain each word in `words` exactly as many times as it appears in `words`. Because words have fixed length, you can slide a window word-by-word (not character-by-character) and use the Permutation-in-String frequency-map trick, run once per possible starting offset (`0` to `wordLength - 1`) to make sure no valid alignment is missed.

**Steps:**
1. Build a frequency map `need` for `words`.
2. Compute `wordLen` and `totalLen = words.length * wordLen`.
3. For each starting offset `start` from `0` to `wordLen - 1`:
   - Use a sliding window over word-sized chunks, starting at `start`, stepping by `wordLen`.
   - Maintain a `window` frequency map and a `count` of matched words. For each new chunk: if it's a word in `need`, add it to `window` and increment `count` (or, if it now exceeds `need`'s count for that word, shrink from the left, word by word, until it doesn't).
   - If a chunk is not any word in `words` at all, reset the window entirely (move `left` to just past this chunk).
   - Whenever the window spans exactly `words.length` words with matching counts, record the window's starting index.
4. Return all recorded indices.

**Why it is correct:** because every word has the same fixed length, the substring can only be validly decomposed into words starting at one of `wordLen` possible alignments relative to the start of `s`. Running the word-level version of the frequency-matching sliding window at each of those `wordLen` starting offsets guarantees every possible alignment is checked, and the same monotonic "excess word forces a shrink" logic from Permutation in String applies at the word level instead of the character level.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Substring concatenation sliding window over word chunks">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "barfoothefoobarman", words = ["foo","bar"], wordLen=3</text>
    <rect x="20" y="40" width="60" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="80" y="40" width="60" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="60" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="50" y="60" fill="#e6edf3" text-anchor="middle">bar</text>
    <text x="110" y="60" fill="#e6edf3" text-anchor="middle">foo</text>
    <text x="170" y="60" fill="#e6edf3" text-anchor="middle">the</text>
    <text x="20" y="95" fill="#8b949e">chunks "bar","foo" match need exactly -&gt; record start 0</text>
    <text x="20" y="118" fill="#8b949e">chunk "the" is not in words -&gt; window resets entirely from here</text>
  </g>
</svg>

Reading `s` in fixed-length word chunks, matching against a word frequency map, mirrors Permutation in String at the granularity of whole words.

## 5. Runnable example

```java
// SubstringConcatenationAllWords.java
import java.util.*;

public class SubstringConcatenationAllWords {

    // Level 1 -- Brute force: for every starting index, check whether the
    // next words.length words (in some order) exactly match words, using
    // a frequency map rebuilt each time. O(n * words.length) time.
    static List<Integer> bruteForce(String s, String[] words) {
        List<Integer> result = new ArrayList<>();
        if (words.length == 0) return result;
        int wordLen = words[0].length();
        int totalLen = wordLen * words.length;
        Map<String, Integer> need = new HashMap<>();
        for (String w : words) need.merge(w, 1, Integer::sum);

        for (int i = 0; i + totalLen <= s.length(); i++) {
            Map<String, Integer> seen = new HashMap<>();
            boolean ok = true;
            for (int j = 0; j < words.length; j++) {
                String chunk = s.substring(i + j * wordLen, i + (j + 1) * wordLen);
                seen.merge(chunk, 1, Integer::sum);
                if (seen.get(chunk) > need.getOrDefault(chunk, 0)) { ok = false; break; }
            }
            if (ok) result.add(i);
        }
        return result;
    }

    // KEY INSIGHT: since words have fixed length, sliding a window one
    // WORD at a time (not one character at a time), at each of wordLen
    // possible starting offsets, turns this into words.length separate
    // runs of the Permutation-in-String frequency-matching technique.

    // Level 2 -- Optimal: word-level sliding window per offset. O(n *
    // wordLen) time overall, O(words.length) space.
    public static List<Integer> findSubstring(String s, String[] words) {
        List<Integer> result = new ArrayList<>();
        if (words.length == 0 || s.isEmpty()) return result;
        int wordLen = words[0].length();
        int numWords = words.length;
        int totalLen = wordLen * numWords;
        if (s.length() < totalLen) return result;

        Map<String, Integer> need = new HashMap<>();
        for (String w : words) need.merge(w, 1, Integer::sum);

        for (int start = 0; start < wordLen; start++) {
            Map<String, Integer> window = new HashMap<>();
            int left = start, count = 0;
            for (int right = start; right + wordLen <= s.length(); right += wordLen) {
                String chunk = s.substring(right, right + wordLen);
                if (need.containsKey(chunk)) {
                    window.merge(chunk, 1, Integer::sum);
                    count++;
                    while (window.get(chunk) > need.get(chunk)) {
                        String leftChunk = s.substring(left, left + wordLen);
                        window.merge(leftChunk, -1, Integer::sum);
                        count--;
                        left += wordLen;
                    }
                    if (count == numWords) {
                        result.add(left);
                        String leftChunk = s.substring(left, left + wordLen);
                        window.merge(leftChunk, -1, Integer::sum);
                        count--;
                        left += wordLen;
                    }
                } else {
                    window.clear();
                    count = 0;
                    left = right + wordLen;
                }
            }
        }
        return result;
    }

    // Level 3 -- Hardened: words containing duplicate entries (e.g.
    // ["foo", "foo"]) are handled correctly, since `need` counts them by
    // frequency, not by presence alone.
    static List<Integer> hardened(String s, String[] words) {
        if (s == null || words == null) throw new IllegalArgumentException("inputs must not be null");
        return findSubstring(s, words);
    }

    public static void main(String[] args) {
        String s = "barfoothefoobarman";
        String[] words = {"foo", "bar"};
        System.out.println("brute force: " + bruteForce(s, words));
        System.out.println("optimal:     " + findSubstring(s, words));
        System.out.println("duplicate words: " + hardened("foobarfoobar", new String[] {"foo", "bar", "foo"}));
    }
}
```

How to run: save as `SubstringConcatenationAllWords.java`, then run `java SubstringConcatenationAllWords.java`.

## 6. Walkthrough

Dry run of `findSubstring("barfoothefoobarman", ["foo","bar"])` for offset `start = 0` (`wordLen = 3`, `numWords = 2`):

| right | chunk | in need? | window after | count | action |
|---|---|---|---|---|---|
| 0 | "bar" | yes | {bar:1} | 1 | count < 2, keep going |
| 3 | "foo" | yes | {bar:1,foo:1} | 2 | count == 2! record start=0; remove chunk at left=0 ("bar"), count=1, left=3 |
| 6 | "the" | no | cleared | 0 | reset: left=9 |
| 9 | "foo" | yes | {foo:1} | 1 | keep going |
| 12 | "bar" | yes | {foo:1,bar:1} | 2 | count == 2! record start=9; remove chunk at left=9 ("foo"), count=1, left=12 |
| 15 | "man" | no | cleared | 0 | reset |

Result from this offset: `[0, 9]`. The other offset (`start = 1, 2`) finds no additional matches for this input. Final answer: `[0, 9]`. Time complexity: O(n · wordLen), across all `wordLen` offsets combined, each doing an amortized linear scan. Space complexity: O(numWords) for the frequency maps.

## 7. Gotchas & takeaways

> Gotcha: sliding character-by-character instead of word-by-word (i.e., checking every index `i` instead of only aligned word boundaries) either misses valid matches or requires far more redundant substring extraction — always advance in fixed `wordLen` steps within each offset's scan.

- This problem needs `wordLen` separate scans (one per starting offset within a word) to guarantee every alignment is checked — a single word-by-word scan starting only at index 0 would miss matches that start at index 1, 2, etc. within the first word's length.
- Related problems: Permutation in String, Find All Anagrams in a String, Minimum Window Substring.
