---
card: data-structures
gi: 110
slug: avl-trees-rotations
title: AVL trees & rotations
---

## 1. What it is

An **AVL tree** is a binary search tree (BST) that adds one extra invariant: for every node, the heights of its left and right subtrees differ by at most 1. This **balance factor** rule is checked and restored after every insert and delete, using a local restructuring move called a **rotation**.

## 2. Why & when

A plain BST degrades to a linked list, with O(n) search, if you insert already-sorted data. An AVL tree prevents that by rebalancing itself immediately after any change, guaranteeing O(log n) height at all times. Choose an AVL tree over a plain BST whenever lookups must stay fast regardless of insertion order — for example, in a database index or a language runtime's ordered map.

## 3. Core concept

**The structure's shape.** An AVL tree is a BST plus a stored **height** (or balance factor) at every node. The balance factor of a node is `height(left subtree) - height(right subtree)`; a valid AVL tree keeps this value in `{-1, 0, 1}` at every node.

**How the invariant makes operations fast.** Because the balance factor never exceeds 1, the tree's height stays `O(log n)` even in the worst case — unlike a plain BST, which can degrade to `O(n)` height. Since search, insert, and delete all cost `O(height)`, bounding the height directly bounds every operation.

**Rotations restore the invariant.** After an insert or delete, walk back up from the changed node to the root, updating heights. If a node's balance factor becomes `+2` or `-2`, it is unbalanced, and a rotation fixes it locally:

- **Left rotation:** used when a node is right-heavy. The right child becomes the new subtree root; the old root becomes that child's left child.
- **Right rotation:** the mirror image, used when a node is left-heavy.
- **Left-right / right-left rotations:** two rotations in sequence, needed when the heavy subtree itself leans the opposite way (e.g. a right-heavy node whose right child is left-heavy).

Each rotation is a constant-time pointer rewiring — it does not touch the rest of the tree, so restoring balance after one insert costs `O(log n)` total (the walk up, plus at most one double rotation).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A left-heavy unbalanced tree rooted at 30 being fixed by a right rotation, promoting 20 to the new root">
  <g font-family="sans-serif" font-size="11">
    <text x="130" y="16" fill="#8b949e" text-anchor="middle">before: unbalanced (left-heavy)</text>
    <circle cx="130" cy="40" r="18" fill="#0d1117" stroke="#f0883e"/><text x="130" y="44" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <circle cx="90" cy="100" r="18" fill="#161b22" stroke="#79c0ff"/><text x="90" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <circle cx="60" cy="160" r="18" fill="#161b22" stroke="#79c0ff"/><text x="60" y="164" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <line x1="118" y1="52" x2="102" y2="88" stroke="#8b949e"/>
    <line x1="80" y1="112" x2="68" y2="148" stroke="#8b949e"/>
    <text x="130" y="200" fill="#f0883e" text-anchor="middle" font-size="9">balance(30) = 2 -&gt; unbalanced</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">after: right rotation on 30</text>
    <circle cx="480" cy="60" r="18" fill="#0d1117" stroke="#79c0ff"/><text x="480" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <circle cx="440" cy="120" r="18" fill="#161b22" stroke="#79c0ff"/><text x="440" y="124" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <circle cx="520" cy="120" r="18" fill="#161b22" stroke="#f0883e"/><text x="520" y="124" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <line x1="468" y1="72" x2="452" y2="108" stroke="#8b949e"/>
    <line x1="492" y1="72" x2="508" y2="108" stroke="#8b949e"/>
    <text x="480" y="200" fill="#79c0ff" text-anchor="middle" font-size="9">balanced: heights differ by <= 1</text>
  </g>
</svg>

Node `30` is left-heavy by 2, so a single right rotation promotes `20` to the root; `30` becomes `20`'s right child, restoring balance.

## 5. Runnable example

