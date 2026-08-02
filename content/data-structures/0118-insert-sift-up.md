---
card: data-structures
gi: 118
slug: insert-sift-up
title: Insert & sift-up
---

## 1. What it is

**Sift-up** (also called "bubble up" or "percolate up") is the repair step that runs after inserting a new value into a heap. It repeatedly compares the new value against its parent and swaps upward until the heap property holds again, or the value reaches the root.

## 2. Why & when

Adding a value at the next free array slot keeps the tree complete, but it can break the heap property — the new value might be smaller (for a min-heap) than its parent. Sift-up is the general-purpose fix for exactly that one local violation. It comes up any time you insert into a heap, and it is also the core of `decrease-key` in graph algorithms like Dijkstra's: lowering a value in place still requires the same "check against parent, swap upward if needed" repair.

## 3. Core concept

**How the operation works.** Insert always happens at the next free index (`data[size]`, then `size++`), preserving completeness immediately. Then, starting at that new index:

1. Compare the value against its parent (`data[parent(i)]`).
2. If the parent is worse (larger, for a min-heap), swap them.
3. Move `i` to the parent's old index, and repeat, until either the parent is no longer worse, or `i` reaches the root (index `0`).

**The invariant it must preserve.** After sift-up finishes, every parent-child pair along the path from the new value's original position up to its final resting place must satisfy the heap property — and, critically, sift-up must NOT disturb any other part of the tree; it only ever touches nodes on that single upward path.

**Why it terminates in O(log n).** Each swap moves the value one level up a tree whose height is `O(log n)` (the tree stays complete, so its height is bounded by `log2(n) + 1`). In the worst case, the newly inserted value is smaller than everything on the path to the root, so it swaps all the way up — still only `O(log n)` swaps, since that is the maximum number of levels to cross.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting value 2 at the next free leaf position, then sifting it up past two parents that are both larger, until it reaches the root">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">insert 2 -&gt; placed as a leaf, then sifts up past 8 and 5</text>
    <circle cx="320" cy="40" r="16" fill="#161b22" stroke="#8b949e"/><text x="320" y="44" fill="#e6edf3" text-anchor="middle" font-size="8">3</text>
    <circle cx="260" cy="95" r="16" fill="#161b22" stroke="#f0883e"/><text x="260" y="99" fill="#e6edf3" text-anchor="middle" font-size="8">5</text>
    <circle cx="380" cy="95" r="16" fill="#161b22" stroke="#8b949e"/><text x="380" y="99" fill="#e6edf3" text-anchor="middle" font-size="8">9</text>
    <circle cx="230" cy="150" r="16" fill="#161b22" stroke="#f0883e"/><text x="230" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">8</text>
    <circle cx="290" cy="150" r="16" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="290" y="154" fill="#e6edf3" text-anchor="middle" font-size="8">2</text>
    <line x1="308" y1="52" x2="272" y2="83" stroke="#8b949e"/><line x1="332" y1="52" x2="368" y2="83" stroke="#8b949e"/>
    <line x1="248" y1="107" x2="236" y2="138" stroke="#8b949e"/><line x1="272" y1="107" x2="284" y2="138" stroke="#8b949e"/>
    <text x="290" y="185" fill="#79c0ff" text-anchor="middle" font-size="9">step 1: 2 &lt; 8 (parent) -&gt; swap</text>
    <text x="290" y="205" fill="#79c0ff" text-anchor="middle" font-size="9">step 2: 2 &lt; 5 (new parent) -&gt; swap; 2 becomes new root</text>
  </g>
</svg>

`2` is inserted as the last leaf. It is smaller than its parent `8`, so it swaps up; it is still smaller than its new parent `5`, so it swaps again, becoming the new root after two upward steps.

## 5. Runnable example

