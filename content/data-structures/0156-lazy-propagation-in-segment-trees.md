---
card: data-structures
gi: 156
slug: lazy-propagation-in-segment-trees
title: Lazy propagation in segment trees
---

## 1. What it is

**Lazy propagation** is a technique that lets a [segment tree](0152-segment-tree-range-query-update.md) apply an update to an entire range in `O(log n)`, instead of updating every element in that range one by one. Each node gets a "lazy" tag that says "apply this pending change to my children later, only if someone actually asks to go there."

## 2. Why & when

A plain segment tree already updates a single index in `O(log n)`. But updating a whole range — "add 5 to every element from index 3 to 9" — by looping over each index costs `O(range length)`, which can be `O(n)` in the worst case. Lazy propagation fixes this: it marks the top-level nodes covering the range as "dirty" and defers pushing the change down until a later query or update actually needs to visit their children.

## 3. Core concept

**The shape.** The same segment tree array, plus a parallel `lazy[]` array. `lazy[node]` holds a pending update not yet applied to `node`'s children (it has already been applied to `node`'s own combined value).

**The invariant.** A node's own stored value is always up to date. Its children's values may be stale by exactly what `lazy[node]` says — that debt is paid the moment anyone visits the children.

**The two extra steps.**
- **Apply-and-defer:** when a range update fully covers a node's range, update that node's value immediately (multiply the delta by the range size, for a sum tree), and add the delta to `lazy[node]` instead of recursing into its children.
- **Push-down:** before reading or recursing into a node's children for any reason, first move `lazy[node]` onto `lazy[left child]` and `lazy[right child]` (updating their stored values too), then clear `lazy[node]` to zero.

**Why it keeps updates at `O(log n)`.** A range update only fully applies-and-defers at `O(log n)` "boundary" nodes — the same nodes a plain range query would stop at — and only pushes down along the `O(log n)` path it actually recurses through. It never eagerly visits every leaf in the range.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A segment tree node marked lazy after a range update, with the tag pushed down only when a later operation visits its children">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="240" y="10" width="140" height="40" fill="#161b22" stroke="#f0883e"/>
    <text x="310" y="26" text-anchor="middle">[0,3] sum=20</text>
    <text x="310" y="42" text-anchor="middle" fill="#f0883e">lazy=+2 (pending)</text>

    <rect x="120" y="90" width="120" height="40" fill="#21262d" stroke="#8b949e" stroke-dasharray="3,3"/>
    <text x="180" y="106" text-anchor="middle">[0,1] sum=8</text>
    <text x="180" y="122" text-anchor="middle" fill="#8b949e">stale (not yet +2)</text>

    <rect x="400" y="90" width="120" height="40" fill="#21262d" stroke="#8b949e" stroke-dasharray="3,3"/>
    <text x="460" y="106" text-anchor="middle">[2,3] sum=12</text>
    <text x="460" y="122" text-anchor="middle" fill="#8b949e">stale (not yet +2)</text>

    <line x1="310" y1="50" x2="180" y2="90" stroke="#8b949e" stroke-dasharray="3,3"/>
    <line x1="310" y1="50" x2="460" y2="90" stroke="#8b949e" stroke-dasharray="3,3"/>

    <text x="310" y="170" font-size="9" fill="#8b949e">next query touches [0,1] -&gt; push lazy(+2) down first:</text>
    <text x="310" y="190" font-size="9" fill="#e6edf3">[0,1] becomes sum=8+2*2=12, its own lazy becomes +2; parent's lazy clears to 0</text>
  </g>
</svg>

The parent's value is already correct; the children only catch up the moment they are visited.

## 5. Runnable example

