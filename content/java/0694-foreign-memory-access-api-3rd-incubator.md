---
card: java
gi: 694
slug: foreign-memory-access-api-3rd-incubator
title: Foreign-Memory Access API (3rd incubator)
---

## 1. What it is

**Java 16** shipped the **Foreign-Memory Access API** for its **third round of incubation** (JEP 393), continuing refinement of the API first incubated in Java 14 (see [Foreign-Memory Access API (incubator)](0671-foreign-memory-access-api-incubator.md)) and again in Java 15. This round consolidated and unified concepts (like unbounded vs. bounded memory segments) and refined the `MemorySegment` / `MemoryAddress` / `MemoryLayout` API surface based on two prior rounds of feedback, while remaining under `jdk.incubator.foreign` and still requiring `--add-modules jdk.incubator.foreign` to use. The core capability was unchanged across incubations: safe, explicit, deterministic allocation and access of memory **outside the Java heap**, with bounds-checking on every access.

## 2. Why & when

Off-heap memory access in Java traditionally meant `sun.misc.Unsafe` (an internal, unsupported API with no bounds checking — an out-of-bounds access could silently corrupt unrelated memory or crash the JVM) or `java.nio.ByteBuffer.allocateDirect(...)` (safer, but limited in size, awkward for structured data, and without fine control over lifecycle). The Foreign-Memory Access API's goal, across all three incubation rounds, was a **safe** off-heap memory API: every access is bounds-checked, memory segments have a well-defined lifecycle (allocated, used, explicitly freed via `close()`), and — crucially — an out-of-bounds access throws a normal Java exception instead of corrupting memory or crashing the process. The third round specifically focused on unifying and simplifying the segment/address/layout model after feedback from the first two rounds revealed rough edges. Reach for it (understanding it stayed an evolving incubator API for additional rounds after Java 16, eventually merging with the Foreign Linker API into the unified Foreign Function & Memory API) whenever you need large amounts of memory outside normal heap management — memory-mapped files, large off-heap buffers for high-performance computing, or data structures interoperating with native code.

## 3. Core concept

```java
// Java 16 (3rd incubator round) — requires --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

try (MemorySegment segment = MemorySegment.allocateNative(4 * 10)) { // 10 ints, off-heap
    for (int i = 0; i < 10; i++) {
        MemoryAccess.setIntAtOffset(segment, i * 4L, i * i);
    }
    for (int i = 0; i < 10; i++) {
        System.out.print(MemoryAccess.getIntAtOffset(segment, i * 4L) + " ");
    }
}
// segment is automatically, deterministically freed here (try-with-resources)
```

The memory backing `segment` lives entirely off the Java heap, is bounds-checked on every access, and is deterministically released when the `try`-with-resources block exits — no garbage-collector involvement at all.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A MemorySegment represents a bounds-checked region of off-heap native memory, distinct from the managed Java heap">
  <rect x="20" y="20" width="260" height="150" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Java heap</text>
  <text x="150" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ordinary objects</text>
  <text x="150" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">garbage-collected</text>

  <rect x="330" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Off-heap MemorySegment</text>
  <text x="465" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bounds-checked accesses</text>
  <text x="465" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">explicit close() releases it</text>
  <text x="465" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">not managed by the GC</text>
</svg>

Two entirely separate memory worlds: the managed, garbage-collected heap, and explicitly-managed, bounds-checked native memory.

## 5. Runnable example

Scenario: a small off-heap array-like buffer — first writing and reading a sequence of ints, then demonstrating the bounds-checking guarantee by deliberately reading past the allocated region, then structuring access with `MemoryLayout`/`VarHandle` for named-field-style access into an off-heap "record" rather than raw byte offsets.

### Level 1 — Basic

```java
// File: OffHeapBasic.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

public class OffHeapBasic {
    public static void main(String[] args) {
        try (MemorySegment segment = MemorySegment.allocateNative(4 * 10)) {
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

**How to run:**
```
javac --add-modules jdk.incubator.foreign --release 16 OffHeapBasic.java
java --add-modules jdk.incubator.foreign OffHeapBasic
```

Expected output:
```
0 1 4 9 16 25 36 49 64 81
```

### Level 2 — Intermediate

```java
// File: OffHeapBoundsCheck.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.MemoryAccess;

public class OffHeapBoundsCheck {
    public static void main(String[] args) {
        try (MemorySegment segment = MemorySegment.allocateNative(4 * 5)) { // 5 ints = 20 bytes
            for (int i = 0; i < 5; i++) {
                MemoryAccess.setIntAtOffset(segment, i * 4L, (i + 1) * 100);
            }
            System.out.println("Wrote 5 ints successfully.");

            try {
                MemoryAccess.getIntAtOffset(segment, 20L); // one int past the valid range
            } catch (IndexOutOfBoundsException e) {
                System.out.println("Caught expected bounds violation.");
            }

            System.out.println("Last valid value: " + MemoryAccess.getIntAtOffset(segment, 16L));
        }
    }
}
```

**How to run:**
```
javac --add-modules jdk.incubator.foreign --release 16 OffHeapBoundsCheck.java
java --add-modules jdk.incubator.foreign OffHeapBoundsCheck
```

Expected output:
```
Wrote 5 ints successfully.
Caught expected bounds violation.
Last valid value: 500
```

### Level 3 — Advanced

```java
// File: OffHeapStructLayout.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.VarHandle;

