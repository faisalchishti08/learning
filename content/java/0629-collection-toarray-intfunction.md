---
card: java
gi: 629
slug: collection-toarray-intfunction
title: Collection.toArray(IntFunction)
---

## 1. What it is

`Collection.toArray(IntFunction<T[]> generator)` is a Java 11 method that converts a collection to a **typed array** using a generator function (typically an array constructor reference like `String[]::new`). It is the modern, concise replacement for the pre-Java 11 pattern `collection.toArray(new Type[0])`. The `IntFunction<T[]>` parameter is a function that takes an `int` (the collection size) and returns an array of type `T[]` of that size. The method guarantees the returned array is exactly the right size (no trailing nulls) and is safely typed.

## 2. Why & when

Before Java 11, there were two ways to convert a `Collection` to a typed array: `toArray(new Type[0])` (which creates a zero-length array that is discarded — wasteful but idiomatic) and `toArray(new Type[collection.size()])` (which avoids the discard but is more verbose). Both are clunky. `toArray(IntFunction)` — typically written as `toArray(Type[]::new)` — reads fluently as "convert to an array of Type" and uses the collection's known size to allocate a correctly-sized array with no waste. Use it whenever you need to convert a `Collection` to a typed array in Java 11+. The older `toArray(T[])` overloads are not deprecated but `toArray(IntFunction)` is the preferred form.

## 3. Core concept

```java
List<String> names = List.of("Alice", "Bob", "Charlie");

// Java 11+ (preferred):
String[] arr1 = names.toArray(String[]::new);

// Pre-Java 11 (still works):
String[] arr2 = names.toArray(new String[0]);

// Both produce identical results:
System.out.println(Arrays.equals(arr1, arr2));  // true
```

The method uses the generator function to create an array of the correct size, fills it with the collection's elements, and returns it. If the collection is empty, the generator is called with `0` and the returned empty array is returned directly.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toArray(IntFunction) converts a collection to a typed array using a constructor reference">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="130" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="85" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">List&lt;String&gt;</text>
  <text x="85" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">["A", "B", "C"]</text>

  <text x="165" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="185" y="20" width="200" height="50" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="285" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">.toArray(String[]::new)</text>
  <text x="285" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">called with size=3 → new String[3]</text>

  <text x="400" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="420" y="25" width="120" height="40" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="480" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">String[]</text>
  <text x="480" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">["A","B","C"]</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Generator: IntFunction&lt;T[]&gt; — takes int size, returns T[] of that size</text>
  <text x="20" y="118" fill="#3fb950" font-size="9" font-family="sans-serif">Result is exactly sized (no trailing nulls), typed correctly (no cast needed)</text>
</svg>

`toArray(String[]::new)` replaces the verbose `toArray(new String[0])` pattern with a fluent, intention-revealing method reference.

## 5. Runnable example

Scenario: processing a dataset of product records — starting with basic collection-to-array conversion, extending to different collection types and streaming, and finally handling performance considerations and edge cases.

### Level 1 — Basic

```java
// File: ToArrayDemo.java
import java.util.*;

public class ToArrayDemo {
    public static void main(String[] args) {
        List<String> fruits = List.of("Apple", "Banana", "Cherry", "Date");

        // Java 11+: toArray with constructor reference
        String[] fruitArray = fruits.toArray(String[]::new);

        System.out.println("Collection: " + fruits);
        System.out.println("Array:      " + Arrays.toString(fruitArray));
        System.out.println("Array type: " + fruitArray.getClass().getSimpleName());
    }
}
```

**How to run:** `java ToArrayDemo.java`

Expected output:
```
Collection: [Apple, Banana, Cherry, Date]
Array:      [Apple, Banana, Cherry, Date]
Array type: String[]
```

The simplest usage: `collection.toArray(Type[]::new)` converts a `List<String>` to `String[]` in one fluent expression. No casting, no pre-sizing — the constructor reference handles allocation.

