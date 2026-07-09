---
card: java
gi: 737
slug: foreign-function-memory-api-2nd-preview
title: Foreign Function & Memory API (2nd preview)
---

## 1. What it is

**Java 20** (JEP 434) is the **second preview** of the [Foreign Function & Memory API](0729-foreign-function-memory-api-preview.md), continuing directly from its first preview round in Java 19. The core capabilities — off-heap `MemorySegment`s with explicit-lifetime `MemorySession`s, and native function calls via `Linker` and `FunctionDescriptor` — carry forward, with this round's changes centered on API refinement: clearer separation between segment allocation and the session managing its lifetime, and adjustments to how upcalls (native code calling *back* into Java) are configured. As with every round of this feature so far, it remains a preview requiring `--enable-preview`, continuing to converge toward its eventual finalized shape.

## 2. Why & when

By the second preview, the incubator-era foundational design (segments, sessions, linkers, downcalls) had already been validated across two incubator rounds and one prior preview round; this round's refinements come from feedback specifically about ergonomics and edge cases discovered through real preview usage — how allocation APIs compose with session lifetimes, and how the less-common but important **upcall** direction (a native C function invoking a Java method as a callback, the mirror image of a downcall) should be configured safely. Upcalls matter for a real class of native interop that downcalls alone can't cover: C libraries that take a function pointer argument and call it later — a `qsort`-style comparator, an event callback, a native library's plugin hook. Supporting this direction safely (constructing a native-callable function pointer that, when invoked from C, safely re-enters the JVM and runs Java code) is meaningfully more delicate than downcalls, since it has to guard against a native caller invoking the callback after the JVM-side context it depends on has already been torn down. This round's preview refinements are specifically about getting that upcall configuration API right before finalization. Use this API, and specifically its upcall support, when native interop needs to go both directions — not just Java calling into C, but C calling back into Java.

## 3. Core concept

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

