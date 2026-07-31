---
card: data-structures
gi: 17
slug: contiguous-memory-cache-locality
title: Contiguous memory & cache locality
---

## 1. What it is

**Contiguous memory** means elements are stored back-to-back, with no gaps, at consecutive addresses — this is how an array is laid out. **Cache locality** is the performance benefit that comes from this layout: modern CPUs fetch memory in fixed-size chunks called **cache lines** (typically 64 bytes), so reading one array element pulls several of its neighbors into the fast CPU cache for free, before you even ask for them.

## 2. Why & when

This matters whenever you choose between an array and a linked structure (like `LinkedList`) for performance-sensitive code that scans data sequentially. Two structures can have identical Big-O complexity — both `ArrayList` and `LinkedList` iterate in O(n) — yet the array-backed one runs several times faster in practice, purely because of cache locality. Recognizing this explains why "asymptotically equal" code can have very different real-world speed.

## 3. Core concept

**How a cache line works.** When the CPU reads `arr[0]`, it does not fetch 4 bytes in isolation — it pulls in an entire 64-byte cache line, which for an `int[]` covers roughly 16 consecutive elements. If your next access is `arr[1]`, it is very likely already sitting in the fast cache, so it costs almost nothing extra.

**Why linked structures defeat this.** A `LinkedList`'s nodes are scattered across the heap wherever the allocator happened to place them. Walking from one node to the next means following a pointer to a essentially random address, which usually misses the cache and forces a slow trip to main memory — for every single node.

**Sequential access vs random access.** Cache locality helps most for sequential scans (a `for` loop over an array). Random-access patterns (jumping to unpredictable indexes) benefit less, since neighboring data may not be touched again soon regardless of how it is laid out.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array pulling several elements into one cache line versus linked list nodes scattered across memory, each requiring a separate fetch">
  <g font-family="sans-serif" font-size="12">
    <text x="160" y="20" fill="#8b949e" text-anchor="middle">array: one fetch loads a whole cache line</text>
    <rect x="30" y="30" width="260" height="30" fill="none" stroke="#f0883e"/>
    <rect x="35" y="35" width="40" height="20" fill="#161b22" stroke="#3fb950"/>
    <rect x="80" y="35" width="40" height="20" fill="#161b22" stroke="#3fb950"/>
    <rect x="125" y="35" width="40" height="20" fill="#161b22" stroke="#3fb950"/>
    <rect x="170" y="35" width="40" height="20" fill="#161b22" stroke="#3fb950"/>
    <rect x="215" y="35" width="40" height="20" fill="#161b22" stroke="#3fb950"/>
    <text x="160" y="80" fill="#79c0ff" text-anchor="middle" font-size="10">1 memory fetch -&gt; 5 elements ready in cache</text>

    <text x="480" y="20" fill="#8b949e" text-anchor="middle">linked list: nodes scattered, each a separate fetch</text>
    <rect x="380" y="100" width="30" height="20" fill="#161b22" stroke="#79c0ff"/>
    <rect x="560" y="40" width="30" height="20" fill="#161b22" stroke="#79c0ff"/>
    <rect x="450" y="150" width="30" height="20" fill="#161b22" stroke="#79c0ff"/>
    <line x1="410" y1="110" x2="555" y2="50" stroke="#8b949e" stroke-dasharray="3,3"/>
    <line x1="575" y1="60" x2="465" y2="150" stroke="#8b949e" stroke-dasharray="3,3"/>
    <text x="480" y="180" fill="#79c0ff" text-anchor="middle" font-size="10">3 nodes -&gt; 3 separate, likely slow, memory fetches</text>
  </g>
</svg>

Reading one array element brings its neighbors along for free. Reading one linked-list node tells you nothing about where the next one lives in memory.

## 5. Runnable example

```java
// ContiguousMemoryCacheLocality.java
import java.util.LinkedList;
import java.util.List;
import java.util.ArrayList;

public class ContiguousMemoryCacheLocality {

    // Basic: sum an array sequentially -- the cache-friendly access pattern.
    static long sumArray(int[] arr) {
        long sum = 0;
        for (int i = 0; i < arr.length; i++) sum += arr[i]; // sequential, contiguous
        return sum;
    }

    static void basicLevel() {
        int[] arr = new int[2_000_000];
        for (int i = 0; i < arr.length; i++) arr[i] = i;
        long start = System.nanoTime();
        long sum = sumArray(arr);
        long elapsed = System.nanoTime() - start;
        System.out.println("basic: array sum -> " + sum + ", time(ns) -> " + elapsed);
    }

    // Intermediate: sum a LinkedList of the same size -- same O(n), scattered layout.
    static long sumLinkedList(List<Integer> list) {
        long sum = 0;
        for (int value : list) sum += value; // O(n), but each node access can miss the cache
        return sum;
    }

    static void intermediateLevel() {
        List<Integer> linked = new LinkedList<>();
        for (int i = 0; i < 2_000_000; i++) linked.add(i);
        long start = System.nanoTime();
        long sum = sumLinkedList(linked);
        long elapsed = System.nanoTime() - start;
        System.out.println("intermediate: linked list sum -> " + sum + ", time(ns) -> " + elapsed);
    }

    // Advanced: same element count, but backed by an array-based ArrayList, for comparison.
    static void advancedLevel() {
        List<Integer> arrayBacked = new ArrayList<>();
        for (int i = 0; i < 2_000_000; i++) arrayBacked.add(i);
        long start = System.nanoTime();
        long sum = sumLinkedList(arrayBacked); // same loop code, different backing structure
        long elapsed = System.nanoTime() - start;
        System.out.println("advanced: ArrayList sum -> " + sum + ", time(ns) -> " + elapsed);
        System.out.println("advanced: same Big-O (O(n)) as LinkedList, but contiguous storage is typically faster");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ContiguousMemoryCacheLocality.java`, then run `java ContiguousMemoryCacheLocality.java`. Compare the three printed timings.

## 6. Walkthrough

1. `basicLevel()` sums a raw `int[]` of 2 million elements. Each step of the loop touches the very next memory address, so most reads are served from a cache line already pulled in by an earlier read.
2. `intermediateLevel()` sums a `LinkedList<Integer>` holding the same values. The algorithm is still O(n) — same asymptotic complexity — but each node was allocated separately, so the JVM's memory allocator likely scattered them across the heap.
3. Walking the linked list means following a pointer to a new, unpredictable address on every step, which tends to miss the cache far more often than the array loop did.
4. `advancedLevel()` repeats the same summing loop over an `ArrayList`, which stores its elements in one contiguous `Object[]` array internally — it should track much closer to the raw array's timing than the linked list's.
5. Comparing the three printed times shows that identical Big-O complexity does not mean identical real speed — memory layout is a second, independent factor that Big-O notation does not capture.

## 7. Gotchas & takeaways

> Gotcha: Big-O analysis says `ArrayList.get(i)` and stepping through a `LinkedList` are both valid O(n) full scans, so it is easy to assume they perform similarly. In practice the array-backed version is often several times faster, purely from cache locality — always benchmark performance-critical code rather than trusting Big-O alone.

- Contiguous memory lets the CPU cache pull in several neighboring elements with one fetch, benefiting sequential scans the most.
- Linked structures scatter nodes across the heap, so each traversal step is a potentially separate, slow memory fetch.
- Two structures with the same Big-O complexity can still differ meaningfully in real-world speed because of memory layout.
- Related concepts: [Random access by index (O(1))](0018-random-access-by-index-o-1.md), [Static (fixed-size) arrays](0015-static-fixed-size-arrays.md).