### Level 2 — Intermediate

```java
// File: ToArrayStreams.java
import java.util.*;
import java.util.stream.*;

public class ToArrayStreams {
    public static void main(String[] args) {
        List<String> words = List.of("java", "python", "rust", "kotlin", "scala");

        // Filter and convert to array
        String[] longWords = words.stream()
            .filter(w -> w.length() > 4)
            .toArray(String[]::new);

        System.out.println("Long words (>4 chars): " + Arrays.toString(longWords));

        // Map and convert
        Integer[] lengths = words.stream()
            .map(String::length)
            .toArray(Integer[]::new);

        System.out.println("Word lengths: " + Arrays.toString(lengths));

        // Convert a Set
        Set<Integer> uniqueLengths = words.stream()
            .map(String::length)
            .collect(Collectors.toSet());

        Integer[] uniqueArr = uniqueLengths.toArray(Integer[]::new);
        System.out.println("Unique lengths: " + Arrays.toString(uniqueArr));

        // Empty collection
        List<String> empty = List.of();
        String[] emptyArr = empty.toArray(String[]::new);
        System.out.println("\nEmpty list → array: " + Arrays.toString(emptyArr));
        System.out.println("Empty array length: " + emptyArr.length);
    }
}
```

**How to run:** `java ToArrayStreams.java`

Expected output:
```
Long words (>4 chars): [python, kotlin, scala]
Word lengths: [4, 6, 4, 6, 5]
Unique lengths: [4, 5, 6]

Empty list → array: []
Empty array length: 0
```

The real-world concern: stream pipelines. `Stream.toArray(IntFunction)` uses the same generator pattern — `stream.toArray(String[]::new)` — providing a consistent API across the collections framework. The generator handles empty collections correctly (creates a zero-length array).

### Level 3 — Advanced

```java
// File: ToArrayAdvanced.java
import java.util.*;
import java.util.concurrent.*;

public class ToArrayAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Old vs new API comparison ===\n");

        List<Integer> numbers = List.of(1, 2, 3, 4, 5);

        // Old way 1: zero-length array (creates throwaway array)
        Integer[] old1 = numbers.toArray(new Integer[0]);
        System.out.println("Old (new Integer[0]):   " + Arrays.toString(old1));

        // Old way 2: pre-sized array
        Integer[] old2 = numbers.toArray(new Integer[numbers.size()]);
        System.out.println("Old (pre-sized):         " + Arrays.toString(old2));

        // New way: constructor reference
        Integer[] modern = numbers.toArray(Integer[]::new);
        System.out.println("New (Integer[]::new):    " + Arrays.toString(modern));

        System.out.println("\n=== Different collection types ===\n");

        // LinkedList
        LinkedList<String> linked = new LinkedList<>(List.of("X", "Y", "Z"));
        String[] fromLinked = linked.toArray(String[]::new);
        System.out.println("From LinkedList: " + Arrays.toString(fromLinked));

        // CopyOnWriteArrayList
        CopyOnWriteArrayList<String> cowList =
            new CopyOnWriteArrayList<>(List.of("A", "B"));
        String[] fromCow = cowList.toArray(String[]::new);
        System.out.println("From CopyOnWriteArrayList: " + Arrays.toString(fromCow));

        // TreeSet (sorted)
        TreeSet<String> sorted = new TreeSet<>(List.of("Charlie", "Alice", "Bob"));
        String[] fromSorted = sorted.toArray(String[]::new);
        System.out.println("From TreeSet (sorted): " + Arrays.toString(fromSorted));

        System.out.println("\n=== Performance note ===\n");

        // Benchmark: new Integer[0] vs Integer[]::new
        List<Integer> big = new ArrayList<>();
        for (int i = 0; i < 100000; i++) big.add(i);

        long start = System.nanoTime();
        for (int i = 0; i < 1000; i++) big.toArray(new Integer[0]);
        long oldTime = System.nanoTime() - start;

        start = System.nanoTime();
        for (int i = 0; i < 1000; i++) big.toArray(Integer[]::new);
        long newTime = System.nanoTime() - start;

        System.out.printf("new Integer[0]:   %d ms%n", oldTime / 1_000_000);
        System.out.printf("Integer[]::new:   %d ms%n", newTime / 1_000_000);
        System.out.println("(new Integer[0] is optimised in modern JDKs — both are fast)");
    }
}
```

