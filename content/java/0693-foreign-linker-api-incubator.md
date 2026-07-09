---
card: java
gi: 693
slug: foreign-linker-api-incubator
title: Foreign Linker API (incubator)
---

## 1. What it is

**Java 16** introduced the **Foreign Linker API** as an **incubator module** (JEP 389, part of the broader Project Panama effort) — an API for calling **native code** (functions in C libraries, for example) directly from Java, without writing any JNI (Java Native Interface) glue code in C/C++. Historically, calling into a native library from Java meant writing a JNI shim: hand-written native C code, compiled separately per platform, that bridged Java method calls to native function calls. The Foreign Linker API lets Java code look up a native function by its symbol name and invoke it directly through a `MethodHandle`, with the JVM handling the calling-convention details (how arguments are passed in registers/stack per the platform's ABI) automatically.

## 2. Why & when

JNI has been Java's only official way to call native code since Java 1.1, and it has always been notoriously painful: every native function you want to call needs hand-written C glue code compiled for every target platform, error handling across the Java/native boundary is fragile, and a single mistake in the native glue code can crash the entire JVM process with no recoverable exception. Project Panama's Foreign Linker API set out to make calling native code a pure-Java affair — no separate native compilation step, no C glue code to maintain — letting Java code express "call this C function with this signature" directly, with the JVM itself generating the appropriate native call stub at runtime based on a described function signature. Reach for it (understanding it remained an incubating, evolving API for several JDK releases beyond 16) when you need to call into an existing native library (a system API, a high-performance native math library, an OS-specific capability) without writing or maintaining separate JNI glue code per platform.

## 3. Core concept

```java
// Java 16 incubator API — requires --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;

// Look up the C standard library's strlen() function and call it from Java
CLinker linker = CLinker.getInstance();
MethodHandle strlen = linker.downcallHandle(
        CLinker.systemLookup().lookup("strlen").get(),
        MethodType.methodType(long.class, MemoryAddress.class),
        FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER)
);

try (MemorySegment cString = CLinker.toCString("hello world")) {
    long length = (long) strlen.invoke(cString.address());
    System.out.println("Length via native strlen(): " + length);
}
```

No C compiler, no JNI header generation, no hand-written native shim — the native function is looked up and invoked entirely from Java source.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JNI requires hand-written native glue code compiled per platform; the Foreign Linker API calls native functions directly from Java via a generated MethodHandle">
  <rect x="20" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Traditional JNI</text>
  <text x="155" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java code</text>
  <text x="155" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ hand-written C glue (per platform)</text>
  <text x="155" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">native library function</text>
  <text x="155" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compile step required</text>

  <rect x="330" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Foreign Linker API</text>
  <text x="470" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java code</text>
  <text x="470" y="90" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">↓ CLinker.downcallHandle(...)</text>
  <text x="470" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">native library function</text>
  <text x="470" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no separate compile step</text>
</svg>

Both reach the same native function; the Foreign Linker API removes the hand-written native glue code entirely.

## 5. Runnable example

Scenario: calling into the C standard library — first invoking `strlen` on a simple string, then calling `getpid` (no arguments) to fetch the current process ID, then wrapping the pattern in a small reusable helper that looks up and calls an arbitrary named C function taking one string argument and returning a `long`.

### Level 1 — Basic

```java
// File: NativeStrlen.java
// Requires the incubating Foreign Linker API (Java 16): --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;

public class NativeStrlen {
    public static void main(String[] args) throws Throwable {
        CLinker linker = CLinker.getInstance();
        MethodHandle strlen = linker.downcallHandle(
                CLinker.systemLookup().lookup("strlen").get(),
                MethodType.methodType(long.class, MemoryAddress.class),
                FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER)
        );

        try (MemorySegment cString = CLinker.toCString("hello world")) {
            long length = (long) strlen.invoke(cString.address());
            System.out.println("Length via native strlen(): " + length);
        }
    }
}
```

**How to run (on a platform with a C standard library, e.g. Linux or macOS):**
```
java --add-modules jdk.incubator.foreign -Dforeign.restricted=permit NativeStrlen.java
```

Expected output:
```
Length via native strlen(): 11
```

### Level 2 — Intermediate

```java
// File: NativeGetPid.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;

public class NativeGetPid {
    public static void main(String[] args) throws Throwable {
        CLinker linker = CLinker.getInstance();
        MethodHandle getpid = linker.downcallHandle(
                CLinker.systemLookup().lookup("getpid").get(),
                MethodType.methodType(int.class),
                FunctionDescriptor.of(CLinker.C_INT)
        );

        int pid = (int) getpid.invoke();
        long javaPid = ProcessHandle.current().pid();
        System.out.println("Native getpid() matches ProcessHandle.current().pid(): " + (pid == javaPid));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.foreign -Dforeign.restricted=permit NativeGetPid.java
```

Expected output (the actual process ID varies every run, so the program checks equality rather than printing the raw number):
```
Native getpid() matches ProcessHandle.current().pid(): true
```

Calling a **zero-argument** native function (`getpid`, returning an `int`) shows the `MethodType`/`FunctionDescriptor` pair simplifying to no parameters at all, and cross-checks the native call's result against `ProcessHandle.current().pid()` — the ordinary, pure-Java way to get the same information — confirming the native call genuinely reaches the real OS-level process ID (checked via equality rather than printing the raw value, since the actual process ID differs on every run).

### Level 3 — Advanced

```java
// File: NativeFunctionHelper.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;

public class NativeFunctionHelper {
    static MethodHandle lookupStringToLong(String symbolName) {
        CLinker linker = CLinker.getInstance();
        return linker.downcallHandle(
                CLinker.systemLookup().lookup(symbolName)
                        .orElseThrow(() -> new IllegalArgumentException("symbol not found: " + symbolName)),
                MethodType.methodType(long.class, MemoryAddress.class),
                FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER)
        );
    }

    static long callWithCString(MethodHandle handle, String input) throws Throwable {
        try (MemorySegment cString = CLinker.toCString(input)) {
            return (long) handle.invoke(cString.address());
        }
    }

    public static void main(String[] args) throws Throwable {
        MethodHandle strlen = lookupStringToLong("strlen");

        String[] samples = { "hi", "hello world", "", "Panama Foreign Linker API" };
        for (String s : samples) {
            long len = callWithCString(strlen, s);
            System.out.println("strlen(\"" + s + "\") = " + len + " (Java length: " + s.length() + ")");
        }
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.foreign -Dforeign.restricted=permit NativeFunctionHelper.java
```

Expected output:
```
strlen("hi") = 2 (Java length: 2)
strlen("hello world") = 11 (Java length: 11)
strlen("") = 0 (Java length: 0)
strlen("Panama Foreign Linker API") = 25 (Java length: 25)
```

Level 3 wraps the lookup-and-call pattern into two small reusable helpers — `lookupStringToLong` (finds and describes any C function matching the "take a string, return a long" shape) and `callWithCString` (handles the native-string conversion and cleanup) — showing how repeated native calls can be structured cleanly rather than repeating the full `CLinker`/`MethodHandle` boilerplate at every call site.

## 6. Walkthrough

1. `lookupStringToLong(symbolName)` calls `CLinker.systemLookup().lookup(symbolName)` — this searches the set of symbols available in the standard system libraries already loaded into the process (on most platforms, this includes the C standard library) for a function with the given name, returning an `Optional<MemoryAddress>` (the native memory address of that function) which `.orElseThrow(...)` unwraps or fails clearly on if the symbol isn't found.
2. `linker.downcallHandle(address, methodType, functionDescriptor)` then asks the `CLinker` to generate a Java `MethodHandle` that, when invoked, performs a native call to that address using the calling convention implied by the `FunctionDescriptor` (`FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER)` describes "returns a C `long`, takes one C pointer argument") — this is the step where the JVM does the work a hand-written JNI shim used to have to do manually: translating between Java's calling convention and the native platform's ABI.
3. In `main`, `lookupStringToLong("strlen")` is called once, producing a reusable `MethodHandle` bound specifically to the C standard library's `strlen` function.
4. For each sample string, `callWithCString(strlen, s)` is called. Inside, `CLinker.toCString(input)` allocates a native memory segment (via a `try`-with-resources block, since native memory must be explicitly freed rather than garbage-collected) containing `input`'s bytes encoded as a null-terminated C string — the format `strlen` expects.
5. `handle.invoke(cString.address())` performs the actual native call: the JVM passes `cString`'s native memory address to `strlen` following the platform's real C calling convention, `strlen` walks the bytes until it finds the null terminator (counting everything before it), and the resulting `long` count is returned back across the Java/native boundary as the `MethodHandle` invocation's return value.
6. The `try`-with-resources block's `close()` (implicit at the end of `callWithCString`) releases the native memory segment `cString` allocated, since — unlike ordinary Java objects — off-heap native memory isn't automatically reclaimed by the garbage collector and must be explicitly freed to avoid a native memory leak.
7. Back in `main`, each call's result (`len`) is printed alongside the input string's own Java-native `.length()` for comparison — for these ASCII-only samples, the byte count `strlen` computes matches the Java `String`'s character count exactly, confirming the round trip (Java string → native C string → native `strlen` call → `long` result) behaved correctly for every sample, including the empty string (`strlen("") = 0`).

```
lookupStringToLong("strlen")
        │
CLinker.systemLookup().lookup("strlen") ──► native function address
        │
linker.downcallHandle(address, methodType, descriptor) ──► MethodHandle
        │
callWithCString(handle, "hello world")
        │
CLinker.toCString(...) ──► native memory segment (auto-closed)
        │
handle.invoke(segment.address()) ──► native strlen() call ──► long result
```

## 7. Gotchas & takeaways

> The Foreign Linker API was an **incubator module** in Java 16 (`jdk.incubator.foreign`, requiring `--add-modules jdk.incubator.foreign`), and additionally required an explicit "restricted" opt-in (such as `-Dforeign.restricted=permit`, exact flag varying by JDK build) since it deliberately allows Java code to bypass normal safety guarantees by calling arbitrary native functions. The API's class and method names, and even its module name, changed across subsequent JDK releases as Project Panama continued evolving it toward eventual standardization — code written against the Java 16 incubator will very likely need updates for later JDK versions.

- Native calls bypass the JVM's usual memory-safety guarantees — a bug in the native function being called (or a mismatched `FunctionDescriptor` that misdescribes its actual signature) can crash the JVM process, exactly as with JNI, though the Foreign Linker API removes the *glue-code-writing* burden, not the fundamental risk of calling unsafe native code.
- Native memory allocated via APIs like `CLinker.toCString(...)` must be managed explicitly (typically via `try`-with-resources, as shown) — it is not garbage-collected, and forgetting to close a `MemorySegment` leaks native memory outside the JVM heap.
- `CLinker.systemLookup()` only finds symbols in libraries already loaded into the process (commonly the C standard library and other system libraries) — loading and calling into an arbitrary third-party native library requires additional APIs (from the companion Foreign-Memory Access work) to load that library first.
- This API was explicitly part of **Project Panama**, whose broader goal (spanning the Foreign Linker API and the related [Foreign-Memory Access API](0694-foreign-memory-access-api-3rd-incubator.md)) was to make native interoperability and off-heap memory access a first-class, safer, pure-Java capability, eventually superseding JNI for most use cases.
- Given the API's rapid evolution across incubator rounds, any production code depending on it in this era needed careful version pinning and close attention to release notes for breaking changes between JDK versions.
