---
card: java
gi: 618
slug: parallel-full-gc-for-g1
title: Parallel Full GC for G1
---

## 1. What it is

Java 10 improved the G1 garbage collector by making its full (stop-the-world) collections **parallel**, using multiple threads to mark and compact the heap. Before Java 10, G1's full GC was single-threaded — it used a single thread to mark live objects and compact the heap, causing full GC pauses to scale linearly with heap size. With parallel full GC, the marking and compaction phases use the same thread pool as G1's young and mixed collections, dramatically reducing full GC pause times on large heaps and multi-core machines.

## 2. Why & when

A full GC in G1 is a fallback mechanism — it happens when concurrent marking cannot keep up with the allocation rate, when the heap is nearly exhausted, or when a `System.gc()` call forces a full collection. Before Java 10, even a machine with 32 cores would use only 1 core for G1's full GC, turning an already-bad situation into a catastrophic pause (multi-second or even multi-minute on large heaps). Parallelising the full GC means that when the worst-case scenario does happen, the JVM recovers faster — the pause is still a full GC, but it's over sooner because all cores participate. This is critical for production systems where a full GC is a "surge protect" event: it should be rare, but when it happens, it must not take the service offline for minutes.

## 3. Core concept

```
G1 Full GC (JDK 9):
  Stop-the-world → 1 thread marks → 1 thread compacts → resume
  Pause ~ heap_size / single_thread_speed

G1 Full GC (JDK 10+):
  Stop-the-world → N threads mark → N threads compact → resume
  Pause ~ heap_size / (N × thread_speed)

Parallelism controlled by:
  -XX:ParallelGCThreads=N  (default: number of CPU cores ≤ 8)
```

The same `-XX:ParallelGCThreads` flag that controls G1's young and mixed collection parallelism now also applies to full GCs. No new flags needed — the improvement is automatic.

## 4. Diagram

<svg viewBox="0 0 560 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK 10 parallelises G1 full GC marking and compaction across multiple threads">
  <rect x="20" y="10" width="520" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#f85149" font-size="11" font-family="sans-serif">JDK 9 — Single-threaded Full GC</text>
  <rect x="30" y="45" width="80" height="20" rx="3" fill="#f85149" stroke="#f85149"/>
  <text x="70" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Thread 1</text>
  <text x="120" y="60" fill="#8b949e" font-size="9" font-family="monospace">mark → compact → done</text>
  <text x="330" y="60" fill="#8b949e" font-size="9" font-family="monospace">Thread 2–N: idle</text>

  <rect x="30" y="75" width="80" height="20" rx="3" fill="#8b949e" stroke="#8b949e" opacity="0.3"/>
  <text x="70" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Thread 2</text>
  <rect x="30" y="100" width="80" height="20" rx="3" fill="#8b949e" stroke="#8b949e" opacity="0.3"/>
  <text x="70" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Thread N</text>

  <line x1="30" y1="125" x2="540" y2="125" stroke="#8b949e" stroke-width="0.5"/>

  <text x="30" y="145" fill="#6db33f" font-size="11" font-family="sans-serif">JDK 10+ — Parallel Full GC</text>
  <rect x="30" y="155" width="80" height="20" rx="3" fill="#6db33f" stroke="#6db33f"/>
  <text x="70" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Thread 1</text>
  <rect x="120" y="155" width="80" height="20" rx="3" fill="#6db33f" stroke="#6db33f"/>
  <text x="160" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Thread 2</text>
  <rect x="210" y="155" width="80" height="20" rx="3" fill="#6db33f" stroke="#6db33f"/>
  <text x="250" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Thread N</text>
  <text x="300" y="170" fill="#8b949e" font-size="9" font-family="monospace">all mark + compact together</text>
</svg>

Single-threaded full GC (JDK 9) versus parallel full GC (JDK 10+). All threads participate, reducing pause time.

## 5. Runnable example

Scenario: demonstrating the concept and monitoring of G1 full GC parallelism — starting with checking GC configuration, extending to simulating memory pressure that triggers a full GC, and finally comparing the parallelism controls.

### Level 1 — Basic

```java
// File: G1ParallelFullGCDemo.java
import java.lang.management.*;

public class G1ParallelFullGCDemo {
    public static void main(String[] args) {
        System.out.println("=== G1 Parallel Full GC (JDK 10+) ===\n");

        System.out.println("In JDK 9, G1 full GC used a single thread.");
        System.out.println("In JDK 10+, G1 full GC is parallel — all cores help.\n");

        // Check available processors
        int cores = Runtime.getRuntime().availableProcessors();
        System.out.println("Available CPU cores: " + cores);
        System.out.println("G1 will use up to " + cores + " threads for full GC.");

        // Check which GC is active
        for (var gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            if (gc.getName().contains("G1 Old")) {
                System.out.println("\nG1 Old Generation collector detected.");
                System.out.println("  Collections: " + gc.getCollectionCount());
                System.out.println("  Total time:  " + gc.getCollectionTime() + "ms");
            }
        }

        System.out.println("\nTo observe full GC with -Xlog:");
        System.out.println("  $ java -Xlog:gc*=info -Xmx256m " +
            G1ParallelFullGCDemo.class.getSimpleName() + ".java");
        System.out.println("  Look for: 'Pause Full (G1 Compaction Pause)'");
    }
}
```

