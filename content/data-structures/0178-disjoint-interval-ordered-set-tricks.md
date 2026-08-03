---
card: data-structures
gi: 178
slug: disjoint-interval-ordered-set-tricks
title: Disjoint interval / ordered set tricks
---

## 1. What it is

This is a technique, not a new structure: use an ordered map or set — Java's [TreeMap or TreeSet](0113-treemap-treeset-red-black-backed.md), backed by a red-black tree — to maintain a collection of **non-overlapping intervals**, keyed by each interval's start. Because the map stays sorted, you can find the interval immediately before or after any point in `O(log n)`, which is exactly what merging and querying intervals needs.

## 2. Why & when

Use this when you need to insert intervals one at a time, automatically merging any that overlap or touch, and later query "which interval (if any) contains this point?" — booking systems, tracking free/busy time ranges, or "merge intervals" style problems that arrive incrementally rather than all at once. A `TreeMap<Integer, Integer>` (start to end) gives you `O(log n)` neighbor lookups via `floorKey` and `ceilingKey`, which a plain sorted array cannot do without an `O(n)` shift on every insert.

## 3. Core concept

**The shape.** A `TreeMap<Integer, Integer>` where each entry `start -> end` represents one interval, and the invariant is that no two entries overlap or touch — every gap between consecutive intervals is real.

**The key operations a `TreeMap` provides that make this work.**
- `floorEntry(x)`: the entry with the largest key `<= x` — the interval that might start before or at `x` and could contain or touch it.
- `ceilingEntry(x)`: the entry with the smallest key `>= x` — the next interval at or after `x`.
- `headMap` / `tailMap` / `subMap`: a view of all entries strictly before, after, or between two keys — used to find every interval that a new insertion overlaps.

**Inserting a new interval `[start, end]` while keeping the set merged.** First, check `floorEntry(start)`: if it exists and its `end >= start`, it overlaps the new interval, so extend the new interval's `start` to that entry's start and remove it. Then repeatedly check `ceilingEntry(start)` (or the current merged start): while the next interval's `start <= end`, it overlaps too — extend `end` to cover it and remove it. Finally, insert the fully-merged `[start, end]`.

**Why sorted-map neighbor queries beat a plain array here.** An array approach to "find all intervals overlapping this new one" needs either a full scan (`O(n)`) or a binary search plus a scan of overlapping neighbors (still `O(n)` worst case, when many intervals merge at once, but `O(log n)` to *locate* the starting point). A `TreeMap` gives `O(log n)` to find where to start, and removal of merged entries is also `O(log n)` each — well-suited to a workload of many incremental insertions.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A TreeMap of disjoint intervals, with a new interval insertion using floorEntry and ceilingEntry to find and merge overlapping neighbors">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Existing intervals in TreeMap: [1,3] [6,9] [12,15]</text>
    <line x1="20" y1="40" x2="600" y2="40" stroke="#8b949e"/>
    <rect x="30" y="30" width="60" height="20" fill="#161b22" stroke="#79c0ff"/><text x="60" y="44" text-anchor="middle" font-size="8">[1,3]</text>
    <rect x="150" y="30" width="90" height="20" fill="#161b22" stroke="#79c0ff"/><text x="195" y="44" text-anchor="middle" font-size="8">[6,9]</text>
    <rect x="330" y="30" width="90" height="20" fill="#161b22" stroke="#79c0ff"/><text x="375" y="44" text-anchor="middle" font-size="8">[12,15]</text>

    <text x="10" y="90">Insert [2, 8]:</text>
    <rect x="60" y="80" width="240" height="20" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="180" y="94" text-anchor="middle" font-size="8">[2,8] overlaps [1,3] and [6,9]</text>

    <text x="10" y="140">floorEntry(2) -&gt; [1,3], overlaps -&gt; extend start to 1, remove [1,3]</text>
    <text x="10" y="160">ceilingEntry(1) -&gt; [6,9], 6&lt;=8 overlaps -&gt; extend end to 9, remove [6,9]</text>
    <text x="10" y="180" fill="#3fb950">result: [1,9] and [12,15] -- fully merged, still disjoint and sorted</text>
  </g>
</svg>

`floorEntry` and `ceilingEntry` locate exactly the neighbors that might overlap a new insertion.

## 5. Runnable example

