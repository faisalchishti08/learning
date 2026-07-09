---
card: java
gi: 793
slug: compact-object-headers-experimental
title: Compact object headers (experimental)
---

## 1. What it is

**Java 24** (JEP 450) adds an **experimental** option, `-XX:+UseCompactObjectHeaders`, that shrinks the per-object header every Java object carries from its traditional size (12 or 16 bytes, depending on JVM configuration) down to **8 bytes**. Every single object on the heap — every `String`, every `ArrayList` node, every small wrapper object — carries a header the JVM uses to track its class, hash code, lock state, and GC-related bits; compacting that header directly reduces heap memory usage and improves cache density, with no change to Java-level object semantics at all.

## 2. Why & when

Object headers are pure overhead from an application's point of view — they carry no data the program itself asked for — but they exist on *every* object, so their size compounds directly with allocation-heavy workloads. A program allocating millions of small objects (a common pattern with immutable value types, small records, boxed primitives, or short-lived collection nodes) pays that header cost millions of times over, and a smaller header means more actual object data fits in the same amount of CPU cache, on top of the direct heap-size reduction. This became newly practical because of groundwork laid by earlier JVM changes (increasingly compact class-pointer encoding and simplified locking metadata), letting the JVM team compress what used to require two 8-byte words (the mark word for hashcode/lock state, and the class pointer) down into a single 8-byte word. It's marked experimental because it changes a very low-level, pervasive JVM data structure — the kind of change that benefits from broad real-world testing before being trusted as a default, given how deeply object headers are woven into the JVM's internals (locking, garbage collection, JIT-compiled code assumptions).

## 3. Core concept

```
# Traditional object headers (12 or 16 bytes per object, JVM-configuration dependent)
java MyApp

# Experimental compact object headers (8 bytes per object)
java -XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders MyApp
```

No source code changes anywhere — this is a pure JVM-internals change, observable only via memory usage and, indirectly, performance on allocation-heavy workloads.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Compact object headers shrink the per-object overhead every Java object carries from twelve or sixteen bytes down to eight bytes, with no change to Java-level object semantics">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="160" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Traditional header</text>
  <text x="160" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mark word (8B) + class pointer (4-8B)</text>
  <text x="160" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">= 12-16 bytes per object</text>

  <rect x="340" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Compact header (experimental)</text>
  <text x="480" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">everything packed into 1 word</text>
  <text x="480" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">= 8 bytes per object</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The savings multiply by every object ever allocated — biggest impact on small-object-heavy workloads</text>
</svg>

*A pure per-object overhead reduction, invisible at the Java source level but measurable in heap footprint.*

## 5. Runnable example

Scenario: an allocation-heavy workload of many small objects, growing from measuring raw memory usage into a direct before/after comparison of heap footprint with compact headers enabled.

### Level 1 — Basic

```java
import java.util.*;

public class CompactHeadersBasic {
    record Point(int x, int y) {} // a small, header-dominated object

    public static void main(String[] args) {
        List<Point> points = new ArrayList<>();
        for (int i = 0; i < 5_000_000; i++) {
            points.add(new Point(i, i * 2));
        }
        System.out.println("allocated " + points.size() + " points");
        System.out.println("free memory: " + Runtime.getRuntime().freeMemory() / 1_000_000 + " MB");
    }
}
```

**How to run:** `java -Xmx1g CompactHeadersBasic.java` (JDK 24+; run once with default headers to establish a baseline).

Five million small `Point` records, each holding just two `int` fields (8 bytes of actual data) but carrying a full object header on top — a textbook case where header overhead is a large fraction of each object's total size.

### Level 2 — Intermediate

```java
import java.util.*;

public class CompactHeadersMeasured {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        Runtime rt = Runtime.getRuntime();
        System.gc(); // request a collection to get a cleaner baseline reading
        long before = rt.totalMemory() - rt.freeMemory();

        List<Point> points = new ArrayList<>();
        for (int i = 0; i < 5_000_000; i++) {
            points.add(new Point(i, i * 2));
        }

        long after = rt.totalMemory() - rt.freeMemory();
        System.out.println("approx. heap used by 5,000,000 Points: "
            + (after - before) / 1_000_000 + " MB");
        System.out.println("bytes per Point (approx): "
            + (after - before) / points.size());
    }
}
```

