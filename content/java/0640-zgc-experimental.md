---
card: java
gi: 640
slug: zgc-experimental
title: ZGC (experimental)
---

## 1. What it is

**ZGC** (Z Garbage Collector) is a **scalable, low-latency garbage collector** introduced as an experimental feature in Java 11 (JEP 333). Its defining promise: sub-millisecond pause times regardless of heap size — from 8 MB to 16 TB. ZGC achieves this by performing almost all work concurrently with the application threads, including object relocation (compaction). The "Z" doesn't officially stand for anything (it was originally the last letter of the alphabet, signifying a final, ultimate collector). ZGC is enabled with `-XX:+UnlockExperimentalVMOptions -XX:+UseZGC`. It became production-ready in Java 15.

## 2. Why & when

Traditional GCs (G1, Parallel, Serial) have pause times that grow with heap size — a 100 GB heap may see multi-second pauses. For applications that demand consistent sub-millisecond response times (financial trading, real-time bidding, game servers), these pauses are unacceptable. ZGC solves this by using **coloured pointers** (metadata stored in unused bits of 64-bit pointers) and **load barriers** to perform compaction without "stop-the-world" phases except for root scanning (which takes <1 ms). Use ZGC when you need consistently low latency with large heaps. As of Java 21+, ZGC also supports **generational collection** for even better throughput.

## 3. Core concept

```bash
# Enable ZGC (experimental in Java 11, production in Java 15+)
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx16g MyApp.java

# Key characteristics:
# - Pause times: typically <1 ms (sub-millisecond)
# - Heap sizes: 8 MB to 16 TB
# - Concurrent: marking, relocation, reference processing all concurrent
# - Compacting: yes (unlike CMS which could fragment)
# - Single-generation (Java 11-20); generational from Java 21+
```

ZGC uses **coloured pointers**: 64-bit object references store GC state (marked, remapped, etc.) in unused high bits. Load barriers (small code snippets injected by the JIT) check the colour bits on every object reference load and perform fixup if needed — this is how ZGC avoids stop-the-world pauses.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZGC performs nearly all GC work concurrently, achieving sub-millisecond pauses">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#8b949e" font-size="10" font-family="sans-serif">ZGC Phases (all concurrent with application except root scanning):</text>

  <rect x="30" y="45" width="85" height="22" rx="3" fill="#0d1117" stroke="#79c0ff"/>
  <text x="72" y="60" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Mark Start</text>
  <text x="125" y="60" fill="#8b949e" font-size="14" font-family="monospace">→</text>
  <rect x="135" y="45" width="85" height="22" rx="3" fill="#0d1117" stroke="#79c0ff"/>
  <text x="177" y="60" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Concurrent Mark</text>
  <text x="230" y="60" fill="#8b949e" font-size="14" font-family="monospace">→</text>
  <rect x="240" y="45" width="85" height="22" rx="3" fill="#0d1117" stroke="#79c0ff"/>
  <text x="282" y="60" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Concurrent Relocate</text>
  <text x="335" y="60" fill="#8b949e" font-size="14" font-family="monospace">→</text>
  <text x="345" y="60" fill="#3fb950" font-size="8" font-family="monospace">done</text>

  <text x="30" y="82" fill="#f85149" font-size="9" font-family="sans-serif">Stop-the-world: root scanning only (&lt;0.1 ms typically). Everything else is concurrent.</text>

  <text x="30" y="102" fill="#8b949e" font-size="9" font-family="sans-serif">Key techniques: coloured pointers (metadata in object refs) + load barriers (JIT-injected fixup code)</text>
  <text x="30" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">Experimental in Java 11 (JEP 333), production-ready in Java 15, generational mode in Java 21</text>
</svg>

ZGC's innovation is that compaction (relocation) happens concurrently — objects move while the application is running, thanks to coloured pointers and load barriers that transparently fix up stale references.

## 5. Runnable example

Scenario: demonstrating ZGC's low-pause behaviour by creating a high-allocation workload — starting with basic observation, extending to pause-time comparison, and finally discussing ZGC's trade-offs.

### Level 1 — Basic

