---
card: java
gi: 886
slug: countdownlatch
title: CountDownLatch
---

## 1. What it is

`CountDownLatch` is a one-time synchronization gate initialized with a fixed count. One or more threads call `await()` to block until the count reaches zero; other threads call `countDown()` to decrement it, once each. When the count hits zero, every waiting thread is released simultaneously — and the latch stays open forever after: it cannot be reset or reused. It models exactly one thing: "wait until N specific events have all happened."

## 2. Why & when

Use `CountDownLatch` whenever a thread (or several) must wait for a known, fixed number of other things to finish before proceeding — waiting for N worker threads to finish initializing before serving the first request, or waiting for all of several dependent services to report "ready" before starting the main workload. It's also useful in reverse: a "starting gate" pattern, where a latch initialized to 1 lets several worker threads all block on `await()` until a single `countDown()` call releases them simultaneously, useful for maximizing contention in tests or benchmarks. Because it's single-use, reach for [`CyclicBarrier`](0887-cyclicbarrier.md) instead when you need the same coordination point to be reused repeatedly (e.g., synchronizing threads at the end of every iteration of a loop).

## 3. Core concept

```java
CountDownLatch readyLatch = new CountDownLatch(3); // wait for 3 events

// Three worker threads, each doing this once when their init finishes:
readyLatch.countDown();

// The main thread:
readyLatch.await(); // blocks until all 3 have called countDown()
System.out.println("all workers ready, proceeding");
```

`await()` can also take a timeout (`await(long, TimeUnit)`), returning `false` if the count never reached zero within that window, rather than blocking forever.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Main thread awaits a latch initialized to 3; three worker threads each call countDown once; once the count reaches zero, the main thread is released">
  <rect x="20" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Main thread: await() -- BLOCKED</text>

  <rect x="240" y="20" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Worker A: countDown()</text>
  <rect x="240" y="60" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Worker B: countDown()</text>
  <rect x="240" y="100" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Worker C: countDown()</text>

  <text x="460" y="15" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">count: 3 -&gt; 2 -&gt; 1 -&gt; 0</text>
  <rect x="420" y="60" width="180" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">count reaches 0 -&gt; latch opens</text>

  <line x1="360" y1="35" x2="416" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a21)"/>
  <line x1="360" y1="75" x2="416" y2="77" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a21)"/>
  <line x1="360" y1="115" x2="416" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a21)"/>
  <line x1="510" y1="60" x2="180" y2="45" stroke="#f0883e" stroke-width="2" stroke-dasharray="4" marker-end="url(#a21)"/>
  <text x="330" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Main thread's await() returns the instant the count hits zero -- a one-time gate.</text>
  <defs><marker id="a21" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The latch releases exactly once, when the count reaches zero — it can never be reset or reused afterward.*

## 5. Runnable example

Scenario: a service that must wait for several subsystems to finish initializing before accepting requests, growing from a naive polling wait, to a correct `CountDownLatch`, to a "starting gate" pattern that also uses a latch to release several worker threads simultaneously for a benchmark.

### Level 1 — Basic

```java
public class PollingWait {
    static volatile int readyCount = 0;

    static void initSubsystem(int id) {
        try { Thread.sleep(50 * (id + 1)); } catch (InterruptedException ignored) {}
        readyCount++; // NOT thread-safe, but illustrative of the polling approach's shape
        System.out.println("subsystem " + id + " ready");
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 3; i++) {
            final int id = i;
            new Thread(() -> initSubsystem(id)).start();
        }
        while (readyCount < 3) {
            Thread.sleep(5); // POLLING -- wastes CPU, adds latency, and readyCount isn't even safely published
        }
        System.out.println("all subsystems ready, starting service");
    }
}
```

**How to run:** `java PollingWait.java` (JDK 17+).

Expected output shape (order of "ready" messages depends on the sleep durations):
```
subsystem 0 ready
subsystem 1 ready
subsystem 2 ready
all subsystems ready, starting service
```

