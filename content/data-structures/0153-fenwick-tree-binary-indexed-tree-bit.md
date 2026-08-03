---
card: data-structures
gi: 153
slug: fenwick-tree-binary-indexed-tree-bit
title: Fenwick tree / Binary Indexed Tree (BIT)
---

## 1. What it is

A **Fenwick tree**, also called a **Binary Indexed Tree (BIT)**, is a compact array-based structure that answers prefix-sum queries and point updates in `O(log n)` time. It stores partial sums at cleverly chosen indices, so each index is responsible for summing a range whose length matches the lowest set bit of that index's position.

## 2. Why & when

Use a Fenwick tree when you only need **prefix sums** (or range sums derived from two prefix sums) plus point updates, and you want less code and less memory than a [segment tree](0152-segment-tree-range-query-update.md). A Fenwick tree is a single array of size `n + 1`, with no explicit tree nodes or pointers, which makes it faster to write and slightly faster to run. It cannot directly do range min/max, only sums (or other invertible operations).

## 3. Core concept

**The shape.** An array `tree[1..n]` (1-indexed). Index `i` stores the sum of a range ending at `i`, whose length is `i`'s lowest set bit — written `i & (-i)`. For example, `i = 6` (binary `110`) has lowest set bit `2`, so `tree[6]` covers indices `5` and `6`.

**The invariant.** `tree[i]` always equals the sum of exactly `i & (-i)` elements ending at index `i`. This lets both operations walk a chain of `O(log n)` indices:
- **Update** index `i`: add the delta to `tree[i]`, then move to `i + (i & -i)` and repeat, until past `n`. This "fixes" every larger range that includes `i`.
- **Prefix sum** up to `i`: read `tree[i]`, then move to `i - (i & -i)` and repeat, summing as you go, until you reach `0`.

**Why it makes operations fast.** Each move strips or adds one bit in the binary representation of the index, so both walks take at most `O(log n)` steps — the number of bits in `n`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fenwick tree array where each index covers a range whose length equals its lowest set bit">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">index:</text>
    <text x="10" y="120">covers:</text>
    <g>
      <text x="90" y="20" text-anchor="middle">1</text><text x="90" y="120" text-anchor="middle">[1,1]</text>
      <text x="140" y="20" text-anchor="middle">2</text><text x="140" y="120" text-anchor="middle">[1,2]</text>
      <text x="190" y="20" text-anchor="middle">3</text><text x="190" y="120" text-anchor="middle">[3,3]</text>
      <text x="240" y="20" text-anchor="middle">4</text><text x="240" y="120" text-anchor="middle">[1,4]</text>
      <text x="290" y="20" text-anchor="middle">5</text><text x="290" y="120" text-anchor="middle">[5,5]</text>
      <text x="340" y="20" text-anchor="middle">6</text><text x="340" y="120" text-anchor="middle">[5,6]</text>
      <text x="390" y="20" text-anchor="middle">7</text><text x="390" y="120" text-anchor="middle">[7,7]</text>
      <text x="440" y="20" text-anchor="middle">8</text><text x="440" y="120" text-anchor="middle">[1,8]</text>
    </g>
    <rect x="70" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="120" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="170" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="220" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="270" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="320" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="370" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <rect x="420" y="40" width="40" height="24" fill="#161b22" stroke="#79c0ff"/>
    <path d="M 240 100 L 240 90 L 90 90 L 90 66" stroke="#f0883e" fill="none"/>
    <path d="M 240 100 L 240 90 L 140 90 L 140 66" stroke="#f0883e" fill="none"/>
    <path d="M 240 100 L 240 66" stroke="#f0883e" fill="none"/>
    <path d="M 240 100 L 240 90 L 190 90 L 190 66" stroke="#f0883e" fill="none"/>
    <text x="240" y="150" text-anchor="middle" font-size="8" fill="#f0883e">update(4, +v) touches 4, 8, ...</text>
    <text x="240" y="200" font-size="8" fill="#8b949e">update(i): i += i &amp; (-i)   |   prefixSum(i): i -= i &amp; (-i)</text>
  </g>
</svg>

`update(4, +v)` walks `4 -> 8 -> ...`, touching every Fenwick node whose range includes index 4.

## 5. Runnable example

