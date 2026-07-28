---
card: leetcode-patterns
gi: 563
slug: range-sum-query-mutable
title: Range Sum Query - Mutable
---

## 1. What it is

Design a class that supports two operations on an integer array: `update(index, value)` (change the element at `index` to `value`), and `sumRange(left, right)` (return the sum of elements from `left` to `right`, inclusive) — with both operations called repeatedly, in any order. Example: `nums = [1,3,5]`; after `update(1, 2)`, `sumRange(0,2)` returns `8` (`1+2+5`).

## 2. Why & when

The word "Mutable" in the title is the direct [signal](0560-segment-tree-bit-signal-range-queries-with-point-range-updat.md): the array changes between queries, so a plain prefix-sum array (fast query, but O(n) to rebuild after any update) is the wrong tool. A Fenwick tree gives both operations O(log n) time. Constraints: up to 30,000 elements and up to 30,000 calls to each operation.

## 3. Core concept

**Key idea:** maintain a Fenwick tree over the array. `update(index, value)` computes the **delta** (`value - currentValue`) and applies that delta to the Fenwick tree, then updates a separate copy of the current array (needed to compute future deltas correctly). `sumRange(left, right)` computes `prefixSum(right) - prefixSum(left - 1)` using the Fenwick tree's 1-indexed convention.

**Steps:**
1. Store `nums` as given, and build a Fenwick tree by calling `update` once per initial element.
2. `update(index, value)`: compute `delta = value - nums[index]`, apply `delta` to the Fenwick tree at `index + 1` (1-indexed), then set `nums[index] = value`.
3. `sumRange(left, right)`: return `fenwick.prefixSum(right + 1) - fenwick.prefixSum(left)`.

**Why storing a separate copy of the current array is necessary:** a Fenwick tree only supports *additive* updates (apply a delta), not *overwrite* (set to a value) directly. Computing the correct delta for an overwrite requires knowing the value being replaced — which the Fenwick tree's internal structure does not expose directly, so a plain array copy is kept alongside it.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="update(1,2) on [1,3,5] computes delta -1 and applies it to the Fenwick tree, then sumRange uses two prefix sums">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums=[1,3,5], update(1,2): delta = 2-3 = -1</text>
    <text x="20" y="50" fill="#79c0ff">fenwick.update(2, -1)  (1-indexed: array index 1 -&gt; fenwick index 2)</text>
    <text x="20" y="80" fill="#3fb950">nums becomes [1,2,5]</text>
    <text x="20" y="110" fill="#e6edf3">sumRange(0,2) = prefixSum(3) - prefixSum(0) = 8 - 0 = 8</text>
  </g>
</svg>

An overwrite update is translated into a delta before being applied to the Fenwick tree, which only understands additive changes.

## 5. Runnable example

**Level 1 — Brute force.** `sumRange` scans the array directly each time, O(n) per query; `update` is O(1). Fast updates, slow queries.

**KEY INSIGHT:** a Fenwick tree balances both operations to O(log n), which is the right tradeoff whenever updates and queries interleave repeatedly.

**Level 2 — Optimal.** Fenwick tree with a delta-based update, O(log n) per operation.

**Level 3 — Hardened.** Handles repeated updates to the same index, and a `sumRange` call over the full array.

```java
// NumArray.java
public class NumArray {

    int[] nums;
    int[] tree;
    int n;

    public NumArray(int[] nums) {
        this.n = nums.length;
        this.nums = new int[n];
        this.tree = new int[n + 1];
        for (int i = 0; i < n; i++) {
            update(i, nums[i]);
        }
    }

    void fenwickAdd(int i, int delta) { // 1-indexed
        for (; i <= n; i += i & (-i)) tree[i] += delta;
    }

    int prefixSum(int i) { // 1-indexed
        int sum = 0;
        for (; i > 0; i -= i & (-i)) sum += tree[i];
        return sum;
    }

    public void update(int index, int value) {
        int delta = value - nums[index];
        nums[index] = value;
        fenwickAdd(index + 1, delta);
    }

    public int sumRange(int left, int right) {
        return prefixSum(right + 1) - prefixSum(left);
    }

    public static void main(String[] args) {
        NumArray obj = new NumArray(new int[]{1, 3, 5});
        System.out.println(obj.sumRange(0, 2)); // 9
        obj.update(1, 2);
        System.out.println(obj.sumRange(0, 2)); // 8
    }
}
```

**How to run:** save as `NumArray.java`, then run `java NumArray.java`.

## 6. Walkthrough

Trace `NumArray([1,3,5])`, then `sumRange(0,2)`, `update(1,2)`, `sumRange(0,2)`:

1. Constructor calls `update(0,1)`, `update(1,3)`, `update(2,5)`, each computing a delta from `nums`'s initial zero state and applying it to the Fenwick tree, ending with `nums=[1,3,5]`.
2. `sumRange(0,2)`: `prefixSum(3) - prefixSum(0) = 9 - 0 = 9`.
3. `update(1,2)`: `delta = 2 - 3 = -1`. `nums` becomes `[1,2,5]`. Fenwick tree adds `-1` at 1-indexed position `2`.
4. `sumRange(0,2)`: `prefixSum(3) - prefixSum(0)`. The Fenwick tree's internal sums now reflect the `-1` delta, giving `8 - 0 = 8`.

## 7. Gotchas & takeaways

> Gotcha: applying `update`'s new `value` directly to the Fenwick tree (instead of computing `value - nums[index]` first) is wrong — the Fenwick tree's `update` method only ever *adds* a delta to existing sums; passing the raw new value would incorrectly add it on top of the old value still baked into the tree.

- Signal: "Mutable" in a range-sum-query problem title means a Fenwick tree (or segment tree) is expected — plain prefix sums cannot handle updates efficiently.
- Keep a separate current-value array alongside the Fenwick tree, since the tree only supports additive updates, not direct overwrites.
- Related problems: Range Sum Query 2D - Mutable (the 2D extension), Count of Smaller Numbers After Self (a different use of the same structure).
