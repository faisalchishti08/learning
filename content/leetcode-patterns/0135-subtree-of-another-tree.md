---
card: leetcode-patterns
gi: 135
slug: subtree-of-another-tree
title: Subtree of Another Tree
---

## 1. What it is

Given the roots of two binary trees, `root` and `subRoot`, return `true` if there is a node in `root` such that the subtree rooted at that node is identical (structure and values) to the tree rooted at `subRoot`. Example: `root = [3,4,5,1,2]`, `subRoot = [4,1,2]` → `true`.

## 2. Why & when

This combines two Tree DFS ideas already covered: Same Tree (checking two trees match node by node) and a traversal that visits every node of `root` as a candidate starting point. It belongs in this section because "does this subtree match" is answered with the exact same recursive equality check from Same Tree, just called once per node of `root` instead of once overall.

## 3. Core concept

**Key idea:** walk every node of `root` (pre-order is fine, any order works). At each node, run the Same Tree check between that node's subtree and `subRoot`. If any node passes, the answer is `true`.

**Steps:**
1. Base case: if `root == null`, return `false` (an empty tree has no subtree to match a non-empty `subRoot`; if `subRoot` is also `null` a separate check upfront can return `true`, but LeetCode guarantees `subRoot` is non-empty).
2. Check: if `isSameTree(root, subRoot)` is `true`, return `true` immediately.
3. Recurse: return `isSubtree(root.left, subRoot) || isSubtree(root.right, subRoot)`.
4. `isSameTree` is the identical helper from the Same Tree problem: both `null` -> `true`; one `null` -> `false`; values differ -> `false`; otherwise recurse both children with `&&`.

**Why it is correct:** every node of `root` is tried exactly once as a candidate root for the match, and `isSameTree` correctly confirms an EXACT structural and value match starting from that candidate, so the `||` across all candidates finds a match if and only if one genuinely exists anywhere in `root`.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Trying every node of root as a candidate match for subRoot">
  <g font-family="sans-serif" font-size="12">
    <circle cx="220" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="220" y="34" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="160" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="160" y="84" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="280" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="280" y="84" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="130" cy="130" r="14" fill="#161b22" stroke="#3fb950"/><text x="130" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="190" cy="130" r="14" fill="#161b22" stroke="#3fb950"/><text x="190" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <line x1="211" y1="43" x2="169" y2="68" stroke="#8b949e"/>
    <line x1="229" y1="43" x2="271" y2="68" stroke="#8b949e"/>
    <line x1="150" y1="93" x2="136" y2="118" stroke="#8b949e"/>
    <line x1="170" y1="93" x2="184" y2="118" stroke="#8b949e"/>
    <text x="10" y="15" fill="#8b949e">Tree root</text>
    <circle cx="380" cy="55" r="14" fill="#161b22" stroke="#3fb950"/><text x="380" y="59" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="350" cy="105" r="13" fill="#161b22" stroke="#3fb950"/><text x="350" y="109" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <circle cx="410" cy="105" r="13" fill="#161b22" stroke="#3fb950"/><text x="410" y="109" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <line x1="373" y1="67" x2="357" y2="93" stroke="#8b949e"/>
    <line x1="387" y1="67" x2="403" y2="93" stroke="#8b949e"/>
    <text x="340" y="30" fill="#8b949e">subRoot</text>
    <text x="10" y="180" fill="#e6edf3">isSameTree(node 3, subRoot) fails; isSameTree(node 4, subRoot) matches -&gt; true</text>
  </g>
</svg>

The candidate rooted at `4` (green) matches `subRoot` exactly, so the search stops and returns `true`.

## 5. Runnable example

```java
// SubtreeOfAnotherTree.java
public class SubtreeOfAnotherTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: serialize both root and subRoot to strings
    // (with null markers), then check if subRoot's string is a substring
    // of root's string. O(n * m) worst case for the substring search
    // (or O(n+m) with a linear-time algorithm), plus O(n+m) for building
    // the strings -- more machinery than a direct recursive check needs.
    static boolean bruteForce(TreeNode root, TreeNode subRoot) {
        StringBuilder rootStr = new StringBuilder();
        StringBuilder subStr = new StringBuilder();
        serialize(root, rootStr);
        serialize(subRoot, subStr);
        return rootStr.toString().contains(subStr.toString());
    }

    static void serialize(TreeNode node, StringBuilder sb) {
        if (node == null) { sb.append(",#"); return; }
        sb.append(",").append(node.val);
        serialize(node.left, sb);
        serialize(node.right, sb);
    }

    // KEY INSIGHT: reuse the exact Same Tree check as a sub-routine,
    // called once per node of root -- no string building needed, just
    // the equality recursion you already know.

    // Level 2 -- Optimal: try isSameTree at every node of root.
    // O(n * m) worst case (n = size of root, m = size of subRoot),
    // O(h) space (recursion stack).
    public static boolean isSubtree(TreeNode root, TreeNode subRoot) {
        if (root == null) return false;
        if (isSameTree(root, subRoot)) return true;
        return isSubtree(root.left, subRoot) || isSubtree(root.right, subRoot);
    }

    static boolean isSameTree(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        if (a.val != b.val) return false;
        return isSameTree(a.left, b.left) && isSameTree(a.right, b.right);
    }

    // Level 3 -- Hardened: subRoot equal to the whole root tree must
    // return true (matched at the very first candidate), and subRoot
    // not appearing anywhere must return false after trying every node.
    static boolean hardened(TreeNode root, TreeNode subRoot) {
        return isSubtree(root, subRoot);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3,
            new TreeNode(4, new TreeNode(1), new TreeNode(2)),
            new TreeNode(5));
        TreeNode subRoot = new TreeNode(4, new TreeNode(1), new TreeNode(2));

        System.out.println(bruteForce(root, subRoot));
        System.out.println(isSubtree(root, subRoot));
        System.out.println(hardened(root, root));
    }
}
```

How to run: save as `SubtreeOfAnotherTree.java`, then run `java SubtreeOfAnotherTree.java`.

## 6. Walkthrough

Dry run of `isSubtree(root, subRoot)` where `root = [3,4,5,1,2]` and `subRoot = [4,1,2]`:

| call | isSameTree check | result |
|---|---|---|
| isSubtree(3, subRoot) | isSameTree(3, 4) fails at root value | false, recurse into children |
| isSubtree(4, subRoot) | isSameTree(4, 4): values match, recurse (1,1) and (2,2), both match | true |

Since `isSubtree(4, subRoot)` returns `true`, the `||` short-circuits and the overall call returns `true` without ever visiting node `5`. Time complexity: O(n * m) worst case, where `n` is the size of `root` and `m` is the size of `subRoot` (each candidate match attempt can cost up to O(m)). Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: two different nodes holding the same value, where one has extra descendants the other lacks, are NOT the same subtree — always run the full `isSameTree` check (which also compares structure via the `null` checks), never just compare the single root value at the candidate node.

- Reusing a previously solved sub-problem (Same Tree) as a helper, instead of reinventing equality logic, is the fastest way to build this solution correctly.
- Related problems: Same Tree (the exact helper this problem calls at every candidate node), Binary Tree Level Order Traversal (a different way to visit every node, useful if you needed the candidates in level order instead of pre-order).
