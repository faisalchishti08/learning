---
card: data-structures
gi: 117
slug: d-ary-heaps-overview
title: d-ary heaps (overview)
---

## 1. What it is

A **d-ary heap** generalizes a binary heap: instead of every node having at most 2 children, every node has at most `d` children. A binary heap is simply the special case `d = 2`. The same array representation and heap property apply — only the branching factor changes.

## 2. Why & when

A d-ary heap trades insert cost against extract cost. A larger `d` makes the tree shorter (height `O(log_d n)` instead of `O(log_2 n)`), so bubbling a value up to the root during insert touches fewer levels — faster inserts. But extracting the best element now must compare against up to `d` children at each level instead of 2 — slower per-level work during "bubble down." Choose a larger `d` (often 4) when inserts vastly outnumber extractions, which is common in graph algorithms like Dijkstra's, where you decrease-key far more often than you extract-min.

## 3. Core concept

**The structure's shape.** The same completeness rule applies, generalized: for a node at array index `i`, its children live at indices `d*i + 1` through `d*i + d`, and its parent lives at index `(i - 1) / d`. Setting `d = 2` recovers the exact binary-heap formulas.

**How the invariant makes operations fast, and the tradeoff.** A d-ary heap of `n` nodes has height `O(log_d n)` — larger `d` means a shorter tree, so "bubble up" during insert does fewer swaps (`O(log_d n)` instead of `O(log_2 n)`). But "bubble down" during extraction must scan up to `d` children to find the smallest at every level, costing `O(d * log_d n)` — worse than binary's `O(log_2 n)` once `d` grows large enough that the extra per-level comparisons outweigh the shorter height.

**When to pick which `d`.** Dijkstra's algorithm on a dense graph performs many more decrease-key/insert operations than extract-min operations, so a 4-ary or 8-ary heap often outperforms a binary heap there in practice, despite the theoretically worse extract cost — the insert savings dominate.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A binary heap of height 3 next to a 4-ary heap holding the same 7 values at height 2, showing the shorter tree from a larger branching factor">
  <g font-family="sans-serif" font-size="11">
    <text x="140" y="16" fill="#8b949e" text-anchor="middle">binary heap (d=2), 7 nodes, height 3</text>
    <circle cx="140" cy="35" r="14" fill="#161b22" stroke="#79c0ff"/><text x="140" y="39" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <circle cx="100" cy="80" r="12" fill="#161b22" stroke="#8b949e"/><text x="100" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">2</text>
    <circle cx="180" cy="80" r="12" fill="#161b22" stroke="#8b949e"/><text x="180" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">3</text>
    <circle cx="70" cy="125" r="10" fill="#161b22" stroke="#8b949e"/><text x="70" y="129" fill="#e6edf3" text-anchor="middle" font-size="6">4</text>
    <circle cx="130" cy="125" r="10" fill="#161b22" stroke="#8b949e"/><text x="130" y="129" fill="#e6edf3" text-anchor="middle" font-size="6">5</text>
    <circle cx="150" cy="125" r="10" fill="#161b22" stroke="#8b949e"/><text x="150" y="129" fill="#e6edf3" text-anchor="middle" font-size="6">6</text>
    <circle cx="210" cy="125" r="10" fill="#161b22" stroke="#8b949e"/><text x="210" y="129" fill="#e6edf3" text-anchor="middle" font-size="6">7</text>
    <line x1="130" y1="45" x2="108" y2="70" stroke="#8b949e"/><line x1="150" y1="45" x2="172" y2="70" stroke="#8b949e"/>

    <text x="480" y="16" fill="#79c0ff" text-anchor="middle">4-ary heap (d=4), same 7 nodes, height 2</text>
    <circle cx="480" cy="40" r="14" fill="#0d1117" stroke="#f0883e"/><text x="480" y="44" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <circle cx="400" cy="100" r="11" fill="#161b22" stroke="#79c0ff"/><text x="400" y="104" fill="#e6edf3" text-anchor="middle" font-size="7">2</text>
    <circle cx="450" cy="100" r="11" fill="#161b22" stroke="#79c0ff"/><text x="450" y="104" fill="#e6edf3" text-anchor="middle" font-size="7">3</text>
    <circle cx="500" cy="100" r="11" fill="#161b22" stroke="#79c0ff"/><text x="500" y="104" fill="#e6edf3" text-anchor="middle" font-size="7">4</text>
    <circle cx="550" cy="100" r="11" fill="#161b22" stroke="#79c0ff"/><text x="550" y="104" fill="#e6edf3" text-anchor="middle" font-size="7">5</text>
    <line x1="465" y1="50" x2="410" y2="88" stroke="#8b949e"/><line x1="475" y1="52" x2="452" y2="88" stroke="#8b949e"/>
    <line x1="485" y1="52" x2="498" y2="88" stroke="#8b949e"/><line x1="495" y1="50" x2="546" y2="88" stroke="#8b949e"/>
    <text x="480" y="200" fill="#79c0ff" text-anchor="middle" font-size="9">same node count, shorter tree -- fewer levels to bubble up during insert</text>
  </g>
