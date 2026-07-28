---
card: leetcode-patterns
gi: 560
slug: segment-tree-bit-signal-range-queries-with-point-range-updat
title: Segment Tree / BIT — signal: range queries with point/range updates
---

## 1. What it is

A segment tree and a Fenwick tree (also called a Binary Indexed Tree, or BIT) are both data structures that answer **range queries** — "what is the sum/min/max over indices `[i, j]`" — while also supporting **updates** to individual elements, both in `O(log n)` time. Plain arrays or [prefix sums](0488-prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma.md) cannot do both efficiently at once.

## 2. Why & when

Reach for a segment tree or Fenwick tree whenever a problem repeatedly asks for range aggregates (sum, min, max, count) **and** repeatedly modifies individual elements, interleaved in any order. A plain prefix-sum array answers a range-sum query in O(1), but any single update forces an O(n) rebuild of the whole prefix array — too slow if updates and queries alternate many times.

Learn to recognize these signals in a problem statement:

- **"Update an element, then query a range sum/min/max"** repeated many times — the direct definition: mutable range queries.
- **"Count elements smaller/larger than X to the right/left of each position"** — solvable by processing elements in order and using a Fenwick tree over *value ranks* (not array indices) to count how many smaller/larger values have been seen so far.
- **"Book/reserve intervals, detect overlaps, or count overlap depth"** — a segment tree over the value range (like a calendar's timeline) supports "does this interval overlap anything" and "what is the maximum overlap count" efficiently.
- **"Range sum query, but the array changes"** ("Mutable" in the problem title is the tell) — the direct segment-tree-vs-plain-prefix-sum decision point.
- **"Stack squares/intervals and query the maximum height at any point"** — a segment tree (or a coordinate-compressed array) tracking a running maximum over ranges.

The alternative is recomputing from scratch after every update (O(n) per update) or, for read-only static data, plain prefix sums (O(1) query, but no updates at all). Segment trees and Fenwick trees are the middle ground: O(log n) for both operations.

## 3. Core concept

**Key idea:** both structures store *partial aggregates* over ranges, arranged so any full range `[0, n)` can be reconstructed from O(log n) of these partial pieces, and any single-element update only needs to fix O(log n) of those pieces (the ones that happen to cover the updated index).

**Segment tree:** a binary tree where each node covers a contiguous range; a leaf covers one element, and each internal node's value is the combination (sum, min, max) of its two children's ranges. A query decomposes the requested range into a handful of these node-ranges; an update walks from a leaf up to the root, fixing every ancestor.

**Fenwick tree (BIT):** a flat array where each index implicitly "owns" a specific range, determined by the lowest set bit of that index (a compact binary-trick alternative to an explicit tree). It supports prefix sums and point updates with very little code, but only for operations with an inverse (like sum, via subtraction) — not min/max, which segment trees handle but Fenwick trees generally cannot.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A segment tree over 4 elements, where each internal node stores the sum of its range">
  <g font-family="sans-serif" font-size="12">
    <rect x="290" y="10" width="120" height="35" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="32" fill="#e6edf3" text-anchor="middle">[0,4): sum=10</text>
    <rect x="150" y="70" width="120" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="210" y="92" fill="#e6edf3" text-anchor="middle">[0,2): sum=3</text>
    <rect x="430" y="70" width="120" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="490" y="92" fill="#e6edf3" text-anchor="middle">[2,4): sum=7</text>
    <line x1="350" y1="45" x2="210" y2="70" stroke="#8b949e"/>
    <line x1="350" y1="45" x2="490" y2="70" stroke="#8b949e"/>
    <rect x="80" y="130" width="90" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="125" y="152" fill="#e6edf3" text-anchor="middle" font-size="11">[0,1): 1</text>
    <rect x="250" y="130" width="90" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="295" y="152" fill="#e6edf3" text-anchor="middle" font-size="11">[1,2): 2</text>
    <rect x="360" y="130" width="90" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="405" y="152" fill="#e6edf3" text-anchor="middle" font-size="11">[2,3): 3</text>
    <rect x="530" y="130" width="90" height="35" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="575" y="152" fill="#e6edf3" text-anchor="middle" font-size="11">[3,4): 4</text>
    <line x1="210" y1="105" x2="125" y2="130" stroke="#8b949e"/>
    <line x1="210" y1="105" x2="295" y2="130" stroke="#8b949e"/>
    <line x1="490" y1="105" x2="405" y2="130" stroke="#8b949e"/>
    <line x1="490" y1="105" x2="575" y2="130" stroke="#8b949e"/>
  </g>
</svg>

Each internal node's sum equals the sum of its two children — updating one leaf only requires fixing the O(log n) ancestors on the path back to the root.

## 5. Runnable example

The artifact below is a reusable signal-checker: it compares a naive O(n) recompute-per-update range-sum approach against a Fenwick tree.

### Signal-checker

```java
// SegmentTreeSignal.java
public class SegmentTreeSignal {

    static int naiveRangeSum(int[] arr, int left, int right) {
        int sum = 0;
        for (int i = left; i <= right; i++) sum += arr[i];
        return sum;
    }

    static class Fenwick {
        int[] tree;
        int n;
        Fenwick(int n) {
            this.n = n;
            tree = new int[n + 1];
        }
        void update(int i, int delta) { // 1-indexed
            for (; i <= n; i += i & (-i)) tree[i] += delta;
        }
        int prefixSum(int i) {
            int sum = 0;
            for (; i > 0; i -= i & (-i)) sum += tree[i];
            return sum;
        }
        int rangeSum(int left, int right) { // 1-indexed inclusive
            return prefixSum(right) - prefixSum(left - 1);
        }
    }

    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 4, 5};
        System.out.println("naive sum[1..3]: " + naiveRangeSum(arr, 1, 3));

        Fenwick fenwick = new Fenwick(arr.length);
        for (int i = 0; i < arr.length; i++) fenwick.update(i + 1, arr[i]);
        System.out.println("fenwick sum[2..4] (1-indexed): " + fenwick.rangeSum(2, 4));

        arr[1] = 20; // update index 1 (value 2 -> 20)
        fenwick.update(2, 20 - 2); // apply the same delta to the Fenwick tree
        System.out.println("naive sum[1..3] after update: " + naiveRangeSum(arr, 1, 3));
        System.out.println("fenwick sum[2..4] after update: " + fenwick.rangeSum(2, 4));
    }
}
```

**How to run:** save as `SegmentTreeSignal.java`, then run `java SegmentTreeSignal.java`.

## 6. Walkthrough

1. You read a problem that repeats "update a value, then query a range" many times. That is the direct segment tree / Fenwick tree signal.
2. The naive approach recomputes the requested range sum directly from the array every time — correct, but each query costs O(range length), and it re-reads the raw array after every update with no reuse of prior work.
3. The Fenwick tree instead maintains partial sums; `rangeSum(2,4)` combines two `prefixSum` calls, each walking O(log n) tree nodes rather than scanning the range.
4. Updating index `1` (0-indexed) by a delta of `18` (from `2` to `20`) costs the Fenwick tree O(log n) — it only touches the handful of tree nodes whose implicit range includes index `1`, not the whole array.
5. Both approaches agree on the answer, but the Fenwick tree's update cost stays O(log n) regardless of array size, while the naive approach's per-update cost (if it tried to maintain a prefix-sum array) would be O(n).

## 7. Gotchas & takeaways

> Gotcha: reaching for a segment tree or Fenwick tree when the array is **never updated** is unnecessary complexity — a plain prefix-sum array (O(1) query, no update support needed) is simpler and just as fast for read-only range queries.

- Signal words: "mutable," "update then query," "range sum/min/max with point updates," "count smaller/larger elements as you process a sequence," "overlap/booking count."
- Fenwick trees are shorter to code but limited to invertible operations (sum, XOR); segment trees handle any combinable operation (min, max, gcd) at the cost of more code.
- Alternative: plain prefix sums for static (read-only) data; brute-force recomputation only for small n or few queries.
