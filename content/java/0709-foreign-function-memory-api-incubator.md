---
card: java
gi: 709
slug: foreign-function-memory-api-incubator
title: Foreign Function & Memory API (incubator)
---

## 1. What it is

**Java 17** unified the two previously separate incubating Panama APIs — the [Foreign-Memory Access API](0694-foreign-memory-access-api-3rd-incubator.md) (off-heap memory) and the [Foreign Linker API](0693-foreign-linker-api-incubator.md) (calling native functions) — into one combined, jointly-incubating **Foreign Function & Memory (FFM) API** (JEP 412), still under the `jdk.incubator.foreign` package. The individual pieces (`MemorySegment`, `MemoryAddress`, `MemoryLayout`, `CLinker`, `SymbolLookup`) remain conceptually the same, but Java 17 introduced **`ResourceScope`**, replacing the earlier, more scattered lifecycle-management approach with one unified concept controlling when an off-heap memory segment or a native library handle gets deterministically released.

## 2. Why & when

Splitting native memory access and native function calls into two separate incubating APIs made sense while each was independently maturing, but in practice the two are used together constantly: you allocate off-heap memory to hold arguments, call a native function that reads or writes that memory, then need to release it — and getting that lifecycle right across two loosely related APIs was harder than it needed to be. JEP 412 merged them under one coherent design centered on `ResourceScope`: a scope that can be **confined** (usable only by the thread that created it, cheap to check), **shared** (usable by multiple threads, with extra safety checks), or **global** (never closed, for memory or handles that should simply outlive the whole application). Closing a scope deterministically frees every memory segment and native resource associated with it — a `try`-with-resources block over a `ResourceScope` is the idiomatic way to guarantee off-heap memory doesn't leak. Reach for this API (understanding its class names and exact API shape changed again in later JDK releases before final standardization) when you need off-heap memory with deterministic, scoped cleanup, when calling native library functions without JNI glue code, or both together — which is precisely the combined use case this unification was designed for.

## 3. Core concept

```java
// Java 17 incubator — requires --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;

try (ResourceScope scope = ResourceScope.newConfinedScope()) {
    // Off-heap memory, tied to this scope's lifecycle
    MemorySegment segment = MemorySegment.allocateNative(4 * Integer.BYTES, scope);
    MemoryAccess.setIntAtIndex(segment, 0, 42);

    // A native function call, using memory from the same scope
    MethodHandle abs = CLinker.getInstance().downcallHandle(
            CLinker.systemLookup().lookup("abs").get(),
            java.lang.invoke.MethodType.methodType(int.class, int.class),
            FunctionDescriptor.of(CLinker.C_INT, CLinker.C_INT)
    );
    int result = (int) abs.invoke(-42);
    System.out.println("abs(-42) = " + result);
} // scope.close() runs automatically here, freeing the off-heap memory deterministically
```

One `ResourceScope` governs both the off-heap memory segment's lifecycle and, conceptually, any native resources acquired within it — closing it once cleans up everything.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ResourceScope governs the lifecycle of both off-heap MemorySegments and native function call resources together; closing the scope releases everything deterministically">
  <rect x="180" y="15" width="280" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">try (ResourceScope scope = ...)</text>

  <rect x="60" y="80" width="220" height="60" rx="8" fill="#161b22" stroke="#79c0ff"/>
  <text x="170" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">MemorySegment</text>
  <text x="170" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">off-heap memory, tied to scope</text>

  <rect x="360" y="80" width="220" height="60" rx="8" fill="#161b22" stroke="#79c0ff"/>
  <text x="470" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CLinker downcall</text>
  <text x="470" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">native function call</text>

  <line x1="170" y1="140" x2="320" y2="170" stroke="#f0883e" stroke-width="1.5"/>
  <line x1="470" y1="140" x2="320" y2="170" stroke="#f0883e" stroke-width="1.5"/>
  <text x="320" y="190" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">scope.close() — both released together, deterministically</text>
