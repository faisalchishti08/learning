---
card: leetcode-patterns
gi: 72
slug: non-overlapping-intervals
title: Non-overlapping Intervals
---

## 1. What it is

Given an array of intervals, find the minimum number of intervals you must remove so that the rest do not overlap. Example: `intervals = [[1,2],[2,3],[3,4],[1,3]]` → `1` (removing `[1,3]` leaves `[1,2],[2,3],[3,4]`, which do not overlap).

## 2. Why & when

This looks like a merge problem, but it is really a variant of the classic "activity selection" greedy problem. Instead of merging overlaps, you must choose which intervals to *keep* so that as many as possible survive without overlapping — the removals are just the leftovers. Sorting by end time (not start time) is the key twist that separates this problem from ordinary interval merging.

## 3. Core concept

**Key idea:** sort intervals by their end value. Greedily keep an interval if it starts at or after the end of the last interval you kept. Every interval that cannot be kept must be removed.

**Steps:**
1. Sort `intervals` by `end` ascending.
2. Set `lastEnd = intervals[0].end`, `removed = 0`, having kept `intervals[0]`.
3. For each subsequent interval:
   - If `interval.start < lastEnd`, it overlaps the last kept interval — remove it: `removed++`.
   - Otherwise, keep it: `lastEnd = interval.end`.
4. Return `removed`.

**Why it is correct:** sorting by end time means the interval that finishes earliest always leaves the most room for future intervals to fit without overlapping. Greedily always keeping the earliest-finishing available interval is provably optimal — any other choice can only finish later, which can never allow strictly more future intervals to be kept.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Greedy interval selection sorted by end time">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals sorted by end: [1,2], [2,3], [1,3], [3,4]</text>
    <rect x="20" y="45" width="40" height="20" fill="#161b22" stroke="#3fb950"/><text x="40" y="60" fill="#3fb950" text-anchor="middle" font-size="10">[1,2] keep</text>
    <rect x="60" y="70" width="40" height="20" fill="#161b22" stroke="#3fb950"/><text x="80" y="85" fill="#3fb950" text-anchor="middle" font-size="10">[2,3] keep</text>
    <rect x="20" y="95" width="80" height="20" fill="#161b22" stroke="#f0883e"/><text x="60" y="110" fill="#f0883e" text-anchor="middle" font-size="10">[1,3] REMOVE (starts before lastEnd=3)</text>
    <rect x="100" y="70" width="40" height="20" fill="#161b22" stroke="#3fb950"/><text x="120" y="60" fill="#3fb950" text-anchor="middle" font-size="10">[3,4] keep</text>
    <text x="20" y="150" fill="#8b949e">kept: [1,2],[2,3],[3,4] -- removed: 1 interval ([1,3])</text>
  </g>
</svg>

Sorting by end value and greedily keeping the earliest-finishing non-overlapping interval identifies `[1,3]` as the one interval that must go.

## 5. Runnable example

```java
// NonOverlappingIntervals.java
import java.util.*;

public class NonOverlappingIntervals {

    // Level 1 -- Brute force: try all subsets, check which are fully
    // non-overlapping, find the largest kept subset. O(2^n) time --
    // completely infeasible beyond tiny inputs.
    static int bruteForce(int[][] intervals) {
        int n = intervals.length;
        int best = 0;
        for (int mask = 0; mask < (1 << n); mask++) {
            List<int[]> subset = new ArrayList<>();
            for (int i = 0; i < n; i++) if ((mask & (1 << i)) != 0) subset.add(intervals[i]);
            if (isNonOverlapping(subset)) best = Math.max(best, subset.size());
        }
        return n - best;
    }

    static boolean isNonOverlapping(List<int[]> list) {
        list.sort((a, b) -> Integer.compare(a[0], b[0]));
        for (int i = 1; i < list.size(); i++) {
            if (list.get(i)[0] < list.get(i - 1)[1]) return false;
        }
        return true;
    }

    // KEY INSIGHT: sorting by END time and greedily keeping the
    // earliest-finishing interval available always leaves the most room
    // for future intervals -- so counting overlaps directly gives the
    // minimum removals, no subset search needed.

    // Level 2 -- Optimal: greedy, sorted by end. O(n log n) time,
    // O(1) extra space (excluding the sort).
    public static int eraseOverlapIntervals(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[1], b[1]));
        int removed = 0;
        int lastEnd = intervals[0][1];
        for (int i = 1; i < intervals.length; i++) {
            if (intervals[i][0] < lastEnd) {
                removed++;
            } else {
                lastEnd = intervals[i][1];
            }
        }
        return removed;
    }

    // Level 3 -- Hardened: intervals that touch exactly at the boundary
    // (e.g. [1,2] and [2,3]) do NOT count as overlapping, since a
    // strict "<" comparison is used for the start-vs-lastEnd check.
    static int hardened(int[][] intervals) {
        return eraseOverlapIntervals(intervals);
    }

    public static void main(String[] args) {
        int[][] a = {{1, 2}, {2, 3}, {3, 4}, {1, 3}};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + eraseOverlapIntervals(a));

        int[][] touching = {{1, 2}, {2, 3}};
        System.out.println("touching (expect 0): " + hardened(touching));
    }
}
```

How to run: save as `NonOverlappingIntervals.java`, then run `java NonOverlappingIntervals.java`.

## 6. Walkthrough

Dry run of `eraseOverlapIntervals` on intervals sorted by end: `[[1,2],[2,3],[1,3],[3,4]]`:

| step | interval | start < lastEnd? | action | lastEnd |
|---|---|---|---|---|
| start | [1,2] kept | — | initial keep | 2 |
| 1 | [2,3] | 2 < 2? no | keep | 3 |
| 2 | [1,3] | 1 < 3? yes | remove (removed=1) | 3 (unchanged) |
| 3 | [3,4] | 3 < 3? no | keep | 4 |

Result: `removed = 1`. Time complexity: O(n log n), dominated by the sort. Space complexity: O(1) extra space.

## 7. Gotchas & takeaways

> Gotcha: sorting by *start* time instead of *end* time breaks the greedy proof — the earliest-starting interval is not necessarily the one that leaves the most room for the rest, since it might also be the longest.

- This problem is the "keep the maximum, count the leftovers" twin of Merge Intervals — same sort-then-scan shape, opposite goal.
- Related problems: Minimum Number of Arrows to Burst Balloons (identical greedy idea, sorted by end, just phrased as counting groups instead of removals), Meeting Rooms II.
