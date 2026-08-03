---
card: data-structures
gi: 152
slug: segment-tree-range-query-update
title: Segment tree (range query & update)
---

## 1. What it is

A **segment tree** is a binary tree built over an array. Each leaf holds one array element. Each internal node holds a combined value (sum, min, or max) of the elements in its subtree's range. Think of it as a tournament bracket: each round combines two smaller results into one bigger result, all the way up to a single champion node covering the whole array.

## 2. Why & when

Use a segment tree when you need both **range queries** (sum, min, or max over `[left, right]`) and **point or range updates**, and both must run fast on a large, changing array. A plain array answers a range-sum query in `O(n)` per query. A segment tree answers it in `O(log n)`, and also updates a single element in `O(log n)`. Prefer a simpler [prefix sum array](0157-range-sum-range-min-max-queries.md) when the array never changes.

## 3. Core concept

**The shape.** A segment tree over `n` elements is a complete binary tree stored in an array of size `4n`. Node `i` covers a range `[lo, hi]`. Its left child covers `[lo, mid]`, its right child covers `[mid+1, hi]`, where `mid = (lo + hi) / 2`. A leaf covers a single index.

**The invariant.** Every internal node's value equals the combination (sum, min, or max) of its two children's values. This invariant is rebuilt bottom-up once at construction, then repaired top-down after every update.

**Why it makes operations fast.** A range query `[l, r]` never visits all `n` leaves. It only descends into a node when that node's range partially overlaps `[l, r]`; a node whose range sits fully inside `[l, r]` or fully outside it is resolved in `O(1)`. Because the tree has height `O(log n)`, and each level does `O(1)` work per relevant node, a query touches only `O(log n)` nodes.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A segment tree over array [2,5,1,4,9,3], each node showing the range it covers and the sum for that range">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="270" y="10" width="100" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="25" text-anchor="middle">[0,5]</text><text x="320" y="37" text-anchor="middle">sum=24</text>

    <rect x="130" y="70" width="100" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="180" y="85" text-anchor="middle">[0,2]</text><text x="180" y="97" text-anchor="middle">sum=8</text>
    <rect x="410" y="70" width="100" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="460" y="85" text-anchor="middle">[3,5]</text><text x="460" y="97" text-anchor="middle">sum=16</text>

    <rect x="60" y="140" width="80" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="100" y="155" text-anchor="middle">[0,1]</text><text x="100" y="167" text-anchor="middle">sum=7</text>
    <rect x="220" y="140" width="60" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="250" y="155" text-anchor="middle">[2,2]</text><text x="250" y="167" text-anchor="middle">sum=1</text>
    <rect x="340" y="140" width="80" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="380" y="155" text-anchor="middle">[3,4]</text><text x="380" y="167" text-anchor="middle">sum=13</text>
    <rect x="500" y="140" width="60" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="530" y="155" text-anchor="middle">[5,5]</text><text x="530" y="167" text-anchor="middle">sum=3</text>

    <rect x="30" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="50" y="227" text-anchor="middle">2</text>
    <rect x="90" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="110" y="227" text-anchor="middle">5</text>
    <rect x="230" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="250" y="227" text-anchor="middle">1</text>
    <rect x="330" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="350" y="227" text-anchor="middle">4</text>
    <rect x="390" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="410" y="227" text-anchor="middle">9</text>
    <rect x="510" y="210" width="40" height="26" fill="#0d1117" stroke="#8b949e"/><text x="530" y="227" text-anchor="middle">3</text>

    <line x1="320" y1="40" x2="180" y2="70" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="460" y2="70" stroke="#79c0ff"/>
    <line x1="180" y1="100" x2="100" y2="140" stroke="#79c0ff"/>
    <line x1="180" y1="100" x2="250" y2="140" stroke="#79c0ff"/>
    <line x1="460" y1="100" x2="380" y2="140" stroke="#79c0ff"/>
    <line x1="460" y1="100" x2="530" y2="140" stroke="#79c0ff"/>
  </g>
</svg>

Each parent's sum equals the sum of its two children. Only `O(log n)` nodes lie on the path from any leaf to the root.

## 5. Runnable example

