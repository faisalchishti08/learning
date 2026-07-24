---
card: leetcode-patterns
gi: 281
slug: kth-largest-element-in-an-array
title: Kth Largest Element in an Array
---

## 1. What it is

Given an integer array `nums` and an integer `k`, return the `k`-th largest element — the `k`-th largest in SORTED ORDER, not the `k`-th distinct value. Example: `nums = [3,2,1,5,6,4]`, `k = 2` → `5` (the sorted array is `[1,2,3,4,5,6]`, and the 2nd largest is `5`).

## 2. Why & when

This is the single-answer version of the Top-K Elements pattern: instead of returning all `k` top elements, you return just the smallest one among them. It belongs to the size-k-heap signal. Use this shape whenever a problem asks for a specific rank (the `k`-th biggest or smallest), rather than the full top-k set.

## 3. Core concept

**Key idea:** maintain a min-heap of size `k`. After processing every element, the heap's smallest member (its head) is exactly the `k`-th largest element overall.

**Steps:**
1. Create a min-heap (`PriorityQueue<Integer>`, natural ordering).
2. For each number in `nums`, offer it to the heap.
3. If the heap size exceeds `k`, poll (remove) the head — the current smallest of the kept elements.
4. After the scan, the heap's head is the `k`-th largest element.

**Why it is correct:** the heap always holds the `k` largest elements seen so far, because anything smaller than the heap's current minimum gets evicted immediately. Once every element has been processed, those `k` survivors are the true `k` largest values in the whole array, and the smallest one among them is, by definition, the `k`-th largest overall.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap of size 2 tracking the 2 largest values from 3,2,1,5,6,4, ending with head equal to 5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [3,2,1,5,6,4], k = 2</text>
    <text x="10" y="45">see 3 -&gt; heap [3]</text>
    <text x="10" y="65">see 2 -&gt; heap [2,3]</text>
    <text x="10" y="85">see 1 -&gt; 1 &lt; min(2) -&gt; skip -&gt; heap [2,3]</text>
    <text x="10" y="105">see 5 -&gt; evict 2, insert 5 -&gt; heap [3,5]</text>
    <text x="10" y="125">see 6 -&gt; evict 3, insert 6 -&gt; heap [5,6]</text>
    <text x="10" y="145">see 4 -&gt; 4 &lt; min(5) -&gt; skip -&gt; heap [5,6]</text>
    <rect x="10" y="150" width="140" height="0" fill="none"/>
  </g>
</svg>

The heap's head after the scan, `5`, is the 2nd largest value in the array.

## 5. Runnable example

```java
// KthLargestInArray.java
import java.util.PriorityQueue;

public class KthLargestInArray {

    // Level 1 -- Brute force: sort nums descending, return nums[k-1].
    // Correct, but O(n log n), sorting the whole array even though
    // only one rank is needed.

    // KEY INSIGHT: you never need a full ordering -- a min-heap capped
    // at size k always holds exactly the k largest values, and its
    // head is the k-th largest.

    // Level 2 -- Optimal: size-k min-heap, O(n log k).
    static int findKthLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int num : nums) {
            heap.offer(num);
            if (heap.size() > k) {
                heap.poll();
            }
        }
        return heap.peek();
    }

    // Level 3 -- Hardened: works when k equals nums.length (the heap
    // ends up holding every element, and its head is the overall
    // minimum, which is correctly the "n-th largest") and when nums
    // contains duplicate values (duplicates are treated as separate
    // heap entries, matching the problem's "k-th in sorted order").

    public static void main(String[] args) {
        System.out.println(findKthLargest(new int[]{3, 2, 1, 5, 6, 4}, 2));
        // 5
        System.out.println(findKthLargest(new int[]{3, 2, 3, 1, 2, 4, 5, 5, 6}, 4));
        // 4
    }
}
```

**How to run:** `java KthLargestInArray.java`

## 6. Walkthrough

Trace `findKthLargest([3,2,1,5,6,4], 2)`:

| num | heap before | action | heap after |
|---|---|---|---|
| 3 | [] | offer | [3] |
| 2 | [3] | offer | [2,3] |
| 1 | [2,3] | offer, size 3 &gt; 2, poll | [2,3] |
| 5 | [2,3] | offer, size 3 &gt; 2, poll(2) | [3,5] |
| 6 | [3,5] | offer, size 3 &gt; 2, poll(3) | [5,6] |
| 4 | [5,6] | offer, size 3 &gt; 2, poll(4) | [5,6] |

Final heap `[5,6]`; head `= 5`, the 2nd largest. Time complexity is O(n log k): one O(log k) heap operation per element. Space is O(k), for the heap.

## 7. Gotchas & takeaways

> Gotcha: when polling after every offer that overflows the heap, the number that gets removed is not always the number you just inserted — the heap always removes its true current MINIMUM, which could be an older element. Tracing the heap contents (not just "did we just add or remove") avoids this mistake.

- The heap head after the full scan directly answers "k-th largest" — no extra sorting step needed at the end.
- Quickselect (a partition-based algorithm related to quicksort) solves this in average O(n) time, trading worst-case O(n²) for a faster average case; the heap approach is simpler to write correctly and has a guaranteed O(n log k) bound.
- Related problems: Top K Frequent Elements (returns a set instead of a single rank), Kth Largest Element in a Stream (the same heap, but elements arrive incrementally).
