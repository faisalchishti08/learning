---
card: java
gi: 564
slug: stampedlock
title: StampedLock
---

## 1. What it is

`StampedLock` (`java.util.concurrent.locks`) is a Java 8 lock that adds a third mode — **optimistic reading** — alongside the usual exclusive write lock and shared read lock. Every lock/unlock operation returns or consumes a `long` **stamp**, which is both a lock token and, for optimistic reads, a version number you can check to see if a write happened while you were reading.

## 2. Why & when

`ReentrantReadWriteLock` lets many readers run concurrently but blocks all of them while a writer holds the lock — fine, but under heavy read contention, readers still pay the cost of acquiring and releasing an actual lock (atomic operations, potential thread suspension). `StampedLock`'s optimistic read mode skips that cost entirely: you read data *without* taking any lock at all, then afterward check a stamp to see whether a writer interfered. If nothing changed, you're done — no lock was ever acquired. If a writer did interfere, you fall back to a real (pessimistic) read lock and retry. This trades a small chance of wasted work (re-reading) for much higher throughput under mostly-read, occasionally-write workloads — the classic profile of caches and configuration objects.

## 3. Core concept

```java
StampedLock lock = new StampedLock();

// Optimistic read — no actual locking happens.
long stamp = lock.tryOptimisticRead();
double x = point.x, y = point.y; // read fields without a lock
if (!lock.validate(stamp)) {
    // a write happened concurrently — fall back to a real read lock
    stamp = lock.readLock();
    try { x = point.x; y = point.y; }
    finally { lock.unlockRead(stamp); }
}
```

`tryOptimisticRead()` returns a stamp immediately, without blocking anyone. `validate(stamp)` checks whether a write lock was acquired (and released) since that stamp was issued — if it returns `false`, the data you just read might be inconsistent, and you must re-read under a real lock.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optimistic read: read without locking, then validate; only fall back to a real lock if invalidated">
  <rect x="10" y="10" width="280" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">tryOptimisticRead() -&gt; stamp</text>

  <rect x="10" y="60" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">read fields (NO lock held)</text>

  <rect x="10" y="110" width="280" height="40" rx="6" fill="#1c2430" stroke="#d2a8ff"/>
  <text x="150" y="135" fill="#d2a8ff" font-size="11" text-anchor="middle" font-family="monospace">validate(stamp)?</text>

  <line x1="290" y1="130" x2="380" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#s1)"/>
  <text x="400" y="70" fill="#8b949e" font-size="10" font-family="sans-serif">valid -&gt; done, no lock ever taken</text>

  <line x1="290" y1="130" x2="380" y2="170" stroke="#f85149" stroke-width="1.5" marker-end="url(#s2)"/>
  <text x="400" y="185" fill="#f85149" font-size="10" font-family="sans-serif">invalid -&gt; fall back to readLock() and retry</text>

  <defs>
    <marker id="s1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="s2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The common case (no concurrent write) pays for a read with zero locking overhead; the rare case (a write did interfere) falls back to a correctness-guaranteeing real lock.

## 5. Runnable example

Scenario: a shared 2D `Point` that many threads read concurrently while occasionally being moved by a writer thread — starting with basic exclusive read/write locking, then adding optimistic reads with fallback, then building a small benchmark comparing optimistic vs. pessimistic read throughput under concurrent load.

### Level 1 — Basic

```java
import java.util.concurrent.locks.StampedLock;

public class StampedLockBasic {
    static class Point {
        private double x, y;
        private final StampedLock lock = new StampedLock();

        void move(double deltaX, double deltaY) {
            long stamp = lock.writeLock();
            try {
                x += deltaX;
                y += deltaY;
            } finally {
                lock.unlockWrite(stamp);
            }
        }

        double distanceFromOrigin() {
            long stamp = lock.readLock();
            try {
                return Math.sqrt(x * x + y * y);
            } finally {
                lock.unlockRead(stamp);
            }
        }
    }

    public static void main(String[] args) {
        Point point = new Point();
        point.move(3, 4);
        System.out.println("Distance: " + point.distanceFromOrigin());
    }
}
```

**How to run:** `java StampedLockBasic.java`

Expected output:
```
Distance: 5.0
```

