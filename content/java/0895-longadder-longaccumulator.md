---
card: java
gi: 895
slug: longadder-longaccumulator
title: LongAdder / LongAccumulator
---

## 1. What it is

`LongAdder` is a specialized counter, purpose-built to outperform `AtomicLong` specifically under high-contention increments from many threads. Instead of every thread CAS-ing the *same* single underlying value, `LongAdder` internally maintains a set of separate "cells," and different threads' updates get spread across different cells (reducing CAS contention on any one memory location) — `sum()` (or `longValue()`) adds up all the cells to produce the current total on demand. `LongAccumulator` generalizes the same striped-cell technique to an arbitrary associative combining function (not just addition) supplied at construction, such as `Long::max` or `Long::sum`.

## 2. Why & when

Under low or moderate contention, `AtomicLong.incrementAndGet()` is simple, fast, and gives you an exact, immediately-consistent value on every call. Under *very* high contention — many threads hammering the same counter simultaneously, as in a hot request-counting metric — the single memory location an `AtomicLong` protects becomes a bottleneck: every thread's CAS attempt contends with every other thread's, and failed CAS attempts retry repeatedly. `LongAdder` trades away one property (`sum()` isn't necessarily perfectly up-to-the-microsecond consistent if called concurrently with in-flight updates, though it settles to the correct total once updates quiesce) for much better write throughput under contention, by letting concurrent increments land on different internal cells that don't contend with each other. Use `LongAdder` for write-heavy, read-infrequently counters — metrics, request tallies, hit counters — where you increment far more often than you read the total. Use `LongAccumulator` for the same striping benefit with a different combining operation, such as tracking a running maximum or minimum under high contention.

## 3. Core concept

```java
LongAdder hitCounter = new LongAdder();
hitCounter.increment(); // spreads across internal cells under contention -- fast writes
long total = hitCounter.sum(); // reads and combines all cells -- use sparingly under heavy concurrent writes

LongAccumulator maxTracker = new LongAccumulator(Long::max, Long.MIN_VALUE);
maxTracker.accumulate(someValue); // combines someValue with the current running value via Long::max
long currentMax = maxTracker.get();
```

`LongAdder.increment()` is the write-optimized operation; `sum()` is comparatively more expensive (it visits every internal cell) and is meant to be called far less often than increments happen.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple threads each incrementing a different internal cell of a LongAdder, avoiding contention on a single shared value; sum adds all cells together when the total is needed">
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">LongAdder internal cells (simplified)</text>
  <rect x="60" y="35" width="90" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cell 0: 412</text>
  <rect x="180" y="35" width="90" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="225" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cell 1: 398</text>
  <rect x="300" y="35" width="90" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="345" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cell 2: 405</text>
  <rect x="420" y="35" width="90" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="465" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cell 3: 389</text>

  <text x="105" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">T1, T5, T9... write here</text>
  <text x="225" y="95" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">T2, T6... write here</text>
  <text x="345" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">T3, T7... write here</text>
  <text x="465" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T4, T8... write here</text>

  <rect x="230" y="130" width="180" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sum() = 412+398+405+389 = 1604</text>
</svg>

*Threads are spread across cells, so most concurrent writes never contend for the same CAS target; `sum()` combines every cell only when the total is actually needed.*

## 5. Runnable example

Scenario: a high-throughput request counter under heavy concurrent load, growing from `AtomicLong` establishing a baseline, to `LongAdder` demonstrating improved write throughput under contention, to `LongAccumulator` tracking a running maximum latency alongside the count.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicLongBaseline {
    static AtomicLong counter = new AtomicLong(0);

    public static void main(String[] args) throws InterruptedException {
        int threads = 16;
        int incrementsPerThread = 2_000_000;
        ExecutorService pool = Executors.newFixedThreadPool(threads);

        long start = System.currentTimeMillis();
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) counter.incrementAndGet();
            });
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);

        System.out.println("total = " + counter.get());
        System.out.println("elapsed with AtomicLong under heavy contention: " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

**How to run:** `java AtomicLongBaseline.java` (JDK 17+).

Expected output shape (elapsed time is machine-dependent, establishing a baseline for comparison):
```
total = 32000000
elapsed with AtomicLong under heavy contention: 850ms
```

Correct, but with 16 threads all CAS-contending on the exact same `AtomicLong` memory location tens of millions of times, a meaningful fraction of CAS attempts fail and must retry.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class LongAdderImprovedThroughput {
    static LongAdder counter = new LongAdder();

    public static void main(String[] args) throws InterruptedException {
        int threads = 16;
        int incrementsPerThread = 2_000_000;
        ExecutorService pool = Executors.newFixedThreadPool(threads);

        long start = System.currentTimeMillis();
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) counter.increment();
            });
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);

        System.out.println("total = " + counter.sum());
        System.out.println("elapsed with LongAdder under the SAME contention: " + (System.currentTimeMillis() - start) + "ms (typically faster)");
    }
}
```

**How to run:** `java LongAdderImprovedThroughput.java`.

Expected output shape (typically noticeably faster than the AtomicLong baseline, under real contention):
```
total = 32000000
elapsed with LongAdder under the SAME contention: 320ms (typically faster)
```

The real-world concern added: the identical workload (16 threads, 32 million total increments) now spreads its CAS contention across `LongAdder`'s internal cells instead of one single memory location — under genuine multi-core contention, this typically completes measurably faster than the `AtomicLong` baseline, since far fewer CAS attempts fail and retry.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class LongAccumulatorMaxTracking {
    static LongAdder requestCount = new LongAdder();
    static LongAccumulator maxLatency = new LongAccumulator(Long::max, Long.MIN_VALUE);

    static void handleRequest(long simulatedLatencyMs) {
        requestCount.increment();
        maxLatency.accumulate(simulatedLatencyMs); // atomically combines via Long::max, striped like LongAdder
    }

    public static void main(String[] args) throws InterruptedException {
        int threads = 16;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        java.util.Random random = new java.util.Random(42);

        for (int t = 0; t < threads; t++) {
            long[] latencies = new long[10_000];
            for (int i = 0; i < latencies.length; i++) latencies[i] = 1 + random.nextInt(200);
            pool.submit(() -> {
                for (long latency : latencies) handleRequest(latency);
            });
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);

        System.out.println("total requests: " + requestCount.sum());
        System.out.println("max observed latency: " + maxLatency.get() + "ms (correctly tracked under high concurrency)");
    }
}
```

