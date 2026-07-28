---
card: leetcode-patterns
gi: 566
slug: my-calendar-ii
title: My Calendar II
---

## 1. What it is

Like [My Calendar I](0565-my-calendar-i.md), but a **double booking** (exactly two events overlapping) is now allowed. A `book(start, end)` call fails only if it would create a **triple booking** — three events all overlapping at some point in time. Example: `book(10,20)` → `true`; `book(15,25)` → `true` (a double booking, allowed); `book(20,30)` → `true`; `book(10,25)` → `false` (would triple-book `[15,20)`, since it already has two events there).

## 2. Why & when

This extends the range-overlap-checking [signal](0560-segment-tree-bit-signal-range-queries-with-point-range-updat.md) from "any overlap" to "would this push some point's overlap count to 3." Tracking not just individual bookings but also the regions that are *already* double-booked lets each new call check against a much smaller set. Constraints: up to 1,000 calls to `book`.

## 3. Core concept

**Key idea:** maintain two lists: `bookings` (every successfully booked event) and `overlaps` (every region currently covered by exactly two overlapping bookings — the "danger zones" where a third booking cannot be allowed). A new booking is rejected only if it overlaps any interval in `overlaps`. If accepted, compute its intersection with every existing single booking and add each such intersection to `overlaps` (these are the new double-booked regions this booking creates), then add the new event to `bookings`.

**Steps:**
1. For the new interval `(start, end)`: check it against every interval in `overlaps`. If any overlap, return `false` immediately — accepting would create a triple booking somewhere.
2. Otherwise, for every existing interval in `bookings`, compute its intersection with `(start, end)` (if any); add each non-empty intersection to `overlaps`.
3. Add `(start, end)` to `bookings`. Return `true`.

**Why checking against `overlaps` (not `bookings`) is what enforces the "at most double" rule:** a new booking overlapping a *single* existing booking only creates a double booking — always allowed. It is only overlapping an already-double-booked region that would push some point to three simultaneous events, which is exactly what `overlaps` tracks and blocks.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three events where the third would triple-book the region already double-booked by the first two">
  <g font-family="sans-serif" font-size="12">
    <rect x="50" y="20" width="150" height="25" fill="#3fb950" opacity="0.6"/>
    <text x="125" y="37" fill="#0d1117" text-anchor="middle" font-size="10">[10,20)</text>
    <rect x="150" y="50" width="150" height="25" fill="#3fb950" opacity="0.6"/>
    <text x="225" y="67" fill="#0d1117" text-anchor="middle" font-size="10">[15,25)</text>
    <rect x="150" y="80" width="50" height="20" fill="#f0883e" opacity="0.8"/>
    <text x="175" y="94" fill="#0d1117" text-anchor="middle" font-size="9">overlap [15,20)</text>
    <rect x="50" y="115" width="150" height="25" fill="#79c0ff" opacity="0.6"/>
    <text x="125" y="132" fill="#0d1117" text-anchor="middle" font-size="10">attempt [10,25)</text>
    <text x="400" y="90" fill="#f0883e">attempt overlaps [15,20) region: rejected</text>
  </g>
</svg>

Events `[10,20)` and `[15,25)` together double-book `[15,20)`. A third event `[10,25)` overlaps that region, so it is rejected to avoid a triple booking.

## 5. Runnable example

**Level 1 — Brute force.** For each new booking, count overlaps against every existing single event using a sweep or brute pairwise check for any point reaching count 3. Complex and slow to implement directly per call.

**KEY INSIGHT:** explicitly tracking the double-booked regions as their own interval list turns "would this create a triple booking" into a simple overlap check against that smaller list.

**Level 2 — Optimal.** Maintain `bookings` and `overlaps` lists, O(n) per call (n = calls so far).

**Level 3 — Hardened.** Handles a new booking that partially overlaps multiple existing bookings at once (each intersection is tracked separately), and touching (non-overlapping) intervals.

```java
// MyCalendarII.java
import java.util.*;

public class MyCalendarII {

    List<int[]> bookings = new ArrayList<>();
    List<int[]> overlaps = new ArrayList<>();

    public boolean book(int start, int end) {
        for (int[] overlap : overlaps) {
            if (start < overlap[1] && overlap[0] < end) {
                return false; // would create a triple booking
            }
        }
        for (int[] existing : bookings) {
            int overlapStart = Math.max(start, existing[0]);
            int overlapEnd = Math.min(end, existing[1]);
            if (overlapStart < overlapEnd) {
                overlaps.add(new int[]{overlapStart, overlapEnd});
            }
        }
        bookings.add(new int[]{start, end});
        return true;
    }

    public static void main(String[] args) {
        MyCalendarII cal = new MyCalendarII();
        System.out.println(cal.book(10, 20)); // true
        System.out.println(cal.book(50, 60)); // true
        System.out.println(cal.book(10, 40)); // true, double books [10,20)
        System.out.println(cal.book(5, 15));  // false, would triple book [10,15)
        System.out.println(cal.book(5, 10));  // true, touches [10,...) only
        System.out.println(cal.book(25, 55)); // true, double books [25,40) and [50,55)
    }
}
```

**How to run:** save as `MyCalendarII.java`, then run `java MyCalendarII.java`.

## 6. Walkthrough

Trace `book(10,20)`, `book(50,60)`, `book(10,40)`, `book(5,15)`:

| call | check against overlaps | new overlaps created | bookings after |
|---|---|---|---|
| book(10,20) | none exist | none | [[10,20)] |
| book(50,60) | none overlap | none | [[10,20),[50,60)] |
| book(10,40) | none overlap | intersects [10,20): adds overlap [10,20) | [[10,20),[50,60),[10,40)] |
| book(5,15) | overlaps [10,20) at [10,15) | rejected | unchanged, returns `false` |

The fourth call fails because `[5,15)` overlaps the already-double-booked region `[10,20)` (created by the first and third bookings), which would make `[10,15)` triple-booked.

## 7. Gotchas & takeaways

> Gotcha: computing intersections against `overlaps` (instead of `bookings`) when adding *new* double-booked regions is wrong — the new double-booked regions come from intersecting the new booking with existing *single* bookings, not with existing double-booked regions (which are already correctly checked separately, as the rejection condition).

- Signal: "allow up to K overlapping events, reject anything beyond" generalizes the simple overlap check into tracking regions at each overlap depth explicitly.
- Two parallel interval lists — one for all bookings, one for regions at the "one below the limit" depth — is a clean, small-n-friendly alternative to a full segment tree with lazy propagation.
- Related problems: My Calendar I (the K=1 case), My Calendar III (returns the actual maximum depth, not just a boolean).
