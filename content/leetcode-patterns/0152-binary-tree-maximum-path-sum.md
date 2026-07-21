---
card: leetcode-patterns
gi: 152
slug: binary-tree-maximum-path-sum
title: Binary Tree Maximum Path Sum
---

## 1. What it is

Given the `root` of a binary tree, return the maximum sum of any non-empty path. A path is any sequence of nodes connected by edges, where each node appears at most once; it does NOT need to pass through the root, and it does not need to end at a leaf. Example: `root = [-10,9,20,null,null,15,7]` → `42` (path `15 -> 20 -> 7`, none of which is the root).

## 2. Why & when

This is the general version of Diameter of Binary Tree: instead of maximizing a COUNT of edges through each node, you maximize a SUM of values through each node, and negative values mean a branch can actively hurt rather than just add zero extra length. It belongs in this section because both problems use the exact same "post-order combine, update a global best at every node" shape — only the combine formula changes.

## 3. Core concept

**Key idea:** define `bestDownward(node)` — the maximum sum of a path that starts at `node` and goes down into at most one child (needed because a path passed UP to a parent can only continue through one side, never branch). Separately, at every node, compute the best "through this node as the peak" value using BOTH children, and update a global maximum with it.

**Steps:**
1. Keep a global `maxPathSum` variable, initialized to negative infinity.
2. Define `bestDownward(node)`: base case, if `node == null`, return `0`.
3. Recurse: `leftGain = max(bestDownward(node.left), 0)` (clamp negative contributions to `0` — skip a child branch entirely if it would only hurt).
4. Recurse: `rightGain = max(bestDownward(node.right), 0)`.
5. Update: `maxPathSum = max(maxPathSum, node.val + leftGain + rightGain)` (the best path with `node` as its highest point, possibly using both children).
6. Return `node.val + max(leftGain, rightGain)` (what this node can contribute UPWARD to its own parent — only one side, since a path continuing to the parent cannot branch both ways).

**Why it is correct:** clamping each child's gain to at least `0` correctly models "don't extend the path through a branch that would only decrease the sum"; the global `maxPathSum` check considers every node as a potential path "peak" (using both children at once), which covers every possible path in the tree, while the RETURN value only ever offers one side upward, since a valid path can bend at most once (at its peak) and must otherwise run in a single unbroken line.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A node's peak value uses both children; its return value upward uses only the better one">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#f85149"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">-10</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">9</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#3fb950"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">20</text>
    <circle cx="270" cy="140" r="14" fill="#161b22" stroke="#3fb950"/><text x="270" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">15</text>
    <circle cx="330" cy="140" r="14" fill="#161b22" stroke="#3fb950"/><text x="330" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">7</text>
    <line x1="222" y1="43" x2="168" y2="72" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="292" y2="72" stroke="#3fb950" stroke-width="2"/>
    <line x1="292" y1="98" x2="276" y2="126" stroke="#3fb950" stroke-width="2"/>
    <line x1="308" y1="98" x2="324" y2="126" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="175" fill="#e6edf3">Peak at 20: uses BOTH children (15+20+7=42); root -10 is never worth including</text>
  </g>
</svg>

The best path (green) peaks at `20`, using both its children — it never needs to pass through the negative root.

## 5. Runnable example

