---
card: leetcode-patterns
gi: 81
slug: data-stream-as-disjoint-intervals
title: Data Stream as Disjoint Intervals
---

## 1. What it is

Design a class that receives a stream of integers, one at a time via `addNum(value)`, and can return the current set of disjoint (non-overlapping) intervals covering all numbers seen so far via `getIntervals()`. Example: after calling `addNum(1)`, `addNum(3)`, `addNum(7)`, `addNum(2)`, `addNum(6)`, `getIntervals()` returns `[[1,3],[6,7]]`.

## 2. Why & when

Re-sorting and re-merging the entire set of seen numbers from scratch on every `addNum` call wastes work, since most numbers do not change the interval structure much. Maintaining an ordered map of interval boundaries, updated incrementally, keeps each insertion fast — while still relying on the same Merge Intervals idea to decide whether a new number joins an existing interval or starts a new one.

## 3. Core concept

**Key idea:** keep a sorted map from each interval's start value to its end value. When a new number arrives, find its potential neighbors (the interval ending just before it, and the interval starting just after it) and decide whether to merge with one or both, extend one, or insert a brand-new single-number interval.

**Steps for `addNum(value)`:**
1. If `value` already falls inside an existing interval, do nothing.
2. Check whether `value - 1` is the end of some interval (a "left neighbor" to merge with) and whether `value + 1` is the start of some interval (a "right neighbor" to merge with).
3. Merge according to which neighbors exist:
   - Both neighbors exist: merge all three into one interval (left neighbor's start to right neighbor's end); remove the right neighbor's old entry.
   - Only the left neighbor exists: extend it by moving its end to `value`.
   - Only the right neighbor exists: extend it by moving its start (the map key) to `value`.
   - Neither exists: insert a new single-value interval `[value, value]`.

**Steps for `getIntervals()`:** return the sorted map's entries directly as `[start, end]` pairs — the map's natural ordering already keeps them sorted and merged.

**Why it is correct:** because every insertion immediately re-merges with any adjacent interval, the map is always kept in the fully-merged state — the same end state Merge Intervals would compute from scratch, but reached incrementally in O(log n) per insertion instead of O(n log n) per call.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Incremental interval merging as new numbers arrive">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">stream: addNum(1), addNum(3), addNum(7), addNum(2), addNum(6)</text>
    <text x="20" y="45" fill="#8b949e">after 1: [[1,1]]</text>
    <text x="20" y="65" fill="#8b949e">after 3: [[1,1],[3,3]] (not adjacent to 1)</text>
    <text x="20" y="85" fill="#8b949e">after 7: [[1,1],[3,3],[7,7]]</text>
    <text x="20" y="105" fill="#3fb950">after 2: 2 has left neighbor 1 AND right neighbor 3 -&gt; merge into [[1,3],[7,7]]</text>
    <text x="20" y="125" fill="#3fb950">after 6: 6 has right neighbor 7, no left neighbor -&gt; extend to [[1,3],[6,7]]</text>
  </g>
</svg>

Each new number checks only its immediate left and right neighbors in the sorted map, merging incrementally instead of re-scanning every interval seen so far.

## 5. Runnable example