**How to run:** `java ToArrayAdvanced.java`

Expected output (times will vary):
```
=== Old vs new API comparison ===

Old (new Integer[0]):   [1, 2, 3, 4, 5]
Old (pre-sized):         [1, 2, 3, 4, 5]
New (Integer[]::new):    [1, 2, 3, 4, 5]

=== Different collection types ===

From LinkedList: [X, Y, Z]
From CopyOnWriteArrayList: [A, B]
From TreeSet (sorted): [Alice, Bob, Charlie]

=== Performance note ===

new Integer[0]:   ... ms
Integer[]::new:   ... ms
(new Integer[0] is optimised in modern JDKs — both are fast)
```

The production-flavoured hard cases: (1) `toArray(IntFunction)` works uniformly across all `Collection` subtypes — `LinkedList`, `CopyOnWriteArrayList`, `TreeSet` — because it's a default method on the `Collection` interface. (2) The old `new Type[0]` pattern is actually optimised in modern JDKs (HotSpot intrinsics replace the zero-length array allocation), so the performance difference is negligible. The primary benefit of `Type[]::new` is readability and intent. (3) For empty collections, the generator receives `0` and produces a zero-length array — no edge-case handling needed.

## 6. Walkthrough

Tracing `List<String> names = List.of("Alice", "Bob", "Charlie"); String[] arr = names.toArray(String[]::new);`:

1. `List.of(...)` creates an immutable list of three strings.

2. `names.toArray(String[]::new)` is called. This is the `Collection.toArray(IntFunction<T[]>)` default method.

3. The default implementation first asks the collection for its size via `size()`. For our list, this returns `3`.

4. The generator function `String[]::new` (equivalent to `size -> new String[size]`) is invoked with the argument `3`. This allocates `new String[3]` — an array of three `null` elements.

5. The collection's elements are copied into the allocated array in iteration order. After copying, the array contains `["Alice", "Bob", "Charlie"]`.

6. If the collection's size matches the array's length (which it does — both are 3), the array is returned directly. If the collection had fewer elements (unlikely since we used `size()`), the method would return `Arrays.copyOf(array, actualSize)`.

7. The `String[]` is returned to the caller. No element casting is needed — the array is already `String[]`.

## 7. Gotchas & takeaways

> The generator function receives the **collection's reported size**, which may be larger than the actual number of elements for concurrently-modified collections. The method handles this by returning a truncated copy. In practice, this edge case only matters for concurrent collections accessed without proper synchronisation.

- `toArray(IntFunction)` was added as a default method on `Collection` in Java 11, meaning all existing `Collection` implementations automatically get this method without modification.
- The generator is called with `size()` — not the actual iteration count — as the argument. If the collection is modified during the `toArray` call (by another thread), the result is still safe but may be a copy of the correctly-sized portion.
- The method is equivalent to `stream().toArray(IntFunction)` but may be more efficient for collections that can directly copy their internal storage to an array (e.g. `ArrayList`).
- For primitive arrays (`int[]`, `long[]`, `double[]`), use `Stream.toArray(IntFunction)` with primitive streams (`IntStream.toArray()`, `LongStream.toArray()`). `Collection.toArray(IntFunction)` only works with reference types.
- Prefer `collection.toArray(Type[]::new)` over `collection.toArray(new Type[0])` in Java 11+ code for readability. The performance is equivalent.
