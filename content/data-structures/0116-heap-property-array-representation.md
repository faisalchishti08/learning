---
card: data-structures
gi: 116
slug: heap-property-array-representation
title: Heap property & array representation
---

## 1. What it is

The **array representation** of a heap stores a complete binary tree's nodes in a plain array, level by level, left to right — with no pointers at all. A node's parent and children are found purely by arithmetic on its array index, not by following a `next` or `child` reference.

## 2. Why & when

Pointer-based trees spend extra memory on `left`/`right`/`parent` references per node, and pay a cache-miss cost jumping between scattered heap-allocated objects. Because a binary heap is always a *complete* tree — no gaps — its shape is fully predictable from its size alone, so the array layout wastes nothing and keeps every node contiguous in memory, which is faster in practice as well as simpler to implement.

## 3. Core concept

**How the operation works.** For a node stored at array index `i` (0-based):

- its left child lives at index `2i + 1`
- its right child lives at index `2i + 2`
- its parent lives at index `(i - 1) / 2` (integer division)

These formulas work *only* because the tree is complete — every index from `0` to `size - 1` is occupied, with no gaps, so "the next node in level order" always lands at a predictable array slot.

**The invariant it must preserve.** Completeness itself is an invariant: every insert must add its new value at the *next* free index (`array[size]`, then `size++`), never at an arbitrary empty slot, or the parent/child index formulas above would silently point at the wrong nodes.

**Why this is fast.** Computing a parent or child index is O(1) arithmetic — no traversal, no dereferencing a chain of pointers. Combined with the array's contiguous memory layout, this makes heap operations both asymptotically efficient (O(log n), bounded by the tree's height) and fast in absolute terms (few cache misses).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A heap tree with five nodes overlaid with its array indices 0 through 4, showing index 1's children at array positions 3 and 4">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <text x="330" y="20" fill="#8b949e" font-size="8">idx 0</text>
    <circle cx="220" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="250" y="80" fill="#8b949e" font-size="8">idx 1</text>
    <circle cx="380" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <text x="410" y="80" fill="#8b949e" font-size="8">idx 2</text>
    <circle cx="180" cy="150" r="16" fill="#161b22" stroke="#8b949e"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">9</text>
    <text x="150" y="140" fill="#8b949e" font-size="8">idx 3</text>
    <circle cx="260" cy="150" r="16" fill="#161b22" stroke="#8b949e"/><text x="260" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">7</text>
    <text x="290" y="140" fill="#8b949e" font-size="8">idx 4</text>
    <line x1="286" y1="42" x2="234" y2="78" stroke="#8b949e"/>
    <line x1="314" y1="42" x2="366" y2="78" stroke="#8b949e"/>
    <line x1="208" y1="102" x2="192" y2="138" stroke="#8b949e"/>
    <line x1="232" y1="102" x2="248" y2="138" stroke="#8b949e"/>
    <rect x="60" y="180" width="480" height="26" fill="#0d1117" stroke="#79c0ff"/>
    <text x="300" y="197" fill="#e6edf3" text-anchor="middle" font-size="9">array: [3, 5, 8, 9, 7]  --  idx 1's children (2*1+1=3, 2*1+2=4) are 9 and 7</text>
  </g>
</svg>

Node `5` sits at array index `1`; its children `9` and `7` sit at exactly indices `2*1+1=3` and `2*1+2=4` — pure arithmetic, no pointers needed.

## 5. Runnable example

