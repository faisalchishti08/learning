---
card: leetcode-patterns
gi: 143
slug: flatten-binary-tree-to-linked-list
title: Flatten Binary Tree to Linked List
---

## 1. What it is

Given the `root` of a binary tree, flatten it in place into a "linked list" that follows the same shape as a `TreeNode`: every node's `left` child becomes `null`, and every node's `right` child points to the next node in pre-order traversal order. Example: `root = [1,2,5,3,4,null,6]` → `[1,null,2,null,3,null,4,null,5,null,6]` (a single rightward chain in pre-order: `1,2,3,4,5,6`).

## 2. Why & when

The target order is pre-order (root, then left subtree, then right subtree), so this is Tree DFS where the "combine" step rewires pointers instead of returning a value. It belongs in this section because the clean way to do it is post-order: fully flatten the left and right subtrees first, THEN splice the flattened left chain between the root and the flattened right chain.

## 3. Core concept

**Key idea:** flatten the left subtree and the right subtree first (post-order, so both are already single right-going chains). Then: save the old right subtree, move the (now-flattened) left subtree into `node.right`, set `node.left = null`, and attach the saved old right subtree to the end of the newly-moved chain.

**Steps:**
1. Base case: if `node == null`, return.
2. Recurse: `flatten(node.left)`, then `flatten(node.right)` (both subtrees are now flattened into right-only chains).
3. Save: `oldRight = node.right`.
4. Move: `node.right = node.left`, `node.left = null`.
5. Find the tail of the chain just moved into `node.right` (walk `.right` until it is `null`).
6. Attach: `tail.right = oldRight`.

**Why it is correct:** because both children are fully flattened before this node touches them, moving the left chain into the right slot and then appending the saved original right chain to its tail produces exactly pre-order: this node, then everything that was its left subtree (in pre-order), then everything that was its right subtree (in pre-order).

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Move flattened left chain into the right slot, then reattach the old right chain at its tail">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="60" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="30" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="30" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="90" cy="80" r="15" fill="#161b22" stroke="#f85149"/><text x="90" y="84" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="52" y1="43" x2="36" y2="68" stroke="#3fb950" stroke-width="2"/>
    <line x1="68" y1="43" x2="84" y2="68" stroke="#f85149" stroke-width="2"/>
    <text x="10" y="15" fill="#8b949e">Before: 1 has left=2 (already flattened), right=5 (already flattened)</text>
    <circle cx="260" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="260" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="330" cy="30" r="15" fill="#161b22" stroke="#3fb950"/><text x="330" y="34" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="400" cy="30" r="15" fill="#161b22" stroke="#f85149"/><text x="400" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="275" y1="30" x2="315" y2="30" stroke="#3fb950" stroke-width="2"/>
    <line x1="345" y1="30" x2="385" y2="30" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="200" y="80" fill="#e6edf3">After: 1.right = 2 (moved chain), tail of that chain's .right = 5 (old right, reattached)</text>
  </g>
</svg>

The flattened left chain is spliced in as the new right child, and the saved old right chain is reattached at the end of it.

## 5. Runnable example

```java
// FlattenBinaryTree.java
public class FlattenBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: collect every node in pre-order into a
    // list first, then rewire the list into a right-only chain in a
    // second pass. O(n) time, O(n) EXTRA space for the list, versus
    // rewiring pointers directly during one recursive pass.
    static void bruteForce(TreeNode root) {
        java.util.List<TreeNode> nodes = new java.util.ArrayList<>();
        preorderCollect(root, nodes);
        for (int i = 0; i + 1 < nodes.size(); i++) {
            nodes.get(i).left = null;
            nodes.get(i).right = nodes.get(i + 1);
        }
        if (!nodes.isEmpty()) nodes.get(nodes.size() - 1).left = null;
    }

    static void preorderCollect(TreeNode node, java.util.List<TreeNode> nodes) {
        if (node == null) return;
        nodes.add(node);
        preorderCollect(node.left, nodes);
        preorderCollect(node.right, nodes);
    }

    // KEY INSIGHT: flattening both subtrees first (post-order), then
    // splicing the already-flattened left chain in as the right child
    // and reattaching the saved old right chain at its tail, rewires
    // pointers in place with no auxiliary list.

    // Level 2 -- Optimal: post-order DFS with in-place pointer splicing.
    // O(n) time, O(h) space (recursion stack); no extra list.
    public static void flatten(TreeNode node) {
        if (node == null) return;
        flatten(node.left);
        flatten(node.right);

        TreeNode oldRight = node.right;
        node.right = node.left;
        node.left = null;

        TreeNode tail = node;
        while (tail.right != null) tail = tail.right;
        tail.right = oldRight;
    }

    // Level 3 -- Hardened: a node with no left child (only a right
    // child already flattened) must be left unchanged aside from the
    // no-op move (node.right = null moved into node.right = null).
    static void hardened(TreeNode root) {
        flatten(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(3), new TreeNode(4)),
            new TreeNode(5, null, new TreeNode(6)));

        flatten(root);
        StringBuilder sb = new StringBuilder();
        TreeNode cur = root;
        while (cur != null) { sb.append(cur.val).append(" "); cur = cur.right; }
        System.out.println(sb.toString().trim());

        TreeNode single = new TreeNode(9);
        hardened(single);
        System.out.println(single.val + " " + single.left + " " + single.right);
    }
}
```

How to run: save as `FlattenBinaryTree.java`, then run `java FlattenBinaryTree.java`.

## 6. Walkthrough

Dry run of `flatten` on `[1,2,5,3,4,null,6]` (`1` has left `2`, right `5`; `2` has left `3`, right `4`; `5` has right `6`):

1. `flatten(3)`, `flatten(4)`: both are leaves, nothing to do.
2. `flatten(2)`: `oldRight = 4`. Move: `2.right = 3`, `2.left = null`. Walk to tail of `[3]`, which is `3` itself. Attach: `3.right = 4`. Now `2`'s chain is `2 -> 3 -> 4`.
3. `flatten(6)`: leaf, nothing to do.
4. `flatten(5)`: `oldRight = 6`. Move: `5.right = null` (5 had no left child), `5.left = null`. Tail of an empty moved chain is `5` itself. Attach: `5.right = 6`. Now `5`'s chain is `5 -> 6`.
5. `flatten(1)`: `oldRight = (the 5 -> 6 chain)`. Move: `1.right = (the 2 -> 3 -> 4 chain)`, `1.left = null`. Walk to the tail of `2 -> 3 -> 4`, which is `4`. Attach: `4.right = (the 5 -> 6 chain)`.

Final chain: `1 -> 2 -> 3 -> 4 -> 5 -> 6`. Time complexity: O(n) overall — although finding each tail costs up to O(subtree size), the total tail-walking work across the whole recursion sums to O(n), the same bound as a full traversal. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: saving `oldRight` AFTER already overwriting `node.right` (instead of before) loses the original right subtree forever — the save step must happen first, before `node.right` is reassigned.

- The "walk to the tail" step, while it looks like it could add an extra O(n) factor, is bounded overall: every node is visited as part of exactly one tail-walk across the whole algorithm, keeping the total cost linear.
- Related problems: Construct Binary Tree from Preorder and Inorder Traversal (also reasons about pre-order structure, there to build a tree rather than rewire an existing one), Binary Tree Paths (produces pre-order-style root-to-leaf sequences as strings instead of rewiring pointers).
