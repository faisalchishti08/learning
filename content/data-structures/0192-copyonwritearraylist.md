---
card: data-structures
gi: 192
slug: copyonwritearraylist
title: CopyOnWriteArrayList
---

## 1. What it is

`CopyOnWriteArrayList` is a thread-safe `List` where every mutating operation (`add`, `remove`, `set`) creates a **brand-new copy** of the entire backing array, rather than modifying the existing one in place. Reads always operate on a stable, unchanging array reference, needing no locking at all.

## 2. Why & when

Use `CopyOnWriteArrayList` for lists that are read constantly but written to rarely — a list of event listeners, a set of configuration values checked on every request but updated only occasionally, or any shared list where iteration vastly outnumbers mutation. Its `O(n)` write cost (copying the whole array) makes it a poor fit for write-heavy workloads; for those, [ConcurrentHashMap](0191-concurrenthashmap.md)-style fine-grained locking (or a different structure entirely) is more appropriate.

## 3. Core concept

**What backs it.** A single `volatile` reference to an array. Every read operation (`get`, iteration) reads this reference once and works with the array it points to, entirely lock-free. Every write operation acquires an internal lock, but only to safely swap the reference — the actual array copy-and-modify work does not block concurrent readers, who keep using whatever array reference they already grabbed.

**The core mechanism, step by step.** A mutation (say, `add(x)`) does not touch the current array in place. Instead, it: allocates a new array one element larger, copies every existing element into it, appends the new element, and finally updates the `volatile` reference to point at this new array. Any reader already iterating the old array continues seeing the old array's contents — this is not a bug, it is the deliberate fail-safe design covered in [fail-fast vs fail-safe iterators](0187-fail-fast-vs-fail-safe-iterators.md).

**Why iteration never throws, and never sees a partial mutation.** An iterator created via `.iterator()` captures a reference to the array at that exact moment. Because arrays are never mutated in place — every write is a full copy-and-swap — the iterator's captured array can never change underneath it. The iterator either sees the whole array as it was, unchanged, for the entire traversal, with no possibility of seeing a half-updated state.

**The cost.** Every mutation is `O(n)` — proportional to the list's current size, regardless of how small the actual change is. Adding one element to a list of a million elements copies all million. This is the direct tradeoff for lock-free, always-consistent reads.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CopyOnWriteArrayList replacing its entire backing array on every write, while an in-progress iterator keeps using its own captured reference to the old array">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Before add(4): volatile ref -&gt; array_v1 [1,2,3]</text>
    <rect x="20" y="30" width="150" height="30" fill="#161b22" stroke="#79c0ff"/><text x="95" y="50" text-anchor="middle" font-size="9">array_v1: [1,2,3]</text>

    <text x="10" y="90">add(4): copy, append, then swap the reference</text>
    <rect x="20" y="100" width="150" height="30" fill="#0d1117" stroke="#8b949e"/><text x="95" y="120" text-anchor="middle" font-size="9">array_v1 [1,2,3] (old, unreferenced by list)</text>
    <rect x="220" y="100" width="180" height="30" fill="#161b22" stroke="#3fb950"/><text x="310" y="120" text-anchor="middle" font-size="9">array_v2: [1,2,3,4] (new, live)</text>

    <text x="10" y="160" fill="#f0883e">iterator created BEFORE add(4) still holds array_v1</text>
    <text x="10" y="180" fill="#f0883e">-&gt; sees [1,2,3] for its whole traversal, never [1,2,3,4]</text>
  </g>
</svg>

Old array references stay valid and unchanged; only the list's own pointer moves to the new array.

## 5. Runnable example

