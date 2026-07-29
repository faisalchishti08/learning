---
card: leetcode-patterns
gi: 584
slug: design-underground-system
title: Design Underground System
---

## 1. What it is

Design an `UndergroundSystem` class that tracks passenger check-ins and check-outs to compute average travel times between station pairs. `checkIn(id, stationName, t)` records that passenger `id` entered `stationName` at time `t`. `checkOut(id, stationName, t)` records that the same passenger left the system at `stationName` at time `t`, completing one trip. `getAverageTime(startStation, endStation)` returns the average travel time over every completed trip recorded between those two specific stations, in that direction. Example: `checkIn(1, "A", 3)`, `checkOut(1, "B", 8)` (a 5-minute trip from A to B), `getAverageTime("A", "B")` → `5.0`.

## 2. Why & when

This is a two-stage bookkeeping problem: first, pair each passenger's `checkIn` with their later `checkOut` (using the passenger `id` as the join key); second, aggregate the resulting trip durations per station pair. Both stages are pure O(1)-per-call lookups if you pick the right key for each `HashMap` — the challenge is recognizing that two *separate* maps, keyed differently, are needed, not one.

## 3. Core concept

**Key idea:** use one `HashMap<id, (station, time)>` to hold *in-progress* trips (from `checkIn` until the matching `checkOut` arrives), and a second `HashMap<(startStation, endStation), (totalTime, tripCount)>` to accumulate *completed* trip statistics per route.

**Steps:**
1. `checkIn(id, stationName, t)`: store `checkIns[id] = (stationName, t)`. Nothing to aggregate yet — the trip is not complete.
2. `checkOut(id, stationName, t)`: look up `checkIns[id]` to get the start `(startStation, startTime)`; remove `id` from `checkIns` (the trip is now complete, no longer in progress). Compute `duration = t - startTime`. Update `routeStats[(startStation, stationName)]`: add `duration` to its running total, and increment its trip count.
3. `getAverageTime(startStation, endStation)`: look up `routeStats[(startStation, endStation)]` and return `totalTime / tripCount` as a `double`.

**Why two maps, not one:** the two maps answer two different questions with two different keys. `checkIns` answers "where and when did passenger `id` last check in" (keyed by passenger). `routeStats` answers "what is the running total and count for this specific route" (keyed by a station pair). Conflating them would mean re-deriving one from the other on every call, at extra cost, for no benefit.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="checkOut looks up the passenger's in-progress trip by id, then updates the route's running total keyed by station pair">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">checkIns (by passenger id)</text>
    <rect x="30" y="30" width="240" height="35" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">id=1 -&gt; ("A", t=3)</text>
    <text x="150" y="90" fill="#79c0ff" text-anchor="middle" font-size="11">checkOut(1, "B", 8): lookup id=1, duration=8-3=5</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">routeStats (by station pair)</text>
    <rect x="410" y="30" width="240" height="35" fill="#161b22" stroke="#f0883e"/>
    <text x="530" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">("A","B") -&gt; total+=5, count+=1</text>
    <line x1="270" y1="47" x2="410" y2="47" stroke="#79c0ff" marker-end="url(#a8)"/>
    <defs><marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <text x="350" y="150" fill="#8b949e" text-anchor="middle">getAverageTime("A","B") = total / count, read directly from routeStats</text>
  </g>
</svg>

`checkOut` bridges the two maps: it reads the in-progress trip by passenger `id`, then writes the resulting duration into the aggregate keyed by station pair.

## 5. Runnable example

**Level 1 — Brute force.** Store every completed trip as a raw `(startStation, endStation, duration)` record in a list, and on every `getAverageTime` call, scan the whole list filtering for matching stations and averaging. O(n) per `getAverageTime` call, where `n` grows with every checkout ever recorded.

**KEY INSIGHT:** since `getAverageTime` only ever needs a running total and count (never the individual durations), aggregate incrementally at `checkOut` time instead of storing raw history — this turns an O(n) query into an O(1) lookup, at the cost of no extra work per `checkOut` (it was already O(1)).

**Level 2 — Optimal.** Two `HashMap`s as described above, O(1) average for every method.

**Level 3 — Hardened.** Uses a combined station-pair string key (or a small record/pair type) consistently, and correctly removes the passenger's entry from `checkIns` on `checkOut` so a later `checkIn` by the same `id` does not collide with stale data.

```java
// UndergroundSystem.java
import java.util.*;

public class UndergroundSystem {

    private static class Trip { // completed-route aggregate
        double totalTime = 0;
        int count = 0;
    }

    private final Map<Integer, Object[]> checkIns = new HashMap<>(); // id -> [station, time]
    private final Map<String, Trip> routeStats = new HashMap<>();    // "start->end" -> aggregate

    public void checkIn(int id, String stationName, int t) {
        checkIns.put(id, new Object[]{stationName, t});
    }

    public void checkOut(int id, String stationName, int t) {
        Object[] start = checkIns.remove(id);
        String startStation = (String) start[0];
        int startTime = (int) start[1];

        String routeKey = startStation + "->" + stationName;
        Trip trip = routeStats.computeIfAbsent(routeKey, k -> new Trip());
        trip.totalTime += (t - startTime);
        trip.count++;
    }

    public double getAverageTime(String startStation, String endStation) {
        Trip trip = routeStats.get(startStation + "->" + endStation);
        return trip.totalTime / trip.count;
    }

    public static void main(String[] args) {
        UndergroundSystem system = new UndergroundSystem();
        system.checkIn(1, "A", 3);
        system.checkOut(1, "B", 8);
        System.out.println(system.getAverageTime("A", "B")); // 5.0

        system.checkIn(2, "A", 10);
        system.checkOut(2, "B", 18);
        System.out.println(system.getAverageTime("A", "B")); // (5 + 8) / 2 = 6.5
    }
}
```

**How to run:** save as `UndergroundSystem.java`, then run `java UndergroundSystem.java`.

## 6. Walkthrough

Trace `checkIn(1,"A",3)`, `checkOut(1,"B",8)`, `checkIn(2,"A",10)`, `checkOut(2,"B",18)`, `getAverageTime("A","B")`:

1. `checkIn(1,"A",3)`: `checkIns = {1: ["A", 3]}`.
2. `checkOut(1,"B",8)`: remove `checkIns[1]` -> `("A", 3)`. `duration = 8 - 3 = 5`. `routeStats["A->B"]` created: `totalTime=5, count=1`.
3. `checkIn(2,"A",10)`: `checkIns = {2: ["A", 10]}` (entry for `1` is already gone).
4. `checkOut(2,"B",18)`: remove `checkIns[2]` -> `("A", 10)`. `duration = 18 - 10 = 8`. `routeStats["A->B"]` updated: `totalTime=5+8=13, count=2`.
5. `getAverageTime("A","B")`: `13 / 2 = 6.5`.

## 7. Gotchas & takeaways

> Gotcha: using a plain string concatenation like `startStation + endStation` (no separator) as a map key can silently collide two different station pairs — for example, stations `"AB"` to `"C"` and `"A"` to `"BC"` would both produce the key `"ABC"`; always join with an unambiguous separator (like `"->"`) that cannot itself appear as part of a station name in the intended way.

- Signal: "match a start event to a later end event by some shared ID, then aggregate by a different key" is the two-map signal — one map for in-progress joins, one for the aggregated result.
- Aggregate incrementally (running total and count) at write time rather than storing raw history and scanning it at query time.
- Related problems: Two Sum (the simplest form of "match by a key seen earlier"), Design Hit Counter (aggregates by time window instead of by a paired id).
