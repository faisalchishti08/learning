---
card: leetcode-patterns
gi: 80
slug: divide-intervals-into-minimum-number-of-groups
title: Divide Intervals Into Minimum Number of Groups
---

## 1. What it is

Given an array of intervals, divide them into the minimum number of groups such that no two intervals in the same group overlap. Return that minimum number of groups. Example: `intervals = [[5,10],[6,8],[1,5],[2,3],[1,10]]` → `3`.

## 2. Why & when

This problem is Meeting Rooms II wearing a different name: "minimum number of groups so nothing overlaps within a group" is identical to "minimum number of rooms so nothing overlaps within a room." Both questions ask for the peak number of intervals that are simultaneously active at any single point, which the sweep-line template computes directly.

## 3. Core concept

**Key idea:** sort all start times and all end times separately. Walk through starts in order; each start either reuses a group whose interval has already ended (advance the end pointer) or requires a brand-new group. The maximum number of simultaneously open groups is the answer.

**Steps:**
1. Extract all `start` values into one sorted array, all `end` values into another sorted array.
2. Use two pointers, `s` and `e`, and a counter `active`, tracking peak.
3. Walk `s` through the starts. If `starts[s] <= ends[e]`, a new group is needed (they overlap) — increment `active` and update `peak`; otherwise, a group has freed up — advance `e` without changing `active`.
4. Return `peak`.

**Why it is correct:** this is exactly the Meeting Rooms II sweep-line logic — the "peak number of intervals active at once" is the minimum number of non-overlapping groups needed, since each group can hold at most one interval active at any given instant, and you cannot do better than the true peak concurrency.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Grouping overlapping intervals using peak concurrency">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">intervals: [5,10], [6,8], [1,5], [2,3], [1,10]</text>
    <rect x="20" y="45" width="20" height="18" fill="#161b22" stroke="#79c0ff"/><text x="30" y="58" fill="#8b949e" text-anchor="middle" font-size="8">[1,5]</text>
    <rect x="40" y="45" width="10" height="18" fill="#161b22" stroke="#f0883e"/><text x="45" y="58" fill="#8b949e" text-anchor="middle" font-size="7">[2,3]</text>
    <rect x="20" y="68" width="90" height="18" fill="#161b22" stroke="#3fb950"/><text x="65" y="81" fill="#8b949e" text-anchor="middle" font-size="8">[1,10]</text>
    <rect x="45" y="91" width="45" height="18" fill="#161b22" stroke="#79c0ff"/><text x="67" y="104" fill="#8b949e" text-anchor="middle" font-size="8">[5,10]</text>
    <rect x="55" y="114" width="20" height="18" fill="#161b22" stroke="#f0883e"/><text x="65" y="127" fill="#8b949e" text-anchor="middle" font-size="7">[6,8]</text>
    <text x="20" y="155" fill="#8b949e">peak overlap at x=2 (or x=6): [1,5],[2,3],[1,10] all active -&gt; 3 groups needed</text>
  </g>
</svg>

At `x = 2`, three intervals — `[1,5]`, `[2,3]`, and `[1,10]` — are simultaneously active, so at least three groups are required; the sweep finds this peak directly.

## 5. Runnable example

```java
// DivideIntervalsIntoMinimumGroups.java
import java.util.*;

public class DivideIntervalsIntoMinimumGroups {

    // Level 1 -- Brute force: min-heap of active end times, same as the
    // Meeting Rooms II brute-force approach. O(n log n) time -- correct,
    // but heap overhead is avoidable with two sorted arrays.
    static int bruteForce(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        PriorityQueue<Integer> ends = new PriorityQueue<>();
        for (int[] iv : intervals) {
            if (!ends.isEmpty() && ends.peek() < iv[0]) {
                ends.poll();
            }
            ends.offer(iv[1]);
        }
        return ends.size();
    }

    // KEY INSIGHT: "minimum groups so nothing overlaps within a group" is
    // exactly "peak number of intervals active at once" -- identical to
    // Meeting Rooms II, just phrased as groups instead of rooms.

    // Level 2 -- Optimal: two sorted arrays, two-pointer sweep. O(n log n)
    // time (dominated by sorting), O(n) space.
    public static int minGroups(int[][] intervals) {
        int n = intervals.length;
        int[] starts = new int[n], ends = new int[n];
        for (int i = 0; i < n; i++) {
            starts[i] = intervals[i][0];
            ends[i] = intervals[i][1];
        }
        Arrays.sort(starts);
        Arrays.sort(ends);

        int s = 0, e = 0, active = 0, peak = 0;
        while (s < n) {
            if (starts[s] <= ends[e]) {
                active++;
                peak = Math.max(peak, active);
                s++;
            } else {
                active--;
                e++;
            }
        }
        return peak;
    }

    // Level 3 -- Hardened: intervals that all share the exact same range
    // (every one needs its own group).
    static int hardened(int[][] intervals) {
        return minGroups(intervals);
    }

    public static void main(String[] args) {
        int[][] a = {{5, 10}, {6, 8}, {1, 5}, {2, 3}, {1, 10}};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + minGroups(a));

        int[][] identical = {{1, 3}, {1, 3}, {1, 3}};
        System.out.println("all identical (expect 3): " + hardened(identical));
    }
}
```

How to run: save as `DivideIntervalsIntoMinimumGroups.java`, then run `java DivideIntervalsIntoMinimumGroups.java`.

## 6. Walkthrough

Dry run with `starts = [1,1,2,5,6]`, `ends = [3,5,8,10,10]`:

| step | starts[s] | ends[e] | condition | action | active | peak |
|---|---|---|---|---|---|---|
| 1 | 1 | 3 | 1<=3 | active++, s++ | 1 | 1 |
| 2 | 1 | 3 | 1<=3 | active++, s++ | 2 | 2 |
| 3 | 2 | 3 | 2<=3 | active++, s++ | 3 | 3 |
| 4 | 5 | 3 | 5<=3? no | active--, e++ | 2 | 3 |
| 5 | 5 | 5 | 5<=5 | active++, s++ | 3 | 3 |
| 6 | 6 | 5 | 6<=5? no | active--, e++ | 2 | 3 |
| 7 | 6 | 8 | 6<=8 | active++, s++ | 3 | 3 |

Result: `peak = 3`. Time complexity: O(n log n), dominated by sorting the two arrays. Space complexity: O(n).

## 7. Gotchas & takeaways

> Gotcha: this problem uses `<=` for the overlap check (`starts[s] <= ends[e]`), unlike Meeting Rooms II's strict `<`, because touching intervals like `[1,5]` and `[5,10]` here still count as needing separate groups — always re-check the exact boundary condition the problem defines.

- Recognizing this as a relabeled Meeting Rooms II is the entire difficulty of the problem — the algorithm itself is unchanged.
- Related problems: Meeting Rooms II (identical algorithm, different wording), Car Pooling (weighted version of the same peak-concurrency idea).