</svg>

Memory allocation and native calls, previously governed by two separate APIs, now share one unified scope-based lifecycle.

## 5. Runnable example

Scenario: filling and reading a small off-heap buffer, then calling a native C library function that operates on that same memory — first basic allocation and manual read/write with a confined scope, then calling `strlen` on a native C string built inside a scope, then a version explicitly comparing a `confined` scope (fast, single-thread-only) against a `shared` scope (usable across threads, with extra safety checks), demonstrating the trade-off `ResourceScope` was designed to make explicit.

### Level 1 — Basic

```java
// File: OffHeapBasic.java
// Requires the incubating FFM API (Java 17): --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.MemoryAccess;
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.ResourceScope;

public class OffHeapBasic {
    public static void main(String[] args) {
        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment segment = MemorySegment.allocateNative(4 * Integer.BYTES, scope);

            for (int i = 0; i < 4; i++) {
                MemoryAccess.setIntAtIndex(segment, i, i * i);
            }
            for (int i = 0; i < 4; i++) {
                System.out.println("segment[" + i + "] = " + MemoryAccess.getIntAtIndex(segment, i));
            }
        } // off-heap memory is freed automatically here
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.foreign OffHeapBasic.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.foreign
segment[0] = 0
segment[1] = 1
segment[2] = 4
segment[3] = 9
```

### Level 2 — Intermediate

```java
// File: NativeStrlenScoped.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.*;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;

public class NativeStrlenScoped {
    public static void main(String[] args) throws Throwable {
        MethodHandle strlen = CLinker.getInstance().downcallHandle(
                CLinker.systemLookup().lookup("strlen").get(),
                MethodType.methodType(long.class, MemoryAddress.class),
                FunctionDescriptor.of(CLinker.C_LONG, CLinker.C_POINTER)
        );

        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment cString = CLinker.toCString("hello, panama", scope);
            long length = (long) strlen.invoke(cString.address());
            System.out.println("Native strlen(\"hello, panama\") = " + length);
        } // the native C string's backing memory is released here
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.foreign NativeStrlenScoped.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.foreign
Native strlen("hello, panama") = 13
```

### Level 3 — Advanced

```java
// File: ScopeComparison.java
// Requires: --add-modules jdk.incubator.foreign
import jdk.incubator.foreign.MemoryAccess;
import jdk.incubator.foreign.MemorySegment;
import jdk.incubator.foreign.ResourceScope;

public class ScopeComparison {
    static void useConfinedScope() {
        try (ResourceScope scope = ResourceScope.newConfinedScope()) {
            MemorySegment segment = MemorySegment.allocateNative(Integer.BYTES, scope);
            MemoryAccess.setInt(segment, 99);
            System.out.println("[confined] value = " + MemoryAccess.getInt(segment)
                    + " (only the creating thread may access this segment)");
        }
    }

    static void useSharedScopeAcrossThreads() throws InterruptedException {
        try (ResourceScope scope = ResourceScope.newSharedScope()) {
            MemorySegment segment = MemorySegment.allocateNative(Integer.BYTES, scope);
            MemoryAccess.setInt(segment, 0);

            Thread worker = new Thread(() -> {
                MemoryAccess.setInt(segment, 7);
                System.out.println("[shared] worker thread wrote value = " + MemoryAccess.getInt(segment));
            });
            worker.start();
            worker.join();

            System.out.println("[shared] main thread reads final value = " + MemoryAccess.getInt(segment));
        } // scope.close() waits until it is safe, then releases the segment
    }

    public static void main(String[] args) throws InterruptedException {
        useConfinedScope();
        useSharedScopeAcrossThreads();
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.foreign ScopeComparison.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.foreign
[confined] value = 99 (only the creating thread may access this segment)
[shared] worker thread wrote value = 7
[shared] main thread reads final value = 7
```

## 6. Walkthrough

