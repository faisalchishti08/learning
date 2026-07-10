---
card: java
gi: 869
slug: stampedlock-optimistic-reads
title: StampedLock (optimistic reads)
---

## 1. What it is

`java.util.concurrent.locks.StampedLock` is a lock (added in Java 8) with three modes: exclusive write, non-exclusive (blocking) read — much like `ReadWriteLock` — and a third, distinctive mode called **optimistic reading**, which takes no lock at all. `tryOptimisticRead()` returns a `long` **stamp** immediately, without blocking any writer. The reader then does its work and afterward calls `validate(stamp)` to check whether any write occurred in the meantime; if a write did happen, the stamp is invalid, and the reader must fall back to a real, blocking read. When optimistic validation succeeds (the common case, since writes are rare), the entire read happened with zero locking overhead.

## 2. Why & when

`ReadWriteLock` already lets readers run concurrently with each other, but every reader still has to do the bookkeeping of acquiring and releasing an actual lock object — atomic increments/decrements of a reader count, visible to other threads. `StampedLock`'s optimistic mode skips that entirely for the extremely-read-heavy case: since writes are rare, most reads can simply proceed against the data, then cheaply check afterward "did nobody change this while I was looking?" This makes it faster than `ReadWriteLock` under very read-heavy contention. The cost is complexity and a sharp restriction: the code executed between `tryOptimisticRead()` and `validate()` must not have any externally visible side effects and must not throw based on inconsistent data it might be reading mid-write, since it could be operating on a state that's actively being mutated by a concurrent writer. Use it for hot, simple numeric or reference reads (e.g., reading a pair of `x`/`y` coordinates) where retry-on-failure is cheap and side-effect-free; avoid it for anything complex, where a torn read could cause the read logic itself to misbehave (like an array index out of bounds) before validation even gets a chance to catch it.

## 3. Core concept

```java
StampedLock sl = new StampedLock();

long stamp = sl.tryOptimisticRead();  // no lock acquired -- immediate, non-blocking
int localX = x, localY = y;           // read shared fields WITHOUT holding any lock
if (!sl.validate(stamp)) {            // did a writer sneak in between the read and here?
    stamp = sl.readLock();            // fall back to a real, blocking read lock
    try {
        localX = x;
        localY = y;
    } finally {
        sl.unlockRead(stamp);
    }
}
// localX, localY are now guaranteed consistent
```

The optimistic path costs almost nothing when there's no writer contention — no CAS, no memory barrier for acquiring a "lock" — but it demands a fallback path for the rare case a write really did race with the read.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optimistic read takes a stamp with no locking, reads data, then validates the stamp; if a writer intervened, it falls back to a real read lock and retries">
  <rect x="20" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">tryOptimisticRead() -- get stamp, NO lock</text>

  <rect x="270" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">read fields locally</text>

  <rect x="480" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">validate(stamp)</text>

  <line x1="240" y1="40" x2="265" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a7)"/>
  <line x1="450" y1="40" x2="475" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a7)"/>

  <rect x="380" y="100" width="220" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="490" y="125" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">invalid -&gt; fall back to readLock(), retry</text>
  <line x1="550" y1="60" x2="490" y2="98" stroke="#f0883e" stroke-width="2" marker-end="url(#a7)"/>

  <rect x="40" y="100" width="220" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="125" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">valid -&gt; use the data, done, zero locking cost</text>
  <line x1="550" y1="60" x2="200" y2="98" stroke="#6db33f" stroke-width="2" marker-end="url(#a7)"/>

  <defs><marker id="a7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The common case (no concurrent writer) is nearly free; the rare case (a writer intervened) falls back to a genuine blocking read.*

## 5. Runnable example

Scenario: a mutable 2D point shared between a fast-moving writer thread and many reader threads, growing from a `ReadWriteLock` baseline, to the optimistic-read fast path, to a version that correctly handles a *torn read* by validating before trusting the values at all.

