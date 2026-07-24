---
card: leetcode-patterns
gi: 290
slug: sort-the-people
title: Sort the People
---

## 1. What it is

Given an array of strings `names` and an integer array `heights`, both of the same length, where `heights[i]` is the height of the person named `names[i]`, return `names` sorted so the tallest person comes first. All heights are distinct. Example: `names = ["Mary","John","Emma"]`, `heights = [180,165,170]` → `["Mary","Emma","John"]`.

## 2. Why & when

This is a top-k-style ranking problem where `k` equals the FULL array length: every name must be ranked by its paired height, descending. It uses the size-k-heap idea's underlying comparator technique, but since every element is kept (not just the top `k`), a plain full-array sort by a paired key is the simpler and equally efficient choice. Use this shape whenever a problem ranks one array by VALUES stored in a second, parallel array.

## 3. Core concept

**Key idea:** pair each name with its height, sort the pairs by height descending, then extract just the names in that order.

**Steps:**
1. Create an array of indices `0` to `n-1`.
2. Sort the indices using a comparator that compares `heights[i]` for two indices, descending.
3. Build the result by reading `names[i]` in the sorted index order.

**Why it is correct:** sorting the INDICES (instead of directly sorting the names or heights arrays) keeps each name correctly paired with its own height throughout the sort, since the comparator always looks up `heights[index]` for the ORIGINAL index, regardless of how the indices get reordered. Because heights are guaranteed distinct, the descending order is unambiguous, with no ties to break.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sorting index array by paired height values descending, then reading names in that order">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">names = [Mary, John, Emma], heights = [180, 165, 170]</text>
    <text x="10" y="45">indices = [0, 1, 2]</text>
    <text x="10" y="65">sort indices by heights[i] desc: [0 (180), 2 (170), 1 (165)]</text>
    <rect x="10" y="85" width="230" height="24" fill="#3fb950"/><text x="125" y="102" fill="#0d1117" text-anchor="middle" font-size="10">result = [Mary, Emma, John]</text>
  </g>
</svg>

Sorting indices (not the names directly) keeps each name correctly paired with its own height.

## 5. Runnable example

```java
// SortThePeople.java
import java.util.*;

public class SortThePeople {

    // KEY INSIGHT: sort an array of INDICES by a comparator that
    // looks up a parallel array's values -- this keeps two
    // differently-typed parallel arrays correctly paired through
    // the sort, without building intermediate pair objects.

    static String[] sortPeople(String[] names, int[] heights) {
        int n = names.length;
        Integer[] indices = new Integer[n];
        for (int i = 0; i < n; i++) indices[i] = i;

        Arrays.sort(indices, (a, b) -> heights[b] - heights[a]); // descending

        String[] result = new String[n];
        for (int i = 0; i < n; i++) {
            result[i] = names[indices[i]];
        }
        return result;
    }

    public static void main(String[] args) {
        String[] result = sortPeople(
            new String[]{"Mary", "John", "Emma"},
            new int[]{180, 165, 170}
        );
        System.out.println(Arrays.toString(result));
        // [Mary, Emma, John]
    }
}
```

**How to run:** `java SortThePeople.java`

## 6. Walkthrough

Trace `sortPeople(["Mary","John","Emma"], [180,165,170])`:

| index | name | height |
|---|---|---|
| 0 | Mary | 180 |
| 1 | John | 165 |
| 2 | Emma | 170 |

Sorting `indices = [0,1,2]` by `heights[i]` descending gives `[0, 2, 1]` (180, then 170, then 165). Reading `names` at those indices produces `["Mary", "Emma", "John"]`. Time complexity is O(n log n), the cost of sorting `n` indices. Space is O(n), for the boxed `Integer[]` index array and the result array.

## 7. Gotchas & takeaways

> Gotcha: sorting `names` and `heights` as two SEPARATE arrays (for example, sorting `heights` directly and independently reordering `names`) is incorrect unless done through a single shared permutation — sorting each array on its own destroys the pairing between a name and its original height.

- This problem is a full-array special case of the size-k-heap idea: when `k` equals the array length, a plain O(n log n) sort by the paired key is simpler and equally fast as any heap-based approach.
- Sorting an INDEX array with a comparator that references a parallel array is a reusable technique whenever you must reorder one array based on values stored in another.
- Related problems: Find the Kth Largest Integer in the Array (a custom comparator for numeric strings), Kth Largest Element in an Array (a plain numeric ranking, no parallel array involved).
