---
card: java
gi: 406
slug: reentrantreadwritelock
title: ReentrantReadWriteLock
---

## 1. What it is

`ReentrantReadWriteLock` provides a **pair** of locks that share the same underlying state: a **read lock**, which can be held simultaneously by any number of threads as long as no thread holds the write lock, and a **write lock**, which is exclusive — only one thread may hold it, and no reader can hold the read lock at the same time. You obtain each via `.readLock()` and `.writeLock()`, and each behaves like a regular `Lock` (`.lock()`/`.unlock()`).

## 2. Why & when

A plain `ReentrantLock` (or `synchronized` block) is all-or-nothing: only one thread total, whether reading or writing. But many real workloads are **read-heavy and write-rare** — a cached configuration object, a lookup table refreshed occasionally, an in-memory index. With a plain lock, two threads that both just want to *read* the data still block each other unnecessarily, even though neither would ever corrupt anything by reading concurrently.

`ReentrantReadWriteLock` fixes this by allowing unlimited concurrent readers when no writer is active, while still fully serializing writers against both other writers and all readers. This can dramatically improve throughput for read-heavy data, at the cost of slightly more overhead per lock/unlock than a plain lock, and added complexity: you must remember which lock (read or write) to acquire for which operation, and get it right, since acquiring the wrong one either under-protects a write or needlessly serializes reads.

## 3. Core concept

```java
import java.util.concurrent.locks.ReentrantReadWriteLock;

ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();

// Many threads can hold this at once, as long as no thread holds the write lock:
rwLock.readLock().lock();
try {
    // read shared data
} finally {
    rwLock.readLock().unlock();
}

// Only one thread at a time, and no readers may be active concurrently:
rwLock.writeLock().lock();
try {
    // modify shared data
} finally {
    rwLock.writeLock().unlock();
}
```

Think of it as a library reading room versus renovating that same room. Any number of people can sit and read (readLock) at once. But the moment renovation starts (writeLock), everyone must leave and no one new is let in until it's done — and renovation itself only ever has one crew.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple readers can hold the read lock simultaneously; the write lock is exclusive against both readers and other writers">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">No writer active: many readers allowed concurrently</text>
  <rect x="30" y="38" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="80" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Reader A</text>
  <rect x="140" y="38" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="190" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Reader B</text>
  <rect x="250" y="38" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="300" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Reader C</text>

  <text x="20" y="110" fill="#e6edf3" font-size="11" font-family="sans-serif">Writer active: it holds the room ALONE, no readers or other writers</text>
  <rect x="30" y="122" width="140" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="100" y="142" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Writer (exclusive)</text>
  <rect x="200" y="122" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="250" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Reader D: waits</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Readers never block other readers; a writer blocks everyone, and everyone blocks a writer.</text>
</svg>

Reads can overlap freely; a write always has the whole lock to itself.

## 5. Runnable example

Scenario: an in-memory configuration cache read constantly by request-handling threads and refreshed occasionally by a background updater — the same cache, evolved from a plain lock that needlessly serializes concurrent reads, through the read/write split, to a version demonstrating lock downgrading (holding the write lock, then safely stepping down to the read lock without ever fully releasing access).

### Level 1 — Basic

```java
import java.util.concurrent.locks.ReentrantLock;
import java.util.HashMap;
import java.util.Map;

public class ConfigCachePlainLock {
    static final Map<String, String> config = new HashMap<>();
    static final ReentrantLock lock = new ReentrantLock();

    static String read(String key) {
        lock.lock();
        try {
            return config.get(key);
        } finally {
            lock.unlock();
        }
    }

    static void write(String key, String value) {
        lock.lock();
        try {
            config.put(key, value);
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) {
        write("timeout", "30s");
        System.out.println("timeout = " + read("timeout"));
        // Problem: even two concurrent READERS block each other here, unnecessarily -- see Level 2
    }
}
```

**How to run:** `java ConfigCachePlainLock.java`

A single `ReentrantLock` protects both reads and writes correctly, but it also means two threads that both only want to *read* the config still serialize against each other — wasted concurrency for a workload where reads vastly outnumber writes.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.HashMap;
import java.util.Map;

public class ConfigCacheReadWriteLock {
    static final Map<String, String> config = new HashMap<>();
    static final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();

    static String read(String key) {
        rwLock.readLock().lock();
        try {
            return config.get(key);
        } finally {
            rwLock.readLock().unlock();
        }
    }

