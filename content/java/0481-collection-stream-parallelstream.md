---
card: java
gi: 481
slug: collection-stream-parallelstream
title: Collection.stream() / parallelStream()
---

## 1. What it is

`Collection<T>.stream()`, added in Java 8, is a `default` method every `Collection` (`List`, `Set`, and their implementations) inherits, returning a `Stream<T>` view over that collection's elements — the entry point into the Stream API for essentially any existing collection. `Collection.parallelStream()` is its sibling, returning a stream whose operations may run **concurrently across multiple threads** instead of sequentially on one.

## 2. Why & when

Before streams, processing a collection meant writing an explicit loop — iterate, check a condition, accumulate a result — every time, even for common operations like "filter these" or "transform those." `stream()` gives every collection a uniform, declarative way to express that kind of processing as a pipeline of operations (`filter`, `map`, `collect`, and many more), read top to bottom as a description of *what* should happen rather than *how* to loop and accumulate it by hand.

You call `.stream()` any time you want to process a collection's elements through the Stream API — filtering, transforming, collecting into a new structure, computing an aggregate. You reach for `.parallelStream()` specifically when the work per element is substantial enough that splitting it across multiple CPU cores would meaningfully speed things up — for small collections or cheap per-element work, the overhead of coordinating parallel execution typically outweighs any benefit, so `.stream()` (sequential) remains the right default unless you've measured that parallelism actually helps for your specific workload.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<String> names = List.of("Charlie", "Alice", "Bob");

// .stream() -- sequential: elements processed one at a time, in order, on the calling thread
List<String> sortedSequential = names.stream()
        .sorted()
        .collect(Collectors.toList());

// .parallelStream() -- MAY split work across multiple threads (Java's common ForkJoinPool)
List<String> sortedParallel = names.parallelStream()
        .sorted()
        .collect(Collectors.toList());

// Both produce the SAME final result -- parallelism changes HOW the work is done, not WHAT the result is.
System.out.println(sortedSequential.equals(sortedParallel)); // true
```

The stream returned by either method offers the identical set of operations (`filter`, `map`, `collect`, and so on) — `parallelStream()` differs only in *execution strategy*, not in what operations are available or what the final result represents.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="stream processes elements sequentially on one thread; parallelStream may split the work across multiple threads, but both produce the same final result">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">.stream() -- sequential, one thread</text>
  <rect x="20" y="38" width="580" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="56" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">element1 -&gt; element2 -&gt; element3 -&gt; element4  (in order, one thread)</text>

  <text x="20" y="95" fill="#8b949e" font-size="11" font-family="sans-serif">.parallelStream() -- MAY split across multiple threads</text>
  <rect x="20" y="105" width="280" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="160" y="123" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">element1, element2 (thread A)</text>
  <rect x="320" y="105" width="280" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="460" y="123" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">element3, element4 (thread B)</text>
</svg>

Sequential processes strictly in order on one thread; parallel may split the workload across several — the final result is the same either way, only the execution path differs.

## 5. Runnable example

Scenario: processing a collection of order amounts — evolved from `.stream()` used for a basic filter-and-collect pipeline, through `.parallelStream()` producing the identical result for an aggregation, to a case demonstrating why per-element operation order is not guaranteed under parallel execution, even though the final aggregated result is.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class StreamBasic {
    public static void main(String[] args) {
        Set<Integer> orderAmounts = new LinkedHashSet<>(List.of(120, 45, 300, 15, 200));

        List<Integer> largeOrders = orderAmounts.stream()
                .filter(amount -> amount >= 100)
                .sorted()
                .collect(Collectors.toList());

        System.out.println(largeOrders);
    }
}
```

**How to run:** `java StreamBasic.java`

Expected output:
```
[120, 200, 300]
```

`orderAmounts.stream()` returns a `Stream<Integer>` view over the `Set`'s elements. `.filter(...)` keeps only amounts `>= 100`, `.sorted()` orders them ascending, and `.collect(Collectors.toList())` gathers the final result into a `List` — a complete pipeline expressed declaratively, with no explicit loop written by hand.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ParallelStreamAggregation {
    public static void main(String[] args) {
        List<Integer> orderAmounts = new ArrayList<>();
        for (int i = 1; i <= 100_000; i++) {
            orderAmounts.add(i);
        }

        // Aggregation (sum) is a natural fit for parallelStream -- combining partial sums
        // from different threads is safe and order-independent.
        long sequentialSum = orderAmounts.stream().mapToLong(Integer::longValue).sum();
        long parallelSum = orderAmounts.parallelStream().mapToLong(Integer::longValue).sum();

        System.out.println("Sequential sum: " + sequentialSum);
        System.out.println("Parallel sum: " + parallelSum);
        System.out.println("Same result: " + (sequentialSum == parallelSum));
    }
}
```

**How to run:** `java ParallelStreamAggregation.java`

Expected output:
```
Sequential sum: 5000050000
Parallel sum: 5000050000
Same result: true
```

The real-world concern this shows: for a genuinely large collection (100,000 elements) and a workload that's naturally splittable and combinable (summing numbers), `parallelStream()` produces the exact same final result as `stream()` — parallelism changes only the internal execution strategy (splitting the sum across threads and combining partial sums), never the mathematically correct final answer for a well-behaved, order-independent aggregation like `sum()`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.atomic.*;
import java.util.stream.*;

public class ParallelStreamOrderCaveat {
    public static void main(String[] args) {
        List<Integer> numbers = new ArrayList<>();
        for (int i = 1; i <= 20; i++) {
            numbers.add(i);
        }

        // forEach on a PARALLEL stream does NOT guarantee per-element processing order --
        // different runs (and different machines) may print elements in different orders.
        // This is why side-effecting operations like printing need forEachOrdered if
        // order-sensitive output is required.
        List<Integer> collectedInOrder = numbers.parallelStream()
                .map(n -> n * n)
                .collect(Collectors.toList()); // collect() DOES preserve encounter order

        System.out.println("Collected result (order preserved): " + collectedInOrder);

        AtomicInteger sum = new AtomicInteger(0);
        numbers.parallelStream().forEach(n -> sum.addAndGet(n)); // safe: AtomicInteger, order-independent
        System.out.println("Sum via parallel forEach: " + sum.get());
    }
}
```

