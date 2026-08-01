---
card: data-structures
gi: 83
slug: java-util-priorityqueue-binary-heap
title: java.util.PriorityQueue (binary heap)
---

## 1. What it is

`java.util.PriorityQueue` is Java's built-in priority queue, implemented internally as a **binary heap**: a complete binary tree stored in a plain array, where every parent is never worse (by the comparator) than its children. It implements `Queue`, so it supports `offer`/`poll`/`peek`, but `poll()` always returns the current highest-priority element, not the oldest one.

## 2. Why & when

Use `PriorityQueue` whenever you need "always give me the current best" behavior — Dijkstra's algorithm, merging k sorted lists, finding the k largest/smallest elements in a stream, or any greedy algorithm that repeatedly picks the best remaining option. It gives O(log n) insert and O(log n) removal-of-the-best, which beats sorting the whole collection every time the best element changes.

## 3. Core concept

**What backs it.** A resizable array holding a complete binary tree, indexed so a node at array index `i` has children at `2i + 1` and `2i + 2`, and a parent at `(i - 1) / 2`. This layout needs no explicit pointers — child and parent positions are computed arithmetically.

**Ordering and complexity guarantees.** By default, `PriorityQueue` is a **min-heap**: `poll()` returns the smallest element by natural ordering (`Comparable`), or by a supplied `Comparator`. `offer` and `poll` are both O(log n) — they only need to walk up or down one path in the tree, not touch every element. `peek` is O(1), since the best element always sits at index `0`.

**Basic usage — common methods.**

| Method | Effect | Complexity |
|---|---|---|
| `offer(e)` | insert; "bubble up" until the heap property holds | O(log n) |
| `poll()` | remove and return the root (best); move the last element to the root, "bubble down" | O(log n) |
| `peek()` | return the root without removing | O(1) |

**Iteration, comparators, a realistic task.** Iterating a `PriorityQueue` directly does *not* give sorted order — only repeated `poll()` does. Supplying a `Comparator` (e.g. `Comparator.reverseOrder()` for a max-heap, or a field-based comparator for custom objects) changes what "best" means, without changing any of the algorithm's guarantees.

## 4. Diagram

<svg viewBox="0 0 500 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A min heap as a tree with root 3, children 5 and 8, and the same data laid out as a flat array 3, 5, 8 where child and parent positions are computed by index arithmetic">
  <g font-family="sans-serif" font-size="11">
    <circle cx="200" cy="30" r="20" fill="#0d1117" stroke="#f0883e"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <circle cx="140" cy="90" r="20" fill="#161b22" stroke="#8b949e"/><text x="140" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <circle cx="260" cy="90" r="20" fill="#161b22" stroke="#8b949e"/><text x="260" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <line x1="185" y1="45" x2="155" y2="75" stroke="#8b949e"/>
    <line x1="215" y1="45" x2="245" y2="75" stroke="#8b949e"/>
    <text x="200" y="130" fill="#79c0ff" text-anchor="middle" font-size="9">array layout: [3, 5, 8] -- index 0=root, children at 2i+1, 2i+2</text>
    <rect x="140" y="150" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="160" y="167" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="180" y="150" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="200" y="167" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <rect x="220" y="150" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="240" y="167" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <text x="160" y="195" fill="#8b949e" text-anchor="middle" font-size="9">idx 0</text>
    <text x="200" y="195" fill="#8b949e" text-anchor="middle" font-size="9">idx 1</text>
    <text x="240" y="195" fill="#8b949e" text-anchor="middle" font-size="9">idx 2</text>
  </g>
</svg>

The same heap exists as a tree conceptually and as a flat array physically; array index `0` is always the current best element.

## 5. Runnable example

```java
// PriorityQueueDemo.java
import java.util.Comparator;
import java.util.PriorityQueue;

public class PriorityQueueDemo {

    // Basic: common methods on a min-heap of integers.
    static void basicLevel() {
        PriorityQueue<Integer> pq = new PriorityQueue<>();
        pq.offer(8);
        pq.offer(3);
        pq.offer(5);
        System.out.println("basic: peek (smallest) -> " + pq.peek());
        System.out.println("basic: poll order -> " + pq.poll() + ", " + pq.poll() + ", " + pq.poll());
    }

    // Intermediate: iteration order does NOT reflect priority order -- only poll() does; also a comparator-driven max-heap.
    static void intermediateLevel() {
        PriorityQueue<Integer> pq = new PriorityQueue<>(java.util.List.of(8, 3, 5));
        System.out.println("intermediate: raw iteration (NOT guaranteed sorted) -> " + pq);

        StringBuilder polledOrder = new StringBuilder();
        while (!pq.isEmpty()) polledOrder.append(pq.poll()).append(" ");
        System.out.println("intermediate: poll() order (correctly sorted ascending) -> " + polledOrder.toString().trim());

        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
        maxHeap.offer(8); maxHeap.offer(3); maxHeap.offer(5);
        System.out.println("intermediate: max-heap poll order -> " + maxHeap.poll() + ", " + maxHeap.poll() + ", " + maxHeap.poll());
    }

    // Advanced: a realistic task -- find the k largest elements in a stream using a MIN-heap of size k.
    static java.util.List<Integer> kLargest(int[] nums, int k) {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(); // smallest of the "current top k" sits at the root
        for (int n : nums) {
            minHeap.offer(n);
            if (minHeap.size() > k) minHeap.poll(); // evict the current smallest once the heap exceeds size k
        }
        return new java.util.ArrayList<>(minHeap); // the k largest values, in no particular order
    }

    static void advancedLevel() {
        int[] nums = {3, 1, 5, 12, 2, 11};
        System.out.println("advanced: 3 largest of [3,1,5,12,2,11] -> " + kLargest(nums, 3));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PriorityQueueDemo.java`, then run `java PriorityQueueDemo.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `8, 3, 5`. `peek()` returns `3` — the current minimum — regardless of insertion order. Polling all three gives `3, 5, 8`, fully sorted ascending.
2. `intermediateLevel()` prints the raw internal array via `toString()`, which is **not** guaranteed sorted (it only satisfies the weaker heap property, parent ≤ children) — only draining via `poll()` produces sorted output. The max-heap variant, built with `Comparator.reverseOrder()`, flips "best" to mean largest, giving `8, 5, 3`.
3. `advancedLevel()`'s `kLargest` uses a *min*-heap (not a max-heap) of bounded size `k`, which is the standard trick for "k largest" problems: the heap always holds the current best `k` candidates, and the *smallest* among them (the root) is evicted whenever a new element pushes the heap over size `k`. This keeps only genuinely large values, using O(n log k) time instead of sorting the whole array at O(n log n).

## 7. Gotchas & takeaways

> Gotcha: for the "k largest" pattern, using a max-heap instead of a min-heap is a common but backwards mistake — a max-heap would let you cheaply find the single largest element, but evicting to keep only `k` elements needs cheap access to the *current smallest* of the retained set, which is exactly what a min-heap's root gives you.

- `PriorityQueue` is a binary heap: a complete tree stored in an array, with `offer`/`poll` at O(log n) and `peek` at O(1).
- Iterating it directly does not give sorted order; only repeated `poll()` does.
- A `Comparator` changes what "best" means (min-heap by default, or a custom/reversed order) without changing the complexity guarantees.
- For "k largest" problems, use a bounded min-heap of size `k`; for "k smallest," use a bounded max-heap of size `k`.
- Related concepts: [Priority queue concept](0075-priority-queue-concept.md), [Queue & Deque interfaces](0082-queue-deque-interfaces.md).
