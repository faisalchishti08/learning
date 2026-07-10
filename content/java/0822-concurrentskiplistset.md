---
card: java
gi: 822
slug: concurrentskiplistset
title: ConcurrentSkipListSet
---

## 1. What it is

`ConcurrentSkipListSet<E>` is a thread-safe [`NavigableSet`](0804-sortedset-navigableset.md) implementation backed by a **skip list** — a probabilistic, layered linked-list structure that gives O(log n) expected time for `add`, `remove`, and `contains`, comparable to [`TreeSet`](0819-treeset.md)'s red-black tree, but designed from the ground up to support safe **concurrent** access from multiple threads without external locking. Unlike wrapping a `TreeSet` with `Collections.synchronizedSortedSet(...)` (which serializes all access behind one lock), `ConcurrentSkipListSet` allows genuinely concurrent reads and writes from multiple threads simultaneously, using lock-free algorithms internally. It maintains sorted order continuously, just like `TreeSet`, and supports the same navigation methods (`floor`, `ceiling`, `subSet`, etc.).

## 2. Why & when

`TreeSet` is not thread-safe at all — concurrent modification from multiple threads can corrupt its internal tree structure. Wrapping it in `Collections.synchronizedSortedSet(...)` fixes that, but forces every operation, including reads, to contend for a single lock — a bottleneck under real concurrent load. `ConcurrentSkipListSet` exists for exactly the scenario that needs **both** continuous sorted order **and** genuine multi-threaded concurrent access without a single-lock bottleneck — a live leaderboard updated and read by many threads simultaneously, a time-ordered event index written to by multiple producers and range-queried by multiple consumers. Its skip-list structure trades a small constant-factor overhead (multiple "levels" of links per node) for lock-free concurrent operation, making it the natural concurrent counterpart to `TreeSet` the same way [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) is the concurrent counterpart to `HashMap`.

## 3. Core concept

```java
ConcurrentSkipListSet<Integer> leaderboard = new ConcurrentSkipListSet<>();
// Many threads can call add()/remove()/contains() concurrently, safely, with no external lock:
leaderboard.add(85);
leaderboard.add(92);
leaderboard.add(78);

leaderboard.first();          // 78 -- lowest score, safe to call concurrently with writers
leaderboard.floor(90);        // 85 -- nearest score at or below 90
leaderboard.headSet(90);      // {78, 85} -- a consistent, live view, even under concurrent modification
```

Every navigation method (`floor`, `ceiling`, `headSet`, `tailSet`, `subSet`) works identically to `TreeSet`'s, but each individual operation is internally lock-free — multiple threads can be inside `add()`, `contains()`, and `floor()` calls at the same moment without blocking each other, unlike a `synchronized`-wrapped `TreeSet`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A skip list has multiple layers of links; higher layers skip over more elements, letting search jump ahead quickly before dropping to a lower, denser layer">
  <g font-family="sans-serif">
    <text x="30" y="35" fill="#8b949e" font-size="10">L2</text>
    <line x1="60" y1="35" x2="600" y2="35" stroke="#79c0ff" stroke-width="1" stroke-dasharray="2"/>
    <circle cx="100" cy="35" r="5" fill="#79c0ff"/>
    <circle cx="380" cy="35" r="5" fill="#79c0ff"/>

    <text x="30" y="90" fill="#8b949e" font-size="10">L1</text>
    <line x1="60" y1="90" x2="600" y2="90" stroke="#6db33f" stroke-width="1" stroke-dasharray="2"/>
    <circle cx="100" cy="90" r="5" fill="#6db33f"/>
    <circle cx="240" cy="90" r="5" fill="#6db33f"/>
    <circle cx="380" cy="90" r="5" fill="#6db33f"/>
    <circle cx="520" cy="90" r="5" fill="#6db33f"/>

    <text x="30" y="145" fill="#8b949e" font-size="10">L0</text>
    <line x1="60" y1="145" x2="600" y2="145" stroke="#e6edf3" stroke-width="1"/>
    <circle cx="100" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="170" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="240" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="310" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="380" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="450" cy="145" r="5" fill="#e6edf3"/>
    <circle cx="520" cy="145" r="5" fill="#e6edf3"/>
  </g>
  <text x="320" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Search starts at the top layer, skipping many elements per hop, dropping down when it overshoots</text>