```java
// BinaryTreeMaximumPathSum.java
public class BinaryTreeMaximumPathSum {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: for every node, treat it as the path's
    // starting point and separately compute the best downward-only path
    // sum from it (no "both children at once" check), then also check
    // each subtree independently. This misses the "peak with both
    // children" case entirely unless carefully special-cased, and is
    // included here only to contrast with the correct combine below --
    // in practice, getting this right without the peak-tracking trick
    // requires effectively reimplementing Level 2's logic per node.
    // O(n^2) time if done as repeated per-node downward scans.
    static int bruteForce(TreeNode root) {
        maxSeen = Integer.MIN_VALUE;
        scanEveryNodeAsPeak(root);
        return maxSeen;
    }

    static int maxSeen;

    static void scanEveryNodeAsPeak(TreeNode node) {
        if (node == null) return;
        int leftGain = Math.max(downwardOnly(node.left), 0);
        int rightGain = Math.max(downwardOnly(node.right), 0);
        maxSeen = Math.max(maxSeen, node.val + leftGain + rightGain);
        scanEveryNodeAsPeak(node.left);
        scanEveryNodeAsPeak(node.right);
    }

    static int downwardOnly(TreeNode node) {
        if (node == null) return 0;
        int leftGain = Math.max(downwardOnly(node.left), 0);
        int rightGain = Math.max(downwardOnly(node.right), 0);
        return node.val + Math.max(leftGain, rightGain);
    }

    // KEY INSIGHT: a single post-order pass can compute BOTH the
    // "downward only" value to return upward AND update a global best
    // "peak using both children" value at the same time -- no need to
    // call a separate downward-only helper repeatedly for every node.

    // Level 2 -- Optimal: one post-order pass, tracking a global max
    // while returning the single-side downward gain. O(n) time, O(h)
    // space (recursion stack).
    static int maxPathSum;

    public static int maxPathSum(TreeNode root) {
        maxPathSum = Integer.MIN_VALUE;
        bestDownward(root);
        return maxPathSum;
    }

    static int bestDownward(TreeNode node) {
        if (node == null) return 0;
        int leftGain = Math.max(bestDownward(node.left), 0);
        int rightGain = Math.max(bestDownward(node.right), 0);
        maxPathSum = Math.max(maxPathSum, node.val + leftGain + rightGain);
        return node.val + Math.max(leftGain, rightGain);
    }

    // Level 3 -- Hardened: a tree where every value is negative must
    // still return the single largest (least negative) node value,
    // since a path must be non-empty and clamping gains to 0 correctly
    // avoids ever forcing a negative branch into the answer.
    static int hardened(TreeNode root) {
        return maxPathSum(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(-10,
            new TreeNode(9),
            new TreeNode(20, new TreeNode(15), new TreeNode(7)));

        System.out.println(bruteForce(root));
        System.out.println(maxPathSum(root));

        TreeNode allNegative = new TreeNode(-3, new TreeNode(-2), null);
        System.out.println(hardened(allNegative));
    }
}
```

How to run: save as `BinaryTreeMaximumPathSum.java`, then run `java BinaryTreeMaximumPathSum.java`.

## 6. Walkthrough

Dry run of `bestDownward` on `[-10,9,20,null,null,15,7]`:

| call | leftGain | rightGain | maxPathSum after | returns (upward) |
|---|---|---|---|---|
| bestDownward(9) | 0 | 0 | max(-inf, 9)=9 | 9 |
| bestDownward(15) | 0 | 0 | max(9, 15)=15 | 15 |
| bestDownward(7) | 0 | 0 | max(15, 7)=15 (unchanged) | 7 |
| bestDownward(20) | max(15,0)=15 | max(7,0)=7 | max(15, 20+15+7=42)=42 | `20 + max(15,7) = 35` |
| bestDownward(-10) | max(9,0)=9 | max(35,0)=35 | max(42, -10+9+35=34)=42 (unchanged) | `-10 + max(9,35) = 25` |

Final `maxPathSum = 42`, from the path `15 -> 20 -> 7` discovered when `20` was processed as a peak. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting to clamp `leftGain`/`rightGain` to at least `0` (using `Math.max(bestDownward(child), 0)`) means a negative-value branch would be forced into both the peak calculation and the upward return value, even when simply excluding that branch would give a better sum.

- The RETURN value (usable by a parent) and the GLOBAL max (the final answer) are two different things computed in the same pass — the return value can only ever include one child's contribution, while the global max is allowed to use both, since only the global max represents a complete, standalone path.
- Related problems: Diameter of Binary Tree (the exact same two-value technique — a returned "single-side" value plus a globally tracked best — applied to edge counts instead of value sums), House Robber III (also returns extra information from every node to avoid recomputation, there a pair of mutually exclusive totals).
