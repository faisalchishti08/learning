---
card: java
gi: 928
slug: mark-sweep-mark-compact-copying
title: Mark-sweep / mark-compact / copying
---

## 1. What it is

These are the three foundational algorithms real garbage collectors build on to actually reclaim memory, once [reachability analysis](0926-reachability-gc-roots.md) has determined which objects are alive. **Mark-sweep** has two phases: mark (trace reachability from GC roots, flagging every live object) and sweep (walk the entire heap region, treating every unmarked object's space as free) — simple, but leaves the heap fragmented, with free space scattered in gaps between surviving objects rather than in one contiguous block. **Mark-compact** adds a third phase after marking: it slides all surviving objects together toward one end of the region, eliminating fragmentation entirely, at the cost of the extra work needed to relocate objects and fix up every reference that pointed to them. **Copying** collection (used specifically for the young generation, exploiting the [generational hypothesis](0925-generational-hypothesis-young-old-eden-survivor.md)) divides memory into two halves; it copies every *live* object from the currently-active half into the other half (compacting them as it goes, for free, as a side effect of copying), then simply treats the entire old half as reclaimed — extremely fast for regions where most objects are expected to be garbage, since the work is proportional to how much survives, not to the region's total size.

## 2. Why & when

Each algorithm makes a different tradeoff between speed, memory overhead, and fragmentation, which is exactly why real collectors combine them differently for different heap regions. Copying collection is ideal for the young generation precisely because the generational hypothesis holds there — since most objects die young, "copying only the survivors" touches very little data most of the time, making it extremely fast, at the cost of needing double the memory (one half always sits empty, reserved for the next copy) — an acceptable tradeoff since the young generation is comparatively small anyway. Mark-compact is better suited to the old generation, where most objects genuinely are expected to survive any given collection (copying-style "copy the survivors" would mean copying nearly everything, defeating copying's whole efficiency advantage) — compaction here avoids fragmentation, which matters more in a region expected to hold long-lived data for a long time, at the cost of a more expensive relocation phase. Plain mark-sweep (without compaction) trades away the compaction cost but risks fragmentation, which can eventually cause allocation failures even when total free memory is technically sufficient, just not contiguous — a real, historically significant issue that's exactly why most modern collectors add at least occasional compaction even to otherwise mark-sweep-based old-generation collection.

## 3. Core concept

```
Mark-sweep:      [mark reachable] -> [sweep: reclaim unmarked objects' space in place]
                  Result: free space in scattered gaps -- FRAGMENTED.

Mark-compact:     [mark reachable] -> [slide survivors together] -> [fix up references]
                  Result: free space in ONE contiguous block -- no fragmentation, but relocation cost.

Copying:          [copy every LIVE object from Half A to Half B] -> [treat all of Half A as free]
                  Result: naturally compact (copying inherently arranges survivors contiguously),
                  fast when few objects survive, but needs 2x memory (one half always reserved, empty).
```

Each algorithm's cost is proportional to a different thing: mark-sweep's sweep phase touches the whole region regardless of how much is garbage; copying's cost is proportional only to how much *survives*; mark-compact pays both a full mark pass and a relocation pass.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three collection strategies applied to the same heap region with scattered live objects: mark-sweep leaves gaps between survivors, mark-compact slides survivors together leaving one contiguous free block, copying moves survivors to a second half entirely">
  <text x="110" y="15" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Mark-sweep</text>
  <rect x="20" y="25" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="60" y="25" width="20" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="90" y="25" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="130" y="25" width="15" height="25" fill="none" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="155" y="25" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">free space FRAGMENTED</text>

  <text x="110" y="90" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Mark-compact</text>
  <rect x="20" y="100" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="50" y="100" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="80" y="100" width="30" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="110" y="100" width="75" height="25" fill="none" stroke="#6db33f"/>
  <text x="105" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ONE contiguous free block</text>

  <text x="480" y="15" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Copying (two halves)</text>
  <rect x="380" y="25" width="30" height="25" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="440" y="25" width="30" height="25" fill="#1c2430" stroke="#6db33f"/>
  <rect x="470" y="25" width="30" height="25" fill="#1c2430" stroke="#6db33f"/>
  <text x="420" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Half A (now free)</text>
  <text x="475" y="65" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Half B (survivors, packed)</text>
</svg>

*Three different ways of turning "which objects are still alive" into reclaimed, usable memory — each with a different speed/fragmentation/memory-overhead tradeoff.*

## 5. Runnable example

Scenario: since these algorithms are internal to the collector and not directly invokable from Java code, this example demonstrates their *effects* — fragmentation versus compaction — by observing allocation behavior and GC logs under different collector configurations, growing from a baseline showing typical young-generation (copying) behavior, to observing old-generation behavior under sustained retention, to comparing collectors with different compaction strategies.

### Level 1 — Basic

```java
public class YoungGenCopyingBehavior {
    public static void main(String[] args) throws InterruptedException {
        // Allocate many short-lived objects of VARYING sizes -- if this were collected via
        // plain mark-sweep without compaction, it would tend to fragment badly, since
        // objects of different sizes die in an interleaved, unpredictable pattern.
        for (int i = 0; i < 500_000; i++) {
            byte[] garbage = new byte[100 + (i % 50) * 20]; // varying sizes, all short-lived
        }
        System.out.println("done -- check the GC log above for 'Pause Young' events");
        System.out.println("(the young generation uses a COPYING collector by default in most modern JVMs --");
        System.out.println(" survivors are copied to a fresh space, inherently compacting them for free)");
    }
}
```

**How to run:** `java -Xlog:gc YoungGenCopyingBehavior.java` (JDK 17+).

Expected output shape (multiple fast "Pause Young" events, each reclaiming most of the examined memory):
```
[0.04s][info][gc] GC(0) Pause Young ... 4M->1M(64M) 2.1ms
[0.08s][info][gc] GC(1) Pause Young ... 5M->1M(64M) 1.9ms
...
done -- check the GC log above for 'Pause Young' events
(the young generation uses a COPYING collector by default in most modern JVMs --
 survivors are copied to a fresh space, inherently compacting them for free)
```

Despite allocating objects of many different, interleaved sizes (a pattern that would fragment a plain, non-compacting mark-sweep region), the young generation's copying collector produces no fragmentation at all — every minor GC's "after" state is implicitly compact, since copying survivors into a fresh space naturally packs them together with no gaps.

### Level 2 — Intermediate

```java
import java.util.*;

public class OldGenRetentionAndCompaction {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> retained = new ArrayList<>();

        for (int i = 0; i < 3000; i++) {
            // Allocate and IMMEDIATELY retain varying-sized objects, forcing promotion into
            // the old generation -- and, critically, occasionally REMOVE some retained objects
            // out of order, creating gaps a non-compacting collector would need to fragment around.
            retained.add(new byte[50_000 + (i % 20) * 5000]);
            if (i % 7 == 0 && !retained.isEmpty()) {
                retained.remove(retained.size() / 2); // remove from the MIDDLE -- creates a gap
            }
        }

        System.out.println("final retained count: " + retained.size());
        System.out.println("check the GC log above for 'Pause Full' events, if any occurred,");
        System.out.println("and note whether allocation continued succeeding despite the gaps created");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx128m OldGenRetentionAndCompaction.java` (JDK 17+; a modest heap cap makes old-generation pressure, and any resulting full/compacting collections, appear more readily).

Expected output shape (allocation succeeds throughout, and any full GC events reflect the collector compacting around the gaps created by out-of-order removal):
```
[0.05s][info][gc] GC(0) Pause Young ... 4M->1M(64M) 2.0ms
...
[1.20s][info][gc] GC(22) Pause Full (Ergonomics) ... 95M->60M(128M) 85ms
...
final retained count: ...
check the GC log above for 'Pause Full' events, if any occurred,
and note whether allocation continued succeeding despite the gaps created
```

The real-world concern added: deliberately removing retained objects out of order (from the middle of the list, not just the end) simulates a realistic pattern of old-generation objects becoming garbage in an unpredictable, interleaved order — exactly the pattern that would badly fragment a purely mark-sweep (non-compacting) collector over time; observing that allocation continues succeeding, and that any full GC's reported "after" size reflects genuinely reclaimed, usable contiguous space, is indirect but real evidence of the collector's compaction work paying off.

### Level 3 — Advanced

```java
import java.util.*;

public class ComparingCollectorConfigurations {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> retained = new ArrayList<>();
        long start = System.nanoTime();

        for (int i = 0; i < 5000; i++) {
            retained.add(new byte[30_000 + (i % 30) * 3000]);
            if (i % 5 == 0 && retained.size() > 10) {
                retained.remove(retained.size() / 3); // fragmentation-inducing removal pattern
            }
            if (i % 1000 == 0) {
                for (int j = 0; j < 5000; j++) {
                    byte[] shortLived = new byte[500]; // interleave short-lived young-gen churn too
                }
            }
        }

        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("final retained: " + retained.size() + ", elapsed: " + elapsedMs + "ms");
        System.out.println("compare this run's GC log across different collectors (see 'How to run')");
    }
}
```

**How to run:** run this three ways and compare the `-Xlog:gc` output and total elapsed time: `java -Xlog:gc -Xmx200m -XX:+UseG1GC ComparingCollectorConfigurations.java` (G1, a mostly region-based, incrementally-compacting collector), `java -Xlog:gc -Xmx200m -XX:+UseSerialGC ComparingCollectorConfigurations.java` (the simple serial collector, using mark-compact for its old generation), and `java -Xlog:gc -Xmx200m -XX:+UseParallelGC ComparingCollectorConfigurations.java` (JDK 17+; each collector implements these fundamental algorithms somewhat differently, with different pause characteristics).

Expected output shape (illustrative — exact numbers and GC event types vary significantly by collector and JVM version, but all three should complete correctly, with differing pause patterns reflecting their different underlying compaction strategies):
```
(G1GC):        final retained: ..., elapsed: 480ms  -- many small, incremental region-based collections
(SerialGC):     final retained: ..., elapsed: 650ms  -- fewer, larger mark-compact pauses on the old gen
(ParallelGC):   final retained: ..., elapsed: 410ms  -- similar algorithms to Serial, but multi-threaded
```

This adds the production-flavored hard case: running the identical, deliberately fragmentation-inducing and allocation-churning workload against three genuinely different collector implementations, each of which realizes the mark-sweep/mark-compact/copying algorithms differently (G1 divides the heap into many small regions and compacts incrementally, region by region, rather than compacting the entire old generation at once; Serial and Parallel use more traditional whole-generation mark-compact for the old generation, differing mainly in whether the actual work is single- or multi-threaded) — directly demonstrating that "which collector algorithm" is a genuine, measurable, configurable choice with real performance consequences for a given workload's specific allocation and retention pattern, not just an abstract textbook distinction.

## 6. Walkthrough

Reasoning through what each collector configuration is doing differently in `ComparingCollectorConfigurations.main`:

1. Every configuration must handle the same two allocation pressures: the young generation churning through many small, short-lived arrays (the periodic burst of 5000 `shortLived` allocations), and the old generation accumulating a growing, fragmentation-inducing set of retained `byte[]` arrays (from `retained`, with objects removed from arbitrary positions, not just the end).
2. Under G1, the heap is divided into many small, independently-collectible regions rather than one monolithic young/old split — G1 can incrementally collect and compact just the regions that are most profitable to reclaim at any given moment ("garbage-first," hence the name), rather than needing a single large pause to compact an entire old generation at once; this tends to produce more, but individually smaller and more predictable, pauses.
3. Under Serial GC, the old generation is collected via a single-threaded mark-compact pass when needed — simple and low-overhead for small heaps, but any given full collection pauses the entire program for the duration of that single-threaded mark-and-compact work, potentially producing longer individual pauses for a heap and retention pattern like this one, especially as it grows.
4. Under Parallel GC, the same fundamental mark-compact strategy for the old generation is used, but the actual marking and compaction work is spread across multiple threads — for a multi-core machine, this can substantially reduce the wall-clock duration of any individual full-collection pause compared to Serial GC's single-threaded approach, even though the total amount of CPU work performed is similar.
5. Because the workload here deliberately creates old-generation fragmentation pressure (objects removed from the middle of a growing collection, not just the end) alongside sustained young-generation churn, the specific way each collector handles compaction — incrementally and region-by-region (G1) versus in occasional, larger, whole-generation passes (Serial/Parallel) — becomes directly visible in both the shape of the GC log output and the overall elapsed time, rather than being a purely theoretical distinction.
6. None of the three configurations produce incorrect results — the actual retained object count (`retained.size()`) and program logic are identical regardless of collector choice; what differs is purely the performance characteristics (pause frequency, pause duration, total overhead) of reclaiming and compacting memory for this specific allocation pattern, which is exactly the kind of tradeoff a real production system would tune based on its own latency and throughput requirements.

## 7. Gotchas & takeaways

> **Gotcha:** these algorithms (mark-sweep, mark-compact, copying) are internal implementation strategies, and real, modern production collectors (G1, ZGC, Shenandoah, and others) combine, hybridize, and refine them in increasingly sophisticated ways (region-based collection, concurrent marking, incremental compaction) — treat this tutorial's three-algorithm framework as the essential conceptual foundation for understanding *why* garbage collectors behave the way they do, not as a literal, complete description of any single modern collector's actual internal implementation.

- Mark-sweep marks reachable objects and reclaims everything else in place, but leaves the heap fragmented; mark-compact adds a relocation phase to eliminate fragmentation at the cost of extra relocation work; copying collection copies survivors into a fresh space (inherently compacting them for free) and is fast specifically when few objects are expected to survive.
- Copying collection suits the young generation (few survivors expected, per the [generational hypothesis](0925-generational-hypothesis-young-old-eden-survivor.md)); mark-compact suits the old generation (most objects expected to survive, so copying nearly everything would be wasteful, but fragmentation still needs addressing since old-generation objects live a long time).
- Fragmentation is a real, historically significant problem for non-compacting collectors — it can cause allocation failures even when total free memory is technically sufficient, simply because no single contiguous block is large enough for a given request.
- Different JVM collectors (G1, Serial, Parallel, and others) implement these fundamental strategies differently — often with meaningfully different pause-frequency and pause-duration tradeoffs for the same underlying workload, making collector choice a genuine, measurable performance decision.
- See [reachability & GC roots](0926-reachability-gc-roots.md) for how the "mark" phase actually determines liveness, and [the generational hypothesis](0925-generational-hypothesis-young-old-eden-survivor.md) for the empirical observation that motivates applying different algorithms to different heap regions in the first place.
