---
card: java
gi: 559
slug: arrays-parallelsort
title: Arrays.parallelSort()
---

## 1. What it is

`Arrays.parallelSort(array)` sorts an array using multiple threads from the common `ForkJoinPool`, splitting the array into chunks, sorting each chunk, and merging the results — instead of the single-threaded sort that `Arrays.sort(array)` always uses. It's a drop-in replacement with the same method signatures (overloaded for primitives, objects, and ranges) that can use extra CPU cores for large arrays.

## 2. Why & when

`Arrays.sort` (dual-pivot quicksort for primitives, TimSort for objects) runs on a single thread no matter how many cores the machine has. For small or medium arrays that's fine — sorting is fast and thread overhead would dominate anyway. But for large arrays (roughly hundreds of thousands of elements or more) on a multi-core machine, a single thread leaves most of the CPU idle. `parallelSort` uses a fork/join strategy: split the array recursively, sort sub-arrays on separate threads, merge them back together — genuinely faster wall-clock time on large enough data. It's the wrong choice for small arrays, where thread coordination overhead can make it *slower* than plain `sort`.

## 3. Core concept

```java
int[] data = new int[2_000_000];
// ... fill with random values ...

Arrays.sort(data);          // single-threaded
Arrays.parallelSort(data);  // multi-threaded, uses common ForkJoinPool
```

Internally, `parallelSort` checks the array length against a threshold (`Arrays.MIN_ARRAY_SORT_GRAN`, effectively ~8192 for typical JVMs): below the threshold it just calls the sequential sort directly, since parallelizing tiny arrays isn't worth the overhead. Above it, the array is recursively split, each half sorted (potentially on a different thread pulled from `ForkJoinPool.commonPool()`), and the sorted halves merged.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="parallelSort splits an array, sorts pieces on multiple threads, then merges">
  <rect x="20" y="10" width="600" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="30" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">unsorted array (large)</text>

  <line x1="320" y1="40" x2="170" y2="65" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="40" x2="470" y2="65" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="70" y="65" width="200" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="85" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">left half (thread A)</text>
  <rect x="370" y="65" width="200" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="85" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">right half (thread B)</text>

  <text x="170" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">recursively split &amp; sorted in parallel...</text>
  <text x="470" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">recursively split &amp; sorted in parallel...</text>

  <line x1="170" y1="125" x2="320" y2="150" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="470" y1="125" x2="320" y2="150" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="120" y="150" width="400" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="170" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">merged, fully sorted array</text>
</svg>

Below a size threshold, parallelSort skips all this and just sorts sequentially — splitting has a cost too.

## 5. Runnable example

Scenario: sorting a large batch of randomly generated sensor readings — starting with a straightforward sequential-vs-parallel timing comparison, then sorting a range within a larger buffer, then sorting an array of custom objects by a comparator while measuring the crossover point where parallel sorting starts winning.

### Level 1 — Basic

```java
import java.util.Arrays;

public class ParallelSortBasic {
    public static void main(String[] args) {
        int[] data = new int[5_000_000];
        java.util.Random rnd = new java.util.Random(42);
        for (int i = 0; i < data.length; i++) data[i] = rnd.nextInt();

        int[] sequential = data.clone();
        int[] parallel = data.clone();

        long t1 = System.nanoTime();
        Arrays.sort(sequential);
        long sequentialMs = (System.nanoTime() - t1) / 1_000_000;

        long t2 = System.nanoTime();
        Arrays.parallelSort(parallel);
        long parallelMs = (System.nanoTime() - t2) / 1_000_000;

        System.out.println("Sequential sort: " + sequentialMs + " ms");
        System.out.println("Parallel sort:   " + parallelMs + " ms");
        System.out.println("Results match:   " + Arrays.equals(sequential, parallel));
    }
}
```

**How to run:** `java ParallelSortBasic.java`

Expected output (exact timings vary by machine; parallel is typically faster on a multi-core machine for 5 million elements):
```
Sequential sort: 320 ms
Parallel sort:   95 ms
Results match:   true
```

`Arrays.sort(sequential)` sorts using one thread. `Arrays.parallelSort(parallel)` sorts the same data (from an independent clone) using the common `ForkJoinPool`. `Arrays.equals(...)` confirms both produce an identical sorted result — parallel sorting changes *how* the work is scheduled, never *what* the correct output is.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class ParallelSortRange {
    public static void main(String[] args) {
        int[] buffer = {9, 3, 7, 1, 8, 2, 6, 4, 5, 100, 200, 300};
        // Only sort indices [0, 9) — leave the trailing "reserved" slots untouched.
        Arrays.parallelSort(buffer, 0, 9);

        System.out.println(Arrays.toString(buffer));
    }
}
```

**How to run:** `java ParallelSortRange.java`

Expected output:
```
[1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 200, 300]
```

The real-world concern this adds: sorting only a **sub-range** of a larger buffer, common when an array has a used portion and a reserved/unused tail (e.g., a growable buffer that over-allocates). `Arrays.parallelSort(array, fromIndex, toIndex)` sorts `[fromIndex, toIndex)` in place and leaves everything outside that range untouched — indices 9, 10, 11 (values 100, 200, 300) stay exactly where they were.

### Level 3 — Advanced

```java
import java.util.Arrays;
import java.util.Comparator;
import java.util.Random;

