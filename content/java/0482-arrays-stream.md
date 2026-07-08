---
card: java
gi: 482
slug: arrays-stream
title: Arrays.stream()
---

## 1. What it is

`Arrays.stream(array)` is a `static` factory method that produces a `Stream` view over an array's elements — the array equivalent of `Collection.stream()`, for the many cases where your data lives in a plain Java array rather than a `List` or `Set`. It's overloaded to return the appropriate stream type for the array's element type: `Arrays.stream(int[])` returns an `IntStream`, `Arrays.stream(double[])` returns a `DoubleStream`, and `Arrays.stream(T[])` (any reference type) returns a `Stream<T>`.

## 2. Why & when

Arrays predate the Stream API by two decades and, unlike `Collection`, don't have a `.stream()` instance method of their own — arrays in Java are a low-level language construct, not objects with methods you can add to via a `default` method the way `Collection` could be extended. `Arrays.stream(array)` bridges that gap: it's the standard way to bring an array's contents into the same declarative pipeline style (`filter`, `map`, `collect`, and the rest) that `Collection.stream()` offers for actual collections.

You reach for `Arrays.stream(array)` any time your data starts life as a plain array — the result of `String.split()`, a fixed-size numeric buffer, data read from a legacy API that returns arrays — and you want to process it with stream operations rather than a manual loop. For primitive arrays (`int[]`, `long[]`, `double[]`), it also has the benefit of returning the primitive-specialized stream type directly, avoiding the boxing a `Stream<Integer>` conversion would otherwise require.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

int[] numbers = {5, 3, 8, 1, 9};
IntStream intStream = Arrays.stream(numbers); // primitive IntStream -- no boxing
int sum = Arrays.stream(numbers).sum();        // 26

String[] words = {"banana", "apple", "cherry"};
Stream<String> wordStream = Arrays.stream(words); // Stream<String> for reference types
List<String> sorted = Arrays.stream(words).sorted().collect(Collectors.toList());

// A partial range: only elements from index 1 (inclusive) to 4 (exclusive)
int[] partial = Arrays.stream(numbers, 1, 4).toArray(); // {3, 8, 1}
```

`Arrays.stream` is overloaded per element type — the compiler picks the right overload based on the array's declared type, returning `IntStream`/`LongStream`/`DoubleStream` for the matching primitive array type, or `Stream<T>` for any reference type array.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arrays.stream produces the appropriately typed stream depending on the array's element type -- IntStream for int arrays, Stream of T for reference type arrays">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="110" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">int[] numbers</text>
  <text x="230" y="52" fill="#8b949e" font-size="12" font-family="sans-serif">-&gt;</text>
  <rect x="260" y="30" width="180" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="350" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">IntStream</text>

  <rect x="20" y="85" width="180" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="110" y="107" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">String[] words</text>
  <text x="230" y="107" fill="#8b949e" font-size="12" font-family="sans-serif">-&gt;</text>
  <rect x="260" y="85" width="180" height="34" rx="4" fill="#1c2430" stroke="#f0883e"/><text x="350" y="107" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">Stream&lt;String&gt;</text>
</svg>

The overload selected — and therefore the stream type returned — follows directly from the array's own element type.

## 5. Runnable example

Scenario: processing sensor readings that arrive as a primitive array — evolved from `Arrays.stream` on an `int[]` computing basic statistics, through streaming a `String[]` of labels alongside the numeric data, to `Arrays.stream` with a range to process only a sliding window of the full array.

### Level 1 — Basic

```java
import java.util.*;

public class ArraysStreamBasic {
    public static void main(String[] args) {
        int[] readings = { 42, 58, 39, 71, 65, 33 };

        int sum = Arrays.stream(readings).sum();
        double average = Arrays.stream(readings).average().orElse(0);
        int max = Arrays.stream(readings).max().orElse(0);

        System.out.println("Sum: " + sum);
        System.out.println("Average: " + average);
        System.out.println("Max: " + max);
    }
}
```

**How to run:** `java ArraysStreamBasic.java`

Expected output:
```
Sum: 308
Average: 51.333333333333336
Max: 71
```

`Arrays.stream(readings)` returns an `IntStream`, giving direct access to primitive numeric aggregations like `sum()`, `average()` (returning `OptionalDouble`, hence `.orElse(0)`), and `max()` (returning `OptionalInt`) — no boxing to `Integer` happens anywhere in this pipeline. Each of the three calls creates a fresh stream from the same array, since a stream can only be consumed once.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ArraysStreamReferenceType {
    public static void main(String[] args) {
        String[] labels = { "sensorA", "sensorB", "sensorC" };
        int[] readings = { 42, 58, 39 };

        // Arrays.stream on a reference-type array returns Stream<T> -- combine with IntStream.range
        // for indexed access when two parallel arrays need to be processed together.
        List<String> report = IntStream.range(0, labels.length)
                .mapToObj(i -> labels[i] + ": " + readings[i])
                .collect(Collectors.toList());

        report.forEach(System.out::println);

        long countAboveAverage = Arrays.stream(readings)
                .filter(reading -> reading > Arrays.stream(readings).average().orElse(0))
                .count();
        System.out.println("Readings above average: " + countAboveAverage);
    }
}
```

