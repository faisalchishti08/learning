---
card: leetcode-patterns
gi: 282
slug: k-closest-points-to-origin
title: K Closest Points to Origin
---

## 1. What it is

Given an array of points on the XY plane and an integer `k`, return the `k` points closest to the origin `(0, 0)`. Distance is the usual Euclidean distance. You may return the answer in any order. Example: `points = [[1,3],[-2,2]]`, `k = 1` → `[[-2,2]]`.

## 2. Why & when

This is the distance-based variant of Top-K Elements: instead of ranking raw numbers, you rank points by a computed score (their squared distance from the origin). It uses the size-k-heap signal. Use this shape whenever a problem ranks compound objects (points, intervals, records) by some derived numeric key, and only the `k` best matter.

## 3. Core concept

**Key idea:** keep a max-heap of size `k`, ordered by squared distance from the origin. When a closer point arrives and the heap is full, evict the current FARTHEST point kept.

**Steps:**
1. Create a max-heap of points, ordered by `x*x + y*y` (squared distance) descending.
2. For each point, offer it to the heap.
3. If the heap size exceeds `k`, poll (remove) the head — the farthest point currently kept.
4. After the scan, the heap holds the `k` closest points.

**Why it is correct:** squared distance preserves the same ordering as true distance, since both `x*x + y*y` and its square root grow together for non-negative values — so comparing squared distances avoids a `Math.sqrt` call with no loss of correctness. The max-heap always discards the single farthest point whenever a closer candidate would otherwise make it overflow past `k`, so the survivors are always the `k` closest seen so far.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap of size 1 by squared distance, keeping the closer of two points to the origin">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">points = [[1,3], [-2,2]], k = 1</text>
    <text x="10" y="45">[1,3]:  dist^2 = 1 + 9  = 10</text>
    <text x="10" y="65">[-2,2]: dist^2 = 4 + 4  = 8</text>
    <text x="10" y="90">see [1,3]  -&gt; heap [ (10,[1,3]) ]</text>
    <text x="10" y="110">see [-2,2] -&gt; 8 &lt; max(10) -&gt; evict [1,3], insert [-2,2]</text>
    <rect x="10" y="125" width="150" height="24" fill="#3fb950"/><text x="85" y="142" fill="#0d1117" text-anchor="middle" font-size="10">result = [[-2, 2]]</text>
  </g>
</svg>

The max-heap evicts the farthest point whenever a strictly closer one arrives.

## 5. Runnable example

```java
// KClosestPointsToOrigin.java
import java.util.*;

public class KClosestPointsToOrigin {

    // Level 1 -- Brute force: sort all points by squared distance
    // ascending, take the first k. Correct, but O(n log n), sorting
    // every point even though only k are needed.

    // KEY INSIGHT: squared distance preserves ordering, avoiding
    // sqrt calls; a size-k max-heap keeps only the k closest points
    // seen so far, evicting the farthest one on overflow.

    // Level 2 -- Optimal: size-k max-heap by squared distance.
    static int[][] kClosest(int[][] points, int k) {
        PriorityQueue<int[]> heap = new PriorityQueue<>(
            (a, b) -> distSq(b) - distSq(a) // max-heap: farthest at head
        );
        for (int[] point : points) {
            heap.offer(point);
            if (heap.size() > k) {
                heap.poll();
            }
        }
        return heap.toArray(new int[heap.size()][]);
    }

    static int distSq(int[] point) {
        return point[0] * point[0] + point[1] * point[1];
    }

    // Level 3 -- Hardened: works when k equals points.length (the
    // heap ends up holding every point, all returned) and when two
    // points share the same distance (both are kept if they fit
    // within k; the problem accepts any valid answer for ties).

    public static void main(String[] args) {
        int[][] result = kClosest(new int[][]{{1, 3}, {-2, 2}}, 1);
        System.out.println(Arrays.deepToString(result));
        // [[-2, 2]]
    }
}
```

**How to run:** `java KClosestPointsToOrigin.java`

## 6. Walkthrough

Trace `kClosest([[1,3],[-2,2]], 1)`:

| point | dist² | heap before | action | heap after |
|---|---|---|---|---|
| [1,3] | 10 | [] | offer | [(10,[1,3])] |
| [-2,2] | 8 | [(10,[1,3])] | offer, size 2 &gt; 1, poll head (farthest = [1,3]) | [(8,[-2,2])] |

Final heap holds `[[-2,2]]`, the closer point. Time complexity is O(n log k): one O(log k) heap operation per point, plus O(1) for the squared-distance computation. Space is O(k), for the heap.

## 7. Gotchas & takeaways

> Gotcha: computing `Math.sqrt` for every distance comparison is unnecessary and slower — since all distances are non-negative, comparing SQUARED distances gives the identical ordering, and skips a costly floating-point operation on every comparison.

- Ranking by a DERIVED key (squared distance) instead of the raw value is a common twist on Top-K Elements — the heap comparator changes, but the size-k-heap mechanics stay the same.
- A max-heap here (not a min-heap) because you want to evict the WORST (farthest) candidate on overflow, keeping the best (closest) `k`.
- Related problems: Kth Largest Element in an Array (the same size-k heap, ranking by raw value instead of a derived distance), Top K Frequent Elements (ranking by a derived frequency key).