`lock.writeLock()` blocks until exclusive access is granted and returns a stamp identifying that specific lock acquisition; `lock.unlockWrite(stamp)` releases it, and the stamp must match — this is a plain, correctness-first exclusive lock, functionally similar to `ReentrantLock`. `lock.readLock()`/`unlockRead(stamp)` work the same way but allow multiple concurrent readers, blocked only by an active writer — this level uses `StampedLock` exactly like a `ReadWriteLock`, without yet using its distinguishing optimistic-read feature.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.StampedLock;

public class StampedLockOptimistic {
    static class Point {
        private double x, y;
        private final StampedLock lock = new StampedLock();

        void move(double deltaX, double deltaY) {
            long stamp = lock.writeLock();
            try {
                x += deltaX;
                y += deltaY;
            } finally {
                lock.unlockWrite(stamp);
            }
        }

        double distanceFromOrigin() {
            long stamp = lock.tryOptimisticRead(); // no lock taken yet
            double currentX = x, currentY = y;

            if (!lock.validate(stamp)) {
                // A write happened between the read and the validate — fall back to a real lock.
                stamp = lock.readLock();
                try {
                    currentX = x;
                    currentY = y;
                } finally {
                    lock.unlockRead(stamp);
                }
            }
            return Math.sqrt(currentX * currentX + currentY * currentY);
        }
    }

    public static void main(String[] args) {
        Point point = new Point();
        point.move(3, 4);
        System.out.println("Distance: " + point.distanceFromOrigin());
        point.move(1, 0); // move to (4, 4)
        System.out.println("Distance: " + point.distanceFromOrigin());
    }
}
```

**How to run:** `java StampedLockOptimistic.java`

Expected output:
```
Distance: 5.0
Distance: 5.656854249492381
```

The real-world concern this adds: **avoiding lock overhead on the read path entirely in the uncontended case.** `tryOptimisticRead()` returns a stamp without blocking or taking any actual lock — `x` and `y` are read speculatively. `lock.validate(stamp)` then checks whether any write lock was acquired and released since that stamp was issued; in this single-threaded example there's never a concurrent writer, so `validate` always succeeds and the fallback `readLock()` branch never executes — the whole read happens with zero lock acquisition cost.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.StampedLock;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.CountDownLatch;

public class StampedLockConcurrent {
    static class Point {
        private double x, y;
        private final StampedLock lock = new StampedLock();
        private final AtomicInteger optimisticSuccesses = new AtomicInteger();
        private final AtomicInteger optimisticFailures = new AtomicInteger();

        void move(double deltaX, double deltaY) {
            long stamp = lock.writeLock();
            try {
                x += deltaX;
                y += deltaY;
            } finally {
                lock.unlockWrite(stamp);
            }
        }

        double distanceFromOrigin() {
            long stamp = lock.tryOptimisticRead();
            double currentX = x, currentY = y;

            if (!lock.validate(stamp)) {
                optimisticFailures.incrementAndGet();
                stamp = lock.readLock();
                try {
                    currentX = x;
                    currentY = y;
                } finally {
                    lock.unlockRead(stamp);
                }
            } else {
                optimisticSuccesses.incrementAndGet();
            }
            return Math.sqrt(currentX * currentX + currentY * currentY);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Point point = new Point();
        int readerCount = 4;
        int readsPerThread = 50_000;
        CountDownLatch done = new CountDownLatch(readerCount + 1);

        // Reader threads: hammer distanceFromOrigin() using optimistic reads.
        for (int i = 0; i < readerCount; i++) {
            new Thread(() -> {
                for (int r = 0; r < readsPerThread; r++) point.distanceFromOrigin();
                done.countDown();
            }).start();
        }

        // Writer thread: moves the point periodically while readers are active.
        new Thread(() -> {
            for (int w = 0; w < 200; w++) {
                point.move(0.001, 0.001);
            }
            done.countDown();
        }).start();

        done.await();
        int successes = point.optimisticSuccesses.get();
        int failures = point.optimisticFailures.get();
        System.out.println("Optimistic reads that needed no fallback: " + (successes > 0));
        System.out.println("Total reads observed: " + (successes + failures == readerCount * readsPerThread));
    }
}
```

