---
card: data-structures
gi: 106
slug: lowest-common-ancestor-lca
title: Lowest common ancestor (LCA)
---

## 1. What it is

The **lowest common ancestor (LCA)** of two nodes `p` and `q` in a tree is the deepest node that has both `p` and `q` as descendants (a node is considered a descendant of itself for this definition). It is the point where the paths from the root to `p` and from the root to `q` most recently diverge.

## 2. Why & when

LCA shows up whenever you need to find the "closest shared point" between two nodes: file-system path resolution (the shared parent directory of two files), version-control history (the common ancestor commit of two branches), or organizational hierarchy queries ("who is the lowest manager both employees report to"). It also has a genuinely different, simpler algorithm on a BST versus a plain binary tree, making it a good test of whether you actually understand the BST invariant.

## 3. Core concept

**BST case — use the ordering invariant directly.** Starting at the root, compare both `p.value` and `q.value` against the current node's value. If both are smaller, the LCA must be in the left subtree (recurse left). If both are larger, recurse right. The moment they are *not* both on the same side (one is smaller or equal, one is larger or equal), the current node is the LCA — this is exactly the point where the paths to `p` and `q` diverge.

**Why the BST approach works.** Because of the ordering invariant, if both `p` and `q` are smaller than the current node, both must live entirely within the left subtree, so the LCA — being an ancestor of both — must also be in the left subtree. The same logic applies symmetrically for "both larger." The first node where this stops being true is, by definition, the lowest node that still has both as descendants.

**Plain binary tree case — no ordering to exploit, use post-order recursion.** Recurse into both children. If a node's left and right subtrees *each* report finding one of `p`/`q` (i.e., one was found on each side), the current node is the LCA. If only one side reports a find, propagate that find upward — the LCA must be further up, or possibly *is* that found node itself, if it turns out to be an ancestor of the other target.

**Why the plain-tree approach works.** Without an ordering invariant, there is no way to know which subtree to search without actually searching both. The post-order structure (process children before combining results at the parent) is exactly what lets a node "learn" whether each of its subtrees contains one of the targets, before deciding whether it itself is the LCA.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A BST where searching for the LCA of 2 and 8 starts at root 6, and since 2 is smaller and 8 is larger than 6, the search stops immediately at 6 as the LCA">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">6</text>
    <text x="360" y="20" fill="#f0883e" font-size="9">LCA of 2 and 8</text>
    <circle cx="220" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <circle cx="380" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <line x1="288" y1="42" x2="232" y2="78" stroke="#8b949e"/>
    <line x1="312" y1="42" x2="368" y2="78" stroke="#8b949e"/>
    <text x="300" y="140" fill="#79c0ff" text-anchor="middle" font-size="9">2 &lt; 6 (go left path); 8 &gt; 6 (go right path) -- diverge HERE -&gt; 6 is the LCA</text>
  </g>
</svg>

`2` is smaller than `6`, `8` is larger — the search paths to each diverge at the very first comparison, so `6` itself is the LCA.

## 5. Runnable example

