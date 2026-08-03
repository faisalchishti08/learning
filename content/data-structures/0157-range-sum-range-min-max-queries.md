---
card: data-structures
gi: 157
slug: range-sum-range-min-max-queries
title: Range-sum & range-min/max queries
---

## 1. What it is

**Range queries** ask for a combined value — sum, minimum, or maximum — over a contiguous slice `[l, r]` of an array. Several structures answer this question, and picking the right one depends on one thing: does the array change after you build the structure?

## 2. Why & when

Every one of these structures solves the same question with a different tradeoff between build time, query time, and update time. Choosing the slowest structure "just to be safe" wastes both code and runtime; choosing one that cannot update when your data actually changes forces an expensive rebuild. This page exists to help you pick correctly before you write any code.

## 3. Core concept

**The decision criteria.**
- **Does the array ever change after the structure is built?** If never, prefer a static structure. If yes, you need an updatable one.
- **Do you need sum, or min/max?** A [Fenwick tree](0153-fenwick-tree-binary-indexed-tree-bit.md) only supports operations with an inverse (sum, XOR) — it cannot do min/max. A [sparse table](0155-sparse-table-static-range-queries.md) only supports idempotent operations (min, max, gcd) — summing with it double-counts overlaps.
- **Point updates, or range updates?** A plain [segment tree](0152-segment-tree-range-query-update.md) does point updates in `O(log n)`. Range updates need [lazy propagation](0156-lazy-propagation-in-segment-trees.md) to stay at `O(log n)` instead of `O(range length)`.

**The four options, ranked by how much the array changes:**

| Structure | Build | Query | Update | Use when |
|---|---|---|---|---|
| Prefix sum array | `O(n)` | `O(1)` | not supported (rebuild `O(n)`) | static array, sum only |
| Sparse table | `O(n log n)` | `O(1)` | not supported (rebuild `O(n log n)`) | static array, min/max/gcd |
| Fenwick tree (BIT) | `O(n)` or `O(n log n)` | `O(log n)` | `O(log n)` point update | changing array, sum only |
| Segment tree (+ lazy) | `O(n)` | `O(log n)` | `O(log n)` point or range update | changing array, min/max/sum, or range updates |

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decision tree for choosing a range-query structure based on whether the array changes and whether sum or min/max is needed">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="260" y="10" width="140" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="330" y="31" text-anchor="middle">array changes?</text>

    <rect x="80" y="80" width="160" height="34" fill="#0d1117" stroke="#8b949e"/>
    <text x="160" y="101" text-anchor="middle">no -&gt; static structure</text>
    <rect x="420" y="80" width="160" height="34" fill="#0d1117" stroke="#8b949e"/>
    <text x="500" y="101" text-anchor="middle">yes -&gt; updatable structure</text>

    <line x1="330" y1="44" x2="160" y2="80" stroke="#79c0ff"/>
    <line x1="330" y1="44" x2="500" y2="80" stroke="#79c0ff"/>

    <rect x="20" y="150" width="120" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="80" y="171" text-anchor="middle" font-size="9">sum: prefix array</text>
    <rect x="150" y="150" width="120" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="210" y="171" text-anchor="middle" font-size="9">min/max: sparse table</text>
    <rect x="360" y="150" width="120" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="420" y="171" text-anchor="middle" font-size="9">sum: Fenwick tree</text>
    <rect x="490" y="150" width="140" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="560" y="171" text-anchor="middle" font-size="9">min/max/range-update: segment tree</text>

    <line x1="160" y1="114" x2="80" y2="150" stroke="#8b949e"/>
    <line x1="160" y1="114" x2="210" y2="150" stroke="#8b949e"/>
    <line x1="500" y1="114" x2="420" y2="150" stroke="#8b949e"/>
    <line x1="500" y1="114" x2="560" y2="150" stroke="#8b949e"/>
  </g>
</svg>

Two questions — "does it change?" and "sum or min/max?" — pick the structure.

## 5. Runnable example

