---
card: data-structures
gi: 112
slug: why-balancing-matters-skew-to-o-n
title: Why balancing matters (skew to O(n))
---

## 1. What it is

A binary search tree (BST) only guarantees an ordering rule, not a shape. Nothing stops one that has been fed sorted or near-sorted data from becoming a long, lopsided chain — in the worst case, every node has exactly one child, and the tree is really just a linked list wearing a tree's clothing.

## 2. Why & when

Search, insert, and delete on a BST all cost `O(height)`. A balanced tree keeps height at `O(log n)`, so these operations stay fast. A skewed tree can have height `O(n)`, which silently turns every operation into a linear scan — the exact cost a BST was supposed to avoid. This matters whenever input arrives in a predictable order (sorted logs, sequential IDs, alphabetically sorted names), which is common enough in practice that unbalanced BSTs are rarely used directly in production code.

## 3. Core concept

**How the skew happens.** A plain BST insert always places a new value by comparing it down from the root and attaching it as a leaf — it never repositions existing nodes. If you insert `1, 2, 3, 4, 5` in that order, each new value is larger than everything already in the tree, so each one becomes the right child of the previous one. The result is a straight rightward chain of height `5`, not a bushy tree of height `~3`.

**Height directly drives cost.** Searching for a value walks from the root down one path to a `null` child or a match — that path's length is bounded by the tree's height. A balanced tree of `n` nodes has height `O(log n)`; a fully skewed tree has height `O(n)`. So the same `search` code, unchanged, runs in `O(log n)` on one input order and `O(n)` on another — the algorithm did not change, only the shape did.

**The fix: rebalance after every change.** Self-balancing trees like an [AVL tree](0110-avl-trees-rotations.md) or a [red-black tree](0111-red-black-trees.md) restructure themselves — using rotations — immediately after each insert or delete, so the height never drifts far from `log2(n)`, regardless of the order values arrive in.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two trees holding the same five values: a skewed chain of height five from sorted insertion, versus a balanced tree of height three">
  <g font-family="sans-serif" font-size="11">
    <text x="130" y="16" fill="#f0883e" text-anchor="middle">insert 1,2,3,4,5 in order -&gt; skewed, height 5</text>
    <circle cx="130" cy="35" r="14" fill="#161b22" stroke="#f0883e"/><text x="130" y="39" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <circle cx="160" cy="65" r="14" fill="#161b22" stroke="#f0883e"/><text x="160" y="69" fill="#e6edf3" text-anchor="middle" font-size="8">2</text>
    <circle cx="190" cy="95" r="14" fill="#161b22" stroke="#f0883e"/><text x="190" y="99" fill="#e6edf3" text-anchor="middle" font-size="8">3</text>
    <circle cx="220" cy="125" r="14" fill="#161b22" stroke="#f0883e"/><text x="220" y="129" fill="#e6edf3" text-anchor="middle" font-size="8">4</text>
    <circle cx="250" cy="155" r="14" fill="#161b22" stroke="#f0883e"/><text x="250" y="159" fill="#e6edf3" text-anchor="middle" font-size="8">5</text>
    <line x1="140" y1="45" x2="150" y2="55" stroke="#8b949e"/>
    <line x1="170" y1="75" x2="180" y2="85" stroke="#8b949e"/>
    <line x1="200" y1="105" x2="210" y2="115" stroke="#8b949e"/>
    <line x1="230" y1="135" x2="240" y2="145" stroke="#8b949e"/>
    <text x="190" y="200" fill="#f0883e" text-anchor="middle" font-size="9">search(5) visits ALL 5 nodes -- O(n)</text>

    <text x="480" y="16" fill="#79c0ff" text-anchor="middle">same values, balanced -&gt; height 3</text>
    <circle cx="480" cy="35" r="16" fill="#0d1117" stroke="#79c0ff"/><text x="480" y="39" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <circle cx="440" cy="85" r="14" fill="#161b22" stroke="#79c0ff"/><text x="440" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <circle cx="520" cy="85" r="14" fill="#161b22" stroke="#79c0ff"/><text x="520" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">4</text>
    <circle cx="460" cy="135" r="12" fill="#161b22" stroke="#79c0ff"/><text x="460" y="139" fill="#e6edf3" text-anchor="middle" font-size="7">2</text>
    <circle cx="540" cy="135" r="12" fill="#161b22" stroke="#79c0ff"/><text x="540" y="139" fill="#e6edf3" text-anchor="middle" font-size="7">5</text>
    <line x1="468" y1="45" x2="452" y2="73" stroke="#8b949e"/>
    <line x1="492" y1="45" x2="508" y2="73" stroke="#8b949e"/>
    <line x1="448" y1="97" x2="456" y2="123" stroke="#8b949e"/>
    <line x1="528" y1="97" x2="536" y2="123" stroke="#8b949e"/>
    <text x="480" y="200" fill="#79c0ff" text-anchor="middle" font-size="9">search(5) visits only 2 nodes -- O(log n)</text>
  </g>
