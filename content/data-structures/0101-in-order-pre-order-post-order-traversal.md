---
card: data-structures
gi: 101
slug: in-order-pre-order-post-order-traversal
title: In-order / pre-order / post-order traversal
---

## 1. What it is

These are the three standard **depth-first** ways to visit every node of a binary tree, distinguished only by *when* the current node is visited relative to its two children. **Pre-order**: node, then left, then right. **In-order**: left, then node, then right. **Post-order**: left, then right, then node.

## 2. Why & when

Each order fits a different task, because each visits nodes in a different relationship to the tree's structure. In-order on a BST visits values in sorted order — the standard way to read out a BST's contents. Pre-order is used to copy or serialize a tree (parent before children, so you can rebuild by reading parents first). Post-order is used to safely delete a tree, or evaluate an expression tree (children fully processed before their parent needs their results).

## 3. Core concept

**How the operation transforms the structure — it doesn't; it only defines a visit order.** All three traversals visit every node exactly once; they never modify the tree. They differ only in the *order* the visit (whatever "visit" means for the task — printing, summing, collecting) happens relative to recursing into `left` and `right`.

**Pre-order: node first.** `visit(node); recurse(left); recurse(right);` — the node is processed before either subtree is explored. This is the natural order for copying a tree: write the current node first, then you have enough information to know where its children attach when rebuilding.

**In-order: node in the middle.** `recurse(left); visit(node); recurse(right);` — for a BST specifically, this produces values in ascending sorted order, since everything in `left` is smaller and everything in `right` is larger, so visiting `left` completely, then the node, then `right` completely visits everything in increasing order.

**Post-order: node last.** `recurse(left); recurse(right); visit(node);` — the node is processed only after both subtrees are fully done. This is required whenever the node's own processing depends on results from its children — deleting a node only after its children are deleted, or evaluating an operator node only after both its operand subtrees have been evaluated.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small tree with root A, left child B, right child C, showing the three visit orders as sequences: pre-order A B C, in-order B A C, post-order B C A">
  <g font-family="sans-serif" font-size="11">
    <circle cx="320" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="320" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="260" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="260" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="380" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="308" y1="42" x2="272" y2="78" stroke="#8b949e"/>
    <line x1="332" y1="42" x2="368" y2="78" stroke="#8b949e"/>
    <text x="20" y="140" fill="#79c0ff">pre-order (node, left, right):  A B C</text>
    <text x="20" y="160" fill="#f0883e">in-order (left, node, right):   B A C</text>
    <text x="20" y="180" fill="#a5d6ff">post-order (left, right, node): B C A</text>
  </g>
</svg>

The same tree, three different visit orders — only the position of the node's own visit relative to its two children changes.

## 5. Runnable example

```java
// TreeTraversals.java
import java.util.ArrayList;
import java.util.List;

public class TreeTraversals {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Basic: pre-order -- node, then left, then right. Used to serialize/copy a tree.
    static void preOrder(TreeNode node, List<Integer> out) {
        if (node == null) return;
        out.add(node.value);       // visit node FIRST
        preOrder(node.left, out);
        preOrder(node.right, out);
    }

    static void basicLevel() {
        TreeNode root = new TreeNode(8, new TreeNode(3, new TreeNode(1), new TreeNode(6)), new TreeNode(10));
        List<Integer> out = new ArrayList<>();
        preOrder(root, out);
        System.out.println("basic: pre-order -> " + out);
    }

    // Intermediate: in-order -- left, node, right. On a BST, this always produces SORTED output.
    static void inOrder(TreeNode node, List<Integer> out) {
        if (node == null) return;
        inOrder(node.left, out);
        out.add(node.value);       // visit node in the MIDDLE
        inOrder(node.right, out);
    }

    static void intermediateLevel() {
        TreeNode root = new TreeNode(8, new TreeNode(3, new TreeNode(1), new TreeNode(6)), new TreeNode(10));
        List<Integer> out = new ArrayList<>();
        inOrder(root, out);
        System.out.println("intermediate: in-order -> " + out + " (sorted, since this is a valid BST)");
    }

    // Advanced: post-order -- left, right, node. Used to safely delete a tree, or evaluate an expression tree.
    static void postOrder(TreeNode node, List<Integer> out) {
        if (node == null) return;
        postOrder(node.left, out);
        postOrder(node.right, out);
        out.add(node.value);       // visit node LAST
    }

    // A realistic post-order use: evaluate an expression tree where leaves are numbers, internal nodes are operators (encoded as negative sentinels here for simplicity).
    static int evaluate(TreeNode node) {
        if (node.left == null && node.right == null) return node.value; // leaf: a literal number
        int left = evaluate(node.left);   // children MUST be fully evaluated first -- classic post-order dependency
        int right = evaluate(node.right);
        return switch (node.value) {
            case -1 -> left + right; // -1 encodes "+"
            case -2 -> left * right; // -2 encodes "*"
            default -> throw new IllegalStateException("unknown operator");
        };
    }

    static void advancedLevel() {
        TreeNode root = new TreeNode(8, new TreeNode(3, new TreeNode(1), new TreeNode(6)), new TreeNode(10));
        List<Integer> out = new ArrayList<>();
        postOrder(root, out);
        System.out.println("advanced: post-order -> " + out);

        // expression tree for (3 + 4) * 2
        TreeNode exprTree = new TreeNode(-2, new TreeNode(-1, new TreeNode(3), new TreeNode(4)), new TreeNode(2));
        System.out.println("advanced: evaluate (3 + 4) * 2 via post-order -> " + evaluate(exprTree));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TreeTraversals.java`, then run `java TreeTraversals.java`.

## 6. Walkthrough

Trace all three orders on the tree `8(left: 3(left: 1, right: 6), right: 10)`:

- **Pre-order** visits `8` first, then dives into its left subtree (`3` first, then `1`, then `6`), then its right subtree (`10`): `8, 3, 1, 6, 10`.
- **In-order** fully explores left before visiting a node: left subtree of `8` gives `1, 3, 6` (in sorted order within that subtree), then `8` itself, then right subtree `10`: `1, 3, 6, 8, 10` — fully sorted, confirming this is a valid BST.
- **Post-order** fully explores both children before visiting a node: `1, 6, 3` (left subtree, itself post-order), then `10` (right subtree), then `8` last: `1, 6, 3, 10, 8`.

For the expression-tree evaluation of `(3 + 4) * 2`: `evaluate` recurses to the leaves `3` and `4` first (post-order dependency — you cannot evaluate `+` without both operands), computes `3 + 4 = 7`, then combines that result with the other child `2` at the `*` node: `7 * 2 = 14`.

## 7. Gotchas & takeaways

> Gotcha: mixing up in-order and pre-order is a very common slip under interview pressure — a fast way to double-check: in-order on a BST must come out sorted; if your traced output is not sorted, you likely swapped the position of the node visit relative to the left recursion.

- Pre-order (node, left, right): use for copying/serializing a tree.
- In-order (left, node, right): use to read a BST's values in sorted order.
- Post-order (left, right, node): use whenever a node's processing depends on its children's results first — deletion, expression evaluation.
- All three are O(n) time (visit every node once) and O(h) space for the recursion stack, where `h` is the tree's height.
- Related concepts: [Level-order (BFS) traversal](0102-level-order-bfs-traversal.md), [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md).
