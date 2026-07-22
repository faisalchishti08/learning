---
card: leetcode-patterns
gi: 209
slug: the-skyline-problem
title: The Skyline Problem
---

## 1. What it is

Given `buildings[i] = [lefti, righti, heighti]`, compute the SKYLINE — the outline formed by all buildings viewed from a distance — as a list of `[x, height]` key points where the height changes. Example: `buildings = [[2,9,10],[3,7,15],[5,12,12]]` → `[[2,10],[3,15],[7,12],[12,0]]`.

## 2. Why & when

At any x-coordinate, the skyline's height is the MAXIMUM height among all buildings currently "active" (their x-range includes that point). Sweeping left to right through building edges, and tracking active heights with a max-heap that supports lazy removal (a building "ending" is a removal), efficiently answers "what is the current max height" after every edge event.

## 3. Core concept

**Key idea:** convert every building into two EVENTS: a "start" event at `left` (marking the building as active, contributing `height`) and an "end" event at `right` (marking it inactive). Sort all events by x-coordinate (with start events processed before end events at the same x, and taller buildings starting before shorter ones end, to avoid missing a needed key point). Sweep through events left to right, maintaining a max-heap of currently active heights (using lazy deletion for buildings that have ended); whenever the max active height CHANGES after processing an event, record a new key point.

**Steps:**
1. Convert each `[left, right, height]` building into a start event `[left, -height]` (negative marks "start," and sorts taller buildings first at the same x) and an end event `[right, height]` (positive marks "end").
2. Sort all events by x-coordinate; ties broken by the event value (negative/start events come before positive/end events, and among starts, more negative — taller — comes first).
3. Sweep through events, maintaining a max-heap (or a multiset) of active heights and a "currently ending" count per height (or use lazy deletion by index).
4. For a start event, add its height to the active set. For an end event, remove its height from the active set.
5. After processing each event, check the current maximum active height (0 if none). If it DIFFERS from the last recorded height, append `[x, newMaxHeight]` to the result.

**Why it is correct:** every place the skyline's height changes corresponds exactly to a building starting or ending — sorting events left to right and tracking the max active height after each one captures exactly those transition points. The tie-break rules (process starts before ends at the same x, taller starts before shorter ones) ensure that simultaneous events at the same x-coordinate produce the correct single key point rather than a spurious dip or duplicate.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sweep line processes start and end events left to right, recording a new key point whenever the max active height changes">
  <g font-family="sans-serif" font-size="12">
    <rect x="40" y="60" width="60" height="80" fill="#3fb950" opacity="0.5"/>
    <rect x="80" y="30" width="60" height="110" fill="#79c0ff" opacity="0.5"/>
    <rect x="120" y="80" width="80" height="60" fill="#e3b341" opacity="0.5"/>
    <line x1="20" y1="140" x2="440" y2="140" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">sweeping left to right, the skyline height = max active building height at each x</text>
  </g>
</svg>

The skyline outline (not drawn) is the running maximum of all overlapping building heights, changing exactly at building edges.

## 5. Runnable example

```java
// TheSkylineProblem.java
import java.util.*;

public class TheSkylineProblem {

    // Level 1 -- Brute force: collect every distinct x-coordinate, and
    // for each, linearly scan all buildings to find the max height
    // active at that x. Correct, but O(n^2) -- checking every building
    // against every coordinate.

    // KEY INSIGHT: sweep left to right through START/END events, using
    // a max-heap (with lazy removal for ended buildings) to track the
    // active maximum incrementally -- avoids re-scanning all buildings
    // at every coordinate.

    // Level 2 -- Optimal: event sweep + max-heap with lazy deletion.
    static List<List<Integer>> getSkyline(int[][] buildings) {
        List<int[]> events = new ArrayList<>();
        for (int[] b : buildings) {
            events.add(new int[]{b[0], -b[2]}); // start: negative height
            events.add(new int[]{b[1], b[2]});  // end: positive height
        }
        events.sort((a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);

        PriorityQueue<Integer> active = new PriorityQueue<>(Collections.reverseOrder());
        Map<Integer, Integer> toRemove = new HashMap<>();
        active.add(0);

        List<List<Integer>> result = new ArrayList<>();
        int prevMax = 0;

        for (int[] event : events) {
            int x = event[0];
            if (event[1] < 0) {
                active.add(-event[1]);
            } else {
                toRemove.merge(event[1], 1, Integer::sum);
            }

            while (!active.isEmpty() && toRemove.getOrDefault(active.peek(), 0) > 0) {
                toRemove.merge(active.peek(), -1, Integer::sum);
                active.poll();
            }

            int currentMax = active.peek();
            if (currentMax != prevMax) {
                result.add(Arrays.asList(x, currentMax));
                prevMax = currentMax;
            }
        }
        return result;
    }

    // Level 3 -- Hardened: seeding `active` with a permanent `0`
    // ensures `active.peek()` is always defined, even when no building
    // is currently active (ground level), avoiding an empty-heap
    // exception.

    public static void main(String[] args) {
        System.out.println(getSkyline(new int[][]{{2,9,10},{3,7,15},{5,12,12}}));
        // [[2, 10], [3, 15], [7, 12], [12, 0]]
    }
}
```

**How to run:** `java TheSkylineProblem.java`

## 6. Walkthrough

Trace events for `buildings = [[2,9,10],[3,7,15],[5,12,12]]`, sorted: `[2,-10],[3,-15],[5,-12],[7,15],[9,10],[12,12]`:

| Event | active max before | Action | active max after | Key point |
|---|---|---|---|---|
| [2,-10] | 0 | push 10 | 10 | [2,10] |
| [3,-15] | 10 | push 15 | 15 | [3,15] |
| [5,-12] | 15 | push 12 | 15 (unchanged) | none |
| [7,15] | 15 | mark 15 for removal, lazily pop it | 12 | [7,12] |
| [9,10] | 12 | mark 10 for removal, lazily pop it | 12 (unchanged, 12 still active) | none |
| [12,12] | 12 | mark 12 for removal, lazily pop it | 0 | [12,0] |

Result: `[[2,10],[3,15],[7,12],[12,0]]`, matching the expected output. Time complexity is O(n log n), for sorting events plus O(log n) heap operations per event; space is O(n) for the heap, removal map, and events list.

## 7. Gotchas & takeaways

> Gotcha: sorting start and end events at the SAME x-coordinate incorrectly (e.g. ends before starts) can produce a spurious dip in the skyline — a building ending exactly where another starts at the same height must not create a false drop to a lower height in between.

- Encoding start events as NEGATIVE height and end events as POSITIVE height is a compact trick that makes the sort comparator naturally handle both "starts before ends" and "taller starts first" with a single numeric comparison.
- The permanent `0` seeded into `active` represents "ground level" and must never be removed — it guarantees `active.peek()` is always valid.
- Related problems: Meeting Rooms III (similar event-sweep-with-heap structure, different domain), Sliding Window Median (same lazy-deletion-from-heap technique).
