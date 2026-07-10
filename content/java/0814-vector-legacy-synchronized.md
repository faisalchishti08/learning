---
card: java
gi: 814
slug: vector-legacy-synchronized
title: Vector (legacy, synchronized)
---

## 1. What it is

`Vector` is a resizable-array `List` implementation that predates the Collections Framework itself — it shipped in Java 1.0, years before generics, the `Collection` interface, or `ArrayList` existed. Every one of its methods is `synchronized`, meaning only one thread can execute any method on a given `Vector` instance at a time. It was retrofitted to implement `List` when the Collections Framework arrived in Java 1.2, so it behaves like an `ArrayList` functionally, but with built-in per-method locking that `ArrayList` deliberately does not have.

## 2. Why & when

Back before the Collections Framework, `Vector` was simply "the" resizable array class, and it was made thread-safe by default because there was no separate concept yet of "thread-safe vs. not" collection variants — every method just synchronized on the instance. Once `ArrayList` arrived as the modern, unsynchronized alternative, `Vector`'s built-in locking became a liability more often than a benefit: synchronizing *every single method call* — even in single-threaded code that never needs it — adds real, unavoidable overhead, and per-method synchronization doesn't even provide correct thread safety for compound operations like "check if empty, then add" (that sequence can still race between the check and the add, even though each individual call is synchronized). Modern code essentially never has a good reason to choose `Vector` deliberately: single-threaded code should use `ArrayList`, and multi-threaded code needs either explicit external locking, `Collections.synchronizedList(new ArrayList<>())`, or (often better) [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md). `Vector` mostly appears today in decades-old codebases or APIs that haven't been modernized.

## 3. Core concept

```java
Vector<String> legacy = new Vector<>();
legacy.add("a");    // this call is synchronized internally
legacy.add("b");    // so is this one

// But this common "check-then-act" pattern is still NOT thread-safe overall,
// even though each individual call IS synchronized:
if (!legacy.contains("c")) {  // synchronized call #1
    legacy.add("c");           // synchronized call #2 -- another thread could sneak in between these two calls
}
```

Synchronizing each method individually prevents two threads from corrupting the internal array simultaneously, but it does nothing to make a multi-step sequence of calls atomic as a whole.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vector synchronizes each individual method call, but a check-then-act sequence across two separate calls can still race between two threads">
  <text x="320" y="25" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Two threads both running: if (!v.contains("c")) v.add("c");</text>

  <rect x="40" y="50" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="75" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Thread A: contains("c") -&gt; false</text>

  <rect x="340" y="50" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="75" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Thread B: contains("c") -&gt; false</text>

  <rect x="40" y="110" width="260" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="170" y="135" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Thread A: add("c")</text>

  <rect x="340" y="110" width="260" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="470" y="135" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Thread B: add("c") — duplicate!</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both contains() calls ran before either add() — "c" ends up added twice</text>
</svg>

*Each call is individually synchronized, but the gap between two calls is not — compound operations still race.*

## 5. Runnable example

Scenario: a shared counter log accessed by multiple threads, growing from basic `Vector` usage to the check-then-act race it doesn't prevent, to migrating that same logic onto a genuinely safer modern alternative.

### Level 1 — Basic

```java
import java.util.*;

public class VectorBasic {
    public static void main(String[] args) {
        Vector<String> log = new Vector<>();
        log.add("event-1");
        log.add("event-2");
        log.addElement("event-3"); // legacy pre-Collections-Framework method name, still present

        System.out.println("log: " + log);
        System.out.println("first element (legacy accessor): " + log.firstElement());
        System.out.println("size: " + log.size());
    }
}
```

**How to run:** `java VectorBasic.java` (JDK 17+).

Expected output:
```
log: [event-1, event-2, event-3]
first element (legacy accessor): event-1
size: 3
```

`Vector` behaves like a `List` (because it is one), but also carries legacy-era method names like `addElement`/`firstElement`/`elementAt` left over from before the Collections Framework standardized on `add`/`get`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.*;