**How to run:** `java G1ParallelFullGCDemo.java`

Expected output (varies):
```
=== G1 Parallel Full GC (JDK 10+) ===

In JDK 9, G1 full GC used a single thread.
In JDK 10+, G1 full GC is parallel — all cores help.

Available CPU cores: 8
G1 will use up to 8 threads for full GC.

G1 Old Generation collector detected.
  Collections: 0
  Total time:  0ms

To observe full GC with -Xlog:
  $ java -Xlog:gc*=info -Xmx256m G1ParallelFullGCDemo.java
  Look for: 'Pause Full (G1 Compaction Pause)'
```

The simplest demonstration: checking available cores (which G1 uses for parallelism) and the G1 Old Generation collector status.

### Level 2 — Intermediate

```java
// File: FullGCTrigger.java
import java.util.*;

public class FullGCTrigger {

    // Fill memory to trigger GC pressure
    static void allocateUntilFull() {
        List<byte[]> mem = new ArrayList<>();
        try {
            for (int i = 0; ; i++) {
                mem.add(new byte[10_000_000]); // 10 MB each
                if (i % 10 == 0) {
                    Runtime rt = Runtime.getRuntime();
                    long used = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
                    System.out.printf("  Allocated %d MB...%n", used);
                }
            }
        } catch (OutOfMemoryError e) {
            System.out.println("  OutOfMemoryError — GC could not recover");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Triggering Full GC (G1 Parallel) ===\n");

        System.out.println("This program allocates memory rapidly to trigger GC.");
        System.out.println("G1 will attempt young GCs first, then concurrent marking,");
        System.out.println("and if memory pressure is too high, a parallel full GC.\n");

        System.out.println("GC thread configuration:");
        int cores = Runtime.getRuntime().availableProcessors();
        System.out.println("  -XX:ParallelGCThreads=" + Math.min(cores, 8) + " (default: min(cores, 8))");
        System.out.println("  -XX:ConcGCThreads=" + Math.max(1, cores / 4) + " (default: cores/4)\n");

        System.out.println("Flags to control parallelism:");
        System.out.println("  -XX:ParallelGCThreads=N    — threads for stop-the-world phases");
        System.out.println("  -XX:ConcGCThreads=N        — threads for concurrent marking");
        System.out.println("  -XX:+UseG1GC               — force G1 (default since JDK 9)\n");

        System.out.println("Starting allocation...");
        allocateUntilFull();
    }
}
```

**How to run:** `java -Xmx256m FullGCTrigger.java`

Expected output:
```
=== Triggering Full GC (G1 Parallel) ===

This program allocates memory rapidly to trigger GC.
G1 will attempt young GCs first, then concurrent marking,
and if memory pressure is too high, a parallel full GC.

GC thread configuration:
  -XX:ParallelGCThreads=8 (default: min(cores, 8))
  -XX:ConcGCThreads=2 (default: cores/4)

Flags to control parallelism:
  -XX:ParallelGCThreads=N    — threads for stop-the-world phases
  -XX:ConcGCThreads=N        — threads for concurrent marking
  -XX:+UseG1GC               — force G1 (default since JDK 9)

Starting allocation...
  Allocated 10 MB...
  Allocated 20 MB...
  ...
  OutOfMemoryError — GC could not recover
```

The real-world concern: a program that intentionally triggers GC pressure to demonstrate the GC hierarchy (young GC → concurrent marking → full GC). The parallel full GC only kicks in as a last resort — it's the safety net when all other GC mechanisms can't keep up.

### Level 3 — Advanced

```java
// File: GCParallelismComparison.java

public class GCParallelismComparison {
    public static void main(String[] args) {
        System.out.println("=== G1 Parallel Full GC: JDK 9 vs JDK 10+ ===\n");

        int cores = Runtime.getRuntime().availableProcessors();

        System.out.printf("%-25s %-15s %-15s%n", "Aspect", "JDK 9", "JDK 10+");
        System.out.println("─".repeat(55));

        System.out.printf("%-25s %-15s %-15s%n",
            "Full GC threads", "1 (single)", cores + " (parallel)");
        System.out.printf("%-25s %-15s %-15s%n",
            "Young GC", "Parallel", "Parallel (same)");
        System.out.printf("%-25s %-15s %-15s%n",
            "Mixed GC", "Parallel", "Parallel (same)");
        System.out.printf("%-25s %-15s %-15s%n",
            "Concurrent marking", "Concurrent", "Concurrent (same)");
        System.out.printf("%-25s %-15s %-15s%n",
            "Full GC speedup", "baseline", cores + "× (theoretical)");

        System.out.println("\nReal-world impact (16 GB heap, 8 cores):");
        System.out.println("  JDK 9  full GC: ~12 seconds  (single thread)");
        System.out.println("  JDK 10 full GC: ~3 seconds   (8 threads)");
        System.out.println("  Difference: 4× faster, still a full GC but over faster\n");

        System.out.println("Key points:");
        System.out.println("  1. Parallel full GC does NOT make full GCs happen less often");
        System.out.println("     — it only makes them finish faster when they do happen.");
        System.out.println("  2. The goal is still to AVOID full GCs entirely through");
        System.out.println("     proper heap sizing and G1 tuning.");
        System.out.println("  3. Parallel full GC is automatic — no new flags needed.");
        System.out.println("  4. -XX:ParallelGCThreads controls the thread count.");
        System.out.println("  5. This was backported to JDK 8u40+ for G1 as well.");
    }
}
```

