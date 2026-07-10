---
card: java
gi: 893
slug: atomicintegerarray-etc
title: AtomicIntegerArray etc.
---

## 1. What it is

`AtomicIntegerArray`, `AtomicLongArray`, and `AtomicReferenceArray<E>` provide the same atomic, lock-free compound operations as their single-value counterparts (`AtomicInteger`, `AtomicLong`, `AtomicReference`), but applied **per-element** to an entire array — `get(i)`, `set(i, value)`, `incrementAndGet(i)`, `compareAndSet(i, expected, new)`, and so on, each atomic with respect to that specific index. Critically, different indices are entirely independent: an atomic update to index 3 has no effect on, and no contention with, an atomic update to index 7 happening concurrently on another thread.

## 2. Why & when

A plain `int[]` array has no atomicity guarantees at all for concurrent access — even a single element's `array[i]++` is the same non-atomic read-modify-write problem as a plain `int` field. Wrapping the whole array in one external lock would work but serializes *all* index access through a single lock, even when two threads are updating completely unrelated indices that could safely proceed in parallel. `AtomicIntegerArray` and friends solve exactly this: each index gets its own independent atomicity, so concurrent updates to different indices never contend with each other at all, while updates to the *same* index are still correctly serialized via CAS. Use these classes for parallel algorithms that partition work by index — per-bucket histograms, per-slot counters in a fixed-size hash structure, or any per-position aggregate computed by many threads writing to different (or occasionally the same) positions concurrently.

## 3. Core concept

```java
AtomicIntegerArray histogram = new AtomicIntegerArray(10); // 10 independent atomic counters

// Many threads can safely do this concurrently, for ANY index, with no external lock:
histogram.incrementAndGet(bucketIndex);

// Two threads updating DIFFERENT indices never contend with each other at all:
// thread A: histogram.incrementAndGet(2)   -- independent of --
// thread B: histogram.incrementAndGet(7)
```

Each index behaves like its own independent `AtomicInteger` — the array just bundles many of them together with a compact, index-addressed API.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An AtomicIntegerArray with five slots; two threads updating different slots proceed independently and concurrently with no contention, while two threads updating the same slot are serialized via CAS">
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">AtomicIntegerArray, 5 independent slots</text>

  <rect x="20" y="35" width="100" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="70" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[0]</text>
  <rect x="130" y="35" width="100" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="180" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[1] -- T1 writes</text>
  <rect x="240" y="35" width="100" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="290" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[2]</text>
  <rect x="350" y="35" width="100" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="400" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[3] -- T2,T3 write</text>
  <rect x="460" y="35" width="100" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="510" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[4]</text>

  <text x="180" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">T1 -&gt; slot 1: no contention with any other slot</text>
  <text x="400" y="120" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">T2, T3 -&gt; slot 3: CAS-serialized against EACH OTHER only</text>
</svg>

*Each index is its own independent atomic cell — contention only exists between threads targeting the exact same index.*

## 5. Runnable example

