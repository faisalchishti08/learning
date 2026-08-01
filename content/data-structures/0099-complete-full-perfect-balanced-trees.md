---
card: data-structures
gi: 99
slug: complete-full-perfect-balanced-trees
title: Complete / full / perfect / balanced trees
---

## 1. What it is

These four terms describe different **shape constraints** a binary tree can satisfy, and they are easy to confuse because they sound similar but mean genuinely different things. **Full**: every node has 0 or 2 children (never exactly 1). **Complete**: every level is fully filled except possibly the last, which fills left to right. **Perfect**: every internal node has exactly 2 children, and every leaf sits at the same depth. **Balanced**: for every node, the heights of its left and right subtrees differ by no more than some small bound (commonly 1).

## 2. Why & when

These shapes matter because they each guarantee different performance properties. A binary heap must be **complete** (it is why heaps are efficiently array-backed). A **balanced** BST (AVL, red-black tree) guarantees O(log n) operations, where an unbalanced BST can degrade to O(n). Recognizing which shape a problem needs — or which shape a given tree already has — is a frequent, quick interview check.

## 3. Core concept

**Full — the "0 or 2" rule.** No node has exactly one child. A node either has zero children (a leaf) or two. This says nothing about depth or level-filling — a full tree can still be very lopsided.

**Complete — filled left to right, level by level.** Every level except possibly the last is completely filled, and the last level's nodes are as far left as possible, with no gaps. This is the exact property a binary heap relies on to be stored efficiently in a flat array (see [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md)) — the array-index parent/child formulas only work correctly because there are no gaps.

**Perfect — the strictest shape.** Every internal node has exactly 2 children, *and* every leaf is at the exact same depth. A perfect tree of height `h` has exactly `2^(h+1) - 1` nodes — every level is completely full, with no exceptions anywhere, not even the last level.

**Balanced — bounded height difference, not a fixed shape.** For every node, `|height(left subtree) - height(right subtree)|` stays within a small bound (AVL trees enforce at most `1`; red-black trees allow more slack but still bound the ratio between the longest and shortest root-to-leaf paths). Balance is what keeps a BST's height at O(log n) instead of degrading toward O(n) for a skewed insertion order.

**How the four relate.** Perfect implies complete, and perfect implies full, and perfect implies balanced — a perfect tree satisfies all four simultaneously. But each property can hold independently of the others: a tree can be full without being complete, complete without being full, or balanced without being either.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four small trees side by side illustrating full but not complete, complete but not full, perfect satisfying all constraints, and balanced but neither full nor complete">
  <g font-family="sans-serif" font-size="10">
    <text x="70" y="16" fill="#79c0ff" text-anchor="middle">FULL (not complete)</text>
    <circle cx="70" cy="35" r="12" fill="#0d1117" stroke="#79c0ff"/>
    <circle cx="40" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="100" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="20" cy="105" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="60" cy="105" r="12" fill="#161b22" stroke="#8b949e"/>
    <line x1="70" y1="45" x2="45" y2="60" stroke="#8b949e"/><line x1="70" y1="45" x2="95" y2="60" stroke="#8b949e"/>
    <line x1="35" y1="80" x2="22" y2="95" stroke="#8b949e"/><line x1="35" y1="80" x2="58" y2="95" stroke="#8b949e"/>

    <text x="240" y="16" fill="#f0883e" text-anchor="middle">COMPLETE (not full)</text>
    <circle cx="240" cy="35" r="12" fill="#0d1117" stroke="#f0883e"/>
    <circle cx="210" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="270" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="195" cy="105" r="12" fill="#161b22" stroke="#8b949e"/>
    <line x1="240" y1="45" x2="215" y2="60" stroke="#8b949e"/><line x1="240" y1="45" x2="265" y2="60" stroke="#8b949e"/>
    <line x1="205" y1="80" x2="197" y2="95" stroke="#8b949e"/>

    <text x="410" y="16" fill="#a5d6ff" text-anchor="middle">PERFECT (all four)</text>
    <circle cx="410" cy="35" r="12" fill="#0d1117" stroke="#a5d6ff"/>
    <circle cx="380" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="440" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <line x1="410" y1="45" x2="385" y2="60" stroke="#8b949e"/><line x1="410" y1="45" x2="435" y2="60" stroke="#8b949e"/>

    <text x="560" y="16" fill="#79c0ff" text-anchor="middle">BALANCED only</text>
    <circle cx="560" cy="35" r="12" fill="#0d1117" stroke="#79c0ff"/>
    <circle cx="530" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="590" cy="70" r="12" fill="#161b22" stroke="#8b949e"/>
    <circle cx="500" cy="105" r="12" fill="#161b22" stroke="#8b949e"/>
    <line x1="560" y1="45" x2="535" y2="60" stroke="#8b949e"/><line x1="560" y1="45" x2="585" y2="60" stroke="#8b949e"/>
    <line x1="525" y1="80" x2="502" y2="95" stroke="#8b949e"/>
  </g>
</svg>

Full only constrains "0 or 2 children per node." Complete constrains level-filling, left to right. Perfect requires both, at every level, with no exceptions. Balanced only bounds height difference, independent of node-count shape.

