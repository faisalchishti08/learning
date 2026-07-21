---
card: leetcode-patterns
gi: 123
slug: deepest-leaves-sum
title: Deepest Leaves Sum
---

## 1. What it is

Given the `root` of a binary tree, return the sum of the values of the nodes at the deepest level. Example: `root = [1,2,3,4,5,null,6,7,null,null,null,null,8]` → `15` (the deepest level holds `7` and `8`, and `7 + 8 = 15`).

## 2. Why & when

Tree BFS visits levels in order and always finishes one level completely before starting the next, so the last level it finishes is guaranteed to be the deepest one. It belongs in this section because you do not need to know the tree's height in advance — BFS discovers the deepest level naturally, by simply overwriting the running answer every level until the queue empties.

## 3. Core concept

**Key idea:** run level-order BFS, summing each level's values into a variable that gets reset at the start of every level. Because the loop only stops when the queue is empty (after the last, deepest level), the final value of that variable is the deepest level's sum.

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Set `levelSum = 0`.
   - Loop `levelSize` times: dequeue a node, add its value to `levelSum`, push its non-null children.
3. After the loop ends, `levelSum` holds the sum of the last level processed — the deepest one. Return it.

**Why it is correct:** the loop condition `while (!queue.isEmpty())` only stops once no level remains, so the last assignment to `levelSum` before the loop exits is necessarily the deepest level's sum; no extra depth tracking is needed.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The last level BFS finishes is always the deepest">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="30" r="14" fill="#161b22" stroke="#79c0ff"/><text x="240" y="34" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="180" cy="75" r="14" fill="#161b22" stroke="#79c0ff"/><text x="180" y="79" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="300" cy="75" r="14" fill="#161b22" stroke="#79c0ff"/><text x="300" y="79" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="150" cy="120" r="14" fill="#161b22" stroke="#79c0ff"/><text x="150" y="124" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="210" cy="120" r="14" fill="#161b22" stroke="#79c0ff"/><text x="210" y="124" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <circle cx="330" cy="120" r="14" fill="#161b22" stroke="#79c0ff"/><text x="330" y="124" fill="#e6edf3" text-anchor="middle" font-size="11">6</text>
    <circle cx="150" cy="165" r="14" fill="#161b22" stroke="#3fb950"/><text x="150" y="169" fill="#e6edf3" text-anchor="middle" font-size="11">7</text>
    <circle cx="330" cy="165" r="14" fill="#161b22" stroke="#3fb950"/><text x="330" y="169" fill="#e6edf3" text-anchor="middle" font-size="11">8</text>
    <line x1="234" y1="43" x2="186" y2="63" stroke="#8b949e"/>
    <line x1="246" y1="43" x2="294" y2="63" stroke="#8b949e"/>
    <line x1="174" y1="87" x2="154" y2="108" stroke="#8b949e"/>
    <line x1="322" y1="87" x2="332" y2="108" stroke="#8b949e"/>
    <line x1="148" y1="132" x2="150" y2="153" stroke="#8b949e"/>
    <line x1="332" y1="132" x2="330" y2="153" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Deepest level (green): 7 + 8 = 15</text>
  </g>
</svg>

The loop keeps overwriting `levelSum`; whatever value it holds when the queue finally empties belongs to the deepest level.

## 5. Runnable example

```java
// DeepestLeavesSum.java
import java.util.*;

public class DeepestLeavesSum {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: DFS tracking the maximum depth seen so far
    // and the running sum for that depth; reset the sum whenever a
    // strictly deeper node is found. O(n) time, but needs two mutable
    // fields threaded through recursion instead of one loop variable.
    static int bruteForce(TreeNode root) {
        int[] maxDepth = {-1};
        int[] sum = {0};
        dfs(root, 0, maxDepth, sum);
        return sum[0];
    }

    static void dfs(TreeNode node, int depth, int[] maxDepth, int[] sum) {
        if (node == null) return;
        if (depth > maxDepth[0]) { maxDepth[0] = depth; sum[0] = 0; }
        if (depth == maxDepth[0]) sum[0] += node.val;
        dfs(node.left, depth + 1, maxDepth, sum);
        dfs(node.right, depth + 1, maxDepth, sum);
    }

    // KEY INSIGHT: BFS's queue empties right after the deepest level is
    // drained, so simply overwriting levelSum every iteration -- with no
    // "is this deeper?" check at all -- leaves the correct sum behind.

    // Level 2 -- Optimal: BFS with levelSize, overwriting levelSum every
    // level. O(n) time, O(w) space (widest level).
    public static int deepestLeavesSum(TreeNode root) {
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int levelSum = 0;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            levelSum = 0;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                levelSum += node.val;
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
        }
        return levelSum;
    }

    // Level 3 -- Hardened: a single-node tree must return that node's own
    // value, since its one level is also the deepest level.
    static int hardened(TreeNode root) {
        return deepestLeavesSum(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4, new TreeNode(7), null), new TreeNode(5)),
            new TreeNode(3, null, new TreeNode(6, null, new TreeNode(8))));

        System.out.println(bruteForce(root));
        System.out.println(deepestLeavesSum(root));
        System.out.println(hardened(new TreeNode(9)));
    }
}
```

How to run: save as `DeepestLeavesSum.java`, then run `java DeepestLeavesSum.java`.

## 6. Walkthrough

Dry run of `deepestLeavesSum` on the example tree:

| level | levelSize | dequeued | levelSum |
|---|---|---|---|
| 0 | 1 | 1 | 1 |
| 1 | 2 | 2, 3 | 5 |
| 2 | 3 | 4, 5, 6 | 15 |
| 3 | 2 | 7, 8 | 15 |

After level 3 the queue is empty, so the loop stops with `levelSum = 15`, the sum of `7` and `8`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: initializing `levelSum` once before the loop and only adding to it (never resetting) accidentally sums every node in the whole tree, not just the deepest level — `levelSum` must be reset to `0` inside the outer loop, at the start of each level.

- No explicit depth tracking or comparison is needed; the queue naturally empties right after the deepest level, so "the last value written" is "the deepest level's sum" for free.
- Related problems: Maximum Depth of Binary Tree (needs only the depth number, not the leaf sum), Average of Levels in Binary Tree (keeps every level's result instead of only the last one).