1. `main` calls `useConfinedScope()` first: it opens a `ResourceScope.newConfinedScope()`, allocates a single `int`-sized off-heap segment tied to it, writes `99` via `MemoryAccess.setInt`, reads it back, and prints it — the scope is confined to the thread that created it, which is the cheapest and simplest lifecycle mode, appropriate whenever off-heap memory never needs to leave the thread that allocated it.
2. `useSharedScopeAcrossThreads()` instead opens a `ResourceScope.newSharedScope()`, allocates a segment from it, and initializes it to `0` on the main thread.
3. A new `Thread` is started whose body writes `7` into that same segment via `MemoryAccess.setInt` and immediately reads it back to confirm the write — this cross-thread access is exactly what a *confined* scope would forbid at runtime (attempting it would throw), but a *shared* scope explicitly permits, at the cost of extra internal synchronization checks the confined variant skips.
4. `worker.join()` ensures the main thread waits for the worker thread's write to complete before proceeding; `main` then reads the segment's final value (`7`) itself, confirming the write made by the other thread is visible here — off-heap memory is genuinely shared state, so ordinary Java visibility rules (here enforced simply via `Thread.join()`'s happens-before guarantee) still apply to it exactly as they would for any other shared mutable state.
5. Both `try`-with-resources blocks close their respective `ResourceScope` at the end, which is the point where the underlying native memory is actually released back to the operating system — for the shared scope specifically, `close()` may need to wait until it can be certain no other thread is still concurrently accessing the segment, which is part of the extra safety a shared scope provides over a confined one.
6. In `NativeStrlenScoped` (Level 2), `CLinker.toCString("hello, panama", scope)` allocates a native, null-terminated C-style string *inside* the given scope in one call, so its off-heap backing memory is released automatically the moment that scope closes — tying the native string's lifetime directly to the surrounding `try`-with-resources block, exactly the unification of memory-lifecycle and native-interop concerns this JEP was designed to deliver.

```
ResourceScope.newConfinedScope()  -> fast, single-thread-only access
ResourceScope.newSharedScope()    -> multi-thread access, extra safety checks
        │                                   │
   allocateNative(..., scope)      allocateNative(..., scope)
        │                                   │
     scope.close()                   scope.close() (may wait for safe release)
```

## 7. Gotchas & takeaways

> The FFM API remained an **incubator module** in Java 17 (`--add-modules jdk.incubator.foreign` required on both compilation and execution) — its exact class names and API shape (including `ResourceScope` itself) **changed again** in subsequent JDK releases on the path to final standardization as `java.lang.foreign` years later. Code written against this Java 17 incubator will not compile unchanged against later previews or the finalized API.
- Using a **confined** scope from a thread other than the one that created it throws at runtime — this is a deliberate safety check, not a bug; use a **shared** scope explicitly whenever cross-thread access to the same off-heap memory is genuinely needed.
- Closing a scope invalidates every `MemorySegment` allocated within it — attempting to read or write a segment after its scope is closed throws, which is exactly the safety net that replaces manual, error-prone "did I already free this?" bookkeeping from raw native-memory APIs like `sun.misc.Unsafe`.
- `ResourceScope.globalScope()` (not shown above) exists for memory or native resources meant to live for the entire application's lifetime and never be explicitly closed — appropriate only for cases where deterministic release genuinely isn't needed.
- This unification directly supersedes the two separate, earlier incubator entries — [Foreign-Memory Access API (3rd incubator)](0694-foreign-memory-access-api-3rd-incubator.md) and [Foreign Linker API](0693-foreign-linker-api-incubator.md) — both from Java 16; code written against those needs updating to the `ResourceScope`-based lifecycle model shown here to work under Java 17's unified API.
- See [Vector API (2nd incubator)](0710-vector-api-2nd-incubator.md), landing in this same release, for another incubating Project Panama API that gained direct interop with `MemorySegment` in Java 17 — vector loads and stores can read from and write to the exact same off-heap memory this API manages.
