---
card: java
gi: 729
slug: foreign-function-memory-api-preview
title: Foreign Function & Memory API (preview)
---

## 1. What it is

**Java 19** (JEP 424) graduates the Foreign Function & Memory API from **incubator** status (as it was in its [second incubator round in Java 18](0721-foreign-function-memory-api-2nd-incubator.md)) to a **preview** feature, now living in the standard `java.lang.foreign` package instead of `jdk.incubator.foreign`. This is a meaningful status upgrade: incubator modules are explicitly experimental extensions outside the normal `java.*` namespace, while preview features are drafts of what will become permanent, standard Java APIs — closer to finalization, with the same core capabilities (off-heap `MemorySegment`s with explicit-lifetime `MemorySession`s, and native function calls via `Linker`) but a more settled design following two rounds of incubator feedback.

## 2. Why & when

Moving from incubator to preview status signals the API's design has matured enough that the platform team is confident enough in its shape to put it through the language's formal preview process — a more rigorous, higher-visibility bar than incubation, requiring a JEP and broad review before it can later be finalized as a permanent standard feature. The underlying motivation is unchanged from the incubator rounds: give Java code safe, bounds-checked, deterministic-lifetime access to off-heap memory without `sun.misc.Unsafe`, and let Java call native C functions directly without hand-written JNI glue code. What's new in this preview round, compared to Java 18's second incubator, is a cleaned-up API surface: `MemorySession` now more clearly separates *confined* sessions (usable from one thread, closable explicitly, fastest) from *shared* sessions (usable from multiple threads, garbage-collected), and the linker API (`Linker`, replacing the incubator's `CLinker`) has a more direct, less ceremony-heavy method-handle-building path. Reach for this preview the same way as its incubator predecessor: prototyping and building code that needs off-heap memory management or native interop, while expecting the exact API surface to still shift somewhat before final standardization.

## 3. Core concept

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

// Off-heap memory, now in java.lang.foreign (not jdk.incubator.foreign)
try (MemorySession session = MemorySession.openConfined()) {
    MemorySegment segment = MemorySegment.allocateNative(4, session);
    segment.set(ValueLayout.JAVA_INT, 0, 42);
    int value = segment.get(ValueLayout.JAVA_INT, 0);
}

// Native calls via the renamed, streamlined Linker API
Linker linker = Linker.nativeLinker();
MethodHandle strlen = linker.downcallHandle(
    linker.defaultLookup().find("strlen").orElseThrow(),
    FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));
```

The core concepts — segments, sessions, layouts, linkers, downcalls — carry over directly from the incubator rounds; the package and some type names are what changed.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Foreign Function and Memory API progressed from an incubator module in Java 17 and 18 to a preview feature in java.lang.foreign in Java 19, on its way to full standardization">
  <rect x="20" y="60" width="160" height="70" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="85" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 17-18</text>
  <text x="100" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jdk.incubator.foreign</text>
  <text x="100" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">incubator, --add-modules</text>

  <line x1="185" y1="95" x2="245" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#a8)"/>

  <rect x="250" y="60" width="160" height="70" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 19</text>
  <text x="330" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">java.lang.foreign</text>
  <text x="330" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">preview, --enable-preview</text>

  <line x1="415" y1="95" x2="475" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a8)"/>

  <rect x="480" y="60" width="140" height="70" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="85" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Later JDKs</text>
  <text x="550" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">finalized, standard</text>

  <defs><marker id="a8" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Java 19's preview status is the middle step between incubation and full standardization.

## 5. Runnable example

Scenario: computing a checksum over a block of native memory representing sensor readings, growing from basic off-heap allocation and access, to a structured layout for multiple readings using `MemoryLayout`, to calling a real native C library function (`sqrt` from libm) on values pulled straight from off-heap memory — demonstrating the preview API's streamlined session and linker usage end to end.

### Level 1 — Basic

```java
// File: ForeignBasic.java
// Run with --enable-preview: FFM API is a preview feature in Java 19,
// living in java.lang.foreign (promoted from the jdk.incubator.foreign module).
import java.lang.foreign.*;