```java
// FenwickTree.java
public class FenwickTree {

    // Basic: 1-indexed Fenwick tree supporting point update and prefix sum.
    static class BIT {
        int[] tree;
        int n;

        BIT(int n) { this.n = n; tree = new int[n + 1]; }

        void update(int index, int delta) {
            for (int i = index; i <= n; i += i & (-i)) {
                tree[i] += delta;
            }
        }

        int prefixSum(int index) {
            int sum = 0;
            for (int i = index; i > 0; i -= i & (-i)) {
                sum += tree[i];
            }
            return sum;
        }
    }

    static void basicLevel() {
        BIT bit = new BIT(8);
        int[] values = {0, 2, 5, 1, 4, 9, 3, 7, 6}; // index 0 unused
        for (int i = 1; i <= 8; i++) bit.update(i, values[i]);

        System.out.println("basic: prefixSum(4) -> " + bit.prefixSum(4));
    }

    // Intermediate: range sum via two prefix sums, plus a live point update.
    static class RangeBIT extends BIT {
        RangeBIT(int n) { super(n); }

        int rangeSum(int l, int r) { return prefixSum(r) - prefixSum(l - 1); }
    }

    static void intermediateLevel() {
        RangeBIT bit = new RangeBIT(8);
        int[] values = {0, 2, 5, 1, 4, 9, 3, 7, 6};
        for (int i = 1; i <= 8; i++) bit.update(i, values[i]);

        System.out.println("intermediate: rangeSum(2,5) -> " + bit.rangeSum(2, 5));
        bit.update(3, 10); // add 10 at index 3
        System.out.println("intermediate: rangeSum(2,5) after +10 at index 3 -> " + bit.rangeSum(2, 5));
    }

    // Advanced: build the BIT from an initial array in O(n) instead of n separate O(log n) updates.
    static class FastBuildBIT extends BIT {
        FastBuildBIT(int[] values) {
            super(values.length);
            for (int i = 1; i <= n; i++) tree[i] += values[i - 1];
            for (int i = 1; i <= n; i++) {
                int parent = i + (i & (-i));
                if (parent <= n) tree[parent] += tree[i];
            }
        }
    }

    static void advancedLevel() {
        FastBuildBIT bit = new FastBuildBIT(new int[]{2, 5, 1, 4, 9, 3, 7, 6});
        System.out.println("advanced: prefixSum(8) via O(n) build -> " + bit.prefixSum(8));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java FenwickTree.java`

## 6. Walkthrough

Build the BIT over `[2, 5, 1, 4, 9, 3, 7, 6]` (1-indexed) by calling `update(i, values[i])` for `i = 1..8`. Each call climbs from `i` toward `n` by repeatedly adding the lowest set bit.

Trace `prefixSum(4)`. Start at `i = 4` (binary `100`), add `tree[4]` (covers `[1,4]`). Move to `i - (i & -i) = 4 - 4 = 0`, so the loop stops. Result: `tree[4] = 2+5+1+4 = 12`.

Trace `prefixSum(6)`. Start at `i = 6` (binary `110`), add `tree[6]` (covers `[5,6] = 9+3 = 12`). Move to `i = 6 - 2 = 4`, add `tree[4] = 12`. Move to `i = 0`, stop. Total: `12 + 12 = 24`.

So `rangeSum(2, 5) = prefixSum(5) - prefixSum(1) = (2+5+1+4+9) - 2 = 21 - 2 = 19`.

Now update index `3` by `+10`. Start at `i = 3` (binary `011`), add `10` to `tree[3]`. Move to `i = 3 + 1 = 4`, add `10` to `tree[4]`. Move to `i = 4 + 4 = 8`, add `10` to `tree[8]`. Move to `i = 8 + 8 = 16 > n`, stop. Only three nodes changed, and every prefix sum crossing index 3 is now correct.

**Complexity.** Point update: `O(log n)`. Prefix sum: `O(log n)`. Range sum: `O(log n)`. Space: `O(n)`. Building from an existing array: `O(n)` with the linear-build trick, or `O(n log n)` with `n` separate updates.

## 7. Gotchas & takeaways

> Fenwick trees are 1-indexed by convention. Calling `update(0, ...)` or `prefixSum(0)` is a silent no-op because `i & (-i)` at `i = 0` never advances the loop — always shift your data to start at index 1.

- A Fenwick tree only supports operations with an inverse (sum, XOR). It cannot do range min/max directly, because you cannot "subtract" a minimum the way you subtract a sum.
- For range **updates** plus range **sum queries**, use two Fenwick trees (a well-known extension) rather than switching to a full segment tree.
- Prefer a segment tree when you need min/max, or when the combine operation has no inverse.
