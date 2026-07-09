---
card: java
gi: 756
slug: vector-api-6th-incubator
title: Vector API (6th incubator)
---

## 1. What it is

**Java 21** (JEP 448) is the **sixth incubator** round of the [Vector API](0738-vector-api-5th-incubator.md), continuing to refine `jdk.incubator.vector`. The core programming model — `VectorSpecies`, lane-based operations, masks, fused multiply-add, horizontal reductions — remains stable from the fifth incubator round covered in [Java 20](0738-vector-api-5th-incubator.md). This round focuses on integrating more cleanly with other recently added JDK features, most notably ensuring vector operations compose correctly with the [Foreign Function & Memory API](0755-foreign-function-memory-api-3rd-preview.md)'s `MemorySegment` for reading and writing vector data directly to and from off-heap memory, alongside continued performance tuning across hardware backends.

## 2. Why & when

A recurring real-world need for numeric, SIMD-accelerated code is operating on data that doesn't live on the Java heap at all — large buffers read from disk, memory-mapped files, or native libraries via the Foreign Function & Memory API. Before this round's integration work, moving data between an off-heap `MemorySegment` and the Vector API's `DoubleVector`/`IntVector`/etc. types required copying through an intermediate on-heap array, an unnecessary cost for hot numeric loops that could otherwise operate on the off-heap memory directly. This sixth incubator round strengthens exactly that path: vector load and store operations that read from and write to a `MemorySegment` directly, without an intermediate heap array — meaningful for workloads combining native interop with numeric computation, such as applying a signal-processing filter to audio samples read from a memory-mapped file, or accelerating computation over a large native buffer produced by a C library.

## 3. Core concept

```java
import java.lang.foreign.*;
import jdk.incubator.vector.*;

static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

static double sumFromMemorySegment(MemorySegment segment) {
    int laneCount = SPECIES.length();
    long elementCount = segment.byteSize() / Double.BYTES;
    DoubleVector acc = DoubleVector.zero(SPECIES);
    long i = 0;
    long bound = SPECIES.loopBound(elementCount);
    for (; i < bound; i += laneCount) {
        DoubleVector v = DoubleVector.fromMemorySegment(SPECIES, segment, i * Double.BYTES, java.nio.ByteOrder.nativeOrder());
        acc = acc.add(v);
    }
    double sum = acc.reduceLanes(VectorOperators.ADD);
    for (; i < elementCount; i++) {
        sum += segment.getAtIndex(ValueLayout.JAVA_DOUBLE, i);
    }
    return sum;
}
```

`DoubleVector.fromMemorySegment` reads a full vector's worth of `double`s directly from off-heap memory, skipping any intermediate on-heap array entirely.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vector loads and stores now read directly from and write directly to off-heap MemorySegments, avoiding an intermediate on-heap array copy" >
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">off-heap MemorySegment</text>

  <line x1="200" y1="45" x2="260" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow756)"/>
  <defs><marker id="arrow756" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
  <text x="230" y="35" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">direct</text>

  <rect x="270" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="360" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DoubleVector (SIMD lanes)</text>

  <rect x="20" y="110" width="430" height="50" rx="8" fill="#0f1620" stroke="#8b949e" opacity="0.6"/>
  <text x="235" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">previously: MemorySegment -&gt; heap array copy -&gt; Vector (extra step, avoided now)</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Direct off-heap vector I/O matters for native-interop-heavy numeric code</text>
</svg>

*Skipping the heap-array intermediary matters most when the data is already off-heap for another reason.*

## 5. Runnable example

Scenario: computing statistics over a large buffer of native memory (as if read from a memory-mapped file), growing from array-based vector math into direct off-heap vector I/O.

### Level 1 — Basic

```java
import jdk.incubator.vector.*;

public class VectorArrayBasic {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sum(double[] data) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        int i = 0;
        int bound = SPECIES.loopBound(data.length);
        for (; i < bound; i += SPECIES.length()) {
            acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < data.length; i++) total += data[i];
        return total;
    }

    public static void main(String[] args) {
        double[] data = new double[1000];
        for (int i = 0; i < data.length; i++) data[i] = i;
        System.out.println("sum: " + sum(data));
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector VectorArrayBasic.java` (JDK 21+).

This is the familiar array-based Vector API pattern from earlier incubator rounds — data lives in an on-heap `double[]`, and `DoubleVector.fromArray` reads directly from it.

### Level 2 — Intermediate

```java
import java.lang.foreign.*;
import jdk.incubator.vector.*;

public class VectorMemorySegment {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sumFromSegment(MemorySegment segment) {
        long elementCount = segment.byteSize() / Double.BYTES;
        DoubleVector acc = DoubleVector.zero(SPECIES);
        long i = 0;
        long bound = SPECIES.loopBound(elementCount);
        for (; i < bound; i += SPECIES.length()) {
            DoubleVector v = DoubleVector.fromMemorySegment(
                SPECIES, segment, i * Double.BYTES, java.nio.ByteOrder.nativeOrder());
            acc = acc.add(v);
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < elementCount; i++) {
            total += segment.getAtIndex(ValueLayout.JAVA_DOUBLE, i);
        }
        return total;
    }

    public static void main(String[] args) {
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment segment = arena.allocate(1000L * Double.BYTES);
            for (long i = 0; i < 1000; i++) {
                segment.setAtIndex(ValueLayout.JAVA_DOUBLE, i, (double) i);
            }
            System.out.println("sum: " + sumFromSegment(segment));
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 21 VectorMemorySegment.java`.

