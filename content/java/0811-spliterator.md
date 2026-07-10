---
card: java
gi: 811
slug: spliterator
title: Spliterator
---

## 1. What it is

`Spliterator<T>` ("**split**able **iterator**," Java 8) is the traversal interface that powers the Streams API's ability to process a source both sequentially and **in parallel**. Instead of only `hasNext()`/`next()`, it centers on `tryAdvance(action)` (process one element and return whether there was one), `forEachRemaining(action)` (process all remaining elements), and — the key addition — `trySplit()`, which attempts to carve off a chunk of the remaining elements into a **new** `Spliterator` covering that chunk, leaving the original covering the rest. It also reports `characteristics()` (flags like `ORDERED`, `SIZED`, `DISTINCT`, `SORTED`) and `estimateSize()`, which let stream infrastructure make smart decisions about whether and how to split further.

## 2. Why & when

A regular `Iterator` is inherently sequential — there's no way to hand half of it to another thread, because `hasNext()`/`next()` only describe "give me the next one," never "give me a self-contained piece of the remainder." Parallel streams need exactly that: a way to recursively divide a data source into independent chunks that separate threads can process without coordination, then combine the results. `Spliterator` exists to make that division a first-class, implementable operation. You'd implement a custom `Spliterator` yourself when you have a data source the standard library doesn't already know how to split efficiently (a custom on-disk format, a specialized array-backed structure) and want `StreamSupport.stream(spliterator, parallel)` to process it correctly in parallel; for ordinary collections, `Collection.spliterator()` already provides one, and most code never needs to touch this interface directly.

## 3. Core concept

```java
List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8);
Spliterator<Integer> spliterator = numbers.spliterator();

Spliterator<Integer> firstHalf = spliterator.trySplit(); // spliterator now covers only the SECOND half
// firstHalf covers roughly [1,2,3,4], spliterator now covers roughly [5,6,7,8]

firstHalf.forEachRemaining(System.out::println);   // processes its half
spliterator.forEachRemaining(System.out::println); // processes the other half
```

`trySplit()` mutates the spliterator it's called on to cover only the *remaining* portion, and returns a new spliterator covering the *split-off* portion — the two together still cover exactly what the original covered, with no overlap and no gaps.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spliterator splits recursively into halves, each processed by a separate thread, until the pieces are small enough to process directly">
  <rect x="230" y="15" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">[1..8] full spliterator</text>

  <line x1="290" y1="55" x2="150" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#a811)"/>
  <line x1="350" y1="55" x2="490" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#a811)"/>
  <defs><marker id="a811" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="70" y="95" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[1..4] (trySplit result)</text>

  <rect x="410" y="95" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[5..8] (remaining original)</text>

  <line x1="150" y1="135" x2="150" y2="160" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a811b)"/>
  <line x1="490" y1="135" x2="490" y2="160" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a811b)"/>
  <defs><marker id="a811b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>

  <text x="150" y="180" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">thread A processes</text>
  <text x="490" y="180" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">thread B processes</text>
</svg>

*Each `trySplit()` call divides the remaining elements in two; the fork/join pool assigns the pieces to separate threads.*

## 5. Runnable example

Scenario: summing a large collection of numbers, growing from using a `Spliterator` sequentially, to manually splitting it to sum in two halves, to a fully custom `Spliterator` over a raw `int[]` that plugs into a genuinely parallel stream.

### Level 1 — Basic

```java
import java.util.*;
import java.util.function.*;

public class SpliteratorBasic {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8);
        Spliterator<Integer> spliterator = numbers.spliterator();

        int[] total = {0};
        Consumer<Integer> accumulate = n -> total[0] += n;

        spliterator.forEachRemaining(accumulate);
        System.out.println("total: " + total[0]);
        System.out.println("estimated size before (already consumed, now 0): " + spliterator.estimateSize());
    }
}
```

**How to run:** `java SpliteratorBasic.java` (JDK 17+).

Expected output:
```
total: 36
estimated size before (already consumed, now 0): 0
```

Used purely sequentially here — `forEachRemaining` walks every element exactly once, similar to a plain `Iterator`'s `forEachRemaining`. After consumption, `estimateSize()` correctly reports `0` remaining elements.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.function.*;

