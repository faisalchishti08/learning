---
card: java
gi: 888
slug: semaphore
title: Semaphore
---

## 1. What it is

`Semaphore` manages a fixed number of **permits**: `acquire()` blocks until a permit is available and then takes one; `release()` gives a permit back. Unlike a lock, a semaphore isn't tied to "one owner" — it's tied to a *count*, so up to N threads can hold a permit simultaneously (where N is the number the semaphore was constructed with), making it the natural tool for limiting concurrent access to a resource with finite capacity, rather than enforcing single-threaded exclusive access the way `synchronized` or `ReentrantLock` do.

## 2. Why & when

Use a `Semaphore` whenever you need to cap the number of threads doing something concurrently, without necessarily caring *which* threads — limiting concurrent connections to a database or external API to avoid overwhelming it, limiting how many threads can hold expensive in-memory buffers at once, or implementing a simple resource pool. A semaphore with exactly 1 permit behaves like a lock (mutual exclusion), but a semaphore with N permits generalizes that to "up to N at a time," which a plain lock cannot express. `tryAcquire()` (optionally with a timeout) lets a thread give up rather than block forever if no permit becomes available in time — useful for graceful degradation under load instead of unbounded queuing.

## 3. Core concept

```java
Semaphore connectionLimiter = new Semaphore(3); // at most 3 concurrent "connections"

void useConnection() throws InterruptedException {
    connectionLimiter.acquire(); // blocks if 3 are already in use
    try {
        // do work using the limited resource
    } finally {
        connectionLimiter.release(); // ALWAYS release, even on exception, to avoid permanently losing a permit
    }
}
```

Any number of distinct threads can each hold one of the 3 permits at once — a semaphore constrains *how many* concurrent holders there are, not *which specific thread* holds it, which is the key difference from a lock.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A semaphore with 3 permits: three threads hold permits and run concurrently, a fourth thread blocks until one is released">
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Semaphore(3) -- 3 permits total</text>

  <rect x="20" y="35" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T1 holds permit -- running</text>
  <rect x="190" y="35" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="265" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T2 holds permit -- running</text>
  <rect x="360" y="35" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="435" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T3 holds permit -- running</text>

  <rect x="190" y="100" width="150" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="265" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T4: acquire() -- BLOCKED, no permits free</text>

  <line x1="95" y1="70" x2="265" y2="98" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="330" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Once any of T1/T2/T3 calls release(), T4's acquire() unblocks.</text>
</svg>

*Three permits allow three concurrent holders; a fourth thread waits until one is released, rather than being blocked by a single owning thread.*

## 5. Runnable example

