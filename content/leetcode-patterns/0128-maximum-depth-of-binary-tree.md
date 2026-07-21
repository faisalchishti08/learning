---
card: leetcode-patterns
gi: 128
slug: maximum-depth-of-binary-tree
title: Maximum Depth of Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return its maximum depth: the number of nodes along the longest path from the root down to the farthest leaf. Example: `root = [3,9,20,null,null,15,7]` → `3` (path `3 -> 20 -> 15` or `3 -> 20 -> 7`).

## 2. Why & when

This is the simplest possible Tree DFS: a node's depth only depends on the deeper of its two children's depths, which is exactly a post-order combine. It belongs in the Tree DFS section because there is no natural "level" grouping needed — you only need one number per subtree, computed bottom-up.

## 3. Core concept

**Key idea:** the depth of a node is `1` plus the larger depth of its two children. An empty tree has depth `0`.

**Steps:**
1. Base case: if `node == null`, return `0`.
2. Recurse: `leftDepth = maxDepth(node.left)`, `rightDepth = maxDepth(node.right)`.
3. Combine: return `1 + max(leftDepth, rightDepth)`.

**Why it is correct:** every node's depth counts itself (`+1`) plus whichever child subtree is taller; taking the max instead of the sum ensures you follow the single longest path, not both branches at once.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Depth combines as 1 plus the taller child's depth">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="40" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">9</text>
    <circle cx="300" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">20</text>
    <circle cx="270" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="270" y="150" fill="#e6edf3" text-anchor="middle">15</text>
    <circle cx="330" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="330" y="150" fill="#e6edf3" text-anchor="middle">7</text>
    <line x1="222" y1="49" x2="168" y2="77" stroke="#8b949e"/>
    <line x1="238" y1="49" x2="292" y2="77" stroke="#3fb950" stroke-width="2"/>
    <line x1="292" y1="104" x2="276" y2="132" stroke="#3fb950" stroke-width="2"/>
    <line x1="308" y1="104" x2="324" y2="132" stroke="#8b949e"/>
    <text x="10" y="180" fill="#e6edf3">depth(9)=1, depth(20)=1+max(1,1)=2, depth(3)=1+max(1,2)=3</text>
  </g>
</svg>

The longest path (green) runs through node `20`, so the root's depth is `1 + 2 = 3`.

## 5. Runnable example

```java
// MaximumDepthOfBinaryTree.java
public class MaximumDepthOfBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: BFS counting levels, one more than needed
    // for a pure depth question. O(n) time, O(w) space (widest level),
    // which needs a queue instead of the simpler recursive combine below.
    static int bruteForce(TreeNode root) {
        if (root == null) return 0;
        java.util.Queue<TreeNode> queue = new java.util.LinkedList<>();
        queue.offer(root);
        int depth = 0;
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            depth++;
        }
        return depth;
    }

    // KEY INSIGHT: depth is a pure post-order combine -- 1 plus the taller
    // child's depth -- so plain recursion needs no queue or level counter.

    // Level 2 -- Optimal: post-order DFS. O(n) time, O(h) space
    // (recursion stack, h = tree height).
    public static int maxDepth(TreeNode root) {
        if (root == null) return 0;
        int leftDepth = maxDepth(root.left);
        int rightDepth = maxDepth(root.right);
        return 1 + Math.max(leftDepth, rightDepth);
    }

    // Level 3 -- Hardened: a single-node tree must return 1, and an
    // empty tree must return 0, not throw on a null root.
    static int hardened(TreeNode root) {
        return maxDepth(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3,
            new TreeNode(9),
            new TreeNode(20, new TreeNode(15), new TreeNode(7)));

        System.out.println(bruteForce(root));
        System.out.println(maxDepth(root));
        System.out.println(hardened(null));
    }
}
```

How to run: save as `MaximumDepthOfBinaryTree.java`, then run `java MaximumDepthOfBinaryTree.java`.

## 6. Walkthrough

Dry run of `maxDepth(root)` on `[3,9,20,null,null,15,7]`:

| call | leftDepth | rightDepth | returns |
|---|---|---|---|
| maxDepth(9) | 0 | 0 | 1 |
| maxDepth(15) | 0 | 0 | 1 |
| maxDepth(7) | 0 | 0 | 1 |
| maxDepth(20) | 1 | 1 | 2 |
| maxDepth(3) | 1 | 2 | 3 |

Final result: `3`. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack depth, where `h` is the tree's height.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `null` base case returns `0` (not `1`) makes every leaf report depth `2` instead of `1`, since a leaf's two `null` children would otherwise be treated as depth-`1` subtrees.

- This exact combine — `1 + max(left, right)` — is the seed for Balanced Binary Tree and Diameter of Binary Tree, both of which reuse a depth-like computation and add one more check on top.
- Related problems: Minimum Depth of Binary Tree (uses `min` instead of `max`, and needs a special case for one-sided nodes), Balanced Binary Tree (compares left and right depths at every node, not just at the root).
