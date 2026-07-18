---
card: leetcode-patterns
gi: 76
slug: car-pooling
title: Car Pooling
---

## 1. What it is

A car has a fixed passenger `capacity`. It picks up and drops off passengers along a route according to `trips`, where `trips[i] = [numPassengers, from_i, to_i]` means picking up `numPassengers` at location `from_i` and dropping them off at location `to_i`. Determine whether the car can complete every trip without ever exceeding `capacity`. Example: `trips = [[2,1,5],[3,3,7]]`, `capacity = 4` → `false` (between locations 3 and 5, both trips overlap: `2 + 3 = 5 > 4`).

## 2. Why & when

This is Meeting Rooms II with a twist: instead of counting how many meetings overlap, you must sum how many passengers overlap at each point along the route, since each "interval" (trip) carries a weight (passenger count) instead of counting as a flat `1`. The same sweep-line idea from the pattern-meta pages applies, but each event adds or subtracts the passenger count instead of `1`.

## 3. Core concept

**Key idea:** convert each trip into two weighted events — a `+numPassengers` event at `from` and a `-numPassengers` event at `to`. Sort all events by location. Scan through them, maintaining a running passenger total. If the total ever exceeds `capacity`, the car cannot complete the trips.

**Steps:**
1. For each trip `[num, from, to]`, create events `(from, +num)` and `(to, -num)`.
2. Sort events by location; if two events share a location, process the drop-off (`-num`) before the pickup (`+num`), since a passenger leaving frees a seat for one arriving at the same point.
3. Scan events in order, adding each event's delta to a running total.
4. If the running total ever exceeds `capacity`, return `false`. If the scan finishes without exceeding capacity, return `true`.

**Why it is correct:** the running total at any location is exactly the number of passengers physically in the car at that point along the route. Checking it after every event catches the exact moment (if any) where capacity is exceeded, since capacity violations can only happen at a pickup point.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sweep line tracking passenger count along a route">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">trips: [2 passengers, 1-&gt;5], [3 passengers, 3-&gt;7]; capacity = 4</text>
    <line x1="20" y1="90" x2="600" y2="90" stroke="#30363d"/>
    <circle cx="60" cy="90" r="4" fill="#3fb950"/><text x="60" y="110" fill="#8b949e" font-size="10">1:+2</text>
    <circle cx="220" cy="90" r="4" fill="#3fb950"/><text x="220" y="110" fill="#8b949e" font-size="10">3:+3</text>
    <circle cx="380" cy="90" r="4" fill="#f0883e"/><text x="380" y="110" fill="#8b949e" font-size="10">5:-2</text>
    <circle cx="540" cy="90" r="4" fill="#f0883e"/><text x="540" y="110" fill="#8b949e" font-size="10">7:-3</text>
    <text x="20" y="60" fill="#8b949e">running total: 2, 5 (exceeds 4!), 3, 0</text>
    <text x="20" y="150" fill="#f0883e">between location 3 and 5, the car needs 5 seats but only has 4 -&gt; false</text>
  </g>
</svg>

Between locations `3` and `5`, both trips overlap: `2 + 3 = 5` passengers exceeds the `4`-seat capacity — the sweep catches this the moment the second pickup event fires.

## 5. Runnable example

```java
// CarPooling.java
import java.util.*;

public class CarPooling {

    // Level 1 -- Brute force: for every trip, add its passenger count to
    // every location in its range using an array offset by the minimum
    // coordinate. O(n * range) time -- wastes work when the location
    // range is large relative to the number of trips.
    static boolean bruteForce(int[][] trips, int capacity) {
        int maxLoc = 0;
        for (int[] t : trips) maxLoc = Math.max(maxLoc, t[2]);
        int[] passengerAt = new int[maxLoc + 1];
        for (int[] t : trips) {
            for (int loc = t[1]; loc < t[2]; loc++) {
                passengerAt[loc] += t[0];
                if (passengerAt[loc] > capacity) return false;
            }
        }
        return true;
    }

    // KEY INSIGHT: representing each trip as a weighted +num / -num pair
    // of sweep-line events turns "does passenger count ever exceed
    // capacity" into a single sorted scan, regardless of how large the
    // location coordinates are.

    // Level 2 -- Optimal: weighted sweep line. O(n log n) time,
    // O(n) space for the events.
    public static boolean carPooling(int[][] trips, int capacity) {
        int n = trips.length;
        int[][] events = new int[2 * n][2]; // [location, delta]
        for (int i = 0; i < n; i++) {
            events[2 * i] = new int[] {trips[i][1], trips[i][0]};
            events[2 * i + 1] = new int[] {trips[i][2], -trips[i][0]};
        }
        // drop-offs before pickups at the same location: sort by
        // location, then by delta ascending (negative deltas first).
        Arrays.sort(events, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);

        int passengers = 0;
        for (int[] e : events) {
            passengers += e[1];
            if (passengers > capacity) return false;
        }
        return true;
    }

    // Level 3 -- Hardened: a trip that starts and ends at the same
    // location as another trip's drop-off, verifying the "drop-off
    // before pickup" tie-break avoids a false capacity violation.
    static boolean hardened(int[][] trips, int capacity) {
        return carPooling(trips, capacity);
    }

    public static void main(String[] args) {
        int[][] a = {{2, 1, 5}, {3, 3, 7}};
        System.out.println("brute force (expect false): " + bruteForce(a, 4));
        System.out.println("optimal (expect false):     " + carPooling(a, 4));

        int[][] backToBack = {{2, 1, 3}, {3, 3, 5}};
        System.out.println("back-to-back at 3 (expect true): " + hardened(backToBack, 3));
    }
}
```

How to run: save as `CarPooling.java`, then run `java CarPooling.java`.

## 6. Walkthrough

Dry run of `carPooling([[2,1,5],[3,3,7]], 4)`:

Events sorted: `(1,+2), (3,+3), (5,-2), (7,-3)`.

| step | event | passengers | exceeds capacity 4? |
|---|---|---|---|
| 1 | (1,+2) | 2 | no |
| 2 | (3,+3) | 5 | **yes -> return false** |

Result: `false`, matching the expected answer. Time complexity: O(n log n), dominated by sorting `2n` events. Space complexity: O(n) for the events array.

## 7. Gotchas & takeaways

> Gotcha: sorting ties (pickup and drop-off at the same location) with pickups (`+num`) before drop-offs (`-num`) overcounts capacity for a passenger who leaves exactly where another boards — always process `-num` events first at a shared location.

- This problem generalizes Meeting Rooms II by giving each "meeting" (trip) a weight instead of a flat count of `1` — the sweep-line shape is otherwise identical.
- Related problems: Meeting Rooms II (unweighted version), Minimum Number of Arrows to Burst Balloons (weight-free grouping instead of a running sum).