Scenario: limiting concurrent access to a small pool of "expensive" resources (simulated), growing from unbounded concurrency, to a correctly-limiting `Semaphore`, to a version using `tryAcquire` with a timeout for graceful degradation under sustained overload.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class UnboundedConcurrency {
    static AtomicInteger concurrentUsers = new AtomicInteger(0);
    static AtomicInteger maxObserved = new AtomicInteger(0);

    static void useExpensiveResource(int id) {
        int current = concurrentUsers.incrementAndGet();
        maxObserved.updateAndGet(prev -> Math.max(prev, current));
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        concurrentUsers.decrementAndGet();
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(10);
        for (int i = 0; i < 10; i++) {
            final int id = i;
            pool.submit(() -> useExpensiveResource(id)); // NOTHING limits how many run at once
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("max concurrent users observed: " + maxObserved.get() + " (uncontrolled -- could be all 10 at once)");
    }
}
```

**How to run:** `java UnboundedConcurrency.java` (JDK 17+).

Expected output shape:
```
max concurrent users observed: 10 (uncontrolled -- could be all 10 at once)
```

Nothing here limits how many threads simultaneously use the "expensive resource" — if it represents something with real capacity limits (a database connection pool, a rate-limited API), this can overwhelm it.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SemaphoreLimitedConcurrency {
    static final Semaphore semaphore = new Semaphore(3); // at most 3 concurrent users
    static AtomicInteger concurrentUsers = new AtomicInteger(0);
    static AtomicInteger maxObserved = new AtomicInteger(0);

    static void useExpensiveResource(int id) throws InterruptedException {
        semaphore.acquire(); // blocks if 3 permits are already taken
        try {
            int current = concurrentUsers.incrementAndGet();
            maxObserved.updateAndGet(prev -> Math.max(prev, current));
            Thread.sleep(50);
            concurrentUsers.decrementAndGet();
        } finally {
            semaphore.release(); // ALWAYS release, even if the work above throws
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(10);
        for (int i = 0; i < 10; i++) {
            final int id = i;
            pool.submit(() -> {
                try { useExpensiveResource(id); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("max concurrent users observed: " + maxObserved.get() + " (capped at 3, as intended)");
    }
}
```

**How to run:** `java SemaphoreLimitedConcurrency.java`.

Expected output:
```
max concurrent users observed: 3 (capped at 3, as intended)
```

The real-world concern added: even with 10 threads all wanting to use the resource simultaneously, the semaphore ensures at most 3 are ever actually "inside" at once — the other 7 correctly queue up on `acquire()` and proceed only as permits are released.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class TryAcquireGracefulDegradation {
    static final Semaphore semaphore = new Semaphore(3);
    static AtomicInteger served = new AtomicInteger(0);
    static AtomicInteger degraded = new AtomicInteger(0);

    static void useExpensiveResourceOrDegrade(int id) throws InterruptedException {
        if (semaphore.tryAcquire(100, TimeUnit.MILLISECONDS)) { // give up after 100ms instead of blocking forever
            try {
                served.incrementAndGet();
                Thread.sleep(150); // simulate real work
            } finally {
                semaphore.release();
            }
        } else {
            degraded.incrementAndGet(); // couldn't get a permit in time -- fall back gracefully
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(10);
        for (int i = 0; i < 10; i++) {
            final int id = i;
            pool.submit(() -> {
                try { useExpensiveResourceOrDegrade(id); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("served fully: " + served.get());
        System.out.println("degraded (gave up gracefully): " + degraded.get());
        System.out.println("total: " + (served.get() + degraded.get()) + " (all 10 requests handled, none hung forever)");
    }
}
```

**How to run:** `java TryAcquireGracefulDegradation.java`.

Expected output shape (exact split depends on timing, but all 10 are accounted for):
```
served fully: 6
degraded (gave up gracefully): 4
total: 10 (all 10 requests handled, none hung forever)
```

This adds the production-flavored hard case: with only 3 permits, 150ms of work per served request, and 10 competing threads, an unbounded `acquire()` would eventually serve everyone but could make later threads wait a long time. `tryAcquire(100ms)` instead gives each thread a bounded wait, after which it gracefully degrades (skips the expensive resource, falls back to some cheaper behavior) rather than queuing indefinitely — a common real-world pattern for maintaining responsiveness under load rather than letting a resource bottleneck cascade into unbounded latency for every caller.

## 6. Walkthrough

Tracing `TryAcquireGracefulDegradation.main` under load:

1. Ten tasks are submitted to a 10-thread pool essentially simultaneously, each calling `useExpensiveResourceOrDegrade`.
2. The first three tasks to call `semaphore.tryAcquire(100, TimeUnit.MILLISECONDS)` succeed immediately, since all 3 permits are free — each proceeds into its `try` block, increments `served`, and sleeps 150ms to simulate real work.
3. The remaining seven tasks call `tryAcquire` but find no permits available; each blocks for up to 100ms waiting for one to free up.
4. Since the three "in progress" tasks each take 150ms and there are only 3 permits, none of the three initial holders releases before the 100ms timeout elapses for the waiting tasks — so all seven waiting tasks time out, `tryAcquire` returns `false` for each, and they increment `degraded` instead of proceeding.
5. After 150ms, the first three tasks finish their work and call `semaphore.release()` in their `finally` blocks, but by this point, most (in this specific timing scenario) of the waiting threads have already given up at the 100ms mark — though the exact split between "served" and "degraded" depends on precise timing and could vary slightly between runs.
6. `pool.shutdown()` and `awaitTermination` wait for every submitted task (served or degraded) to finish before the final counts are printed, confirming all 10 original requests were accounted for — some served fully, some gracefully degraded, but none left hanging indefinitely.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `release()` — especially inside error paths or without a `finally` block — permanently reduces the semaphore's effective permit count, eventually starving every future `acquire()` call as permits leak away one by one with no way to recover them short of restarting the process.

- A `Semaphore` manages a count of permits, not ownership by a specific thread — any thread can acquire, and (unless you build additional discipline around it) any thread can release, even one that never acquired.
- A single-permit semaphore behaves like a mutual-exclusion lock; the real value is N > 1, limiting concurrent access to a resource with genuine capacity constraints.
- Always release permits in a `finally` block, matching every `acquire()` — a leaked permit is a subtle, cumulative bug that only manifests as gradually increasing contention over the life of the process.
- `tryAcquire(timeout, unit)` enables graceful degradation under sustained overload instead of unbounded blocking or unbounded queuing — decide deliberately what "give up gracefully" means for your specific use case.
- For coordinating an exact number of one-time completion events rather than limiting ongoing concurrent access, [`CountDownLatch`](0886-countdownlatch.md) is the more appropriate tool.
