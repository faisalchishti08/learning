---
card: leetcode-patterns
gi: 111
slug: minimum-depth-of-binary-tree
title: Minimum Depth of Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return its minimum depth — the number of nodes along the shortest path from the root down to the nearest leaf. A leaf is a node with no children. Example: `root = [3,9,20,null,null,15,7]` → `2` (the path `3 -> 9` reaches a leaf in 2 nodes).

## 2. Why & when

Minimum depth is a "nearest target" question, and BFS finds the nearest target without exploring the whole tree. DFS would need to explore every path to a leaf and keep the smallest, wasting work on deep branches once a shallow leaf has already been found. BFS visits nodes in depth order, so the very first leaf it encounters is guaranteed to be at the minimum depth — it can stop immediately.

## 3. Core concept

**Key idea:** run level-order BFS, tracking the current depth. The moment a dequeued node has no children (it is a leaf), return the current depth — no need to look further, since BFS already guarantees nothing shallower remains unvisited.

**Steps:**
1. If `root` is `null`, return `0` (no nodes at all).
2. Push `root` onto the queue. Set `depth = 1` (root counts as depth 1, matching LeetCode's node-count convention).
3. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Loop `levelSize` times: remove the front node. If it has no left and no right child, return `depth` immediately.
   - Otherwise push its non-null children.
   - After the inner loop finishes with no leaf found, increment `depth`.
4. (Unreachable if the tree is non-empty — the loop always finds a leaf before the queue empties.)

**Why it is correct:** BFS visits every node at depth `d` before any node at depth `d + 1`. The first leaf found while draining level `d` is therefore the shallowest leaf in the whole tree — no leaf at a smaller depth can exist, because that depth was already fully drained without finding one.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS stopping at the first leaf found, which is the minimum depth">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="240" y="40" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="170" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="170" y="95" fill="#e6edf3" text-anchor="middle">9</text>
    <circle cx="310" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="310" y="95" fill="#e6edf3" text-anchor="middle">20</text>
    <circle cx="280" cy="145" r="16" fill="#161b22" stroke="#30363d"/><text x="280" y="150" fill="#e6edf3" text-anchor="middle">15</text>
    <circle cx="340" cy="145" r="16" fill="#161b22" stroke="#30363d"/><text x="340" y="150" fill="#e6edf3" text-anchor="middle">7</text>
    <line x1="232" y1="49" x2="178" y2="77" stroke="#8b949e"/>
    <line x1="248" y1="49" x2="302" y2="77" stroke="#8b949e"/>
    <line x1="302" y1="104" x2="286" y2="132" stroke="#8b949e"/>
    <line x1="318" y1="104" x2="334" y2="132" stroke="#8b949e"/>
    <text x="20" y="180" fill="#e6edf3">Node 9 is a leaf found at depth 2 -&gt; return 2 immediately, skip node 20's subtree.</text>
  </g>
</svg>

Node `9` is reached and recognized as a leaf before node `20`'s children are ever explored — BFS never needs to look past the shallowest leaf.

## 5. Runnable example

```java
// MinimumDepthOfBinaryTree.java
import java.util.*;

public class MinimumDepthOfBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS every root-to-leaf path, tracking the
    // minimum length seen. Must visit every node in the worst case, even
    // after the true minimum has already been found. O(n) time, O(h) space.
    static int bruteForce(TreeNode root) {
        if (root == null) return 0;
        if (root.left == null && root.right == null) return 1;
        int min = Integer.MAX_VALUE;
        if (root.left != null) min = Math.min(min, bruteForce(root.left));
        if (root.right != null) min = Math.min(min, bruteForce(root.right));
        return 1 + min;
    }

    // KEY INSIGHT: BFS visits nodes in depth order, so the first leaf it
    // dequeues is guaranteed to be at the minimum possible depth -- no
    // need to keep searching once it is found.

    // Level 2 -- Optimal: BFS, return as soon as a leaf is dequeued.
    // O(n) worst case time (can be much less), O(w) space.
    public static int minDepth(TreeNode root) {
        if (root == null) return 0;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int depth = 1;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.left == null && node.right == null) return depth;
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            depth++;
        }
        return depth; // unreachable for a non-empty tree
    }

    // Level 3 -- Hardened: a node with only ONE child is not a leaf --
    // the minimum depth must follow the existing child, not stop early
    // just because one side is null.
    static int hardened(TreeNode root) {
        return minDepth(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        root.left = new TreeNode(9);
        root.right = new TreeNode(20);
        root.right.left = new TreeNode(15);
        root.right.right = new TreeNode(7);
        System.out.println(bruteForce(root));
        System.out.println(minDepth(root));

        // one-sided tree: 1 has only a right child 2, which has only a
        // right child 3. The path through the null left child of 1 does
        // NOT count -- minimum depth must be 3, not 1.
        TreeNode oneSided = new TreeNode(1);
        oneSided.right = new TreeNode(2);
        oneSided.right.right = new TreeNode(3);
        System.out.println(hardened(oneSided));
    }
}
```

How to run: save as `MinimumDepthOfBinaryTree.java`, then run `java MinimumDepthOfBinaryTree.java`.

## 6. Walkthrough

Dry run of `minDepth` on `[3,9,20,null,null,15,7]`:

| depth | levelSize | nodes checked | leaf found? |
|---|---|---|---|
| 1 | 1 | 3 (has children) | no |
| 2 | 2 | 9 (no children) | **yes, return 2** |

Node `9` is dequeued first within depth 2 and has no children, so the function returns `2` immediately — node `20` is never even checked. Time complexity: O(n) worst case (a tree where the only leaf is the last node visited); often much less. Space complexity: O(w), the widest level.

## 7. Gotchas & takeaways

> Gotcha: treating a node with exactly one child as a leaf. `if (node.left == null || node.right == null) return depth` is wrong — a node with only a right child is not a leaf, and stopping there gives a depth that ignores the existing subtree.

- Only stop at a node where **both** children are `null`.
- Related problems: Maximum Depth of Binary Tree (DFS is fine there, since you must visit every node anyway to find the max), Binary Tree Level Order Traversal (collect full levels instead of stopping early).