```java
// AvlTree.java
public class AvlTree {

    static class Node {
        int value, height = 1;
        Node left, right;
        Node(int value) { this.value = value; }
    }

    static int height(Node n) { return n == null ? 0 : n.height; }
    static int balanceFactor(Node n) { return n == null ? 0 : height(n.left) - height(n.right); }
    static void recompute(Node n) { n.height = 1 + Math.max(height(n.left), height(n.right)); }

    // Basic: the two rotation primitives every rebalance is built from.
    static Node rotateRight(Node y) {
        Node x = y.left;
        y.left = x.right;
        x.right = y;
        recompute(y); // recompute the LOWER node first -- its height depends on its (now smaller) subtree
        recompute(x);
        return x; // x is the new subtree root
    }

    static Node rotateLeft(Node x) {
        Node y = x.right;
        x.right = y.left;
        y.left = x;
        recompute(x);
        recompute(y);
        return y;
    }

    static void basicLevel() {
        Node root = new Node(30);
        root.left = new Node(20);
        root.left.left = new Node(10);
        root.height = 3; root.left.height = 2; root.left.left.height = 1;

        System.out.println("basic: balance(30) before rotation -> " + balanceFactor(root));
        root = rotateRight(root);
        System.out.println("basic: new root after rotateRight -> " + root.value);
        System.out.println("basic: balance(new root) after rotation -> " + balanceFactor(root));
    }

    // Intermediate: a full self-balancing insert, picking the right rotation case from the balance factor.
    static Node insert(Node node, int value) {
        if (node == null) return new Node(value);
        if (value < node.value) node.left = insert(node.left, value);
        else if (value > node.value) node.right = insert(node.right, value);
        else return node;

        recompute(node);
        int balance = balanceFactor(node);

        if (balance > 1 && value < node.left.value) return rotateRight(node);               // left-left case
        if (balance < -1 && value > node.right.value) return rotateLeft(node);              // right-right case
        if (balance > 1 && value > node.left.value) {                                       // left-right case
            node.left = rotateLeft(node.left);
            return rotateRight(node);
        }
        if (balance < -1 && value < node.right.value) {                                     // right-left case
            node.right = rotateRight(node.right);
            return rotateLeft(node);
        }
        return node;
    }

    static void inOrder(Node node, StringBuilder out) {
        if (node == null) return;
        inOrder(node.left, out);
        out.append(node.value).append(" ");
        inOrder(node.right, out);
    }

    static void intermediateLevel() {
        Node root = null;
        for (int v : new int[]{10, 20, 30, 40, 50, 25}) root = insert(root, v); // 10,20,30 alone would skew a plain BST

        StringBuilder out = new StringBuilder();
        inOrder(root, out);
        System.out.println("intermediate: in-order after inserting 10,20,30,40,50,25 -> " + out.toString().trim());
        System.out.println("intermediate: root after rebalancing -> " + root.value + ", height -> " + root.height);
    }

    // Advanced: insert enough sorted data to prove height stays O(log n), unlike a plain BST's O(n) chain.
    static void advancedLevel() {
        Node root = null;
        for (int v = 1; v <= 1000; v++) root = insert(root, v); // fully sorted input -- worst case for a plain BST

        System.out.println("advanced: inserted 1000 sorted values, final height -> " + root.height);
        System.out.println("advanced: log2(1000) ~= 10, so an AVL tree's height stays close to that bound");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AvlTree.java`, then run `java AvlTree.java`.

## 6. Walkthrough

1. `basicLevel()` builds an already-unbalanced tree by hand: `30` has left child `20`, which has left child `10` — a balance factor of `2` at `30`. `rotateRight(30)` promotes `20` to be the new subtree root, makes `30` its right child, and re-attaches `20`'s old right subtree (empty here) as `30`'s new left subtree. The result has balance `0` at the new root.
2. `intermediateLevel()` inserts `10, 20, 30` in sorted order — which would make a plain BST degenerate into a straight chain. After `30` is inserted, `insert` detects `balance(10) = -2` (right-heavy) and applies a left rotation, keeping the tree bushy. It continues through `40, 50, 25`, each time rechecking balance factors on the way back up the recursion and rotating whenever a node's balance leaves `{-1, 0, 1}`.
3. `advancedLevel()` inserts `1` through `1000` in strictly increasing order. A plain BST would produce a chain of height `1000`; the AVL tree's continuous rebalancing keeps its height close to `log2(1000) ≈ 10`, confirming the `O(log n)` guarantee holds even for the worst possible insertion order.

## 7. Gotchas & takeaways

> Gotcha: after a rotation, recompute the height of the node that moved *down* first, then the node that moved *up* — the new root's height depends on its children's already-updated heights. Recomputing in the wrong order leaves stale height values that cause future balance-factor checks to misfire.

- The AVL invariant (`balance factor ∈ {-1, 0, 1}` at every node) guarantees `O(log n)` height, and therefore `O(log n)` search, insert, and delete, even in the worst case.
- There are exactly four rebalancing cases: left-left, right-right (single rotation), and left-right, right-left (double rotation).
- Balance-factor checks happen bottom-up, on the path back from the inserted/deleted node to the root — at most one (possibly double) rotation is needed to restore balance after a single insert.
- Related concepts: [Red-black trees](0111-red-black-trees.md), [Why balancing matters (skew to O(n))](0112-why-balancing-matters-skew-to-o-n.md), [BST insert / search / delete](0103-bst-insert-search-delete.md).
