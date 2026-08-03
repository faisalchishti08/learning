---
card: data-structures
gi: 154
slug: interval-tree
title: Interval tree
---

## 1. What it is

An **interval tree** stores a set of intervals (ranges like `[15, 20]`) and answers "which stored intervals overlap this query interval (or point)?" quickly. It is a binary search tree keyed by each interval's start, where every node also remembers the **maximum end value** in its whole subtree.

## 2. Why & when

Use an interval tree when you must repeatedly find overlaps among many intervals — meeting-room booking conflicts, genome-range lookups, or which UI elements overlap a click region. Checking every stored interval against the query is `O(n)` per query. An interval tree answers "does anything overlap?" or "find one overlap" in `O(log n)`, and lists all overlaps in `O(log n + k)` for `k` results.

## 3. Core concept

**The shape.** A balanced [binary search tree](0098-binary-tree-binary-search-tree-bst.md) (or a red-black tree). Each node stores one interval `[low, high]`, ordered by `low`. Each node also stores `maxEnd`: the largest `high` value anywhere in its subtree (itself included).

**The invariant.** `maxEnd(node) = max(node.high, maxEnd(left), maxEnd(right))`. This is maintained bottom-up, the same way a segment tree maintains its combined values.

**Why it makes overlap search fast.** To find an overlap with query `[qlow, qhigh]`, start at the root. If the root's interval overlaps the query, return it. Otherwise, only descend left if the left subtree's `maxEnd >= qlow` — because if even the largest end on the left is smaller than `qlow`, nothing on the left can possibly reach the query's start. This prunes half the tree at every step that fails the check, giving `O(log n)` instead of `O(n)`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An interval tree where each node stores an interval and the max end value in its subtree">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="270" y="10" width="120" height="36" fill="#161b22" stroke="#79c0ff"/>
    <text x="330" y="26" text-anchor="middle">[15,20]</text><text x="330" y="40" text-anchor="middle">maxEnd=30</text>

    <rect x="90" y="80" width="120" height="36" fill="#161b22" stroke="#79c0ff"/>
    <text x="150" y="96" text-anchor="middle">[5,12]</text><text x="150" y="110" text-anchor="middle">maxEnd=12</text>

    <rect x="450" y="80" width="120" height="36" fill="#161b22" stroke="#79c0ff"/>
    <text x="510" y="96" text-anchor="middle">[17,30]</text><text x="510" y="110" text-anchor="middle">maxEnd=30</text>

    <rect x="450" y="150" width="120" height="36" fill="#0d1117" stroke="#8b949e"/>
    <text x="510" y="166" text-anchor="middle">[26,28]</text><text x="510" y="180" text-anchor="middle">maxEnd=28</text>

    <line x1="330" y1="46" x2="150" y2="80" stroke="#79c0ff"/>
    <line x1="330" y1="46" x2="510" y2="80" stroke="#79c0ff"/>
    <line x1="510" y1="116" x2="510" y2="150" stroke="#79c0ff"/>

    <text x="330" y="210" font-size="9" fill="#8b949e">query [19,21]: root overlaps -&gt; return [15,20] (or keep searching for all overlaps)</text>
  </g>
</svg>

`maxEnd` lets a search skip an entire subtree once its largest end can no longer reach the query's start.

## 5. Runnable example

