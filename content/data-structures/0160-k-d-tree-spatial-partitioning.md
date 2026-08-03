---
card: data-structures
gi: 160
slug: k-d-tree-spatial-partitioning
title: k-d tree (spatial partitioning)
---

## 1. What it is

A **k-d tree** (short for "k-dimensional tree") is a binary tree that organizes points in multi-dimensional space. It works like a [BST](0098-binary-tree-binary-search-tree-bst.md), but instead of always comparing on one key, it **cycles through dimensions** as it goes deeper — split on x at the root, y at the next level, x again below that, and so on for 2D data.

## 2. Why & when

Use a k-d tree when you need to search points by spatial location — "find the nearest restaurant to this coordinate" or "find all points inside this rectangle." Checking every point against a query is `O(n)`. A balanced k-d tree answers a nearest-neighbor or range query in roughly `O(log n)` for low dimensions (2D or 3D), by pruning entire regions of space that cannot possibly contain a better answer.

## 3. Core concept

**The shape.** Each node holds one point and a **splitting dimension** determined by its depth: at depth `0`, split on the x-coordinate; at depth `1`, split on y; at depth `2`, back to x (for 2D data — cycle through all `k` dimensions as depth grows). Points with a smaller value on that dimension go left; larger go right, the same rule as a BST but restricted to one coordinate at a time.

**The invariant.** Every node's subtree occupies one rectangular region of space. The splitting line through a node divides that region into two smaller rectangles, one per child. As you descend, the region shrinks.

**Why it makes nearest-neighbor search fast.** Searching for the closest point to a query works like this: descend the tree as if inserting the query point, remembering the best point found so far. Then backtrack up the tree; at each node, check whether the splitting plane is closer to the query than the current best distance. If it is farther than the best distance found so far, that whole other subtree is **pruned** — skipped entirely, because no point in it could possibly be closer than what you already have.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 2D k-d tree shown as recursive splitting lines dividing the plane, alternating between vertical and horizontal splits">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="20" y="20" width="300" height="180" fill="none" stroke="#8b949e"/>
    <line x1="150" y1="20" x2="150" y2="200" stroke="#79c0ff" stroke-width="2"/>
    <text x="150" y="14" text-anchor="middle" font-size="9" fill="#79c0ff">split x=150 (root)</text>

    <line x1="20" y1="90" x2="150" y2="90" stroke="#f0883e"/>
    <text x="85" y="84" text-anchor="middle" font-size="8" fill="#f0883e">split y</text>
    <line x1="150" y1="140" x2="320" y2="140" stroke="#f0883e"/>
    <text x="235" y="134" text-anchor="middle" font-size="8" fill="#f0883e">split y</text>

    <circle cx="150" cy="90" r="3" fill="#e6edf3"/>
    <circle cx="80" cy="90" r="3" fill="#e6edf3"/>
    <circle cx="60" cy="150" r="3" fill="#e6edf3"/>
    <circle cx="230" cy="140" r="3" fill="#e6edf3"/>
    <circle cx="280" cy="60" r="3" fill="#e6edf3"/>
    <circle cx="270" cy="180" r="3" fill="#e6edf3"/>

    <text x="400" y="40" font-size="9">root splits x -&gt; children split y -&gt; grandchildren split x again</text>
    <text x="400" y="60" font-size="9" fill="#8b949e">each split halves the plane into rectangular regions</text>
    <text x="400" y="90" font-size="9" fill="#f0883e">nearest-neighbor search skips a region once its</text>
    <text x="400" y="105" font-size="9" fill="#f0883e">splitting line is farther than the current best distance</text>
  </g>
</svg>

Alternating splits (x, then y, then x...) carve the plane into nested rectangles.

## 5. Runnable example

