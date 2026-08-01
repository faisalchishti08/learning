---
card: data-structures
gi: 97
slug: tree-terminology-root-height-depth-leaf
title: 'Tree terminology (root, height, depth, leaf)'
---

## 1. What it is

A **tree** is a hierarchical structure of nodes, where each node has at most one **parent** and any number of **children**, starting from a single node with no parent called the **root**. A node with no children is a **leaf**. Every other node is an **internal node**. This vocabulary is the shared language for every tree topic that follows.

## 2. Why & when

Precise terminology matters because "height" and "depth" are easy to confuse, and off-by-one errors in tree algorithms often trace back to exactly that confusion. Getting these definitions solid before writing traversal or balancing code prevents a whole class of bugs where an algorithm is "one level off."

## 3. Core concept

**Root, parent, child, leaf.** The **root** is the single node with no parent — the starting point of the whole tree. A node's **children** are the nodes directly below it, connected by an edge. A **leaf** is a node with zero children. A node that is neither the root nor a leaf is an **internal node**.

**Depth of a node.** The **depth** of a node is the number of edges on the path from the root down to that node. The root itself has depth `0`. A child of the root has depth `1`, and so on — depth counts *downward from the root, to* the node.

**Height of a node, and height of the tree.** The **height** of a node is the number of edges on the longest path from that node *down* to a leaf. A leaf has height `0`. The **height of the tree** is the height of its root — the longest root-to-leaf path in the whole tree.

**Why the distinction matters for algorithms.** Depth is naturally computed top-down (you know a node's depth once you know its parent's depth, plus one) — this is how depth is tracked during a traversal that starts at the root. Height is naturally computed bottom-up (you need to know both children's heights before you can compute a node's own height) — this is why height is typically computed with a post-order-style recursive function that returns a value up from the leaves.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small tree with root A at depth 0, children B and C at depth 1, and grandchildren D, E, F at depth 2, with height labeled from each node down to the deepest leaf below it">
  <g font-family="sans-serif" font-size="11">
    <circle cx="320" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="320" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <text x="360" y="34" fill="#f0883e" font-size="9">root, depth 0, height 2</text>
    <circle cx="220" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <text x="140" y="94" fill="#79c0ff" font-size="9">depth 1, height 1</text>
    <circle cx="420" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="420" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <text x="460" y="94" fill="#79c0ff" font-size="9">depth 1, height 0 (leaf)</text>
    <circle cx="170" cy="150" r="18" fill="#161b22" stroke="#8b949e"/><text x="170" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <circle cx="270" cy="150" r="18" fill="#161b22" stroke="#8b949e"/><text x="270" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">E</text>
    <text x="220" y="190" fill="#a5d6ff" font-size="9" text-anchor="middle">D, E: depth 2, height 0 (leaves)</text>
    <line x1="308" y1="42" x2="232" y2="78" stroke="#8b949e"/>
    <line x1="332" y1="42" x2="408" y2="78" stroke="#8b949e"/>
    <line x1="208" y1="102" x2="180" y2="138" stroke="#8b949e"/>
    <line x1="232" y1="102" x2="260" y2="138" stroke="#8b949e"/>
  </g>
</svg>

`A` is the root (depth `0`). `C` is a leaf at depth `1`. `D` and `E` are leaves at depth `2`. The tree's height is `2` — the longest root-to-leaf path, `A -> B -> D` (or `A -> B -> E`).

## 5. Runnable example

