---
card: data-structures
gi: 177
slug: fenwick-vs-segment-tree-tradeoffs
title: Fenwick vs segment tree tradeoffs
---

## 1. What it is

A [Fenwick tree (BIT)](0153-fenwick-tree-binary-indexed-tree-bit.md) and a [segment tree](0152-segment-tree-range-query-update.md) both answer range queries with updates in `O(log n)`. This page compares them directly, so the choice between them is a quick decision, not a coin flip.

## 2. Why & when

Both structures solve overlapping problems, which makes it tempting to always reach for the more powerful one (the segment tree). But the Fenwick tree's simplicity is a real advantage when it applies — less code to write correctly under interview or production time pressure, and a smaller constant factor per operation. Knowing exactly where each one's capability ends is what makes the choice fast instead of guesswork.

## 3. Core concept

**The decision criteria.**
- **What operation do you need?** Sum (or any operation with an inverse, like XOR) can use either structure. Min, max, or GCD (operations **without** an inverse) can only use a segment tree.
- **Do you need range updates, not just point updates?** A Fenwick tree's simplest form only does point updates cleanly. A segment tree with [lazy propagation](0156-lazy-propagation-in-segment-trees.md) handles range updates naturally. A Fenwick tree *can* be extended to support range updates with range queries using a well-known two-BIT trick, but it is more fragile to implement correctly than a segment tree's lazy propagation.
- **How much code do you want to write and maintain?** A Fenwick tree is roughly 15-20 lines: one array, two small loops. A segment tree (with lazy propagation) is 60-100+ lines: recursive build, query, update, and push-down logic.

**The comparison table.**

| Aspect | Fenwick tree (BIT) | Segment tree |
|---|---|---|
| Supported operations | sum, XOR (needs an inverse) | any associative op: sum, min, max, gcd |
| Point update | `O(log n)`, simple | `O(log n)`, simple |
| Range update | needs a two-BIT trick, fragile | `O(log n)` with lazy propagation, natural |
| Code size | small (~20 lines) | larger (~80+ lines with lazy propagation) |
| Constant factor | smaller (no recursion, tight loop) | larger (recursive calls, more branching) |
| Memory | `n + 1` ints | `4n` ints |

**Why the Fenwick tree's constraint (needing an inverse) is fundamental, not a missing feature.** Its `prefixSum(r) - prefixSum(l-1)` trick for range queries only works because subtraction "undoes" addition. There is no equivalent "undo" for `min` or `max` — you cannot recover the minimum of `[l, r]` from the minimum of `[0, r]` and the minimum of `[0, l-1]`, because information about which elements were excluded is lost. A segment tree never relies on an inverse; it always recombines from smaller ranges directly, so it works for any associative operation.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decision flow for choosing between a Fenwick tree and a segment tree based on the operation needed and whether range updates are required">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="250" y="10" width="140" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="31" text-anchor="middle">need min/max/gcd?</text>

    <rect x="60" y="80" width="160" height="34" fill="#0d1117" stroke="#8b949e"/>
    <text x="140" y="101" text-anchor="middle">no (sum/XOR only)</text>
    <rect x="420" y="80" width="160" height="34" fill="#0d1117" stroke="#8b949e"/>
    <text x="500" y="101" text-anchor="middle">yes -&gt; segment tree</text>

    <line x1="320" y1="44" x2="140" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="44" x2="500" y2="80" stroke="#79c0ff"/>

    <rect x="20" y="150" width="140" height="34" fill="#161b22" stroke="#3fb950"/>
    <text x="90" y="171" text-anchor="middle" font-size="9">point updates: Fenwick tree</text>
    <rect x="180" y="150" width="180" height="34" fill="#161b22" stroke="#f0883e"/>
    <text x="270" y="171" text-anchor="middle" font-size="9">range updates: segment tree + lazy</text>

    <line x1="140" y1="114" x2="90" y2="150" stroke="#8b949e"/>
    <line x1="140" y1="114" x2="270" y2="150" stroke="#8b949e"/>
  </g>
</svg>

Two questions — operation type, then update type — settle the choice.

## 5. Runnable example