```java
// SegmentTree.java
public class SegmentTree {

    // Basic: build a sum segment tree and query a range.
    static class SumTree {
        int[] tree;
        int n;

        SumTree(int[] arr) {
            n = arr.length;
            tree = new int[4 * n];
            build(arr, 1, 0, n - 1);
        }

        void build(int[] arr, int node, int lo, int hi) {
            if (lo == hi) { tree[node] = arr[lo]; return; }
            int mid = (lo + hi) / 2;
            build(arr, 2 * node, lo, mid);
            build(arr, 2 * node + 1, mid + 1, hi);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        int query(int node, int lo, int hi, int l, int r) {
            if (r < lo || hi < l) return 0;
            if (l <= lo && hi <= r) return tree[node];
            int mid = (lo + hi) / 2;
            return query(2 * node, lo, mid, l, r) + query(2 * node + 1, mid + 1, hi, l, r);
        }

        int queryRange(int l, int r) { return query(1, 0, n - 1, l, r); }
    }

    static void basicLevel() {
        SumTree t = new SumTree(new int[]{2, 5, 1, 4, 9, 3});
        System.out.println("basic: sum[1,4] -> " + t.queryRange(1, 4));
    }

    // Intermediate: point update, repairing the invariant on the path back to the root.
    static class UpdatableSumTree extends SumTree {
        UpdatableSumTree(int[] arr) { super(arr); }

        void update(int node, int lo, int hi, int index, int value) {
            if (lo == hi) { tree[node] = value; return; }
            int mid = (lo + hi) / 2;
            if (index <= mid) update(2 * node, lo, mid, index, value);
            else update(2 * node + 1, mid + 1, hi, index, value);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        void updateIndex(int index, int value) { update(1, 0, n - 1, index, value); }
    }

    static void intermediateLevel() {
        UpdatableSumTree t = new UpdatableSumTree(new int[]{2, 5, 1, 4, 9, 3});
        t.updateIndex(2, 10);
        System.out.println("intermediate: sum[1,4] after update -> " + t.queryRange(1, 4));
    }

    // Advanced: a generic min-segment-tree using a combine function, showing the tree is not sum-only.
    interface Combine { int apply(int a, int b); }

    static class GenericTree {
        int[] tree;
        int n;
        Combine combine;
        int identity;

        GenericTree(int[] arr, Combine combine, int identity) {
            this.n = arr.length;
            this.combine = combine;
            this.identity = identity;
            tree = new int[4 * n];
            build(arr, 1, 0, n - 1);
        }

        void build(int[] arr, int node, int lo, int hi) {
            if (lo == hi) { tree[node] = arr[lo]; return; }
            int mid = (lo + hi) / 2;
            build(arr, 2 * node, lo, mid);
            build(arr, 2 * node + 1, mid + 1, hi);
            tree[node] = combine.apply(tree[2 * node], tree[2 * node + 1]);
        }

        int query(int node, int lo, int hi, int l, int r) {
            if (r < lo || hi < l) return identity;
            if (l <= lo && hi <= r) return tree[node];
            int mid = (lo + hi) / 2;
            return combine.apply(query(2 * node, lo, mid, l, r), query(2 * node + 1, mid + 1, hi, l, r));
        }

        int queryRange(int l, int r) { return query(1, 0, n - 1, l, r); }
    }

    static void advancedLevel() {
        GenericTree minTree = new GenericTree(new int[]{2, 5, 1, 4, 9, 3}, Math::min, Integer.MAX_VALUE);
        System.out.println("advanced: min[1,4] -> " + minTree.queryRange(1, 4));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java SegmentTree.java`

## 6. Walkthrough

Build the tree over `[2, 5, 1, 4, 9, 3]`. The build recurses down to leaves `[2], [5], [1], [4], [9], [3]`, then combines upward: `[0,1] = 2+5 = 7`, `[3,4] = 4+9 = 13`, `[0,2] = 7+1 = 8`, `[3,5] = 13+3 = 16`, `[0,5] = 8+16 = 24`.

Now query `sum[1, 4]`. Start at the root `[0,5]`. Its range is not fully inside `[1,4]`, so descend. `[0,2]` overlaps partially, so descend further: `[0,1]` overlaps partially (only index 1 matters), `[2,2]` is fully inside `[1,4]`, return `1` directly. `[3,5]` overlaps partially: `[3,4]` is fully inside `[1,4]`, return `13` directly; `[5,5]` lies outside, return `0`. Sum the fully-inside contributions: `5 (from index 1) + 1 + 13 = 19`.

Now update index `2` from `1` to `10`. Walk from the root to the leaf `[2,2]`, set it to `10`, then recompute every ancestor on the way back up: `[0,2] = 7 + 10 = 17`, `[0,5] = 17 + 16 = 33`. The next `sum[1,4]` query now returns `5 + 10 + 13 = 28`.

**Complexity.** Build: `O(n)`. Range query: `O(log n)`. Point update: `O(log n)`. Space: `O(n)` (the `4n`-sized array is a safe upper bound for any `n`).

## 7. Gotchas & takeaways

> Sizing the backing array as `4 * n` looks wasteful, but it is the proven safe bound for a recursive segment tree that is not guaranteed to be a perfect power of two; using `2 * n` can throw `ArrayIndexOutOfBoundsException` on some sizes.

- A segment tree needs an **associative** combine function (sum, min, max, gcd). It does not work for non-associative operations like average.
- For range **updates** (not just point updates), use [lazy propagation](0156-lazy-propagation-in-segment-trees.md) instead of updating every leaf in the range one by one.
- If the array never changes, a [sparse table](0155-sparse-table-static-range-queries.md) answers min/max range queries in `O(1)` with less code.
