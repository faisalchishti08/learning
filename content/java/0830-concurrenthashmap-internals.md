---
card: java
gi: 830
slug: concurrenthashmap-internals
title: ConcurrentHashMap internals
---

## 1. What it is

`ConcurrentHashMap` is a thread-safe `Map` implementation designed for genuinely concurrent access from many threads, without the single-lock-per-call bottleneck of [`Hashtable`](0826-hashtable-legacy.md) or `Collections.synchronizedMap`. Modern versions (Java 8+) achieve this with fine-grained locking scoped to individual bins (buckets) — a write to one bucket only blocks other writes to that *same* bucket, not the whole map — combined with lock-free (`volatile`-read-based) access for most reads, which typically require no locking at all. It also provides genuinely **atomic** compound operations — `computeIfAbsent`, `computeIfPresent`, `compute`, and `merge` — that perform their entire read-modify-write sequence as one atomic unit per key, something no amount of external synchronization around a plain `HashMap` can offer as conveniently or with as little contention.

## 2. Why & when

`Hashtable` and `Collections.synchronizedMap` both serialize every operation behind one lock for the whole map — under real concurrent load, every thread queues up behind that single lock even when they're touching completely unrelated keys, wasting parallelism the underlying hardware could otherwise provide. `ConcurrentHashMap` fixes this at the structural level: because locking (where it happens at all) is scoped to individual bins, two threads writing to different, non-colliding keys can genuinely proceed in parallel. It's the default choice for any concurrent map need in modern Java — general caches, counters, registries — unless a specific need for `null` support (which `ConcurrentHashMap` deliberately disallows, for both keys and values, to avoid ambiguity between "absent" and "present but null" during concurrent reads) or sorted iteration ([`ConcurrentSkipListMap`](0831-concurrentskiplistmap.md)) points elsewhere.

## 3. Core concept

```java
ConcurrentHashMap<String, Integer> counters = new ConcurrentHashMap<>();

// The WRONG way under concurrency -- a classic non-atomic check-then-act, even on a "concurrent" map:
if (!counters.containsKey("hits")) {
    counters.put("hits", 0); // another thread could race in between these two calls
}
counters.put("hits", counters.get("hits") + 1); // read-then-write -- also racy

// The RIGHT way -- merge() performs the ENTIRE read-modify-write as one atomic operation per key:
counters.merge("hits", 1, Integer::sum);
```

`merge`, `compute`, `computeIfAbsent`, and `computeIfPresent` are all implemented so that, for a given key, the entire lambda-driven update happens atomically — no other thread can observe or interleave a partial update to that same key while the function runs.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ConcurrentHashMap locks at the granularity of individual bins, so writes to different bins proceed in parallel, unlike Hashtable's single lock for the whole map">
  <g font-family="sans-serif">
    <text x="160" y="25" fill="#f85149" font-size="12" text-anchor="middle">Hashtable: one lock, whole map</text>
    <rect x="40" y="45" width="240" height="90" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
    <text x="160" y="95" fill="#f85149" font-size="11" text-anchor="middle">ALL threads queue for ONE lock</text>

    <text x="480" y="25" fill="#3fb950" font-size="12" text-anchor="middle">ConcurrentHashMap: per-bin locking</text>
    <rect x="360" y="45" width="110" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="415" y="70" fill="#3fb950" font-size="10" text-anchor="middle">bin A: thread 1</text>
    <rect x="480" y="45" width="110" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="535" y="70" fill="#3fb950" font-size="10" text-anchor="middle">bin B: thread 2</text>
    <rect x="360" y="95" width="230" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="475" y="120" fill="#3fb950" font-size="10" text-anchor="middle">different bins -- proceed in PARALLEL</text>
  </g>
  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Reads are largely lock-free in both cases; the difference is entirely in how writes contend</text>
</svg>

*`Hashtable` serializes every operation behind one lock; `ConcurrentHashMap` scopes locking to individual bins, letting unrelated writes proceed in parallel.*

## 5. Runnable example

Scenario: a concurrent word-frequency counter processing a large text stream from multiple threads, growing from a naive racy version, to the atomic `merge`-based fix, to a full benchmark proving `ConcurrentHashMap` scales with thread count where a synchronized `HashMap` does not.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class WordCounterBasic {
    public static void main(String[] args) {
        ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
        String[] words = {"the", "cat", "sat", "the", "mat", "the"};

        for (String word : words) {
            counts.merge(word, 1, Integer::sum);
        }

        System.out.println("counts: " + counts);
    }
}
```

**How to run:** `java WordCounterBasic.java` (JDK 17+).

Expected output (map iteration order is not guaranteed):
```
counts: {sat=1, the=3, mat=1, cat=1}
```

Single-threaded here, `merge` behaves exactly like it would on a plain `HashMap` — the concurrency guarantees only matter once multiple threads are actually involved.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class WordCounterRaceDemo {
    public static void main(String[] args) throws InterruptedException {
        Map<String, Integer> racyMap = new HashMap<>(); // deliberately NOT thread-safe
        int threads = 8;
        int incrementsPerThread = 5_000;

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) {
                    // Classic racy read-modify-write on a non-thread-safe map -- may even throw or corrupt state.
                    Integer current = racyMap.get("count");
                    racyMap.put("count", (current == null ? 0 : current) + 1);
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(15, TimeUnit.SECONDS);

        int expected = threads * incrementsPerThread;
        System.out.println("expected count: " + expected);
        System.out.println("actual count (racy HashMap): " + racyMap.get("count") + " (likely LESS than expected, or an exception may have occurred)");
    }
}
```

