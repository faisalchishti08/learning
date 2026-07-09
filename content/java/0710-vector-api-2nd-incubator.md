---
card: java
gi: 710
slug: vector-api-2nd-incubator
title: Vector API (2nd incubator)
---

## 1. What it is

The **Vector API**, first incubated in [Java 16](0691-stream-mapmulti-later-vector-api-incubator.md) (JEP 338), returned for a **second incubator round** in **Java 17** (JEP 414) with performance work, API refinements, and — most notably for interoperability — the ability to load vector data directly from, and store it directly into, an off-heap `MemorySegment` from the [Foreign Function & Memory API](0709-foreign-function-memory-api-incubator.md), which was itself unified in this exact same release. This means a vectorized computation can now read its input straight out of off-heap native memory and write its output straight back into it, without first copying that data into an on-heap Java array.

## 2. Why & when

The first incubator round proved out the core `VectorSpecies`/`IntVector`/`FloatVector` programming model for SIMD-style array processing, but it only worked against on-heap Java arrays (`IntVector.fromArray(...)`, `.intoArray(...)`). Numerically intensive code increasingly deals with data that already lives off-heap — read from a memory-mapped file, received from a native library, or shared with native code via the FFM API — and forcing a copy into a Java array just to vectorize a computation, then copying the result back out, adds real overhead and defeats some of the performance benefit vectorization is meant to provide. JEP 414 closed that gap by adding `fromMemorySegment(...)` and `intoMemorySegment(...)` methods directly on vector types, letting vectorized code operate on off-heap memory in place. Reach for this combination specifically when a numerically-heavy computation's input or output already lives in off-heap memory (from the FFM API, a memory-mapped file, or similar) and you want to vectorize it without paying for an intermediate on-heap copy.

## 3. Core concept

```java
// Java 17 (2nd incubator) — requires:
// --add-modules jdk.incubator.vector,jdk.incubator.foreign
import jdk.incubator.vector.*;
import jdk.incubator.foreign.*;

static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

try (ResourceScope scope = ResourceScope.newConfinedScope()) {
    MemorySegment segment = MemorySegment.allocateNative(SPECIES.vectorByteSize(), scope);
    // ... native code, or off-heap I/O, fills 'segment' with data ...
    IntVector v = IntVector.fromMemorySegment(SPECIES, segment, 0, java.nio.ByteOrder.nativeOrder());
    IntVector doubled = v.mul(2);
    doubled.intoMemorySegment(segment, 0, java.nio.ByteOrder.nativeOrder());
}
```

The vector is loaded directly from off-heap memory, computed on, and written straight back — no on-heap array ever enters the picture.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="In the first Vector API incubator, vectors could only load from and store to on-heap Java arrays; the second incubator adds direct load and store to off-heap MemorySegments">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16 (1st incubator)</text>
  <text x="160" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">int[] array (on-heap)</text>
  <text x="160" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">IntVector.fromArray(...)</text>
  <text x="160" y="120" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">v.intoArray(...)</text>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">off-heap data needs a copy first</text>

  <rect x="340" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17 (2nd incubator)</text>
  <text x="480" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">MemorySegment (off-heap)</text>
  <text x="480" y="100" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">IntVector.fromMemorySegment(...)</text>
  <text x="480" y="120" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">v.intoMemorySegment(...)</text>
  <text x="480" y="150" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">no on-heap copy needed</text>
</svg>

Vector loads and stores gain a direct path to off-heap memory, alongside the original on-heap array support.

## 5. Runnable example

Scenario: doubling every element of an integer buffer — first the familiar on-heap array version as a baseline, then the same computation performed entirely against an off-heap `MemorySegment` using the new `fromMemorySegment`/`intoMemorySegment` methods, then a version that measures and compares the on-heap and off-heap paths to confirm they produce identical results despite operating on entirely different memory.

### Level 1 — Basic

```java
// File: DoubleArrayBasic.java
// Requires: --add-modules jdk.incubator.vector
import jdk.incubator.vector.IntVector;
import jdk.incubator.vector.VectorSpecies;

public class DoubleArrayBasic {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    public static void main(String[] args) {
        int[] data = new int[16];
        for (int i = 0; i < data.length; i++) data[i] = i;

        int upperBound = SPECIES.loopBound(data.length);
        int i = 0;
        for (; i < upperBound; i += SPECIES.length()) {
            IntVector v = IntVector.fromArray(SPECIES, data, i);
            v.mul(2).intoArray(data, i);
        }
        for (; i < data.length; i++) data[i] *= 2; // scalar tail

        System.out.println(java.util.Arrays.toString(data));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector DoubleArrayBasic.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.vector
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
```

