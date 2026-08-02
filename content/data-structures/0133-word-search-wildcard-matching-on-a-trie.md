---
card: data-structures
gi: 133
slug: word-search-wildcard-matching-on-a-trie
title: Word search & wildcard matching on a trie
---

## 1. What it is

**Wildcard matching** on a trie searches for a word where some characters are replaced by a wildcard (commonly `.`, meaning "any single character"). Instead of following exactly one child per character, a wildcard forces the search to branch into **every** child at that position, checking each one recursively.

## 2. Why & when

Plain `search` only works when every character is known. Real lookup needs often involve partial knowledge — a crossword-style "5-letter word, second letter is `a`, rest unknown" query, or LeetCode's "Design Add and Search Words Data Structure" problem. Building this on a trie keeps the known characters as cheap, direct lookups, and only pays the cost of branching at the positions that are actually wildcards.

## 3. Core concept

**How the operation works.** Walk the target string one character at a time, exactly like a normal trie search, with one difference: whenever the current character is a wildcard, instead of following one specific child, recurse into **every** child of the current node, trying each one as a candidate for that position. If any one of those recursive branches eventually succeeds (reaches the end of the string on a node marked `isEndOfWord`), the whole search succeeds.

**The invariant it must preserve.** A normal trie search only ever has one active node at a time. A wildcard search must explore multiple candidate paths simultaneously (via recursion, trying each child in turn) — success on *any* explored path counts as an overall match, since "any single character" only needs one interpretation to work.

**Complexity, and why wildcards are expensive.** A search with no wildcards costs `O(length)`, following one child per character. A search with `w` wildcard positions can cost up to `O(alphabet_size^w * length)` in the worst case, since each wildcard position can branch into every possible child. A word made entirely of wildcards degenerates into "visit every node in the whole trie."

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Searching the pattern c dot t against a trie storing cat, cot, and cup, branching at the wildcard position into both a and o, and matching successfully via the a branch">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">pattern: "c.t"  (dictionary: cat, cot, cup)</text>
    <circle cx="80" cy="50" r="12" fill="#161b22" stroke="#8b949e"/><text x="80" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">c</text>
    <circle cx="160" cy="30" r="12" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="160" y="34" fill="#e6edf3" text-anchor="middle" font-size="8">a</text>
    <circle cx="160" cy="70" r="12" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="160" y="74" fill="#e6edf3" text-anchor="middle" font-size="8">o</text>
    <circle cx="160" cy="110" r="12" fill="#161b22" stroke="#8b949e"/><text x="160" y="114" fill="#e6edf3" text-anchor="middle" font-size="8">u</text>
    <line x1="92" y1="50" x2="148" y2="34" stroke="#79c0ff" stroke-width="2"/>
    <line x1="92" y1="50" x2="148" y2="66" stroke="#79c0ff" stroke-width="2"/>
    <line x1="92" y1="52" x2="148" y2="106" stroke="#8b949e"/>
    <text x="260" y="30" fill="#79c0ff" font-size="9">'.' branches here -&gt; try 'a'</text>
    <text x="260" y="70" fill="#79c0ff" font-size="9">'.' branches here -&gt; try 'o'</text>
    <text x="260" y="110" fill="#8b949e" font-size="9">'u' leads to "cup", not "c.t" -- irrelevant here</text>
    <circle cx="220" cy="30" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="220" y="34" fill="#e6edf3" text-anchor="middle" font-size="8">t*</text>
    <circle cx="220" cy="70" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="220" y="74" fill="#e6edf3" text-anchor="middle" font-size="8">t*</text>
    <line x1="172" y1="30" x2="208" y2="30" stroke="#79c0ff" stroke-width="2"/>
    <line x1="172" y1="70" x2="208" y2="70" stroke="#79c0ff" stroke-width="2"/>
    <text x="300" y="150" fill="#f0883e" text-anchor="middle" font-size="10">both branches reach a 't' node marked isEndOfWord -- "c.t" matches BOTH cat and cot</text>
  </g>
</svg>

At the wildcard position, the search tries every child (`a`, `o`, `u`), recursing into each. Both the `a` and `o` branches reach a matching `t` node, so `"c.t"` successfully matches (it does not need to find every match, just confirm at least one exists).

## 5. Runnable example

