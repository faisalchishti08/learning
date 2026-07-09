---
card: java
gi: 610
slug: g1-as-default-gc-from-9
title: G1 as default GC (from 9)
---

## 1. What it is

Starting with JDK 9, the **Garbage-First (G1)** garbage collector became the default GC on server-class machines (those with 2+ CPUs and 2+ GB RAM, which covers virtually all modern servers and developer workstations). Before JDK 9, the default was the Parallel GC (throughput collector), which prioritised raw throughput at the expense of pause times. G1 prioritises predictable, low-latency pause times by dividing the heap into equal-sized regions and performing incremental, concurrent collection — aiming to keep GC pauses below a configurable target (default: 200 ms).

## 2. Why & when

The Parallel GC was optimised for batch processing — maximum throughput, with little regard for pause times. Pauses could stretch into multiple seconds for large heaps because the entire young generation (or worse, the entire heap for a full GC) was collected in one stop-the-world event. As Java shifted from batch processing to interactive services (web servers, microservices, real-time data pipelines), predictable pause times became more important than raw throughput. G1 addresses this by breaking the heap into ~2048 regions and collecting only a subset of regions in each pause — the "garbage-first" strategy targets regions with the most garbage, maximising reclaimed memory per pause while staying within a configurable pause-time target (`-XX:MaxGCPauseMillis`).

## 3. Core concept

```
Heap layout under G1 (simplified):

┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ E │ E │ S │ S │ O │ O │ H │ F │ F │ F │  ...
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  ↑   ↑   ↑       ↑       ↑       ↑
  Eden Survivor  Old    Humongous  Free

Regions: equal-sized chunks (~1–32 MB each, ~2048 total)
G1 cycle: Young-only → Mixed (young + some old) → Concurrent marking
Pause target: -XX:MaxGCPauseMillis=200 (default)
```

G1's heap is a set of equally sized regions. Each region can be Eden, Survivor, Old, Humongous (for large objects spanning multiple regions), or Free. A G1 collection cycle has three phases: (1) Young-only collections (fast, frequent, collects Eden + Survivor), (2) Concurrent marking (runs in the background while the application runs, identifies regions with the most garbage), and (3) Mixed collections (collects young regions plus a subset of old regions, chosen to maximise reclamation while staying within the pause target).

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="G1 GC divides the heap into regions and does incremental, targeted collection">
  <rect x="20" y="10" width="560" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">G1 Heap: ~2048 regions, each 1–32 MB</text>

  <rect x="30" y="48" width="40" height="28" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="50" y="67" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">E</text>
  <rect x="72" y="48" width="40" height="28" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="92" y="67" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">E</text>
  <rect x="114" y="48" width="40" height="28" rx="3" fill="#0d1117" stroke="#79c0ff"/>
  <text x="134" y="67" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">S</text>
  <rect x="156" y="48" width="60" height="28" rx="3" fill="#0d1117" stroke="#f0883e"/>
  <text x="186" y="67" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">Old</text>
  <rect x="218" y="48" width="60" height="28" rx="3" fill="#0d1117" stroke="#f0883e"/>
  <text x="248" y="67" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">Old</text>
  <rect x="280" y="48" width="60" height="28" rx="3" fill="#0d1117" stroke="#f0883e"/>
  <text x="310" y="67" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">Old*</text>
  <rect x="342" y="48" width="60" height="28" rx="3" fill="#8b949e" stroke="#8b949e" opacity="0.5"/>
  <text x="372" y="67" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Free</text>
  <rect x="404" y="48" width="60" height="28" rx="3" fill="#8b949e" stroke="#8b949e" opacity="0.5"/>
  <text x="434" y="67" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Free</text>
  <text x="470" y="67" fill="#8b949e" font-size="9" font-family="monospace">...</text>

  <text x="30" y="105" fill="#6db33f" font-size="10" font-family="sans-serif">E=Eden  S=Survivor  Old=Tenured  Old*=target region (most garbage)</text>

  <text x="30" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">Young collection (frequent, fast):</text>
  <text x="30" y="148" fill="#8b949e" font-size="9" font-family="monospace">  Collect E+S → promote survivors to Old → keep pause under target</text>

  <text x="30" y="170" fill="#8b949e" font-size="10" font-family="sans-serif">Mixed collection (less frequent):</text>
  <text x="30" y="188" fill="#8b949e" font-size="9" font-family="monospace">  Collect E+S + selected Old(*) regions → reclaims the most garbage per pause</text>