```java
// File: ZGCDemo.java
public class ZGCDemo {
    public static void main(String[] args) {
        System.out.println("Current GC: " +
            java.lang.management.ManagementFactory.getGarbageCollectorMXBeans()
                .stream().map(Object::toString)
                .reduce((a, b) -> a + ", " + b).orElse("unknown"));

        System.out.println("\nTo run with ZGC:");
        System.out.println("  java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx2g ZGCDemo.java");
        System.out.println("  java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xlog:gc* ZGCDemo.java");
        System.out.println("\nZGC key properties:");
        System.out.println("  - Pause times: <1 ms (target), <10 ms (maximum)");
        System.out.println("  - Heap sizes: 8 MB to 16 TB");
        System.out.println("  - Compacting: yes (objects move while app runs)");
        System.out.println("  - Overhead: ~15% throughput reduction vs G1");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx2g ZGCDemo.java`

Expected output:
```
Current GC: ...

To run with ZGC:
  java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx2g ZGCDemo.java
  java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xlog:gc* ZGCDemo.java

ZGC key properties:
  - Pause times: <1 ms (target), <10 ms (maximum)
  - Heap sizes: 8 MB to 16 TB
  - Compacting: yes (objects move while app runs)
  - Overhead: ~15% throughput reduction vs G1
```

### Level 2 — Intermediate

```java
// File: ZGCWorkload.java
import java.util.*;

public class ZGCWorkload {
    public static void main(String[] args) throws Exception {
        System.out.println("=== ZGC Workload Simulation ===\n");
        System.out.println("Allocating and discarding objects rapidly...");
        System.out.println("(Run with -Xlog:gc to see ZGC pause times)\n");

        long start = System.currentTimeMillis();
        int allocations = 0;

        // Simulate a memory-churn workload: allocate and discard quickly
        List<byte[]> chunks = new ArrayList<>();

        for (int wave = 0; wave < 20; wave++) {
            // Allocate 50 MB of 1 MB chunks
            for (int i = 0; i < 50; i++) {
                chunks.add(new byte[1024 * 1024]);  // 1 MB
                allocations++;
            }
            // Discard all but the last few (simulating cache eviction)
            if (chunks.size() > 5) {
                chunks.subList(0, chunks.size() - 5).clear();
            }

            long elapsed = System.currentTimeMillis() - start;
            System.out.printf("  Wave %2d: %,d allocations, %,d ms elapsed%n",
                wave + 1, allocations, elapsed);

            Thread.sleep(50);  // let GC breathe
        }

        long total = System.currentTimeMillis() - start;
        System.out.printf("\nCompleted in %,d ms with %,d total allocations%n",
            total, allocations);

        System.out.println("\nRun with different GCs to compare:");
        System.out.println("  ZGC:     -XX:+UnlockExperimentalVMOptions -XX:+UseZGC");
        System.out.println("  G1:      -XX:+UseG1GC");
        System.out.println("  Parallel: -XX:+UseParallelGC");
        System.out.println("\nAdd -Xlog:gc for detailed GC pause-time logging");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx512m ZGCWorkload.java`

Expected output:
```
=== ZGC Workload Simulation ===

Allocating and discarding objects rapidly...
(Run with -Xlog:gc to see ZGC pause times)

  Wave  1: 50 allocations, ... ms elapsed
  Wave  2: 100 allocations, ... ms elapsed
  ...
Completed in ... ms with 1,000 total allocations

Run with different GCs to compare:
  ZGC:      -XX:+UnlockExperimentalVMOptions -XX:+UseZGC
  G1:       -XX:+UseG1GC
  Parallel: -XX:+UseParallelGC

Add -Xlog:gc for detailed GC pause-time logging
```

The real-world concern: comparing GC performance. Run the same workload with different GC flags and observe throughput and pause times via `-Xlog:gc`.

### Level 3 — Advanced

