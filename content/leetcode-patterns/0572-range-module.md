---
card: leetcode-patterns
gi: 572
slug: range-module
title: Range Module
---

## 1. What it is

Design a `RangeModule` that tracks which half-open integer ranges `[left, right)` are currently "tracked." It supports `addRange(left, right)` (mark every integer in the range as tracked), `queryRange(left, right)` (return `true` only if **every** integer in the range is currently tracked), and `removeRange(left, right)` (unmark every integer in the range). Example: `addRange(10,20)`, `removeRange(14,16)`, `queryRange(10,14)` → `true`; `queryRange(13,15)` → `false` (index `14` was removed).

## 2. Why & when

This is the most general problem in the [Segment Tree / BIT](0560-segment-tree-bit-signal-range-queries-with-point-range-updat.md) family covered so far: it needs range **assignment** in both directions (mark tracked, mark untracked) plus a range **query** that must confirm *every* point in a range agrees (not just report a max or sum). A `TreeMap` of merged, non-overlapping tracked intervals is the standard efficient approach — conceptually a "compressed" segment tree that only stores the boundaries where the tracked/untracked state actually changes. Constraints: up to 10,000 calls, values up to `10^9`.

## 3. Core concept

**Key idea:** maintain a `TreeMap<Integer, Integer>` where each entry `(start, end)` represents one maximal tracked interval, and no two entries ever touch or overlap (they are always merged into the fewest possible intervals). `addRange` finds every existing interval that overlaps or touches the new range, merges them all into one combined interval, and replaces them. `removeRange` finds every existing interval that overlaps the range to remove, and either shrinks, splits, or deletes each one so the removed portion is gone. `queryRange` finds the single interval (if any) that could fully contain the query range and checks it directly.

**Steps for `addRange(left, right)`:**
1. Find the entry with the largest `start <= right` (via `floorEntry(right)`) — begin scanning backward from there, and consider extending `left` down to the start of any adjacent/overlapping earlier interval, and `right` up to the end of any adjacent/overlapping later interval.
2. Remove every interval fully absorbed by the (possibly extended) `[left, right)` range.
3. Insert the single merged interval `(left, right)`.

**Steps for `removeRange(left, right)`:**
1. Find every existing interval that overlaps `[left, right)`.
2. For each: if it extends before `left`, keep the portion before `left` as a new (shrunk) interval. If it extends after `right`, keep the portion after `right` as a new (shrunk) interval. Remove the original entry (replaced by 0, 1, or 2 shrunk pieces).

**Steps for `queryRange(left, right)`:** find `floorEntry(left)` — the one interval that could possibly contain `[left, right)` entirely. Return `true` only if it exists and its `end >= right`.

**Why intervals are kept merged and non-overlapping at all times:** this invariant is what makes both `floorEntry` lookups and the "at most a few intervals affected per call" bound work — without merging, `addRange` calls could accumulate many small overlapping fragments over time, and both `queryRange` and future `addRange`/`removeRange` calls would need to inspect an unbounded number of them instead of a small, predictable set.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="removeRange splitting one tracked interval into two smaller tracked intervals around the removed portion">
  <g font-family="sans-serif" font-size="12">
    <rect x="50" y="30" width="300" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="200" y="50" fill="#0d1117" text-anchor="middle" font-size="11">tracked [10,20)</text>
    <rect x="170" y="80" width="60" height="30" fill="#f0883e" opacity="0.7"/>
    <text x="200" y="100" fill="#0d1117" text-anchor="middle" font-size="10">removeRange(14,16)</text>
    <rect x="50" y="130" width="120" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="110" y="150" fill="#0d1117" text-anchor="middle" font-size="10">[10,14)</text>
    <rect x="230" y="130" width="120" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="290" y="150" fill="#0d1117" text-anchor="middle" font-size="10">[16,20)</text>
  </g>
</svg>

Removing `[14,16)` from the tracked interval `[10,20)` splits it into two remaining tracked intervals, `[10,14)` and `[16,20)`.

## 5. Runnable example

**Level 1 — Brute force.** Track state with a `boolean[]` array over the entire possible value range, or a `HashSet<Integer>` of tracked points. Infeasible for a `10^9` range, and each range operation costs O(range width) either way.

**KEY INSIGHT:** since only interval boundaries ever matter, keeping a `TreeMap` of merged, non-overlapping intervals compresses the representation to O(number of calls) entries, regardless of the coordinate range.