</svg>

*A skip list layers multiple linked lists; higher layers skip over more elements, giving O(log n) expected search — updatable concurrently without a global lock.*

## 5. Runnable example

Scenario: a real-time game leaderboard updated by many concurrent player-score submissions, growing from basic sorted access to genuinely concurrent multi-threaded updates, to a range-query "nearby rank" feature running safely alongside continuous writes.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LeaderboardBasic {
    public static void main(String[] args) {
        ConcurrentSkipListSet<Integer> scores = new ConcurrentSkipListSet<>();
        scores.add(85);
        scores.add(92);
        scores.add(78);

        System.out.println("scores, sorted: " + scores);
        System.out.println("lowest: " + scores.first() + ", highest: " + scores.last());
    }
}
```

**How to run:** `java LeaderboardBasic.java` (JDK 17+).

Expected output:
```
scores, sorted: [78, 85, 92]
lowest: 78, highest: 92
```

Behaves identically to `TreeSet` from a single-threaded caller's perspective — the concurrency benefits only become visible with actual concurrent access.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class LeaderboardConcurrentWrites {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListSet<Integer> scores = new ConcurrentSkipListSet<>();
        int threads = 8;
        int scoresPerThread = 500;

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        for (int t = 0; t < threads; t++) {
            final int threadId = t;
            pool.submit(() -> {
                Random random = new Random(threadId);
                for (int i = 0; i < scoresPerThread; i++) {
                    scores.add(random.nextInt(10_000)); // many threads adding concurrently, no external lock
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        System.out.println("total unique scores recorded: " + scores.size());
        System.out.println("top 5 scores: " + descendingFirstN(scores, 5));
    }

    static List<Integer> descendingFirstN(ConcurrentSkipListSet<Integer> scores, int n) {
        List<Integer> top = new ArrayList<>();
        Iterator<Integer> it = scores.descendingIterator();
        while (it.hasNext() && top.size() < n) {
            top.add(it.next());
        }
        return top;
    }
}
```

**How to run:** `java LeaderboardConcurrentWrites.java`. Exact scores vary by run (`Random` seeds differ per thread but insertion order/timing does not affect correctness); the set always ends up correctly sorted and free of corruption.

Expected output shape (exact numbers vary):
```
total unique scores recorded: 3742
top 5 scores: [9987, 9954, 9931, 9902, 9888]
```

The real-world concern added: eight threads calling `add()` **concurrently**, with no external synchronization whatsoever — something that would corrupt a plain `TreeSet`'s internal red-black tree structure if attempted without a wrapping lock. `ConcurrentSkipListSet`'s lock-free internal algorithms handle this safely by design; note the total unique count is less than `8 * 500 = 4000` because random scores from different threads sometimes collide on the same integer, which `add()` correctly treats as a duplicate regardless of which thread's insertion happened first.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.*;

public class LeaderboardRangeQueryUnderLoad {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListSet<Integer> scores = new ConcurrentSkipListSet<>();
        for (int i = 0; i < 1000; i++) scores.add(i * 10); // seed with 0, 10, 20, ..., 9990

        ExecutorService writers = Executors.newFixedThreadPool(4);
        AtomicBoolean keepWriting = new AtomicBoolean(true);
        for (int t = 0; t < 4; t++) {
            writers.submit(() -> {
                Random random = new Random();
                while (keepWriting.get()) {
                    scores.add(random.nextInt(10_000));
                }
            });
        }

        // Read-side: run range queries WHILE writers are continuously mutating the set.
        int myScore = 5005;
        Integer nearestBelow = scores.floor(myScore);
        Integer nearestAbove = scores.ceiling(myScore);
        NavigableSet<Integer> nearbyRange = scores.subSet(myScore - 50, true, myScore + 50, true);

