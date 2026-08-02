---
card: data-structures
gi: 127
slug: compressed-trie-radix-tree
title: Compressed trie / radix tree
---

## 1. What it is

A **radix tree** (also called a **compressed trie** or **PATRICIA trie**) is a trie where every node with only one child is merged with that child, so an edge holds a whole substring instead of a single character. This removes the long single-child chains a plain trie forms whenever few words share a branching point.

## 2. Why & when

A plain trie storing `"romane"`, `"romanus"`, and `"romulus"` creates one node per character, including a long unbranching chain for `"rom"` before the words diverge. That wastes memory and adds pointer-chasing overhead for no benefit, since a chain of single-child nodes carries no actual branching decision. A radix tree collapses each such chain into one edge labeled with the whole substring, cutting node count sharply — this matters for large dictionaries, IP routing tables, and version-control-style file path storage, where many keys share long common prefixes.

## 3. Core concept

**The structure's shape.** Instead of one edge per character, each edge is labeled with a **substring** (possibly several characters long). A node only exists where the paths for two or more stored keys actually diverge, or at a stored word's end.

**How it differs from a plain trie.** A plain trie's node for `"rom"` (after inserting `"romane"`, `"romanus"`, `"romulus"`) would be a chain: `r -> o -> m`, three separate nodes, each with exactly one child, before `"roman"` and `"romulus"` finally diverge at the fourth character. A radix tree instead has a single edge labeled `"rom"` directly from the root to the node where `"roman"` and `"romulus"` split — no intermediate single-child nodes at all.

**Insert and search still cost `O(length of the key)`.** Searching now compares against a substring at each edge (not a single character), but the total number of characters compared along any root-to-leaf path is still bounded by the key's length — the compression changes *how many nodes* you visit, not the total *work per character*.

**Splitting an edge on insert.** Inserting a new key that shares only part of an existing edge's substring requires splitting that edge: a new intermediate node is created at the point where the new key and the existing edge diverge, and the edge's remaining substring becomes a new edge below that split point.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A radix tree storing romane, romanus, and romulus, with a single edge labeled rom from the root, then splitting into an-e-a and an-us and ulus branches">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="14" fill="#161b22" stroke="#8b949e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="7">root</text>
    <circle cx="300" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="300" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">*</text>
    <text x="340" y="65" fill="#79c0ff" font-size="9">"rom"</text>
    <line x1="300" y1="44" x2="300" y2="76" stroke="#79c0ff" stroke-width="2"/>
    <circle cx="220" cy="150" r="14" fill="#161b22" stroke="#79c0ff"/><text x="220" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">*</text>
    <circle cx="400" cy="150" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="400" y="154" fill="#e6edf3" text-anchor="middle" font-size="7">ulus*</text>
    <text x="230" y="120" fill="#79c0ff" font-size="9">"an"</text>
    <text x="420" y="120" fill="#79c0ff" font-size="9">"ulus"</text>
    <line x1="290" y1="102" x2="230" y2="138" stroke="#79c0ff" stroke-width="2"/>
    <line x1="310" y1="102" x2="390" y2="138" stroke="#79c0ff" stroke-width="2"/>
    <circle cx="180" cy="200" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="180" y="204" fill="#e6edf3" text-anchor="middle" font-size="6">e*</text>
    <circle cx="260" cy="200" r="14" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="260" y="204" fill="#e6edf3" text-anchor="middle" font-size="6">us*</text>
    <text x="180" y="175" fill="#79c0ff" font-size="8">"e"</text>
    <text x="270" y="175" fill="#79c0ff" font-size="8">"us"</text>
    <line x1="212" y1="162" x2="188" y2="188" stroke="#79c0ff" stroke-width="2"/>
    <line x1="228" y1="162" x2="252" y2="188" stroke="#79c0ff" stroke-width="2"/>
  </g>
</svg>

One edge labeled `"rom"` replaces what would be three single-child nodes in a plain trie; the tree only branches where the stored words actually diverge (`e` vs `us`, and `an` vs `ulus`).

## 5. Runnable example

