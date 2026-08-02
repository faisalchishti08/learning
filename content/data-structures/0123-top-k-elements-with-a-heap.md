---
card: data-structures
gi: 123
slug: top-k-elements-with-a-heap
title: Top-K elements with a heap
---

## 1. What it is

The **top-K pattern** finds the K largest (or smallest, or most frequent) elements in a collection without fully sorting it. It keeps a heap of bounded size K, evicting the current worst candidate whenever the heap grows past K — so the heap always holds exactly the best K candidates seen so far.

## 2. Why & when

Sorting the entire input to find the top K costs `O(n log n)`. A bounded heap does it in `O(n log k)` — much cheaper when `k` is small relative to `n`, which is the common case ("top 10 trending topics" out of millions of posts). It also works on a data **stream**, where you cannot hold everything in memory at once, since the heap only ever needs to hold `k` elements.

## 3. Core concept

**How the operation works, for "K largest".** Use a **min-heap** of bounded size `k` (this is the counter-intuitive part — a min-heap, not a max-heap):

1. Offer each element into the heap.
2. If the heap's size exceeds `k`, poll (remove) the minimum.
3. After processing every element, the heap holds exactly the `k` largest values, with the *smallest of those k* sitting at the root.

**Why a min-heap, not a max-heap, for "K largest".** The heap's root needs to answer "which of my current top-k candidates is the weakest, so I can evict it if something better shows up?" — that is a *minimum* query among the retained set, even though the overall goal is to find large values. A max-heap would only tell you the single largest value seen, which is not what eviction needs.

**Extending to "Top K Frequent Elements".** Count occurrences with a frequency map first (see [Frequency maps & grouping](0096-frequency-maps-grouping-computeifabsent-merge.md)), then run the exact same bounded min-heap pattern over the map's `(value, count)` entries, ordered by `count`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stream of numbers processed one at a time into a bounded min heap of size 3, evicting the smallest whenever the heap exceeds size 3, ending with the 3 largest values retained">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="20" fill="#8b949e">stream: 3, 1, 5, 12, 2, 11  (k=3)</text>
    <rect x="20" y="35" width="60" height="26" fill="#161b22" stroke="#8b949e"/><text x="50" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 3</text>
    <rect x="90" y="35" width="60" height="26" fill="#161b22" stroke="#8b949e"/><text x="120" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 1</text>
    <rect x="160" y="35" width="60" height="26" fill="#161b22" stroke="#8b949e"/><text x="190" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 5</text>
    <text x="120" y="80" fill="#79c0ff" font-size="9">heap: {1,3,5} -- size 3, at capacity</text>
    <rect x="260" y="35" width="70" height="26" fill="#0d1117" stroke="#f0883e"/><text x="295" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 12</text>
    <text x="295" y="80" fill="#f0883e" font-size="9">size 4 &gt; k -&gt; poll evicts 1 (the smallest)</text>
    <text x="295" y="100" fill="#79c0ff" font-size="9">heap: {3,5,12}</text>
    <rect x="360" y="35" width="60" height="26" fill="#161b22" stroke="#8b949e"/><text x="390" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 2</text>
    <text x="390" y="80" fill="#f0883e" font-size="9">size 4 &gt; k -&gt; poll evicts 2 immediately</text>
    <rect x="440" y="35" width="70" height="26" fill="#0d1117" stroke="#f0883e"/><text x="475" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">offer 11</text>
    <text x="475" y="80" fill="#f0883e" font-size="9">size 4 &gt; k -&gt; poll evicts 3</text>
    <text x="300" y="140" fill="#79c0ff" text-anchor="middle" font-size="10">final heap: {5, 11, 12} -- exactly the 3 largest values seen</text>
  </g>
</svg>

Each time the min-heap's size exceeds `k`, the current smallest is evicted — after the whole stream, only the K largest values remain, with the weakest of them at the root.

## 5. Runnable example

