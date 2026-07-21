---
card: leetcode-patterns
gi: 129
slug: same-tree
title: Same Tree
---

## 1. What it is

Given the roots of two binary trees, `p` and `q`, return `true` if they are structurally identical and every corresponding node holds the same value. Example: `p = [1,2,3]`, `q = [1,2,3]` → `true`; `p = [1,2]`, `q = [1,null,2]` → `false` (the `2` hangs on different sides).

## 2. Why & when

This is Tree DFS over two trees at once: at every pair of corresponding nodes, you must confirm they match, then confirm both left subtrees match, and both right subtrees match. It belongs in this section because it needs the recursion to finish checking an entire pair of subtrees before the parent's "are these equal" answer can be trusted.

## 3. Core concept

**Key idea:** two trees are the same if their roots match (both `null`, or both non-null with equal values) AND their left subtrees are the same AND their right subtrees are the same.

**Steps:**
1. Base case: if both `p` and `q` are `null`, return `true` (two empty trees are equal).
2. Base case: if exactly one of `p`, `q` is `null` (not both), return `false` (different shapes).
3. Base case: if `p.val != q.val`, return `false` (same shape, different value).
4. Recurse: return `isSameTree(p.left, q.left) && isSameTree(p.right, q.right)`.

**Why it is correct:** the three base cases cover every way two single nodes can disagree (different null-ness, different value); once those are ruled out, the trees can only be equal if BOTH subtree pairs are also equal, which the recursive `&&` enforces.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing two trees node by node in lockstep">
  <g font-family="sans-serif" font-size="12">
    <circle cx="120" cy="35" r="16" fill="#161b22" stroke="#3fb950"/><text x="120" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="80" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="80" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="160" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="160" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="112" y1="49" x2="88" y2="77" stroke="#3fb950"/>
    <line x1="128" y1="49" x2="152" y2="77" stroke="#3fb950"/>
    <text x="60" y="15" fill="#8b949e">Tree p</text>
    <circle cx="340" cy="35" r="16" fill="#161b22" stroke="#f85149"/><text x="340" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="380" cy="90" r="16" fill="#161b22" stroke="#f85149"/><text x="380" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="348" y1="49" x2="372" y2="77" stroke="#f85149"/>
    <text x="300" y="15" fill="#8b949e">Tree q</text>
    <text x="10" y="170" fill="#e6edf3">p.right=3 exists, q.right=null -&gt; mismatch at that pair -&gt; false</text>
  </g>
</svg>

The mismatch is detected at the first pair of nodes where one side is `null` and the other is not.

## 5. Runnable example

```java
// SameTree.java
public class SameTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: serialize both trees to strings (including
    // markers for null children) and compare the strings. O(n) time and
    // space for the two serialized strings, more memory than needed for
    // a direct structural comparison.
    static boolean bruteForce(TreeNode p, TreeNode q) {
        StringBuilder sp = new StringBuilder();
        StringBuilder sq = new StringBuilder();
        serialize(p, sp);
        serialize(q, sq);
        return sp.toString().equals(sq.toString());
    }

    static void serialize(TreeNode node, StringBuilder sb) {
        if (node == null) { sb.append("#,"); return; }
        sb.append(node.val).append(",");
        serialize(node.left, sb);
        serialize(node.right, sb);
    }

    // KEY INSIGHT: comparing both trees pair by pair, node by node, in
    // the same recursive call needs no intermediate string -- the
    // recursion itself IS the comparison.

    // Level 2 -- Optimal: paired DFS, comparing node-by-node.
    // O(n) time, O(h) space (recursion stack).
    public static boolean isSameTree(TreeNode p, TreeNode q) {
        if (p == null && q == null) return true;
        if (p == null || q == null) return false;
        if (p.val != q.val) return false;
        return isSameTree(p.left, q.left) && isSameTree(p.right, q.right);
    }

    // Level 3 -- Hardened: two single-node trees with equal values must
    // return true; two trees where only ONE side has a null child (not
    // both) must return false, never throw a NullPointerException.
    static boolean hardened(TreeNode p, TreeNode q) {
        return isSameTree(p, q);
    }

    public static void main(String[] args) {
        TreeNode p = new TreeNode(1, new TreeNode(2), new TreeNode(3));
        TreeNode q = new TreeNode(1, new TreeNode(2), new TreeNode(3));
        TreeNode r = new TreeNode(1, new TreeNode(2), null);

        System.out.println(bruteForce(p, q));
        System.out.println(isSameTree(p, q));
        System.out.println(hardened(p, r));
    }
}
```

How to run: save as `SameTree.java`, then run `java SameTree.java`.

## 6. Walkthrough

Dry run of `isSameTree(p, q)` where `p = [1,2,3]` and `q = [1,2,3]`:

| call | p node | q node | check | result |
|---|---|---|---|---|
| isSameTree(p, q) | 1 | 1 | values equal, recurse both sides | pending |
| isSameTree(p.left, q.left) | 2 | 2 | values equal, both children null | true |
| isSameTree(p.right, q.right) | 3 | 3 | values equal, both children null | true |
| combine | - | - | true && true | true |

Final result: `true`. Time complexity: O(n), where `n` is the smaller of the two trees' node counts (recursion stops early on the first mismatch). Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: checking `p.val != q.val` before checking for `null` throws a `NullPointerException` the moment one of `p` or `q` is `null` — the null checks must come first, in the order shown (both null, then either null, then value).

- The three base cases are not interchangeable in order: checking "both null" before "either null" is what correctly lets two empty trees be equal while still catching a shape mismatch.
- Related problems: Symmetric Tree (compares a tree against its own mirror instead of a second tree), Subtree of Another Tree (reuses this exact function to check if any subtree matches, not just the whole tree).
