---
card: data-structures
gi: 128
slug: ternary-search-tree
title: Ternary search tree
---

## 1. What it is

A **ternary search tree (TST)** stores strings like a trie, but each node has exactly **three** children — `left`, `middle`, `right` — instead of one child per possible character. A node holds one character; `left` and `right` lead to nodes with a smaller or larger character at the *same* position, while `middle` advances to the *next* character in the string.

## 2. Why & when

A plain trie node with 26 array slots (for lowercase English letters) wastes memory when most slots are `null` — common for large alphabets like Unicode, or sparse datasets. A TST uses only three references per node, no matter the alphabet size, trading a little more comparison work per character (a binary-search-like left/right step) for much less memory per node — a middle ground between a trie's speed and a hash set's compactness.

## 3. Core concept

**The structure's shape.** Each node holds a character, `left`, `middle`, `right` child references, and an `isEndOfWord` flag. `left`/`right` form a binary-search-tree-like structure *among siblings* at the same character position; `middle` is the only edge that consumes a character and moves to the next position in the string.

**How the invariant makes lookups work.** At each node, compare the target string's current character against the node's character: go `left` if smaller, `right` if larger (still comparing the *same* character position), or `middle` if equal (advancing to the *next* character). This means each node handles a three-way branch, unlike a trie's node, which fans out directly to every possible next character in one step.

**Complexity.** Search and insert cost `O(length of the string)` on average, though a poorly balanced tree (built from characters inserted in sorted order) can push the `left`/`right` chains toward `O(length * alphabet size)` in the worst case — the same skew risk an unbalanced BST has, applied per character position.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ternary search tree node for the letter c with a middle child leading toward the next character, and left and right children for smaller and larger letters at the same position">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="16" fill="#0d1117" stroke="#f0883e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">c</text>
    <circle cx="220" cy="90" r="14" fill="#161b22" stroke="#8b949e"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">a</text>
    <circle cx="300" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="300" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">a</text>
    <circle cx="380" cy="90" r="14" fill="#161b22" stroke="#8b949e"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">o</text>
    <text x="220" y="70" fill="#8b949e" font-size="8">left (smaller)</text>
    <text x="300" y="70" fill="#79c0ff" font-size="8">middle (next char)</text>
    <text x="380" y="70" fill="#8b949e" font-size="8">right (larger)</text>
    <line x1="288" y1="42" x2="228" y2="78" stroke="#8b949e"/>
    <line x1="300" y1="46" x2="300" y2="76" stroke="#79c0ff" stroke-width="2"/>
    <line x1="312" y1="42" x2="372" y2="78" stroke="#8b949e"/>
    <text x="300" y="130" fill="#79c0ff" text-anchor="middle" font-size="9">"c" is the FIRST character of "cat"/"car" (via middle "a") and "cot" (via right "o")</text>
  </g>
</svg>

The root node holds `c`, the first character shared by `"cat"`, `"car"`, and `"cot"`. `middle` leads toward `a` (continuing `"ca..."`), while `right` leads toward a different first-position sibling like `a` (a smaller letter than `c` at the *same* position, for a word like `"ant"`) or `o` (larger, for `"cot"`).

## 5. Runnable example

