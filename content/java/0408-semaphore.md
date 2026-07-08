---
card: java
gi: 408
slug: semaphore
title: Semaphore
---

## 1. What it is

A `Semaphore` guards access to a limited number of "permits." A thread calls `acquire()` to take a permit (blocking if none are available) and `release()` to give one back. Unlike a `Lock`, which allows exactly one thread through at a time, a `Semaphore` constructed with `n` permits allows up to `n` threads through **simultaneously** — it's a lock generalised from "1 at a time" to "N at a time."

## 2. Why & when

Plenty of concurrency problems aren't "only one thread may do this" but rather "at most N threads may do this at once" — limiting concurrent connections to a database, capping how many threads hit a rate-limited external API simultaneously, or restricting concurrent access to a fixed-size resource pool (like a set of 5 physical printers, or 10 available file handles). A `ReentrantLock` can't express "N at a time" directly; `Semaphore` was built exactly for this.

You reach for `Semaphore` any time there's a **countable, limited resource** shared across threads: connection pools, rate limiters, or bounding how many threads may concurrently execute an expensive operation, even when that operation itself needs no other synchronization.

## 3. Core concept

```java
import java.util.concurrent.Semaphore;

Semaphore permits = new Semaphore(3); // allow up to 3 threads through at once

permits.acquire(); // takes one permit; BLOCKS if all 3 are currently held by other threads
try {
    // do the limited work — at most 3 threads are ever in here concurrently
} finally {
    permits.release(); // gives the permit back, potentially unblocking a waiting thread
}
```

Notice permits don't need to be acquired and released by the same conceptual "owner" the way a lock does — a `Semaphore` has no notion of which thread holds which permit, it just tracks a count. This makes it flexible for producer/consumer-style signalling too, not just mutual exclusion.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Semaphore with 3 permits lets 3 threads run concurrently; a 4th thread blocks in acquire until one of the first 3 releases">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">Semaphore(3): 3 permits available</text>

  <rect x="30" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="90" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread A: holds 1</text>
  <rect x="170" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="230" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B: holds 1</text>
  <rect x="310" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="370" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread C: holds 1</text>
  <rect x="450" y="40" width="150" height="34" rx="6" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/><text x="525" y="61" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Thread D: acquire() BLOCKS</text>

  <text x="320" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">0 permits remain -- Thread D waits until A, B, or C calls release()</text>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The moment any of A/B/C release, D's acquire() unblocks and it proceeds.</text>
</svg>

Exactly `n` threads may hold a permit at once; the `(n+1)`th blocks until a permit is returned.

## 5. Runnable example

Scenario: limiting concurrent access to a small pool of database connections — the same connection pool, evolved from a naive version with no limit (which would overwhelm the database), through a `Semaphore`-limited version, to one using `tryAcquire` with a timeout so callers can fail fast rather than wait indefinitely under sustained overload.

### Level 1 — Basic

```java
public class DbCallsUnlimited {
    static void useConnection(String caller) throws InterruptedException {
        System.out.println(caller + " acquired a connection");
        Thread.sleep(100); // simulates a query
        System.out.println(caller + " released its connection");
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 5; i++) {
            int id = i;
            new Thread(() -> {
                try { useConnection("caller-" + id); } catch (InterruptedException ignored) { }
            }).start();
        }
        Thread.sleep(500); // let them all finish before main exits
    }
}
```

**How to run:** `java DbCallsUnlimited.java`

All 5 callers "use a connection" simultaneously with no limit at all — fine for a demo, but if the real database can only sustain, say, 2 concurrent connections, this would overwhelm it in production.

### Level 2 — Intermediate

```java
import java.util.concurrent.Semaphore;

public class DbCallsSemaphoreLimited {
    static final Semaphore connectionPermits = new Semaphore(2); // simulate a pool of 2 connections

    static void useConnection(String caller) throws InterruptedException {
        connectionPermits.acquire(); // blocks if both connections are already in use
        try {
            System.out.println(caller + " acquired a connection");
            Thread.sleep(100);
            System.out.println(caller + " released its connection");
        } finally {
            connectionPermits.release();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 5; i++) {
            int id = i;
            new Thread(() -> {
                try { useConnection("caller-" + id); } catch (InterruptedException ignored) { }
            }).start();
        }
        Thread.sleep(500);
    }
}
```