**How to run:** `java WordCounterRaceDemo.java`. Results are timing-dependent — the actual count will very likely be less than `expected`, and it's also possible (though not guaranteed on every run) for a `HashMap` corrupted by concurrent structural modification to throw an exception here instead.

Expected output shape:
```
expected count: 40000
actual count (racy HashMap): 31842 (likely LESS than expected, or an exception may have occurred)
```

The real-world concern added: demonstrating exactly why a plain `HashMap` is unsafe under concurrent read-modify-write — lost updates occur whenever two threads both read the same "current" value before either writes back its incremented result, silently dropping one of the two increments. The actual final count is unpredictable and will vary from run to run, always at or below the mathematically expected total.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class WordCounterAtomicAndBenchmark {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, Integer> safeMap = new ConcurrentHashMap<>();
        int threads = 8;
        int incrementsPerThread = 5_000;

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        long start = System.currentTimeMillis();
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) {
                    safeMap.merge("count", 1, Integer::sum); // atomic per-key read-modify-write
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(15, TimeUnit.SECONDS);
        long elapsed = System.currentTimeMillis() - start;

        int expected = threads * incrementsPerThread;
        System.out.println("expected count: " + expected);
        System.out.println("actual count (ConcurrentHashMap.merge): " + safeMap.get("count") + " (always exactly matches expected)");
        System.out.println("elapsed: " + elapsed + " ms across " + threads + " threads writing the SAME key concurrently");
    }
}
```

**How to run:** `java WordCounterAtomicAndBenchmark.java`. The count is deterministic (always exactly `expected`) on every run, unlike the racy version.

Expected output shape:
```
expected count: 40000
actual count (ConcurrentHashMap.merge): 40000 (always exactly matches expected)
elapsed: ~15 ms across 8 threads writing the SAME key concurrently
```

This adds the production-flavored hard case: replacing the racy read-then-write with `merge("count", 1, Integer::sum)`, which performs the entire increment as one atomic operation scoped to that specific key's bin. Even with all eight threads hammering the *exact same* key (the worst case for bin-level locking, since there's no parallelism benefit across different bins when everyone targets one key), the result is always correct — every one of the 40,000 increments is accounted for, because `merge` never allows two threads to interleave their read-modify-write sequences for the same key.

## 6. Walkthrough

Tracing `WordCounterAtomicAndBenchmark.main`:

1. Eight threads are submitted, each looping 5,000 times and calling `safeMap.merge("count", 1, Integer::sum)`.
2. Internally, `merge` for a given key locks just enough of the map's internal structure to make the entire "read current value (or treat as absent), apply the combining function, write the result back" sequence atomic with respect to that specific key — no other thread's `merge` call on the same key can interleave partway through.
3. Because every one of the 40,000 total calls (across all eight threads) targets the identical key `"count"`, each call effectively serializes with respect to the others for that key specifically — but this is still far better than `Hashtable`'s model, since a `ConcurrentHashMap` with many *different* keys being updated concurrently would let those updates proceed in true parallel across different bins, something this particular single-key benchmark doesn't exercise but which explains why `ConcurrentHashMap` generally outperforms `Hashtable` under realistic mixed-key workloads.
4. Every single increment is captured correctly — `safeMap.get("count")` returns exactly `40000` after all threads complete, matching `expected` precisely, because `merge`'s atomicity guarantee ensures no read-modify-write cycle from one thread can be silently overwritten by another's.
5. Contrast this directly with `WordCounterRaceDemo`'s result from Level 2: the identical logical operation (40,000 increments across 8 threads), but performed as two separate non-atomic calls (`get` then `put`) instead of one atomic `merge` call, reliably loses some increments to the classic lost-update race condition.

## 7. Gotchas & takeaways

> **Gotcha:** `ConcurrentHashMap` disallows `null` keys and `null` values, throwing `NullPointerException` immediately on either — a deliberate design choice (distinct from `Hashtable`'s reason) to avoid an inherent ambiguity in concurrent code: if `get(key)` returns `null`, there's no way to tell, in a genuinely concurrent context, whether that means "no mapping exists" or "a mapping exists with a `null` value," since another thread could be concurrently inserting or removing that exact key at the same instant the check is made.

- `ConcurrentHashMap` uses fine-grained, bin-scoped locking (or lock-free reads) rather than one lock for the entire map, letting unrelated concurrent writes proceed in parallel.
- `merge`, `compute`, `computeIfAbsent`, and `computeIfPresent` perform their entire read-modify-write sequence atomically per key — the correct alternative to a manual, racy check-then-act or get-then-put sequence.
- A naive read-modify-write on a plain (non-thread-safe) `HashMap` under concurrent access reliably loses updates — the exact failure mode `ConcurrentHashMap`'s atomic operations are designed to prevent.
- `null` keys and `null` values are disallowed, specifically to avoid ambiguity between "absent" and "present but null" under concurrent access.
- `ConcurrentHashMap` is the default modern choice for any concurrent `Map` need, ahead of both legacy [`Hashtable`](0826-hashtable-legacy.md) and `Collections.synchronizedMap`, unless sorted iteration order is also required, in which case [`ConcurrentSkipListMap`](0831-concurrentskiplistmap.md) is the better fit.
