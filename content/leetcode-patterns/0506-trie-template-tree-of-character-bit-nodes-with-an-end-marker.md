---
card: leetcode-patterns
gi: 506
slug: trie-template-tree-of-character-bit-nodes-with-an-end-marker
title: Trie — template: tree of character/bit nodes with an end marker
---

## 1. What it is

The trie template is a `TrieNode` class with an array (or map) of children and an "end of word" flag, plus three operations built the same way every time: `insert`, `search` (exact match), and `startsWith` (prefix match). Once memorized, adapting a trie to a new problem is mostly about what extra data you attach to each node.

## 2. Why & when

Use a fixed-size array of children (size 26 for lowercase letters, size 2 for a bit-trie) when the alphabet is small and known — it is faster than a hash map and avoids boxing overhead. Use a `Map<Character, TrieNode>` when the alphabet is large, sparse, or unknown ahead of time (like arbitrary Unicode or mixed-case strings).

## 3. Core concept

**Node structure.** Each `TrieNode` holds `children[26]` (or a map) and a boolean `isEnd`. Some problems attach extra fields (a count, a value, a list of matching words) to support their specific query.

**`insert(word)`.** Start at the root. For each character, compute its index (`c - 'a'`); if `children[index]` is null, create a new `TrieNode` there. Move into that child. After the last character, set `isEnd = true` on the final node.

**`search(word)`.** Same walk as `insert`, but without creating nodes: if any character's child is missing, return `false` immediately. After the full walk, return the final node's `isEnd` flag (a full path without `isEnd` means the word is only a prefix of something else, not a stored word itself).

**`startsWith(prefix)`.** Identical walk to `search`, but return `true` as soon as the full path exists — the `isEnd` flag does not matter, since a prefix does not need to be a complete word.

**Why `search` and `startsWith` differ only in the final check:** both need the same path to exist; the only question is whether that path must end exactly at a stored word (`search`) or may continue further (`startsWith`). This single-flag distinction is what lets a trie answer both kinds of query with almost identical code.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Trie template: insert creates nodes, search and startsWith walk the same path with different final checks">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="200" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="120" y="45" fill="#e6edf3" text-anchor="middle">insert: walk + create missing nodes</text>
    <rect x="20" y="80" width="200" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="120" y="105" fill="#e6edf3" text-anchor="middle">search: walk, fail if missing</text>
    <rect x="20" y="140" width="200" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="120" y="165" fill="#e6edf3" text-anchor="middle">then check node.isEnd</text>
    <rect x="400" y="80" width="200" height="40" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="105" fill="#e6edf3" text-anchor="middle">startsWith: same walk</text>
    <rect x="400" y="140" width="200" height="40" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="165" fill="#e6edf3" text-anchor="middle">path exists = true (isEnd ignored)</text>
  </g>
</svg>

`insert` builds the path; `search` and `startsWith` share the same walk, differing only in the final check.

## 5. Runnable example

The full trie template with all three operations.

```java
// TrieTemplate.java
public class TrieTemplate {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    static class Trie {
        private final TrieNode root = new TrieNode();

        void insert(String word) {
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

        boolean search(String word) {
            TrieNode node = walk(word);
            return node != null && node.isEnd;
        }

        boolean startsWith(String prefix) {
            return walk(prefix) != null;
        }
    }

    public static void main(String[] args) {
        Trie trie = new Trie();
        trie.insert("apple");

        System.out.println(trie.search("apple"));     // true
        System.out.println(trie.search("app"));       // false (only a prefix, not inserted as a word)
        System.out.println(trie.startsWith("app"));   // true

        trie.insert("app");
        System.out.println(trie.search("app"));       // true (now inserted as its own word)
    }
}
```

**How to run:** save as `TrieTemplate.java`, then run `java TrieTemplate.java`.

## 6. Walkthrough

1. `trie.insert("apple")` creates 5 new nodes, one per character, and marks the final `e` node's `isEnd = true`.
2. `trie.search("apple")` walks the same 5 nodes, finds them all present, and checks `isEnd` on the last one — `true`, since it was inserted.
3. `trie.search("app")` walks 3 nodes (`a`, `p`, `p`), all present (they were created as part of inserting "apple"), but the third node's `isEnd` is `false` (no word was ever inserted stopping exactly there) — returns `false`.
4. `trie.startsWith("app")` walks the same 3 nodes and returns `true` as soon as the path exists, without checking `isEnd` at all.
5. After `trie.insert("app")`, that third node's `isEnd` becomes `true`, so `trie.search("app")` now also returns `true`.

## 7. Gotchas & takeaways

> Gotcha: implementing `search` by only checking whether the path exists (like `startsWith` does) incorrectly returns `true` for prefixes that were never inserted as their own word — always check the final node's `isEnd` flag for exact-match search.

- `insert` creates nodes as needed; `search` and `startsWith` only read, never create.
- The only difference between `search` and `startsWith` is the final `isEnd` check — memorize the shared walk once, then branch on that single condition.
- A fixed-size `children[26]` array is simpler and faster than a hash map when the alphabet is small and known in advance.
