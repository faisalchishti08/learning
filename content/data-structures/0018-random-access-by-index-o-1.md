---
card: data-structures
gi: 18
slug: random-access-by-index-o-1
title: Random access by index (O(1))
---

## 1. What it is

**Random access** means reaching any element directly by its position, in the same amount of time no matter where it sits in the collection. An array offers this with **O(1)** (constant time) complexity: `arr[999_999]` costs exactly the same as `arr[0]`. This is the defining strength of arrays, in contrast to structures like a linked list, where reaching the millionth element means walking through the 999,999 before it.

## 2. Why & when

Choose an array (or an array-backed structure like `ArrayList`) whenever your code frequently reads elements by known position — indexing into a lookup table, jumping to a specific row, or random-access algorithms like binary search. If your access pattern is mostly "find the next/previous element" rather than "jump to position k", the O(1) advantage of arrays matters less.

## 3. Core concept

**Why it is O(1): direct address arithmetic.** An array's elements are contiguous and equally sized, so the address of `arr[i]` is computed directly: `base_address + i * element_size`. This is one multiplication and one addition — a fixed amount of work regardless of `i` or the array's total length.

**Contrast: O(n) access in a linked list.** A `LinkedList` has no such formula. To reach the `i`-th node, you must follow `i` `next` pointers one at a time starting from the head (or from the tail, whichever is closer, for a doubly linked list) — the work grows linearly with `i`.

**Constant time does not mean "instant" or "free".** O(1) means the cost does not grow with input size — it can still involve real work (the multiply, the add, the memory fetch). It is "constant" relative to `n`, not literally zero-cost.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array index 500000 reached in one step via address math, versus a linked list requiring 500000 pointer hops">
  <g font-family="sans-serif" font-size="12">
    <text x="160" y="20" fill="#8b949e" text-anchor="middle">array: arr[500000]</text>
    <rect x="60" y="35" width="200" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="160" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">base + 500000*4 -&gt; direct hit</text>
    <text x="160" y="90" fill="#79c0ff" text-anchor="middle" font-size="10">one computation, regardless of index</text>

    <text x="480" y="20" fill="#8b949e" text-anchor="middle">linked list: node #500000</text>
    <rect x="380" y="35" width="30" height="25" fill="#161b22" stroke="#79c0ff"/><text x="395" y="52" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <rect x="420" y="35" width="30" height="25" fill="#161b22" stroke="#79c0ff"/><text x="435" y="52" fill="#e6edf3" text-anchor="middle" font-size="8">2</text>
    <rect x="460" y="35" width="30" height="25" fill="#161b22" stroke="#79c0ff"/><text x="475" y="52" fill="#e6edf3" text-anchor="middle" font-size="8">3</text>
    <text x="500" y="52" fill="#8b949e" font-size="14">...</text>
    <rect x="540" y="35" width="60" height="25" fill="#161b22" stroke="#79c0ff"/><text x="570" y="52" fill="#e6edf3" text-anchor="middle" font-size="8">500000</text>
    <text x="480" y="90" fill="#79c0ff" text-anchor="middle" font-size="10">500000 pointer hops, one node at a time</text>
  </g>
</svg>

The array jumps directly to the address. The linked list must hop through every earlier node first — the cost scales with the index.

## 5. Runnable example

```java
// RandomAccessByIndex.java
import java.util.LinkedList;
import java.util.List;

public class RandomAccessByIndex {

    // Basic: array access cost does not depend on the index.
    static void basicLevel() {
        int[] arr = new int[1_000_000];
        for (int i = 0; i < arr.length; i++) arr[i] = i;

        long t1 = System.nanoTime();
        int early = arr[10];
        long time1 = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        int late = arr[999_990];
        long time2 = System.nanoTime() - t2;

        System.out.println("basic: arr[10]=" + early + " time(ns)=" + time1);
        System.out.println("basic: arr[999990]=" + late + " time(ns)=" + time2 + " (roughly the same cost)");
    }

    // Intermediate: LinkedList.get(i) cost grows with i, because it must walk from the head.
    static void intermediateLevel() {
        List<Integer> linked = new LinkedList<>();
        for (int i = 0; i < 200_000; i++) linked.add(i);

        long t1 = System.nanoTime();
        int early = linked.get(10);
        long time1 = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        int late = linked.get(199_990);
        long time2 = System.nanoTime() - t2;

        System.out.println("intermediate: get(10)=" + early + " time(ns)=" + time1);
        System.out.println("intermediate: get(199990)=" + late + " time(ns)=" + time2 + " (noticeably slower — walked further)");
    }

    // Advanced: random access lets binary search work at all -- it needs O(1) jumps to the midpoint.
    static int binarySearch(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int midVal = sorted[mid]; // O(1) jump straight to the midpoint -- this is the whole trick
            if (midVal == target) return mid;
            if (midVal < target) lo = mid + 1; else hi = mid - 1;
        }
        return -1;
    }

    static void advancedLevel() {
        int[] sorted = new int[1_000_000];
        for (int i = 0; i < sorted.length; i++) sorted[i] = i * 2;
        int index = binarySearch(sorted, 1_999_998);
        System.out.println("advanced: found target at index -> " + index);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `RandomAccessByIndex.java`, then run `java RandomAccessByIndex.java`.

## 6. Walkthrough

1. `basicLevel()` reads `arr[10]` and `arr[999_990]` and times each separately. Both reads resolve to one address computation, so their timings should land in the same ballpark despite one index being far larger than the other.
2. `intermediateLevel()` calls `LinkedList.get(10)` and `LinkedList.get(199_990)`. `get(i)` internally walks `i` `next` references from the head one at a time, so `get(199_990)` does roughly 20,000 times more work than `get(10)` — the timing gap should be visible.
3. `advancedLevel()`'s `binarySearch` repeatedly jumps to `sorted[mid]`. Every jump is an O(1) random access — this is only efficient because arrays support it; running the same algorithm over a `LinkedList` would make each "jump" an O(n) walk, destroying binary search's advantage.
4. The search narrows the range by half on each step, using direct index math to land exactly on the midpoint, until it finds the target or the range is empty.

## 7. Gotchas & takeaways

> Gotcha: `LinkedList.get(i)` looks like it should behave like `arr[i]`, since both are called with an index, but it is O(n), not O(1) — calling `get(i)` in a loop over a `LinkedList` silently turns an O(n) algorithm into O(n²). Use an iterator (or an array-backed list) when scanning a `LinkedList` in order.

- Array indexing is O(1) because the element's address is computed directly from the index — no traversal needed.
- Structures without a formula for "address of element i" (like linked lists) require O(n) traversal for indexed access.
- Algorithms like binary search rely on O(1) random access to be efficient at all; they degrade badly on structures without it.
- Related concepts: [Contiguous memory & cache locality](0017-contiguous-memory-cache-locality.md), [Binary search on a sorted array](0025-binary-search-on-a-sorted-array.md).
