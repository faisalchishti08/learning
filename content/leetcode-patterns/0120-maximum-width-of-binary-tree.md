---
card: leetcode-patterns
gi: 120
slug: maximum-width-of-binary-tree
title: Maximum Width of Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return the maximum width among all levels. The width of a level is the distance between its leftmost and rightmost non-null nodes, counting the null nodes in between as if the tree were a complete binary tree. Example: `root = [1,3,2,5,3,null,9]` → `4` (the bottom level spans positions that are 4 apart, even though one slot in between is empty).

## 2. Why & when

This is Tree BFS with each node carrying a position index, the same index you would get numbering a complete binary tree left to right (root at `0`, left child at `2*i`, right child at `2*i + 1`). It belongs in this section because the level boundary (`levelSize`) is what tells you which two positions — first and last dequeued — define that level's width.

## 3. Core concept

**Key idea:** run level-order BFS, but push `(node, position)` pairs instead of bare nodes. A node at position `i` has left child at position `2*i` and right child at `2*i + 1`. For each level, the width is `lastPosition - firstPosition + 1`.

**Steps:**
1. Push `(root, 0)` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Record `firstPosition` from the first pair dequeued this level.
   - Loop `levelSize` times: dequeue `(node, position)`; if last in the level, record `lastPosition = position`; push `(node.left, 2*position)` and `(node.right, 2*position + 1)` when non-null.
   - Update `maxWidth = max(maxWidth, lastPosition - firstPosition + 1)`.
3. Return `maxWidth`.

**Why it is correct:** the position formula mirrors array indexing of a complete binary tree, so it stays consistent across parent-child edges regardless of which nodes are actually null; subtracting first from last position measures the true span even across gaps.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Positions numbered like a complete binary tree reveal the true width">
  <g font-family="sans-serif" font-size="12">
    <circle cx="250" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="250" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="270" y="30" fill="#8b949e" font-size="10">pos 0</text>
    <circle cx="180" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="180" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="150" y="80" fill="#8b949e" font-size="10">pos 1</text>
    <circle cx="320" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="330" y="80" fill="#8b949e" font-size="10">pos 2</text>
    <circle cx="150" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="150" y="150" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="115" y="165" fill="#3fb950" font-size="10">pos 2</text>
    <circle cx="350" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="350" y="150" fill="#e6edf3" text-anchor="middle">9</text>
    <text x="360" y="165" fill="#3fb950" font-size="10">pos 5</text>
    <line x1="242" y1="49" x2="188" y2="77" stroke="#8b949e"/>
    <line x1="258" y1="49" x2="312" y2="77" stroke="#8b949e"/>
    <line x1="172" y1="104" x2="158" y2="132" stroke="#8b949e"/>
    <line x1="328" y1="104" x2="352" y2="132" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Bottom level: positions 2 to 5 -&gt; width 5 - 2 + 1 = 4</text>
  </g>
</svg>

Numbering positions like array indices exposes the gap between `5` and `9`, giving a width of `4` even though only two nodes exist at that level.

## 5. Runnable example

```java
// MaximumWidthOfBinaryTree.java
import java.util.*;

public class MaximumWidthOfBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    static class Pair {
        TreeNode node;
        long position;
        Pair(TreeNode node, long position) { this.node = node; this.position = position; }
    }

    // Level 1 -- Brute force: DFS recording the leftmost position seen so
    // far at each depth, then comparing every node's position against it.
    // O(n) time, correct but needs a growable per-depth "leftmost" list
    // instead of reading first/last directly off one queue drain.
    static int bruteForce(TreeNode root) {
        List<Long> leftmost = new ArrayList<>();
        return (int) dfs(root, 0, 0, leftmost);
    }

    static long dfs(TreeNode node, int depth, long position, List<Long> leftmost) {
        if (node == null) return 0;
        if (depth == leftmost.size()) leftmost.add(position);
        long width = position - leftmost.get(depth) + 1;
        long leftWidth = dfs(node.left, depth + 1, position * 2, leftmost);
        long rightWidth = dfs(node.right, depth + 1, position * 2 + 1, leftmost);
        return Math.max(width, Math.max(leftWidth, rightWidth));
    }

    // KEY INSIGHT: a queue already dequeues a level's nodes in left-to-right
    // order, so the position of the FIRST and LAST dequeue within a
    // levelSize window directly gives that level's width -- no need to
    // track a running "leftmost" across recursive calls.

    // Level 2 -- Optimal: BFS with levelSize and positions, reading
    // first/last position per level. O(n) time, O(w) space (widest level).
    public static int widthOfBinaryTree(TreeNode root) {
        if (root == null) return 0;
        int maxWidth = 0;
        Queue<Pair> queue = new LinkedList<>();
        queue.offer(new Pair(root, 0));

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            long firstPosition = queue.peek().position;
            long lastPosition = firstPosition;
            for (int i = 0; i < levelSize; i++) {
                Pair current = queue.poll();
                lastPosition = current.position;
                if (current.node.left != null) queue.offer(new Pair(current.node.left, current.position * 2));
                if (current.node.right != null) queue.offer(new Pair(current.node.right, current.position * 2 + 1));
            }
            maxWidth = (int) Math.max(maxWidth, lastPosition - firstPosition + 1);
        }
        return maxWidth;
    }

    // Level 3 -- Hardened: a deep tree that is left-skewed only must not
    // overflow position values; normalising position by subtracting
    // firstPosition before multiplying keeps numbers small.
    static int hardened(TreeNode root) {
        return widthOfBinaryTree(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(3);
        root.right = new TreeNode(2);
        root.left.left = new TreeNode(5);
        root.left.right = new TreeNode(3);
        root.right.right = new TreeNode(9);

        System.out.println(bruteForce(root));
        System.out.println(widthOfBinaryTree(root));
        System.out.println(hardened(new TreeNode(1)));
    }
}
```

How to run: save as `MaximumWidthOfBinaryTree.java`, then run `java MaximumWidthOfBinaryTree.java`.

## 6. Walkthrough

Dry run of `widthOfBinaryTree` on `[1,3,2,5,3,null,9]`:

| level | dequeued (node, position) | firstPosition | lastPosition | width |
|---|---|---|---|---|
| 0 | (1, 0) | 0 | 0 | 1 |
| 1 | (3, 1), (2, 2) | 1 | 2 | 2 |
| 2 | (5, 2), (3, 5), (9, 5) — note 3's right slot (pos 5) is null so only (5,2) and (9,5) exist | 2 | 5 | 4 |

Final `maxWidth = 4`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: not resetting or normalising positions can overflow a 32-bit `int` on a deep, unbalanced tree, since positions double at every level — use `long` for position arithmetic.

- The width counts the gap even when the middle nodes are `null`; only the leftmost and rightmost present nodes of the level matter.
- Related problems: Binary Tree Level Order Traversal (needs only node values, not positions), Maximum Level Sum of a Binary Tree (reduces a level to a sum instead of a span).
