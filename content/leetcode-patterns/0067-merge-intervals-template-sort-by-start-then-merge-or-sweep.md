---
card: leetcode-patterns
gi: 67
slug: merge-intervals-template-sort-by-start-then-merge-or-sweep
title: Merge Intervals — template: sort by start, then merge or sweep
---

## 1. What it is

This page gives the two reusable code shapes for the Merge Intervals pattern: the **merge template** (combine overlapping intervals into fewer, wider ones) and the **sweep-line template** (count how many intervals are active at each point in time, useful for scheduling problems).

## 2. Why & when

Most problems in this pattern reduce to one of these two shapes. If the question asks you to combine or list overlapping ranges, use the merge template. If the question asks "how many things are happening at once" (like meeting rooms needed), use the sweep-line template, which turns each interval into two events — a start and an end — and scans those events in time order.

## 3. Core concept

**Merge template (from the previous page):**
1. Sort intervals by start.
2. Scan left to right, extending the current interval's end whenever the next interval overlaps, otherwise starting a new group.

**Sweep-line template:**
1. Convert each interval `[start, end]` into two events: `(start, +1)` and `(end, -1)`.
2. Sort all events by time; break ties by processing `-1` (end) events before `+1` (start) events at the same timestamp, when a meeting ending exactly as another starts should not count as an overlap.
3. Scan the sorted events, maintaining a running counter. Add `+1` or `-1` at each event. Track the maximum value the counter reaches — that is the peak number of simultaneous intervals.

**Why both work:** the merge template exploits the fact that sorted starts make overlaps detectable in one pass. The sweep-line template exploits the fact that "how many intervals cover this moment" only changes at interval boundaries, so you only need to examine those boundary points, not every possible moment in time.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sweep line counting active intervals over time">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals: [0,30], [5,10], [15,20] -&gt; events: (0,+1)(5,+1)(10,-1)(15,+1)(20,-1)(30,-1)</text>
    <line x1="20" y1="100" x2="600" y2="100" stroke="#30363d"/>
    <circle cx="40" cy="100" r="4" fill="#3fb950"/><text x="40" y="120" fill="#8b949e" font-size="10">0:+1</text>
    <circle cx="140" cy="100" r="4" fill="#3fb950"/><text x="140" y="120" fill="#8b949e" font-size="10">5:+1</text>
    <circle cx="240" cy="100" r="4" fill="#f0883e"/><text x="240" y="120" fill="#8b949e" font-size="10">10:-1</text>
    <circle cx="340" cy="100" r="4" fill="#3fb950"/><text x="340" y="120" fill="#8b949e" font-size="10">15:+1</text>
    <circle cx="440" cy="100" r="4" fill="#f0883e"/><text x="440" y="120" fill="#8b949e" font-size="10">20:-1</text>
    <circle cx="580" cy="100" r="4" fill="#f0883e"/><text x="580" y="120" fill="#8b949e" font-size="10">30:-1</text>
    <text x="20" y="70" fill="#8b949e">running count: 1, 2, 1, 2, 1, 0 -&gt; peak = 2 simultaneous intervals</text>
  </g>
</svg>

Sweeping through start/end events in time order tracks how many intervals overlap at once without ever examining a non-boundary moment.

## 5. Runnable example

```java
// MergeIntervalsTemplate.java
import java.util.*;

public class MergeIntervalsTemplate {

    // Template 1: merge overlapping intervals.
    static int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> result = new ArrayList<>();
        int[] current = intervals[0];
        for (int i = 1; i < intervals.length; i++) {
            if (intervals[i][0] <= current[1]) {
                current[1] = Math.max(current[1], intervals[i][1]);
            } else {
                result.add(current);
                current = intervals[i];
            }
        }
        result.add(current);
        return result.toArray(new int[0][]);
    }

    // Template 2: sweep line -- peak number of simultaneously active
    // intervals (e.g. minimum meeting rooms needed).
    static int peakOverlap(int[][] intervals) {
        int n = intervals.length;
        int[][] events = new int[2 * n][2]; // [time, delta]
        for (int i = 0; i < n; i++) {
            events[2 * i] = new int[] {intervals[i][0], 1};
            events[2 * i + 1] = new int[] {intervals[i][1], -1};
        }
        Arrays.sort(events, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);
        int running = 0, peak = 0;
        for (int[] e : events) {
            running += e[1];
            peak = Math.max(peak, running);
        }
        return peak;
    }

    public static void main(String[] args) {
        int[][] toMerge = {{1, 3}, {2, 6}, {8, 10}};
        for (int[] iv : merge(toMerge)) System.out.println(Arrays.toString(iv));

        int[][] meetings = {{0, 30}, {5, 10}, {15, 20}};
        System.out.println("peak overlap (rooms needed): " + peakOverlap(meetings));
    }
}
```

How to run: save as `MergeIntervalsTemplate.java`, then run `java MergeIntervalsTemplate.java`.

## 6. Walkthrough

Trace `peakOverlap` on `[[0,30],[5,10],[15,20]]`:

1. Events sorted by time: `(0,+1), (5,+1), (10,-1), (15,+1), (20,-1), (30,-1)`.
2. Running count after each event: `1, 2, 1, 2, 1, 0`.
3. Peak value reached: `2` — at most two meetings ever overlap at the same instant, so two rooms are needed.

## 7. Gotchas & takeaways

> Gotcha: sorting tied timestamps with `+1` before `-1` (instead of `-1` first) counts a meeting ending at time `10` and another starting at time `10` as overlapping, which is wrong when a room becomes free exactly as the next meeting begins.

- Pick the merge template when the answer is "the merged ranges themselves"; pick the sweep-line template when the answer is "a count of how many overlap at once."
- Both templates depend on sorting first — O(n log n) is the time floor for any Merge Intervals problem.