```java
// CopyOnWriteArrayListDemo.java
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

public class CopyOnWriteArrayListDemo {

    // Basic: safe concurrent iteration and mutation from different threads, no ConcurrentModificationException.
    static void basicLevel() throws InterruptedException {
        CopyOnWriteArrayList<Integer> list = new CopyOnWriteArrayList<>(List.of(1, 2, 3));

        Thread reader = new Thread(() -> {
            for (int value : list) {
                System.out.println("basic: reader saw -> " + value);
            }
        });
        Thread writer = new Thread(() -> list.add(4));

        reader.start();
        writer.start();
        reader.join();
        writer.join();

        System.out.println("basic: final list -> " + list);
    }

    // Intermediate: the classic use case -- a shared listener list, iterated far more often than modified.
    interface Listener { void onEvent(String event); }

    static class EventBus {
        CopyOnWriteArrayList<Listener> listeners = new CopyOnWriteArrayList<>();

        void subscribe(Listener listener) { listeners.add(listener); }

        void publish(String event) {
            for (Listener listener : listeners) { // safe even if a listener subscribes/unsubscribes during this loop
                listener.onEvent(event);
            }
        }
    }

    static void intermediateLevel() {
        EventBus bus = new EventBus();
        bus.subscribe(event -> System.out.println("intermediate: listener A got -> " + event));
        bus.subscribe(event -> {
            System.out.println("intermediate: listener B got -> " + event);
            bus.subscribe(e -> System.out.println("intermediate: newly added listener C got -> " + e));
        });

        bus.publish("first event");   // listener C is added mid-publish, but this iteration's snapshot excludes it
        bus.publish("second event");  // listener C IS present now, since this is a new iteration over the new array
    }

    // Advanced: measuring the O(n) write cost directly, to show why this structure suits read-heavy workloads only.
    static void advancedLevel() {
        int n = 20_000;
        CopyOnWriteArrayList<Integer> cowList = new CopyOnWriteArrayList<>();
        long start = System.nanoTime();
        for (int i = 0; i < n; i++) cowList.add(i); // each add() copies the whole array so far
        long cowTime = System.nanoTime() - start;

        List<Integer> plainSynced = Collections.synchronizedList(new ArrayList<>());
        start = System.nanoTime();
        for (int i = 0; i < n; i++) plainSynced.add(i);
        long syncedTime = System.nanoTime() - start;

        System.out.printf("advanced: CopyOnWriteArrayList %d appends -> %.1f ms%n", n, cowTime / 1_000_000.0);
        System.out.printf("advanced: synchronizedList %d appends -> %.1f ms%n", n, syncedTime / 1_000_000.0);
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java CopyOnWriteArrayListDemo.java`

## 6. Walkthrough

In `basicLevel`, a reader thread iterates `[1, 2, 3]` while a writer thread concurrently calls `add(4)`. Regardless of the exact timing, the reader never throws `ConcurrentModificationException` — it either sees `[1, 2, 3]` (if its iterator captured the array before the write completed) or, since the iterator is created once at the start of the for-each loop, it consistently uses whichever array reference it grabbed at that moment. After both threads finish, `list` itself (a fresh read of the current reference) correctly shows `[1, 2, 3, 4]`.

In the `EventBus` example: `publish("first event")` starts iterating the current listener array (`[A, B]`). While handling `B`, a new listener `C` is subscribed — this calls `add`, which creates a **new** array `[A, B, C]` and swaps the bus's reference to it. But the `publish` call's iterator already grabbed the **old** array `[A, B]` before this happened, so it finishes this iteration without ever calling `C`. The next call, `publish("second event")`, creates a fresh iterator, which reads the *current* reference — now pointing at `[A, B, C]` — so `C` receives this second event correctly.

The `advancedLevel` benchmark appends `20,000` elements one at a time. For `CopyOnWriteArrayList`, each `add` copies the entire array built so far, making the total cost `O(n^2)` for `n` sequential appends — dramatically slower than `Collections.synchronizedList(new ArrayList<>())`, whose amortized `O(1)` appends (via array doubling) make the whole sequence `O(n)`. This stark difference is exactly why `CopyOnWriteArrayList` is reserved for read-heavy, write-rare scenarios.

**Complexity.** Read (`get`, iteration): `O(1)` per `get`, `O(n)` for a full traversal, lock-free. Write (`add`, `remove`, `set`): `O(n)` per call, due to the full array copy. Space: `O(n)`, with a temporary `O(n)` spike during each write while both the old and new arrays briefly coexist.

## 7. Gotchas & takeaways

> An iterator created before a concurrent mutation will **never** see that mutation, no matter how the two threads are timed — this is a deliberate design (a true snapshot, not a "best-effort" weak consistency), and code that assumes an iterator will pick up in-flight changes will be surprised.

- Never use `CopyOnWriteArrayList` for a large, frequently-mutated list — the `O(n)` cost per write, repeated often, degrades badly; reach for it specifically when reads vastly outnumber writes.
- The listener-list pattern (subscribe rarely, publish/iterate often) is the textbook use case this structure was designed for — it appears throughout Java's own standard library and many frameworks for exactly this reason.
- For a structure with balanced, frequent reads **and** writes across many threads, prefer [ConcurrentHashMap](0191-concurrenthashmap.md) (for map-shaped data) or a purpose-built concurrent queue (see [concurrent queues overview](0193-concurrent-queues-overview.md)) instead.
