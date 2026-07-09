---
card: java
gi: 527
slug: stream-cannot-be-reused
title: Stream cannot be reused
---

## 1. What it is

A Java `Stream` is **single-use**: once a terminal operation has run on it (`forEach`, `collect`, `count`, `findFirst`, and so on), that stream instance is considered *consumed*, and any further attempt to use it — even just building a new pipeline off of it, without calling another terminal operation — throws `IllegalStateException: stream has already been operated upon or closed`. This is different from a `Collection`, which can be iterated over as many times as you like.

## 2. Why & when

Streams model a single pipeline of computation over a data source, not a reusable data structure — the stream itself holds no elements; it's a description of how to process elements pulled from some underlying source (a `Collection`, an array, a generator function). Once that pipeline has been driven to completion by a terminal operation, there's nothing left to "run again" — the stream's internal state reflects that it has already been traversed. Understanding this is essential for writing correct code: any time you need to process the same data in two different ways (two different counts, a count *and* a collected list), you need two separate stream instances, typically by calling `.stream()` again on the same source collection.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = List.of(1, 2, 3, 4, 5);

Stream<Integer> stream = numbers.stream();
long count = stream.count(); // terminal operation -- consumes the stream

// stream.forEach(System.out::println); // would throw IllegalStateException here

// Correct: get a FRESH stream from the source for each new pipeline
long evenCount = numbers.stream().filter(n -> n % 2 == 0).count();
List<Integer> doubled = numbers.stream().map(n -> n * 2).toList();
```

Each `.stream()` call on a `Collection` produces a brand-new, independent `Stream` instance — the `Collection` itself is reusable, but each individual stream built from it is not.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a terminal operation consumes a stream; a second terminal operation on the same instance throws">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Stream instance</text>
  <line x1="170" y1="35" x2="270" y2="35" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowSR)"/>
  <text x="220" y="25" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">.count()</text>
  <rect x="280" y="20" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="325" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">result</text>
  <line x1="100" y1="50" x2="100" y2="90" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrowSR2)"/>
  <text x="180" y="105" fill="#f85149" font-size="11" font-family="sans-serif">.forEach(...) again -&gt; IllegalStateException</text>
  <defs>
    <marker id="arrowSR" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrowSR2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Once `.count()` (a terminal operation) has run on this stream instance, any further operation on the *same* instance throws — a fresh stream is needed for further processing.

## 5. Runnable example

Scenario: computing several different reports from the same order data — evolved from triggering the reuse exception directly, through the correct fix using fresh streams per computation, to a version that extracts a reusable `Supplier<Stream<T>>` pattern for cleanly running multiple pipelines over the same source.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ReuseException {
    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 120, 30, 200, 75);

        Stream<Integer> stream = orderAmounts.stream();
        long count = stream.count();
        System.out.println("Count: " + count);

        try {
            long sum = stream.mapToInt(Integer::intValue).sum(); // reusing the SAME stream instance
            System.out.println("Sum: " + sum);
        } catch (IllegalStateException e) {
            System.out.println("Failed as expected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ReuseException.java`

Expected output:
```
Count: 5
Failed as expected: stream has already been operated upon or closed
```

`.count()` is a terminal operation, and once it runs on `stream`, that specific instance is consumed. Attempting to call `.mapToInt(...)` on the *same* `stream` variable afterward throws `IllegalStateException`, exactly as documented — the stream cannot be "rewound" or reused, regardless of what operation is attempted next.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ReuseFixed {
    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 120, 30, 200, 75);

        // Correct: call .stream() again to get a fresh instance for each independent computation.
        long count = orderAmounts.stream().count();
        int sum = orderAmounts.stream().mapToInt(Integer::intValue).sum();
        OptionalInt max = orderAmounts.stream().mapToInt(Integer::intValue).max();

        System.out.println("Count: " + count);
        System.out.println("Sum: " + sum);
        System.out.println("Max: " + max.orElse(0));
    }
}
```

**How to run:** `java ReuseFixed.java`

Expected output:
```
Count: 5
Sum: 475
Max: 200
```

The real-world concern this adds: three separate, independent computations over the same `orderAmounts` list, each needing its own fresh `Stream` instance via a separate `.stream()` call on the underlying `List` — the `List` itself is perfectly reusable (that's what makes `.stream()` callable multiple times on it), even though no single `Stream` instance built from it can be reused.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class ReuseWithSupplier {
    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 120, 30, 200, 75);

        // A Supplier<Stream<T>> defers stream creation -- calling .get() produces a FRESH stream each time.
        Supplier<Stream<Integer>> streamSupplier = orderAmounts::stream;

        long count = streamSupplier.get().count();
        int sum = streamSupplier.get().mapToInt(Integer::intValue).sum();
        List<Integer> largeOrders = streamSupplier.get().filter(a -> a > 100).toList();

        System.out.println("Count: " + count);
        System.out.println("Sum: " + sum);
        System.out.println("Large orders (>100): " + largeOrders);
    }
}
```

