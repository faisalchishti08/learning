---
card: leetcode-patterns
gi: 114
slug: binary-tree-zigzag-level-order-traversal
title: Binary Tree Zigzag Level Order Traversal
---

## 1. What it is

Given the `root` of a binary tree, return its node values level by level, but alternate the reading direction: level 0 left-to-right, level 1 right-to-left, level 2 left-to-right, and so on. Example: `root = [3,9,20,null,null,15,7]` → `[[3],[20,9],[15,7]]`.

## 2. Why & when

This builds directly on plain level-order BFS. Tree BFS already gives you one list per level in left-to-right order; zigzag only adds a direction flag that reverses every other list. It belongs in this section because the level boundary (`levelSize`) is still what separates the levels — the zigzag is a small transform applied on top.

## 3. Core concept

**Key idea:** run the standard level-order BFS. Keep a boolean flag that toggles after each level. When the flag says "reverse", reverse the collected list for that level before adding it to the result.

**Steps:**
1. Push `root` onto the queue. Set `leftToRight = true`.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Collect the level's values into `currentLevel`, same as plain level order.
   - If `leftToRight` is false, reverse `currentLevel`.
   - Append `currentLevel` to the result. Flip `leftToRight`.
3. Return the result.

**Why it is correct:** the queue always dequeues nodes left to right regardless of the flag, so `currentLevel` is always built in left-to-right order first; reversing it after collection is what produces the alternating direction, without needing to change how children are pushed.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Alternating traversal direction per level">
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
    <text x="120" y="65" fill="#3fb950">-&gt;</text>
    <text x="120" y="120" fill="#f85149">&lt;-</text>
    <text x="10" y="185" fill="#e6edf3">Result: [[3], [20,9], [15,7]]</text>
  </g>
</svg>

Level 0 reads left to right, level 1 reads right to left after being reversed, level 2 reads left to right again.

## 5. Runnable example

```java
// BinaryTreeZigzagLevelOrderTraversal.java
import java.util.*;

public class BinaryTreeZigzagLevelOrderTraversal {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: plain level order first, then reverse every
    // other inner list in a second pass. O(n) time, but does a second full
    // pass over the result instead of reversing while building it.
    static List<List<Integer>> bruteForce(TreeNode root) {
        List<List<Integer>> levels = plainLevelOrder(root);
        for (int i = 1; i < levels.size(); i += 2) {
            Collections.reverse(levels.get(i));
        }
        return levels;
    }

    static List<List<Integer>> plainLevelOrder(TreeNode root) {
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

    // KEY INSIGHT: the queue always drains left to right, so a single
    // boolean flag flipped once per level is enough to decide whether to
    // reverse that level's list -- no second pass over the whole result.

    // Level 2 -- Optimal: BFS with levelSize and a toggling direction flag.
    // O(n) time, O(w) space (widest level in the queue).
    public static List<List<Integer>> zigzagLevelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        boolean leftToRight = true;
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> currentLevel = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                currentLevel.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            if (!leftToRight) Collections.reverse(currentLevel);
            result.add(currentLevel);
            leftToRight = !leftToRight;
        }
        return result;
    }

    // Level 3 -- Hardened: a single-node tree must return [[val]], with
    // the direction flag never affecting a level of size one.
    static List<List<Integer>> hardened(TreeNode root) {
        return zigzagLevelOrder(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        root.left = new TreeNode(9);
        root.right = new TreeNode(20);
        root.right.left = new TreeNode(15);
        root.right.right = new TreeNode(7);

        System.out.println(bruteForce(root));
        System.out.println(zigzagLevelOrder(root));
        System.out.println(hardened(new TreeNode(1)));
    }
}
```

How to run: save as `BinaryTreeZigzagLevelOrderTraversal.java`, then run `java BinaryTreeZigzagLevelOrderTraversal.java`.

## 6. Walkthrough

Dry run of `zigzagLevelOrder` on `[3,9,20,null,null,15,7]`:

| level | levelSize | dequeued (order) | leftToRight | currentLevel before/after reverse |
|---|---|---|---|---|
| 0 | 1 | 3 | true | [3] / [3] |
| 1 | 2 | 9, 20 | false | [9,20] / [20,9] |
| 2 | 2 | 15, 7 | true | [15,7] / [15,7] |

Final result: `[[3], [20,9], [15,7]]`. Time complexity: O(n), every node visited once, reversal costs O(levelSize) per level which sums to O(n). Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: flipping `leftToRight` before collecting the level (instead of after) applies the reverse to the wrong level — always toggle at the end of the loop body, after the level is appended.

- Reversing `currentLevel` in place is cheaper than reversing the whole result at the end, since it touches each value once instead of doing a second full pass.
- Related problems: Binary Tree Level Order Traversal (the plain version this builds on), Binary Tree Level Order Traversal II (reverses the list of levels, not the levels themselves).
