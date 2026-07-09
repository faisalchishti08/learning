---
card: java
gi: 792
slug: generational-shenandoah-experimental
title: Generational Shenandoah (experimental)
---

## 1. What it is

**Java 24** (JEP 404) adds an **experimental generational mode** to the Shenandoah garbage collector, enabled with `-XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational`. Like [generational ZGC](0749-generational-zgc.md), it splits the heap into a **young generation** for newly allocated, short-lived objects and an **old generation** for longer-lived survivors, applying the generational hypothesis (most objects die young) to reduce the total collector work needed to keep pace with allocation — while preserving Shenandoah's existing low-pause-time character. Being marked **experimental**, it must be explicitly unlocked with `-XX:+UnlockExperimentalVMOptions` and is not yet recommended for production use without careful evaluation.

## 2. Why & when

Shenandoah, like ZGC, was originally built as a single-generation collector: the whole heap treated as one region, scanned in its entirety on every collection cycle. That design delivers Shenandoah's headline feature — pause times that don't scale with heap size — but at the cost of doing more total collection work than necessary for workloads where most objects genuinely die young and a smaller fraction survive long-term, which describes the overwhelming majority of real applications. Generational ZGC proved out this same idea for ZGC across several stable releases; generational Shenandoah applies the identical reasoning to Shenandoah's collector, letting teams already committed to Shenandoah (rather than ZGC) get the same category of CPU-overhead improvement, without having to switch collectors entirely just to gain generational behavior. The experimental flag exists precisely because this is new: unlike ZGC's now-default generational mode, Shenandoah's generational mode needs its own round of real-world validation before the JDK team is ready to promote it, deprecate the old mode, or eventually flip the default the way JEP 474 did for ZGC.

## 3. Core concept

```
# Experimental generational Shenandoah — requires explicitly unlocking experimental options
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational -Xmx4g -Xlog:gc MyApp

# Compare against Shenandoah's traditional single-generation mode
java -XX:+UseShenandoahGC -XX:ShenandoahGCMode=satb -Xmx4g -Xlog:gc MyApp
```

Both modes share Shenandoah's low-pause-time design; the generational mode changes how much total collection work is needed, not the pause-time guarantee itself.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Generational Shenandoah, like generational ZGC, splits the heap into a frequently-collected young generation and a rarely-collected old generation, but remains experimental and requires unlocking experimental VM options">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">-XX:+UnlockExperimentalVMOptions -XX:ShenandoahGCMode=generational</text>

  <rect x="20" y="90" width="260" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="112" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Young generation</text>
  <text x="150" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">collected often, mostly garbage</text>

  <rect x="300" y="90" width="320" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="460" y="112" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Old generation</text>
  <text x="460" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">collected rarely, mostly live</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same low-pause design as non-generational Shenandoah, less total collector work — still experimental</text>
</svg>

*The same generational strategy proven by ZGC, now applied to Shenandoah, one release before it's considered stable.*

## 5. Runnable example

Scenario: the same short-lived-buffer-plus-small-cache workload used to demonstrate generational ZGC, run instead under generational Shenandoah, growing into a direct comparison against Shenandoah's traditional mode.

### Level 1 — Basic

```java
import java.util.*;

public class ShenandoahGenBasic {
    public static void main(String[] args) {
        List<byte[]> shortLived;
        for (int round = 0; round < 200_000; round++) {
            shortLived = new ArrayList<>();
            for (int i = 0; i < 10; i++) {
                shortLived.add(new byte[1024]);
            }
        }
        System.out.println("done allocating");
    }
}
```

**How to run:** `java -Xmx256m ShenandoahGenBasic.java` (JDK 24+; a baseline run with no special GC flags yet).

The familiar "most objects die young" workload from earlier generational-collector examples — 2,000,000 short-lived 1 KB buffers, discarded almost immediately after allocation.

### Level 2 — Intermediate

```java
import java.util.*;

public class ShenandoahGenWithSurvivors {
    static final List<byte[]> longLivedCache = new ArrayList<>();

    public static void main(String[] args) {
        for (int round = 0; round < 200_000; round++) {
            List<byte[]> shortLived = new ArrayList<>();
            for (int i = 0; i < 10; i++) {
                shortLived.add(new byte[1024]);
            }
            if (round % 1000 == 0) {
                longLivedCache.add(new byte[1024]);
            }
        }
        System.out.println("cache size (long-lived survivors): " + longLivedCache.size());
    }
}
```

