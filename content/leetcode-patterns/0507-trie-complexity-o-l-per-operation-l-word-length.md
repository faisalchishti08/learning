---
card: leetcode-patterns
gi: 507
slug: trie-complexity-o-l-per-operation-l-word-length
title: Trie — complexity: O(L) per operation (L = word length)
---

## 1. What it is

This page explains why every core trie operation (`insert`, `search`, `startsWith`) runs in time proportional only to the length of the word or prefix involved, `O(L)`, completely independent of how many other words are stored — and lists the named problems that use the pattern.

## 2. Why & when

Interviewers often follow up a trie solution by asking "what if there are a million words stored — does that slow down a single search?" Explaining why the answer is "no, only the query's own length matters" demonstrates you understand what the tree structure actually buys you, not just that "tries are fast."

## 3. Core concept

**Time — O(L) per operation, where L is the word or prefix length.** Each of `insert`, `search`, and `startsWith` walks exactly one character at a time, moving to a child node with a single array index (or hash map lookup). The walk takes exactly `L` steps for a word of length `L` — it never depends on `n`, the number of words already stored in the trie, because each step only looks at the *current* node's children, not the whole tree.

**Space — O(total characters across all inserted words), worst case.** Every distinct character position, across all inserted words, can create at most one new node. Shared prefixes reuse existing nodes instead of creating new ones, so the actual space used is often far less than the sum of all word lengths — but the worst case (no shared prefixes at all) is still bounded by that sum.

**Contrast with a hash set of words.** A hash set answers `contains(word)` in O(L) too (you must at least hash the whole word), but it cannot answer `startsWith(prefix)` at all without scanning every stored word — turning a prefix check into an O(n · L) operation. The trie's tree structure is what makes prefix queries just as fast as exact-match queries.

**Why n (word count) never appears in the per-operation cost:** at each step of the walk, the trie only examines the current node's children array (a fixed number of slots), never the rest of the tree. Whether the trie stores 10 words or 10 million, looking up one child by its character index takes the same constant time.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A trie search taking exactly L steps regardless of how many other words share the tree">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Searching a 5-letter word takes exactly 5 steps</text>
    <text x="20" y="45" fill="#8b949e">...whether the trie holds 3 words or 3 million:</text>
    <text x="20" y="70" fill="#79c0ff">trie with 3 words: search("apple") -&gt; 5 node visits</text>
    <text x="20" y="90" fill="#79c0ff">trie with 3,000,000 words: search("apple") -&gt; still 5 node visits</text>
    <text x="20" y="120" fill="#f0883e">hash set startsWith check: must scan up to n stored words -&gt; O(n * L)</text>
    <text x="20" y="140" fill="#3fb950">trie startsWith check: still just 5 node visits -&gt; O(L)</text>
  </g>
</svg>

The trie's per-operation cost depends only on the query's length, never on the number of stored words.

## 5. Runnable example

An instrumented trie that counts node visits per operation, confirming the count equals the word length regardless of how many words are already stored.

```java
// TrieComplexity.java
public class TrieComplexity {

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
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.isEnd = true;
        }

        int searchVisitCount(String word) {
            TrieNode node = root;
            int visits = 0;
            for (char c : word.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) return visits;
                node = node.children[index];
                visits++;
            }
            return visits;
        }
    }

    public static void main(String[] args) {
        Trie trie = new Trie();
        String[] words = {"apple", "app", "application", "banana", "band", "bandana"};
        for (String w : words) trie.insert(w);

        System.out.println("trie holds " + words.length + " words");
        System.out.println("search('apple') visits: " + trie.searchVisitCount("apple") + " (word length: 5)");
        System.out.println("search('bandana') visits: " + trie.searchVisitCount("bandana") + " (word length: 7)");

        // insert many more words sharing prefixes; visit count for the same queries stays unchanged
        for (int i = 0; i < 1000; i++) trie.insert("app" + i);
        System.out.println("after inserting 1000 more words:");
        System.out.println("search('apple') visits: " + trie.searchVisitCount("apple") + " (still 5)");
    }
}
```

**How to run:** save as `TrieComplexity.java`, then run `java TrieComplexity.java`.

## 6. Walkthrough

1. The trie starts with 6 words inserted, sharing prefixes like `app` (in "app", "apple", "application") and `ban` (in "banana", "band", "bandana").
2. `searchVisitCount("apple")` walks 5 nodes (`a`, `p`, `p`, `l`, `e`), one per character — exactly the word's length.
3. `searchVisitCount("bandana")` walks 7 nodes, again exactly matching its length.
4. After inserting 1000 more words (all sharing the `app` prefix), the trie has grown substantially in total node count, but `searchVisitCount("apple")` still visits exactly 5 nodes — the extra words all branch off *after* the `apple` path, so they never add work to this particular search.
5. This confirms the O(L) bound holds regardless of how many words share (or don't share) prefixes with the query.

## 7. Gotchas & takeaways

> Gotcha: assuming a trie is "always more memory-efficient" than a hash set is not guaranteed — a trie with many short, unrelated words (no shared prefixes) can use more memory than a hash set storing the same words, since every distinct prefix character gets its own node.

- Time: O(L) for `insert`, `search`, and `startsWith`, where L is the word or prefix length — completely independent of the number of words stored.
- Space: O(total characters across all words) worst case, less when words share prefixes.
- Reference problems that use this pattern: Implement Trie (Prefix Tree), Design Add and Search Words Data Structure, Replace Words, Search Suggestions System, Longest Word in Dictionary, Map Sum Pairs.