```java
// SiftUp.java
import java.util.Arrays;

public class SiftUp {

    static int parent(int i) { return (i - 1) / 2; }

    // Basic: sift-up in isolation -- given an array that is a valid heap EXCEPT possibly at the last index, fix it.
    static void siftUp(int[] heap, int i) {
        while (i > 0 && heap[parent(i)] > heap[i]) {
            int t = heap[i]; heap[i] = heap[parent(i)]; heap[parent(i)] = t;
            i = parent(i);
        }
    }

    static void basicLevel() {
        int[] heap = {3, 5, 9, 8, 2}; // valid heap for indices 0..3; index 4 (value 2) was just inserted
        System.out.println("basic: before siftUp -> " + Arrays.toString(heap));
        siftUp(heap, 4);
        System.out.println("basic: after siftUp(4) -> " + Arrays.toString(heap));
    }

    // Intermediate: a full insert operation, built from "place at next slot" + siftUp.
    static int[] insert(int[] heap, int size, int value) {
        heap[size] = value;
        siftUp(heap, size);
        return heap;
    }

    static void intermediateLevel() {
        int[] heap = new int[10];
        int size = 0;
        int[] toInsert = {5, 8, 3, 9, 2, 7};
        for (int v : toInsert) { heap = insert(heap, size, v); size++; }
        System.out.println("intermediate: heap array after inserting " + Arrays.toString(toInsert) + " -> "
            + Arrays.toString(Arrays.copyOf(heap, size)));
    }

    // Advanced: count swaps performed, to show sift-up costs at most O(log n) -- never more than the tree's height.
    static int siftUpCounting(int[] heap, int i) {
        int swaps = 0;
        while (i > 0 && heap[parent(i)] > heap[i]) {
            int t = heap[i]; heap[i] = heap[parent(i)]; heap[parent(i)] = t;
            i = parent(i);
            swaps++;
        }
        return swaps;
    }

    static void advancedLevel() {
        int[] heap = new int[1100];
        int size = 0;
        for (int v = 1000; v >= 1; v--) { // insert in DECREASING order -- the worst case, forcing max sift-up work each time
            heap[size] = v;
            int swaps = siftUpCounting(heap, size);
            size++;
            if (v == 1) System.out.println("advanced: inserting the final (smallest) value required " + swaps + " swaps");
        }
        System.out.println("advanced: log2(1000) ~= 10 -- worst-case swap count for any single insert stays near that bound");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SiftUp.java`, then run `java SiftUp.java`.

## 6. Walkthrough

1. `basicLevel()` starts from `{3, 5, 9, 8, 2}`, where every index except the last already satisfies the heap property. `siftUp(heap, 4)` compares `heap[4] = 2` against `heap[parent(4)] = heap[1] = 5`; since `2 < 5`, it swaps, producing `{3, 2, 9, 8, 5}` and moving the cursor to index `1`. It then compares `heap[1] = 2` against `heap[parent(1)] = heap[0] = 3`; since `2 < 3`, it swaps again, producing `{2, 3, 9, 8, 5}`. Index `0` is the root, so the loop stops.
2. `intermediateLevel()` builds a full heap by repeatedly inserting at the next slot and calling `siftUp`. Each insertion only ever touches the single path from the new leaf to wherever it settles — the rest of the array is untouched by that call.
3. `advancedLevel()` inserts `1000, 999, ..., 1` — strictly decreasing order, the worst case, since every new value is smaller than everything already in the heap and must sift all the way to the root. Counting swaps for the final insert (value `1`) shows a swap count close to `log2(1000) ≈ 10`, confirming sift-up never does more work than the tree's height, even in this adversarial case.

## 7. Gotchas & takeaways

> Gotcha: sift-up only ever compares a node against its *parent*, never against its sibling or any other node — do not confuse it with sift-down, which must check *both* children to find the correct direction to swap.

- Sift-up repairs a heap after a value is placed at the next free array slot, moving it upward while it violates the heap property against its parent.
- It touches only one path (leaf to final position), costing O(log n) — the height of a complete binary tree of `n` nodes.
- The same mechanism implements `decrease-key`: after lowering a value in place, sift-up restores the property exactly the same way as after a fresh insert.
- Related concepts: [Binary heap (min-heap & max-heap)](0115-binary-heap-min-heap-max-heap.md), [Extract-min/max & sift-down](0119-extract-min-max-sift-down.md).
