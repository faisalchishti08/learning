---
card: java
gi: 662
slug: zgc-uncommit-unused-memory
title: ZGC uncommit unused memory
---

## 1. What it is

**ZGC uncommit unused memory**, added in **Java 13** (JEP 351), teaches the Z Garbage Collector (ZGC, itself introduced experimentally in Java 11) to return unused heap memory back to the operating system, the same idea covered for G1 in [G1 promptly return unused memory](0655-g1-promptly-return-unused-memory.md) but implemented for ZGC's very different architecture. Before this, ZGC — despite being designed for very large heaps with ultra-low pause times — would keep every region of heap memory it had ever committed, never shrinking back down even after a usage spike passed and the application returned to a much smaller working set. JEP 351 adds a background mechanism (enabled by default) that periodically checks for heap regions no longer in use and uncommits them, controllable primarily through `-Xmx` (max heap) together with `-XX:SoftMaxHeapSize` (Java 13 groundwork) or, in the immediate JEP 351 mechanism, exposed via `-XX:ZUncommitDelay` for how long memory must be idle before it's returned.

## 2. Why & when

ZGC's core value proposition is scaling to very large heaps (multi-terabyte) with pause times that stay in the single-digit-millisecond range regardless of heap size — but a collector built for huge heaps is exactly the kind of collector where holding onto unused committed memory indefinitely is most costly. An application that briefly needs 32 GB during a startup burst or a periodic batch job, then settles into using 2 GB most of the time, would otherwise keep 32 GB reserved from the OS forever under old ZGC behavior — a serious problem in containerized and multi-tenant environments where memory is billed or shared. Uncommitting unused memory lets ZGC-based applications have their cake and eat it too: request a large `-Xmx` ceiling to handle spikes gracefully, while letting the JVM's actual OS-visible footprint shrink back down during quieter periods. This matters whenever you're running ZGC in a container, cloud VM, or any environment where memory footprint (not just peak capacity) is a cost or a scarce resource.

## 3. Core concept

```bash
# ZGC with a generous max heap, but memory returns to the OS when unused
java -XX:+UseZGC -Xmx16g -Xlog:gc+heap MyApp

# Uncommit behavior is on by default in Java 13+; ZUncommitDelay controls
# how long (in seconds) memory must sit idle before ZGC returns it.
java -XX:+UseZGC -Xmx16g -XX:ZUncommitDelay=300 MyApp

# To disable uncommitting entirely (e.g. to keep memory pre-touched/warm):
java -XX:+UseZGC -Xmx16g -XX:-ZUncommit MyApp
```

`-XX:ZUncommitDelay` (default 300 seconds) sets how long a region must remain unused before ZGC considers it safe to release — a cooldown that avoids repeatedly committing/uncommitting the same memory if usage oscillates.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZGC heap usage spikes for a batch job then settles low; after a ZUncommitDelay cooldown, unused committed memory is returned to the OS">
  <line x1="30" y1="160" x2="600" y2="160" stroke="#8b949e" stroke-width="1"/>
  <line x1="30" y1="20" x2="30" y2="160" stroke="#8b949e" stroke-width="1"/>
  <text x="10" y="25" fill="#8b949e" font-size="9" font-family="sans-serif">mem</text>

  <path d="M30,140 L100,140 L150,35 L220,35 L260,140 L600,140" fill="none" stroke="#f85149" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="420" y="130" fill="#f85149" font-size="10" font-family="sans-serif">committed (stays high, uncommit disabled)</text>

  <path d="M30,145 L100,145 L150,40 L220,40 L260,145 L340,145 L360,150 L600,150" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="380" y="172" fill="#6db33f" font-size="10" font-family="sans-serif">uncommit enabled: returns to OS after ZUncommitDelay</text>

  <text x="150" y="30" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">batch job spike</text>
  <line x1="260" y1="145" x2="360" y2="145" stroke="#79c0ff" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="310" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ZUncommitDelay</text>
  <text x="310" y="113" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">cooldown (default 300s)</text>
</svg>

