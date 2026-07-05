---
card: java
gi: 164
slug: stringbuffer-synchronized-mutable
title: StringBuffer (synchronized, mutable)
---

## 1. What it is

`StringBuffer` is a **mutable** sequence of characters — unlike `String`, calling a method like `append` or `insert` on a `StringBuffer` modifies the *same object in place* rather than creating a new one. It's also **synchronized**, meaning its methods are thread-safe: multiple threads can call methods on the same `StringBuffer` instance without corrupting its internal state, at the cost of some performance overhead from that synchronization.

```java
StringBuffer buffer = new StringBuffer("Hello");
buffer.append(", world!"); // modifies buffer IN PLACE — no new object created

System.out.println(buffer); // "Hello, world!"
System.out.println(buffer.toString()); // same content, converted to an actual String when needed
```

Contrast this directly with `String`: `"Hello".concat(", world!")` would create and return a brand-new `String`, leaving the original `"Hello"` untouched; `buffer.append(", world!")` instead changes `buffer` itself, and there is no new object to capture — the same `buffer` variable already reflects the change.

## 2. Why & when

`StringBuffer` exists specifically to solve the performance problem that comes from `String`'s immutability when building text incrementally:

- **Building strings across many operations (especially in a loop)** — each `String` concatenation with `+` creates a new object; a `StringBuffer` grows an internal, resizable character buffer in place, avoiding that repeated allocation entirely.
- **Multi-threaded string building** — if multiple threads genuinely need to append to the *same* shared buffer concurrently, `StringBuffer`'s built-in synchronization prevents corrupted, interleaved writes.

In practice, `StringBuffer` has largely been superseded by `StringBuilder` (added in Java 1.5), which offers the identical API but **without** synchronization — since the vast majority of string-building happens within a single thread, `StringBuilder`'s lack of synchronization overhead makes it faster for that common case, with no downside unless the buffer is genuinely shared across threads. `StringBuffer` remains relevant specifically for that multi-threaded scenario, and for reading/maintaining older code that predates `StringBuilder`.

## 3. Core concept

```java
public class StringBufferDemo {
    public static void main(String[] args) {
        StringBuffer buffer = new StringBuffer();

        for (int i = 1; i <= 5; i++) {
            buffer.append("Item ").append(i).append("\n"); // each call mutates the SAME object
        }

        System.out.println(buffer.toString());
        System.out.println("Final length: " + buffer.length());
    }
}
```

Every `.append(...)` call in the loop modifies the *same* `buffer` object — there is no new object created on each iteration, unlike what repeated `+` concatenation on a `String` would produce. `buffer.length()` reports the total character count accumulated across all five appends.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StringBuffer diagram: a single mutable buffer object grows in place as append is called repeatedly in a loop, contrasted with a String where each concatenation would instead create a brand new discarded object every time." >
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">StringBuffer: ONE object, grown in place across repeated append() calls</text>

  <rect x="60" y="45" width="580" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="67" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">buffer: "Item 1\nItem 2\nItem 3\n..." (same object, growing)</text>

  <path d="M 350 79 L 350 60" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="2,2"/>
  <text x="350" y="100" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">append() called 5 times — ZERO new objects created, unlike repeated String + concatenation</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Compare: 5 rounds of String "+" concatenation would create 5 separate, mostly-discarded String objects.</text>
</svg>

`StringBuffer` mutates one underlying object across every call — no intermediate objects are created or discarded along the way.

## 5. Runnable example

Scenario: building a large formatted report from many rows of data — starting with a basic `StringBuffer` accumulating loop, then comparing its behavior conceptually against what repeated `String` concatenation would have done, then hardening it into a reusable report-builder that demonstrates `StringBuffer`'s mutable, in-place nature by passing the same buffer into a helper method that continues appending to it.

### Level 1 — Basic

```java
public class ReportBasic {
    public static void main(String[] args) {
        StringBuffer report = new StringBuffer();
        String[] items = { "Coffee", "Bagel", "Juice" };

        for (String item : items) {
            report.append("- ").append(item).append("\n");
        }

        System.out.println(report.toString());
    }
}
```

**How to run:** `java ReportBasic.java`

Each pass through the loop calls three chained `.append(...)` calls on the *same* `report` object — by the time the loop finishes, `report` contains all three lines accumulated in place, and `report.toString()` converts the final accumulated content into an actual, immutable `String` only once, at the very end.

### Level 2 — Intermediate

Same report building, now demonstrating that `StringBuffer`'s mutations are visible through **any reference** to the same object — passing `report` into a method that appends more content, and observing the change reflected back in `main` without any return value needed.

```java
public class ReportIntermediate {

    static void appendFooter(StringBuffer buffer, int itemCount) {
        buffer.append("---\n").append("Total items: ").append(itemCount).append("\n");
        // no return needed — buffer is mutated directly, visible to the caller
    }

    public static void main(String[] args) {
        StringBuffer report = new StringBuffer();
        String[] items = { "Coffee", "Bagel", "Juice" };

        for (String item : items) {
            report.append("- ").append(item).append("\n");
        }

        appendFooter(report, items.length); // mutates the SAME buffer main() already holds a reference to

        System.out.println(report.toString());
    }
}
```

