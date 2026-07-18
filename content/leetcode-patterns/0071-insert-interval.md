---
card: leetcode-patterns
gi: 71
slug: insert-interval
title: Insert Interval
---

## 1. What it is

Given a list of non-overlapping intervals sorted by start time, and a new interval, insert the new interval into the list, merging any overlaps, and return the resulting sorted, non-overlapping list. Example: `intervals = [[1,3],[6,9]]`, `newInterval = [2,5]` → `[[1,5],[6,9]]`.

## 2. Why & when

You could append the new interval to the list and re-run the full Merge Intervals algorithm, including a full re-sort — but that wastes the fact that the existing list is already sorted and merged. This problem's real signal is: exploit the "already sorted" special case from the complexity page, and only pay for what actually changes.

## 3. Core concept

**Key idea:** split the scan into three phases, since the existing intervals are already sorted: intervals that end entirely before the new interval starts (no overlap, copy as-is), intervals that overlap the new interval (absorb them into it, expanding its bounds), and intervals that start entirely after the new interval ends (no overlap, copy as-is).

**Steps:**
1. Phase 1: while the current interval's end is less than `newInterval.start`, it cannot overlap — add it to the result directly, advance.
2. Phase 2: while the current interval's start is less than or equal to `newInterval.end`, it overlaps — expand `newInterval` to `[min(starts), max(ends)]`, advance.
3. Add the (possibly expanded) `newInterval` to the result.
4. Phase 3: add all remaining intervals directly — they start after `newInterval` ends.

**Why it is correct:** because the input is already sorted and non-overlapping, "does this interval overlap the new one" only flips from false to true once, and then from true to false once — exactly the three phases above, each requiring only one linear pass with no backtracking.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting and merging a new interval into a sorted list">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals = [1,3], [6,9]; newInterval = [2,5]</text>
    <rect x="20" y="45" width="60" height="20" fill="#161b22" stroke="#30363d"/><text x="50" y="60" fill="#8b949e" text-anchor="middle" font-size="10">[1,3]</text>
    <rect x="80" y="70" width="90" height="20" fill="#161b22" stroke="#f0883e"/><text x="125" y="85" fill="#f0883e" text-anchor="middle" font-size="10">new [2,5]</text>
    <rect x="220" y="45" width="90" height="20" fill="#161b22" stroke="#30363d"/><text x="265" y="60" fill="#8b949e" text-anchor="middle" font-size="10">[6,9]</text>
    <rect x="20" y="100" width="150" height="18" fill="none" stroke="#3fb950" stroke-dasharray="4,2"/><text x="95" y="113" fill="#3fb950" text-anchor="middle" font-size="10">merged [1,5]</text>
    <text x="20" y="150" fill="#8b949e">result: [[1,5], [6,9]] -- [1,3] and [2,5] overlap and merge; [6,9] is untouched</text>
  </g>
</svg>

`[1,3]` overlaps the new interval `[2,5]` and merges into it; `[6,9]` starts after the merged range ends, so it is copied through unchanged.

## 5. Runnable example

```java
// InsertInterval.java
import java.util.*;

public class InsertInterval {

    // Level 1 -- Brute force: append the new interval, then run the full
    // general Merge Intervals algorithm (sort + scan). O(n log n) time --
    // wastes a sort on data that was already sorted.
    static int[][] bruteForce(int[][] intervals, int[] newInterval) {
        List<int[]> all = new ArrayList<>(Arrays.asList(intervals));
        all.add(newInterval);
        int[][] arr = all.toArray(new int[0][]);
        Arrays.sort(arr, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> result = new ArrayList<>();
        int[] current = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i][0] <= current[1]) current[1] = Math.max(current[1], arr[i][1]);
            else { result.add(current); current = arr[i]; }
        }
        result.add(current);
        return result.toArray(new int[0][]);
    }

    // KEY INSIGHT: since the input is already sorted and non-overlapping,
    // "overlaps the new interval" flips from false to true exactly once
    // and back to false exactly once -- three linear phases, no sort.

    // Level 2 -- Optimal: three-phase single pass. O(n) time, O(n) space.
    public static int[][] insert(int[][] intervals, int[] newInterval) {
        List<int[]> result = new ArrayList<>();
        int i = 0, n = intervals.length;

        while (i < n && intervals[i][1] < newInterval[0]) {
            result.add(intervals[i]);
            i++;
        }

        int start = newInterval[0], end = newInterval[1];
        while (i < n && intervals[i][0] <= end) {
            start = Math.min(start, intervals[i][0]);
            end = Math.max(end, intervals[i][1]);
            i++;
        }
        result.add(new int[] {start, end});

        while (i < n) {
            result.add(intervals[i]);
            i++;
        }
        return result.toArray(new int[0][]);
    }

    // Level 3 -- Hardened: new interval that overlaps nothing (inserted
    // in the correct sorted position), and an empty starting list.
    static int[][] hardened(int[][] intervals, int[] newInterval) {
        return insert(intervals, newInterval);
    }

    public static void main(String[] args) {
        int[][] a = {{1, 3}, {6, 9}};
        int[] newA = {2, 5};
        System.out.println("brute force: " + Arrays.deepToString(bruteForce(a, newA)));
        System.out.println("optimal:     " + Arrays.deepToString(insert(a, newA)));

        int[][] noOverlap = {{1, 2}, {7, 9}};
        int[] middle = {4, 5};
        System.out.println("no overlap:  " + Arrays.deepToString(hardened(noOverlap, middle)));

        System.out.println("empty list:  " + Arrays.deepToString(hardened(new int[0][], new int[] {5, 7})));
    }
}
```

How to run: save as `InsertInterval.java`, then run `java InsertInterval.java`.

## 6. Walkthrough

Dry run of `insert([[1,3],[6,9]], [2,5])`:

1. **Phase 1:** `intervals[0] = [1,3]`, end `3 < newInterval.start (2)`? No (`3 >= 2`). Phase 1 adds nothing; `i` stays `0`.
2. **Phase 2:** `intervals[0].start (1) <= newInterval.end (5)`? Yes — merge: `start = min(2,1) = 1`, `end = max(5,3) = 5`. Advance `i = 1`. Check `intervals[1] = [6,9]`: `start (6) <= end (5)`? No — stop phase 2.
3. Add the merged interval `[1, 5]` to the result.
4. **Phase 3:** add remaining `intervals[1] = [6,9]` directly.
5. Result: `[[1,5],[6,9]]`.

Time complexity: O(n), one linear pass with no sort needed. Space complexity: O(n) for the result.

## 7. Gotchas & takeaways

> Gotcha: using `<` instead of `<=` in the phase-2 overlap check (`intervals[i][0] <= end`) misses the boundary case where an existing interval starts exactly where the new interval ends — e.g. `[6,9]` and `newInterval=[2,6]` should merge into `[2,9]`, not stay separate.

- The three-phase pattern (before / overlapping / after) is a useful decomposition whenever new data must merge into an already-sorted, already-merged structure — avoid re-sorting when you can exploit existing order.
- Related problems: Merge Intervals (the general, non-incremental version), Employee Free Time (also merges across already-sorted schedules).