**How to run:** `java ReuseWithSupplier.java`

Expected output:
```
Count: 5
Sum: 475
Large orders (>100): [120, 200]
```

This uses a `Supplier<Stream<Integer>>` (`orderAmounts::stream`, a method reference) as an explicit, reusable "stream factory" — each call to `streamSupplier.get()` invokes `.stream()` on `orderAmounts` fresh, producing a brand-new `Stream` instance every time. This pattern is especially useful when passing "a way to get a stream of this data" around as a value (e.g. to a method that needs to run its own pipeline), rather than passing an already-built (and therefore single-use) `Stream` directly.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `orderAmounts` holds five values: `50, 120, 30, 200, 75`. `streamSupplier` is assigned the method reference `orderAmounts::stream` — at this point, no stream has actually been created yet; the supplier just knows *how* to create one on demand.

`streamSupplier.get()` is called for the first time, in `.count()`: this invokes `orderAmounts.stream()`, producing a fresh `Stream<Integer>` over the five values. `.count()` (terminal) consumes it immediately, returning `5`.

`streamSupplier.get()` is called a second time, in the sum computation: this invokes `orderAmounts.stream()` *again*, producing an entirely new, independent `Stream<Integer>` instance — unrelated to the one consumed a moment ago. `.mapToInt(Integer::intValue).sum()` processes this fresh stream: `50 + 120 + 30 + 200 + 75 = 475`.

`streamSupplier.get()` is called a third time, in the large-orders computation: another fresh stream is created. `.filter(a -> a > 100)` keeps `120` and `200` (both exceed `100`; `50`, `30`, `75` are dropped), and `.toList()` collects them.

```
streamSupplier.get() call #1 -> fresh Stream -> .count()                    -> 5
streamSupplier.get() call #2 -> fresh Stream -> .mapToInt(...).sum()        -> 475
streamSupplier.get() call #3 -> fresh Stream -> .filter(>100).toList()      -> [120, 200]

(three independent Stream instances, each created fresh, each consumed exactly once)
```

Each of the three `streamSupplier.get()` calls produces a genuinely independent `Stream` instance, consumed by exactly one terminal operation — no instance is ever reused, so no `IllegalStateException` occurs. `main` prints `"Count: 5"`, `"Sum: 475"`, and `"Large orders (>100): [120, 200]"`.

## 7. Gotchas & takeaways

> The "stream cannot be reused" exception can surface in surprising places, such as when a stream variable is accidentally referenced twice — once inside a conditional branch that runs a terminal operation, and again afterward. Always double-check that a `Stream` variable is genuinely fresh (i.e. came directly from a `.stream()` call or equivalent factory, with no terminal operation run on it yet) before passing it to any new pipeline step.

- A `Stream` instance can only have one terminal operation run on it; any further use after that throws `IllegalStateException`.
- Building an intermediate pipeline (`.filter(...)`, `.map(...)`) on an already-consumed stream also throws, not just calling a second terminal operation — the exception fires the moment *anything* is attempted on a spent stream.
- The fix for needing multiple independent computations over the same data is simply to call `.stream()` (or equivalent) again on the underlying source for each computation.
- A `Supplier<Stream<T>>` (often just a method reference like `collection::stream`) is a clean way to pass around "a way to get a fresh stream" rather than an already-built, single-use `Stream` instance.
- This single-use restriction is fundamentally different from `Iterator`, which can also only be traversed once, but also different from `Collection`, which — unlike either — supports being iterated or streamed repeatedly.
