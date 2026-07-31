---
card: data-structures
gi: 20
slug: array-resizing-amortized-append
title: Array resizing & amortized append
---

## 1. What it is

A **dynamic array** (Java's `ArrayList`) behaves like it can grow forever, even though it is built on top of a fixed-size array underneath. When the backing array fills up, `ArrayList` allocates a **new, bigger** array — typically 1.5x to 2x the old capacity — copies every old element into it, and discards the old array. This is called **resizing**, and the trick that makes repeated `add()` calls still fast on average is called **amortized** analysis.

## 2. Why & when

You rely on this every time you call `list.add(value)` without knowing the final size ahead of time. Understanding resizing explains two things: why `ArrayList` occasionally has a slow `add()` call (when a resize triggers) mixed with many fast ones, and why pre-sizing a list with `new ArrayList<>(expectedSize)` avoids that wasted copying when the final size is known.

## 3. Core concept

**Growth strategy: double (or 1.5x) the capacity, not add a fixed amount.** If capacity grew by a fixed number (say +1 each time), every single append would trigger a copy, making every `add()` an O(n) operation — O(n²) total for n appends. Doubling instead makes resizes rarer and rarer as the array gets bigger.

**Why doubling gives O(1) amortized cost.** "Amortized" means averaged over a long sequence of operations, not the cost of any one call. Appending n elements with doubling triggers resizes at sizes 1, 2, 4, 8, ... up to n. The total copying work across all resizes sums to about 2n — a constant multiple of n. Spread that 2n total cost over n appends, and each append costs O(1) *on average*, even though a handful of individual calls are O(n).

**The individual spike is real, just rare.** Any single `add()` call that triggers a resize is genuinely O(n) — it copies every existing element. Amortized analysis does not hide that cost; it shows that such expensive calls happen so infrequently (only at power-of-two-ish sizes) that they do not change the average per-call cost.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Capacity doubling from 2 to 4 to 8, with occasional expensive copy operations getting rarer as size grows">
  <g font-family="sans-serif" font-size="12">
    <text x="320" y="20" fill="#8b949e" text-anchor="middle">capacity doubles: 2 -&gt; 4 -&gt; 8, resizes get rarer</text>
    <rect x="30" y="40" width="40" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="30" y="70" width="40" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <text x="50" y="110" fill="#8b949e" text-anchor="middle" font-size="10">cap=2</text>

    <rect x="140" y="40" width="40" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="180" y="40" width="40" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="140" y="70" width="40" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <rect x="180" y="70" width="40" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <text x="180" y="110" fill="#8b949e" text-anchor="middle" font-size="10">cap=4 (copy 2)</text>

    <rect x="290" y="40" width="30" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="320" y="40" width="30" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="350" y="40" width="30" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="380" y="40" width="30" height="25" fill="#161b22" stroke="#3fb950"/>
    <rect x="290" y="70" width="30" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <rect x="320" y="70" width="30" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <rect x="350" y="70" width="30" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <rect x="380" y="70" width="30" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <text x="350" y="110" fill="#8b949e" text-anchor="middle" font-size="10">cap=8 (copy 4)</text>

    <text x="320" y="150" fill="#79c0ff" text-anchor="middle">total copying across all resizes ~ 2n -&gt; O(1) amortized per append</text>
  </g>
</svg>

Each resize copies more elements than the last, but resizes happen exponentially less often — the total copying work stays proportional to n.

## 5. Runnable example

```java
// ArrayResizingAmortizedAppend.java
import java.util.ArrayList;
import java.util.List;

public class ArrayResizingAmortizedAppend {

    // Basic: a hand-rolled dynamic array that doubles capacity when full.
    static final class SimpleDynamicArray {
        private int[] data = new int[1];
        private int size = 0;

        void append(int value) {
            if (size == data.length) {
                int[] bigger = new int[data.length * 2]; // double the capacity
                System.arraycopy(data, 0, bigger, 0, size); // copy every existing element
                data = bigger;
                System.out.println("  [resized to capacity " + data.length + "]");
            }
            data[size++] = value;
        }

        int size() { return size; }
    }

    static void basicLevel() {
        SimpleDynamicArray arr = new SimpleDynamicArray();
        for (int i = 1; i <= 8; i++) {
            System.out.println("basic: appending " + i + " (size before=" + arr.size() + ")");
            arr.append(i);
        }
    }

    // Intermediate: timing individual ArrayList.add() calls shows occasional spikes at resize points.
    static void intermediateLevel() {
        List<Integer> list = new ArrayList<>();
        long maxSpike = 0;
        for (int i = 0; i < 100_000; i++) {
            long start = System.nanoTime();
            list.add(i);
            long elapsed = System.nanoTime() - start;
            if (elapsed > maxSpike) maxSpike = elapsed;
        }
        System.out.println("intermediate: slowest single add() out of 100,000 -> " + maxSpike + "ns (a resize event)");
    }

    // Advanced: pre-sizing avoids the copying entirely when the final size is known ahead of time.
    static void advancedLevel() {
        int n = 500_000;

        long t1 = System.nanoTime();
        List<Integer> grown = new ArrayList<>(); // starts small, resizes many times
        for (int i = 0; i < n; i++) grown.add(i);
        long growTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        List<Integer> preSized = new ArrayList<>(n); // capacity reserved up front, zero resizes
        for (int i = 0; i < n; i++) preSized.add(i);
        long preSizedTime = System.nanoTime() - t2;

        System.out.println("advanced: default growth time(ns) -> " + growTime);
        System.out.println("advanced: pre-sized time(ns) -> " + preSizedTime + " (no resize copying at all)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArrayResizingAmortizedAppend.java`, then run `java ArrayResizingAmortizedAppend.java`.

## 6. Walkthrough

1. `basicLevel()` starts `SimpleDynamicArray` with capacity 1. Appending `1` fills it immediately; appending `2` triggers a resize to capacity 2, copying 1 element.
2. Appending `3` triggers another resize (capacity 2 is full) to capacity 4, copying 2 elements. Appending `5` later triggers a resize to capacity 8, copying 4 elements — each resize is more expensive, but happens at exponentially larger sizes.
3. `intermediateLevel()` calls `ArrayList.add()` 100,000 times and records the single slowest call. That spike marks the moment a resize copy ran; the other 99,999+ calls were fast O(1) appends into existing capacity.
4. `advancedLevel()` compares default growth (many resizes as the list grows from empty to 500,000) against pre-sizing the `ArrayList` with its final capacity up front (`new ArrayList<>(n)`), which needs zero resize copies.
5. The pre-sized version should run measurably faster, since it skips all the repeated allocate-and-copy work that default growth performs along the way.

## 7. Gotchas & takeaways

> Gotcha: "amortized O(1)" describes the *average* cost over many calls, not the cost of any single call — an individual `add()` that triggers a resize is a real O(n) operation. In latency-sensitive code (e.g. a hot loop with a hard per-call time budget), that occasional spike can matter even though the long-run average is cheap.

- Dynamic arrays grow by allocating a bigger backing array and copying every element over, typically doubling capacity each time.
- Doubling (not fixed-size growth) is what makes the *total* copying cost across n appends proportional to n, giving O(1) amortized cost per append.
- Pre-sizing a collection with `new ArrayList<>(expectedSize)` avoids resize copying entirely when the final size is known.
- Related concepts: [Amortized analysis: dynamic array doubling](0004-amortized-analysis-dynamic-array-doubling.md), [Insert / delete shifting cost](0019-insert-delete-shifting-cost.md).
