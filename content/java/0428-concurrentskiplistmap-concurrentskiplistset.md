---
card: java
gi: 428
slug: concurrentskiplistmap-concurrentskiplistset
title: ConcurrentSkipListMap / ConcurrentSkipListSet
---

## 1. What it is

`ConcurrentSkipListMap` and `ConcurrentSkipListSet`, added in Java 6, are thread-safe, **sorted** collections — the concurrent equivalents of `TreeMap`/`TreeSet`, implementing `NavigableMap`/`NavigableSet` (covered in the previous two tutorials) with full support for `floor`/`ceiling`/`higher`/`lower`, range views, and descending order, all safely usable from multiple threads without any external synchronization. Internally, they use a **skip list** (a probabilistic, layered linked-list structure) rather than a red-black tree, since skip lists support lock-free concurrent insertion and traversal more naturally than balanced binary trees do.

## 2. Why & when

`TreeMap`/`TreeSet` are not thread-safe — concurrent modification from multiple threads can corrupt their internal tree structure. Wrapping one in `Collections.synchronizedSortedMap(...)` fixes the corruption risk but funnels every operation, including reads, through a single lock, and critically, **iterating a synchronized wrapper still requires the caller to manually synchronize on it externally** to avoid `ConcurrentModificationException` — an easy detail to miss.

`ConcurrentSkipListMap`/`Set` solve both problems directly: concurrent reads and writes are safe with no external locking needed at all, and their iterators are **weakly consistent** — they never throw `ConcurrentModificationException`, and reflect the state of the collection at some point at or after the iterator was created, without a snapshot or a lock. You reach for these any time you need `NavigableMap`/`NavigableSet`-style sorted, "closest match" behavior (a leaderboard, a sorted event timeline, a priced tier lookup) *and* the collection is genuinely shared and mutated across multiple threads — a case plain `TreeMap`/`TreeSet` simply cannot handle safely.

## 3. Core concept

```java
import java.util.concurrent.*;

ConcurrentSkipListMap<Integer, String> leaderboard = new ConcurrentSkipListMap<>();

// Safe to call from multiple threads concurrently, with no external synchronization:
leaderboard.put(500, "Alice");
leaderboard.put(300, "Bob");

// Full NavigableMap API works exactly as on TreeMap:
leaderboard.floorKey(400);        // 300
leaderboard.descendingMap();      // a reverse-order view, safe to iterate even during concurrent writes

// Iterating never throws ConcurrentModificationException, even if another thread
// inserts or removes an entry mid-iteration -- the iterator is "weakly consistent."
for (var entry : leaderboard.entrySet()) {
    // safe, even under concurrent modification from other threads
}
```

The tradeoff for this concurrency safety is that a weakly-consistent iterator might not reflect *every* concurrent change made during its traversal — it's guaranteed not to throw or corrupt anything, but it's not a frozen, fully up-to-date snapshot either.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A TreeMap wrapped for thread safety still requires external synchronization during iteration and throws ConcurrentModificationException if that's forgotten; ConcurrentSkipListMap needs no external locking and its iterator never throws">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">synchronizedSortedMap(TreeMap): iteration still needs manual synchronized(map){...}</text>
  <rect x="30" y="38" width="560" height="26" rx="4" fill="#1c2430" stroke="#f85149"/><text x="310" y="56" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">forget this, and a concurrent writer throws ConcurrentModificationException</text>

  <text x="20" y="100" fill="#6db33f" font-size="11" font-family="sans-serif">ConcurrentSkipListMap: no external locking needed, iterator never throws</text>
  <rect x="30" y="112" width="560" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="310" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">weakly-consistent iteration: safe under concurrent modification, always</text>
</svg>

`ConcurrentSkipListMap` removes an entire class of "did I remember to synchronize the iteration" bugs.

## 5. Runnable example

