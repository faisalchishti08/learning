---
card: leetcode-patterns
gi: 139
slug: lowest-common-ancestor-of-a-binary-tree
title: Lowest Common Ancestor of a Binary Tree
---

## 1. What it is

Given the `root` of a binary tree and two nodes `p` and `q` that both exist in the tree, return their lowest common ancestor (LCA): the deepest node that has both `p` and `q` as descendants (a node can be a descendant of itself). Example: `root = [3,5,1,6,2,0,8,null,null,7,4]`, `p = 5`, `q = 1` → `3`.

## 2. Why & when

This is a post-order Tree DFS: a node can only know whether `p` and/or `q` were found in its left and right subtrees after both recursive calls return. It belongs in this section because the LCA is identified exactly at the node where the search results from the two children "meet" — one side reports finding `p`, the other reports finding `q` (or the current node itself is one of them).

## 3. Core concept

**Key idea:** search both subtrees for `p` and `q`. A node is the LCA if `p` and `q` are found in different subtrees (one on the left, one on the right), OR if the node itself is `p` or `q` and the other target is found in either subtree.

**Steps:**
1. Base case: if `node == null`, or `node == p`, or `node == q`, return `node` (propagate the found target, or `null`, upward).
2. Recurse: `leftResult = lca(node.left, p, q)`, `rightResult = lca(node.right, p, q)`.
3. Combine: if both `leftResult` and `rightResult` are non-null, `node` is the LCA — return `node`.
4. Otherwise, return whichever of `leftResult`, `rightResult` is non-null (or `null` if neither found anything).

**Why it is correct:** if `p` and `q` are found in different subtrees of `node`, then `node` is the deepest point where their paths from the root diverge, making it exactly their lowest common ancestor; if only one side finds something, that result (which might already be the LCA found deeper, or just `p`/`q` itself still bubbling up) is passed upward unchanged.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The LCA is where results from two different subtrees converge">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="221" y1="44" x2="169" y2="72" stroke="#3fb950" stroke-width="2"/>
    <line x1="239" y1="44" x2="291" y2="72" stroke="#3fb950" stroke-width="2"/>
    <text x="60" y="115" fill="#79c0ff" font-size="11">left subtree returns p=5</text>
    <text x="280" y="115" fill="#79c0ff" font-size="11">right subtree returns q=1</text>
    <text x="10" y="175" fill="#e6edf3">Both children return non-null (5 and 1) -&gt; node 3 is the LCA</text>
  </g>
</svg>

Node `3` receives a non-null result from both its left call (found `5`) and its right call (found `1`), so it is identified as the LCA.

## 5. Runnable example

```java
// LowestCommonAncestor.java
public class LowestCommonAncestor {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: find the root-to-node path for p and for
    // q separately (two DFS calls), then walk both paths together and
    // return the last node where they still match. O(n) time but two
    // full traversals plus O(h) extra space for two stored paths,
    // instead of one combined traversal.
    static TreeNode bruteForce(TreeNode root, TreeNode p, TreeNode q) {
        java.util.List<TreeNode> pathToP = new java.util.ArrayList<>();
        java.util.List<TreeNode> pathToQ = new java.util.ArrayList<>();
        findPath(root, p, pathToP);
        findPath(root, q, pathToQ);
        TreeNode lca = root;
        for (int i = 0; i < pathToP.size() && i < pathToQ.size(); i++) {
            if (pathToP.get(i) != pathToQ.get(i)) break;
            lca = pathToP.get(i);
        }
        return lca;
    }

    static boolean findPath(TreeNode node, TreeNode target, java.util.List<TreeNode> path) {
        if (node == null) return false;
        path.add(node);
        if (node == target) return true;
        if (findPath(node.left, target, path) || findPath(node.right, target, path)) return true;
        path.remove(path.size() - 1);
        return false;
    }

    // KEY INSIGHT: instead of building and comparing two full paths, a
    // single post-order pass can find p and q at the same time -- the
    // node where their "found" signals from left and right converge IS
    // the LCA, discovered in one traversal.

    // Level 2 -- Optimal: one post-order DFS, checking convergence.
    // O(n) time, O(h) space (recursion stack).
    public static TreeNode lowestCommonAncestor(TreeNode node, TreeNode p, TreeNode q) {
        if (node == null || node == p || node == q) return node;
        TreeNode leftResult = lowestCommonAncestor(node.left, p, q);
        TreeNode rightResult = lowestCommonAncestor(node.right, p, q);
        if (leftResult != null && rightResult != null) return node;
        return leftResult != null ? leftResult : rightResult;
    }

    // Level 3 -- Hardened: when p is itself an ancestor of q (or vice
    // versa), the LCA must be p (or q) itself, not some node further up.
    static TreeNode hardened(TreeNode root, TreeNode p, TreeNode q) {
        return lowestCommonAncestor(root, p, q);
    }

    public static void main(String[] args) {
        TreeNode five = new TreeNode(5);
        TreeNode one = new TreeNode(1);
        TreeNode root = new TreeNode(3, five, one);
        five.left = new TreeNode(6);
        five.right = new TreeNode(2);
        one.left = new TreeNode(0);
        one.right = new TreeNode(8);
        TreeNode seven = new TreeNode(7);
        TreeNode four = new TreeNode(4);
        five.right.left = seven;
        five.right.right = four;

        System.out.println(bruteForce(root, five, one).val);
        System.out.println(lowestCommonAncestor(root, five, one).val);
        System.out.println(hardened(root, five, four).val);
    }
}
```

How to run: save as `LowestCommonAncestor.java`, then run `java LowestCommonAncestor.java`.

## 6. Walkthrough

Dry run of `lowestCommonAncestor(root, p=5, q=1)` on the example tree:

| call | leftResult | rightResult | returns |
|---|---|---|---|
| lowestCommonAncestor(5, 5, 1) | - | - | `5` (node == p, base case) |
| lowestCommonAncestor(1, 5, 1) | - | - | `1` (node == q, base case) |
| lowestCommonAncestor(3, 5, 1) | 5 | 1 | both non-null -> `3` |

Final result: `3`. Time complexity: O(n), every node visited at most once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: the base case `node == p || node == q` must return `node` immediately WITHOUT recursing further into that node's own children — even if `q` happens to be a descendant of `p`, the correct LCA is `p` itself, and continuing to search inside `p`'s subtree for `q` would still work here (since the result bubbles up correctly), but treating `p` as a plain internal node without this early return would miss the case where `p` IS the answer.

- This same post-order "does each side report something" convergence check works even when `p` or `q` does not exist in the tree at all (extra validation), though the classic version of this problem guarantees both exist.
- Related problems: All Nodes Distance K in Binary Tree (also reasons about ancestors, but via explicit parent pointers and BFS rather than a converging post-order search), Binary Tree Paths (produces the ancestor chain as an explicit path instead of just the deepest common one).