### Level 2 — Intermediate

```java
// File: DoubleMemorySegment.java
// Requires: --add-modules jdk.incubator.vector,jdk.incubator.foreign
import jdk.incubator.vector.IntVector;
import jdk.incubator.vector.VectorSpecies;
import jdk.incubator.foreign.MemoryAccess;
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.ResourceScope;

import java.nio.ByteOrder;

public class DoubleMemorySegment {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    public static void main(String[] args) {
        int elementCount = 16;

        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment segment = MemorySegment.allocateNative((long) elementCount * Integer.BYTES, scope);

            for (int i = 0; i < elementCount; i++) {
                MemoryAccess.setIntAtIndex(segment, i, i);
            }

            int width = SPECIES.length();
            int upperBound = SPECIES.loopBound(elementCount);
            int i = 0;
            for (; i < upperBound; i += width) {
                long byteOffset = (long) i * Integer.BYTES;
                IntVector v = IntVector.fromMemorySegment(SPECIES, segment, byteOffset, ByteOrder.nativeOrder());
                v.mul(2).intoMemorySegment(segment, byteOffset, ByteOrder.nativeOrder());
            }
            for (; i < elementCount; i++) { // scalar tail
                MemoryAccess.setIntAtIndex(segment, i, MemoryAccess.getIntAtIndex(segment, i) * 2);
            }

            StringBuilder sb = new StringBuilder("[");
            for (int idx = 0; idx < elementCount; idx++) {
                if (idx > 0) sb.append(", ");
                sb.append(MemoryAccess.getIntAtIndex(segment, idx));
            }
            sb.append("]");
            System.out.println(sb);
        }
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector,jdk.incubator.foreign DoubleMemorySegment.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.vector, jdk.incubator.foreign
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
```

### Level 3 — Advanced

```java
// File: OnHeapVsOffHeapCompare.java
// Requires: --add-modules jdk.incubator.vector,jdk.incubator.foreign
import jdk.incubator.vector.IntVector;
import jdk.incubator.vector.VectorSpecies;
import jdk.incubator.foreign.MemoryAccess;
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.ResourceScope;

import java.nio.ByteOrder;

public class OnHeapVsOffHeapCompare {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    static int[] doubleOnHeap(int[] data) {
        int[] result = data.clone();
        int width = SPECIES.length();
        int upperBound = SPECIES.loopBound(result.length);
        int i = 0;
        for (; i < upperBound; i += width) {
            IntVector.fromArray(SPECIES, result, i).mul(2).intoArray(result, i);
        }
        for (; i < result.length; i++) result[i] *= 2;
        return result;
    }

    static int[] doubleOffHeap(int[] data) {
        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment segment = MemorySegment.allocateNative((long) data.length * Integer.BYTES, scope);
            for (int i = 0; i < data.length; i++) MemoryAccess.setIntAtIndex(segment, i, data[i]);

            int width = SPECIES.length();
            int upperBound = SPECIES.loopBound(data.length);
            int i = 0;
            for (; i < upperBound; i += width) {
                long byteOffset = (long) i * Integer.BYTES;
                IntVector v = IntVector.fromMemorySegment(SPECIES, segment, byteOffset, ByteOrder.nativeOrder());
                v.mul(2).intoMemorySegment(segment, byteOffset, ByteOrder.nativeOrder());
            }
            for (; i < data.length; i++) {
                MemoryAccess.setIntAtIndex(segment, i, MemoryAccess.getIntAtIndex(segment, i) * 2);
            }

            int[] result = new int[data.length];
            for (int idx = 0; idx < data.length; idx++) result[idx] = MemoryAccess.getIntAtIndex(segment, idx);
            return result;
        }
    }

    public static void main(String[] args) {
        int[] input = new int[1000];
        for (int i = 0; i < input.length; i++) input[i] = i;

        int[] onHeapResult = doubleOnHeap(input);
        int[] offHeapResult = doubleOffHeap(input);

        System.out.println("On-heap  result[0..3]:  " + java.util.Arrays.toString(java.util.Arrays.copyOf(onHeapResult, 4)));
        System.out.println("Off-heap result[0..3]:  " + java.util.Arrays.toString(java.util.Arrays.copyOf(offHeapResult, 4)));
        System.out.println("Results identical: " + java.util.Arrays.equals(onHeapResult, offHeapResult));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector,jdk.incubator.foreign OnHeapVsOffHeapCompare.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.vector, jdk.incubator.foreign
On-heap  result[0..3]:  [0, 2, 4, 6]
Off-heap result[0..3]:  [0, 2, 4, 6]
Results identical: true
```