</svg>

The same five values, in the same BST rule, form either a five-deep chain or a three-deep balanced tree — shape alone changes search cost from `O(n)` to `O(log n)`.

## 5. Runnable example

```java
// SkewVsBalanced.java
public class SkewVsBalanced {

    static class Node {
        int value;
        Node left, right;
        Node(int value) { this.value = value; }
    }

    static Node insertPlainBst(Node node, int value) {
        if (node == null) return new Node(value);
        if (value < node.value) node.left = insertPlainBst(node.left, value);
        else if (value > node.value) node.right = insertPlainBst(node.right, value);
        return node;
    }

    static int height(Node node) {
        if (node == null) return 0;
        return 1 + Math.max(height(node.left), height(node.right));
    }

    static int comparisonsToFind(Node node, int target, int count) {
        if (node == null) return count; // not found; count reflects how far the search walked
        if (node.value == target) return count + 1;
        return target < node.value
            ? comparisonsToFind(node.left, target, count + 1)
            : comparisonsToFind(node.right, target, count + 1);
    }

    // Basic: insert already-sorted data -- the worst case for a plain BST.
    static void basicLevel() {
        Node root = null;
        for (int v = 1; v <= 5; v++) root = insertPlainBst(root, v); // sorted input -> guaranteed skew

        System.out.println("basic: inserted 1..5 sorted, height -> " + height(root) + " (expected worst case: 5)");
        System.out.println("basic: comparisons to find 5 -> " + comparisonsToFind(root, 5, 0));
    }

    // Intermediate: the SAME values, inserted in an order that happens to build a balanced tree, for comparison.
    static void intermediateLevel() {
        Node root = null;
        for (int v : new int[]{3, 1, 4, 2, 5}) root = insertPlainBst(root, v); // middle-first order -> bushy tree

        System.out.println("intermediate: same 5 values, balanced insertion order, height -> " + height(root));
        System.out.println("intermediate: comparisons to find 5 -> " + comparisonsToFind(root, 5, 0));
    }

    // Advanced: scale up to show the gap between O(log n) and O(n) growing sharply with size.
    static void advancedLevel() {
        int n = 10000;
        Node sortedRoot = null;
        for (int v = 1; v <= n; v++) sortedRoot = insertPlainBst(sortedRoot, v); // fully sorted -> a chain of height n

        System.out.println("advanced: n=" + n + " sorted inserts, height -> " + height(sortedRoot) + " (linear in n)");
        System.out.println("advanced: log2(" + n + ") ~= 13 -- a balanced tree would stay near that height instead");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SkewVsBalanced.java`, then run `java SkewVsBalanced.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `1, 2, 3, 4, 5` in order. Each value is larger than every node already in the tree, so `insertPlainBst` always recurses into `node.right` and attaches the new value as a right child at the bottom. The result is a straight chain, and `height` correctly reports `5`. Finding `5` requires walking past `1, 2, 3, 4` first — `5` comparisons for `5` values, the signature of `O(n)` behavior.
2. `intermediateLevel()` inserts the exact same five values, but in the order `3, 1, 4, 2, 5` — the middle value first. `3` becomes the root; `1` and `4` split into its left and right subtrees; `2` and `5` fill in as leaves. The resulting height is `3`, and finding `5` now takes only `2` comparisons (`3 -> 4 -> 5`), because the tree fans out instead of chaining.
3. `advancedLevel()` scales the sorted-insertion case up to `10,000` values. The chain's height grows to `10,000` — strictly linear — while `log2(10000) ≈ 13` shows how much shorter a balanced tree's height would stay. The gap between the two grows without bound as `n` increases, which is exactly why production ordered structures never leave balancing to chance.

## 7. Gotchas & takeaways

> Gotcha: the danger is not "random bad luck" — it is *predictable* input order (already-sorted data, sequential timestamps, auto-incrementing IDs) that reliably triggers the worst case, because real-world data is often already sorted or nearly sorted before it reaches your tree.

- A BST's height depends entirely on insertion order, not on the values themselves — the same values can produce height `O(log n)` or `O(n)` depending on the order they arrive in.
- Every BST operation costs `O(height)`, so an unbounded height silently degrades every operation to linear time, with no error or warning.
- Self-balancing trees (AVL, red-black) fix this by rebalancing after every insert and delete, guaranteeing `O(log n)` height regardless of input order.
- Related concepts: [AVL trees & rotations](0110-avl-trees-rotations.md), [Red-black trees](0111-red-black-trees.md), [BST insert / search / delete](0103-bst-insert-search-delete.md).
