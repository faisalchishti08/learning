---
card: java
gi: 934
slug: shenandoah
title: Shenandoah
---

## 1. What it is

Shenandoah is a low-pause garbage collector, developed by Red Hat and available in OpenJDK builds since Java 12, that pursues the same headline goal as [ZGC](0933-zgc.md) — pause times that stay small and roughly independent of heap size — but reaches it through a different mechanism: instead of colored pointers baked into the reference bits themselves, Shenandoah gives each object a **forwarding pointer** (an extra word stored alongside the object) that points to the object's current, up-to-date location, and inserts a lightweight **read/write barrier** into application code that follows this forwarding pointer whenever an object might have moved. This lets Shenandoah, like ZGC, perform concurrent compaction (relocating live objects while the application keeps running) rather than requiring a stop-the-world pause for that step, which is traditionally the most expensive part of any compacting collector.

## 2. Why & when

Shenandoah targets essentially the same use case as ZGC: applications where worst-case pause time matters more than raw throughput, regardless of heap size — services with strict latency SLAs, large heaps where a traditional collector's compaction pause would be unacceptable, and workloads where predictability of tail latency matters as much as its average. The two collectors are close enough in goals and results that the choice between them, on JDKs where both are available, often comes down to specific version availability, vendor distribution (Shenandoah has historically had strong support in Red Hat's OpenJDK builds), or fine differences in overhead characteristics for a specific workload's allocation pattern, rather than a fundamental difference in what problem each solves. Like ZGC, the barrier mechanism that enables concurrent compaction adds a small constant overhead to relevant object accesses, so — exactly as with ZGC — Shenandoah is the wrong choice for small heaps or throughput-bound batch workloads with no latency requirement, where that overhead buys nothing.

## 3. Core concept

```
Every object has an extra FORWARDING POINTER field alongside its data:

  Object (old copy)                Object (new copy, after concurrent relocation)
  [forwarding ptr] --------------> [actual live data]
  [(stale data, ignored)]

Read/write barrier inserted at relevant access points:
  - On read: follow the forwarding pointer to get the CURRENT, correct copy
  - On write: ensure the write lands on the CURRENT copy, not a stale one

Because every access is transparently redirected through the forwarding pointer,
the GC can copy an object to a new location WHILE the application keeps
using references to it -- no stop-the-world pause needed for relocation itself.
```

The forwarding pointer is conceptually simple — one extra field per object — but its cost is paid continuously, on every relevant access, in exchange for eliminating the traditional need to freeze the world during compaction.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application thread following an object's forwarding pointer through a read barrier to reach its relocated copy while GC threads concurrently copy objects to new locations">
  <rect x="20" y="30" width="150" height="40" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="46" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Old object copy</text>
  <text x="95" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">[forwarding ptr] -&gt;</text>

  <rect x="220" y="30" width="150" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="295" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">New object copy</text>
  <text x="295" y="60" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">(current, live data)</text>

  <line x1="170" y1="50" x2="220" y2="50" stroke="#79c0ff" marker-end="url(#arrow)"/>

  <rect x="420" y="20" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="39" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">App thread reads/writes via barrier</text>
  <line x1="400" y1="35" x2="420" y2="35" stroke="#79c0ff"/>

  <text x="320" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GC threads copy objects to new locations CONCURRENTLY</text>
  <text x="320" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">while the app keeps reading/writing through the barrier</text>
  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Result: compaction happens without a stop-the-world pause</text>
</svg>

*Shenandoah's forwarding pointer plus read/write barrier let the application keep using an object correctly while the collector relocates it in the background.*

## 5. Runnable example

Scenario: observe Shenandoah's concurrent-compaction behavior — starting with a basic enabled workload, then scaling retention to trigger a full concurrent-evacuation cycle, then comparing pause characteristics directly against G1 on the same large-heap retention workload.

### Level 1 — Basic

```java
public class ShenandoahBaseline {
    public static void main(String[] args) {
        for (int i = 0; i < 3_000_000; i++) {
            byte[] garbage = new byte[64];
        }
        System.out.println("done -- check -Xlog:gc for Shenandoah pause events");
    }
}
```

**How to run:** `java -Xlog:gc -XX:+UseShenandoahGC ShenandoahBaseline.java` (JDK 17+; requires a JDK build with Shenandoah included — most mainstream OpenJDK distributions ship it).

Expected output shape:
```
[0.02s][info][gc] GC(0) Pause Init Mark 0.180ms
[0.03s][info][gc] GC(0) Pause Final Mark 0.220ms
[0.05s][info][gc] GC(0) Pause Init Update Refs 0.090ms
[0.06s][info][gc] GC(0) Pause Final Update Refs 0.150ms
done -- check -Xlog:gc for Shenandoah pause events
```

Shenandoah's cycle is broken into several small named pauses (Init Mark, Final Mark, Init/Final Update Refs) bracketing longer concurrent phases — each individual pause stays well under a millisecond even at this small scale.

### Level 2 — Intermediate

```java
import java.util.*;

public class ShenandoahLargeRetention {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 2_000_000; i++) {
            retained.add(new byte[500]);
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check for 'Pause Init/Final Mark' and 'Concurrent evacuation' log lines");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx4g -XX:+UseShenandoahGC ShenandoahLargeRetention.java` (JDK 17+).

