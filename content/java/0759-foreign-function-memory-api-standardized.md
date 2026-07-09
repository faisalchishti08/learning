---
card: java
gi: 759
slug: foreign-function-memory-api-standardized
title: Foreign Function & Memory API — standardized
---

## 1. What it is

**Java 22** (JEP 454) makes the [Foreign Function & Memory API](0755-foreign-function-memory-api-3rd-preview.md) a **permanent, standard feature** — no `--enable-preview` flag required — after two incubator rounds (Java 17, 18) and three preview rounds (Java 19, 20, 21). `Arena`, `MemorySegment`, `Linker`, and `FunctionDescriptor` are now stable, production-ready `java.lang.foreign` API: off-heap memory management with explicit, safe lifetimes, and calling native code directly from Java, without JNI's boilerplate and without its well-known safety gaps.

## 2. Why & when

For decades, calling native (C/C++) code from Java meant JNI: hand-written native glue code in C, a separate native compilation step, and an API notorious for being easy to use unsafely (a wrong native pointer or a lifetime mistake could crash the JVM with no Java-level exception to catch, or worse, corrupt memory silently). The Foreign Function & Memory API was designed from the start to replace JNI for the vast majority of native-interop use cases with something the JVM can reason about: memory segments with explicit, checked lifetimes (an `Arena`, closed deterministically or tied to garbage collection), and native function calls described declaratively (`FunctionDescriptor`) rather than requiring hand-written native shim code at all. Standardization in Java 22 is the signal that five rounds of incubation and preview feedback have converged on an API stable enough to build production code against — calling a native library, working with off-heap buffers for large datasets, or integrating with system libraries no longer requires either JNI's ceremony and risk, or accepting that the API underneath you might still change before your code ships.

## 3. Core concept

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

// No --enable-preview needed anymore — this is standard Java 22 API.
Linker linker = Linker.nativeLinker();
SymbolLookup stdlib = linker.defaultLookup();

