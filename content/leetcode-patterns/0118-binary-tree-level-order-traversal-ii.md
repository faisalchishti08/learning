---
card: leetcode-patterns
gi: 118
slug: binary-tree-level-order-traversal-ii
title: Binary Tree Level Order Traversal II
---

## 1. What it is

Given the `root` of a binary tree, return its node values level by level, but with the levels ordered bottom-up: the deepest level first, the root's level last. Example: `root = [3,9,20,null,null,15,7]` → `[[15,7],[9,20],[3]]`.

## 2. Why & when

This is plain level-order BFS with the final list reversed. Tree BFS already builds one list per level from top to bottom; this problem only asks for those lists in the opposite order. It belongs in this section because `levelSize` is still what separates the levels — reversing the list of levels is a small transform applied after the traversal, not a change to the traversal itself.

## 3. Core concept

**Key idea:** run the standard level-order BFS, building the result top-down exactly as usual. Once the traversal finishes, reverse the outer list so the deepest level ends up first.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Collect the level's values into `currentLevel`, same as plain level order.
   - Append `currentLevel` to the result.
3. Reverse the result list (the list of levels, not the values inside each level).
4. Return the reversed result.

**Why it is correct:** BFS always finishes a level before starting the next, so the result is built in strict top-to-bottom order; reversing that finished list swaps top-to-bottom into bottom-to-top without touching the order of values inside any single level.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing the list of levels after a normal top-down BFS">
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
    <text x="10" y="185" fill="#e6edf3">Top-down: [[3],[9,20],[15,7]] -&gt; reversed: [[15,7],[9,20],[3]]</text>
  </g>
</svg>

BFS still builds levels top to bottom; only the final list of levels gets reversed.

## 5. Runnable example

```java
// BinaryTreeLevelOrderTraversalII.java
import java.util.*;

public class BinaryTreeLevelOrderTraversalII {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS with a depth argument, inserting each
    // new level's list at index 0 instead of appending. O(n) time, but
    // inserting at the front of an ArrayList is O(levels) per insert,
    // making the depth bookkeeping more expensive than it needs to be.
    static List<List<Integer>> bruteForce(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        dfs(root, 0, result);
        return result;
    }

    static void dfs(TreeNode node, int depth, List<List<Integer>> result) {
        if (node == null) return;
        if (depth >= result.size()) result.add(0, new ArrayList<>());
        result.get(result.size() - 1 - depth).add(node.val);
        dfs(node.left, depth + 1, result);
        dfs(node.right, depth + 1, result);
    }

    // KEY INSIGHT: building the levels top-down with a plain queue is the
    // same amount of work as building them any other way, so it is cheaper
    // to append normally and reverse the finished list once at the end.

    // Level 2 -- Optimal: BFS with levelSize, appending each level
    // normally, then one reversal at the end. O(n) time, O(w) space
    // (widest level in the queue).
    public static List<List<Integer>> levelOrderBottom(TreeNode root) {
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
        Collections.reverse(result);
        return result;
    }

    // Level 3 -- Hardened: an empty tree must return an empty list, and
    // reversing that empty list must not throw or add a phantom level.
    static List<List<Integer>> hardened(TreeNode root) {
        return levelOrderBottom(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        root.left = new TreeNode(9);
        root.right = new TreeNode(20);
        root.right.left = new TreeNode(15);
        root.right.right = new TreeNode(7);

        System.out.println(bruteForce(root));
        System.out.println(levelOrderBottom(root));
        System.out.println(hardened(null));
    }
}
```

How to run: save as `BinaryTreeLevelOrderTraversalII.java`, then run `java BinaryTreeLevelOrderTraversalII.java`.

## 6. Walkthrough

Dry run of `levelOrderBottom` on `[3,9,20,null,null,15,7]`:

| step | action | result so far |
|---|---|---|
| level 0 | collect [3] | [[3]] |
| level 1 | collect [9,20] | [[3],[9,20]] |
| level 2 | collect [15,7] | [[3],[9,20],[15,7]] |
| reverse | flip outer list | [[15,7],[9,20],[3]] |

Final result: `[[15,7],[9,20],[3]]`. Time complexity: O(n) for the traversal plus O(number of levels) for the reversal, which is bounded by O(n); overall O(n). Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: reversing the values inside each level (instead of the outer list of levels) gives left-right-flipped rows in the right order — always call `Collections.reverse` on the outer list, not on each `currentLevel`.

- Appending normally and reversing once at the end is simpler and no slower than inserting at index `0` on every level, which costs O(levels) per insert on an `ArrayList`.
- Related problems: Binary Tree Level Order Traversal (the top-down version this builds on), Binary Tree Zigzag Level Order Traversal (reverses alternating levels in place, not the whole list).
