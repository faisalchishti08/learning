---
card: leetcode-patterns
gi: 400
slug: russian-doll-envelopes
title: Russian Doll Envelopes
---

## 1. What it is

Given a list of envelopes `[width, height]`, one envelope can fit inside another only if BOTH its width and height are STRICTLY SMALLER. Return the MAXIMUM number of envelopes that can be nested inside each other, like Russian dolls. Example: `envelopes = [[5,4],[6,4],[6,7],[2,3]]` → `3` (`[2,3] -> [5,4] -> [6,7]`).

## 2. Why & when

This is LIS on TWO dimensions, reduced to LIS on ONE dimension via a clever sort: sort by width ascending, and for TIES in width, sort by height DESCENDING. After this sort, finding the longest nesting chain becomes exactly the longest increasing subsequence of the HEIGHTS alone. Use this shape whenever a problem needs a chain that is strictly increasing in TWO attributes simultaneously — the descending tie-break on the second attribute is the key trick that prevents same-first-attribute elements from being incorrectly chained.

## 3. Core concept

**Key idea:** sort envelopes by width ascending; for equal widths, sort by height DESCENDING. Then run the standard LIS algorithm (patience sorting, for O(n log n)) on just the HEIGHT sequence.

**Steps:**
1. Sort `envelopes` by `[0]` (width) ascending; break ties by `[1]` (height) descending.
2. Extract the heights, in this sorted order, into an array.
3. Run the O(n log n) patience-sorting LIS algorithm on the height array (strictly increasing).
4. Return the resulting LIS length.

**Why the descending tie-break on height is essential:** two envelopes with the SAME width can never nest inside each other (nesting requires BOTH dimensions to be strictly smaller). If ties were sorted by height ASCENDING instead, the LIS scan over heights could incorrectly treat two same-width envelopes as a valid increasing pair (since their heights would appear in increasing order too). Sorting ties DESCENDING instead ensures that, within a group of equal widths, the heights appear in DECREASING order — so the LIS algorithm can never pick two of them into the same increasing chain, correctly forbidding same-width nesting.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="envelopes sorted by width ascending and height descending for ties, reducing to a plain lis on the height sequence">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">envelopes = [[5,4],[6,4],[6,7],[2,3]]</text>
    <text x="10" y="45">sorted: [2,3], [5,4], [6,7], [6,4] (width-6 group: height DESC: 7 before 4)</text>
    <text x="10" y="65">heights sequence: [3, 4, 7, 4] -- run plain LIS</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">LIS of heights = 3</text>
  </g>
</svg>

The descending height tie-break makes same-width envelopes appear "decreasing," so LIS never chains two of them together.

## 5. Runnable example

```java
// RussianDollEnvelopes.java
import java.util.*;

public class RussianDollEnvelopes {

    // KEY INSIGHT: sort by width ascending, height DESCENDING on ties
    // -- this reduces 2D nesting to a plain 1D LIS on heights, since
    // same-width envelopes can never chain together after this sort.

    static int maxEnvelopes(int[][] envelopes) {
        Arrays.sort(envelopes, (a, b) ->
                a[0] != b[0] ? a[0] - b[0] : b[1] - a[1]);

        List<Integer> tails = new ArrayList<>();
        for (int[] envelope : envelopes) {
            int height = envelope[1];
            int pos = Collections.binarySearch(tails, height);
            if (pos < 0) pos = -(pos + 1);
            if (pos == tails.size()) {
                tails.add(height);
            } else {
                tails.set(pos, height);
            }
        }
        return tails.size();
    }

    public static void main(String[] args) {
        System.out.println(maxEnvelopes(new int[][]{{5, 4}, {6, 4}, {6, 7}, {2, 3}}));
        // 3
        System.out.println(maxEnvelopes(new int[][]{{1, 1}, {1, 1}, {1, 1}}));
        // 1
    }
}
```

**How to run:** `java RussianDollEnvelopes.java`

## 6. Walkthrough

Trace `maxEnvelopes([[5,4],[6,4],[6,7],[2,3]])`, sorted to `[[2,3],[5,4],[6,7],[6,4]]`, heights `[3,4,7,4]`:

| height processed | tails before | action | tails after |
|---|---|---|---|
| 3 | [] | append | [3] |
| 4 | [3] | append | [3,4] |
| 7 | [3,4] | append | [3,4,7] |
| 4 | [3,4,7] | replace index 1 | [3,4,7] |

Final `tails.size() = 3`, matching the expected answer. Time complexity is O(n log n) (dominated by sorting and the patience-sorting LIS). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: sorting ties by height ASCENDING (the natural instinct, matching the width sort direction) is WRONG here — it would let same-width envelopes chain together in the LIS scan, overcounting the nesting depth.

- Reducing a 2D "strictly increasing in both dimensions" chain to a 1D LIS via a clever sort (ascending on the primary key, DESCENDING on the secondary key for ties) is a general and powerful technique — watch for it whenever a problem needs BOTH dimensions to strictly increase together.
- This problem reuses Template B (patience sorting) from the pattern's template page directly, once the sort has reduced it to a 1D problem.
- Related problems: Best Team With No Conflicts (a similar two-attribute sort-then-LIS technique, but ties are sorted ASCENDING there, since same-age players are explicitly ALLOWED to combine, unlike same-width envelopes here).
