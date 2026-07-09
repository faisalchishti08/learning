---
card: java
gi: 755
slug: foreign-function-memory-api-3rd-preview
title: Foreign Function & Memory API (3rd preview)
---

## 1. What it is

**Java 21** (JEP 442) is the **third preview** of the [Foreign Function & Memory API](0737-foreign-function-memory-api-2nd-preview.md), continuing from its second preview round in Java 20. The core model — off-heap `MemorySegment`s, explicit-lifetime arenas managing when native memory is freed, native calls via `Linker` and `FunctionDescriptor`, and upcalls for native-to-Java callbacks — carries forward, with this round renaming and consolidating the session/lifetime concept into the current **`Arena`** abstraction (replacing the earlier `MemorySession` terminology from prior rounds) and tightening safety guarantees around confined vs. shared memory access across threads. As with every round so far, it remains a preview requiring `--enable-preview`.

## 2. Why & when

Naming and lifetime-management churn across preview rounds (`MemorySession` in earlier rounds, `Arena` here) is a normal part of a complex, safety-critical API converging toward finalization — this is exactly the kind of design refinement preview status exists to surface before an API is locked in permanently. `Arena` consolidates what a "session" was trying to express (who owns this memory, and when is it safe to free) into a clearer single concept with well-defined variants: `Arena.ofConfined()` for memory only ever accessed by the thread that created it (the cheapest, safest default), `Arena.ofShared()` for memory that legitimately needs cross-thread access, and `Arena.global()`/`Arena.ofAuto()` for memory that should live for the whole program or be garbage-collected respectively. Getting this exactly right matters because the entire safety value proposition of the FFM API — replacing JNI's `unsafe`, crash-prone native memory access with something the JVM can reason about — depends on the lifetime-and-ownership model being both correct and easy to use correctly by default; a confusing or leaky lifetime API would undermine the whole point.

## 3. Core concept

```java
import java.lang.foreign.*;

// Arena replaces the earlier "MemorySession" terminology from prior preview rounds.
try (Arena arena = Arena.ofConfined()) {
    MemorySegment segment = arena.allocate(100); // 100 bytes of off-heap memory
    segment.set(ValueLayout.JAVA_INT, 0, 42);
    int value = segment.get(ValueLayout.JAVA_INT, 0);
    System.out.println(value); // 42
} // segment is freed here, deterministically, when the confined arena closes
```

`Arena.ofConfined()` ties the memory's lifetime directly to the try-with-resources block and restricts access to the thread that created it — the safest and most common pattern.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An Arena owns the lifetime of one or more off-heap memory segments; different Arena kinds trade off confinement, sharing, and automatic cleanup">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Arena — owns lifetime of off-heap MemorySegments</text>

  <rect x="20" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ofConfined()</text>
  <text x="110" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one thread, deterministic close</text>

  <rect x="230" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ofShared()</text>
  <text x="320" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">multi-thread access</text>

  <rect x="440" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="530" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ofAuto() / global()</text>
  <text x="530" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GC-managed / program lifetime</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Choosing the right Arena kind is choosing an ownership and safety model, not just a lifetime</text>
</svg>

*`Arena` names both who is allowed to touch the memory and when it gets freed.*

## 5. Runnable example

Scenario: computing a checksum over a native memory buffer, growing from a simple confined allocation into shared, multi-threaded access.

### Level 1 — Basic

```java
import java.lang.foreign.*;

public class ArenaBasic {
    public static void main(String[] args) {
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment buffer = arena.allocate(16);
            for (int i = 0; i < 16; i++) {
                buffer.set(ValueLayout.JAVA_BYTE, i, (byte) i);
            }
            long sum = 0;
            for (int i = 0; i < 16; i++) {
                sum += buffer.get(ValueLayout.JAVA_BYTE, i);
            }
            System.out.println("checksum: " + sum);
        } // buffer freed here
    }
}
```

**How to run:** `java --enable-preview --source 21 ArenaBasic.java` (JDK 21+).

This allocates 16 bytes of off-heap memory in a confined arena, fills it, sums it, and lets the try-with-resources block free it deterministically — the simplest possible use of `Arena`.

### Level 2 — Intermediate

```java
import java.lang.foreign.*;

public class ArenaLargerBuffer {
    static long checksum(MemorySegment buffer) {
        long sum = 0;
        for (long i = 0; i < buffer.byteSize(); i++) {
            sum += buffer.get(ValueLayout.JAVA_BYTE, i);
        }
        return sum;
    }

    public static void main(String[] args) {
        final int SIZE = 1_000_000;
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment buffer = arena.allocate(SIZE);
            for (long i = 0; i < SIZE; i++) {
                buffer.set(ValueLayout.JAVA_BYTE, i, (byte) (i % 256));
            }
            System.out.println("checksum of " + SIZE + " bytes: " + checksum(buffer));
        }
    }
}
```

