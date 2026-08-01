---
card: data-structures
gi: 104
slug: bst-successor-predecessor
title: BST successor & predecessor
---

## 1. What it is

The **in-order successor** of a node is the node that would come immediately after it in an in-order traversal — the next-larger value in the whole tree. The **in-order predecessor** is the node that would come immediately before it — the next-smaller value. Both can be found in O(h) time (`h` = tree height) without ever running a full traversal.

## 2. Why & when

Successor/predecessor is the exact mechanism BST delete relies on for its two-children case (see [BST insert / search / delete](0103-bst-insert-search-delete.md)). It also answers "what is the next/previous value" queries directly — useful for range queries, or iterating a BST in sorted order one step at a time without traversing the whole tree upfront.

## 3. Core concept

**Case A — the node has a right subtree.** The successor is the **leftmost node of the right subtree** — the smallest value that is still greater than the current node. Walk `node.right`, then keep going `.left` until there is no more left child.

**Case B — the node has no right subtree.** The successor must be found by walking *up* from the node, toward the root, until you move up from a left child (i.e., the first ancestor for which the current node is in its left subtree) — that ancestor is the successor, since it is the smallest value greater than everything in the node's own subtree.

**Why this works — the two cases combined.** If a right subtree exists, the immediate "next value" must be its smallest member, since everything in the right subtree is already greater than the node, and the leftmost node of that subtree is the smallest such value. If no right subtree exists, there is nothing greater within the node's own subtree, so the search must go up; the first "turn left" ancestor is the first one where the current node's whole subtree (including the node itself) sat on the *smaller* side, meaning that ancestor is the next value up.

**Predecessor is the exact mirror image.** Case A: if a left subtree exists, the predecessor is its **rightmost** node. Case B: otherwise, walk up until moving up from a *right* child — that ancestor is the predecessor.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Finding the successor of node 5 which has a right subtree, by going right once to 8 then left as far as possible to reach 6, the smallest value in that right subtree">
  <g font-family="sans-serif" font-size="11">
    <circle cx="200" cy="30" r="18" fill="#161b22" stroke="#8b949e"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <circle cx="140" cy="90" r="18" fill="#0d1117" stroke="#f0883e"/><text x="140" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="90" y="80" fill="#f0883e" font-size="9">find successor of 5</text>
    <circle cx="260" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="260" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">15</text>
    <circle cx="180" cy="150" r="18" fill="#161b22" stroke="#79c0ff"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <circle cx="150" cy="190" r="16" fill="#0d1117" stroke="#79c0ff"/><text x="150" y="194" fill="#e6edf3" text-anchor="middle" font-size="9">6</text>
    <text x="150" y="205" fill="#79c0ff" font-size="9" text-anchor="middle">successor</text>
    <line x1="188" y1="42" x2="152" y2="78" stroke="#8b949e"/>
    <line x1="212" y1="42" x2="248" y2="78" stroke="#8b949e"/>
    <line x1="152" y1="102" x2="172" y2="138" stroke="#8b949e"/>
    <line x1="174" y1="160" x2="158" y2="180" stroke="#79c0ff"/>
    <text x="380" y="90" fill="#8b949e" font-size="10">5 has a right subtree (8, with left child 6)</text>
    <text x="380" y="105" fill="#8b949e" font-size="10">go right to 8, then left as far</text>
    <text x="380" y="120" fill="#8b949e" font-size="10">as possible -&gt; land on 6</text>
  </g>
</svg>

`5`'s successor: go right once (to `8`), then left as far as possible (to `6`) — the smallest value in `5`'s right subtree.

## 5. Runnable example

