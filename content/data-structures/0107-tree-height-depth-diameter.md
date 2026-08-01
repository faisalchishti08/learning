---
card: data-structures
gi: 107
slug: tree-height-depth-diameter
title: 'Tree height, depth & diameter'
---

## 1. What it is

Height and depth were introduced as terminology in [Tree terminology (root, height, depth, leaf)](0097-tree-terminology-root-height-depth-leaf.md). The **diameter** of a tree is a related but distinct measurement: the length (in edges) of the longest path between *any* two nodes in the tree — that path does not have to pass through the root, and does not have to end at a leaf.

## 2. Why & when

Computing height is the building block for balance checks (an AVL tree's rebalancing decision, or [Complete / full / perfect / balanced trees](0099-complete-full-perfect-balanced-trees.md)'s `isBalanced`). Diameter is a distinct, commonly asked problem in its own right, because the naive approach recomputes height repeatedly, an easy-to-miss inefficiency worth recognizing and fixing.

## 3. Core concept

**Height, recap.** `height(node) = 1 + max(height(left), height(right))`, with an empty subtree conventionally having height `-1`. This is a straightforward bottom-up recursion.

**Diameter — the key realization.** The longest path between any two nodes either passes through a specific node as its "peak" (going down into the left subtree, then down into the right subtree), or it lies entirely within one subtree, not touching the current node at all. The diameter of the whole tree is the maximum, over every node, of `height(left) + height(right) + 2` (the path down-left, through the node, down-right — counted in edges) — but you must check this at *every* node, not just the root, since the longest path might be entirely contained within some subtree.

**Level 1 — naive: recompute height at every node.** For each node, compute `height(left) + height(right) + 2` and recurse into both children to check their sub-diameters too — but each height computation itself walks its entire subtree, so this recomputes the same heights over and over, giving O(n²) in the worst case (a skewed tree).

**KEY INSIGHT.** Height and diameter can be computed in the *same single pass*: a recursive function can return a node's height while *also* updating a running "best diameter seen so far" as a side effect, computed once at each node using values it already had to compute for the height calculation anyway.

**Level 2 — optimal: one post-order pass.** A helper function computes height as usual, but at each node also checks whether `leftHeight + rightHeight + 2` beats the best diameter found so far (tracked in a shared variable, or returned alongside the height). Since each node's height is computed exactly once, this runs in O(n) total.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree where the longest path runs entirely through the left subtree, not through the root, illustrating why diameter must be checked at every node, not just the root">
  <g font-family="sans-serif" font-size="11">
    <circle cx="380" cy="30" r="16" fill="#161b22" stroke="#8b949e"/><text x="380" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="260" cy="80" r="16" fill="#0d1117" stroke="#f0883e"/><text x="260" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="480" cy="80" r="16" fill="#161b22" stroke="#8b949e"/><text x="480" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="200" cy="130" r="16" fill="#0d1117" stroke="#f0883e"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <circle cx="300" cy="130" r="16" fill="#0d1117" stroke="#f0883e"/><text x="300" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">E</text>
    <circle cx="170" cy="180" r="14" fill="#0d1117" stroke="#f0883e"/><text x="170" y="184" fill="#e6edf3" text-anchor="middle" font-size="8">F</text>
    <circle cx="330" cy="180" r="14" fill="#0d1117" stroke="#f0883e"/><text x="330" y="184" fill="#e6edf3" text-anchor="middle" font-size="8">G</text>
    <line x1="368" y1="42" x2="272" y2="68" stroke="#8b949e"/>
    <line x1="392" y1="42" x2="468" y2="68" stroke="#8b949e"/>
    <line x1="248" y1="92" x2="212" y2="118" stroke="#f0883e"/>
    <line x1="272" y1="92" x2="288" y2="118" stroke="#f0883e"/>
    <line x1="192" y1="142" x2="178" y2="166" stroke="#f0883e"/>
    <line x1="308" y1="142" x2="322" y2="166" stroke="#f0883e"/>
    <text x="250" y="205" fill="#f0883e" text-anchor="middle" font-size="9">longest path F-D-B-E-G (4 edges) stays entirely in B's subtree -- never touches root A</text>
  </g>
</svg>

The diameter (`F -> D -> B -> E -> G`, 4 edges) is entirely contained within `B`'s subtree — checking only the root's two subtree heights would completely miss it.

## 5. Runnable example

