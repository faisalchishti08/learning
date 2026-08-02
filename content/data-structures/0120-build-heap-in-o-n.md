---
card: data-structures
gi: 120
slug: build-heap-in-o-n
title: Build-heap in O(n)
---

## 1. What it is

**Build-heap** turns an arbitrary, unordered array into a valid heap, in place. The naive approach — inserting each element one at a time with sift-up — costs `O(n log n)`. A cleverer approach, sifting down from the last non-leaf node backward to the root, does it in `O(n)` — the standard algorithm behind heap sort's first phase.

## 2. Why & when

Whenever you need to turn an existing array into a heap all at once (rather than building it up element by element), the `O(n)` method is strictly better than repeated inserts, and it is what every production heap constructor (including `java.util.PriorityQueue`'s array-based constructor) actually uses. Understanding *why* it is `O(n)` and not `O(n log n)` is a classic complexity-analysis exercise.

## 3. Core concept

**How the operation works.** Treat the input array as an already-complete tree shape (it trivially is one, since any array can be read as a complete binary tree by index). Then, starting from the last non-leaf node (index `n/2 - 1`, since every index beyond that is a leaf) and walking backward to index `0`, call sift-down on each node.

**Why start from the last non-leaf, not index 0.** A leaf node is trivially a valid one-node heap by itself — nothing to fix. Working backward guarantees that by the time you sift-down a given node, *both of its subtrees are already valid heaps* — sift-down assumes exactly that precondition (it only fixes a violation at the very top of an otherwise-valid heap).

**Why this is O(n), not O(n log n).** Sift-down's cost is proportional to a node's *height* (distance to its farthest leaf), not to the tree's overall height. Most nodes are near the bottom of the tree and have small height — a heap of `n` nodes has roughly `n/2` leaves (height 0, free), `n/4` nodes at height 1, `n/8` at height 2, and so on. Summing `(number of nodes at height h) * h` over all heights gives a geometric-like series that converges to `O(n)`, not `O(n log n)` — most of the work is done at the cheap, shallow levels.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building a heap bottom up: the last non-leaf node is sifted down first, then the algorithm proceeds backward toward the root, so every node's subtrees are already valid heaps when its turn comes">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="16" fill="#161b22" stroke="#8b949e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="8">idx 0</text>
    <circle cx="220" cy="85" r="16" fill="#161b22" stroke="#8b949e"/><text x="220" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">idx 1</text>
    <circle cx="380" cy="85" r="16" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="380" y="89" fill="#e6edf3" text-anchor="middle" font-size="7">idx 2 (start)</text>
    <circle cx="180" cy="140" r="14" fill="#161b22" stroke="#8b949e"/><text x="180" y="144" fill="#e6edf3" text-anchor="middle" font-size="7">idx 3</text>
    <circle cx="260" cy="140" r="14" fill="#161b22" stroke="#8b949e"/><text x="260" y="144" fill="#e6edf3" text-anchor="middle" font-size="7">idx 4</text>
    <circle cx="340" cy="140" r="14" fill="#161b22" stroke="#8b949e"/><text x="340" y="144" fill="#e6edf3" text-anchor="middle" font-size="7">idx 5</text>
    <circle cx="420" cy="140" r="14" fill="#161b22" stroke="#8b949e"/><text x="420" y="144" fill="#e6edf3" text-anchor="middle" font-size="7">idx 6</text>
    <line x1="286" y1="42" x2="234" y2="73" stroke="#8b949e"/><line x1="314" y1="42" x2="366" y2="73" stroke="#8b949e"/>
    <line x1="206" y1="97" x2="188" y2="128" stroke="#8b949e"/><line x1="230" y1="97" x2="252" y2="128" stroke="#8b949e"/>
    <line x1="366" y1="97" x2="348" y2="128" stroke="#8b949e"/><line x1="390" y1="97" x2="410" y2="128" stroke="#8b949e"/>
    <text x="300" y="185" fill="#79c0ff" text-anchor="middle" font-size="9">n=7 -&gt; last non-leaf = n/2-1 = 2. Process order: idx 2, idx 1, idx 0.</text>
    <text x="300" y="205" fill="#8b949e" text-anchor="middle" font-size="9">Indices 3-6 are leaves -- already valid one-node heaps, no work needed.</text>
  </g>
</svg>

For 7 nodes, indices `3`–`6` are leaves (no work). Processing starts at index `2` (the last non-leaf) and moves backward to index `0`, so every sift-down always has two already-valid subtrees beneath it.

## 5. Runnable example

```java
// BuildHeap.java
import java.util.Arrays;

public class BuildHeap {

    static int leftChild(int i) { return 2 * i + 1; }
    static int rightChild(int i) { return 2 * i + 2; }

    static void siftDown(int[] heap, int size, int i) {
        while (true) {
            int left = leftChild(i), right = rightChild(i), smallest = i;
            if (left < size && heap[left] < heap[smallest]) smallest = left;
            if (right < size && heap[right] < heap[smallest]) smallest = right;
            if (smallest == i) break;
            int t = heap[i]; heap[i] = heap[smallest]; heap[smallest] = t;
            i = smallest;
        }
    }

    // Basic: the O(n) build-heap algorithm -- start at the last non-leaf, walk backward to the root.
    static void buildHeap(int[] array) {
        int n = array.length;
        for (int i = n / 2 - 1; i >= 0; i--) siftDown(array, n, i);
    }

    static void basicLevel() {
        int[] array = {9, 4, 7, 1, 3, 8, 2}; // arbitrary, unordered input
        System.out.println("basic: before buildHeap -> " + Arrays.toString(array));
        buildHeap(array);
        System.out.println("basic: after buildHeap -> " + Arrays.toString(array) + " (valid min-heap now)");
    }

    // Intermediate: the naive O(n log n) alternative -- insert one at a time with sift-up -- for comparison.
    static int parent(int i) { return (i - 1) / 2; }

    static void siftUp(int[] heap, int i) {
        while (i > 0 && heap[parent(i)] > heap[i]) {
            int t = heap[i]; heap[i] = heap[parent(i)]; heap[parent(i)] = t;
            i = parent(i);
        }
    }

    static int[] buildHeapNaive(int[] input) {
        int[] heap = new int[input.length];
        for (int i = 0; i < input.length; i++) {
            heap[i] = input[i];
            siftUp(heap, i);
        }
        return heap;
    }

    static void intermediateLevel() {
        int[] input = {9, 4, 7, 1, 3, 8, 2};
        int[] result = buildHeapNaive(input);
        System.out.println("intermediate: naive insert-one-at-a-time result -> " + Arrays.toString(result) + " (also a valid heap, but O(n log n))");
    }

    // Advanced: count total swaps for the O(n) method versus the naive method, on the same larger input.
    static int siftDownCounting(int[] heap, int size, int i) {
        int swaps = 0;
        while (true) {
            int left = leftChild(i), right = rightChild(i), smallest = i;
            if (left < size && heap[left] < heap[smallest]) smallest = left;
            if (right < size && heap[right] < heap[smallest]) smallest = right;
            if (smallest == i) break;
            int t = heap[i]; heap[i] = heap[smallest]; heap[smallest] = t;
            i = smallest;
            swaps++;
        }
        return swaps;
    }

    static void advancedLevel() {
        int n = 1000;
        int[] array = new int[n];
        for (int i = 0; i < n; i++) array[i] = n - i; // strictly decreasing -- reverse-sorted input

        int totalSwaps = 0;
        for (int i = n / 2 - 1; i >= 0; i--) totalSwaps += siftDownCounting(array, n, i);

        System.out.println("advanced: n=" + n + " reverse-sorted input, total swaps for O(n) buildHeap -> " + totalSwaps);
        System.out.println("advanced: far fewer than n*log2(n) ~= " + (int) (n * (Math.log(n) / Math.log(2))) + ", confirming the O(n) bound");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BuildHeap.java`, then run `java BuildHeap.java`.

## 6. Walkthrough

1. `basicLevel()` starts with the unordered array `{9, 4, 7, 1, 3, 8, 2}` (7 elements). `buildHeap` computes `n/2 - 1 = 2` as the starting index, then calls `siftDown` on indices `2, 1, 0` in that order. By the time index `0` (the root, holding `9`) is processed, both its subtrees (rooted at indices `1` and `2`) are already valid heaps, so `siftDown` on the root only needs to push `9` down through an already-correct structure.
2. `intermediateLevel()` builds a heap from the same input using the naive one-at-a-time insert approach. Both methods produce a valid heap (though not necessarily an identical array layout, since heaps do not have a unique valid arrangement) — but the naive method calls `siftUp`, which can traverse all `O(log n)` levels on every single insert.
3. `advancedLevel()` counts total swaps across the whole `O(n)` build for `1000` reverse-sorted elements, and compares that count against the naive method's theoretical `n * log2(n)` bound. The `O(n)` method's total comes out far lower, concretely demonstrating the complexity gap the sum-over-heights argument predicts.

## 7. Gotchas & takeaways

> Gotcha: starting the backward loop at `n/2 - 1` (not `n - 1`) is essential — indices from `n/2` onward are all leaves, and calling `siftDown` on a leaf is harmless but wasted work; more importantly, the *correctness* of the algorithm depends on processing nodes in an order where every node's children have already been fixed, which only holds when walking backward from the last non-leaf.
- The naive way to build a heap (insert one at a time, `siftUp` after each) costs `O(n log n)`; sifting down from the last non-leaf backward to the root costs `O(n)`.
- The `O(n)` bound comes from the fact that most nodes sit near the bottom of the tree, where `siftDown`'s cost (proportional to a node's height, not the tree's height) is small.
- This backward, bottom-up sift-down is the first phase of heap sort.
- Related concepts: [Extract-min/max & sift-down](0119-extract-min-max-sift-down.md), [Heap sort](0121-heap-sort.md).
