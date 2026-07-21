---
card: leetcode-patterns
gi: 130
slug: symmetric-tree
title: Symmetric Tree
---

## 1. What it is

Given the `root` of a binary tree, return `true` if it is a mirror of itself around its center — the left subtree is a mirror image of the right subtree. Example: `root = [1,2,2,3,4,4,3]` → `true`; `root = [1,2,2,null,3,null,3]` → `false`.

## 2. Why & when

This is Tree DFS run on two subtrees at once, just like Same Tree, but the comparison is crossed: the left subtree's left side must match the right subtree's right side, and vice versa. It belongs in this section because "is this a mirror" can only be answered once you know both mirrored subtree pairs are themselves mirrors, all the way down — a post-order combine.

## 3. Core concept

**Key idea:** a tree is symmetric if its left and right subtrees are mirrors of each other. Two subtrees `left` and `right` are mirrors if: both are `null`, or both are non-null with equal values AND `left.left` mirrors `right.right` AND `left.right` mirrors `right.left` (the sides are swapped, not matched straight across).

**Steps:**
1. Handle the empty tree: if `root == null`, return `true`.
2. Call a helper `isMirror(left, right)` starting with `root.left` and `root.right`.
3. Inside `isMirror`: if both are `null`, return `true`. If exactly one is `null`, return `false`. If values differ, return `false`.
4. Recurse crossed: return `isMirror(left.left, right.right) && isMirror(left.right, right.left)`.

**Why it is correct:** a mirror image flips left and right at every level, so comparing `left.left` to `right.right` (both are the "outer" grandchildren) and `left.right` to `right.left` (both are the "inner" grandchildren) is what correctly checks the reflection, instead of comparing same-side children which would only check for an identical (not mirrored) tree.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mirrored comparison crosses left-left with right-right">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="160" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="300" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="300" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="120" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="120" y="134" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="200" cy="130" r="15" fill="#161b22" stroke="#79c0ff"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="260" cy="130" r="15" fill="#161b22" stroke="#79c0ff"/><text x="260" y="134" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="340" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="340" y="134" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="221" y1="43" x2="169" y2="68" stroke="#8b949e"/>
    <line x1="239" y1="43" x2="291" y2="68" stroke="#8b949e"/>
    <line x1="150" y1="93" x2="128" y2="118" stroke="#8b949e"/>
    <line x1="170" y1="93" x2="192" y2="118" stroke="#8b949e"/>
    <line x1="290" y1="93" x2="268" y2="118" stroke="#8b949e"/>
    <line x1="310" y1="93" x2="332" y2="118" stroke="#8b949e"/>
    <path d="M 120 145 Q 230 175 340 145" fill="none" stroke="#3fb950" stroke-dasharray="4,3"/>
    <text x="10" y="185" fill="#e6edf3">outer pair (green): left.left=3 mirrors right.right=3</text>
  </g>
</svg>

Comparing outer grandchildren to outer grandchildren (and inner to inner) is the "crossed" check that a straight same-tree comparison would miss.

## 5. Runnable example

```java
// SymmetricTree.java
public class SymmetricTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: build an explicit mirrored copy of the
    // right subtree (swap every node's children recursively), then
    // compare it to the left subtree with a plain same-tree check.
    // O(n) time, O(n) EXTRA space for the mirrored copy.
    static boolean bruteForce(TreeNode root) {
        if (root == null) return true;
        TreeNode mirroredRight = mirror(root.right);
        return sameTree(root.left, mirroredRight);
    }

    static TreeNode mirror(TreeNode node) {
        if (node == null) return null;
        return new TreeNode(node.val, mirror(node.right), mirror(node.left));
    }

    static boolean sameTree(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        return a.val == b.val && sameTree(a.left, b.left) && sameTree(a.right, b.right);
    }

    // KEY INSIGHT: you do not need to build a physical mirrored copy --
    // comparing left.left to right.right (and left.right to right.left)
    // directly checks the mirror relationship with no extra tree.

    // Level 2 -- Optimal: crossed paired DFS, no extra tree built.
    // O(n) time, O(h) space (recursion stack).
    public static boolean isSymmetric(TreeNode root) {
        if (root == null) return true;
        return isMirror(root.left, root.right);
    }

    static boolean isMirror(TreeNode left, TreeNode right) {
        if (left == null && right == null) return true;
        if (left == null || right == null) return false;
        if (left.val != right.val) return false;
        return isMirror(left.left, right.right) && isMirror(left.right, right.left);
    }

    // Level 3 -- Hardened: a single-node tree (no children) must return
    // true, and a tree with only a left child on one side but only a
    // right child on the matching mirrored side must return false.
    static boolean hardened(TreeNode root) {
        return isSymmetric(root);
    }

    public static void main(String[] args) {
        TreeNode symmetric = new TreeNode(1,
            new TreeNode(2, new TreeNode(3), new TreeNode(4)),
            new TreeNode(2, new TreeNode(4), new TreeNode(3)));
        TreeNode asymmetric = new TreeNode(1,
            new TreeNode(2, null, new TreeNode(3)),
            new TreeNode(2, null, new TreeNode(3)));

        System.out.println(bruteForce(symmetric));
        System.out.println(isSymmetric(symmetric));
        System.out.println(hardened(asymmetric));
    }
}
```

How to run: save as `SymmetricTree.java`, then run `java SymmetricTree.java`.

## 6. Walkthrough

Dry run of `isSymmetric(root)` on `[1,2,2,3,4,4,3]`:

| call | left node | right node | crossed recursion | result |
|---|---|---|---|---|
| isMirror(root.left, root.right) | 2 | 2 | values equal, recurse crossed | pending |
| isMirror(2.left=3, 2.right=3) | 3 | 3 | both leaves, both children null | true |
| isMirror(2.right=4, 2.left=4) | 4 | 4 | both leaves, both children null | true |
| combine | - | - | true && true | true |

Final result: `true`. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: writing `isMirror(left.left, right.left)` (same side on both) instead of `isMirror(left.left, right.right)` (crossed) checks whether the tree is identical to itself, which is trivially unrelated to symmetry — always cross the sides when comparing mirrors.

- A single node or an empty tree is always symmetric — it has no sides to compare, so the recursion's `null`/`null` base case returns `true` correctly.
- Related problems: Same Tree (the straight, non-crossed comparison this problem adapts), Invert Binary Tree (produces an actual mirrored tree, which is what this problem avoids building).
