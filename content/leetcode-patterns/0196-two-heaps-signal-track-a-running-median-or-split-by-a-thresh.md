---
card: leetcode-patterns
gi: 196
slug: two-heaps-signal-track-a-running-median-or-split-by-a-thresh
title: Two Heaps — signal: track a running median or split by a threshold
---

## 1. What it is

Two heaps is a technique where you maintain a max-heap for the smaller half of your data and a min-heap for the larger half, keeping both halves balanced in size. The top of each heap gives you instant access to the boundary between "low" and "high" — which is exactly what you need to compute a running median. Think of it as a see-saw: the max-heap holds everything below the midpoint, the min-heap holds everything above it, and both stay balanced as new elements arrive.

## 2. Why & when

You reach for two heaps when a brute-force solution would re-sort the entire dataset (or a large slice of it) every time a new element arrives, giving O(n log n) per update. Two heaps cuts this to O(log n) per update by keeping the data pre-partitioned into two ordered halves, so finding the median (or any threshold-based value) never requires touching every element.

Learn to recognize these signals in a problem statement:

- **"Find the median"** as data streams in one element at a time (`addNum` / `findMedian` style APIs). This is the textbook two-heaps use case.
- **"Track the running/sliding median"** over a fixed-size window as it moves across an array.
- **"Split into two groups by size or by threshold"** — problems where you need the k smallest AND the rest partitioned, updated incrementally.
- **A scheduling or resource-allocation problem with two competing priority orders** — e.g. one heap for "available now, cheapest first" and another for "not yet available, sorted by unlock time."

The alternative is a sorted data structure like a `TreeMap` or a balanced binary search tree, which also supports O(log n) insert and O(log n) median lookup, but two heaps is simpler to implement and is the pattern interviewers expect for streaming-median questions specifically.

## 3. Core concept

Two heaps always follow the same shape: a max-heap (`lower`) holds the smaller half of the seen values, and a min-heap (`upper`) holds the larger half. The invariant is that every value in `lower` is `<=` every value in `upper`, and the two heaps' sizes differ by at most 1.

**Insertion.** A new value is pushed into ONE heap first — typically `lower` if it is smaller than `lower`'s max (or `lower` is empty), otherwise `upper`. Then a rebalancing step moves the top of the larger heap to the smaller heap if the size difference exceeds 1.

**Median query.** If the heaps are equal size, the median is the average of both tops. If one heap has one more element, the median is that heap's top.

The key insight: because each heap is internally ordered (via the heap property) and the two heaps together partition the data at the median, you never need to look at more than the two top elements to answer a median query, and inserting a new element only requires a constant number of heap operations, each O(log n).

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap holding the lower half, min-heap holding the upper half, tops meeting at the median">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">lower (max-heap)</text>
    <circle cx="60" cy="60" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="64" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="30" cy="110" r="16" fill="#161b22" stroke="#3fb950"/><text x="30" y="114" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="90" cy="110" r="16" fill="#161b22" stroke="#3fb950"/><text x="90" y="114" fill="#e6edf3" text-anchor="middle">4</text>

    <text x="280" y="20" fill="#e6edf3" font-weight="bold">upper (min-heap)</text>
    <circle cx="320" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="320" y="64" fill="#e6edf3" text-anchor="middle">6</text>
    <circle cx="290" cy="110" r="16" fill="#161b22" stroke="#79c0ff"/><text x="290" y="114" fill="#e6edf3" text-anchor="middle">8</text>
    <circle cx="350" cy="110" r="16" fill="#161b22" stroke="#79c0ff"/><text x="350" y="114" fill="#e6edf3" text-anchor="middle">7</text>

    <text x="190" y="65" fill="#e3b341" text-anchor="middle">median</text>
    <line x1="78" y1="60" x2="302" y2="60" stroke="#e3b341" stroke-dasharray="4,3"/>
  </g>
</svg>

The max-heap's top (`5`) and min-heap's top (`6`) sit right at the boundary; with equal-sized heaps, the median is their average.

## 5. Runnable example

A tiny probe you can run to confirm the two-heaps signal applies: check whether a problem's data can be cleanly split into "smaller half" and "larger half" with a meaningful boundary value.

### Signal-checker

```java
// TwoHeapsSignal.java
import java.util.*;

public class TwoHeapsSignal {
    public static void main(String[] args) {
        int[] stream = {5, 3, 8, 4, 6, 7};
        PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());
        PriorityQueue<Integer> upper = new PriorityQueue<>();

        for (int num : stream) {
            if (lower.isEmpty() || num <= lower.peek()) lower.add(num);
            else upper.add(num);
        }

        System.out.println("lower half (max-heap): " + lower);
        System.out.println("upper half (min-heap): " + upper);
        System.out.println("-> a clean size-balanced split exists, two heaps applies");
    }
}
```

**How to run:** `java TwoHeapsSignal.java`

## 6. Walkthrough

1. You read the problem statement. It mentions numbers arriving one at a time and asks you to report the median after each one.
2. "Running median on a stream" is the clearest two-heaps signal — no sorting from scratch is acceptable at each step.
3. You set up `lower` as a max-heap and `upper` as a min-heap, both empty.
4. Running the checker above on `{5, 3, 8, 4, 6, 7}` shows the data does split cleanly into two ordered halves with a well-defined boundary.
5. This confirms two heaps is the right structure: each insertion will need only a constant number of heap operations, and the median will always be readable from the two tops.

## 7. Gotchas & takeaways

> Gotcha: inserting a new value into the WRONG heap first (e.g. always into `upper` regardless of value) breaks the "every lower value <= every upper value" invariant, and no amount of later rebalancing by size alone can fix a value sitting in the wrong half.

- Always compare the new value against `lower`'s top BEFORE deciding which heap to insert into — size-based rebalancing only fixes COUNT imbalance, not value misplacement.
- The two-heap sizes should differ by at most 1 — enforce this after every insertion, not just occasionally.
- If you see "running median" or "streaming data, need the middle value repeatedly," it is almost always two heaps, not re-sorting.