</svg>

The same set of values takes 3 levels as a binary heap but only 2 levels as a 4-ary heap — insert's "bubble up" crosses fewer levels, at the cost of scanning more children per level during extraction.

## 5. Runnable example

```java
// DAryHeap.java
import java.util.Arrays;

public class DAryHeap {

    int[] data;
    int size = 0;
    final int d; // branching factor

    DAryHeap(int capacity, int d) {
        data = new int[capacity];
        this.d = d;
    }

    int parent(int i) { return (i - 1) / d; }
    int firstChild(int i) { return d * i + 1; }

    void swap(int i, int j) { int t = data[i]; data[i] = data[j]; data[j] = t; }

    // Basic: insert -- bubble up, using the generalized parent formula (d-ary version of a binary heap's insert).
    void insert(int value) {
        data[size] = value;
        int i = size;
        size++;
        while (i > 0 && data[parent(i)] > data[i]) {
            swap(i, parent(i));
            i = parent(i);
        }
    }

    static void basicLevel() {
        DAryHeap heap = new DAryHeap(10, 4); // 4-ary heap
        for (int v : new int[]{5, 8, 3, 9, 7, 6, 10}) heap.insert(v);
        System.out.println("basic: 4-ary heap array -> " + Arrays.toString(Arrays.copyOf(heap.data, heap.size)));
        System.out.println("basic: root (smallest) -> " + heap.data[0]);
    }

    // Intermediate: extractMin -- bubble down, scanning up to d children instead of just 2.
    int extractMin() {
        int min = data[0];
        size--;
        data[0] = data[size];
        int i = 0;
        while (true) {
            int smallest = i;
            int start = firstChild(i);
            for (int c = start; c < start + d && c < size; c++) { // scan ALL d children, not just 2
                if (data[c] < data[smallest]) smallest = c;
            }
            if (smallest == i) break;
            swap(i, smallest);
            i = smallest;
        }
        return min;
    }

    static void intermediateLevel() {
        DAryHeap heap = new DAryHeap(10, 4);
        for (int v : new int[]{5, 8, 3, 9, 7, 6, 10}) heap.insert(v);

        StringBuilder order = new StringBuilder();
        while (heap.size > 0) order.append(heap.extractMin()).append(" ");
        System.out.println("intermediate: extractMin repeatedly on 4-ary heap -> " + order.toString().trim());
    }

    // Advanced: compare heights of a binary heap (d=2) vs a 4-ary heap holding the SAME number of elements.
    static int heightFor(int n, int d) {
        int height = 0, capacityAtHeight = 1, total = 1;
        while (total < n) {
            capacityAtHeight *= d;
            total += capacityAtHeight;
            height++;
        }
        return height;
    }

    static void advancedLevel() {
        int n = 1000;
        System.out.println("advanced: n=" + n + ", binary heap (d=2) height -> " + heightFor(n, 2));
        System.out.println("advanced: n=" + n + ", 4-ary heap (d=4) height -> " + heightFor(n, 4));
        System.out.println("advanced: shorter height -> fewer levels for insert's bubble-up to cross");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DAryHeap.java`, then run `java DAryHeap.java`.

## 6. Walkthrough

1. `basicLevel()` inserts seven values into a 4-ary heap. Because `d = 4`, each node can have up to four children, so the tree stays shallow — `insert`'s bubble-up loop uses `parent(i) = (i-1)/4` instead of `(i-1)/2`, meaning fewer parent hops before reaching the root compared to a binary heap holding the same values.
2. `intermediateLevel()` extracts repeatedly. `extractMin`'s bubble-down loop now scans a range of up to `d` children (`firstChild(i)` through `firstChild(i) + d - 1`) to find the smallest, instead of just two — more comparisons per level, but there are fewer levels overall.
3. `advancedLevel()` computes tree height for `n = 1000` elements at `d = 2` versus `d = 4`. The 4-ary heap comes out noticeably shorter, confirming `O(log_d n)` height shrinks as `d` grows — the concrete reason insert gets cheaper as branching factor increases.

## 7. Gotchas & takeaways

> Gotcha: increasing `d` is not free — extract-min's per-level cost grows to `O(d)` comparisons, so past a certain point (very large `d`), the extra scanning per level outweighs the height savings. In practice `d = 4` is a common sweet spot; going much higher rarely helps.

- A d-ary heap generalizes a binary heap by letting each node have up to `d` children; `d = 2` recovers the ordinary binary heap.
- Parent/child index formulas generalize directly: children of `i` are `d*i + 1` through `d*i + d`; parent is `(i - 1) / d`.
- Larger `d` shortens the tree (cheaper insert/bubble-up) but makes each bubble-down step scan more children (costlier extract-min).
- Related concepts: [Binary heap (min-heap & max-heap)](0115-binary-heap-min-heap-max-heap.md), [Heap property & array representation](0116-heap-property-array-representation.md).
