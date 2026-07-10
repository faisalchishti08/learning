---
card: java
gi: 868
slug: readwritelock
title: ReadWriteLock
---

## 1. What it is

`java.util.concurrent.locks.ReadWriteLock` (typically implemented via `ReentrantReadWriteLock`) splits locking into two separate locks that cooperate: a **read lock** that can be held by any number of threads *simultaneously*, as long as no thread holds the write lock, and a **write lock** that is exclusive — only one thread can hold it, and no reader can hold the read lock at the same time. This is a direct improvement over a plain mutual-exclusion lock for workloads where reads vastly outnumber writes: readers no longer block each other, only writers block everyone.

## 2. Why & when

A plain `synchronized` block or `ReentrantLock` treats every access — read or write — as needing exclusive access, which is wasteful when the actual data races only matter for writes: two threads simultaneously *reading* an unchanging value can never corrupt anything, so there's no correctness reason to serialize them. Use `ReadWriteLock` for shared, mutable data structures that are read far more often than they're written — a configuration cache refreshed occasionally but read constantly, an in-memory index, a shared lookup table. It is the wrong tool when writes are frequent or roughly as common as reads, since the extra bookkeeping `ReadWriteLock` needs (tracking multiple simultaneous readers, and handling the readers-to-writer transition) can actually make it slower than a plain lock under write-heavy or balanced workloads.

## 3. Core concept

```java
ReadWriteLock rwLock = new ReentrantReadWriteLock();
Lock readLock = rwLock.readLock();
Lock writeLock = rwLock.writeLock();

// Any number of threads can hold readLock at once:
readLock.lock();
try { /* read shared data */ } finally { readLock.unlock(); }

// Only one thread can hold writeLock, and no reader can hold readLock meanwhile:
writeLock.lock();
try { /* mutate shared data */ } finally { writeLock.unlock(); }
```

The two `Lock` objects returned by `readLock()` and `writeLock()` are two views onto the *same* underlying `ReentrantReadWriteLock` — they coordinate with each other even though they're called separately.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple reader threads holding the read lock simultaneously, then a writer thread waiting for all readers to finish before acquiring the exclusive write lock">
  <rect x="20" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="43" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Reader 1 -- read lock</text>
  <rect x="20" y="65" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Reader 2 -- read lock</text>
  <rect x="20" y="110" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="133" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Reader 3 -- read lock</text>
  <text x="110" y="10" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">all three run CONCURRENTLY</text>

  <rect x="330" y="65" width="280" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Writer -- WAITS for all readers to release</text>

  <line x1="200" y1="80" x2="325" y2="80" stroke="#8b949e" stroke-width="2" stroke-dasharray="4"/>

  <rect x="330" y="140" width="280" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="163" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Writer -- EXCLUSIVE write lock, no readers allowed</text>
  <line x1="470" y1="100" x2="470" y2="138" stroke="#6db33f" stroke-width="2" marker-end="url(#a6)"/>
  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

*Readers never block each other; a writer must wait for every current reader to finish, and blocks all future readers until it's done.*

## 5. Runnable example

Scenario: a shared, occasionally-updated in-memory price cache, growing from a plain-lock version that unnecessarily serializes all reads, to a `ReadWriteLock` version letting concurrent reads through, to a version demonstrating and avoiding the classic read-lock-upgrade deadlock.

### Level 1 — Basic

```java
import java.util.concurrent.locks.*;
import java.util.*;

public class PlainLockCache {
    private final Lock lock = new ReentrantLock(); // one lock for everything -- reads block each other too
    private final Map<String, Double> prices = new HashMap<>();

    double getPrice(String symbol) {
        lock.lock();
        try {
            return prices.getOrDefault(symbol, 0.0);
        } finally {
            lock.unlock();
        }
    }

    void setPrice(String symbol, double price) {
        lock.lock();
        try {
            prices.put(symbol, price);
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) {
        PlainLockCache cache = new PlainLockCache();
        cache.setPrice("AAPL", 190.50);
        System.out.println("AAPL = " + cache.getPrice("AAPL"));
    }
}
```

**How to run:** `java PlainLockCache.java` (JDK 17+).

Expected output:
```
AAPL = 190.5
```

Correct, but every `getPrice` call — even though reads never conflict with each other — is serialized against every other read *and* every write by the single `Lock`, wasting parallelism in a read-heavy workload.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;
import java.util.*;

public class ReadWriteLockCache {
    private final ReadWriteLock rwLock = new ReentrantReadWriteLock();
    private final Lock readLock = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();
    private final Map<String, Double> prices = new HashMap<>();

    double getPrice(String symbol) {
        readLock.lock(); // multiple threads can hold this concurrently
        try {
            return prices.getOrDefault(symbol, 0.0);
        } finally {
            readLock.unlock();
        }
    }

