---
card: data-structures
gi: 115
slug: binary-heap-min-heap-max-heap
title: Binary heap (min-heap & max-heap)
---

## 1. What it is

A **binary heap** is a **complete binary tree** — every level is fully filled except possibly the last, which fills left to right — that also satisfies the **heap property**: in a **min-heap**, every parent's value is less than or equal to both its children's values; in a **max-heap**, every parent is greater than or equal to both children. Unlike a binary search tree (BST), a heap has no left-vs-right ordering rule — only parent-vs-child.

## 2. Why & when

Use a binary heap whenever you repeatedly need the current smallest (or largest) item from a changing collection — Dijkstra's shortest path, a task scheduler running the most urgent job next, or the "top K" family of problems. A heap gives O(1) access to the best element and O(log n) insert/removal, which beats keeping the collection fully sorted (O(log n) access, but O(n) insert into the right position, or O(n log n) to re-sort).

## 3. Core concept

**The structure's shape.** "Complete" means the tree has no gaps: if you number nodes level by level, left to right, starting at `0`, every index from `0` up to `size - 1` is filled — there are no missing nodes partway through a level. This completeness is what lets a heap live in a plain array instead of needing explicit node pointers, covered in its own topic ([Heap property & array representation](0116-heap-property-array-representation.md)).

**The heap property, precisely.** For a min-heap, every node `n` satisfies `n.value <= n.left.value` and `n.value <= n.right.value` (when those children exist). This is weaker than a BST's invariant — it says nothing about how a node's left child compares to its right child, or how either compares to nodes in a different subtree entirely.

**How the invariant makes "find the best" fast.** Because every parent is never worse than its children, the single best value in the whole heap is always at the root — no scanning needed, giving O(1) access. Restoring the property after a change only requires fixing the one path from the change back to the root (or down to a leaf), which is why insert and remove cost O(log n): the height of a complete tree of `n` nodes is always `O(log n)`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A min heap with root 3, children 5 and 8, and grandchildren 9, 7, showing every parent is less than or equal to its children">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <circle cx="220" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <circle cx="380" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="380" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <circle cx="180" cy="150" r="16" fill="#161b22" stroke="#8b949e"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">9</text>
    <circle cx="260" cy="150" r="16" fill="#161b22" stroke="#8b949e"/><text x="260" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">7</text>
    <line x1="286" y1="42" x2="234" y2="78" stroke="#8b949e"/>
    <line x1="314" y1="42" x2="366" y2="78" stroke="#8b949e"/>
    <line x1="208" y1="102" x2="192" y2="138" stroke="#8b949e"/>
    <line x1="232" y1="102" x2="248" y2="138" stroke="#8b949e"/>
    <text x="300" y="195" fill="#79c0ff" text-anchor="middle" font-size="9">every parent &lt;= its children -- but 9 and 7 are unordered relative to each other</text>
  </g>
</svg>

`3` is the smallest value and sits at the root; `5 <= 9` and `5 <= 7` hold, but `9` and `7` (siblings, not parent/child) have no required order between them.

## 5. Runnable example