**How to run:** `java DbCallsSemaphoreLimited.java`

With `Semaphore(2)`, only 2 callers ever hold a connection simultaneously — the other 3 block in `acquire()` until one of the first 2 finishes and calls `release()`, protecting the (simulated) database from more concurrent load than it can handle.

### Level 3 — Advanced

```java
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;

public class DbCallsSemaphoreTimeout {
    static final Semaphore connectionPermits = new Semaphore(2);

    static boolean useConnection(String caller) throws InterruptedException {
        // Don't wait forever for a connection -- fail fast if the pool is saturated for too long
        if (!connectionPermits.tryAcquire(150, TimeUnit.MILLISECONDS)) {
            System.out.println(caller + " gave up: no connection available in time");
            return false;
        }
        try {
            System.out.println(caller + " acquired a connection");
            Thread.sleep(200);
            System.out.println(caller + " released its connection");
            return true;
        } finally {
            connectionPermits.release();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 5; i++) {
            int id = i;
            new Thread(() -> {
                try { useConnection("caller-" + id); } catch (InterruptedException ignored) { }
            }).start();
        }
        Thread.sleep(600);
    }
}
```

**How to run:** `java DbCallsSemaphoreTimeout.java`

`tryAcquire(150, TimeUnit.MILLISECONDS)` gives each caller a bounded window to get a connection; with 5 callers, a pool of 2, and each holding its connection for 200ms, some callers will time out and give up rather than piling up indefinitely — a more realistic, production-safe pattern than blocking forever under sustained overload.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, launching 5 threads (`caller-1` through `caller-5`) almost simultaneously, each calling `useConnection`. `connectionPermits` starts with 2 available permits.

Suppose `caller-1` and `caller-2` are the first two to call `tryAcquire(150, TimeUnit.MILLISECONDS)` — since 2 permits are available, both succeed immediately, dropping the available count to 0. Both print `"acquired a connection"` and begin their simulated 200ms query via `Thread.sleep(200)`.

`caller-3`, `caller-4`, and `caller-5` then attempt `tryAcquire` but find 0 permits available — each blocks, waiting up to 150ms for a permit to free up. Since `caller-1` and `caller-2` are each sleeping for 200ms (longer than the 150ms wait budget), none of the permits are released in time for any of `caller-3`, `4`, or `5` — all three time out, each printing `"gave up: no connection available in time"` and returning `false` without ever touching the (simulated) database.

After their 200ms sleep, `caller-1` and `caller-2` each print `"released its connection"` and, in their `finally` blocks, call `connectionPermits.release()`, returning both permits to the pool (available count back to 2) — but by this point, `caller-3`, `4`, and `5` have already given up and are no longer waiting, so nothing further happens with those returned permits in this particular run.

`main`'s `Thread.sleep(600)` gives all 5 threads enough time to finish before the JVM exits.

Expected output (the exact two "winning" callers can vary by scheduling, but the shape — 2 succeed, 3 give up — is stable):
```
caller-1 acquired a connection
caller-2 acquired a connection
caller-3 gave up: no connection available in time
caller-4 gave up: no connection available in time
caller-5 gave up: no connection available in time
caller-1 released its connection
caller-2 released its connection
```

## 7. Gotchas & takeaways

> Always pair `acquire()` with `release()` in a `try/finally`, exactly like a lock. If code between `acquire()` and `release()` throws and `release()` is skipped, that permit is **lost forever** — the semaphore's available count permanently shrinks by one, eventually starving all other threads even though nothing is technically deadlocked.

- `Semaphore(n)` generalises mutual exclusion from "1 thread at a time" (a lock) to "up to `n` threads at a time."
- `acquire()` blocks until a permit is available; `tryAcquire()` (with or without a timeout) lets a thread give up instead of waiting indefinitely.
- Permits aren't tied to the thread that acquired them the way a lock is tied to its owner — any thread can call `release()`, which makes `Semaphore` useful for signalling patterns too, not just mutual exclusion.
- Always release in a `finally` block — a "leaked" permit (never released) permanently reduces the pool's effective capacity.
- Common use cases: bounding concurrent connections to a limited external resource, rate-limiting concurrent access to an expensive operation, or implementing a custom bounded resource pool.
