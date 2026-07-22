---
card: leetcode-patterns
gi: 197
slug: two-heaps-template-a-max-heap-for-the-low-half-a-min-heap-fo
title: Two Heaps — template: a max-heap for the low half, a min-heap for the high half
---

## 1. What it is

A template is the reusable skeleton of code you write first, before filling in problem-specific logic. For two heaps, the skeleton has three parts: an insertion routine, a rebalancing routine, and a query routine. Once memorized, solving a new two-heaps problem becomes "insert into the right heap, rebalance, then read the tops."

## 2. Why & when

Interviewers expect correct, bug-free heap balancing on the first try, since off-by-one errors in the size check are easy to make under pressure. Memorizing this exact template — including the specific order of insert-then-rebalance — removes that risk and lets you focus on the problem-specific twist (e.g. weighted medians, sliding windows, or scheduling order).

## 3. Core concept

**The template, in order:**

1. **Declare two heaps.** `PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());` (max-heap) and `PriorityQueue<Integer> upper = new PriorityQueue<>();` (min-heap, the default).
2. **Insert.** Compare the new value against `lower.peek()` (or insert into `lower` if it is empty). If the new value is `<= lower.peek()`, add it to `lower`; otherwise add it to `upper`.
3. **Rebalance.** After insertion, if `lower.size() > upper.size() + 1`, move `lower.poll()` into `upper`. If `upper.size() > lower.size()`, move `upper.poll()` into `lower`. This keeps `lower` always equal to or exactly one larger than `upper`.
4. **Query.** If `lower.size() == upper.size()`, the median is `(lower.peek() + upper.peek()) / 2.0`. Otherwise (since `lower` is always the larger one after rebalancing), the median is `lower.peek()`.

This four-step shape does not change across problems — what changes is what gets stored in each heap's elements (raw numbers, `[value, index]` pairs, or custom comparators for scheduling order) and what the query step computes beyond a simple median.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Insert into one heap, then rebalance by moving the top element if sizes differ by more than one">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3" font-weight="bold">Step 1: insert 6 into upper (6 > lower.peek()=5)</text>
    <circle cx="60" cy="70" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="74" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="200" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="200" y="74" fill="#e6edf3" text-anchor="middle">6</text>

    <text x="20" y="120" fill="#e6edf3" font-weight="bold">Step 2: rebalance if sizes differ by &gt; 1</text>
    <path d="M120,150 L160,150" stroke="#e3b341" marker-end="url(#a5)"/>
    <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e3b341"/></marker></defs>
    <text x="20" y="170" fill="#8b949e">move lower.poll() to upper, or upper.poll() to lower, as needed</text>
  </g>
</svg>

Insert first into the heap the value belongs to, then rebalance sizes by moving exactly one element if needed.

## 5. Runnable example

The full MedianFinder template, ready to adapt for any two-heaps problem.

```java
// MedianFinder.java
import java.util.*;

public class MedianFinder {
    private PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());
    private PriorityQueue<Integer> upper = new PriorityQueue<>();

    public void addNum(int num) {
        if (lower.isEmpty() || num <= lower.peek()) lower.add(num);
        else upper.add(num);

        if (lower.size() > upper.size() + 1) upper.add(lower.poll());
        else if (upper.size() > lower.size()) lower.add(upper.poll());
    }

    public double findMedian() {
        if (lower.size() == upper.size()) {
            return (lower.peek() + upper.peek()) / 2.0;
        }
        return lower.peek();
    }

    public static void main(String[] args) {
        MedianFinder finder = new MedianFinder();
        int[] stream = {5, 3, 8, 4, 6, 7};
        for (int num : stream) {
            finder.addNum(num);
            System.out.println("after adding " + num + ", median = " + finder.findMedian());
        }
    }
}
```

**How to run:** `java MedianFinder.java`

## 6. Walkthrough

1. `addNum(5)`: `lower` is empty, so `5` goes into `lower`. Sizes are `lower=1, upper=0` — no rebalance needed. Median = `5`.
2. `addNum(3)`: `3 <= lower.peek()=5`, goes into `lower`. Sizes `lower=2, upper=0` — `lower.size() > upper.size()+1` (2 > 1), so move `lower.poll()=5` to `upper`. Now `lower={3}, upper={5}`. Median = `(3+5)/2.0 = 4.0`.
3. `addNum(8)`: `8 > lower.peek()=3`, goes into `upper`. Sizes `lower=1, upper=2` — `upper.size() > lower.size()` (2 > 1), so move `upper.poll()=5` to `lower`. Now `lower={3,5}, upper={8}`. Median = `lower.peek()=5`.
4. This insert-then-rebalance cycle repeats for every new number, always leaving the heaps within 1 of each other in size.

## 7. Gotchas & takeaways

> Gotcha: using `else if` for the two rebalance conditions (instead of two independent `if` checks) is actually correct here, since only one of the two imbalance directions can ever occur after a single insertion — but writing BOTH as unconditional `if` statements is a common defensive habit that also works and guards against future edits that insert multiple elements at once.

- Always insert THEN rebalance — never rebalance before the new value has been placed in the correct initial heap.
- `Collections.reverseOrder()` for `lower` gives you the max-heap; the default `PriorityQueue<>()` constructor gives you the min-heap for `upper` — mixing these up silently breaks every operation.
- This exact template is the starting point for Find Median from Data Stream, IPO, and Furthest Building You Can Reach — the twist in each is what gets stored in the heap elements and what extra logic runs around the core insert/rebalance/query steps.
