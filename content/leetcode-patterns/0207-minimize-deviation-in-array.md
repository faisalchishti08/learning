---
card: leetcode-patterns
gi: 207
slug: minimize-deviation-in-array
title: Minimize Deviation in Array
---

## 1. What it is

Given an array `nums`, you may repeatedly do either operation on any element: double an even number, or halve (integer division) an even number back down — actually, the real rule is: double any ODD number once, or halve any EVEN number any number of times. Minimize the difference between the maximum and minimum values in the array after any sequence of operations. Example: `nums = [1,2,3,4]` → `1`.

## 2. Why & when

Every odd number can only move in ONE direction (double it once, becoming even), while every even number can shrink repeatedly (halve it until odd). The optimal strategy: first make every number as LARGE as possible (double all odds once), then greedily shrink the CURRENT maximum (the number with the most room to fall) as long as doing so keeps reducing the max-min gap. A max-heap tracking the current maximum, alongside a running minimum, drives this greedy shrink.

## 3. Core concept

**Key idea:** double every odd number once up front (this is always beneficial or neutral, since an odd number can never be reduced otherwise). Push all values into a max-heap, and track the running minimum separately. Repeatedly pop the max-heap's top; if it is even, halve it and push it back (this can only help, since it might lower the max while raising the min if the halved value becomes the new min). Stop when the top is odd (it cannot shrink further without breaking the "double once" rule) — at that point, the current `max - min` is optimal.

**Steps:**
1. For every odd number in `nums`, double it (this normalizes all numbers to their maximum reachable value from the "make everything as large as possible" strategy).
2. Push all (possibly doubled) values into a max-heap, and track the minimum value across the whole array separately.
3. Loop: pop the max-heap's top. Update the best `max - min` seen so far using this top and the current running minimum.
4. If the popped top is odd, stop (it has no further moves available). Otherwise, halve it, update the running minimum if this new value is smaller, and push it back into the heap.
5. Return the best `max - min` found across all iterations.

**Why it is correct:** starting from every number's LARGEST possible value and only ever shrinking the CURRENT maximum is optimal because shrinking anything other than the current max can never reduce the max-min gap (the gap is bounded below by the max, so only reducing the max — or reducing the min, tracked automatically as a side effect of a halving that produces a new smallest value — helps). Stopping once the max-heap's top is odd is correct because an odd number has no legal move left to shrink it further.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap tracks the current maximum; each round halves it if even, shrinking the gap, until it becomes odd">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="60" r="18" fill="#161b22" stroke="#e3b341"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle">8</text>
    <path d="M130,60 L200,60" stroke="#79c0ff" marker-end="url(#a8)"/>
    <defs><marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <circle cx="230" cy="60" r="18" fill="#161b22" stroke="#e3b341"/><text x="230" y="64" fill="#e6edf3" text-anchor="middle">4</text>
    <path d="M260,60 L330,60" stroke="#79c0ff" marker-end="url(#a8)"/>
    <circle cx="360" cy="60" r="18" fill="#161b22" stroke="#f85149"/><text x="360" y="64" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="10" y="15" fill="#e6edf3">current max halves each round (8-&gt;4-&gt;2) as long as it stays even, shrinking the max-min gap</text>
  </g>
</svg>

The heap's top (current maximum) keeps halving while even, and each halved value is checked against the running minimum before the loop stops at an odd top.

## 5. Runnable example

```java
// MinimizeDeviationInArray.java
import java.util.*;

public class MinimizeDeviationInArray {

    // Level 1 -- Brute force: try all combinations of operations up to
    // some bound via BFS/DFS over possible array states, tracking the
    // minimum deviation found. Correct in principle, but the state
    // space explodes combinatorially -- completely impractical beyond
    // tiny arrays.

    // KEY INSIGHT: normalize everything to its LARGEST reachable value
    // first (double all odds once), then greedily shrink only the
    // CURRENT max as long as it is even -- a max-heap makes finding
    // "the current max" an O(log n) operation each round.

    // Level 2 -- Optimal: max-heap of current values, greedy shrink of
    // the max.
    static int minimumDeviation(int[] nums) {
        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
        int minVal = Integer.MAX_VALUE;

        for (int num : nums) {
            int value = (num % 2 == 1) ? num * 2 : num;
            maxHeap.add(value);
            minVal = Math.min(minVal, value);
        }

        int result = Integer.MAX_VALUE;
        while (true) {
            int max = maxHeap.poll();
            result = Math.min(result, max - minVal);
            if (max % 2 != 0) break;
            int halved = max / 2;
            minVal = Math.min(minVal, halved);
            maxHeap.add(halved);
        }
        return result;
    }

    // Level 3 -- Hardened: `minVal` is updated BEFORE the loop even
    // starts (during the initial doubling pass), so the very first
    // `max - minVal` comparison is already correct, not relying on the
    // loop body to establish it.

    public static void main(String[] args) {
        System.out.println(minimumDeviation(new int[]{1,2,3,4})); // 1
        System.out.println(minimumDeviation(new int[]{4,1,5,20,3})); // 3
        System.out.println(minimumDeviation(new int[]{2,10,8})); // 3
    }
}
```

**How to run:** `java MinimizeDeviationInArray.java`

## 6. Walkthrough

Trace `nums = [1,2,3,4]`: doubling odds gives `[2,2,6,4]` (1→2, 3→6), `minVal = 2`.

| Round | maxHeap top | result so far | Action |
|---|---|---|---|
| 1 | 6 | min(∞, 6-2)=4 | even, halve to 3, minVal stays 2, push 3 |
| 2 | 4 | min(4, 4-2)=2 | even, halve to 2, minVal stays 2, push 2 |
| 3 | 3 | min(2, 3-2)=1 | odd, stop |

Result is `1`, matching the expected output. Time complexity is O(n log n), since each halving operation adds at most one more heap operation per original element (each value can only halve O(log(max value)) times); space is O(n) for the heap.

## 7. Gotchas & takeaways

> Gotcha: forgetting to update `minVal` when a NEW halved value is pushed back into the heap misses the case where the shrinking maximum becomes the new overall minimum, which can make the true best deviation look worse than it actually is.

- Doubling every odd number ONCE, up front, before the main loop, correctly represents "odd numbers have exactly one legal move" — do not try to double them again inside the loop.
- The loop must check `max % 2 != 0` on the POPPED value's ORIGINAL parity before halving — a value that started even and has been halved down to odd correctly stops, since further halving is not a legal integer operation for an odd number in this problem.
- Related problems: Furthest Building You Can Reach (max-heap-adjacent greedy, different mechanics), Find Median from Data Stream (max-heap as one half of the two-heaps core structure).