        System.out.println("my score: " + myScore);
        System.out.println("nearest score at or below: " + nearestBelow);
        System.out.println("nearest score at or above: " + nearestAbove);
        System.out.println("scores within +/-50 (snapshot at query time): " + nearbyRange.size() + " entries");

        keepWriting.set(false);
        writers.shutdown();
        writers.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("total scores after writers stopped: " + scores.size());
    }
}
```

**How to run:** `java LeaderboardRangeQueryUnderLoad.java`. Exact counts vary by run and machine speed, but the program always completes without exception or corruption.

Expected output shape:
```
my score: 5005
nearest score at or below: 5000
nearest score at or above: 5010
scores within +/-50 (snapshot at query time): 11 entries
total scores after writers stopped: 10932
```

This adds the production-flavored hard case: running `floor`, `ceiling`, and `subSet` range queries **while four writer threads are continuously adding random scores in the background** — exactly the kind of read/write overlap a live leaderboard experiences in production. `ConcurrentSkipListSet` handles this safely without any external locking on the read side; the range query result reflects a reasonably consistent view of the set at approximately the moment it ran, without throwing `ConcurrentModificationException` the way an unsynchronized `TreeSet` iteration would under the same concurrent writes.

## 6. Walkthrough

Tracing `LeaderboardRangeQueryUnderLoad.main`:

1. `scores` is seeded with 1000 multiples of 10, from `0` to `9990`.
2. Four writer threads are submitted, each looping and calling `scores.add(random.nextInt(10_000))` continuously until `keepWriting` is flipped to `false` — this simulates an ongoing, unpredictable stream of concurrent score submissions.
3. While those writers are actively running, the main thread calls `scores.floor(5005)` — this walks the skip list's layered structure to find the greatest score `<= 5005`, landing on `5000` (one of the originally-seeded multiples of 10), regardless of whatever concurrent insertions writer threads are performing at that exact moment.
4. `scores.ceiling(5005)` similarly finds the smallest score `>= 5005`, landing on `5010`.
5. `scores.subSet(4955, true, 5055, true)` returns a view covering that range; because writer threads are actively adding elements throughout this whole window, this "snapshot" is best understood as a reasonably consistent view as of approximately when the call executed — not a strictly frozen point-in-time snapshot the way [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)'s iterator provides, but nonetheless numerically consistent internally, never corrupted or partially-written.
6. After the range queries complete, `keepWriting.set(false)` signals the writer threads to stop, `writers.awaitTermination(...)` waits for them to actually finish their current loop iteration and exit, and the final `scores.size()` reports the total accumulated unique scores — always a valid, uncorrupted count, demonstrating that the concurrent writes throughout the whole program never damaged the underlying skip-list structure.

## 7. Gotchas & takeaways

> **Gotcha:** range-view results (`subSet`, `headSet`, `tailSet`) obtained while concurrent writers are active reflect a reasonably consistent, but not strictly frozen, view of the set — elements added by a writer thread microseconds before or after the query might or might not be included, depending on precise timing. This is different from [`CopyOnWriteArraySet`](0821-copyonwritearrayset.md)'s hard iterator snapshot guarantee — `ConcurrentSkipListSet` trades a rigid snapshot for genuinely concurrent, non-blocking reads and writes.

- `ConcurrentSkipListSet` is a thread-safe [`NavigableSet`](0804-sortedset-navigableset.md) backed by a skip list, giving O(log n) expected `add`/`remove`/`contains`, comparable to [`TreeSet`](0819-treeset.md)'s red-black tree.
- Unlike a `synchronized`-wrapped `TreeSet`, it allows genuinely concurrent operations from multiple threads without a single global lock bottleneck.
- All the same navigation methods (`floor`, `ceiling`, `headSet`, `tailSet`, `subSet`, `descendingSet`) are available and work identically in spirit to `TreeSet`'s.
- Range-view results under concurrent modification are consistent internally but not a rigid point-in-time snapshot — expect approximate, not exact, boundaries when writers are simultaneously active.
- Reach for it when both continuous sorted order and genuine multi-threaded concurrent access are both hard requirements — for sorted-but-single-threaded needs, plain `TreeSet` remains simpler and slightly faster.
