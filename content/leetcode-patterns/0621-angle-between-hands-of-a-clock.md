---
card: leetcode-patterns
gi: 621
slug: angle-between-hands-of-a-clock
title: Angle Between Hands of a Clock
---

## 1. What it is

Given `hour` (`1` to `12`) and `minutes` (`0` to `59`), return the **smaller** angle (in degrees) formed between the clock's hour hand and minute hand. Example: `hour=12, minutes=30` → `165` (the hour hand has moved partway toward `1` since `30` minutes have passed, while the minute hand points at `6`); `hour=3, minutes=30` → `75`.

## 2. Why & when

This is pure coordinate/angle geometry: each hand's position is a function of time, expressed in degrees around a 360-degree circle. The minute hand moves a fixed, easy-to-compute amount per minute; the trickier part is that the **hour hand also moves continuously** between hour marks as minutes pass — it does not jump instantly from one hour position to the next.

## 3. Core concept

**Key idea:** compute each hand's angle independently as degrees from the 12 o'clock position, then take the absolute difference between them. The minute hand completes a full 360-degree circle in 60 minutes, so it moves `360/60 = 6` degrees per minute. The hour hand completes a full 360-degree circle in 12 hours (720 minutes total), so it moves `360/720 = 0.5` degrees per minute — and crucially, it keeps moving continuously as minutes pass within the current hour, not just at the top of the hour.

**Steps:**
1. Compute the minute hand's angle: `minuteAngle = minutes * 6` (degrees from 12 o'clock).
2. Compute the hour hand's angle: `hourAngle = (hour % 12) * 30 + minutes * 0.5` — the `(hour % 12) * 30` term accounts for the hour hand's position at the exact top of the hour (each of the 12 hour marks is `360/12 = 30` degrees apart), and the `minutes * 0.5` term accounts for how far the hour hand has crept forward *within* the current hour.
3. Compute the raw difference: `diff = Math.abs(hourAngle - minuteAngle)`.
4. Since the problem wants the **smaller** angle (clocks are circular, so an angle and its "360 minus itself" complement are the two possible answers, and the smaller one is always `<= 180`), return `Math.min(diff, 360 - diff)`.

**Why `hour % 12` is necessary even though the input is constrained to `1..12`:** when `hour = 12`, the hour hand's true angular position is at the 12 o'clock mark, degree `0` — not degree `360` (which `12 * 30` would incorrectly compute). Taking `hour % 12` correctly maps `12` to `0` before multiplying by `30`, matching the hour hand's actual physical position.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At 3:30, the minute hand points straight down at 180 degrees while the hour hand has crept halfway between 3 and 4, at 105 degrees">
  <g font-family="sans-serif" font-size="12">
    <circle cx="200" cy="100" r="70" fill="none" stroke="#30363d"/>
    <line x1="200" y1="100" x2="200" y2="30" stroke="#f0883e" stroke-width="3"/>
    <text x="200" y="20" fill="#f0883e" text-anchor="middle" font-size="10">minute hand: 30*6=180deg</text>
    <line x1="200" y1="100" x2="266" y2="135" stroke="#3fb950" stroke-width="3"/>
    <text x="290" y="140" fill="#3fb950" font-size="10">hour hand: 3*30+30*0.5=105deg</text>
    <text x="350" y="170" fill="#79c0ff" text-anchor="middle">|180-105|=75, min(75, 360-75)=75</text>
  </g>
</svg>

The hour hand is not fixed at the "3" mark — it has moved a further `15` degrees toward `4`, since `30` minutes (half an hour) have passed, matching its continuous `0.5` degrees-per-minute motion.

## 5. Runnable example

**Level 1 — Brute force.** Treat the hour hand as fixed at its exact hour mark (`hour * 30` degrees), ignoring the minutes' contribution to its position. This is a common but **incorrect** simplification — it gives the wrong answer whenever `minutes != 0`, since it misses the hour hand's continuous motion.

**KEY INSIGHT:** the hour hand's angle is a function of *both* `hour` and `minutes`, not `hour` alone — it moves `0.5` degrees for every minute that passes, exactly `1/12` as fast as the minute hand's `6` degrees per minute (since the hour hand covers 12 times less angular distance, `30` degrees per hour versus `360` degrees per hour, in the same amount of time).

**Level 2 — Optimal.** Direct formula for both hands' angles, then `min(diff, 360-diff)`, O(1) time and space.

**Level 3 — Hardened.** Correctly uses `hour % 12` so that `hour=12` maps to angular position `0`, not `360`, and correctly returns the smaller of the two possible angle interpretations (an angle and its complement to 360).

```java
// AngleBetweenHandsOfAClock.java
public class AngleBetweenHandsOfAClock {

    public static double angleClock(int hour, int minutes) {
        double minuteAngle = minutes * 6.0;
        double hourAngle = (hour % 12) * 30.0 + minutes * 0.5;

        double diff = Math.abs(hourAngle - minuteAngle);
        return Math.min(diff, 360 - diff);
    }

    public static void main(String[] args) {
        System.out.println(angleClock(12, 30)); // 165.0
        System.out.println(angleClock(3, 30));  // 75.0
    }
}
```

**How to run:** save as `AngleBetweenHandsOfAClock.java`, then run `java AngleBetweenHandsOfAClock.java`.

## 6. Walkthrough

Trace `angleClock(3, 30)`:

1. `minuteAngle = 30 * 6.0 = 180.0` (the minute hand points straight down, at the "6" mark).
2. `hourAngle = (3 % 12) * 30.0 + 30 * 0.5 = 90.0 + 15.0 = 105.0` (the hour hand has moved 15 degrees past the "3" mark, halfway toward "4", since 30 minutes is half an hour).
3. `diff = |105.0 - 180.0| = 75.0`.
4. `min(75.0, 360 - 75.0) = min(75.0, 285.0) = 75.0`.

Result: `75.0` degrees, matching the expected answer.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `minutes * 0.5` contribution to the hour hand's angle (treating it as fixed at `hour * 30` regardless of minutes) is the single most common mistake on this problem — the hour hand visibly creeps between hour marks as time passes, and the formula must reflect that continuous motion.

- Signal: computing an angle or position that changes continuously over time (not in discrete jumps) is a rate-times-elapsed-time signal — identify each moving part's degrees (or units) per unit of time.
- The final `min(diff, 360-diff)` step is needed because any angle on a circle has a complementary angle summing to 360 — the problem always wants the smaller of the two.
- Related problems: none directly in this section, but the general technique (rate x time, then reduce to the range [0, 180] via a complement check) generalizes to other periodic/circular angle problems.