public class SpliteratorManualSplit {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8);
        Spliterator<Integer> spliterator = numbers.spliterator();

        System.out.println("estimated size before split: " + spliterator.estimateSize());

        Spliterator<Integer> firstHalf = spliterator.trySplit();
        System.out.println("estimated size of first half:  " + (firstHalf == null ? "null (couldn't split)" : firstHalf.estimateSize()));
        System.out.println("estimated size of second half: " + spliterator.estimateSize());

        int[] firstSum = {0};
        int[] secondSum = {0};
        if (firstHalf != null) firstHalf.forEachRemaining(n -> firstSum[0] += n);
        spliterator.forEachRemaining(n -> secondSum[0] += n);

        System.out.println("first half sum: " + firstSum[0] + ", second half sum: " + secondSum[0]);
        System.out.println("combined total: " + (firstSum[0] + secondSum[0]));
    }
}
```

**How to run:** `java SpliteratorManualSplit.java`.

Expected output:
```
estimated size before split: 8
estimated size of first half:  4
estimated size of second half: 4
first half sum: 10, second half sum: 26
combined total: 36
```

The real-world concern added: manually invoking `trySplit()` and observing exactly what happens — the original spliterator (estimated size 8) shrinks to cover only the second half (size 4) once split, while the returned `firstHalf` covers the other 4 elements. Summing both halves independently and adding the results matches the sequential total from Level 1, confirming the split is lossless and non-overlapping.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class IntArraySpliterator implements Spliterator<Integer> {
    private final int[] array;
    private int start, end; // covers [start, end)

    public IntArraySpliterator(int[] array, int start, int end) {
        this.array = array;
        this.start = start;
        this.end = end;
    }

    @Override
    public boolean tryAdvance(Consumer<? super Integer> action) {
        if (start >= end) return false;
        action.accept(array[start]);
        start++;
        return true;
    }

    @Override
    public Spliterator<Integer> trySplit() {
        int remaining = end - start;
        if (remaining < 2) return null; // too small to usefully split further
        int mid = start + remaining / 2;
        Spliterator<Integer> firstHalf = new IntArraySpliterator(array, start, mid);
        this.start = mid; // this spliterator now covers only the second half
        return firstHalf;
    }

    @Override
    public long estimateSize() {
        return end - start;
    }

    @Override
    public int characteristics() {
        return ORDERED | SIZED | SUBSIZED | NONNULL;
    }

    public static void main(String[] args) {
        int[] data = new int[1000];
        for (int i = 0; i < data.length; i++) data[i] = i + 1; // 1..1000

        IntArraySpliterator customSpliterator = new IntArraySpliterator(data, 0, data.length);

        long total = StreamSupport.stream(customSpliterator, true) // true = request a parallel stream
            .mapToLong(Integer::longValue)
            .sum();

        System.out.println("sum of 1..1000 via custom parallel Spliterator: " + total);
        System.out.println("expected (n*(n+1)/2 for n=1000): " + (1000L * 1001 / 2));
    }
}
```

**How to run:** `java IntArraySpliterator.java`.

Expected output:
```
sum of 1..1000 via custom parallel Spliterator: 500500
expected (n*(n+1)/2 for n=1000): 500500
```

This adds the production-flavored hard case: a fully **custom `Spliterator`** implementation wrapping a raw `int[]`, correctly reporting `SIZED`/`SUBSIZED` (so the stream framework knows exact remaining counts cheaply) and `ORDERED` (so it knows element order matters), with `trySplit()` dividing the covered range in half each time. Passing it to `StreamSupport.stream(customSpliterator, true)` lets the standard fork/join common pool recursively call `trySplit()` as many times as it judges useful, processing the resulting pieces across multiple threads, and combining partial sums — all driven by this one custom class implementing four methods.

## 6. Walkthrough

Tracing `IntArraySpliterator.main`:

1. `data` is filled with the integers 1 through 1000, and `customSpliterator` is constructed covering the whole array (`start=0, end=1000`).
2. `StreamSupport.stream(customSpliterator, true)` builds a parallel `Stream<Integer>` backed by this spliterator; the `true` flag tells the stream machinery to actually attempt parallel execution rather than falling back to sequential.
3. When the terminal operation (`.sum()`, via `.mapToLong(...)`) runs, the underlying fork/join framework repeatedly calls `trySplit()` on `customSpliterator`: each call computes `mid = start + remaining/2`, constructs a new `IntArraySpliterator` covering `[start, mid)`, and mutates the original to cover only `[mid, end)` — exactly mirroring the manual split demonstrated in Level 2, but now happening recursively and automatically, dozens of times, until the pieces are small enough (or the framework decides splitting further isn't worth it) that `characteristics()` reporting `SIZED`/`SUBSIZED` helps it make that call cheaply.
4. Each leaf-level piece is processed by a worker thread calling `tryAdvance` (or `forEachRemaining`) repeatedly, accumulating a partial sum for its slice of the array.
5. The fork/join framework combines all partial sums back together into the final `total`, which the `.sum()` terminal operation returns — `500500`, matching the closed-form formula `n(n+1)/2` for `n=1000`, confirming every element was counted exactly once across however many splits and threads were actually used.

## 7. Gotchas & takeaways

> **Gotcha:** `trySplit()` returning `null` doesn't mean an error — it means "this spliterator has decided not to split further" (often because too few elements remain to make splitting worthwhile), and the stream framework handles that gracefully by processing the remainder sequentially or via a different path. A correct `Spliterator` implementation must handle repeated `trySplit()` calls returning `null` at some point without breaking traversal.

- `Spliterator<T>` adds `trySplit()` to the `Iterator`-like traversal contract (`tryAdvance`, `forEachRemaining`), enabling genuine parallel decomposition of a data source.
- `trySplit()` mutates the original to cover only the remaining portion and returns a new spliterator covering the split-off portion — the two together must cover exactly the original range, no overlap or gap.
- `characteristics()` flags like `ORDERED`, `SIZED`, `SUBSIZED`, and `SORTED` let the stream framework make efficient splitting and combining decisions without inspecting the actual elements.
- `Collection.spliterator()` already provides a correct spliterator for standard collections — implement a custom one only for data sources the standard library doesn't cover.
- `StreamSupport.stream(spliterator, parallel)` is the bridge from a raw `Spliterator` to the full Streams API, including genuine multi-threaded parallel execution when `parallel` is `true`.
