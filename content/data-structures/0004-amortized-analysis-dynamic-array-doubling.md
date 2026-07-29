---
card: data-structures
gi: 4
slug: amortized-analysis-dynamic-array-doubling
title: Amortized analysis (dynamic-array doubling)
---

## 1. What it is

**Amortized analysis** measures the *average* cost of an operation across a long sequence of operations, even when individual operations can occasionally be much more expensive than others. A dynamic array (like Java's `ArrayList`) is the canonical example: `add()` is usually O(1), but occasionally triggers an O(n) resize (copying every existing element into a larger backing array) — yet the amortized cost of `add()`, averaged over many calls, is still O(1).

## 2. Why & when

Use amortized analysis whenever a data structure has rare-but-expensive operations that are triggered by, and roughly proportional to, the number of preceding cheap operations — this is a very different situation from a genuinely unpredictable worst case, since the expensive operations here follow a predictable pattern that "pays for itself" over time. Recognizing this pattern avoids incorrectly concluding that a data structure is O(n) per operation just because *some* calls are O(n).

## 3. Core concept

**Why array doubling achieves O(1) amortized, not just O(n) worst case, per `add`:** when a dynamic array's backing array is full, resizing to **double** the capacity (not just adding one more slot) is the key design choice. After a resize to capacity `2n`, the array can absorb `n` more cheap O(1) additions before it needs to resize again. This means an expensive O(n) resize is always followed by a long stretch of `n` cheap O(1) operations that "earn back" the cost of that resize.

**The accounting argument (a standard way to formalize amortized cost):** imagine each `add()` call is charged a flat fee of `3` "credits," regardless of whether it triggers a resize. Of these: `1` credit pays for inserting the new element itself. The other `2` credits are banked, to be spent later. When a resize eventually happens (copying `n` existing elements), each of those `n` elements has *already* banked `2` credits from when it was originally added — exactly enough to pay for its own copy during the resize. Since every element's own eventual "copy cost" was pre-paid when it was first inserted, the total cost across any sequence of `n` additions is bounded by `O(n)` total, or O(1) *per operation on average* — this is precisely what "amortized O(1)" means.

**Why doubling (not fixed-increment growth) is essential for this argument to work:** if the array instead grew by a *fixed* amount (say, always adding `10` more slots when full, rather than doubling), the number of resizes over `n` insertions would be `O(n)` (roughly `n/10` resizes), and each resize costs O(current size) — the total cost across all resizes would then be O(n²), giving O(n) amortized per operation, not O(1). Doubling ensures the number of resizes is only O(log n), and the *total* copying work across all resizes sums to O(n) (a geometric series: `n/2 + n/4 + n/8 + ... < n`), which is what keeps the amortized cost constant.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cost per add() call over time: mostly flat O(1) bars, with occasional tall spikes at resize points, but the spikes shrink in frequency as capacity doubles">
  <g font-family="sans-serif" font-size="11">
    <line x1="40" y1="150" x2="660" y2="150" stroke="#8b949e"/>
    <rect x="50" y="140" width="15" height="10" fill="#3fb950"/>
    <rect x="70" y="140" width="15" height="10" fill="#3fb950"/>
    <rect x="90" y="80" width="15" height="70" fill="#f85149"/>
    <text x="97" y="75" fill="#f85149" text-anchor="middle" font-size="10">resize</text>
    <rect x="110" y="140" width="15" height="10" fill="#3fb950"/>
    <rect x="130" y="140" width="15" height="10" fill="#3fb950"/>
    <rect x="150" y="140" width="15" height="10" fill="#3fb950"/>
    <rect x="170" y="60" width="15" height="90" fill="#f85149"/>
    <text x="177" y="55" fill="#f85149" text-anchor="middle" font-size="10">resize</text>
    <rect x="190" y="140" width="200" height="10" fill="#3fb950"/>
    <text x="290" y="135" fill="#8b949e" text-anchor="middle" font-size="10">many cheap O(1) adds</text>
    <text x="350" y="20" fill="#79c0ff" text-anchor="middle">resizes grow rarer as capacity doubles - averaged cost per add stays O(1)</text>
  </g>
</svg>

Each resize is followed by a proportionally longer stretch of cheap operations before the next resize — the rare expensive spikes are outpaced by the growing gaps between them.

## 5. Runnable example

The artifact below implements a minimal dynamic array with doubling, and measures the *total* number of element copies across many additions, showing it stays proportional to `n`, not `n²`.

```java
// AmortizedDynamicArray.java
public class AmortizedDynamicArray {

    private int[] data;
    private int size;
    private long totalCopies = 0; // tracks total element-copy work across all resizes

    public AmortizedDynamicArray(int initialCapacity) {
        data = new int[initialCapacity];
        size = 0;
    }

    public void add(int value) {
        if (size == data.length) {
            resize();
        }
        data[size++] = value;
    }

    private void resize() {
        int[] newData = new int[data.length * 2];
        for (int i = 0; i < data.length; i++) {
            newData[i] = data[i];
            totalCopies++;
        }
        data = newData;
    }

    public static void main(String[] args) {
        int n = 100000;
        AmortizedDynamicArray arr = new AmortizedDynamicArray(1);

        for (int i = 0; i < n; i++) {
            arr.add(i);
        }

        System.out.println("n = " + n);
        System.out.println("total copy operations across all resizes: " + arr.totalCopies);
        System.out.println("ratio (totalCopies / n): " + ((double) arr.totalCopies / n));
        // ratio stays small and bounded (close to 1-2), NOT growing with n - confirms O(1) amortized
    }
}
```

**How to run:** save as `AmortizedDynamicArray.java`, then run `java AmortizedDynamicArray.java`.

## 6. Walkthrough

1. Starting with `initialCapacity=1`, the first `add` fills the array immediately. Each subsequent `add` that finds the array full triggers a `resize()`, doubling capacity: `1 -> 2 -> 4 -> 8 -> ... -> up to just past 100000`.
2. Each `resize()` call copies every existing element into the new, larger array, incrementing `totalCopies` once per element copied.
3. Across `100000` total `add` calls, only about `log2(100000) ≈ 17` resizes ever happen, and the copies performed across *all* of them sum to less than `2 x 100000` (a geometric series: `1 + 2 + 4 + ... + 65536 < 2 x 65536`), even though `n=100000` individual `add` calls happened.
4. The printed ratio (`totalCopies / n`) stays close to a small constant (around `1`–`2`), not growing as `n` grows — this is the direct empirical signature of O(1) amortized cost: the *total* work across `n` operations is O(n), so the *average* work per operation is O(1).

## 7. Gotchas & takeaways

> Gotcha: amortized O(1) does **not** mean every individual `add()` call is fast — a single unlucky call can still trigger an O(n) resize, which matters for latency-sensitive systems (like real-time applications) where one slow call, even if rare, can be a real problem; amortized analysis describes *average* cost over a sequence, not a guarantee about any single call.

- Amortized analysis measures the average cost per operation over a long sequence, allowing occasional expensive operations as long as they are proportionally rare.
- Doubling (not fixed-increment growth) is what makes dynamic array resizing achieve O(1) amortized `add` — the total copying work across all resizes sums to O(n), not O(n²).
- Related concepts: [Best / average / worst case analysis](0003-best-average-worst-case-analysis.md) (a related but distinct idea — amortized cost is about cost *across a sequence of operations*, not about different possible inputs to a single operation).
