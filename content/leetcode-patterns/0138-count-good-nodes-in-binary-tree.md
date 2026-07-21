---
card: leetcode-patterns
gi: 138
slug: count-good-nodes-in-binary-tree
title: Count Good Nodes in Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, a node `X` is "good" if, on the path from the root to `X`, no node has a value greater than `X`'s value. Return the number of good nodes. Example: `root = [3,1,4,3,null,1,5]` → `4` (the good nodes are `3` (root), `4`, `5`, and the second `3`).

## 2. Why & when

This needs the pre-order "pass state down" style of Tree DFS: the only information a node needs to decide if it is good is the maximum value seen so far on the path from the root, which its parent already knows and can hand down. It belongs in this section because the check is naturally made BEFORE recursing further, using state built up on the way down, not information combined back up from children.

## 3. Core concept

**Key idea:** carry `maxSoFar` down the recursion, starting at negative infinity (or the root's own value). At each node, if `node.val >= maxSoFar`, it is good — count it, and update `maxSoFar` to `node.val` before recursing into both children.

**Steps:**
1. Base case: if `node == null`, return `0`.
2. Check: `isGood = node.val >= maxSoFar ? 1 : 0`.
3. Update: `newMax = max(maxSoFar, node.val)`.
4. Recurse: return `isGood + countGood(node.left, newMax) + countGood(node.right, newMax)`.
5. Call the helper starting with `maxSoFar = Integer.MIN_VALUE` (or `root.val`) so the root itself always counts as good.

**Why it is correct:** `maxSoFar` is threaded down fresh for every branch (never shared or mutated across siblings), so it always equals the true maximum among all ancestors from the root to the current node — exactly what "good" is defined against.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="maxSoFar travels down and each node compares itself against it">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="250" y="20" fill="#3fb950" font-size="10">max=3, good</text>
    <circle cx="170" cy="80" r="15" fill="#161b22" stroke="#f85149"/><text x="170" y="84" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="90" y="75" fill="#f85149" font-size="10">1 &lt; 3, not good</text>
    <circle cx="290" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="290" y="84" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="310" y="75" fill="#3fb950" font-size="10">4 &gt;= 3, good, max=4</text>
    <circle cx="150" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="60" y="145" fill="#3fb950" font-size="10">3 &gt;= 3, good (ties count)</text>
    <line x1="222" y1="43" x2="178" y2="68" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="282" y2="68" stroke="#8b949e"/>
    <line x1="163" y1="93" x2="153" y2="118" stroke="#8b949e"/>
    <text x="10" y="180" fill="#e6edf3">Node 1's child (3) compares against maxSoFar=3 (from root), not against its parent 1</text>
  </g>
</svg>

The second `3` compares against `maxSoFar = 3` inherited from the root, not against its immediate parent's value of `1`.

## 5. Runnable example

```java
// CountGoodNodesInBinaryTree.java
public class CountGoodNodesInBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: for every node, walk back up to the root
    // via a parent map (or re-walk down from the root along the stored
    // path) to find the max ancestor value, then compare. O(n^2) time
    // worst case, since finding "the path to this node" is redone for
    // every single node instead of being carried along during one pass.
    static int bruteForce(TreeNode root) {
        java.util.List<TreeNode> path = new java.util.ArrayList<>();
        int[] count = {0};
        countAlongPaths(root, path, count);
        return count[0];
    }

    static void countAlongPaths(TreeNode node, java.util.List<TreeNode> path, int[] count) {
        if (node == null) return;
        path.add(node);
        int maxOnPath = Integer.MIN_VALUE;
        for (TreeNode ancestor : path) maxOnPath = Math.max(maxOnPath, ancestor.val);
        if (node.val == maxOnPath) count[0]++;
        countAlongPaths(node.left, path, count);
        countAlongPaths(node.right, path, count);
        path.remove(path.size() - 1);
    }

    // KEY INSIGHT: the parent already knows the max value seen so far on
    // its own path from the root -- passing that single number down as
    // a recursion argument avoids recomputing the max ancestor for every
    // node from scratch.

    // Level 2 -- Optimal: pre-order DFS carrying maxSoFar down.
    // O(n) time, O(h) space (recursion stack).
    public static int goodNodes(TreeNode root) {
        return countGood(root, Integer.MIN_VALUE);
    }

    static int countGood(TreeNode node, int maxSoFar) {
        if (node == null) return 0;
        int isGood = node.val >= maxSoFar ? 1 : 0;
        int newMax = Math.max(maxSoFar, node.val);
        return isGood + countGood(node.left, newMax) + countGood(node.right, newMax);
    }

    // Level 3 -- Hardened: a tree containing negative values must still
    // correctly count the root as good, since maxSoFar starts at
    // Integer.MIN_VALUE, never at 0.
    static int hardened(TreeNode root) {
        return goodNodes(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3,
            new TreeNode(1, new TreeNode(3), null),
            new TreeNode(4, new TreeNode(1), new TreeNode(5)));

        System.out.println(bruteForce(root));
        System.out.println(goodNodes(root));
        TreeNode negatives = new TreeNode(-1, new TreeNode(-2), null);
        System.out.println(hardened(negatives));
    }
}
```

How to run: save as `CountGoodNodesInBinaryTree.java`, then run `java CountGoodNodesInBinaryTree.java`.

## 6. Walkthrough

Dry run of `countGood` on `[3,1,4,3,null,1,5]`:

| node | maxSoFar in | isGood | newMax out |
|---|---|---|---|
| 3 (root) | -infinity | 1 | 3 |
| 1 | 3 | 0 (1 &lt; 3) | 3 |
| 3 (grandchild) | 3 | 1 (3 &gt;= 3) | 3 |
| 4 | 3 | 1 (4 &gt;= 3) | 4 |
| 1 (grandchild) | 4 | 0 (1 &lt; 4) | 4 |
| 5 | 4 | 1 (5 &gt;= 4) | 5 |

Total good nodes: `1 + 0 + 1 + 1 + 0 + 1 = 4`. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: using strict `>` instead of `>=` when checking "is this node good" would wrongly exclude a node that TIES the maximum ancestor value — the problem counts ties as good, so the comparison must be `node.val >= maxSoFar`.

- `maxSoFar` is passed by value (a fresh copy per call), so updating it in one branch never leaks into a sibling branch — no explicit backtracking step is needed here, unlike Path Sum II's shared mutable list.
- Related problems: Path Sum (also threads accumulated state down the recursion, there a running sum instead of a running max), Kth Smallest Element in a BST (a different kind of state carried through a DFS, there a counter instead of a max).
