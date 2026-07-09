---
card: java
gi: 781
slug: zgc-generational-by-default
title: ZGC generational by default
---

## 1. What it is

**Java 23** (JEP 474) makes **generational mode the default** for the Z Garbage Collector. Where Java 21 introduced [generational ZGC](0749-generational-zgc.md) as an opt-in mode (`-XX:+UseZGC -XX:+ZGenerational`), from Java 23 onward simply passing `-XX:+UseZGC` gives you the generational collector automatically — no extra flag needed. The old single-generation mode still exists but is now **deprecated**, selected only by explicitly passing `-XX:-ZGenerational`, and is slated for eventual removal.

## 2. Why & when

Generational ZGC shipped as a preview-adjacent opt-in specifically so it could accumulate real production usage before the JDK team committed to making it the default — flipping a garbage collector's default behavior affects every application that doesn't pin a specific GC flag, so that decision demands strong evidence it's the right choice for the overwhelming majority of workloads. By Java 23, that evidence was in: generational ZGC's reduced CPU overhead and higher throughput, for the same sub-millisecond pause-time guarantee, held up consistently across the workloads it saw in the field, with essentially no regressions for workloads that don't match the generational hypothesis particularly well. Making it the default reflects that confidence, and it simplifies the on-ramp for anyone adopting ZGC for the first time — `-XX:+UseZGC` alone now gives you the better-performing mode, without needing to know that a second flag existed and mattered.

## 3. Core concept

```
# Java 21-22: generational mode required an explicit flag
java -XX:+UseZGC -XX:+ZGenerational -Xmx4g MyApp

# Java 23+: generational mode is the default — this is now equivalent
java -XX:+UseZGC -Xmx4g MyApp

# Opting back into the deprecated single-generation mode, if needed
java -XX:+UseZGC -XX:-ZGenerational -Xmx4g MyApp
```

The same generational behavior from Java 21's opt-in mode is now what `-XX:+UseZGC` gives you automatically.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 23, plain UseZGC meant single-generation mode and an extra flag was needed for generational mode; from Java 23, plain UseZGC means generational mode by default, with the old mode requiring an explicit opt-out flag">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="160" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java 21-22</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:+UseZGC = single-generation; +ZGenerational opt-in</text>

  <rect x="340" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 23+</text>
  <text x="480" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:+UseZGC = generational by default; -ZGenerational opt-out (deprecated)</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The default flips; the deprecated old mode is still reachable but on its way out</text>
</svg>

*The flag polarity for "which ZGC mode do I get" inverts between Java 22 and Java 23.*

## 5. Runnable example

Scenario: the same allocation-heavy workload used to demonstrate generational ZGC's benefit, growing from Java 21-style explicit flags into confirming Java 23's new default, then explicitly comparing default vs. the now-deprecated legacy mode.

### Level 1 — Basic

```java
import java.util.*;

public class ZgcDefaultBasic {
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

**How to run:** `java -Xmx256m -XX:+UseZGC -Xlog:gc ZgcDefaultBasic.java` (JDK 23+).

No `-XX:+ZGenerational` flag is present at all — on Java 23, `-XX:+UseZGC` alone is enough to get generational ZGC; the `-Xlog:gc` output will show generational-style cycle logging (frequent young-generation collections) even though the flag was never explicitly requested.

### Level 2 — Intermediate

```java
import java.util.*;