```java
// HeapArrayRepresentation.java
import java.util.Arrays;

public class HeapArrayRepresentation {

    // Basic: the three index formulas that replace pointer chasing.
    static int parentIndex(int i) { return (i - 1) / 2; }
    static int leftChildIndex(int i) { return 2 * i + 1; }
    static int rightChildIndex(int i) { return 2 * i + 2; }

    static void basicLevel() {
        int[] heap = {3, 5, 8, 9, 7}; // a valid min-heap in array form
        System.out.println("basic: heap array -> " + Arrays.toString(heap));
        System.out.println("basic: parent of index 3 (value 9) -> index " + parentIndex(3) + " (value " + heap[parentIndex(3)] + ")");
        System.out.println("basic: children of index 1 (value 5) -> indices " + leftChildIndex(1) + "," + rightChildIndex(1)
            + " (values " + heap[leftChildIndex(1)] + "," + heap[rightChildIndex(1)] + ")");
    }

    // Intermediate: verify the heap property holds by checking EVERY parent-child pair using only index math.
    static boolean isValidMinHeap(int[] heap, int size) {
        for (int i = 0; i < size; i++) {
            int left = leftChildIndex(i), right = rightChildIndex(i);
            if (left < size && heap[i] > heap[left]) return false;
            if (right < size && heap[i] > heap[right]) return false;
        }
        return true;
    }

    static void intermediateLevel() {
        int[] validHeap = {3, 5, 8, 9, 7};
        int[] invalidHeap = {3, 5, 8, 1, 7}; // index 3 (value 1) is smaller than its parent at index 1 (value 5) -- violates the property

        System.out.println("intermediate: {3,5,8,9,7} valid min-heap? -> " + isValidMinHeap(validHeap, validHeap.length));
        System.out.println("intermediate: {3,5,8,1,7} valid min-heap? -> " + isValidMinHeap(invalidHeap, invalidHeap.length));
    }

    // Advanced: reconstruct the tree shape (level by level) purely from the array, to make completeness concrete.
    static void printLevels(int[] heap, int size) {
        int level = 0, index = 0;
        while (index < size) {
            int levelSize = (int) Math.pow(2, level);
            StringBuilder row = new StringBuilder("level " + level + ": ");
            for (int i = 0; i < levelSize && index < size; i++, index++) row.append(heap[index]).append(" ");
            System.out.println("advanced: " + row.toString().trim());
            level++;
        }
    }

    static void advancedLevel() {
        int[] heap = {3, 5, 8, 9, 7, 6, 10};
        System.out.println("advanced: array -> " + Arrays.toString(heap));
        printLevels(heap, heap.length);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HeapArrayRepresentation.java`, then run `java HeapArrayRepresentation.java`.

## 6. Walkthrough

1. `basicLevel()` applies the three formulas directly to a fixed array. `parentIndex(3)` computes `(3-1)/2 = 1`, correctly pointing at value `5` — the actual parent of `9` in the tree this array represents. `leftChildIndex(1)` and `rightChildIndex(1)` compute `3` and `4`, correctly locating `9` and `7` as `5`'s children.
2. `intermediateLevel()` checks the heap property across the whole array using only index arithmetic — no tree object exists at all. `{3,5,8,9,7}` passes every parent-child comparison. `{3,5,8,1,7}` fails at index `1` (value `5`) versus its left child at index `3` (value `1`), since `5 > 1` violates the min-heap rule.
3. `advancedLevel()` walks the array level by level, using the fact that level `L` holds exactly `2^L` array positions (except possibly the last, partially-filled level), and reconstructs `level 0: 3`, `level 1: 5 8`, `level 2: 9 7 6 10` — the exact tree shape, recovered purely from array positions.

## 7. Gotchas & takeaways

> Gotcha: the parent/child index formulas only work because a heap is a *complete* tree with no gaps — applying them to an array with holes (e.g. a removed middle element left empty instead of being filled in) silently computes the wrong parent or child, since the arithmetic assumes contiguous, gap-free indices.

- Left child of index `i` is `2i + 1`; right child is `2i + 2`; parent is `(i - 1) / 2` — all O(1) arithmetic, no pointers.
- This layout only works because a heap is always a complete tree — every insert must go at the next free slot, and every removal must fill the gap immediately.
- Array representation avoids per-node pointer overhead and keeps the structure cache-friendly (contiguous memory).
- Related concepts: [Binary heap (min-heap & max-heap)](0115-binary-heap-min-heap-max-heap.md), [Insert & sift-up](0118-insert-sift-up.md), [Extract-min/max & sift-down](0119-extract-min-max-sift-down.md).
