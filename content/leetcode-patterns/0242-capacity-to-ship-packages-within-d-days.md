---
card: leetcode-patterns
gi: 242
slug: capacity-to-ship-packages-within-d-days
title: Capacity To Ship Packages Within D Days
---

## 1. What it is

You must ship `weights` (an array of package weights, in order) within `days` days. Each day, load packages onto a ship in order, up to the ship's weight capacity, without splitting a package across two days. Find the MINIMUM ship capacity that gets everything shipped within `days` days. Example: `weights = [1,2,3,4,5,6,7,8,9,10]`, `days = 5` → `15`.

## 2. Why & when

This is Koko Eating Bananas wearing a different costume: a larger ship capacity always needs fewer or equal days, never more — a monotonic relationship perfect for binary search on the answer. Use this shape whenever a problem asks for the minimum "capacity," "bandwidth," or "budget" that satisfies a day/time constraint, given items processed in a fixed order.

## 3. Core concept

**Key idea:** define `daysNeeded(capacity)` as a greedy simulation: walk through `weights` in order, loading each package onto the "current day's load" if it fits under `capacity`; when it doesn't fit, start a new day. This function is monotonic — decreasing as `capacity` increases. Binary search over candidate capacities for the smallest one where `daysNeeded(capacity) <= days`.

**Steps:**
1. Set `lo = max(weights)` (the ship must be able to carry the single heaviest package), `hi = sum(weights)` (one day, carrying everything at once, always works).
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. Compute `days_ = daysNeeded(mid)` by greedily simulating the loading process.
4. If `days_ <= days`, capacity `mid` works, and a smaller capacity might also work: set `hi = mid`.
5. Otherwise, capacity `mid` is too small: set `lo = mid + 1`.
6. When the loop ends, `lo == hi` is the minimum valid capacity.

**Why it is correct:** `daysNeeded(capacity)` strictly decreases (or stays the same) as `capacity` increases, since a bigger ship can only fit as many or more packages per day. This monotonic relationship means "is `daysNeeded(capacity) <= days`?" flips from false to true exactly once as `capacity` grows, and binary search finds that exact flip point — the minimum working capacity.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Weights 1 through 10, days 5, capacity 15 loads packages into 5 days exactly">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">weights = [1,2,3,4,5,6,7,8,9,10], days = 5</text>
    <text x="10" y="45">capacity 15: day1=[1,2,3,4,5]=15, day2=[6,7]=13, day3=[8]=8, day4=[9]=9, day5=[10]=10</text>
    <rect x="10" y="60" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="25" y="77" text-anchor="middle" font-size="9">14</text>
    <rect x="40" y="60" width="30" height="24" fill="#3fb950"/><text x="55" y="77" fill="#0d1117" text-anchor="middle" font-size="9">15</text>
    <text x="10" y="110">capacity 14 needs 6 days (too slow); capacity 15 needs exactly 5</text>
    <text x="10" y="135">minimum capacity that fits within 5 days: 15</text>
  </g>
</svg>

Larger capacity always ships in fewer or equal days; the search finds the smallest capacity where that day count still fits the deadline.

## 5. Runnable example

```java
// CapacityToShipPackages.java
public class CapacityToShipPackages {

    // Level 1 -- Brute force: try capacity = max(weights), max(weights)
    // + 1, ... increasing by one, simulating daysNeeded(capacity) each
    // time, stopping at the first capacity that fits within `days`.
    // Correct, but O(sum(weights)) capacities tried in the worst case.

    // KEY INSIGHT: daysNeeded(capacity) is monotonically non-increasing
    // in capacity, so binary search over the capacity range finds the
    // minimum working capacity in O(log(sum(weights))) tries.

    // Level 2 -- Optimal: binary search on the answer.
    static int shipWithinDays(int[] weights, int days) {
        int lo = 0, hi = 0;
        for (int w : weights) {
            lo = Math.max(lo, w);
            hi += w;
        }

        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (daysNeeded(weights, mid) <= days) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    static int daysNeeded(int[] weights, int capacity) {
        int days = 1, currentLoad = 0;
        for (int w : weights) {
            if (currentLoad + w > capacity) {
                days++;
                currentLoad = 0;
            }
            currentLoad += w;
        }
        return days;
    }

    // Level 3 -- Hardened: lo starts at max(weights), not 1, since any
    // capacity smaller than the heaviest single package can never
    // ship that package at all -- an important tightening of the
    // search range beyond the generic "1 to sum" bounds.

    public static void main(String[] args) {
        int[] weights = {1,2,3,4,5,6,7,8,9,10};
        System.out.println(shipWithinDays(weights, 5));
        // 15
    }
}
```

**How to run:** `java CapacityToShipPackages.java`

## 6. Walkthrough

Trace `shipWithinDays(weights, 5)`, `lo=10, hi=55`:

| lo | hi | mid | daysNeeded(mid) | <= 5? | action |
|---|---|---|---|---|---|
| 10 | 55 | 32 | 2 | yes | hi = 32 |
| 10 | 32 | 21 | 3 | yes | hi = 21 |
| 10 | 21 | 15 | 5 | yes | hi = 15 |
| 10 | 15 | 12 | 6 | no | lo = 13 |
| 13 | 15 | 14 | 6 | no | lo = 15 |
| 15 | 15 | — | — | loop ends | return 15 |

The minimum capacity `15` matches the expected answer. Time complexity is O(n · log(sum(weights))), where `n` is the number of packages. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: starting the search at `lo = 1` instead of `lo = max(weights)` still gives the correct final answer, but wastes early binary search steps checking capacities that could never possibly work, since any capacity below the heaviest single package makes `daysNeeded` undefined (that package could never be loaded at all).

- This problem and Koko Eating Bananas share the exact same binary-search-on-answer shape; only the simulation function (`hoursNeeded` versus `daysNeeded`) differs.
- The greedy simulation inside `daysNeeded` is itself optimal: always loading as much as fits before starting a new day never does worse than any other valid loading order, for a FIXED capacity.
- Related problems: Koko Eating Bananas (identical shape, a different simulation function), Minimum Speed to Arrive on Time (same shape, checking total travel time against an integer speed).