```java
// BstSuccessorPredecessor.java
public class BstSuccessorPredecessor {

    static class TreeNode {
        int value;
        TreeNode left, right, parent; // parent reference needed for the "no right subtree" case

        TreeNode(int value) { this.value = value; }
    }

    static TreeNode insert(TreeNode node, TreeNode parent, int value) {
        if (node == null) {
            TreeNode created = new TreeNode(value);
            created.parent = parent;
            return created;
        }
        if (value < node.value) node.left = insert(node.left, node, value);
        else if (value > node.value) node.right = insert(node.right, node, value);
        return node;
    }

    // Basic: successor, case A -- node HAS a right subtree.
    static TreeNode successor(TreeNode node) {
        if (node.right != null) {
            TreeNode current = node.right;
            while (current.left != null) current = current.left; // leftmost node of the right subtree
            return current;
        }
        // case B: no right subtree -- walk up until moving up from a left child
        TreeNode current = node;
        while (current.parent != null && current.parent.right == current) current = current.parent;
        return current.parent; // may be null, if node holds the maximum value in the whole tree
    }

    static void basicLevel() {
        TreeNode root = null;
        for (int v : new int[]{10, 5, 15, 8, 6}) root = insert(root, null, v);

        TreeNode node5 = find(root, 5);
        System.out.println("basic: successor of 5 (has right subtree) -> " + successor(node5).value);
    }

    static TreeNode find(TreeNode node, int target) {
        if (node == null || node.value == target) return node;
        return target < node.value ? find(node.left, target) : find(node.right, target);
    }

    // Intermediate: successor, case B -- node has NO right subtree, must walk up via parent references.
    static void intermediateLevel() {
        TreeNode root = null;
        for (int v : new int[]{10, 5, 15, 8, 6}) root = insert(root, null, v);

        TreeNode node6 = find(root, 6); // 6 has no children at all
        System.out.println("intermediate: successor of 6 (no right subtree, walk up) -> " + successor(node6).value);

        TreeNode node15 = find(root, 15); // 15 is the maximum value in the whole tree
        TreeNode successorOf15 = successor(node15);
        System.out.println("intermediate: successor of the maximum value (15) -> " + successorOf15); // null: nothing is greater
    }

    // Advanced: predecessor -- the mirror-image algorithm, both cases.
    static TreeNode predecessor(TreeNode node) {
        if (node.left != null) {
            TreeNode current = node.left;
            while (current.right != null) current = current.right; // rightmost node of the left subtree
            return current;
        }
        TreeNode current = node;
        while (current.parent != null && current.parent.left == current) current = current.parent;
        return current.parent;
    }

    static void advancedLevel() {
        TreeNode root = null;
        for (int v : new int[]{10, 5, 15, 8, 6}) root = insert(root, null, v);

        TreeNode node8 = find(root, 8);
        System.out.println("advanced: predecessor of 8 (has left subtree) -> " + predecessor(node8).value);

        TreeNode node10 = find(root, 10);
        System.out.println("advanced: predecessor of 10 (has left subtree, rightmost of it) -> " + predecessor(node10).value);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BstSuccessorPredecessor.java`, then run `java BstSuccessorPredecessor.java`.

## 6. Walkthrough

Tree built from `[10, 5, 15, 8, 6]`: `10(left: 5(right: 8(left: 6)), right: 15)`.

1. `basicLevel()` finds the successor of `5`. Since `5.right` is `8` (not `null`), case A applies: walk `8`, then `8.left` is `6`, then `6.left` is `null` — stop, successor is `6`.
2. `intermediateLevel()` finds the successor of `6`, which has no right subtree — case B applies. Walk up: `6`'s parent is `8`, and `6` is `8`'s *left* child (not right), so the loop condition (`parent.right == current`) is immediately false, and `current.parent` (`8`) is the answer directly. For `15` (the maximum value in the tree), case B walks all the way up without ever finding a "moved up from a left child" turn, so `current.parent` ends up `null` — correctly signaling there is no successor, since `15` is already the largest value present.
3. `advancedLevel()` mirrors the logic for predecessor: `8` has a left subtree (`6`), so its predecessor is the rightmost node there — `6` itself, since `6` has no right child. `10`'s predecessor uses its left subtree (`5`, with `8` and `6` beneath it) — the rightmost node there is `8` (since `8.right` is `null`).

## 7. Gotchas & takeaways

> Gotcha: the "walk up" case (case B) requires each node to store a `parent` reference — a BST without parent pointers cannot efficiently find a successor/predecessor for an arbitrary node without either re-searching from the root or doing a full traversal; this is a specific design decision to make when building a BST that will need this operation.

- Successor: if a right subtree exists, its leftmost node; otherwise, walk up until moving up from a left child.
- Predecessor: if a left subtree exists, its rightmost node; otherwise, walk up until moving up from a right child.
- Both run in O(h) time, where `h` is the tree's height — no full traversal needed.
- The tree's maximum value has no successor; the minimum value has no predecessor — both return `null` correctly under this algorithm.
- Related concepts: [BST insert / search / delete](0103-bst-insert-search-delete.md), [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md).