## 6. Walkthrough

1. `main` builds one input array of 1,000 ascending integers, then runs it through both `doubleOnHeap` (the familiar Level 1–style vectorized array computation) and `doubleOffHeap` (the new off-heap path), each of which independently doubles every element.
2. `doubleOffHeap` opens a confined `ResourceScope`, allocates an off-heap `MemorySegment` sized for exactly `data.length` ints, and copies the input array's values into it one at a time via `MemoryAccess.setIntAtIndex` — this initial copy exists only because the input started life as an on-heap array for this demonstration; in a real off-heap scenario, the data might already be sitting in that segment (written there by native code, or read from a memory-mapped file), with no on-heap copy ever needed.
3. The main vectorized loop mirrors the on-heap version almost exactly, but calls `IntVector.fromMemorySegment(SPECIES, segment, byteOffset, ByteOrder.nativeOrder())` instead of `fromArray`, and `intoMemorySegment(segment, byteOffset, ...)` instead of `intoArray` — the byte offset (rather than an element index) is required because a `MemorySegment` is addressed in raw bytes, so each step advances by `SPECIES.length()` elements but the offset passed to the vector load/store methods must be that count converted to bytes (`i * Integer.BYTES`).
4. `ByteOrder.nativeOrder()` tells the vector load/store methods to interpret the segment's bytes using whatever endianness the current CPU natively uses — important because off-heap memory has no inherent "this is an int array" structure the way a Java `int[]` does; the byte layout must be interpreted consistently by both the code writing and the code reading it.
5. Once the vectorized loop (plus its scalar tail for any remaining elements) finishes, `doubleOffHeap` copies the segment's contents back out into a fresh on-heap `int[]` purely so this example can print and compare it against the on-heap path's result — again, a real off-heap-native workload might never need this final copy either, if the off-heap result is destined for another native call or output operation.
6. `main` prints a few sample values from each path and a full `Arrays.equals` comparison across all 1,000 elements, confirming both paths compute the mathematically identical result despite one operating on a Java heap array and the other on raw off-heap native memory the whole time.

```
Input: int[1000] (0, 1, 2, ..., 999)
        │                              │
  doubleOnHeap (IntVector.fromArray/intoArray)     doubleOffHeap (fromMemorySegment/intoMemorySegment)
        │                              │
    result array                  result array (via MemorySegment round-trip)
        └──────────── Arrays.equals -> true ────────┘
```

## 7. Gotchas & takeaways

> Both the Vector API and the FFM API remained **incubator modules** in Java 17 — this example requires `--add-modules jdk.incubator.vector,jdk.incubator.foreign` (both, comma-separated) on compilation and execution, and neither API's exact shape was final at this point; class and method names in both APIs changed further in subsequent JDK releases before eventual standardization.
- `fromMemorySegment`/`intoMemorySegment` take a **byte offset**, not an element index — forgetting to multiply the element index by the element's byte size (`Integer.BYTES` for `int`) is a common mistake that silently reads or writes the wrong memory location rather than throwing.
- Always pass an explicit `ByteOrder` to these methods — off-heap memory has no built-in notion of "this is an array of ints in platform-native order" the way a Java array does, so the byte order must be specified consistently everywhere the segment is read or written, including by any native code sharing that memory.
- The performance benefit of skipping an on-heap copy only materializes when the data **already lives off-heap** for some other reason (native interop, memory-mapped I/O); manufacturing an off-heap segment purely to vectorize data that started on-heap (as this tutorial's example does, for demonstration) adds overhead rather than removing it.
- See [Foreign Function & Memory API (incubator)](0709-foreign-function-memory-api-incubator.md) for the `ResourceScope`/`MemorySegment` fundamentals this integration builds on, and [Vector API (1st incubator)](0691-stream-mapmulti-later-vector-api-incubator.md) for the core `VectorSpecies`/`IntVector` programming model this release extends rather than replaces.
- As always with the Vector API, confirm via profiling that a computation is genuinely the bottleneck before reaching for explicit vectorization — the added complexity of managing off-heap memory scopes on top of vector code is only worth it when both the off-heap data source and the numerical workload are real, measured concerns.
