---
card: leetcode-patterns
gi: 205
slug: sliding-window-median
title: Sliding Window Median
---

## 1. What it is

Given an array `nums` and window size `k`, return the median of each contiguous window of size `k` as it slides from the start of the array to the end. Example: `nums = [1,3,-1,-3,5,3,6,7]`, `k = 3` → `[1,-1,-1,3,5,6]`.

## 2. Why & when

This extends Find Median from Data Stream with a REMOVAL requirement: as the window slides, the oldest element must leave. Standard heaps do not support efficient removal of an arbitrary element, so this needs "lazy deletion" — mark an element as removed, and only actually clean it out when it surfaces at the top of a heap.

## 3. Core concept

**Key idea:** keep the same two-heaps structure (`lower` max-heap, `upper` min-heap) as the streaming median problem, but add a hash map counting how many times each value is PENDING removal. When a value needs to leave the window, increment its pending-removal count instead of searching the heap for it. Before trusting any heap's top (for a median read or a rebalance decision), first "clean" that heap: pop and discard any top value that still has a pending removal count, decrementing the count each time.

**Steps:**
1. Slide a window of size `k` across `nums`. For each new element entering, insert it into the appropriate heap using the standard two-heaps insert rule, then rebalance.
2. For the element LEAVING the window (once the window is full and moving), increment its count in a `pendingRemoval` map, and adjust a size counter for whichever heap it logically belongs to (based on its value relative to the current split).
3. Before reading `findMedian()`, or before comparing heap tops during rebalancing, call a "prune" helper: while a heap's top has a positive pending-removal count, pop it and decrement the count.
4. Track EFFECTIVE sizes of `lower` and `upper` (excluding pending removals) separately from the heaps' raw sizes, since raw sizes include stale entries not yet popped.
5. Read the median using effective sizes and the pruned tops, exactly like the streaming version.

**Why it is correct:** lazy deletion defers the cost of removing an arbitrary element until it would actually affect an operation's correctness (a top read or a rebalance) — at that point, the stale value is guaranteed to be at the top of ITS heap eventually (since heaps only expose their extreme value), so pruning tops as needed correctly simulates true removal without a full heap search.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Element leaving the window is lazily marked for removal, cleaned from a heap only when it reaches the top">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#f85149"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle">3*</text>
    <circle cx="160" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="160" y="64" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="10" y="15" fill="#e6edf3">3* is marked for removal but stays in the heap until it surfaces at the top -- then it's popped and discarded</text>
  </g>
</svg>

A value marked for lazy removal (`3*`) stays physically in the heap until it happens to rise to the top, at which point it is popped and discarded instead of read.

## 5. Runnable example

```java
// SlidingWindowMedian.java
import java.util.*;

public class SlidingWindowMedian {

    // Level 1 -- Brute force: for each window position, copy the k
    // elements into a fresh array, sort it, and read the median.
    // Correct, but O(n * k log k) total -- resorting from scratch for
    // every single window slide.

    // KEY INSIGHT: reuse the two-heaps structure across window slides,
    // using LAZY DELETION for the element leaving the window -- avoid
    // an expensive heap search by only cleaning stale tops when they
    // would actually be read.

    // Level 2 -- Optimal: two heaps + lazy deletion via a pending-
    // removal count map.
    private PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());
    private PriorityQueue<Integer> upper = new PriorityQueue<>();
    private Map<Integer, Integer> pending = new HashMap<>();
    private int lowerSize = 0, upperSize = 0;

    static double[] medianSlidingWindow(int[] nums, int k) {
        SlidingWindowMedian sw = new SlidingWindowMedian();
        double[] result = new double[nums.length - k + 1];
        for (int i = 0; i < nums.length; i++) {
            sw.add(nums[i]);
            if (i >= k) sw.remove(nums[i - k]);
            if (i >= k - 1) result[i - k + 1] = sw.median();
        }
        return result;
    }

    void add(int num) {
        if (lower.isEmpty() || num <= lower.peek()) { lower.add(num); lowerSize++; }
        else { upper.add(num); upperSize++; }
        rebalance();
    }

    void remove(int num) {
        pending.merge(num, 1, Integer::sum);
        if (!lower.isEmpty() && num <= lower.peek()) lowerSize--;
        else upperSize--;
        prune(lower);
        prune(upper);
        rebalance();
    }

    void prune(PriorityQueue<Integer> heap) {
        while (!heap.isEmpty() && pending.getOrDefault(heap.peek(), 0) > 0) {
            pending.merge(heap.peek(), -1, Integer::sum);
            heap.poll();
        }
    }

    void rebalance() {
        if (lowerSize > upperSize + 1) {
            upper.add(lower.poll()); lowerSize--; upperSize++;
            prune(lower);
        } else if (upperSize > lowerSize) {
            lower.add(upper.poll()); upperSize--; lowerSize++;
            prune(upper);
        }
    }

    double median() {
        prune(lower); prune(upper);
        if (lowerSize == upperSize) return ((long) lower.peek() + upper.peek()) / 2.0;
        return lower.peek();
    }

    // Level 3 -- Hardened: `((long) lower.peek() + upper.peek())`
    // avoids integer overflow when averaging two large int values, and
    // pruning happens before EVERY top read, not just once at setup.

    public static void main(String[] args) {
        System.out.println(Arrays.toString(medianSlidingWindow(new int[]{1,3,-1,-3,5,3,6,7}, 3)));
        // [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
    }
}
```

**How to run:** `java SlidingWindowMedian.java`

## 6. Walkthrough

Trace the window sliding from `[1,3,-1]` (median 1) to `[3,-1,-3]` (median -1):

| Step | Action | lower (effective) | upper (effective) |
|---|---|---|---|
| window full | {1,3,-1} | lower={1,-1}(2) | upper={3}(1) → median=1 |
| slide: add 3(dup value, treated by comparison rule), remove 1 | mark 1 pending | prune finds 1 not yet at top; rebalance may surface it later | — |
| after prune during median() | stale 1 popped when it reaches lower's top | lower={-1}(1) | upper={3,3}(2) → rebalance moves one 3 to lower |

Final state for window `[3,-1,-3]`: median = `-1`, matching the expected output. Time complexity is O(n log k), since each of the n elements triggers a bounded number of O(log k) heap operations; space is O(k) for the heaps and pending map.

## 7. Gotchas & takeaways

> Gotcha: forgetting to prune BOTH heaps (not just the one being read) before a rebalance step can move a stale, pending-removal value from one heap into the other, where it then incorrectly blocks a later prune from working (since the size bookkeeping assumed it was already accounted for).

- Track `lowerSize`/`upperSize` (effective, excluding pending removals) SEPARATELY from `heap.size()` (raw, includes stale entries) — mixing these up breaks every size comparison.
- Cast to `long` before averaging two `int` medians — `nums` values can be large enough that their sum overflows a 32-bit `int`.
- Related problems: Find Median from Data Stream (identical two-heaps core, no removal needed), Sliding Window Maximum (a different technique, monotonic deque, for a different sliding-window statistic).