</svg>

G1 targets the regions with the most garbage (the "garbage-first" regions) during mixed collections, maximising reclamation per pause.

## 5. Runnable example

Scenario: exploring GC configuration and behaviour — starting with checking which GC is in use, extending to configuring G1's pause-time target and observing its effect, and finally comparing GC collector options available in the JDK.

### Level 1 — Basic

```java
// File: G1DefaultDemo.java
import java.lang.management.*;
import java.util.*;

public class G1DefaultDemo {
    public static void main(String[] args) {
        System.out.println("=== G1: The Default GC (JDK 9+) ===\n");

        // Check which GC is active
        List<GarbageCollectorMXBean> gcBeans = ManagementFactory.getGarbageCollectorMXBeans();
        System.out.println("Active garbage collectors:");
        for (var gc : gcBeans) {
            System.out.printf("  %s (%s)%n",
                gc.getName(),
                String.join(", ", gc.getMemoryPoolNames()));
        }

        // G1 typically shows: "G1 Young Generation" and "G1 Old Generation"
        boolean isG1 = gcBeans.stream()
            .anyMatch(gc -> gc.getName().contains("G1"));
        System.out.println("\nUsing G1: " + isG1);

        if (isG1) {
            System.out.println("\nG1 is the default GC on server-class machines since JDK 9.");
            System.out.println("It replaced the Parallel GC (throughput collector).");
        }

        System.out.println("\nKey G1 flags:");
        System.out.println("  -XX:+UseG1GC            (force G1, but it's the default)");
        System.out.println("  -XX:MaxGCPauseMillis=200 (pause target, default 200ms)");
        System.out.println("  -XX:G1HeapRegionSize=4M  (region size, 1–32 MB)");
    }
}
```

**How to run:** `java G1DefaultDemo.java`

Expected output (varies by JVM configuration):
```
=== G1: The Default GC (JDK 9+) ===

Active garbage collectors:
  G1 Young Generation (G1 Eden Space, G1 Survivor Space, G1 Old Gen)
  G1 Old Generation (G1 Eden Space, G1 Survivor Space, G1 Old Gen)

Using G1: true

G1 is the default GC on server-class machines since JDK 9.
It replaced the Parallel GC (throughput collector).

Key G1 flags:
  -XX:+UseG1GC            (force G1, but it's the default)
  -XX:MaxGCPauseMillis=200 (pause target, default 200ms)
  -XX:G1HeapRegionSize=4M  (region size, 1–32 MB)
```

The simplest check: use `ManagementFactory.getGarbageCollectorMXBeans()` to identify which GC is active. On a server-class machine with JDK 9+, the output shows "G1 Young Generation" and "G1 Old Generation."

### Level 2 — Intermediate