```java
// DisjointIntervalTricks.java
import java.util.*;

public class DisjointIntervalTricks {

    // Basic: insert intervals one at a time into a TreeMap, merging overlaps as they arrive.
    static class IntervalSet {
        TreeMap<Integer, Integer> intervals = new TreeMap<>();

        void insert(int start, int end) {
            Map.Entry<Integer, Integer> lower = intervals.floorEntry(start);
            if (lower != null && lower.getValue() >= start) {
                start = Math.min(start, lower.getKey());
                end = Math.max(end, lower.getValue());
                intervals.remove(lower.getKey());
            }

            Map.Entry<Integer, Integer> next = intervals.ceilingEntry(start);
            while (next != null && next.getKey() <= end) {
                end = Math.max(end, next.getValue());
                intervals.remove(next.getKey());
                next = intervals.ceilingEntry(start);
            }

            intervals.put(start, end);
        }
    }

    static void basicLevel() {
        IntervalSet set = new IntervalSet();
        set.insert(1, 3);
        set.insert(6, 9);
        set.insert(12, 15);
        set.insert(2, 8); // merges [1,3] and [6,9] into [1,9]

        System.out.println("basic: merged intervals -> " + set.intervals);
    }

    // Intermediate: query "which interval, if any, contains this point?" using floorEntry.
    static Integer[] containingInterval(IntervalSet set, int point) {
        Map.Entry<Integer, Integer> candidate = set.intervals.floorEntry(point);
        if (candidate != null && candidate.getValue() >= point) {
            return new Integer[]{candidate.getKey(), candidate.getValue()};
        }
        return null;
    }

    static void intermediateLevel() {
        IntervalSet set = new IntervalSet();
        set.insert(1, 9);
        set.insert(12, 15);

        System.out.println("intermediate: containing(5) -> " + Arrays.toString(containingInterval(set, 5)));
        System.out.println("intermediate: containing(10) -> " + Arrays.toString(containingInterval(set, 10)));
        System.out.println("intermediate: containing(13) -> " + Arrays.toString(containingInterval(set, 13)));
    }

    // Advanced: "employee free time" style problem -- given many merged busy intervals, find the gaps.
    static List<int[]> findGaps(IntervalSet set, int rangeStart, int rangeEnd) {
        List<int[]> gaps = new ArrayList<>();
        int cursor = rangeStart;
        for (Map.Entry<Integer, Integer> entry : set.intervals.entrySet()) {
            if (entry.getKey() > cursor) {
                gaps.add(new int[]{cursor, entry.getKey()});
            }
            cursor = Math.max(cursor, entry.getValue());
        }
        if (cursor < rangeEnd) gaps.add(new int[]{cursor, rangeEnd});
        return gaps;
    }

    static void advancedLevel() {
        IntervalSet busy = new IntervalSet();
        busy.insert(9, 10);
        busy.insert(12, 13);
        busy.insert(16, 18);

        List<int[]> freeTime = findGaps(busy, 9, 18);
        for (int[] gap : freeTime) System.out.println("advanced: free time -> [" + gap[0] + ", " + gap[1] + "]");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java DisjointIntervalTricks.java`

## 6. Walkthrough

Start with `[1,3]`, `[6,9]`, `[12,15]` already inserted. Call `insert(2, 8)`. First, `floorEntry(2)` finds `[1,3]` (largest key `<= 2`). Since `3 >= 2`, they overlap: extend `start` to `min(2,1) = 1` and `end` to `max(8,3) = 8`, then remove `[1,3]`.

Next, `ceilingEntry(1)` (using the updated `start`) finds `[6,9]` (smallest remaining key `>= 1`). Since `6 <= 8` (the current `end`), they overlap too: extend `end` to `max(8,9) = 9`, remove `[6,9]`. Check `ceilingEntry(1)` again: now finds `[12,15]`, but `12 > 9`, so the loop stops — no more overlaps.

Insert the fully merged `[1, 9]`. The final map holds `{1=9, 12=15}` — two disjoint intervals, correctly merged from four insertions.

For `containingInterval(5)`: `floorEntry(5)` finds `[1,9]` (key `1 <= 5`), and since `9 >= 5`, the point `5` is inside it — return `[1,9]`. For `containingInterval(10)`: `floorEntry(10)` also finds `[1,9]`, but `9 < 10`, so it does **not** contain `10` — return `null`, correctly identifying the gap between the two intervals.

**Complexity.** Insert (with merging): `O(log n)` to find the floor/ceiling neighbors, plus `O(k log n)` to remove the `k` intervals that get merged away — each individual insert is `O(log n)` amortized, since any interval can only be merged away once across the whole sequence of insertions. Point-containment query: `O(log n)`.

## 7. Gotchas & takeaways

> The check `lower.getValue() >= start` (not `>`) is what correctly merges **touching** intervals like `[1,3]` and `[3,5]` into `[1,5]`, not just strictly overlapping ones. Whether touching intervals should merge depends on the problem statement — read it carefully, since `>` vs `>=` changes this behavior.

- Always re-fetch `ceilingEntry(start)` inside the `while` loop after each removal — caching the iterator or entry from before a removal can throw a `ConcurrentModificationException` or read stale data.
- This technique assumes intervals are inserted with **known endpoints** and merging is the goal. For fixed, unchanging intervals where you need every overlap with many queries (not insertion-time merging), an [interval tree](0154-interval-tree.md) is the more direct fit.
- `TreeMap`'s `O(log n)` guarantees come from its red-black tree backing — the same reason it beats a `HashMap` (no ordering) or a plain sorted `ArrayList` (`O(n)` insertion due to shifting) for this exact use case.
