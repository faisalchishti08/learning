---
card: leetcode-patterns
gi: 293
slug: k-way-merge-signal-merge-k-sorted-lists-arrays-or-pick-acros
title: K-way Merge — signal: merge k sorted lists/arrays or pick across k sequences
---

## 1. What it is

K-way Merge problems combine `k` ALREADY-SORTED sequences (lists, arrays, or matrix rows) into one sorted output, or repeatedly pick the next-smallest value across all `k` sequences. Think of merging `k` sorted decks of cards into one sorted deck, always taking whichever visible top card is smallest.

## 2. Why & when

Reach for this pattern whenever you have MULTIPLE sorted sequences and need to combine, rank, or pick across them in sorted order, without concatenating everything and re-sorting from scratch. Re-sorting a combined array of total size `n` costs O(n log n); a k-way merge does the same job in O(n log k), by exploiting the fact that each individual sequence is already sorted.

Learn to recognize these signals in a problem statement:

- **"Merge k sorted lists/arrays"** — a direct k-way merge into one sorted output.
- **"Kth smallest element in a sorted matrix"** — each row (or column) of the matrix is itself a sorted sequence; merge across rows to find a specific rank.
- **"Find the smallest range covering elements from k lists"** — repeatedly advance the current minimum across all `k` lists.
- **"K pairs with smallest sums"** — generating sums lazily in sorted order across two sorted arrays is a two-way (then generalized k-way) merge.

The alternative — dumping every element from every sequence into one big array and sorting it — ignores the fact that each sequence already arrives sorted, wasting the ordering you were handed for free.

## 3. Core concept

The pattern always uses a MIN-HEAP holding one "current candidate" from each of the `k` sequences:

**Seed the heap.** Push the first (smallest) element of each of the `k` sequences into the heap, tagged with which sequence it came from.

**Repeatedly extract and advance.** Pop the heap's minimum — this is guaranteed to be the smallest value not yet output, across ALL `k` sequences, since every sequence's un-popped elements are still at least as large as its current head. Push that sequence's NEXT element (if any) into the heap to replace what was just popped.

**Stop when done.** Continue until the heap is empty (full merge) or until you have popped the specific number of elements you needed (for a "kth smallest" style question).

The key insight: at any moment, the true next-smallest value across all sequences MUST be one of the `k` current heads, because every sequence is sorted internally — so you only ever need to compare `k` candidates at a time, not the full `n` elements.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap holding the current head of three sorted lists, repeatedly popping the smallest and advancing that list">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Lists: [1,4,7], [2,5,8], [3,6,9]  (k=3)</text>
    <text x="10" y="45">seed heap with heads: [1, 2, 3]</text>
    <text x="10" y="65">pop 1 (from list A) -&gt; output [1] -&gt; push A's next (4) -&gt; heap [2,3,4]</text>
    <text x="10" y="85">pop 2 (from list B) -&gt; output [1,2] -&gt; push B's next (5) -&gt; heap [3,4,5]</text>
    <text x="10" y="105">pop 3 (from list C) -&gt; output [1,2,3] -&gt; push C's next (6) -&gt; heap [4,5,6]</text>
    <rect x="10" y="120" width="200" height="24" fill="#3fb950"/><text x="110" y="137" fill="#0d1117" text-anchor="middle" font-size="10">merged so far: 1, 2, 3, ...</text>
  </g>
</svg>

Each pop-and-push keeps the heap size fixed at `k`, always holding the current head of every unfinished sequence.

## 5. Runnable example

```java
// KWayMergeSignal.java
import java.util.PriorityQueue;

public class KWayMergeSignal {

    // Signal check: merge k sorted arrays into one sorted output,
    // using a min-heap holding one (value, arrayIndex, elementIndex).
    static int[] mergeKSortedArrays(int[][] arrays) {
        int total = 0;
        for (int[] arr : arrays) total += arr.length;

        // {value, arrayIndex, elementIndex}
        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        for (int i = 0; i < arrays.length; i++) {
            if (arrays[i].length > 0) heap.offer(new int[]{arrays[i][0], i, 0});
        }

        int[] result = new int[total];
        int idx = 0;
        while (!heap.isEmpty()) {
            int[] top = heap.poll();
            result[idx++] = top[0];
            int arrIdx = top[1], elemIdx = top[2] + 1;
            if (elemIdx < arrays[arrIdx].length) {
                heap.offer(new int[]{arrays[arrIdx][elemIdx], arrIdx, elemIdx});
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] arrays = {{1, 4, 7}, {2, 5, 8}, {3, 6, 9}};
        System.out.println(java.util.Arrays.toString(mergeKSortedArrays(arrays)));
        // [1, 2, 3, 4, 5, 6, 7, 8, 9]
    }
}
```

**How to run:** `java KWayMergeSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Merge k sorted lists" is the direct k-way-merge signal — seed a heap with one head per list.
2. Running `mergeKSortedArrays` on `[[1,4,7],[2,5,8],[3,6,9]]` confirms the output comes out fully sorted: `[1,2,3,4,5,6,7,8,9]`.
3. If instead the problem says "kth smallest in a sorted matrix," recognize each ROW as one of the `k` sorted sequences, and stop popping once you reach the desired rank.
4. If the problem says "smallest range covering elements from k lists," recognize it needs the heap's CURRENT minimum AND maximum tracked together at every step, not just a full merge.
5. This upfront classification (full merge vs. rank query vs. range tracking) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: forgetting to push a sequence's NEXT element after popping its current head silently drops that sequence from the merge early, producing a shorter-than-expected, incorrectly-merged result — every pop must be paired with a push (unless that sequence is exhausted).

- A min-heap of size `k`, holding one candidate per sequence: the core K-way Merge signal.
- Works for lists, arrays, or matrix rows/columns — anything already internally sorted.
- Distinguish "full merge" (heap runs until empty) from "kth smallest" (heap runs exactly `k` pops) from "range tracking" (heap runs while also tracking a running max).
