---
card: leetcode-patterns
gi: 126
slug: tree-dfs-template-recurse-pre-in-post-order-combine-child-re
title: Tree DFS — template: recurse pre/in/post-order, combine child results
---

## 1. What it is

This is the reusable template for Tree DFS: a recursive function visits a node, recurses into its children, and combines the results. The three classic orders — pre-order (process node, then children), in-order (process left, then node, then right), and post-order (process children, then node) — differ only in WHEN you touch the node's own value relative to the recursive calls.

## 2. Why & when

Most DFS problems are naturally post-order: you need the fully combined answer from both children before you can compute the answer at the current node (maximum depth, diameter, balanced check). Pre-order fits problems that pass information DOWN the tree, like tracking the running sum along a root-to-leaf path. In-order is mostly used for binary search trees, since it visits nodes in sorted order.

Use pre-order when a parent needs to hand information to its children (a path so far, a running total, an allowed range). Use post-order when a parent needs to receive information back from its children (a subtree's height, sum, or a boolean like "is balanced"). Use in-order specifically when the sorted-order property of a binary search tree matters.

## 3. Core concept

**Key idea:** the three orders are the same three lines of code — recurse left, recurse right, do work at the node — just written in a different sequence.

**Steps for post-order (the most common shape):**
1. Base case: if `node == null`, return the identity value for the combination (e.g. `0` for sum, `true` for "is valid").
2. Recurse into `node.left`, capturing its returned result.
3. Recurse into `node.right`, capturing its returned result.
4. Combine both results with `node.val` (or `node` itself), and return the combined value.

**Steps for pre-order (pass state down):**
1. Base case: if `node == null`, stop (or record a completed path).
2. Do work at `node` using the state passed in from the parent (e.g. `runningSum + node.val`).
3. Recurse into `node.left`, passing the updated state.
4. Recurse into `node.right`, passing the updated state.

**Why it works:** post-order guarantees both children's answers exist before the parent combines them, since the recursive calls run to completion first. Pre-order guarantees the parent's contribution is folded into the state before either child ever runs, so every node sees the correct accumulated state from the root down to itself.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pre-order pushes state down; post-order pulls results up">
  <g font-family="sans-serif" font-size="12">
    <circle cx="140" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="140" y="40" fill="#e6edf3" text-anchor="middle">N</text>
    <circle cx="90" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="90" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">L</text>
    <circle cx="190" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="190" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">R</text>
    <line x1="132" y1="49" x2="98" y2="77" stroke="#3fb950" stroke-width="2"/>
    <line x1="148" y1="49" x2="182" y2="77" stroke="#3fb950" stroke-width="2"/>
    <text x="60" y="70" fill="#3fb950" font-size="10">state down</text>
    <circle cx="380" cy="35" r="16" fill="#161b22" stroke="#f85149"/><text x="380" y="40" fill="#e6edf3" text-anchor="middle">N</text>
    <circle cx="330" cy="90" r="14" fill="#161b22" stroke="#f85149"/><text x="330" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">L</text>
    <circle cx="430" cy="90" r="14" fill="#161b22" stroke="#f85149"/><text x="430" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">R</text>
    <line x1="338" y1="80" x2="372" y2="49" stroke="#f85149" stroke-width="2"/>
    <line x1="422" y1="80" x2="388" y2="49" stroke="#f85149" stroke-width="2"/>
    <text x="330" y="130" fill="#f85149" font-size="10">results up</text>
    <text x="10" y="175" fill="#e6edf3">Pre-order (left): parent hands state to children before recursing.</text>
    <text x="10" y="188" fill="#e6edf3">Post-order (right): parent combines children's results after they return.</text>
  </g>
</svg>

Pre-order sends information from parent to child; post-order collects information from child to parent.

## 5. Runnable example

```java
// TreeDfsOrders.java
public class TreeDfsOrders {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Post-order template: combine child results with this node's value,
    // AFTER both recursive calls return. Here: subtree height.
    static int height(TreeNode node) {
        if (node == null) return 0;
        int leftHeight = height(node.left);
        int rightHeight = height(node.right);
        return 1 + Math.max(leftHeight, rightHeight);
    }

    // Pre-order template: pass accumulated state DOWN before recursing.
    // Here: does any root-to-leaf path sum to targetSum?
    static boolean hasPathSum(TreeNode node, int remaining) {
        if (node == null) return false;
        int updatedRemaining = remaining - node.val;
        if (node.left == null && node.right == null) return updatedRemaining == 0;
        return hasPathSum(node.left, updatedRemaining) || hasPathSum(node.right, updatedRemaining);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(5,
            new TreeNode(4, new TreeNode(11, new TreeNode(7), new TreeNode(2)), null),
            new TreeNode(8));

        System.out.println(height(root));
        System.out.println(hasPathSum(root, 22));
        System.out.println(hasPathSum(root, 100));
    }
}
```

How to run: save as `TreeDfsOrders.java`, then run `java TreeDfsOrders.java`.

## 6. Walkthrough

Trace of `height(root)` (post-order) on the tree above:

1. `height(5)` calls `height(4)` first.
2. `height(4)` calls `height(11)`: `height(7) = 1`, `height(2) = 1`, so `height(11) = 1 + max(1,1) = 2`.
3. `height(4) = 1 + max(2, 0) = 3` (right child of 4 is null, height 0).
4. `height(5)` calls `height(8) = 1` (leaf).
5. `height(5) = 1 + max(3, 1) = 4`.

Trace of `hasPathSum(root, 22)` (pre-order): remaining starts at `22`. At `5`: remaining becomes `17`. At `4`: remaining becomes `13`. At `11`: remaining becomes `2`. At leaf `7`: remaining becomes `-5`, not `0`, fails. Backtrack, try leaf `2`: remaining becomes `0`, matches — path `5 -> 4 -> 11 -> 2` sums to `22`, so the function returns `true`.

## 7. Gotchas & takeaways

> Gotcha: mixing the two styles — trying to both pass state down AND combine results up in the same recursive call without being deliberate about it — is where most Tree DFS bugs come from. Decide up front whether this problem needs "information from parent to child" or "information from child to parent", then write only that shape.

- Post-order is the right default when in doubt: most tree metrics (height, diameter, balance, sum) are naturally bottom-up.
- Related patterns: Tree BFS (Problem 108) groups by level instead of by subtree; this template groups by subtree completion instead.
