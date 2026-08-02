---
card: data-structures
gi: 125
slug: running-median-with-two-heaps
title: Running median with two heaps
---

## 1. What it is

The **running median** problem tracks the median of a stream of numbers, recomputing it after every new value arrives. The standard solution splits the data into two heaps: a **max-heap** holding the smaller half of the values seen so far, and a **min-heap** holding the larger half — the median is then found from just the two roots, in O(1), without ever sorting anything.

## 2. Why & when

Recomputing the median from scratch after every insert (by sorting) costs `O(n log n)` per value, or `O(n^2 log n)` over a whole stream — far too slow. The two-heap technique keeps each new value's insertion at `O(log n)` and every median query at `O(1)`, which is essential for a true streaming setting where values arrive continuously and you cannot afford to re-sort.

## 3. Core concept

**How the operation works.** Maintain two heaps:

- **`lowerHalf`** (a max-heap): holds the smaller half of all values seen so far. Its root is the *largest* of the small half.
- **`upperHalf`** (a min-heap): holds the larger half. Its root is the *smallest* of the large half.

For each new value:

1. Add it to `lowerHalf` (tentatively).
2. Move `lowerHalf`'s root over to `upperHalf`, to guarantee every value in `lowerHalf` is `<= ` every value in `upperHalf` (this handles the case where the new value actually belonged in the upper half).
3. **Rebalance sizes:** if `upperHalf` now has more elements than `lowerHalf`, move its root back to `lowerHalf`. This keeps the two heaps within one element of each other in size at all times.

**The invariant it must preserve.** At every point: every value in `lowerHalf` is `<=` every value in `upperHalf`, and the two heaps' sizes differ by at most 1. Both conditions together guarantee the median sits at one (or both) of the two roots.

**Reading the median.** If the heaps are the same size, the median is the average of both roots (an even total count). If `lowerHalf` has one more element (by convention), its root alone is the median (an odd total count).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two heaps side by side: a max heap holding the smaller half of values with root 5, and a min heap holding the larger half with root 8, together giving the median">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">lowerHalf (max-heap): smaller half</text>
    <circle cx="150" cy="45" r="18" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="150" y="49" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <circle cx="110" cy="100" r="14" fill="#161b22" stroke="#8b949e"/><text x="110" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">2</text>
    <circle cx="190" cy="100" r="14" fill="#161b22" stroke="#8b949e"/><text x="190" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">3</text>
    <line x1="138" y1="58" x2="118" y2="88" stroke="#8b949e"/><line x1="162" y1="58" x2="182" y2="88" stroke="#8b949e"/>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">upperHalf (min-heap): larger half</text>
    <circle cx="480" cy="45" r="18" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="480" y="49" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <circle cx="440" cy="100" r="14" fill="#161b22" stroke="#8b949e"/><text x="440" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">9</text>
    <circle cx="520" cy="100" r="14" fill="#161b22" stroke="#8b949e"/><text x="520" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">12</text>
    <line x1="468" y1="58" x2="448" y2="88" stroke="#8b949e"/><line x1="492" y1="58" x2="512" y2="88" stroke="#8b949e"/>

    <text x="315" y="50" fill="#e6edf3" font-size="16">|</text>
    <text x="315" y="150" fill="#79c0ff" text-anchor="middle" font-size="10">both heaps size 3 -&gt; median = (5 + 8) / 2 = 6.5</text>
  </g>
</svg>

`lowerHalf`'s root (`5`) is the largest of the small values; `upperHalf`'s root (`8`) is the smallest of the large values. With both heaps equal in size, the median is their average.

## 5. Runnable example

