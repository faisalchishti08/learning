---
card: data-structures
gi: 126
slug: prefix-tree-trie-structure
title: Prefix tree (trie) structure
---

## 1. What it is

A **trie** (pronounced "try", short for re**trie**val tree, and also called a **prefix tree**) is a tree where each edge represents one character, and each root-to-node path spells out a string prefix. Every node marks whether the prefix ending there is also a **complete word**, not just a prefix of a longer one.

## 2. Why & when

A trie stores a set of strings so that any operation based on a *prefix* — "does any word start with `pre`?", "autocomplete what the user has typed so far" — costs only `O(length of the prefix)`, completely independent of how many words are stored. A hash set can check "is this exact string present?" just as fast, but it cannot answer "does anything start with this?" without scanning every entry; a trie answers both in the same way, by construction.

## 3. Core concept

**The structure's shape.** Each node holds a collection of children, one per possible next character (using either a fixed-size array or a map — see [Trie node with a children map/array](0132-trie-node-with-a-children-map-array.md)), plus a boolean flag, `isEndOfWord`, marking whether the path from the root to this node spells a complete stored word.

**The core invariant.** Every path from the root to any node spells out exactly one prefix, and that path is unique — there is only one way to reach the node for a given prefix, since each character maps to exactly one child slot per node. This is what makes lookups deterministic: given a string, there is exactly one path to follow, character by character.

**How the invariant makes prefix operations fast.** Because each node corresponds to exactly one prefix, checking "does this prefix exist?" is just a walk of `length(prefix)` steps down from the root, following one child link per character. If any needed child is missing partway through, the prefix does not exist — no scanning of the whole stored word set is ever required.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A trie storing cat, car, and dog, sharing the c-a prefix path before splitting into t and r, with end of word markers on the terminal nodes">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="25" r="14" fill="#161b22" stroke="#8b949e"/><text x="300" y="29" fill="#e6edf3" text-anchor="middle" font-size="8">root</text>
    <circle cx="220" cy="75" r="14" fill="#161b22" stroke="#79c0ff"/><text x="220" y="79" fill="#e6edf3" text-anchor="middle" font-size="9">c</text>
    <circle cx="400" cy="75" r="14" fill="#161b22" stroke="#79c0ff"/><text x="400" y="79" fill="#e6edf3" text-anchor="middle" font-size="9">d</text>
    <circle cx="220" cy="125" r="14" fill="#161b22" stroke="#79c0ff"/><text x="220" y="129" fill="#e6edf3" text-anchor="middle" font-size="9">a</text>
    <circle cx="400" cy="125" r="14" fill="#161b22" stroke="#79c0ff"/><text x="400" y="129" fill="#e6edf3" text-anchor="middle" font-size="9">o</text>
    <circle cx="180" cy="175" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="180" y="179" fill="#e6edf3" text-anchor="middle" font-size="9">t</text>
    <circle cx="260" cy="175" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="260" y="179" fill="#e6edf3" text-anchor="middle" font-size="9">r</text>
    <circle cx="400" cy="175" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="400" y="179" fill="#e6edf3" text-anchor="middle" font-size="9">g</text>
    <line x1="290" y1="35" x2="230" y2="65" stroke="#8b949e"/>
    <line x1="310" y1="35" x2="390" y2="65" stroke="#8b949e"/>
    <line x1="220" y1="89" x2="220" y2="111" stroke="#8b949e"/>
    <line x1="400" y1="89" x2="400" y2="111" stroke="#8b949e"/>
    <line x1="212" y1="138" x2="188" y2="162" stroke="#8b949e"/>
    <line x1="228" y1="138" x2="252" y2="162" stroke="#8b949e"/>
    <line x1="400" y1="139" x2="400" y2="161" stroke="#8b949e"/>
    <text x="220" y="205" fill="#f0883e" text-anchor="middle" font-size="9">"cat" and "car" share the c-a prefix path</text>
    <text x="400" y="205" fill="#f0883e" text-anchor="middle" font-size="9">"dog" is a separate branch</text>
  </g>
</svg>

Orange nodes mark `isEndOfWord = true`. `"cat"` and `"car"` share the path `c -> a` before diverging; `"dog"` shares no path with either, since it starts with a different letter.

## 5. Runnable example

