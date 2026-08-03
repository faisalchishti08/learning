---
card: data-structures
gi: 189
slug: arrays-aslist-list-of-factory-methods
title: Arrays.asList & List.of factory methods
---

## 1. What it is

`Arrays.asList(...)` and `List.of(...)` are both quick ways to build a `List` from a fixed set of values, but they produce meaningfully different objects. `Arrays.asList` returns a **fixed-size** list backed directly by an array. `List.of` (Java 9+) returns a **truly immutable** list, unconnected to any array you can still reach.

## 2. Why & when

Reach for `List.of` in modern Java (9+) for the common case: a small, fixed, read-only list, especially for constants or test data. Reach for `Arrays.asList` specifically when you need a `List` view over an **existing array** that you want to keep able to modify through the array reference, or when you need a list that allows `set()` but not `add()`/`remove()` (a genuinely useful, if unusual, middle ground). Knowing exactly which operations each supports avoids a common class of runtime surprises.

## 3. Core concept

**What `Arrays.asList` actually returns.** Not a `java.util.ArrayList` — it returns a private inner class, `Arrays.ArrayList`, that wraps the array passed to it directly, with no copy. This wrapper supports `set(index, value)` (which writes straight through to the backing array) but throws `UnsupportedOperationException` for `add()` and `remove()`, since those would need to resize the backing array, which `Arrays.asList`'s wrapper does not support.

**Why `Arrays.asList` is "fixed-size," not "immutable."** "Fixed-size" means the list's length cannot change (no `add`/`remove`), but its **contents** can — via `set()`, or via directly mutating the original array, since the list is a live view over it. This is a distinct, weaker guarantee than `List.of`'s full immutability.

**What `List.of` actually returns.** A genuinely immutable implementation, backed by a private array **copied** from the arguments — there is no way to reach or mutate that backing array from outside. Every mutating method (`add`, `remove`, `set`) throws `UnsupportedOperationException`. `List.of` also rejects `null` elements outright, which `Arrays.asList` does not.

**The varargs pitfall shared by both.** Calling `Arrays.asList(intArray)` with a primitive `int[]` (not `Integer[]`) does **not** produce a `List<Integer>` of the array's elements — because `int[]` cannot be auto-boxed into `Integer[]`, Java treats the whole array as a single varargs argument, producing a `List<int[]>` with exactly one element: the array itself. `List.of` avoids the ambiguity for this specific case, but the general lesson (mind autoboxing with varargs and arrays) applies to both.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arrays.asList wrapping an array directly, allowing set() to write through, versus List.of copying data into a fully independent immutable structure">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Arrays.asList(array):</text>
    <rect x="20" y="30" width="140" height="30" fill="#161b22" stroke="#f0883e"/><text x="90" y="50" text-anchor="middle" font-size="9">Integer[] array</text>
    <rect x="220" y="30" width="140" height="30" fill="#0d1117" stroke="#f0883e"/><text x="290" y="50" text-anchor="middle" font-size="9">List view (set() OK)</text>
    <line x1="160" y1="45" x2="220" y2="45" stroke="#f0883e"/>
    <text x="20" y="80" font-size="9" fill="#f0883e">array[0] = 99 -&gt; list also shows 99 (same backing storage)</text>
    <text x="20" y="100" font-size="9" fill="#f0883e">list.add(x) -&gt; throws (fixed size, no resize support)</text>

    <text x="10" y="140">List.of(1, 2, 3):</text>
    <rect x="20" y="150" width="200" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="170" text-anchor="middle" font-size="9">independent copy, fully immutable</text>
    <text x="20" y="190" font-size="9" fill="#3fb950">no array reference exists to mutate it through</text>
  </g>
</svg>

`Arrays.asList` is a live, fixed-size window onto an array; `List.of` owns an independent, frozen copy.

## 5. Runnable example

