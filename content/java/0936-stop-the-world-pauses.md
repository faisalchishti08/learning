---
card: java
gi: 936
slug: stop-the-world-pauses
title: Stop-the-world pauses
---

## 1. What it is

A stop-the-world (STW) pause is a period during which the JVM suspends every application thread simultaneously so that some internal operation — most commonly a garbage-collection phase, but also things like deoptimization, biased-lock revocation, or certain JFR/thread-dump operations — can run against a heap and thread state that is guaranteed not to change underneath it. The mechanism behind this is the **safepoint**: a point in generated code where a thread's state is fully known and consistent (no half-finished object allocation, no in-progress stack unwinding), and where the thread can be safely parked. Before a stop-the-world operation can begin, every application thread must first reach a safepoint — the JVM inserts periodic safepoint-poll checks into compiled code specifically so this can happen promptly, and a thread that is, say, in a very long uninterrupted loop with no safepoint poll can actually delay the *entire* pause for every other thread until it finally reaches one.

## 2. Why & when

Stop-the-world pauses exist because many GC operations (most notably relocating/compacting live objects, or finalizing which objects are reachable) are fundamentally unsafe to perform while application threads might simultaneously be reading or writing the very references and objects being moved or classified — without pausing, a thread could observe a half-moved object, a stale reference, or an inconsistent view of what's reachable, leading to memory corruption or incorrect program behavior. Every collector must reckon with this tradeoff somewhere: [Serial](0929-serial-gc.md) and [Parallel GC](0930-parallel-gc.md) accept full, generation-wide stop-the-world pauses as the simplest correct approach; [G1](0932-g1-gc.md) shrinks the *scope* of each pause to a handful of regions rather than a whole generation; and [ZGC](0933-zgc.md) and [Shenandoah](0934-shenandoah.md) go further still, using clever barrier mechanisms to make even object relocation itself safe to do concurrently, leaving only tiny root-synchronization pauses that stay sub-millisecond regardless of heap size. Understanding stop-the-world pauses matters practically whenever you are diagnosing latency spikes in a Java application — a request that mysteriously takes 200ms longer than usual, with no application-level explanation, is very often a stop-the-world GC pause (or a safepoint delayed by one slow-to-reach-safepoint thread) rather than a bug in application logic.

## 3. Core concept

```
Thread A: -----running-----[safepoint poll: reached]---[PARKED]---[resume]-----
Thread B: --running--------[safepoint poll: reached]---[PARKED]---[resume]-----
Thread C: -------------------------running-------------[safepoint poll: reached, FINALLY]---[PARKED]--[resume]--
                                                          ^
                                     Thread C was slow to reach a safepoint --
                                     it delayed the START of the pause for A and B too,
                                     even though they were ready earlier ("time to safepoint").

                        [ALL THREADS NOW PARKED -- the actual STW operation runs here] --[resume all]
```

The pause an application experiences is not just "the GC work itself" — it also includes however long the *slowest* thread took to reach a safepoint, a component often called "time to safepoint" (TTSP), which can itself dominate the perceived pause under certain workloads.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three application threads running at different speeds, each reaching a safepoint poll at a different time, with the actual stop-the-world operation only beginning once the slowest thread arrives">
  <text x="320" y="16" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Time-to-safepoint: the pause waits for the SLOWEST thread</text>

  <line x1="20" y1="40" x2="280" y2="40" stroke="#79c0ff" stroke-width="3"/>
  <circle cx="280" cy="40" r="4" fill="#79c0ff"/>
  <text x="150" y="35" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A: reaches safepoint early</text>

  <line x1="20" y1="75" x2="320" y2="75" stroke="#6db33f" stroke-width="3"/>
  <circle cx="320" cy="75" r="4" fill="#6db33f"/>
  <text x="170" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Thread B: reaches safepoint a bit later</text>

  <line x1="20" y1="110" x2="460" y2="110" stroke="#f0883e" stroke-width="3"/>
  <circle cx="460" cy="110" r="4" fill="#f0883e"/>
  <text x="220" y="105" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Thread C: long loop, slow to reach safepoint -- DELAYS EVERYONE</text>

  <line x1="460" y1="10" x2="460" y2="150" stroke="#8b949e" stroke-dasharray="4"/>
  <rect x="460" y="130" width="120" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="149" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">STW work begins HERE</text>
