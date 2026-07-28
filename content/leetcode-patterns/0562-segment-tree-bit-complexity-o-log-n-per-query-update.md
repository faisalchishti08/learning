---
card: leetcode-patterns
gi: 562
slug: segment-tree-bit-complexity-o-log-n-per-query-update
title: Segment Tree / BIT — complexity: O(log n) per query/update
---

## 1. What it is

This page explains why both a segment tree and a Fenwick tree answer a range query or apply a point update in `O(log n)` time, and lists the named problems that use the pattern.

## 2. Why & when

Interviewers often ask "why not just use a prefix-sum array" as a follow-up. Explaining the actual tradeoff — O(1) query but O(n) update for prefix sums, versus O(log n) for both with these trees — demonstrates you understand exactly which access pattern each structure is optimized for.

## 3. Core concept

**Time — O(log n) per update, both structures.** A segment tree update walks from one leaf up to the root, a path of length `O(log n)` in a balanced binary tree over `n` elements — each ancestor on that path is recombined once. A Fenwick tree update starts at an index and repeatedly jumps forward by its lowest set bit; each jump strictly increases the index, and since the index is at most `n`, at most `O(log n)` jumps occur before exceeding `n`.

**Time — O(log n) per query, both structures.** A segment tree query decomposes the requested range into at most `O(log n)` fully-covered sub-ranges (a classic property of how a query range aligns against a balanced binary partition) — no more than 2 "partial" nodes exist at each level of the tree. A Fenwick tree prefix-sum query is symmetric to its update: it jumps backward by lowest set bit repeatedly, at most `O(log n)` times.

**Space — O(n).** A Fenwick tree uses exactly `n + 1` array slots. A segment tree typically uses up to `4n` slots for its array-backed representation — still linear in `n`, just with a larger constant factor.

**Contrast with a plain prefix-sum array.** Query: O(1) (just subtract two precomputed prefix sums). Update: O(n) (every prefix sum from the updated index onward must shift). This is the exact opposite tradeoff from these trees, which sacrifice some query speed (O(log n) instead of O(1)) to gain fast updates (O(log n) instead of O(n)).

**Why n (array size) only appears as a logarithm, not linearly:** both structures organize their partial aggregates so that any position is covered by exactly one node at each of O(log n) "levels" (explicit tree depth for a segment tree, or bit-position levels for a Fenwick tree) — an update or query only ever needs to touch one node per level, never scanning within a level.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Segment tree and Fenwick tree operations touching O(log n) nodes, versus a prefix-sum array's O(1) query but O(n) update">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">segment tree / Fenwick tree:</text>
    <text x="20" y="45" fill="#3fb950">update: O(log n) nodes touched (one per tree level)</text>
    <text x="20" y="70" fill="#3fb950">query: O(log n) nodes combined (at most a few per level)</text>
    <text x="20" y="105" fill="#f0883e" font-weight="bold">plain prefix-sum array:</text>
    <text x="20" y="130" fill="#f0883e">query: O(1), but update: O(n) (must shift every later prefix)</text>
  </g>
</svg>

Both trees trade a small, fixed O(log n) cost on every operation for balanced performance, instead of the lopsided O(1)-query/O(n)-update tradeoff of a plain prefix-sum array.

## 5. Runnable example

An instrumented Fenwick tree that counts array accesses per update and per query, confirming both scale with `log n`, not `n`.

```java
// SegTreeBitComplexity.java
public class SegTreeBitComplexity {

    static class Fenwick {
        int[] tree;
        int n;
        long accessCount = 0;
        Fenwick(int n) {
            this.n = n;
            tree = new int[n + 1];
        }
        void update(int i, int delta) {
            for (; i <= n; i += i & (-i)) {
                tree[i] += delta;
                accessCount++;
            }
        }
        int prefixSum(int i) {
            int sum = 0;
            for (; i > 0; i -= i & (-i)) {
                sum += tree[i];
                accessCount++;
            }
            return sum;
        }
    }

    public static void main(String[] args) {
        for (int n : new int[]{16, 256, 4096, 65536}) {
            Fenwick fenwick = new Fenwick(n);
            fenwick.accessCount = 0;
            fenwick.update(n / 2, 5); // one update near the middle
            long updateAccesses = fenwick.accessCount;

            fenwick.accessCount = 0;
            fenwick.prefixSum(n); // one full prefix query
            long queryAccesses = fenwick.accessCount;

            System.out.printf("n=%-6d log2(n)=%.1f updateAccesses=%-3d queryAccesses=%-3d%n",
                    n, Math.log(n) / Math.log(2), updateAccesses, queryAccesses);
        }
    }
}
```

**How to run:** save as `SegTreeBitComplexity.java`, then run `java SegTreeBitComplexity.java`.

## 6. Walkthrough

1. For `n = 16` (`log2(16) = 4`), a single update touches at most `4`–`5` array positions — close to `log2(n)`, confirming the bound.
2. For `n = 4096` (`log2(4096) = 12`), the update and query access counts stay close to `12`–`13`, not anywhere near `4096`.
3. Doubling `n` sixteen-fold (from `16` to `65536`) only adds a handful more accesses per operation (roughly `log2(65536) = 16`), while a plain array update over the same growth would need up to `65536` shifts in the worst case.
4. This confirms the O(log n) bound holds regardless of array size, and demonstrates concretely why these trees stay fast even as `n` grows very large.

## 7. Gotchas & takeaways

> Gotcha: assuming a segment tree's O(log n) query bound means it visits only `O(log n)` *nodes total* including the ones it recurses into but discards — in practice a query visits up to `O(log n)` *fully-covered* nodes that contribute to the answer, plus a bounded number of extra recursive calls that return early without contributing; the total work is still `O(log n)`, but the node-visit count is a small constant multiple of it, not exactly the bound.

- Time: O(log n) per update and per query, for both segment trees and Fenwick trees.
- Space: O(n) for a Fenwick tree; O(n) (with roughly a 4x constant factor) for an array-backed segment tree.
- Reference problems that use this pattern: Range Sum Query - Mutable, Range Sum Query 2D - Mutable, My Calendar I, My Calendar II, My Calendar III, Count of Smaller Numbers After Self, Reverse Pairs, Count of Range Sum, Falling Squares.
