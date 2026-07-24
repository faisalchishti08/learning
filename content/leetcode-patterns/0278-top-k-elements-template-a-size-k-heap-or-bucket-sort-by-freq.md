---
card: leetcode-patterns
gi: 278
slug: top-k-elements-template-a-size-k-heap-or-bucket-sort-by-freq
title: Top-K Elements — template: a size-k heap or bucket sort by frequency
---

## 1. What it is

This page gives the two reusable templates for Top-K Elements problems: a size-k heap for "top k by value or distance," and a frequency-bucket array for "top k by count." Both templates plug directly into a wide range of problems with almost no change.

## 2. Why & when

Use the size-k heap template whenever you compare elements directly (by value, by distance, by any comparable score) and the input size `n` is much larger than `k`. Use the bucket-sort template whenever you rank by frequency and want strict O(n) time instead of a heap's O(n log k). The alternative — sorting everything — always works but costs more time than either template needs.

## 3. Core concept

**Template A — size-k heap.**
1. Create a `PriorityQueue` ordered so its head is the "worst" candidate currently kept (a min-heap when you want the `k` largest, a max-heap when you want the `k` smallest).
2. Scan every element. Push it into the heap.
3. If the heap's size exceeds `k`, poll (remove) the head — this discards whichever element is currently the weakest of the group.
4. When the scan finishes, the heap holds exactly the `k` elements you wanted.

**Template B — bucket sort by frequency.**
1. Count occurrences of every distinct value with a `HashMap<Value, Integer>`.
2. Create an array of buckets, indexed `0` to `n` (the maximum possible count). `buckets[i]` is a list of every value that occurs exactly `i` times.
3. Walk the bucket array from the highest index down, collecting values until you have `k` of them.

Why they work: Template A never lets its heap grow past `k`, so every heap operation costs O(log k), not O(log n) — that is the entire time saving. Template B skips comparison-based sorting altogether: since a count can never exceed `n`, indexing directly by count buckets values in O(n) with no comparisons at all.

## 4. Diagram

<svg viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bucket sort by frequency: values placed into buckets indexed by how many times they occur">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">nums = [1,1,1,2,2,3], k = 2</text>
    <text x="10" y="45">counts: 1-&gt;3, 2-&gt;2, 3-&gt;1</text>
    <text x="10" y="70">bucket[1] = [3]</text>
    <text x="10" y="90">bucket[2] = [2]</text>
    <text x="10" y="110">bucket[3] = [1]</text>
    <text x="10" y="135">read buckets high-&gt;low: bucket[3]=[1], bucket[2]=[2] ... stop, have k=2</text>
    <rect x="10" y="150" width="130" height="24" fill="#3fb950"/><text x="75" y="167" fill="#0d1117" text-anchor="middle" font-size="10">top-2 = [1, 2]</text>
  </g>
</svg>

Reading buckets from the highest count downward yields the most frequent values first, with no comparisons.

## 5. Runnable example

```java
// TopKTemplate.java
import java.util.*;

public class TopKTemplate {

    // Template A: size-k min-heap for the k largest values.
    static int[] kLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int num : nums) {
            heap.offer(num);
            if (heap.size() > k) heap.poll();
        }
        int[] out = new int[heap.size()];
        for (int i = out.length - 1; i >= 0; i--) out[i] = heap.poll();
        return out;
    }

    // Template B: bucket sort by frequency for the k most frequent values.
    static int[] kMostFrequent(int[] nums, int k) {
        Map<Integer, Integer> counts = new HashMap<>();
        for (int num : nums) counts.merge(num, 1, Integer::sum);

        List<Integer>[] buckets = new List[nums.length + 1];
        for (Map.Entry<Integer, Integer> e : counts.entrySet()) {
            int freq = e.getValue();
            if (buckets[freq] == null) buckets[freq] = new ArrayList<>();
            buckets[freq].add(e.getKey());
        }

        int[] result = new int[k];
        int idx = 0;
        for (int freq = buckets.length - 1; freq >= 0 && idx < k; freq--) {
            if (buckets[freq] == null) continue;
            for (int val : buckets[freq]) {
                if (idx == k) break;
                result[idx++] = val;
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(kLargest(new int[]{3, 7, 1, 9, 4}, 3)));
        // [4, 7, 9]

        System.out.println(Arrays.toString(kMostFrequent(new int[]{1, 1, 1, 2, 2, 3}, 2)));
        // [1, 2]
    }
}
```

**How to run:** `java TopKTemplate.java`

## 6. Walkthrough

1. `kLargest([3,7,1,9,4], 3)` scans each number, keeping the heap size capped at 3. It ends with `{4,7,9}`, then drains the heap smallest-first into `[4,7,9]`.
2. `kMostFrequent([1,1,1,2,2,3], 2)` first counts: `1` occurs 3 times, `2` occurs 2 times, `3` occurs 1 time.
3. It places `3` into `bucket[1]`, `2` into `bucket[2]`, and `1` into `bucket[3]`.
4. Reading buckets from index `6` down to `0`, it finds `bucket[3] = [1]` first, then `bucket[2] = [2]`, filling the result `[1, 2]` and stopping once it has `k = 2` values.
5. Both templates avoid a full sort: Template A bounds heap size at `k`; Template B never compares values, it only indexes by count.

## 7. Gotchas & takeaways

> Gotcha: the bucket array must be sized `nums.length + 1`, since a value could in theory appear every single time (frequency up to `n`). Sizing it smaller causes an `ArrayIndexOutOfBoundsException` on that edge case.

- Template A (size-k heap): use when ranking by value, distance, or any comparable score. Cost: O(n log k).
- Template B (frequency buckets): use when ranking by count. Cost: O(n), strictly faster than any heap-based approach.
- Both templates return the top-k set — if the problem also wants a specific ORDER (like sorted ascending), add a final sort of just the `k` results, which costs only O(k log k).