```java
// DataStreamAsDisjointIntervals.java
import java.util.*;

public class DataStreamAsDisjointIntervals {

    // Level 1 -- Brute force: store every raw number in a sorted set;
    // rebuild the merged interval list from scratch on every
    // getIntervals() call. O(n) per addNum insert into a TreeSet,
    // O(n) per getIntervals rebuild -- wastes repeated full rebuilds.
    static class BruteForce {
        TreeSet<Integer> seen = new TreeSet<>();

        void addNum(int value) { seen.add(value); }

        int[][] getIntervals() {
            List<int[]> result = new ArrayList<>();
            Integer start = null, prev = null;
            for (int v : seen) {
                if (start == null) { start = v; prev = v; }
                else if (v == prev + 1) { prev = v; }
                else { result.add(new int[] {start, prev}); start = v; prev = v; }
            }
            if (start != null) result.add(new int[] {start, prev});
            return result.toArray(new int[0][]);
        }
    }

    // KEY INSIGHT: only the interval immediately before and after the new
    // value can possibly merge with it -- a TreeMap keyed by interval
    // start lets each addNum touch just those two neighbors, O(log n),
    // keeping the structure always fully merged.

    // Level 2 -- Optimal: TreeMap of start -> end, merged incrementally.
    // O(log n) per addNum, O(n) per getIntervals (just reading the map).
    static class SummaryRanges {
        TreeMap<Integer, Integer> intervals = new TreeMap<>();

        void addNum(int value) {
            Map.Entry<Integer, Integer> floor = intervals.floorEntry(value);
            if (floor != null && floor.getValue() >= value) return; // already covered

            boolean mergeLeft = floor != null && floor.getValue() + 1 == value;
            Map.Entry<Integer, Integer> ceiling = intervals.higherEntry(value);
            boolean mergeRight = ceiling != null && ceiling.getKey() - 1 == value;

            if (mergeLeft && mergeRight) {
                intervals.put(floor.getKey(), ceiling.getValue());
                intervals.remove(ceiling.getKey());
            } else if (mergeLeft) {
                intervals.put(floor.getKey(), value);
            } else if (mergeRight) {
                intervals.remove(ceiling.getKey());
                intervals.put(value, ceiling.getValue());
            } else {
                intervals.put(value, value);
            }
        }

        int[][] getIntervals() {
            int[][] result = new int[intervals.size()][2];
            int i = 0;
            for (Map.Entry<Integer, Integer> e : intervals.entrySet()) {
                result[i++] = new int[] {e.getKey(), e.getValue()};
            }
            return result;
        }
    }

    public static void main(String[] args) {
        BruteForce bf = new BruteForce();
        for (int v : new int[] {1, 3, 7, 2, 6}) bf.addNum(v);
        System.out.println("brute force: " + Arrays.deepToString(bf.getIntervals()));

        SummaryRanges opt = new SummaryRanges();
        for (int v : new int[] {1, 3, 7, 2, 6}) opt.addNum(v);
        System.out.println("optimal:     " + Arrays.deepToString(opt.getIntervals()));

        // Level 3 -- Hardened: adding a duplicate number that already
        // falls inside an existing interval must be a no-op.
        opt.addNum(2); // already covered by [1,3]
        System.out.println("after duplicate add(2): " + Arrays.deepToString(opt.getIntervals()));
    }
}
```

How to run: save as `DataStreamAsDisjointIntervals.java`, then run `java DataStreamAsDisjointIntervals.java`.

## 6. Walkthrough

Trace `SummaryRanges` receiving `1, 3, 7, 2, 6` in order:

1. `addNum(1)`: no floor, no ceiling entry exists yet. Insert `[1,1]`.
2. `addNum(3)`: floor is `[1,1]`, `1 + 1 == 3`? No (`2 != 3`) — no left merge. No ceiling. Insert `[3,3]`. Map: `{1:1, 3:3}`.
3. `addNum(7)`: floor is `[3,3]`, no merge; no ceiling. Insert `[7,7]`. Map: `{1:1, 3:3, 7:7}`.
4. `addNum(2)`: floor is `[1,1]`, `1 + 1 == 2` — left merge. Ceiling is `[3,3]`, `3 - 1 == 2` — right merge. Both merge: `put(1, 3)`, remove `3`. Map: `{1:3, 7:7}`.
5. `addNum(6)`: floor is `[1,3]`, `3 + 1 == 6`? No — no left merge. Ceiling is `[7,7]`, `7 - 1 == 6` — right merge. `remove(7)`, `put(6, 7)`. Map: `{1:3, 6:7}`.

`getIntervals()` returns `[[1,3],[6,7]]`, matching the expected result. Time complexity: O(log n) per `addNum` (TreeMap operations), O(k) per `getIntervals` where `k` is the number of merged intervals. Space complexity: O(k) for the map.

## 7. Gotchas & takeaways

> Gotcha: forgetting the very first check — whether `value` already falls inside the `floorEntry`'s range (`floor.getValue() >= value`) — causes duplicate or already-covered numbers to incorrectly create overlapping or redundant entries in the map.

- This problem shows the "maintain the merged state incrementally" variant of Merge Intervals, useful whenever data arrives over time rather than all at once.
- Related problems: Merge Intervals (the batch version this design avoids re-running), Insert Interval (a single incremental insert, but into an array rather than a live streaming structure).