    static void write(String key, String value) {
        rwLock.writeLock().lock();
        try {
            config.put(key, value);
        } finally {
            rwLock.writeLock().unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        write("timeout", "30s");

        Runnable reader = () -> {
            for (int i = 0; i < 3; i++) {
                System.out.println(Thread.currentThread().getName() + " read timeout=" + read("timeout"));
            }
        };

        Thread r1 = new Thread(reader, "reader-1");
        Thread r2 = new Thread(reader, "reader-2");
        r1.start(); r2.start();
        r1.join(); r2.join();
    }
}
```

**How to run:** `java ConfigCacheReadWriteLock.java`

`reader-1` and `reader-2` both call `read()` and both hold the **read lock simultaneously** — since no writer is active, `ReentrantReadWriteLock` allows this concurrency freely, unlike Level 1's plain lock, which would have forced them to take turns even though neither modifies anything.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.HashMap;
import java.util.Map;

public class ConfigCacheDowngrade {
    static final Map<String, String> config = new HashMap<>(Map.of("timeout", "30s"));
    static final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();

    // Refresh the config AND immediately read it back, without ever giving another writer
    // a window to sneak in a conflicting change between the write and the read.
    static String refreshAndRead(String key, String newValue) {
        rwLock.writeLock().lock();
        String result;
        try {
            config.put(key, newValue);
            // LOCK DOWNGRADE: acquire the read lock BEFORE releasing the write lock
            rwLock.readLock().lock();
        } finally {
            rwLock.writeLock().unlock(); // now only holding the read lock -- no other writer can have snuck in
        }
        try {
            result = config.get(key); // safe: still holding the read lock
        } finally {
            rwLock.readLock().unlock();
        }
        return result;
    }

    public static void main(String[] args) {
        String result = refreshAndRead("timeout", "60s");
        System.out.println("Refreshed and confirmed: timeout = " + result);
    }
}
```

**How to run:** `java ConfigCacheDowngrade.java`

**Lock downgrading** — acquiring the read lock *while still holding* the write lock, then releasing the write lock — guarantees no other writer can modify the data in the gap between writing and reading it back. The reverse (upgrading a read lock to a write lock) is **not supported** by `ReentrantReadWriteLock` and will deadlock if attempted, which is why downgrading is the only safe direction.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, calling `refreshAndRead("timeout", "60s")`.

Inside, `rwLock.writeLock().lock()` is acquired first — since no other thread holds any lock yet, this succeeds immediately, granting exclusive access. `config.put("timeout", "60s")` updates the map; at this point, `config` now holds `"60s"`, but only this thread can see or touch it, since the write lock is exclusive.

Still holding the write lock, the code calls `rwLock.readLock().lock()` — this is the **downgrade step**. Because `ReentrantReadWriteLock` allows a thread already holding the write lock to also acquire the read lock (this is explicitly supported and safe), this succeeds immediately too. At this moment, the thread holds *both* locks simultaneously.

The `finally` block for the outer `try` then runs `rwLock.writeLock().unlock()` — releasing only the *write* lock, while the read lock (acquired a moment ago) is still held. This is the crucial guarantee: between putting the new value and reading it back, no other thread could have acquired the write lock to change `"timeout"` to something else, because this thread never gave up all locking — it went straight from "holding write" to "holding read," with no gap where the data was unprotected.

The second `try` block then reads `config.get("timeout")`, safely, since the read lock is still held — this returns `"60s"`, the value just written, guaranteed not to have been changed by anyone else in between. Finally, `rwLock.readLock().unlock()` releases the read lock, and the confirmed value is returned and printed.

Expected output:
```
Refreshed and confirmed: timeout = 60s
```

## 7. Gotchas & takeaways

> `ReentrantReadWriteLock` supports **downgrading** (write lock → read lock, without a gap) but explicitly does **not** support **upgrading** (read lock → write lock). If a thread holding the read lock tries to also acquire the write lock while still holding the read lock, it deadlocks — because the write lock cannot be granted while any read lock (including its own) is held. Always release the read lock fully before attempting to acquire the write lock.

- The read lock can be held by any number of threads simultaneously, as long as no thread holds the write lock.
- The write lock is fully exclusive — no readers and no other writers may hold anything while it's held.
- Best fit: data that's read far more often than it's written (caches, configuration, lookup tables) — the read-lock concurrency is where the performance win comes from.
- Downgrading (write → read, without releasing in between) is safe and commonly used to guarantee no other writer can interleave between a write and its immediate read-back.
- Upgrading (read → write) is unsupported and will deadlock — if you need to conditionally write after reading, release the read lock first, then acquire the write lock and re-check the condition.
