---
card: leetcode-patterns
gi: 115
slug: binary-tree-right-side-view
title: Binary Tree Right Side View
---

## 1. What it is

Given the `root` of a binary tree, return the values you would see standing on the right side of the tree, ordered from top to bottom — that is, the last (rightmost) node of each level. Example: `root = [1,2,3,null,5,null,4]` → `[1,3,4]`.

## 2. Why & when

This is a small variant of level-order BFS: instead of collecting every value in a level, you only keep the last one dequeued. It belongs in this section because `levelSize` is what tells you which dequeue is the last one in the level — the one visible from the right.

## 3. Core concept

**Key idea:** run level-order BFS. For each level, note the value of the node dequeued at index `levelSize - 1` (the last one in that level) and add only that value to the result.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Loop `levelSize` times with index `i`: dequeue a node, push its non-null children; if `i == levelSize - 1`, add the node's value to the result.
3. Return the result.

**Why it is correct:** `levelSize` fixes exactly how many dequeues belong to the current level, so the dequeue at position `levelSize - 1` is guaranteed to be the rightmost node visited in that level, regardless of how many children it or its siblings have.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Only the rightmost node of each level is kept">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="35" r="16" fill="#161b22" stroke="#3fb950"/><text x="230" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="300" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="190" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="190" y="150" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="330" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="330" y="150" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="222" y1="49" x2="168" y2="77" stroke="#8b949e"/>
    <line x1="238" y1="49" x2="292" y2="77" stroke="#8b949e"/>
    <line x1="172" y1="104" x2="188" y2="132" stroke="#8b949e"/>
    <line x1="308" y1="104" x2="326" y2="132" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Right side view: [1, 3, 4] (green nodes)</text>
  </g>
</svg>

The green nodes are the last one dequeued at each level — the ones visible when looking from the right.

## 5. Runnable example

```java
// BinaryTreeRightSideView.java
import java.util.*;

public class BinaryTreeRightSideView {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS that always visits right before left,
    // recording the first node seen at each new depth. O(n) time, correct
    // but relies on remembering to flip the usual left-first DFS order.
    static List<Integer> bruteForce(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        dfsRightFirst(root, 0, result);
        return result;
    }

    static void dfsRightFirst(TreeNode node, int depth, List<Integer> result) {
        if (node == null) return;
        if (depth == result.size()) result.add(node.val);
        dfsRightFirst(node.right, depth + 1, result);
        dfsRightFirst(node.left, depth + 1, result);
    }

    // KEY INSIGHT: BFS already visits every node of a level in left-to-right
    // order, so the node dequeued at index levelSize - 1 is always the
    // rightmost one -- no need to reverse traversal order like DFS does.

    // Level 2 -- Optimal: BFS with levelSize, keeping only the last
    // dequeue of each level. O(n) time, O(w) space (widest level).
    public static List<Integer> rightSideView(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
                if (i == levelSize - 1) result.add(node.val);
            }
        }
        return result;
    }

    // Level 3 -- Hardened: a level whose rightmost node has no right
    // child (like node 2 above, whose child 5 is on the left) must still
    // report 5, not skip the level.
    static List<Integer> hardened(TreeNode root) {
        return rightSideView(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2);
        root.right = new TreeNode(3);
        root.left.right = new TreeNode(5);
        root.right.right = new TreeNode(4);

        System.out.println(bruteForce(root));
        System.out.println(rightSideView(root));
        System.out.println(hardened(root));
    }
}
```

How to run: save as `BinaryTreeRightSideView.java`, then run `java BinaryTreeRightSideView.java`.

## 6. Walkthrough

Dry run of `rightSideView` on `[1,2,3,null,5,null,4]`:

| level | levelSize | dequeue order | i == levelSize-1? | value added |
|---|---|---|---|---|
| 0 | 1 | 1 (i=0) | yes | 1 |
| 1 | 2 | 2 (i=0), 3 (i=1) | i=1 yes | 3 |
| 2 | 2 | 5 (i=0), 4 (i=1) | i=1 yes | 4 |

Final result: `[1, 3, 4]`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: assuming the rightmost node always has a right child is wrong — node `5` is a left child of `2`, but it is still the last node dequeued in its level, so it is still the visible one.

- The check `i == levelSize - 1` looks at dequeue order within the level, not whether a node is a "right child" — that is what makes it work even when the tree is unbalanced.
- Related problems: Binary Tree Level Order Traversal (collect the whole level instead of just the last node), Populating Next Right Pointers in Each Node (links every node in a level instead of picking one).
