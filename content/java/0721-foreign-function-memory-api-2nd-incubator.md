---
card: java
gi: 721
slug: foreign-function-memory-api-2nd-incubator
title: Foreign Function & Memory API (2nd incubator)
---

## 1. What it is

**Java 18** (JEP 419) is the **second incubator** round of the **Foreign Function & Memory API**, the successor project to the old `sun.misc.Unsafe`-based native interop and, longer-term, the intended replacement for JNI (Java Native Interface). It lets Java code allocate and manage memory *outside* the garbage-collected heap (via `MemorySegment` and `MemorySession`, the successors to Java 17's `MemoryAddress`/`MemorySegment` split), and call native functions in C libraries directly from Java (via `Linker`, `FunctionDescriptor`, and method handles) — without writing any native glue code or a single line of C. Being an *incubator* module (`jdk.incubator.foreign`), it requires an explicit `--add-modules` flag to use, and the API surface is still evolving between releases; this second round merged and refined the memory-access and function-call halves that had been developed somewhat separately before.

## 2. Why & when

Calling native code from Java has historically meant JNI: writing a `.c` file with JNI-specific function signatures, compiling it into a platform-specific shared library, and loading it with `System.loadLibrary`. This works, but it's slow to iterate on, requires a C toolchain and per-platform builds, and any mistake in the hand-written glue code (a wrong type size, a missed null check) tends to crash the whole JVM with a native segfault rather than throwing a catchable Java exception. Off-heap memory access had a parallel problem: the only fast way to work with memory outside the GC-managed heap was `sun.misc.Unsafe`, an internal, unsupported, and increasingly restricted API that JEP 471 in later JDKs would go on to remove entirely. The Foreign Function & Memory API was designed to solve both problems together and safely: `MemorySegment` gives bounds-checked, deterministic-lifetime access to off-heap memory without `Unsafe`, and `Linker` lets Java call a native function's address directly, described by its argument and return types, with no C glue code and no separate native library to compile. This matters most for JVM workloads that need to touch large off-heap buffers (memory-mapped files, native interop for machine-learning runtimes, high-performance I/O) or call into an existing C library without writing and maintaining JNI shims. Because it's still incubating in Java 18, treat it as *preview-quality*: useful to learn and prototype with, but expect its exact types and method names to keep shifting release to release until finalization.

## 3. Core concept

```java
// Off-heap memory: allocate, write, read, free — all bounds-checked, no Unsafe.
try (MemorySession session = MemorySession.openConfined()) {
    MemorySegment segment = MemorySegment.allocateNative(4, session); // 4 bytes, off-heap
    segment.set(ValueLayout.JAVA_INT, 0, 42);
    int value = segment.get(ValueLayout.JAVA_INT, 0);
} // memory is freed automatically when the session closes

// Calling a native C function (e.g. strlen from libc) with no JNI glue code:
Linker linker = Linker.nativeLinker();
MethodHandle strlen = linker.downcallHandle(
    linker.defaultLookup().lookup("strlen").get(),
    FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));
```

The `MemorySession` (renamed from `ResourceScope` mid-incubation) ties the lifetime of off-heap memory to a scope the developer controls explicitly, rather than to garbage collection.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java heap memory is garbage collected; a MemorySegment lives off-heap with a lifetime tied to an explicit MemorySession, and Linker lets Java call native C functions directly without JNI glue code">
  <rect x="20" y="30" width="220" height="80" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="130" y="52" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java heap</text>
  <text x="130" y="76" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">objects, GC-managed</text>
  <text x="130" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">lifetime: automatic</text>

  <rect x="260" y="30" width="220" height="80" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">MemorySegment (off-heap)</text>
  <text x="370" y="76" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bounds-checked access</text>
  <text x="370" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">lifetime: MemorySession</text>

  <rect x="500" y="30" width="120" height="80" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Native lib</text>
  <text x="560" y="76" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">libc, .so/.dylib</text>

  <line x1="480" y1="70" x2="500" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#a4)"/>
  <text x="490" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Linker.downcallHandle — no JNI glue code needed</text>

  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Off-heap memory gets an explicit lifetime; native calls go straight from Java to a function's address, with no intermediate C glue code.

## 5. Runnable example

Scenario: working with a small block of off-heap memory representing a fixed-size record, starting with plain allocate/read/write, then adding multiple fields with a `MemoryLayout`, then calling an actual native C library function (`strlen`) to compute the length of a Java string entirely through off-heap memory and a downcall — no JNI, no compiled native code of our own.

### Level 1 — Basic

```java
// File: OffHeapBasic.java
// Run with --add-modules jdk.incubator.foreign — incubator module in Java 18.
import jdk.incubator.foreign.*;
import java.lang.invoke.VarHandle;

public class OffHeapBasic {
    public static void main(String[] args) {
        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment segment = MemorySegment.allocateNative(4, scope); // 4 bytes off-heap
            VarHandle intHandle = ValueLayout.JAVA_INT.varHandle();

            intHandle.set(segment, 42);
            int value = (int) intHandle.get(segment);

            System.out.println("Stored and read back: " + value);
        } // memory freed here, when the scope closes
    }
}
```

**How to run:**
```
javac --release 18 --add-modules jdk.incubator.foreign OffHeapBasic.java
java --add-modules jdk.incubator.foreign OffHeapBasic
```

Expected output:
```
Stored and read back: 42
```

### Level 2 — Intermediate

```java
// File: OffHeapIntermediate.java
// Adds a structured record layout with multiple fields (id: int, score: double),
// the real-world concern of laying out several values in one off-heap block
// with correct offsets, instead of one bare primitive.
import jdk.incubator.foreign.*;
import java.lang.invoke.VarHandle;

public class OffHeapIntermediate {
    public static void main(String[] args) {
        MemoryLayout recordLayout = MemoryLayout.structLayout(
                ValueLayout.JAVA_INT.withName("id"),
                ValueLayout.JAVA_DOUBLE.withName("score"));

        VarHandle idHandle = recordLayout.varHandle(MemoryLayout.PathElement.groupElement("id"));
        VarHandle scoreHandle = recordLayout.varHandle(MemoryLayout.PathElement.groupElement("score"));

        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment record = MemorySegment.allocateNative(recordLayout, scope);

            idHandle.set(record, 101);
            scoreHandle.set(record, 98.6);

            System.out.println("id=" + idHandle.get(record) + " score=" + scoreHandle.get(record));
            System.out.println("Total struct size: " + recordLayout.byteSize() + " bytes");
        }
    }
}
```

**How to run:**
```
javac --release 18 --add-modules jdk.incubator.foreign OffHeapIntermediate.java
java --add-modules jdk.incubator.foreign OffHeapIntermediate
```

Expected output:
```
id=101 score=98.6
Total struct size: 16 bytes
```

The struct size reflects the `int` and `double` fields plus any padding the layout inserts for alignment — visible proof that `MemoryLayout` computes real memory geometry, not just logical field access.

### Level 3 — Advanced

```java
// File: NativeStrlenAdvanced.java
// Calls the real native libc function strlen() on a Java string, entirely
// through off-heap memory and a downcall handle — no JNI, no custom native
// library compiled for this example.
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;

public class NativeStrlenAdvanced {
    public static void main(String[] args) throws Throwable {
        CLinker linker = CLinker.getInstance();

        MethodHandle strlen = linker.downcallHandle(
                CLinker.systemLookup().lookup("strlen").orElseThrow(),
                MethodType.methodType(long.class, MemoryAddress.class),
                FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER));

        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            String javaString = "Hello from off-heap memory!";
            MemorySegment nativeString = CLinker.toCString(javaString, scope);

            long length = (long) strlen.invoke(nativeString.address());

            System.out.println("Java string: \"" + javaString + "\"");
            System.out.println("Java length (chars): " + javaString.length());
            System.out.println("Native strlen (bytes): " + length);
        }
    }
}
```

**How to run:**
```
javac --release 18 --add-modules jdk.incubator.foreign NativeStrlenAdvanced.java
java --enable-native-access=ALL-UNNAMED --add-modules jdk.incubator.foreign NativeStrlenAdvanced
```

Expected output (on a platform where libc's `strlen` is resolvable, such as Linux or macOS):
```
Java string: "Hello from off-heap memory!"
Java length (chars): 28
Native strlen (bytes): 28
```

Note: exact class and method names in this second-incubator API (`CLinker`, `downcallHandle` signatures) shifted again in later JDK releases as the API continued evolving toward finalization; this reflects the actual Java 18 incubator surface.

## 6. Walkthrough

1. `NativeStrlenAdvanced.main` first obtains a `CLinker`, the object responsible for bridging Java method calls to native function calls — this is the Java 18 incubator's entry point for what later, finalized versions of the API call simply `Linker`.
2. `CLinker.systemLookup().lookup("strlen")` searches the process's already-loaded native libraries (including the C standard library, `libc`) for a symbol named `strlen`, and returns its memory address if found — no `System.loadLibrary` call and no custom shared library needed, since `strlen` already lives in a library every process links against.
3. `linker.downcallHandle(address, methodType, functionDescriptor)` builds a `MethodHandle` that, when invoked, transitions from the JVM into native code at that address, passing arguments according to the C calling convention described by `FunctionDescriptor.of(C_LONG, C_POINTER)` — "returns a C `long`, takes one pointer argument" — matching `strlen`'s real C signature, `size_t strlen(const char *s)`.
4. Inside the `try`-with-resources block, `CLinker.toCString(javaString, scope)` allocates an off-heap, null-terminated, UTF-8-encoded copy of the Java string — this is the step that actually crosses from the managed Java heap into unmanaged native memory, since C string functions expect a null-terminated byte buffer, not a Java `String` object.
5. `strlen.invoke(nativeString.address())` performs the actual downcall: control leaves the JVM, `strlen` walks the native byte buffer counting bytes until the terminating null, and returns that count as a native `long`, which the method handle marshals back into a Java `long`.
6. The program prints both `javaString.length()` (Java's *character* count, using UTF-16 code units) and the native `strlen` result (a *byte* count in UTF-8) — for this particular ASCII-only string they happen to match, but the distinction matters for any string containing multi-byte UTF-8 characters, where the two counts would diverge.
7. When the `try`-with-resources block exits, `scope.close()` (implicit) frees the off-heap native string buffer — its lifetime was tied explicitly to `scope`, not to Java garbage collection, so it is reclaimed deterministically the moment the block ends, rather than at some unpredictable future GC cycle.

```
Java String "Hello..."
     |
     v
CLinker.toCString(str, scope)  -> off-heap MemorySegment (null-terminated UTF-8 bytes)
     |
     v
strlen.invoke(segment.address())
     |                                    [JVM  ->  native code, real function call]
     v
native strlen() walks bytes until \0, returns count
     |
     v
long length  (back in Java, via the MethodHandle's return marshalling)
```

## 7. Gotchas & takeaways

> This is an **incubator module** (`jdk.incubator.foreign`) in Java 18 — it requires `--add-modules jdk.incubator.foreign` to compile and run, is not part of the standard `java.*` API, and its class names and method signatures (as seen with `CLinker`, later renamed and reshaped again in subsequent JDK releases before final standardization) are explicitly **not stable** between JDK versions.
- Off-heap `MemorySegment`s are **not garbage collected** — their lifetime is tied to a `ResourceScope` (later renamed `MemorySession` / `Arena` in subsequent JDKs). Forgetting to close the scope, or closing it while a downcall using its memory is still in flight, are real bugs this API is designed to catch with runtime checks rather than crashing silently the way raw pointer misuse in C would.
- Native downcalls can still crash the JVM process if the native function itself is buggy or the `FunctionDescriptor` describes the wrong signature — the API adds safety around memory *access* (bounds checking, lifetime tracking) but cannot make an arbitrary native function itself safe to call.
- `MemoryLayout.structLayout(...)` (Level 2) computes real byte offsets and alignment padding, matching how a C compiler would lay out an equivalent `struct` — this is what makes it possible to read/write native structs from Java without hand-computing offsets.
- The eventual, finalized form of this API (integrated as a standard, non-incubating feature in later LTS releases) is what modern high-performance native interop in Java is built on — worth learning the underlying concepts (segments, sessions/arenas, linkers, downcalls) now even though the exact Java 18 class names shown here changed before finalization.
