---
card: leetcode-patterns
gi: 280
slug: top-k-frequent-elements
title: Top K Frequent Elements
---

## 1. What it is

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order. Example: `nums = [1,1,1,2,2,3]`, `k = 2` → `[1,2]`.

## 2. Why & when

This is the canonical top-k-by-frequency problem. It belongs to the Top-K Elements pattern, specifically the "k most frequent" signal, and can be solved with either the size-k heap template or the bucket-sort template. Use this shape whenever a problem ranks items by how often they occur, not by their raw value.

## 3. Core concept

**Key idea:** count how often each value occurs, then keep only the `k` values with the highest counts, using a bucket array indexed by frequency so no comparison sort is needed.

**Steps:**
1. Build a `HashMap<Integer, Integer>` counting occurrences of each value in `nums`.
2. Create `buckets`, an array of lists sized `nums.length + 1` (a value can occur at most `nums.length` times). `buckets[freq]` holds every value with that exact frequency.
3. Walk `buckets` from the highest index down to `0`, collecting values into the result until `k` values are collected.

**Why it is correct:** every distinct value's frequency is an integer between `1` and `nums.length`, so bucket indices never overflow. Reading from the highest bucket index first guarantees the most frequent values come out first, and since bucket placement and lookup are both direct array indexing, the whole process runs in O(n) with no comparisons.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frequency buckets for nums 1,1,1,2,2,3 showing value 1 in the frequency-3 bucket and value 2 in the frequency-2 bucket">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1, 1, 1, 2, 2, 3], k = 2</text>
    <text x="10" y="45">counts: 1 -&gt; 3, 2 -&gt; 2, 3 -&gt; 1</text>
    <text x="10" y="70">bucket[3] = [1]</text>
    <text x="10" y="90">bucket[2] = [2]</text>
    <text x="10" y="110">bucket[1] = [3]</text>
    <rect x="10" y="125" width="110" height="24" fill="#3fb950"/><text x="65" y="142" fill="#0d1117" text-anchor="middle" font-size="10">result = [1, 2]</text>
  </g>
</svg>

Reading from bucket 3 down to bucket 1 yields values in decreasing frequency order.

## 5. Runnable example

```java
// TopKFrequentElements.java
import java.util.*;

public class TopKFrequentElements {

    // Level 1 -- Brute force: sort all distinct (value, count) pairs by
    // count descending, then take the first k. Correct, but O(m log m)
    // for m distinct values, more work than necessary.

    // KEY INSIGHT: frequency is bounded by nums.length, so you can index
    // buckets directly by count instead of comparing counts with a sort.

    // Level 2 -- Optimal: bucket sort by frequency, O(n).
    static int[] topKFrequent(int[] nums, int k) {
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

    // Level 3 -- Hardened: works when k equals the number of distinct
    // values (every distinct value gets returned) and when all values
    // share the same frequency (order within a bucket is unspecified,
    // which the problem explicitly allows).

    public static void main(String[] args) {
        System.out.println(Arrays.toString(topKFrequent(new int[]{1, 1, 1, 2, 2, 3}, 2)));
        // [1, 2]
        System.out.println(Arrays.toString(topKFrequent(new int[]{1}, 1)));
        // [1]
    }
}
```

**How to run:** `java TopKFrequentElements.java`

## 6. Walkthrough

Trace `topKFrequent([1,1,1,2,2,3], 2)`:

| step | state |
|---|---|
| count | `{1:3, 2:2, 3:1}` |
| bucket[3] | `[1]` |
| bucket[2] | `[2]` |
| bucket[1] | `[3]` |
| scan freq=6..4 | empty, skip |
| scan freq=3 | take `1`, result = `[1]` |
| scan freq=2 | take `2`, result = `[1, 2]`, idx == k, stop |

Final result: `[1, 2]`. Time complexity is O(n): one pass to count, one pass to bucket, and at most `n` bucket slots visited. Space is O(n), for the count map and buckets.

## 7. Gotchas & takeaways

> Gotcha: sizing the bucket array as `nums.length` instead of `nums.length + 1` causes an out-of-bounds error, since a value that occurs `nums.length` times needs index `nums.length` to exist.

- Bucket sort by frequency beats any comparison-based sort here, since frequency has a known, small range (`1` to `n`).
- A size-k min-heap keyed by frequency is an equally valid O(n log k) alternative when you prefer not to allocate a full bucket array.
- Related problems: Sort Characters By Frequency (the same bucket-by-frequency idea, applied to characters), Top K Frequent Words (frequency ranking with a tie-break rule).
