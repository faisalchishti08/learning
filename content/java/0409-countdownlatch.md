---
card: java
gi: 409
slug: countdownlatch
title: CountDownLatch
---

## 1. What it is

`CountDownLatch` is a one-shot synchronization tool that lets one or more threads wait until a set number of events have happened elsewhere. You create it with a fixed count (`new CountDownLatch(3)`), other threads call `countDown()` when their piece of work finishes (decrementing the count), and any thread calling `await()` blocks until the count reaches zero. Once it hits zero, it stays there permanently — a `CountDownLatch` cannot be reset or reused.

## 2. Why & when

A common startup problem: an application shouldn't start serving requests until several independent subsystems (database connection pool, cache warm-up, config load) have each finished initializing. Coordinating this with raw `Thread.join()` calls only works if you know exactly which threads to wait for and they're structured as simple threads — it doesn't generalize well to "wait for N things to happen," especially when those N things are tasks on a shared thread pool rather than dedicated threads you can `join()`.

`CountDownLatch` expresses this directly: initialize it with the number of things to wait for, have each one call `countDown()` when done, and have the waiting thread(s) call `await()`. It also naturally supports "wait for several things to *start*" (initialize the latch, have worker threads count down immediately upon starting, and have a coordinator wait for that before doing something that requires all workers to be alive) — useful for testing race conditions by getting many threads to begin simultaneously.

## 3. Core concept

```java
import java.util.concurrent.CountDownLatch;

CountDownLatch latch = new CountDownLatch(3); // wait for 3 events

// Each of 3 worker threads, upon finishing its part:
latch.countDown(); // decrements the count by one; the 3rd call brings it to zero

// The waiting thread:
latch.await(); // blocks until the count reaches zero, then returns immediately (forever after)
System.out.println("All 3 finished!");
```

Once the count reaches zero, every future call to `await()` (from any thread, at any time) returns immediately — there is no way to "re-arm" a `CountDownLatch` back to a higher count. If you need a reusable barrier, see the next tutorial, `CyclicBarrier`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three worker threads each call countDown once; the waiting thread's await unblocks the moment the count reaches zero">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="105" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Worker 1: countDown()</text>
  <rect x="30" y="75" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="105" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Worker 2: countDown()</text>
  <rect x="30" y="120" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="105" y="142" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Worker 3: countDown()</text>

  <text x="280" y="60" fill="#e6edf3" font-size="11" font-family="sans-serif">count: 3 -&gt; 2 -&gt; 1 -&gt; 0</text>

  <rect x="440" y="75" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="520" y="97" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Coordinator: await()</text>
  <line x1="180" y1="47" x2="435" y2="90" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="180" y1="92" x2="435" y2="92" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="180" y1="137" x2="435" y2="94" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="520" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">unblocks only after all 3 count down</text>
</svg>

`await()` releases the instant the third and final `countDown()` call brings the count to zero.

## 5. Runnable example

Scenario: an application's startup sequence must wait for three subsystems (database, cache, config) to finish initializing before serving requests — the same startup gate, evolved from waiting via `Thread.join()`, through a `CountDownLatch`-based version that works with a thread pool, to one with a bounded timeout so startup doesn't hang forever if a subsystem never finishes.

### Level 1 — Basic

```java
public class StartupJoin {
    static void initSubsystem(String name, long delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        System.out.println(name + " initialized");
    }

    public static void main(String[] args) throws InterruptedException {
        Thread db = new Thread(() -> {
            try { initSubsystem("database", 100); } catch (InterruptedException ignored) { }
        });
        Thread cache = new Thread(() -> {
            try { initSubsystem("cache", 60); } catch (InterruptedException ignored) { }
        });
        Thread config = new Thread(() -> {
            try { initSubsystem("config", 30); } catch (InterruptedException ignored) { }
        });

        db.start(); cache.start(); config.start();
        db.join(); cache.join(); config.join(); // works, but only because we have direct Thread references

        System.out.println("All subsystems ready — starting server.");
    }
}
```

**How to run:** `java StartupJoin.java`

