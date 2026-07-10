---
card: java
gi: 831
slug: concurrentskiplistmap
title: ConcurrentSkipListMap
---

## 1. What it is

`ConcurrentSkipListMap<K, V>` is the concurrent counterpart to [`TreeMap`](0825-treemap-red-black-tree.md) — a thread-safe [`NavigableMap`](0808-sortedmap-navigablemap.md) implementation backed by a **skip list**, giving O(log n) expected time for `put`/`get`/`remove`/navigation operations, just like `TreeMap`'s red-black tree, but designed for genuinely concurrent multi-threaded access without a single map-wide lock. It's the `Map` sibling of [`ConcurrentSkipListSet`](0822-concurrentskiplistset.md) (in fact, `ConcurrentSkipListSet` is implemented internally on top of a `ConcurrentSkipListMap`), and it supports the same full range of navigation methods `TreeMap` does — `floorKey`, `ceilingEntry`, `subMap`, `descendingMap`, and the rest — all safe to call concurrently with ongoing writes from other threads.

## 2. Why & when

`TreeMap` carries no concurrency guarantees at all — concurrent modification from multiple threads can corrupt its internal red-black tree. Wrapping it with `Collections.synchronizedSortedMap(...)` fixes correctness but forces every operation, reads included, to serialize behind one lock. `ConcurrentSkipListMap` exists for exactly the case that needs **both** continuously maintained sorted order **and** genuinely concurrent access without that single-lock bottleneck — a time-indexed event log written to by multiple producer threads and range-queried by multiple consumer threads simultaneously, or a live, sorted price index updated by many market-data feed threads at once. Choose it over [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) specifically when sorted iteration or range/nearest-key queries are a hard requirement — `ConcurrentHashMap` alone gives no ordering guarantee whatsoever.

## 3. Core concept

```java
ConcurrentSkipListMap<Long, String> eventLog = new ConcurrentSkipListMap<>();

// Many threads can safely call these concurrently, with no external locking:
eventLog.put(System.currentTimeMillis(), "user logged in");
eventLog.put(System.currentTimeMillis(), "cache refreshed");

eventLog.firstEntry();          // earliest event, safe to call while writers are active
eventLog.floorEntry(someTime);  // most recent event at or before someTime
eventLog.tailMap(someTime);     // all events from someTime onward -- a live, navigable view
```

Every method available on `TreeMap` is present here with matching semantics, but each is implemented to allow genuinely concurrent execution — multiple threads can be inside `put`, `get`, and `floorEntry` calls at the same time without blocking each other on a shared lock.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple producer threads write timestamped events into a ConcurrentSkipListMap while multiple consumer threads run range queries, all without a single shared lock">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="110" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">producer thread 1</text>
    <rect x="40" y="75" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="110" y="97" fill="#e6edf3" font-size="10" text-anchor="middle">producer thread 2</text>

    <line x1="180" y1="47" x2="260" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a831)"/>
    <line x1="180" y1="92" x2="260" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a831)"/>

    <rect x="260" y="65" width="120" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="320" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">skip list (sorted)</text>

    <line x1="380" y1="75" x2="460" y2="47" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a831)"/>
    <line x1="380" y1="95" x2="460" y2="97" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a831)"/>

    <rect x="460" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="530" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">consumer: range query</text>
    <rect x="460" y="75" width="140" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="530" y="97" fill="#e6edf3" font-size="10" text-anchor="middle">consumer: floorEntry</text>
  </g>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No single lock serializes access — all four threads can operate concurrently</text>

  <defs><marker id="a831" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Multiple producers and consumers operate on the same sorted structure concurrently — no map-wide lock serializes them.*

## 5. Runnable example

Scenario: a shared, time-ordered event log written to by multiple producer threads and queried by range simultaneously, growing from basic sorted storage to genuinely concurrent multi-producer writes, to a live "recent events" range query running safely alongside continuous writes.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class EventLogBasic {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListMap<Long, String> eventLog = new ConcurrentSkipListMap<>();

        eventLog.put(1000L, "startup");
        eventLog.put(3000L, "config loaded");
        eventLog.put(2000L, "connecting to database");

        System.out.println("events in chronological order:");
        eventLog.forEach((time, description) -> System.out.println("  " + time + ": " + description));
    }
}
```

**How to run:** `java EventLogBasic.java` (JDK 17+).

Expected output:
```
events in chronological order:
  1000: startup
  2000: connecting to database
  3000: config loaded
```

Even though `"config loaded"` (timestamp 3000) was inserted before `"connecting to database"` (timestamp 2000), iteration always follows sorted key order — behaving exactly like `TreeMap` from a single-threaded perspective.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class EventLogConcurrentProducers {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListMap<Long, String> eventLog = new ConcurrentSkipListMap<>();
        int producers = 6;
        int eventsPerProducer = 1000;
        AtomicLong sequence = new AtomicLong(); // guarantees unique, monotonically increasing keys

        ExecutorService pool = Executors.newFixedThreadPool(producers);
        for (int p = 0; p < producers; p++) {
            final int producerId = p;
            pool.submit(() -> {
                for (int i = 0; i < eventsPerProducer; i++) {
                    long timestamp = sequence.incrementAndGet();
                    eventLog.put(timestamp, "producer-" + producerId + "-event-" + i);
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        System.out.println("total events recorded: " + eventLog.size());
        System.out.println("first event: " + eventLog.firstEntry());
        System.out.println("last event: " + eventLog.lastEntry());
    }
}
```

