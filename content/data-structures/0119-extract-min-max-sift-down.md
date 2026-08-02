---
card: data-structures
gi: 119
slug: extract-min-max-sift-down
title: extract-min/max & sift-down
---

## 1. What it is

**Sift-down** (also called "bubble down" or "heapify down") is the repair step that runs after removing the root of a heap. It repeatedly compares a value against its children and swaps downward with the smaller (for a min-heap) child, until the heap property holds again or the value reaches a leaf.

## 2. Why & when

The root always holds the best element, so removing it (extract-min or extract-max) is how you consume elements in priority order. But you cannot simply delete the root and leave a hole — the array must stay a complete tree. The standard fix moves the *last* element into the root's old spot, then sifts it down. This comes up every time you drain a heap in priority order, and it is the core of heap sort.

## 3. Core concept

**How the operation works.** To extract the root:

1. Save the root's value (this is the return value).
2. Move the last element in the array to index `0`, and shrink `size` by one.
3. Sift that relocated value down: at each step, find the smaller of its two children (if they exist); if the current node is already smaller than or equal to both, stop. Otherwise, swap with the smaller child and continue from that child's old index.

**The invariant it must preserve.** After sift-down finishes, every parent-child pair along the path from the root down to wherever the relocated value settles must satisfy the heap property. Like sift-up, it must not disturb any node outside that single downward path.