`Thread.join()` works here because we happen to have direct references to all three threads — but this approach breaks down the moment initialization tasks are submitted to a shared `ExecutorService` instead of being their own dedicated `Thread` objects, since `Future`s from a pool don't offer a clean "wait for all of these" primitive as naturally as a latch does.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class StartupLatch {
    static void initSubsystem(String name, long delayMs, CountDownLatch latch) {
        try {
            Thread.sleep(delayMs);
            System.out.println(name + " initialized");
        } catch (InterruptedException ignored) {
        } finally {
            latch.countDown(); // always count down, even if init partially failed
        }
    }

    public static void main(String[] args) throws InterruptedException {
        CountDownLatch startupLatch = new CountDownLatch(3);
        ExecutorService pool = Executors.newFixedThreadPool(3);

        pool.submit(() -> initSubsystem("database", 100, startupLatch));
        pool.submit(() -> initSubsystem("cache", 60, startupLatch));
        pool.submit(() -> initSubsystem("config", 30, startupLatch));

        startupLatch.await(); // blocks main until all 3 have called countDown()
        System.out.println("All subsystems ready — starting server.");

        pool.shutdown();
    }
}
```

**How to run:** `java StartupLatch.java`

Now initialization tasks run on a shared pool (no direct `Thread` references needed); `startupLatch.await()` blocks the main thread until all three tasks have called `countDown()` in their `finally` blocks — this generalizes cleanly to any number of pooled tasks, unlike `Thread.join()`.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class StartupLatchTimeout {
    static void initSubsystem(String name, long delayMs, CountDownLatch latch) {
        try {
            Thread.sleep(delayMs);
            System.out.println(name + " initialized");
        } catch (InterruptedException ignored) {
        } finally {
            latch.countDown();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        CountDownLatch startupLatch = new CountDownLatch(3);
        ExecutorService pool = Executors.newFixedThreadPool(3);

        pool.submit(() -> initSubsystem("database", 100, startupLatch));
        pool.submit(() -> initSubsystem("cache", 60, startupLatch));
        pool.submit(() -> initSubsystem("slow-legacy-system", 5000, startupLatch)); // deliberately slow

        boolean allReady = startupLatch.await(300, TimeUnit.MILLISECONDS); // bounded wait

        if (allReady) {
            System.out.println("All subsystems ready — starting server.");
        } else {
            System.out.println("Timed out after 300ms — starting in degraded mode. Remaining: "
                + startupLatch.getCount());
        }

        pool.shutdown();
    }
}
```

**How to run:** `java StartupLatchTimeout.java`

`await(300, TimeUnit.MILLISECONDS)` returns `false` if the timeout elapses before the count reaches zero, rather than blocking forever — letting the application make a deliberate decision (start in a degraded mode) instead of hanging indefinitely because one slow subsystem never finished. `getCount()` reports how many `countDown()` calls are still outstanding.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `startupLatch` is created with count `3`. Three tasks are submitted to a 3-thread pool: `database` (100ms), `cache` (60ms), and `slow-legacy-system` (5000ms) — all three begin running concurrently almost immediately.

`main` then calls `startupLatch.await(300, TimeUnit.MILLISECONDS)`, blocking for up to 300ms while watching the latch's count.

At around 60ms, the `cache` task finishes its `Thread.sleep(60)`, prints `"cache initialized"`, and its `finally` block calls `latch.countDown()` — count drops from 3 to 2. At around 100ms, `database` finishes similarly, printing `"database initialized"` and dropping the count from 2 to 1.

`slow-legacy-system`, however, is still 4900ms away from finishing its 5000ms sleep when the 300ms timeout on `main`'s `await()` call elapses. Since the count is still `1` (not zero) at that point, `await(300, TimeUnit.MILLISECONDS)` returns `false` rather than continuing to block. The `if (allReady)` check takes the `else` branch, printing a degraded-mode message along with `startupLatch.getCount()`, which reports `1` (the still-outstanding `slow-legacy-system` task).

`main` then proceeds to `pool.shutdown()` — note this does **not** forcibly stop `slow-legacy-system`'s already-running task; `shutdown()` only prevents *new* tasks from being submitted, so the legacy task keeps running in the background (eventually finishing and calling `countDown()` on a latch nobody is watching anymore, which is harmless).

Expected output (exact millisecond timing may vary slightly, but the shape — cache and database finish, legacy times out — is stable):
```
cache initialized
database initialized
Timed out after 300ms — starting in degraded mode. Remaining: 1
```

## 7. Gotchas & takeaways

> A `CountDownLatch` is **one-shot** — once its count reaches zero, it cannot be reset or reused for a second round of waiting. If you need repeated synchronization points (e.g. threads that must sync up at the end of *every* phase of a multi-phase computation), use `CyclicBarrier` instead, covered next.

- Initialize with the exact number of `countDown()` calls you expect; `await()` blocks until that many have happened.
- Always call `countDown()` in a `finally` block if the work being counted might throw — otherwise a failure can leave `await()` blocked forever.
- `await(timeout, unit)` returns `false` on timeout instead of blocking indefinitely — use it whenever "wait forever" isn't an acceptable failure mode.
- `getCount()` reports the current outstanding count, useful for diagnostics or deciding what "still missing" means after a timeout.
- Works cleanly with an `ExecutorService`-based pool, unlike `Thread.join()`, since it doesn't require holding direct references to the threads doing the work.