```java
// IntervalTree.java
import java.util.*;

public class IntervalTree {

    static class Node {
        int low, high, maxEnd;
        Node left, right;

        Node(int low, int high) { this.low = low; this.high = high; this.maxEnd = high; }
    }

    static boolean overlaps(int low1, int high1, int low2, int high2) {
        return low1 <= high2 && low2 <= high1;
    }

    // Basic: insert intervals (unbalanced BST by low, for teaching clarity) and find one overlap.
    static class Tree {
        Node root;

        void insert(int low, int high) { root = insert(root, low, high); }

        Node insert(Node node, int low, int high) {
            if (node == null) return new Node(low, high);
            if (low < node.low) node.left = insert(node.left, low, high);
            else node.right = insert(node.right, low, high);
            node.maxEnd = Math.max(node.maxEnd, high);
            return node;
        }

        Node findOverlap(int low, int high) { return findOverlap(root, low, high); }

        Node findOverlap(Node node, int low, int high) {
            if (node == null) return null;
            if (overlaps(node.low, node.high, low, high)) return node;
            if (node.left != null && node.left.maxEnd >= low) return findOverlap(node.left, low, high);
            return findOverlap(node.right, low, high);
        }
    }

    static void basicLevel() {
        Tree tree = new Tree();
        for (int[] iv : new int[][]{{15, 20}, {10, 30}, {5, 12}, {17, 19}, {30, 40}}) {
            tree.insert(iv[0], iv[1]);
        }
        Node found = tree.findOverlap(6, 7);
        System.out.println("basic: overlap with [6,7] -> [" + found.low + "," + found.high + "]");
    }

    // Intermediate: find ALL overlapping intervals, not just one.
    static class AllOverlapsTree extends Tree {
        void findAllOverlaps(Node node, int low, int high, List<Node> results) {
            if (node == null) return;
            if (overlaps(node.low, node.high, low, high)) results.add(node);
            if (node.left != null && node.left.maxEnd >= low) findAllOverlaps(node.left, low, high, results);
            if (node.right != null) findAllOverlaps(node.right, low, high, results);
        }

        List<Node> findAll(int low, int high) {
            List<Node> results = new ArrayList<>();
            findAllOverlaps(root, low, high, results);
            return results;
        }
    }

    static void intermediateLevel() {
        AllOverlapsTree tree = new AllOverlapsTree();
        for (int[] iv : new int[][]{{15, 20}, {10, 30}, {5, 12}, {17, 19}, {30, 40}}) {
            tree.insert(iv[0], iv[1]);
        }
        List<Node> all = tree.findAll(18, 22);
        StringBuilder sb = new StringBuilder();
        for (Node n : all) sb.append("[").append(n.low).append(",").append(n.high).append("] ");
        System.out.println("intermediate: all overlaps with [18,22] -> " + sb.toString().trim());
    }

    // Advanced: applied to meeting-room conflict checking before booking a new meeting.
    static boolean hasConflict(Tree tree, int start, int end) {
        return tree.findOverlap(start, end) != null;
    }

    static void advancedLevel() {
        Tree bookings = new Tree();
        bookings.insert(9 * 60, 10 * 60);   // 9:00-10:00
        bookings.insert(11 * 60, 12 * 60);  // 11:00-12:00

        int requestStart = 9 * 60 + 30, requestEnd = 10 * 60 + 30; // 9:30-10:30
        System.out.println("advanced: conflict for 9:30-10:30 -> " + hasConflict(bookings, requestStart, requestEnd));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java IntervalTree.java`

## 6. Walkthrough

Insert `[15,20]`, `[10,30]`, `[5,12]`, `[17,19]`, `[30,40]`, in that order, keyed by `low`. `[15,20]` becomes the root. `[10,30]` goes left (`10 < 15`); `[5,12]` goes further left under it; `[17,19]` and `[30,40]` go right of the root. Each insert updates `maxEnd` on the path back to the root, so the root ends with `maxEnd = 40`.

Now query `findOverlap(6, 7)`. At the root `[15,20]`: does `[15,20]` overlap `[6,7]`? No (`15 > 7`). Check the left subtree's `maxEnd`: the left child `[10,30]` has `maxEnd = 30 >= 6`, so descend left. At `[10,30]`: overlap with `[6,7]`? No (`10 > 7`). Left child `[5,12]` has `maxEnd = 12 >= 6`, descend left. At `[5,12]`: overlap with `[6,7]`? Yes, `5 <= 7` and `6 <= 12`. Return `[5,12]`.

Three comparisons found the overlap, without ever touching `[17,19]` or `[30,40]` — the `maxEnd` pruning skipped the right side of the tree entirely.

**Complexity.** With a self-balancing BST backing it: insert `O(log n)`, find one overlap `O(log n)`, find all `k` overlaps `O(log n + k)`. Space: `O(n)`.

## 7. Gotchas & takeaways

> The `maxEnd` pruning rule only tells you a subtree is *safe to skip*; it does not guarantee the subtree you *do* descend into contains an overlap. You must still check the node itself, and possibly backtrack to the other child (as `findAll` does) to be exhaustive.

- A plain unbalanced BST (as shown above, keyed by insertion order) can degrade to `O(n)` per operation on sorted input. Real-world implementations use a red-black tree or an [AVL tree](0110-avl-trees-rotations.md) to guarantee `O(log n)`.
- Interval trees answer "overlap" queries. If you instead need "which point is contained in the most intervals at once," look at a related structure: the segment tree with counting, or an augmented BIT over a coordinate-compressed timeline.
- For **static** intervals with no updates, sorting by start and doing a sweep-line pass is often simpler than building a tree.
