---
card: leetcode-patterns
gi: 79
slug: remove-covered-intervals
title: Remove Covered Intervals
---

## 1. What it is

Given an array of intervals, remove all intervals that are covered by another interval in the list. Interval `[a, b]` is covered by `[c, d]` if `c <= a` and `b <= d`. Return the number of remaining intervals after removing all covered ones. Example: `intervals = [[1,4],[3,6],[2,8]]` → `2` (`[3,6]` is covered by `[2,8]`, since `2 <= 3` and `6 <= 8`).

## 2. Why & when

Checking every pair of intervals for coverage directly costs O(n²). Sorting by start ascending, and by end descending on ties, arranges the intervals so that any interval covering another must appear *before* it in the scan — turning pairwise coverage checks into a single pass that only compares each interval against the widest one seen so far.

## 3. Core concept

**Key idea:** sort intervals by start ascending; break ties by sorting end descending, so that when two intervals share a start, the wider one comes first (and therefore covers the narrower one automatically). Then scan left to right, tracking the maximum end seen among kept intervals. An interval is covered if its end is less than or equal to that running maximum end, since its start is already guaranteed to be at or after the covering interval's start.

**Steps:**
1. Sort `intervals` by `start` ascending; for ties, sort by `end` descending.
2. Set `count = 0`, `maxEnd = -infinity` (or the smallest possible value).
3. For each interval in sorted order:
   - If `interval.end > maxEnd`, it is not covered by anything seen so far — count it: `count++`, update `maxEnd = interval.end`.
   - Otherwise, it is covered — skip it.
4. Return `count`.

**Why it is correct:** after sorting, every interval considered so far has a start at or before the current interval's start. So the current interval is covered exactly when its end does not exceed the largest end seen so far — a smaller or equal end, combined with a later-or-equal start, is the definition of coverage. The end-descending tie-break ensures a same-start pair is handled correctly, since the wider one is processed first and immediately sets `maxEnd` high enough to correctly mark the narrower one as covered.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sorted intervals showing one covered by another">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">sorted: [1,4], [2,8], [3,6]</text>
    <rect x="20" y="45" width="60" height="20" fill="#161b22" stroke="#79c0ff"/><text x="50" y="60" fill="#e6edf3" text-anchor="middle" font-size="10">[1,4] keep, maxEnd=4</text>
    <rect x="40" y="70" width="120" height="20" fill="#161b22" stroke="#79c0ff"/><text x="100" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[2,8] keep, maxEnd=8</text>
    <rect x="60" y="95" width="60" height="20" fill="#161b22" stroke="#f0883e" stroke-dasharray="3,2"/><text x="90" y="110" fill="#f0883e" text-anchor="middle" font-size="10">[3,6] covered (6&lt;=8)</text>
    <text x="20" y="150" fill="#8b949e">result: 2 intervals remain ([1,4] and [2,8])</text>
  </g>
</svg>

`[3,6]`'s end (`6`) does not exceed the running `maxEnd` (`8`) set by `[2,8]`, and its start (`3`) is already at or after `[2,8]`'s start — so it is fully covered and removed.

## 5. Runnable example

```java
// RemoveCoveredIntervals.java
import java.util.*;

public class RemoveCoveredIntervals {

    // Level 1 -- Brute force: check every pair for coverage directly.
    // O(n^2) time -- wastes comparisons that sorting could avoid.
    static int bruteForce(int[][] intervals) {
        int n = intervals.length;
        boolean[] covered = new boolean[n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i == j) continue;
                if (intervals[j][0] <= intervals[i][0] && intervals[i][1] <= intervals[j][1]
                        && (intervals[j][0] != intervals[i][0] || intervals[j][1] != intervals[i][1] || j < i)) {
                    covered[i] = true;
                }
            }
        }
        int count = 0;
        for (boolean c : covered) if (!c) count++;
        return count;
    }

    // KEY INSIGHT: sorting by start ascending, end descending on ties,
    // guarantees any interval that could cover another appears FIRST in
    // the scan -- so tracking only the running max end detects coverage
    // in one linear pass.

    // Level 2 -- Optimal: sort, then single pass tracking max end.
    // O(n log n) time, O(1) extra space.
    public static int removeCoveredIntervals(int[][] intervals) {
        Arrays.sort(intervals, (a, b) ->
            a[0] != b[0] ? a[0] - b[0] : b[1] - a[1]);

        int count = 0;
        int maxEnd = Integer.MIN_VALUE;
        for (int[] iv : intervals) {
            if (iv[1] > maxEnd) {
                count++;
                maxEnd = iv[1];
            }
        }
        return count;
    }

    // Level 3 -- Hardened: two intervals with identical bounds (each
    // covers the other, but only one should be counted, handled by the
    // end-descending tie-break processing the "wider" one first).
    static int hardened(int[][] intervals) {
        return removeCoveredIntervals(intervals);
    }

    public static void main(String[] args) {
        int[][] a = {{1, 4}, {3, 6}, {2, 8}};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + removeCoveredIntervals(a));

        int[][] identical = {{1, 5}, {1, 5}};
        System.out.println("identical (expect 1): " + hardened(identical));
    }
}
```

How to run: save as `RemoveCoveredIntervals.java`, then run `java RemoveCoveredIntervals.java`.

## 6. Walkthrough

Dry run of `removeCoveredIntervals` on sorted `[[1,4],[2,8],[3,6]]`:

| step | interval | end > maxEnd? | action | maxEnd |
|---|---|---|---|---|
| 1 | [1,4] | 4 > -inf | count=1 | 4 |
| 2 | [2,8] | 8 > 4 | count=2 | 8 |
| 3 | [3,6] | 6 > 8? no | covered, skip | 8 |

Result: `count = 2`. Time complexity: O(n log n), dominated by the sort. Space complexity: O(1) extra space.

## 7. Gotchas & takeaways

> Gotcha: sorting by end *ascending* on ties (instead of descending) can cause a narrower interval sharing the same start as a wider one to be counted before the wider one is seen, incorrectly marking the wider one as "not covering" anything, since `maxEnd` would not yet reflect the wider interval's true end.

- The tie-break rule (`end descending` when `start` matches) is the subtle part of this problem — without it, same-start intervals are compared in the wrong order.
- Related problems: Merge Intervals (combines overlaps instead of removing subsets), Non-overlapping Intervals (removes for a different reason — to eliminate overlap, not containment).