The real-world concern added: the data now lives entirely **off-heap** in an `Arena`-managed `MemorySegment` (as it naturally would if read from a memory-mapped file or produced by native code), and `DoubleVector.fromMemorySegment` reads directly from it — no intermediate `double[]` copy anywhere in the hot loop.

### Level 3 — Advanced

```java
import java.lang.foreign.*;
import jdk.incubator.vector.*;
import java.util.concurrent.*;

public class VectorMemorySegmentConcurrent {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sumRange(MemorySegment segment, long startElement, long endElement) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        long i = startElement;
        long bound = startElement + SPECIES.loopBound(endElement - startElement);
        for (; i < bound; i += SPECIES.length()) {
            DoubleVector v = DoubleVector.fromMemorySegment(
                SPECIES, segment, i * Double.BYTES, java.nio.ByteOrder.nativeOrder());
            acc = acc.add(v);
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < endElement; i++) {
            total += segment.getAtIndex(ValueLayout.JAVA_DOUBLE, i);
        }
        return total;
    }

    public static void main(String[] args) throws Exception {
        final long ELEMENT_COUNT = 4_000_000;
        final int CHUNKS = 4;

        try (Arena arena = Arena.ofShared()) {
            MemorySegment segment = arena.allocate(ELEMENT_COUNT * Double.BYTES);
            for (long i = 0; i < ELEMENT_COUNT; i++) {
                segment.setAtIndex(ValueLayout.JAVA_DOUBLE, i, 1.0);
            }

            long chunkSize = ELEMENT_COUNT / CHUNKS;
            try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
                var futures = new java.util.ArrayList<Future<Double>>();
                for (int c = 0; c < CHUNKS; c++) {
                    long start = c * chunkSize;
                    long end = (c == CHUNKS - 1) ? ELEMENT_COUNT : start + chunkSize;
                    futures.add(executor.submit(() -> sumRange(segment, start, end)));
                }
                double total = 0;
                for (var f : futures) total += f.get();
                System.out.println("total sum: " + total);
            }
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 21 VectorMemorySegmentConcurrent.java`.

This adds the production-flavored hard case: 4,000,000 elements in a **shared** off-heap arena, split into four ranges, each summed by a virtual-thread subtask using vectorized `MemorySegment` reads — combining Vector API off-heap integration with [structured, concurrent access to shared off-heap memory](0755-foreign-function-memory-api-3rd-preview.md), the exact kind of numeric-plus-native-interop workload this round's integration work targets.

## 6. Walkthrough

Tracing `VectorMemorySegmentConcurrent.main`:

1. `main` opens a shared arena and allocates enough off-heap memory for 4,000,000 `double`s, then fills every element with `1.0`.
2. It splits the element range into four roughly-equal chunks and submits one task per chunk to a virtual-thread executor, each calling `sumRange(segment, start, end)`.
3. Inside `sumRange`, the vectorized loop reads `SPECIES.length()` elements at a time directly from the shared `segment` via `DoubleVector.fromMemorySegment`, accumulating a running vector sum `acc` — no on-heap array is created or copied to at any point.
4. Once the vectorizable portion of the chunk is exhausted, `acc.reduceLanes(VectorOperators.ADD)` collapses the vector's lanes into a single scalar total, and a final scalar loop (using `segment.getAtIndex`) handles any remaining elements that didn't fill a complete vector.
5. Each of the four subtasks returns its chunk's partial sum; `main` collects all four via `.get()` and adds them into `total`.
6. Since every element was set to `1.0`, the expected total is exactly `4,000,000.0` — a value simple enough to sanity-check that both the chunking and the off-heap vector reads produced the correct result.

Expected output:
```
total sum: 4000000.0
```

## 7. Gotchas & takeaways

> **Gotcha:** `DoubleVector.fromMemorySegment` (and the analogous methods for other lane types) require specifying a `ByteOrder` explicitly — using the wrong byte order (say, reading big-endian data with `nativeOrder()` on a little-endian machine) silently produces garbage values rather than throwing an error, since the bytes are still valid `double` bit patterns, just the wrong ones.

- Sixth incubator round — still `jdk.incubator.vector`, requiring `--add-modules jdk.incubator.vector`.
- This round's headline addition is efficient vector load/store directly against off-heap `MemorySegment`s, avoiding a heap-array copy.
- Most valuable when data is already off-heap for another reason — memory-mapped files, native library buffers, or [FFM API](0755-foreign-function-memory-api-3rd-preview.md) interop — not as a reason to move data off-heap that didn't need to be.
- Combine with `Arena.ofShared()` when multiple threads need to read disjoint regions of the same off-heap buffer concurrently.
- Always specify the correct `ByteOrder` when reading vectors from memory that might have been produced by non-Java code or read from a file with a fixed endianness.