```java
// TopKElements.java
import java.util.PriorityQueue;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Collections;

public class TopKElements {

    // Basic: K largest values from an int stream, using a bounded min-heap.
    static List<Integer> kLargest(int[] nums, int k) {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(); // natural order -- smallest at the root
        for (int n : nums) {
            minHeap.offer(n);
            if (minHeap.size() > k) minHeap.poll(); // evict the current weakest of the retained top-k candidates
        }
        return new ArrayList<>(minHeap);
    }

    static void basicLevel() {
        int[] nums = {3, 1, 5, 12, 2, 11};
        System.out.println("basic: 3 largest of " + java.util.Arrays.toString(nums) + " -> " + kLargest(nums, 3));
    }

    // Intermediate: the same pattern with a Comparator, extended to K SMALLEST -- flip to a bounded MAX-heap instead.
    static List<Integer> kSmallest(int[] nums, int k) {
        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(java.util.Comparator.reverseOrder());
        for (int n : nums) {
            maxHeap.offer(n);
            if (maxHeap.size() > k) maxHeap.poll(); // evict the current LARGEST of the retained bottom-k candidates
        }
        return new ArrayList<>(maxHeap);
    }

    static void intermediateLevel() {
        int[] nums = {3, 1, 5, 12, 2, 11};
        System.out.println("intermediate: 3 smallest of " + java.util.Arrays.toString(nums) + " -> " + kSmallest(nums, 3));
    }

    // Advanced: a realistic task -- Top-K Frequent Elements, combining a frequency map with the bounded-heap pattern.
    static List<Integer> topKFrequent(int[] nums, int k) {
        Map<Integer, Integer> counts = new HashMap<>();
        for (int n : nums) counts.merge(n, 1, Integer::sum);

        PriorityQueue<Map.Entry<Integer, Integer>> minHeap =
            new PriorityQueue<>(java.util.Comparator.comparingInt(Map.Entry::getValue));

        for (Map.Entry<Integer, Integer> entry : counts.entrySet()) {
            minHeap.offer(entry);
            if (minHeap.size() > k) minHeap.poll(); // evict the LEAST frequent of the retained top-k candidates
        }

        List<Integer> result = new ArrayList<>();
        for (Map.Entry<Integer, Integer> entry : minHeap) result.add(entry.getKey());
        Collections.sort(result, Collections.reverseOrder()); // cosmetic: present most frequent first
        return result;
    }

    static void advancedLevel() {
        int[] nums = {1, 1, 1, 2, 2, 3};
        System.out.println("advanced: top-2 most frequent in " + java.util.Arrays.toString(nums) + " -> " + topKFrequent(nums, 2));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TopKElements.java`, then run `java TopKElements.java`.

## 6. Walkthrough

1. `basicLevel()` processes `3, 1, 5, 12, 2, 11` with `k = 3`. After offering `3, 1, 5`, the heap holds all three (`{1, 3, 5}`), exactly at capacity. Offering `12` pushes the size to `4`, so `poll()` evicts the current minimum, `1`. Offering `2` again exceeds capacity, evicting `2` itself (the new minimum after insertion). Offering `11` evicts `3`. The final heap holds `{5, 11, 12}` — the three largest values in the stream, though not necessarily in sorted order within the returned list.
2. `intermediateLevel()` flips the direction with `Comparator.reverseOrder()`, turning the bounded heap into a max-heap that evicts the current *largest* of its retained candidates — correct for "k smallest," since you now want to keep the small values and throw away whichever retained value is too big.
3. `advancedLevel()` first counts occurrences into a `HashMap` (`1` appears 3 times, `2` appears twice, `3` once), then runs the identical bounded-heap pattern over the map's entries, comparing by count instead of by value. The min-heap evicts the least-frequent retained entry whenever it exceeds size `2`, ending with the two most frequent values, `1` and `2`.

## 7. Gotchas & takeaways

> Gotcha: using a max-heap for "k largest" is a common but backwards instinct — a max-heap only makes it cheap to find the single largest value, not to identify (and evict) the *weakest* of your currently retained top-k set, which is exactly what a bounded min-heap's root gives you for free.

- For "k largest," use a bounded **min-heap** of size `k`; for "k smallest," use a bounded **max-heap** of size `k` — the heap type is the opposite of what the goal might suggest.
- This pattern costs `O(n log k)`, cheaper than fully sorting (`O(n log n)`) whenever `k` is much smaller than `n`.
- It also works on a live stream, since the heap never needs to hold more than `k` elements at once.
- Related concepts: [PriorityQueue with a Comparator](0122-priorityqueue-with-a-comparator.md), [Frequency maps & grouping (computeIfAbsent / merge)](0096-frequency-maps-grouping-computeifabsent-merge.md).