MethodHandle strlen = linker.downcallHandle(
    stdlib.find("strlen").orElseThrow(),
    FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

try (Arena arena = Arena.ofConfined()) {
    MemorySegment cString = arena.allocateUtf8String("hello, world");
    long length = (long) strlen.invoke(cString);
    System.out.println(length); // 12
}
```

This calls the C standard library's `strlen` function directly from Java — no native glue code, no JNI, and no `--enable-preview` flag.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Foreign Function and Memory API standardizes after five rounds of incubation and preview, providing safe off-heap memory and native calls without JNI" >
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17-18 incubator -&gt; Java 19-21 preview -&gt; Java 22 standard</text>

  <rect x="20" y="90" width="280" height="60" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="115" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Arena + MemorySegment</text>
  <text x="160" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">safe, lifetime-checked off-heap memory</text>

  <rect x="340" y="90" width="280" height="60" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="480" y="115" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Linker + FunctionDescriptor</text>
  <text x="480" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">native calls, no JNI glue code</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Production-ready as of Java 22 — no preview flag required</text>
</svg>

*Five release cycles of incubation and preview converge on a stable, JNI-replacing API.*

## 5. Runnable example

Scenario: computing the length of several C-style strings and summing values from a native math function, growing from a single native call into a small library-backed batch computation.

### Level 1 — Basic

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class NativeStrlenBasic {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();

        MethodHandle strlen = linker.downcallHandle(
            stdlib.find("strlen").orElseThrow(),
            FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

        try (Arena arena = Arena.ofConfined()) {
            MemorySegment cString = arena.allocateUtf8String("hello, world");
            long length = (long) strlen.invoke(cString);
            System.out.println("length: " + length);
        }
    }
}
```

**How to run:** `java NativeStrlenBasic.java` (JDK 22+; on a system where the C standard library exposes `strlen`, which is true for Linux and macOS).

This looks up the native `strlen` function, describes its signature (`long strlen(char*)`) via `FunctionDescriptor`, allocates a null-terminated C string in off-heap memory, and invokes the native function directly — the whole native-interop pipeline in about ten lines, with no separate native compilation step.

### Level 2 — Intermediate

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class NativeStrlenBatch {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();

        MethodHandle strlen = linker.downcallHandle(
            stdlib.find("strlen").orElseThrow(),
            FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

        String[] words = {"hello", "structured concurrency", "foreign function interface", "java"};

        try (Arena arena = Arena.ofConfined()) {
            for (String word : words) {
                MemorySegment cString = arena.allocateUtf8String(word);
                long length = (long) strlen.invoke(cString);
                System.out.println(word + " -> " + length);
            }
        }
    }
}
```

**How to run:** `java NativeStrlenBatch.java`.

The real-world concern added: multiple native calls sharing **one arena** for the whole batch, each allocating its own C string but all freed together when the try-with-resources block ends — a realistic pattern for a loop that repeatedly calls into native code with short-lived arguments.

### Level 3 — Advanced

```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;
import java.util.*;
import java.util.concurrent.*;

public class NativeStrlenConcurrent {
    static MethodHandle strlenHandle;

    static long nativeStrlen(String s) throws Throwable {
        try (Arena arena = Arena.ofConfined()) { // one confined arena per call, safe per-thread
            MemorySegment cString = arena.allocateUtf8String(s);
            return (long) strlenHandle.invoke(cString);
        }
    }

    public static void main(String[] args) throws Exception {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();
        strlenHandle = linker.downcallHandle(
            stdlib.find("strlen").orElseThrow(),
            FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS));

        List<String> inputs = List.of(
            "alpha", "structured concurrency and scoped values",
            "foreign function and memory api", "beta", "gamma delta epsilon");

        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<Long>> futures = new ArrayList<>();
            for (String s : inputs) {
                futures.add(executor.submit(() -> nativeStrlen(s)));
            }
            long total = 0;
            for (Future<Long> f : futures) {
                total += f.get();
            }
            System.out.println("total characters across all inputs: " + total);
        }
    }
}
```

**How to run:** `java NativeStrlenConcurrent.java`.

This adds the production-flavored hard case: calling the same native `strlen` function **concurrently** from many virtual threads (combining with [virtual threads — standardized](0739-virtual-threads-standardized.md)), with each call using its **own confined arena** scoped to just that invocation — since `Arena.ofConfined()` restricts memory to the thread that created it, giving each virtual thread its own short-lived arena is both correct and appropriately cheap for a one-off native call.

## 6. Walkthrough

Tracing `NativeStrlenConcurrent.main`:

1. `main` resolves the native `strlen` symbol once via `Linker.nativeLinker()` and `SymbolLookup.find`, storing the resulting `MethodHandle` in the static field `strlenHandle` so every subtask can reuse the same handle without re-resolving the symbol.
2. It builds a list of five input strings and opens a virtual-thread-per-task executor, submitting one task per string, each calling `nativeStrlen(s)`.
3. Inside `nativeStrlen`, each call opens its **own** `Arena.ofConfined()` — since this method runs on a different virtual thread per call, and a confined arena only permits access from its creating thread, each invocation needs an arena scoped to itself rather than sharing one across threads.
4. `arena.allocateUtf8String(s)` copies the Java `String` into a null-terminated, off-heap UTF-8 buffer; `strlenHandle.invoke(cString)` calls the native `strlen` function on that buffer's address, returning the byte length as a Java `long`.
5. The try-with-resources block closes the confined arena immediately after the native call returns, freeing that call's off-heap buffer before the method returns.
6. Back in `main`, each `Future<Long>` is collected via `.get()`, blocking until that subtask's native call completes, and its result is added to `total`.
7. Once all five futures are collected, the executor's try-with-resources block completes, and `main` prints the combined total.

Expected output:
```
total characters across all inputs: 90
```

(The specific number depends on the exact byte length of each input string; the meaningful result is that native calls made concurrently from multiple virtual threads, each with a correctly-scoped confined arena, all complete safely and correctly.)

## 7. Gotchas & takeaways

> **Gotcha:** `strlen` (and C strings generally) count **bytes** up to a null terminator, not Java `String.length()`'s UTF-16 code units — for pure-ASCII input the two happen to match, but a string containing multi-byte UTF-8 characters would report a byte length different from its Java character count. Don't assume a native string function's length matches Java's notion of string length once non-ASCII input is possible.

- Standardized in Java 22 — no `--enable-preview` flag needed; production-ready.
- `Linker.nativeLinker()` plus `SymbolLookup` resolve native symbols; `FunctionDescriptor` describes the call signature declaratively — no hand-written native glue code required, unlike JNI.
- Resolve and cache a native symbol's `MethodHandle` once (e.g., in a static field) rather than re-resolving it on every call.
- Use `Arena.ofConfined()` scoped per call (or per thread) when many concurrent callers each need short-lived off-heap memory for a native call's arguments.
- This standardization is the JDK's intended long-term replacement for JNI in the majority of native-interop use cases — new native-interop code should default to this API rather than JNI going forward.