```java
// WildcardTrieSearch.java
import java.util.HashMap;
import java.util.Map;

public class WildcardTrieSearch {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }

    static class WordDictionary {
        TrieNode root = new TrieNode();

        void addWord(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) current = current.children.computeIfAbsent(c, key -> new TrieNode());
            current.isEndOfWord = true;
        }

        // Basic: exact search, no wildcards -- the ordinary trie walk.
        boolean searchExact(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) {
                current = current.children.get(c);
                if (current == null) return false;
            }
            return current.isEndOfWord;
        }

        // Intermediate + Advanced: wildcard search -- '.' branches into every child at that position.
        boolean search(String word) { return searchHelper(root, word, 0); }

        private boolean searchHelper(TrieNode node, String word, int index) {
            if (index == word.length()) return node.isEndOfWord;
            char c = word.charAt(index);

            if (c != '.') {
                TrieNode child = node.children.get(c);
                return child != null && searchHelper(child, word, index + 1); // exactly one path to try
            }

            for (TrieNode child : node.children.values()) { // '.': try EVERY child at this position
                if (searchHelper(child, word, index + 1)) return true; // any single success is enough
            }
            return false;
        }
    }

    static void basicLevel() {
        WordDictionary dict = new WordDictionary();
        dict.addWord("cat");
        System.out.println("basic: searchExact(\"cat\") -> " + dict.searchExact("cat"));
        System.out.println("basic: searchExact(\"cot\") -> " + dict.searchExact("cot"));
    }

    static void intermediateLevel() {
        WordDictionary dict = new WordDictionary();
        for (String w : new String[]{"cat", "cot", "cup"}) dict.addWord(w);

        System.out.println("intermediate: search(\"c.t\") -> " + dict.search("c.t") + " (matches cat AND cot)");
        System.out.println("intermediate: search(\"c.p\") -> " + dict.search("c.p") + " (matches cup)");
        System.out.println("intermediate: search(\"c.x\") -> " + dict.search("c.x") + " (no word ends in x)");
    }

    // Advanced: multiple wildcards, confirming the branching compounds correctly across positions.
    static void advancedLevel() {
        WordDictionary dict = new WordDictionary();
        for (String w : new String[]{"cat", "cot", "cup", "car", "bat"}) dict.addWord(w);

        System.out.println("advanced: search(\"...\") (any 3-letter word) -> " + dict.search("..."));
        System.out.println("advanced: search(\".a.\") (any word with 'a' in the middle) -> " + dict.search(".a."));
        System.out.println("advanced: search(\"....\") (any 4-letter word -- none stored) -> " + dict.search("...."));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `WildcardTrieSearch.java`, then run `java WildcardTrieSearch.java`.

## 6. Walkthrough

1. `basicLevel()` runs exact searches with no wildcards — identical to the ordinary trie `search` operation. `"cat"` matches; `"cot"` does not, since it was never inserted in this dictionary.
2. `intermediateLevel()` searches `"c.t"` against `{"cat", "cot", "cup"}`. At index `0`, `c` matches directly (one path). At index `1`, the wildcard forces the search to try every child of the `c` node: `a`, `o`, and `u`. The `a` branch and `o` branch both continue to index `2`, where `t` matches directly on each, landing on `isEndOfWord` nodes — so the overall search returns `true` on the very first successful branch it finds (the `u` branch, leading toward `"cup"`, is irrelevant here since it needs `p`, not `t`, at index 2, but the search may not even reach it if `a` or `o` already succeeded).
3. `advancedLevel()` searches `"..."` (three wildcards) against a five-word dictionary. Every position branches into every available child, effectively exploring every 3-letter stored word — `"cat"`, `"cot"`, `"cup"`, `"car"`, and `"bat"` are all 3 letters, so this returns `true` almost immediately upon finding the first complete path. `"...."` (four wildcards) explores exhaustively but finds no 4-letter word in the dictionary, correctly returning `false` only after every possible branch has been tried.

## 7. Gotchas & takeaways

> Gotcha: a search pattern made entirely of wildcards degenerates into visiting a large fraction of the whole trie — `search(".".repeat(n))` for a large `n` can be far more expensive than a normal `O(length)` search, since the branching factor compounds at every wildcard position.

- A wildcard character forces the search to try every child at that position, instead of following one specific child.
- The search succeeds as soon as any one branch reaches the end of the string on an `isEndOfWord` node — it does not need to explore every branch once a match is found.
- Cost grows with the number of wildcard positions, up to `O(alphabet_size^w * length)` in the worst case — a small number of wildcards keeps this practical, but many wildcards can be very expensive.
- Related concepts: [Insert / search / startsWith](0129-insert-search-startswith.md), [Spell-check & dictionary lookup](0131-spell-check-dictionary-lookup.md).
