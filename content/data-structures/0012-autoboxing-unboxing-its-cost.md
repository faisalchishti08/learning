---
card: data-structures
gi: 12
slug: autoboxing-unboxing-its-cost
title: Autoboxing / unboxing & its cost
---

## 1. What it is

**Autoboxing** is Java's automatic conversion of a primitive value (like `int`) into its corresponding wrapper object (`Integer`) whenever a reference type is required — for example, adding an `int` to a `List<Integer>`. **Unboxing** is the reverse: automatically extracting the primitive value back out of a wrapper object when a primitive is needed. Both conversions happen invisibly, inserted by the compiler, which is convenient but not free — each conversion has a real memory and performance cost.

## 2. Why & when

This matters whenever primitives need to interact with generic, reference-only APIs — Java generics cannot use primitive types directly (`List<int>` is not valid; it must be `List<Integer>`), so any code storing primitives in a generic collection relies on autoboxing. Recognizing where this happens (often invisibly) explains otherwise-surprising performance costs and subtle bugs, especially around `==` comparison and small-integer caching.

## 3. Core concept

**Why boxing has a real cost:** an `int` is a raw 4-byte value living directly on the stack (or inline within an array/object). An `Integer` is a full heap-allocated object — it has object header overhead (typically 12-16 bytes on most JVMs, for type information and other bookkeeping), plus the 4 bytes for the actual value, plus the cost of the allocation itself and eventual garbage collection. Boxing an `int` into an `Integer` is therefore not just "wrapping" a value — it is allocating a small object on the heap, with all the overhead that implies.

**Why this matters most in loops and large collections:** a `List<Integer>` holding a million integers is not storing a million raw 4-byte values contiguously (like an `int[]` would) — it is storing a million *references*, each pointing to a separately heap-allocated `Integer` object with its own overhead. This can easily use 3-4x more memory than a raw `int[]` of the same logical size, and each autoboxing operation during insertion is extra allocation work the JVM must perform.

**The `Integer` caching gotcha, and why `==` is dangerous for boxed types:** Java caches `Integer` objects for values in the range `-128` to `127` (a JVM-level optimization, since these small values are extremely common) — so `Integer a = 100; Integer b = 100;` might have `a == b` return `true` (same cached object), while `Integer c = 200; Integer d = 200;` has `c == d` return `false` (different objects outside the cached range, each freshly allocated). This inconsistency is a classic source of confusing, hard-to-reproduce bugs — always use `.equals()` (or unbox to compare primitives directly) when comparing `Integer` values, never `==`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An int stored inline as 4 bytes, versus an Integer requiring a full heap object with header overhead plus the value">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">int (primitive)</text>
    <rect x="60" y="30" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="120" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">4 bytes: value</text>
    <text x="500" y="20" fill="#8b949e" text-anchor="middle">Integer (boxed, heap object)</text>
    <rect x="380" y="30" width="240" height="70" fill="none" stroke="#f0883e"/>
    <text x="500" y="55" fill="#e6edf3" text-anchor="middle" font-size="11">object header (~12-16 bytes)</text>
    <text x="500" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">4 bytes: value</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">boxing multiplies memory use several times over, plus allocation/GC cost</text>
  </g>
</svg>

A boxed `Integer` costs several times more memory than the raw `int` value it wraps, due to object header overhead and separate heap allocation.

## 5. Runnable example

The artifact below measures the actual timing difference between summing values in a primitive `int[]` versus a boxed `List<Integer>`, and demonstrates the `Integer` caching `==` gotcha directly.

```java
// AutoboxingUnboxingCost.java
import java.util.*;

public class AutoboxingUnboxingCost {

    public static void main(String[] args) {
        int n = 5_000_000;

        // Primitive array: no boxing.
        int[] primitiveArr = new int[n];
        for (int i = 0; i < n; i++) primitiveArr[i] = i;

        long start = System.nanoTime();
        long primitiveSum = 0;
        for (int i = 0; i < n; i++) primitiveSum += primitiveArr[i];
        long primitiveTime = System.nanoTime() - start;

        // Boxed list: every add() autoboxes an int into an Integer.
        List<Integer> boxedList = new ArrayList<>(n);
        for (int i = 0; i < n; i++) boxedList.add(i); // autoboxing happens here

        start = System.nanoTime();
        long boxedSum = 0;
        for (int value : boxedList) boxedSum += value; // unboxing happens here
        long boxedTime = System.nanoTime() - start;

        System.out.println("primitive sum time: " + primitiveTime + "ns");
        System.out.println("boxed sum time: " + boxedTime + "ns");
        System.out.println("primitive sum == boxed sum: " + (primitiveSum == boxedSum));

        // The Integer caching gotcha:
        Integer a = 100, b = 100;
        Integer c = 200, d = 200;
        System.out.println("100==100 (cached): " + (a == b));   // likely true
        System.out.println("200==200 (not cached): " + (c == d)); // likely false
        System.out.println("200.equals(200) (always correct): " + c.equals(d)); // always true
    }
}
```

**How to run:** save as `AutoboxingUnboxingCost.java`, then run `java AutoboxingUnboxingCost.java`.

## 6. Walkthrough

1. `primitiveArr[i] = i;` stores raw `int` values directly and contiguously in the array — no boxing occurs anywhere in this loop.
2. `boxedList.add(i);` triggers autoboxing on every single call: the compiler inserts an implicit `Integer.valueOf(i)` conversion, allocating (or retrieving from cache, for small values) an `Integer` object for each `int` before it can be stored in the generically-typed `List<Integer>`.
3. Summing `boxedList` in the enhanced `for` loop triggers unboxing on every iteration: each `Integer` object is automatically converted back to a primitive `int` before being added to `boxedSum`.
4. Both sums are mathematically identical (`primitiveSum == boxedSum` prints `true`), but the boxed version's timing is typically noticeably slower, reflecting the extra allocation and unboxing overhead on every single element.
5. The `Integer` caching section shows the practical gotcha directly: `a == b` for the cached value `100` is likely `true` (same cached object), while `c == d` for the uncached value `200` is likely `false` (two separately allocated objects) — even though both pairs are logically "equal" by `.equals()`.

## 7. Gotchas & takeaways

> Gotcha: comparing boxed `Integer` values with `==` works "by accident" for small values (due to JVM caching in the range -128 to 127) but silently breaks for larger values — this makes bugs from using `==` on boxed types especially insidious, since code can pass all tests using small sample values and still fail unpredictably in production with larger ones. Always use `.equals()` for boxed-type content comparison.

- Autoboxing/unboxing lets primitives interact with generic APIs, but each conversion allocates (or, for cached small values, retrieves) a heap object — this adds real memory and performance overhead, especially in tight loops or large collections.
- A collection of boxed types (`List<Integer>`) uses substantially more memory than an equivalent primitive array (`int[]`), due to per-element object header overhead and separate heap allocations.
- Related concepts: [Primitives vs references](0010-primitives-vs-references.md) (the underlying distinction autoboxing bridges), [Stack vs heap allocation](0011-stack-vs-heap-allocation.md) (where boxed objects end up living, unlike the primitives they wrap).
