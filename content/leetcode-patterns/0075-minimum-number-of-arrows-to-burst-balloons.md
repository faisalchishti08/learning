---
card: leetcode-patterns
gi: 75
slug: minimum-number-of-arrows-to-burst-balloons
title: Minimum Number of Arrows to Burst Balloons
---

## 1. What it is

Balloons are represented as intervals `[x_start, x_end]` along a horizontal line. An arrow shot straight up at position `x` bursts every balloon whose interval contains `x`. Find the minimum number of arrows needed to burst all balloons. Example: `points = [[10,16],[2,8],[1,6],[7,12]]` → `2` (one arrow at `x=6` bursts `[2,8]` and `[1,6]`; one arrow at `x=11` bursts `[10,16]` and `[7,12]`).

## 2. Why & when

This problem is structurally identical to Non-overlapping Intervals: grouping balloons that can share one arrow is the same as grouping intervals that overlap. Sorting by end position and greedily deciding when a new arrow is needed reduces this to a single linear scan, just like the greedy removal-counting problem earlier in this section.

## 3. Core concept

**Key idea:** sort balloons by their end coordinate. Shoot the first arrow at the end of the first balloon. Any later balloon that starts at or before that arrow's position is already burst — skip it. The first balloon that starts after the current arrow's position needs a new arrow, placed at its end.

**Steps:**
1. Sort `points` by `end` ascending.
2. Set `arrows = 1`, `arrowPos = points[0].end`.
3. For each subsequent balloon:
   - If `balloon.start > arrowPos`, it is not burst by the current arrow — shoot a new one: `arrows++`, `arrowPos = balloon.end`.
   - Otherwise, it is already burst — do nothing.
4. Return `arrows`.

**Why it is correct:** placing each arrow at the earliest-ending unburst balloon's end coordinate maximizes how many later, overlapping balloons that single arrow can also catch — no other position for that arrow could burst more balloons, since any position further right risks missing a balloon that ends before it.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shooting arrows to burst overlapping balloon intervals">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">balloons sorted by end: [1,6], [2,8], [7,12], [10,16]</text>
    <rect x="20" y="45" width="100" height="18" fill="#161b22" stroke="#79c0ff"/><text x="70" y="58" fill="#e6edf3" text-anchor="middle" font-size="9">[1,6]</text>
    <rect x="40" y="68" width="120" height="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="81" fill="#e6edf3" text-anchor="middle" font-size="9">[2,8]</text>
    <line x1="120" y1="35" x2="120" y2="95" stroke="#3fb950" stroke-width="2"/><text x="120" y="30" fill="#3fb950" text-anchor="middle" font-size="10">arrow@6</text>
    <rect x="140" y="45" width="100" height="18" fill="#161b22" stroke="#f0883e"/><text x="190" y="58" fill="#e6edf3" text-anchor="middle" font-size="9">[7,12]</text>
    <rect x="200" y="68" width="120" height="18" fill="#161b22" stroke="#f0883e"/><text x="260" y="81" fill="#e6edf3" text-anchor="middle" font-size="9">[10,16]</text>
    <line x1="240" y1="35" x2="240" y2="95" stroke="#3fb950" stroke-width="2"/><text x="240" y="30" fill="#3fb950" text-anchor="middle" font-size="10">arrow@12</text>
    <text x="20" y="140" fill="#8b949e">2 arrows burst all 4 balloons: one at x=6, one at x=12</text>
  </g>
</svg>

Each arrow is placed at the end of the earliest-ending unburst balloon, catching every overlapping balloon in one shot before moving to the next group.

## 5. Runnable example

```java
// MinimumArrowsToBurstBalloons.java
import java.util.*;

public class MinimumArrowsToBurstBalloons {

    // Level 1 -- Brute force: try every possible arrow position at every
    // balloon boundary, greedily pick arrows via nested scanning without
    // sorting first. O(n^2) time -- wastes repeated unsorted scans.
    static int bruteForce(int[][] points) {
        boolean[] burst = new boolean[points.length];
        int arrows = 0;
        for (int i = 0; i < points.length; i++) {
            if (burst[i]) continue;
            arrows++;
            int arrowPos = points[i][1];
            for (int j = 0; j < points.length; j++) {
                if (!burst[j] && points[j][0] <= arrowPos && arrowPos <= points[j][1]) {
                    burst[j] = true;
                }
            }
        }
        return arrows;
    }

    // KEY INSIGHT: sorting by END coordinate and always placing the next
    // arrow at the earliest-ending unburst balloon maximizes how many
    // later balloons that single shot also bursts -- identical greedy
    // logic to Non-overlapping Intervals.

    // Level 2 -- Optimal: sort by end, one linear pass. O(n log n) time,
    // O(1) extra space.
    public static int findMinArrowShots(int[][] points) {
        if (points.length == 0) return 0;
        Arrays.sort(points, (a, b) -> Long.compare(a[1], b[1]));

        int arrows = 1;
        long arrowPos = points[0][1];
        for (int i = 1; i < points.length; i++) {
            if (points[i][0] > arrowPos) {
                arrows++;
                arrowPos = points[i][1];
            }
        }
        return arrows;
    }

    // Level 3 -- Hardened: balloons using coordinates near Integer.MIN
    // and MAX values, where naive int overflow in comparisons could
    // misbehave -- using long for arrowPos avoids that class of bug.
    static int hardened(int[][] points) {
        return findMinArrowShots(points);
    }

    public static void main(String[] args) {
        int[][] a = {{10, 16}, {2, 8}, {1, 6}, {7, 12}};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + findMinArrowShots(a));

        int[][] extremes = {{Integer.MIN_VALUE, Integer.MAX_VALUE}};
        System.out.println("extreme range (expect 1): " + hardened(extremes));
    }
}
```

How to run: save as `MinimumArrowsToBurstBalloons.java`, then run `java MinimumArrowsToBurstBalloons.java`.

## 6. Walkthrough

Dry run of `findMinArrowShots` on balloons sorted by end: `[[1,6],[2,8],[7,12],[10,16]]`:

| step | balloon | start > arrowPos? | action | arrowPos |
|---|---|---|---|---|
| start | [1,6] | — | arrows=1 | 6 |
| 1 | [2,8] | 2 > 6? no | already burst | 6 |
| 2 | [7,12] | 7 > 6? yes | arrows=2 | 12 |
| 3 | [10,16] | 10 > 12? no | already burst | 12 |

Result: `arrows = 2`. Time complexity: O(n log n), dominated by the sort. Space complexity: O(1) extra space.

## 7. Gotchas & takeaways

> Gotcha: for very large coordinate ranges, adding or comparing two `int` end/start values can overflow; using `long` for the running `arrowPos` (as in the example) avoids subtle overflow bugs that a strict `int` comparison would not catch until it silently produces a wrong answer.

- This problem and Non-overlapping Intervals share the exact same greedy skeleton — "sort by end, scan, decide keep-or-not" — recognizing the shared shape saves re-deriving the greedy proof each time.
- Related problems: Non-overlapping Intervals (count removals instead of arrows), Meeting Rooms II (peak concurrency instead of grouping).
