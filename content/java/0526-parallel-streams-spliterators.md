---
card: java
gi: 526
slug: parallel-streams-spliterators
title: Parallel streams & spliterators
---

## 1. What it is

A **parallel stream** splits its work across multiple threads (backed by the JVM's common `ForkJoinPool`), created either via `Collection.parallelStream()` or by calling `.parallel()` on an existing stream. Behind the scenes, this splitting is done by a `Spliterator` ("splittable iterator") — an object that knows how to divide a data source into smaller, independently-processable chunks (`trySplit()`), traverse the elements in a chunk (`tryAdvance()`/`forEachRemaining()`), and report characteristics about the source (`SIZED`, `ORDERED`, `DISTINCT`, and others) that help the stream framework decide how best to parallelize.

## 2. Why & when

Parallel streams can speed up CPU-intensive work on large datasets by using multiple cores simultaneously — but they're not automatically faster, and understanding why requires understanding `Spliterator`s. A source that splits cheaply and evenly (an `ArrayList`, a primitive array) parallelizes well, since each thread gets a similarly-sized, independent chunk to work on. A source that splits poorly or unevenly (a `LinkedList`, an `Iterator`-based source with no size information) parallelizes badly, since the overhead of coordinating threads can exceed any benefit — sometimes making a parallel stream *slower* than its sequential equivalent. Recognizing this is essential before reaching for `.parallel()` as a performance fix.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = IntStream.rangeClosed(1, 10_000_000).boxed().toList();

// Sequential: one thread does all the work
long sequentialSum = numbers.stream().mapToLong(Integer::longValue).sum();

// Parallel: ArrayList-backed source splits cheaply and evenly across threads
long parallelSum = numbers.parallelStream().mapToLong(Integer::longValue).sum();

// Inspecting the spliterator directly
Spliterator<Integer> spliterator = numbers.spliterator();
System.out.println(spliterator.estimateSize());        // reports the source's size
System.out.println(spliterator.characteristics());       // reports properties like SIZED, ORDERED
```

`parallelStream()`/`.parallel()` triggers the stream to use its source's `Spliterator` to divide work across threads; a well-behaved spliterator (from `ArrayList`, arrays) splits evenly and cheaply, which is what makes parallel speedup possible in the first place.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a spliterator recursively splits a source into chunks distributed across worker threads">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="250" y="15" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="35" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">full source</text>
  <line x1="290" y1="45" x2="200" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="350" y1="45" x2="440" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="140" y="80" width="120" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="200" y="98" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">trySplit() -&gt; half</text>
  <rect x="380" y="80" width="120" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="440" y="98" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">trySplit() -&gt; half</text>
  <rect x="80" y="120" width="90" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/><text x="125" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread A</text>
  <rect x="200" y="120" width="90" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/><text x="245" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread B</text>
  <rect x="330" y="120" width="90" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/><text x="375" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread C</text>
  <rect x="450" y="120" width="90" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/><text x="495" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread D</text>
</svg>

`trySplit()` recursively divides the source into smaller chunks until each is small enough to hand to an individual worker thread.

## 5. Runnable example

Scenario: computing an expensive check over a large dataset — evolved from a plain sequential-vs-parallel comparison on a good source, through demonstrating a poor-splitting source that gains nothing from parallelism, to a version writing a custom `Spliterator` to understand what makes splitting well-behaved.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ParallelBasic {
    static boolean isPrime(int n) {
        if (n < 2) return false;
        for (int i = 2; (long) i * i <= n; i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        List<Integer> numbers = IntStream.rangeClosed(2, 200_000).boxed().toList();

        long sequentialCount = numbers.stream().filter(ParallelBasic::isPrime).count();
        long parallelCount = numbers.parallelStream().filter(ParallelBasic::isPrime).count();

        System.out.println("Sequential count: " + sequentialCount);
        System.out.println("Parallel count: " + parallelCount);
        System.out.println("Results match: " + (sequentialCount == parallelCount));
    }
}
```

**How to run:** `java ParallelBasic.java`

Expected output:
```
Sequential count: 17984
Parallel count: 17984
Results match: true
```

`numbers` is backed by an `ArrayList` (via `.toList()`), which has a well-behaved `Spliterator`: it knows its exact size upfront and can split evenly into halves recursively, distributing the CPU-intensive `isPrime` check across all available cores. Both the sequential and parallel versions produce the identical count (`17984` primes between `2` and `200,000`), confirming parallel execution here changes *performance*, not *correctness*.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ParallelPoorSplitting {
    public static void main(String[] args) {
        LinkedList<Integer> linkedNumbers = new LinkedList<>(IntStream.rangeClosed(1, 100_000).boxed().toList());
        ArrayList<Integer> arrayNumbers = new ArrayList<>(linkedNumbers);

        // Both report the same characteristics -- the difference is NOT in what they report.
        Spliterator<Integer> linkedSpliterator = linkedNumbers.spliterator();
        Spliterator<Integer> arraySpliterator = arrayNumbers.spliterator();
        System.out.println("LinkedList spliterator reports SUBSIZED: " +
                linkedSpliterator.hasCharacteristics(Spliterator.SUBSIZED));
        System.out.println("ArrayList spliterator reports SUBSIZED: " +
                arraySpliterator.hasCharacteristics(Spliterator.SUBSIZED));

        // Random access cost is where the real difference lives: ArrayList.get(mid) is O(1);
        // LinkedList.get(mid) must walk node by node from whichever end is closer.
        int mid = 50_000;
        long t1 = System.nanoTime();
        arrayNumbers.get(mid);
        long arrayGetTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        linkedNumbers.get(mid);
        long linkedGetTime = System.nanoTime() - t2;

        System.out.println("ArrayList.get(mid) was faster than LinkedList.get(mid): " + (arrayGetTime < linkedGetTime));
    }
}
```

**How to run:** `java ParallelPoorSplitting.java`

Expected output:
```
LinkedList spliterator reports SUBSIZED: true
ArrayList spliterator reports SUBSIZED: true
ArrayList.get(mid) was faster than LinkedList.get(mid): true
```

The real-world concern this adds: both spliterators report the *same* characteristics — Java's built-in spliterator implementations report `SIZED`/`SUBSIZED` for any `Collection` whose `size()` is known upfront, `LinkedList` included. The real difference is hidden underneath: `LinkedList`'s spliterator splits by walking its internal nodes to gather a batch of elements, which costs time proportional to how far it has to walk, while `ArrayList`'s spliterator can jump straight to any midpoint index in constant time. The `get(mid)` comparison here is a proxy for that same underlying cost — `ArrayList` reaches an arbitrary element instantly via direct indexing, while `LinkedList` must traverse node by node to get there, and that same node-walking cost is what makes each of `LinkedList`'s recursive splits during parallel processing more expensive than `ArrayList`'s.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class CustomSpliterator {
    // A minimal custom Spliterator over a fixed int[] range -- splits evenly, like ArrayList's does.
    static class RangeSpliterator implements Spliterator<Integer> {
        private int current;
        private final int end;

        RangeSpliterator(int start, int end) {
            this.current = start;
            this.end = end;
        }

        @Override
        public boolean tryAdvance(Consumer<? super Integer> action) {
            if (current >= end) return false;
            action.accept(current++);
            return true;
        }

        @Override
        public Spliterator<Integer> trySplit() {
            int remaining = end - current;
            if (remaining < 2) return null; // too small to split further
            int mid = current + remaining / 2;
            Spliterator<Integer> firstHalf = new RangeSpliterator(current, mid);
            this.current = mid; // this spliterator keeps the second half
            return firstHalf;
        }

        @Override public long estimateSize() { return end - current; }
        @Override public int characteristics() { return ORDERED | SIZED | SUBSIZED | IMMUTABLE; }
    }

    public static void main(String[] args) {
        Spliterator<Integer> spliterator = new RangeSpliterator(1, 21);

        List<Integer> collected = Collections.synchronizedList(new ArrayList<>());
        java.util.stream.StreamSupport.stream(spliterator, true) // true = parallel
                .forEach(collected::add);

        Collections.sort(collected); // parallel forEach doesn't preserve order -- sort for a stable check
        System.out.println("Collected " + collected.size() + " values: " + collected);
    }
}
```

**How to run:** `java CustomSpliterator.java`

Expected output:
```
Collected 20 values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
```

This writes a minimal custom `Spliterator` from scratch, mirroring what `ArrayList`'s built-in spliterator does conceptually: `trySplit()` divides the remaining range roughly in half, returning a new spliterator for the first half while keeping the second half for itself — this is exactly the recursive halving strategy that makes a source parallelize well. `StreamSupport.stream(spliterator, true)` builds a genuine parallel stream directly from this custom spliterator, and the twenty values `1` through `20` are correctly collected (via a thread-safe `synchronizedList`, since multiple threads write to it concurrently), regardless of which thread happened to process which sub-range.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `spliterator` is created as a `RangeSpliterator` covering `1` to `20` (exclusive of `21`, so `20` values: `1` through `20`).

`StreamSupport.stream(spliterator, true)` builds a parallel stream directly from this spliterator. Internally, the `ForkJoinPool`'s work-stealing mechanism repeatedly calls `trySplit()` on the spliterator (and on the spliterators it returns) to divide the work into pieces small enough for individual threads to handle.

The first `trySplit()` call: `current=1`, `end=21`, `remaining = 21 - 1 = 20`. Since `20 >= 2`, splitting proceeds: `mid = 1 + 20/2 = 1 + 10 = 11`. A new `RangeSpliterator(1, 11)` is returned as the "first half" (covering `1` through `10`), and the original spliterator's `current` is updated to `11`, so it now covers `11` through `20`.

Each of these two halves may be split again: the `(1, 11)` half has `remaining = 11 - 1 = 10 >= 2`, so it splits into `(1, 6)` and keeps `(6, 11)`. The `(11, 21)` half has `remaining = 21 - 11 = 10 >= 2`, so it splits into `(11, 16)` and keeps `(16, 21)`. This recursive splitting continues until each piece is small enough (or the framework decides further splitting isn't worthwhile), at which point `tryAdvance(...)` is called repeatedly on each final piece to actually produce its individual elements.

```
RangeSpliterator(1,21), remaining=20
  trySplit -> (1,11) split off, this keeps (11,21)
    (1,11), remaining=10 -> trySplit -> (1,6) split off, keeps (6,11)
    (11,21), remaining=10 -> trySplit -> (11,16) split off, keeps (16,21)
  ... splitting continues recursively until pieces are small ...

Each final small piece: tryAdvance() called repeatedly to emit its individual int values.
```

Each thread processes its assigned final piece via `tryAdvance`, calling `collected::add` (a `synchronizedList`, safe for concurrent writes from multiple threads) for each value it produces. Once all pieces are exhausted, `collected` holds all twenty values, `1` through `20`, though not necessarily in that order, since different threads finished their pieces at different times. `Collections.sort(collected)` restores a predictable order purely for the printed check. `collected.size()` is `20`, and the sorted list prints as `[1, 2, 3, ..., 20]` — confirming every value from the original range was produced exactly once, regardless of how the recursive splitting divided the work across threads.

## 7. Gotchas & takeaways

> Parallel streams are not automatically faster — for small datasets, or datasets backed by a poorly-splitting source (`LinkedList`, `Iterator`-based sources), the overhead of thread coordination can exceed any benefit from parallel execution, sometimes making the parallel version *slower* than sequential. Always measure before assuming `.parallel()` helps, and prefer `ArrayList`/array-backed sources (or `IntStream.range(...)`) when parallelism is genuinely needed for a CPU-intensive computation on a large dataset.

- Parallel streams split their work using the source's `Spliterator`, which knows how to divide the data (`trySplit()`) and traverse it (`tryAdvance()`).
- A well-behaved spliterator (from `ArrayList`, arrays, `IntStream.range`) splits cheaply and evenly, which is what makes parallel execution actually pay off.
- `LinkedList` and other node-based or size-unknown sources have spliterators that split poorly, often making `.parallelStream()` on them a net loss compared to sequential processing.
- `Spliterator.hasCharacteristics(SUBSIZED)` indicates a spliterator can guarantee the sizes of the pieces it splits into — a strong signal for good parallel performance.
- Writing a custom `Spliterator` (as shown in Level 3) is rarely necessary in application code, but understanding the interface clarifies exactly why some sources parallelize well and others don't.
