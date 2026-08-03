---
card: data-structures
gi: 197
slug: array-vs-linked-structure-memory-tradeoffs
title: Array vs linked structure memory tradeoffs
---

## 1. What it is

Array-backed structures (`ArrayList`, arrays) store elements contiguously — back to back in memory. Linked structures (`LinkedList`, trees, graphs built from nodes) store elements in separately allocated objects connected by references. Both can offer identical Big-O for some operations, but their real-world memory usage and speed can differ sharply, because Big-O ignores constant factors that memory layout controls.

## 2. Why & when

Two structures with the same Big-O complexity are not the same in practice. This page is about the **constant factor** hidden inside Big-O notation — specifically, the effect of CPU cache behavior and per-element memory overhead, which is why an `ArrayList` frequently outperforms a `LinkedList` even for operations where their Big-O complexity is identical or close.

## 3. Core concept

**Contiguous memory and cache locality.** An array stores its elements back-to-back in one continuous memory block. Modern CPUs fetch memory in fixed-size chunks called cache lines (commonly 64 bytes), pulling in several adjacent array elements at once even if you only asked for one. Scanning an array sequentially benefits enormously from this: after the first element triggers a cache-line fetch, the next several elements are often already in the fast CPU cache, needing no additional trip to main memory.

**Why linked structures lose this benefit.** Each node in a linked list (or tree) is a separately allocated object, and the JVM's garbage-collected heap gives no guarantee that logically adjacent nodes sit near each other in physical memory. Walking from one node to the next typically means jumping to a different, unpredictable memory location — a **cache miss** — which can be an order of magnitude slower than reading the next element of an already-cached array.

**Per-element memory overhead.** An array of `int` stores exactly 4 bytes per element (plus one array header). A `LinkedList<Integer>` stores each element as: one node object (with JVM object header overhead, typically 12-16 bytes), one reference to the boxed `Integer` value (8 bytes on most modern JVMs with compressed pointers, more without), the boxed `Integer` object itself (12-16 bytes), and two more references for `prev`/`next` pointers (16 bytes). The result is often **5-10x more memory** per element for a linked structure versus a primitive array holding the same logical data.

**Why this matters even when Big-O ties.** `ArrayList.get(i)` and iterating a `LinkedList` are both, in some sense, "O(n) to visit every element" for a full traversal — but the array version runs measurably faster in practice due to cache locality, and uses a fraction of the memory, due to the overhead difference above. Big-O describes how cost scales with input size; it says nothing about the fixed multiplier attached to that scaling.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array laid out contiguously in memory, fitting several elements per cache line, versus a linked list with nodes scattered across memory, each access a potential cache miss">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Array: contiguous, cache-friendly</text>
    <rect x="20" y="30" width="30" height="30" fill="#161b22" stroke="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#161b22" stroke="#3fb950"/>
    <rect x="80" y="30" width="30" height="30" fill="#161b22" stroke="#3fb950"/>
    <rect x="110" y="30" width="30" height="30" fill="#161b22" stroke="#3fb950"/>
    <rect x="15" y="25" width="130" height="40" fill="none" stroke="#3fb950" stroke-dasharray="3,3"/>
    <text x="80" y="80" text-anchor="middle" font-size="8" fill="#3fb950">one cache-line fetch covers all 4</text>

    <text x="10" y="130">LinkedList: scattered, cache-unfriendly</text>
    <rect x="20" y="140" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="220" y="150" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="380" y="130" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="500" y="160" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <line x1="50" y1="155" x2="220" y2="165" stroke="#f0883e" stroke-dasharray="2,2"/>
    <line x1="250" y1="165" x2="380" y2="145" stroke="#f0883e" stroke-dasharray="2,2"/>
    <line x1="410" y1="145" x2="500" y2="175" stroke="#f0883e" stroke-dasharray="2,2"/>
    <text x="280" y="195" text-anchor="middle" font-size="8" fill="#f0883e">each hop is a potential cache miss -- unpredictable location</text>
  </g>
</svg>

Array elements ride along "for free" in the same cache-line fetch; linked nodes each need their own memory trip.

## 5. Runnable example