```java
// LowestCommonAncestor.java
public class LowestCommonAncestor {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    static TreeNode insert(TreeNode node, int value) {
        if (node == null) return new TreeNode(value);
        if (value < node.value) node.left = insert(node.left, value);
        else if (value > node.value) node.right = insert(node.right, value);
        return node;
    }

    // Basic: LCA in a BST -- uses the ordering invariant to decide direction in O(h) without exploring both subtrees.
    static TreeNode lcaInBst(TreeNode node, int p, int q) {
        if (node == null) return null;
        if (p < node.value && q < node.value) return lcaInBst(node.left, p, q);   // both smaller -> LCA is in the left subtree
        if (p > node.value && q > node.value) return lcaInBst(node.right, p, q); // both larger -> LCA is in the right subtree
        return node; // paths diverge here (or one equals node.value) -- this IS the LCA
    }

    static void basicLevel() {
        TreeNode root = null;
        for (int v : new int[]{6, 2, 8, 0, 4, 7, 9}) root = insert(root, v);

        System.out.println("basic: LCA(2, 8) -> " + lcaInBst(root, 2, 8).value);
        System.out.println("basic: LCA(0, 4) -> " + lcaInBst(root, 0, 4).value);
    }

    static void intermediateLevel() {
        TreeNode root = null;
        for (int v : new int[]{6, 2, 8, 0, 4, 7, 9}) root = insert(root, v);

        System.out.println("intermediate: LCA(0, 2) (one is an ancestor of the other) -> " + lcaInBst(root, 0, 2).value);
        System.out.println("intermediate: LCA(7, 9) -> " + lcaInBst(root, 7, 9).value);
    }

    // Advanced: LCA in a PLAIN binary tree -- no ordering to exploit, must search both subtrees via post-order recursion.
    static TreeNode lcaInPlainTree(TreeNode node, TreeNode p, TreeNode q) {
        if (node == null || node == p || node == q) return node; // found one of the targets (or ran out of tree)

        TreeNode left = lcaInPlainTree(node.left, p, q);
        TreeNode right = lcaInPlainTree(node.right, p, q);

        if (left != null && right != null) return node; // found one target on EACH side -- this node is the LCA
        return left != null ? left : right;              // propagate whichever side found something (or null, if neither did)
    }

    static void advancedLevel() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3));
        TreeNode node4 = root.left.left;
        TreeNode node5 = root.left.right;

        TreeNode lca = lcaInPlainTree(root, node4, node5);
        System.out.println("advanced: LCA of nodes 4 and 5 in a plain tree -> " + lca.value);

        TreeNode node3 = root.right;
        TreeNode lca2 = lcaInPlainTree(root, node4, node3);
        System.out.println("advanced: LCA of nodes 4 and 3 in a plain tree -> " + lca2.value);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LowestCommonAncestor.java`, then run `java LowestCommonAncestor.java`.

## 6. Walkthrough

Trace `lcaInBst` for `LCA(0, 4)` on the tree `6(left: 2(left: 0, right: 4), right: 8(left: 7, right: 9))`:

| Call | node.value | 0 vs node | 4 vs node | action |
|---|---|---|---|---|
| `lcaInBst(6, 0, 4)` | 6 | 0 < 6 | 4 < 6 | both smaller -> recurse left |
| `lcaInBst(2, 0, 4)` | 2 | 0 < 2 | 4 > 2 | not both same side -> **this is the LCA** |

Result: `2`. Compare to `lcaInBst(root, 0, 2)`: at node `2`, `0 < 2` but `2` is not `< 2` (it *is* `2`) — the "both smaller" condition fails, so the function falls through to `return node`, correctly identifying `2` itself as its own ancestor's LCA with `0`.

For the plain-tree case (`advancedLevel`), `lcaInPlainTree` on nodes `4` and `5`: recursing into node `2`, the left call finds `4` directly, the right call finds `5` directly — both sides return non-null, so node `2` is identified as the LCA. For nodes `4` and `3`: recursing from the root, the left subtree (rooted at `2`) eventually finds `4` and returns it; the right subtree is just node `3`, which matches directly and returns itself — both sides of the *root* report non-null, so the root (`1`) is the LCA.

## 7. Gotchas & takeaways

> Gotcha: the plain-tree algorithm assumes both `p` and `q` actually exist somewhere in the tree — if one is missing, the function still returns *some* node without any error, silently giving a wrong answer. If that possibility exists, verify both nodes are present first (a simple search) before trusting the LCA result.

- On a BST, use the ordering invariant directly: both smaller means go left, both larger means go right, otherwise the current node is the LCA — O(h) time, no need to search both subtrees.
- On a plain binary tree, there is no ordering to exploit — recurse into both subtrees and combine results post-order: both sides finding a target means the current node is the LCA.
- A node counts as its own ancestor, so `LCA(p, ancestor-of-p)` correctly returns the ancestor.
- Related concepts: [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md), [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md).
