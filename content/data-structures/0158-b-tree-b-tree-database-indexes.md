---
card: data-structures
gi: 158
slug: b-tree-b-tree-database-indexes
title: B-tree & B+-tree (database indexes)
---

## 1. What it is

A **B-tree** is a self-balancing search tree where each node holds many keys, not just one, and has many children, not just two. A **B+-tree** is a variant where every key lives in the leaves, the leaves are linked together in a chain, and internal nodes only hold copies of keys used for navigation. Both keep the tree extremely short and wide, which matters when data lives on disk.

## 2. Why & when

An in-memory tree like an [AVL tree](0110-avl-trees-rotations.md) picks a small branching factor (2 children) because comparing values in RAM is cheap. A database index lives on disk, where each read is a slow, expensive block fetch — often microseconds to milliseconds versus nanoseconds for RAM. A B-tree trades "more comparisons per node" (cheap, in RAM) for "fewer disk block reads" (expensive), by packing hundreds of keys into each node so one disk read yields hundreds of comparisons' worth of information. This is why B-trees and B+-trees back nearly every relational database index (MySQL's InnoDB, PostgreSQL) and many filesystems.

## 3. Core concept

**The shape.** A B-tree of **order `m`** (also called minimum degree `t`) has nodes with between `t-1` and `2t-1` keys (except the root, which allows fewer). A node with `k` keys has `k+1` children. Keys within a node are sorted, and every child between two keys holds values strictly between them — the same ordering invariant as a BST, generalized to many keys per node.

**The invariant.** Every leaf sits at the **same depth**. Unlike an AVL tree, which balances by rotation, a B-tree balances by **splitting** a node when it overflows (gets too many keys) and **merging** nodes when one underflows (gets too few keys) after a deletion. This guarantees `O(log n)` height without ever needing a node to be "unbalanced" the way a plain BST can be.

**The B+-tree difference.** In a plain B-tree, keys and their associated data can live in internal nodes. In a B+-tree, **all actual data lives in the leaves**; internal nodes only store routing keys, and the leaves are linked in a singly-linked list left to right. This makes range scans (`SELECT * WHERE age BETWEEN 20 AND 30`) fast: find the starting leaf once, then walk the leaf chain — no need to revisit internal nodes.

**Why it makes disk operations fast.** With branching factor `m` in the hundreds, a B-tree over a billion rows has height around `log_m(10^9)`, which is 3–4 for `m = 500`. Each level is one disk read, so a lookup costs only 3–4 disk reads instead of the `log_2(10^9) ≈ 30` reads an in-memory-style binary tree would need.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A B+-tree with a routing root, internal nodes, and leaf nodes linked left to right for range scans">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="250" y="10" width="140" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="30" text-anchor="middle">[ 30 | 60 ]</text>

    <rect x="80" y="80" width="120" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="140" y="100" text-anchor="middle">[ 10 | 20 ]</text>
    <rect x="270" y="80" width="120" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="330" y="100" text-anchor="middle">[ 40 | 50 ]</text>
    <rect x="450" y="80" width="120" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="510" y="100" text-anchor="middle">[ 70 | 80 ]</text>

    <line x1="320" y1="40" x2="140" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="330" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="510" y2="80" stroke="#79c0ff"/>

    <rect x="10" y="150" width="90" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="55" y="170" text-anchor="middle" font-size="9">leaf: 5,10</text>
    <rect x="110" y="150" width="90" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="155" y="170" text-anchor="middle" font-size="9">leaf: 15,20</text>
    <rect x="290" y="150" width="90" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="335" y="170" text-anchor="middle" font-size="9">leaf: 40,45</text>
    <rect x="390" y="150" width="90" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="435" y="170" text-anchor="middle" font-size="9">leaf: 50,55</text>
    <rect x="470" y="150" width="90" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="515" y="170" text-anchor="middle" font-size="9">leaf: 70,75</text>

    <line x1="100" y1="165" x2="110" y2="165" stroke="#f0883e" marker-end="url(#arrow)"/>
    <line x1="200" y1="165" x2="290" y2="165" stroke="#f0883e" stroke-dasharray="2,2"/>
    <line x1="380" y1="165" x2="390" y2="165" stroke="#f0883e"/>
    <line x1="480" y1="165" x2="470" y2="165" stroke="#f0883e" stroke-dasharray="2,2"/>

    <text x="320" y="205" font-size="9" fill="#8b949e">leaves link left-to-right; a range scan walks the chain after one root-to-leaf descent</text>
  </g>
</svg>

Internal nodes only route; every key and its data live in a leaf, and leaves form a chain for fast range scans.

## 5. Runnable example

