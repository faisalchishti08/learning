---
card: leetcode-patterns
gi: 284
slug: kth-largest-element-in-a-stream
title: Kth Largest Element in a Stream
---

## 1. What it is

Design a class `KthLargest` that keeps track of the `k`-th largest element in a growing stream of numbers. The constructor takes `k` and an initial array `nums`. The method `add(val)` adds `val` to the stream and returns the current `k`-th largest element. Example: `k = 3`, initial `nums = [4,5,8,2]`; `add(3)` → `4`; `add(5)` → `5`; `add(10)` → `5`; `add(9)` → `8`; `add(4)` → `8`.

## 2. Why & when

This is the STREAMING version of Kth Largest Element in an Array: instead of one array processed once, values keep arriving one at a time, and each `add` call must answer the same "what is the k-th largest so far" question immediately. Use this shape whenever a problem asks you to maintain a running top-k answer across many incremental updates, not a single one-shot computation.

## 3. Core concept

**Key idea:** keep a persistent min-heap of size `k` as an instance field. Every `add` call inserts the new value and, if needed, evicts the current smallest kept value — exactly like the array version, but the heap survives BETWEEN calls instead of being rebuilt each time.

**Steps:**
1. In the constructor, create the min-heap and offer every value from the initial `nums`, capping the heap at size `k` as you go (mirroring the size-k-heap template).
2. In `add(val)`, offer `val` to the heap.
3. If the heap size exceeds `k`, poll (remove) the head — the current smallest of the kept elements.
4. Return the heap's head — the `k`-th largest value among everything seen so far.

**Why it is correct:** the heap invariant ("holds the k largest values seen so far") is established once in the constructor and preserved by every subsequent `add` call, using the identical offer-then-evict-if-oversized logic. Because the heap persists across calls, you never re-scan old values — each `add` does a fixed, small amount of work regardless of how many values came before it.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Persistent min-heap of size 3 across multiple add calls, updating the k-th largest value each time">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">k = 3, initial nums = [4,5,8,2]</text>
    <text x="10" y="45">constructor -&gt; heap [4,5,8]  (2 dropped, heap capped at k)</text>
    <text x="10" y="65">add(3) -&gt; 3 &lt; min(4) -&gt; heap stays [4,5,8]  -&gt; return 4</text>
    <text x="10" y="85">add(5) -&gt; evict 4, insert 5 -&gt; heap [5,5,8]  -&gt; return 5</text>
    <text x="10" y="105">add(10) -&gt; evict 5, insert 10 -&gt; heap [5,8,10] -&gt; return 5</text>
    <text x="10" y="125">add(9) -&gt; evict 5, insert 9 -&gt; heap [8,9,10]  -&gt; return 8</text>
    <rect x="10" y="140" width="10" height="10" fill="none"/>
  </g>
</svg>

The heap survives across `add` calls, always holding the 3 largest values seen so far.

## 5. Runnable example

```java
// KthLargestInStream.java
import java.util.PriorityQueue;

public class KthLargestInStream {

    // KEY INSIGHT: a size-k min-heap that PERSISTS between calls turns
    // a repeated "k-th largest of everything so far" query into O(log k)
    // work per add, instead of O(n log n) per query if re-sorted each time.

    static class KthLargest {
        private final int k;
        private final PriorityQueue<Integer> heap = new PriorityQueue<>();

        KthLargest(int k, int[] nums) {
            this.k = k;
            for (int num : nums) add(num);
        }

        int add(int val) {
            heap.offer(val);
            if (heap.size() > k) {
                heap.poll();
            }
            return heap.peek();
        }
    }

    public static void main(String[] args) {
        KthLargest kthLargest = new KthLargest(3, new int[]{4, 5, 8, 2});
        System.out.println(kthLargest.add(3));  // 4
        System.out.println(kthLargest.add(5));  // 5
        System.out.println(kthLargest.add(10)); // 5
        System.out.println(kthLargest.add(9));  // 8
        System.out.println(kthLargest.add(4));  // 8
    }
}
```

**How to run:** `java KthLargestInStream.java`

## 6. Walkthrough

Trace the full sequence with `k = 3`:

| call | heap before | action | heap after | returned |
|---|---|---|---|---|
| constructor(4,5,8,2) | [] | offer 4,5,8,2, evict when size &gt; 3 | [4,5,8] | — |
| add(3) | [4,5,8] | offer 3, size 4 &gt; 3, poll(3, the new min) | [4,5,8] | 4 |
| add(5) | [4,5,8] | offer 5, size 4 &gt; 3, poll(4) | [5,5,8] | 5 |
| add(10) | [5,5,8] | offer 10, size 4 &gt; 3, poll(5) | [5,8,10] | 5 |
| add(9) | [5,8,10] | offer 9, size 4 &gt; 3, poll(5) | [8,9,10] | 8 |
| add(4) | [8,9,10] | offer 4, size 4 &gt; 3, poll(4, the new min) | [8,9,10] | 8 |

Time complexity is O(log k) per `add` call (plus O(n log k) for the constructor's initial `n` inserts). Space is O(k), for the persistent heap.

## 7. Gotchas & takeaways

> Gotcha: reusing the constructor's own `add` method to seed the initial heap is convenient, but only correct if `add` already implements the full offer-then-evict-if-oversized logic — if `add` instead assumed the heap always has room, seeding it with more than `k` initial values would silently break the size-k invariant.

- The core technique is identical to Kth Largest Element in an Array — the only new idea is making the heap a persistent field so state carries across calls.
- Each `add` call costs O(log k), regardless of how many values have streamed in before it — the heap never grows past size `k`.
- Related problems: Kth Largest Element in an Array (the one-shot, non-streaming version), Top K Frequent Elements (a different ranking key, same size-k-heap mechanics).
