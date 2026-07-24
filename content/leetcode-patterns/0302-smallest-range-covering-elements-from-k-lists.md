---
card: leetcode-patterns
gi: 302
slug: smallest-range-covering-elements-from-k-lists
title: Smallest Range Covering Elements from K Lists
---

## 1. What it is

Given `k` lists of integers, each sorted ascending, find the smallest range `[a, b]` that includes AT LEAST ONE number from each of the `k` lists. If multiple ranges have the same smallest size, return the one with the smallest `a`. Example: `nums = [[4,10,15,24,26],[0,9,12,20],[5,18,22,30]]` → `[20,24]`.

## 2. Why & when

This is K-way Merge with an extra twist: instead of just producing values in sorted order, you track the CURRENT SPREAD (max minus min) of one candidate from each list at every step, and shrink that spread as you advance. Use this shape whenever a problem needs a range or window that must simultaneously satisfy a condition across `k` sorted sequences at once.

## 3. Core concept

**Key idea:** keep a min-heap holding exactly one current candidate from each of the `k` lists, plus a running `currentMax` of everything currently in the heap. At every step, the range `[heap's min, currentMax]` covers all `k` lists (one value from each). Advance the SMALLEST candidate's list forward, since that is the only way the range's lower bound could shrink.

**Steps:**
1. Push `(value, listIndex, elementIndex)` for the first element of every list into a min-heap; track `currentMax` as the largest of those seeded values.
2. Repeat: let `currentMin` be the heap's minimum. If `currentMax - currentMin` is smaller than the best range found so far (or ties with a smaller `currentMin`), update the best range to `[currentMin, currentMax]`.
3. Pop the heap's minimum. If that list has no more elements, STOP — no further range can cover every list.
4. Otherwise, push that list's next element, and update `currentMax` if the new value is larger.
5. Return the best range found.

**Why it is correct:** at every step, the heap holds exactly one element per list, so `[heap min, currentMax]` always covers all `k` lists by construction. The ONLY way to shrink the range's LEFT edge is to advance whichever list currently holds the smallest value (moving any other list forward could only raise `currentMax` without helping the minimum). Once any list is exhausted, no smaller range covering all `k` lists can exist, since that list can never contribute a value again.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap tracking one candidate per list plus a running max, shrinking the covering range by advancing the smallest candidate each round">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">lists: [4,10,15,24,26], [0,9,12,20], [5,18,22,30]</text>
    <text x="10" y="45">seed heap: 4, 0, 5 -&gt; currentMax=5 -&gt; range [0,5], size 5</text>
    <text x="10" y="65">pop 0 (list B) -&gt; push 9 -&gt; currentMax=9 -&gt; range [4,9], size 5</text>
    <text x="10" y="85">... advancing continues, tracking the best (smallest) range seen ...</text>
    <text x="10" y="110">eventually: heap holds 20(B), 22(C), 24(A) -&gt; range [20,24], size 4</text>
    <rect x="10" y="125" width="180" height="24" fill="#3fb950"/><text x="100" y="142" fill="#0d1117" text-anchor="middle" font-size="10">best range = [20, 24]</text>
  </g>
</svg>

Advancing the smallest candidate each round is the only move that can shrink the range's left edge.

## 5. Runnable example

```java
// SmallestRangeCoveringKLists.java
import java.util.PriorityQueue;

public class SmallestRangeCoveringKLists {

    // KEY INSIGHT: a min-heap with one candidate per list always
    // covers all k lists; the range's right edge only grows, so
    // shrinking the range means always advancing the CURRENT
    // smallest candidate's list.

    static int[] smallestRange(int[][] nums) {
        // {value, listIndex, elementIndex}
        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        int currentMax = Integer.MIN_VALUE;

        for (int i = 0; i < nums.length; i++) {
            heap.offer(new int[]{nums[i][0], i, 0});
            currentMax = Math.max(currentMax, nums[i][0]);
        }

        int bestStart = 0, bestEnd = Integer.MAX_VALUE;

        while (true) {
            int[] top = heap.poll();
            int currentMin = top[0];
            int listIdx = top[1], elemIdx = top[2];

            if (currentMax - currentMin < bestEnd - bestStart) {
                bestStart = currentMin;
                bestEnd = currentMax;
            }

            if (elemIdx + 1 == nums[listIdx].length) {
                break; // this list is exhausted, no smaller full-cover range remains
            }

            int nextVal = nums[listIdx][elemIdx + 1];
            heap.offer(new int[]{nextVal, listIdx, elemIdx + 1});
            currentMax = Math.max(currentMax, nextVal);
        }
        return new int[]{bestStart, bestEnd};
    }

    public static void main(String[] args) {
        int[][] nums = {{4, 10, 15, 24, 26}, {0, 9, 12, 20}, {5, 18, 22, 30}};
        System.out.println(java.util.Arrays.toString(smallestRange(nums)));
        // [20, 24]
    }
}
```

**How to run:** `java SmallestRangeCoveringKLists.java`

## 6. Walkthrough

Trace the key rounds of `smallestRange` on the example:

| round | popped (currentMin) | currentMax | range size | best so far |
|---|---|---|---|---|
| 1 | 0 (list B) | 5 | 5 | [0,5] (first candidate, always recorded) |
| 2–8 | 4, 5, 9, 10, 12, 15, 18 | grows to 24 | 5 to 9 | [0,5] stays best (no smaller range found) |
| 9 | 20 (list B) | 24 | 4 | [20,24] (smaller than 5, becomes new best) |

Round 9 also finds that list B's popped element (`20`) was its LAST element, so the loop stops immediately after. Time complexity is O(n log k), where `n` is the total number of elements across all `k` lists: each element is pushed and popped once, each operation O(log k). Space is O(k), for the heap.

## 7. Gotchas & takeaways

> Gotcha: stopping too early (checking the exhaustion condition BEFORE evaluating the current range) would miss the best range found at the final valid step — always update the best range first, THEN check whether to stop.

- Tracking `currentMax` incrementally (never recomputing it by scanning the heap) is what keeps each round O(log k) instead of O(k).
- The "advance the current minimum" rule is the only correct greedy move — advancing any other list either does nothing useful or can only make the range worse.
- Related problems: Merge k Sorted Lists (the same one-candidate-per-list heap setup, without range tracking), Sliding Window Maximum (a different pattern, but shares the idea of tracking a running extreme value efficiently).