</svg>

*The stop-the-world pause cannot start until every thread reaches a safepoint — the slowest thread sets the floor for when the pause can even begin.*

## 5. Runnable example

Scenario: observe stop-the-world pause behavior directly — starting with a baseline workload showing normal GC pauses, then deliberately introducing a long safepoint-poll-starved loop to inflate time-to-safepoint, then measuring and comparing the actual application-visible pause impact with JFR-style timing.

### Level 1 — Basic

```java
import java.util.*;

public class StwBaseline {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 200_000; i++) {
            retained.add(new byte[200]);
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check -Xlog:safepoint for safepoint pause entries");
    }
}
```

**How to run:** `java -Xlog:safepoint -Xmx64m StwBaseline.java` (JDK 17+).

Expected output shape:
```
[0.02s][info][safepoint] Safepoint "G1CollectForAllocation", Time since last: 15234567 ns, Reaching safepoint: 120 ns, At safepoint: 1823000 ns, Total: 1943000 ns
...
retained: 200000
check -Xlog:safepoint for safepoint pause entries
```

Each safepoint log entry shows exactly the two components discussed above: "Reaching safepoint" (time to safepoint, waiting for all threads to arrive) and "At safepoint" (the actual paused work, here a GC collection).

### Level 2 — Intermediate

```java
public class StwSlowSafepointArrival {
    public static void main(String[] args) throws InterruptedException {
        Thread slowThread = new Thread(() -> {
            long sum = 0;
            // A tight counted loop over primitives can, in some JIT-compiled forms,
            // go a while between safepoint polls -- simulating a "slow to reach safepoint" thread.
            for (long i = 0; i < 5_000_000_000L; i++) {
                sum += i;
            }
            System.out.println("slow thread finished: " + sum);
        });
        slowThread.start();

        Thread.sleep(200); // let the slow thread get running
        System.gc(); // request a GC -- this must wait for the slow thread to reach a safepoint
        System.out.println("GC requested from main thread");
        slowThread.join();
    }
}
```

**How to run:** `java -Xlog:safepoint -Xlog:gc StwSlowSafepointArrival.java` (JDK 17+).

Expected output shape:
```
GC requested from main thread
[0.45s][info][safepoint] Safepoint "System.gc", Reaching safepoint: 48200000 ns, At safepoint: 900000 ns, Total: 49100000 ns
slow thread finished: ...
```

