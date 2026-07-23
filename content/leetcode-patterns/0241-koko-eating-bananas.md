---
card: leetcode-patterns
gi: 241
slug: koko-eating-bananas
title: Koko Eating Bananas
---

## 1. What it is

Koko has `piles` of bananas, and `h` hours before the guards return. Each hour, she picks one pile and eats up to `k` bananas from it (if the pile has fewer than `k`, she finishes that pile and stops for the hour). Find the MINIMUM integer eating speed `k` so she finishes all piles within `h` hours. Example: `piles = [3,6,7,11]`, `h = 8` → `4`.

## 2. Why & when

The eating speed `k` and the hours needed are inversely related: a faster speed always finishes in fewer or equal hours, never more. That monotonic relationship is exactly what binary search on the answer needs. Use this shape whenever a problem asks for the minimum "rate" or "capacity" that satisfies a time or resource constraint, and increasing that rate can only help, never hurt.

## 3. Core concept

**Key idea:** define `hoursNeeded(k)` as the total hours to eat every pile at speed `k`: for each pile, it takes `ceil(pile / k)` hours. This function is monotonic — decreasing as `k` increases. Binary search over candidate speeds `k` from `1` to `max(piles)`, looking for the smallest `k` where `hoursNeeded(k) <= h`.

**Steps:**
1. Set `lo = 1`, `hi = max(piles)` (eating faster than the largest pile never helps beyond finishing it in 1 hour).
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. Compute `hours = hoursNeeded(mid)` by summing `ceil(pile / mid)` for every pile.
4. If `hours <= h`, speed `mid` works, and a smaller speed might also work: set `hi = mid`.
5. Otherwise, speed `mid` is too slow: set `lo = mid + 1`.
6. When the loop ends, `lo == hi` is the minimum valid eating speed.

**Why it is correct:** `hoursNeeded(k)` strictly decreases (or stays the same) as `k` increases, since eating faster per pile never increases the hours needed for that pile. This monotonic relationship means "is `hoursNeeded(k) <= h`?" flips from false to true exactly once as `k` grows, and binary search finds that exact flip point — the minimum working speed.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Piles 3 6 7 11, speeds 1 to 11, hoursNeeded decreases as speed increases, flips true at speed 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">piles = [3,6,7,11], h = 8</text>
    <text x="10" y="45">speed 1: hours = 3+6+7+11 = 27 (too slow)</text>
    <text x="10" y="65">speed 4: hours = 1+2+2+3 = 8 (fits exactly)</text>
    <text x="10" y="85">speed 3: hours = 1+2+3+4 = 10 (too slow)</text>
    <rect x="10" y="100" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="25" y="117" text-anchor="middle" font-size="9">3</text>
    <rect x="40" y="100" width="30" height="24" fill="#3fb950"/><text x="55" y="117" fill="#0d1117" text-anchor="middle" font-size="9">4</text>
    <text x="10" y="140">smallest speed where hoursNeeded &lt;= 8: speed 4</text>
  </g>
</svg>

As the eating speed rises, the hours needed only ever falls, so the search converges on the exact minimum speed that fits in the time limit.

## 5. Runnable example

```java
// KokoEatingBananas.java
public class KokoEatingBananas {

    // Level 1 -- Brute force: try speed = 1, 2, 3, ... increasing by
    // one, computing hoursNeeded(speed) each time, stopping at the
    // first speed that fits within h hours. Correct, but O(max(piles))
    // speeds tried, each costing O(n) to evaluate.

    // KEY INSIGHT: hoursNeeded(speed) is monotonically non-increasing
    // in speed, so binary search over the speed range finds the
    // minimum working speed in O(log(max(piles))) tries instead of a
    // linear scan.

    // Level 2 -- Optimal: binary search on the answer.
    static int minEatingSpeed(int[] piles, int h) {
        int lo = 1, hi = 0;
        for (int pile : piles) hi = Math.max(hi, pile);

        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (hoursNeeded(piles, mid) <= h) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    static long hoursNeeded(int[] piles, int speed) {
        long hours = 0;
        for (int pile : piles) {
            hours += (pile + speed - 1) / speed; // ceil(pile / speed)
        }
        return hours;
    }

    // Level 3 -- Hardened: uses integer ceiling division (pile + speed
    // - 1) / speed instead of Math.ceil on doubles, avoiding floating
    // point rounding errors for large pile sizes.

    public static void main(String[] args) {
        System.out.println(minEatingSpeed(new int[]{3, 6, 7, 11}, 8));
        // 4
    }
}
```

**How to run:** `java KokoEatingBananas.java`

## 6. Walkthrough

Trace `minEatingSpeed(piles, 8)` on `piles = [3,6,7,11]`, `lo=1, hi=11`:

| lo | hi | mid | hoursNeeded(mid) | <= 8? | action |
|---|---|---|---|---|---|
| 1 | 11 | 6 | 1+1+2+2=6 | yes | hi = 6 |
| 1 | 6 | 3 | 1+2+3+4=10 | no | lo = 4 |
| 4 | 6 | 5 | 1+2+2+3=8 | yes | hi = 5 |
| 4 | 5 | 4 | 1+2+2+3=8 | yes | hi = 4 |
| 4 | 4 | — | — | loop ends | return 4 |

The minimum speed `4` matches the expected answer. Time complexity is O(n · log(max(piles))), where `n` is the number of piles (each speed check costs O(n)) and the search itself takes O(log(max(piles))) iterations. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing `ceil(pile / speed)` with floating-point division (`Math.ceil((double) pile / speed)`) risks subtle rounding errors for large values — the integer formula `(pile + speed - 1) / speed` avoids floating point entirely and is exact.

- This is binary search on the answer with the predicate direction FLIPPED compared to First Bad Version: here, LARGER speeds are more likely to satisfy the condition, so `hi = mid` moves toward smaller speeds while still keeping `mid` as a candidate.
- The search range `[1, max(piles)]` is tight: speed `1` is always the slowest useful speed, and no speed faster than the largest pile ever helps beyond finishing that pile in a single hour.
- Related problems: Capacity To Ship Packages Within D Days (identical shape: binary search on a capacity, checking days needed), Minimum Speed to Arrive on Time (same shape, checking total travel time).