Expected output shape:
```
[0.02s][info][gc] GC(0) Pause Init Mark 0.210ms
[0.15s][info][gc] GC(0) Concurrent marking 120.400ms
[0.16s][info][gc] GC(0) Pause Final Mark 0.340ms
[0.18s][info][gc] GC(0) Concurrent evacuation 95.200ms
[0.20s][info][gc] GC(0) Pause Init Update Refs 0.110ms
[0.35s][info][gc] GC(0) Concurrent update references 140.500ms
[0.36s][info][gc] GC(0) Pause Final Update Refs 0.180ms
retained: 2000000
check for 'Pause Init/Final Mark' and 'Concurrent evacuation' log lines
```

The real-world concern added: at this larger, gigabyte-scale retention level, the "Concurrent marking" and "Concurrent evacuation" phases (which take tens to hundreds of milliseconds) are clearly visible as *not* blocking pauses — the actual stop-the-world pauses bracketing them remain sub-millisecond, confirming that the expensive work (marking and, critically, relocating live objects) happens entirely alongside the running application.

### Level 3 — Advanced

```java
import java.util.*;

public class ShenandoahVsG1Comparison {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.nanoTime();
        for (int i = 0; i < 4_000_000; i++) {
            retained.add(new byte[500]);
            if (i % 100_000 == 0) {
                for (int j = 0; j < 50_000; j++) {
                    byte[] churn = new byte[128];
                }
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("retained: " + retained.size() + ", elapsed: " + elapsedMs + "ms");
    }
}
```

**How to run:** compare maximum single-pause duration on the same large-heap workload: `java -Xlog:gc -Xmx6g -XX:+UseShenandoahGC ShenandoahVsG1Comparison.java` versus `java -Xlog:gc -Xmx6g -XX:+UseG1GC ShenandoahVsG1Comparison.java` (JDK 17+).

Expected output shape (illustrative):
```
(Shenandoah): max single pause ~0.9ms across the run, total elapsed: 6300ms
(G1):         max single pause ~190ms (a large mixed collection), total elapsed: 5300ms
```

The production-flavored hard case: on identical large-heap, high-retention workloads, Shenandoah's worst-case single pause stays roughly two orders of magnitude below G1's, at a modest cost in total throughput — the same fundamental latency-for-throughput tradeoff ZGC makes, achieved here via forwarding pointers and read/write barriers rather than colored pointers.

## 6. Walkthrough

Tracing `ShenandoahLargeRetention.main` end to end, following the phases visible in its log:

1. `Pause Init Mark` is a brief stop-the-world pause that snapshots GC roots — the starting points for reachability tracing — before concurrent marking begins; this is intentionally minimal, touching only roots, not the full object graph.
2. `Concurrent marking` then traces reachability across the live heap while the application's loop keeps allocating and retaining objects — since this runs alongside the application rather than pausing it, its duration (shown as ~120ms here) does not block the loop from making progress.
3. `Pause Final Mark` is a second brief pause that finalizes marking, catching anything the application mutated concurrently during the marking phase — analogous in purpose to CMS's "remark" pause, but Shenandoah's design keeps it similarly short regardless of heap size.
4. `Concurrent evacuation` is where Shenandoah copies live objects out of the regions selected for reclamation into fresh space — critically, this is the traditionally pause-inducing step (physically moving objects) that Shenandoah performs *without* stopping the application, made safe by the forwarding-pointer-plus-barrier mechanism: any application thread reading a reference to an object mid-move is transparently redirected, via the barrier, to whichever copy is currently authoritative.
5. `Pause Init Update Refs` and `Concurrent update references` then walk the heap updating stale references to point directly at objects' new locations (rather than relying on the forwarding pointer indirection forever), again mostly concurrently, with only brief pauses to synchronize the start and end of this reference-fixing pass.
6. `Pause Final Update Refs` finalizes the cycle, after which the old, now-empty regions are available for reuse — the program's final retained count and the surrounding log evidence together confirm that this entire compaction cycle, including physically relocating roughly a gigabyte of live data, completed with every individual stop-the-world pause staying in the sub-millisecond range.

## 7. Gotchas & takeaways

> **Gotcha:** Shenandoah's per-access read/write barrier overhead, like ZGC's load barrier, is paid continuously by the running application, not just during a collection cycle — benchmarking Shenandoah against a traditional collector using only *pause time* as the metric misses this; always also compare total throughput/elapsed time for a fair picture of the actual tradeoff being made.

- Shenandoah achieves ZGC-like sub-millisecond pause times using a forwarding pointer per object plus a read/write barrier, rather than colored pointers — a different mechanism aimed at the same goal: concurrent compaction without a stop-the-world relocation pause.
- Its collection cycle breaks into several short, named stop-the-world pauses (Init/Final Mark, Init/Final Update Refs) bracketing much longer concurrent phases (marking, evacuation, reference updating) that run alongside the application.
- It targets the same use case as [ZGC](0933-zgc.md): large heaps with strict pause-time requirements; the barrier overhead makes it a poor fit for small heaps or pure-throughput batch workloads.
- Choosing between Shenandoah and ZGC on a JDK where both are available often comes down to distribution/vendor support or workload-specific overhead characteristics, rather than a fundamental difference in capability.
- See [ZGC](0933-zgc.md) for the alternative mechanism (colored pointers and a load barrier) achieving a comparable low-pause goal, and [G1](0932-g1-gc.md) for the more throughput-favoring baseline both of these compare against.
