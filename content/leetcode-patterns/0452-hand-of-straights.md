---
card: leetcode-patterns
gi: 452
slug: hand-of-straights
title: Hand of Straights
---

## 1. What it is

Given a hand of cards and a group size `groupSize`, determine whether the hand can be split into groups, each of `groupSize` CONSECUTIVE cards. Example: `hand = [1,2,3,6,2,3,4,7,8]`, `groupSize = 3` → `true` (groups `[1,2,3]`, `[2,3,4]`, `[6,7,8]`).

## 2. Why & when

Use this shape whenever a problem asks you to partition a multiset of values into groups of CONSECUTIVE numbers. The greedy rule: always start a new group at the SMALLEST remaining card — since that card can only ever be the START of a consecutive run (nothing smaller than it remains to precede it), there is no other valid choice for it.

## 3. Core concept

**Key idea:** count how many of each card value you have (in a structure that lets you efficiently find the SMALLEST remaining value — a sorted map works well). Repeatedly take the smallest remaining card, and force a run of `groupSize` consecutive cards starting from it.

**Steps:**
1. If the total number of cards is not divisible by `groupSize`, return `false` immediately.
2. Build a count map of card value to how many are left.
3. While cards remain: find the SMALLEST value still present, call it `first`. For each value from `first` to `first + groupSize - 1`: if it is missing, or has fewer copies left than needed, return `false`. Otherwise, use up one copy of it (removing it from the map once its count reaches zero).
4. If every group is formed successfully, return `true`.

**Why the smallest remaining card MUST start a group (the exchange argument):** since no card SMALLER than the current minimum remains, the minimum card cannot be the MIDDLE or END of any consecutive run (there is nothing left to come before it) — its ONLY possible role is to be the START of a run. This makes "always start a group at the current smallest value" not just a reasonable heuristic, but the ONLY valid choice at each step.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the smallest remaining card value must start a new consecutive run since nothing smaller remains to precede it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">counts: 1:1, 2:2, 3:2, 4:1, 6:1, 7:1, 8:1 -- groupSize=3</text>
    <text x="10" y="45">smallest remaining is 1 -- form group [1,2,3]; remaining smallest is now 2</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">form [2,3,4], then [6,7,8] -- all groups valid</text>
  </g>
</svg>

The smallest remaining card has no choice but to start a new consecutive run — nothing smaller is left to precede it.

## 5. Runnable example

```java
// HandOfStraights.java
import java.util.TreeMap;

public class HandOfStraights {

    // KEY INSIGHT: the smallest remaining card can only ever START a
    // run (nothing smaller is left to precede it) -- so it is forced,
    // not just a convenient greedy choice.

    static boolean isNStraightHand(int[] hand, int groupSize) {
        if (hand.length % groupSize != 0) return false;

        TreeMap<Integer, Integer> counts = new TreeMap<>();
        for (int card : hand) counts.merge(card, 1, Integer::sum);

        while (!counts.isEmpty()) {
            int first = counts.firstKey();
            int need = counts.get(first);
            for (int value = first; value < first + groupSize; value++) {
                Integer have = counts.get(value);
                if (have == null || have < need) return false;
                if (have.equals(need)) counts.remove(value);
                else counts.put(value, have - need);
            }
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(isNStraightHand(new int[]{1, 2, 3, 6, 2, 3, 4, 7, 8}, 3));
        // true
        System.out.println(isNStraightHand(new int[]{1, 2, 3, 4, 5}, 4));
        // false
    }
}
```

**How to run:** `java HandOfStraights.java`

## 6. Walkthrough

Trace `isNStraightHand([1,2,3,6,2,3,4,7,8], 3)` (counts start as `{1:1, 2:2, 3:2, 4:1, 6:1, 7:1, 8:1}`):

| iteration | smallest (first) | need | run consumed | counts after |
|---|---|---|---|---|
| 1 | 1 | 1 | 1,2,3 (each -1) | {2:1, 3:1, 4:1, 6:1, 7:1, 8:1} |
| 2 | 2 | 1 | 2,3,4 (each -1) | {6:1, 7:1, 8:1} |
| 3 | 6 | 1 | 6,7,8 (each -1) | {} |

All groups form successfully, matching the expected `true`. Time complexity is O(n log n) (a sorted-map structure, with `O(log n)` per lookup, over `O(n)` total card removals). Space is O(n) for the count map.

## 7. Gotchas & takeaways

> Gotcha: starting a group at any value OTHER than the current smallest remaining card can lead to a false negative — even if a group could technically be formed starting elsewhere, the smallest card is GUARANTEED to need to start SOME group, so processing it first (rather than some arbitrary card) is what the exchange argument requires.

- A sorted structure (like a `TreeMap`) is what makes "find the current smallest remaining value" efficient — without it, finding the minimum each iteration would cost an extra linear scan.
- The divisibility check (`hand.length % groupSize != 0`) is a fast, necessary short-circuit before doing any of the real work.
- Related problems: Assign Cookies (a different matching-based greedy, over two SEPARATE sorted arrays, rather than repeatedly draining one multiset), Can Place Flowers (a different feasibility check, scanning left to right rather than always targeting the current minimum).
