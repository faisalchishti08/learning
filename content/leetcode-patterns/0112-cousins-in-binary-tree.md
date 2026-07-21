---
card: leetcode-patterns
gi: 112
slug: cousins-in-binary-tree
title: Cousins in Binary Tree
---

## 1. What it is

Given the `root` of a binary tree and the values of two distinct nodes `x` and `y`, return `true` if the two nodes are cousins. Two nodes are cousins when they sit at the same depth but have different parents. Example: `root = [1,2,3,4]`, `x = 4`, `y = 3` → `false` (`4` is at depth 2, `3` is at depth 1).

## 2. Why & when

This problem needs Tree BFS because "same depth" is exactly what level-by-level traversal gives you for free. You process one level at a time, so you can check both the depth and the parent of a node without extra bookkeeping. It belongs in this section because the level boundary (`levelSize`) is what lets you compare nodes fairly, one level at a time.

## 3. Core concept

**Key idea:** run level-order BFS. At each level, track each node's parent alongside the node itself. If both target values appear in the same level, they are cousins only when their parents differ.

**Steps:**
1. Push `root` with a `null` parent onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Track the parent of `x` and the parent of `y` if either is found in this level.
   - Loop `levelSize` times: dequeue a `(node, parent)` pair, push its children with itself as their parent.
   - After the loop, if both `x` and `y` were found in this level, return `parentOf(x) != parentOf(y)`.
3. If the level ends and only one of `x`, `y` was found, return `false` (different depths).

**Why it is correct:** the `levelSize` snapshot isolates exactly one depth per iteration, so finding both values inside the same iteration proves equal depth. Comparing the parent references then proves or disproves the cousin relationship.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two nodes at the same depth with different parents are cousins">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="300" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="130" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="130" y="150" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="330" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="330" y="150" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="222" y1="49" x2="168" y2="77" stroke="#8b949e"/>
    <line x1="238" y1="49" x2="292" y2="77" stroke="#8b949e"/>
    <line x1="152" y1="104" x2="134" y2="132" stroke="#8b949e"/>
    <line x1="308" y1="104" x2="326" y2="132" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">4 and 5: same depth (2), different parents (2 and 3) -&gt; cousins</text>
  </g>
</svg>

Both green nodes sit at depth 2 but hang off different parents, so BFS marks them as cousins.

## 5. Runnable example

```java
// CousinsInBinaryTree.java
import java.util.*;

public class CousinsInBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS twice, once to find each target's depth
    // and parent value, then compare. O(n) time but walks the tree twice
    // and needs two separate recursive helpers.
    static boolean bruteForce(TreeNode root, int x, int y) {
        int[] depthX = findDepthAndParent(root, x, null, 0);
        int[] depthY = findDepthAndParent(root, y, null, 0);
        return depthX[0] == depthY[0] && depthX[1] != depthY[1];
    }

    static int[] findDepthAndParent(TreeNode node, int target, TreeNode parent, int depth) {
        if (node == null) return null;
        if (node.val == target) return new int[]{depth, parent == null ? -1 : parent.val};
        int[] left = findDepthAndParent(node.left, target, node, depth + 1);
        if (left != null) return left;
        return findDepthAndParent(node.right, target, node, depth + 1);
    }

    // KEY INSIGHT: BFS already groups nodes by depth in one queue drain, so a
    // single level-order pass finds both targets' parents without two DFS calls.

    // Level 2 -- Optimal: BFS with levelSize, tracking parent references for
    // x and y as the level is drained. O(n) time, O(w) space (widest level).
    public static boolean isCousins(TreeNode root, int x, int y) {
        if (root == null) return false;
        Queue<TreeNode> queue = new LinkedList<>();
        Map<TreeNode, TreeNode> parentOf = new IdentityHashMap<>();
        queue.offer(root);
        parentOf.put(root, null);

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            TreeNode foundX = null, foundY = null;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.val == x) foundX = node;
                if (node.val == y) foundY = node;
                if (node.left != null) { parentOf.put(node.left, node); queue.offer(node.left); }
                if (node.right != null) { parentOf.put(node.right, node); queue.offer(node.right); }
            }
            if (foundX != null && foundY != null) return parentOf.get(foundX) != parentOf.get(foundY);
            if (foundX != null || foundY != null) return false;
        }
        return false;
    }

    // Level 3 -- Hardened: siblings (same parent) must return false, and
    // a node compared against a non-existent value must not throw.
    static boolean hardened(TreeNode root, int x, int y) {
        return isCousins(root, x, y);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2);
        root.right = new TreeNode(3);
        root.left.left = new TreeNode(4);
        root.right.right = new TreeNode(5);

        System.out.println(bruteForce(root, 4, 5));
        System.out.println(isCousins(root, 4, 5));
        System.out.println(hardened(root, 2, 3));
    }
}
```

How to run: save as `CousinsInBinaryTree.java`, then run `java CousinsInBinaryTree.java`.

## 6. Walkthrough

Dry run of `isCousins(root, 4, 5)` on the tree above:

| level | levelSize | dequeued | foundX (4) | foundY (5) | parent(4) | parent(5) |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | null | null | - | - |
| 1 | 2 | 2, 3 | null | null | - | - |
| 2 | 2 | 4, 5 | node 4 | node 5 | node 2 | node 3 |

Both targets appear in level 2, so the loop checks `parentOf(4) != parentOf(5)`, which is `node 2 != node 3`, `true`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue and the parent map.

## 7. Gotchas & takeaways

> Gotcha: two nodes at the same depth with the same parent (true siblings) are NOT cousins — always check the parent difference, not just the depth match.

- Comparing `TreeNode` references (not values) for the parent check avoids bugs when two different nodes coincidentally hold the same `val`.
- Related problems: Binary Tree Level Order Traversal (collect whole levels), Symmetric Tree (compares mirrored positions instead of arbitrary cousins).
