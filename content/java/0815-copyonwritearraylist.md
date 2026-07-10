---
card: java
gi: 815
slug: copyonwritearraylist
title: CopyOnWriteArrayList
---

## 1. What it is

`CopyOnWriteArrayList` is a thread-safe `List` implementation (in `java.util.concurrent`) built on a completely different safety strategy than [`Vector`](0814-vector-legacy-synchronized.md)'s per-method locking: every **mutating** operation (`add`, `remove`, `set`) copies the entire backing array, applies the change to the copy, and then atomically swaps the internal reference to point at the new array. Reads (`get`, iteration, `size`) never lock at all — they simply read whatever array reference was current at the moment they started, entirely undisturbed by concurrent writes happening elsewhere. Iterators obtained from a `CopyOnWriteArrayList` are **snapshot iterators**: they iterate the array as it existed at the moment `iterator()` was called, and never throw `ConcurrentModificationException`, even if the list is mutated concurrently.

## 2. Why & when

Lock-based thread safety (like `Vector`'s) forces every reader to contend with every writer, even when reads vastly outnumber writes — a poor trade-off for workloads like a list of event listeners that's iterated constantly but modified rarely (a listener registering or unregistering). `CopyOnWriteArrayList` flips the cost: writes become expensive (a full array copy every time), but reads become essentially free — no locking, no blocking, no exceptions from concurrent modification. This is exactly the right trade for **read-heavy, write-light** concurrent scenarios: listener lists, configuration snapshots read far more often than updated, or any list iterated far more frequently than mutated. It is the *wrong* choice for write-heavy workloads — copying a large array on every single `add()` call scales badly as the list grows.

## 3. Core concept

```java
CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>();
listeners.add("logger");
listeners.add("metrics");

Iterator<String> snapshot = listeners.iterator(); // captures the array AS IT IS right now

listeners.add("audit"); // mutates a NEW internal array; the snapshot above is unaffected

while (snapshot.hasNext()) {
    System.out.println(snapshot.next()); // still only prints "logger" and "metrics" -- "audit" is invisible to this iterator
}
```

The iterator obtained before the `add("audit")` call never sees `"audit"`, because it's iterating a frozen snapshot of the array from before that write — this is fundamentally different from `ArrayList`'s fail-fast iterator, which would throw `ConcurrentModificationException` in the equivalent situation instead of silently ignoring the change.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A CopyOnWriteArrayList write copies the entire array, mutates the copy, then atomically swaps the reference, so any iterator already in progress keeps reading the old array undisturbed">
  <rect x="40" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">array v1: [logger, metrics]</text>

  <text x="320" y="55" fill="#79c0ff" font-size="10" font-family="sans-serif">&lt;- iterator snapshot still reads this</text>

  <line x1="150" y1="70" x2="150" y2="100" stroke="#f0883e" stroke-width="2" marker-end="url(#a815)"/>
  <text x="270" y="90" fill="#f0883e" font-size="10" font-family="sans-serif">add("audit") copies + appends</text>

  <rect x="40" y="105" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="180" y="130" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">array v2: [logger, metrics, audit]</text>
  <text x="470" y="130" fill="#3fb950" font-size="10" font-family="sans-serif">&lt;- new reads see this instead</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The internal reference swaps atomically; readers already in flight are unaffected either way</text>

  <defs><marker id="a815" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

*Writes copy-and-swap the whole array; readers always see a consistent, unchanging snapshot for the duration of their operation.*

## 5. Runnable example

Scenario: a shared event-listener registry, growing from basic thread-safe registration/notification to proving iteration never throws during concurrent modification, to a realistic multi-writer benchmark showing the actual cost of the copy-on-write strategy.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.*;

public class ListenerRegistryBasic {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>();
        listeners.add("logger");
        listeners.add("metrics");
        listeners.add("audit");

        System.out.println("notifying listeners:");
        for (String listener : listeners) {
            System.out.println("  -> " + listener + " notified");
        }
    }
}
```

**How to run:** `java ListenerRegistryBasic.java` (JDK 17+).

Expected output:
```
notifying listeners:
  -> logger notified
  -> metrics notified
  -> audit notified
```

Used single-threaded here, `CopyOnWriteArrayList` behaves exactly like an `ArrayList` — the difference only becomes visible under concurrent modification.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class ListenerRegistrySnapshot {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>();
        listeners.add("logger");
        listeners.add("metrics");

        Iterator<String> inProgressNotification = listeners.iterator(); // snapshot taken NOW

        // Simulate a listener registering itself WHILE notification is in progress elsewhere --
        // an ArrayList's iterator would throw ConcurrentModificationException here instead.
        listeners.add("audit");
        listeners.remove("logger");

        System.out.println("in-progress notification only sees the OLD snapshot:");
        while (inProgressNotification.hasNext()) {
            System.out.println("  -> " + inProgressNotification.next() + " notified");
        }

        System.out.println("current listener list (reflects the concurrent changes): " + listeners);
    }
}
```