```java
// BTree.java
import java.util.*;

public class BTree {

    // Basic: a simplified in-memory B-tree (order-based, minimum degree t) supporting insert and search.
    static class Node {
        List<Integer> keys = new ArrayList<>();
        List<Node> children = new ArrayList<>();
        boolean leaf = true;
    }

    static class SimpleBTree {
        Node root = new Node();
        int t; // minimum degree: node has between t-1 and 2t-1 keys

        SimpleBTree(int t) { this.t = t; }

        boolean search(Node node, int key) {
            int i = 0;
            while (i < node.keys.size() && key > node.keys.get(i)) i++;
            if (i < node.keys.size() && node.keys.get(i) == key) return true;
            if (node.leaf) return false;
            return search(node.children.get(i), key);
        }

        boolean search(int key) { return search(root, key); }

        void insert(int key) {
            if (root.keys.size() == 2 * t - 1) {
                Node newRoot = new Node();
                newRoot.leaf = false;
                newRoot.children.add(root);
                splitChild(newRoot, 0);
                root = newRoot;
            }
            insertNonFull(root, key);
        }

        void splitChild(Node parent, int index) {
            Node child = parent.children.get(index);
            Node sibling = new Node();
            sibling.leaf = child.leaf;

            for (int j = t; j < 2 * t - 1; j++) sibling.keys.add(child.keys.get(j));
            if (!child.leaf) {
                for (int j = t; j < 2 * t; j++) sibling.children.add(child.children.get(j));
                child.children.subList(t, child.children.size()).clear();
            }

            int midKey = child.keys.get(t - 1);
            child.keys.subList(t - 1, child.keys.size()).clear();

            parent.children.add(index + 1, sibling);
            parent.keys.add(index, midKey);
        }

        void insertNonFull(Node node, int key) {
            int i = node.keys.size() - 1;
            if (node.leaf) {
                node.keys.add(0); // grow by one slot
                while (i >= 0 && key < node.keys.get(i)) {
                    node.keys.set(i + 1, node.keys.get(i));
                    i--;
                }
                node.keys.set(i + 1, key);
            } else {
                while (i >= 0 && key < node.keys.get(i)) i--;
                i++;
                if (node.children.get(i).keys.size() == 2 * t - 1) {
                    splitChild(node, i);
                    if (key > node.keys.get(i)) i++;
                }
                insertNonFull(node.children.get(i), key);
            }
        }
    }

    static void basicLevel() {
        SimpleBTree tree = new SimpleBTree(2); // minimum degree 2 -> nodes hold 1-3 keys
        for (int key : new int[]{10, 20, 5, 6, 12, 30, 7, 17}) tree.insert(key);

        System.out.println("basic: search(6) -> " + tree.search(6));
        System.out.println("basic: search(99) -> " + tree.search(99));
    }

    // Intermediate: inspect the tree's structure after enough inserts to force a root split.
    static void intermediateLevel() {
        SimpleBTree tree = new SimpleBTree(2);
        for (int key = 1; key <= 10; key++) tree.insert(key);

        System.out.println("intermediate: root key count after 10 inserts -> " + tree.root.keys.size());
        System.out.println("intermediate: root is leaf? -> " + tree.root.leaf);
    }

    // Advanced: simulate the "one node = one disk block" cost model, counting node visits per search.
    static int visitsForSearch(SimpleBTree tree, int key) {
        int[] visits = {0};
        countingSearch(tree.root, key, visits);
        return visits[0];
    }

    static boolean countingSearch(Node node, int key, int[] visits) {
        visits[0]++;
        int i = 0;
        while (i < node.keys.size() && key > node.keys.get(i)) i++;
        if (i < node.keys.size() && node.keys.get(i) == key) return true;
        if (node.leaf) return false;
        return countingSearch(node.children.get(i), key, visits);
    }

    static void advancedLevel() {
        SimpleBTree tree = new SimpleBTree(2);
        for (int key = 1; key <= 30; key++) tree.insert(key);

        System.out.println("advanced: node visits ('disk reads') to find 25 -> " + visitsForSearch(tree, 25));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java BTree.java`

## 6. Walkthrough

Build a B-tree with minimum degree `t = 2` (each node holds 1 to 3 keys). Insert `10, 20, 5, 6, 12, 30, 7, 17` one at a time. The root starts empty and absorbs keys until it would exceed `2t-1 = 3` keys. Inserting `6` after `10, 20, 5` would make 4 keys, so the tree splits the root first: the middle key (`10`) moves up to a brand-new root, and the old root's keys split into `[5]` and `[20]` as two children. Now `6` inserts into the left child `[5]`, becoming `[5, 6]`.

This split-before-overflow pattern repeats as more keys arrive, so the tree grows **wider**, not taller, keeping every leaf at the same depth.

Trace `search(6)`. Start at the root `[10]`. Since `6 < 10`, go to the left child. That child holds `[5, 6]` (or similar, depending on later splits); scan its keys left to right, find `6`, return `true`. In a real disk-backed B-tree, each node visited here is exactly one disk block read, so a 3-node path means 3 disk reads regardless of how many total keys are stored.

**Complexity.** Search, insert, delete: `O(log_t n)`, where `t` is the minimum degree (branching factor). Because `t` is large (hundreds, for a disk-backed index), `log_t n` stays tiny (3-4) even for billions of keys. Space: `O(n)`.

## 7. Gotchas & takeaways

> A B-tree's branching factor is chosen to match the disk block size (or the database page size), not arbitrarily. A node's total serialized size should fit in one page (commonly 4 KB or 16 KB) — that constraint, not "make it fast," is what decides `t` in a real database.

- Use a **B-tree** when internal nodes may also serve as fast paths to non-leaf data. Use a **B+-tree** when you need efficient **range scans** — almost all production database indexes are B+-trees for exactly this reason.
- Deletion in a B-tree is more involved than insertion: it must borrow a key from a sibling or merge nodes to keep every node above the minimum key count. Most textbook treatments skip this; production database code implements it carefully.
- Don't reach for a B-tree in pure in-memory Java code with a small dataset — a [TreeMap](0113-treemap-treeset-red-black-backed.md) (backed by a red-black tree) or an [AVL tree](0110-avl-trees-rotations.md) is simpler and just as fast when disk I/O is not the bottleneck.
