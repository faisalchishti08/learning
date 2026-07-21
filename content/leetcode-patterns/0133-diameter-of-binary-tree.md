---
card: leetcode-patterns
gi: 133
slug: diameter-of-binary-tree
title: Diameter of Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return the length (in edges) of the longest path between any two nodes. The path does not need to pass through the root. Example: `root = [1,2,3,4,5]` → `3` (the longest path is `4 -> 2 -> 1 -> 3`, or `5 -> 2 -> 1 -> 3`, each with 3 edges).

## 2. Why & when

The diameter through any single node equals the depth of its left subtree plus the depth of its right subtree — so computing it needs the same depth combine as Maximum Depth of Binary Tree, but with a second, separate variable that tracks the best "left depth + right depth" seen at ANY node, not just the root. It belongs in this section because both quantities (depth, and the running best diameter) are only known once a node's children have already returned their depths — a post-order combine, done once, that updates two things instead of one.

## 3. Core concept

**Key idea:** while computing each node's depth (post-order, same as Maximum Depth), also check whether `leftDepth + rightDepth` at this node beats the best diameter seen so far, and update it if so. The final answer is the best diameter found across the whole tree, not just at the root.

**Steps:**
1. Keep a variable `maxDiameter` outside the recursion (a field, or an array of size 1 to mutate from inside).
2. Define `depth(node)`: base case, if `node == null`, return `0`.
3. Recurse: `leftDepth = depth(node.left)`, `rightDepth = depth(node.right)`.
4. Update: `maxDiameter = max(maxDiameter, leftDepth + rightDepth)`.
5. Return `1 + max(leftDepth, rightDepth)` (the node's own depth, for its parent's use).
6. Call `depth(root)` once; the answer is whatever `maxDiameter` ended up holding.

**Why it is correct:** every node is visited exactly once by the depth recursion, and at each visit the diameter check considers that node as the "peak" of a path going down its left side and down its right side — since every possible path's highest point is some node, checking all nodes as candidate peaks covers every possible path.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The diameter through a node is its left depth plus its right depth">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="35" r="16" fill="#161b22" stroke="#3fb950"/><text x="230" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="300" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="120" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="120" y="150" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="200" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="200" y="150" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="222" y1="49" x2="168" y2="77" stroke="#3fb950" stroke-width="2"/>
    <line x1="238" y1="49" x2="292" y2="77" stroke="#3fb950" stroke-width="2"/>
    <line x1="152" y1="104" x2="128" y2="132" stroke="#3fb950" stroke-width="2"/>
    <line x1="168" y1="104" x2="192" y2="132" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="180" fill="#e6edf3">At node 1: leftDepth(2)=2, rightDepth(3)=1 -&gt; diameter candidate 2+1=3</text>
  </g>
</svg>

The path `4 -> 2 -> 1 -> 3` has 3 edges, matching `leftDepth(1) + rightDepth(1) = 2 + 1 = 3`.

## 5. Runnable example

```java
// DiameterOfBinaryTree.java
public class DiameterOfBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: for every node, independently compute its
    // left and right subtree depths from scratch, and track the best
    // sum. O(n^2) time in the worst case (a skewed tree), since depth()
    // is recomputed from zero for every node instead of reusing results.
    static int bruteForce(TreeNode root) {
        if (root == null) return 0;
        int throughRoot = depthSlow(root.left) + depthSlow(root.right);
        return Math.max(throughRoot, Math.max(bruteForce(root.left), bruteForce(root.right)));
    }

    static int depthSlow(TreeNode node) {
        if (node == null) return 0;
        return 1 + Math.max(depthSlow(node.left), depthSlow(node.right));
    }

    // KEY INSIGHT: the same single depth() pass that computes every
    // node's depth can ALSO update a running best diameter as it goes,
    // so no node's depth is ever recomputed a second time.

    // Level 2 -- Optimal: one post-order pass computing depth and
    // updating maxDiameter together. O(n) time, O(h) space (recursion stack).
    static int maxDiameter;

    public static int diameterOfBinaryTree(TreeNode root) {
        maxDiameter = 0;
        depth(root);
        return maxDiameter;
    }

    static int depth(TreeNode node) {
        if (node == null) return 0;
        int leftDepth = depth(node.left);
        int rightDepth = depth(node.right);
        maxDiameter = Math.max(maxDiameter, leftDepth + rightDepth);
        return 1 + Math.max(leftDepth, rightDepth);
    }

    // Level 3 -- Hardened: a single-node tree must return diameter 0
    // (no edges at all), and a left-skewed chain of n nodes must return
    // n - 1, not confuse depth with diameter.
    static int hardened(TreeNode root) {
        return diameterOfBinaryTree(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3));

        System.out.println(bruteForce(root));
        System.out.println(diameterOfBinaryTree(root));
        System.out.println(hardened(new TreeNode(9)));
    }
}
```

How to run: save as `DiameterOfBinaryTree.java`, then run `java DiameterOfBinaryTree.java`.

## 6. Walkthrough

Dry run of `diameterOfBinaryTree(root)` on `[1,2,3,4,5]`:

| call | leftDepth | rightDepth | maxDiameter after | returns |
|---|---|---|---|---|
| depth(4) | 0 | 0 | 0 | 1 |
| depth(5) | 0 | 0 | 0 | 1 |
| depth(2) | 1 | 1 | 2 (1+1) | 2 |
| depth(3) | 0 | 0 | 2 (unchanged) | 1 |
| depth(1) | 2 | 1 | 3 (2+1, beats 2) | 3 |

Final `maxDiameter = 3`. Time complexity: O(n), every node visited exactly once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: returning `maxDiameter` directly from `depth()` (instead of returning the node's own depth, and keeping `maxDiameter` as a separate tracked value) breaks the recursion — the parent needs its child's DEPTH to compute its own depth, not the best diameter seen so far in that subtree.

- The diameter is a path between any two nodes, so it does NOT have to pass through the root — checking `leftDepth + rightDepth` at every node, not just the root, is what makes this correct.
- Related problems: Maximum Depth of Binary Tree (the depth computation this problem extends), Balanced Binary Tree (also tracks a second value alongside depth, this time a boolean, using the same one-pass technique).
