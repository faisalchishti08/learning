---
card: leetcode-patterns
gi: 571
slug: falling-squares
title: Falling Squares
---

## 1. What it is

Squares fall one at a time onto an infinite number line (the x-axis), each described by `positions[i] = [left, sideLength]`. A square lands on top of the tallest existing stack of squares that overlaps its horizontal span `[left, left + sideLength)`, then stays there. After each square lands, record the **tallest height across the entire number line so far**. Example: `positions = [[1,2],[2,3],[6,1]]` → `[2,5,5]`.

## 2. Why & when

Each square's landing height depends on a **range-max query** over its horizontal span, and landing there is a **range update** setting that whole span to the new (taller) height. This is exactly the [segment tree](0561-segment-tree-bit-template-segment-tree-or-fenwick-tree-over.md) signal — but the update is a range **assignment** (set to a value), not a range add, so the segment tree needs lazy propagation for "assign the max of this range to at least this height." Constraints: up to 1,000 squares, positions up to `10^8`.

## 3. Core concept

**Key idea:** coordinate-compress every square's left and right (`left + sideLength`) boundary into a sorted list of critical x-coordinates. Build a segment tree over the **elementary intervals** between consecutive critical coordinates (not over raw x-values, which could span up to `10^8`). For each square: query the maximum height already present across its horizontal span, compute its landing height as that maximum plus its own side length, then update that same span so every covered interval's height becomes at least this new height.

**Steps:**
1. Collect every square's `left` and `right = left + sideLength` into a sorted set of critical coordinates; map each to its index.
2. Build a segment tree (array-backed, with lazy propagation) over the `m - 1` elementary intervals between consecutive critical coordinates, all starting at height `0`.
3. For each square: convert `[left, right)` into the corresponding leaf-index range `[li, ri]` using the coordinate map. Query the current maximum height over `[li, ri]`.
4. Compute `newHeight = queryMax + sideLength`. Update `[li, ri]` so every covered leaf's height becomes `max(currentHeight, newHeight)` (using a lazy "assign at least this height" propagation).
5. Track a running global maximum across all updates so far, and append it to the result after each square.

**Why the range update is "assign the max" and not "add":** a falling square does not stack its height *on top of* every point in its span additively — it rests flat, at one single height, across its entire footprint, replacing whatever was there (which, by construction, can never exceed the new height, since the new height was computed as the query's own maximum plus the square's height). This is fundamentally a "range max assignment," a different lazy-propagation shape than the "range add" used in problems like My Calendar III.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Square 2 spanning [2,5) lands on top of square 1's height at x=2, reaching a new height of 5 across its whole span">
  <g font-family="sans-serif" font-size="12">
    <rect x="50" y="120" width="100" height="40" fill="#3fb950" opacity="0.7"/>
    <text x="100" y="145" fill="#0d1117" text-anchor="middle" font-size="11">square1: [1,3) h=2</text>
    <rect x="100" y="40" width="200" height="80" fill="#f0883e" opacity="0.7"/>
    <text x="200" y="85" fill="#0d1117" text-anchor="middle" font-size="11">square2: [2,5) lands at h=2+3=5</text>
    <text x="400" y="90" fill="#79c0ff">query max over [2,5) finds square1's height 2 at x=2</text>
    <text x="400" y="115" fill="#3fb950">entire [2,5) span becomes height 5, even where nothing was before</text>
  </g>
</svg>

Square 2's landing height comes from the tallest point in its footprint (square 1's height of `2`), but the resulting height of `5` covers its *entire* span, including the previously-empty part.

## 5. Runnable example

**Level 1 — Brute force.** For each square, scan a height array over every unit x-coordinate in its span, taking the max, then filling the span with the new height. O(n * range width) — infeasible for positions up to `10^8`.

**KEY INSIGHT:** coordinate-compressing to only the O(n) critical boundaries actually mentioned by the input, then using a segment tree with range-max-assignment lazy propagation, avoids ever touching the huge raw coordinate range.

**Level 2 — Optimal.** Coordinate compression plus a segment tree with lazy "assign at least this height" propagation, O(n log n).

**Level 3 — Hardened.** Handles a square that lands entirely on empty ground (`queryMax = 0`), and squares with overlapping but not identical spans.