public class VectorRaceDemo {
    public static void main(String[] args) throws InterruptedException {
        Vector<String> uniqueEvents = new Vector<>();
        ExecutorService pool = Executors.newFixedThreadPool(4);

        Runnable addIfAbsent = () -> {
            if (!uniqueEvents.contains("startup")) { // synchronized call #1
                uniqueEvents.add("startup");            // synchronized call #2 -- gap between these two is NOT protected
            }
        };

        for (int i = 0; i < 4; i++) {
            pool.submit(addIfAbsent);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        // Individually-synchronized methods do NOT make this compound check-then-act sequence atomic.
        System.out.println("uniqueEvents (may contain duplicates!): " + uniqueEvents);
        System.out.println("count of \"startup\" entries: " + Collections.frequency(uniqueEvents, "startup"));
    }
}
```

**How to run:** `java VectorRaceDemo.java`. (Outcome is timing-dependent — run it a few times; duplicates appear intermittently, which is exactly the point.)

Expected output (illustrative — the count varies by run, and may occasionally be 1 if timing happens to avoid the race):
```
uniqueEvents (may contain duplicates!): [startup, startup]
count of "startup" entries: 2
```

The real-world concern added: proving that `Vector`'s per-method synchronization does **not** prevent this extremely common bug pattern — checking a condition and then acting on it is two separate synchronized calls, with an unprotected gap between them where another thread can interleave. `Vector` being "thread-safe" only ever meant "individual method calls won't corrupt the internal array" — never "sequences of calls are atomic."

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class ModernMigration {
    public static void main(String[] args) throws InterruptedException {
        // The correct fix: synchronize the WHOLE compound operation explicitly,
        // using a lock that covers the entire check-then-act sequence.
        List<String> uniqueEvents = Collections.synchronizedList(new ArrayList<>());
        ExecutorService pool = Executors.newFixedThreadPool(4);

        Runnable addIfAbsentSafe = () -> {
            synchronized (uniqueEvents) { // lock spans BOTH the check and the act
                if (!uniqueEvents.contains("startup")) {
                    uniqueEvents.add("startup");
                }
            }
        };

        for (int i = 0; i < 4; i++) {
            pool.submit(addIfAbsentSafe);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("uniqueEvents (correctly deduplicated): " + uniqueEvents);
        System.out.println("count of \"startup\" entries: " + Collections.frequency(uniqueEvents, "startup"));
    }
}
```

**How to run:** `java ModernMigration.java`.

Expected output (deterministic — always exactly 1, run after run):
```
uniqueEvents (correctly deduplicated): [startup]
count of "startup" entries: 1
```

This adds the production-flavored hard case: the actual fix for the Level 2 race. `Collections.synchronizedList(new ArrayList<>())` gives per-method synchronization similar to `Vector` (same limitation on compound operations), but wrapping the **entire** check-then-act sequence in an explicit `synchronized (uniqueEvents) { ... }` block — locking on the list object itself — makes the whole compound operation atomic, which neither `Vector`'s nor `Collections.synchronizedList`'s built-in per-method locking can do on their own.

## 6. Walkthrough

Tracing `ModernMigration.main`:

1. `uniqueEvents` is a `Collections.synchronizedList`-wrapped `ArrayList` — functionally similar to `Vector` in that each individual method call is synchronized on the same lock.
2. Four tasks are submitted to a four-thread pool, each running `addIfAbsentSafe`, which wraps its check-then-act logic in `synchronized (uniqueEvents) { ... }` — this explicitly acquires the **same** lock object that `Collections.synchronizedList` uses internally for its own method-level synchronization, meaning this external block genuinely excludes other threads for its entire duration, not just for one method call at a time.
3. Whichever thread acquires the lock first executes both `contains("startup")` (returns `false`, since the list starts empty) and `add("startup")` as one uninterrupted unit before releasing the lock.
4. Every other thread, blocked waiting for the same lock, only gets to run its own `synchronized` block afterward — by which point `contains("startup")` correctly returns `true`, so `add` is never called again.
5. The result is deterministic: exactly one `"startup"` entry, every time, because the lock's scope was widened to cover the entire compound operation rather than relying on each method call's own internal synchronization.

## 7. Gotchas & takeaways

> **Gotcha:** "this collection is synchronized" only ever means individual method calls are thread-safe — it says nothing about sequences of calls. Any check-then-act, read-modify-write, or iterate-while-possibly-mutating pattern needs its own explicit external locking (or a structurally different approach, like [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md)'s atomic `computeIfAbsent`) regardless of whether the underlying collection is `Vector`, `Collections.synchronizedList`, or anything else built on per-method locking.

- `Vector` predates the Collections Framework; every method is individually `synchronized`, adding overhead even in single-threaded use.
- Being "synchronized" only protects individual method calls, not multi-call sequences like check-then-act — that requires an explicit external lock spanning the whole sequence.
- Modern code should default to `ArrayList` for single-threaded use; for concurrent use, prefer `Collections.synchronizedList(new ArrayList<>())` with explicit external locking for compound operations, or [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md) for read-heavy, write-light workloads.
- `Vector` retains legacy method names (`addElement`, `firstElement`, `elementAt`) from before the Collections Framework standardized on `List`'s modern method names.
- There is essentially no reason to choose `Vector` deliberately in new code — it exists today mainly for backward compatibility with old APIs and codebases.