```java
// File: ZGCAdvanced.java
import java.lang.management.*;
import javax.management.*;
import java.util.*;

public class ZGCAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== ZGC — Deep Dive ===\n");

        // 1. Check current GC
        List<GarbageCollectorMXBean> gcs = ManagementFactory.getGarbageCollectorMXBeans();
        System.out.println("Active GCs:");
        for (var gc : gcs) {
            System.out.println("  " + gc.getName() +
                " — collections: " + gc.getCollectionCount() +
                ", time: " + gc.getCollectionTime() + " ms");
        }

        // 2. ZGC vs other GCs comparison
        System.out.println("\n=== GC Comparison ===\n");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "GC", "Max Pause", "Compacting?", "Max Heap");
        System.out.println("-".repeat(60));
        System.out.printf("%-15s %-15s %-12s %-15s%n", "Serial", "100-500 ms", "Yes", "<1 GB");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "Parallel", "100-500 ms", "Yes", ">100 GB");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "G1", "<100 ms", "Partial", ">100 GB");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "ZGC", "<1 ms", "Yes", "16 TB");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "Shenandoah", "<1 ms", "Yes", ">100 GB");
        System.out.printf("%-15s %-15s %-12s %-15s%n", "Epsilon", "0 ms", "No", "N/A");

        System.out.println("\n=== ZGC Technical Details ===\n");

        System.out.println("1. Coloured Pointers:");
        System.out.println("   64-bit object references use unused bits (42-bit address space");
        System.out.println("   on x86-64 leaves 22 bits for metadata). ZGC steals 4 bits to");
        System.out.println("   encode object state: Marked0, Marked1, Remapped, Finalizable.");
        System.out.println("   This is why ZGC requires 64-bit JVM and has a 16 TB heap limit.");
        System.out.println();
        System.out.println("2. Load Barriers:");
        System.out.println("   The JIT compiler injects a 'load barrier' (small code snippet)");
        System.out.println("   before every object field access. The barrier checks the colour");
        System.out.println("   bits and fixes up stale references (e.g., pointing to relocated");
        System.out.println("   objects). This is ~4% overhead on average.");
        System.out.println();
        System.out.println("3. Generational ZGC (Java 21+):");
        System.out.println("   Splits heap into young and old generations, collecting young");
        System.out.println("   objects more frequently. Improves throughput while maintaining");
        System.out.println("   sub-millisecond pauses. Enabled with -XX:+ZGenerational.");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC ZGCAdvanced.java`

Expected output:
```
=== ZGC — Deep Dive ===

Active GCs:
  Z Garbage Collector — collections: ..., time: ... ms
  Z Garbage Collector — collections: ..., time: ... ms

=== GC Comparison ===

GC              Max Pause       Compacting?  Max Heap       
------------------------------------------------------------
Serial          100-500 ms      Yes          <1 GB          
Parallel        100-500 ms      Yes          >100 GB        
G1              <100 ms         Partial      >100 GB        
ZGC             <1 ms           Yes          16 TB          
Shenandoah      <1 ms           Yes          >100 GB        
Epsilon         0 ms            No           N/A            
...
```

The production-flavoured hard cases: (1) **ZGC requires 64-bit JVM** — it won't work on 32-bit platforms. (2) **ZGC trades throughput for latency** — expect ~10-15% lower throughput than G1 for the same heap size. (3) **Coloured pointers limit heap to 16 TB** (on x86-64; different on ARM). (4) ZGC is best for latency-sensitive, large-heap applications. For smaller heaps (<4 GB) with moderate latency requirements, G1 may be a better fit.

## 6. Walkthrough

Tracing ZGC's concurrent relocation:

1. Application thread reads `obj.field`. The JIT-compiled code has a **load barrier** before the field access.

2. The load barrier checks the colour bits on `obj`'s reference. If the colour says "remapped" (normal state), the access proceeds normally — the barrier is just a few CPU instructions.

3. If the colour says "needs remap" (object was relocated by ZGC), the load barrier follows a **forwarding table** to find the new location of `obj`, updates the reference to point to the new location (self-healing), and proceeds with the access.

4. This happens **while the application is running** — no stop-the-world pause. The application threads occasionally do a tiny bit of GC work (updating a stale reference), keeping pause times in the microsecond range.

5. ZGC's concurrent phases (mark, relocate) run on dedicated GC threads. Only **root scanning** requires stopping application threads, and it typically completes in <0.1 ms regardless of heap size.

## 7. Gotchas & takeaways

> ZGC is **not a drop-in performance upgrade** from G1. It trades throughput (10-15% lower) for latency (100x lower pauses). For batch processing where pause time doesn't matter, G1 or Parallel GC will deliver higher throughput. Choose GC based on your performance goals, not fashion.

- ZGC requires a **64-bit JVM** (coloured pointers need 64-bit address space). 32-bit platforms are not supported.
- In Java 11, ZGC is **experimental** (`-XX:+UnlockExperimentalVMOptions` required). It became production-ready in Java 15. For production use, deploy on JDK 17+ with ZGC.
- ZGC **always compacts** — unlike G1 (which can fall back to full GCs) or CMS (which never compacted). This means no fragmentation and no unpredictable full-GC pauses.
- ZGC's **heap limit** is 16 TB on x86-64 (limited by the 42-bit virtual address space minus coloured-pointer bits). Larger heaps require different platforms or future JDK versions.
- ZGC uses **NUMA-aware** allocation: objects are allocated in memory local to the thread's NUMA node. This improves performance on multi-socket servers.