## 5. Runnable example

```java
// TreeShapeChecks.java
public class TreeShapeChecks {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Basic: isFull -- every node has 0 or 2 children, never exactly 1.
    static boolean isFull(TreeNode node) {
        if (node == null) return true;
        if ((node.left == null) != (node.right == null)) return false; // exactly one child present: violates "full"
        return isFull(node.left) && isFull(node.right);
    }

    static void basicLevel() {
        TreeNode full = new TreeNode(1, new TreeNode(2), new TreeNode(3));
        TreeNode notFull = new TreeNode(1, new TreeNode(2), null); // one child missing

        System.out.println("basic: isFull(balanced pair) -> " + isFull(full));
        System.out.println("basic: isFull(one child missing) -> " + isFull(notFull));
    }

    // Intermediate: isPerfect -- combine "full" with "every leaf at the same depth", via a height check.
    static int height(TreeNode node) {
        if (node == null) return -1;
        return 1 + Math.max(height(node.left), height(node.right));
    }

    static boolean isPerfect(TreeNode node) {
        return isPerfect(node, height(node), 0);
    }

    static boolean isPerfect(TreeNode node, int expectedHeight, int currentDepth) {
        if (node == null) return true;
        if (node.left == null && node.right == null) return currentDepth == expectedHeight; // leaf must be at the exact expected depth
        if (node.left == null || node.right == null) return false; // must be full too
        return isPerfect(node.left, expectedHeight, currentDepth + 1) && isPerfect(node.right, expectedHeight, currentDepth + 1);
    }

    static void intermediateLevel() {
        TreeNode perfect = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3, new TreeNode(6), new TreeNode(7)));
        TreeNode notPerfect = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), null), // leaf 4 is deeper than a hypothetical sibling of 2 at the same level
            new TreeNode(3));

        System.out.println("intermediate: isPerfect(fully filled 3-level tree) -> " + isPerfect(perfect));
        System.out.println("intermediate: isPerfect(uneven leaves) -> " + isPerfect(notPerfect));
    }

    // Advanced: isBalanced -- for every node, left/right subtree heights differ by at most 1.
    static boolean isBalanced(TreeNode node) {
        return checkBalanced(node) != Integer.MIN_VALUE;
    }

    static int checkBalanced(TreeNode node) { // returns height if balanced, or a sentinel if NOT balanced anywhere below
        if (node == null) return -1;
        int leftHeight = checkBalanced(node.left);
        if (leftHeight == Integer.MIN_VALUE) return Integer.MIN_VALUE; // already found an imbalance deeper down
        int rightHeight = checkBalanced(node.right);
        if (rightHeight == Integer.MIN_VALUE) return Integer.MIN_VALUE;
        if (Math.abs(leftHeight - rightHeight) > 1) return Integer.MIN_VALUE; // imbalance found HERE
        return 1 + Math.max(leftHeight, rightHeight);
    }

    static void advancedLevel() {
        TreeNode balanced = new TreeNode(1, new TreeNode(2), new TreeNode(3, new TreeNode(4), null));
        TreeNode skewed = new TreeNode(1, new TreeNode(2, new TreeNode(3, new TreeNode(4), null), null), null); // a chain

        System.out.println("advanced: isBalanced(mildly uneven tree) -> " + isBalanced(balanced));
        System.out.println("advanced: isBalanced(chain of 4 nodes) -> " + isBalanced(skewed));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TreeShapeChecks.java`, then run `java TreeShapeChecks.java`.

## 6. Walkthrough

1. `basicLevel()`'s `isFull` recursively checks that no node has exactly one child. The two-leaf tree passes; the tree with one missing child fails immediately at that node, since `(left == null) != (right == null)` is `true` there.
2. `intermediateLevel()`'s `isPerfect` first computes the tree's overall height, then walks down checking every leaf lands at exactly that depth, and every internal node has exactly two children. The fully filled 3-level tree passes; the uneven tree fails, since one leaf (`4`) sits deeper than a leaf on the other branch (`3`, which is itself a leaf one level shallower).
3. `advancedLevel()`'s `isBalanced` computes height and checks the balance condition in the *same* recursive pass, using `Integer.MIN_VALUE` as a sentinel meaning "already found an imbalance somewhere below — stop checking further." A 4-node straight-line chain fails balance (a subtree of height `2` next to an empty subtree of height `-1` differs by `3`), while a tree with only a small height difference at each node passes.

## 7. Gotchas & takeaways

> Gotcha: "balanced" does not mean "perfect," and does not even mean "complete" — a balanced tree can still look visually lopsided, as long as no single node's two subtrees differ in height by more than the allowed bound. Do not assume a balanced tree has any particular node count or level-filling pattern.

- Full: every node has 0 or 2 children. Complete: filled left to right, level by level, with only the last level allowed gaps (on the right). Perfect: full and complete and every leaf at the same depth. Balanced: bounded height difference at every node, independent of the other three.
- Perfect implies all the others; the others do not imply each other.
- Complete shape is what lets a binary heap live efficiently in a flat array.
- Balance is what keeps BST operations at O(log n) instead of degrading toward O(n).
- Related concepts: [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md), [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md).
