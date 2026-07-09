---
card: java
gi: 671
slug: foreign-memory-access-api-incubator
title: Foreign-Memory Access API (incubator)
---

## 1. What it is

The **Foreign-Memory Access API**, introduced as an **incubator module** (`jdk.incubator.foreign`, JEP 370) in **Java 14**, gives Java programs a safe, efficient way to allocate and access memory that lives **outside the Java heap** — memory the garbage collector doesn't manage — without resorting to the notoriously unsafe `sun.misc.Unsafe` class or JNI native code. Its core types are `MemorySegment` (a bounds-checked, typed handle to a contiguous region of memory, either on- or off-heap) and `MemoryAddress`/`MemoryLayout` (describing where within a segment you are and how its bytes are structured). Unlike `Unsafe`, every access through this API is bounds-checked and lifecycle-checked at runtime — reading past the end of a segment or after it's been closed throws a proper exception rather than corrupting memory or crashing the JVM. Being an **incubator module** meant it shipped in a non-`java.*` package, required an explicit `--add-modules jdk.incubator.foreign` flag to use, and its API was expected to change before eventual standardization (it would evolve significantly over subsequent JDK releases before finalizing as the Foreign Function & Memory API years later).

## 2. Why & when

Java programs that need to interact with off-heap memory — for performance (avoiding GC pressure on huge datasets), for interop with native libraries, or for memory-mapped files — historically had exactly two bad options: `java.nio.ByteBuffer.allocateDirect()`, which works but has clunky, limited APIs and no fine-grained lifecycle control, or `sun.misc.Unsafe`, which is fast and flexible but entirely unchecked — a single indexing mistake can silently corrupt unrelated memory or crash the JVM outright, and it was never a supported public API to begin with. The Foreign-Memory Access API targets exactly this gap: safe, checked, deterministic-lifecycle access to off-heap memory, with performance close to `Unsafe` because the JIT compiler can optimize the bounds checks away in hot loops once it proves they're unnecessary. As an incubator feature, most application developers wouldn't reach for it directly in Java 14 — its primary audience was library authors experimenting with high-performance off-heap data structures, native interop layers, and researchers providing feedback that shaped the API's eventual finalized form.

## 3. Core concept

```java
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

// Allocate 100 bytes of off-heap memory, safely bounds-checked.
try (MemorySegment segment = MemorySegment.allocateNative(100)) {
    MemoryAccess.setIntAtOffset(segment, 0, 42);
    int value = MemoryAccess.getIntAtOffset(segment, 0);
    System.out.println(value); // 42

    // This throws a checked exception, NOT silent memory corruption:
    // MemoryAccess.getIntAtOffset(segment, 200); // IndexOutOfBoundsException
} // segment is automatically freed here (try-with-resources)
```

```
javac --add-modules jdk.incubator.foreign --release 14 MyApp.java
java  --add-modules jdk.incubator.foreign MyApp
```

`MemorySegment` implements `AutoCloseable`, so its off-heap memory has a clear, deterministic lifecycle tied to a `try`-with-resources block, rather than depending on unpredictable garbage collection timing.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unsafe gives unchecked direct memory access with no lifecycle; the Foreign-Memory Access API gives bounds-checked, lifecycle-managed off-heap access">
  <rect x="10" y="15" width="290" height="140" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="37" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">sun.misc.Unsafe</text>
  <text x="25" y="65" fill="#e6edf3" font-size="10" font-family="monospace">unsafe.putInt(addr, 42);</text>
  <text x="25" y="85" fill="#f85149" font-size="9" font-family="sans-serif">No bounds checking —</text>
  <text x="25" y="100" fill="#f85149" font-size="9" font-family="sans-serif">wrong offset corrupts</text>
  <text x="25" y="115" fill="#f85149" font-size="9" font-family="sans-serif">unrelated memory silently.</text>
  <text x="25" y="140" fill="#8b949e" font-size="9" font-family="sans-serif">No deterministic free.</text>

  <rect x="320" y="15" width="290" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="37" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">MemorySegment (incubator)</text>
  <text x="335" y="65" fill="#e6edf3" font-size="10" font-family="monospace">MemoryAccess.setIntAtOffset(</text>
  <text x="335" y="80" fill="#e6edf3" font-size="10" font-family="monospace">  segment, 0, 42);</text>
  <text x="335" y="105" fill="#6db33f" font-size="9" font-family="sans-serif">Out-of-bounds access throws</text>
  <text x="335" y="120" fill="#6db33f" font-size="9" font-family="sans-serif">a real exception, safely.</text>
  <text x="335" y="140" fill="#79c0ff" font-size="9" font-family="sans-serif">try-with-resources frees it.</text>
