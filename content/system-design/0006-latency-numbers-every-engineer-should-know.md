---
card: system-design
gi: 6
slug: latency-numbers-every-engineer-should-know
title: Latency numbers every engineer should know
---

## 1. What it is

**Latency** is the time it takes for one operation to complete — reading from memory, reading from disk, or sending data across a network. "Latency numbers every engineer should know" is a well-known reference table (popularized by Jeff Dean at Google) of roughly how long common operations take, from a memory access (nanoseconds) to a round trip across the world (hundreds of milliseconds).

Think of it as a engineer's version of knowing that walking a mile takes about 20 minutes, while driving it takes about 2: knowing the rough speed of each mode of transport lets you judge quickly whether a plan is realistic.

## 2. Why & when

You use these numbers to judge, on the spot, whether a design choice is fast enough — and to explain *why* one design is faster than another. If reading from an in-memory cache takes about 1 microsecond and reading from disk takes about 1,000 times longer, you can justify adding a cache with a real number instead of a vague "caching is faster". These numbers also explain why a network call across data centers dominates a request's total latency far more than any in-process computation does.

You reach for this table whenever you are deciding where data should live (memory, disk, cache, another region) or estimating the total latency of a request that touches several components.

## 3. Core concept

**The approximate numbers, in increasing order (values vary by hardware, but the relative gaps matter more than exact numbers):**

| Operation | Approx. latency |
|---|---|
| L1 cache reference | ~1 nanosecond (ns) |
| Main memory (RAM) reference | ~100 ns |
| Read 1 MB sequentially from RAM | ~10 microseconds (µs) |
| Round trip within the same data center | ~500 µs (0.5 ms) |
| Read 1 MB sequentially from SSD | ~1 ms |
| Disk seek (spinning disk) | ~10 ms |
| Read 1 MB sequentially from a spinning disk | ~20 ms |
| Round trip between two continents (e.g. US ↔ Europe) | ~150 ms |

**The rule this table teaches:** each step down the table is roughly 10 to 1,000 times slower than the step above it. Memory is fast; disk is slow; the network, especially across a long distance, is by far the slowest. This is why caching (keeping data in RAM instead of on disk) and placing servers close to users (reducing network distance) are two of the most powerful levers in system design — they attack the two biggest gaps in this table.

## 4. Diagram

```
 L1 cache        |*  1 ns
 RAM              |*  100 ns
 same-DC round trip    |------*  500,000 ns (0.5 ms)
 SSD read (1MB)         |-------*  1,000,000 ns (1 ms)
 disk seek                |----------*  10,000,000 ns (10 ms)
 cross-continent round trip    |--------------------------* 150,000,000 ns (150 ms)

 (log-scale sketch: each * is roughly 10-1000x further right than the one above)
```
*Caption: latency spans nine orders of magnitude from L1 cache to a cross-continent network round trip.*

## 5. Runnable example

### Artifact: a Java program that estimates total request latency across components

```java
import java.util.*;

public class LatencyEstimator {

    // Approximate latencies in nanoseconds.
    static final long L1_CACHE_NS = 1L;
    static final long RAM_NS = 100L;
    static final long SAME_DC_ROUND_TRIP_NS = 500_000L;         // 0.5 ms
    static final long SSD_READ_1MB_NS = 1_000_000L;             // 1 ms
    static final long DISK_SEEK_NS = 10_000_000L;                // 10 ms
    static final long CROSS_CONTINENT_ROUND_TRIP_NS = 150_000_000L; // 150 ms

    public static void main(String[] args) {
        // Scenario A: cache hit, same data center.
        long cacheHitPath = SAME_DC_ROUND_TRIP_NS + RAM_NS;

        // Scenario B: cache miss, read from SSD, same data center.
        long cacheMissPath = SAME_DC_ROUND_TRIP_NS + SSD_READ_1MB_NS + DISK_SEEK_NS;

        // Scenario C: cache miss, and the user is on another continent.
        long worstCasePath = CROSS_CONTINENT_ROUND_TRIP_NS + SSD_READ_1MB_NS + DISK_SEEK_NS;

        System.out.printf("Cache hit, same DC:        %.2f ms%n", cacheHitPath / 1_000_000.0);
        System.out.printf("Cache miss, same DC:       %.2f ms%n", cacheMissPath / 1_000_000.0);
        System.out.printf("Cache miss, cross-continent: %.2f ms%n", worstCasePath / 1_000_000.0);
    }
}
```

**How to run:** save as `LatencyEstimator.java`, run `java LatencyEstimator.java` (JDK 17+).

## 6. Walkthrough

1. The constants at the top encode the reference table's numbers, in nanoseconds, so all arithmetic stays in one unit.
2. `cacheHitPath` models a request that finds its data already in a same-data-center cache: one network round trip plus a fast RAM read.
3. `cacheMissPath` models a request that must fall back to reading from SSD, adding a disk seek and an SSD read on top of the same network round trip.
4. `worstCasePath` models the worst realistic case: the user is on another continent, and the cache still misses.
5. Output:
```
Cache hit, same DC:        0.50 ms
Cache miss, same DC:       11.50 ms
Cache miss, cross-continent: 161.00 ms
```
6. The gap between the first and third numbers, roughly 320x, is the concrete argument for two design moves: cache hot data in memory, and place servers near users. Both attack the largest terms in this sum.

## 7. Gotchas & takeaways

> **Gotcha:** engineers often assume computation time dominates a request's latency. In reality, network round trips and disk access dominate almost every real request; the actual CPU work is usually the smallest term in the sum.

- Memorize the rough shape of the table (nanoseconds for memory, microseconds/milliseconds for disk, tens to hundreds of milliseconds for network), not the exact numbers.
- Use this table to justify caching and geographic placement decisions with real numbers, not vague claims.
- When estimating a request's total latency, add up every hop: network in, any disk reads, any downstream service calls, network out.
