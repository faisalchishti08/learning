---
card: leetcode-patterns
gi: 113
slug: binary-tree-level-order-traversal
title: Binary Tree Level Order Traversal
---

## 1. What it is

Given the `root` of a binary tree, return the values of its nodes as a list of lists, one inner list per level, ordered top to bottom and left to right. Example: `root = [3,9,20,null,null,15,7]` → `[[3],[9,20],[15,7]]`.

## 2. Why & when

This is the textbook use of Tree BFS: the queue naturally visits nodes in level order, so you only need to know where one level ends and the next begins. It belongs in this section because `levelSize` is the whole trick — without it you cannot tell which dequeued values belong to which inner list.

## 3. Core concept

**Key idea:** run level-order BFS. For each level, collect every value into its own list before moving to the next level.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Create an empty list `currentLevel`.
   - Loop `levelSize` times: dequeue a node, add its value to `currentLevel`, push its non-null children.
   - Append `currentLevel` to the result.
3. Return the result.

**Why it is correct:** the `levelSize` snapshot is taken before any children of the current level are pushed, so the loop drains exactly the nodes that were already in the queue, never a child pushed during the same iteration.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collecting node values level by level">
  <g font-family="sans-serif" font-size="12">
    <circle cx="250" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="250" y="40" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="180" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="180" y="95" fill="#e6edf3" text-anchor="middle">9</text>
    <circle cx="320" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">20</text>
    <circle cx="290" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="290" y="150" fill="#e6edf3" text-anchor="middle">15</text>
    <circle cx="350" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="350" y="150" fill="#e6edf3" text-anchor="middle">7</text>
    <line x1="242" y1="49" x2="188" y2="77" stroke="#8b949e"/>
    <line x1="258" y1="49" x2="312" y2="77" stroke="#8b949e"/>
    <line x1="312" y1="104" x2="296" y2="132" stroke="#8b949e"/>
    <line x1="328" y1="104" x2="344" y2="132" stroke="#8b949e"/>
    <text x="30" y="185" fill="#e6edf3">Result: [[3], [9,20], [15,7]]</text>
  </g>
</svg>

Each level's nodes are collected into their own list before the next level starts draining.

## 5. Runnable example

```java
// BinaryTreeLevelOrderTraversal.java
import java.util.*;

public class BinaryTreeLevelOrderTraversal {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS with a depth argument, appending each
    // value into the list at index `depth`, creating a new list on first
    // visit to that depth. O(n) time, but mixes recursion with index
    // bookkeeping instead of using the queue that BFS gives for free.
    static List<List<Integer>> bruteForce(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        dfs(root, 0, result);
        return result;
    }

    static void dfs(TreeNode node, int depth, List<List<Integer>> result) {
        if (node == null) return;
        if (depth == result.size()) result.add(new ArrayList<>());
        result.get(depth).add(node.val);
        dfs(node.left, depth + 1, result);
        dfs(node.right, depth + 1, result);
    }

    // KEY INSIGHT: a queue already visits nodes level by level in the order
    // they were pushed, so snapshotting queue.size() before draining a level
    // replaces the depth-index bookkeeping DFS needs.

    // Level 2 -- Optimal: BFS with levelSize, one list per level.
    // O(n) time, O(w) space (widest level in the queue).
    public static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> currentLevel = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                currentLevel.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(currentLevel);
        }
        return result;
    }

    // Level 3 -- Hardened: an empty tree must return an empty list, not
    // a list containing one empty list.
    static List<List<Integer>> hardened(TreeNode root) {
        return levelOrder(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        root.left = new TreeNode(9);
        root.right = new TreeNode(20);
        root.right.left = new TreeNode(15);
        root.right.right = new TreeNode(7);

        System.out.println(bruteForce(root));
        System.out.println(levelOrder(root));
        System.out.println(hardened(null));
    }
}
```

How to run: save as `BinaryTreeLevelOrderTraversal.java`, then run `java BinaryTreeLevelOrderTraversal.java`.

## 6. Walkthrough

Dry run of `levelOrder` on `[3,9,20,null,null,15,7]`:

| level | levelSize | dequeued | currentLevel | queue after |
|---|---|---|---|---|
| 0 | 1 | 3 | [3] | [9, 20] |
| 1 | 2 | 9, 20 | [9, 20] | [15, 7] |
| 2 | 2 | 15, 7 | [15, 7] | [] |

Final result: `[[3], [9,20], [15,7]]`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level's node count, for the queue.

## 7. Gotchas & takeaways

> Gotcha: reading `queue.size()` inside the inner loop instead of caching it before the loop starts gives the wrong count once children are pushed, silently merging two levels into one.

- Always snapshot `levelSize` before the inner loop begins; it is the single line that turns plain BFS into level-order BFS.
- Related problems: Average of Levels in Binary Tree (reduce each level to one number), Binary Tree Zigzag Level Order Traversal (alternate the direction per level).
