---
card: java
gi: 931
slug: cms-removed
title: CMS (removed)
---

## 1. What it is

CMS (Concurrent Mark Sweep) was HotSpot's first mainstream low-pause collector for the old generation: instead of stopping the world for the entire mark phase like [Serial](0929-serial-gc.md) or [Parallel GC](0930-parallel-gc.md), it performed most of its marking work *concurrently* with running application threads, pausing the world only briefly at the start (initial mark) and partway through (remark) — trading extra CPU overhead and algorithmic complexity for dramatically shorter individual pauses. It was deprecated in Java 9 (JEP 291) and fully removed in Java 14 (JEP 363); any modern JDK (17+) will refuse to start with `-XX:+UseConcMarkSweepGC`, printing an error rather than falling back silently. It is documented here because a huge amount of existing production tuning knowledge, blog posts, and legacy configuration still references it, and because understanding *why* it was removed illuminates what [G1](0932-g1-gc.md) (its replacement) does better.

## 2. Why & when

CMS is relevant today only in a historical and migration sense — there is no "when to use it" for new work, since it cannot run on any currently-supported JDK. It matters because two of its structural weaknesses directly motivated G1's design and are useful to understand: first, CMS used plain mark-**sweep** (not compact) for the old generation, so it never eliminated fragmentation — over a long enough run, fragmentation could grow until the collector could no longer find contiguous space for a large allocation, forcing a fallback to a full, single-threaded, stop-the-world compacting collection, at exactly the worst possible moment (when memory was already tight); second, CMS ran its concurrent phases as a genuinely separate, hand-tuned collector bolted onto the existing young/old generational structure, rather than being designed from scratch around a unified, region-based heap layout, which made it notoriously difficult to tune correctly and prone to a specific failure mode called "concurrent mode failure," where the concurrent cycle didn't finish reclaiming space fast enough to keep ahead of allocation, again forcing an expensive full GC.

## 3. Core concept

```
CMS collection cycle (old generation only; young gen used ordinary copying):

[STW: Initial Mark]  -- pause -- mark GC roots only (fast)
        |
        v
[Concurrent Mark]    -- NO pause -- trace reachability while app threads keep running
        |
        v
[STW: Remark]        -- pause -- fix up anything the app mutated during concurrent mark
        |
        v
[Concurrent Sweep]   -- NO pause -- reclaim unmarked objects' space (NOT compacted)
        |
        v
Old generation now has free space, but potentially FRAGMENTED
(no compaction step) -- risk of eventual "concurrent mode failure"
requiring a full, single-threaded, stop-the-world fallback collection.
```

The key structural weakness: two short pauses instead of one long one was a real win for latency, but skipping compaction meant fragmentation was never actually solved, only deferred.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CMS collection cycle showing short stop-the-world initial mark and remark pauses bracketing longer concurrent mark and sweep phases, with a fragmentation warning">
  <rect x="10" y="30" width="90" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="55" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">STW: Initial Mark</text>

  <rect x="110" y="30" width="160" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="190" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Concurrent Mark (app keeps running)</text>

  <rect x="280" y="30" width="90" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="325" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">STW: Remark</text>

  <rect x="380" y="30" width="160" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Concurrent Sweep (app keeps running)</text>

  <text x="320" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Two SHORT pauses instead of one LONG one -- good for latency</text>
  <text x="320" y="130" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">BUT: sweep never compacts -- fragmentation accumulates</text>
  <text x="320" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">risk: "concurrent mode failure" -&gt; expensive full STW fallback GC</text>
</svg>

*CMS traded one long pause for two short ones, but never solved fragmentation — the gap that G1 was designed to close.*

## 5. Runnable example

Scenario: since CMS cannot run on JDK 17+, this example demonstrates the migration reality directly — attempting to use the removed flag, observing the JVM's actual error, then showing the recommended modern replacement achieving the same low-pause goal, growing from the basic failure, to understanding the specific error message, to a working G1-based equivalent workload.

### Level 1 — Basic

```java
public class CmsRemovedDemo {
    public static void main(String[] args) {
        System.out.println("This class does nothing special --");
        System.out.println("the point is which JVM flag you launch it with.");
    }
}
```

**How to run:** `java -XX:+UseConcMarkSweepGC CmsRemovedDemo.java` (any JDK 17+).

Expected output (the JVM refuses to start at all):
```
Unrecognized VM option 'UseConcMarkSweepGC'
Did you mean '-XX:+UseParallelGC'?
Error: Could not create the Java Virtual Machine.
Error: A fatal exception has occurred. Program will exit.
```

The class body never even runs — CMS was removed at the JVM level in Java 14, so the flag itself is now unrecognized, not merely deprecated-but-tolerated.

### Level 2 — Intermediate

```java
public class CmsRemovedDeprecationHistory {
    public static void main(String[] args) {
        String v = System.getProperty("java.version");
        System.out.println("Running on JDK " + v);
        System.out.println("CMS status by version:");
        System.out.println("  Java 9-13:  deprecated (JEP 291) -- still usable, prints a warning");
        System.out.println("  Java 14+:   removed entirely (JEP 363) -- flag unrecognized, JVM refuses to start");
    }
}
```

