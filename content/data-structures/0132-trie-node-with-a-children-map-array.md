---
card: data-structures
gi: 132
slug: trie-node-with-a-children-map-array
title: Trie node with a children map/array
---

## 1. What it is

Every trie node needs a way to store its children, keyed by character. The two standard choices are a **fixed-size array** (one slot per possible character, e.g. `children[26]` for lowercase English letters) or a **`Map<Character, TrieNode>`** (only allocating an entry for characters that actually appear).

## 2. Why & when

This choice affects both memory use and lookup speed, and it depends entirely on the alphabet. For a small, fixed alphabet (lowercase English letters), an array gives `O(1)` child lookup via direct indexing, with a small, predictable memory cost per node. For a large or unbounded alphabet (all of Unicode, arbitrary bytes, or when most nodes only ever use a few of many possible characters), a map avoids allocating space for characters that never appear, at the cost of slightly slower lookups (hashing instead of direct indexing).

## 3. Core concept

**Array-backed node.** `TrieNode { TrieNode[] children = new TrieNode[26]; boolean isEndOfWord; }`. To find the child for character `c`, compute `c - 'a'` and index directly: `children[c - 'a']`. This is `O(1)` with a small constant factor (no hashing), but every node — even one with only a single child — allocates all 26 slots.

**Map-backed node.** `TrieNode { Map<Character, TrieNode> children = new HashMap<>(); boolean isEndOfWord; }`. Only characters that actually have a child get an entry. Lookup is `O(1)` on average (hash lookup), but with more overhead per lookup than direct array indexing, and each entry costs more memory than a bare array slot (a `HashMap` entry carries object overhead beyond just the reference).

**The concrete tradeoff.** For a dictionary of lowercase English words, most trie nodes near the root have several children (dense), while most nodes near the leaves have exactly one child (sparse). An array wastes memory on sparse leaf nodes; a map wastes a little speed on dense root-level nodes. In practice, a fixed small alphabet almost always favors the array, since 26 references is a small, bounded, predictable cost.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same trie node with only two actual children shown as a mostly empty 26 slot array on one side, and as a compact two entry map on the other side">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">array-backed: children[26]</text>
    <rect x="20" y="30" width="260" height="26" fill="#161b22" stroke="#8b949e"/>
    <rect x="20" y="30" width="20" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="30" y="47" fill="#79c0ff" text-anchor="middle" font-size="7">a</text>
    <rect x="60" y="30" width="20" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="70" y="47" fill="#79c0ff" text-anchor="middle" font-size="7">t</text>
    <text x="150" y="80" fill="#8b949e" text-anchor="middle" font-size="9">24 of 26 slots are null -- allocated but unused</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">map-backed: HashMap&lt;Character,TrieNode&gt;</text>
    <rect x="400" y="30" width="80" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="440" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">'a' -&gt; node</text>
    <rect x="490" y="30" width="80" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="530" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">'t' -&gt; node</text>
    <text x="480" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">only 2 entries exist -- no wasted slots</text>
  </g>
</svg>

The same node, with only children for `a` and `t`. The array allocates 26 slots regardless (24 unused); the map allocates exactly 2 entries.

## 5. Runnable example