```java
// RangeQueryChoice.java
public class RangeQueryChoice {

    // Basic: static array, sum only -> prefix sum array. O(n) build, O(1) query, no update.
    static class PrefixSum {
        long[] prefix;

        PrefixSum(int[] arr) {
            prefix = new long[arr.length + 1];
            for (int i = 0; i < arr.length; i++) prefix[i + 1] = prefix[i] + arr[i];
        }

        long rangeSum(int l, int r) { return prefix[r + 1] - prefix[l]; }
    }

    static void basicLevel() {
        PrefixSum ps = new PrefixSum(new int[]{2, 5, 1, 4, 9, 3});
        System.out.println("basic (static, sum): rangeSum(1,4) -> " + ps.rangeSum(1, 4));
    }

    // Intermediate: static array, min only -> sparse table. O(n log n) build, O(1) query.
    static class SparseMin {
        int[][] table;
        int[] log;

        SparseMin(int[] arr) {
            int n = arr.length;
            log = new int[n + 1];
            for (int i = 2; i <= n; i++) log[i] = log[i / 2] + 1;
            int maxK = log[n] + 1;
            table = new int[maxK][n];
            table[0] = arr.clone();
            for (int k = 1; k < maxK; k++) {
                int len = 1 << k;
                for (int i = 0; i + len <= n; i++) {
                    table[k][i] = Math.min(table[k - 1][i], table[k - 1][i + len / 2]);
                }
            }
        }

        int rangeMin(int l, int r) {
            int k = log[r - l + 1];
            return Math.min(table[k][l], table[k][r - (1 << k) + 1]);
        }
    }

    static void intermediateLevel() {
        SparseMin sm = new SparseMin(new int[]{2, 5, 1, 4, 9, 3});
        System.out.println("intermediate (static, min): rangeMin(1,4) -> " + sm.rangeMin(1, 4));
    }

    // Advanced: changing array, both sum and min needed -> compare BIT (sum, updatable) vs
    // segment tree (min, updatable), showing why one structure cannot serve both cleanly.
    static class BIT {
        int[] tree;
        int n;

        BIT(int n) { this.n = n; tree = new int[n + 1]; }

        void update(int i, int delta) { for (; i <= n; i += i & (-i)) tree[i] += delta; }
        int prefixSum(int i) { int s = 0; for (; i > 0; i -= i & (-i)) s += tree[i]; return s; }
        int rangeSum(int l, int r) { return prefixSum(r) - prefixSum(l - 1); }
    }

    static void advancedLevel() {
        int[] values = {2, 5, 1, 4, 9, 3};
        BIT bit = new BIT(values.length);
        for (int i = 0; i < values.length; i++) bit.update(i + 1, values[i]);

        System.out.println("advanced (changing, sum via BIT): rangeSum(2,5) -> " + bit.rangeSum(2, 5));
        bit.update(3, 10); // array now effectively [2,5,11,4,9,3] at 1-indexed position 3
        System.out.println("advanced (changing, sum via BIT): rangeSum(2,5) after update -> " + bit.rangeSum(2, 5));
        System.out.println("advanced note: min/max on a changing array needs a segment tree, not a BIT");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java RangeQueryChoice.java`

## 6. Walkthrough

**Scenario 1 — a leaderboard's total score, computed once from a log file, never updated.** The array is static and you only need sums. Pick the prefix sum array: `O(n)` to build, `O(1)` per query, and no code to handle updates at all.

**Scenario 2 — the daily minimum temperature over any date range, for a fixed historical dataset.** Static array again, but now you need `min`, not `sum`. A prefix sum array cannot do this (there is no "prefix min" that lets you subtract). Pick a sparse table: `O(n log n)` to build once, `O(1)` per query.

**Scenario 3 — a live leaderboard where scores change every few seconds, and you need the total score of the top 10 players by rank range.** The array changes, and you need sum. Pick a Fenwick tree: `O(log n)` per update, `O(log n)` per range sum, far less code than a segment tree.

**Scenario 4 — a live stock-price tracker where you need the minimum price in the last N updates, and prices change constantly.** The array changes and you need `min`. A Fenwick tree cannot do min (no inverse operation). Pick a segment tree: `O(log n)` update, `O(log n)` query, and it naturally supports any associative combine function.

## 7. Gotchas & takeaways

> Reaching for a segment tree by default "because it can do everything" is not free — it is more code, more memory, and slower per operation than the specialized structure the situation actually calls for. Match the structure to the two decision criteria first.

- A Fenwick tree cannot do range min/max, because there is no way to "undo" a minimum the way `prefixSum(r) - prefixSum(l-1)` undoes a sum.
- A sparse table cannot do sum, because its `O(1)` trick relies on overlapping ranges being harmless (`min(a,a)=a`), which is false for sum (`a+a != a`).
- If you need range updates (not just point updates) alongside range queries, only the segment tree with [lazy propagation](0156-lazy-propagation-in-segment-trees.md) handles it in `O(log n)`.