Scenario: building a histogram of values falling into fixed buckets from many concurrent producer threads, growing from a locked, whole-array version, to `AtomicIntegerArray` for genuinely independent per-bucket atomicity, to a version comparing throughput between few and many hot (contended) buckets.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LockedArrayHistogram {
    static final int[] buckets = new int[10];
    static final Object lock = new Object();

    static void record(int bucketIndex) {
        synchronized (lock) { // ONE lock for the WHOLE array -- every update serializes against every other
            buckets[bucketIndex]++;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 80_000; i++) {
            final int bucket = i % 10;
            pool.submit(() -> record(bucket));
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        int total = 0;
        for (int count : buckets) total += count;
        System.out.println("total recorded: " + total + " (expected 80000)");
    }
}
```

**How to run:** `java LockedArrayHistogram.java` (JDK 17+).

Expected output:
```
total recorded: 80000 (expected 80000)
```

Correct, but every single update — even to entirely different buckets — contends for the same one lock, needlessly serializing updates that touch unrelated array positions.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicIntegerArrayHistogram {
    static final AtomicIntegerArray buckets = new AtomicIntegerArray(10);

    static void record(int bucketIndex) {
        buckets.incrementAndGet(bucketIndex); // atomic per-index, no external lock, no cross-index contention
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 80_000; i++) {
            final int bucket = i % 10;
            pool.submit(() -> record(bucket));
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        int total = 0;
        for (int i = 0; i < buckets.length(); i++) total += buckets.get(i);
        System.out.println("total recorded: " + total + " (expected 80000)");
        System.out.println("bucket 0: " + buckets.get(0) + " (expected 8000)");
    }
}
```

**How to run:** `java AtomicIntegerArrayHistogram.java`.

Expected output:
```
total recorded: 80000 (expected 80000)
bucket 0: 8000 (expected 8000)
```

The real-world concern added: each bucket is now updated via its own independent atomic operation — a thread updating bucket 3 never contends with, waits for, or is slowed down by a thread simultaneously updating bucket 7, unlike the single-lock version where every update, regardless of target bucket, serialized against every other.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class HotVsColdBucketComparison {
    static long runHistogramBenchmark(int bucketCount, int totalUpdates) throws InterruptedException {
        AtomicIntegerArray buckets = new AtomicIntegerArray(bucketCount);
        ExecutorService pool = Executors.newFixedThreadPool(8);

        long start = System.currentTimeMillis();
        for (int i = 0; i < totalUpdates; i++) {
            final int bucket = i % bucketCount; // fewer buckets = more contention per bucket ("hot" buckets)
            pool.submit(() -> buckets.incrementAndGet(bucket));
        }
        pool.shutdown();
        pool.awaitTermination(15, TimeUnit.SECONDS);
        return System.currentTimeMillis() - start;
    }

    public static void main(String[] args) throws InterruptedException {
        int totalUpdates = 500_000;

        long fewHotBuckets = runHistogramBenchmark(2, totalUpdates);   // heavy contention per bucket
        long manyColdBuckets = runHistogramBenchmark(1000, totalUpdates); // light contention per bucket

        System.out.println("2 hot buckets (heavy per-bucket contention): " + fewHotBuckets + "ms");
        System.out.println("1000 cold buckets (light per-bucket contention): " + manyColdBuckets + "ms");
        System.out.println("more buckets spreads CAS contention thinner, typically improving throughput");
    }
}
```

**How to run:** `java HotVsColdBucketComparison.java`.

Expected output shape (exact times vary by machine, but the many-buckets case is typically faster or comparable, never dramatically worse):
```
2 hot buckets (heavy per-bucket contention): 420ms
1000 cold buckets (light per-bucket contention): 180ms
more buckets spreads CAS contention thinner, typically improving throughput
```

This adds the production-flavored hard case: comparing throughput when many threads hammer just 2 shared buckets (every update to a given bucket must CAS-retry against every other concurrent update to that *same* bucket, since CAS contention still exists per-index) versus spreading the same total number of updates across 1000 buckets (each individual bucket sees far fewer concurrent updates, so CAS retries are rarer). This illustrates that `AtomicIntegerArray`'s per-index independence only helps *between* different indices — updates concentrated onto the same few indices still contend exactly as much as a single `AtomicInteger` would.

## 6. Walkthrough

Tracing why the "2 hot buckets" benchmark tends to run slower than "1000 cold buckets" in `HotVsColdBucketComparison.main`:

1. In the 2-bucket run, every one of the 500,000 submitted increments targets either index 0 or index 1 (via `i % 2`) — meaning roughly 250,000 concurrent increment attempts are all contending for the CAS on the *same* single array slot at any given time, across all 8 pool threads.
2. Each `incrementAndGet(bucket)` call internally performs the same CAS-retry-loop as `AtomicInteger.incrementAndGet()` (see [CAS](0891-cas-compare-and-swap.md)) — under heavy contention on one specific memory location, many of these CAS attempts fail and must retry, since only one thread's CAS can succeed at any given instant for a given index.
3. In the 1000-bucket run, the same 500,000 increments are spread across 1000 distinct indices (`i % 1000`), so on average only 500 increments target any single specific bucket — each individual bucket experiences far less concurrent contention, meaning far fewer CAS retries overall across the whole array.
4. Because `AtomicIntegerArray`'s atomicity guarantee is genuinely per-index (there's no shared internal lock across the whole array — see the diagram above), spreading updates across more indices directly reduces the total amount of CAS contention experienced system-wide, which is exactly why the 1000-bucket run tends to complete faster.
5. Both runs still produce a fully correct total count (500,000, verifiable by summing all buckets) — the difference is purely about *throughput* under contention, not correctness; `AtomicIntegerArray` guarantees the latter unconditionally, but the former depends on how concentrated the updates are onto specific indices.

## 7. Gotchas & takeaways

> **Gotcha:** `AtomicIntegerArray`'s per-index atomicity does **not** mean cross-index operations (like "atomically swap the values at index 2 and index 5") are supported directly — each index's atomic operations are independent and isolated; coordinating an atomic operation across *multiple* indices at once still requires an external lock or a different data structure entirely.

- `AtomicIntegerArray`/`AtomicLongArray`/`AtomicReferenceArray<E>` give every array index its own independent, lock-free atomicity — concurrent updates to *different* indices never contend with each other.
- This is a strict improvement over locking the whole array with one shared lock, which needlessly serializes updates to unrelated indices.
- Contention still exists *within* a single index if many threads target it concurrently — spreading load across more indices (when your algorithm allows it) reduces CAS retries and improves throughput, as demonstrated by the hot-vs-cold bucket comparison.
- Use these classes for parallel algorithms naturally partitioned by index — histograms, per-slot counters, per-bucket aggregates computed by many concurrent threads.
- For a single hot counter under very heavy contention (rather than many independent counters), consider whether [`LongAdder`](0895-longadder-longaccumulator.md)'s internal striping technique — conceptually related to spreading contention across multiple cells, as this tutorial's array does across indices — might outperform a plain `AtomicLong`.