```java
// LazySegmentTree.java
public class LazySegmentTree {

    // Basic: a sum segment tree with lazy propagation for range-add, range-sum.
    static class LazySumTree {
        long[] tree;
        long[] lazy;
        int n;

        LazySumTree(int[] arr) {
            n = arr.length;
            tree = new long[4 * n];
            lazy = new long[4 * n];
            build(arr, 1, 0, n - 1);
        }

        void build(int[] arr, int node, int lo, int hi) {
            if (lo == hi) { tree[node] = arr[lo]; return; }
            int mid = (lo + hi) / 2;
            build(arr, 2 * node, lo, mid);
            build(arr, 2 * node + 1, mid + 1, hi);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        void pushDown(int node, int lo, int hi) {
            if (lazy[node] == 0) return;
            int mid = (lo + hi) / 2;
            applyLazy(2 * node, lo, mid, lazy[node]);
            applyLazy(2 * node + 1, mid + 1, hi, lazy[node]);
            lazy[node] = 0;
        }

        void applyLazy(int node, int lo, int hi, long delta) {
            tree[node] += delta * (hi - lo + 1);
            lazy[node] += delta;
        }

        void rangeAdd(int node, int lo, int hi, int l, int r, long delta) {
            if (r < lo || hi < l) return;
            if (l <= lo && hi <= r) { applyLazy(node, lo, hi, delta); return; }
            pushDown(node, lo, hi);
            int mid = (lo + hi) / 2;
            rangeAdd(2 * node, lo, mid, l, r, delta);
            rangeAdd(2 * node + 1, mid + 1, hi, l, r, delta);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        long rangeSum(int node, int lo, int hi, int l, int r) {
            if (r < lo || hi < l) return 0;
            if (l <= lo && hi <= r) return tree[node];
            pushDown(node, lo, hi);
            int mid = (lo + hi) / 2;
            return rangeSum(2 * node, lo, mid, l, r) + rangeSum(2 * node + 1, mid + 1, hi, l, r);
        }

        void add(int l, int r, long delta) { rangeAdd(1, 0, n - 1, l, r, delta); }
        long sum(int l, int r) { return rangeSum(1, 0, n - 1, l, r); }
    }

    static void basicLevel() {
        LazySumTree t = new LazySumTree(new int[]{2, 5, 1, 4, 9, 3});
        t.add(0, 3, 2); // add 2 to indices 0..3
        System.out.println("basic: sum[0,3] after +2 -> " + t.sum(0, 3));
    }

    // Intermediate: repeated overlapping range updates, showing the pending tags stack correctly.
    static void intermediateLevel() {
        LazySumTree t = new LazySumTree(new int[]{2, 5, 1, 4, 9, 3});
        t.add(0, 5, 1);   // +1 to everything
        t.add(2, 4, 10);  // +10 to indices 2..4
        System.out.println("intermediate: sum[0,5] -> " + t.sum(0, 5));
        System.out.println("intermediate: sum[2,4] -> " + t.sum(2, 4));
    }

    // Advanced: interleave range updates and range queries to confirm push-down keeps every read correct.
    static void advancedLevel() {
        LazySumTree t = new LazySumTree(new int[]{0, 0, 0, 0, 0, 0, 0, 0});
        t.add(0, 7, 1);
        System.out.println("advanced: sum[0,7] -> " + t.sum(0, 7));
        t.add(3, 5, 5);
        System.out.println("advanced: sum[3,5] -> " + t.sum(3, 5));
        System.out.println("advanced: sum[0,2] (untouched by second update) -> " + t.sum(0, 2));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java LazySegmentTree.java`

## 6. Walkthrough

Start with `[2, 5, 1, 4, 9, 3]` and call `add(0, 3, 2)`. The recursion reaches node `[0,3]`, which is fully covered by the update range. It applies the delta immediately: `tree[node] += 2 * 4 = 8`, and sets `lazy[node] = 2`. It does **not** recurse into `[0,1]` or `[2,3]` — their stored values are now stale by `+2`, but nobody has asked to read them yet.

Now call `sum(0, 3)`. The recursion reaches node `[0,3]` again. Since the query range exactly matches, it returns `tree[node]` directly — already correct, no push-down needed. Result: `2+5+1+4 = 12`, plus the `+2*4 = 8` already folded in, giving `20`.

Now call `sum(0, 1)` instead (a narrower range). The recursion reaches `[0,3]`, which only partially covers `[0,1]`, so it must descend. Before descending, it calls `pushDown`: `lazy[node] = 2` is moved onto both children — `[0,1]`'s value becomes `7 + 2*2 = 11` and its own `lazy` becomes `2`; `[2,3]`'s value becomes `5 + 2*2 = 9` and its `lazy` becomes `2`. The parent's `lazy` clears to `0`. Now the recursion can safely read `[0,1]` and get the correct, up-to-date answer of `11`.

**Complexity.** Range update: `O(log n)`. Range query: `O(log n)`. Space: `O(n)` for the extra `lazy` array.

## 7. Gotchas & takeaways

> Forgetting to call `pushDown` before recursing into children is the most common bug. It silently returns stale values, because the parent looks correct in isolation — the bug only shows up when a query narrower than a prior update reads a child directly.

- Always push down **before** you read or recurse into a node's children, in both the update function and the query function — not just one of them.
- The `delta * (hi - lo + 1)` step (scaling by range size) only works for range-**add**. Range-**assign** ("set every element in this range to `v`") needs a different apply rule and often a sentinel to distinguish "no pending update" from "pending update of value 0".
- If your data never needs range updates, only point updates, plain [segment tree](0152-segment-tree-range-query-update.md) recursion is simpler and needs no lazy array at all.