**Why you must compare against BOTH children, not just one.** Swapping with the *larger* child (in a min-heap) instead of the smaller one can leave the heap property violated: if the current node ends up smaller than one child but still larger than the other, the property still fails. Always identify the smaller of the two children first, then swap only if the current node is worse than that one.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Extracting the root 3, replacing it with the last element 9, then sifting 9 down past the smaller of its two children twice until it settles as a leaf">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">root removed; last element (9) moved to root, then sifts down</text>
    <circle cx="320" cy="40" r="16" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="320" y="44" fill="#e6edf3" text-anchor="middle" font-size="8">9</text>
    <circle cx="260" cy="95" r="16" fill="#161b22" stroke="#f0883e"/><text x="260" y="99" fill="#e6edf3" text-anchor="middle" font-size="8">4</text>
    <circle cx="380" cy="95" r="16" fill="#161b22" stroke="#8b949e"/><text x="380" y="99" fill="#e6edf3" text-anchor="middle" font-size="8">7</text>
    <circle cx="230" cy="150" r="16" fill="#161b22" stroke="#f0883e"/><text x="230" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">5</text>
    <circle cx="290" cy="150" r="16" fill="#161b22" stroke="#8b949e"/><text x="290" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">6</text>
    <line x1="308" y1="52" x2="272" y2="83" stroke="#8b949e"/><line x1="332" y1="52" x2="368" y2="83" stroke="#8b949e"/>
    <line x1="248" y1="107" x2="236" y2="138" stroke="#8b949e"/><line x1="272" y1="107" x2="284" y2="138" stroke="#8b949e"/>
    <text x="320" y="185" fill="#79c0ff" text-anchor="middle" font-size="9">step 1: children of 9 are 4,7 -- smaller is 4 -&gt; swap</text>
    <text x="320" y="205" fill="#79c0ff" text-anchor="middle" font-size="9">step 2: children of 9 (now at old 4's spot) are 5,6 -- smaller is 5 -&gt; swap</text>
  </g>
</svg>

`9` replaces the removed root. Its children are `4` and `7`; `4` is smaller, so `9` swaps with `4`. At its new position, `9`'s children are `5` and `6`; `5` is smaller, so `9` swaps again, settling as a leaf.

## 5. Runnable example

```java
// SiftDown.java
import java.util.Arrays;

public class SiftDown {

    static int leftChild(int i) { return 2 * i + 1; }
    static int rightChild(int i) { return 2 * i + 2; }

    // Basic: sift-down in isolation -- given an array valid EXCEPT possibly at the root, fix it.
    static void siftDown(int[] heap, int size, int i) {
        while (true) {
            int left = leftChild(i), right = rightChild(i), smallest = i;
            if (left < size && heap[left] < heap[smallest]) smallest = left;   // check LEFT child
            if (right < size && heap[right] < heap[smallest]) smallest = right; // check RIGHT child too -- both matter
            if (smallest == i) break; // neither child is smaller -- property holds
            int t = heap[i]; heap[i] = heap[smallest]; heap[smallest] = t;
            i = smallest;
        }
    }

    static void basicLevel() {
        int[] heap = {9, 4, 7, 5, 6}; // valid EXCEPT the root
        System.out.println("basic: before siftDown -> " + Arrays.toString(heap));
        siftDown(heap, heap.length, 0);
        System.out.println("basic: after siftDown(0) -> " + Arrays.toString(heap));
    }

    // Intermediate: a full extractMin, built from "save root, move last to root, shrink, siftDown".
    static int extractMin(int[] heap, int size) {
        int min = heap[0];
        heap[0] = heap[size - 1];
        siftDown(heap, size - 1, 0); // note: sift over the SHRUNK size, excluding the old last slot
        return min;
    }

    static void intermediateLevel() {
        int[] heap = {3, 5, 8, 9, 7, 6, 10};
        int size = heap.length;
        StringBuilder order = new StringBuilder();
        while (size > 0) {
            order.append(extractMin(heap, size)).append(" ");
            size--;
        }
        System.out.println("intermediate: repeated extractMin -> " + order.toString().trim() + " (fully sorted ascending)");
    }

    // Advanced: the iterative (non-recursive) form is what production code uses -- confirm it handles a one-sided child too.
    static void advancedLevel() {
        int[] oneChild = {2, 9}; // size 2: index 0 has only ONE child, at index 1; rightChild(0)=2 is out of range
        System.out.println("advanced: before -> " + Arrays.toString(oneChild));
        siftDown(oneChild, oneChild.length, 0);
        System.out.println("advanced: after siftDown on a node with only ONE child -> " + Arrays.toString(oneChild));
        System.out.println("advanced: the right < size check correctly skips the missing right child");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SiftDown.java`, then run `java SiftDown.java`.

## 6. Walkthrough

1. `basicLevel()` starts from `{9, 4, 7, 5, 6}`, where the root `9` violates the property (both children are smaller). `siftDown` finds `left = 4` (index 1), `right = 7` (index 2); `4` is smaller, so `smallest = 1`. It swaps `9` and `4`, giving `{4, 9, 7, 5, 6}`, and continues from index `1`. There, `9`'s children are `5` (index 3) and `6` (index 4); `5` is smaller, so it swaps again: `{4, 5, 7, 9, 6}`. Index `3` (value `9`) is a leaf, so the loop stops.
2. `intermediateLevel()` repeats `extractMin` on a 7-element heap, each time saving the root, moving the last element in, shrinking the effective size by one, then sifting down. The full sequence of returned minimums comes out `3, 5, 6, 7, 8, 9, 10` — completely sorted, since each extraction correctly restores the heap property before the next one runs.
3. `advancedLevel()` sifts down a two-element heap where the root has only a left child (no right child exists, since index `2` would be out of bounds for `size = 2`). The `right < size` guard correctly skips the missing child, and the comparison only considers the left child — confirming the bounds checks handle a partially-filled last level correctly.

## 7. Gotchas & takeaways

> Gotcha: always find the smaller of the two children *before* deciding whether to swap — comparing against only one child (or swapping with the wrong one) can leave the other child still smaller than the current node, silently breaking the heap property one level down.

- Sift-down repairs the heap after the root is replaced by the last element; it swaps downward with the smaller child until the current node is no worse than both children.
- It must check both children's array bounds (`left < size`, `right < size`) since the last level of a complete tree may be only partially filled.
- Repeated extract-min (each followed by sift-down) drains a heap in fully sorted order — this is exactly how heap sort works.
- Related concepts: [Insert & sift-up](0118-insert-sift-up.md), [Build-heap in O(n)](0120-build-heap-in-o-n.md), [Heap sort](0121-heap-sort.md).
