---
card: leetcode-patterns
gi: 70
slug: merge-intervals
title: Merge Intervals
---

## 1. What it is

Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals and return the smallest array of non-overlapping intervals that covers all the intervals in the input. Example: `intervals = [[1,3],[2,6],[8,10],[15,18]]` → `[[1,6],[8,10],[15,18]]`.

## 2. Why & when

This is the canonical named problem for the Merge Intervals pattern-meta pages earlier in this section. Comparing every pair of intervals directly costs O(n²). Sorting by start time first reduces this to a single linear scan, because after sorting, only adjacent intervals can possibly overlap.

## 3. Core concept

**Key idea:** sort by start time, then walk through the intervals, merging each one into a running "current" interval as long as it overlaps, and starting a new "current" interval as soon as one does not.

**Steps:**
1. Sort `intervals` by `start` ascending.
2. Initialize `current = intervals[0]` and an empty result list.
3. For each subsequent interval `next`:
   - If `next.start <= current.end`, merge: `current.end = max(current.end, next.end)`.
   - Otherwise, push `current` to the result and set `current = next`.
4. Push the final `current` to the result after the loop.

**Why it is correct:** sorting guarantees that any interval overlapping the current merged range must appear immediately in the scan order — its start cannot be smaller than intervals already processed, so once an interval's start exceeds the current range's end, no later interval (with an even larger start) can overlap it either.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merging four intervals into three groups">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals = [1,3], [2,6], [8,10], [15,18]</text>
    <rect x="20" y="45" width="60" height="20" fill="#161b22" stroke="#79c0ff"/>
    <rect x="50" y="70" width="120" height="20" fill="#161b22" stroke="#79c0ff"/>
    <rect x="20" y="100" width="150" height="18" fill="none" stroke="#3fb950" stroke-dasharray="4,2"/><text x="95" y="113" fill="#3fb950" text-anchor="middle" font-size="10">merged [1,6]</text>
    <rect x="260" y="70" width="60" height="20" fill="#161b22" stroke="#f0883e"/><text x="290" y="113" fill="#8b949e" text-anchor="middle" font-size="10">[8,10] stays</text>
    <rect x="440" y="70" width="90" height="20" fill="#161b22" stroke="#f0883e"/><text x="485" y="113" fill="#8b949e" text-anchor="middle" font-size="10">[15,18] stays</text>
    <text x="20" y="150" fill="#8b949e">result: [[1,6], [8,10], [15,18]]</text>
  </g>
</svg>

`[1,3]` and `[2,6]` overlap (`2 <= 3`) and merge into `[1,6]`; `[8,10]` and `[15,18]` each start after the previous range ends, so they stay separate.

## 5. Runnable example

```java
// MergeIntervals.java
import java.util.*;

public class MergeIntervals {

    // Level 1 -- Brute force: repeatedly scan all pairs, merging any that
    // overlap, until no merge happens in a full pass. O(n^3) worst case
    // -- wastes huge amounts of repeated pairwise comparison.
    static int[][] bruteForce(int[][] intervals) {
        List<int[]> list = new ArrayList<>(Arrays.asList(intervals));
        boolean mergedAny = true;
        while (mergedAny) {
            mergedAny = false;
            outer:
            for (int i = 0; i < list.size(); i++) {
                for (int j = i + 1; j < list.size(); j++) {
                    int[] a = list.get(i), b = list.get(j);
                    if (a[0] <= b[1] && b[0] <= a[1]) {
                        int[] merged = {Math.min(a[0], b[0]), Math.max(a[1], b[1])};
                        list.remove(j);
                        list.remove(i);
                        list.add(merged);
                        mergedAny = true;
                        break outer;
                    }
                }
            }
        }
        return list.toArray(new int[0][]);
    }

    // KEY INSIGHT: sorting by start time guarantees any interval that can
    // overlap the current merged range appears immediately next in the
    // scan -- so a single linear pass replaces all pairwise comparisons.

    // Level 2 -- Optimal: sort then single-pass merge. O(n log n) time,
    // O(n) space.
    public static int[][] merge(int[][] intervals) {
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

    // Level 3 -- Hardened: a single interval, and an interval fully
    // contained inside another (e.g. [1,10] and [2,3]).
    static int[][] hardened(int[][] intervals) {
        return merge(intervals);
    }

    public static void main(String[] args) {
        int[][] a = {{1, 3}, {2, 6}, {8, 10}, {15, 18}};
        System.out.println("brute force: " + Arrays.deepToString(bruteForce(a)));
        System.out.println("optimal:     " + Arrays.deepToString(merge(a)));

        int[][] contained = {{1, 10}, {2, 3}};
        System.out.println("contained:   " + Arrays.deepToString(hardened(contained)));
    }
}
```

How to run: save as `MergeIntervals.java`, then run `java MergeIntervals.java`.

## 6. Walkthrough

Dry run of `merge([[1,3],[2,6],[8,10],[15,18]])`:

| step | current | next | overlap? | action |
|---|---|---|---|---|
| start | [1,3] | — | — | — |
| 1 | [1,3] | [2,6] | 2<=3 yes | current=[1,6] |
| 2 | [1,6] | [8,10] | 8<=6 no | save [1,6]; current=[8,10] |
| 3 | [8,10] | [15,18] | 15<=10 no | save [8,10]; current=[15,18] |
| end | — | — | — | save [15,18] |

Result: `[[1,6],[8,10],[15,18]]`. Time complexity: O(n log n), dominated by the sort. Space complexity: O(n) for the result.

## 7. Gotchas & takeaways

> Gotcha: using `Math.max(current[1], intervals[i][1])` is required, not just `intervals[i][1]` — a later interval can be fully contained inside the current one (like `[2,3]` inside `[1,10]`), and blindly overwriting the end would shrink the merged range incorrectly.

- This is the direct template application from the pattern-meta pages — no variation needed beyond the base merge loop.
- Related problems: Insert Interval (merge a single new interval into an already-sorted, already-merged list), Non-overlapping Intervals (count removals instead of merging).