```java
// FenwickVsSegmentTree.java
public class FenwickVsSegmentTree {

    // Basic: Fenwick tree for sum with point updates -- the simple, fast-to-write case.
    static class Fenwick {
        int[] tree;
        int n;

        Fenwick(int n) { this.n = n; tree = new int[n + 1]; }

        void update(int i, int delta) { for (; i <= n; i += i & (-i)) tree[i] += delta; }
        int prefixSum(int i) { int s = 0; for (; i > 0; i -= i & (-i)) s += tree[i]; return s; }
        int rangeSum(int l, int r) { return prefixSum(r) - prefixSum(l - 1); }
    }

    static void basicLevel() {
        Fenwick fenwick = new Fenwick(6);
        int[] values = {0, 2, 5, 1, 4, 9, 3};
        for (int i = 1; i <= 6; i++) fenwick.update(i, values[i]);

        System.out.println("basic (Fenwick, sum): rangeSum(2,5) -> " + fenwick.rangeSum(2, 5));
    }

    // Intermediate: segment tree for min -- the case Fenwick cannot handle at all.
    static class SegTreeMin {
        int[] tree;
        int n;

        SegTreeMin(int[] arr) {
            n = arr.length;
            tree = new int[4 * n];
            build(arr, 1, 0, n - 1);
        }

        void build(int[] arr, int node, int lo, int hi) {
            if (lo == hi) { tree[node] = arr[lo]; return; }
            int mid = (lo + hi) / 2;
            build(arr, 2 * node, lo, mid);
            build(arr, 2 * node + 1, mid + 1, hi);
            tree[node] = Math.min(tree[2 * node], tree[2 * node + 1]);
        }

        int query(int node, int lo, int hi, int l, int r) {
            if (r < lo || hi < l) return Integer.MAX_VALUE;
            if (l <= lo && hi <= r) return tree[node];
            int mid = (lo + hi) / 2;
            return Math.min(query(2 * node, lo, mid, l, r), query(2 * node + 1, mid + 1, hi, l, r));
        }

        int rangeMin(int l, int r) { return query(1, 0, n - 1, l, r); }
    }

    static void intermediateLevel() {
        SegTreeMin segTree = new SegTreeMin(new int[]{2, 5, 1, 4, 9, 3});
        System.out.println("intermediate (segment tree, min -- Fenwick cannot do this): rangeMin(1,4) -> " + segTree.rangeMin(1, 4));
    }

    // Advanced: both handle sum + point update identically for the same input, confirming interchangeable results
    // when the operation is one Fenwick CAN support.
    static class SegTreeSum {
        int[] tree;
        int n;

        SegTreeSum(int[] arr) {
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

        int rangeSum(int l, int r) { return query(1, 0, n - 1, l, r); }
    }

    static void advancedLevel() {
        int[] values = {2, 5, 1, 4, 9, 3};
        Fenwick fenwick = new Fenwick(6);
        for (int i = 0; i < values.length; i++) fenwick.update(i + 1, values[i]);
        SegTreeSum segTree = new SegTreeSum(values);

        int fenwickResult = fenwick.rangeSum(2, 5);
        int segTreeResult = segTree.rangeSum(1, 4); // 0-indexed equivalent of Fenwick's 1-indexed [2,5]

        System.out.println("advanced: Fenwick sum -> " + fenwickResult + ", segment tree sum -> " + segTreeResult + " (same range, same answer)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java FenwickVsSegmentTree.java`

## 6. Walkthrough

**Scenario 1 — a running leaderboard total, updated as scores change.** Sum, point updates only. Both structures work; the Fenwick tree is the better choice for its smaller code footprint and lower constant factor.

**Scenario 2 — the minimum stock price in a sliding window, as new prices arrive.** Min, point updates. A Fenwick tree cannot do this at all — `basicLevel` and `intermediateLevel` in the code above show exactly this split: Fenwick handles the sum case, but the min case requires a segment tree from the start.

**Scenario 3 — adding a flat bonus to every player's score in a rank range, then querying total score in another range.** Sum, but now with **range** updates. A plain Fenwick tree only supports point updates cleanly; reaching for the two-BIT range-update extension adds real complexity. A segment tree with [lazy propagation](0156-lazy-propagation-in-segment-trees.md) handles this directly, using the same core recursion just described.

The `advancedLevel` example confirms both structures agree exactly on the same sum query over the same data, when the problem is squarely within both structures' capability — validating that neither is "wrong," they simply have different capability boundaries.

**Complexity.** Both: `O(log n)` per operation. The difference is not in asymptotic complexity but in constant factor (Fenwick's iterative loop beats a segment tree's recursive calls), code complexity, and — critically — which operations are even supported at all.

## 7. Gotchas & takeaways

> Defaulting to a segment tree "because it can do everything" costs real engineering time: more code to write, more edge cases to test, and a larger memory footprint (`4n` vs `n+1`). When the problem only needs sum with point updates, that extra cost buys nothing.

- The one question that eliminates the Fenwick tree entirely: does the operation have an inverse? If not (min, max, gcd), only a segment tree works.
- The second question: are updates ever applied to a **range**, not just a single point? If yes, a segment tree with lazy propagation is far less error-prone than the Fenwick tree's range-update extension.
- When both apply equally, prefer the Fenwick tree for its smaller, simpler, faster-to-verify implementation — this matters especially under time pressure, like a coding interview or a production hotfix.
