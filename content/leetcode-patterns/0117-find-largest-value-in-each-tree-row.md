---
card: leetcode-patterns
gi: 117
slug: find-largest-value-in-each-tree-row
title: Find Largest Value in Each Tree Row
---

## 1. What it is

Given the `root` of a binary tree, return the largest value in each row (level), as a list ordered from the root's row downward. Example: `root = [1,3,2,5,3,null,9]` → `[1, 3, 9]` (row 0 is `1`; row 1 is `3, 2`, max `3`; row 2 is `5, 3, 9`, max `9`).

## 2. Why & when

This is Tree BFS reduced to a maximum instead of a sum or a full list. It belongs in this section because the level boundary (`levelSize`) is what tells the algorithm when to stop comparing values for the current row and start a fresh maximum for the next one.

## 3. Core concept

**Key idea:** run level-order BFS. For each level, track a running maximum as nodes are dequeued, then add that maximum to the result once the level is fully drained.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Initialize `rowMax = Integer.MIN_VALUE`.
   - Loop `levelSize` times: dequeue a node, update `rowMax = max(rowMax, node.val)`, push its non-null children.
   - Append `rowMax` to the result.
3. Return the result.

**Why it is correct:** the `levelSize` snapshot guarantees the inner loop only compares values from the current row before `rowMax` is recorded, so no value from a later row can leak into an earlier row's maximum.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tracking the running maximum per level">
  <g font-family="sans-serif" font-size="12">
    <circle cx="250" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="250" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="180" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="180" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="320" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="150" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="150" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="210" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="210" y="150" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="350" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="350" y="150" fill="#e6edf3" text-anchor="middle">9</text>
    <line x1="242" y1="49" x2="188" y2="77" stroke="#8b949e"/>
    <line x1="258" y1="49" x2="312" y2="77" stroke="#8b949e"/>
    <line x1="172" y1="104" x2="158" y2="132" stroke="#8b949e"/>
    <line x1="188" y1="104" x2="204" y2="132" stroke="#8b949e"/>
    <line x1="328" y1="104" x2="344" y2="132" stroke="#8b949e"/>
    <text x="20" y="185" fill="#e6edf3">Row maxes: [1] -&gt; 1, [3,2] -&gt; 3, [5,3,9] -&gt; 9</text>
  </g>
</svg>

The running maximum for row 2 is updated as `5`, then `5`, then `9`, giving the final row max `9`.

## 5. Runnable example

```java
// FindLargestValueInEachTreeRow.java
import java.util.*;

public class FindLargestValueInEachTreeRow {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS with a depth argument, updating a
    // per-depth max stored in a list, extending the list on first visit
    // to a new depth. O(n) time, correct but tracks depth explicitly
    // instead of using the queue's natural level grouping.
    static List<Integer> bruteForce(TreeNode root) {
        List<Integer> maxes = new ArrayList<>();
        dfs(root, 0, maxes);
        return maxes;
    }

    static void dfs(TreeNode node, int depth, List<Integer> maxes) {
        if (node == null) return;
        if (depth == maxes.size()) maxes.add(node.val);
        else maxes.set(depth, Math.max(maxes.get(depth), node.val));
        dfs(node.left, depth + 1, maxes);
        dfs(node.right, depth + 1, maxes);
    }

    // KEY INSIGHT: BFS already isolates one row per queue-drain, so a
    // single running rowMax updated during that drain replaces the
    // per-depth list DFS needs to maintain across recursive calls.

    // Level 2 -- Optimal: BFS with levelSize, tracking rowMax as the
    // level is drained. O(n) time, O(w) space (widest level).
    public static List<Integer> largestValues(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            int rowMax = Integer.MIN_VALUE;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                rowMax = Math.max(rowMax, node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(rowMax);
        }
        return result;
    }

    // Level 3 -- Hardened: a tree containing negative values must still
    // report the correct (possibly negative) max, since rowMax starts at
    // Integer.MIN_VALUE rather than 0.
    static List<Integer> hardened(TreeNode root) {
        return largestValues(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(3);
        root.right = new TreeNode(2);
        root.left.left = new TreeNode(5);
        root.left.right = new TreeNode(3);
        root.right.right = new TreeNode(9);

        System.out.println(bruteForce(root));
        System.out.println(largestValues(root));
        TreeNode negatives = new TreeNode(-5);
        negatives.left = new TreeNode(-3);
        System.out.println(hardened(negatives));
    }
}
```

How to run: save as `FindLargestValueInEachTreeRow.java`, then run `java FindLargestValueInEachTreeRow.java`.

## 6. Walkthrough

Dry run of `largestValues` on `[1,3,2,5,3,null,9]`:

| level | levelSize | dequeued | rowMax after each dequeue | recorded max |
|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 |
| 1 | 2 | 3, 2 | 3, 3 | 3 |
| 2 | 3 | 5, 3, 9 | 5, 5, 9 | 9 |

Final result: `[1, 3, 9]`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: initializing `rowMax` to `0` instead of `Integer.MIN_VALUE` silently gives a wrong answer when every value in a row is negative.

- Resetting `rowMax` at the start of every level (inside the outer loop, before the inner loop) is what keeps rows independent — never carry a max over from the previous row.
- Related problems: Average of Levels in Binary Tree (sum and divide instead of max), Binary Tree Level Order Traversal (collect the full row instead of reducing it to one number).
