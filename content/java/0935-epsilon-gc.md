---
card: java
gi: 935
slug: epsilon-gc
title: Epsilon GC
---

## 1. What it is

Epsilon (available since Java 11, via `-XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC`) is a deliberately minimal, "do-nothing" garbage collector: it allocates memory exactly like any other collector's young generation, but it never reclaims anything at all. Once the heap fills up, the JVM throws an `OutOfMemoryError` and terminates — there is no marking, no sweeping, no compaction, no collection cycle of any kind. It exists specifically as a control and measurement tool rather than a production reclaiming strategy, giving developers a way to measure a program's true, unmediated allocation cost and memory footprint with zero GC-induced noise in the measurement.

## 2. Why & when

Epsilon is useful in a small number of specific, well-understood scenarios: performance testing, where you want to measure the absolute lower bound on allocation and pause overhead a real collector could ever achieve (since any real collector adds *some* overhead on top of what Epsilon shows); extremely short-lived processes where the entire program runs and exits well before the heap could plausibly fill (a serverless function invocation, a one-shot CLI tool) — memory that's never reclaimed doesn't matter if the process is about to end anyway; and last-resort testing of memory pressure — deliberately using Epsilon to find the exact allocation pattern that would cause a program to run out of memory, without any collector intervening to delay or mask the failure. It is never appropriate for a real, long-running production service with unbounded or even just large allocation volume, since there is no reclamation mechanism whatsoever — the heap fills monotonically and the JVM will eventually and unavoidably crash with an `OutOfMemoryError`.

## 3. Core concept

```
Normal collector:  allocate -> [heap fills] -> COLLECT (reclaim garbage) -> allocate -> ...
                                                     ^^^^^^^^^^^^^^^^^^^^^^
                                                     repeats indefinitely

Epsilon:           allocate -> allocate -> allocate -> ... -> [heap fills] -> OutOfMemoryError
                               (no collection step exists at all)
```

Epsilon is, in effect, a baseline: whatever allocation throughput and latency a program achieves under Epsilon represents the theoretical ceiling any real collector's overhead is subtracted from.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Heap occupancy under a normal collector oscillating between allocation and collection versus Epsilon GC which rises monotonically until an OutOfMemoryError">
  <text x="150" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Normal collector: heap occupancy over time</text>
  <polyline points="20,60 60,30 65,55 110,25 115,50 160,20 165,48 210,22 215,50 260,25" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">sawtooth: allocate up, collect down, repeat</text>

  <text x="480" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Epsilon GC: heap occupancy over time</text>
  <line x1="380" y1="60" x2="600" y2="20" stroke="#f0883e" stroke-width="2"/>
  <text x="490" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">straight line up -- NO collection, ever</text>

  <line x1="600" y1="20" x2="600" y2="5" stroke="#f0883e" stroke-dasharray="2"/>
  <text x="600" y="130" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">heap full -&gt; OutOfMemoryError, JVM exits</text>
</svg>

*Where a normal collector's heap occupancy oscillates as it repeatedly reclaims garbage, Epsilon's occupancy rises monotonically until the heap is exhausted.*

## 5. Runnable example

Scenario: measure a program's raw, uncollected allocation behavior — starting with a basic Epsilon-enabled workload that intentionally stays under the heap limit, then deliberately exceeding it to observe the guaranteed `OutOfMemoryError`, then using Epsilon as a measurement baseline compared against a real collector on identical allocation-heavy code.

### Level 1 — Basic

```java
public class EpsilonWithinBudget {
    public static void main(String[] args) {
        // Allocate a bounded, known amount that comfortably fits the heap -- no collection needed.
        for (int i = 0; i < 100_000; i++) {
            byte[] data = new byte[100];
        }
        System.out.println("done -- completed without needing any garbage collection at all");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx64m EpsilonWithinBudget.java` (JDK 17+).

Expected output:
```
done -- completed without needing any garbage collection at all
```

Since total allocation here (roughly 10 MB across the loop, mostly immediately eligible for reclamation under a real collector) stays well under the 64 MB heap cap, Epsilon never needs to reclaim anything — the program runs to completion exactly as if garbage were free, since Epsilon never even attempts to identify or reclaim it.

### Level 2 — Intermediate

```java
public class EpsilonExceedingBudget {
    public static void main(String[] args) {
        long count = 0;
        try {
            for (int i = 0; i < 100_000_000; i++) {
                byte[] data = new byte[1024]; // 1KB per iteration -- will exceed a small heap
                count++;
            }
        } finally {
            System.out.println("allocated " + count + " objects before running out of memory");
        }
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx32m EpsilonExceedingBudget.java` (JDK 17+; deliberately small heap to force exhaustion quickly).