**How to run:** `java LongAccumulatorMaxTracking.java`.

Expected output shape (max latency is deterministic given the seeded random generator's range 1-200):
```
total requests: 160000
max observed latency: 200ms (correctly tracked under high concurrency)
```

This adds the production-flavored hard case: tracking **two** independent striped metrics simultaneously — a `LongAdder` for a simple count and a `LongAccumulator` for a running maximum, using `Long::max` as the combining function — both benefiting from the same internal cell-striping technique to minimize contention, demonstrating that the striping approach generalizes cleanly beyond simple addition to any associative combining operation.

## 6. Walkthrough

Tracing `LongAccumulatorMaxTracking.main`:

1. 16 threads are each given their own pre-generated array of 10,000 random latency values (seeded for determinism), and each submitted task loops over its own array, calling `handleRequest(latency)` for each one.
2. Each call to `handleRequest` does two independent striped updates: `requestCount.increment()` (a `LongAdder`, incrementing one of its internal cells) and `maxLatency.accumulate(simulatedLatencyMs)` (a `LongAccumulator`, combining the new value into one of its internal cells via `Long::max`).
3. Internally, `LongAccumulator.accumulate(x)` works like `LongAdder`'s striping: it picks one of several internal cells (based on which thread is calling, to spread contention) and atomically combines that cell's current value with `x` using the supplied function (`Long::max` here) via a CAS-retry loop — so two threads updating *different* cells never contend, while updates to the *same* cell still correctly combine via CAS.
4. Because `Long::max` is associative and commutative, it doesn't matter what order the 160,000 total `accumulate` calls happen to interleave in across the 16 concurrent threads and the accumulator's internal cells — the final combined result is guaranteed to be the true maximum across every single value ever passed to `accumulate`.
5. After all threads finish (`pool.awaitTermination`), `requestCount.sum()` adds up every `LongAdder` cell to report the total request count (160,000, exactly 16 × 10,000), and `maxLatency.get()` combines every `LongAccumulator` cell (via the same `Long::max` function used for individual updates) to report the true overall maximum latency observed across all threads.
6. Both values are exact and correct despite the high degree of concurrent contention, because the striping technique only affects *how* contention is distributed internally — it never affects the correctness of the final combined result once all writers have finished.

## 7. Gotchas & takeaways

> **Gotcha:** `LongAdder.sum()` (and `LongAccumulator.get()`) is **not** guaranteed to reflect a value that was ever truly "current" at any single instant if called concurrently with in-flight `increment()`/`accumulate()` calls from other threads — it may reflect an intermediate mix of some-but-not-all in-progress updates. For a metric read only occasionally after writes have settled (like reporting a final total after a batch completes), this is irrelevant; for a value that must be read frequently and needs strict up-to-the-instant consistency, `AtomicLong` may actually be the more appropriate choice despite its higher contention cost.

- `LongAdder`/`LongAccumulator` trade `sum()`/`get()`'s"immediate perfect consistency under concurrent writes" for significantly better write throughput under high contention, by striping updates across multiple internal cells instead of contending on one shared value.
- Use them for write-heavy, read-infrequently counters and aggregates — metrics, hit counters, request tallies — where the true value is only needed occasionally, not on every single write.
- `LongAccumulator` generalizes the same technique beyond addition to any associative combining function supplied at construction (`Long::max`, `Long::min`, `Long::sum`, or a custom one).
- Prefer `AtomicLong` when you need a value that's exactly, immediately consistent on every read even under concurrent writes, or when contention is low enough that the striping technique's benefit wouldn't matter anyway.
- The underlying striping technique is conceptually similar to spreading contention across [`AtomicIntegerArray`](0893-atomicintegerarray-etc.md)'s independent indices — both reduce CAS contention by avoiding a single shared point of contention, just applied at different levels of the API.
