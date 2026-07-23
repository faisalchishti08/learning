---
card: leetcode-patterns
gi: 250
slug: successful-pairs-of-spells-and-potions
title: Successful Pairs of Spells and Potions
---

## 1. What it is

Given `spells` and `potions` arrays, and a `success` threshold, a pair `(spell, potion)` is SUCCESSFUL if `spell * potion >= success`. For each spell, return how many potions form a successful pair with it. Example: `spells = [5,1,3]`, `potions = [1,2,3,4,5]`, `success = 7` → `[4,0,3]` (spell `5` succeeds with potions `2,3,4,5`; spell `1` succeeds with none; spell `3` succeeds with `3,4,5`).

## 2. Why & when

Once `potions` is sorted, the condition `spell * potion >= success` is monotonic across potions for a FIXED spell: small potions fail, large potions succeed, with one crossover point. Use this shape whenever a problem asks you to count, for each item in one list, how many items in a second (sortable) list satisfy a threshold condition against it — sort once, then binary search once per item.

## 3. Core concept

**Key idea:** sort `potions` first. For each `spell`, binary search `potions` for the smallest index where `spell * potions[index] >= success`. Every potion from that index to the end of the array succeeds with this spell, so the count of successful potions is `potions.length - index`.

**Steps:**
1. Sort `potions` in ascending order.
2. For each `spell` in `spells`: binary search for the smallest index `idx` where `(long) spell * potions[idx] >= success`.
3. Use `lo = 0`, `hi = potions.length`; while `lo < hi`: compute `mid = lo + (hi - lo) / 2`; if `spell * potions[mid] >= success`, set `hi = mid`; else set `lo = mid + 1`.
4. The count of successful potions for this spell is `potions.length - lo`.
5. Collect one count per spell into the result array.

**Why it is correct:** for a fixed `spell`, `spell * potions[index]` increases as `potions[index]` increases (potions are sorted, and `spell` is a fixed non-negative multiplier), so the condition `spell * potions[index] >= success` is false for small indices and true from some point onward — a clean monotonic flip. Binary search finds that exact flip index, and everything from there to the end is a valid pair, giving the count directly without checking each potion individually.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Potions 1 2 3 4 5 sorted, spell 5, success 7, threshold at potion index 1 value 2, 4 potions succeed">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">potions (sorted) = [1,2,3,4,5], spell = 5, success = 7</text>
    <rect x="10" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="25" y="47" text-anchor="middle" font-size="9">1 (5)</text>
    <rect x="40" y="30" width="30" height="24" fill="#3fb950"/><text x="55" y="47" fill="#0d1117" text-anchor="middle" font-size="9">2 (10)</text>
    <rect x="70" y="30" width="30" height="24" fill="#3fb950"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">3 (15)</text>
    <rect x="100" y="30" width="30" height="24" fill="#3fb950"/><text x="115" y="47" fill="#0d1117" text-anchor="middle" font-size="9">4 (20)</text>
    <rect x="130" y="30" width="30" height="24" fill="#3fb950"/><text x="145" y="47" fill="#0d1117" text-anchor="middle" font-size="9">5 (25)</text>
    <text x="10" y="80">1*5=5 &lt; 7 fails; 2*5=10 &gt;= 7 succeeds -- flip at index 1</text>
    <text x="10" y="105">count = potions.length - index = 5 - 1 = 4</text>
  </g>
</svg>

Once sorted, a single binary search per spell finds where the product crosses the success threshold, giving the count directly.

## 5. Runnable example

```java
// SuccessfulPairsOfSpellsAndPotions.java
import java.util.*;

public class SuccessfulPairsOfSpellsAndPotions {

    // Level 1 -- Brute force: for each spell, scan every potion and
    // count how many satisfy spell * potion >= success. Correct, but
    // O(spells.length * potions.length) -- ignores that sorting
    // potions once enables a much faster per-spell search.

    // KEY INSIGHT: after sorting potions, "spell * potion >= success"
    // is monotonic across potions for a fixed spell, so a single
    // binary search per spell finds the success threshold directly.

    // Level 2 -- Optimal: sort once, binary search per spell.
    static int[] successfulPairs(int[] spells, int[] potions, long success) {
        int[] sortedPotions = potions.clone();
        Arrays.sort(sortedPotions);

        int[] result = new int[spells.length];
        for (int i = 0; i < spells.length; i++) {
            int spell = spells[i];
            int lo = 0, hi = sortedPotions.length;
            while (lo < hi) {
                int mid = lo + (hi - lo) / 2;
                if ((long) spell * sortedPotions[mid] >= success) hi = mid;
                else lo = mid + 1;
            }
            result[i] = sortedPotions.length - lo;
        }
        return result;
    }

    // Level 3 -- Hardened: casts the product to long before comparing
    // to `success`, avoiding int overflow when spell and potion values
    // are both large.

    public static void main(String[] args) {
        int[] spells = {5, 1, 3};
        int[] potions = {1, 2, 3, 4, 5};
        System.out.println(Arrays.toString(successfulPairs(spells, potions, 7)));
        // [4, 0, 3]
    }
}
```

**How to run:** `java SuccessfulPairsOfSpellsAndPotions.java`

## 6. Walkthrough

`potions` sorted is `[1,2,3,4,5]`. Trace the binary search for `spell = 3`, `success = 7`, `lo=0, hi=5`:

| lo | hi | mid | potions[mid] | spell*potions[mid] | >= 7? | action |
|---|---|---|---|---|---|---|
| 0 | 5 | 2 | 3 | 9 | yes | hi = 2 |
| 0 | 2 | 1 | 2 | 6 | no | lo = 2 |
| 2 | 2 | — | — | — | loop ends | index = 2 |

Successful count for spell `3` is `5 - 2 = 3` (potions `3, 4, 5`), matching the expected `[4,0,3]`. Time complexity is O((n + m) · log m), where `n` is the number of spells and `m` is the number of potions: O(m log m) to sort, then O(log m) per spell. Space is O(m) for the sorted copy.

## 7. Gotchas & takeaways

> Gotcha: computing `spell * potions[mid]` as a plain `int` can overflow when both values are large — cast at least one operand to `long` before multiplying, since the overflow would silently produce a wrong, possibly negative, comparison result.

- Sorting `potions` once, up front, is what makes the per-spell binary search valid — running this search on an unsorted `potions` array gives meaningless results.
- The result count is `potions.length - lo`, not `lo` itself — a common off-by-direction mistake, since the search finds the START of the successful range, and everything from there onward counts.
- Related problems: Find K Closest Elements (a different per-query binary search over a sorted array), Koko Eating Bananas (a different monotonic threshold search, over speed instead of a per-item product).