**How to run:** `java ParallelStreamOrderCaveat.java`

Expected output:
```
Collected result (order preserved): [1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 289, 324, 361, 400]
Sum via parallel forEach: 210
```

Even under parallel execution, `collect(Collectors.toList())` **preserves the original encounter order** of the source collection — parallelism affects only *how* elements are processed internally, not the order of the final collected result, for order-preserving terminal operations. The `AtomicInteger` accumulation demonstrates the correct way to safely combine results from a `parallelStream().forEach(...)`: a plain, non-thread-safe accumulator (like an ordinary `int` or unsynchronized `List.add`) would risk lost updates or corruption under concurrent access, but `AtomicInteger.addAndGet` is specifically designed to be safe when called from multiple threads simultaneously.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `numbers` is populated with integers `1` through `20`, in order.

`numbers.parallelStream().map(n -> n * n).collect(Collectors.toList())` runs a parallel pipeline: internally, the source list may be split into sub-ranges processed concurrently across multiple threads (Java's common `ForkJoinPool`), each thread squaring its assigned elements. Regardless of which thread processed which element, or in what order the squaring actually happened across threads, `collect(Collectors.toList())` reassembles the results in the **original source order** — this is a documented guarantee of `collect` for ordered source collections, distinguishing it from unordered operations. The result is `[1, 4, 9, 16, ..., 400]`, printed as the first line.

`numbers.parallelStream().forEach(n -> sum.addAndGet(n))` runs a second parallel pipeline. Here, multiple threads may call `sum.addAndGet(n)` concurrently, each for a different element (or elements) from `numbers`. `AtomicInteger.addAndGet` performs its read-modify-write atomically, meaning even if two threads call it at nearly the same moment, neither update is lost — the operation is safe under exactly this kind of concurrent access, unlike a plain `int` variable, whose `+=` operation is not atomic and could lose updates under concurrent modification.

```
numbers: 1, 2, 3, ..., 20 (order fixed in source)
parallelStream().map(square).collect(toList())  --> internally split/processed concurrently,
                                                      reassembled in ORIGINAL order --> [1,4,9,...,400]
parallelStream().forEach(sum.addAndGet)         --> concurrent adds, each safe via AtomicInteger
                                                      --> final sum = 1+2+...+20 = 210
```

After both pipelines complete, `sum.get()` reads the fully accumulated total, `210` (the sum of integers 1 through 20), which is printed as the second line — correct regardless of the actual order in which individual threads performed their additions, because addition is commutative and `AtomicInteger` guarantees no update is ever lost.

## 7. Gotchas & takeaways

> `forEach` on a parallel stream does **not** guarantee elements are visited in source order — if you need both parallelism and guaranteed visitation order for a side-effecting operation, use `forEachOrdered` instead (at some cost to parallel efficiency, since it must coordinate ordering across threads). Mutating shared, non-thread-safe state (a plain `List`, a plain counter) from inside a `parallelStream()` operation is a common source of subtle, hard-to-reproduce bugs — always ensure any shared state touched inside a parallel stream's lambda is genuinely thread-safe, as `AtomicInteger` is here.

- `Collection.stream()` returns a sequential `Stream<T>` view over the collection's elements; `Collection.parallelStream()` returns one that may process elements across multiple threads.
- Both offer the identical set of stream operations — the difference is purely about execution strategy, not about what operations are available.
- `collect(Collectors.toList())` and similar ordered collectors preserve the original source order even under parallel execution — parallelism affects internal processing, not the guaranteed final ordering of an ordered result.
- `forEach` on a parallel stream does not guarantee per-element visitation order; use `forEachOrdered` if order-sensitive side effects are required, understanding this reduces some of the parallelism benefit.
- Reach for `parallelStream()` only when the collection is large and the per-element work is substantial enough to outweigh the coordination overhead — for small collections or cheap operations, sequential `stream()` is typically just as fast or faster, and always simpler to reason about.