The real-world concern added: the "Reaching safepoint" component here is disproportionately large relative to "At safepoint" — the actual GC work itself is quick, but waiting for the long-running counted loop to reach its next safepoint poll dominates the total pause, directly illustrating that a single badly-behaved thread can inflate a pause well beyond what the GC work alone would take.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public class StwImpactMeasurement {
    public static void main(String[] args) throws InterruptedException {
        AtomicLong maxObservedGapNs = new AtomicLong(0);
        Thread latencyProbe = new Thread(() -> {
            long last = System.nanoTime();
            while (!Thread.currentThread().isInterrupted()) {
                long now = System.nanoTime();
                long gap = now - last;
                maxObservedGapNs.updateAndGet(prev -> Math.max(prev, gap));
                last = now;
            }
        });
        latencyProbe.setDaemon(true);
        latencyProbe.start();

        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 2_000_000; i++) {
            retained.add(new byte[500]);
        }

        latencyProbe.interrupt();
        System.out.println("retained: " + retained.size());
        System.out.println("max observed scheduling gap (proxy for worst STW pause): "
                + (maxObservedGapNs.get() / 1_000_000) + "ms");
    }
}
```

**How to run:** run under a collector with large pauses versus one with small pauses to see the probe's measured gap change accordingly: `java -Xmx128m -XX:+UseSerialGC StwImpactMeasurement.java` versus `java -Xmx128m -XX:+UseG1GC StwImpactMeasurement.java` (JDK 17+).

Expected output shape (illustrative):
```
(SerialGC): retained: 2000000, max observed scheduling gap (proxy for worst STW pause): 210ms
(G1):       retained: 2000000, max observed scheduling gap (proxy for worst STW pause): 18ms
```

The production-flavored hard case: a busy-spinning "latency probe" thread that records the largest gap between its own consecutive timestamp checks acts as a simple, direct proxy for the worst stop-the-world pause any thread in the JVM actually experienced — since during a real STW pause, even this probe thread is parked and cannot record a timestamp, so the gap it observes directly reflects the pause duration, letting you compare collectors' actual worst-case application-visible impact empirically rather than only from GC log summaries.

## 6. Walkthrough

Tracing `StwSlowSafepointArrival.main` end to end:

1. The main thread starts `slowThread`, which begins a long, tight, primitive counted loop summing values into `sum` — this loop contains no allocation, no method calls, and no I/O, meaning it may go a comparatively long stretch between the safepoint-poll checks the JIT compiler inserts into generated code.
2. After a brief sleep to let `slowThread` get running, the main thread calls `System.gc()`, which requests a full garbage collection — but a garbage collection is a stop-the-world operation, so before it can actually begin, the JVM must first bring *every* application thread (including `slowThread`) to a safepoint.
3. Because `slowThread` is deep in its counted loop, it does not reach its next safepoint-poll check immediately — the JVM's safepoint-synchronization mechanism must wait for it, and this waiting period is exactly what the "Reaching safepoint" component of the safepoint log entry measures.
4. Once `slowThread` finally does reach a safepoint poll, it parks itself, and — with every thread now at a safepoint — the actual stop-the-world garbage collection runs (the "At safepoint" component), which is comparatively brief since the live-object volume here is small.
5. After the collection completes, all threads (including `slowThread`) resume; `slowThread` finishes its loop and prints its sum, and the main thread's `join()` call returns, letting the program exit — the log evidence shows clearly that the *total* pause the application experienced was dominated by time-to-safepoint, not by the GC work itself, which is the core lesson: a stop-the-world pause's duration is not purely a function of collector algorithm or heap size — a single thread that is slow to reach a safepoint can inflate it arbitrarily.

## 7. Gotchas & takeaways

> **Gotcha:** a tight loop over primitives with no method calls, allocations, or field writes can, in specific JIT-compiled forms, go surprisingly long between safepoint-poll checks — this is a real, historically significant source of "GC pauses" that are actually mostly time-to-safepoint, not GC work; if a stop-the-world pause looks far larger than the reported GC work justifies, checking `-Xlog:safepoint`'s "Reaching safepoint" component (not just "At safepoint") is the correct next diagnostic step.

- A stop-the-world pause suspends every application thread so a GC (or other JVM-internal) operation can run against a guaranteed-stable heap and thread state.
- Threads can only be paused at a safepoint — a point where their state is fully consistent — and the JVM must wait for the *slowest* thread to reach one before the actual pause work can begin (time-to-safepoint, or TTSP).
- Different collectors accept stop-the-world pauses of very different scope: [Serial](0929-serial-gc.md)/[Parallel GC](0930-parallel-gc.md) pause for a whole generation, [G1](0932-g1-gc.md) pauses for a handful of regions, and [ZGC](0933-zgc.md)/[Shenandoah](0934-shenandoah.md) pause only for brief root synchronization.
- Diagnosing an unexpectedly large pause should check both components separately: `-Xlog:safepoint`'s "Reaching safepoint" (time-to-safepoint) versus "At safepoint" (the actual operation) — a large gap in the former points to a specific slow-to-reach-safepoint thread, not a GC algorithm problem.
- See [GC tuning flags & ergonomics](0937-gc-tuning-flags-ergonomics.md) for the flags that influence pause frequency and duration directly, and [heap dumps & analysis](0940-heap-dumps-analysis.md) for diagnosing what's actually being retained when pauses are driven by genuine memory pressure rather than safepoint delay.
