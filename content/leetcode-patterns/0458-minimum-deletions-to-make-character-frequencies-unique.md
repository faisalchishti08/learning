---
card: leetcode-patterns
gi: 458
slug: minimum-deletions-to-make-character-frequencies-unique
title: Minimum Deletions to Make Character Frequencies Unique
---

## 1. What it is

Given a string, return the MINIMUM number of character deletions needed so that no two DISTINCT characters share the same frequency. Example: `s = "aaabbbcc"` → `2` (frequencies `3, 3, 2` for `a, b, c` — delete one `b` to make it `2`, then delete one `c` to make it `1`, giving `3, 2, 1`).

## 2. Why & when

Use this shape whenever a problem needs to make a set of COUNTS all DISTINCT, by only ever DECREASING them (never increasing, since deletions cannot add characters back). The greedy rule: process frequencies from LARGEST to SMALLEST, and whenever the current frequency collides with one already claimed, keep decrementing it (counting each decrement as one deletion) until it either becomes unique or hits zero.

## 3. Core concept

**Key idea:** count each character's frequency, then process those frequencies in DESCENDING order, using a set of ALREADY-CLAIMED frequency values to detect collisions.

**Steps:**
1. Count the frequency of each of the 26 letters.
2. Sort the non-zero frequencies in DESCENDING order.
3. For each frequency, in that order: while it is `> 0` and ALREADY present in the claimed set, decrement it by `1` and increment the deletion counter.
4. Once the frequency is either `0` or not yet claimed, add it to the claimed set (if `> 0`) and move to the next.
5. Return the total deletion count.

**Why processing LARGEST first is correct:** since frequencies can only DECREASE, a larger frequency has more "room" to shrink down to some lower unclaimed value, while a SMALLER frequency has fewer options below it. Handling the largest frequencies first, while the full range of lower values is still available to shrink into, avoids a smaller frequency getting boxed in with nowhere left to go — this greedy order minimizes wasted deletions across the whole set.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="frequencies processed from largest to smallest each decremented until it no longer collides with an already claimed value">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "aaabbbcc" -- frequencies: a=3, b=3, c=2 -- sorted descending: [3, 3, 2]</text>
    <text x="10" y="45">claim 3 (from a) -- b's frequency 3 collides -- decrement to 2 (1 deletion)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">b=2 collides with c=2 -- decrement b to 1 (1 more deletion) -- total 2</text>
  </g>
</svg>

Processing the largest frequency first leaves the most room for smaller frequencies to shrink into an unclaimed value.

## 5. Runnable example

```java
// MinimumDeletionsToMakeCharacterFrequenciesUnique.java
import java.util.*;

public class MinimumDeletionsToMakeCharacterFrequenciesUnique {

    // KEY INSIGHT: process frequencies largest first -- since counts
    // can only shrink, the largest ones have the most room to move
    // down into an unclaimed value.

    static int minDeletions(String s) {
        int[] freq = new int[26];
        for (char c : s.toCharArray()) freq[c - 'a']++;

        Integer[] sorted = new Integer[26];
        for (int i = 0; i < 26; i++) sorted[i] = freq[i];
        Arrays.sort(sorted, Collections.reverseOrder());

        Set<Integer> claimed = new HashSet<>();
        int deletions = 0;
        for (int count : sorted) {
            while (count > 0 && claimed.contains(count)) {
                count--;
                deletions++;
            }
            if (count > 0) claimed.add(count);
        }
        return deletions;
    }

    public static void main(String[] args) {
        System.out.println(minDeletions("aaabbbcc"));
        // 2
        System.out.println(minDeletions("aab"));
        // 0
    }
}
```

**How to run:** `java MinimumDeletionsToMakeCharacterFrequenciesUnique.java`

## 6. Walkthrough

Trace `minDeletions("aaabbbcc")` (frequencies `a=3, b=3, c=2`, sorted descending `[3, 3, 2, 0, 0, ...]`):

| frequency | claimed so far | collision? | final value used | deletions added |
|---|---|---|---|---|
| 3 (a) | {} | no | 3 | 0 |
| 3 (b) | {3} | yes, decrement to 2 | 2 | 1 |
| 2 (c) | {3, 2} | yes, decrement to 1 | 1 | 1 |
| 0 (rest) | {3, 2, 1} | (zero, skip) | 0 | 0 |

Total `deletions = 0 + 1 + 1 = 2`, matching the expected answer. Time complexity is O(n + k log k), where `k = 26` (counting is O(n); sorting the fixed 26-letter frequency array is O(1) in practice, but written generally as O(k log k)). Space is O(k) for the claimed set.

## 7. Gotchas & takeaways

> Gotcha: once a frequency decrements all the way to `0`, it must NOT be added to the claimed set — multiple characters are allowed to share a frequency of `0` (meaning they were fully deleted), since the "unique frequency" rule only applies to characters that STILL APPEAR in the string.

- Sorting descending, then greedily decrementing on collision: the key ordering choice that guarantees minimal total deletions.
- A `HashSet` of claimed frequencies gives O(1) collision checks, keeping the total work proportional to the number of decrements actually performed, not a slower repeated linear scan.
- Related problems: Reduce Array Size to The Half (a different frequency-based greedy — removing the MOST frequent values first to shrink an array's distinct-element count, rather than making frequencies unique).
