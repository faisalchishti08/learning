---
card: leetcode-patterns
gi: 108
slug: tree-bfs-template-queue-holding-one-level-at-a-time
title: Tree BFS — template: queue holding one level at a time
---

## 1. What it is

This is the reusable template for grouping a breadth-first traversal by level: before draining the queue, record how many nodes are currently in it (`levelSize`), then remove exactly that many nodes before moving to the next level. That count is the boundary between one depth and the next.

## 2. Why & when

A plain BFS loop (see the previous page) visits nodes in level order but mixes them into one flat list — it never tells you where depth 0 ends and depth 1 begins. Most level-based problems need that boundary: printing rows separately, comparing sums per row, or reversing the order within alternating rows.

Use this template whenever a problem needs one result **per level** rather than one result for the whole tree — level order traversal, zigzag traversal, right side view, average per level, or the widest level.

The alternative is DFS with a `depth` argument, appending each node into `result.get(depth)`. That works too, but it needs a list-of-lists and an index computation at every node. The queue-with-`levelSize`-snapshot approach is more direct for BFS-shaped problems, since the queue already visits nodes in level order.

## 3. Core concept

**Key idea:** at the start of each iteration of the outer loop, the queue holds exactly the nodes of one level, and nothing else — no nodes from the level before it (already removed) and no nodes from the level after it (their parents have not been processed yet). Snapshotting the queue's size before draining it isolates that level.

**Steps:**
1. Push `root` onto the queue (skip if `root` is `null`).
2. While the queue is not empty:
   - Save `levelSize = queue.size()` — this is exactly how many nodes belong to the current level.
   - Start a new empty list for this level.
   - Loop `levelSize` times: remove the front node, add its value to the level's list, and push its non-null children onto the back of the queue.
   - Add the completed level list to the overall result.
3. Return the result — a list of lists, one per depth.

**Why it works:** every node pushed during the inner loop belongs to the *next* level, because it is a child of a node from the *current* level. The inner loop only removes `levelSize` nodes — the exact count taken at the top of the iteration — so it stops before touching any of those newly pushed next-level nodes, keeping the two levels cleanly separated.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Snapshotting queue size to isolate one tree level per iteration">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">Before level 1: queue = [2, 3], levelSize = 2</text>
    <rect x="20" y="30" width="50" height="26" fill="#161b22" stroke="#79c0ff"/><text x="45" y="48" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="80" y="30" width="50" height="26" fill="#161b22" stroke="#79c0ff"/><text x="105" y="48" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="160" y="48" fill="#8b949e">&lt;- remove exactly 2</text>

    <text x="20" y="100" fill="#e6edf3">After draining 2, before removing more: queue = [4, 5]</text>
    <rect x="20" y="110" width="50" height="26" fill="#161b22" stroke="#3fb950"/><text x="45" y="128" fill="#e6edf3" text-anchor="middle">4</text>
    <rect x="80" y="110" width="50" height="26" fill="#161b22" stroke="#3fb950"/><text x="105" y="128" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="160" y="128" fill="#8b949e">&lt;- children of 2, queued during level 1</text>

    <text x="20" y="180" fill="#e6edf3">Next iteration: levelSize = queue.size() = 2 again -&gt; level 2 is [4, 5]</text>
  </g>
</svg>

Snapshotting `levelSize` before the inner loop stops it from accidentally consuming next-level nodes that get pushed in mid-loop.

## 5. Runnable example

```java
// TreeBfsTemplate.java
import java.util.*;

public class TreeBfsTemplate {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(level);
        }
        return result;
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2);
        root.right = new TreeNode(3);
        root.left.left = new TreeNode(4);
        root.left.right = new TreeNode(5);

        System.out.println(levelOrder(root));
    }
}
```

How to run: save as `TreeBfsTemplate.java`, then run `java TreeBfsTemplate.java`.

## 6. Walkthrough

1. Queue starts as `[1]`. Outer loop iteration 1: `levelSize = 1`. Remove `1`, add to level, push `2` and `3`. Level list is `[1]`, queue is now `[2, 3]`.
2. Outer loop iteration 2: `levelSize = 2` (snapshot taken now, before removing anything). Remove `2`: push `4`, `5`. Remove `3`: no children. Level list is `[2, 3]`, queue is now `[4, 5]`.
3. Outer loop iteration 3: `levelSize = 2`. Remove `4`, then `5`: neither has children. Level list is `[4, 5]`, queue is now `[]`.
4. Queue is empty, loop ends. Result: `[[1], [2, 3], [4, 5]]`.

## 7. Gotchas & takeaways

> Gotcha: calling `queue.size()` fresh inside the inner loop (instead of once, before the loop starts) reads a growing number as children get pushed in — the inner loop would then never terminate at the level boundary and would swallow the next level too.

- Save `levelSize` in a local variable exactly once, before the inner loop begins.
- This template is the base for zigzag order (reverse alternate levels), right side view (keep only the last node of each level), and per-level aggregates (sum, average, max) — only the body of the inner loop changes.