public class OffHeapStructLayout {
    // Describe a struct-like layout: { int id; double price; } off-heap
    static final MemoryLayout POINT_LAYOUT = MemoryLayout.structLayout(
            MemoryLayouts.JAVA_INT.withName("id"),
            MemoryLayouts.JAVA_DOUBLE.withName("price")
    );

    public static void main(String[] args) {
        VarHandle idHandle = POINT_LAYOUT.varHandle(int.class, MemoryLayout.PathElement.groupElement("id"));
        VarHandle priceHandle = POINT_LAYOUT.varHandle(double.class, MemoryLayout.PathElement.groupElement("price"));

        try (MemorySegment segment = MemorySegment.allocateNative(POINT_LAYOUT)) {
            idHandle.set(segment, 1001);
            priceHandle.set(segment, 49.99);

            int id = (int) idHandle.get(segment);
            double price = (double) priceHandle.get(segment);

            System.out.println("Off-heap record: id=" + id + ", price=" + price);
            System.out.println("Struct size in bytes: " + POINT_LAYOUT.byteSize());
        }
    }
}
```

**How to run:**
```
javac --add-modules jdk.incubator.foreign --release 16 OffHeapStructLayout.java
java --add-modules jdk.incubator.foreign OffHeapStructLayout
```

Expected output:
```
Off-heap record: id=1001, price=49.99
Struct size in bytes: 16
```

Level 3 moves from raw byte offsets to a **named, structured layout** — `MemoryLayout.structLayout(...)` describes a struct-like shape (`id` as a 4-byte int, `price` as an 8-byte double), and `VarHandle`s derived from named path elements (`"id"`, `"price"`) let code read and write fields by name rather than by manually tracked byte offsets, closely mirroring how a native C struct would be accessed while remaining fully bounds-checked Java code.

## 6. Walkthrough

1. `POINT_LAYOUT` is defined as a `MemoryLayout.structLayout(...)` combining a named `int` field (`"id"`) and a named `double` field (`"price"`) — this describes the *shape* of an off-heap record without allocating anything yet, similar to declaring a C `struct` definition.
2. `POINT_LAYOUT.varHandle(int.class, PathElement.groupElement("id"))` derives a `VarHandle` capable of reading/writing exactly the `"id"` field within any `MemorySegment` laid out according to `POINT_LAYOUT` — the path element `"id"` navigates to that specific named member of the struct layout, and the resulting `VarHandle` knows its byte offset and size automatically.
3. `MemorySegment.allocateNative(POINT_LAYOUT)` allocates a new block of off-heap memory sized and aligned exactly to fit `POINT_LAYOUT` (in this case, `16` bytes: 4 for `int`, plus alignment padding, plus 8 for `double`), returned as `segment`.
4. `idHandle.set(segment, 1001)` writes the integer `1001` into the `"id"` field's location within `segment` — the `VarHandle` computes the correct byte offset internally, so calling code never manually computes an offset like `0L` or `4L`.
5. `priceHandle.set(segment, 49.99)` similarly writes the `double` value into the `"price"` field's location, which the layout places immediately after the (possibly padded) `id` field.
6. `idHandle.get(segment)` and `priceHandle.get(segment)` read the two values back out, each cast from `Object` (the `VarHandle` API's generic return type) to the expected primitive type (`int`, `double`).
7. The two retrieved values are printed, confirming a full off-heap round trip: values written by field name, read back by field name, entirely without manual byte-offset arithmetic — while `POINT_LAYOUT.byteSize()` reports the total size (16 bytes) the layout computed for the whole struct, useful for confirming the allocation size matches expectations.
8. When the `try`-with-resources block ends, `segment.close()` is called implicitly, deterministically releasing the off-heap memory back to the operating system — no garbage collector cycle is needed or involved.

```
MemoryLayout.structLayout(int "id", double "price")
        │
   varHandle("id"), varHandle("price")  ← know their own byte offsets
        │
MemorySegment.allocateNative(layout) ──► 16-byte off-heap block
        │
idHandle.set(segment, 1001) / priceHandle.set(segment, 49.99)
        │
idHandle.get(segment) / priceHandle.get(segment) ──► id=1001, price=49.99
```

## 7. Gotchas & takeaways

> This was the **third** incubation round (following Java 14 and Java 15) for the Foreign-Memory Access API — still requiring `--add-modules jdk.incubator.foreign`, still subject to API changes in subsequent releases, and not yet standardized. The API continued to evolve for further rounds after Java 16 before eventually being unified with the Foreign Linker API into a single, later-standardized Foreign Function & Memory API — code written against this specific incubator round is not guaranteed to compile unchanged against later JDK versions.

- Every `MemorySegment` access is bounds-checked — an out-of-bounds read or write throws `IndexOutOfBoundsException` rather than corrupting memory, which is the core safety improvement over both `sun.misc.Unsafe` and raw JNI memory manipulation.
- `MemorySegment`s allocated via `allocateNative(...)` must be explicitly closed (via `try`-with-resources, as shown, or manual `.close()`) — they are **not** garbage-collected, and failing to close one leaks native memory for the life of the process.
- `MemoryLayout` and its derived `VarHandle`s (Level 3's struct-style access) are the recommended way to access structured off-heap data — they eliminate manual byte-offset bookkeeping and automatically account for field sizes and alignment padding.
- This API is closely related to, and eventually merged with, the [Foreign Linker API](0693-foreign-linker-api-incubator.md) — the two together (memory access plus native function calls) form what Project Panama envisioned as a complete, safe native-interoperability story for Java.
- Given the rapid API evolution across incubator rounds, treat any specific class/method names from this era as historical reference rather than a stable API to build long-lived production code against without close attention to the JDK version in use.
