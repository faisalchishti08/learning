---
card: leetcode-patterns
gi: 277
slug: top-k-elements-signal-k-largest-smallest-most-frequent-eleme
title: Top-K Elements — signal: k largest/smallest/most-frequent elements
---

## 1. What it is

Top-K Elements problems ask you to find the `k` largest, `k` smallest, or `k` most/least frequent items in a collection, without fully sorting everything. Think of a leaderboard that only ever needs to show the top 10 scores — you do not need to rank every player, just keep the best 10 visible at all times.

## 2. Why & when

Reach for this pattern whenever a problem asks for a fixed number `k` of extreme or frequent items, instead of asking you to sort the whole input. Sorting the entire array costs O(n log n) time. Top-K techniques answer the same question in O(n log k) time, which is much cheaper when `k` is small compared to `n`.

Learn to recognize these signals in a problem statement:

- **"Find the k largest/smallest elements"** — a direct size-k extremes query.
- **"Find the k most frequent (or least frequent) elements/words"** — frequency counting combined with a top-k selection.
- **"Find the k closest points to a target"** — a distance-based variant of k-smallest.
- **"Kth largest element in a stream"** — the same idea, but the data arrives incrementally and `k` stays fixed.

The alternative — sorting the whole array and slicing the first or last `k` — is simple to write but wastes time ordering elements you will never look at. A size-k heap only tracks the `k` best candidates seen so far.

## 3. Core concept

The pattern has two building blocks, and most problems use one of them.

**A size-k heap.** Keep a heap (priority queue) that holds exactly `k` elements. To find the `k` largest elements, use a MIN-heap of size `k`: whenever a new element beats the heap's smallest member, evict the smallest and insert the new one. After scanning everything, the heap holds the `k` largest. (For `k` smallest, use a MAX-heap of size `k` the same way, in reverse.)

**Bucket sort by frequency.** When ranking by frequency instead of value, first count occurrences with a hash map, then place each distinct value into a bucket indexed by its count (bucket `i` holds every value that appears exactly `i` times). Reading buckets from the highest index down gives the most frequent values in O(n) time, with no heap needed.

The key insight: you never need a full ordering. You only need to know, at each point, whether a new candidate belongs inside the current top-`k` set — and a size-`k` heap (or a frequency bucket array) answers that question cheaply.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A min-heap of size k tracking the k largest elements seen so far, evicting the smallest when a bigger element arrives">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Stream: 3, 7, 1, 9, 4  (k = 3, min-heap of size k)</text>
    <text x="10" y="45">see 3 -&gt; heap [3]</text>
    <text x="10" y="65">see 7 -&gt; heap [3,7]</text>
    <text x="10" y="85">see 1 -&gt; heap [1,3,7]  (heap full, size k)</text>
    <text x="10" y="105">see 9 -&gt; 9 &gt; min(1) -&gt; evict 1, insert 9 -&gt; heap [3,7,9]</text>
    <text x="10" y="125">see 4 -&gt; 4 &gt; min(3) -&gt; evict 3, insert 4 -&gt; heap [4,7,9]</text>
    <rect x="10" y="140" width="120" height="24" fill="#3fb950"/><text x="70" y="157" fill="#0d1117" text-anchor="middle" font-size="10">top-3 = {4,7,9}</text>
  </g>
</svg>

The heap only ever holds `k` items. A new value either gets discarded or swaps in for the current weakest member.

## 5. Runnable example

```java
// TopKSignal.java
import java.util.PriorityQueue;

public class TopKSignal {

    // Signal check 1: k largest via a size-k min-heap.
    static int[] kLargest(int[] nums, int k) {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>();
        for (int num : nums) {
            minHeap.offer(num);
            if (minHeap.size() > k) {
                minHeap.poll(); // evict the current smallest
            }
        }
        int[] result = new int[k];
        for (int i = k - 1; i >= 0; i--) {
            result[i] = minHeap.poll();
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {3, 7, 1, 9, 4};
        int[] top3 = kLargest(nums, 3);
        System.out.println(java.util.Arrays.toString(top3));
        // [4, 7, 9]
    }
}
```

**How to run:** `java TopKSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Find the k largest elements" is the size-k-heap signal — track only the `k` best candidates.
2. Each new number is offered to the min-heap. Once the heap holds `k` items, any smaller number never gets kept.
3. Running `kLargest` on `[3,7,1,9,4]` with `k=3` confirms the heap ends up holding `{4,7,9}`, the three largest values.
4. If instead the problem says "k most frequent elements," that is the frequency-bucket signal — count occurrences first, then bucket by count.
5. This upfront classification (extremes-by-value vs extremes-by-frequency) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: using a MAX-heap for "k largest" is tempting but wasteful — it would need to hold all `n` elements to guarantee correctness, giving back the O(n log n) cost you were trying to avoid. The size-`k` MIN-heap trick only works because you evict early, keeping the heap small the whole time.

- Size-k heap: the signal for "k largest/smallest by value" or "k closest by distance."
- Frequency bucket sort: the signal for "k most/least frequent" when you want O(n) instead of a heap's O(n log k).
- Both approaches avoid sorting the full input — they track only the `k` items that matter.
