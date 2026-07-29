---
card: leetcode-patterns
gi: 623
slug: max-points-on-a-line
title: Max Points on a Line
---

## 1. What it is

Given an array of `points`, where `points[i] = [x, y]`, return the maximum number of points that lie on the same straight line. Example: `points=[[1,1],[2,2],[3,3]]` → `3` (all three lie on the line `y=x`); `points=[[1,1],[3,2],[5,3],[4,1],[2,3],[1,4]]` → `4`.

## 2. Why & when

This is [the Math & Geometry normalized-slope technique](0597-math-geometry-template-modular-arithmetic-in-place-matrix-mo.md), applied to counting: two points lie on the same line through a shared third point if and only if the **slope** from that third point to each of them is identical. Fixing one point and grouping every *other* point by its slope relative to that fixed point directly counts, for each possible line through the fixed point, how many points lie on it.

## 3. Core concept

**Key idea:** for each point `p` (used as a pivot, in turn), compute the normalized slope from `p` to every *other* point `q`, and group points by that slope in a `HashMap<slope, count>`. The largest count in that map (plus 1, for `p` itself) is the most points collinear with `p` through any single line. Repeat for every possible pivot point, and take the overall maximum across all pivots.

**Steps:**
1. If there are `0` or `1` points, return that count directly (trivially collinear).
2. For each pivot point `p` (outer loop): reset a `HashMap<String, Integer>` (or a map keyed by a normalized `(dx, dy)` pair). Also track `maxAtThisPivot = 0` and a count of points that are *exact duplicates* of `p` (same coordinates), since duplicates lie on every line through `p` but have an undefined slope.
3. For each other point `q` (inner loop): if `q` equals `p`, increment the duplicate count. Otherwise, compute the normalized slope `(dx, dy)` between `p` and `q` (reduce by GCD, fix a consistent sign), and increment that slope's count in the map.
4. After the inner loop, the best line through `p` has `maxSlopeCount + duplicateCount + 1` points (`+1` for `p` itself).
5. Track the overall maximum across all pivots.

**Why normalizing the slope with GCD (not comparing raw `dy/dx` as a floating-point ratio) is necessary:** floating-point slope comparison risks precision errors — two mathematically identical slopes computed from different point pairs might not compare exactly equal due to rounding, silently undercounting a line's points. Using integer GCD reduction (as in the earlier slope template) guarantees exact equality comparison, with no floating-point risk.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fixing one point as pivot and grouping every other point by its normalized slope relative to the pivot">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="130" r="6" fill="#3fb950"/><text x="80" y="150" fill="#3fb950" text-anchor="middle" font-size="10">pivot p</text>
    <circle cx="200" cy="90" r="6" fill="#f0883e"/><text x="200" y="75" fill="#f0883e" text-anchor="middle" font-size="10">q1</text>
    <circle cx="320" cy="50" r="6" fill="#f0883e"/><text x="320" y="35" fill="#f0883e" text-anchor="middle" font-size="10">q2</text>
    <circle cx="220" cy="130" r="6" fill="#79c0ff"/><text x="220" y="150" fill="#79c0ff" text-anchor="middle" font-size="10">q3</text>
    <line x1="80" y1="130" x2="320" y2="50" stroke="#8b949e" stroke-dasharray="3,2"/>
    <text x="500" y="60" fill="#79c0ff" text-anchor="middle">slope(p,q1) == slope(p,q2) -&gt; same line, count=2 for that slope</text>
    <text x="500" y="90" fill="#8b949e" text-anchor="middle">slope(p,q3) is different -&gt; separate line, count=1</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle" font-size="11">best line through p: 2 (q1,q2) + 1 (p itself) = 3 points</text>
  </g>
</svg>

Grouping every other point by its slope relative to a fixed pivot directly reveals, for that pivot, how many points share each possible line through it.

## 5. Runnable example

