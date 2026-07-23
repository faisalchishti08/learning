---
card: leetcode-patterns
gi: 247
slug: minimum-speed-to-arrive-on-time
title: Minimum Speed to Arrive on Time
---

## 1. What it is

You must travel across `n` train routes, each with a distance `dist[i]`, arriving within `hour` hours total. Every train has the same integer speed. Except for the LAST train, you must wait for the next integer hour before boarding the next train (partial hours on intermediate trains are rounded up to a full hour of waiting). Find the MINIMUM integer speed to arrive within `hour` hours, or `-1` if impossible. Example: `dist = [1,3,2]`, `hour = 6` → `1`.

## 2. Why & when

A faster speed always finishes in fewer or equal total hours, the same monotonic relationship as Koko Eating Bananas and Capacity To Ship Packages. Use this shape whenever a problem asks for a minimum rate under a time budget, with the twist here being that waiting behavior differs on the LAST leg versus every earlier leg.

## 3. Core concept

**Key idea:** define `timeNeeded(speed)`: for every route except the last, take `ceil(dist[i] / speed)` hours (rounding up, since you must wait for a whole hour to catch the next train). For the last route, take the EXACT time `dist[last] / speed` (no rounding, since you just need to arrive, not catch another train). Binary search over candidate speeds for the smallest one where `timeNeeded(speed) <= hour`.

**Steps:**
1. First check feasibility: if there are more routes than `hour` allows even at infinite speed (specifically, if `dist.length - 1 >= hour`, since each intermediate leg costs at least 1 full hour of waiting), return `-1` immediately.
2. Set `lo = 1`, `hi = 10^7` (a safe upper bound speed, since `hour` and `dist` values are bounded).
3. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
4. Compute `time = timeNeeded(dist, mid)` using the exact-last-leg rule.
5. If `time <= hour`, speed `mid` works: set `hi = mid`.
6. Otherwise, set `lo = mid + 1`.
7. When the loop ends, `lo` is the minimum valid integer speed.

**Why it is correct:** `timeNeeded(speed)` strictly decreases (or stays the same) as `speed` increases, for the same reason as in Koko Eating Bananas — a faster speed can only reduce or keep the time needed for each leg. The special rule for the last leg (no rounding up) does not break this monotonicity, since a smaller exact value only ever helps. Binary search finds the exact minimum speed where the total time first drops to or below `hour`.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Routes 1 3 2, hour 6, speed 1 gives total time 1+3+2=6 exactly, feasible">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dist = [1,3,2], hour = 6</text>
    <text x="10" y="45">speed 1: leg1=ceil(1/1)=1, leg2=ceil(3/1)=3, leg3(exact)=2/1=2</text>
    <text x="10" y="65">total = 1 + 3 + 2 = 6, fits exactly within hour=6</text>
    <rect x="10" y="80" width="30" height="24" fill="#3fb950"/><text x="25" y="97" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <text x="45" y="97">is already the minimum possible speed</text>
    <text x="10" y="130">minimum integer speed: 1</text>
  </g>
</svg>

Rounding up on intermediate legs but not the last one is the only twist on top of the familiar speed-search shape.

## 5. Runnable example

```java
// MinimumSpeedToArriveOnTime.java
public class MinimumSpeedToArriveOnTime {

    // Level 1 -- Brute force: try speed = 1, 2, 3, ... increasing by
    // one, computing timeNeeded(speed) each time. Correct, but O(max
    // speed) tries, each costing O(n) to evaluate.

    // KEY INSIGHT: timeNeeded(speed) is monotonically non-increasing
    // in speed, exactly like Koko Eating Bananas, so binary search
    // over the speed range finds the minimum working speed directly.

    // Level 2 -- Optimal: binary search on the answer.
    static int minSpeedOnTime(int[] dist, double hour) {
        int n = dist.length;
        if (n - 1 >= hour) return -1; // not enough hours even at infinite speed

        int lo = 1, hi = 10_000_000;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (timeNeeded(dist, mid) <= hour) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    static double timeNeeded(int[] dist, int speed) {
        double time = 0;
        for (int i = 0; i < dist.length - 1; i++) {
            time += Math.ceil((double) dist[i] / speed);
        }
        time += (double) dist[dist.length - 1] / speed; // exact, no rounding
        return time;
    }

    // Level 3 -- Hardened: the n-1 >= hour feasibility check upfront
    // avoids running a doomed binary search when even the fastest
    // possible speed cannot satisfy the mandatory whole-hour waits.

    public static void main(String[] args) {
        System.out.println(minSpeedOnTime(new int[]{1, 3, 2}, 6));
        // 1
        System.out.println(minSpeedOnTime(new int[]{1, 3, 2}, 2.7));
        // 3
        System.out.println(minSpeedOnTime(new int[]{1, 3, 2}, 1.9));
        // -1
    }
}
```

**How to run:** `java MinimumSpeedToArriveOnTime.java`

## 6. Walkthrough

Trace `minSpeedOnTime(dist, 2.7)` on `dist = [1,3,2]`, `lo=1, hi=10000000` (shrunk here for clarity):

| speed | leg1 ceil(1/s) | leg2 ceil(3/s) | leg3 exact (2/s) | total | <= 2.7? |
|---|---|---|---|---|---|
| 1 | 1 | 3 | 2.0 | 6.0 | no |
| 2 | 1 | 2 | 1.0 | 4.0 | no |
| 3 | 1 | 1 | 0.667 | 2.667 | yes |

Binary search converges on `speed = 3` as the minimum working speed. Time complexity is O(n · log(maxSpeed)). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: applying `ceil` to the LAST leg's time (treating it the same as every intermediate leg) gives a wrong, overly conservative answer — the last leg only needs to finish by the deadline, not round up to catch a following train, since there isn't one.

- The feasibility check `n - 1 >= hour` must run BEFORE the binary search, since no speed, however large, can satisfy a deadline smaller than the mandatory whole-hour waits between legs.
- This problem is a direct variant of Koko Eating Bananas and Capacity To Ship Packages Within D Days — same binary-search-on-answer shape, different simulation rule.
- Related problems: Koko Eating Bananas (identical shape, simpler per-item rounding), Capacity To Ship Packages Within D Days (same shape, a capacity instead of a speed).