### Level 1 — Basic

```java
import java.util.concurrent.locks.*;

public class ReadWriteLockPoint {
    private final ReadWriteLock rw = new ReentrantReadWriteLock();
    private double x = 0, y = 0;

    void move(double dx, double dy) {
        rw.writeLock().lock();
        try { x += dx; y += dy; } finally { rw.writeLock().unlock(); }
    }

    double distanceFromOrigin() {
        rw.readLock().lock();
        try { return Math.sqrt(x * x + y * y); } finally { rw.readLock().unlock(); }
    }

    public static void main(String[] args) {
        ReadWriteLockPoint p = new ReadWriteLockPoint();
        p.move(3, 4);
        System.out.println("distance = " + p.distanceFromOrigin());
    }
}
```

**How to run:** `java ReadWriteLockPoint.java` (JDK 17+).

Expected output:
```
distance = 5.0
```

Correct and reasonably fast, but every single read still pays the cost of acquiring and releasing an actual read-lock object, even though writes here are comparatively rare.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;

public class StampedLockOptimisticPoint {
    private final StampedLock sl = new StampedLock();
    private double x = 0, y = 0;

    void move(double dx, double dy) {
        long stamp = sl.writeLock();
        try { x += dx; y += dy; } finally { sl.unlockWrite(stamp); }
    }

