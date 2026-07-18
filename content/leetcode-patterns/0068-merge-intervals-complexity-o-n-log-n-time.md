---
card: leetcode-patterns
gi: 68
slug: merge-intervals-complexity-o-n-log-n-time
title: Merge Intervals — complexity: O(n log n) time
---

## 1. What it is

This page states and proves the time and space cost of the Merge Intervals pattern: O(n log n) time, dominated by the initial sort, and O(n) space for the sorted copy and the result (or O(1) extra space if sorting in place and the output does not count against space).

## 2. Why & when

Knowing that O(n log n) is essentially unavoidable for this pattern helps you recognize when a proposed O(n) solution is actually wrong (intervals almost never come pre-sorted in an interview problem) and when it is a legitimate optimization (some follow-ups specify the input is already sorted, which removes the sort and drops the total to O(n)).

## 3. Core concept

**Time — O(n log n):**
- Sorting the `n` intervals by start value costs O(n log n) — this dominates.
- The subsequent merge scan or sweep-line pass over the sorted data (or `2n` events) costs O(n).
- Total: O(n log n) + O(n) = O(n log n).

**Space — O(n):**
- The sort itself may need O(n) space (or O(log n) for the recursion of an in-place sort like quicksort, depending on the language's sort implementation).
- The result list of merged intervals can hold up to `n` intervals in the worst case (no overlaps at all).
- The sweep-line variant creates `2n` events, which is still O(n).

**Special case — already sorted input:** if the problem guarantees the intervals arrive pre-sorted by start (a common variant of Insert Interval), skip the sort entirely and the whole algorithm drops to O(n) time.

| Variant | Time | Space |
|---|---|---|
| Unsorted input, sort then merge | O(n log n) | O(n) |
| Pre-sorted input, merge only | O(n) | O(n) |
| Sweep-line (events sorted) | O(n log n) | O(n) |

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Time breakdown of sort plus scan">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">total time = sort cost + scan cost</text>
    <rect x="20" y="40" width="300" height="30" fill="#161b22" stroke="#f0883e"/><text x="170" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">sort: O(n log n)</text>
    <rect x="320" y="40" width="120" height="30" fill="#161b22" stroke="#3fb950"/><text x="380" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">scan: O(n)</text>
    <text x="20" y="100" fill="#8b949e">sort dominates once n grows -- the single left-to-right scan is comparatively cheap</text>
  </g>
</svg>

The sort bar is drawn wider than the scan bar because O(n log n) grows faster than O(n) as input size increases — sorting is the bottleneck.

## 5. Runnable example

```java
// MergeIntervalsComplexity.java
import java.util.*;

public class MergeIntervalsComplexity {

    // General case: unsorted input. O(n log n) time (sort dominates),
    // O(n) space.
    static int[][] mergeUnsorted(int[][] intervals) {
        int[][] copy = intervals.clone();
        Arrays.sort(copy, (a, b) -> Integer.compare(a[0], b[0])); // O(n log n)
        return mergeSorted(copy); // O(n)
    }

    // Special case: input already sorted by start. O(n) time, O(n) space
    // -- no sort step needed.
    static int[][] mergeSorted(int[][] sortedIntervals) {
        List<int[]> result = new ArrayList<>();
        int[] current = sortedIntervals[0];
        for (int i = 1; i < sortedIntervals.length; i++) {
            if (sortedIntervals[i][0] <= current[1]) {
                current[1] = Math.max(current[1], sortedIntervals[i][1]);
            } else {
                result.add(current);
                current = sortedIntervals[i];
            }
        }
        result.add(current);
        return result.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        int[][] unsorted = {{8, 10}, {1, 3}, {2, 6}, {15, 18}};
        long start = System.nanoTime();
        int[][] result1 = mergeUnsorted(unsorted);
        long unsortedTime = System.nanoTime() - start;

        int[][] alreadySorted = {{1, 3}, {2, 6}, {8, 10}, {15, 18}};
        start = System.nanoTime();
        int[][] result2 = mergeSorted(alreadySorted);
        long sortedTime = System.nanoTime() - start;

        System.out.println("unsorted-path result: " + Arrays.deepToString(result1));
        System.out.println("sorted-path result:   " + Arrays.deepToString(result2));
        System.out.println("(sorted-path skips the O(n log n) sort step entirely)");
    }
}
```

How to run: save as `MergeIntervalsComplexity.java`, then run `java MergeIntervalsComplexity.java`.

## 6. Walkthrough

1. `mergeUnsorted` first sorts the 4 intervals — this step alone costs O(n log n), roughly 4 · log₂(4) = 8 comparison-equivalent units of work for this tiny example, growing much faster than `n` alone as input scales.
2. It then calls `mergeSorted`, which does a single O(n) pass — 3 comparisons for 4 intervals.
3. `mergeSorted`, called directly on already-sorted input, skips the sort step and does only the O(n) pass, producing the identical merged result with strictly less total work.
4. Both paths produce the same merged intervals — `[[1,6],[8,10],[15,18]]`, confirming that skipping the sort (when legally allowed by the problem) only saves time, not correctness.

## 7. Gotchas & takeaways

> Gotcha: assuming a problem's intervals arrive sorted just because they "look sorted" in the example input — always check the constraints section explicitly, since acting on an unsorted array as if it were sorted silently produces wrong merges.

- O(n log n) is close to the theoretical floor for this pattern: you cannot correctly group overlapping intervals without effectively ordering them by position first.
- If a problem explicitly promises sorted input, exploit it — it turns an O(n log n) solution into a true O(n) one.
