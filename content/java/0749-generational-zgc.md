---
card: java
gi: 749
slug: generational-zgc
title: Generational ZGC
---

## 1. What it is

**Java 21** (JEP 439) adds a **generational mode** to the Z Garbage Collector (ZGC), enabled with `-XX:+UseZGC -XX:+ZGenerational` (this became the default ZGC mode in a later release). Generational ZGC splits the heap into a **young generation** for newly allocated, short-lived objects and an **old generation** for objects that have survived multiple collections — applying the well-established "generational hypothesis" (most objects die young) to ZGC's design, which previously treated the whole heap as a single, ungenerationed space. The result is significantly reduced CPU overhead and higher throughput for the same ultra-low pause times ZGC was already known for.

## 2. Why & when

Before generational mode, ZGC already delivered its headline feature — pause times measured in **single-digit milliseconds**, independent of heap size, even at multi-terabyte heaps — by doing almost all of its work concurrently with the running application. But treating the entire heap as one region meant every collection cycle had to scan the *whole* heap for garbage, including old, long-lived objects that were extremely unlikely to have become garbage since the last cycle. Most real workloads follow the generational hypothesis: the overwhelming majority of objects (request-scoped buffers, temporary collections, short-lived local objects) die almost immediately, while a small fraction (caches, connection pools, long-lived singletons) survive indefinitely. Generational ZGC exploits this by collecting the young generation far more frequently and cheaply (it's usually mostly garbage, so there's little live data to preserve) and the old generation much less often — cutting the total CPU work ZGC needs to do to keep pace with allocation, without giving up any of the sub-millisecond-pause guarantee. This matters for any latency-sensitive service running on ZGC where CPU headroom, not just pause time, is a real constraint — trading collector CPU overhead for the same pause-time floor is a straightforward win once your workload matches the generational assumption (which most do).

## 3. Core concept

```
# Enable generational ZGC (JEP 439, Java 21+; became the default in later JDKs)
java -XX:+UseZGC -XX:+ZGenerational -Xmx4g -Xlog:gc MyApp

# Compare against non-generational (single-generation) ZGC
java -XX:+UseZGC -XX:-ZGenerational -Xmx4g -Xlog:gc MyApp
```

Both modes share ZGC's pause-time characteristics; the flag only changes **how much work** the collector does per unit of allocation, which shows up as CPU usage and GC log frequency, not as observable pause-time differences in the application.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Generational ZGC splits the heap into a frequently collected young generation and a rarely collected old generation, reducing total collector work versus scanning the whole heap every cycle">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Non-generational ZGC: every cycle scans the ENTIRE heap</text>

  <rect x="20" y="90" width="260" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="112" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Young generation</text>
  <text x="150" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">collected often, mostly garbage, cheap</text>

  <rect x="300" y="90" width="320" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="460" y="112" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Old generation</text>
  <text x="460" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">collected rarely, mostly live, skipped most cycles</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same sub-millisecond pause times, less total CPU work per byte allocated</text>
</svg>

*Generational ZGC focuses frequent, cheap collections on the generation most likely to hold garbage.*

## 5. Runnable example

Scenario: an allocation-heavy service simulation, growing from a naive allocator into a workload shaped like real generational behavior, with GC configuration to match.

### Level 1 — Basic

```java
import java.util.*;

public class AllocateBasic {
    public static void main(String[] args) {
        List<byte[]> shortLived;
        for (int round = 0; round < 200_000; round++) {
            shortLived = new ArrayList<>();
            for (int i = 0; i < 10; i++) {
                shortLived.add(new byte[1024]); // 1 KB temporary buffers
            }
            // shortLived goes out of scope here — becomes garbage almost immediately
        }
        System.out.println("done allocating");
    }
}
```

**How to run:** `java -Xmx256m AllocateBasic.java` (JDK 21+; works with any GC, no special flags yet).

This allocates 2,000,000 short-lived 1 KB buffers total, each batch of ten discarded at the end of every loop iteration — a textbook "most objects die young" workload, though nothing here yet chooses or configures a specific collector.

### Level 2 — Intermediate

```java
import java.util.*;

public class AllocateWithSurvivors {
    static final List<byte[]> longLivedCache = new ArrayList<>();

    public static void main(String[] args) {
        for (int round = 0; round < 200_000; round++) {
            List<byte[]> shortLived = new ArrayList<>();
            for (int i = 0; i < 10; i++) {
                shortLived.add(new byte[1024]);
            }
            if (round % 1000 == 0) {
                longLivedCache.add(new byte[1024]); // occasionally, something survives
            }
        }
        System.out.println("cache size (long-lived survivors): " + longLivedCache.size());
    }
}
```

**How to run:** `java -Xmx256m -XX:+UseZGC -XX:+ZGenerational -Xlog:gc AllocateWithSurvivors.java`.