**How to run:** `java -Xmx256m -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational -Xlog:gc ShenandoahGenWithSurvivors.java`.

The real-world concern added: a small, genuinely long-lived `longLivedCache` mixed in with the flood of short-lived garbage — under `-Xlog:gc`, generational Shenandoah's log output should show frequent young-generation cycles and far rarer old-generation ones, mirroring what generational ZGC shows for the equivalent workload.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class ShenandoahGenProduction {
    static final Map<Integer, byte[]> connectionPool = new ConcurrentHashMap<>();

    static void handleRequest(int requestId) {
        List<byte[]> buffers = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            buffers.add(new byte[2048]);
        }
        if (requestId % 5000 == 0) {
            connectionPool.put(requestId, new byte[4096]);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.nanoTime();
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 500_000; i++) {
                int requestId = i;
                executor.submit(() -> handleRequest(requestId));
            }
        }
        double seconds = (System.nanoTime() - start) / 1e9;
        System.out.printf("processed 500,000 requests in %.2fs, cache entries=%d%n",
            seconds, connectionPool.size());
    }
}
```

**How to run — compare generational against traditional Shenandoah:**
```
java -Xmx512m -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational -Xlog:gc:file=gen.log ShenandoahGenProduction.java
java -Xmx512m -XX:+UseShenandoahGC -XX:ShenandoahGCMode=satb -Xlog:gc:file=trad.log ShenandoahGenProduction.java
```

This adds the production-flavored hard case: 500,000 concurrent virtual-thread-backed requests, each allocating short-lived buffers with an occasional long-lived cache entry, run once under experimental generational Shenandoah and once under Shenandoah's traditional (`satb`) mode — with GC log output from both compared directly, the same evaluation approach that would confirm (or refute) generational mode's benefit for a specific real workload before committing to it in production.

## 6. Walkthrough

Tracing what happens during one run of `ShenandoahGenProduction` under experimental generational Shenandoah:

1. `main` starts a timer, opens a virtual-thread-per-task executor, and submits 500,000 tasks, each calling `handleRequest`.
2. Each `handleRequest` allocates 20 short-lived `byte[2048]` buffers into a local list that goes out of scope immediately after the method returns — the dominant source of allocation, and nearly all of it dies within microseconds.
3. Every 5,000th request additionally inserts a `byte[4096]` entry into the shared `connectionPool`, representing a small trickle of genuinely long-lived state.
4. Under generational Shenandoah, the young-generation collector handles the flood of short-lived request buffers frequently and cheaply, since most of what it scans is already garbage by the time it runs; the old generation, holding the rare `connectionPool` survivors, is scanned far less often.
5. Once all 500,000 tasks complete, the executor's try-with-resources block closes, `main` computes elapsed time, and prints the summary.
6. Comparing `gen.log` (generational) against `trad.log` (traditional `satb` mode) would typically show generational mode logging more frequent, cheaper young-generation cycles and less total GC CPU time for the same workload — the same qualitative pattern established by generational ZGC, now measured for Shenandoah specifically.

Expected output shape (exact timing varies by machine and JDK build; being experimental, results may also vary release to release as the implementation matures):
```
processed 500,000 requests in 1.9Xs, cache entries=100
```

## 7. Gotchas & takeaways

> **Gotcha:** "experimental" is a stronger caution here than it might sound — unlike generational ZGC (which spent time as an opt-in stable feature before becoming default), generational Shenandoah has not yet had that stabilization period. Treat any performance numbers you measure from it as provisional, re-validate after upgrading to newer JDK releases as the implementation continues to mature, and avoid depending on it for production workloads without your own careful evaluation and a fallback plan.

- Experimental in Java 24 (JEP 404) — requires both `-XX:+UnlockExperimentalVMOptions` and `-XX:+UseShenandoahGC -XX:ShenandoahGCMode=generational`.
- Applies the same generational strategy as [generational ZGC](0749-generational-zgc.md) to Shenandoah: frequent, cheap young-generation collections plus rare old-generation collections, same pause-time character as before.
- Best suited to workloads matching the generational hypothesis — most objects short-lived, a smaller long-lived remainder — the same profile that benefits from generational ZGC.
- Use `-Xlog:gc` to observe collection frequency and cost directly, and compare against Shenandoah's traditional mode on your actual workload before adopting it.
- Given its experimental status, expect continued changes before (if) it eventually stabilizes and potentially becomes Shenandoah's default, mirroring ZGC's own path from opt-in to default.
