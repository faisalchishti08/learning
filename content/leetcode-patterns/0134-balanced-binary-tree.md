---
card: leetcode-patterns
gi: 134
slug: balanced-binary-tree
title: Balanced Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return `true` if it is height-balanced: for every node, the depths of its left and right subtrees differ by at most `1`. Example: `root = [3,9,20,null,null,15,7]` → `true`; `root = [1,2,2,3,3,null,null,4,4]` → `false` (some node's children differ in depth by more than `1`).

## 2. Why & when

Like Diameter of Binary Tree, this needs a depth computation that also checks a condition at every node along the way — here, "is the depth difference at most 1" instead of "what is the best depth sum". It belongs in this section because the naive way (compute depth separately, then check balance separately, at every node) repeats work; the efficient way folds both into one post-order pass.

## 3. Core concept

**Key idea:** compute depth bottom-up as usual, but the moment any subtree is found to be unbalanced, propagate a sentinel value (like `-1`) all the way back up instead of a real depth, so the caller can short-circuit without checking every remaining node.

**Steps:**
1. Define `checkHeight(node)`: base case, if `node == null`, return `0`.
2. Recurse: `leftHeight = checkHeight(node.left)`. If it is already `-1` (unbalanced below), return `-1` immediately.
3. Recurse: `rightHeight = checkHeight(node.right)`. If it is already `-1`, return `-1` immediately.
4. Check: if `abs(leftHeight - rightHeight) > 1`, return `-1` (unbalanced here).
5. Otherwise return `1 + max(leftHeight, rightHeight)` (a normal height).
6. The whole tree is balanced if and only if `checkHeight(root) != -1`.

**Why it is correct:** real tree heights are always `>= 0`, so `-1` can never be confused with a real height; once any subtree reports `-1`, every ancestor also returns `-1` without doing further work, which both signals the final answer and skips unnecessary computation.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Once a subtree is unbalanced, -1 propagates up without further checks">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#f85149"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="170" cy="80" r="15" fill="#161b22" stroke="#f85149"/><text x="170" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="290" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="290" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="140" cy="130" r="15" fill="#161b22" stroke="#f85149"/><text x="140" y="134" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="200" cy="130" r="14" fill="#161b22" stroke="#79c0ff"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="120" cy="170" r="12" fill="#161b22" stroke="#f85149"/><text x="120" y="174" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <line x1="221" y1="43" x2="179" y2="68" stroke="#8b949e"/>
    <line x1="239" y1="43" x2="281" y2="68" stroke="#8b949e"/>
    <line x1="160" y1="93" x2="146" y2="118" stroke="#8b949e"/>
    <line x1="180" y1="93" x2="196" y2="118" stroke="#8b949e"/>
    <line x1="134" y1="143" x2="124" y2="160" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Node 3 (red, left side): height 2 vs 0 on its sibling slot -&gt; diff 2 -&gt; unbalanced, returns -1</text>
  </g>
</svg>

The `-1` from the deepest unbalanced node (red path) propagates straight up to the root without further balance checks along the way.

## 5. Runnable example

```java
// BalancedBinaryTree.java
public class BalancedBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: for every node, independently recompute
    // its left and right subtree heights from scratch and compare them.
    // O(n^2) time in the worst case (a skewed tree), since height() is
    // recomputed for every node instead of reusing child results.
    static boolean bruteForce(TreeNode root) {
        if (root == null) return true;
        int leftHeight = heightSlow(root.left);
        int rightHeight = heightSlow(root.right);
        if (Math.abs(leftHeight - rightHeight) > 1) return false;
        return bruteForce(root.left) && bruteForce(root.right);
    }

    static int heightSlow(TreeNode node) {
        if (node == null) return 0;
        return 1 + Math.max(heightSlow(node.left), heightSlow(node.right));
    }

    // KEY INSIGHT: a single post-order pass can compute height and check
    // balance together, using -1 as a sentinel to short-circuit the
    // moment any subtree is already known to be unbalanced.

    // Level 2 -- Optimal: one pass, -1 sentinel for "already unbalanced".
    // O(n) time, O(h) space (recursion stack).
    public static boolean isBalanced(TreeNode root) {
        return checkHeight(root) != -1;
    }

    static int checkHeight(TreeNode node) {
        if (node == null) return 0;
        int leftHeight = checkHeight(node.left);
        if (leftHeight == -1) return -1;
        int rightHeight = checkHeight(node.right);
        if (rightHeight == -1) return -1;
        if (Math.abs(leftHeight - rightHeight) > 1) return -1;
        return 1 + Math.max(leftHeight, rightHeight);
    }

    // Level 3 -- Hardened: a single-node tree must return true (depth
    // difference 0), and an empty tree must return true by definition
    // (no nodes to violate the balance condition).
    static boolean hardened(TreeNode root) {
        return isBalanced(root);
    }

    public static void main(String[] args) {
        TreeNode balanced = new TreeNode(3,
            new TreeNode(9),
            new TreeNode(20, new TreeNode(15), new TreeNode(7)));
        TreeNode unbalanced = new TreeNode(1,
            new TreeNode(2, new TreeNode(3, new TreeNode(4), null), new TreeNode(3)),
            new TreeNode(2));

        System.out.println(bruteForce(unbalanced));
        System.out.println(isBalanced(balanced));
        System.out.println(hardened(unbalanced));
    }
}
```

How to run: save as `BalancedBinaryTree.java`, then run `java BalancedBinaryTree.java`.

## 6. Walkthrough

Dry run of `checkHeight` on the `unbalanced` tree above (`1 -> (2 -> (3 -> (4, null), 3)), 2)`):

| call | leftHeight | rightHeight | diff | result |
|---|---|---|---|---|
| checkHeight(4) | 0 | 0 | 0 | 1 |
| checkHeight(3, left branch) | 1 | 0 | 1 | 2 |
| checkHeight(3, right leaf) | 0 | 0 | 0 | 1 |
| checkHeight(2, left branch) | 2 | 1 | 1 | 3 |
| checkHeight(2, right leaf) | 0 | 0 | 0 | 1 |
| checkHeight(1) | 3 | 1 | 2 (&gt; 1) | -1 |

Final `checkHeight(root) == -1`, so `isBalanced` returns `false`. Time complexity: O(n), every node visited once (no repeated recomputation). Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check `leftHeight == -1` before computing `rightHeight` still gives the correct final answer, but it wastes work recursing into the right subtree even though the left subtree already proved the tree unbalanced — the early return is what makes this genuinely O(n) instead of doing avoidable extra recursion.

- The `-1` sentinel works because real subtree heights are never negative; picking a sentinel outside the valid output range is a reusable trick for folding a validity check into a value-returning recursion.
- Related problems: Maximum Depth of Binary Tree (the plain height computation this problem augments), Diameter of Binary Tree (also augments the height computation, tracking a running best sum instead of a pass/fail sentinel).