**How to run:** `java ArraysStreamReferenceType.java`

Expected output:
```
sensorA: 42
sensorB: 58
sensorC: 39
Readings above average: 1
```

The real-world concern this adds: two parallel arrays (`labels` and `readings`) need to be processed together, index by index — `IntStream.range(0, labels.length).mapToObj(...)` generates the indices and looks up both arrays at each index, since `Arrays.stream` alone streams only one array's contents at a time, with no built-in way to zip two separate arrays together.

### Level 3 — Advanced

```java
import java.util.*;

public class ArraysStreamRange {
    public static void main(String[] args) {
        int[] readings = { 42, 58, 39, 71, 65, 33, 80, 12 };
        int windowSize = 3;

        // Arrays.stream(array, from, to) streams only a SUB-RANGE -- used here to compute
        // a simple moving average over a sliding window across the full array.
        System.out.println("Moving averages (window=" + windowSize + "):");
        for (int start = 0; start <= readings.length - windowSize; start++) {
            double windowAverage = Arrays.stream(readings, start, start + windowSize)
                    .average()
                    .orElse(0);
            System.out.println("  window[" + start + ".." + (start + windowSize - 1) + "] = " + windowAverage);
        }
    }
}
```

**How to run:** `java ArraysStreamRange.java`

Expected output:
```
Moving averages (window=3):
  window[0..2] = 46.333333333333336
  window[1..3] = 56.0
  window[2..4] = 58.333333333333336
  window[3..5] = 56.333333333333336
  window[4..6] = 59.333333333333336
  window[5..7] = 41.666666666666664
```

`Arrays.stream(array, from, to)` — the three-argument overload — streams only the elements from index `from` (inclusive) to `to` (exclusive), without needing to manually copy that sub-range into a new array first. Here, it computes a **moving average**: sliding a fixed-size window across the array and averaging just the elements inside that window at each position.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `readings` holds eight integers: `42, 58, 39, 71, 65, 33, 80, 12`. `windowSize` is `3`.

The `for` loop runs `start` from `0` up to `readings.length - windowSize = 8 - 3 = 5`, so `start` takes the values `0, 1, 2, 3, 4, 5` — six iterations, one for each valid window position.

For `start = 0`: `Arrays.stream(readings, 0, 3)` streams indices `0, 1, 2` — values `42, 58, 39`. `.average()` computes `(42 + 58 + 39) / 3.0 = 139 / 3.0 ≈ 46.333...`. This is printed as the first window's average.

For `start = 1`: `Arrays.stream(readings, 1, 4)` streams indices `1, 2, 3` — values `58, 39, 71`. Average: `(58 + 39 + 71) / 3.0 = 168 / 3.0 = 56.0`.

```
window[0..2]: 42, 58, 39  --> avg 46.33
window[1..3]: 58, 39, 71  --> avg 56.0
window[2..4]: 39, 71, 65  --> avg 58.33
window[3..5]: 71, 65, 33  --> avg 56.33
window[4..6]: 65, 33, 80  --> avg 59.33
window[5..7]: 33, 80, 12  --> avg 41.67
```

This pattern continues for `start = 2` through `start = 5`, each time streaming a fresh three-element slice of `readings` starting at the current position and computing its average — the window "slides" one position to the right on each loop iteration, and the range-based `Arrays.stream` overload makes this possible without ever constructing an intermediate copied sub-array.

## 7. Gotchas & takeaways

> `Arrays.stream(array)` does **not** copy the array — the returned stream reads directly from the original array's backing storage. If the array is mutated while a stream over it is still being consumed (an unusual but possible scenario, especially with concurrent access), the stream's behavior becomes unpredictable. In normal, single-threaded, non-mutating usage this is a non-issue and, in fact, a performance benefit (no copying overhead) — but it's worth knowing the stream is a live view, not an independent snapshot.

- `Arrays.stream(array)` is the array equivalent of `Collection.stream()` — arrays lack their own `.stream()` method since they predate the Stream API and aren't ordinary objects with `default` methods.
- It's overloaded per array element type: `int[]`/`long[]`/`double[]` arrays produce the matching primitive stream (`IntStream`/`LongStream`/`DoubleStream`), avoiding boxing; any reference-type array `T[]` produces `Stream<T>`.
- The three-argument overload, `Arrays.stream(array, from, to)`, streams only a sub-range of the array without needing to manually copy that range out first.
- Combine `IntStream.range(0, n)` with `Arrays.stream`-style index lookups when you need to process two or more parallel arrays together by index, since streaming a single array alone has no built-in way to "zip" with another.
- The returned stream is a live view over the array's current contents, not a defensive copy — safe and efficient in typical single-threaded use, but worth remembering if the array might be mutated concurrently.
