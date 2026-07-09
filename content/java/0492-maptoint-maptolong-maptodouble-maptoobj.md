---
card: java
gi: 492
slug: maptoint-maptolong-maptodouble-maptoobj
title: mapToInt / mapToLong / mapToDouble / mapToObj
---

## 1. What it is

`mapToInt`, `mapToLong`, and `mapToDouble` convert a `Stream<T>` into a primitive `IntStream`, `LongStream`, or `DoubleStream` respectively, by applying a function that returns the corresponding primitive. `mapToObj` goes the other direction: it converts a primitive stream (`IntStream`, `LongStream`, `DoubleStream`) back into a `Stream<T>` of objects. Together, these four methods are the bridges between the object-based `Stream<T>` API and the primitive-specialized stream types.

## 2. Why & when

Java's generics can't work with primitives directly — a `Stream<Integer>` boxes every `int` into an `Integer` object, which costs memory and CPU for large streams of numeric data. `IntStream`, `LongStream`, and `DoubleStream` exist specifically to avoid that boxing, and they come with numeric-only methods (`sum()`, `average()`, `max()`) that a plain `Stream<Integer>` doesn't have. `mapToInt`/`mapToLong`/`mapToDouble` are how you *enter* that unboxed world from a stream of objects (e.g. extracting a numeric field), and `mapToObj` is how you *leave* it, converting numbers back into richer objects.

You reach for `mapToInt` (and friends) right before you need numeric aggregation (`sum`, `average`, statistics) on a field extracted from a stream of objects. You reach for `mapToObj` when you have a primitive stream (often from `IntStream.range`) and need to turn each number into something else — an object, a formatted string, a lookup result.

## 3. Core concept

```java
import java.util.stream.*;

record Order(String id, int amount) {}

List<Order> orders = List.of(new Order("A", 10), new Order("B", 20));

int total = orders.stream()
        .mapToInt(Order::amount) // Stream<Order> -> IntStream
        .sum(); // 30 -- sum() only exists on IntStream, not Stream<Integer>

Stream<String> labels = IntStream.range(0, 3)
        .mapToObj(i -> "item-" + i); // IntStream -> Stream<String>: "item-0", "item-1", "item-2"
```

`mapToInt`/`mapToLong`/`mapToDouble` unbox into primitive streams to unlock numeric methods; `mapToObj` boxes back into objects when you need to work with something richer than a number.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="mapToInt converts Stream of T to IntStream; mapToObj converts IntStream back to Stream of T">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="40" y="25" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="50" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Stream&lt;Order&gt;</text>
  <line x1="200" y1="45" x2="320" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowMI)"/>
  <text x="260" y="35" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">mapToInt</text>
  <rect x="330" y="25" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="395" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IntStream</text>

  <rect x="330" y="90" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="395" y="115" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IntStream</text>
  <line x1="330" y1="110" x2="210" y2="110" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrowMI2)"/>
  <text x="270" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">mapToObj</text>
  <rect x="40" y="90" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="115" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Stream&lt;String&gt;</text>

  <defs>
    <marker id="arrowMI" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrowMI2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`mapToInt` unboxes objects into a primitive stream; `mapToObj` boxes a primitive stream back into objects — the two directions of the same bridge.

## 5. Runnable example

Scenario: computing order statistics for a small e-commerce report — evolved from a basic sum via `mapToInt`, through full numeric statistics with `summaryStatistics()`, to a version that uses `mapToObj` to turn a generated range of bucket indices into a formatted histogram.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class MapToIntBasic {
    record Order(String id, int amountCents) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("A", 1099),
                new Order("B", 2500),
                new Order("C", 799)
        );

        int totalCents = orders.stream()
                .mapToInt(Order::amountCents)
                .sum();

        System.out.println("Total: $" + (totalCents / 100.0));
    }
}
```

**How to run:** `java MapToIntBasic.java`

Expected output:
```
Total: $43.98
```

`.mapToInt(Order::amountCents)` converts the `Stream<Order>` into an `IntStream` of the raw `amountCents` values (`1099, 2500, 799`) — no boxing to `Integer` involved. `.sum()`, a method that only exists on `IntStream` (not on `Stream<Integer>`), adds them directly: `4398` cents, displayed as `$43.98`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class MapToIntStatistics {
    record Order(String id, int amountCents) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("A", 1099),
                new Order("B", 2500),
                new Order("C", 799),
                new Order("D", 4200)
        );

        IntSummaryStatistics stats = orders.stream()
                .mapToInt(Order::amountCents)
                .summaryStatistics();

        System.out.println("Count: " + stats.getCount());
        System.out.println("Min: " + stats.getMin());
        System.out.println("Max: " + stats.getMax());
        System.out.printf("Average: %.2f%n", stats.getAverage());
    }
}
```

**How to run:** `java MapToIntStatistics.java`

Expected output:
```
Count: 4
Min: 799
Max: 4200
Average: 2149.50
```