```java
// FallingSquares.java
import java.util.*;

public class FallingSquares {

    static class SegTree {
        int[] maxHeight;
        int[] lazy;

        SegTree(int size) {
            maxHeight = new int[4 * Math.max(size, 1)];
            lazy = new int[4 * Math.max(size, 1)];
        }

        void pushDown(int node) {
            if (lazy[node] == 0) return;
            int leftChild = 2 * node + 1, rightChild = 2 * node + 2;
            maxHeight[leftChild] = Math.max(maxHeight[leftChild], lazy[node]);
            lazy[leftChild] = Math.max(lazy[leftChild], lazy[node]);
            maxHeight[rightChild] = Math.max(maxHeight[rightChild], lazy[node]);
            lazy[rightChild] = Math.max(lazy[rightChild], lazy[node]);
            lazy[node] = 0;
        }

        void update(int node, int start, int end, int l, int r, int height) {
            if (r < start || end < l) return;
            if (l <= start && end <= r) {
                maxHeight[node] = Math.max(maxHeight[node], height);
                lazy[node] = Math.max(lazy[node], height);
                return;
            }
            pushDown(node);
            int mid = (start + end) / 2;
            update(2 * node + 1, start, mid, l, r, height);
            update(2 * node + 2, mid + 1, end, l, r, height);
            maxHeight[node] = Math.max(maxHeight[2 * node + 1], maxHeight[2 * node + 2]);
        }

        int query(int node, int start, int end, int l, int r) {
            if (r < start || end < l) return 0;
            if (l <= start && end <= r) return maxHeight[node];
            pushDown(node);
            int mid = (start + end) / 2;
            return Math.max(query(2 * node + 1, start, mid, l, r),
                             query(2 * node + 2, mid + 1, end, l, r));
        }
    }

    static List<Integer> fallingSquares(int[][] positions) {
        TreeSet<Integer> coordSet = new TreeSet<>();
        for (int[] p : positions) {
            coordSet.add(p[0]);
            coordSet.add(p[0] + p[1]);
        }
        List<Integer> coords = new ArrayList<>(coordSet);
        Map<Integer, Integer> indexOf = new HashMap<>();
        for (int i = 0; i < coords.size(); i++) indexOf.put(coords.get(i), i);

        int leafCount = Math.max(coords.size() - 1, 1);
        SegTree tree = new SegTree(leafCount);

        List<Integer> result = new ArrayList<>();
        int globalMax = 0;
        for (int[] p : positions) {
            int left = p[0], right = p[0] + p[1], side = p[1];
            int li = indexOf.get(left);
            int ri = indexOf.get(right) - 1;

            int base = tree.query(0, 0, leafCount - 1, li, ri);
            int newHeight = base + side;
            tree.update(0, 0, leafCount - 1, li, ri, newHeight);

            globalMax = Math.max(globalMax, newHeight);
            result.add(globalMax);
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] positions = {{1, 2}, {2, 3}, {6, 1}};
        System.out.println(fallingSquares(positions)); // [2, 5, 5]
    }
}
```

**How to run:** save as `FallingSquares.java`, then run `java FallingSquares.java`.

## 6. Walkthrough

Trace `fallingSquares([[1,2],[2,3],[6,1]])`. Critical coordinates: `{1,2,3,5,6,7}`, giving elementary intervals `[1,2), [2,3), [3,5), [5,6), [6,7)` at leaf indices `0..4`.

| square | span (leaf indices) | query max | newHeight | globalMax |
|---|---|---|---|---|
| [1,2) → [1,3) | li=0, ri=1 | 0 | 0+2=2 | 2 |
| [2,3) → [2,5) | li=1, ri=2 | 2 (leaf 1 already set to 2) | 2+3=5 | 5 |
| [6,1) → [6,7) | li=4, ri=4 | 0 (untouched) | 0+1=1 | 5 (unchanged) |

Result: `[2, 5, 5]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using `indexOf.get(right)` directly (instead of `indexOf.get(right) - 1`) as the range's upper leaf index off-by-ones the span by one elementary interval too far, since `right` is the boundary coordinate *after* the square's footprint, not part of it — always subtract 1 to get the last leaf actually inside `[left, right)`.

- Signal: "an object rests at the max height/value across its footprint, then that whole footprint updates to the new value" is a range-max-query plus range-max-assignment segment tree problem, distinct from the range-*add* pattern used elsewhere in this section.
- Coordinate compression is essential whenever the update/query range spans a huge coordinate space but only a small number of distinct boundaries actually matter.
- Related problems: My Calendar III (range-add instead of range-assign), Range Sum Query 2D - Mutable.