**Level 2 — Optimal.** `TreeMap`-based interval merging/splitting, O(log n + k) per call, where k is the number of intervals actually touched.

**Level 3 — Hardened.** Handles `addRange` calls that bridge two previously separate intervals into one, and `removeRange` calls that fully delete an interval with nothing left over.

```java
// RangeModule.java
import java.util.*;

public class RangeModule {

    TreeMap<Integer, Integer> ranges = new TreeMap<>(); // start -> end, merged, non-overlapping

    public void addRange(int left, int right) {
        Map.Entry<Integer, Integer> floor = ranges.floorEntry(left);
        if (floor != null && floor.getValue() >= left) {
            left = Math.min(left, floor.getKey());
            right = Math.max(right, floor.getValue());
        }

        Iterator<Map.Entry<Integer, Integer>> it = ranges.tailMap(left).entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Integer, Integer> entry = it.next();
            if (entry.getKey() > right) break;
            right = Math.max(right, entry.getValue());
            it.remove();
        }
        ranges.put(left, right);
    }

    public boolean queryRange(int left, int right) {
        Map.Entry<Integer, Integer> floor = ranges.floorEntry(left);
        return floor != null && floor.getValue() >= right;
    }

    public void removeRange(int left, int right) {
        Iterator<Map.Entry<Integer, Integer>> it = ranges.tailMap(ranges.floorKey(left) != null ? ranges.floorKey(left) : left)
                .entrySet().iterator();
        List<int[]> toAdd = new ArrayList<>();
        while (it.hasNext()) {
            Map.Entry<Integer, Integer> entry = it.next();
            int start = entry.getKey(), end = entry.getValue();
            if (start >= right) break;
            if (end <= left) continue;

            it.remove();
            if (start < left) toAdd.add(new int[]{start, left});
            if (end > right) toAdd.add(new int[]{right, end});
        }
        for (int[] piece : toAdd) ranges.put(piece[0], piece[1]);
    }

    public static void main(String[] args) {
        RangeModule rm = new RangeModule();
        rm.addRange(10, 20);
        System.out.println(rm.queryRange(10, 14)); // true
        rm.removeRange(14, 16);
        System.out.println(rm.queryRange(10, 14)); // true (unaffected)
        System.out.println(rm.queryRange(13, 15)); // false (14 was removed)
        System.out.println(rm.queryRange(16, 17)); // true (17 still tracked)
    }
}
```

**How to run:** save as `RangeModule.java`, then run `java RangeModule.java`.

## 6. Walkthrough

Trace `addRange(10,20)`, then `removeRange(14,16)`, then the three queries:

1. `addRange(10,20)`: no existing entries, so `ranges = {10: 20}`.
2. `removeRange(14,16)`: finds entry `(10,20)`, which overlaps `[14,16)`. Since `start(10) < left(14)`, keep piece `[10,14)`. Since `end(20) > right(16)`, keep piece `[16,20)`. Remove the original entry, add both pieces: `ranges = {10:14, 16:20}`.
3. `queryRange(10,14)`: `floorEntry(10)` finds `(10,14)`. Its `end(14) >= right(14)` — `true`.
4. `queryRange(13,15)`: `floorEntry(13)` finds `(10,14)`. Its `end(14) >= right(15)`? No (`14 < 15`) — `false`. Correctly detects that index `14` (removed) falls inside the query.
5. `queryRange(16,17)`: `floorEntry(16)` finds `(16,20)`. Its `end(20) >= right(17)` — `true`.

## 7. Gotchas & takeaways

> Gotcha: in `addRange`, checking only `floorEntry(left).getValue() > left` (strict) instead of `>= left` misses the case where the new range starts exactly where an existing interval ends — since intervals are half-open, an existing `[5,10)` and a new `[10,15)` are adjacent and should merge into `[5,15)`, not stay as two separate touching intervals.

- Signal: "track/untrack ranges, then query whether a range is fully tracked" needs both range-assignment directions (mark and unmark) plus an "all points agree" query — a `TreeMap` of merged intervals is the standard, simpler alternative to a full segment tree here, since intervals naturally compress to O(calls) entries.
- Keep tracked intervals merged and non-overlapping at all times — this invariant is what keeps every operation bounded by the number of intervals actually touched, not the coordinate range.
- Related problems: My Calendar I (a read-only version of "does this overlap"), My Calendar III (range-add depth-tracking, a different assignment shape).