// Downcall: Java calls a native function (unchanged pattern from earlier rounds).
Linker linker = Linker.nativeLinker();
MethodHandle strlen = linker.downcallHandle(
    linker.defaultLookup().find("strlen").orElseThrow(),
    FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

// Upcall: a native function calls BACK into Java — this round refines how
// the callback's native-callable function pointer is created and scoped.
MethodHandle javaCallback = /* a MethodHandle to a Java method */;
MemorySegment callbackStub = linker.upcallStub(
    javaCallback,
    FunctionDescriptor.of(ValueLayout.JAVA_INT, ValueLayout.JAVA_INT, ValueLayout.JAVA_INT),
    session); // the stub's lifetime is tied to this session
```

The upcall stub is itself a `MemorySegment` — a real, native-callable function pointer — whose validity is bound to the `MemorySession` that created it, just like any other off-heap resource this API manages.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A downcall lets Java call a native function directly; an upcall creates a native-callable function pointer backed by a Java method, letting native code call back into the JVM, with the pointer's validity tied to a MemorySession">
  <rect x="30" y="30" width="260" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Downcall</text>
  <text x="160" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java  --calls-->  native function</text>
  <text x="160" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">e.g. strlen(), sqrt()</text>

  <rect x="350" y="30" width="260" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Upcall (this round's focus)</text>
  <text x="480" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">native function --calls--&gt;  Java method</text>
  <text x="480" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">e.g. qsort() comparator callback</text>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Both directions cross the same JVM/native boundary,</text>
  <text x="320" y="160" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">but travel opposite ways across it</text>
</svg>

Downcalls and upcalls are mirror images of the same JVM/native boundary crossing.

## 5. Runnable example

Scenario: sorting an array of native integers using the C standard library's `qsort`, which requires a Java-written comparator function to be callable *from* native code — the canonical upcall use case. It grows from a basic downcall baseline (calling `abs` from libc), to setting up an upcall stub wrapping a Java comparator method, to actually invoking native `qsort` with that Java-backed comparator and reading the sorted result back from off-heap memory.

### Level 1 — Basic

```java
// File: DowncallBasic.java
// Run with --enable-preview: FFM API is a 2nd preview feature in Java 20.
// Establishes the downcall baseline before introducing upcalls in later levels.
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class DowncallBasic {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        MethodHandle abs = linker.downcallHandle(
                linker.defaultLookup().find("abs").orElseThrow(),
                FunctionDescriptor.of(ValueLayout.JAVA_INT, ValueLayout.JAVA_INT));

        int result = (int) abs.invoke(-42);
        System.out.println("native abs(-42) = " + result);
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview DowncallBasic.java
java --enable-preview --enable-native-access=ALL-UNNAMED DowncallBasic
```

Expected output:
```
native abs(-42) = 42
```

### Level 2 — Intermediate

```java
// File: UpcallSetupIntermediate.java
// Builds an upcall stub wrapping a Java comparator method, and verifies the
// stub itself is a valid, real function-pointer MemorySegment — the setup
// step before actually handing it to a native function in Level 3.
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

public class UpcallSetupIntermediate {
    // This is the Java method that native code will call back into.
    // qsort's comparator signature: int compare(const void *a, const void *b)
    static int compareInts(MemorySegment a, MemorySegment b) {
        int valueA = a.get(ValueLayout.JAVA_INT, 0);
        int valueB = b.get(ValueLayout.JAVA_INT, 0);
        return Integer.compare(valueA, valueB);
    }

    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();

        MethodHandle comparatorHandle = MethodHandles.lookup().findStatic(
                UpcallSetupIntermediate.class, "compareInts",
                MethodType.methodType(int.class, MemorySegment.class, MemorySegment.class));

        FunctionDescriptor comparatorDescriptor = FunctionDescriptor.of(
                ValueLayout.JAVA_INT, ValueLayout.ADDRESS, ValueLayout.ADDRESS);

        try (MemorySession session = MemorySession.openConfined()) {
            MemorySegment upcallStub = linker.upcallStub(comparatorHandle, comparatorDescriptor, session);
            System.out.println("Upcall stub created: " + upcallStub);
            System.out.println("Is a valid native function pointer: " + (upcallStub.address() != 0));
        } // stub becomes invalid the instant this session closes
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview UpcallSetupIntermediate.java
java --enable-preview --enable-native-access=ALL-UNNAMED UpcallSetupIntermediate
```

Expected output shape (exact address varies):
```
Upcall stub created: MemorySegment{address=0x7f2a3c001040, byteSize=0}
Is a valid native function pointer: true
```

### Level 3 — Advanced

```java
// File: QsortUpcallAdvanced.java
// Actually calls native qsort() from libc, passing the Java comparator's
// upcall stub as the function-pointer argument — native code genuinely
// calls back into the JVM once per comparison during the sort.
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

public class QsortUpcallAdvanced {
    static int callCount = 0;

    static int compareInts(MemorySegment a, MemorySegment b) {
        callCount++;
        int valueA = a.get(ValueLayout.JAVA_INT, 0);
        int valueB = b.get(ValueLayout.JAVA_INT, 0);
        return Integer.compare(valueA, valueB);
    }

    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();

        // The comparator, exposed as a native-callable upcall stub.
        MethodHandle comparatorHandle = MethodHandles.lookup().findStatic(
                QsortUpcallAdvanced.class, "compareInts",
                MethodType.methodType(int.class, MemorySegment.class, MemorySegment.class));
        FunctionDescriptor comparatorDescriptor = FunctionDescriptor.of(
                ValueLayout.JAVA_INT, ValueLayout.ADDRESS, ValueLayout.ADDRESS);

        // qsort's real C signature:
        // void qsort(void *base, size_t nmemb, size_t size, int (*compar)(const void*, const void*))
        MethodHandle qsort = linker.downcallHandle(
                linker.defaultLookup().find("qsort").orElseThrow(),
                FunctionDescriptor.ofVoid(ValueLayout.ADDRESS, ValueLayout.JAVA_LONG,
                        ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

        try (MemorySession session = MemorySession.openConfined()) {
            MemorySegment upcallStub = linker.upcallStub(comparatorHandle, comparatorDescriptor, session);

            int[] values = {5, 2, 8, 1, 9, 3};
            MemorySegment array = MemorySegment.allocateNative(
                    ValueLayout.JAVA_INT.byteSize() * values.length, session);
            for (int i = 0; i < values.length; i++) {
                array.setAtIndex(ValueLayout.JAVA_INT, i, values[i]);
            }

            System.out.println("Before: " + java.util.Arrays.toString(values));

            qsort.invoke(array, (long) values.length, ValueLayout.JAVA_INT.byteSize(), upcallStub);

            int[] sorted = new int[values.length];
            for (int i = 0; i < values.length; i++) {
                sorted[i] = array.getAtIndex(ValueLayout.JAVA_INT, i);
            }
            System.out.println("After:  " + java.util.Arrays.toString(sorted));
            System.out.println("Java comparator was called " + callCount + " times by native qsort()");
        }
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview QsortUpcallAdvanced.java
java --enable-preview --enable-native-access=ALL-UNNAMED QsortUpcallAdvanced
```

Expected output (exact call count may vary slightly by libc implementation, but will be nonzero):
```
Before: [5, 2, 8, 1, 9, 3]
After:  [1, 2, 3, 5, 8, 9]
Java comparator was called 12 times by native qsort()
```

## 6. Walkthrough

1. `QsortUpcallAdvanced.main` first builds two handles: `comparatorHandle`, a plain Java `MethodHandle` referencing the static method `compareInts`, and `qsort`, a downcall handle for the native C library's `qsort` function — both constructed the same way earlier levels and the prior preview round's examples build downcall handles.
2. `linker.upcallStub(comparatorHandle, comparatorDescriptor, session)` is the step unique to this round's focus: it generates a genuine, native-callable **function pointer** — represented as a `MemorySegment` — that, when invoked from native code with two `void*` arguments matching `comparatorDescriptor`'s shape, transitions back into the JVM and runs `compareInts`. This `MemorySegment`'s validity is explicitly tied to `session`, exactly like an ordinary allocated memory segment would be.
3. `array` is allocated off-heap and filled with the six unsorted integers — this is the buffer `qsort` will sort *in place*, native-side, the same way it would sort a C array.
4. `qsort.invoke(array, 6, 4, upcallStub)` performs the actual downcall into native `qsort`, passing: the array's address, the element count (`6`), the element size in bytes (`4`, an `int`'s size), and — critically — `upcallStub`, the native function pointer wrapping the Java comparator, exactly where `qsort`'s C signature expects a `int (*compar)(const void*, const void*)` function pointer argument.
5. Inside native `qsort`'s implementation (genuine C library code, executing entirely outside the JVM), the sorting algorithm repeatedly needs to compare pairs of elements — and each time it does, it calls through the function pointer it was given. Because that pointer is `upcallStub`, each such call **re-enters the JVM**, invoking `compareInts` with two `MemorySegment` arguments pointing at the two array elements being compared right now, in native memory.
6. `compareInts` reads both values via `a.get(JAVA_INT, 0)` and `b.get(JAVA_INT, 0)`, compares them with `Integer.compare`, returns the result back across the boundary into native `qsort`, and increments `callCount` — a plain static field, safely mutable here since `qsort`'s calls happen sequentially on the single thread driving this downcall, not concurrently.
7. Once `qsort.invoke(...)` returns, the sort is complete — `array`'s contents have been rearranged in place by native code, using comparison decisions made entirely by Java code called back into via the upcall stub. Reading `array` back with `getAtIndex` shows the sorted result, and `callCount` confirms the Java comparator was genuinely invoked multiple times by native code during the sort, not merely set up and left unused.

```
Java: qsort.invoke(array, 6, 4, upcallStub)
        |
        v
native qsort() (real C library code, running outside the JVM)
        |
        | needs to compare element i and j
        v
   calls through upcallStub(ptr_i, ptr_j)  ------>  RE-ENTERS THE JVM
        |                                                  |
        |                                          compareInts(a, b) runs
        |                                          reads a.get(INT,0), b.get(INT,0)
        |                                          returns comparison result
        |<-------------------------------------------------|
   continues sorting using that result
        |
        (repeats for every comparison qsort needs)
        |
        v
   array is now sorted in place; qsort.invoke() returns to Java
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 20** (second preview of the Foreign Function & Memory API) — requiring `--enable-preview` for both compilation and execution, plus `--enable-native-access=ALL-UNNAMED` for the native calls themselves; upcall configuration specifically was a focus of refinement in this round and continued to evolve before final standardization.
- An upcall stub is only valid for the lifetime of the `MemorySession` that created it — if native code retains and tries to call the function pointer *after* that session has closed, the result is undefined behavior (potentially a JVM crash), since the stub no longer refers to a live, callable target; this is why the session in Level 3 stays open for the entire duration of the `qsort` call.
- Java code invoked via an upcall (like `compareInts`) runs on whatever thread the native code happens to call it from — for `qsort`, that's the same thread that initiated the downcall, but other native APIs (event loops, async callback registration) might invoke an upcall stub from a different native thread entirely, which is a real design consideration for thread-safety when writing upcall targets.
- Upcalls are the mechanism that makes this API genuinely bidirectional rather than Java-calls-native only — any C API taking a function pointer (sorting comparators, as shown here, but also signal handlers, iteration callbacks, and plugin hook systems) becomes usable from Java specifically because of upcall support.
- As with downcalls, correctness of the `FunctionDescriptor` passed to `upcallStub` matters enormously — it must exactly match the native function pointer type the C API actually expects to call, since a mismatched descriptor (wrong argument types, wrong count) produces undefined, potentially crash-inducing behavior rather than a catchable Java exception.
