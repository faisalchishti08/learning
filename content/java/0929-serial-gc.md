---
card: java
gi: 929
slug: serial-gc
title: Serial GC
---

## 1. What it is

Serial GC is the simplest garbage collector shipped with the JVM: it uses a single thread to do all collection work, in both the young generation (via [copying](0928-mark-sweep-mark-compact-copying.md)) and the old generation (via mark-compact), and it stops every application thread completely while it runs — a full [stop-the-world pause](0936-stop-the-world-pauses.md), with no attempt at concurrency or parallelism anywhere in the algorithm. It is enabled with `-XX:+UseSerialGC`. There is no coordination overhead to manage, no worker-thread pool to synchronize, and no concurrent bookkeeping to maintain, which makes it the collector with the lowest per-collection overhead of any HotSpot GC — at the direct cost of every pause being fully single-threaded, so its duration scales with live-set size and is not reduced by extra CPU cores.

## 2. Why & when

Serial GC exists for environments where the tradeoffs of more sophisticated collectors don't pay off: small heaps (roughly under a few hundred megabytes), single-core or resource-constrained machines (containers with a CPU limit of 1, embedded devices), and short-lived client-style applications where startup time and memory footprint matter more than minimizing pause duration under load. Because it has no thread-coordination machinery, it has the smallest memory footprint and fastest startup of any collector, and on a genuinely single-core machine it is often *no slower* than a "parallel" collector would be anyway, since there are no spare cores for a worker pool to exploit. It becomes the wrong choice as soon as the heap grows large or low pause times matter, because its pauses are strictly proportional to live-set size with no way to spread the work across cores — a multi-gigabyte heap under Serial GC can produce multi-second pauses that would be sliced down to a fraction of that under [Parallel GC](0930-parallel-gc.md) or a concurrent collector like [G1](0932-g1-gc.md).

## 3. Core concept

```
Application threads running...
        |
        v
[ALL APPLICATION THREADS STOPPED] <-- stop-the-world begins
        |
        v
Single GC thread:
   Young gen:  copying collection (Eden -> Survivor, or Survivor -> Survivor/Old)
   Old gen:    mark-compact (mark reachable, slide survivors together)
        |
        v
[APPLICATION THREADS RESUME] <-- stop-the-world ends
```

Every phase — marking, copying, compacting, reference processing — is executed by exactly one thread, so pause duration is a direct, roughly linear function of how much live data the collector has to trace and move; no core count changes that.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Serial GC pause: all application threads halt while a single GC thread performs young-generation copying and old-generation mark-compact, then threads resume">
  <text x="320" y="18" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Serial GC — one thread does everything</text>
  <rect x="20" y="35" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="54" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">App threads running</text>

  <rect x="220" y="35" width="200" height="120" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="52" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">STOP-THE-WORLD</text>
  <rect x="235" y="65" width="170" height="35" fill="none" stroke="#6db33f"/>
  <text x="320" y="86" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">GC thread #1: copy young gen</text>
  <rect x="235" y="105" width="170" height="35" fill="none" stroke="#6db33f"/>
  <text x="320" y="126" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">GC thread #1: mark-compact old gen</text>

  <rect x="440" y="35" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="54" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">App threads resume</text>

  <text x="320" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only ONE worker thread — pause length scales with live-set size, not core count</text>
</svg>

*A single thread performs the entire collection while every application thread is completely halted.*

## 5. Runnable example

Scenario: measure how Serial GC's pause behavior responds to heap size and retained-data volume, starting with a baseline allocation workload, then adding sustained retention to force old-generation collection, then comparing against a more parallel collector on the same workload to show the concrete difference a single worker thread makes.

### Level 1 — Basic

```java
public class SerialGcBaseline {
    public static void main(String[] args) {
        for (int i = 0; i < 2_000_000; i++) {
            byte[] garbage = new byte[64]; // short-lived, collected by young-gen copying
        }
        System.out.println("done -- check -Xlog:gc output for 'Pause Young (Serial ...)' events");
    }
}
```

**How to run:** `java -Xlog:gc -XX:+UseSerialGC SerialGcBaseline.java` (JDK 17+).

Expected output shape:
```
[0.03s][info][gc] GC(0) Pause Young (Serial Young Collection) ... 4M->1M(16M) 3.1ms
[0.05s][info][gc] GC(1) Pause Young (Serial Young Collection) ... 5M->1M(16M) 2.8ms
...
done -- check -Xlog:gc output for 'Pause Young (Serial ...)' events
```

With only short-lived garbage, all collections stay in the young generation and each pause is small, since the copying step only touches whatever tiny fraction of Eden happens to still be alive.

### Level 2 — Intermediate

