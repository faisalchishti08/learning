---
card: java
gi: 683
slug: zgc-production-ready
title: ZGC production-ready
---

## 1. What it is

**Java 15** promoted the **Z Garbage Collector (ZGC)** from an **experimental** feature to a **production-ready, fully supported** garbage collector (JEP 377). ZGC had existed since Java 11 (Linux only, experimental) and gained macOS and Windows ports in Java 14 (also experimental, see [ZGC on macOS & Windows](0673-zgc-on-macos-windows.md)). This release removed the experimental designation entirely: from Java 15 onward, enabling ZGC no longer requires `-XX:+UnlockExperimentalVMOptions` — a single `-XX:+UseZGC` flag is enough, signaling that the JDK team considers ZGC's implementation stable and correctness-tested enough for production workloads.

## 2. Why & when

An "experimental" label on a garbage collector is a real signal to production operators: it means the JDK team isn't yet committing to its correctness or stability under all workloads, and many organizations' change-management policies simply forbid enabling experimental JVM features in production regardless of how well they seem to work in testing. Removing that label after roughly four years of real-world use (since Java 11), bug reports, and refinement across three operating systems reflects genuine confidence built up over that period, not just a marketing change — the underlying algorithm (region-based, colored-pointer, concurrent collection with sub-millisecond pause targets even on multi-terabyte heaps) hadn't fundamentally changed, but the accumulated production feedback justified the reclassification. Reach for `-XX:+UseZGC` without the experimental unlock flag whenever you're deploying a large-heap, low-pause-time-sensitive Java 15+ application — trading systems, real-time bidding platforms, large caches — where G1's occasionally longer pause times (even though generally acceptable) are a concern, and where your organization's policies previously blocked experimental features.

## 3. Core concept

```bash
# Java 11–14: ZGC required the experimental unlock flag
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx16g MyApp

# Java 15 onward: ZGC is production-ready, no unlock flag needed
java -XX:+UseZGC -Xmx16g MyApp
```

The collector's behavior is unchanged by this promotion — it's the same algorithm — but the shorter command line and the removed "experimental" status reflect a real, tested confidence milestone rather than a cosmetic difference.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZGC's journey from experimental on Linux in Java 11, to macOS and Windows in Java 14 (still experimental), to fully production-ready in Java 15">
  <rect x="10" y="60" width="180" height="80" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="85" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 11</text>
  <text x="100" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ZGC on Linux</text>
  <text x="100" y="122" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">EXPERIMENTAL</text>

  <rect x="230" y="60" width="180" height="80" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="85" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 14</text>
  <text x="320" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">+ macOS, Windows</text>
  <text x="320" y="122" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">still EXPERIMENTAL</text>

  <rect x="450" y="60" width="180" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="540" y="85" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 15</text>
  <text x="540" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">all 3 platforms</text>
  <text x="540" y="122" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">PRODUCTION-READY</text>
</svg>

The same collector, matured across three JDK releases from experimental-Linux-only to fully supported everywhere.

## 5. Runnable example

Scenario: confirming ZGC is active and production-flagged, then running an allocation-heavy workload while logging pause times to observe ZGC's sub-millisecond pause characteristic, then a more realistic long-running service simulation that logs pause statistics periodically — the kind of check an operator would script before trusting ZGC in a production rollout.

### Level 1 — Basic

```java
// File: ZgcConfirm.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;

public class ZgcConfirm {
    public static void main(String[] args) {
        for (GarbageCollectorMXBean bean : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.println("Active collector: " + bean.getName());
        }
    }
}
```

**How to run (Java 15+, no experimental unlock flag needed):**
```
java -XX:+UseZGC ZgcConfirm.java
```