public class ZgcDefaultConfirm {
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
        System.out.println("cache size: " + longLivedCache.size());
        System.out.println("+UseZGC generational? " + System.getProperty("java.vm.name"));
    }
}
```

**How to run:** `java -Xmx256m -XX:+UseZGC -Xlog:gc:file=default.log ZgcDefaultConfirm.java`, then inspect `default.log` for generation-tagged GC cycle lines (typically containing `Young` and `Old` phase markers) confirming generational mode ran without any `+ZGenerational` flag.

The real-world concern added: writing the GC log to a file and actually **inspecting it** for evidence of generational behavior — the point being that relying on "it's the default now" without verification is exactly the kind of assumption worth checking once, the same way you'd check any other JDK-version-dependent default.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class ZgcDefaultVsLegacy {
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

**How to run — compare the new default against the deprecated legacy mode:**
```
java -Xmx512m -XX:+UseZGC -Xlog:gc:file=default.log ZgcDefaultVsLegacy.java
java -Xmx512m -XX:+UseZGC -XX:-ZGenerational -Xlog:gc:file=legacy.log ZgcDefaultVsLegacy.java
```

This adds the production-flavored hard case: running the **identical** virtual-thread-heavy, mixed short/long-lived allocation workload twice — once under Java 23's new default (plain `-XX:+UseZGC`) and once under the explicitly-opted-into, now-**deprecated** single-generation mode (`-XX:-ZGenerational`) — so the difference in GC log output and typical throughput is observed directly on the same code, the same way [generational ZGC's introduction](0749-generational-zgc.md) demonstrated the improvement originally, now confirming it's the out-of-the-box behavior.

## 6. Walkthrough

Tracing what differs between the two runs of `ZgcDefaultVsLegacy`:

1. Both runs execute identical application code: 500,000 virtual-thread-backed requests, each allocating 20 short-lived `byte[2048]` buffers and, every 5,000th request, one long-lived `byte[4096]` entry in `connectionPool`.
2. Under the **default** run (`-XX:+UseZGC` alone, Java 23+), the JVM selects generational ZGC without any additional flag — `default.log` shows frequent, cheap young-generation collection cycles handling the flood of short-lived request buffers, with far rarer old-generation cycles handling the trickle of `connectionPool` survivors, exactly as [generational ZGC's own walkthrough](0749-generational-zgc.md) describes.
3. Under the **legacy** run (`-XX:-ZGenerational`, explicitly opting out), the JVM falls back to treating the whole heap as one ungenerationed space — `legacy.log` shows collection cycles that each scan the *entire* live heap, including the long-lived `connectionPool` entries, every single cycle, regardless of how unlikely they are to have become garbage since the last one.
4. Both runs still produce sub-millisecond individual pause times — ZGC's headline pause-time guarantee is unaffected by generational mode either way — but the *default* run typically completes with lower measured total GC CPU time, visible either in wall-clock throughput (the printed `%.2fs`) or more directly by comparing the two log files' cycle counts and per-cycle scanned-heap sizes.
5. Neither run required knowing about `-XX:+ZGenerational` to get the *better* of the two behaviors — that's precisely what "generational by default" delivers: the improved mode is now what you get by doing nothing extra.

Expected output shape (exact timing varies by machine, and is typically similar or slightly favorable for the default run):
```
processed 500,000 requests in 1.7Xs, cache entries=100
```

## 7. Gotchas & takeaways

> **Gotcha:** any existing script, container image, or deployment configuration that explicitly passed `-XX:-ZGenerational` (perhaps copied from older documentation, or set defensively before generational mode was trusted) will, after upgrading to Java 23, **silently keep running the now-deprecated legacy mode** — the JVM won't complain, since the flag is still recognized, just deprecated. Audit JVM flags during a Java 23 upgrade specifically for stray `-ZGenerational`-related settings left over from earlier, more cautious configurations.

- Default flip in Java 23 (JEP 474): `-XX:+UseZGC` alone now selects **generational** ZGC, matching what previously required `-XX:+UseZGC -XX:+ZGenerational` on Java 21-22.
- The old single-generation mode still exists but is **deprecated**, reachable only via the explicit opt-out `-XX:-ZGenerational`, and expected to be removed in a future release.
- Pause-time characteristics are unchanged either way; the difference remains CPU overhead and throughput, as established by [generational ZGC's introduction](0749-generational-zgc.md).
- Upgrading to Java 23 with no ZGC-related flags at all now gets you the generational collector automatically — a meaningful, free improvement for anyone already running plain `-XX:+UseZGC`.
- Review deployment configurations for leftover `-XX:-ZGenerational` flags before or during a Java 23 upgrade, since they now silently opt back into deprecated, less efficient behavior.