Works by accident here, but polling wastes CPU, and `readyCount++` on a plain `int` field read/written by multiple threads without synchronization is a genuine data race — this pattern should not be trusted in real code.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class CountDownLatchWait {
    static void initSubsystem(int id, CountDownLatch latch) {
        try { Thread.sleep(50 * (id + 1)); } catch (InterruptedException ignored) {}
        System.out.println("subsystem " + id + " ready");
        latch.countDown(); // signal completion -- decrements the shared count
    }

    public static void main(String[] args) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(3); // wait for exactly 3 events
        for (int i = 0; i < 3; i++) {
            final int id = i;
            new Thread(() -> initSubsystem(id, latch)).start();
        }

        latch.await(); // blocks efficiently -- no polling, no CPU waste
        System.out.println("all subsystems ready, starting service");
    }
}
```

**How to run:** `java CountDownLatchWait.java`.

Expected output shape:
```
subsystem 0 ready
subsystem 1 ready
subsystem 2 ready
all subsystems ready, starting service
```

The real-world concern added: `latch.await()` blocks the main thread efficiently (no polling loop, no wasted CPU) until exactly three `countDown()` calls have happened, and there's no data race — the latch's internal state handles the cross-thread visibility correctly, unlike the plain `int` counter in Level 1.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class StartingGateBenchmark {
    public static void main(String[] args) throws InterruptedException {
        int workerCount = 8;
        CountDownLatch readyLatch = new CountDownLatch(workerCount); // workers signal "ready to start"
        CountDownLatch startGate = new CountDownLatch(1);            // main signals "GO" to everyone at once
        AtomicInteger completedCount = new AtomicInteger(0);

        for (int i = 0; i < workerCount; i++) {
            final int id = i;
            new Thread(() -> {
                readyLatch.countDown(); // signal this worker is ready and waiting
                try {
                    startGate.await(); // block here until the main thread says GO -- all at once
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                // Real work starts here, for EVERY worker at nearly the exact same instant --
                // maximizing genuine contention, which is exactly what a benchmark or stress test wants.
                completedCount.incrementAndGet();
            }).start();
        }

        readyLatch.await(); // wait until ALL workers are lined up and waiting at the gate
        System.out.println("all " + workerCount + " workers ready and waiting -- releasing now");
        long start = System.nanoTime();
        startGate.countDown(); // releases ALL waiting workers simultaneously

        while (completedCount.get() < workerCount) { Thread.onSpinWait(); } // wait for all to finish
        System.out.println("all workers completed within " + (System.nanoTime() - start) / 1_000_000 + "ms of release");
    }
}
```

**How to run:** `java StartingGateBenchmark.java`.

Expected output shape (elapsed time is small, confirming near-simultaneous release):
```
all 8 workers ready and waiting -- releasing now
all workers completed within 2ms of release
```

This adds the production-flavored hard case: **two** `CountDownLatch` instances working together — `readyLatch` (count = 8) lets the main thread know every worker has reached the starting line and is genuinely blocked and waiting, while `startGate` (count = 1) is the actual "go" signal, released by a single `countDown()` call that unblocks all 8 workers at essentially the same instant. This "rendezvous, then release together" pattern is the standard way to construct fair, high-contention benchmarks or stress tests where you want every thread to start its real work simultaneously, rather than staggered by however long each thread took to spin up.

## 6. Walkthrough

Tracing `StartingGateBenchmark.main`:

1. Eight worker threads are started. Each immediately calls `readyLatch.countDown()` — signaling "I've reached the starting line" — and then calls `startGate.await()`, blocking since `startGate`'s count is still 1.
2. Meanwhile, `main` calls `readyLatch.await()`, which blocks until all eight workers have called their `countDown()` — this guarantees every worker is genuinely parked at `startGate.await()` before `main` proceeds, rather than some workers still being mid-startup.
3. Once `readyLatch` reaches zero, `main`'s `await()` returns, and it prints the "releasing now" message, records the current time via `System.nanoTime()`, then calls `startGate.countDown()`.
4. This single `countDown()` call brings `startGate`'s count from 1 to 0, which releases **every** one of the eight worker threads' `await()` calls essentially simultaneously — none of them staggered by startup timing, since they were all already blocked and waiting.
5. Each released worker immediately increments `completedCount` — since this is the "real work" being benchmarked (kept trivial here for the demo, but representing whatever the actual timed operation would be).
6. `main`'s spin-wait loop (`while (completedCount.get() < workerCount)`) waits for all eight increments to land, then computes the elapsed time since the release — a small number of milliseconds, confirming that all eight threads really did start their work at nearly the same instant rather than one after another.

## 7. Gotchas & takeaways

> **Gotcha:** `CountDownLatch` cannot be reset or reused — once its count reaches zero, it stays open forever; calling `countDown()` further has no effect, and `await()` on an already-open latch returns immediately. If you need the same coordination point to repeat across multiple rounds (e.g., every iteration of a loop), use [`CyclicBarrier`](0887-cyclicbarrier.md) instead, which is explicitly designed to be reused.

- `CountDownLatch` models "wait for N specific events to happen, exactly once" — any thread can call `countDown()`, and any number of threads can call `await()`, all released together the instant the count hits zero.
- It is single-use: once opened, it cannot be closed or reset — construct a new latch if you need the same coordination again.
- The "starting gate" pattern (a latch with count 1, released once to unblock many simultaneously-waiting threads) is a standard technique for maximizing genuine contention in benchmarks and stress tests.
- Prefer `await(timeout, unit)` over the unbounded `await()` in production code where a hung dependency shouldn't block your thread forever.
- For coordination where threads need to wait for *each other* repeatedly (not just for a fixed external count), see [`CyclicBarrier`](0887-cyclicbarrier.md); for limiting concurrent access rather than waiting for completion, see [`Semaphore`](0888-semaphore.md).