```java
// TrieNodeRepresentations.java
import java.util.HashMap;
import java.util.Map;

public class TrieNodeRepresentations {

    // Basic: array-backed node -- O(1) direct indexing, fixed-size allocation per node.
    static class ArrayTrieNode {
        ArrayTrieNode[] children = new ArrayTrieNode[26];
        boolean isEndOfWord = false;

        void insert(ArrayTrieNode node, String word, int index) {
            if (index == word.length()) { node.isEndOfWord = true; return; }
            int slot = word.charAt(index) - 'a';
            if (node.children[slot] == null) node.children[slot] = new ArrayTrieNode();
            insert(node.children[slot], word, index + 1);
        }
    }

    static void basicLevel() {
        ArrayTrieNode root = new ArrayTrieNode();
        root.insert(root, "cat", 0);

        ArrayTrieNode c = root.children['c' - 'a'];
        System.out.println("basic: array node for 'c' exists -> " + (c != null));
        System.out.println("basic: array node for 'z' (never inserted) -> " + root.children['z' - 'a'] + " (allocated slot, but null)");
    }

    // Intermediate: map-backed node -- only allocates entries for characters actually used.
    static class MapTrieNode {
        Map<Character, MapTrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;

        void insert(MapTrieNode node, String word, int index) {
            if (index == word.length()) { node.isEndOfWord = true; return; }
            char c = word.charAt(index);
            node.children.computeIfAbsent(c, key -> new MapTrieNode());
            insert(node.children.get(c), word, index + 1);
        }
    }

    static void intermediateLevel() {
        MapTrieNode root = new MapTrieNode();
        root.insert(root, "cat", 0);

        System.out.println("intermediate: map node's actual key set -> " + root.children.keySet() + " (only 'c' -- no wasted entries)");
        System.out.println("intermediate: map lookup for 'z' -> " + root.children.get('z') + " (no entry exists at all, not even a null slot)");
    }

    // Advanced: measure the concrete memory-shape difference -- count allocated slots vs actual entries across a small dictionary.
    static int countArraySlots(ArrayTrieNode node) {
        int slots = 26; // every array node always allocates all 26, regardless of how many are used
        for (ArrayTrieNode child : node.children) if (child != null) slots += countArraySlots(child);
        return slots;
    }

    static int countMapEntries(MapTrieNode node) {
        int entries = node.children.size(); // only the entries actually present
        for (MapTrieNode child : node.children.values()) entries += countMapEntries(child);
        return entries;
    }

    static void advancedLevel() {
        ArrayTrieNode arrayRoot = new ArrayTrieNode();
        MapTrieNode mapRoot = new MapTrieNode();
        for (String w : new String[]{"cat", "car", "cot", "dog"}) {
            arrayRoot.insert(arrayRoot, w, 0);
            mapRoot.insert(mapRoot, w, 0);
        }

        System.out.println("advanced: total array slots allocated across the whole trie -> " + countArraySlots(arrayRoot));
        System.out.println("advanced: total map entries actually stored across the whole trie -> " + countMapEntries(mapRoot));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TrieNodeRepresentations.java`, then run `java TrieNodeRepresentations.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `"cat"` into an array-backed trie. The node for `c` is found by direct array indexing (`root.children['c' - 'a']`), no hashing involved. Checking the slot for `'z'` (never inserted) returns `null` — the slot was still allocated as part of the fixed-size array, it is simply unused.
2. `intermediateLevel()` inserts the same word into a map-backed trie. The root's `children.keySet()` shows only `{'c'}` — no entry was ever created for the other 25 possible letters, since `HashMap` only stores keys that are actually inserted.
3. `advancedLevel()` builds both representations from the same four-word dictionary and counts allocated array slots versus actual map entries across every node. The array version's slot count is dominated by `26 * (number of nodes)`, most of them unused; the map version's entry count reflects only the characters actually present — concretely showing the memory-shape difference the two designs produce for the same logical trie.

## 7. Gotchas & takeaways

> Gotcha: an array-backed trie only works cleanly for a small, fixed, known alphabet — extending it to full Unicode would require an enormous per-node array (or a fallback to a map anyway), which erases the array's main advantage.

- An array-backed node gives `O(1)` direct-index child lookup with a small constant factor, at the cost of a fixed per-node allocation regardless of how many children are actually used.
- A map-backed node only allocates entries for characters that appear, at the cost of hashing overhead per lookup.
- The right choice depends on the alphabet size and how sparse the tree's branching actually is — small fixed alphabets favor arrays; large or sparse ones favor maps.
- Related concepts: [Prefix tree (trie) structure](0126-prefix-tree-trie-structure.md), [Memory tradeoffs (array vs HashMap children)](0134-memory-tradeoffs-array-vs-hashmap-children.md).
