---
card: leetcode-patterns
gi: 122
slug: even-odd-tree
title: Even Odd Tree
---

## 1. What it is

Given the `root` of a binary tree, return `true` if it is an "even-odd" tree. A binary tree is even-odd when: (1) nodes on even-indexed levels (0, 2, 4, ...) hold odd values that strictly increase left to right, and (2) nodes on odd-indexed levels (1, 3, 5, ...) hold even values that strictly decrease left to right. Example: `root = [1,10,4,3,null,7,9,12,8,6,null,null,2]` → `true`.

## 2. Why & when

Checking a per-level property (odd/even parity, strictly increasing or decreasing) is exactly what Tree BFS is built for: each level is inspected in isolation, in left-to-right dequeue order, before moving to the next. It belongs in this section because `levelSize` again marks where one level's checks stop and the next level's checks — with the opposite parity rule — begin.

## 3. Core concept

**Key idea:** run level-order BFS, tracking the current level's index. On even levels, verify every value is odd and strictly greater than the previous value seen at this level; on odd levels, verify every value is even and strictly less than the previous value. Any violation fails the whole tree immediately.

**Steps:**
1. Push `root` onto the queue. Set `levelIndex = 0`.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`. Set `previousValue = null`.
   - Loop `levelSize` times: dequeue a node; check its parity against `levelIndex % 2`; check its ordering against `previousValue`; if either check fails, return `false`; update `previousValue`; push non-null children.
   - Increment `levelIndex`.
3. If the whole traversal finishes without a failed check, return `true`.

**Why it is correct:** the `levelIndex` parity flips exactly once per fully-drained level, and `previousValue` resets to `null` at the start of each level, so the ordering check never compares values from two different levels against each other.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Even levels increase with odd values, odd levels decrease with even values">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="35" r="16" fill="#161b22" stroke="#3fb950"/><text x="240" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="170" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="170" y="95" fill="#e6edf3" text-anchor="middle">10</text>
    <circle cx="310" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="310" y="95" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="130" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="130" y="150" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="270" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="270" y="150" fill="#e6edf3" text-anchor="middle">7</text>
    <circle cx="350" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="350" y="150" fill="#e6edf3" text-anchor="middle">9</text>
    <line x1="232" y1="49" x2="178" y2="77" stroke="#8b949e"/>
    <line x1="248" y1="49" x2="302" y2="77" stroke="#8b949e"/>
    <line x1="163" y1="104" x2="135" y2="132" stroke="#8b949e"/>
    <line x1="303" y1="104" x2="275" y2="132" stroke="#8b949e"/>
    <line x1="317" y1="104" x2="347" y2="132" stroke="#8b949e"/>
    <text x="10" y="185" fill="#e6edf3">Level 0 (even): 1 odd. Level 1 (odd): 10 &gt; 4, both even. Level 2 (even): 3 &lt; 7 &lt; 9, all odd.</text>
  </g>
</svg>

Green nodes sit on even levels and must strictly increase; blue nodes sit on odd levels and must strictly decrease.

## 5. Runnable example

```java
// EvenOddTree.java
import java.util.*;

public class EvenOddTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: DFS collecting all values per depth into
    // lists first, then validating each list's parity and ordering in a
    // second pass. O(n) time, O(n) extra space for the per-level lists,
    // and two passes instead of validating while draining the queue.
    static boolean bruteForce(TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        collect(root, 0, levels);
        for (int levelIndex = 0; levelIndex < levels.size(); levelIndex++) {
            List<Integer> level = levels.get(levelIndex);
            boolean evenLevel = levelIndex % 2 == 0;
            for (int i = 0; i < level.size(); i++) {
                int value = level.get(i);
                if (evenLevel && value % 2 == 0) return false;
                if (!evenLevel && value % 2 != 0) return false;
                if (i > 0) {
                    int previous = level.get(i - 1);
                    if (evenLevel && value <= previous) return false;
                    if (!evenLevel && value >= previous) return false;
                }
            }
        }
        return true;
    }

    static void collect(TreeNode node, int depth, List<List<Integer>> levels) {
        if (node == null) return;
        if (depth == levels.size()) levels.add(new ArrayList<>());
        levels.get(depth).add(node.val);
        collect(node.left, depth + 1, levels);
        collect(node.right, depth + 1, levels);
    }

    // KEY INSIGHT: validating a level requires only the previous value
    // seen at that same level, so checking while draining the BFS queue
    // avoids storing every level's full list before validating it.

    // Level 2 -- Optimal: BFS with levelSize, validating parity and order
    // inline as each level drains. O(n) time, O(w) space (widest level).
    public static boolean isEvenOddTree(TreeNode root) {
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int levelIndex = 0;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            boolean evenLevel = levelIndex % 2 == 0;
            Integer previousValue = null;
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                int value = node.val;
                if (evenLevel && value % 2 == 0) return false;
                if (!evenLevel && value % 2 != 0) return false;
                if (previousValue != null) {
                    if (evenLevel && value <= previousValue) return false;
                    if (!evenLevel && value >= previousValue) return false;
                }
                previousValue = value;
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            levelIndex++;
        }
        return true;
    }

    // Level 3 -- Hardened: a single-node tree (one value, no ordering to
    // check) must return true whenever that value's parity matches level 0.
    static boolean hardened(TreeNode root) {
        return isEvenOddTree(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(10, new TreeNode(3), null),
            new TreeNode(4, new TreeNode(7), new TreeNode(9)));

        System.out.println(bruteForce(root));
        System.out.println(isEvenOddTree(root));
        System.out.println(hardened(new TreeNode(1)));
    }
}
```

How to run: save as `EvenOddTree.java`, then run `java EvenOddTree.java`.

## 6. Walkthrough

Dry run of `isEvenOddTree` on the example tree:

| level | evenLevel | dequeued values | check |
|---|---|---|---|
| 0 | true | 1 | odd, ok |
| 1 | false | 10, 4 | both even, 10 &gt; 4, decreasing, ok |
| 2 | true | 3, 7, 9 | all odd, 3 &lt; 7 &lt; 9, increasing, ok |

All levels pass, so the final result is `true`. Time complexity: O(n), every node visited once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: using `<=` or `>=` instead of strict `<`/`>` silently accepts equal adjacent values, but the problem requires STRICT increase or decrease — equal neighbours must fail the check.

- Resetting `previousValue` to `null` at the start of every level is essential; otherwise the last value of one level gets compared against the first value of the next, which uses the wrong parity rule.
- Related problems: Binary Tree Level Order Traversal (the same per-level draining, without validation), Maximum Width of Binary Tree (also reasons about a level's span, but by position, not by value ordering).
