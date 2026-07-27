---
card: leetcode-patterns
gi: 505
slug: trie-signal-prefix-search-word-dictionaries-or-bit-tries
title: Trie — signal: prefix search, word dictionaries, or bit-tries
---

## 1. What it is

A trie (pronounced "try," short for retrieval tree) is a tree where each edge represents one character, and a path from the root spells out a string. Words that share a prefix share the same path down to where they diverge — storing "cat" and "car" reuses the shared `c -> a` path, then branches into `t` and `r`.

## 2. Why & when

Reach for a trie whenever a brute-force solution scans an entire list of words to check a prefix, giving O(n · L) time (n words, average length L) for every prefix check. A trie turns "does any word start with this prefix" into a single walk down the tree, taking time proportional only to the prefix's length, regardless of how many words are stored.

Learn to recognize these signals in a problem statement:

- **"Insert a word, then search for exact words or prefixes"** — the direct definition of a trie (`insert`, `search`, `startsWith`).
- **"Autocomplete" or "search suggestions"** — finding all words sharing a given prefix is a trie's core strength: walk to the prefix's node, then explore everything beneath it.
- **"Replace a word with its shortest root"** (e.g. word-stemming problems) — walking a trie of roots finds the shortest matching prefix in one pass.
- **A dictionary with wildcard search** ("`.` matches any character") — a trie handles this with a recursive search that branches into every child when a wildcard is hit, rather than checking every stored word individually.
- **Bit manipulation problems phrased as "maximum XOR of two numbers"** — a **bit-trie** treats each number's binary representation as a "word" of `0`/`1` characters, letting you greedily choose the opposite bit at each level to maximize XOR.

The alternative is a hash set (fast exact lookup, but no prefix support) or scanning every word (O(n · L) per query). A trie is the answer whenever prefixes, not just exact matches, matter.

## 3. Core concept

**Key idea:** each trie node has an array (or map) of children, one slot per possible character (26 for lowercase letters, or 2 for a bit-trie), plus a boolean flag marking "a word ends here." Inserting a word walks down the tree one character at a time, creating any missing nodes, then marks the final node's end-of-word flag. Searching walks the same path; if any character's node is missing, the word (or prefix) is absent.

**Why sharing prefixes saves space and time:** two words with a common prefix (like "cat" and "car") share the same nodes for that prefix's characters. Neither the shared storage nor the shared traversal is duplicated — the tree pays for each distinct prefix only once, no matter how many words extend from it.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A trie storing cat, car, and dog, sharing the shared ca prefix">
  <g font-family="sans-serif" font-size="13">
    <circle cx="350" cy="20" r="15" fill="#161b22" stroke="#79c0ff"/>
    <text x="350" y="25" fill="#e6edf3" text-anchor="middle">root</text>
    <line x1="350" y1="35" x2="250" y2="70" stroke="#8b949e"/>
    <circle cx="250" cy="80" r="15" fill="#161b22" stroke="#30363d"/>
    <text x="250" y="85" fill="#e6edf3" text-anchor="middle">c</text>
    <line x1="350" y1="35" x2="450" y2="70" stroke="#8b949e"/>
    <circle cx="450" cy="80" r="15" fill="#161b22" stroke="#30363d"/>
    <text x="450" y="85" fill="#e6edf3" text-anchor="middle">d</text>
    <line x1="250" y1="95" x2="250" y2="130" stroke="#8b949e"/>
    <circle cx="250" cy="140" r="15" fill="#161b22" stroke="#30363d"/>
    <text x="250" y="145" fill="#e6edf3" text-anchor="middle">a</text>
    <line x1="450" y1="95" x2="450" y2="130" stroke="#8b949e"/>
    <circle cx="450" cy="140" r="15" fill="#161b22" stroke="#30363d"/>
    <text x="450" y="145" fill="#e6edf3" text-anchor="middle">o</text>
    <line x1="250" y1="155" x2="190" y2="190" stroke="#8b949e"/>
    <circle cx="190" cy="200" r="15" fill="#161b22" stroke="#3fb950"/>
    <text x="190" y="205" fill="#e6edf3" text-anchor="middle">t*</text>
    <line x1="250" y1="155" x2="310" y2="190" stroke="#8b949e"/>
    <circle cx="310" cy="200" r="15" fill="#161b22" stroke="#3fb950"/>
    <text x="310" y="205" fill="#e6edf3" text-anchor="middle">r*</text>
    <line x1="450" y1="155" x2="450" y2="190" stroke="#8b949e"/>
    <circle cx="450" cy="200" r="15" fill="#161b22" stroke="#3fb950"/>
    <text x="450" y="205" fill="#e6edf3" text-anchor="middle">g*</text>
  </g>
