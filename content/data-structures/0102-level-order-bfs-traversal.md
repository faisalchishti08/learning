---
card: data-structures
gi: 102
slug: level-order-bfs-traversal
title: Level-order (BFS) traversal
---

## 1. What it is

**Level-order traversal** visits a binary tree's nodes one level at a time, top to bottom, left to right within each level — the root first, then both its children, then all four grandchildren, and so on. Unlike pre/in/post-order (all depth-first), level-order is a **breadth-first** traversal, and it needs a queue instead of recursion.

## 2. Why & when

Use level-order whenever "distance from the root" matters directly: printing a tree in a readable, level-by-level layout, finding the tree's width at each depth, or serializing a tree in a format that groups nodes by level. It is also the traversal that naturally answers "what is the minimum depth to reach some target node," since it discovers nodes in strictly non-decreasing depth order.

## 3. Core concept

**Why a queue, not recursion.** Depth-first traversals use the call stack (via recursion) precisely because they want to go deep before coming back — LIFO order. Level-order wants the *opposite*: process everything at the current depth before moving to the next depth — FIFO order, exactly what a queue provides (see [BFS level-order using a queue](0080-bfs-level-order-using-a-queue.md) for the general graph/tree BFS pattern this specializes).

**The algorithm.** Enqueue the root. While the queue is not empty: dequeue a node, visit it, then enqueue its non-null children (`left` first, then `right`, to preserve left-to-right order within a level). Because every node at depth `d` is enqueued before any node at depth `d+1` (children are only enqueued after their parent is dequeued, and all depth-`d` parents are dequeued before any depth-`d+1` node gets a chance to be dequeued), the queue naturally drains one full level before starting the next.

**Grouping into levels explicitly.** To get each level as its own list (rather than one flat sequence), record `levelSize = queue.size()` at the start of each round of the outer loop, then dequeue exactly that many nodes — they are guaranteed to be exactly the current level's nodes, since every earlier level has already been fully drained by that point.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree with root A, children B and C, grandchildren D E F G, visited in level order: A, then B and C, then D E F G, using a queue that always drains one full level before starting the next">
  <g font-family="sans-serif" font-size="11">
    <circle cx="320" cy="25" r="16" fill="#0d1117" stroke="#f0883e"/><text x="320" y="29" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="240" cy="80" r="16" fill="#161b22" stroke="#79c0ff"/><text x="240" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="400" cy="80" r="16" fill="#161b22" stroke="#79c0ff"/><text x="400" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="200" cy="135" r="16" fill="#161b22" stroke="#a5d6ff"/><text x="200" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <circle cx="280" cy="135" r="16" fill="#161b22" stroke="#a5d6ff"/><text x="280" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">E</text>
    <circle cx="360" cy="135" r="16" fill="#161b22" stroke="#a5d6ff"/><text x="360" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">F</text>
    <circle cx="440" cy="135" r="16" fill="#161b22" stroke="#a5d6ff"/><text x="440" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">G</text>
    <line x1="310" y1="38" x2="250" y2="68" stroke="#8b949e"/>
    <line x1="330" y1="38" x2="390" y2="68" stroke="#8b949e"/>
    <line x1="232" y1="93" x2="208" y2="122" stroke="#8b949e"/>
    <line x1="248" y1="93" x2="272" y2="122" stroke="#8b949e"/>
    <line x1="392" y1="93" x2="368" y2="122" stroke="#8b949e"/>
    <line x1="408" y1="93" x2="432" y2="122" stroke="#8b949e"/>
    <text x="320" y="180" fill="#79c0ff" text-anchor="middle" font-size="9">visit order: A -&gt; B, C -&gt; D, E, F, G  (one full level, then the next)</text>
  </g>
</svg>

The queue always finishes level `d` (dequeuing and enqueuing every node at that depth) before any level-`d+1` node is dequeued.

## 5. Runnable example

```java
// LevelOrderTraversal.java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;

public class LevelOrderTraversal {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Basic: a flat level-order visit sequence.
    static List<Integer> levelOrderFlat(TreeNode root) {
        List<Integer> order = new ArrayList<>();
        if (root == null) return order;
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            order.add(node.value);
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        return order;
    }

    static void basicLevel() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3, new TreeNode(6), new TreeNode(7)));
        System.out.println("basic: level-order (flat) -> " + levelOrderFlat(root));
    }

    // Intermediate: grouped by level, using levelSize = queue.size() at the start of each round.
    static List<List<Integer>> levelOrderGrouped(TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        if (root == null) return levels;
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                level.add(node.value);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            levels.add(level);
        }
        return levels;
    }

    static void intermediateLevel() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3, new TreeNode(6), new TreeNode(7)));
        System.out.println("intermediate: level-order (grouped) -> " + levelOrderGrouped(root));
    }

    // Advanced: zigzag level order -- alternate left-to-right and right-to-left per level, a common variant.
    static List<List<Integer>> zigzagLevelOrder(TreeNode root) {
        List<List<Integer>> levels = levelOrderGrouped(root);
        for (int i = 1; i < levels.size(); i += 2) {
            java.util.Collections.reverse(levels.get(i)); // reverse every OTHER level
        }
        return levels;
    }

    static void advancedLevel() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3, new TreeNode(6), new TreeNode(7)));
        System.out.println("advanced: zigzag level-order -> " + zigzagLevelOrder(root));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LevelOrderTraversal.java`, then run `java LevelOrderTraversal.java`.

## 6. Walkthrough

1. `basicLevel()` builds a perfect 3-level tree and enqueues the root `1`. Dequeuing `1` enqueues `2` and `3`; dequeuing `2` enqueues `4` and `5`; dequeuing `3` enqueues `6` and `7` — the flat visit order comes out `1, 2, 3, 4, 5, 6, 7`, exactly level by level.
2. `intermediateLevel()` adds level boundaries: at the start of the outer loop's first iteration, `levelSize = 1` (just the root), producing `[1]`. Next iteration, `levelSize = 2` (both children just enqueued), producing `[2, 3]`. Next, `levelSize = 4`, producing `[4, 5, 6, 7]`. Final result: `[[1], [2, 3], [4, 5, 6, 7]]`.
3. `advancedLevel()` reuses the grouped result, then reverses every odd-indexed level (the second, fourth, ...) to produce the "zigzag" pattern some problems ask for: `[[1], [3, 2], [4, 5, 6, 7]]` — level `1` (index 1) is reversed to `[3, 2]`, while levels `0` and `2` stay left-to-right.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `null` check before enqueueing a child (`if (node.left != null) queue.offer(node.left)`) would enqueue `null` itself, and then `queue.poll()` would later try to dereference a `null` `TreeNode`, throwing `NullPointerException` — always guard each child before enqueueing it.

- Level-order needs a queue (FIFO), not recursion (which naturally gives depth-first order via the call stack, LIFO).
- `levelSize = queue.size()` at the start of each outer-loop round is the standard trick to group nodes by level.
- Level-order discovers nodes in strictly non-decreasing depth order, making it the right traversal for "shortest distance from the root" questions.
- Related concepts: [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md), [BFS level-order using a queue](0080-bfs-level-order-using-a-queue.md).