**How to run:** `java ListenerRegistrySnapshot.java`.

Expected output:
```
in-progress notification only sees the OLD snapshot:
  -> logger notified
  -> metrics notified
current listener list (reflects the concurrent changes): [metrics, audit]
```

The real-world concern added: proving the snapshot-iterator guarantee directly. Even though `"logger"` is removed and `"audit"` is added *after* the iterator was obtained but *before* iteration finishes, the in-progress notification loop still sees the original two-element snapshot — no exception, no missing or duplicated notification mid-loop, just a consistent (if slightly stale) view.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ListenerRegistryBenchmark {
    public static void main(String[] args) throws InterruptedException {
        CopyOnWriteArrayList<Integer> cowList = new CopyOnWriteArrayList<>();
        int writerThreads = 4;
        int writesPerThread = 2_000;

        long start = System.currentTimeMillis();
        ExecutorService pool = Executors.newFixedThreadPool(writerThreads);
        AtomicInteger nextValue = new AtomicInteger();
        for (int t = 0; t < writerThreads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < writesPerThread; i++) {
                    cowList.add(nextValue.incrementAndGet()); // each add() copies the WHOLE array
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("final size: " + cowList.size());
        System.out.println("total writes: " + (writerThreads * writesPerThread));
        System.out.println("elapsed: " + elapsed + " ms (grows roughly with size^2 as the list gets bigger)");
        System.out.println("-> each add() on a list of size N copies all N existing elements first");
    }
}
```

**How to run:** `java ListenerRegistryBenchmark.java`. Exact timing varies by machine, but it will be noticeably slower than the equivalent workload on a lock-based list, because every single `add()` call copies the entire (ever-growing) array.

Expected output shape:
```
final size: 8000
total writes: 8000
elapsed: ~600 ms (grows roughly with size^2 as the list gets bigger)
-> each add() on a list of size N copies all N existing elements first
```

This adds the production-flavored hard case: demonstrating the actual cost of copy-on-write under a **write-heavy** workload from multiple threads. Every one of the 8,000 `add()` calls copies the entire array as it stood at that moment — the 1st call copies 0 elements, the 8,000th call copies 7,999 — so total work across all writes is roughly O(n²) for n total writes, a real and significant cost that only makes sense to pay when reads vastly outnumber writes.

## 6. Walkthrough

Tracing `ListenerRegistryBenchmark.main`:

1. Four writer threads are submitted to a pool, each looping 2,000 times and calling `cowList.add(...)`.
2. Every call to `add()`, regardless of which thread makes it, internally: acquires an internal lock (so concurrent writers don't corrupt each other), allocates a new array one element larger than the current one, copies every existing element into it, appends the new value, and atomically republishes the new array as the list's current backing array.
3. Because each `add()` copies the *entire* array as it exists at that moment, the cost of each individual write grows linearly with how many elements are already present — the very first calls are cheap (copying almost nothing), but calls happening once the list has grown to thousands of elements are copying thousands of elements each time.
4. Summed across all 8,000 total writes from all four threads, this produces roughly quadratic total work — visibly slower than a lock-based list of the same final size would be for the same number of writes, which is the direct, measurable cost of the copy-on-write strategy.
5. `cowList.size()` after all threads complete reports `8000`, confirming every write from every thread succeeded correctly — the internal locking on writers, combined with atomic reference swaps, ensures no write is lost or corrupted even though four threads are all calling `add()` concurrently.

## 7. Gotchas & takeaways

> **Gotcha:** an iterator's snapshot semantics mean any element added or removed **after** the iterator was created is invisible to that iterator, silently — no exception, no partial visibility, nothing to signal that the view is stale. Code that needs to see the absolute latest state during iteration (rather than a point-in-time snapshot) needs a different concurrency strategy, such as [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md)'s weakly-consistent iterators or explicit synchronization.

- `CopyOnWriteArrayList` makes every write copy the entire backing array and atomically swap the reference; reads and iteration never lock and never throw `ConcurrentModificationException`.
- Iterators are **snapshot-based**: they see the array exactly as it was when `iterator()` was called, permanently, regardless of concurrent mutations afterward.
- This trade-off is ideal for read-heavy, write-light workloads (listener lists, rarely-changed configuration) and poor for write-heavy workloads, where the O(n) copy per write adds up.
- Unlike [`Vector`](0814-vector-legacy-synchronized.md) or `Collections.synchronizedList`, there's no way for `CopyOnWriteArrayList` to throw `ConcurrentModificationException` — its safety model is fundamentally different, not just "the same lock, applied more carefully."
- Choose it deliberately based on the actual read/write ratio of the workload — it is not a universal drop-in replacement for `ArrayList` in concurrent code.