**How to run:** `java EventLogConcurrentProducers.java`. The exact `firstEntry`/`lastEntry` content can vary between runs (since thread scheduling determines which producer claims which sequence number), but `size()` is always exactly `producers * eventsPerProducer`.

Expected output shape:
```
total events recorded: 6000
first event: 1=producer-3-event-0
last event: 6000=producer-2-event-999
```

The real-world concern added: six threads calling `put()` **concurrently**, using an `AtomicLong` to guarantee each event gets a unique, strictly increasing timestamp key even though multiple threads are racing to claim the next sequence number — `ConcurrentSkipListMap`'s lock-free-friendly internal structure handles the concurrent insertions safely, maintaining full sorted order throughout, with every one of the 6,000 events correctly recorded.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.*;

public class EventLogLiveRangeQuery {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListMap<Long, String> eventLog = new ConcurrentSkipListMap<>();
        AtomicLong sequence = new AtomicLong();
        AtomicBoolean keepWriting = new AtomicBoolean(true);

        ExecutorService writers = Executors.newFixedThreadPool(4);
        for (int w = 0; w < 4; w++) {
            writers.submit(() -> {
                while (keepWriting.get()) {
                    long ts = sequence.incrementAndGet();
                    eventLog.put(ts, "event-" + ts);
                }
            });
        }

        Thread.sleep(50); // let writers get a head start

        // Read-side: a "most recent N events" query, run WHILE writers are continuously active.
        long latestSeenAtQueryTime = eventLog.lastKey();
        NavigableMap<Long, String> recentWindow = eventLog.tailMap(latestSeenAtQueryTime - 100, true);

        System.out.println("latest key observed at query time: " + latestSeenAtQueryTime);
        System.out.println("events in the trailing window: " + recentWindow.size() + " (approximately 100, may include a few more from concurrent writes)");

        keepWriting.set(false);
        writers.shutdown();
        writers.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("total events after writers stopped: " + eventLog.size());
    }
}
```

**How to run:** `java EventLogLiveRangeQuery.java`. Exact counts vary by machine speed and timing, but the program always completes correctly without exceptions or data corruption.

Expected output shape:
```
latest key observed at query time: 48213
events in the trailing window: 103
total events after writers stopped: 91847
```

This adds the production-flavored hard case: running a **range query** (`tailMap`, for "the most recent events") while four writer threads are continuously inserting new entries in the background — precisely the read/write overlap a live, high-throughput event log experiences. `eventLog.lastKey()` and `tailMap(...)` both execute safely without external locking, reflecting a reasonably consistent view of the map at approximately the moment they ran, with no risk of `ConcurrentModificationException` or structural corruption despite the ongoing concurrent writes.

## 6. Walkthrough

Tracing `EventLogLiveRangeQuery.main`:

1. Four writer threads are submitted, each looping and calling `eventLog.put(sequence.incrementAndGet(), ...)` continuously until signaled to stop — `AtomicLong.incrementAndGet()` guarantees every thread gets a unique, strictly increasing sequence number even under contention from the other three threads.
2. After a brief head start (`Thread.sleep(50)`), the main thread calls `eventLog.lastKey()`, which walks the skip list's topmost layer to find the current maximum key — safely, even though writer threads may be inserting new, even-larger keys at that exact moment; the call simply returns whatever the largest key happens to be at the instant it completes.
3. `eventLog.tailMap(latestSeenAtQueryTime - 100, true)` returns a `NavigableMap` view covering keys from 100 below the observed latest key up through whatever the map's current maximum is **at the time each subsequent operation on that view executes** — since it's a live view, not a frozen copy, its exact boundary can shift slightly as more concurrent writes land, which is why the reported size is "approximately 100" rather than an exact guarantee.
4. `recentWindow.size()` is printed, reflecting a window that's numerically consistent (never corrupted, no duplicate or missing keys within the reported range) even though the underlying map continued receiving concurrent writes throughout this whole sequence.
5. `keepWriting.set(false)` signals all four writer threads to exit their loops; `writers.awaitTermination(...)` waits for them to actually finish, and the final `eventLog.size()` reports the total accumulated event count — always a valid, uncorrupted number, confirming the skip list's concurrent-safe design held up correctly across the program's entire execution.

## 7. Gotchas & takeaways

> **Gotcha:** like [`ConcurrentSkipListSet`](0822-concurrentskiplistset.md), a range view (`tailMap`, `headMap`, `subMap`) obtained while writers are concurrently active reflects a reasonably consistent, but not rigidly frozen, snapshot — its effective boundary can shift slightly if concurrent writes land in the queried range while the view is still being read. This is a fundamentally different guarantee than [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)'s hard iterator snapshot; don't assume `ConcurrentSkipListMap`'s range views are frozen the same way.

- `ConcurrentSkipListMap` is a thread-safe [`NavigableMap`](0808-sortedmap-navigablemap.md) backed by a skip list, giving O(log n) expected `put`/`get`/`remove`, comparable to [`TreeMap`](0825-treemap-red-black-tree.md)'s red-black tree.
- Unlike `Collections.synchronizedSortedMap`-wrapped `TreeMap`, it supports genuinely concurrent operations from multiple threads without a single global-lock bottleneck.
- It provides the same full navigation API as `TreeMap` (`floorKey`, `ceilingEntry`, `subMap`, `descendingMap`, etc.), all safe to call concurrently with ongoing writes.
- Range views under concurrent modification are internally consistent but not a rigid point-in-time snapshot — their effective boundaries can shift slightly under active concurrent writes.
- Choose it over [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) specifically when sorted order or range/nearest-key queries are hard requirements alongside concurrent access; otherwise `ConcurrentHashMap` remains the simpler, slightly faster default.
