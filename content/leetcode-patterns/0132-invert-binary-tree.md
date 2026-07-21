---
card: leetcode-patterns
gi: 132
slug: invert-binary-tree
title: Invert Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, invert it: swap every node's left and right children, recursively, and return the (now mirrored) root. Example: `root = [4,2,7,1,3,6,9]` → `[4,7,2,9,6,3,1]`.

## 2. Why & when

This is Tree DFS where the "combine" step is a mutation (swap the children) rather than a computed return value. It belongs in this section because you must invert both subtrees first (recursively), then swap them at the current node — a clean post-order shape, even though the function's real job is a side effect, not a returned number.

## 3. Core concept

**Key idea:** to invert a tree rooted at `node`, first invert its left and right subtrees, then swap the (now-inverted) results into `node.left` and `node.right`.

**Steps:**
1. Base case: if `node == null`, return `null` (nothing to invert).
2. Recurse: `left = invertTree(node.left)`, `right = invertTree(node.right)`.
3. Swap: `node.left = right`, `node.right = left`.
4. Return `node`.

**Why it is correct:** inverting a subtree and then swapping it into the opposite slot is the same as saying "this node's new left child is the fully-inverted version of its old right child" — recursing first guarantees the subtree handed up is already correctly inverted before the swap happens at this level.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Swapping left and right children at every node">
  <g font-family="sans-serif" font-size="12">
    <circle cx="120" cy="35" r="15" fill="#161b22" stroke="#79c0ff"/><text x="120" y="39" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="80" cy="90" r="15" fill="#161b22" stroke="#79c0ff"/><text x="80" y="94" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="160" cy="90" r="15" fill="#161b22" stroke="#79c0ff"/><text x="160" y="94" fill="#e6edf3" text-anchor="middle">7</text>
    <line x1="112" y1="48" x2="88" y2="77" stroke="#8b949e"/>
    <line x1="128" y1="48" x2="152" y2="77" stroke="#8b949e"/>
    <text x="20" y="15" fill="#8b949e">Before</text>
    <path d="M 250 100 L 300 100" stroke="#e6edf3" marker-end="url(#arrow)"/>
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker></defs>
    <circle cx="360" cy="35" r="15" fill="#161b22" stroke="#3fb950"/><text x="360" y="39" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="320" cy="90" r="15" fill="#161b22" stroke="#3fb950"/><text x="320" y="94" fill="#e6edf3" text-anchor="middle">7</text>
    <circle cx="400" cy="90" r="15" fill="#161b22" stroke="#3fb950"/><text x="400" y="94" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="352" y1="48" x2="328" y2="77" stroke="#8b949e"/>
    <line x1="368" y1="48" x2="392" y2="77" stroke="#8b949e"/>
    <text x="330" y="15" fill="#8b949e">After</text>
    <text x="10" y="180" fill="#e6edf3">Node 4's children (2, 7) swap to (7, 2); the same swap happens at every node.</text>
  </g>
</svg>

Every node's left and right children trade places, all the way down the tree.

## 5. Runnable example

```java
// InvertBinaryTree.java
public class InvertBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: BFS, swapping each dequeued node's children
    // as it is visited. O(n) time, O(w) space (widest level for the
    // queue) -- correct, but needs a queue where recursion needs none.
    static TreeNode bruteForce(TreeNode root) {
        if (root == null) return null;
        java.util.Queue<TreeNode> queue = new java.util.LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            TreeNode temp = node.left;
            node.left = node.right;
            node.right = temp;
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        return root;
    }

    // KEY INSIGHT: inverting is just "invert both children, then swap
    // them into each other's slot" -- a direct recursive combine needs
    // no explicit traversal order bookkeeping at all.

    // Level 2 -- Optimal: post-order DFS with a swap.
    // O(n) time, O(h) space (recursion stack).
    public static TreeNode invertTree(TreeNode node) {
        if (node == null) return null;
        TreeNode left = invertTree(node.left);
        TreeNode right = invertTree(node.right);
        node.left = right;
        node.right = left;
        return node;
    }

    // Level 3 -- Hardened: a single-node tree must return unchanged
    // (no children to swap), and an empty tree must return null.
    static TreeNode hardened(TreeNode root) {
        return invertTree(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(4,
            new TreeNode(2, new TreeNode(1), new TreeNode(3)),
            new TreeNode(7, new TreeNode(6), new TreeNode(9)));

        TreeNode inverted = invertTree(root);
        System.out.println(inverted.left.val + " " + inverted.right.val);
        System.out.println(inverted.left.left.val + " " + inverted.left.right.val);
        System.out.println(hardened(new TreeNode(5)).val);
    }
}
```

How to run: save as `InvertBinaryTree.java`, then run `java InvertBinaryTree.java`.

## 6. Walkthrough

Dry run of `invertTree(root)` on `[4,2,7,1,3,6,9]`:

1. `invertTree(4)` calls `invertTree(2)` first.
2. `invertTree(2)` calls `invertTree(1)` (leaf, returns itself unchanged) and `invertTree(3)` (leaf, returns itself unchanged).
3. `invertTree(2)` swaps: `2.left = 3`, `2.right = 1`. Returns node `2` (now with children `3, 1`).
4. `invertTree(4)` calls `invertTree(7)`, which similarly swaps `6` and `9` to become `9, 6`.
5. `invertTree(4)` swaps: `4.left = (inverted 7 subtree)`, `4.right = (inverted 2 subtree)`.

Final tree: `[4,7,2,9,6,3,1]`. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: writing `node.left = node.right; node.right = node.left;` directly, without capturing the recursive results in local variables first, loses the original left child — the first line overwrites `node.left` before the second line can read the old value from it.

- This problem mutates the existing tree in place and returns the same root reference; it does not need to allocate any new `TreeNode`.
- Related problems: Symmetric Tree (checks whether a tree already equals its own mirror, without mutating anything), Same Tree (a plain equality check this problem's swap logic could be tested against).
