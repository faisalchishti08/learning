---
card: data-structures
gi: 15
slug: static-fixed-size-arrays
title: Static (fixed-size) arrays
---

## 1. What it is

A **static array** is a data structure that holds a fixed number of elements of the same type, laid out one after another in memory. Once you create it with a size (`new int[10]`), that size never changes — you cannot add an eleventh element without creating a whole new array. Think of it as a row of numbered lockers bolted to a wall: the number of lockers is fixed the day they are installed.

## 2. Why & when

Static arrays are the right choice when you know the maximum number of elements in advance and want the fastest possible reads and writes by position — for example, a fixed lookup table, a game board, or a buffer of a known size. When the number of elements is unknown or changes often, use a dynamic array (like `ArrayList`) instead, which wraps a static array internally and resizes it for you.

## 3. Core concept

**Invariant: fixed length, contiguous layout.** Every element sits at a predictable memory offset from the start of the array: `address(arr[i]) = base_address + i * element_size`. This invariant never changes for the lifetime of the array, and it is exactly what makes indexed access fast.

**Why the invariant makes access O(1).** Because every element is the same size and packed with no gaps, the JVM computes any element's address with one multiplication and one addition — no searching, no traversal. This holds whether `i` is `0` or `9,999`.

**The cost of the fixed size.** Because the size is baked in at creation, growing the array means allocating a brand-new, larger array and copying every old element into it. A static array by itself has no built-in growth mechanism; that logic belongs to a dynamic array built on top of it.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fixed-size array of 6 slots, each at a predictable offset from the base address">
  <g font-family="sans-serif" font-size="12">
    <text x="310" y="20" fill="#8b949e" text-anchor="middle">int[] arr = new int[6]  (fixed size, never grows)</text>
    <g>
      <rect x="30" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="70" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">10</text>
      <rect x="110" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="150" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">20</text>
      <rect x="190" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="230" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">30</text>
      <rect x="270" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="310" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">40</text>
      <rect x="350" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="390" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">50</text>
      <rect x="430" y="40" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="470" y="62" fill="#e6edf3" text-anchor="middle" font-size="11">60</text>
    </g>
    <text x="70" y="90" fill="#8b949e" text-anchor="middle" font-size="10">index 0</text>
    <text x="230" y="90" fill="#8b949e" text-anchor="middle" font-size="10">index 2</text>
    <text x="470" y="90" fill="#8b949e" text-anchor="middle" font-size="10">index 5</text>
    <text x="310" y="130" fill="#79c0ff" text-anchor="middle">address(arr[i]) = base + i * 4 bytes — no 7th slot can ever be added</text>
  </g>
</svg>

Six slots, packed with no gaps. Each slot's address is computed directly from its index, and there is no room to grow the array in place.

## 5. Runnable example

```java
// StaticFixedArray.java
import java.util.Arrays;

public class StaticFixedArray {

    // Basic: create and read a fixed-size array.
    static void basicLevel() {
        int[] scores = new int[5]; // fixed at 5 slots forever
        scores[0] = 90;
        scores[4] = 75;
        System.out.println("basic: scores -> " + Arrays.toString(scores));
        System.out.println("basic: fixed length -> " + scores.length);
    }

    // Intermediate: attempting to go past the fixed bound fails at runtime.
    static void intermediateLevel() {
        int[] fixed = {1, 2, 3};
        try {
            fixed[3] = 4; // no 4th slot exists
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("intermediate: caught -> " + e.getMessage());
        }
    }

    // Advanced: "growing" a static array really means allocating a new, bigger one and copying.
    static int[] grow(int[] original, int newSize) {
        int[] bigger = new int[newSize];      // brand-new fixed array
        System.arraycopy(original, 0, bigger, 0, original.length); // copy every old element
        return bigger;
    }

    static void advancedLevel() {
        int[] small = {1, 2, 3};
        int[] bigger = grow(small, 6);
        System.out.println("advanced: original untouched -> " + Arrays.toString(small));
        System.out.println("advanced: bigger copy -> " + Arrays.toString(bigger));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StaticFixedArray.java`, then run `java StaticFixedArray.java`.

## 6. Walkthrough

1. `basicLevel()` creates `scores` with exactly 5 slots. Writing `scores[0]` and `scores[4]` succeeds because both indexes fall inside the fixed bound `0..4`.
2. `scores.length` reads the stored `length` field instantly — the size was fixed the moment `new int[5]` ran.
3. `intermediateLevel()` tries `fixed[3] = 4` on a 3-element array. There is no slot 3, so the JVM throws `ArrayIndexOutOfBoundsException` at runtime — the fixed size is enforced, not just a suggestion.
4. `advancedLevel()` shows the only way to "grow" a static array: `grow()` allocates an entirely new array of the target size, then `System.arraycopy` copies every element from the old array into the new one.
5. The original `small` array is untouched by `grow()` — it still has 3 slots. `bigger` is a separate object with 6 slots, the first 3 holding the copied values and the rest defaulting to `0`.

## 7. Gotchas & takeaways

> Gotcha: there is no `resize()` method on a Java array, and no way to append past its fixed length. Any "growth" always means allocating a new array and copying — this copy is exactly the O(n) cost that a dynamic array like `ArrayList` hides behind its `add()` method.

- A static array's size is fixed at creation and never changes for its lifetime.
- Fixed size plus contiguous layout is what gives O(1) indexed access — the tradeoff is no built-in growth.
- Going past the bound throws `ArrayIndexOutOfBoundsException` at runtime, not a compile error.
- Related concepts: [Array resizing & amortized append](0020-array-resizing-amortized-append.md) (how dynamic arrays build growth on top of this), [Amortized analysis](0004-amortized-analysis-dynamic-array-doubling.md).