Scenario: a concurrently-updated game leaderboard, queried while players are actively submitting scores — the same leaderboard, evolved from basic concurrent inserts with sorted iteration, through safely iterating while another thread concurrently modifies the map, to querying the top-N scores via `NavigableMap` methods while a concurrent writer inserts more data.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LeaderboardBasic {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListMap<Integer, String> leaderboard = new ConcurrentSkipListMap<>();

        Thread alice = new Thread(() -> {
            leaderboard.put(450, "alice-run1");
            leaderboard.put(720, "alice-run2");
            leaderboard.put(310, "alice-run3");
        });
        Thread bob = new Thread(() -> {
            leaderboard.put(600, "bob-run1");
            leaderboard.put(890, "bob-run2");
            leaderboard.put(500, "bob-run3");
        });

        alice.start(); bob.start();
        alice.join(); bob.join();

        System.out.println("Leaderboard size: " + leaderboard.size());
        System.out.println("Sorted (ascending) iteration works without any external locking:");
        for (var entry : leaderboard.entrySet()) {
            System.out.println("  " + entry.getKey() + " -> " + entry.getValue());
        }
    }
}
```

**How to run:** `java LeaderboardBasic.java`

Two threads insert scores concurrently with no external synchronization at all, and the final iteration is correctly sorted by key regardless of the interleaving between `alice` and `bob`'s insertions — `ConcurrentSkipListMap` handles all the necessary coordination internally.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class LeaderboardConcurrentIteration {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentSkipListMap<Integer, String> leaderboard = new ConcurrentSkipListMap<>();
        leaderboard.put(100, "existing-1");
        leaderboard.put(200, "existing-2");
        leaderboard.put(300, "existing-3");

        CountDownLatch iterationStarted = new CountDownLatch(1);
        CountDownLatch insertDone = new CountDownLatch(1);

        Thread iterator = new Thread(() -> {
            int count = 0;
            for (var entry : leaderboard.entrySet()) {
                count++;
                if (count == 1) {
                    iterationStarted.countDown();
                    try { insertDone.await(); } catch (InterruptedException ignored) { }
                }
            }
            System.out.println("Iteration completed without ConcurrentModificationException. Entries visited: " + count);
        });

        Thread inserter = new Thread(() -> {
            try { iterationStarted.await(); } catch (InterruptedException ignored) { }
            leaderboard.put(150, "inserted-during-iteration"); // modifies the map WHILE the other thread iterates
            insertDone.countDown();
        });

        iterator.start();
        inserter.start();
        iterator.join();
        inserter.join();

        System.out.println("Final map: " + leaderboard);
    }
}
```

**How to run:** `java LeaderboardConcurrentIteration.java`

