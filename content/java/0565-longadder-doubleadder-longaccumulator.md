---
card: java
gi: 565
slug: longadder-doubleadder-longaccumulator
title: LongAdder / DoubleAdder / LongAccumulator
---

## 1. What it is

`LongAdder`, `DoubleAdder`, and `LongAccumulator` (`java.util.concurrent.atomic`) are Java 8 counters designed for **high-contention concurrent updates** — many threads incrementing or accumulating a shared value at once. They give up the ability to atomically read-and-update in a single step (which `AtomicLong` provides) in exchange for dramatically better throughput when many threads are hammering the same counter, by internally spreading updates across multiple memory cells instead of forcing every thread to contend for one.

## 2. Why & when

`AtomicLong.incrementAndGet()` is a single `long` variable updated via compare-and-swap (CAS). Under light contention that's fast, but under **heavy** contention (many threads, all incrementing the same `AtomicLong` constantly) most CAS attempts fail and retry, and threads effectively serialize on that one memory location — throughput collapses as thread count rises. `LongAdder` solves this by maintaining an internal array of counter "cells": under contention, different threads update different cells (avoiding collisions), and the total is only summed up (`sum()`) when someone actually needs to read it. This trades slower reads (summing several cells) for much faster, less-contended writes — exactly the right trade for a counter that's updated far more often than it's read, like a request counter or hit counter under load. `LongAccumulator` generalizes the same idea to any associative combining function, not just addition.

## 3. Core concept

```java
LongAdder hits = new LongAdder();

hits.increment();      // cheap, low-contention update
hits.add(5);
long total = hits.sum(); // reads (and internally combines) the current total

LongAccumulator max = new LongAccumulator(Long::max, Long.MIN_VALUE);
max.accumulate(42);
max.accumulate(17);
long biggest = max.get(); // 42
```

`LongAdder` is specifically addition; `LongAccumulator` takes any `LongBinaryOperator` (like `Long::max`) plus an identity value, generalizing the same low-contention-write strategy to arbitrary associative operations.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AtomicLong forces all threads through one memory cell; LongAdder spreads updates across several cells">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">AtomicLong — every thread contends for ONE cell:</text>
  <rect x="20" y="35" width="120" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="80" y="55" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">value</text>
  <text x="160" y="55" fill="#8b949e" font-size="9" font-family="sans-serif">&lt;- T1, T2, T3, T4 all CAS here</text>

  <text x="20" y="100" fill="#8b949e" font-size="11" font-family="sans-serif">LongAdder — threads spread across multiple cells:</text>
  <rect x="20" y="110" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="65" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">cell[0]</text>
  <rect x="120" y="110" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="165" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">cell[1]</text>
  <rect x="220" y="110" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="265" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">cell[2]</text>
  <rect x="320" y="110" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="365" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">cell[3]</text>
  <text x="20" y="160" fill="#8b949e" font-size="10" font-family="sans-serif">sum() adds all cells together only when a read is actually needed.</text>
</svg>

Fewer collisions on writes means far higher throughput under contention; reads become slightly more work (summing cells) in exchange.

## 5. Runnable example

Scenario: counting page-view events and tracking the peak concurrent-request count in a simulated web server under load — starting with a basic single-threaded counter, then hammering it from many threads to compare `AtomicLong` vs `LongAdder`, then adding a `LongAccumulator` to track a running maximum alongside the count.

### Level 1 — Basic

```java
import java.util.concurrent.atomic.LongAdder;

public class HitCounterBasic {
    public static void main(String[] args) {
        LongAdder hits = new LongAdder();

        hits.increment();
        hits.increment();
        hits.add(3);

        System.out.println("Total hits: " + hits.sum());
    }
}
```

**How to run:** `java HitCounterBasic.java`

Expected output:
```
Total hits: 5
```

`hits.increment()` is shorthand for `add(1)`. `hits.add(3)` adds an arbitrary delta. `hits.sum()` returns the current total by combining all internal cells — in this single-threaded example there's no contention, so it behaves identically to a simple counter, but the API is already the concurrency-ready one.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.LongAdder;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.CountDownLatch;

public class HitCounterConcurrent {
    static void hammer(Runnable incrementAction, int threadCount, int incrementsPerThread) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(threadCount);
        long start = System.nanoTime();
        for (int i = 0; i < threadCount; i++) {
            new Thread(() -> {
                for (int j = 0; j < incrementsPerThread; j++) incrementAction.run();
                latch.countDown();
            }).start();
        }
        latch.await();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("  elapsed: " + elapsedMs + " ms");
    }

    public static void main(String[] args) throws InterruptedException {
        int threadCount = 8;
        int incrementsPerThread = 500_000;

        AtomicLong atomicHits = new AtomicLong();
        System.out.println("AtomicLong:");
        hammer(atomicHits::incrementAndGet, threadCount, incrementsPerThread);
        System.out.println("  total: " + atomicHits.get());

        LongAdder adderHits = new LongAdder();
        System.out.println("LongAdder:");
        hammer(adderHits::increment, threadCount, incrementsPerThread);
        System.out.println("  total: " + adderHits.sum());
    }
}
```

**How to run:** `java HitCounterConcurrent.java`

Expected output (exact timings vary by machine; both totals are always exactly correct, and LongAdder is typically noticeably faster under contention on a multi-core machine):
```
AtomicLong:
  elapsed: 210 ms
  total: 4000000
LongAdder:
  elapsed: 60 ms
  total: 4000000