Expected output (Java 15's original single-generation ZGC exposes one bean named `ZGC`; later JDKs that default to generational ZGC split it into `ZGC Cycles` and `ZGC Pauses` — either way, the bean name(s) contain `"ZGC"`):
```
Active collector: ZGC Cycles
Active collector: ZGC Pauses
```

### Level 2 — Intermediate

```java
// File: ZgcPauseWorkload.java
import java.util.ArrayList;
import java.util.List;

public class ZgcPauseWorkload {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.currentTimeMillis();

        for (int round = 0; round < 30; round++) {
            for (int i = 0; i < 40_000; i++) {
                retained.add(new byte[1024]);
                if (retained.size() > 30_000) retained.remove(0);
            }
        }

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Workload finished in " + elapsed + " ms, retained: " + retained.size());
    }
}
```

**How to run with GC pause logging:**
```
java -XX:+UseZGC -Xlog:gc,gc+phases -Xmx1g ZgcPauseWorkload.java
```

Expected output shape (individual pause phases logged; each is characteristically sub-millisecond):
```
[0.031s][info][gc,phases] Pause Mark Start 0.312ms
[0.045s][info][gc,phases] Pause Mark End 0.198ms
[0.089s][info][gc,phases] Pause Relocate Start 0.287ms
...
Workload finished in 214 ms, retained: 30000
```

### Level 3 — Advanced

```java
// File: ZgcLongRunningCheck.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.ArrayList;
import java.util.List;

public class ZgcLongRunningCheck {
    public static void main(String[] args) throws InterruptedException {
        // Match by "contains" rather than exact equality: Java 15's original
        // ZGC exposes one bean named "ZGC"; later JDKs that default to
        // generational ZGC split it into "ZGC Cycles" and "ZGC Pauses".
        List<GarbageCollectorMXBean> zgcBeans = ManagementFactory.getGarbageCollectorMXBeans().stream()
                .filter(b -> b.getName().contains("ZGC"))
                .toList();

        if (zgcBeans.isEmpty()) {
            System.out.println("ZGC not active — start with -XX:+UseZGC");
            return;
        }
        System.out.println("ZGC confirmed active. Starting simulated service workload...");

        List<byte[]> cache = new ArrayList<>();
        for (int tick = 1; tick <= 5; tick++) {
            for (int i = 0; i < 100_000; i++) {
                cache.add(new byte[512]);
                if (cache.size() > 50_000) cache.remove(0);
            }
            long totalCollections = zgcBeans.stream().mapToLong(GarbageCollectorMXBean::getCollectionCount).sum();
            long totalTime = zgcBeans.stream().mapToLong(GarbageCollectorMXBean::getCollectionTime).sum();
            System.out.printf("Tick %d: GC collections so far=%d, total GC time=%dms%n",
                    tick, totalCollections, totalTime);
        }
        System.out.println("Simulated service run complete. Cache size: " + cache.size());
    }
}
```

**How to run:**
```
java -XX:+UseZGC -Xmx2g ZgcLongRunningCheck.java
```

Expected output shape from an actual run (the exact tick at which counts jump, and the precise values, depend on machine speed, heap size, and JDK version — collection may not even trigger every tick — but the counters are always non-decreasing and the total GC time stays a tiny fraction of the wall-clock run time):
```
ZGC confirmed active. Starting simulated service workload...
Tick 1: GC collections so far=0, total GC time=0ms
Tick 2: GC collections so far=0, total GC time=0ms
Tick 3: GC collections so far=4, total GC time=7ms
Tick 4: GC collections so far=4, total GC time=7ms
Tick 5: GC collections so far=4, total GC time=7ms
Simulated service run complete. Cache size: 50000
```

Level 3 simulates the shape of a real long-running service check: verify the collector at startup, then periodically sample `GarbageCollectorMXBean.getCollectionCount()` and `getCollectionTime()` — the kind of lightweight, ongoing production monitoring an operations team would build around any collector, now reasonable to rely on for ZGC given its production-ready status.

## 6. Walkthrough

1. `main` first confirms ZGC is active by filtering `ManagementFactory.getGarbageCollectorMXBeans()` for beans whose name **contains** `"ZGC"` — the same technique used throughout this collector's evolution, now running with just `-XX:+UseZGC` and no experimental unlock flag, itself a small piece of evidence of the production-ready status this release conferred. Matching by `contains` rather than exact equality keeps the check working whether the running JDK exposes a single `"ZGC"` bean (as Java 15's original design did) or splits it into separate `"ZGC Cycles"` / `"ZGC Pauses"` beans (as later generational-ZGC JDKs do).
2. If no matching beans are found, the program exits early with a hint; otherwise, it keeps the list `zgcBeans` of every matching bean, since there may be more than one.
3. The main loop runs 5 "ticks," each simulating a burst of request-processing allocation: 100,000 small `byte[512]` allocations per tick, with a bounded `cache` list (capped at 50,000 entries via `remove(0)` eviction) standing in for something like an LRU or session cache a real service might maintain.
4. After each tick's allocation burst, the code sums `getCollectionCount()` and `getCollectionTime()` across all matching beans and prints the totals — these are cumulative counters (total collections and total time spent collecting since JVM startup), so their values never decrease, though they may stay flat for a tick or two if the heap hasn't yet filled enough to trigger a cycle, then jump once ZGC's concurrent cycle actually runs and completes.
5. Because ZGC performs almost all of its work concurrently (marking, relocating) with only very short synchronization pauses, the `total GC time` accumulated across all five ticks stays a tiny fraction — typically single-digit milliseconds — of the wall-clock time the workload actually took to allocate and evict half a million small buffers; this is the qualitative signature of ZGC's design that motivated its promotion to production-ready: applications keep running while collection happens in the background.
6. After the fifth tick, `main` prints the final `cache.size()`, confirming the bounded-cache logic behaved as expected (staying at the 50,000 cap) throughout the entire run, with garbage collection having kept up transparently in the background the whole time.

```
startup ──► confirm ZGC active (GarbageCollectorMXBean)
               │
               ▼
   for each tick: allocate burst ──► ZGC collects concurrently (background)
               │
               ▼
       sample cumulative collectionCount / collectionTime
               │
               ▼
        repeat until service workload completes
```

## 7. Gotchas & takeaways

> "Production-ready" describes the JDK team's confidence in ZGC's **correctness and stability**, not a guarantee that it's the *best* collector for every workload. G1 remains the default collector and is the right choice for many applications; ZGC specifically targets very large heaps and strict low-pause-time requirements — benchmark your actual workload before switching a production service's default collector.

- From Java 15 onward, `-XX:+UseZGC` alone is sufficient — omit `-XX:+UnlockExperimentalVMOptions`; including it is now unnecessary (though harmless) for ZGC specifically.
- ZGC's promotion in Java 15 covered Linux, macOS, and Windows uniformly, since [the macOS/Windows ports themselves shipped experimental in Java 14](0673-zgc-on-macos-windows.md) and matured alongside Linux's longer-standing support.
- ZGC is generational (splitting young and old generations) only from a later JDK version onward — the Java 15 production-ready ZGC is the original single-generation design; don't assume generational behavior when reading pause statistics from this era.
- Always verify the active collector via `GarbageCollectorMXBean` in any automated check or benchmark script — a misspelled or unsupported flag can silently be ignored by some JVM configurations, leaving a different collector active than intended.
- Production-ready status typically also affects vendor support policies (some JDK distributions or enterprise support contracts explicitly exclude experimental features from supported configurations) — check your JDK vendor's support matrix if that matters for your deployment.
