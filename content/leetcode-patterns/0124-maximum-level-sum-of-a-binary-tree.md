---
card: leetcode-patterns
gi: 124
slug: maximum-level-sum-of-a-binary-tree
title: Maximum Level Sum of a Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, where levels are numbered starting at `1` for the root, return the level with the maximum sum of node values. If multiple levels tie for the maximum, return the smallest such level number. Example: `root = [1,7,0,7,-8,null,null]` → `2` (level 1 sums to `1`, level 2 sums to `7 + 0 = 7`, level 3 sums to `7 + -8 = -1`; level 2 has the largest sum).

## 2. Why & when

This combines two small ideas you already know from Tree BFS: summing a level (like Average of Levels) and tracking a running best across levels (like Find Largest Value in Each Tree Row, but comparing whole-level sums instead of single values). It belongs in this section because `levelSize` still marks each level's boundary, and a level counter starting at `1` gives you the number to report.

## 3. Core concept

**Key idea:** run level-order BFS, summing each level's values and comparing that sum against the best sum seen so far. Track the level number alongside the sum, and only update the best when a level strictly beats it (never on a tie), so the smallest level number wins ties automatically.

**Steps:**
1. Push `root` onto the queue. Set `levelNumber = 0`, `maxSum = Integer.MIN_VALUE`, `resultLevel = 1`.
2. While the queue is not empty:
   - Increment `levelNumber`.
   - Save `levelSize = queue.size()`. Set `levelSum = 0`.
   - Loop `levelSize` times: dequeue a node, add its value to `levelSum`, push its non-null children.
   - If `levelSum > maxSum`, set `maxSum = levelSum` and `resultLevel = levelNumber`.
3. Return `resultLevel`.

**Why it is correct:** using a strict `>` comparison means the first level to reach a given sum keeps `resultLevel`, and no later level with an equal sum overwrites it — which is exactly the "smallest level number on a tie" rule the problem asks for.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing whole-level sums to find the maximum">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">7</text>
    <circle cx="300" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="130" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="130" y="150" fill="#e6edf3" text-anchor="middle">7</text>
    <circle cx="190" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="190" y="150" fill="#e6edf3" text-anchor="middle">-8</text>
    <line x1="222" y1="49" x2="168" y2="77" stroke="#8b949e"/>
    <line x1="238" y1="49" x2="292" y2="77" stroke="#8b949e"/>
    <line x1="152" y1="104" x2="136" y2="132" stroke="#8b949e"/>
    <line x1="168" y1="104" x2="184" y2="132" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Level 1: sum 1. Level 2 (green): sum 7. Level 3: sum -1. Max is level 2.</text>
  </g>
</svg>

Level 2's sum of `7` beats level 1's sum of `1` and level 3's sum of `-1`, so the answer is level `2`.

## 5. Runnable example

```java
// MaximumLevelSum.java
import java.util.*;

public class MaximumLevelSum {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: DFS accumulating per-depth sums into a
    // growable list, then scanning that list afterward to find the
    // maximum. O(n) time, but needs a second pass over the sums list
    // instead of comparing while the BFS queue drains.
    static int bruteForce(TreeNode root) {
        List<Long> sums = new ArrayList<>();
        dfs(root, 0, sums);
        int resultLevel = 1;
        long maxSum = Long.MIN_VALUE;
        for (int i = 0; i < sums.size(); i++) {
            if (sums.get(i) > maxSum) { maxSum = sums.get(i); resultLevel = i + 1; }
        }
        return resultLevel;
    }

    static void dfs(TreeNode node, int depth, List<Long> sums) {
        if (node == null) return;
        if (depth == sums.size()) sums.add(0L);
        sums.set(depth, sums.get(depth) + node.val);
        dfs(node.left, depth + 1, sums);
        dfs(node.right, depth + 1, sums);
    }

    // KEY INSIGHT: comparing each level's sum against the running best as
    // soon as that level finishes draining avoids storing every level's
    // sum for a later scan -- one pass does both the summing and the compare.

    // Level 2 -- Optimal: BFS with levelSize, comparing levelSum to
    // maxSum inline, level by level. O(n) time, O(w) space (widest level).
    public static int maxLevelSum(TreeNode root) {
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int levelNumber = 0;
        int resultLevel = 1;
        long maxSum = Long.MIN_VALUE;

        while (!queue.isEmpty()) {
            levelNumber++;
            int levelSize = queue.size();
            long levelSum = 0;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                levelSum += node.val;
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            if (levelSum > maxSum) {
                maxSum = levelSum;
                resultLevel = levelNumber;
            }
        }
        return resultLevel;
    }

    // Level 3 -- Hardened: a tree where every level sums to the same
    // negative value must still return level 1 (the first, smallest
    // level number), not the last one.
    static int hardened(TreeNode root) {
        return maxLevelSum(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(7, new TreeNode(7), new TreeNode(-8)),
            new TreeNode(0));

        System.out.println(bruteForce(root));
        System.out.println(maxLevelSum(root));

        TreeNode tie = new TreeNode(-1,
            new TreeNode(-1), null);
        System.out.println(hardened(tie));
    }
}
```

How to run: save as `MaximumLevelSum.java`, then run `java MaximumLevelSum.java`.

## 6. Walkthrough

Dry run of `maxLevelSum` on `[1,7,0,7,-8,null,null]`:

| levelNumber | dequeued | levelSum | maxSum before | maxSum after | resultLevel |
|---|---|---|---|---|---|
| 1 | 1 | 1 | -infinity | 1 | 1 |
| 2 | 7, 0 | 7 | 1 | 7 | 2 |
| 3 | 7, -8 | -1 | 7 | 7 (unchanged) | 2 (unchanged) |

Final `resultLevel = 2`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: using `>=` instead of `>` when updating `maxSum` would let a later level with an equal sum overwrite an earlier, smaller `resultLevel` — the strict `>` is what enforces "return the smallest level number on a tie".

- Summing into a `long` (not `int`) avoids overflow when a level has many large values; the comparison still works the same way once the sum is safely accumulated.
- Related problems: Average of Levels in Binary Tree (report every level's reduced value instead of only the best one), Find Largest Value in Each Tree Row (compares single values per level instead of whole-level sums).
