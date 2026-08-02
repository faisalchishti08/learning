---
card: data-structures
gi: 111
slug: red-black-trees
title: Red-black trees
---

## 1. What it is

A **red-black tree** is a self-balancing binary search tree (BST) where every node is colored either **red** or **black**. A small set of coloring rules guarantees the tree's height never exceeds roughly `2 * log2(n)`, without requiring the strict per-node balance AVL trees enforce.

## 2. Why & when

Red-black trees trade a little search speed for cheaper rebalancing: they need fewer rotations per insert or delete than an AVL tree, because their balance rule is looser. This makes them the standard choice inside library data structures that mix frequent writes with reads — Java's `TreeMap` and `TreeSet`, and `HashMap`'s treeified buckets, are both red-black trees internally.

## 3. Core concept

**The five rules.** A valid red-black tree satisfies all of these:

1. Every node is red or black.
2. The root is always black.
3. Every `null` leaf (an empty child) counts as black.
4. A red node never has a red child (no two reds in a row on any path).
5. Every path from a node down to any of its descendant `null` leaves passes through the same number of black nodes — the node's **black-height**.

**How the rules bound the height.** Rule 5 fixes the black-node count on every path; rule 4 forbids two consecutive reds, so red nodes can at most double the length of any path relative to an all-black path. Combining both facts caps the longest path at roughly twice the shortest, which keeps the tree's overall height at `O(log n)` — looser than AVL's tight balance, but still logarithmic.

**Restoring the rules after insert.** A new node is always inserted red (this cannot violate rule 5, since it adds no black node to any path). If its parent is also red, rule 4 is violated, and the fix depends on the color of the node's "uncle" (the parent's sibling):

- **Uncle is red:** recolor the parent, uncle, and grandparent, then recheck the rules further up — no rotation needed.
- **Uncle is black (or missing):** one or two rotations, plus a recoloring, fix the violation locally, exactly as in an AVL rebalance.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A red black tree with black root 10, red children 5 and 15, showing every root to null path passing through the same number of black nodes">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="18" fill="#161b22" stroke="#8b949e" stroke-width="2"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <text x="340" y="20" fill="#8b949e" font-size="9">black (root)</text>
    <circle cx="220" cy="90" r="18" fill="#3d1418" stroke="#f85149" stroke-width="2"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <circle cx="380" cy="90" r="18" fill="#3d1418" stroke="#f85149" stroke-width="2"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">15</text>
    <text x="150" y="90" fill="#f85149" font-size="9">red</text>
    <text x="450" y="90" fill="#f85149" font-size="9">red</text>
    <circle cx="180" cy="150" r="16" fill="#161b22" stroke="#8b949e" stroke-width="2"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">2</text>
    <circle cx="420" cy="150" r="16" fill="#161b22" stroke="#8b949e" stroke-width="2"/><text x="420" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">20</text>
    <line x1="286" y1="42" x2="234" y2="78" stroke="#8b949e"/>
    <line x1="314" y1="42" x2="366" y2="78" stroke="#8b949e"/>
    <line x1="208" y1="102" x2="192" y2="138" stroke="#8b949e"/>
    <line x1="392" y1="102" x2="408" y2="138" stroke="#8b949e"/>
    <text x="300" y="195" fill="#8b949e" text-anchor="middle" font-size="9">every path root-&gt;null passes through exactly 2 black nodes (counting null as black)</text>
  </g>
</svg>

The root (`10`) and the leaf-level black `null` children give every path the same black-node count, even though red nodes (`5`, `15`) make some paths visually longer.

## 5. Runnable example