```java
// File: G1Configuration.java
import java.util.*;
import java.util.stream.*;

public class G1Configuration {
    public static void main(String[] args) {
        System.out.println("=== G1 Configuration Options ===\n");

        System.out.println("Pause-time target:");
        System.out.println("  -XX:MaxGCPauseMillis=200");
        System.out.println("  G1 will try to keep pauses under 200ms (default).");
        System.out.println("  Lower it: -XX:MaxGCPauseMillis=50 (more aggressive, more CPU)");
        System.out.println("  Raise it: -XX:MaxGCPauseMillis=500 (less aggressive, better throughput)\n");

        System.out.println("Heap region size:");
        System.out.println("  -XX:G1HeapRegionSize=4M");
        System.out.println("  G1 divides the heap into ~2048 regions.");
        System.out.println("  Default is auto-calculated: heap size / 2048.");
        System.out.println("  Example: 8 GB heap → 8G/2048 ≈ 4 MB per region\n");

        System.out.println("Initiating heap occupancy (Mixed GC threshold):");
        System.out.println("  -XX:InitiatingHeapOccupancyPercent=45");
        System.out.println("  When old generation reaches 45% of heap, G1 starts");
        System.out.println("  concurrent marking to prepare for mixed collections.\n");

        System.out.println("Humongous object threshold:");
        System.out.println("  Objects larger than 50% of a region size");
        System.out.println("  are 'humongous' — allocated directly in old gen.");
        System.out.println("  (Default region = 4 MB → humongous = >2 MB object)\n");

        System.out.println("Concurrent GC threads:");
        System.out.println("  -XX:ConcGCThreads=2");
        System.out.println("  Number of threads for concurrent marking.");
        System.out.println("  Default: roughly 25% of ParallelGCThreads.\n");

        System.out.println("Parallel GC threads:");
        System.out.println("  -XX:ParallelGCThreads=4");
        System.out.println("  Number of threads for stop-the-world phases.");
        System.out.println("  Default: number of CPU cores ≤ 8.\n");

        System.out.println("Comparison — G1 vs Parallel vs Serial vs ZGC:");
        System.out.println("  Serial     -XX:+UseSerialGC        (single-threaded, small heaps)");
        System.out.println("  Parallel   -XX:+UseParallelGC      (throughput, batch, JDK 8 default)");
        System.out.println("  G1         -XX:+UseG1GC            (balanced, JDK 9+ default)");
        System.out.println("  ZGC        -XX:+UseZGC             (ultra-low latency, JDK 15+ prod)");
        System.out.println("  Shenandoah -XX:+UseShenandoahGC     (low latency, concurrent compaction)");
    }
}
```

**How to run:** `java G1Configuration.java`

Expected output:
```
=== G1 Configuration Options ===

Pause-time target:
  -XX:MaxGCPauseMillis=200
  G1 will try to keep pauses under 200ms (default).
  Lower it: -XX:MaxGCPauseMillis=50 (more aggressive, more CPU)
  Raise it: -XX:MaxGCPauseMillis=500 (less aggressive, better throughput)

Heap region size:
  -XX:G1HeapRegionSize=4M
  G1 divides the heap into ~2048 regions.
  Default is auto-calculated: heap size / 2048.
  Example: 8 GB heap → 8G/2048 ≈ 4 MB per region

Initiating heap occupancy (Mixed GC threshold):
  -XX:InitiatingHeapOccupancyPercent=45
  When old generation reaches 45% of heap, G1 starts
  concurrent marking to prepare for mixed collections.

Humongous object threshold:
  Objects larger than 50% of a region size
  are 'humongous' — allocated directly in old gen.
  (Default region = 4 MB → humongous = >2 MB object)

Concurrent GC threads:
  -XX:ConcGCThreads=2
  Number of threads for concurrent marking.
  Default: roughly 25% of ParallelGCThreads.

Parallel GC threads:
  -XX:ParallelGCThreads=4
  Number of threads for stop-the-world phases.
  Default: number of CPU cores ≤ 8.

Comparison — G1 vs Parallel vs Serial vs ZGC:
  Serial     -XX:+UseSerialGC        (single-threaded, small heaps)
  Parallel   -XX:+UseParallelGC      (throughput, batch, JDK 8 default)
  G1         -XX:+UseG1GC            (balanced, JDK 9+ default)
  ZGC        -XX:+UseZGC             (ultra-low latency, JDK 15+ prod)
  Shenandoah -XX:+UseShenandoahGC     (low latency, concurrent compaction)
```

The real-world configuration overview: each tuning knob and its default. `MaxGCPauseMillis` is the primary tuning lever — lower values trade throughput for lower latency. The collector comparison helps choose the right GC for the workload.

### Level 3 — Advanced

