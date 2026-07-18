---
card: leetcode-patterns
gi: 66
slug: merge-intervals-signal-overlapping-intervals-or-scheduling
title: Merge Intervals — signal: overlapping intervals or scheduling
---

## 1. What it is

Merge Intervals is a technique for problems that give you a collection of ranges — each with a start and an end — and ask you to combine, compare, or reason about how they overlap. An interval `[a, b]` covers every point from `a` to `b`. Two intervals overlap when one starts before the other ends.

## 2. Why & when

Checking every pair of intervals for overlap directly costs O(n²), since there are O(n²) pairs to compare. Sorting the intervals first by their start time turns the problem into a single left-to-right scan, because once sorted, an interval can only overlap with the ones immediately around it — not with distant ones.

Learn to recognize these signals in a problem statement:

- **"Merge overlapping intervals"** or **"combine ranges that overlap."**
- **"Insert a new interval"** into an already-sorted list of non-overlapping intervals.
- **Scheduling language:** "meeting rooms," "can a person attend all meetings," "minimum rooms needed."
- **"Do these intervals overlap?"** or **"find the intersection"** between two lists of intervals.
- **A list of `[start, end]` pairs** where the question depends on their relative positions, not their individual values.

The alternative is a brute-force pairwise comparison (O(n²)) or, for problems needing to track many simultaneous intervals, a heap or sweep line if simple sorting is not enough. Merge Intervals is the answer when sorting by start (or by start and end together) exposes the structure needed to solve the problem in one pass.

## 3. Core concept

**Key idea:** sort intervals by start time. Then scan left to right, keeping a "current" merged interval. If the next interval's start is less than or equal to the current interval's end, they overlap — extend the current interval's end. Otherwise, the current interval is finished — save it and start a new one.

**Steps:**
1. Sort the intervals by their start value.
2. Initialize `current` to the first interval.
3. For each subsequent interval `next`:
   - If `next.start <= current.end`, they overlap: set `current.end = max(current.end, next.end)`.
   - Otherwise, `current` is finalized (add it to the result); set `current = next`.
4. Add the final `current` to the result after the loop.

**Why it works:** once sorted by start, any interval that could possibly overlap with `current` must appear immediately next in the scan — an interval appearing later has a start time at or after all intervals already processed, so if it does not overlap the current merged range, no later interval will either (their starts only get larger).

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merging overlapping intervals after sorting by start">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals = [1,3], [2,6], [8,10], [15,18] (already sorted by start)</text>
    <rect x="20" y="45" width="80" height="20" fill="#161b22" stroke="#79c0ff"/><text x="60" y="60" fill="#e6edf3" text-anchor="middle" font-size="10">[1,3]</text>
    <rect x="60" y="70" width="160" height="20" fill="#161b22" stroke="#79c0ff"/><text x="140" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[2,6]</text>
    <rect x="20" y="100" width="200" height="18" fill="#161b22" stroke="#3fb950" stroke-dasharray="3,2"/><text x="120" y="113" fill="#3fb950" text-anchor="middle" font-size="10">merged [1,6]</text>
    <rect x="260" y="70" width="80" height="20" fill="#161b22" stroke="#f0883e"/><text x="300" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[8,10] no overlap, new group</text>
    <rect x="440" y="70" width="90" height="20" fill="#161b22" stroke="#f0883e"/><text x="485" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[15,18] no overlap</text>
    <text x="20" y="160" fill="#8b949e">[1,3] and [2,6] overlap (2 &lt;= 3) -&gt; merge into [1,6]; [8,10] starts after 6 -&gt; new group</text>
  </g>
</svg>

Sorting first means only adjacent intervals in the scan can possibly overlap, turning an O(n²) pairwise check into a single O(n) pass.

## 5. Runnable example

A generic "merge overlapping intervals" skeleton you can adapt to related problems in this pattern.

```java
// MergeIntervalsSignal.java
import java.util.*;

public class MergeIntervalsSignal {

    static int[][] mergeOverlapping(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> result = new ArrayList<>();
        int[] current = intervals[0];
        for (int i = 1; i < intervals.length; i++) {
            int[] next = intervals[i];
            if (next[0] <= current[1]) {
                current[1] = Math.max(current[1], next[1]);
            } else {
                result.add(current);
                current = next;
            }
        }
        result.add(current);
        return result.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        int[][] intervals = {{1, 3}, {2, 6}, {8, 10}, {15, 18}};
        int[][] merged = mergeOverlapping(intervals);
        for (int[] iv : merged) System.out.println(Arrays.toString(iv));
    }
}
```

How to run: save as `MergeIntervalsSignal.java`, then run `java MergeIntervalsSignal.java`.

## 6. Walkthrough

1. Sort `[[1,3],[2,6],[8,10],[15,18]]` by start — already sorted.
2. `current = [1,3]`. Next is `[2,6]`: `2 <= 3`, so overlap — `current` becomes `[1,6]`.
3. Next is `[8,10]`: `8 <= 6` is false — no overlap. Save `[1,6]` to the result. `current = [8,10]`.
4. Next is `[15,18]`: `15 <= 10` is false — no overlap. Save `[8,10]`. `current = [15,18]`.
5. Loop ends. Save the final `current = [15,18]`. Result: `[[1,6],[8,10],[15,18]]`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to sort the intervals first — the merge logic silently produces wrong results on unsorted input, since it assumes any overlap can only happen with the immediately preceding interval.

- Sorting costs O(n log n), which dominates the overall time complexity — the merge scan itself is only O(n).
- Watch for whether overlap is defined with `<=` or `<` at the boundary (does `[1,3]` and `[3,5]` count as overlapping, or just touching?) — read the problem statement carefully.
