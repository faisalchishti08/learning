---
card: leetcode-patterns
gi: 512
slug: implement-magic-dictionary
title: Implement Magic Dictionary
---

## 1. What it is

Design a class `MagicDictionary` supporting `buildDict(words)` (build from a list of distinct words) and `search(searchWord)`, which returns `true` if changing **exactly one** character of `searchWord` produces a word that exists in the dictionary (the changed character must differ from the original — you cannot "change" a character to itself). Example: dictionary `["hello", "leetcode"]`, `search("hello")` → `false` (no single-character change needed, since it already matches exactly), `search("hhllo")` → `true` (changing `h` to `e` at index 1 gives "hello").

## 2. Why & when

This extends [Design Add and Search Words Data Structure](0509-design-add-and-search-words-data-structure.md): instead of a wildcard matching any character, you need **exactly one position** to differ from a stored word. A trie walk with a "budget" of exactly one allowed mismatch, tracked through recursion, answers this directly — part of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. Constraints: up to 100 words, each up to 20 characters.

## 3. Core concept

**Key idea:** build a standard trie from the dictionary words. Search recursively, tracking how many character mismatches have been used so far. At each position: if the current trie character matches `searchWord`'s character, continue with no mismatch used; if it does not match, you may take the "used the one allowed mismatch" branch and continue (but only if you have not already used it). At the end, the search succeeds only if the path reaches an `isEnd` node with **exactly** one mismatch used (not zero — the exact match itself does not count as a valid answer).

**Steps:**
1. Build the trie from `words`.
2. `search(searchWord)`: call a recursive helper `matchFrom(node, searchWord, index, mismatchesUsed)`.
3. Base case: if `index == searchWord.length()`, return `node.isEnd && mismatchesUsed == 1`.
4. For each non-null child `c` of the current node: if `c` equals `searchWord.charAt(index)`, recurse with the same `mismatchesUsed`; if `c` differs and `mismatchesUsed == 0`, recurse with `mismatchesUsed + 1`.
5. Return `true` if any of these recursive branches succeeds.

**Why requiring exactly one mismatch (not "at most one") matters:** the problem explicitly disallows returning `true` for an exact match with zero changes — you must actually change one character. Tracking the exact count (not just "at most 1") and checking `== 1` at the base case enforces this precisely.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tracking a mismatch budget of exactly one while walking the trie">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">dictionary = ["hello"]. search("hhllo")</text>
    <text x="20" y="45" fill="#8b949e">h==h (0 mismatches). h!=e, use budget (1 mismatch). l==l. l==l. o==o.</text>
    <text x="20" y="70" fill="#3fb950">reach end of word, isEnd=true, mismatchesUsed=1 exactly -&gt; true</text>
    <text x="20" y="100" fill="#f0883e">search("hello"): every char matches, mismatchesUsed=0 at the end -&gt; false (no change made)</text>
  </g>
</svg>

Exactly one character must differ; both zero mismatches and more than one mismatch are rejected.

## 5. Runnable example

```java
// MagicDictionary.java
public class MagicDictionary {

    private static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    private final TrieNode root = new TrieNode();

    public void buildDict(String[] words) {
        for (String word : words) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.isEnd = true;
        }
    }

    public boolean search(String searchWord) {
        return matchFrom(root, searchWord, 0, 0);
    }

    private boolean matchFrom(TrieNode node, String word, int index, int mismatchesUsed) {
        if (node == null || mismatchesUsed > 1) return false;
        if (index == word.length()) return node.isEnd && mismatchesUsed == 1;

        char target = word.charAt(index);
        for (int i = 0; i < 26; i++) {
            if (node.children[i] == null) continue;
            int nextMismatches = (i == target - 'a') ? mismatchesUsed : mismatchesUsed + 1;
            if (matchFrom(node.children[i], word, index + 1, nextMismatches)) return true;
        }
        return false;
    }

    public static void main(String[] args) {
        MagicDictionary dict = new MagicDictionary();
        dict.buildDict(new String[]{"hello", "leetcode"});

        System.out.println(dict.search("hello"));   // false (exact match, no change made)
        System.out.println(dict.search("hhllo"));   // true (change index 1: h -> e)
        System.out.println(dict.search("hell"));    // false (different length, no match possible)
        System.out.println(dict.search("leetcoded")); // false
    }
}
```

**How to run:** save as `MagicDictionary.java`, then run `java MagicDictionary.java`.

## 6. Walkthrough

Trace `search("hhllo")` against the trie built from `["hello", "leetcode"]`, following the path matching `"hello"`:

| index | target char | trie char | match? | mismatchesUsed after |
|---|---|---|---|---|
| 0 | h | h | yes | 0 |
| 1 | h | e | no | 1 (budget used) |
| 2 | l | l | yes | 1 |
| 3 | l | l | yes | 1 |
| 4 | o | o | yes | 1 |

At `index == 5` (end of word), `node.isEnd = true` (this is the end of "hello") and `mismatchesUsed == 1` exactly — the search returns `true`.

## 7. Gotchas & takeaways

> Gotcha: checking `mismatchesUsed <= 1` instead of `mismatchesUsed == 1` at the base case incorrectly accepts an exact match (zero changes) as a valid answer — the problem requires that exactly one character actually differ.

- Builds on the recursive branching idea from [Design Add and Search Words Data Structure](0509-design-add-and-search-words-data-structure.md), but branches only on *mismatches*, not on every possible character.
- Words of different lengths than `searchWord` can never match, since the trie walk naturally fails once it runs past the word's own length or the trie path ends early.
- Time: O(26 · L) worst case per search, where L is the word length — each position tries up to 26 children, but the mismatch budget of 1 keeps the branching factor low in practice.