</svg>

Same goal (fast off-heap access), fundamentally different safety model: checked exceptions and deterministic cleanup instead of silent corruption and unmanaged lifetimes.

## 5. Runnable example

Scenario: building a small off-heap array of integers and manipulating it — first basic allocation and read/write, then demonstrating the bounds-checking safety net by triggering (and catching) an out-of-bounds access, then a slightly larger example computing a running sum over an off-heap buffer, mimicking a realistic "process a large off-heap dataset" pattern.

### Level 1 — Basic

```java
// File: OffHeapBasic.java
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

public class OffHeapBasic {
    public static void main(String[] args) {
        try (MemorySegment segment = MemorySegment.allocateNative(4 * 10)) { // 10 ints
            for (int i = 0; i < 10; i++) {
                MemoryAccess.setIntAtOffset(segment, i * 4L, i * i);
            }
            for (int i = 0; i < 10; i++) {
                System.out.print(MemoryAccess.getIntAtOffset(segment, i * 4L) + " ");
            }
            System.out.println();
        }
    }
}
```

**How to run:** requires the incubator module flag since this is a Java 14 incubator feature:
```
javac --add-modules jdk.incubator.foreign --release 14 OffHeapBasic.java
java --add-modules jdk.incubator.foreign OffHeapBasic
```

Expected output:
```
0 1 4 9 16 25 36 49 64 81
```

### Level 2 — Intermediate

```java
// File: OffHeapBounds.java
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

public class OffHeapBounds {
    public static void main(String[] args) {
        try (MemorySegment segment = MemorySegment.allocateNative(4 * 5)) { // 5 ints = 20 bytes
            for (int i = 0; i < 5; i++) {
                MemoryAccess.setIntAtOffset(segment, i * 4L, (i + 1) * 100);
            }
            System.out.println("Wrote 5 ints successfully.");

            try {
                // Offset 20 is one int PAST the last valid one (valid offsets: 0,4,8,12,16)
                MemoryAccess.getIntAtOffset(segment, 20L);
            } catch (IndexOutOfBoundsException e) {
                System.out.println("Caught expected bounds violation: " + e.getMessage());
            }

            System.out.println("Last valid value: " + MemoryAccess.getIntAtOffset(segment, 16L));
        }
    }
}
```

**How to run:** `javac --add-modules jdk.incubator.foreign --release 14 OffHeapBounds.java && java --add-modules jdk.incubator.foreign OffHeapBounds`

Expected output:
```
Wrote 5 ints successfully.
Caught expected bounds violation: Out of bound access on segment ...
Last valid value: 500
```

Unlike `Unsafe`, which would have either silently corrupted adjacent memory or crashed the JVM outright on an out-of-bounds write, `MemorySegment` throws a catchable `IndexOutOfBoundsException` — the program continues running normally afterward.

### Level 3 — Advanced

```java
// File: OffHeapRunningSum.java
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

public class OffHeapRunningSum {
    static long sumRange(MemorySegment segment, int fromIndex, int toIndexExclusive) {
        long total = 0;
        for (int i = fromIndex; i < toIndexExclusive; i++) {
            total += MemoryAccess.getIntAtOffset(segment, i * 4L);
        }
        return total;
    }

    public static void main(String[] args) {
        int count = 1000;
        try (MemorySegment segment = MemorySegment.allocateNative(4L * count)) {
            for (int i = 0; i < count; i++) {
                MemoryAccess.setIntAtOffset(segment, i * 4L, i + 1); // values 1..1000
            }

            long fullSum = sumRange(segment, 0, count);
            long firstHalf = sumRange(segment, 0, count / 2);
            long secondHalf = sumRange(segment, count / 2, count);

            System.out.println("Full sum (1..1000): " + fullSum);
            System.out.println("First half sum: " + firstHalf);
            System.out.println("Second half sum: " + secondHalf);
            System.out.println("Halves add up correctly: " + (firstHalf + secondHalf == fullSum));

            try {
                sumRange(segment, 0, count + 1); // deliberately over-read
            } catch (IndexOutOfBoundsException e) {
                System.out.println("Over-read correctly rejected.");
            }
        }
    }
}
```

**How to run:** `javac --add-modules jdk.incubator.foreign --release 14 OffHeapRunningSum.java && java --add-modules jdk.incubator.foreign OffHeapRunningSum`

