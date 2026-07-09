---
card: java
gi: 782
slug: deprecate-memory-access-methods-in-sun-misc-unsafe
title: Deprecate memory-access methods in sun.misc.Unsafe
---

## 1. What it is

**Java 23** (JEP 471) **deprecates for removal** the memory-access methods of `sun.misc.Unsafe` — `allocateMemory`, `reallocateMemory`, `freeMemory`, `getInt`/`putInt` and their sibling primitive accessors, `copyMemory`, and related methods that let code read and write raw off-heap memory directly, bypassing the JVM's normal safety checks. Calling any of these methods now triggers a compile-time deprecation warning (and, depending on configuration, a runtime warning on first use), signaling that they are on a path toward eventual removal, now that the [Foreign Function & Memory API](0759-foreign-function-memory-api-standardized.md) — standardized in Java 22 — provides the safe, supported replacement for what these `Unsafe` methods were being used for.

## 2. Why & when

`sun.misc.Unsafe` was never meant to be public API — the "unsafe" in its name is a warning, not a stylistic choice — but for two decades it was the *only* way to do certain things the JDK offered no other route to: allocate and manipulate off-heap memory directly, perform low-level atomic operations, or access fields without going through normal Java semantics. Libraries and frameworks (high-performance serialization, off-heap caches, some concurrency utilities) reached for it out of necessity, accepting the risk that it could crash the JVM with no Java-level exception on a wrong pointer, could change or vanish in any JDK release without notice, and required security-manager or module-system workarounds to even access. Now that the Foreign Function & Memory API offers everything the memory-access subset of `Unsafe` provided — off-heap allocation via `Arena`, structured reads/writes via `MemorySegment`, all with **checked, safe lifetimes** instead of raw pointers — the JDK can finally start retiring the specific `Unsafe` methods that API supersedes. Deprecation-for-removal is the first, most gentle step: existing code keeps working (with a warning), giving library maintainers a runway to migrate before the methods are ever actually removed in some future release.

## 3. Core concept

```java
// Deprecated for removal in Java 23 — triggers a compiler warning:
sun.misc.Unsafe unsafe = ...; // obtaining an instance already required reflection tricks
long address = unsafe.allocateMemory(64);
unsafe.putInt(address, 0, 42);
int value = unsafe.getInt(address, 0);
unsafe.freeMemory(address);

// The supported, standard replacement (Java 22+):
import java.lang.foreign.*;
try (Arena arena = Arena.ofConfined()) {
    MemorySegment segment = arena.allocate(64);
    segment.set(ValueLayout.JAVA_INT, 0, 42);
    int value2 = segment.get(ValueLayout.JAVA_INT, 0);
} // memory automatically freed when the arena closes
```

Both blocks allocate off-heap memory, write an `int`, and read it back — but the `Arena`/`MemorySegment` version has a checked, automatically-released lifetime, while the `Unsafe` version has a raw pointer that must be manually freed and offers no protection against use-after-free.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sun.misc.Unsafe memory-access methods are deprecated for removal in Java 23, with the Foreign Function and Memory API's Arena and MemorySegment as the safe, standard replacement">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#0f1620" stroke="#f85149"/>
  <text x="160" y="45" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">sun.misc.Unsafe memory methods</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deprecated for removal, Java 23</text>

  <line x1="300" y1="50" x2="350" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a782)"/>
  <defs><marker id="a782" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <text x="325" y="35" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">migrate to</text>

  <rect x="360" y="20" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Arena / MemorySegment</text>
  <text x="490" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">standard since Java 22</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Non-memory Unsafe methods (e.g. compareAndSwap) are unaffected by this JEP</text>
</svg>

*Only `Unsafe`'s memory-access surface is targeted here — the safe replacement has been standard for a full release already.*

## 5. Runnable example

Scenario: an off-heap counter buffer, starting from `Unsafe`-based code as legacy projects might still have it, migrated step by step to the standard Foreign Function & Memory API replacement.

### Level 1 — Basic

```java
import java.lang.reflect.*;
import sun.misc.Unsafe;

public class UnsafeCounterLegacy {
    public static void main(String[] args) throws Exception {
        Field f = Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        Unsafe unsafe = (Unsafe) f.get(null);

        long address = unsafe.allocateMemory(4); // 4 bytes for one int
        unsafe.putInt(address, 0);
        unsafe.putInt(address, unsafe.getInt(address) + 1);
        System.out.println("counter: " + unsafe.getInt(address));
        unsafe.freeMemory(address); // must remember to free manually
    }
}
```

**How to run:** `java --add-opens java.base/sun.misc=ALL-UNNAMED UnsafeCounterLegacy.java` (JDK 23+; this compiles with a deprecation warning on every `Unsafe` memory-access call — a preview of what will eventually become a hard removal).

This is the kind of code many older libraries still contain: reflection to obtain the singleton `Unsafe` instance, then raw pointer allocation, manual read/increment/write, and a manual `freeMemory` call that a forgetful caller could easily skip, leaking the allocation.

### Level 2 — Intermediate

```java
import java.lang.foreign.*;

public class ArenaCounterMigrated {
    public static void main(String[] args) {
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment counter = arena.allocate(ValueLayout.JAVA_INT);
            counter.set(ValueLayout.JAVA_INT, 0, 0);

            int current = counter.get(ValueLayout.JAVA_INT, 0);
            counter.set(ValueLayout.JAVA_INT, 0, current + 1);

            System.out.println("counter: " + counter.get(ValueLayout.JAVA_INT, 0));
        } // memory automatically freed here — no manual freeMemory() call needed
    }
}
```