```java
// ArraysAsListVsListOf.java
import java.util.*;

public class ArraysAsListVsListOf {

    // Basic: Arrays.asList allows set() but not add()/remove(); List.of allows neither.
    static void basicLevel() {
        List<String> fixedSize = Arrays.asList("a", "b", "c");
        fixedSize.set(0, "A"); // allowed: writes through to the backing array
        System.out.println("basic: Arrays.asList after set() -> " + fixedSize);

        try {
            fixedSize.add("d");
        } catch (UnsupportedOperationException e) {
            System.out.println("basic: Arrays.asList blocks add() -> " + e.getClass().getSimpleName());
        }

        List<String> trueImmutable = List.of("a", "b", "c");
        try {
            trueImmutable.set(0, "A");
        } catch (UnsupportedOperationException e) {
            System.out.println("basic: List.of blocks set() too -> " + e.getClass().getSimpleName());
        }
    }

    // Intermediate: Arrays.asList is a live VIEW over the original array -- mutating the array changes the list.
    static void intermediateLevel() {
        String[] array = {"x", "y", "z"};
        List<String> view = Arrays.asList(array);

        array[1] = "Y"; // mutate the array directly
        System.out.println("intermediate: list reflects the array mutation -> " + view);

        view.set(2, "Z"); // mutate through the list
        System.out.println("intermediate: array reflects the list mutation -> " + Arrays.toString(array));
    }

    // Advanced: the primitive-array varargs pitfall with Arrays.asList.
    static void advancedLevel() {
        int[] primitiveArray = {1, 2, 3};
        List<int[]> wrongList = Arrays.asList(primitiveArray); // NOT List<Integer> -- one element: the whole array
        System.out.println("advanced: Arrays.asList(int[]) size (expect 1, not 3) -> " + wrongList.size());

        Integer[] boxedArray = {1, 2, 3};
        List<Integer> rightList = Arrays.asList(boxedArray); // correctly List<Integer> with 3 elements
        System.out.println("advanced: Arrays.asList(Integer[]) size (expect 3) -> " + rightList.size());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ArraysAsListVsListOf.java`

## 6. Walkthrough

`Arrays.asList("a", "b", "c")` creates a fixed-size wrapper. Calling `.set(0, "A")` succeeds, changing the underlying array in place — the list becomes `["A", "b", "c"]`. Calling `.add("d")` throws `UnsupportedOperationException`, because the wrapper has no mechanism to grow the fixed-length array backing it. `List.of("a", "b", "c")`, by contrast, blocks `.set(0, "A")` too — its immutability is total, not just "fixed length."

For the live-view behavior: create `String[] array = {"x", "y", "z"}` and wrap it with `Arrays.asList(array)`. Mutating `array[1] = "Y"` directly changes what the list reports, since the list holds no separate copy — printing the list shows `[x, Y, z]`. Going the other direction, calling `view.set(2, "Z")` writes through to the array itself — printing the array afterward shows `[x, Y, Z]`. Both directions of this connection are a direct consequence of `Arrays.asList` never copying data.

For the varargs pitfall: `Arrays.asList(primitiveArray)` where `primitiveArray` is `int[]` cannot autobox to `Integer[]` (Java has no direct `int` to `Integer[]` conversion), so the compiler instead treats the single `int[]` argument as the **one** varargs element — producing `List<int[]>` with `size() == 1`, not the expected `List<Integer>` with 3 elements. Using `Integer[]` instead avoids this trap entirely, since `Integer[]` matches the varargs `T...` parameter type directly.

**Complexity.** Both `Arrays.asList` and `List.of`: `O(1)` for `Arrays.asList` (no copy, just wraps), `O(n)` for `List.of` (must copy into its own private backing array). Both give `O(1)` element access afterward.

## 7. Gotchas & takeaways

> The `int[]` varargs pitfall is a real, easy-to-hit bug — always double check that you are passing a boxed array type (`Integer[]`, `Long[]`, etc.) to `Arrays.asList` when working with what should be a list of numbers, or use `IntStream.of(primitiveArray).boxed().toList()` to convert a primitive array correctly.

- `Arrays.asList` is the correct tool specifically when you want a `List` that stays connected to a specific array — this is genuinely useful for adapting legacy array-based APIs to `List`-based code without copying.
- `new ArrayList<>(Arrays.asList(...))` is a common idiom to get a **fully mutable, independent** list from a small set of literal values — it copies `Arrays.asList`'s fixed-size wrapper into a real `ArrayList`, gaining `add`/`remove` support.
- For anything meant to be a read-only constant or a small literal collection in modern code, prefer `List.of(...)` — it is safer (no accidental array-mutation surprises) and communicates intent more clearly than `Arrays.asList(...)`.
