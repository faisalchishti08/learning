---
card: data-structures
gi: 98
slug: binary-tree-binary-search-tree-bst
title: 'Binary tree & binary search tree (BST)'
---

## 1. What it is

A **binary tree** is a tree where every node has at most two children, conventionally called **left** and **right**. A **binary search tree (BST)** is a binary tree with one extra invariant: for every node, every value in its left subtree is smaller, and every value in its right subtree is larger, than the node's own value. That single ordering rule is what makes a BST searchable efficiently.

## 2. Why & when

Binary trees are the foundation for a huge range of structures (heaps, tries, balanced trees like AVL and red-black trees). A BST specifically is the tool whenever you need ordered data with fast insert, search, and delete, all faster than a sorted array's O(n) insert — and, unlike a hash table, a BST also supports finding the minimum, maximum, or a range of values efficiently, in sorted order.

## 3. Core concept

**The structure's shape.** Each node holds a value and two child references, `left` and `right`, either of which can be `null`. There is no fixed shape requirement beyond "at most two children" — a binary tree can be perfectly balanced, or a completely lopsided chain (see [Complete / full / perfect / balanced trees](0099-complete-full-perfect-balanced-trees.md) for the shape variants).

**The BST invariant, precisely.** For every node `n`: every value in `n.left`'s subtree is `< n.value`, and every value in `n.right`'s subtree is `> n.value`. Critically, this must hold for the *entire* subtree, not just the immediate children — a node's right child's left grandchild must still be greater than the original node, not just greater than its immediate parent.

**How the invariant makes search fast.** At any node during a search for a target value, comparing the target against the current node's value tells you which entire subtree to explore next, and lets you discard the other subtree completely — the target cannot possibly be there, since the BST invariant guarantees every value on the wrong side is on the wrong side of the target too. This is what gives O(h) search, where `h` is the tree's height — for a balanced tree, `h = O(log n)`; for a degenerate, chain-like tree, `h = O(n)`.

## 4. Diagram

<svg viewBox="0 0 500 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A binary search tree with root 8, left subtree rooted at 3 holding smaller values, right subtree rooted at 10 holding larger values">
  <g font-family="sans-serif" font-size="11">
    <circle cx="250" cy="30" r="20" fill="#0d1117" stroke="#f0883e"/><text x="250" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <circle cx="150" cy="90" r="20" fill="#161b22" stroke="#79c0ff"/><text x="150" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <circle cx="350" cy="90" r="20" fill="#161b22" stroke="#f0883e"/><text x="350" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <circle cx="100" cy="150" r="20" fill="#161b22" stroke="#79c0ff"/><text x="100" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <circle cx="200" cy="150" r="20" fill="#161b22" stroke="#79c0ff"/><text x="200" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">6</text>
    <circle cx="400" cy="150" r="20" fill="#161b22" stroke="#f0883e"/><text x="400" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">14</text>
    <line x1="235" y1="45" x2="165" y2="75" stroke="#8b949e"/>
    <line x1="265" y1="45" x2="335" y2="75" stroke="#8b949e"/>
    <line x1="135" y1="105" x2="115" y2="135" stroke="#8b949e"/>
    <line x1="165" y1="105" x2="185" y2="135" stroke="#8b949e"/>
    <line x1="365" y1="105" x2="385" y2="135" stroke="#8b949e"/>
    <text x="150" y="195" fill="#79c0ff" text-anchor="middle" font-size="9">everything under 3 is &lt; 8</text>
    <text x="350" y="195" fill="#f0883e" text-anchor="middle" font-size="9">everything under 10 is &gt; 8</text>
  </g>
</svg>

Every value in the left subtree of `8` (`3, 1, 6`) is smaller; every value in the right subtree (`10, 14`) is larger — including values several levels deep, not just direct children.

## 5. Runnable example

