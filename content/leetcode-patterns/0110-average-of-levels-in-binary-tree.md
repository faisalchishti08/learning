---
card: leetcode-patterns
gi: 110
slug: average-of-levels-in-binary-tree
title: Average of Levels in Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return the average value of the nodes at each level, as a list of doubles ordered from the root's level downward. Example: `root = [3,9,20,null,null,15,7]` → `[3.0, 14.5, 11.0]` (level 0 is just `3`; level 1 is `9` and `20`, average `14.5`; level 2 is `15` and `7`, average `11.0`).

## 2. Why & when

This is a direct application of the Tree BFS template: process one level at a time, and instead of collecting every value, sum them and divide by the level's node count. It belongs to this section because it needs the level boundary that `levelSize` gives you — without it, you cannot tell which values to average together.

## 3. Core concept

**Key idea:** run the standard level-by-level BFS. For each level, sum the values of its `levelSize` nodes as they are dequeued, then divide by `levelSize` to get that level's average.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Initialize `sum = 0` for this level.
   - Loop `levelSize` times: remove the front node, add its value to `sum`, push its non-null children.
   - Append `sum / levelSize` (as a `double`) to the result list.
3. Return the result list.

**Why it is correct:** the `levelSize` snapshot guarantees the inner loop touches exactly the nodes of the current level, so `sum` only ever contains values from that one level before it is divided.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Averaging node values level by level">
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
    <text x="20" y="185" fill="#e6edf3">Averages: [3] -&gt; 3.0, [9,20] -&gt; 14.5, [15,7] -&gt; 11.0</text>
  </g>
</svg>

Each level's nodes are summed as they leave the queue, then divided by the level's node count.

## 5. Runnable example

```java
// AverageOfLevels.java
import java.util.*;

public class AverageOfLevels {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS with a depth argument, collecting sums
    // and counts per depth in parallel lists, then dividing at the end.
    // O(n) time, O(h) recursion space plus O(number of levels) for the
    // sum/count lists -- more bookkeeping than the BFS version needs.
    static List<Double> bruteForce(TreeNode root) {
        List<Long> sums = new ArrayList<>();
        List<Integer> counts = new ArrayList<>();
        dfs(root, 0, sums, counts);
        List<Double> result = new ArrayList<>();
        for (int i = 0; i < sums.size(); i++) result.add(sums.get(i) / (double) counts.get(i));
        return result;
    }

    static void dfs(TreeNode node, int depth, List<Long> sums, List<Integer> counts) {
        if (node == null) return;
        if (depth == sums.size()) { sums.add(0L); counts.add(0); }
        sums.set(depth, sums.get(depth) + node.val);
        counts.set(depth, counts.get(depth) + 1);
        dfs(node.left, depth + 1, sums, counts);
        dfs(node.right, depth + 1, sums, counts);
    }

    // KEY INSIGHT: BFS already visits nodes grouped by level, so summing
    // as you drain the queue avoids the separate depth bookkeeping DFS needs.

    // Level 2 -- Optimal: BFS with levelSize, summing and dividing per
    // level. O(n) time, O(w) space (widest level in the queue).
    public static List<Double> averageOfLevels(TreeNode root) {
        List<Double> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            long sum = 0;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                sum += node.val;
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(sum / (double) levelSize);
        }
        return result;
    }

    // Level 3 -- Hardened: a single-node tree still returns one average
    // equal to that node's own value.
    static List<Double> hardened(TreeNode root) {
        return averageOfLevels(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        root.left = new TreeNode(9);
        root.right = new TreeNode(20);
        root.right.left = new TreeNode(15);
        root.right.right = new TreeNode(7);

        System.out.println(bruteForce(root));
        System.out.println(averageOfLevels(root));
        System.out.println(hardened(new TreeNode(5)));
    }
}
```

How to run: save as `AverageOfLevels.java`, then run `java AverageOfLevels.java`.

## 6. Walkthrough

Dry run of `averageOfLevels` on `[3,9,20,null,null,15,7]`:

| level | levelSize | nodes dequeued | sum | average |
|---|---|---|---|---|
| 0 | 1 | 3 | 3 | 3.0 |
| 1 | 2 | 9, 20 | 29 | 14.5 |
| 2 | 2 | 15, 7 | 22 | 11.0 |

Final result: `[3.0, 14.5, 11.0]`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level's node count, for the queue.

## 7. Gotchas & takeaways

> Gotcha: summing node values with `int` can overflow when a level has many large values (e.g. up to `10^4` nodes each up to `10^4`) — use `long` for the running sum before dividing.

- Dividing `sum / levelSize` when both are integers truncates to an integer in Java — cast at least one operand to `double` (or store `sum` as `long` and divide by `(double) levelSize`, as shown above) to get a correct decimal average.
- Related problems: Binary Tree Level Order Traversal (collect full levels instead of averages), Find Largest Value in Each Tree Row (max instead of average).
