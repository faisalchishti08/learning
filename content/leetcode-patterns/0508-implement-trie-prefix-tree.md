---
card: leetcode-patterns
gi: 508
slug: implement-trie-prefix-tree
title: Implement Trie (Prefix Tree)
---

## 1. What it is

Implement a `Trie` class with three methods: `insert(word)` adds a word; `search(word)` returns whether the exact word was inserted; `startsWith(prefix)` returns whether any inserted word begins with `prefix`. Example: insert `"apple"`; `search("apple")` → `true`; `search("app")` → `false`; `startsWith("app")` → `true`.

## 2. Why & when

This is the direct, foundational implementation of the [trie template](0506-trie-template-tree-of-character-bit-nodes-with-an-end-marker.md) — every other trie problem in this section builds on exactly this structure. Constraints: up to 30,000 total operations, words made of lowercase English letters.

## 3. Core concept

**Key idea:** each `TrieNode` has a fixed-size array of 26 children (one per lowercase letter) and an `isEnd` boolean. `insert` walks the word, creating any missing child nodes, and marks `isEnd` on the final node. `search` and `startsWith` share an identical walk; `search` additionally requires the final node's `isEnd` to be `true`.

**Steps:**
1. `insert(word)`: start at the root; for each character, compute `index = c - 'a'`; create `children[index]` if missing; move into it. Mark the last node's `isEnd = true`.
2. `search(word)`: walk the same way; if any child is missing, return `false`. After the walk, return the final node's `isEnd`.
3. `startsWith(prefix)`: identical walk to `search`, but return `true` as soon as the full path exists, ignoring `isEnd`.

**Why a fixed-size array (not a hash map) is the right choice here:** the alphabet is fixed and small (26 lowercase letters), so a direct array index is both simpler and faster than hashing a character — no hash computation or collision handling needed.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting apple then querying search and startsWith">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">insert("apple")</text>
    <text x="20" y="45" fill="#8b949e">root -&gt; a -&gt; p -&gt; p -&gt; l -&gt; e(isEnd=true)</text>
    <text x="20" y="75" fill="#79c0ff">search("apple"): walk all 5 nodes, last isEnd=true -&gt; true</text>
    <text x="20" y="100" fill="#f0883e">search("app"): walk 3 nodes (all exist), but that node's isEnd=false -&gt; false</text>
    <text x="20" y="125" fill="#3fb950">startsWith("app"): walk 3 nodes, path exists -&gt; true (isEnd ignored)</text>
  </g>
</svg>

`search` requires both the path AND `isEnd`; `startsWith` only requires the path.

## 5. Runnable example

```java
// Trie.java
public class Trie {

    private static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    private final TrieNode root;

    public Trie() {
        root = new TrieNode();
    }

    public void insert(String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) {
                node.children[index] = new TrieNode();
            }
            node = node.children[index];
        }
        node.isEnd = true;
    }

    private TrieNode walk(String s) {
        TrieNode node = root;
        for (char c : s.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) return null;
            node = node.children[index];
        }
        return node;
    }

    public boolean search(String word) {
        TrieNode node = walk(word);
        return node != null && node.isEnd;
    }

    public boolean startsWith(String prefix) {
        return walk(prefix) != null;
    }

    public static void main(String[] args) {
        Trie trie = new Trie();
        trie.insert("apple");
        System.out.println(trie.search("apple"));   // true
        System.out.println(trie.search("app"));     // false
        System.out.println(trie.startsWith("app")); // true
        trie.insert("app");
        System.out.println(trie.search("app"));     // true
    }
}
```

**How to run:** save as `Trie.java`, then run `java Trie.java`.

## 6. Walkthrough

Trace the sequence of calls `insert("apple")`, `search("apple")`, `search("app")`, `startsWith("app")`, `insert("app")`, `search("app")`:

| call | path walked | node created? | isEnd check | result |
|---|---|---|---|---|
| insert("apple") | a,p,p,l,e | all 5 created | mark e.isEnd=true | — |
| search("apple") | a,p,p,l,e | none (all exist) | e.isEnd=true | true |
| search("app") | a,p,p | none (exist, shared with "apple") | p(2nd).isEnd=false | false |
| startsWith("app") | a,p,p | none | not checked | true |
| insert("app") | a,p,p | none (exist) | mark p(2nd).isEnd=true | — |
| search("app") | a,p,p | none | p(2nd).isEnd=true (now) | true |

## 7. Gotchas & takeaways

> Gotcha: reusing the same `walk` helper for both `search` and `startsWith` is correct and encouraged — but forgetting to check `isEnd` in `search` (copy-pasting `startsWith`'s logic) silently turns every prefix into a "found" word.

- This is the reference implementation every other trie problem in this section extends or specializes.
- A fixed `children[26]` array beats a hash map here, since the alphabet is small and known.
- Time: O(L) for every operation, where L is the word or prefix length; space: O(total characters inserted), less when words share prefixes.