```java
import java.util.*;

public class SerialGcOldGenPressure {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 200_000; i++) {
            retained.add(new byte[200]); // promoted into old gen over time, forcing a full GC eventually
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check the log for a 'Pause Full (Serial Old ...)' event -- note its duration");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx64m -XX:+UseSerialGC SerialGcOldGenPressure.java` (JDK 17+; a small heap forces the old generation to fill and trigger a full mark-compact collection).

Expected output shape:
```
[0.02s][info][gc] GC(0) Pause Young (Serial Young Collection) ... 4M->1M(16M) 2.9ms
...
[0.31s][info][gc] GC(14) Pause Full (Serial Old Collection) ... 60M->22M(64M) 145ms
retained: 200000
check the log for a 'Pause Full (Serial Old ...)' event -- note its duration
```

The real-world concern added: sustained retention forces objects to survive long enough to be promoted to the old generation, which eventually triggers a single-threaded full mark-compact — visibly the most expensive pause type Serial GC produces, since it must trace and physically relocate every surviving object in one pass on one thread.

### Level 3 — Advanced

```java
import java.util.*;

public class SerialVsParallelComparison {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.nanoTime();
        for (int i = 0; i < 400_000; i++) {
            retained.add(new byte[300]);
            if (i % 50_000 == 0) {
                for (int j = 0; j < 20_000; j++) {
                    byte[] churn = new byte[128]; // interleave young-gen churn
                }
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("retained: " + retained.size() + ", elapsed: " + elapsedMs + "ms");
    }
}
```

**How to run:** run twice on a multi-core machine and compare total elapsed time and full-GC pause durations from `-Xlog:gc`: `java -Xlog:gc -Xmx128m -XX:+UseSerialGC SerialVsParallelComparison.java` versus `java -Xlog:gc -Xmx128m -XX:+UseParallelGC SerialVsParallelComparison.java` (JDK 17+).

Expected output shape (illustrative — exact numbers vary by machine):
```
(SerialGC):    retained: 400000, elapsed: 810ms   -- fewer, longer single-threaded full-GC pauses
(ParallelGC):  retained: 400000, elapsed: 540ms   -- same algorithm family, multi-threaded, shorter pauses
```

The production-flavored hard case: on a multi-core machine with a genuinely large retained data set, Serial GC's single-threaded full collections become measurably slower than Parallel GC's multi-threaded equivalent doing the same underlying mark-compact work — demonstrating concretely why Serial GC is recommended only for small heaps or genuinely single-core environments where that extra parallelism has nothing to exploit anyway.

## 6. Walkthrough

Tracing `SerialGcOldGenPressure.main` end to end:

1. The loop allocates 200,000 small `byte[]` objects, retaining every one of them in `retained` — nothing here is garbage, so every object survives every young-generation collection it's caught in.
2. Each time Eden fills, a young-generation pause fires: the single GC thread stops all application threads, copies every live object out of Eden (and the active Survivor space) into the other Survivor space, and resumes the application — since `retained` keeps every object alive, this copying step gets more expensive as the list grows, because more and more objects must be copied on each pass rather than being reclaimed as garbage.
3. Objects that survive enough young-generation collections are promoted into the old generation, per the usual generational-GC lifecycle — this promoted population keeps growing since nothing in `retained` is ever released.
4. Once the old generation itself fills (accelerated here by the small `-Xmx64m` cap), a full collection triggers: the single GC thread marks every reachable object across the *entire* heap, then compacts the old generation by sliding survivors together and fixing up references — this is the "Pause Full (Serial Old Collection)" line in the log, and it is the single most expensive event Serial GC produces, since it is single-threaded and touches the whole heap.
5. The program prints the final retained count and exits — logically identical output regardless of which collector ran, but the log above will show the tell-tale long single-threaded full-GC pause, which is the entire point of the exercise: to make Serial GC's behavior directly observable in the log rather than purely theoretical.

## 7. Gotchas & takeaways

> **Gotcha:** Serial GC's pauses do not get shorter on a machine with more CPU cores — since it only ever uses one thread for collection, adding cores helps your *application* run in parallel but does nothing for GC pause duration; picking Serial GC on a large multi-core server with a big heap is usually a configuration mistake, not a deliberate choice.

- Serial GC uses exactly one thread for both young-generation copying and old-generation mark-compact, and stops all application threads for the full duration of every collection.
- It has the lowest overhead and smallest footprint of any HotSpot collector, making it the right choice for small heaps, single-core machines, and short-lived client applications.
- Pause duration scales with live-set size, not with available CPU cores — on a large heap with plenty of spare cores, [Parallel GC](0930-parallel-gc.md) will almost always outperform it.
- The most expensive event it produces is a full collection (mark-compact across the entire old generation), visible in `-Xlog:gc` output as `Pause Full (Serial Old Collection)`.
- See [mark-sweep / mark-compact / copying](0928-mark-sweep-mark-compact-copying.md) for the underlying algorithms Serial GC applies single-threadedly, and [stop-the-world pauses](0936-stop-the-world-pauses.md) for why halting every application thread is necessary at all.
