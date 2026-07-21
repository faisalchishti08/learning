---
card: leetcode-patterns
gi: 149
slug: delete-node-in-a-bst
title: Delete Node in a BST
---

## 1. What it is

Given the `root` of a binary search tree (BST) and a value `key`, delete the node with that value and return the (possibly new) root, keeping the tree a valid BST. Example: `root = [5,3,6,2,4,null,7]`, `key = 3` → a tree like `[5,4,6,2,null,null,7]` (any valid rearrangement that preserves BST order is accepted).

## 2. Why & when

Deleting a BST node needs the BST search property to find the target (go left or right based on comparison), and then a specific fix-up depending on how many children the found node has. It belongs in Tree DFS because finding the node and rebuilding the tree around it is one recursive pre-order-style search, with the actual "delete" logic applied once the target is located.

## 3. Core concept

**Key idea:** search for `key` using standard BST navigation. Once found, handle three cases: no children (just remove it), one child (replace it with that child), or two children (replace its value with its in-order successor — the smallest value in its right subtree — then delete that successor from the right subtree instead, which is now a simpler one-or-zero-child deletion).

**Steps:**
1. Base case: if `node == null`, return `null` (key not found in this subtree, nothing to delete).
2. If `key < node.val`, recurse: `node.left = delete(node.left, key)`.
3. If `key > node.val`, recurse: `node.right = delete(node.right, key)`.
4. If `key == node.val` (found it): if `node.left == null`, return `node.right` (splice out, promoting the right child). If `node.right == null`, return `node.left` (promoting the left child).
5. If both children exist: find `successor` = the leftmost node in `node.right` (the smallest value greater than `node.val`). Set `node.val = successor.val`. Then `node.right = delete(node.right, successor.val)` (delete the successor from the right subtree, where it is now guaranteed to have at most one child).
6. Return `node`.

**Why it is correct:** the in-order successor is the smallest value strictly greater than `node.val`, so replacing `node.val` with it preserves the BST ordering (everything still left of `node` is smaller, everything still right is at least as large); the successor itself, being the leftmost node of a subtree, can never have a left child, so deleting it recursively always falls into the simpler zero-or-one-child case.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deleting a two-child node by replacing its value with its in-order successor">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#f85149"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">6</text>
    <circle cx="130" cy="140" r="14" fill="#161b22" stroke="#79c0ff"/><text x="130" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="190" cy="140" r="14" fill="#161b22" stroke="#3fb950"/><text x="190" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <line x1="222" y1="43" x2="168" y2="72" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="292" y2="72" stroke="#8b949e"/>
    <line x1="150" y1="98" x2="135" y2="126" stroke="#8b949e"/>
    <line x1="170" y1="98" x2="185" y2="126" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="175" fill="#e6edf3">Delete 3 (red): its in-order successor is 4 (green) -- copy 4 into node 3's slot, then delete the old 4</text>
  </g>
</svg>

Node `3`'s in-order successor (`4`, its right child's leftmost descendant) replaces its value; then the original `4` is removed as a simple, childless deletion.

## 5. Runnable example

```java
// DeleteNodeInBST.java
public class DeleteNodeInBST {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: collect every value via in-order traversal
    // EXCEPT the key, then rebuild a fresh, balanced-ish BST from that
    // sorted list using recursive midpoint selection. O(n) time and
    // O(n) extra space for the collected list, and it discards the
    // original tree structure entirely instead of doing a local fix-up.
    static TreeNode bruteForce(TreeNode root, int key) {
        java.util.List<Integer> values = new java.util.ArrayList<>();
        collectExcept(root, key, values);
        return buildFromSorted(values, 0, values.size() - 1);
    }

    static void collectExcept(TreeNode node, int key, java.util.List<Integer> values) {
        if (node == null) return;
        collectExcept(node.left, key, values);
        if (node.val != key) values.add(node.val);
        collectExcept(node.right, key, values);
    }

    static TreeNode buildFromSorted(java.util.List<Integer> values, int left, int right) {
        if (left > right) return null;
        int mid = left + (right - left) / 2;
        TreeNode node = new TreeNode(values.get(mid));
        node.left = buildFromSorted(values, left, mid - 1);
        node.right = buildFromSorted(values, mid + 1, right);
        return node;
    }

    // KEY INSIGHT: only the target node's local neighborhood needs to
    // change -- swapping in the in-order successor's value and then
    // removing that successor (which has at most one child) fixes the
    // tree with a local edit, no full rebuild required.

    // Level 2 -- Optimal: BST search + three-case delete (leaf,
    // one child, two children via in-order successor).
    // O(h) time, O(h) space (recursion stack).
    public static TreeNode deleteNode(TreeNode node, int key) {
        if (node == null) return null;
        if (key < node.val) {
            node.left = deleteNode(node.left, key);
        } else if (key > node.val) {
            node.right = deleteNode(node.right, key);
        } else {
            if (node.left == null) return node.right;
            if (node.right == null) return node.left;
            TreeNode successor = node.right;
            while (successor.left != null) successor = successor.left;
            node.val = successor.val;
            node.right = deleteNode(node.right, successor.val);
        }
        return node;
    }

    // Level 3 -- Hardened: deleting a key that does not exist in the
    // tree must return the tree unchanged, and deleting the root of a
    // single-node tree must return null.
    static TreeNode hardened(TreeNode root, int key) {
        return deleteNode(root, key);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(5,
            new TreeNode(3, new TreeNode(2), new TreeNode(4)),
            new TreeNode(6, null, new TreeNode(7)));

        TreeNode a = bruteForce(root, 3);
        System.out.println(a.val);

        TreeNode root2 = new TreeNode(5,
            new TreeNode(3, new TreeNode(2), new TreeNode(4)),
            new TreeNode(6, null, new TreeNode(7)));
        TreeNode b = deleteNode(root2, 3);
        System.out.println(b.val + " " + b.left.val);

        System.out.println(hardened(new TreeNode(9), 9));
    }
}
```

How to run: save as `DeleteNodeInBST.java`, then run `java DeleteNodeInBST.java`.

## 6. Walkthrough

Dry run of `deleteNode(root, key=3)` on `[5,3,6,2,4,null,7]`:

| call | comparison | action |
|---|---|---|
| deleteNode(5, 3) | 3 &lt; 5 | recurse left: `node.left = deleteNode(3, 3)` |
| deleteNode(3, 3) | key == node.val, found it | both children exist; find successor: leftmost of `3.right` (which is `4`, with no left child) -> successor = 4 |
| deleteNode(3, 3) continued | - | `node.val = 4`; recurse: `node.right = deleteNode(4, 4)` |
| deleteNode(4, 4) | key == node.val | no children -> return `null` |

After the recursion unwinds, the node that was `3` now holds value `4` and has `null` as its right child, and `5.left` points to this updated node. Time complexity: O(h), where `h` is the tree's height (search plus the successor lookup, both bounded by height). Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: when the target node has two children, replacing its VALUE with the successor's value (and then deleting the successor node) is the standard technique — deleting the target node object directly and trying to reattach its subtrees to the successor's original position is far more error-prone and unnecessary.

- Using the in-order PREDECESSOR (the largest value in the left subtree) instead of the successor works equally well and is an equally valid alternative implementation.
- Related problems: Validate Binary Search Tree (the same BST ordering property this problem must preserve after every deletion), Kth Smallest Element in a BST (relies on the same in-order structure that determines which node is the "successor" here).
