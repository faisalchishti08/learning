---
card: data-structures
gi: 134
slug: memory-tradeoffs-array-vs-hashmap-children
title: Memory tradeoffs (array vs HashMap children)
---

## 1. What it is

This is the decision problem introduced in [Trie node with a children map/array](0132-trie-node-with-a-children-map-array.md): given a specific dataset and alphabet, should a trie node's children be stored in a fixed-size array or a `HashMap`? The right answer depends on alphabet size, tree density (branching factor), and how many nodes the trie is expected to hold.

## 2. Why & when

Picking the wrong representation for a large trie can waste enormous amounts of memory, or slow down every lookup. A dictionary of millions of lowercase English words, built with array-backed nodes, allocates 26 references at every single node — including the many nodes near the leaves that only ever have one child. Knowing when that tradeoff is worth it (versus when a map's per-character allocation wins) is a practical system-design skill, not just a trie implementation detail.

## 3. Core concept

**The decision criteria.**

- **Alphabet size:** a small, fixed alphabet (26 lowercase letters, digits, DNA bases) favors arrays — the fixed per-node cost is small and bounded. A large or unbounded alphabet (full Unicode, arbitrary bytes) makes arrays impractical; maps are the only reasonable choice.
- **Branching density:** if most nodes use most of the alphabet's slots (dense branching, common near the root of a trie built from a large vocabulary), arrays waste little and gain speed. If most nodes use only one or two children (sparse branching, common near the leaves, or in tries over long unique identifiers), maps waste much less memory.
- **Lookup speed requirements:** array indexing is unconditionally `O(1)` with a tiny constant factor (no hashing, no bucket lookup). A `HashMap` lookup is `O(1)` on average but with real per-call overhead (computing a hash, resolving a bucket) — for extremely hot code paths (e.g. a compiler's symbol table), that difference can matter.

**A middle ground: hybrid nodes.** Some production tries switch representations *per node*, based on how many children that specific node actually has — a node with many children uses a small array or a bitset for `O(1)` access, while a node with few children uses a compact structure (a short sorted list, checked linearly, or a sparse map). This adapts to the tree's actual density instead of committing to one representation everywhere.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decision tree: small fixed alphabet plus dense branching favors arrays; large or sparse cases favor a HashMap; mixed density favors a hybrid per node choice">
  <g font-family="sans-serif" font-size="11">
    <rect x="260" y="10" width="160" height="30" fill="#161b22" stroke="#8b949e"/><text x="340" y="30" fill="#e6edf3" text-anchor="middle" font-size="9">alphabet size?</text>
    <text x="180" y="60" fill="#8b949e" font-size="9">small, fixed</text>
    <text x="480" y="60" fill="#8b949e" font-size="9">large / unbounded</text>
    <line x1="290" y1="40" x2="200" y2="75" stroke="#8b949e"/>
    <line x1="390" y1="40" x2="480" y2="75" stroke="#8b949e"/>
    <rect x="120" y="80" width="160" height="30" fill="#161b22" stroke="#79c0ff"/><text x="200" y="100" fill="#e6edf3" text-anchor="middle" font-size="9">branching density?</text>
    <rect x="400" y="80" width="160" height="30" fill="#0d1117" stroke="#f0883e"/><text x="480" y="100" fill="#e6edf3" text-anchor="middle" font-size="9">use HashMap</text>
    <text x="120" y="145" fill="#79c0ff" font-size="9">dense -&gt; array</text>
    <text x="260" y="145" fill="#79c0ff" font-size="9">sparse -&gt; HashMap</text>
    <line x1="170" y1="110" x2="120" y2="135" stroke="#8b949e"/>
    <line x1="230" y1="110" x2="260" y2="135" stroke="#8b949e"/>
    <text x="340" y="180" fill="#8b949e" text-anchor="middle" font-size="9">mixed density across the tree -&gt; hybrid: array/bitset for dense nodes, compact map for sparse ones</text>
  </g>
</svg>

Choose by alphabet size first (small/fixed vs large/unbounded), then by how densely each node actually branches — with a hybrid approach available for trees where density varies a lot by depth.

## 5. Runnable example

```java
// MemoryTradeoffsDemo.java
import java.util.HashMap;
import java.util.Map;

public class MemoryTradeoffsDemo {

    interface TrieNode {
        TrieNode getChild(char c);
        void setChild(char c, TrieNode node);
        boolean isEndOfWord();
        void setEndOfWord(boolean value);
    }

    static class ArrayNode implements TrieNode {
        TrieNode[] children = new TrieNode[26]; // fixed cost: always 26 references, used or not
        boolean end;
        public TrieNode getChild(char c) { return children[c - 'a']; }
        public void setChild(char c, TrieNode node) { children[c - 'a'] = node; }
        public boolean isEndOfWord() { return end; }
        public void setEndOfWord(boolean value) { end = value; }
    }

    static class MapNode implements TrieNode {
        Map<Character, TrieNode> children = new HashMap<>(); // variable cost: one entry per ACTUAL child
        boolean end;
        public TrieNode getChild(char c) { return children.get(c); }
        public void setChild(char c, TrieNode node) { children.put(c, node); }
        public boolean isEndOfWord() { return end; }
        public void setEndOfWord(boolean value) { end = value; }
    }

    // Basic: build the SAME dictionary using both representations, through one shared insert routine.
    static void insert(TrieNode root, String word, java.util.function.Supplier<TrieNode> factory) {
        TrieNode current = root;
        for (char c : word.toCharArray()) {
            TrieNode next = current.getChild(c);
            if (next == null) { next = factory.get(); current.setChild(c, next); }
            current = next;
        }
        current.setEndOfWord(true);
    }

    static void basicLevel() {
        TrieNode arrayRoot = new ArrayNode();
        TrieNode mapRoot = new MapNode();
        insert(arrayRoot, "cat", ArrayNode::new);
        insert(mapRoot, "cat", MapNode::new);

        System.out.println("basic: array root's child for 'c' exists -> " + (arrayRoot.getChild('c') != null));
        System.out.println("basic: map root's child for 'c' exists -> " + (mapRoot.getChild('c') != null));
    }

    // Intermediate: count total allocated "child slots" for each representation, on a SPARSE dictionary (long unique IDs).
    static int countArraySlots(TrieNode node) {
        if (!(node instanceof ArrayNode arrayNode)) return 0;
        int total = 26;
        for (TrieNode child : arrayNode.children) if (child != null) total += countArraySlots(child);
        return total;
    }

    static int countMapEntries(TrieNode node) {
        if (!(node instanceof MapNode mapNode)) return 0;
        int total = mapNode.children.size();
        for (TrieNode child : mapNode.children.values()) total += countMapEntries(child);
        return total;
    }

    static void intermediateLevel() {
        String[] sparseIds = {"a1b2c3d4e5", "f6g7h8i9j0", "k1l2m3n4o5"}; // long, mostly-unique paths -- sparse branching

        TrieNode arrayRoot = new ArrayNode();
        TrieNode mapRoot = new MapNode();
        for (String id : sparseIds) { insert(arrayRoot, id.replaceAll("[^a-z]", "a"), ArrayNode::new); insert(mapRoot, id.replaceAll("[^a-z]", "a"), MapNode::new); }

        System.out.println("intermediate: sparse dataset -- array slots -> " + countArraySlots(arrayRoot) + ", map entries -> " + countMapEntries(mapRoot));
        System.out.println("intermediate: map uses far fewer allocated references for this sparse, long-path data");
    }

    // Advanced: the OPPOSITE case -- a dense dictionary where most nodes near the root use most of the alphabet.
    static void advancedLevel() {
        TrieNode arrayRoot = new ArrayNode();
        TrieNode mapRoot = new MapNode();
        String[] denseWords = new String[26];
        for (int i = 0; i < 26; i++) denseWords[i] = "" + (char) ('a' + i) + "x"; // every letter used as a first character

        for (String w : denseWords) { insert(arrayRoot, w, ArrayNode::new); insert(mapRoot, w, MapNode::new); }

        System.out.println("advanced: dense dataset (root has all 26 children) -- array slots -> " + countArraySlots(arrayRoot)
            + ", map entries -> " + countMapEntries(mapRoot));
        System.out.println("advanced: with dense branching, the map's entry count approaches the array's slot count -- less of an advantage");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MemoryTradeoffsDemo.java`, then run `java MemoryTradeoffsDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds the same one-word dictionary using both an `ArrayNode`-backed and `MapNode`-backed trie, confirming both correctly store `"cat"` and can look up its first character's child.
2. `intermediateLevel()` inserts a sparse dataset — long, mostly-unique strings where each node typically has just one child. The array version still allocates `26` references at every node, giving a large total slot count; the map version's entry count is much closer to the actual number of characters inserted, since it never allocates for the 25 characters that never appear at each node. This is the scenario where a map clearly wins on memory.
3. `advancedLevel()` inserts the opposite case: 26 two-letter words, one starting with each letter of the alphabet, so the root node uses all 26 possible children (fully dense at that one node). Here the map's entry count for the root approaches the array's fixed 26-slot cost — the map's memory advantage shrinks as branching density increases, confirming the tradeoff is genuinely data-dependent, not a universal rule.

## 7. Gotchas & takeaways

> Gotcha: the "right" representation is not fixed — it depends on the *actual* data the trie will hold. Benchmarking or estimating with representative data (not just a small example) is the only reliable way to choose, since the same trie shape can favor either representation depending on alphabet size and branching density.

- Small, fixed alphabet + dense branching favors arrays: `O(1)` direct indexing, small fixed per-node cost.
- Large or unbounded alphabet, or sparse branching, favors a `HashMap`: entries scale with actual children present, not with alphabet size.
- Some production tries use hybrid nodes, choosing array or map per node based on that node's own branching factor.
- Related concepts: [Trie node with a children map/array](0132-trie-node-with-a-children-map-array.md), [Prefix tree (trie) structure](0126-prefix-tree-trie-structure.md).
