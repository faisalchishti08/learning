---
card: leetcode-patterns
gi: 459
slug: advantage-shuffle
title: Advantage Shuffle
---

## 1. What it is

Given two arrays `A` and `B` of the same length, rearrange `A` so that the number of indices where `A[i] > B[i]` is MAXIMIZED (this is called `A`'s "advantage" over `B`). Return the rearranged `A`. Example: `A = [2,7,11,15]`, `B = [1,10,4,11]` → `[2,11,7,15]`.

## 2. Why & when

Use this shape whenever a problem asks you to MATCH one array against another to maximize how many pairs satisfy a "greater than" comparison. This is a variant of the classic "assign resources to beat targets" pattern (similar in spirit to Assign Cookies), solved with a technique sometimes called the "advantage shuffle" or "greedy horse racing" strategy.

## 3. Core concept

**Key idea:** sort `A` ascending. Process `B`'s values from LARGEST to SMALLEST; for each, if the LARGEST remaining value in `A` can beat it, use that value; otherwise, sacrifice the SMALLEST remaining value in `A` (since it cannot beat this or any larger `B` value anyway).

**Steps:**
1. Sort `A` ascending. Sort `B`'s ORIGINAL INDICES by `B`'s value, DESCENDING (so you process the toughest targets first).
2. Maintain two pointers into sorted `A`: `left` (smallest unused) and `right` (largest unused).
3. For each `B` index, in descending-value order: if `A[right] > B[thisIndex]`, this largest remaining `A` value beats the target — assign it to that index, and decrement `right`. Otherwise, this largest remaining `A` value CANNOT beat the target (and neither can any smaller one) — sacrifice `A[left]` to this index instead, and increment `left`.
4. Build the result array using these assignments, placed back at `B`'s ORIGINAL indices.

**Why sacrificing the SMALLEST `A` value (not some other one) when no beat is possible is correct:** if the largest remaining `A` value cannot beat the current (currently the LARGEST remaining) `B` target, then NO remaining `A` value can beat it either — so this particular `B` value is a guaranteed loss no matter which `A` value gets assigned to it. Using the SMALLEST available `A` value here wastes the least potential — every OTHER `A` value is preserved for a `B` target it might still be able to beat.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the largest remaining a value tried against the largest remaining b target if it wins it is used otherwise the smallest a value is sacrificed">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">sorted A = [2, 7, 11, 15]; B (descending) = 11, 10, 4, 1</text>
    <text x="10" y="45">largest A (15) vs largest B (11): 15 &gt; 11, use 15; largest A now 11</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">11 vs 10: use 11; 7 vs 4: use 7; 2 vs 1: use 2 -- all beat their target</text>
  </g>
</svg>

The largest remaining value from A is tried first against the toughest remaining target — if it cannot win there, nothing can, so the smallest value is sacrificed instead.

## 5. Runnable example

```java
// AdvantageShuffle.java
import java.util.*;

public class AdvantageShuffle {

    // KEY INSIGHT: if the LARGEST remaining A value can't beat the
    // LARGEST remaining B target, nothing can -- sacrifice the
    // SMALLEST A value there instead, wasting the least potential.

    static int[] advantageCount(int[] A, int[] B) {
        int n = A.length;
        int[] sortedA = A.clone();
        Arrays.sort(sortedA);

        Integer[] bIndices = new Integer[n];
        for (int i = 0; i < n; i++) bIndices[i] = i;
        Arrays.sort(bIndices, (x, y) -> B[y] - B[x]); // B's indices, by value descending

        int[] result = new int[n];
        int left = 0, right = n - 1;
        for (int bIdx : bIndices) {
            if (sortedA[right] > B[bIdx]) {
                result[bIdx] = sortedA[right];
                right--;
            } else {
                result[bIdx] = sortedA[left];
                left++;
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(advantageCount(new int[]{2, 7, 11, 15}, new int[]{1, 10, 4, 11})));
        // [2, 11, 7, 15]
    }
}
```

**How to run:** `java AdvantageShuffle.java`

## 6. Walkthrough

Trace `advantageCount([2,7,11,15], [1,10,4,11])` (sortedA = `[2,7,11,15]`; B's indices by value descending: index `3` (B=11), index `1` (B=10), index `2` (B=4), index `0` (B=1)):

| B index processed | B value | largest remaining A | beats? | assigned | left/right after |
|---|---|---|---|---|---|
| 3 | 11 | 15 | yes | result[3]=15 | right=2 |
| 1 | 10 | 11 | yes | result[1]=11 | right=1 |
| 2 | 4 | 7 | yes | result[2]=7 | right=0 |
| 0 | 1 | 2 | yes | result[0]=2 | left=1 |

Final `result = [2, 11, 7, 15]`, matching the expected answer — every position beats its `B` target. Time complexity is O(n log n) (two sorts). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: processing `B` from SMALLEST to LARGEST instead of largest to smallest can lead to a WORSE outcome — an easy `B` target might get matched with an `A` value that a LATER, tougher `B` target actually needed, wasting winning potential that a stricter processing order would have preserved.

- Sorting `A` once, then a two-pointer sweep (largest-vs-largest, sacrificing smallest on a loss): the standard "advantage shuffle" technique for this exact matching shape.
- Tracking `B`'s ORIGINAL indices (not just its sorted values) is essential, since the final answer must be placed back into the positions `B` actually occupies.
- Related problems: Assign Cookies (a related matching-based greedy, but minimizing WASTE rather than maximizing WINS, with a simpler single-direction two-pointer scan), Two City Scheduling (a different matching greedy — assigning people to one of two groups by relative cost, rather than matching pairwise against a target array).
