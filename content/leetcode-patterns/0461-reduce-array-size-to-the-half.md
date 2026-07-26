---
card: leetcode-patterns
gi: 461
slug: reduce-array-size-to-the-half
title: Reduce Array Size to The Half
---

## 1. What it is

Given an array, remove elements (by VALUE — removing one occurrence of a value removes ALL other elements matching that value too, since you choose to remove a "set" of matching values) so that the array's SIZE is reduced by at least half, using as FEW distinct values removed as possible. Return the minimum count of distinct values to remove. Example: `arr = [3,3,3,3,5,5,5,2,2,7]` → `2` (remove all `3`s and all `5`s: `4 + 3 = 7` elements gone, out of `10`, leaving `3 <= 5`).

## 2. Why & when

Use this shape whenever a problem lets you remove entire GROUPS (by shared value) to hit a size target, and asks for the FEWEST groups needed. The greedy rule: remove the LARGEST groups first — each removal should eliminate as many elements as possible, to reach the target size using as few distinct removals as it takes.

## 3. Core concept

**Key idea:** count the frequency of every distinct value. Sort these frequencies in DESCENDING order, and keep removing the LARGEST remaining frequency until at least half the array is gone.

**Steps:**
1. Build a frequency count for every distinct value.
2. Collect the frequencies into a list, and sort it DESCENDING.
3. Set `target = arr.length / 2` (the minimum number of elements that must be removed).
4. Walk through the sorted frequencies, accumulating a running `removed` total and a `setsUsed` counter; stop the moment `removed >= target`.
5. Return `setsUsed`.

**Why removing the LARGEST frequencies first minimizes the count (the exchange argument):** to reach the target removed-count using as FEW distinct values as possible, each removal should count for as much as it possibly can — removing a SMALLER group instead of an available LARGER one would need to be compensated by removing an EXTRA group later to make up the difference, which can only ever match or exceed the number of removals the greedy (largest-first) approach uses.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="frequencies sorted descending removed one at a time accumulating toward the target until half the array is gone">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr length 10, target = 5 removed -- frequencies: 3:4, 5:3, 2:2, 7:1 -- sorted: [4,3,2,1]</text>
    <text x="10" y="45">remove value with freq 4 (the 3s) -- removed=4, setsUsed=1 -- not yet at target</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">remove value with freq 3 (the 5s) -- removed=7 &gt;= 5 -- stop, setsUsed=2</text>
  </g>
</svg>

Removing the largest remaining frequency first reaches the removal target using the fewest distinct groups.

## 5. Runnable example

```java
// ReduceArraySizeToTheHalf.java
import java.util.*;

public class ReduceArraySizeToTheHalf {

    // KEY INSIGHT: remove the LARGEST remaining frequency group first
    // -- each removal should eliminate as many elements as possible,
    // minimizing how many distinct removals are needed.

    static int minSetSize(int[] arr) {
        Map<Integer, Integer> freq = new HashMap<>();
        for (int value : arr) freq.merge(value, 1, Integer::sum);

        List<Integer> counts = new ArrayList<>(freq.values());
        counts.sort(Collections.reverseOrder());

        int target = arr.length / 2;
        int removed = 0, setsUsed = 0;
        for (int count : counts) {
            removed += count;
            setsUsed++;
            if (removed >= target) break;
        }
        return setsUsed;
    }

    public static void main(String[] args) {
        System.out.println(minSetSize(new int[]{3, 3, 3, 3, 5, 5, 5, 2, 2, 7}));
        // 2
        System.out.println(minSetSize(new int[]{7, 7, 7, 7, 7, 7}));
        // 1
    }
}
```

**How to run:** `java ReduceArraySizeToTheHalf.java`

## 6. Walkthrough

Trace `minSetSize([3,3,3,3,5,5,5,2,2,7])` (`target = 10/2 = 5`; frequencies `3:4, 5:3, 2:2, 7:1`, sorted descending `[4,3,2,1]`):

| step | frequency removed | removed total | removed >= target? | setsUsed |
|---|---|---|---|---|
| 1 | 4 (the 3s) | 4 | 4 >= 5? no | 1 |
| 2 | 3 (the 5s) | 7 | 7 >= 5? yes | 2 |

`setsUsed = 2`, matching the expected answer. Time complexity is O(n log n) (counting is O(n); sorting the distinct-value frequencies dominates). Space is O(n) for the frequency map.

## 7. Gotchas & takeaways

> Gotcha: the target is `arr.length / 2` using INTEGER division, and the loop must stop the moment `removed >= target` (not `>`) — removing EXACTLY half (or more) satisfies "reduced by at least half," so an off-by-one comparison here would either stop one group too early or waste an unnecessary extra removal.

- Sorting frequencies descending, then greedily removing the largest first: the standard "reach a target using the fewest groups" greedy shape.
- A `HashMap` for counting plus a sorted list of just the VALUES (not the keys) is all that is needed — which specific values get removed does not matter for the final count, only how many distinct removals were used.
- Related problems: Minimum Deletions to Make Character Frequencies Unique (a related frequency-based greedy, but decrementing counts to make them unique rather than removing whole groups to hit a size target).
