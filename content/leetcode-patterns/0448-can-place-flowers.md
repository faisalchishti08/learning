---
card: leetcode-patterns
gi: 448
slug: can-place-flowers
title: Can Place Flowers
---

## 1. What it is

Given a row of plots (`1` = already planted, `0` = empty), where no two flowers may be adjacent, determine if `n` NEW flowers can be planted without violating the rule. Example: `flowerbed = [1,0,0,0,1]`, `n = 1` → `true`.

## 2. Why & when

Use this shape whenever a problem asks whether enough "gaps" exist to place non-adjacent items, given some positions are ALREADY fixed. The greedy rule: scan left to right, and PLANT a flower the moment a position is both empty and has no adjacent flower — never skip a valid opportunity, since delaying it can only reduce future options.

## 3. Core concept

**Key idea:** scan the array once. At each position, if it is EMPTY (`0`) and BOTH neighbors are also empty (or off the edge of the array), plant a flower there immediately, and count it.

**Steps:**
1. For each index `i` where `flowerbed[i] == 0`: check `leftOk` (`i == 0` or `flowerbed[i-1] == 0`) and `rightOk` (`i == last index` or `flowerbed[i+1] == 0`).
2. If BOTH are true, plant a flower at `i` (update `flowerbed[i] = 1` so later checks see it correctly) and increment a counter.
3. After scanning the whole array, return whether the counter is `>= n`.

**Why planting IMMEDIATELY (never skipping a valid spot) is correct:** any valid opportunity to plant a flower right now can only ever help, never hurt, later positions — a flower placed at `i` only affects `i-1` and `i+1`'s eligibility, and SKIPPING a valid spot at `i` gains nothing (it does not make any LATER position more plantable), while every flower successfully placed strictly increases the running count toward `n`. So greedily planting whenever possible is never worse than waiting.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="scanning left to right and planting a flower the instant a position and both its neighbors are empty">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">flowerbed = [1, 0, 0, 0, 1]</text>
    <text x="10" y="45">i=1: left=1 (occupied) -- skip</text>
    <text x="10" y="65">i=2: left=0, right=0 -- PLANT here immediately</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">i=3: left is now occupied (just planted) -- skip</text>
  </g>
</svg>

Planting the instant a valid gap appears is always at least as good as waiting for a later opportunity.

## 5. Runnable example

```java
// CanPlaceFlowers.java
public class CanPlaceFlowers {

    // KEY INSIGHT: plant the instant a position is empty with both
    // neighbors empty -- skipping a valid spot never helps a later
    // position, since it doesn't change any other index's eligibility.

    static boolean canPlaceFlowers(int[] flowerbed, int n) {
        int count = 0;
        for (int i = 0; i < flowerbed.length; i++) {
            if (flowerbed[i] == 0) {
                boolean leftOk = (i == 0) || flowerbed[i - 1] == 0;
                boolean rightOk = (i == flowerbed.length - 1) || flowerbed[i + 1] == 0;
                if (leftOk && rightOk) {
                    flowerbed[i] = 1;
                    count++;
                }
            }
        }
        return count >= n;
    }

    public static void main(String[] args) {
        System.out.println(canPlaceFlowers(new int[]{1, 0, 0, 0, 1}, 1));
        // true
        System.out.println(canPlaceFlowers(new int[]{1, 0, 0, 0, 1}, 2));
        // false
    }
}
```

**How to run:** `java CanPlaceFlowers.java`

## 6. Walkthrough

Trace `canPlaceFlowers([1,0,0,0,1], n=2)`:

| i | flowerbed[i] | leftOk | rightOk | action | count |
|---|---|---|---|---|---|
| 0 | 1 | — | — | already planted, skip | 0 |
| 1 | 0 | false (left=1) | — | skip | 0 |
| 2 | 0 | true | true | PLANT | 1 |
| 3 | 0 | false (left now 1) | — | skip | 1 |
| 4 | 1 | — | — | already planted, skip | 1 |

Final `count = 1`, which is `< n = 2`, so the function returns `false`, matching the expected answer. Time complexity is O(n). Space is O(1) (the array is modified in place, no extra structure needed).

## 7. Gotchas & takeaways

> Gotcha: checking `leftOk` and `rightOk` AFTER updating `flowerbed[i] = 1` for a PREVIOUS planting is essential — the update at one index directly affects whether the NEXT index is eligible, so the array must be modified in place (or an equivalent running "was the previous position just planted" flag must be tracked) as the scan proceeds.

- Scanning once, planting immediately whenever eligible: the simplest possible "no two adjacent" greedy feasibility check.
- Updating the array in place (rather than only reading original values) is what correctly propagates each planting's effect to the very next check.
- Related problems: Assign Cookies (a different greedy shape — matching two sorted arrays, rather than a single left-to-right feasibility scan), Hand of Straights (a greedy feasibility check too, but built around removing the smallest remaining value repeatedly, not a left-to-right array scan).