```java
// TreeHeightDiameter.java
public class TreeHeightDiameter {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Basic: plain height, bottom-up recursion.
    static int height(TreeNode node) {
        if (node == null) return -1;
        return 1 + Math.max(height(node.left), height(node.right));
    }

    static void basicLevel() {
        TreeNode root = new TreeNode(1, new TreeNode(2, new TreeNode(4), null), new TreeNode(3));
        System.out.println("basic: height of tree -> " + height(root));
    }

    // Level 1: naive diameter -- recomputes height repeatedly, O(n^2) worst case.
    static int diameterNaive(TreeNode node) {
        if (node == null) return 0;
        int throughNode = height(node.left) + height(node.right) + 2; // recomputes height() from scratch here
        int bestInSubtrees = Math.max(diameterNaive(node.left), diameterNaive(node.right));
        return Math.max(throughNode, bestInSubtrees);
    }

    static void intermediateLevelNaive() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4, new TreeNode(6), new TreeNode(7)), new TreeNode(5)),
            new TreeNode(3));
        System.out.println("intermediate: naive diameter -> " + diameterNaive(root) + " (correct, but recomputes height repeatedly)");
    }

    // KEY INSIGHT: height and diameter can be computed in ONE pass -- height() already visits every node needed.

    // Level 2: optimal -- single post-order pass, tracking the best diameter as a side effect.
    static int bestDiameter; // shared across the recursive calls for this one computation

    static int heightAndTrackDiameter(TreeNode node) {
        if (node == null) return -1;
        int leftHeight = heightAndTrackDiameter(node.left);
        int rightHeight = heightAndTrackDiameter(node.right);
        bestDiameter = Math.max(bestDiameter, leftHeight + rightHeight + 2); // check at EVERY node, using values already computed
        return 1 + Math.max(leftHeight, rightHeight);
    }

    static int diameterOptimal(TreeNode root) {
        bestDiameter = 0;
        heightAndTrackDiameter(root);
        return bestDiameter;
    }

    static void advancedLevel() {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4, new TreeNode(6), new TreeNode(7)), new TreeNode(5)),
            new TreeNode(3));
        System.out.println("advanced: optimal diameter -> " + diameterOptimal(root) + " (single pass, O(n))");
        System.out.println("advanced: matches naive result -> " + (diameterOptimal(root) == diameterNaive(root)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevelNaive();
        advancedLevel();
    }
}
```

**How to run:** save as `TreeHeightDiameter.java`, then run `java TreeHeightDiameter.java`.

## 6. Walkthrough

Trace `diameterOptimal` on `1(left: 2(left: 4(left: 6, right: 7), right: 5), right: 3)`:

1. Recursion reaches `6` and `7` (leaves): each returns height `0`, and at each, `bestDiameter` checks `-1 + -1 + 2 = 0` (no children on either side).
2. At node `4`: `leftHeight = 0` (from `6`), `rightHeight = 0` (from `7`), so `bestDiameter` updates to `max(0, 0 + 0 + 2) = 2` — the path `6 -> 4 -> 7`.
3. At node `5` (a leaf): height `0`, no update to `bestDiameter` beyond what a leaf contributes (`-1 + -1 + 2 = 0`, already smaller than the current best).
4. At node `2`: `leftHeight = 1` (from `4`'s subtree, height `1 + max(0,0) = 1`), `rightHeight = 0` (from `5`). `bestDiameter` updates to `max(2, 1 + 0 + 2) = 3` — the path `6 -> 4 -> 2 -> 5` (or `7 -> 4 -> 2 -> 5`).
5. At node `1` (root): `leftHeight = 2` (from `2`'s subtree), `rightHeight = 0` (from `3`, a leaf). Check `max(3, 2 + 0 + 2) = 4` — the path `6 -> 4 -> 2 -> 1 -> 3` (or `7 -> ...`), which is longer still.

Final diameter: `4` edges — and this longest path *does* pass through the root here, but the algorithm checked every node along the way (not just the root), which is exactly what makes it correct even for trees like the diagram's example, where the longest path stays entirely within a non-root subtree.

## 7. Gotchas & takeaways

> Gotcha: diameter is measured in *edges*, not *nodes* — a path through `k` nodes has `k - 1` edges; a common off-by-one mistake is to report the node count instead, which is one too many.

- Diameter is the longest path between any two nodes, which may or may not pass through the root.
- The naive approach recomputes height repeatedly at every node, giving O(n²) worst case; the optimal approach computes height and tracks the best diameter in the same single post-order pass, giving O(n).
- Diameter must be checked at every node, not just the root, since the longest path can be entirely contained within one subtree.
- Related concepts: [Tree terminology (root, height, depth, leaf)](0097-tree-terminology-root-height-depth-leaf.md), [Complete / full / perfect / balanced trees](0099-complete-full-perfect-balanced-trees.md).
