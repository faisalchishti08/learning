---
card: leetcode-patterns
gi: 204
slug: find-median-from-data-stream
title: Find Median from Data Stream
---

## 1. What it is

Design a data structure that supports `addNum(int num)` (add a number from the stream) and `findMedian()` (return the median of all numbers added so far), both called repeatedly and interleaved. Example: after `addNum(1)`, `addNum(2)`, `addNum(3)`, `findMedian()` returns `2`.

## 2. Why & when

This is the two-heaps pattern's namesake problem: the direct, textbook application with no extra twist. It is the exact template — a max-heap for the lower half, a min-heap for the upper half, rebalanced after every insertion.

## 3. Core concept

**Key idea:** maintain `lower` (max-heap) for the smaller half of numbers seen and `upper` (min-heap) for the larger half, keeping their sizes within 1 of each other. The median is always readable from the top(s) of these two heaps without scanning any data.

**Steps:**
1. On `addNum(num)`: if `lower` is empty or `num <= lower.peek()`, add `num` to `lower`; otherwise add it to `upper`.
2. Rebalance: if `lower.size() > upper.size() + 1`, move `lower.poll()` into `upper`. If `upper.size() > lower.size()`, move `upper.poll()` into `lower`.
3. On `findMedian()`: if the two heaps are equal size, return the average of both tops. Otherwise, return `lower`'s top (since `lower` is always the larger or equal one after rebalancing).

**Why it is correct:** every value in `lower` is `<=` every value in `upper`, an invariant maintained by always inserting relative to `lower`'s current max before rebalancing by size. With sizes differing by at most 1, the two tops sit exactly at the boundary between the lower and upper halves of the sorted data — which is the definition of the median for both even and odd counts.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap for lower half, min-heap for upper half, median read from the tops">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="80" r="18" fill="#161b22" stroke="#3fb950"/><text x="100" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="80" cy="130" r="14" fill="#161b22" stroke="#3fb950"/><text x="80" y="134" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="320" cy="80" r="18" fill="#161b22" stroke="#79c0ff"/><text x="320" y="84" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="210" y="84" fill="#e3b341" text-anchor="middle">median = 2</text>
    <text x="10" y="15" fill="#e6edf3">after adding 1,2,3: lower={2,1}, upper={3}; unequal sizes, median = lower.peek() = 2</text>
  </g>
</svg>

With three numbers, `lower` holds one extra element, so the median is directly `lower`'s top.

## 5. Runnable example

```java
// MedianFinder.java
import java.util.*;

public class MedianFinder {

    // Level 1 -- Brute force: keep a single sorted list, using binary
    // search to find the insertion point on each addNum, then shifting
    // elements to insert. Correct, but O(n) per insertion (the shift),
    // versus O(log n) with two heaps.

    // KEY INSIGHT: split the data into two heaps at the median boundary
    // -- a max-heap for everything below it, a min-heap for everything
    // above -- so both insertion and median lookup avoid touching most
    // of the data.

    // Level 2 -- Optimal: two heaps, insert-then-rebalance.
    private PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());
    private PriorityQueue<Integer> upper = new PriorityQueue<>();

    public void addNum(int num) {
        if (lower.isEmpty() || num <= lower.peek()) lower.add(num);
        else upper.add(num);

        if (lower.size() > upper.size() + 1) upper.add(lower.poll());
        else if (upper.size() > lower.size()) lower.add(upper.poll());
    }

    public double findMedian() {
        if (lower.size() == upper.size()) return (lower.peek() + upper.peek()) / 2.0;
        return lower.peek();
    }

    // Level 3 -- Hardened: works correctly whether addNum and
    // findMedian calls are interleaved in any order, since the
    // invariant (sizes within 1, lower <= upper) is restored after
    // EVERY single addNum call, not just at the end of a batch.

    public static void main(String[] args) {
        MedianFinder finder = new MedianFinder();
        finder.addNum(1);
        finder.addNum(2);
        System.out.println(finder.findMedian()); // 1.5
        finder.addNum(3);
        System.out.println(finder.findMedian()); // 2.0
    }
}
```

**How to run:** `java MedianFinder.java`

## 6. Walkthrough

Trace `addNum(1)`, `addNum(2)`, `findMedian()`, `addNum(3)`, `findMedian()`:

| Call | lower | upper | Result |
|---|---|---|---|
| addNum(1) | {1} | {} | — |
| addNum(2) | {1} | {2} (2 > lower.peek()=1, then sizes equal, no rebalance needed) | — |
| findMedian() | {1} | {2} | (1+2)/2.0 = 1.5 |
| addNum(3) | {1} | {2,3} → rebalance moves 2 to lower | {1,2} \| {3} | — |
| findMedian() | {1,2} | {3} | lower.peek() = 2 |

Both results match the problem's expected outputs. Time complexity is O(log n) per `addNum`, O(1) per `findMedian`; space is O(n) for storing every element across both heaps.

## 7. Gotchas & takeaways

> Gotcha: comparing the new value against `upper.peek()` instead of `lower.peek()` when deciding which heap to insert into breaks the core invariant — the decision must always be relative to the CURRENT boundary, which is `lower`'s max.

- This is the reference/baseline problem for the whole two-heaps pattern — every variant (sliding window, IPO, scheduling) reuses this exact insert-then-rebalance skeleton with a different twist layered on top.
- `Collections.reverseOrder()` is essential for `lower` — without it, `lower` would be a min-heap and the whole invariant would invert.
- Related problems: Sliding Window Median (same two heaps, plus lazy deletion for elements leaving the window), IPO (max-heap greedy selection, a different but related heap-based pattern).
