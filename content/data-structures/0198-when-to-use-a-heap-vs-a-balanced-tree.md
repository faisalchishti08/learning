---
card: data-structures
gi: 198
slug: when-to-use-a-heap-vs-a-balanced-tree
title: When to use a heap vs a balanced tree
---

## 1. What it is

A [binary heap](0116-heap-property-array-representation.md) (`PriorityQueue`) and a [balanced BST](0110-avl-trees-rotations.md) (`TreeMap`/`TreeSet`) both keep elements in a partially-ordered structure with `O(log n)` insert, but they answer completely different questions well. A heap only ever gives you fast access to the **single extreme** element. A balanced BST gives you fast access to **any** element, in full sorted order.

## 2. Why & when

Confusing these two is a common mistake, because both feel like "the sorted-ish structure." Use a heap when your workload is specifically "repeatedly process the current smallest/largest item" and nothing else — task scheduling, Dijkstra's algorithm, merging k sorted lists, top-k problems. Use a balanced BST when you need to search for an arbitrary element, iterate in full sorted order, or answer range/nearest queries — none of which a heap supports efficiently.

## 3. Core concept

**The decision criteria.**
- **Do you only ever need the current min/max, repeatedly, as the set changes?** → heap. It is faster and simpler for exactly this.
- **Do you need to search for an arbitrary element by value, not just the extreme?** → balanced BST. A heap only guarantees the root is smallest (or largest) — every other element's position relative to a search target is unconstrained, making search `O(n)` in a heap.
- **Do you need sorted iteration of all elements?** → balanced BST, `O(n)` to traverse in order. A heap's array layout is **not** sorted overall; only repeated extraction produces sorted output, destroying the heap in the process.
- **Do you need range queries ("all elements between X and Y") or nearest-neighbor queries ("largest element <= X")?** → balanced BST only. A heap has no mechanism for this at all.

**Why a heap is faster for its one job.** A heap only maintains one invariant — every parent is smaller (or larger) than its children — which is much weaker than a BST's invariant (every node's entire left subtree is smaller, entire right subtree is larger). This weaker invariant means insert and extract-min only need to fix a single path from root to a leaf (or vice versa) with cheap swaps, and the heap can be stored compactly in a plain array with no node objects or pointers at all — see [heap property & array representation](0116-heap-property-array-representation.md).

**Why a BST is more capable but not "just as fast."** A balanced BST's stronger ordering invariant is what enables search, range queries, and sorted iteration — but maintaining that stronger invariant (via rotations in an [AVL tree](0110-avl-trees-rotations.md), or color-flips in a red-black tree) costs more implementation complexity and a somewhat larger constant factor than a heap's simple array-based sift-up/sift-down operations.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A heap where only the root is guaranteed smallest, versus a balanced BST where every node's position reflects full sorted order">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Heap: only root guaranteed min</text>
    <circle cx="120" cy="40" r="16" fill="#161b22" stroke="#3fb950"/><text x="120" y="44" text-anchor="middle" font-size="9">2</text>
    <circle cx="80" cy="90" r="14" fill="#0d1117" stroke="#8b949e"/><text x="80" y="94" text-anchor="middle" font-size="8">7</text>
    <circle cx="160" cy="90" r="14" fill="#0d1117" stroke="#8b949e"/><text x="160" y="94" text-anchor="middle" font-size="8">5</text>
    <line x1="120" y1="54" x2="80" y2="78" stroke="#3fb950"/>
    <line x1="120" y1="54" x2="160" y2="78" stroke="#3fb950"/>
    <text x="120" y="130" text-anchor="middle" font-size="8" fill="#f0883e">7 and 5 have NO defined relative order</text>

    <text x="400" y="20">Balanced BST: every node's position is meaningful</text>
    <circle cx="470" cy="40" r="16" fill="#161b22" stroke="#79c0ff"/><text x="470" y="44" text-anchor="middle" font-size="9">5</text>
    <circle cx="430" cy="90" r="14" fill="#0d1117" stroke="#8b949e"/><text x="430" y="94" text-anchor="middle" font-size="8">2</text>
    <circle cx="510" cy="90" r="14" fill="#0d1117" stroke="#8b949e"/><text x="510" y="94" text-anchor="middle" font-size="8">7</text>
    <line x1="470" y1="54" x2="430" y2="78" stroke="#79c0ff"/>
    <line x1="470" y1="54" x2="510" y2="78" stroke="#79c0ff"/>
    <text x="470" y="130" text-anchor="middle" font-size="8" fill="#3fb950">search(2): go left, guaranteed correct</text>
  </g>
