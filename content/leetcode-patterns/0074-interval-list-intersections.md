---
card: leetcode-patterns
gi: 74
slug: interval-list-intersections
title: Interval List Intersections
---

## 1. What it is

Given two lists of closed intervals, `firstList` and `secondList`, each sorted and each internally non-overlapping, return the intersection of the two lists — every range of overlap between an interval from the first list and one from the second. Example: `firstList = [[0,2],[5,10],[13,23],[24,25]]`, `secondList = [[1,5],[8,12],[15,24],[25,26]]` → `[[1,2],[5,5],[8,10],[15,23],[24,24],[24,25]]`.

## 2. Why & when

Comparing every interval from the first list against every interval from the second is O(n · m). Because both lists are already sorted, a merge-style two-pointer walk — one pointer per list — finds every intersection in a single combined pass, similar in spirit to merging two sorted arrays.

## 3. Core concept

**Key idea:** walk both lists simultaneously with one pointer each. At each step, compute the overlap (if any) between the current interval from each list. Then advance whichever pointer's interval ends first — that interval cannot possibly overlap anything further along in the other list.

**Steps:**
1. Set `i = 0`, `j = 0`.
2. While `i < firstList.length` and `j < secondList.length`:
   - Compute `lo = max(firstList[i].start, secondList[j].start)` and `hi = min(firstList[i].end, secondList[j].end)`.
   - If `lo <= hi`, `[lo, hi]` is a valid intersection — add it to the result.
   - Advance the pointer whose interval has the smaller `end` value (that interval is fully consumed).
3. Return the result.

**Why it is correct:** an interval's overlap potential with the other list ends once its own end point passes — advancing that pointer is always safe, because no future interval in its own list starts earlier (the list is sorted), so nothing earlier could still be pending. The other list's current interval may still have more overlaps ahead, so it stays in place.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointers walking sorted interval lists to find overlaps">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">A: [0,2], [5,10]     B: [1,5], [8,12]</text>
    <rect x="20" y="45" width="40" height="20" fill="#161b22" stroke="#79c0ff"/><text x="40" y="60" fill="#e6edf3" text-anchor="middle" font-size="10">[0,2]</text>
    <rect x="40" y="70" width="80" height="20" fill="#161b22" stroke="#f0883e"/><text x="80" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[1,5]</text>
    <rect x="40" y="100" width="20" height="16" fill="none" stroke="#3fb950" stroke-dasharray="3,2"/><text x="50" y="112" fill="#3fb950" text-anchor="middle" font-size="9">[1,2]</text>
    <rect x="140" y="45" width="100" height="20" fill="#161b22" stroke="#79c0ff"/><text x="190" y="60" fill="#e6edf3" text-anchor="middle" font-size="10">[5,10]</text>
    <rect x="220" y="70" width="80" height="20" fill="#161b22" stroke="#f0883e"/><text x="260" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[8,12]</text>
    <rect x="220" y="100" width="20" height="16" fill="none" stroke="#3fb950" stroke-dasharray="3,2"/><text x="230" y="112" fill="#3fb950" text-anchor="middle" font-size="9">[8,10]</text>
    <text x="20" y="150" fill="#8b949e">overlap = max(starts) to min(ends); advance whichever interval ends first</text>
  </g>
</svg>

`[0,2]` and `[1,5]` overlap on `[1,2]`; `[0,2]` ends first, so its pointer advances to `[5,10]`, which then overlaps `[1,5]`... and the walk continues finding each overlap in order.

## 5. Runnable example

```java
// IntervalListIntersections.java
import java.util.*;

public class IntervalListIntersections {

    // Level 1 -- Brute force: compare every pair from both lists.
    // O(n * m) time -- wastes comparisons the sorted order could skip.
    static int[][] bruteForce(int[][] a, int[][] b) {
        List<int[]> result = new ArrayList<>();
        for (int[] x : a) {
            for (int[] y : b) {
                int lo = Math.max(x[0], y[0]);
                int hi = Math.min(x[1], y[1]);
                if (lo <= hi) result.add(new int[] {lo, hi});
            }
        }
        return result.toArray(new int[0][]);
    }

    // KEY INSIGHT: because both lists are sorted and internally
    // non-overlapping, whichever current interval ends FIRST can never
    // overlap anything further along -- advance only that pointer.

    // Level 2 -- Optimal: two pointers, one merge-style pass. O(n + m)
    // time, O(n + m) space for the result.
    public static int[][] intervalIntersection(int[][] a, int[][] b) {
        List<int[]> result = new ArrayList<>();
        int i = 0, j = 0;
        while (i < a.length && j < b.length) {
            int lo = Math.max(a[i][0], b[j][0]);
            int hi = Math.min(a[i][1], b[j][1]);
            if (lo <= hi) result.add(new int[] {lo, hi});

            if (a[i][1] < b[j][1]) i++;
            else j++;
        }
        return result.toArray(new int[0][]);
    }

    // Level 3 -- Hardened: one list is empty, or the two lists never
    // overlap at all.
    static int[][] hardened(int[][] a, int[][] b) {
        return intervalIntersection(a, b);
    }

    public static void main(String[] args) {
        int[][] a = {{0, 2}, {5, 10}, {13, 23}, {24, 25}};
        int[][] b = {{1, 5}, {8, 12}, {15, 24}, {25, 26}};
        System.out.println("brute force: " + Arrays.deepToString(bruteForce(a, b)));
        System.out.println("optimal:     " + Arrays.deepToString(intervalIntersection(a, b)));

        System.out.println("empty list:  " + Arrays.deepToString(hardened(new int[0][], b)));
    }
}
```

How to run: save as `IntervalListIntersections.java`, then run `java IntervalListIntersections.java`.

## 6. Walkthrough

Dry run of `intervalIntersection` on the first two intervals of each list, `a = [0,2]`, `b = [1,5]`:

| step | a[i] | b[j] | lo | hi | valid? | added | advance |
|---|---|---|---|---|---|---|---|
| 1 | [0,2] | [1,5] | max(0,1)=1 | min(2,5)=2 | 1<=2 yes | [1,2] | a[i].end (2) < b[j].end (5) -> i++ |
| 2 | [5,10] | [1,5] | max(5,1)=5 | min(10,5)=5 | 5<=5 yes | [5,5] | a[i].end (10) < b[j].end (5)? no -> j++ |

The walk continues this way across the full lists, producing every overlap in order. Time complexity: O(n + m), one combined pass. Space complexity: O(n + m) for the result in the worst case.

## 7. Gotchas & takeaways

> Gotcha: a zero-length overlap like `[5,5]` (a single touching point) is a valid intersection under `lo <= hi` — do not skip it by mistakenly requiring `lo < hi`.

- Advancing "whichever interval ends first" is the same core idea as the merge step in Merge Two Sorted Lists — recognizing the two-pointer merge shape transfers directly.
- Related problems: Merge Intervals (single list, not two), Employee Free Time (finds gaps instead of overlaps across multiple sorted lists).