```java
// TernarySearchTree.java
public class TernarySearchTree {

    static class TSTNode {
        char character;
        TSTNode left, middle, right;
        boolean isEndOfWord = false;
        TSTNode(char character) { this.character = character; }
    }

    TSTNode root;

    // Basic: insert, using left/right for sibling characters and middle to advance through the string.
    TSTNode insert(TSTNode node, String word, int index) {
        char c = word.charAt(index);
        if (node == null) node = new TSTNode(c);

        if (c < node.character) node.left = insert(node.left, word, index);
        else if (c > node.character) node.right = insert(node.right, word, index);
        else if (index + 1 < word.length()) node.middle = insert(node.middle, word, index + 1); // matched -- advance to next char
        else node.isEndOfWord = true; // matched AND this was the last character

        return node;
    }

    void insert(String word) { root = insert(root, word, 0); }

    static void basicLevel() {
        TernarySearchTree tst = new TernarySearchTree();
        tst.insert("cat");
        System.out.println("basic: inserted 'cat' -> root character -> " + tst.root.character);
        System.out.println("basic: root.middle character (2nd letter 'a') -> " + tst.root.middle.character);
    }

    // Intermediate: search, following the same three-way branching rule.
    boolean search(TSTNode node, String word, int index) {
        if (node == null) return false;
        char c = word.charAt(index);

        if (c < node.character) return search(node.left, word, index);
        if (c > node.character) return search(node.right, word, index);
        if (index + 1 < word.length()) return search(node.middle, word, index + 1);
        return node.isEndOfWord;
    }

    boolean search(String word) { return search(root, word, 0); }

    static void intermediateLevel() {
        TernarySearchTree tst = new TernarySearchTree();
        for (String w : new String[]{"cat", "car", "cot"}) tst.insert(w);

        System.out.println("intermediate: search('cat') -> " + tst.search("cat"));
        System.out.println("intermediate: search('cot') -> " + tst.search("cot"));
        System.out.println("intermediate: search('ca') -> " + tst.search("ca") + " (false -- 'ca' alone was never inserted)");
        System.out.println("intermediate: search('dog') -> " + tst.search("dog"));
    }

    // Advanced: a realistic task -- collect all stored words, confirming the left/right/middle shape stores everything correctly.
    void collect(TSTNode node, StringBuilder prefix, java.util.List<String> results) {
        if (node == null) return;
        collect(node.left, prefix, results);

        prefix.append(node.character);
        if (node.isEndOfWord) results.add(prefix.toString());
        collect(node.middle, prefix, results);
        prefix.deleteCharAt(prefix.length() - 1); // backtrack before returning to the caller

        collect(node.right, prefix, results);
    }

    static void advancedLevel() {
        TernarySearchTree tst = new TernarySearchTree();
        for (String w : new String[]{"cat", "car", "cot", "dog"}) tst.insert(w);

        java.util.List<String> allWords = new java.util.ArrayList<>();
        tst.collect(tst.root, new StringBuilder(), allWords);
        java.util.Collections.sort(allWords);
        System.out.println("advanced: all stored words -> " + allWords);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TernarySearchTree.java`, then run `java TernarySearchTree.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `"cat"` into an empty tree. The root becomes `c` (index 0). Since it is a fresh match at this position, the code advances via `middle` to index `1`, creating a new node for `a`. `root.middle.character` prints `a`, confirming the middle link advances through the string rather than branching sideways.
2. `intermediateLevel()` inserts `"cat"`, `"car"`, `"cot"`. `search("ca")` walks `c` (match, advance), `a` (match, but `index+1 == word.length()`, so it checks `isEndOfWord` on the `a` node) — which is `false`, since `"ca"` was never inserted on its own, only as a prefix of `"cat"`/`"car"`. `search("dog")` fails at the very first comparison: `d > c`, so it follows `right`, but no `right` child exists yet (nothing larger than `c` was ever inserted at the first position), returning `false` immediately.
3. `advancedLevel()`'s `collect` performs an in-order-style traversal: visit `left` (smaller siblings), then this node (checking `isEndOfWord` and recursing into `middle` to continue building longer words), then `right` (larger siblings) — with `prefix` acting as a shared, backtracked buffer across all four stored words. The result correctly lists all four words in sorted order.

## 7. Gotchas & takeaways

> Gotcha: `left`/`right` compare the character at the **current** position only — they never advance the string index. Only `middle` advances. Confusing this (e.g. advancing the index on a `left`/`right` step) silently corrupts every lookup past the first mismatched character.

- A TST node has three children (`left`, `right`, `middle`) instead of one-per-character, trading memory for a per-character comparison step.
- `left`/`right` compare siblings at the same position (like a BST); `middle` is the only edge that consumes a character and moves forward.
- Average-case cost is `O(length of the string)`, but a poorly balanced tree (from sorted-order insertion) can degrade toward `O(length * alphabet size)`, mirroring an unbalanced BST's skew risk.
- Related concepts: [Prefix tree (trie) structure](0126-prefix-tree-trie-structure.md), [Compressed trie / radix tree](0127-compressed-trie-radix-tree.md).
