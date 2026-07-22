---
card: leetcode-patterns
gi: 199
slug: find-right-interval
title: Find Right Interval
---

## 1. What it is

Given an array of `intervals` where `intervals[i] = [starti, endi]`, for each interval find the interval with the SMALLEST `start` that is `>= endi` (its "right interval"). Return an array of indices, using `-1` where no such interval exists. Example: `intervals = [[3,4],[2,3],[1,2]]` → `[-1,0,1]`.

## 2. Why & when

For each interval's end value, you need to find the smallest start value that is at least as large — a repeated "find the ceiling" query. A min-heap ordered by start value lets you repeatedly pop off candidates smaller than the current target, giving you direct access to the smallest qualifying start without a fresh scan each time.

## 3. Core concept

**Key idea:** push every interval's `[start, originalIndex]` pair into a min-heap ordered by `start`. Then, for each interval's `end` value (processed in SORTED order of `end`), repeatedly pop from the heap while its top's `start` is smaller than the current `end` — those popped starts can never be a valid answer for this or any LATER (larger) end value, so they are safe to discard. The heap's new top, if its start is `>= end`, is the answer.

**Steps:**
1. Build a min-heap of `[start, index]` pairs, one per interval, ordered by `start`.
2. Sort the intervals by `end` value, keeping track of each interval's original index.
3. For each interval in order of increasing `end`: while the heap's top has `start < end`, pop it (discard — it can never satisfy this or a larger future `end`).
4. After popping, if the heap is non-empty, its top's index is the answer for this interval; otherwise the answer is `-1`.
5. Because ends are processed in increasing order, POPPED elements are never needed again — this lets each heap element be pushed once and popped at most once across the whole run.

**Why it is correct:** processing `end` values in increasing order means any interval popped for being `< end` is also `<` every later, larger `end` — so discarding it permanently is safe. The heap's top, after discarding, is by definition the smallest `start` that is `>= end`, which is exactly the answer's requirement.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap of interval starts; ends processed in increasing order, discarding starts too small to matter again">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="160" y="64" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="220" cy="60" r="16" fill="#161b22" stroke="#e3b341"/><text x="220" y="64" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="10" y="15" fill="#e6edf3">min-heap of starts; pop while top &lt; current end -- popped starts never useful again since ends only grow</text>
  </g>
</svg>

The min-heap always exposes the smallest remaining start; values popped for being too small are safely discarded forever, since future `end`s only get larger.

## 5. Runnable example

```java
// FindRightInterval.java
import java.util.*;

public class FindRightInterval {

    // Level 1 -- Brute force: for each interval's end, binary search
    // (or linear scan) a separately sorted array of starts for the
    // ceiling. Correct and actually similarly efficient (O(n log n)),
    // but the heap version demonstrates the pattern's core idea:
    // discard-forever via increasing-order processing, which
    // generalizes to problems where a sorted array ceiling search
    // isn't as natural a fit.

    // KEY INSIGHT: process ends in SORTED order, so any heap element
    // popped for being too small can be discarded FOREVER -- it will
    // never be needed for a later (larger) end value either.

    // Level 2 -- Optimal: min-heap of starts, sorted ends, pop-and-
    // discard.
    static int[] findRightInterval(int[][] intervals) {
        int n = intervals.length;
        PriorityQueue<int[]> startHeap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        for (int i = 0; i < n; i++) {
            startHeap.add(new int[]{intervals[i][0], i});
        }

        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> intervals[a][1] - intervals[b][1]);

        int[] result = new int[n];
        for (int idx : order) {
            int end = intervals[idx][1];
            while (!startHeap.isEmpty() && startHeap.peek()[0] < end) {
                startHeap.poll();
            }
            result[idx] = startHeap.isEmpty() ? -1 : startHeap.peek()[1];
        }
        return result;
    }

    // Level 3 -- Hardened: intervals whose own start equals their own
    // end correctly find themselves as a valid right interval (start
    // >= end holds with equality), since the heap comparison uses
    // "<", not "<=", for the discard condition.

    public static void main(String[] args) {
        System.out.println(Arrays.toString(findRightInterval(new int[][]{{3,4},{2,3},{1,2}}))); // [-1, 0, 1]
        System.out.println(Arrays.toString(findRightInterval(new int[][]{{1,4},{2,3},{3,4}}))); // [-1, 2, -1]
    }
}
```

**How to run:** `java FindRightInterval.java`

## 6. Walkthrough

Trace `intervals = [[3,4],[2,3],[1,2]]` (indices 0,1,2), ends sorted order: index 2 (end=2), index 1 (end=3), index 0 (end=4):

| Step | Processing index | end | Pop while top.start < end | Heap top after popping | Answer |
|---|---|---|---|---|---|
| 1 | 2 | 2 | none (all starts 1,2,3 >= 2 initially, smallest is 1... wait 1 < 2) | pop start=1 (index 2); top becomes start=2 (index 1) | index 1 |
| 2 | 1 | 3 | pop start=2 (index 1); top becomes start=3 (index 0) | start=3 (index 0) | index 0 |
| 3 | 0 | 4 | pop start=3 (index 0); heap empty | — | -1 |

Result: `result[2]=1, result[1]=0, result[0]=-1` → `[-1, 0, 1]`. Time complexity is O(n log n), for building the heap and sorting, plus O(n log n) total across all pop operations (each element popped once); space is O(n) for the heap and order array.

## 7. Gotchas & takeaways

> Gotcha: popping elements permanently works ONLY because ends are processed in non-decreasing order — processing intervals in their ORIGINAL array order instead would incorrectly discard a start that a LATER (but smaller) end value still needed.

- Store the original index alongside each start/end value — after sorting or heap operations reorder things, you need to know which answer slot to fill.
- This "process queries in sorted order, discard-forever from a heap" idea also appears outside interval problems, whenever a threshold only ever grows across the queries.
- Related problems: Furthest Building You Can Reach (heap discards used ladders permanently), Meeting Rooms II (min-heap of end times, similar discard-when-freed logic).