```java
// File: GCWorkloadDemo.java
import java.lang.management.*;
import java.util.*;

public class GCWorkloadDemo {

    static void printGCStats() {
        long youngPauses = 0, oldPauses = 0;
        long youngTime = 0, oldTime = 0;

        for (var gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            if (gc.getName().contains("Young")) {
                youngPauses = gc.getCollectionCount();
                youngTime = gc.getCollectionTime();
            } else if (gc.getName().contains("Old") || gc.getName().contains("Mixed")) {
                oldPauses = gc.getCollectionCount();
                oldTime = gc.getCollectionTime();
            }
        }

        Runtime rt = Runtime.getRuntime();
        long usedMB = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
        long maxMB  = rt.maxMemory() / (1024 * 1024);

        System.out.printf(
            "Heap: %d/%d MB | Young GCs: %d (%dms) | Old/Mixed GCs: %d (%dms)%n",
            usedMB, maxMB, youngPauses, youngTime, oldPauses, oldTime
        );
    }

    public static void main(String[] args) {
        System.out.println("=== G1 GC Workload Simulation ===\n");

        System.out.println("Simulating a memory-intensive workload...\n");

        // Phase 1: Allocate many small objects (triggers young GCs)
        System.out.println("Phase 1: Allocating small objects (young GCs)...");
        List<byte[]> smallObjects = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            smallObjects.add(new byte[100_000]); // 100 KB each
            if (i % 25 == 0) {
                printGCStats();
            }
        }
        smallObjects.clear(); // Let them be collected
        System.gc();
        System.out.println();

        // Phase 2: Allocate larger objects (some may be humongous)
        System.out.println("Phase 2: Allocating larger objects...");
        List<byte[]> largeObjects = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            largeObjects.add(new byte[2_000_000]); // 2 MB each
            if (i % 5 == 0) {
                printGCStats();
            }
        }

        System.out.println("\n=== Summary ===");
        System.out.println("During this run, G1 performed young collections");
        System.out.println("to reclaim short-lived objects from Eden regions.");
        System.out.println("The 2 MB objects (>50% of default 4 MB region)");
        System.out.println("are 'humongous' — G1 allocates them directly in old gen.");
        System.out.println();
        System.out.println("Run with: java -Xlog:gc*=info " + GCWorkloadDemo.class.getSimpleName() + ".java");
        System.out.println("to see the actual GC log events as they happen.");
    }
}
```

**How to run:** `java GCWorkloadDemo.java`

Expected output (GC timings vary):
```
=== G1 GC Workload Simulation ===

Simulating a memory-intensive workload...

Phase 1: Allocating small objects (young GCs)...
Heap: 12/2048 MB | Young GCs: 0 (0ms) | Old/Mixed GCs: 0 (0ms)
Heap: 45/2048 MB | Young GCs: 2 (12ms) | Old/Mixed GCs: 0 (0ms)
Heap: 78/2048 MB | Young GCs: 4 (25ms) | Old/Mixed GCs: 0 (0ms)
Heap: 120/2048 MB | Young GCs: 7 (42ms) | Old/Mixed GCs: 0 (0ms)

Phase 2: Allocating larger objects...
Heap: 15/2048 MB | Young GCs: 8 (45ms) | Old/Mixed GCs: 1 (8ms)
Heap: 52/2048 MB | Young GCs: 10 (58ms) | Old/Mixed GCs: 1 (8ms)
Heap: 89/2048 MB | Young GCs: 12 (72ms) | Old/Mixed GCs: 1 (8ms)
Heap: 128/2048 MB | Young GCs: 14 (85ms) | Old/Mixed GCs: 1 (8ms)

=== Summary ===
During this run, G1 performed young collections
to reclaim short-lived objects from Eden regions.
The 2 MB objects (>50% of default 4 MB region)
are 'humongous' — G1 allocates them directly in old gen.

Run with: java -Xlog:gc*=info GCWorkloadDemo.java
to see the actual GC log events as they happen.
```

The production-flavoured workload simulation: a two-phase memory allocation that triggers both young GCs (from small, short-lived objects) and shows how humongous objects (larger than 50% of a G1 region) skip the young generation entirely and are allocated directly in the old generation. The `printGCStats()` method uses `ManagementFactory` to read live GC counters, demonstrating programmatic GC monitoring.

## 6. Walkthrough

Tracing G1's behaviour during the Phase 1 allocations in the Level 3 example:

1. **Initial state**: The JVM starts with an empty heap. G1 has divided the heap into regions (default auto-sizing produces ~2048 regions). Initially, all regions are Free.

2. **Allocation begins**: `new byte[100_000]` (100 KB) is allocated. G1 takes a Free region and designates it as Eden. The object is allocated there. Subsequent allocations fill Eden.