```java
// RadixTree.java
import java.util.ArrayList;
import java.util.List;

public class RadixTree {

    static class RadixNode {
        String edgeLabel; // the substring on the edge LEADING to this node (empty for the root)
        boolean isEndOfWord = false;
        List<RadixNode> children = new ArrayList<>();
        RadixNode(String edgeLabel) { this.edgeLabel = edgeLabel; }
    }

    RadixNode root = new RadixNode("");

    static int commonPrefixLength(String a, String b) {
        int i = 0;
        while (i < a.length() && i < b.length() && a.charAt(i) == b.charAt(i)) i++;
        return i;
    }

    // Basic: insert, splitting an existing edge when the new key only partially matches it.
    void insert(String word) {
        RadixNode current = root;
        String remaining = word;

        outer:
        while (true) {
            for (RadixNode child : current.children) {
                int common = commonPrefixLength(remaining, child.edgeLabel);
                if (common == 0) continue; // this child shares nothing with what's left of the word -- try the next one

                if (common == child.edgeLabel.length()) { // fully consumes this edge -- descend and keep going
                    remaining = remaining.substring(common);
                    current = child;
                    if (remaining.isEmpty()) { current.isEndOfWord = true; return; }
                    continue outer;
                }

                // partial match: split the edge at the point of divergence
                RadixNode splitNode = new RadixNode(child.edgeLabel.substring(0, common));
                child.edgeLabel = child.edgeLabel.substring(common);
                splitNode.children.add(child);
                current.children.remove(child);
                current.children.add(splitNode);

                remaining = remaining.substring(common);
                if (remaining.isEmpty()) { splitNode.isEndOfWord = true; return; }

                RadixNode newLeaf = new RadixNode(remaining);
                newLeaf.isEndOfWord = true;
                splitNode.children.add(newLeaf);
                return;
            }
            // no existing child shares any prefix with what's left -- add a brand new leaf
            RadixNode newLeaf = new RadixNode(remaining);
            newLeaf.isEndOfWord = true;
            current.children.add(newLeaf);
            return;
        }
    }

    static void basicLevel() {
        RadixTree tree = new RadixTree();
        tree.insert("romane");
        System.out.println("basic: after inserting 'romane', root's single child edge -> \"" + tree.root.children.get(0).edgeLabel + "\"");
    }

    // Intermediate: insert a word that shares only PART of an existing edge, forcing a split.
    static int countNodes(RadixNode node) {
        int count = 1;
        for (RadixNode child : node.children) count += countNodes(child);
        return count;
    }

    static void intermediateLevel() {
        RadixTree tree = new RadixTree();
        tree.insert("romane");
        tree.insert("romanus"); // shares "roman" with "romane", diverges at "e" vs "us"
        tree.insert("romulus"); // shares only "rom" with the existing "roman..." edge

        System.out.println("intermediate: total nodes after inserting romane, romanus, romulus -> " + (countNodes(tree.root) - 1));
        System.out.println("intermediate: root's child edge (shared prefix) -> \"" + tree.root.children.get(0).edgeLabel + "\"");
    }

    // Advanced: search by walking edges (comparing substrings, not single characters).
    static boolean search(RadixNode node, String remaining) {
        if (remaining.isEmpty()) return node.isEndOfWord;
        for (RadixNode child : node.children) {
            if (remaining.startsWith(child.edgeLabel)) {
                return search(child, remaining.substring(child.edgeLabel.length()));
            }
        }
        return false;
    }

    static void advancedLevel() {
        RadixTree tree = new RadixTree();
        for (String w : new String[]{"romane", "romanus", "romulus"}) tree.insert(w);

        System.out.println("advanced: search(\"romanus\") -> " + search(tree.root, "romanus"));
        System.out.println("advanced: search(\"roman\") -> " + search(tree.root, "roman") + " (false -- 'roman' alone was never inserted)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `RadixTree.java`, then run `java RadixTree.java`.

## 6. Walkthrough

1. `basicLevel()` inserts a single word, `"romane"`, into an empty tree. Since there are no existing children to compare against, it becomes one leaf edge labeled with the entire word, `"romane"`.
2. `intermediateLevel()` inserts `"romanus"` next. It shares the prefix `"roman"` with the existing `"romane"` edge, but diverges at the 6th character (`e` vs `u`), so the edge is split: a new intermediate node gets the shared edge `"roman"`, with two children, `"e"` and `"us"`. Inserting `"romulus"` then shares only `"rom"` with that intermediate node's edge, triggering another split, producing the exact three-level shape shown in the diagram. The final node count comes out far lower than a plain trie's per-character node count would give for the same three words.
3. `advancedLevel()`'s `search` walks the tree comparing whole substrings (via `startsWith`) at each step, rather than one character at a time. Searching `"romanus"` matches `"rom"`, then `"an"`, then `"us"`, landing on a node marked `isEndOfWord`, returning `true`. Searching `"roman"` matches `"rom"` and `"an"` but leaves no remaining characters to match against the `"e"`/`"us"` children, so it lands on the `an`-node — which was never itself marked as a complete word, correctly returning `false`.

## 7. Gotchas & takeaways

> Gotcha: implementing edge splitting incorrectly — forgetting to reassign the split-off remainder as a child of the new intermediate node — silently loses the original word that edge represented. Always verify that after a split, every word that used to be reachable is still reachable.

- A radix tree merges chains of single-child trie nodes into one edge holding a substring, cutting node count for dictionaries with long shared prefixes.
- Insert and search still cost `O(length of the key)` in total character comparisons — compression reduces node count, not per-character work.
- Inserting a key that only partially matches an existing edge requires splitting that edge at the point of divergence.
- Related concepts: [Prefix tree (trie) structure](0126-prefix-tree-trie-structure.md), [Ternary search tree](0128-ternary-search-tree.md).
