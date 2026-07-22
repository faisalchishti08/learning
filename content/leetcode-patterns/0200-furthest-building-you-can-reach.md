---
card: leetcode-patterns
gi: 200
slug: furthest-building-you-can-reach
title: Furthest Building You Can Reach
---

## 1. What it is

Given an array `heights` of building heights, `bricks`, and `ladders`, starting at building `0`, you can move to the next building for free if it is the same height or shorter. If it is taller, you must use either a ladder (covers any height gap) or bricks (one brick per unit of height gap). Return the furthest building index you can reach. Example: `heights = [4,2,7,6,9,14,12]`, `bricks = 5`, `ladders = 1` → `4`.

## 2. Why & when

The greedy insight is: ladders are more valuable on the LARGEST height gaps you have seen so far, since a ladder covers any gap for free while bricks cost proportional to the gap size. A min-heap tracking the smallest gap among your currently-assigned ladders lets you cheaply "downgrade" the least valuable ladder usage to bricks whenever a bigger gap comes along and you are out of ladders.

## 3. Core concept

**Key idea:** whenever you hit a height gap, tentatively use a ladder (push the gap size onto a min-heap of "ladder-covered gaps"). If you have used MORE ladders than you actually have, that means the SMALLEST gap in the heap should have used bricks instead — pop it and pay bricks for it. Fail (return the current index) if you cannot afford those bricks.

**Steps:**
1. Walk through consecutive building pairs; if the next building is not taller, move on for free.
2. If there is a height gap, push it onto a min-heap and always ASSUME a ladder was used for it.
3. If the heap's size exceeds the number of ladders available, pop the SMALLEST gap from the heap — that gap should have used bricks instead, since it costs the least to convert.
4. Subtract that popped gap from `bricks`. If `bricks` goes negative, return the CURRENT building index (this is as far as you can go).
5. If you successfully process every building, return the last index (`heights.length - 1`).

**Why it is correct:** always assigning a ladder first, then downgrading the SMALLEST heap gap to bricks when out of ladders, guarantees you keep ladders on the LARGEST gaps seen so far — this is optimal because using a ladder on a gap saves exactly that gap's worth of bricks, so saving ladders for the biggest gaps saves the most bricks overall. Any other assignment strategy would use bricks on a gap at least as large as one currently ladder-covered, wasting more bricks than necessary.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ladders assigned to the largest gaps; smallest heap gap downgraded to bricks when ladders run out">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="100" width="20" height="60" fill="#3fb950"/>
    <rect x="60" y="60" width="20" height="100" fill="#3fb950"/>
    <rect x="100" y="20" width="20" height="140" fill="#e3b341"/>
    <text x="10" y="15" fill="#e6edf3">small gaps (green) covered by bricks; largest gap (gold) kept on a ladder</text>
  </g>
</svg>

The largest height gap keeps its ladder; smaller gaps in the heap get downgraded to bricks first when ladders are scarce.

## 5. Runnable example

```java
// FurthestBuildingYouCanReach.java
import java.util.*;

public class FurthestBuildingYouCanReach {

    // Level 1 -- Brute force / greedy without a heap: always use
    // bricks first, only falling back to a ladder when bricks run out.
    // This is WRONG in general -- it might spend all bricks on small
    // early gaps and have no bricks left for the ladder-worthy gap that
    // should have been saved, since it never revisits earlier
    // decisions.

    // KEY INSIGHT: use a MIN-HEAP to track the gaps currently assigned
    // to ladders -- when ladders run out, the heap lets you cheaply
    // find and downgrade the SMALLEST such gap to bricks, effectively
    // "reconsidering" an earlier decision in O(log n).

    // Level 2 -- Optimal: min-heap of ladder-assigned gaps, downgrade
    // smallest when over budget.
    static int furthestBuilding(int[] heights, int bricks, int ladders) {
        PriorityQueue<Integer> ladderGaps = new PriorityQueue<>();
        for (int i = 0; i < heights.length - 1; i++) {
            int gap = heights[i + 1] - heights[i];
            if (gap <= 0) continue;

            ladderGaps.add(gap);
            if (ladderGaps.size() > ladders) {
                bricks -= ladderGaps.poll();
            }
            if (bricks < 0) return i;
        }
        return heights.length - 1;
    }

    // Level 3 -- Hardened: a gap of exactly 0 (same height) is
    // correctly skipped via `gap <= 0`, never consuming a ladder or
    // bricks unnecessarily.

    public static void main(String[] args) {
        System.out.println(furthestBuilding(new int[]{4,2,7,6,9,14,12}, 5, 1)); // 4
        System.out.println(furthestBuilding(new int[]{4,12,2,7,3,18,20,3,19}, 10, 2)); // 7
        System.out.println(furthestBuilding(new int[]{14,3,19,3}, 17, 0)); // 3
    }
}
```

**How to run:** `java FurthestBuildingYouCanReach.java`

## 6. Walkthrough

Trace `heights = [4,2,7,6,9,14,12]`, `bricks = 5`, `ladders = 1`:

| i | gap | ladderGaps after push | size > ladders? | bricks after downgrade |
|---|---|---|---|---|
| 0→1 | -2 (skip) | — | — | 5 |
| 1→2 | 5 | {5} | no (1 <= 1) | 5 |
| 2→3 | -1 (skip) | — | — | 5 |
| 3→4 | 3 | {3,5} | yes (2 > 1), pop 3 | 5 - 3 = 2 |
| 4→5 | 5 | {5,5} | yes (2 > 1), pop 5 | 2 - 5 = -3 → return i=4 |

Result matches the expected `4`. Time complexity is O(n log n), since each of the n-1 gaps triggers at most one heap push and possibly one pop; space is O(ladders) for the heap size (bounded by the number of ladders at any time, plus one).

## 7. Gotchas & takeaways

> Gotcha: downgrading the LARGEST gap in the heap instead of the smallest (e.g. using a max-heap by mistake) wastes MORE bricks than necessary on every downgrade, since the whole point is to keep the ladder on the biggest gap and pay bricks for the cheapest one.

- The heap only ever needs to hold `ladders + 1` elements at a time — right after a push that exceeds the ladder count, one gets popped immediately, keeping the heap small.
- Returning `heights.length - 1` (not `heights.length`) when the loop completes fully is the "you made it to the end" case — double-check this off-by-one.
- Related problems: IPO (max-heap greedy selection, different resource constraint), Find Right Interval (heap-based discard-forever logic).