Expected output:
```
Full sum (1..1000): 500500
First half sum: 125250
Second half sum: 375250
Halves add up correctly: true
Over-read correctly rejected.
```

Level 3 fills a 4000-byte off-heap segment with 1000 sequential integers and computes sums over sub-ranges directly against that off-heap memory — no Java heap array is involved at all — and demonstrates that an attempt to read past the segment's allocated bounds is caught safely rather than causing undefined behavior, the central safety guarantee this incubator API was designed to provide over `Unsafe`.

## 6. Walkthrough

1. `main` allocates a native (off-heap) memory segment sized `4L * count` bytes — `4000` bytes for `1000` 4-byte integers — via `MemorySegment.allocateNative(...)`, opened in a try-with-resources block so its lifetime is deterministic and explicit.
2. The first loop writes values `1` through `1000` into the segment: `MemoryAccess.setIntAtOffset(segment, i * 4L, i + 1)` computes each integer's byte offset (`0, 4, 8, ...`) and writes `i + 1` there — this memory lives entirely outside the Java heap; the JVM's garbage collector never scans or moves it.
3. `sumRange(segment, 0, count)` is called to compute the full sum. Inside, a `long total` accumulator starts at `0`, and the loop reads each integer back via `MemoryAccess.getIntAtOffset(segment, i * 4L)` for `i` from `0` to `999`, adding each to `total`. Because these are checked accesses, each call internally verifies the computed offset plus the access width (4 bytes for an `int`) falls within the segment's allocated `4000`-byte bounds before performing the read.
4. After summing `1 + 2 + ... + 1000`, `total` reaches `500500` (the well-known triangular-number formula result for 1000), returned as `fullSum`.
5. `sumRange(segment, 0, count / 2)` and `sumRange(segment, count / 2, count)` compute the first and second halves separately, `125250` and `375250` respectively — the program then verifies these two halves sum back to the full total, confirming the off-heap reads are consistent and correctly indexed.
6. Finally, `sumRange(segment, 0, count + 1)` is called inside a `try` block — this deliberately asks the loop to read index `1000` (offset `4000`), one integer past the segment's valid range (`0` through `999`, i.e., byte offsets `0` through `3996`). When the loop reaches `i = 1000`, `MemoryAccess.getIntAtOffset(segment, 4000L)` performs its bounds check, determines that reading 4 bytes starting at offset `4000` would extend to byte `4004` — past the segment's `4000`-byte allocation — and throws `IndexOutOfBoundsException` instead of reading whatever unrelated memory happens to sit past the allocation.
7. That exception propagates out of `sumRange` and is caught by `main`'s `catch` block, printing confirmation that the over-read was safely rejected — the program remains in a fully valid state afterward, unlike what an equivalent `Unsafe`-based over-read might have done.

```
segment: [int0][int1]...[int999]   (4000 bytes, indices 0..999 valid)
sumRange(0, 1000)   ──► reads offsets 0..3996 ──► total=500500 ✓
sumRange(0, 1001)   ──► reads offset 4000 ──► bounds check fails ──► IndexOutOfBoundsException
```

## 7. Gotchas & takeaways

> As an **incubator module**, this API required `--add-modules jdk.incubator.foreign` on both `javac` and `java`, lived in the non-standard `jdk.incubator.foreign` package (not `java.*`), and its exact API shape — class names, method signatures — changed significantly across subsequent JDK releases before eventual standardization as the Foreign Function & Memory API. Code written against this Java 14 incubator API is **not** forward-compatible with later finalized versions without changes; treat Java 14-era usage of this API as exploratory, not something to depend on unchanged in long-lived production code.

- `MemorySegment` provides bounds-checked, lifecycle-managed access to off-heap memory — a safe alternative to `sun.misc.Unsafe` for this use case.
- Off-heap memory allocated this way is never touched by the garbage collector — you must explicitly manage its lifetime, typically via try-with-resources, since `MemorySegment` implements `AutoCloseable`.
- Bounds violations throw `IndexOutOfBoundsException`, a normal catchable exception — not a JVM crash or silent memory corruption, which is the core safety improvement over `Unsafe`-based approaches.
- This API's primary Java 14 audience was library authors and researchers providing feedback, not typical application developers — it wasn't intended for broad production adoption while still incubating.
- If you encounter `jdk.incubator.foreign` in older code, know that it was superseded by later APIs (culminating in the standardized Foreign Function & Memory API) — don't assume method names or class structures transfer directly to modern JDK versions.