**How to run:** `java GCParallelismComparison.java`

Expected output:
```
=== G1 Parallel Full GC: JDK 9 vs JDK 10+ ===

Aspect                    JDK 9           JDK 10+        
───────────────────────────────────────────────────────
Full GC threads           1 (single)      8 (parallel)  
Young GC                  Parallel        Parallel (same)
Mixed GC                  Parallel        Parallel (same)
Concurrent marking        Concurrent      Concurrent (same)
Full GC speedup           baseline        8× (theoretical)

Real-world impact (16 GB heap, 8 cores):
  JDK 9  full GC: ~12 seconds  (single thread)
  JDK 10 full GC: ~3 seconds   (8 threads)
  Difference: 4× faster, still a full GC but over faster

Key points:
  1. Parallel full GC does NOT make full GCs happen less often
     — it only makes them finish faster when they do happen.
  2. The goal is still to AVOID full GCs entirely through
     proper heap sizing and G1 tuning.
  3. Parallel full GC is automatic — no new flags needed.
  4. -XX:ParallelGCThreads controls the thread count.
  5. This was backported to JDK 8u40+ for G1 as well.
```

The production-flavoured comparison: JDK 9 vs JDK 10+ full GC performance across all dimensions. The table shows that only full GC changed — young, mixed, and concurrent phases were already parallel.

## 6. Walkthrough

Tracing a full GC event in JDK 10+ with G1:

1. **Trigger**: The application's allocation rate exceeds G1's ability to reclaim memory through young and mixed collections. The old generation is nearly full, and concurrent marking cannot complete in time. G1 decides a full GC is the only option.

2. **Stop-the-world**: All application threads are brought to a safepoint. This is the "stop" in stop-the-world.

3. **Parallel marking** (all `ParallelGCThreads` threads):
   - The heap is divided into work chunks.
   - Each thread takes a chunk, traces live objects starting from GC roots (thread stacks, static fields, JNI references).
   - Threads coordinate via work-stealing: if one thread finishes its chunk early, it takes work from another thread's queue.
   - In JDK 9, only one thread did this — the other threads were paused but idle.

4. **Parallel compaction** (all `ParallelGCThreads` threads):
   - After marking, the heap is compacted to eliminate fragmentation.
   - Live objects are moved toward the start of the heap, creating contiguous free space.
   - Each thread handles a portion of the heap, moving objects and updating references.
   - In JDK 9, only one thread performed compaction.

5. **Resume**: Application threads are released from the safepoint. The heap now has a large contiguous free region, and allocation can resume.

```
Full GC timeline (JDK 10, 8 cores):
  Stop → [T1 marks] [T2 marks] ... [T8 marks]  ← parallel
       → [T1 compacts] [T2 compacts] ... [T8 compacts]  ← parallel
       → Resume

Full GC timeline (JDK 9, same heap):
  Stop → [T1 marks]  [T2 idle] ... [T8 idle]  ← single-threaded
       → [T1 compacts]  [T2 idle] ... [T8 idle]  ← single-threaded
       → Resume
```

## 7. Gotchas & takeaways

> Parallel full GC is a **mitigation**, not a solution — full GCs are still bad. A parallel full GC on a 16 GB heap still takes seconds (just fewer seconds). The correct approach is to avoid full GCs entirely through proper heap sizing (`-Xmx`, `-Xms`), tuning `-XX:MaxGCPauseMillis`, and monitoring with `-Xlog:gc*=info`. Use parallel full GC as insurance, not as a design target.

- Parallel full GC uses the same `-XX:ParallelGCThreads` as young and mixed collections. The default is `min(cores, 8)` for small machines, `cores * 5/8 + 3` for larger machines. You rarely need to tune this.
- This improvement was **backported to JDK 8** (JDK 8u40+) for G1 as well — it was considered important enough to bring back to the LTS release. If you're on JDK 8 with G1, check your update version.
- The parallelism is for **stop-the-world full GCs** specifically. Concurrent marking (which runs while the application runs) uses `-XX:ConcGCThreads` (default ~25% of `ParallelGCThreads`).
- A full GC log line with G1 in JDK 10+ looks like: `[123.456s][info][gc] GC(42) Pause Full (G1 Compaction Pause) 3500M->2100M(4096M) 2345.678ms` — the parallel nature is not explicitly logged but the reduced pause time reflects it. 