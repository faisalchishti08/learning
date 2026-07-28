---
card: leetcode-patterns
gi: 561
slug: segment-tree-bit-template-segment-tree-or-fenwick-tree-over
title: Segment Tree / BIT — template: segment tree or Fenwick tree over the array
---

## 1. What it is

Two reusable templates: a **segment tree** (an explicit binary tree, usually array-backed, supporting any combinable operation) and a **Fenwick tree** (a compact array using bit tricks, limited to invertible operations like sum). Once memorized, adapting either to a new problem is mostly about swapping the combine function (sum, min, max) and the indexing convention (0-indexed vs 1-indexed).

## 2. Why & when

Use a Fenwick tree when the operation is sum (or any operation with an inverse, like XOR) — it needs less code and a smaller constant factor. Use a segment tree when the operation is min, max, gcd, or something else without an inverse, or when the problem needs range updates with lazy propagation (deferring an update to a whole range instead of touching each element).

## 3. Core concept

**Segment tree (array-backed, 0-indexed, sum example).**
- Store the tree in an array of size `4n` (a safe upper bound for any array of size `n`). Node `i` covers some range; its children are at `2i+1` and `2i+2`.
- **Build:** recursively split `[left, right)` in half, build each half, then combine (`tree[i] = tree[left child] + tree[right child]`).
- **Update(index, value):** recurse toward the leaf covering `index`, set it, then recombine every ancestor on the way back up.
- **Query(left, right):** recurse; if the current node's range is fully inside `[left, right)`, return its stored value directly; if fully outside, return the identity (0 for sum); otherwise recurse into both children and combine.

**Fenwick tree (1-indexed, sum example).**
- Store a flat array `tree[1..n]`. Index `i` implicitly owns a range determined by `i`'s lowest set bit (`i & (-i)`).
- **Update(index, delta):** starting at `index`, repeatedly add `delta` to `tree[index]`, then move to `index += index & (-index)`, until past `n`.
- **PrefixSum(index):** starting at `index`, repeatedly add `tree[index]`, then move to `index -= index & (-index)`, until reaching `0`.
- **RangeSum(left, right):** `PrefixSum(right) - PrefixSum(left - 1)`.

**Why the segment tree's array size is `4n`, not `2n`:** a segment tree built on a non-power-of-two `n` is not a perfectly balanced binary tree, so its array representation can need up to roughly `4n` slots in the worst case to avoid index collisions — using `4n` is a simple, safe bound that avoids computing the exact minimum.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Segment tree update walking from a leaf up to the root versus Fenwick tree update jumping by lowest-set-bit increments">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="300" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="170" y="45" fill="#e6edf3" text-anchor="middle">Segment tree update: leaf -&gt; parent -&gt; ... -&gt; root</text>
    <text x="170" y="62" fill="#8b949e" text-anchor="middle" font-size="11">O(log n) ancestors recombined</text>
    <rect x="380" y="20" width="300" height="50" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="530" y="45" fill="#e6edf3" text-anchor="middle">Fenwick update: i += i &amp; (-i), repeat</text>
    <text x="530" y="62" fill="#8b949e" text-anchor="middle" font-size="11">O(log n) jumps using bit tricks</text>
    <text x="350" y="120" fill="#79c0ff" text-anchor="middle">both touch O(log n) positions per update; Fenwick uses no explicit tree structure</text>
  </g>
</svg>

Both templates limit each update to O(log n) positions — the segment tree via explicit parent pointers, the Fenwick tree via a bit-manipulation jump.

## 5. Runnable example

Both templates implemented for range-sum with point-update, on the same data.

```java
// SegmentTreeFenwickTemplate.java
public class SegmentTreeFenwickTemplate {

    static class SegmentTree {
        int[] tree;
        int n;
        SegmentTree(int[] arr) {
            n = arr.length;
            tree = new int[4 * n];
            build(arr, 0, 0, n - 1);
        }
        void build(int[] arr, int node, int start, int end) {
            if (start == end) {
                tree[node] = arr[start];
                return;
            }
            int mid = (start + end) / 2;
            build(arr, 2 * node + 1, start, mid);
            build(arr, 2 * node + 2, mid + 1, end);
            tree[node] = tree[2 * node + 1] + tree[2 * node + 2];
        }
        void update(int node, int start, int end, int index, int value) {
            if (start == end) {
                tree[node] = value;
                return;
            }
            int mid = (start + end) / 2;
            if (index <= mid) update(2 * node + 1, start, mid, index, value);
            else update(2 * node + 2, mid + 1, end, index, value);
            tree[node] = tree[2 * node + 1] + tree[2 * node + 2];
        }
        int query(int node, int start, int end, int left, int right) {
            if (right < start || end < left) return 0;
            if (left <= start && end <= right) return tree[node];
            int mid = (start + end) / 2;
            return query(2 * node + 1, start, mid, left, right)
                 + query(2 * node + 2, mid + 1, end, left, right);
        }
    }

    static class Fenwick {
        int[] tree;
        int n;
        Fenwick(int n) {
            this.n = n;
            tree = new int[n + 1];
        }
        void update(int i, int delta) {
            for (; i <= n; i += i & (-i)) tree[i] += delta;
        }
        int prefixSum(int i) {
            int sum = 0;
            for (; i > 0; i -= i & (-i)) sum += tree[i];
            return sum;
        }
    }

    public static void main(String[] args) {
        int[] arr = {1, 3, 5, 7, 9, 11};

        SegmentTree segTree = new SegmentTree(arr);
        System.out.println("segTree sum[1..3]: " + segTree.query(0, 0, arr.length - 1, 1, 3));
        segTree.update(0, 0, arr.length - 1, 1, 30); // arr[1]: 3 -> 30
        System.out.println("segTree sum[1..3] after update: " + segTree.query(0, 0, arr.length - 1, 1, 3));

        Fenwick fenwick = new Fenwick(arr.length);
        for (int i = 0; i < arr.length; i++) fenwick.update(i + 1, arr[i]);
        System.out.println("fenwick prefixSum(4) (1-indexed, arr[0..3]): " + fenwick.prefixSum(4));
    }
}
```

**How to run:** save as `SegmentTreeFenwickTemplate.java`, then run `java SegmentTreeFenwickTemplate.java`.

## 6. Walkthrough

Trace `segTree.query(0, 0, 5, 1, 3)` on `[1,3,5,7,9,11]`:

1. Root covers `[0,5]`, requested range `[1,3]` is partially inside — recurse into both children.
2. Left child covers `[0,2]`, partially overlaps `[1,3]` — recurse: leaf `1` (index 1, value `3`, in range) contributes `3`; leaf for index `2` (value `5`, in range) contributes `5`. Combined: `8`.
3. Right child covers `[3,5]`, partially overlaps `[1,3]` — only index `3` (value `7`) is in range; the rest of that subtree contributes `0`.
4. Total: `8 + 7 = 15`, matching `3 + 5 + 7`.

## 7. Gotchas & takeaways

> Gotcha: in the Fenwick tree, forgetting that it is naturally **1-indexed** (index `0` breaks the `i & (-i)` bit trick, since it never terminates the loop correctly) is a common off-by-one bug — always map problem indices to `i + 1` before calling `update` or `prefixSum`.

- Segment tree: more code, but supports any combinable operation (min, max, gcd) and range updates via lazy propagation.
- Fenwick tree: less code, faster in practice, but limited to invertible operations like sum, and is 1-indexed by convention.
- Both achieve O(log n) per update and per query, dramatically better than O(n) naive recomputation for interleaved update/query workloads.