**Level 1 — Brute force.** For every triple of points, check whether they are collinear (using the cross-product test: `(y2-y1)*(x3-x1) == (y3-y1)*(x2-x1)`), and track the largest connected collinear group. O(n^3) or worse to assemble groups from pairwise triple checks — very slow.

**KEY INSIGHT:** fixing one point as a pivot and grouping every other point by its slope relative to that pivot directly counts every line through the pivot in a single pass — repeating this for every possible pivot point covers every line in the dataset, without ever explicitly checking triples.

**Level 2 — Optimal.** Nested loop: for each pivot, one pass over all other points computing and grouping normalized slopes, O(n^2) time overall, O(n) space per pivot's slope map.

**Level 3 — Hardened.** Correctly handles duplicate points (same coordinates as the pivot), which have an undefined slope but must still count toward every line through the pivot, and correctly normalizes the slope's sign so that opposite-direction vectors along the same line are grouped together.

```java
// MaxPointsOnALine.java
import java.util.*;

public class MaxPointsOnALine {

    private static int gcd(int a, int b) {
        return b == 0 ? a : gcd(b, a % b);
    }

    public static int maxPoints(int[][] points) {
        int n = points.length;
        if (n <= 2) return n;

        int overallMax = 1;

        for (int i = 0; i < n; i++) {
            Map<String, Integer> slopeCounts = new HashMap<>();
            int duplicates = 0;
            int maxAtThisPivot = 0;

            for (int j = 0; j < n; j++) {
                if (i == j) continue;
                int dx = points[j][0] - points[i][0];
                int dy = points[j][1] - points[i][1];

                if (dx == 0 && dy == 0) {
                    duplicates++;
                    continue;
                }

                int g = gcd(Math.abs(dx), Math.abs(dy));
                dx /= g;
                dy /= g;
                if (dx < 0 || (dx == 0 && dy < 0)) {
                    dx = -dx;
                    dy = -dy;
                }

                String key = dx + "," + dy;
                int count = slopeCounts.getOrDefault(key, 0) + 1;
                slopeCounts.put(key, count);
                maxAtThisPivot = Math.max(maxAtThisPivot, count);
            }

            overallMax = Math.max(overallMax, maxAtThisPivot + duplicates + 1);
        }

        return overallMax;
    }

    public static void main(String[] args) {
        int[][] points = {{1, 1}, {2, 2}, {3, 3}};
        System.out.println(maxPoints(points)); // 3
    }
}
```

**How to run:** save as `MaxPointsOnALine.java`, then run `java MaxPointsOnALine.java`.

## 6. Walkthrough

Trace `maxPoints([[1,1],[2,2],[3,3]])` with pivot `i=0` (`points[0]=[1,1]`):

| j | points[j] | dx,dy | gcd | normalized (dx,dy) | slopeCounts after |
|---|---|---|---|---|---|
| 1 | [2,2] | 1,1 | 1 | (1,1) | {"1,1":1} |
| 2 | [3,3] | 2,2 | 2 | (1,1) | {"1,1":2} |

`maxAtThisPivot = 2` (both other points share the slope `(1,1)`). `duplicates = 0`. Total for this pivot: `2 + 0 + 1 = 3`. Since `n=3`, this is already the overall maximum. Result: `3`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to special-case `dx == 0 && dy == 0` (a duplicate point) before computing the GCD causes a division by zero (`gcd(0,0)` returns `0`, and dividing `dx`/`dy` by `0` is undefined) — duplicate points must be tracked separately and added directly to the final count, since they lie on every line through the pivot regardless of slope.

- Signal: "count points/items lying on the same line/direction" is the pivot-plus-normalized-slope-grouping signal.
- Integer GCD normalization (not floating-point slope) is required for reliable, exact equality comparison between slopes.
- Related problems: none directly in this section, but the normalized-slope technique generalizes to any "same direction" or "collinear" grouping problem.