```java
// RedBlackTree.java
public class RedBlackTree {

    static final boolean RED = true, BLACK = false;

    static class Node {
        int value;
        boolean color = RED; // new nodes are always inserted red
        Node left, right, parent;
        Node(int value) { this.value = value; }
    }

    Node root;

    static boolean colorOf(Node n) { return n == null ? BLACK : n.color; } // null counts as black (rule 3)

    // Basic: the rotation primitives, identical in shape to an AVL tree's, but also fixing up parent pointers.
    void rotateLeft(Node x) {
        Node y = x.right;
        x.right = y.left;
        if (y.left != null) y.left.parent = x;
        y.parent = x.parent;
        if (x.parent == null) root = y;
        else if (x == x.parent.left) x.parent.left = y;
        else x.parent.right = y;
        y.left = x;
        x.parent = y;
    }

    void rotateRight(Node y) {
        Node x = y.left;
        y.left = x.right;
        if (x.right != null) x.right.parent = y;
        x.parent = y.parent;
        if (y.parent == null) root = x;
        else if (y == y.parent.left) y.parent.left = x;
        else y.parent.right = x;
        x.right = y;
        y.parent = x;
    }

    // Intermediate: insert like a plain BST, then fix up red-red violations bottom-up.
    void insert(int value) {
        Node node = new Node(value);
        Node parent = null, cur = root;
        while (cur != null) {
            parent = cur;
            cur = value < cur.value ? cur.left : cur.right;
        }
        node.parent = parent;
        if (parent == null) root = node;
        else if (value < parent.value) parent.left = node;
        else parent.right = node;
        fixInsert(node);
    }

    void fixInsert(Node node) {
        while (colorOf(node.parent) == RED) {
            Node parent = node.parent, grandparent = parent.parent;
            boolean parentIsLeft = parent == grandparent.left;
            Node uncle = parentIsLeft ? grandparent.right : grandparent.left;

            if (colorOf(uncle) == RED) { // uncle red: recolor and move up -- no rotation needed
                parent.color = BLACK;
                uncle.color = BLACK;
                grandparent.color = RED;
                node = grandparent;
            } else { // uncle black: rotation(s) plus recoloring fix it locally
                if (parentIsLeft && node == parent.right) { node = parent; rotateLeft(node); parent = node.parent; }
                else if (!parentIsLeft && node == parent.left) { node = parent; rotateRight(node); parent = node.parent; }
                parent.color = BLACK;
                grandparent.color = RED;
                if (parentIsLeft) rotateRight(grandparent); else rotateLeft(grandparent);
            }
            if (node == root) break;
        }
        root.color = BLACK; // rule 2: the root is always black
    }

    static void inOrder(Node node, StringBuilder out) {
        if (node == null) return;
        inOrder(node.left, out);
        out.append(node.value).append(node.color == RED ? "R " : "B ");
        inOrder(node.right, out);
    }

    static int blackHeight(Node node) {
        if (node == null) return 1; // null counts as one black node (rule 3)
        int left = blackHeight(node.left), right = blackHeight(node.right);
        return Math.max(left, right) + (colorOf(node) == BLACK ? 1 : 0);
    }

    static void basicAndIntermediate() {
        RedBlackTree tree = new RedBlackTree();
        for (int v : new int[]{10, 5, 15, 2, 20}) tree.insert(v);

        StringBuilder out = new StringBuilder();
        inOrder(tree.root, out);
        System.out.println("basic+intermediate: in-order with colors -> " + out.toString().trim());
        System.out.println("intermediate: root color -> " + (tree.root.color == BLACK ? "BLACK (rule 2 holds)" : "RED (bug!)"));
    }

    // Advanced: insert enough sorted values to confirm height stays close to 2*log2(n), unlike a plain BST.
    static void advancedLevel() {
        RedBlackTree tree = new RedBlackTree();
        for (int v = 1; v <= 1000; v++) tree.insert(v); // sorted input -- worst case for a plain BST

        int height = heightOf(tree.root);
        System.out.println("advanced: inserted 1000 sorted values, tree height -> " + height);
        System.out.println("advanced: bound 2*log2(1000) ~= 20, black-height -> " + blackHeight(tree.root));
    }

    static int heightOf(Node node) {
        if (node == null) return 0;
        return 1 + Math.max(heightOf(node.left), heightOf(node.right));
    }

    public static void main(String[] args) {
        basicAndIntermediate();
        advancedLevel();
    }
}
```

**How to run:** save as `RedBlackTree.java`, then run `java RedBlackTree.java`.

## 6. Walkthrough

1. `basicAndIntermediate()` inserts `10, 5, 15, 2, 20`. `10` becomes the root and is immediately recolored black (rule 2). `5` and `15` are inserted red as children of the black root — no violation, since their parent is black. `2` is inserted red under `5`; because `5` is also red, `fixInsert` checks `2`'s uncle (`15`). Since `15` is red, the fix recolors `5` and `15` to black and `10` to red, then continues checking from `10` upward — but `10` is the root, so it is forced back to black at the end.
2. The printed in-order traversal shows each node's color; the root always prints `B` (black), confirming rule 2 held after all the recoloring.
3. `advancedLevel()` inserts `1` through `1000` in sorted order — the same adversarial input that breaks a plain BST into an `O(n)`-height chain. The red-black tree's height comes out close to the `2 * log2(1000) ≈ 20` bound, and `blackHeight` confirms every path carries the same black-node count, proving rule 5 held throughout every insert.

## 7. Gotchas & takeaways

> Gotcha: the "uncle is red" case only recolors and moves the violation check up the tree — it does **not** rotate. Applying a rotation in that case, instead of recoloring and continuing the loop from the grandparent, is a common bug that leaves the tree in a state where rule 4 is fixed locally but may still be violated higher up.

- Red-black trees allow a looser balance than AVL trees (height up to `~2 * log2(n)` instead of a tight `1.44 * log2(n)`), trading slightly slower lookups for fewer rotations per write.
- The root is always black; every `null` leaf counts as black; a red node never has a red child; every root-to-leaf path has the same black-node count.
- Java's `TreeMap` and `TreeSet` are red-black trees internally, as is a treeified `HashMap` bucket.
- Related concepts: [AVL trees & rotations](0110-avl-trees-rotations.md), [Why balancing matters (skew to O(n))](0112-why-balancing-matters-skew-to-o-n.md), [TreeMap & TreeSet (red-black backed)](0113-treemap-treeset-red-black-backed.md).
