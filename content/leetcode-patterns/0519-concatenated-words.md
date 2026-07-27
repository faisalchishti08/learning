---
card: leetcode-patterns
gi: 519
slug: concatenated-words
title: Concatenated Words
---

## 1. What it is

Given a list of distinct `words` (no duplicates, no empty strings), find every word that can be built by concatenating **at least two** other shorter words from the same list. Example: `words = ["cat","cats","catsdogcats","dog","dogcatsdog","hippopotamuses","rat","ratcatdogcat"]` → `["catsdogcats","dogcatsdog","ratcatdogcat"]`.

## 2. Why & when

Checking "can this word be split into pieces that all exist elsewhere in the dictionary" is a prefix-matching problem repeated at every possible split point — a trie of all words lets you find, at each position in the candidate word, exactly how far a valid dictionary word extends, part of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family combined with dynamic programming (the classic "word break" recurrence). Constraints: up to 10,000 words, total characters up to 600,000.

## 3. Core concept

**Key idea:** insert every word into a trie. For each candidate word `w` of length `n`, run a boolean DP: `canBuild[i]` means "the prefix `w[0..i)` can be fully built from one or more dictionary words." Fill it by walking the trie from every reachable split position. The only twist: the single match that covers the *entire* word in one piece (starting at position 0 and ending at position `n`) must be excluded, since the problem requires **at least two** pieces, not one.

**Steps:**
1. Insert every word into a trie.
2. For each word `w`, initialize `canBuild[0] = true` (the empty prefix trivially "builds").
3. For each start position `i` from `0` to `n - 1` where `canBuild[i]` is true, walk the trie from the root matching `w[i], w[i+1], ...`. Whenever the walk passes a node with `isEnd = true` at some end position `j + 1`: if this match is the *entire* word (`i == 0` and `j + 1 == n`), skip it — do not mark `canBuild[n]` from this single piece. Otherwise, set `canBuild[j + 1] = true`.
4. `w` qualifies if `canBuild[n]` ends up `true` — since the whole-word single match was excluded, any way of reaching `canBuild[n]` now necessarily uses at least two pieces.
5. Collect every qualifying word.

**Why excluding just the one `i==0, end==n` case is enough (no separate piece-counter needed):** the *only* way to reach `canBuild[n]` using exactly one piece is the single match that starts at `0` and ends at `n` — every other path that reaches `canBuild[n]` necessarily passed through some earlier `canBuild[k]` (`0 < k < n`) first, which already required at least one prior piece. Blocking only that one special case is enough to guarantee any remaining path to `canBuild[n]` uses two or more pieces.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dynamic programming over split positions, combined with trie prefix matching at each position">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">word = "catsdogcats", dictionary has "cats", "dog"</text>
    <text x="20" y="45" fill="#8b949e">canBuild[0]=true. from position 0, trie matches "cats" (4 chars) -&gt; canBuild[4]=true</text>
    <text x="20" y="65" fill="#8b949e">from position 4, trie matches "dog" (3 chars) -&gt; canBuild[7]=true</text>
    <text x="20" y="90" fill="#3fb950">from position 7, trie matches "cats" again -&gt; canBuild[11]=true (11 = full length)</text>
    <text x="20" y="120" fill="#79c0ff">canBuild[11]=true via 3 pieces (cats, dog, cats) -&gt; qualifies (the whole-word single match was excluded)</text>
  </g>
</svg>

Each reachable split position marks the next piece's start; the single whole-word match is the only path explicitly blocked.

## 5. Runnable example

```java
// ConcatenatedWords.java
import java.util.*;

public class ConcatenatedWords {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    static TrieNode root = new TrieNode();

    static void insert(String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) node.children[index] = new TrieNode();
            node = node.children[index];
        }
        node.isEnd = true;
    }

    // returns true if word can be split into >= 2 dictionary words
    static boolean canBuildFromAtLeastTwo(String word) {
        int n = word.length();
        boolean[] canBuild = new boolean[n + 1];
        canBuild[0] = true;

        for (int i = 0; i < n; i++) {
            if (!canBuild[i]) continue;
            TrieNode node = root;
            for (int j = i; j < n; j++) {
                int index = word.charAt(j) - 'a';
                node = node.children[index];
                if (node == null) break;
                int end = j + 1;
                if (node.isEnd && !(i == 0 && end == n)) {
                    canBuild[end] = true; // exclude the single whole-word match
                }
            }
        }
        return canBuild[n];
    }

    static List<String> findAllConcatenatedWordsInADict(String[] words) {
        for (String word : words) {
            if (!word.isEmpty()) insert(word);
        }
        List<String> result = new ArrayList<>();
        for (String word : words) {
            if (!word.isEmpty() && canBuildFromAtLeastTwo(word)) {
                result.add(word);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        String[] words = {"cat", "cats", "catsdogcats", "dog", "dogcatsdog", "hippopotamuses", "rat", "ratcatdogcat"};
        System.out.println(findAllConcatenatedWordsInADict(words));
        // [catsdogcats, dogcatsdog, ratcatdogcat]
    }
}
```

**How to run:** save as `ConcatenatedWords.java`, then run `java ConcatenatedWords.java`.

## 6. Walkthrough

Trace `canBuildFromAtLeastTwo("catsdogcats")` (length 11) with the dictionary containing `"cat"`, `"cats"`, `"dog"`, and `"catsdogcats"` itself:

| i (start) | canBuild[i]? | trie walk finds isEnd at end= | excluded (whole-word)? | canBuild updated |
|---|---|---|---|---|
| 0 | true | 3 ("cat"), 4 ("cats") | no | canBuild[3]=true, canBuild[4]=true |
| 0 | true | 11 ("catsdogcats" itself) | **yes** (i=0, end=n=11) | not set |
| 3 | true | (no dictionary word starts "sdog...") | — | — |
| 4 | true | 7 ("dog") | no | canBuild[7]=true |
| 7 | true | 10 ("cat"), 11 ("cats") | no (i=7, not 0) | canBuild[10]=true, canBuild[11]=true |

`canBuild[11]` ends up `true`, reached via the 3-piece path (`cats` + `dog` + `cats`) starting at `i=7` — not via the excluded single whole-word match. The word qualifies.

## 7. Gotchas & takeaways

> Gotcha: excluding the whole-word match everywhere (not just when `i == 0`) is wrong and would break legitimate matches — a dictionary word matching a piece of the *remaining* suffix (starting from some `i > 0`) is exactly what a valid multi-piece decomposition looks like. Only the specific case `i == 0 && end == n` (the entire word matching itself in one piece) needs to be blocked.

- Combining a trie with a DP over split positions turns "can this be split into dictionary words" into an O(L²) check per word (L = word length), instead of trying every possible split combinatorially.
- Insert all words (including the ones you will later test) into the same trie — a word can be built from *other* words in the list, which the trie contains alongside everything else.
- Time: O(total characters across all words) to build the trie, O(L²) per word to run the DP, where L is that word's length.