```java
// RunningMedian.java
import java.util.PriorityQueue;
import java.util.Comparator;

public class RunningMedian {

    PriorityQueue<Integer> lowerHalf = new PriorityQueue<>(Comparator.reverseOrder()); // max-heap: smaller half
    PriorityQueue<Integer> upperHalf = new PriorityQueue<>();                          // min-heap: larger half

    // Basic: add one value, maintaining both invariants (ordering between heaps, and size balance).
    void addNumber(int value) {
        lowerHalf.offer(value);                 // step 1: tentatively add to the small-half heap
        upperHalf.offer(lowerHalf.poll());       // step 2: move its max over, guaranteeing lowerHalf <= upperHalf everywhere

        if (upperHalf.size() > lowerHalf.size()) { // step 3: rebalance if upperHalf grew too large
            lowerHalf.offer(upperHalf.poll());
        }
    }

    double getMedian() {
        if (lowerHalf.size() > upperHalf.size()) return lowerHalf.peek(); // odd total: lowerHalf holds the extra element
        return (lowerHalf.peek() + upperHalf.peek()) / 2.0;               // even total: average both roots
    }

    static void basicLevel() {
        RunningMedian rm = new RunningMedian();
        rm.addNumber(5);
        System.out.println("basic: after adding 5, median -> " + rm.getMedian());
        rm.addNumber(3);
        System.out.println("basic: after adding 3, median -> " + rm.getMedian());
        rm.addNumber(8);
        System.out.println("basic: after adding 8, median -> " + rm.getMedian());
    }

    // Intermediate: a longer stream, tracing the median after each insertion.
    static void intermediateLevel() {
        RunningMedian rm = new RunningMedian();
        int[] stream = {5, 2, 9, 12, 3, 8};
        for (int v : stream) {
            rm.addNumber(v);
            System.out.println("intermediate: after adding " + v + ", median -> " + rm.getMedian());
        }
    }

    // Advanced: confirm correctness against a brute-force sort-and-check approach, over a larger randomized stream.
    static double bruteForceMedian(java.util.List<Integer> soFar) {
        java.util.List<Integer> sorted = new java.util.ArrayList<>(soFar);
        java.util.Collections.sort(sorted);
        int n = sorted.size();
        return (n % 2 == 1) ? sorted.get(n / 2) : (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2.0;
    }

    static void advancedLevel() {
        RunningMedian rm = new RunningMedian();
        java.util.List<Integer> seenSoFar = new java.util.ArrayList<>();
        java.util.Random random = new java.util.Random(42);
        boolean allMatch = true;

        for (int i = 0; i < 200; i++) {
            int value = random.nextInt(1000);
            rm.addNumber(value);
            seenSoFar.add(value);
            if (Math.abs(rm.getMedian() - bruteForceMedian(seenSoFar)) > 1e-9) allMatch = false;
        }
        System.out.println("advanced: two-heap median matched brute-force sort on all 200 insertions -> " + allMatch);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `RunningMedian.java`, then run `java RunningMedian.java`.

## 6. Walkthrough

1. `basicLevel()` adds `5`: it goes into `lowerHalf`, immediately moves to `upperHalf` (since `lowerHalf` was empty, its "max" is just `5` itself), then rebalances back into `lowerHalf` since `upperHalf` (size 1) now exceeds `lowerHalf` (size 0). Median: `5`. Adding `3`: it goes into `lowerHalf` (now `{5, 3}`, max `5` moves to `upperHalf`), giving `lowerHalf = {3}`, `upperHalf = {5}` — equal sizes, median `(3+5)/2 = 4.0`. Adding `8`: it enters `lowerHalf` alongside `3` (max is `8`, which moves to `upperHalf`), giving `lowerHalf = {3}`, `upperHalf = {5, 8}`; rebalancing moves `upperHalf`'s min (`5`) back to `lowerHalf`, giving `lowerHalf = {3, 5}`, `upperHalf = {8}` — median is `lowerHalf`'s root, `5`.
2. `intermediateLevel()` traces the median after each of six insertions, showing it update correctly at every step without ever re-sorting the whole stream so far.
3. `advancedLevel()` cross-checks the two-heap result against a brute-force "sort everything and pick the middle" reference implementation across 200 random insertions, confirming the two approaches agree at every single step — a practical correctness proof for the incremental algorithm.

## 7. Gotchas & takeaways

> Gotcha: always insert into `lowerHalf` first and then move its max to `upperHalf` — inserting directly into whichever heap "seems right" for the new value, skipping that shuffle step, breaks the cross-heap invariant (every `lowerHalf` value `<=` every `upperHalf` value) whenever the new value would have belonged in the other heap.

- `lowerHalf` is a max-heap (smaller half); `upperHalf` is a min-heap (larger half); their roots alone determine the median.
- Every insertion costs `O(log n)`; every median query costs `O(1)` — the key advantage over re-sorting per insertion.
- The size-balancing step is what keeps the median query correct — the two heaps must never differ in size by more than 1.
- Related concepts: [PriorityQueue with a Comparator](0122-priorityqueue-with-a-comparator.md), [Top-K elements with a heap](0123-top-k-elements-with-a-heap.md).