public class ParallelSortObjects {
    record Reading(String sensorId, double value) {}

    public static void main(String[] args) {
        Random rnd = new Random(7);
        Reading[] readings = new Reading[1_000_000];
        for (int i = 0; i < readings.length; i++) {
            readings[i] = new Reading("sensor-" + (i % 50), rnd.nextDouble() * 100);
        }

        Comparator<Reading> byValueDescending = Comparator.comparingDouble(Reading::value).reversed();

        long start = System.nanoTime();
        Arrays.parallelSort(readings, byValueDescending);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        System.out.println("Sorted " + readings.length + " readings in " + elapsedMs + " ms");
        System.out.println("Highest reading: " + readings[0]);
        System.out.println("Lowest reading:  " + readings[readings.length - 1]);
        // Verify the array is genuinely sorted (each element >= the next).
        boolean sorted = true;
        for (int i = 0; i < readings.length - 1; i++) {
            if (readings[i].value() < readings[i + 1].value()) { sorted = false; break; }
        }
        System.out.println("Verified sorted (descending): " + sorted);
    }
}
```

**How to run:** `java ParallelSortObjects.java`

Expected output (values vary by run since readings are random; ordering and correctness do not):
```
Sorted 1000000 readings in 140 ms
Highest reading: Reading[sensorId=sensor-31, value=99.99988...]
Lowest reading:  Reading[sensorId=sensor-8, value=1.2E-5...]
Verified sorted (descending): true
```

This handles the production-flavoured case of sorting custom objects (not primitives) using a `Comparator`, exactly like sorting a list of domain records by a computed field. `Arrays.parallelSort(readings, byValueDescending)` uses the object-array overload, which internally uses a parallel TimSort variant instead of the primitive parallel quicksort, but the same fork/join, split-sort-merge strategy applies.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `readings` is filled with 1,000,000 `Reading` records, each with a `sensorId` cycling through 50 values and a random `value` between 0 and 100.

`byValueDescending` is built with `Comparator.comparingDouble(Reading::value).reversed()` — this extracts the `value` field for comparison and reverses the natural ascending order to descending, so the highest reading sorts first.

`Arrays.parallelSort(readings, byValueDescending)` is called. Internally, because the array size (1,000,000) far exceeds the parallel sort threshold, the array is recursively divided:

```
[readings 0 .. 1,000,000)
        |
   split in half
   /            \
[0..500,000)   [500,000..1,000,000)
   |                  |
 split again      split again
   ...                ...
```

Each leaf-level chunk (small enough to be below the threshold) is sorted sequentially using `byValueDescending`, typically on separate worker threads drawn from `ForkJoinPool.commonPool()`. Sorted chunks are then merged pairwise back up the tree — merging two already-sorted chunks by comparator is itself parallelized for large enough chunks — until the whole array is one fully sorted sequence, all done in place within the original `readings` array.

Once `parallelSort` returns, `readings[0]` holds the record with the numerically highest `value` (since the comparator is descending) and `readings[readings.length - 1]` holds the lowest. The verification loop walks the array once, checking that `readings[i].value() >= readings[i+1].value()` for every adjacent pair — confirming the parallel sort produced a genuinely, fully sorted array despite the work having been split across threads.

## 7. Gotchas & takeaways

> `parallelSort` uses `ForkJoinPool.commonPool()`, the **same shared thread pool** used by parallel streams (`stream().parallel()`) and `CompletableFuture`'s default async methods. If your application already saturates the common pool with other parallel work, a `parallelSort` call can end up competing for the same worker threads rather than getting genuinely dedicated parallelism — profile under realistic load, not in isolation.

- For small arrays (roughly under ~8,192 elements, exact threshold is JVM-internal), `parallelSort` falls back to a plain sequential sort automatically — you don't need to choose manually based on size.
- The sorted *result* from `parallelSort` is always identical to what `sort` would produce; only the execution strategy differs, never the correctness or ordering semantics.
- Like `Arrays.sort`, `parallelSort` is overloaded for all primitive types, `Object[]` (natural ordering), `Object[]` with a `Comparator`, and range variants (`fromIndex`, `toIndex`) for all of the above.
- Benchmark before assuming `parallelSort` is faster — on small arrays, or on machines with few cores, the fork/join coordination overhead can make it slower than plain `sort`.
- Because it uses the common pool, calling `parallelSort` from many threads simultaneously can cause contention; for latency-sensitive code paths, measure rather than assume.