    void setPrice(String symbol, double price) {
        writeLock.lock(); // exclusive -- blocks all readers and other writers
        try {
            prices.put(symbol, price);
        } finally {
            writeLock.unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ReadWriteLockCache cache = new ReadWriteLockCache();
        cache.setPrice("AAPL", 190.50);

        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 8; i++) {
            pool.submit(() -> {
                for (int j = 0; j < 100_000; j++) cache.getPrice("AAPL"); // pure reads, run concurrently
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        System.out.println("8 threads x 100000 concurrent reads completed, final price = " + cache.getPrice("AAPL"));
    }
}
```

**How to run:** `java ReadWriteLockCache.java`.

Expected output:
```
8 threads x 100000 concurrent reads completed, final price = 190.5
```

The real-world concern added: eight threads hammering `getPrice` concurrently now genuinely run their reads in parallel with each other (only blocking against a concurrent writer, of which there are none here), rather than needlessly queuing up behind a single exclusive lock as in Level 1 — throughput for read-heavy workloads improves accordingly.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.*;

public class ReadWriteLockUpgradeSafely {
    private final ReadWriteLock rwLock = new ReentrantReadWriteLock();
    private final Lock readLock = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();
    private final Map<String, Double> prices = new HashMap<>();

    // WRONG pattern (commented out): holding the read lock and then calling writeLock.lock()
    // deadlocks, because ReentrantReadWriteLock does not support upgrading read -> write directly --
    // the write lock cannot be acquired while ANY thread (including this one) still holds the read lock.
    //
    // void brokenUpdateIfAbsent(String symbol, double fallback) {
    //     readLock.lock();
    //     try {
    //         if (!prices.containsKey(symbol)) {
    //             writeLock.lock(); // DEADLOCK: this thread still holds readLock
    //             ...
    //         }
    //     } finally { readLock.unlock(); }
    // }

    // CORRECT pattern: release the read lock BEFORE acquiring the write lock,
    // then re-check the condition after acquiring the write lock (another thread
    // may have changed things in between -- this is the standard "check-then-act" fix).
    void updateIfAbsent(String symbol, double fallback) {
        readLock.lock();
        boolean present;
        try {
            present = prices.containsKey(symbol);
        } finally {
            readLock.unlock(); // MUST release read lock before trying to acquire write lock
        }
        if (!present) {
            writeLock.lock();
            try {
                prices.putIfAbsent(symbol, fallback); // re-check: another writer may have won the race
            } finally {
                writeLock.unlock();
            }
        }
    }

    double getPrice(String symbol) {
        readLock.lock();
        try { return prices.getOrDefault(symbol, 0.0); }
        finally { readLock.unlock(); }
    }

    public static void main(String[] args) {
        ReadWriteLockUpgradeSafely cache = new ReadWriteLockUpgradeSafely();
        cache.updateIfAbsent("GOOG", 140.00);
        cache.updateIfAbsent("GOOG", 999.00); // should NOT overwrite -- already present
        System.out.println("GOOG = " + cache.getPrice("GOOG") + " (expected 140.0, not overwritten)");
    }
}
```

**How to run:** `java ReadWriteLockUpgradeSafely.java`.

Expected output:
```
GOOG = 140.0 (expected 140.0, not overwritten)
```

This adds the production-flavored hard case: `ReentrantReadWriteLock` does **not** support upgrading a held read lock directly into the write lock — attempting to acquire `writeLock` while still holding `readLock` deadlocks, since the write lock cannot be granted while any reader (including the requester itself) still holds the read lock. The correct pattern releases the read lock first, then acquires the write lock and **re-checks** the condition (`putIfAbsent` rather than a blind `put`), since another thread could have changed the data during the brief window between releasing the read lock and acquiring the write lock.

## 6. Walkthrough

Tracing `ReadWriteLockUpgradeSafely.main`:

1. `cache.updateIfAbsent("GOOG", 140.00)` acquires `readLock`, checks `prices.containsKey("GOOG")` — `false`, since the map is empty — then releases `readLock` in the `finally` block, *before* touching the write lock.
2. Because `present` was `false`, it acquires `writeLock` (now uncontended, since the read lock was already released) and calls `prices.putIfAbsent("GOOG", 140.00)`, which inserts the value since the key is still absent, then releases `writeLock`.
3. `cache.updateIfAbsent("GOOG", 999.00)` runs the same sequence: acquires `readLock`, finds `containsKey("GOOG")` is now `true` (from step 2), releases `readLock`, and — because `present` was `true` — **skips** acquiring the write lock entirely, leaving the existing value untouched.
4. Even in the case where `present` had been `false` for both calls (e.g., if two threads called `updateIfAbsent` concurrently on a fresh key), the re-check inside the write lock via `putIfAbsent` (not a blind `put`) ensures whichever thread acquires the write lock second simply finds the key already there and does nothing — no lost update, no overwrite, despite the read-then-write not being a single atomic operation.
5. `cache.getPrice("GOOG")` acquires `readLock`, reads `140.0`, releases `readLock`, and the final `println` confirms the second `updateIfAbsent` call correctly left the original value in place.

## 7. Gotchas & takeaways

> **Gotcha:** `ReentrantReadWriteLock` does not support upgrading a read lock to a write lock while holding it — doing so deadlocks, because the write lock can never be granted while any reader (including the very thread attempting the upgrade) still holds the read lock. Always release the read lock first, then acquire the write lock and re-check whatever condition you originally read, since the data may have changed in between.

- Readers never block other readers; only a writer blocks everyone (readers and other writers) and is blocked by any existing reader or writer.
- `ReadWriteLock` pays off specifically for read-heavy, write-light workloads — measure before assuming it beats a plain `ReentrantLock` for balanced or write-heavy access patterns.
- Downgrading (holding the write lock and then acquiring the read lock before releasing the write lock) **is** supported by `ReentrantReadWriteLock` and is a common, safe pattern; upgrading (read → write) is not.
- Always re-check any condition read under the read lock after acquiring the write lock — the world can change in the gap between releasing one lock and acquiring the other.
- For an alternative that avoids locking entirely for reads under specific access patterns, see [`StampedLock`'s optimistic reads](0869-stampedlock-optimistic-reads.md), which can outperform `ReadWriteLock` further at the cost of a more careful usage pattern.
