---
card: leetcode-patterns
gi: 140
slug: validate-binary-search-tree
title: Validate Binary Search Tree
---

## 1. What it is

Given the `root` of a binary tree, return `true` if it is a valid binary search tree (BST): for every node, all values in its left subtree are strictly less than the node's value, and all values in its right subtree are strictly greater. Example: `root = [5,1,4,null,null,3,6]` → `false` (node `4` sits in `5`'s right subtree, so every node there must be greater than `5` — but `4 < 5`, which breaks the rule even though `4`'s own two children, `3` and `6`, look fine next to `4` itself).

## 2. Why & when

Checking only "is `node.left.val < node.val < node.right.val`" locally is NOT enough — a node deep in the left subtree must still be less than every ancestor above it, not just its immediate parent. This needs the pre-order "pass state down" style of Tree DFS: each node is validated against a `(lowerBound, upperBound)` range inherited from its ancestors, and it narrows that range further for its own children.

## 3. Core concept

**Key idea:** every node must fall strictly within a valid `(lowerBound, upperBound)` range. The root's range is `(-infinity, +infinity)`. When recursing left, the `upperBound` narrows to the current node's value (everything in the left subtree must be less than it). When recursing right, the `lowerBound` narrows to the current node's value.

**Steps:**
1. Base case: if `node == null`, return `true` (an empty subtree is trivially valid).
2. Check: if `node.val <= lowerBound || node.val >= upperBound`, return `false`.
3. Recurse left with the narrowed range: `validate(node.left, lowerBound, node.val)`.
4. Recurse right with the narrowed range: `validate(node.right, node.val, upperBound)`.
5. Return `true` only if both recursive calls return `true`.

**Why it is correct:** the range passed to each node is the intersection of every constraint imposed by its ancestors — a left turn always tightens the upper bound, a right turn always tightens the lower bound — so by the time a leaf is checked, its allowed range already reflects every ancestor's requirement, not just its direct parent's.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bounds narrow on the way down; a left turn tightens the upper bound">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="250" y="20" fill="#8b949e" font-size="10">(-inf, +inf)</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="70" y="80" fill="#8b949e" font-size="10">(-inf, 5)</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#f85149"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="330" y="80" fill="#f85149" font-size="10">(5, +inf) -- 4 fails!</text>
    <line x1="221" y1="44" x2="169" y2="72" stroke="#8b949e"/>
    <line x1="239" y1="44" x2="291" y2="72" stroke="#f85149" stroke-width="2"/>
    <text x="10" y="180" fill="#e6edf3">Node 4 is 5's right child, so it must be &gt; 5, but 4 &lt; 5 -&gt; invalid BST</text>
  </g>
</svg>

Node `4` inherits the bound `(5, +infinity)` because it sits in `5`'s right subtree, but `4` fails that bound.

## 5. Runnable example

```java
// ValidateBinarySearchTree.java
import java.util.*;

public class ValidateBinarySearchTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: in-order traversal collects values into a
    // list, then check the list is strictly increasing. O(n) time,
    // O(n) EXTRA space for the list, versus checking bounds directly
    // during one pass with no auxiliary storage.
    static boolean bruteForce(TreeNode root) {
        List<Integer> values = new ArrayList<>();
        inorder(root, values);
        for (int i = 1; i < values.size(); i++) {
            if (values.get(i) <= values.get(i - 1)) return false;
        }
        return true;
    }

    static void inorder(TreeNode node, List<Integer> values) {
        if (node == null) return;
        inorder(node.left, values);
        values.add(node.val);
        inorder(node.right, values);
    }

    // KEY INSIGHT: passing a shrinking (lowerBound, upperBound) range
    // down the recursion checks every node against ALL its ancestors at
    // once, with no need to materialize the full in-order sequence.

    // Level 2 -- Optimal: pre-order DFS with a narrowing valid range.
    // O(n) time, O(h) space (recursion stack).
    public static boolean isValidBST(TreeNode root) {
        return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    static boolean validate(TreeNode node, long lowerBound, long upperBound) {
        if (node == null) return true;
        if (node.val <= lowerBound || node.val >= upperBound) return false;
        return validate(node.left, lowerBound, node.val) && validate(node.right, node.val, upperBound);
    }

    // Level 3 -- Hardened: a tree whose values already span Integer.MIN_
    // VALUE or Integer.MAX_VALUE must still validate correctly, which is
    // why the bounds use `long`, not `int` (avoiding overflow at the
    // initial +/- infinity sentinels).
    static boolean hardened(TreeNode root) {
        return isValidBST(root);
    }

    public static void main(String[] args) {
        TreeNode invalid = new TreeNode(5,
            new TreeNode(1),
            new TreeNode(4, new TreeNode(3), new TreeNode(6)));
        TreeNode valid = new TreeNode(5,
            new TreeNode(3),
            new TreeNode(8));

        System.out.println(bruteForce(invalid));
        System.out.println(isValidBST(valid));
        TreeNode edge = new TreeNode(Integer.MIN_VALUE);
        System.out.println(hardened(edge));
    }
}
```

How to run: save as `ValidateBinarySearchTree.java`, then run `java ValidateBinarySearchTree.java`.

## 6. Walkthrough

Dry run of `validate` on the `invalid` tree `[5,1,4,null,null,3,6]`:

| node | lowerBound | upperBound | check | result |
|---|---|---|---|---|
| 5 | -infinity | +infinity | -infinity &lt; 5 &lt; +infinity | ok, recurse |
| 1 (left of 5) | -infinity | 5 | -infinity &lt; 1 &lt; 5 | ok, recurse |
| 4 (right of 5) | 5 | +infinity | is `4 <= 5`? yes | **fails** |

The recursion returns `false` as soon as node `4` violates its inherited lower bound of `5`, without needing to check `4`'s own children. Time complexity: O(n) worst case, every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: comparing only a node against its immediate parent (instead of the full inherited range) misses violations from higher ancestors — in the example, `4`'s parent-only check (`1 < 4 < 6`) would look fine, but `4` also needs to respect the root's constraint that everything in its right subtree exceeds `5`.

- Using `long` bounds (or `Integer.MIN_VALUE - 1L` / `Integer.MAX_VALUE + 1L` style sentinels) avoids an overflow bug when the tree legitimately contains `Integer.MIN_VALUE` or `Integer.MAX_VALUE` as a node value.
- Related problems: Kth Smallest Element in a BST (relies on the same BST ordering property, read via in-order traversal instead of validated via bounds), Insert into a Binary Search Tree (must preserve this same ordering invariant when adding a new node).
