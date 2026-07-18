---
card: leetcode-patterns
gi: 73
slug: meeting-rooms-ii
title: Meeting Rooms II
---

## 1. What it is

Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, find the minimum number of conference rooms required so that no two meetings needing the same room overlap. Example: `intervals = [[0,30],[5,10],[15,20]]` → `2` (meetings `[5,10]` and `[15,20]` can share a room, but `[0,30]` overlaps both, needing a second room).

## 2. Why & when

This is the direct application of the sweep-line template from the pattern-meta pages: the question "how many rooms are needed" is exactly "what is the peak number of meetings happening at the same instant." Sorting starts and ends separately, then scanning them together, answers this in one pass.

## 3. Core concept

**Key idea:** split every meeting into a "start" event and an "end" event. Sort all start times and all end times independently. Walk through the start times in order; for each new meeting starting, check whether any earlier meeting has already ended (using the earliest unprocessed end time) — if so, reuse that room instead of adding a new one.

**Steps:**
1. Extract all start times into one sorted array; all end times into another sorted array.
2. Use two pointers, `s` for the start array and `e` for the end array, and a `rooms` counter.
3. For each start time in order:
   - If the current start time is greater than or equal to the earliest unprocessed end time, a room has freed up — reuse it: advance `e`, do not increase `rooms`.
   - Otherwise, no room is free — increase `rooms`.
   - Advance `s`.
4. Return the maximum value `rooms` ever reaches.

**Why it is correct:** processing start times in order and comparing each against the earliest still-open end time correctly simulates rooms being freed as soon as possible. If a new meeting starts before any room frees up, a new room is genuinely required at that moment; this greedy simulation tracks the true peak concurrency.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Meeting rooms needed via separately sorted starts and ends">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">meetings: [0,30], [5,10], [15,20]</text>
    <text x="20" y="45" fill="#79c0ff">starts sorted: 0, 5, 15</text>
    <text x="20" y="70" fill="#f0883e">ends sorted:   10, 20, 30</text>
    <text x="20" y="105" fill="#8b949e">start 0: no room free (no ends yet) -&gt; rooms=1</text>
    <text x="20" y="125" fill="#8b949e">start 5: earliest end 10 &gt; 5 -&gt; not free -&gt; rooms=2</text>
    <text x="20" y="145" fill="#8b949e">start 15: earliest end 10 &lt;= 15 -&gt; room freed, reuse -&gt; rooms stays 2</text>
  </g>
</svg>

Comparing each new start against the earliest still-open end simulates rooms freeing up in real time, without ever building an explicit room-assignment table.

## 5. Runnable example

```java
// MeetingRoomsII.java
import java.util.*;

public class MeetingRoomsII {

    // Level 1 -- Brute force: sweep-line with a min-heap of active end
    // times. O(n log n) time -- correct and common, but heap overhead is
    // avoidable when only a COUNT (not which room) is needed.
    static int bruteForce(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        PriorityQueue<Integer> endTimes = new PriorityQueue<>();
        for (int[] iv : intervals) {
            if (!endTimes.isEmpty() && endTimes.peek() <= iv[0]) {
                endTimes.poll();
            }
            endTimes.offer(iv[1]);
        }
        return endTimes.size();
    }

    // KEY INSIGHT: separating starts and ends into two independently
    // sorted arrays lets two pointers simulate room reuse directly --
    // no heap needed, since the earliest end is always found by pointer
    // position, not by re-querying a priority structure.

    // Level 2 -- Optimal: two sorted arrays, two pointers. O(n log n)
    // time (dominated by sorting), O(n) space for the two arrays.
    public static int minMeetingRooms(int[][] intervals) {
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
            if (starts[s] < ends[e]) {
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

    // Level 3 -- Hardened: all meetings share the exact same time slot
    // (every meeting needs its own room).
    static int hardened(int[][] intervals) {
        return minMeetingRooms(intervals);
    }

    public static void main(String[] args) {
        int[][] a = {{0, 30}, {5, 10}, {15, 20}};
        System.out.println("brute force (heap): " + bruteForce(a.clone()));
        System.out.println("optimal (two ptr):  " + minMeetingRooms(a));

        int[][] identical = {{1, 5}, {1, 5}, {1, 5}};
        System.out.println("all identical (expect 3): " + hardened(identical));
    }
}
```

How to run: save as `MeetingRoomsII.java`, then run `java MeetingRoomsII.java`.

## 6. Walkthrough

Dry run of the two-pointer occupancy scan inside `minMeetingRooms` with `starts = [0,5,15]`, `ends = [10,20,30]`:

| step | s | e | starts[s] | ends[e] | condition | action | active | peak |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 10 | 0<10 | active++, s++ | 1 | 1 |
| 2 | 1 | 0 | 5 | 10 | 5<10 | active++, s++ | 2 | 2 |
| 3 | 2 | 0 | 15 | 10 | 15<10 false | active--, e++ | 1 | 2 |
| 4 | 2 | 1 | 15 | 20 | 15<20 | active++, s++ | 2 | 2 |

`s` reaches `n`, loop ends. Peak: `2`. Time complexity: O(n log n), dominated by sorting the two arrays. Space complexity: O(n) for the separated arrays.

## 7. Gotchas & takeaways

> Gotcha: using `<=` instead of `<` in `starts[s] < ends[e]` treats a meeting starting exactly when another ends as an overlap, which overcounts rooms for back-to-back meetings that should share a room.

- This problem is the textbook sweep-line application named directly by the pattern-meta template page.
- Related problems: Minimum Number of Arrows to Burst Balloons (same peak-overlap idea, different framing), Car Pooling (sweep line with variable "capacity used" instead of a simple count).