Expected output shape:
```
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
        at EpsilonExceedingBudget.main(EpsilonExceedingBudget.java:5)
allocated 31234 objects before running out of memory
```

The real-world concern added: this demonstrates Epsilon's defining, deliberate limitation directly — because nothing is ever reclaimed, even short-lived garbage accumulates permanently, and a workload that a real collector would run indefinitely under (since the `byte[] data` objects are immediately unreachable after each iteration) instead exhausts a 32 MB heap in well under a second.

### Level 3 — Advanced

```java
public class EpsilonAsMeasurementBaseline {
    public static void main(String[] args) {
        long start = System.nanoTime();
        long total = 0;
        for (int i = 0; i < 500_000; i++) {
            byte[] data = new byte[128];
            total += data.length;
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total bytes touched: " + total + ", elapsed: " + elapsedMs + "ms");
    }
}
```

**How to run:** compare raw allocation throughput against a real collector on identical code and a heap sized to comfortably fit the whole run without exhausting: `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx512m EpsilonAsMeasurementBaseline.java` versus `java -XX:+UseG1GC -Xmx512m EpsilonAsMeasurementBaseline.java` (JDK 17+).

Expected output shape (illustrative):
```
(Epsilon): total bytes touched: 64000000, elapsed: 38ms   -- zero GC overhead, pure allocation cost
(G1):      total bytes touched: 64000000, elapsed: 52ms   -- includes real collection cycles' overhead
```

The production-flavored hard case: with the heap sized generously enough that even a real collector barely needs to run, the remaining gap between Epsilon's time and G1's time isolates roughly what G1's bookkeeping and any collection cycles it did run actually cost — exactly the kind of controlled, GC-overhead-isolating measurement Epsilon is built to enable.

## 6. Walkthrough

Tracing `EpsilonExceedingBudget.main` end to end:

1. The loop begins allocating 1 KB `byte[]` arrays in a tight loop, intending to run 100 million iterations — under any real collector, each `data` array becomes unreachable garbage the very next iteration (nothing retains a reference to it), so a real young-generation collector would reclaim this space continuously and the loop could, in principle, run indefinitely.
2. Under Epsilon, none of that reclamation happens — every single allocated array's memory remains committed and unavailable for reuse for the entire remainder of the program's life, regardless of reachability, because Epsilon has no marking or sweeping logic at all.
3. As iterations proceed, heap occupancy therefore rises monotonically and linearly with the total bytes allocated so far — roughly 1 KB per iteration — with no oscillation or reclamation ever bringing it back down.
4. Once occupancy reaches the `-Xmx32m` cap, the very next allocation attempt fails outright: the JVM throws `OutOfMemoryError: Java heap space` at the exact allocation site (`new byte[1024]` inside the loop), since there is no fallback strategy — no full GC to attempt, no compaction to try — Epsilon simply has nothing left to offer.
5. The `finally` block still runs (as Java guarantees), printing however many objects were successfully allocated before the failure — this count is deterministic given a fixed heap size and per-iteration allocation size, since Epsilon's occupancy growth is exactly linear and predictable, unlike a real collector's occupancy, whose failure point (if it ever failed at all) would depend on live-set size, not total allocation volume.
6. The program then terminates with a non-zero exit status, having demonstrated exactly the tradeoff Epsilon makes explicit: total absence of collection overhead, in exchange for a hard, unavoidable ceiling on total lifetime allocation volume.

## 7. Gotchas & takeaways

> **Gotcha:** Epsilon requires `-XX:+UnlockExperimentalVMOptions` alongside `-XX:+UseEpsilonGC` — it is intentionally gated as an experimental option, a signal that it is not meant for casual or accidental production use; running a real service under Epsilon by mistake (for example, via a copy-pasted benchmarking flag left in a deployment config) will eventually and unavoidably crash the process once the heap fills, with no warning beyond the eventual `OutOfMemoryError`.

- Epsilon allocates memory normally but never reclaims any of it — there is no marking, sweeping, or compaction step at all, by design.
- Once the heap fills, the JVM throws `OutOfMemoryError` and the process must exit; there is no fallback or recovery path.
- Its main legitimate uses are performance measurement (isolating true allocation cost with zero GC-induced noise), extremely short-lived processes that will exit before the heap could fill, and deliberately testing an application's memory-pressure behavior.
- It is never appropriate for a real long-running production service, since any nonzero sustained allocation rate makes an eventual crash a certainty, not a possibility.
- Compare it conceptually against real collectors like [Serial](0929-serial-gc.md), [Parallel](0930-parallel-gc.md), [G1](0932-g1-gc.md), [ZGC](0933-zgc.md), and [Shenandoah](0934-shenandoah.md) — all of which trade some overhead for the ability to run indefinitely; Epsilon trades that ability away entirely to show what "zero GC overhead" actually costs.