The real-world concern added: a small `longLivedCache` that accumulates a handful of survivors (200 objects total, one per 1,000 rounds) alongside the flood of short-lived garbage — mirroring a real service's mix of request-scoped temporaries and a small long-lived cache. Running with `-Xlog:gc` prints ZGC's cycle log lines, showing frequent young-generation collections and far rarer old-generation ones.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class AllocateProduction {
    static final Map<Integer, byte[]> connectionPool = new ConcurrentHashMap<>();

    static void handleRequest(int requestId) {
        // request-scoped, short-lived allocations — the bulk of GC pressure
        List<byte[]> buffers = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            buffers.add(new byte[2048]);
        }
        // simulate occasional long-lived connection registration
        if (requestId % 5000 == 0) {
            connectionPool.put(requestId, new byte[4096]);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.nanoTime();
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 500_000; i++) {
                int requestId = i;
                executor.submit(() -> handleRequest(requestId));
            }
        }
        double seconds = (System.nanoTime() - start) / 1e9;
        System.out.printf("processed 500,000 requests in %.2fs, cache entries=%d%n",
            seconds, connectionPool.size());
    }
}
```

**How to run:**
```
java -Xmx512m -XX:+UseZGC -XX:+ZGenerational -Xlog:gc:file=gen.log AllocateProduction.java
java -Xmx512m -XX:+UseZGC -XX:-ZGenerational -Xlog:gc:file=nongen.log AllocateProduction.java
```

This adds the production-flavored hard case: 500,000 concurrent virtual-thread-backed requests (combining with [virtual threads — standardized](0739-virtual-threads-standardized.md)), each allocating a burst of short-lived buffers and occasionally registering a long-lived entry in a shared `ConcurrentHashMap` — then comparing GC log output between generational and non-generational ZGC to see the difference in collection frequency and total logged GC CPU time directly, rather than just taking the improvement on faith.

## 6. Walkthrough

Tracing what happens during one run of `AllocateProduction` under generational ZGC:

1. `main` starts a timer, then opens a virtual-thread-per-task executor and submits 500,000 tasks, each calling `handleRequest(requestId)`.
2. Each `handleRequest` call allocates 20 short-lived `byte[2048]` buffers into a local `ArrayList` that goes out of scope the moment the method returns — this is the overwhelming majority of all allocation in the program, and virtually all of it becomes garbage within microseconds of being created.
3. Every 5,000th request additionally inserts a `byte[4096]` entry into `connectionPool`, a `ConcurrentHashMap` that lives for the entire run — a small trickle of genuinely long-lived allocation representing, say, persistent connection state.
4. Under the hood, generational ZGC's young-generation collector runs frequently and cheaply: because the young generation fills almost entirely with the request-scoped buffers that die within microseconds, most young-generation collection cycles find very little live data to preserve, so each cycle finishes fast and the collector rarely needs to touch the old generation at all.
5. The rare `connectionPool` entries that survive several young-generation collections get **promoted** to the old generation, which is scanned far less often — exactly the behavior the generational hypothesis predicts, and exactly what `-Xlog:gc` output would show as a low ratio of old-generation to young-generation collection cycles.
6. Once all 500,000 submitted tasks complete, the try-with-resources block's implicit `executor.close()` returns, `main` computes elapsed time, and prints the final summary line.

Expected output shape (exact timing varies by machine):
```
processed 500,000 requests in 1.8Xs, cache entries=100
```

Comparing `gen.log` against `nongen.log` (from the two commands above) would show the generational run logging **more young-generation cycles but far less total scanned-heap work per cycle**, and typically a lower overall GC CPU percentage for the same workload — the concrete, measurable form of "generational ZGC does less total work for the same pause-time guarantee."

## 7. Gotchas & takeaways

> **Gotcha:** generational ZGC's benefit is proportional to how well a workload actually matches the generational hypothesis. A workload that allocates huge, long-lived objects directly (skipping a "young" phase entirely — e.g., loading a multi-gigabyte dataset once at startup and holding it for the process lifetime) sees little advantage from generational mode, since there's no flood of young garbage for the young-generation collector to reclaim cheaply.

- Enable with `-XX:+UseZGC -XX:+ZGenerational` on Java 21 (later JDKs made this the default ZGC behavior — check your JDK version's release notes before assuming the flag is still needed).
- Generational ZGC keeps the same sub-millisecond pause-time guarantee as non-generational ZGC; the improvement is in **CPU overhead and throughput**, not pause latency.
- Best suited to workloads matching the generational hypothesis: lots of short-lived allocation, a smaller amount of long-lived state — true of most request/response and event-processing services.
- Use `-Xlog:gc` (or a dedicated log file via `-Xlog:gc:file=...`) to observe collection frequency and cycle cost directly rather than assuming the improvement applies to your workload.
- Combine with [virtual threads](0739-virtual-threads-standardized.md) carefully: massive concurrency means massive allocation concurrency too, which is exactly the scenario generational GC design is meant to absorb efficiently.