3. **Eden fills up**: After several allocations, Eden regions are full. G1 triggers a **Young-only collection** (stop-the-world):
   - Live objects in Eden are copied to a Survivor region (or promoted to Old if they've survived enough collections).
   - Dead objects are simply discarded (Eden regions become Free).
   - The pause is brief (typically single-digit milliseconds for small heaps).
   - The `GarbageCollectorMXBean` count for "G1 Young Generation" increments by 1.

4. **More allocations, more young GCs**: This cycle repeats — allocate until Eden fills, young GC, continue. Each young GC promotes surviving objects to Survivor regions, and eventually from Survivor to Old regions.

5. **Old gen accumulation**: As promoted objects accumulate in Old regions, the old generation occupancy grows. When it reaches `InitiatingHeapOccupancyPercent` (default 45%), G1 starts **Concurrent marking**:
   - Runs in the background while the application continues to run.
   - Marks live objects across the entire heap.
   - Identifies Old regions with the most garbage (the "garbage-first" regions).

6. **Mixed collection**: After marking completes, G1 schedules **Mixed collections**. These collect all Young regions plus a subset of Old regions (the ones identified as having the most garbage). The number of Old regions to collect is calculated so the pause stays within `MaxGCPauseMillis`.

7. **The loop continues**: Young collections remain frequent, mixed collections happen periodically when old gen fills up. This is G1's core loop — incremental, targeted collection with predictable pauses.

```
Application running
  │
  ├─ Allocation fills Eden ─────► Young GC (stop-the-world, ~5ms)
  │   │                              │
  │   │   ┌──────────────────────────┘
  │   │   ▼
  │   │  Live → Survivor, Dead → discard
  │   │  (Eden regions become Free)
  │   │
  │   └─ Allocation continues ──► Eden fills again ──► Young GC
  │                                                      │
  │   ... repeat ...                                     │
  │                                                      │
  ├─ Old gen reaches 45% ──────► Concurrent marking (background)
  │   │                              │
  │   │   ┌──────────────────────────┘
  │   │   ▼
  │   │  Mark live objects, find garbage-rich Old regions
  │   │
  │   └─ Mixed GC (stop-the-world)
  │        Collect: Young + selected Old regions
  │        (pause < MaxGCPauseMillis)
  │
  └─ Application continues
```

## 7. Gotchas & takeaways

> G1's `MaxGCPauseMillis` is a **soft target**, not a hard guarantee — G1 will try to meet it, but if the heap is too large, the live set is too large, or the application's allocation rate is too high, pauses may exceed the target. G1 also cannot control pauses caused by humongous object allocation (which may trigger a full GC), `System.gc()` calls, or JNI critical sections. Use `-Xlog:gc+ergo*=debug` to see why G1 is missing its pause target.

- G1 replaced the Parallel GC as the default in JDK 9, but that doesn't mean it's always the best choice. For pure batch processing with no latency requirements (e.g. overnight ETL jobs), the Parallel GC often delivers 10–20% higher throughput. Benchmark both.
- Humongous objects (larger than 50% of a G1 region) are a known G1 pain point — they're allocated directly in the old generation and can only be collected during a full GC or a concurrent cleanup. Avoid large `byte[]` buffers, huge `ArrayList` backing arrays, and large `String` objects where possible, or increase the region size to reduce humongous allocations.
- G1's region size is auto-calculated but can be manually set with `-XX:G1HeapRegionSize`. The heap must be at least ~2 MB × 2048 ≈ 4 GB for 2 MB regions, or ~32 MB × 2048 ≈ 64 GB for 32 MB regions. The number of regions is always ~2048.
- `System.gc()` with G1 triggers a concurrent cycle by default (not a stop-the-world full GC like with Parallel GC). Use `-XX:+ExplicitGCInvokesConcurrent` (default with G1) to keep the pause short, or `-XX:+DisableExplicitGC` to ignore `System.gc()` calls entirely.
- Monitor G1 with `-Xlog:gc*=info` — the unified log format gives you pause times, heap occupancy before/after each GC, concurrent marking duration, and humongous allocation counts. This is the first diagnostic step for any G1 performance issue. 