</svg>

A heap only orders parent-child pairs; a BST orders every node relative to every other node.

## 5. Runnable example

```java
// HeapVsBalancedTree.java
import java.util.*;

public class HeapVsBalancedTree {

    // Basic: PriorityQueue for repeated "process the cheapest item next" -- exactly what a heap is for.
    static void basicLevel() {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(List.of(9, 3, 7, 1, 5));
        System.out.println("basic: repeated poll() gives sorted order via the heap -> ");
        while (!minHeap.isEmpty()) System.out.print(minHeap.poll() + " ");
        System.out.println();
    }

    // Intermediate: searching for an arbitrary value -- a heap needs O(n), a TreeSet needs O(log n).
    static void intermediateLevel() {
        PriorityQueue<Integer> heap = new PriorityQueue<>(List.of(9, 3, 7, 1, 5));
        TreeSet<Integer> tree = new TreeSet<>(List.of(9, 3, 7, 1, 5));

        System.out.println("intermediate: heap.contains(7) -- O(n) internally -> " + heap.contains(7));
        System.out.println("intermediate: tree.contains(7) -- O(log n) internally -> " + tree.contains(7));
    }

    // Advanced: range and nearest-neighbor queries -- only TreeSet can answer these at all.
    static void advancedLevel() {
        TreeSet<Integer> scores = new TreeSet<>(List.of(55, 62, 71, 84, 90, 95));

        System.out.println("advanced: scores between 60 and 85 -> " + scores.subSet(60, true, 85, true));
        System.out.println("advanced: nearest score <= 80 -> " + scores.floor(80));

        // A PriorityQueue has no equivalent methods at all -- this capability simply does not exist on a heap.
        PriorityQueue<Integer> heapScores = new PriorityQueue<>(scores);
        System.out.println("advanced: heap can only cheaply give the overall minimum -> " + heapScores.peek());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java HeapVsBalancedTree.java`

## 6. Walkthrough

`basicLevel` builds a `PriorityQueue` from `[9, 3, 7, 1, 5]`. Its internal array is **not** fully sorted — it only guarantees the root (index `0`) is the minimum. But repeatedly calling `poll()` removes the current minimum, re-heapifies, and repeats, so the **sequence of outputs** comes out sorted: `1, 3, 5, 7, 9`. This is the heap's core trick: it produces sorted *output over time*, without ever fully sorting its *internal storage*.

`intermediateLevel` searches for `7` in both structures. `PriorityQueue.contains` must check every element linearly, since the heap's array offers no shortcut for finding an arbitrary value — only the root position is meaningful. `TreeSet.contains` walks the red-black tree, using the BST ordering invariant to eliminate half the remaining candidates at each step, reaching the answer in `O(log n)`.

`advancedLevel` asks for "scores between 60 and 85" and "the nearest score `<= 80`." `TreeSet.subSet(60, true, 85, true)` returns a live view of exactly the matching range in `O(log n)` to construct. `TreeSet.floor(80)` finds the nearest qualifying score directly. Neither operation has any equivalent on `PriorityQueue` — a heap's structure carries no information that would let it answer either question faster than scanning every element.

**Complexity.** Heap (`PriorityQueue`): insert `O(log n)`, peek min/max `O(1)`, extract min/max `O(log n)`, search arbitrary value `O(n)`, no range/nearest support. Balanced BST (`TreeMap`/`TreeSet`): insert `O(log n)`, search arbitrary value `O(log n)`, min/max `O(log n)` (via `firstKey`/`lastKey`, slightly more than a heap's `O(1)` peek), range and nearest queries `O(log n)`.

## 7. Gotchas & takeaways

> A heap does **not** keep its data fully sorted internally — only the root is guaranteed to be the extreme value at any given moment. Assuming a `PriorityQueue`'s iteration order (via `for` loop or `.toString()`) reflects sorted order is a common and incorrect assumption; only repeated `poll()` calls guarantee that.

- If your workload's only need is "always process the current best candidate next," a heap is both simpler to use and cheaper per operation than a balanced BST — do not reach for `TreeSet` just because it feels more "general purpose."
- If your workload ever needs to search for, delete, or query the range around an arbitrary (non-extreme) element, a heap cannot do this efficiently — a balanced BST is the only correct choice among the two.
- Some problems need *both*: a heap for "process cheapest next" and a separate hash-based index for "find and update this specific element's priority" — this combination (sometimes called an "indexed priority queue") is a common, deliberate hybrid when both access patterns matter simultaneously.