After the spike ends, ZGC waits `ZUncommitDelay` seconds of sustained low usage before releasing the now-idle regions back to the operating system.

## 5. Runnable example

Scenario: a program that simulates a one-time large batch computation followed by a long idle period — first observing memory behavior with default ZGC settings, then shortening the uncommit delay to make the effect observable quickly, then a self-monitoring version that reports its own committed heap size over time using `MemoryMXBean`.

### Level 1 — Basic

```java
// File: BatchSpike.java
import java.util.ArrayList;
import java.util.List;

public class BatchSpike {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> batch = new ArrayList<>();
        System.out.println("Starting batch allocation...");
        for (int i = 0; i < 4000; i++) {
            batch.add(new byte[1024 * 1024]); // ~4 GB total
        }
        System.out.println("Batch done: " + batch.size() + " MB allocated.");

        batch.clear();
        batch = null;
        System.out.println("Batch cleared. Going idle...");
        Thread.sleep(120_000); // idle period long enough to observe uncommit
        System.out.println("Done idling.");
    }
}
```

**How to run:** `java -XX:+UseZGC -Xmx8g BatchSpike.java`

While this runs, monitor process RSS in another terminal (`ps -o rss -p <pid>` on macOS/Linux). Expected behavior: RSS climbs during the batch allocation, then — after the default `ZUncommitDelay` of 300 seconds passes during a longer idle stretch than shown here — would eventually drop back down; within this program's 120-second sleep, the default delay hasn't yet elapsed, so RSS is expected to remain near its peak the whole time.

### Level 2 — Intermediate

**How to run with a much shorter uncommit delay**, so the effect is observable within the same 120-second sleep:
```
java -XX:+UseZGC -Xmx8g -XX:ZUncommitDelay=10 -Xlog:gc+heap BatchSpike.java
```

Expected console output (program messages plus GC heap-region log lines):
```
Starting batch allocation...
Batch done: 4000 MB allocated.
Batch cleared. Going idle...
[15.203s][info][gc,heap] Uncommitted 3072M(37.5%) 4096M->1024M(8192M)
Done idling.
```

With `ZUncommitDelay=10`, once the batch's memory has sat idle for roughly 10 seconds, ZGC's background uncommit mechanism releases the now-unused regions — visible both in the GC heap log and as a drop in the process's RSS observed externally, without any change to the program's own printed output.

### Level 3 — Advanced

```java
// File: BatchSpikeMonitored.java
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;
import java.util.ArrayList;
import java.util.List;

public class BatchSpikeMonitored {
    static void report(String label) {
        MemoryUsage heap = ManagementFactory.getMemoryMXBean().getHeapMemoryUsage();
        System.out.printf("%-20s committed=%dMB used=%dMB%n",
            label, heap.getCommitted() / (1024 * 1024), heap.getUsed() / (1024 * 1024));
    }

    public static void main(String[] args) throws InterruptedException {
        report("startup");

        List<byte[]> batch = new ArrayList<>();
        for (int i = 0; i < 3000; i++) {
            batch.add(new byte[1024 * 1024]);
        }
        report("after batch");

        batch.clear();
        batch = null;
        report("after clear");

        for (int i = 0; i < 6; i++) {
            Thread.sleep(5_000);
            report("idle +" + ((i + 1) * 5) + "s");
        }
    }
}
```

**How to run:** `java -XX:+UseZGC -Xmx6g -XX:ZUncommitDelay=10 BatchSpikeMonitored.java`

Expected output (approximate values):
```
startup              committed=128MB used=12MB
after batch          committed=3200MB used=3072MB
after clear          committed=3200MB used=64MB
idle +5s             committed=3200MB used=58MB
idle +10s            committed=3200MB used=55MB
idle +15s            committed=650MB used=52MB
idle +20s            committed=620MB used=50MB
idle +25s            committed=620MB used=49MB
idle +30s            committed=620MB used=48MB
```

Level 3 mirrors the pattern used for G1 in [G1 promptly return unused memory](0655-g1-promptly-return-unused-memory.md): `used` drops immediately once references are cleared and a collection reclaims the garbage, but `committed` — the memory actually reserved from the OS — only drops once ZGC's periodic uncommit mechanism, gated by `ZUncommitDelay`, has had enough idle time to act, visible here as the sharp drop between the "idle +10s" and "idle +15s" checkpoints.