**How to run:** `java CmsRemovedDeprecationHistory.java` (JDK 17+; this always runs, since it uses default flags — no CMS flag is passed here).

Expected output shape:
```
Running on JDK 17.0.9
CMS status by version:
  Java 9-13:  deprecated (JEP 291) -- still usable, prints a warning
  Java 14+:   removed entirely (JEP 363) -- flag unrecognized, JVM refuses to start
```

The real-world concern added: understanding that this was a two-stage removal (deprecate with a warning, then remove entirely) matters for anyone migrating an old production JVM configuration forward — a config that merely printed a warning on Java 11 will refuse to boot at all on Java 17.

### Level 3 — Advanced

```java
import java.util.*;

public class MigratingCmsWorkloadToG1 {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 300_000; i++) {
            retained.add(new byte[200]);
            if (i % 6 == 0 && !retained.isEmpty()) {
                retained.remove(retained.size() / 2); // fragmentation-inducing pattern, as CMS never compacted
            }
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check the log -- G1 compacts incrementally, avoiding CMS's fragmentation failure mode");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx128m -XX:+UseG1GC MigratingCmsWorkloadToG1.java` (JDK 17+; this is the recommended modern replacement for an old CMS-tuned workload).

Expected output shape:
```
[0.03s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) ... 4M->1M(128M) 1.8ms
...
[0.40s][info][gc] GC(9) Pause Young (Concurrent Start) (G1 Evacuation Pause) ... 60M->28M(128M) 6.2ms
retained: 300000
check the log -- G1 compacts incrementally, avoiding CMS's fragmentation failure mode
```

The production-flavored hard case: the same deliberately fragmentation-inducing removal pattern that would have eventually driven CMS into a "concurrent mode failure" runs cleanly under G1, because G1 both marks concurrently *and* compacts incrementally, region by region — directly demonstrating why G1 was built as CMS's structural successor rather than an incremental patch.

## 6. Walkthrough

Tracing the migration story end to end, using `MigratingCmsWorkloadToG1.main` as the anchor:

1. Historically, this same allocation-and-removal workload run under CMS would begin with an `Initial Mark` stop-the-world pause (fast — it only marks GC roots), followed by a `Concurrent Mark` phase running alongside the application threads still executing the loop.
2. A `Remark` stop-the-world pause would follow, catching up on anything the application mutated during concurrent marking (a necessary correctness step, since the heap kept changing underneath the concurrent tracer).
3. A `Concurrent Sweep` phase would then reclaim unmarked objects' space — but critically, *without compacting* — so the deliberately out-of-order removal pattern in this workload (removing from the middle of `retained`, not just the end) would leave the old generation increasingly fragmented with each cycle.
4. Given enough cycles, CMS could enter "concurrent mode failure": the concurrent cycle failing to reclaim space fast enough relative to ongoing allocation, forcing an expensive full, single-threaded, stop-the-world fallback collection — precisely the worst-case pause CMS was originally built to avoid.
5. Under G1 (this example's actual collector), the heap is divided into many small regions; G1 also marks concurrently, but *does* compact — incrementally, one region at a time, choosing the most garbage-rich regions first ("garbage-first") — so the same fragmentation-inducing removal pattern here never accumulates into a crisis requiring an expensive fallback, which is exactly what the "G1 Evacuation Pause" log lines above reflect: small, steady, compacting pauses instead of an eventual large recovery pause.
6. The program finishes and prints its retained count, with the surrounding log evidence showing the structural improvement G1 represents over CMS for exactly the kind of workload CMS historically struggled with.

## 7. Gotchas & takeaways

> **Gotcha:** any JVM startup script, container image, or configuration file still passing `-XX:+UseConcMarkSweepGC` (or CMS-specific tuning flags like `-XX:CMSInitiatingOccupancyFraction`) will fail to start entirely on Java 14+ — this is a common, easy-to-miss breakage when upgrading legacy services across major JDK versions, and it is worth grepping deployment configs for CMS flags *before* an upgrade, not after a production outage.

- CMS reduced pause times by marking concurrently with the application, pausing the world only briefly for initial mark and remark.
- It never compacted the old generation (plain mark-sweep, not mark-compact), so fragmentation accumulated over time and could eventually trigger an expensive full stop-the-world fallback collection ("concurrent mode failure").
- Deprecated in Java 9 (JEP 291), fully removed in Java 14 (JEP 363) — any JDK 17+ JVM will refuse to start if given `-XX:+UseConcMarkSweepGC`.
- [G1 GC](0932-g1-gc.md) is its structural successor: it also marks concurrently, but additionally compacts incrementally region-by-region, closing exactly the fragmentation gap that made CMS eventually unreliable.
- When migrating an old CMS-tuned production JVM configuration forward, audit for CMS-specific flags first — they will cause an immediate startup failure, not a silent fallback, on modern JDKs.