**How to run:** `java --enable-preview --source 21 ArenaLargerBuffer.java`.

The real-world concern added: a **1 MB buffer** and a reusable `checksum` method operating on any `MemorySegment` — showing that off-heap memory of meaningful size behaves like any other buffer to work with, while still being freed deterministically and never touching the Java heap or garbage collector.

### Level 3 — Advanced

```java
import java.lang.foreign.*;
import java.util.concurrent.*;

public class ArenaShared {
    static long partialChecksum(MemorySegment buffer, long start, long end) {
        long sum = 0;
        for (long i = start; i < end; i++) {
            sum += buffer.get(ValueLayout.JAVA_BYTE, i);
        }
        return sum;
    }

    public static void main(String[] args) throws Exception {
        final int SIZE = 4_000_000;
        final int CHUNKS = 4;

        try (Arena arena = Arena.ofShared()) { // shared: safe for multiple threads to read
            MemorySegment buffer = arena.allocate(SIZE);
            for (long i = 0; i < SIZE; i++) {
                buffer.set(ValueLayout.JAVA_BYTE, i, (byte) (i % 256));
            }

            long chunkSize = SIZE / CHUNKS;
            try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
                var futures = new java.util.ArrayList<Future<Long>>();
                for (int c = 0; c < CHUNKS; c++) {
                    long start = c * chunkSize;
                    long end = (c == CHUNKS - 1) ? SIZE : start + chunkSize;
                    futures.add(executor.submit(() -> partialChecksum(buffer, start, end)));
                }
                long total = 0;
                for (var f : futures) total += f.get();
                System.out.println("total checksum: " + total);
            }
        } // safe: all subtasks finished before the shared arena closes
    }
}
```

**How to run:** `java --enable-preview --source 21 ArenaShared.java`.

This adds the production-flavored hard case: **`Arena.ofShared()`** allowing four virtual-thread subtasks (combining with [virtual threads — standardized](0739-virtual-threads-standardized.md)) to concurrently read disjoint regions of the *same* off-heap buffer — something `Arena.ofConfined()` would forbid, since a confined arena restricts access to its creating thread only.

## 6. Walkthrough

Tracing `ArenaShared.main`:

1. `main` opens a shared arena and allocates a 4,000,000-byte off-heap segment, then fills it sequentially with a repeating byte pattern.
2. It computes `chunkSize = 1,000,000` and, inside a virtual-thread-per-task executor, submits four tasks, each calling `partialChecksum(buffer, start, end)` over a distinct quarter of the buffer.
3. Because `buffer` was allocated from a **shared** arena, each subtask (running on its own virtual thread) is permitted to read from it concurrently — a confined arena's memory can only be touched by the single thread that created the arena, which would make this concurrent design illegal and throw at runtime.
4. Each `partialChecksum` call loops over its assigned byte range, summing values, and returns its partial sum as a `Future<Long>`.
5. Back in `main`, the loop over `futures` calls `.get()` on each, blocking until that subtask finishes, and accumulates `total`.
6. The inner try-with-resources block for the executor closes first (waiting for all four subtasks), and only afterward does the outer try-with-resources block close the shared `arena`, freeing `buffer` — guaranteeing no subtask could still be reading from the buffer at the moment it's freed.
7. `main` prints the combined checksum.

Expected output:
```
total checksum: 510000000
```

(The exact number follows from the specific `(byte)(i % 256)` fill pattern and buffer size; the meaningful result is that concurrent reads over a shared arena's memory work correctly and the total matches what a single-threaded pass over the whole buffer would compute.)

## 7. Gotchas & takeaways

> **Gotcha:** a **confined** arena's memory segment can only be accessed by the thread that created the arena — passing such a segment to a different thread and touching it there throws `WrongThreadException` at runtime, not a compile error. Reach for `Arena.ofShared()` deliberately whenever multiple threads genuinely need to touch the same off-heap memory, rather than working around a `WrongThreadException` by widening confinement without thinking about the actual safety implications.

- Preview in Java 21, continuing from Java 19/20's preview rounds — `MemorySession` terminology from earlier rounds is now `Arena`.
- `Arena.ofConfined()` is the safest, cheapest default: single-thread access, deterministic close via try-with-resources.
- `Arena.ofShared()` allows multi-thread access when genuinely needed — required for patterns like fanning out concurrent reads across virtual threads.
- `Arena.ofAuto()` ties a segment's lifetime to garbage collection instead of an explicit close, trading determinism for convenience; `Arena.global()` never closes at all.
- Still a preview — expect API refinement before finalization, and treat the exact class/method names here as specific to Java 21.