## 6. Walkthrough

1. `main` calls `report("startup")`, reading the heap's `committed` and `used` figures via `MemoryMXBean` while the JVM is essentially freshly started — both values are small.
2. The loop allocates 3000 one-megabyte `byte[]` objects into `batch`, forcing ZGC to commit additional heap regions from the OS as the live data set grows toward roughly 3 GB. `report("after batch")` shows both `committed` and `used` near that peak.
3. `batch.clear()` and `batch = null` drop every reference to those 3000 arrays, making them garbage. By the time `report("after clear")` runs, a GC cycle has typically already reclaimed most of that memory, so `used` falls sharply — but `committed` stays at its peak, because reclaiming *live-object* space (marking it free) is a different step from *uncommitting* the underlying OS memory pages, which ZGC intentionally defers.
4. The subsequent loop sleeps in 5-second increments, calling `report(...)` after each — this is the "idle" period `ZUncommitDelay=10` is measuring against. During the first two checkpoints (`+5s`, `+10s`), not enough idle time has passed yet, so `committed` remains unchanged even though the memory sits completely unused.
5. Once roughly 10 seconds of sustained idleness have elapsed (matching the configured `ZUncommitDelay`), ZGC's background uncommit mechanism runs: it identifies heap regions that have held no live data for the required cooldown period and returns them to the operating system via the appropriate OS-level memory-release call.
6. This shows up as the sharp drop in `committed` visible between the `"idle +10s"` and `"idle +15s"` checkpoints — the JVM's OS-visible memory footprint contracts from roughly its 3 GB peak down to something much closer to what's actually still needed.
7. Remaining checkpoints (`+20s` through `+30s`) show `committed` staying near its new, lower value, since there's nothing further to reclaim — the process has settled into a footprint proportional to its actual current usage rather than its historical peak.

```
startup: committed=128MB
   │ allocate 3GB
after batch: committed=3200MB, used=3072MB
   │ clear references, GC reclaims live-data bookkeeping
after clear: committed=3200MB (unchanged!), used=64MB (dropped)
   │ idle 10s+ → ZUncommitDelay cooldown elapses → uncommit unused regions
idle +15s: committed=650MB (dropped!), used=52MB
```

## 7. Gotchas & takeaways

> Uncommitting is **enabled by default** in Java 13+ ZGC (unlike G1's periodic-GC memory return, which requires explicitly setting `G1PeriodicGCInterval`), but it's gated by `ZUncommitDelay` (default 300 seconds) — a JVM that goes idle for only a minute or two, then resumes heavy allocation, may never actually uncommit anything, which is intentional: the delay avoids the overhead of repeatedly committing and uncommitting the same memory during normal usage fluctuations. Tune `ZUncommitDelay` down only if you have a specific, measured need for faster memory release in a short-lived or bursty workload.

- ZGC's uncommit behavior is on by default; disable it with `-XX:-ZUncommit` if you specifically want the JVM to hold onto peak committed memory (e.g. to avoid re-commit costs on a workload with frequent, unpredictable spikes).
- `committed` memory (reserved from the OS) and `used` memory (holding live objects) are distinct metrics — dropping references shrinks `used` via normal GC quickly, but shrinking `committed` requires the separate, delayed uncommit mechanism.
- This is architecturally similar in *goal* to G1's [periodic GC memory return](0655-g1-promptly-return-unused-memory.md) but implemented differently, fitting ZGC's region-based, mostly-concurrent design.
- Especially valuable for ZGC users running large-heap-capable JVMs (`-Xmx` set generously to handle spikes) in containers or shared hosts, where actual footprint — not just configured ceiling — determines cost and neighbor impact.
- Verify the effect with `MemoryMXBean.getHeapMemoryUsage().getCommitted()` or OS-level RSS monitoring, since committed-vs-used distinctions aren't visible from simple heap-usage percentage metrics alone.
