---
card: leetcode-patterns
gi: 136
slug: path-sum-ii
title: Path Sum II
---

## 1. What it is

Given the `root` of a binary tree and an integer `targetSum`, return ALL root-to-leaf paths where the node values add up to exactly `targetSum`. Each path is returned as a list of node values, in order from root to leaf. Example: `root = [5,4,8,11,null,13,4,7,2,null,null,5,1]`, `targetSum = 22` → `[[5,4,11,2],[5,8,4,5]]`.

## 2. Why & when

This extends Path Sum by needing the actual paths, not just a yes/no answer, which means you must track the current path as you descend and remove the last step when you backtrack. It belongs in this section as the natural next step after Path Sum: same pre-order "carry state down" shape, plus a `List` used as a shared, mutable path buffer that is added to on the way down and undone on the way back up.

## 3. Core concept

**Key idea:** carry both a running `remaining` sum and a `currentPath` list down the recursion. Add the current node to `currentPath` before recursing into its children; if a leaf's value exactly uses up the remaining sum, copy `currentPath` into the result. After both recursive calls return, remove the current node from `currentPath` — this is the backtrack step, since the same list is reused for every branch.

**Steps:**
1. Base case: if `node == null`, return (nothing to add).
2. Add: `currentPath.add(node.val)`, `remaining -= node.val`.
3. Base case: if `node` is a leaf and `remaining == 0`, copy `currentPath` into the result list.
4. Recurse: call on `node.left` and `node.right` with the updated `remaining` and the same `currentPath`.
5. Backtrack: `currentPath.removeLast()` — undo step 2's addition before returning to the caller, so the parent's next branch starts clean.

**Why it is correct:** because `currentPath` is one shared list reused across every recursive branch, the backtrack step (removing the last element after both children return) is essential — without it, values from an already-explored branch would still be sitting in the list when a sibling branch runs, producing wrong paths.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="currentPath grows going down and shrinks going back up (backtracking)">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="170" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="170" y="84" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="140" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="140" y="134" fill="#e6edf3" text-anchor="middle">11</text>
    <circle cx="120" cy="170" r="12" fill="#161b22" stroke="#3fb950"/><text x="120" y="174" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <line x1="222" y1="43" x2="178" y2="68" stroke="#3fb950" stroke-width="2"/>
    <line x1="162" y1="93" x2="146" y2="118" stroke="#3fb950" stroke-width="2"/>
    <line x1="135" y1="142" x2="124" y2="160" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="15" fill="#e6edf3">Down: path=[5] -&gt; [5,4] -&gt; [5,4,11] -&gt; [5,4,11,2], leaf, remaining=0 -&gt; record</text>
    <text x="10" y="185" fill="#e6edf3">Up (backtrack): [5,4,11,2] -&gt; [5,4,11] -&gt; [5,4] -&gt; [5] -&gt; [] before trying next branch</text>
  </g>
</svg>

The path list grows on the way down and is trimmed back on the way up, so the same list can be reused for the next branch.

## 5. Runnable example

```java
// PathSumII.java
import java.util.*;

public class PathSumII {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: build a brand-new list at every recursive
    // call (instead of one shared, mutated list), so no backtracking
    // step is needed, but it costs O(n) extra copying per root-to-leaf
    // path instead of O(1) amortized append/remove on a shared list.
    static List<List<Integer>> bruteForce(TreeNode root, int targetSum) {
        List<List<Integer>> result = new ArrayList<>();
        collect(root, targetSum, new ArrayList<>(), result);
        return result;
    }

    static void collect(TreeNode node, int remaining, List<Integer> pathSoFar, List<List<Integer>> result) {
        if (node == null) return;
        List<Integer> newPath = new ArrayList<>(pathSoFar);
        newPath.add(node.val);
        int newRemaining = remaining - node.val;
        if (node.left == null && node.right == null && newRemaining == 0) {
            result.add(newPath);
            return;
        }
        collect(node.left, newRemaining, newPath, result);
        collect(node.right, newRemaining, newPath, result);
    }

    // KEY INSIGHT: one shared, mutable list avoids copying the path at
    // every node -- add before recursing, remove after both children
    // return (backtrack), so the list is always correct for whichever
    // branch is currently being explored.

    // Level 2 -- Optimal: shared currentPath list with backtracking.
    // O(n) time overall (each node added and removed once), O(h) space
    // for the recursion stack plus the path list.
    public static List<List<Integer>> pathSum(TreeNode root, int targetSum) {
        List<List<Integer>> result = new ArrayList<>();
        dfs(root, targetSum, new ArrayList<>(), result);
        return result;
    }

    static void dfs(TreeNode node, int remaining, List<Integer> currentPath, List<List<Integer>> result) {
        if (node == null) return;
        currentPath.add(node.val);
        remaining -= node.val;
        if (node.left == null && node.right == null && remaining == 0) {
            result.add(new ArrayList<>(currentPath));
        } else {
            dfs(node.left, remaining, currentPath, result);
            dfs(node.right, remaining, currentPath, result);
        }
        currentPath.remove(currentPath.size() - 1);
    }

    // Level 3 -- Hardened: a leaf-only path that sums correctly at a
    // shallow depth must not block sibling branches from being explored
    // -- the backtrack after each call must run regardless of whether a
    // match was recorded.
    static List<List<Integer>> hardened(TreeNode root, int targetSum) {
        return pathSum(root, targetSum);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(5,
            new TreeNode(4, new TreeNode(11, new TreeNode(7), new TreeNode(2)), null),
            new TreeNode(8, new TreeNode(13), new TreeNode(4, new TreeNode(5), new TreeNode(1))));

        System.out.println(bruteForce(root, 22));
        System.out.println(pathSum(root, 22));
        System.out.println(hardened(root, 100));
    }
}
```

How to run: save as `PathSumII.java`, then run `java PathSumII.java`.

## 6. Walkthrough

Dry run of `dfs` on the path `5 -> 4 -> 11 -> 2` (part of the tree above, `targetSum = 22`):

| node | currentPath after add | remaining | is leaf & remaining==0? | action |
|---|---|---|---|---|
| 5 | [5] | 17 | no | recurse left |
| 4 | [5,4] | 13 | no | recurse left |
| 11 | [5,4,11] | 2 | no | recurse left (7), then right (2) |
| 7 | [5,4,11,7] | -5 | leaf, but remaining != 0 | backtrack, remove 7 |
| 2 | [5,4,11,2] | 0 | leaf, remaining == 0 | record `[5,4,11,2]`, backtrack, remove 2 |

After both children of `11` return, `11` is removed, then `4`, then `5` — leaving `currentPath` empty and ready for the sibling branch through `8`. Time complexity: O(n) to visit every node, plus O(n) total for copying matched paths. Space complexity: O(h) for the recursion stack and the shared path list.

## 7. Gotchas & takeaways

> Gotcha: adding `new ArrayList<>(currentPath)` (a copy) instead of `currentPath` itself when recording a match is required — storing the live `currentPath` reference directly would mean every recorded "match" keeps changing as later backtracking mutates the same list, corrupting every previously saved answer.

- The `currentPath.remove(...)` backtrack step must run unconditionally, after both recursive calls, not only in the `else` branch — otherwise a node that WAS a valid leaf match is never removed, and its value leaks into sibling paths.
- Related problems: Path Sum (the yes/no version this problem extends with actual path collection), Binary Tree Level Order Traversal (a different traversal shape, but with the same "build a list per branch/level" idea).