**How to run:** `java ArenaCounterMigrated.java` (JDK 22+; no deprecation warning, no `--add-opens`, no reflection).

The real-world concern added: the exact same off-heap counter, expressed with `Arena`/`MemorySegment` — no reflection to obtain a singleton, no raw pointer arithmetic, and no risk of a leaked allocation, since the `try`-with-resources block frees the memory automatically the moment it exits, success or failure.

### Level 3 — Advanced

```java
import java.lang.foreign.*;
import java.util.concurrent.*;
import java.util.*;

public class ArenaCounterConcurrent {
    public static void main(String[] args) throws Exception {
        int counterCount = 5;
        List<Long> finalValues = Collections.synchronizedList(new ArrayList<>());

        try (Arena arena = Arena.ofShared()) { // shared across threads, unlike ofConfined
            MemorySegment counters = arena.allocate(ValueLayout.JAVA_INT, counterCount);

            try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
                List<Future<?>> futures = new ArrayList<>();
                for (int c = 0; c < counterCount; c++) {
                    int slot = c;
                    futures.add(executor.submit(() -> {
                        for (int i = 0; i < 1000; i++) {
                            long offset = (long) slot * ValueLayout.JAVA_INT.byteSize();
                            int current = counters.get(ValueLayout.JAVA_INT, offset);
                            counters.set(ValueLayout.JAVA_INT, offset, current + 1);
                        }
                    }));
                }
                for (var f : futures) f.get();
            }

            for (int c = 0; c < counterCount; c++) {
                long offset = (long) c * ValueLayout.JAVA_INT.byteSize();
                finalValues.add((long) counters.get(ValueLayout.JAVA_INT, offset));
            }
        } // shared arena's off-heap memory freed automatically once every thread is done

        System.out.println("final counters: " + finalValues);
    }
}
```

**How to run:** `java ArenaCounterConcurrent.java` (JDK 22+).

This adds the production-flavored hard case: an **off-heap array of five counters**, each independently incremented 1,000 times by its own virtual thread, sharing one `Arena.ofShared()` — a scenario the raw `Unsafe` approach could technically also support, but only by the caller manually ensuring no thread frees the memory while another is still using it; here, the arena's lifetime is tied to the enclosing `try`-with-resources block, and `Arena.ofShared()` explicitly documents that it's safe for multiple threads to access the segment concurrently (each writing to its own non-overlapping slot, avoiding a data race on any individual counter).

## 6. Walkthrough

Tracing `ArenaCounterConcurrent.main`:

1. `main` opens a **shared** arena (`Arena.ofShared()`, distinct from the single-threaded `Arena.ofConfined()` used in the previous level) and allocates one contiguous off-heap block sized for five `int`s via `arena.allocate(ValueLayout.JAVA_INT, counterCount)`.
2. It starts a virtual-thread-per-task executor and submits five tasks, one per counter slot; each task loops 1,000 times, computing its slot's **byte offset** (`slot * ValueLayout.JAVA_INT.byteSize()`, i.e. `slot * 4`) into the shared segment, then reading and incrementing just that `int`.
3. Because each virtual thread only ever touches its **own** slot's offset, there's no data race between threads even though they're all writing into the same underlying off-heap block concurrently — the safety here comes from the program's own slot-partitioning discipline, not from the `Arena` API itself, which (correctly) doesn't prevent two threads from racing on the *same* offset if the caller's logic allowed that.
4. `main` waits for every submitted task's `Future` via `.get()`, ensuring all 5,000 total increments (5 counters × 1,000 each) have completed before reading any values back.
5. It then reads each of the five slots back into `finalValues`, expecting each to equal `1000`.
6. The outer `try`-with-resources block for the shared arena closes after this, automatically releasing the off-heap memory — safe to do here because every thread that was using the segment has already finished, confirmed by the earlier `.get()` calls.

Expected output:
```
final counters: [1000, 1000, 1000, 1000, 1000]
```

## 7. Gotchas & takeaways

> **Gotcha:** deprecation-for-removal is not immediate removal — `sun.misc.Unsafe`'s memory-access methods still **work** in Java 23, just with a warning. Don't panic-migrate production code the day this ships; do treat the warning as the starting signal for a planned migration, since a future JDK release is expected to actually remove these methods, at which point code still calling them would fail to compile or run at all.

- Java 23 (JEP 471) deprecates-for-removal `sun.misc.Unsafe`'s memory-access methods (`allocateMemory`, `freeMemory`, `getInt`/`putInt` and siblings, `copyMemory`) — non-memory `Unsafe` methods (like compare-and-swap operations) are **not** affected by this JEP.
- The [Foreign Function & Memory API](0759-foreign-function-memory-api-standardized.md)'s `Arena` and `MemorySegment`, standard since Java 22, are the direct, safe replacement — checked lifetimes instead of raw pointers, automatic cleanup instead of manual `freeMemory` calls.
- `Arena.ofConfined()` restricts a segment to one thread; `Arena.ofShared()` allows safe concurrent access from multiple threads to the *segment itself* — though avoiding races on individual values within it remains the caller's responsibility, same as with any shared mutable off-heap memory.
- Libraries still depending on `Unsafe`'s memory methods should plan a migration now rather than waiting for an eventual hard removal to force the issue.
- This deprecation is a direct, practical consequence of the Foreign Function & Memory API's standardization — the JDK doesn't retire a risky escape hatch until a safe, equally capable replacement has existed and stabilized first.