The `iterator` thread deliberately pauses after visiting its first entry, giving `inserter` a chance to modify the map **mid-iteration** — on a plain `TreeMap`, this would throw `ConcurrentModificationException`. On `ConcurrentSkipListMap`, the iteration completes cleanly with no exception; it simply doesn't see the entry inserted after the iteration had already begun (a "weakly consistent" view), even though the map's final state correctly includes it.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class LeaderboardTopN {
    public static void main(String[] args) throws Exception {
        ConcurrentSkipListMap<Integer, String> leaderboard = new ConcurrentSkipListMap<>();
        leaderboard.put(100, "p1");
        leaderboard.put(200, "p2");
        leaderboard.put(300, "p3");
        leaderboard.put(400, "p4");
        leaderboard.put(500, "p5"); // p5 (500) and p4 (400) are currently the top 2

        CountDownLatch readerStarted = new CountDownLatch(1);

        // A concurrent writer inserting a LOW score -- it must never affect the top-2 result,
        // and (the real point of this example) must never throw or corrupt the reader's iteration.
        Thread writer = new Thread(() -> {
            try { readerStarted.await(); } catch (InterruptedException ignored) { }
            leaderboard.put(50, "late-joiner"); // concurrent structural modification, mid-iteration
        });

        Thread reader = new Thread(() -> {
            NavigableMap<Integer, String> highestFirst = leaderboard.descendingMap();
            Map<Integer, String> topTwo = new LinkedHashMap<>();
            int taken = 0;
            for (var entry : highestFirst.entrySet()) {
                readerStarted.countDown(); // let the writer proceed once iteration has begun
                if (taken++ == 2) break;
                topTwo.put(entry.getKey(), entry.getValue());
            }
            System.out.println("Top 2 (unaffected by the concurrent low-score insert): " + topTwo);
        });

        reader.start();
        writer.start();
        reader.join();
        writer.join();

        System.out.println("Final leaderboard (the concurrent insert DID land, safely): " + leaderboard);
    }
}
```

**How to run:** `java LeaderboardTopN.java`

`leaderboard.descendingMap()` (from `NavigableMap`) is used to query the top 2 scores while another thread concurrently inserts a new, lower entry — the top-2 result is correctly unaffected (since 50 doesn't belong in the top 2 regardless of timing), and the concurrent insert lands safely in the underlying map without disrupting the read in progress.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `leaderboard` starts with five entries, keyed by score: 100, 200, 300, 400, 500 (mapped to `p1` through `p5`). `readerStarted` is a `CountDownLatch` with count 1.

`reader` and `writer` both start. Inside `reader`, `leaderboard.descendingMap()` creates a reverse-order view (highest score first). The `for` loop begins iterating: on its very first entry (500, `"p5"`), it calls `readerStarted.countDown()` — this signals `writer`, which has been blocked in `readerStarted.await()`, to proceed. `taken++ == 2` is `false` on this first entry (`taken` was `0`, now becomes `1`), so `topTwo.put(500, "p5")` runs.

Meanwhile, once signalled, `writer` calls `leaderboard.put(50, "late-joiner")` — this structurally modifies the underlying skip list *while* `reader`'s iteration is still in progress. Because `ConcurrentSkipListMap`'s iterators are weakly consistent, this concurrent modification does **not** throw any exception in `reader`'s loop.

Back in `reader`'s loop, the second entry (400, `"p4"`) is visited: `readerStarted.countDown()` is called again (harmless — a `CountDownLatch` that's already at zero simply does nothing further), `taken++ == 2` is still `false` (`taken` goes from `1` to `2`), so `topTwo.put(400, "p4")` runs. On the third entry, `taken++ == 2` is now `true` (checked when `taken` is `2`, before incrementing to `3`), so the loop `break`s — `50` (inserted by `writer`, and in any case far too low to matter for a top-2 result) is never even reached in the descending traversal at this point, since it hasn't necessarily been observed yet, and wouldn't qualify anyway.

`reader` prints `topTwo`, which contains exactly `{500=p5, 400=p4}` — correct and unaffected by the concurrent insert. Both threads then `join()`, and `main` prints the final `leaderboard`, which **does** include the `50 -> "late-joiner"` entry the writer inserted, sorted correctly into its proper position.

Expected output:
```
Top 2 (unaffected by the concurrent low-score insert): {500=p5, 400=p4}
Final leaderboard (the concurrent insert DID land, safely): {50=late-joiner, 100=p1, 200=p2, 300=p3, 400=p4, 500=p5}
```

## 7. Gotchas & takeaways

> "Weakly consistent" does **not** mean "eventually consistent" or "safe to treat as a point-in-time snapshot." A weakly-consistent iterator over `ConcurrentSkipListMap`/`Set` is guaranteed to never throw `ConcurrentModificationException` and to reflect *some* valid state of the collection, but it might see some, all, or none of the changes made by other threads during its traversal. If you need a true frozen snapshot for a calculation, copy the data first (e.g. `new TreeMap<>(concurrentSkipListMap)`) rather than relying on iteration order guarantees mid-traversal.

- `ConcurrentSkipListMap`/`Set` are the thread-safe equivalents of `TreeMap`/`TreeSet`, implementing the full `NavigableMap`/`NavigableSet` API with no external synchronization required.
- Internally backed by a skip list (a layered, probabilistic linked structure) rather than a red-black tree, since skip lists support lock-free concurrent modification more naturally.
- Their iterators are weakly consistent: safe under concurrent modification (never throw), but not guaranteed to reflect every change made during the traversal.
- Reach for these whenever you need sorted, "closest match" (`floor`/`ceiling`/etc.) behavior *and* genuine multi-thread sharing — plain `TreeMap`/`TreeSet` cannot safely handle the latter.
- All the `NavigableMap`/`NavigableSet` methods covered in the previous two tutorials (`floorKey`, `descendingMap`, `subSet`, `pollFirstEntry`, etc.) work identically here, just with added thread safety.