```java
// TreeTerminologyDemo.java
public class TreeTerminologyDemo {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
    }

    // Basic: compute a node's depth by walking DOWN from the root, counting edges.
    static int depthOf(TreeNode root, TreeNode target, int currentDepth) {
        if (root == null) return -1; // not found on this path
        if (root == target) return currentDepth;
        int leftResult = depthOf(root.left, target, currentDepth + 1);
        if (leftResult != -1) return leftResult;
        return depthOf(root.right, target, currentDepth + 1);
    }

    static void basicLevel() {
        TreeNode a = new TreeNode(1);
        a.left = new TreeNode(2);
        a.right = new TreeNode(3);
        a.left.left = new TreeNode(4);

        System.out.println("basic: depth of root (A) -> " + depthOf(a, a, 0));
        System.out.println("basic: depth of a.left.left (D) -> " + depthOf(a, a.left.left, 0));
    }

    // Intermediate: compute HEIGHT by recursing DOWN to leaves first, then combining results on the way back up.
    static int heightOf(TreeNode node) {
        if (node == null) return -1; // convention: an empty subtree has height -1, so a single leaf node has height 0
        int leftHeight = heightOf(node.left);   // must know children's heights FIRST
        int rightHeight = heightOf(node.right); // (this is why height is bottom-up, unlike depth)
        return 1 + Math.max(leftHeight, rightHeight);
    }

    static boolean isLeaf(TreeNode node) {
        return node != null && node.left == null && node.right == null;
    }

    static void intermediateLevel() {
        TreeNode a = new TreeNode(1);
        a.left = new TreeNode(2);
        a.right = new TreeNode(3);
        a.left.left = new TreeNode(4);

        System.out.println("intermediate: height of whole tree (from root) -> " + heightOf(a));
        System.out.println("intermediate: height of a.right (leaf C) -> " + heightOf(a.right));
        System.out.println("intermediate: isLeaf(a.right) -> " + isLeaf(a.right));
        System.out.println("intermediate: isLeaf(a) -> " + isLeaf(a));
    }

    // Advanced: confirm depth (top-down) and height (bottom-up) give DIFFERENT numbers for the same node, on purpose.
    static void advancedLevel() {
        TreeNode a = new TreeNode(1);
        a.left = new TreeNode(2);
        a.left.left = new TreeNode(3);
        a.left.left.left = new TreeNode(4); // a long chain: A -> B -> C -> D

        TreeNode b = a.left;
        System.out.println("advanced: node B's depth (edges from root DOWN to B) -> " + depthOf(a, b, 0));
        System.out.println("advanced: node B's height (edges from B DOWN to its deepest leaf) -> " + heightOf(b));
        System.out.println("advanced: these are DIFFERENT numbers on purpose -- depth looks up toward the root, height looks down toward leaves");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TreeTerminologyDemo.java`, then run `java TreeTerminologyDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds `A(root) -> B, C`, with `B -> D`. `depthOf` walks from the root, incrementing a counter on every step down, until it finds the target — the root's own depth is `0`, and `D` (two edges below the root) has depth `2`.
2. `intermediateLevel()` computes height the opposite direction: `heightOf(node)` cannot return an answer until it knows both children's heights, so recursion goes all the way down to `null` (returning `-1`, so a true leaf computes `1 + max(-1, -1) = 0`) before any value comes back up. `heightOf(a)` for the whole tree is `2` (root down to `D`, the deepest leaf, is two edges: `A -> B -> D`).
3. `advancedLevel()` builds a deliberately lopsided chain and shows that a single node (`B`) has both a depth (from the root, looking up) and a height (from `B` down to its own deepest leaf, looking down) — and these are two genuinely different numbers describing two different things about the same node, not the same measurement from two directions.

## 7. Gotchas & takeaways

> Gotcha: the height convention (empty subtree = `-1`, single leaf = `0`) is one common convention, but not universal — some sources define a single-node tree as having height `1`, counting nodes instead of edges. Always state which convention you are using, since mixing them silently produces off-by-one bugs.

- Depth counts edges from the root *down to* a node; height counts edges from a node *down to* its deepest leaf.
- The root has depth `0`; a leaf has height `0` (under the edge-counting convention used here).
- Depth is naturally computed top-down; height is naturally computed bottom-up, since it needs both children's results first.
- Related concepts: [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md), [Tree height, depth & diameter](0107-tree-height-depth-diameter.md).
