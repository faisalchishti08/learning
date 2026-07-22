---
card: leetcode-patterns
gi: 210
slug: meeting-rooms-iii
title: Meeting Rooms III
---

## 1. What it is

Given `n` rooms (numbered `0` to `n-1`) and `meetings[i] = [starti, endi]`, each meeting uses the LOWEST-numbered available room; if none is available, the meeting waits until the earliest room frees up and then runs for its original duration starting from that time. Return the room number that hosted the MOST meetings. Example: `n = 2`, `meetings = [[0,10],[1,5],[2,7],[3,4]]` → `0`.

## 2. Why & when

This is Process Tasks Using Servers wearing a "meeting room" costume: rooms are the servers (with "weight" being just the room number, always picking the smallest available), and meetings are the tasks. Two heaps again — free rooms (min-heap by room number) and busy rooms (min-heap by the time they free up) — drive the simulation.

## 3. Core concept

**Key idea:** sort meetings by start time. Maintain a min-heap of free room numbers, and a min-heap of `[freeAtTime, roomNumber]` for busy rooms. For each meeting, first move any busy room that has freed up (by the meeting's start time) into the free-room heap. If a room is free, use the LOWEST-numbered one, running the meeting for its exact `[start, end]` duration. If no room is free, take the busy room that frees up EARLIEST, and run the meeting starting from that free time instead (shifting both its start and end forward by the delay), then move that room back into the busy heap with the new end time.

**Steps:**
1. Sort meetings by `start` time. Initialize a free-room heap with rooms `0` to `n-1`, and an empty busy-room heap (ordered by `freeAtTime`, tie-broken by room number).
2. For each meeting `[start, end]`: move every busy room with `freeAtTime <= start` into the free heap.
3. If the free heap has a room, pop the smallest room number, use it for `[start, end]`, and push `[end, room]` into the busy heap.
4. If no room is free, pop the busy heap's earliest-freeing room `[freeAtTime, room]`; run the meeting for `[freeAtTime, freeAtTime + (end - start)]` in that room, and push the new `[newEnd, room]` back into the busy heap.
5. Track a count array of meetings hosted per room; increment the count for whichever room was used.
6. After all meetings are processed, return the room index with the maximum count (smallest index wins ties).

**Why it is correct:** processing meetings in start-time order and always preferring the SMALLEST available room number directly implements the stated assignment rule. When forced to delay a meeting, using the room that frees up EARLIEST minimizes the delay, which is the only sensible choice since any other busy room would free later, delaying the meeting more without benefit.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Free rooms picked by smallest number; if none free, the earliest-freeing busy room is used with a delayed start">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">free (by room number)</text>
    <circle cx="60" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="60" y="64" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="260" y="20" fill="#e6edf3" font-weight="bold">busy (by free time)</text>
    <circle cx="300" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="64" fill="#e6edf3" text-anchor="middle">t=5</text>
    <text x="10" y="15" fill="#e6edf3">meeting picks the smallest free room, or waits for the earliest busy room if none are free</text>
  </g>
</svg>

The free-room heap always offers the smallest available room number; the busy-room heap tells you which room frees up soonest when a meeting must wait.

## 5. Runnable example

```java
// MeetingRoomsIII.java
import java.util.*;

public class MeetingRoomsIII {

    // Level 1 -- Brute force: for each meeting, linearly scan all n
    // rooms to find the smallest free one (checking each room's
    // busy-until time against the meeting's start). Correct, but O(n)
    // per meeting instead of O(log n).

    // KEY INSIGHT: two min-heaps -- free rooms by number, busy rooms by
    // free time -- turn both "smallest free room" and "which room
    // frees up soonest" into O(log n) heap operations.

    // Level 2 -- Optimal: dual heaps, delay logic when no room is
    // free.
    static int mostBooked(int n, int[][] meetings) {
        Arrays.sort(meetings, (a, b) -> a[0] - b[0]);
        PriorityQueue<Integer> free = new PriorityQueue<>();
        for (int i = 0; i < n; i++) free.add(i);
        PriorityQueue<long[]> busy = new PriorityQueue<>(
            (a, b) -> a[0] != b[0] ? Long.compare(a[0], b[0]) : Long.compare(a[1], b[1])
        );

        long[] count = new long[n];
        for (int[] m : meetings) {
            long start = m[0], end = m[1];
            while (!busy.isEmpty() && busy.peek()[0] <= start) {
                free.add((int) busy.poll()[1]);
            }
            if (!free.isEmpty()) {
                int room = free.poll();
                busy.add(new long[]{end, room});
                count[room]++;
            } else {
                long[] earliest = busy.poll();
                long newStart = earliest[0];
                int room = (int) earliest[1];
                long duration = end - start;
                busy.add(new long[]{newStart + duration, room});
                count[room]++;
            }
        }

        int best = 0;
        for (int i = 1; i < n; i++) if (count[i] > count[best]) best = i;
        return best;
    }

    // Level 3 -- Hardened: `duration` is computed from the ORIGINAL
    // meeting length (end - start), not recomputed after the delay --
    // a delayed meeting keeps its full original length, just shifted
    // later.

    public static void main(String[] args) {
        System.out.println(mostBooked(2, new int[][]{{0,10},{1,5},{2,7},{3,4}})); // 0
        System.out.println(mostBooked(3, new int[][]{{1,20},{2,10},{3,5},{4,9},{6,8}})); // 1
    }
}
```

**How to run:** `java MeetingRoomsIII.java`

## 6. Walkthrough

Trace `n = 2`, `meetings = [[0,10],[1,5],[2,7],[3,4]]` (already sorted by start):

| Meeting | Free rooms | Action | Busy after |
|---|---|---|---|
| [0,10] | {0,1} | room0 free, use it | room0 busy until 10 |
| [1,5] | {1} (room0 busy until 10 > start 1) | room1 free, use it | room1 busy until 5 |
| [2,7] | {} (both busy: room0 until 10, room1 until 5) | no free room, earliest-freeing is room1 at t=5; delay: run [5, 5+(7-2)=10] in room1 | room1 busy until 10 |
| [3,4] | {} (room0 busy until 10, room1 busy until 10) | no free room; both rooms free at the same time, tie broken by smaller room number → room0; delay: run [10, 10+(4-3)=11] in room0 | room0 busy until 11 |

Counts: room0 hosted `[0,10]` and `[3,4]` (2 meetings), room1 hosted `[1,5]` and `[2,7]` (2 meetings) — tie broken by smallest index → room `0`. Time complexity is O(m log(m + n)), where m is the number of meetings, for sorting plus heap operations; space is O(n) for the heaps and count array.

## 7. Gotchas & takeaways

> Gotcha: using the ORIGINAL `end` time (instead of `newStart + duration`) when a meeting is delayed keeps the meeting's absolute end time fixed instead of its LENGTH — this is wrong, since a delayed meeting still takes the same amount of time to complete, just starting later.

- Sort meetings by `start` time FIRST — the whole simulation depends on processing them in that order, since later meetings might need to wait for earlier ones.
- The count array should use `long` if meeting counts could be very large in adversarial inputs, though `int` suffices for typical constraints — check the problem's stated bounds.
- Related problems: Process Tasks Using Servers (identical dual-heap structure, workers instead of rooms), Single-Threaded CPU (single-worker version of the same availability pattern).