```java
// TrieStructure.java
import java.util.HashMap;
import java.util.Map;

public class TrieStructure {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) {
                current = current.children.computeIfAbsent(c, key -> new TrieNode()); // create the child if it does not exist yet
            }
            current.isEndOfWord = true; // mark the path just walked as a complete word
        }
    }

    // Basic: build a trie from a small vocabulary and inspect its shape.
    static void basicLevel() {
        Trie trie = new Trie();
        trie.insert("cat");
        trie.insert("car");
        trie.insert("dog");

        TrieNode afterCa = trie.root.children.get('c').children.get('a');
        System.out.println("basic: node after 'ca' has children -> " + afterCa.children.keySet());
        System.out.println("basic: node after 'ca' is a complete word? -> " + afterCa.isEndOfWord + " (expected false -- 'ca' alone was never inserted)");
    }

    // Intermediate: confirm the shared-prefix structure by counting distinct nodes vs total characters inserted.
    static int countNodes(TrieNode node) {
        int count = 1; // count this node itself
        for (TrieNode child : node.children.values()) count += countNodes(child);
        return count;
    }

    static void intermediateLevel() {
        Trie trie = new Trie();
        String[] words = {"cat", "car", "cart", "dog"};
        for (String w : words) trie.insert(w);

        int totalCharacters = 0;
        for (String w : words) totalCharacters += w.length();

        System.out.println("intermediate: inserted " + java.util.Arrays.toString(words) + " (total chars = " + totalCharacters + ")");
        System.out.println("intermediate: distinct trie nodes (excluding root) -> " + (countNodes(trie.root) - 1)
            + " -- fewer than total chars, thanks to the shared 'ca'/'car' prefix");
    }

    // Advanced: mark and check isEndOfWord correctly distinguishes a prefix from a stored word.
    static void advancedLevel() {
        Trie trie = new Trie();
        trie.insert("car");
        trie.insert("cartoon");

        TrieNode afterCar = trie.root.children.get('c').children.get('a').children.get('r');
        System.out.println("advanced: node after 'car' isEndOfWord -> " + afterCar.isEndOfWord + " (true -- 'car' itself was inserted)");

        TrieNode afterCart = afterCar.children.get('t');
        System.out.println("advanced: node after 'cart' isEndOfWord -> " + afterCart.isEndOfWord + " (false -- 'cart' was never inserted, only 'cartoon')");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TrieStructure.java`, then run `java TrieStructure.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `"cat"`, `"car"`, `"dog"`. After inserting `"cat"`, the path `root -> c -> a -> t` exists, with `t` marked `isEndOfWord`. Inserting `"car"` reuses the existing `c` and `a` nodes (via `computeIfAbsent`, which only creates a node if it is missing) and adds a new `r` child under `a`. The node after `"ca"` therefore has two children, `t` and `r`, but is itself not marked as a complete word, since `"ca"` alone was never inserted.
2. `intermediateLevel()` inserts four words totaling many characters, but counts far fewer distinct trie nodes, because `"cat"`, `"car"`, and `"cart"` all share the `c -> a` prefix path (and `"car"`/`"cart"` also share `c -> a -> r`) — the trie only stores each distinct prefix once, no matter how many words extend it.
3. `advancedLevel()` inserts `"car"` and `"cartoon"` — a case where one stored word is itself a prefix of another. The node after `"car"` is correctly marked `isEndOfWord = true`, while the node after `"cart"` (a prefix of `"cartoon"`, but never inserted on its own) is correctly `false` — proving `isEndOfWord` distinguishes "this exact string is a stored word" from "this is merely a prefix of something longer."

## 7. Gotchas & takeaways

> Gotcha: a node existing on the path is not the same as that prefix being a stored word — always check `isEndOfWord`, not just "did I reach a node without hitting a missing child," or you will treat every prefix of every word as if it were itself a complete word.

- A trie stores strings as root-to-node paths, one character per edge, with shared prefixes sharing the same path.
- `isEndOfWord` (or an equivalent marker) is what distinguishes "this is a complete stored word" from "this is merely a prefix of something longer."
- Prefix and word lookups both cost `O(length of the string)`, independent of how many words are stored — the trie's core advantage over a hash set.
- Related concepts: [Insert / search / startsWith](0129-insert-search-startswith.md), [Trie node with a children map/array](0132-trie-node-with-a-children-map-array.md).