public class ForeignBasic {
    public static void main(String[] args) {
        try (MemorySession session = MemorySession.openConfined()) {
            MemorySegment segment = MemorySegment.allocateNative(4 * 4, session); // 4 ints

            for (int i = 0; i < 4; i++) {
                segment.setAtIndex(ValueLayout.JAVA_INT, i, (i + 1) * 10);
            }

            int sum = 0;
            for (int i = 0; i < 4; i++) {
                sum += segment.getAtIndex(ValueLayout.JAVA_INT, i);
            }

            System.out.println("Sum of off-heap values: " + sum);
        } // segment freed here
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ForeignBasic.java
java --enable-preview ForeignBasic
```

Expected output:
```
Sum of off-heap values: 100
```

### Level 2 — Intermediate

```java
// File: ForeignLayoutIntermediate.java
// Uses a structured MemoryLayout to represent an array of two-field sensor
// readings (id: int, temperature: double) laid out contiguously off-heap.
import java.lang.foreign.*;
import java.lang.invoke.VarHandle;

public class ForeignLayoutIntermediate {
    public static void main(String[] args) {
        MemoryLayout readingLayout = MemoryLayout.structLayout(
                ValueLayout.JAVA_INT.withName("id"),
                ValueLayout.JAVA_DOUBLE.withName("temperature"));
        SequenceLayout readingsLayout = MemoryLayout.sequenceLayout(3, readingLayout);

        VarHandle idHandle = readingsLayout.varHandle(
                MemoryLayout.PathElement.sequenceElement(), MemoryLayout.PathElement.groupElement("id"));
        VarHandle tempHandle = readingsLayout.varHandle(
                MemoryLayout.PathElement.sequenceElement(), MemoryLayout.PathElement.groupElement("temperature"));

        try (MemorySession session = MemorySession.openConfined()) {
            MemorySegment readings = MemorySegment.allocateNative(readingsLayout, session);

            int[] ids = {101, 102, 103};
            double[] temps = {21.5, 22.0, 19.8};
            for (int i = 0; i < 3; i++) {
                idHandle.set(readings, (long) i, ids[i]);
                tempHandle.set(readings, (long) i, temps[i]);
            }

            double sum = 0;
            for (int i = 0; i < 3; i++) {
                int id = (int) idHandle.get(readings, (long) i);
                double temp = (double) tempHandle.get(readings, (long) i);
                System.out.println("reading id=" + id + " temp=" + temp);
                sum += temp;
            }
            System.out.println("Average temperature: " + (sum / 3));
        }
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ForeignLayoutIntermediate.java
java --enable-preview ForeignLayoutIntermediate
```

Expected output:
```
reading id=101 temp=21.5
reading id=102 temp=22.0
reading id=103 temp=19.8
Average temperature: 21.1
```

### Level 3 — Advanced

```java
// File: ForeignSqrtAdvanced.java
// Calls the real native sqrt() from libm on values stored off-heap,
// combining structured layout access with a native downcall — the
// production-flavored shape: process off-heap data using native routines.
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class ForeignSqrtAdvanced {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        MethodHandle sqrt = linker.downcallHandle(
                linker.defaultLookup().find("sqrt").orElseThrow(),
                FunctionDescriptor.of(ValueLayout.JAVA_DOUBLE, ValueLayout.JAVA_DOUBLE));

        try (MemorySession session = MemorySession.openConfined()) {
            double[] values = {4.0, 9.0, 16.0, 25.0};
            MemorySegment segment = MemorySegment.allocateNative(
                    ValueLayout.JAVA_DOUBLE.byteSize() * values.length, session);

            for (int i = 0; i < values.length; i++) {
                segment.setAtIndex(ValueLayout.JAVA_DOUBLE, i, values[i]);
            }

            System.out.println("Computing square roots via native sqrt():");
            for (int i = 0; i < values.length; i++) {
                double input = segment.getAtIndex(ValueLayout.JAVA_DOUBLE, i);
                double result = (double) sqrt.invoke(input);
                System.out.println("sqrt(" + input + ") = " + result);
            }
        }
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ForeignSqrtAdvanced.java
java --enable-preview --enable-native-access=ALL-UNNAMED ForeignSqrtAdvanced
```

Expected output (on a platform where libm's `sqrt` resolves, such as Linux or macOS):
```
Computing square roots via native sqrt():
sqrt(4.0) = 2.0
sqrt(9.0) = 3.0
sqrt(16.0) = 4.0
sqrt(25.0) = 5.0
```

## 6. Walkthrough

1. `ForeignSqrtAdvanced.main` first obtains `Linker.nativeLinker()` — the Java 19 preview's streamlined entry point for native interop, replacing the incubator round's `CLinker.getInstance()`.
2. `linker.defaultLookup().find("sqrt")` searches the process's default set of loaded native libraries (which includes the C math library, `libm`, on POSIX systems) for the `sqrt` symbol, returning its address.
3. `linker.downcallHandle(address, FunctionDescriptor.of(JAVA_DOUBLE, JAVA_DOUBLE))` builds a `MethodHandle` describing `sqrt`'s real C signature — `double sqrt(double x)` — matching one `double` argument to one `double` return value, exactly as declared in `<math.h>`.
4. Inside the `try`-with-resources block, `MemorySegment.allocateNative(...)` reserves an off-heap block sized for four `double`s, and `setAtIndex` writes each of the four input values into it — this data now lives entirely outside the Java garbage-collected heap.
5. The loop then reads each value back with `getAtIndex` (proving the off-heap write/read round-trip works) and passes it to `sqrt.invoke(input)` — this call performs the actual downcall, transitioning execution from the JVM into the native `sqrt` function, computing the square root using the CPU's native floating-point square root instruction, and returning the result back into the JVM as a Java `double`.
6. Each computed result is printed immediately, showing the input pulled from off-heap memory and the output computed by a real native library call — no part of this computation happened via any Java-level math implementation; `Math.sqrt` was deliberately *not* used here, to demonstrate the actual native call path this API provides.
7. When the `try`-with-resources block exits, the `MemorySession` closes and the off-heap segment holding the four input `double`s is freed deterministically — its lifetime was tied explicitly to `session`, matching the same lifetime-management model introduced in the incubator rounds, now under the preview API's `java.lang.foreign.MemorySession`.

```
double[] values (off-heap MemorySegment)
        |
        v
segment.getAtIndex(JAVA_DOUBLE, i)  -> double input
        |
        v
sqrt.invoke(input)                          [JVM -> native libm sqrt(), real CPU sqrt instruction]
        |
        v
double result  (marshalled back into Java)
        |
        v
printed: "sqrt(16.0) = 4.0"
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 19** — `javac` needs `--release 19 --enable-preview` and `java` needs `--enable-preview`; running native downcalls generally also needs `--enable-native-access=ALL-UNNAMED` (or a specific module name) to acknowledge that native calls bypass the JVM's usual memory-safety guarantees. The exact package (`java.lang.foreign`) is stable relative to the incubator's `jdk.incubator.foreign`, but individual class and method names still shifted somewhat before final standardization in later JDKs.
- The promotion from incubator (Java 17-18) to preview (Java 19) reflects real design settling, not just a rename — `CLinker` became `Linker` with a more direct API, and `ResourceScope` became `MemorySession` with clearer confined-vs-shared semantics, both incorporating feedback from the incubator rounds.
- As with the incubator version, off-heap `MemorySegment`s are **not** garbage collected — their lifetime is bound to the `MemorySession` (or its later-renamed successor `Arena`) that allocated them, and using a segment after its session has closed throws, rather than silently reading freed memory, which is the core safety guarantee this API provides over raw pointers.
- `MemoryLayout.structLayout`/`sequenceLayout` (Level 2) compute real, C-compatible byte offsets and padding — the same technique used here for an array of sensor readings applies directly to interop with any native struct array a C library expects.
- Native downcalls (Level 3) can still crash the process if the native function itself is unsafe to call with the given arguments — this API adds safety around Java-side memory access and lifetime tracking, but cannot make an arbitrary native function's own behavior memory-safe.
- Treat this API's Java 19 preview surface as a strong preview of the eventual finalized shape, useful for learning the core concepts (segments, sessions/arenas, linkers, layouts, downcalls) now — but expect minor renames and refinements before any given preview release's exact class names become permanent.