```java
// KDTree.java
import java.util.*;

public class KDTree {

    record Point(double x, double y) {}

    static class Node {
        Point point;
        Node left, right;
        Node(Point point) { this.point = point; }
    }

    // Basic: build a k-d tree by inserting points, alternating split dimension by depth.
    static class Tree {
        Node root;

        void insert(Point point) { root = insert(root, point, 0); }

        Node insert(Node node, Point point, int depth) {
            if (node == null) return new Node(point);
            boolean splitOnX = depth % 2 == 0;
            double nodeVal = splitOnX ? node.point.x() : node.point.y();
            double pointVal = splitOnX ? point.x() : point.y();
            if (pointVal < nodeVal) node.left = insert(node.left, point, depth + 1);
            else node.right = insert(node.right, point, depth + 1);
            return node;
        }
    }

    static void basicLevel() {
        Tree tree = new Tree();
        for (double[] xy : new double[][]{{5, 4}, {2, 6}, {8, 1}, {1, 3}, {7, 7}, {9, 2}}) {
            tree.insert(new Point(xy[0], xy[1]));
        }
        System.out.println("basic: root point -> " + tree.root.point);
    }

    // Intermediate: nearest-neighbor search with pruning.
    static double distSq(Point a, Point b) {
        double dx = a.x() - b.x(), dy = a.y() - b.y();
        return dx * dx + dy * dy;
    }

    static class NearestSearch {
        Point best;
        double bestDist = Double.MAX_VALUE;

        void search(Node node, Point target, int depth) {
            if (node == null) return;
            double d = distSq(node.point, target);
            if (d < bestDist) { bestDist = d; best = node.point; }

            boolean splitOnX = depth % 2 == 0;
            double nodeVal = splitOnX ? node.point.x() : node.point.y();
            double targetVal = splitOnX ? target.x() : target.y();
            double diff = targetVal - nodeVal;

            Node nearChild = diff < 0 ? node.left : node.right;
            Node farChild = diff < 0 ? node.right : node.left;

            search(nearChild, target, depth + 1);
            // Only explore the far side if it could possibly hold a closer point.
            if (diff * diff < bestDist) {
                search(farChild, target, depth + 1);
            }
        }
    }

    static void intermediateLevel() {
        Tree tree = new Tree();
        for (double[] xy : new double[][]{{5, 4}, {2, 6}, {8, 1}, {1, 3}, {7, 7}, {9, 2}}) {
            tree.insert(new Point(xy[0], xy[1]));
        }
        NearestSearch search = new NearestSearch();
        Point query = new Point(6, 5);
        search.search(tree.root, query, 0);
        System.out.println("intermediate: nearest to " + query + " -> " + search.best);
    }

    // Advanced: range search, collecting all points inside a rectangle.
    static void rangeSearch(Node node, double xMin, double xMax, double yMin, double yMax, int depth, List<Point> results) {
        if (node == null) return;
        Point p = node.point;
        if (p.x() >= xMin && p.x() <= xMax && p.y() >= yMin && p.y() <= yMax) results.add(p);

        boolean splitOnX = depth % 2 == 0;
        double nodeVal = splitOnX ? p.x() : p.y();
        double lo = splitOnX ? xMin : yMin;
        double hi = splitOnX ? xMax : yMax;

        if (lo <= nodeVal) rangeSearch(node.left, xMin, xMax, yMin, yMax, depth + 1, results);
        if (hi >= nodeVal) rangeSearch(node.right, xMin, xMax, yMin, yMax, depth + 1, results);
    }

    static void advancedLevel() {
        Tree tree = new Tree();
        for (double[] xy : new double[][]{{5, 4}, {2, 6}, {8, 1}, {1, 3}, {7, 7}, {9, 2}}) {
            tree.insert(new Point(xy[0], xy[1]));
        }
        List<Point> results = new ArrayList<>();
        rangeSearch(tree.root, 0, 6, 0, 6, 0, results);
        System.out.println("advanced: points in [0,6]x[0,6] -> " + results);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java KDTree.java`

## 6. Walkthrough

Insert `(5,4), (2,6), (8,1), (1,3), (7,7), (9,2)` in that order. `(5,4)` becomes the root, splitting on `x` (depth 0). `(2,6)` has `x=2 < 5`, goes left. `(8,1)` has `x=8 > 5`, goes right. `(1,3)` compares against `(2,6)` on `y` (depth 1, since it descended once already): `3 < 6`, goes left of `(2,6)`. And so on — the split dimension alternates with depth.

Trace nearest-neighbor search for query `(6,5)`. Start at root `(5,4)`: distance² = `(6-5)² + (5-4)² = 2`. Record it as best. Root splits on `x`; query's `x=6 > 5`, so descend right first (the "near" side) into `(8,1)`'s subtree, then check the "far" side (left) only if `|6-5|² = 1 < bestDist`. Since `1 < 2`, the left side must also be checked — it might hold something closer. This backtrack-and-prune pattern repeats at every level, and the search finishes having visited only a handful of the six nodes, not all of them.

**Complexity.** Build: `O(n log n)` for a balanced tree (choosing the median at each level). Nearest-neighbor and range search: `O(log n)` average for a balanced 2D tree, degrading toward `O(n)` for high dimensions or an unbalanced tree (the "curse of dimensionality"). Space: `O(n)`.

## 7. Gotchas & takeaways

> A k-d tree built by naive sequential insertion (as shown above) can become unbalanced, the same way an unbalanced [BST](0098-binary-tree-binary-search-tree-bst.md) can. For guaranteed balance, build the tree by repeatedly picking the **median** point on the current splitting dimension as the root of each subtree.

- The pruning check (`diff * diff < bestDist`) is the entire reason k-d trees beat a linear scan — skipping it turns the search back into `O(n)`.
- k-d trees lose their advantage in high dimensions (`k` above roughly 20), because almost every subtree ends up within pruning distance, and the search degrades toward checking every point anyway.
- For point data specifically bucketed by 2D map regions (not arbitrary nearest-neighbor queries), a [quadtree](0161-quadtree-geohashing-spatial-indexing.md) is often simpler to reason about.
