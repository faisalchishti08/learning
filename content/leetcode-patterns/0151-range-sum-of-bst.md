---
card: leetcode-patterns
gi: 151
slug: range-sum-of-bst
title: Range Sum of BST
---

## 1. What it is

Given the `root` of a binary search tree (BST) and two integers `low` and `high`, return the sum of values of all nodes with a value in the inclusive range `[low, high]`. Example: `root = [10,5,15,3,7,null,18]`, `low = 7`, `high = 15` → `32` (`7 + 10 + 15 = 32`).

## 2. Why & when

A plain "visit every node and check the range" DFS would work, but it wastes time exploring subtrees that the BST property already guarantees are entirely out of range. This belongs in Tree DFS as an example of using the BST search property to PRUNE branches: if a node's value is below `low`, its entire left subtree is also below `low` and can be skipped; if it is above `high`, its entire right subtree can be skipped.

## 3. Core concept

**Key idea:** at each node, if its value is less than `low`, only its right subtree could possibly contain values in range (everything in its left subtree is even smaller). If its value is greater than `high`, only its left subtree could possibly help (everything in its right subtree is even larger). Otherwise, the node itself counts, and both subtrees still need checking.

**Steps:**
1. Base case: if `node == null`, return `0`.
2. If `node.val < low`, return `rangeSum(node.right, low, high)` (skip the left subtree entirely).
3. If `node.val > high`, return `rangeSum(node.left, low, high)` (skip the right subtree entirely).
4. Otherwise (`low <= node.val <= high`): return `node.val + rangeSum(node.left, low, high) + rangeSum(node.right, low, high)`.

**Why it is correct:** the BST property guarantees every value in `node.left` is `<= node.val` and every value in `node.right` is `>= node.val`, so once `node.val` itself is confirmed too small (or too large), the entire subtree on the "wrong" side is provably out of range and can be skipped without checking any of its nodes individually.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A value below low prunes its entire left subtree from the search">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">10</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#f85149"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">15</text>
    <circle cx="130" cy="140" r="13" fill="#161b22" stroke="#8b949e" stroke-dasharray="3,2"/><text x="130" y="144" fill="#8b949e" text-anchor="middle" font-size="10">3</text>
    <circle cx="190" cy="140" r="13" fill="#161b22" stroke="#3fb950"/><text x="190" y="144" fill="#e6edf3" text-anchor="middle" font-size="10">7</text>
    <circle cx="340" cy="140" r="13" fill="#161b22" stroke="#3fb950"/><text x="340" y="144" fill="#e6edf3" text-anchor="middle" font-size="10">18</text>
    <line x1="222" y1="43" x2="168" y2="72" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="292" y2="72" stroke="#8b949e"/>
    <line x1="150" y1="97" x2="135" y2="126" stroke="#8b949e" stroke-dasharray="3,2"/>
    <line x1="170" y1="97" x2="185" y2="126" stroke="#8b949e"/>
    <line x1="317" y1="97" x2="333" y2="126" stroke="#8b949e"/>
    <text x="10" y="180" fill="#e6edf3">Node 5 &lt; low(7): skip its LEFT subtree (node 3, dashed) entirely, only check its right (7)</text>
  </g>
</svg>

Node `5` is below `low = 7`, so its left subtree (`3`, dashed) is guaranteed out of range and never visited.

## 5. Runnable example

```java
// RangeSumOfBST.java
public class RangeSumOfBST {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: visit EVERY node regardless of the BST
    // property, checking the range at each one. O(n) time always, even
    // when large parts of the tree are provably out of range and could
    // have been skipped.
    static int bruteForce(TreeNode node, int low, int high) {
        if (node == null) return 0;
        int sum = (node.val >= low && node.val <= high) ? node.val : 0;
        return sum + bruteForce(node.left, low, high) + bruteForce(node.right, low, high);
    }

    // KEY INSIGHT: the BST ordering guarantees an entire subtree is out
    // of range once its root is out of range on the correct side --
    // pruning that subtree skips real work instead of just checking and
    // discarding each of its nodes individually.

    // Level 2 -- Optimal: BST-aware DFS that prunes out-of-range
    // subtrees entirely. O(visited nodes) time, often much less than
    // O(n) when many nodes fall outside [low, high]; O(h) space
    // (recursion stack).
    public static int rangeSumBST(TreeNode node, int low, int high) {
        if (node == null) return 0;
        if (node.val < low) return rangeSumBST(node.right, low, high);
        if (node.val > high) return rangeSumBST(node.left, low, high);
        return node.val + rangeSumBST(node.left, low, high) + rangeSumBST(node.right, low, high);
    }

    // Level 3 -- Hardened: a range that excludes every node in the tree
    // must return 0, and a range that includes every node must return
    // the same total as summing the whole tree.
    static int hardened(TreeNode root, int low, int high) {
        return rangeSumBST(root, low, high);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(10,
            new TreeNode(5, new TreeNode(3), new TreeNode(7)),
            new TreeNode(15, null, new TreeNode(18)));

        System.out.println(bruteForce(root, 7, 15));
        System.out.println(rangeSumBST(root, 7, 15));
        System.out.println(hardened(root, 100, 200));
    }
}
```

How to run: save as `RangeSumOfBST.java`, then run `java RangeSumOfBST.java`.

## 6. Walkthrough

Dry run of `rangeSumBST` on `[10,5,15,3,7,null,18]` with `low = 7`, `high = 15`:

| call | node.val | comparison | action |
|---|---|---|---|
| rangeSumBST(10, 7, 15) | 10 | in range | `10 + left + right` |
| rangeSumBST(5, 7, 15) | 5 | `5 < 7` | skip left (`3`), recurse only into right: `rangeSumBST(7, ...)` |
| rangeSumBST(7, 7, 15) | 7 | in range | `7 + 0 + 0 = 7` (leaf) |
| rangeSumBST(15, 7, 15) | 15 | in range | `15 + 0 + right` |
| rangeSumBST(18, 7, 15) | 18 | `18 > 15` | skip right (none), recurse only into left (none): returns `0` |

Total: `10 + 7 + 15 + 0 = 32`. Node `3` is never visited at all, since it was pruned the moment `5` was found below `low`. Time complexity: O(number of nodes actually visited), which can be much less than O(n) when the range excludes large subtrees. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: writing this as a plain tree traversal that checks every node (the brute-force version) still gives the correct answer, but it misses the entire point of having a BST — the efficient solution must use the ordering property to skip whole subtrees, not just skip individual out-of-range values after visiting them.

- The pruning only works because the input is guaranteed to be a valid BST; running the same left/right skip logic on an arbitrary (non-BST) binary tree would silently produce a wrong answer, since out-of-range values could still be hiding in the "skipped" subtree.
- Related problems: Validate Binary Search Tree (confirms the ordering property this problem's pruning logic depends on), Delete Node in a BST (also navigates using BST comparisons to avoid visiting irrelevant branches).