```java
// ArrayVsLinkedMemory.java
import java.util.*;

public class ArrayVsLinkedMemory {

    // Basic: measure sequential traversal speed, array-backed vs linked, for the same data.
    static void basicLevel() {
        int n = 1_000_000;
        List<Integer> arrayList = new ArrayList<>();
        List<Integer> linkedList = new LinkedList<>();
        for (int i = 0; i < n; i++) { arrayList.add(i); linkedList.add(i); }

        long sum1 = 0;
        long start1 = System.nanoTime();
        for (int value : arrayList) sum1 += value; // sequential, cache-friendly access
        long arrayTime = System.nanoTime() - start1;

        long sum2 = 0;
        long start2 = System.nanoTime();
        for (int value : linkedList) sum2 += value; // sequential, but scattered node hops
        long linkedTime = System.nanoTime() - start2;

        System.out.printf("basic: ArrayList traversal (%d elements) -> %.1f ms%n", n, arrayTime / 1_000_000.0);
        System.out.printf("basic: LinkedList traversal (%d elements) -> %.1f ms%n", n, linkedTime / 1_000_000.0);
    }

    // Intermediate: show the O(n^2) trap of indexed access on a LinkedList, versus O(n) for ArrayList.
    static void intermediateLevel() {
        int n = 5_000; // smaller n -- this pattern is O(n^2) for LinkedList and would be very slow at scale
        List<Integer> arrayList = new ArrayList<>();
        List<Integer> linkedList = new LinkedList<>();
        for (int i = 0; i < n; i++) { arrayList.add(i); linkedList.add(i); }

        long start1 = System.nanoTime();
        long sum1 = 0;
        for (int i = 0; i < arrayList.size(); i++) sum1 += arrayList.get(i); // O(1) per get -- O(n) total
        long arrayTime = System.nanoTime() - start1;

        long start2 = System.nanoTime();
        long sum2 = 0;
        for (int i = 0; i < linkedList.size(); i++) sum2 += linkedList.get(i); // O(n) per get -- O(n^2) total
        long linkedTime = System.nanoTime() - start2;

        System.out.printf("intermediate: ArrayList indexed get loop -> %.1f ms%n", arrayTime / 1_000_000.0);
        System.out.printf("intermediate: LinkedList indexed get loop (O(n^2)!) -> %.1f ms%n", linkedTime / 1_000_000.0);
    }

    // Advanced: estimate the per-element memory overhead difference using Java's memory footprint characteristics.
    static void advancedLevel() {
        int n = 100_000;
        // int[]: n * 4 bytes + a small array header, roughly 400 KB for 100,000 ints.
        int estimatedArrayBytes = n * 4 + 16;

        // LinkedList<Integer>: each element needs a Node (header + 3 refs ~ 32-40 bytes)
        // plus a boxed Integer object (~16 bytes), roughly 48-56 bytes per element.
        int estimatedLinkedListBytes = n * 52;

        System.out.printf("advanced: estimated int[] memory for %d elements -> ~%d KB%n", n, estimatedArrayBytes / 1024);
        System.out.printf("advanced: estimated LinkedList<Integer> memory for %d elements -> ~%d KB%n", n, estimatedLinkedListBytes / 1024);
        System.out.printf("advanced: overhead ratio -> ~%.1fx%n", (double) estimatedLinkedListBytes / estimatedArrayBytes);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ArrayVsLinkedMemory.java`

## 6. Walkthrough

Both `basicLevel` traversals visit every one of a million elements exactly once, and both are `O(n)` by the Big-O rulebook. But `ArrayList`'s for-each loop reads sequential memory addresses, letting the CPU's cache prefetcher do its job effectively — measured wall-clock time is typically noticeably faster than `LinkedList`'s traversal, which follows a `next` reference to a new, unpredictable memory location on every single step, frequently missing the cache and paying the full cost of a main-memory fetch.

`intermediateLevel` demonstrates a much starker, complexity-class difference (not just a constant factor): looping with `list.get(i)` for increasing `i`. For `ArrayList`, each `get(i)` is a direct `O(1)` array-offset calculation, so the whole loop is `O(n)`. For `LinkedList`, each `get(i)` must walk from the nearer end of the list to reach position `i`, costing `O(i)` (or `O(n-i)`) — repeated for every `i` from `0` to `n`, the total cost becomes `O(n^2)`. This is why the benchmark deliberately uses a smaller `n` for this specific test — at the full million-element scale used in `basicLevel`, this `O(n^2)` pattern on a `LinkedList` would take dramatically longer.

For memory: a primitive `int[]` needs essentially `4` bytes per element. A `LinkedList<Integer>` needs a node object (with JVM object header and `prev`/`next` references) **and** a separately boxed `Integer` object per element, together typically landing around `48-56` bytes per element — roughly `10x` the array's footprint for the same logical data, purely from structural and boxing overhead that has nothing to do with the actual values being stored.

**Complexity.** Both structures share the same Big-O for full sequential traversal (`O(n)`) — the difference here is entirely in constant factors: cache behavior and per-element memory overhead, neither of which Big-O notation captures.

## 7. Gotchas & takeaways

> Two structures having identical Big-O complexity for an operation does not mean identical real-world performance — always consider memory layout (contiguous vs scattered) and per-element overhead (primitive vs boxed, plus node/reference overhead) when the constant factor actually matters, such as in performance-critical or memory-constrained code.

- Prefer primitive-backed structures (`int[]`, or libraries offering primitive collections like `IntArrayList`) over boxed generic collections (`List<Integer>`) when working with large volumes of primitive data — the memory and cache-locality savings can be substantial.
- `LinkedList.get(i)` in a loop is a classic accidental `O(n^2)` — always prefer an iterator (or a for-each loop) for sequential access to a `LinkedList`, reserving indexed `get` for `ArrayList`-like structures.
- This memory-layout consideration is a separate, orthogonal axis from the [ordered vs unordered tradeoff](0196-ordered-vs-unordered-structure-tradeoffs.md) covered on the previous page — a design decision can need to account for both simultaneously.