</svg>

`cat`, `car`, and `dog` share prefixes where their letters overlap; `*` marks a node where a word ends.

## 5. Runnable example

The artifact below is a reusable signal-checker: it compares brute-force prefix scanning against a trie's prefix walk, on a small dictionary.

### Signal-checker

```java
// TrieSignal.java
import java.util.*;

public class TrieSignal {

    static boolean bruteForceHasPrefix(List<String> words, String prefix) {
        for (String word : words) {
            if (word.startsWith(prefix)) return true;
        }
        return false;
    }

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isWord = false;
    }

    static TrieNode buildTrie(List<String> words) {
        TrieNode root = new TrieNode();
        for (String word : words) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                node = node.children.computeIfAbsent(c, k -> new TrieNode());
            }
            node.isWord = true;
        }
        return root;
    }

    static boolean trieHasPrefix(TrieNode root, String prefix) {
        TrieNode node = root;
        for (char c : prefix.toCharArray()) {
            node = node.children.get(c);
            if (node == null) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        List<String> words = Arrays.asList("cat", "car", "dog", "dodge");
        TrieNode root = buildTrie(words);

        System.out.println("brute force has prefix 'ca': " + bruteForceHasPrefix(words, "ca"));
        System.out.println("trie        has prefix 'ca': " + trieHasPrefix(root, "ca"));
        System.out.println("trie        has prefix 'do': " + trieHasPrefix(root, "do"));
        System.out.println("trie        has prefix 'x':  " + trieHasPrefix(root, "x"));
    }
}
```

**How to run:** save as `TrieSignal.java`, then run `java TrieSignal.java`.

## 6. Walkthrough

1. You read a problem asking you to insert words into a dictionary, then repeatedly answer "does any stored word start with this prefix." That is the direct trie signal.
2. You build a trie from `["cat", "car", "dog", "dodge"]`: the root branches into `c` and `d`; `c` leads to `a`, which branches into `t` (marking "cat") and `r` (marking "car"); `d` leads to `o`, then `g` (marking "dog"), and `dodge` extends further with its own branch.
3. Checking prefix `"ca"` walks `root -> c -> a` — both nodes exist, so the prefix is present, matching the brute-force scan.
4. Checking prefix `"do"` walks `root -> d -> o` — both exist (shared by both "dog" and "dodge"), confirming the prefix in one two-step walk instead of scanning every word.
5. Checking prefix `"x"` fails immediately at the root, since no child for `x` exists — O(1) rejection instead of scanning the whole word list.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `isWord` flag means a trie cannot distinguish "this path exists because it's a prefix of a longer word" from "a word actually ends here" — searching for an exact word must check both that the path exists AND that the final node's `isWord` flag is true.

- Signal words: "prefix," "autocomplete," "dictionary of words," "wildcard search," "maximum XOR" (bit-trie).
- A trie trades memory (one node per distinct prefix character) for prefix-query speed proportional only to the query length, not the dictionary size.
- Alternative: a hash set answers exact-match queries in O(1) but cannot answer prefix queries at all.