```

The real-world concern this adds: **genuine multi-threaded contention**, where 8 threads each perform 500,000 increments concurrently on the same counter — 4,000,000 total increments. Both `AtomicLong` and `LongAdder` produce the exact same, fully correct total (no increments are lost to races), but `LongAdder` typically finishes faster because its internal cell-striping reduces contention between threads competing for the same memory location, which matters more as thread count and contention rise.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.LongAdder;
import java.util.concurrent.atomic.LongAccumulator;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadLocalRandom;

public class ServerLoadStats {
    static class LoadTracker {
        private final LongAdder totalRequests = new LongAdder();
        private final LongAccumulator peakLatencyMs = new LongAccumulator(Long::max, Long.MIN_VALUE);

        void recordRequest(long latencyMs) {
            totalRequests.increment();
            peakLatencyMs.accumulate(latencyMs);
        }

        String report() {
            return "Total requests: " + totalRequests.sum() + ", Peak latency: " + peakLatencyMs.get() + " ms";
        }
    }

    public static void main(String[] args) throws InterruptedException {
        LoadTracker tracker = new LoadTracker();
        int threadCount = 6;
        int requestsPerThread = 100_000;
        CountDownLatch latch = new CountDownLatch(threadCount);

        for (int i = 0; i < threadCount; i++) {
            new Thread(() -> {
                ThreadLocalRandom random = ThreadLocalRandom.current();
                for (int j = 0; j < requestsPerThread; j++) {
                    long simulatedLatency = random.nextInt(1, 200);
                    tracker.recordRequest(simulatedLatency);
                }
                latch.countDown();
            }).start();
        }

        latch.await();
        System.out.println(tracker.report());
        System.out.println("Expected total: " + (threadCount * requestsPerThread));
    }
}
```

**How to run:** `java ServerLoadStats.java`

Expected output (peak latency value varies by run since it's randomly generated, but is always between 1 and 199; total is deterministic):
```
Total requests: 600000, Peak latency: 199 ms
Expected total: 600000
```

This combines a `LongAdder` (for a plain running count) with a `LongAccumulator` (for a running maximum) under real concurrent load — exactly the pattern a web server's request-tracking middleware would use: cheaply incrementing a hit counter and cheaply tracking the worst-case latency seen so far, both updated on every single request from potentially many concurrent handler threads, without either counter becoming a contention bottleneck.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. A single shared `LoadTracker` is created, holding a `LongAdder` (`totalRequests`) and a `LongAccumulator` configured with `Long::max` and an identity of `Long.MIN_VALUE` (`peakLatencyMs`) — the identity value is what `peakLatencyMs.get()` would return if `accumulate` were never called, chosen so that any real latency value is guaranteed to be larger.

Six threads are started, each looping 100,000 times. Each iteration generates a random simulated latency between 1 and 199 (via `ThreadLocalRandom`, itself designed to avoid contention between threads — each thread gets its own generator instance) and calls `tracker.recordRequest(simulatedLatency)`.

Inside `recordRequest`, two independent low-contention updates happen: `totalRequests.increment()` bumps the request counter using the cell-striping strategy from part 4, and `peakLatencyMs.accumulate(latencyMs)` combines the new latency with whatever the accumulator currently holds using the `Long::max` function, internally using the same kind of striped-cell strategy `LongAdder` uses — but combining via `max` instead of `+`.

```
Thread A: recordRequest(87)  -> totalRequests: cellA += 1 | peakLatencyMs: cellA = max(cellA, 87)
Thread B: recordRequest(150) -> totalRequests: cellB += 1 | peakLatencyMs: cellB = max(cellB, 150)
Thread C: recordRequest(42)  -> totalRequests: cellC += 1 | peakLatencyMs: cellC = max(cellC, 42)
...(600,000 such calls spread across 6 threads, largely non-colliding)...
```

Because six threads run concurrently and each is independently updating cells rather than one shared value, there's little to no contention even with 600,000 total updates happening in a tight window.

After `latch.await()` returns (all six threads finished their 100,000 iterations each), `tracker.report()` is called. `totalRequests.sum()` walks the internal cells and adds them together, producing the true total of `600,000` — exactly `6 * 100,000`, confirming no update was lost despite the concurrent, low-contention writes. `peakLatencyMs.get()` similarly combines the internal cells using `Long::max`, yielding the single highest latency value observed across all 600,000 simulated requests, which will be `199` with overwhelming probability given 600,000 draws from `[1, 199]`.

## 7. Gotchas & takeaways

> `LongAdder.sum()` (and `LongAccumulator.get()`) is **not atomic with respect to concurrent updates** — if writer threads are actively calling `increment()`/`accumulate()` while `sum()` runs, the returned total might not reflect every single one of those concurrent writes (it's an approximation that becomes exact once writes stop). For a snapshot total during active writes, this is expected and acceptable for most metrics/counter use cases; if you need a value that's guaranteed atomic at every instant, `LongAdder` is the wrong tool — use `AtomicLong` instead.

- `LongAdder`/`DoubleAdder` are specifically for **addition**; use `LongAccumulator`/`DoubleAccumulator` for any other associative combining operation (max, min, bitwise OR, etc.) by supplying a `LongBinaryOperator`/`DoubleBinaryOperator` and an identity value.
- Under **low** contention (few threads, infrequent updates), `AtomicLong` and `LongAdder` perform similarly — the advantage of `LongAdder` only shows up under genuinely high contention. Don't reach for it reflexively; measure if it matters.
- `LongAdder` uses more memory than a single `AtomicLong` (it may allocate an array of cells internally, growing under contention), a reasonable trade for a counter but not for a value you need many independent instances of.
- Neither `LongAdder` nor `AtomicLong` supports atomic "compare and set to X only if currently Y" semantics the way `AtomicLong` alone does with `compareAndSet` — `LongAdder` intentionally drops that capability in exchange for write throughput.
- Both `LongAdder` and `LongAccumulator` extend `Number`, so `intValue()`, `longValue()`, etc. are available, but `sum()`/`get()` are the idiomatic accessors for their respective types.
