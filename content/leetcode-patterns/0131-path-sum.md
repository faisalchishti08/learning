---
card: leetcode-patterns
gi: 131
slug: path-sum
title: Path Sum
---

## 1. What it is

Given the `root` of a binary tree and an integer `targetSum`, return `true` if there is a root-to-leaf path where the node values add up to exactly `targetSum`. Example: `root = [5,4,8,11,null,13,4,7,2,null,null,null,1]`, `targetSum = 22` → `true` (path `5 -> 4 -> 11 -> 2` sums to `22`).

## 2. Why & when

This needs the running-total-passed-down (pre-order) style of Tree DFS: at each node you subtract its value from the remaining target and hand that updated remainder to the children. It belongs in this section because you can only tell if a path sums correctly once you reach a leaf — the state (remaining sum) is built up along the way down, not combined back up.

## 3. Core concept

**Key idea:** carry a `remaining` value down the recursion, starting at `targetSum` and subtracting each node's value as you descend. A path is valid if, upon reaching a leaf, `remaining` equals exactly that leaf's value (equivalently, `remaining - leaf.val == 0`).

**Steps:**
1. Base case: if `node == null`, return `false` (an empty path cannot sum to anything).
2. Update: `remaining -= node.val`.
3. Base case: if `node` is a leaf (`left == null && right == null`), return `remaining == 0`.
4. Recurse: return `hasPathSum(node.left, remaining) || hasPathSum(node.right, remaining)`.

**Why it is correct:** the `remaining` value at any node always equals `targetSum` minus the sum of every ancestor from the root down to that node, so checking `remaining == 0` at a leaf is exactly checking that the full root-to-leaf path summed to `targetSum`.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Remaining sum shrinks as the path descends toward a leaf">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="250" y="20" fill="#3fb950" font-size="10">rem=22</text>
    <circle cx="180" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="180" y="84" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="130" y="70" fill="#3fb950" font-size="10">rem=17</text>
    <circle cx="150" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle">11</text>
    <text x="90" y="120" fill="#3fb950" font-size="10">rem=13</text>
    <circle cx="130" cy="175" r="12" fill="#161b22" stroke="#3fb950"/><text x="130" y="179" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <text x="20" y="185" fill="#3fb950" font-size="10">rem=2, leaf, 2-2=0</text>
    <line x1="222" y1="43" x2="188" y2="68" stroke="#3fb950" stroke-width="2"/>
    <line x1="172" y1="93" x2="156" y2="118" stroke="#3fb950" stroke-width="2"/>
    <line x1="145" y1="142" x2="134" y2="164" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="15" fill="#e6edf3">5 -&gt; 4 -&gt; 11 -&gt; 2: 22-5-4-11-2 = 0 -&gt; path found</text>
  </g>
</svg>

Each node subtracts its own value from the remaining target on the way down; the leaf checks if the running remainder finally hits `0`.

## 5. Runnable example

```java
// PathSum.java
public class PathSum {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: collect every root-to-leaf path's total
    // sum into a list, then scan the list for targetSum. O(n) time and
    // O(n) extra space for the list of sums, more memory than needed
    // since only a yes/no answer is required.
    static boolean bruteForce(TreeNode root, int targetSum) {
        java.util.List<Integer> sums = new java.util.ArrayList<>();
        collectPathSums(root, 0, sums);
        return sums.contains(targetSum);
    }

    static void collectPathSums(TreeNode node, int sumSoFar, java.util.List<Integer> sums) {
        if (node == null) return;
        int newSum = sumSoFar + node.val;
        if (node.left == null && node.right == null) { sums.add(newSum); return; }
        collectPathSums(node.left, newSum, sums);
        collectPathSums(node.right, newSum, sums);
    }

    // KEY INSIGHT: you do not need every path's sum -- subtracting each
    // node's value from a running "remaining" target lets a leaf check
    // "does this path sum to targetSum" with one comparison, no list.

    // Level 2 -- Optimal: pre-order DFS carrying remaining sum down.
    // O(n) time, O(h) space (recursion stack).
    public static boolean hasPathSum(TreeNode node, int remaining) {
        if (node == null) return false;
        remaining -= node.val;
        if (node.left == null && node.right == null) return remaining == 0;
        return hasPathSum(node.left, remaining) || hasPathSum(node.right, remaining);
    }

    // Level 3 -- Hardened: an empty tree must return false (no path
    // exists at all), and a single-node tree must match only when
    // targetSum equals that one node's value.
    static boolean hardened(TreeNode root, int targetSum) {
        return hasPathSum(root, targetSum);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(5,
            new TreeNode(4, new TreeNode(11, new TreeNode(7), new TreeNode(2)), null),
            new TreeNode(8, new TreeNode(13), new TreeNode(4, null, new TreeNode(1))));

        System.out.println(bruteForce(root, 22));
        System.out.println(hasPathSum(root, 22));
        System.out.println(hardened(null, 0));
    }
}
```

How to run: save as `PathSum.java`, then run `java PathSum.java`.

## 6. Walkthrough

Dry run of `hasPathSum(root, 22)` following the path `5 -> 4 -> 11 -> 2`:

| node | remaining before | remaining after | is leaf? | action |
|---|---|---|---|---|
| 5 | 22 | 17 | no | recurse left (4) |
| 4 | 17 | 13 | no | recurse left (11) |
| 11 | 13 | 2 | no | recurse left (7) first, fails; then recurse right (2) |
| 2 | 2 | 0 | yes | `remaining == 0` -> true |

The `7` branch is tried first (`remaining` would become `2 - 7 = -5`, not `0` at that leaf, so it returns `false`), then the `2` branch succeeds. Time complexity: O(n) worst case, every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: checking `remaining == 0` at any node (not just a leaf) would wrongly accept a path that stops early at an internal node — the sum must be checked ONLY when `node.left == null && node.right == null`, i.e. a genuine root-to-leaf path.

- Negative values in the tree mean `remaining` is not guaranteed to shrink toward `0` monotonically, so there is no early-exit shortcut — the full recursion must run.
- Related problems: Path Sum II (collects every matching path, not just a yes/no answer), Diameter of Binary Tree (a different post-order combine that also walks every root-to-leaf-shaped path, but measures length, not value sum).