The real-world concern this adds: instead of just one aggregate (`sum`), the full picture — count, min, max, average — is needed at once. `summaryStatistics()`, available only on the primitive stream types, computes all four in a single pass and returns them bundled in an `IntSummaryStatistics` object, avoiding four separate passes over the same data.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class MapToObjHistogram {
    record Order(String id, int amountCents) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("A", 1099), new Order("B", 2500), new Order("C", 799),
                new Order("D", 4200), new Order("E", 3100), new Order("F", 1850)
        );

        int bucketWidth = 1000; // cents
        int numBuckets = 5;

        int[] counts = new int[numBuckets];
        orders.stream()
                .mapToInt(Order::amountCents)
                .map(cents -> Math.min(cents / bucketWidth, numBuckets - 1)) // still an IntStream -- clamp to last bucket
                .forEach(bucket -> counts[bucket]++);

        // Turn the bucket indices 0..numBuckets into formatted histogram lines via mapToObj.
        IntStream.range(0, numBuckets)
                .mapToObj(i -> "$" + i + "0-" + (i + 1) + "0: " + "*".repeat(counts[i]))
                .forEach(System.out::println);
    }
}
```

**How to run:** `java MapToObjHistogram.java`

Expected output:
```
$00-10: *
$10-20: **
$20-30: *
$30-40: *
$40-50: *
```

This uses `mapToObj` to close the loop: `IntStream.range(0, numBuckets)` (see [[intstream-range-rangeclosed]]) generates plain bucket indices `0..4`, and `.mapToObj(i -> ...)` converts each index into a formatted `String` label with a bar of asterisks — turning primitive numbers back into display-ready objects, the opposite direction from the `mapToInt` calls used to build the histogram data itself.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Six orders are defined with various `amountCents` values; `bucketWidth` is `1000` cents (`$10`), and there are `5` buckets.

`orders.stream().mapToInt(Order::amountCents)` converts the six `Order` objects into a primitive `IntStream` of `1099, 2500, 799, 4200, 3100, 1850`.

`.map(cents -> Math.min(cents / bucketWidth, numBuckets - 1))` (this `map` is `IntStream.map`, which takes an `IntUnaryOperator` and stays within `IntStream` — distinct from `Stream.map`) computes each order's bucket index: `1099 / 1000 = 1`, `2500 / 1000 = 2`, `799 / 1000 = 0`, `4200 / 1000 = 4`, `3100 / 1000 = 3`, `1850 / 1000 = 1`. `Math.min(..., 4)` clamps any bucket that would exceed index `4` (not needed here, since none reach `5`).

`.forEach(bucket -> counts[bucket]++)` increments the `counts` array at each computed bucket index: bucket `1` (from `1099`) makes `counts[1] = 1`; bucket `2` (from `2500`) makes `counts[2] = 1`; bucket `0` (from `799`) makes `counts[0] = 1`; bucket `4` (from `4200`) makes `counts[4] = 1`; bucket `3` (from `3100`) makes `counts[3] = 1`; bucket `1` again (from `1850`) makes `counts[1] = 2`.

```
1099 -> bucket 1        2500 -> bucket 2        799  -> bucket 0
4200 -> bucket 4        3100 -> bucket 3        1850 -> bucket 1

Final counts: [1, 2, 1, 1, 1]   (index = bucket 0..4)
```

Bucket `0` receives one order (`799`), bucket `1` receives two (`1099` and `1850`), and buckets `2`, `3`, `4` each receive exactly one (`2500`, `3100`, `4200` respectively) — so `counts` ends up as `[1, 2, 1, 1, 1]`.

`IntStream.range(0, numBuckets)` then generates `0, 1, 2, 3, 4`. `.mapToObj(i -> "$" + i + "0-" + (i + 1) + "0: " + "*".repeat(counts[i]))` converts each index into a label: for `i=0`, `"$00-10: " + "*".repeat(counts[0]=1)` = `"$00-10: *"`; for `i=1`, `"$10-20: " + "*".repeat(counts[1]=2)` = `"$10-20: **"`; for `i=2`, `"$20-30: " + "*".repeat(1)` = `"$20-30: *"`; and likewise `"$30-40: *"` and `"$40-50: *"` for buckets `3` and `4`. `.forEach(System.out::println)` prints all five formatted lines in bucket order, matching the two-order bucket (`$10-20`) with the only line carrying two asterisks.

## 7. Gotchas & takeaways

> Calling `.sum()`, `.average()`, or `.summaryStatistics()` directly on a `Stream<Integer>` won't compile — those methods exist only on the primitive stream types (`IntStream`, `LongStream`, `DoubleStream`). You must first convert with `mapToInt`/`mapToLong`/`mapToDouble` before those aggregation methods become available.

- `mapToInt`/`mapToLong`/`mapToDouble` convert `Stream<T>` into the corresponding primitive stream, unlocking numeric-only operations (`sum`, `average`, `summaryStatistics`) and avoiding boxing overhead.
- `mapToObj` converts a primitive stream back into a `Stream<T>` — the reverse bridge, used when a primitive result needs to become a richer object or formatted `String`.
- `IntStream` (and `LongStream`/`DoubleStream`) has its own `map(IntUnaryOperator)` that stays within the primitive stream, distinct from `Stream.map(Function)` which can change type.
- `summaryStatistics()` computes count, min, max, sum, and average in a single pass — far more efficient than calling four separate terminal operations on four separate stream pipelines.
- `IntStream.range(...).mapToObj(...)` is a common pattern for generating a sequence of formatted, index-derived objects or strings — pairing range generation ([[intstream-range-rangeclosed]]) with the bridge back to object streams.