    double distanceFromOrigin() {
        long stamp = sl.tryOptimisticRead(); // no lock taken
        double curX = x, curY = y;           // speculative read
        if (!sl.validate(stamp)) {           // did a writer intervene?
            stamp = sl.readLock();           // fall back to a real read lock
            try {
                curX = x;
                curY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(curX * curX + curY * curY);
    }

    public static void main(String[] args) {
        StampedLockOptimisticPoint p = new StampedLockOptimisticPoint();
        p.move(3, 4);
        System.out.println("distance = " + p.distanceFromOrigin() + " (computed via the optimistic fast path)");
    }
}
```

**How to run:** `java StampedLockOptimisticPoint.java`.

Expected output:
```
distance = 5.0 (computed via the optimistic fast path)
```

The real-world concern added: `distanceFromOrigin()` now takes no lock at all in the common, uncontended case — `tryOptimisticRead()` returns a stamp instantly, the fields are read speculatively, and `validate()` confirms no writer touched `x`/`y` in between, all without ever calling an actual lock/unlock pair.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;

public class StampedLockUnderContention {
    private final StampedLock sl = new StampedLock();
    private double x = 0, y = 0;

    void move(double dx, double dy) {
        long stamp = sl.writeLock();
        try {
            x += dx;
            try { Thread.sleep(1); } catch (InterruptedException ignored) {} // widen the race window
            y += dy;
        } finally {
            sl.unlockWrite(stamp);
        }
    }

    double distanceFromOrigin() {
        long stamp = sl.tryOptimisticRead();
        double curX = x, curY = y; // could be a TORN read: x from after a move, y from before it
        if (!sl.validate(stamp)) {
            // optimistic read was invalidated by a concurrent writer -- fall back and retry for real
            stamp = sl.readLock();
            try {
                curX = x;
                curY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(curX * curX + curY * curY);
    }

    public static void main(String[] args) throws InterruptedException {
        StampedLockUnderContention p = new StampedLockUnderContention();
        ExecutorService pool = Executors.newFixedThreadPool(2);

        pool.submit(() -> { for (int i = 0; i < 5; i++) p.move(3, 4); }); // writer, moves (3,4) repeatedly
        Future<?> readerTask = pool.submit(() -> {
            for (int i = 0; i < 5; i++) {
                double d = p.distanceFromOrigin();
                // every result must be a valid distance for SOME consistent (x,y) pair the writer produced,
                // never a torn combination -- validate() guarantees this, even under a widened race window
                System.out.println("distance sample: " + d);
            }
        });

        readerTask.get();
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("final distance = " + p.distanceFromOrigin());
    }
}
```

**How to run:** `java StampedLockUnderContention.java`.

Expected output shape (exact intermediate samples vary, but every one is a value `validate()` confirmed consistent, and the final is always exact):
```
distance sample: 5.0
distance sample: 10.0
distance sample: 15.0
distance sample: 20.0
distance sample: 25.0
final distance = 25.0
```

This adds the production-flavored hard case: an artificially widened race window (`Thread.sleep(1)` between updating `x` and `y`) makes a torn read — reading the *new* `x` but the *old* `y` — much more likely to actually occur during the test. `validate(stamp)` catches exactly this: if the writer's `unlockWrite` happened between the optimistic read of `x` and `y`, the stamp is invalidated, and the code falls back to a real `readLock()` to get a guaranteed-consistent pair — so every printed sample is always a value that corresponds to some real, complete state the point actually had, never a mismatched torn combination.

## 6. Walkthrough

Tracing one call to `distanceFromOrigin()` racing against a concurrent `move(3, 4)`:

1. `sl.tryOptimisticRead()` returns a stamp representing the lock's current version — no actual lock is acquired, so this never blocks, even if a writer is mid-update.
2. `curX = x; curY = y;` reads both fields directly and speculatively. If the writer's `move` call happens to be between its `x += dx` and `y += dy` lines at this exact moment, `curX` reflects the *new* `x` while `curY` still reflects the *old* `y` — a torn, logically inconsistent pair.
3. `sl.validate(stamp)` checks whether any write lock was acquired (and released) since the stamp was taken. If the writer's `move` call did overlap with the read window, validation fails (`false`).
4. On failure, the code falls back to `sl.readLock()` — a genuine, blocking read lock that cannot be held concurrently with the writer's exclusive write lock — and re-reads `x` and `y`, this time guaranteed to see one single, complete, consistent snapshot (whichever the writer had fully committed to by the time the read lock was granted).
5. `sl.unlockRead(stamp)` releases the fallback lock, and `Math.sqrt(curX*curX + curY*curY)` computes the distance from a value that is now guaranteed to correspond to some real, complete state the point had at some point in time — never a mismatched torn combination.
6. Across the five writer moves and five reader samples in the demo, most optimistic reads likely succeed on the first try (since the actual overlap window is small, even with the added sleep it's not *guaranteed* to always be hit) — but whenever one does get invalidated, the fallback silently and transparently produces a correct answer anyway, which is exactly the contract `StampedLock`'s optimistic mode promises.

## 7. Gotchas & takeaways

> **Gotcha:** code between `tryOptimisticRead()` and `validate()` must be side-effect-free and must never assume the values it reads are consistent with each other — since a concurrent writer might be actively mutating the data underneath it. Never index an array, dereference a pointer-like reference, or throw an exception based on unvalidated optimistically-read values; validate first, or you risk crashing or misbehaving on a genuinely torn, mid-write snapshot rather than just computing a slightly wrong number that gets discarded anyway.

- `StampedLock`'s optimistic mode takes no lock at all for reads — it's faster than `ReadWriteLock` for extremely read-heavy, low-write workloads, at the cost of a mandatory validate-and-retry pattern.
- Always call `validate(stamp)` after reading and before trusting or acting on the values — skipping it defeats the entire safety model and can expose genuinely inconsistent data.
- Keep the code between the optimistic read and its validation minimal, cheap, and free of side effects or exceptions based on the (possibly inconsistent) data.
- `StampedLock` is **not** reentrant the way `synchronized` or `ReentrantLock` are — recursively re-acquiring the same lock mode from the same thread can deadlock; be careful porting code that relied on reentrancy.
- For workloads with more balanced or unpredictable read/write ratios, or where the extra care of optimistic reads isn't worth the complexity, prefer the simpler [`ReadWriteLock`](0868-readwritelock.md) instead.