```java
// BinaryTreeAndBST.java
public class BinaryTreeAndBST {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
    }

    // Basic: a plain binary tree with NO ordering invariant -- just parent/child structure.
    static void basicLevel() {
        TreeNode root = new TreeNode(5);
        root.left = new TreeNode(9);  // note: larger than the root -- perfectly valid for a plain binary tree
        root.right = new TreeNode(1); // note: smaller than the root -- also fine, no BST rule applies here

        System.out.println("basic: plain binary tree, root=" + root.value + ", left=" + root.left.value + ", right=" + root.right.value);
        System.out.println("basic: no ordering constraint -- left being larger than root is completely valid");
    }

    // Intermediate: build a proper BST by inserting in a way that respects the ordering invariant, then search it.
    static TreeNode insert(TreeNode node, int value) {
        if (node == null) return new TreeNode(value);
        if (value < node.value) node.left = insert(node.left, value);
        else if (value > node.value) node.right = insert(node.right, value);
        return node; // value == node.value: no duplicate inserted
    }

    static boolean search(TreeNode node, int target) {
        if (node == null) return false;
        if (target == node.value) return true;
        return target < node.value ? search(node.left, target) : search(node.right, target); // discard the WRONG half every step
    }

    static void intermediateLevel() {
        TreeNode root = null;
        for (int v : new int[]{8, 3, 10, 1, 6, 14}) root = insert(root, v);

        System.out.println("intermediate: search(6) -> " + search(root, 6));
        System.out.println("intermediate: search(7) -> " + search(root, 7));
    }

    // Advanced: an in-order traversal of a BST always visits values in SORTED order -- direct proof the invariant holds.
    static void inOrder(TreeNode node, StringBuilder out) {
        if (node == null) return;
        inOrder(node.left, out);
        out.append(node.value).append(" ");
        inOrder(node.right, out);
    }

    static void advancedLevel() {
        TreeNode root = null;
        for (int v : new int[]{8, 3, 10, 1, 6, 14, 4, 7}) root = insert(root, v);

        StringBuilder out = new StringBuilder();
        inOrder(root, out);
        System.out.println("advanced: in-order traversal -> " + out.toString().trim() + " (sorted -- confirms the BST invariant holds everywhere)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BinaryTreeAndBST.java`, then run `java BinaryTreeAndBST.java`.

## 6. Walkthrough

1. `basicLevel()` builds a plain binary tree where the root's left child (`9`) is *larger* than the root (`5`) — this is completely valid, since a plain binary tree has no ordering rule at all, only the "at most two children" shape constraint.
2. `intermediateLevel()` inserts `8, 3, 10, 1, 6, 14` following the BST rule (smaller goes left, larger goes right, recursively), producing the tree shown in the diagram. `search(6)` compares `6` against `8` (go left, since `6 < 8`), then against `3` (go right, since `6 > 3`), then finds `6` — three comparisons, discarding half the remaining tree at each step. `search(7)` follows the same path but reaches a `null` child where `7` would need to be, correctly returning `false`.
3. `advancedLevel()` inserts a larger set of values and runs an in-order traversal (left subtree, then node, then right subtree — covered in its own topic). The output comes out perfectly sorted (`1 3 4 6 7 8 10 14`) — this is not a coincidence; it is a direct, guaranteed consequence of the BST invariant holding at every node, and it is the standard way to sanity-check that a BST-building algorithm is correct.

## 7. Gotchas & takeaways

> Gotcha: the BST invariant applies to the *entire* subtree, not just a node's immediate children — a common bug when validating a BST is checking only `node.left.value < node.value < node.right.value` locally, which misses violations further down (e.g. a right-subtree's left-grandchild that happens to be smaller than the original ancestor). See [Validate a BST](0105-validate-a-bst.md) for the correct approach.

- A binary tree only constrains shape (at most two children per node); a BST additionally constrains ordering (left subtree smaller, right subtree larger, recursively, at every node).
- The BST ordering invariant is what lets search discard half the remaining tree at each step, giving O(h) search where `h` is the tree's height.
- An in-order traversal of a valid BST always produces values in sorted order — a useful correctness check.
- Related concepts: [BST insert / search / delete](0103-bst-insert-search-delete.md), [Validate a BST](0105-validate-a-bst.md), [Tree terminology (root, height, depth, leaf)](0097-tree-terminology-root-height-depth-leaf.md).