**How to run:** `java StampedLockConcurrent.java`

Expected output:
```
Optimistic reads that needed no fallback: true
Total reads observed: true
```

This handles the production-flavoured case of **genuine concurrent access**: four reader threads calling `distanceFromOrigin()` 50,000 times each while a writer thread concurrently calls `move(...)` 200 times. Because writes are relatively rare compared to reads, the vast majority of `tryOptimisticRead()` calls succeed without ever falling back to `readLock()` — `optimisticSuccesses` ends up far larger than `optimisticFailures`, demonstrating the throughput advantage `StampedLock` offers over a plain `ReadWriteLock` under a read-heavy workload.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four reader threads and one writer thread are started, all sharing a single `Point` instance and its `StampedLock`.

Each reader thread loops 50,000 times calling `point.distanceFromOrigin()`. Inside, `lock.tryOptimisticRead()` returns a stamp representing "the lock's current version, with no actual lock acquired" — this call never blocks, regardless of what other threads are doing. `currentX` and `currentY` are then read directly from the (potentially concurrently-modified) fields.

```
Reader thread:                          Writer thread (concurrently):
stamp = tryOptimisticRead()             writeLock() -> acquires exclusive access
currentX = x; currentY = y  <---------- x += 0.001; y += 0.001   (fields change mid-read!)
validate(stamp)                         unlockWrite(stamp)
  -> if a write completed during        
     the read window, validate()        
     returns false
```

`lock.validate(stamp)` checks whether any writer acquired and released the write lock since `stamp` was issued. If a writer's `move(...)` call happened to overlap with a reader's field reads, `validate` returns `false`; the reader then falls back to `lock.readLock()`, which blocks (if necessary) until any in-progress write finishes, and re-reads `x`/`y` under that genuine lock — guaranteeing a consistent pair of values this time. `optimisticFailures` is incremented in that branch. If no overlapping write occurred, `validate` returns `true`, the speculative read is trusted as-is, and `optimisticSuccesses` is incremented — no lock was ever taken for that read.

The writer thread runs 200 `move(...)` calls, each acquiring the exclusive write lock briefly, mutating `x` and `y`, then releasing it. Because 200 writes are vastly outnumbered by `4 * 50,000 = 200,000` total reads, the overwhelming majority of optimistic reads complete before a concurrent write can invalidate them.

After `done.await()` returns (all five threads finished), `main` checks two invariants: `successes > 0` confirms that at least some reads took the fast, lock-free optimistic path (expected to be nearly all of them, though the exact count is nondeterministic and thus not asserted precisely), and `successes + failures == readerCount * readsPerThread` confirms every single read was accounted for by exactly one of the two counters — no read was silently lost or double-counted.

## 7. Gotchas & takeaways

> Inside an optimistic-read block, you must **not** perform any action that can't be safely undone or that has externally visible side effects (printing to a log with values you haven't validated yet, throwing based on a not-yet-validated invariant, etc.) — the values read may be torn or inconsistent until `validate(stamp)` confirms them. Only read plain fields into local variables, validate, and *then* act on the validated values (or fall back and re-read).

- `StampedLock` is **not reentrant** — unlike `ReentrantLock` or `ReentrantReadWriteLock`, a thread that already holds the write lock and tries to acquire it again (even indirectly) will deadlock against itself.
- Stamps are just `long` values; passing the wrong stamp to `unlockWrite`/`unlockRead` (e.g., from a different acquisition) is a programming error the lock does not fully guard against — always store and use the exact stamp returned by the matching lock call.
- `tryOptimisticRead()` can return `0` in rare internal states — the API contract is that you must still call `validate(0)`, which will correctly return `false`, triggering the same fallback path.
- `StampedLock` also supports lock **conversion** (`tryConvertToWriteLock`, etc.) for upgrading a read stamp to a write stamp without fully releasing and reacquiring — an advanced feature useful for read-modify-write sequences.
- Use `StampedLock` when reads vastly outnumber writes and read code can be structured as "read into locals, then validate"; for read-heavy code that can't easily be restructured that way (e.g., reads that must call out to other locking code), a plain `ReentrantReadWriteLock` is simpler and still safe.
