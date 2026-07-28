---
card: leetcode-patterns
gi: 565
slug: my-calendar-i
title: My Calendar I
---

## 1. What it is

Design a `MyCalendar` class that books events, each defined by a half-open interval `[start, end)`. A `book(start, end)` call succeeds (returns `true`) only if it does not overlap any previously booked event; otherwise it fails (returns `false`) and nothing is booked. Example: `book(10,20)` → `true`; `book(15,25)` → `false` (overlaps `[10,20)`); `book(20,30)` → `true` (touches but does not overlap, since intervals are half-open).

## 2. Why & when

This is the entry point into the [Segment Tree / BIT](0560-segment-tree-bit-signal-range-queries-with-point-range-updat.md) family of problems: repeatedly checking "does this new range overlap anything already recorded" is a range query, and recording a successful booking is an update. With event counts kept small (up to 1,000 calls), a `TreeMap` of existing bookings, checked against its neighbors, answers each query in O(log n) without needing a full segment tree. Constraints: up to 1,000 calls to `book`.

## 3. Core concept

**Key idea:** keep all booked events in a `TreeMap<Integer, Integer>` keyed by `start`, mapping to `end`. A `TreeMap` keeps entries sorted by key, so the only two bookings that could possibly overlap a new `[start, end)` are the one immediately **before** it (`floorEntry(start)`) and the one immediately **after** it (`ceilingEntry(start)`) — every other booking is either entirely before or entirely after and cannot overlap.

**Steps:**
1. Find `floorEntry(start)` — the closest existing booking starting at or before `start`. If it exists and `floorEntry.end > start`, the new event overlaps it — return `false`.
2. Find `ceilingEntry(start)` — the closest existing booking starting at or after `start`. If it exists and `ceilingEntry.start < end`, the new event overlaps it — return `false`.
3. Otherwise, insert `(start, end)` into the map and return `true`.

**Why checking only these two neighbors is sufficient:** bookings in a `TreeMap` are sorted by start time and, since successful bookings never overlap each other, they also never overlap in a way that would let some *farther* booking touch the new interval while its immediate neighbor does not. If the immediate predecessor does not overlap, every earlier booking (ending even sooner) cannot either; symmetric logic applies to the successor.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A new booking checked only against its floor and ceiling neighbors in a sorted TreeMap of existing bookings">
  <g font-family="sans-serif" font-size="13">
    <rect x="50" y="40" width="120" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="110" y="60" fill="#0d1117" text-anchor="middle" font-size="11">[10,20) existing</text>
    <rect x="400" y="40" width="120" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="460" y="60" fill="#0d1117" text-anchor="middle" font-size="11">[50,60) existing</text>
    <rect x="200" y="90" width="150" height="30" fill="#f0883e" opacity="0.6"/>
    <text x="275" y="110" fill="#0d1117" text-anchor="middle" font-size="11">[25,40) new booking</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">floor=[10,20), ceiling=[50,60): neither overlaps -&gt; book succeeds</text>
  </g>
</svg>

The new booking `[25,40)` only needs to check against its immediate floor and ceiling neighbors — every other existing booking is provably too far away to overlap.

## 5. Runnable example

**Level 1 — Brute force.** Store all bookings in a list, and on each `book` call, scan the entire list checking for overlap against every existing entry. O(n) per call.

**KEY INSIGHT:** since successful bookings never overlap each other, they stay naturally sorted and non-overlapping — only the two neighbors immediately adjacent to a new booking's start time can possibly conflict with it.

**Level 2 — Optimal.** `TreeMap` with `floorEntry`/`ceilingEntry`, O(log n) per call.

**Level 3 — Hardened.** Handles half-open interval semantics correctly (touching endpoints, like `[10,20)` and `[20,30)`, do not overlap), and the first booking ever made (both neighbor lookups return `null`).

```java
// MyCalendarI.java
import java.util.*;

public class MyCalendarI {

    TreeMap<Integer, Integer> bookings = new TreeMap<>();

    public boolean book(int start, int end) {
        Map.Entry<Integer, Integer> floor = bookings.floorEntry(start);
        if (floor != null && floor.getValue() > start) {
            return false; // overlaps the booking that starts at or before `start`
        }
        Map.Entry<Integer, Integer> ceiling = bookings.ceilingEntry(start);
        if (ceiling != null && ceiling.getKey() < end) {
            return false; // overlaps the booking that starts at or after `start`
        }
        bookings.put(start, end);
        return true;
    }

    public static void main(String[] args) {
        MyCalendarI cal = new MyCalendarI();
        System.out.println(cal.book(10, 20)); // true
        System.out.println(cal.book(15, 25)); // false, overlaps [10,20)
        System.out.println(cal.book(20, 30)); // true, touches but does not overlap
    }
}
```

**How to run:** save as `MyCalendarI.java`, then run `java MyCalendarI.java`.

## 6. Walkthrough

Trace `book(10,20)`, `book(15,25)`, `book(20,30)`:

| call | floorEntry(start) | overlap? | ceilingEntry(start) | overlap? | result |
|---|---|---|---|---|---|
| book(10,20) | none | no | none | no | `true`; map={10:20} |
| book(15,25) | (10,20) | `20 > 15` -> yes | — | — | `false` |
| book(20,30) | (10,20) | `20 > 20`? no | none | no | `true`; map={10:20, 20:30} |

The second call fails because the existing booking `[10,20)` extends past the new booking's start (`15`). The third call succeeds because `end=20` of the existing booking is not greater than `start=20` of the new one — they touch but do not overlap.

## 7. Gotchas & takeaways

> Gotcha: using `end >= start` instead of `end > start` (and symmetrically for the ceiling check) treats touching intervals as overlapping, which is wrong for this problem's half-open `[start, end)` semantics — `[10,20)` and `[20,30)` are adjacent, not overlapping.

- Signal: repeated "does this new range conflict with anything already recorded" checks are a range-query pattern; a sorted structure like `TreeMap` is often simpler than a full segment tree when the number of calls is small.
- Only the two `TreeMap` neighbors immediately around a new interval's start can possibly overlap it, thanks to the invariant that existing bookings never overlap each other.
- Related problems: My Calendar II (allows one overlap, not two), My Calendar III (tracks the maximum overlap depth).