**How to run:** `java ReportIntermediate.java`

`appendFooter` receives `buffer` as a parameter and calls `.append(...)` on it directly — because `StringBuffer` is mutable and `buffer` inside the method refers to the *exact same object* as `report` in `main`, these appends are immediately visible in `main`'s `report` variable the moment `appendFooter` returns, with no return value required at all. This is fundamentally different from how a `String`-returning helper method would need to work, since a `String` parameter's mutations (via `concat`, etc.) would need to be explicitly returned and reassigned by the caller.

### Level 3 — Advanced

Same report builder, now demonstrating `StringBuffer`'s thread-safety directly: multiple threads append to the **same shared buffer** concurrently, and the synchronized methods ensure the final result contains every append cleanly, with no corrupted or interleaved output — something a naive, unsynchronized approach could not guarantee.

```java
public class ReportAdvanced {
    public static void main(String[] args) throws InterruptedException {
        StringBuffer sharedReport = new StringBuffer();
        int threadCount = 4;
        int appendsPerThread = 1000;

        Thread[] threads = new Thread[threadCount];
        for (int t = 0; t < threadCount; t++) {
            final int threadId = t;
            threads[t] = new Thread(() -> {
                for (int i = 0; i < appendsPerThread; i++) {
                    sharedReport.append("T").append(threadId).append(" ");
                }
            });
        }

        for (Thread thread : threads) thread.start();
        for (Thread thread : threads) thread.join(); // wait for every thread to finish

        int expectedEntries = threadCount * appendsPerThread;
        int actualEntries = sharedReport.toString().split(" ").length;
        System.out.println("Expected entries: " + expectedEntries + ", actual entries: " + actualEntries);
    }
}
```

**How to run:** `java ReportAdvanced.java`

Four threads each append `1000` tagged entries to the exact same `sharedReport` object concurrently, with no external locking added by this code — `StringBuffer`'s own internal synchronization on each `append` call is what prevents the threads' writes from corrupting each other's data or losing entries entirely. `sharedReport.toString().split(" ").length` counts how many space-separated entries actually ended up in the final buffer; because `StringBuffer` is synchronized, this count reliably matches `expectedEntries` (`4000`) every time this program runs, regardless of how the operating system happens to interleave the four threads' execution.

## 6. Walkthrough

Trace what happens when two threads (simplified to just two, for clarity) both attempt to call `append` on the same `StringBuffer` at nearly the same moment:

**Thread A calls `sharedReport.append("T0 ")`.** Because `StringBuffer`'s methods are synchronized, Thread A acquires an internal lock on `sharedReport` before modifying its internal character array. While Thread A holds this lock, no other thread can execute a synchronized method on the same object.

**Thread B calls `sharedReport.append("T1 ")` at nearly the same instant.** Since Thread A currently holds the lock, Thread B's call **blocks** — it waits until Thread A's `append` call fully completes and releases the lock.

**Thread A finishes appending `"T0 "` and releases the lock.** The internal buffer now correctly contains `"T0 "` fully intact, with no partial or corrupted write.

**Thread B's blocked call now proceeds.** It acquires the lock, appends `"T1 "` completely, and releases the lock in turn.

```
Thread A: append("T0 ") -- acquires lock -- writes fully -- releases lock
Thread B: append("T1 ") -- BLOCKS until A releases -- then acquires lock -- writes fully -- releases lock
Result: buffer contains both "T0 " and "T1 " completely, in some order, but never interleaved/corrupted
```

**Final result for the full program.** With four threads each performing 1000 appends, every single append is individually protected by this same locking behavior — so even though the *order* in which different threads' entries appear in the final buffer is unpredictable (which thread's "turn" comes when is left to the OS scheduler), the *count* of entries is always exactly `4000`, since no append is ever lost or corrupted by a concurrent write.

## 7. Gotchas & takeaways

> **`StringBuffer`'s synchronization only protects against corrupted internal state from concurrent method calls — it does not guarantee a specific ordering of those calls, nor does it make a whole multi-step sequence of operations atomic.** If code needs to read the buffer's current length and then append based on that length as one atomic unit, external synchronization is still required around that whole sequence, since each individual method call is synchronized on its own, not the combination.

> **For single-threaded string building — the overwhelming majority of real-world cases — `StringBuilder` is the better default, since it offers the identical API without the performance cost of unnecessary synchronization.** Reach for `StringBuffer` specifically when the same buffer instance is genuinely shared and mutated across multiple threads.

- `StringBuffer` is a mutable, resizable character sequence — methods like `append`/`insert`/`delete` modify the same object in place, unlike `String`'s immutable transformations.
- Its methods are synchronized, making individual method calls thread-safe when the same instance is shared across threads.
- Passing a `StringBuffer` to a method and having that method mutate it requires no return value — the caller's reference already sees the change, unlike passing a `String`.
- For single-threaded code, prefer `StringBuilder` (covered as the modern default elsewhere) — reserve `StringBuffer` for genuinely concurrent, shared-buffer scenarios.