**How to run — compare the two header modes directly:**
```
java -Xmx1g CompactHeadersMeasured.java
java -Xmx1g -XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders CompactHeadersMeasured.java
```

The real-world concern added: an actual, if approximate, **measurement** of per-object memory cost via `Runtime.totalMemory()`/`freeMemory()` before and after the allocation loop — run twice, with and without `-XX:+UseCompactObjectHeaders`, the reported "bytes per Point" should be measurably smaller in the compact-header run, giving concrete evidence of the improvement rather than taking it on faith.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class CompactHeadersConcurrentCache {
    record CacheEntry(int key, long value, long timestamp) {}

    static final ConcurrentHashMap<Integer, CacheEntry> cache = new ConcurrentHashMap<>();

    public static void main(String[] args) throws InterruptedException {
        Runtime rt = Runtime.getRuntime();
        System.gc();
        long before = rt.totalMemory() - rt.freeMemory();

        long start = System.nanoTime();
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 2_000_000; i++) {
                int key = i;
                executor.submit(() ->
                    cache.put(key, new CacheEntry(key, key * 100L, System.nanoTime())));
            }
        }
        double seconds = (System.nanoTime() - start) / 1e9;

        long after = rt.totalMemory() - rt.freeMemory();
        System.out.printf("populated %,d cache entries in %.2fs%n", cache.size(), seconds);
        System.out.println("approx. heap used: " + (after - before) / 1_000_000 + " MB");
    }
}
```

**How to run:**
```
java -Xmx2g CompactHeadersConcurrentCache.java
java -Xmx2g -XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders CompactHeadersConcurrentCache.java
```

This adds the production-flavored hard case: a **concurrent** cache populated by 2,000,000 virtual-thread-backed tasks, each inserting a small `CacheEntry` record — a shape much closer to a real in-memory cache under concurrent load — measuring both memory footprint and, indirectly, whether the reduced header size (and correspondingly better CPU cache density) has any measurable effect on wall-clock throughput for a workload this allocation-heavy.

## 6. Walkthrough

Tracing `CompactHeadersConcurrentCache.main` under compact headers:

1. `main` requests a garbage collection and records a baseline heap-usage figure via `Runtime.totalMemory() - Runtime.freeMemory()`.
2. It opens a virtual-thread-per-task executor and submits 2,000,000 tasks, each constructing a `CacheEntry` record (three `long`/`int`-ish fields) and inserting it into a shared `ConcurrentHashMap` keyed by an integer.
3. Each `CacheEntry` object, regardless of header mode, carries the same three fields' worth of actual data — but under `-XX:+UseCompactObjectHeaders`, each one's header consumes 8 bytes instead of 12-16, and the `Integer` keys and `ConcurrentHashMap` internal node objects benefit the same way, since *every* object on the heap gets the smaller header, not just `CacheEntry` itself.
4. Once all 2,000,000 submissions complete, `main` measures elapsed time and heap usage again, computing the difference from the baseline.
5. `main` prints the entry count, elapsed time, and approximate heap consumed — comparing this output between the two JVM invocations (with and without the experimental flag) is how the improvement becomes directly observable.

Expected output shape (exact numbers vary by machine and JDK build; the compact-header run should show measurably lower approximate heap usage for the same 2,000,000 entries):
```
populated 2,000,000 cache entries in 1.2Xs
approx. heap used: 210 MB
```

## 7. Gotchas & takeaways

> **Gotcha:** `Runtime.totalMemory()`/`freeMemory()`-based measurements are approximate — JVM heap growth, garbage collection timing, and JIT warmup all introduce noise, so treat single-run numbers as directional, not precise. For rigorous before/after comparisons, run each configuration multiple times, request explicit `System.gc()` calls at consistent points, and consider a dedicated memory-profiling tool rather than relying solely on `Runtime`'s coarse figures.

- Experimental in Java 24 (JEP 450) — requires `-XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders`.
- Shrinks every object's header from 12-16 bytes down to 8 bytes, with **zero** Java-level semantic change — no source code is affected.
- Biggest impact on workloads allocating many small objects (records, boxed primitives, small collection nodes), where header overhead is a large fraction of total object size.
- Also improves CPU cache density indirectly, since more actual object data fits in the same cache line/page when headers are smaller.
- Being experimental and touching such a low-level, pervasive JVM structure, it warrants careful evaluation on your own workload before production adoption, and its stability/default status may change in future JDK releases.