```java
// BinaryHeap.java
import java.util.Arrays;

public class BinaryHeap {

    int[] data;
    int size = 0;

    BinaryHeap(int capacity) { data = new int[capacity]; }

    static int parent(int i) { return (i - 1) / 2; }
    static int leftChild(int i) { return 2 * i + 1; }
    static int rightChild(int i) { return 2 * i + 2; }

    void swap(int i, int j) { int t = data[i]; data[i] = data[j]; data[j] = t; }

    // Basic: insert, restoring the heap property by "bubbling up" toward the root.
    void insert(int value) {
        data[size] = value;
        int i = size;
        size++;
        while (i > 0 && data[parent(i)] > data[i]) { // min-heap: a parent worse than its child violates the property
            swap(i, parent(i));
            i = parent(i);
        }
    }

    static void basicLevel() {
        BinaryHeap heap = new BinaryHeap(10);
        for (int v : new int[]{5, 8, 3, 9, 7}) heap.insert(v);
        System.out.println("basic: array after inserting 5,8,3,9,7 -> " + Arrays.toString(Arrays.copyOf(heap.data, heap.size)));
        System.out.println("basic: root (smallest) -> " + heap.data[0]);
    }

    // Intermediate: extractMin, restoring the property by "bubbling down" from the root.
    int extractMin() {
        int min = data[0];
        size--;
        data[0] = data[size]; // move the last element to the root
        int i = 0;
        while (true) {
            int left = leftChild(i), right = rightChild(i), smallest = i;
            if (left < size && data[left] < data[smallest]) smallest = left;
            if (right < size && data[right] < data[smallest]) smallest = right;
            if (smallest == i) break; // property already holds -- stop
            swap(i, smallest);
            i = smallest;
        }
        return min;
    }

    static void intermediateLevel() {
        BinaryHeap heap = new BinaryHeap(10);
        for (int v : new int[]{5, 8, 3, 9, 7}) heap.insert(v);

        StringBuilder order = new StringBuilder();
        while (heap.size > 0) order.append(heap.extractMin()).append(" ");
        System.out.println("intermediate: extractMin repeatedly -> " + order.toString().trim() + " (sorted ascending)");
    }

    // Advanced: a max-heap variant -- flip every comparison, nothing else changes.
    static class MaxHeap {
        int[] data;
        int size = 0;
        MaxHeap(int capacity) { data = new int[capacity]; }

        void insert(int value) {
            data[size] = value;
            int i = size++;
            while (i > 0 && data[BinaryHeap.parent(i)] < data[i]) { // flipped: parent WORSE (smaller) than child
                int t = data[i]; data[i] = data[BinaryHeap.parent(i)]; data[BinaryHeap.parent(i)] = t;
                i = BinaryHeap.parent(i);
            }
        }
    }

    static void advancedLevel() {
        MaxHeap heap = new MaxHeap(10);
        for (int v : new int[]{5, 8, 3, 9, 7}) heap.insert(v);
        System.out.println("advanced: max-heap root (largest) -> " + heap.data[0]);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BinaryHeap.java`, then run `java BinaryHeap.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `5, 8, 3, 9, 7` one at a time. Each `insert` places the new value at the next free array slot, then compares it against its parent, swapping upward while the parent is larger. Inserting `3` (after `5, 8`) starts at index `2`, compares against parent `5` at index `0`, and swaps — `3` becomes the new root, since it is smaller than everything checked so far.
2. `intermediateLevel()` repeatedly calls `extractMin`, which always removes the root (the current smallest), replaces it with the last array element, then "bubbles down": at each step it compares the moved value against both children and swaps with whichever child is smaller, until the property holds again. Repeating this drains the heap in fully sorted order: `3, 5, 7, 8, 9`.
3. `advancedLevel()`'s `MaxHeap` is identical in structure, with every comparison direction flipped (`<` becomes `>`). The root ends up holding `9`, the largest value, proving the same array-based mechanism works for either ordering — only the comparison direction changes.

## 7. Gotchas & takeaways

> Gotcha: a heap only orders parent versus child, never sibling versus sibling, and never left versus right — do not assume a heap gives sorted order by any traversal other than repeated extraction. Printing the raw array is not sorted output.

- A binary heap is a complete binary tree stored in an array, satisfying the heap property (parent never worse than its children).
- It gives O(1) access to the best element, and O(log n) insert (bubble up) and removal-of-the-best (bubble down).
- A heap is weaker than a BST — it has no ordering rule between siblings or across subtrees, only along the parent-child chain.
- Related concepts: [Heap property & array representation](0116-heap-property-array-representation.md), [Insert & sift-up](0118-insert-sift-up.md), [Extract-min/max & sift-down](0119-extract-min-max-sift-down.md).
