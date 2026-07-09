---
card: java
gi: 653
slug: shenandoah-gc-experimental
title: Shenandoah GC (experimental)
---

## 1. What it is

**Shenandoah** is a low-pause-time garbage collector contributed by Red Hat, added to OpenJDK as an **experimental** feature in **Java 12** (JEP 189). Its defining trait is that it performs the expensive work of *compacting* the heap (moving live objects together to eliminate fragmentation) **concurrently with your running application threads**, instead of stopping the whole JVM to do it. This keeps GC pause times short and, crucially, roughly **constant regardless of heap size** — a 200 MB heap and a 200 GB heap see similarly short pauses, which is not true of most other collectors. Being "experimental" meant it shipped behind `-XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC` and wasn't considered production-ready or a default choice yet.

## 2. Why & when

Traditional garbage collectors (like the default G1) mostly compact concurrently too, but still need occasional "stop-the-world" pauses whose length tends to grow with the size of the live object set being moved — bigger heaps can mean longer pauses. For applications with strict low-latency requirements (trading systems, real-time services, large in-memory caches) even G1's pauses can be too long as heaps grow into the tens or hundreds of gigabytes. Shenandoah targets exactly that gap: it trades some CPU throughput (concurrent compaction takes more total work) for dramatically shorter, heap-size-independent pauses. Reach for it — once it matured past experimental status in later JDKs — when your priority is minimizing pause times on large heaps, and you can afford somewhat higher CPU usage to get there; stick with G1 (the default) for typical throughput-oriented workloads where pauses in the tens-of-milliseconds range are already acceptable.

## 3. Core concept

```bash
# Enabling Shenandoah in Java 12 (experimental — needs the unlock flag)
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -Xmx4g MyApp

# Compare: default G1
java -XX:+UseG1GC -Xmx4g MyApp

# Observe pause behavior
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -Xlog:gc MyApp
```

The key architectural difference: Shenandoah uses **Brooks pointers** (an extra indirection word per object) so it can move an object to a new location while application threads keep reading/writing through the old reference — the pointer transparently redirects to the new location, letting compaction happen without stopping the app to fix up every reference at once.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Traditional stop-the-world compaction pauses the whole app; Shenandoah compacts concurrently while the app keeps running">
  <rect x="10" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="42" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Stop-the-world compaction</text>
  <rect x="25" y="55" width="260" height="20" fill="#3fb950" opacity="0.6"/>
  <text x="155" y="69" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">app running</text>
  <rect x="25" y="80" width="260" height="30" fill="#f85149"/>
  <text x="155" y="99" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">PAUSE — compacting (app frozen)</text>
  <rect x="25" y="115" width="260" height="20" fill="#3fb950" opacity="0.6"/>
  <text x="155" y="129" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">app running</text>
  <text x="25" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">Pause length grows with</text>
  <text x="25" y="174" fill="#8b949e" font-size="9" font-family="sans-serif">the size of live data moved.</text>

  <rect x="320" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Shenandoah concurrent compaction</text>
  <rect x="335" y="55" width="260" height="80" fill="#3fb950" opacity="0.6"/>
  <text x="465" y="80" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">app running</text>
  <text x="465" y="98" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">+ GC compacting concurrently</text>
  <text x="465" y="114" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">(via Brooks-pointer indirection)</text>
  <rect x="335" y="140" width="260" height="10" fill="#f85149"/>
  <text x="465" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only brief, near-constant pauses</text>
  <text x="465" y="174" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">regardless of heap size</text>
</svg>

Shenandoah shrinks the red "frozen app" window to a sliver, moving nearly all compaction work into the green "app still running" zone.

## 5. Runnable example

Scenario: observing how a heap-heavy allocation workload behaves under different collectors — first running it with the default collector, then switching to Shenandoah, then adding GC logging to compare pause behavior directly.

### Level 1 — Basic

```java
// File: AllocatorApp.java
import java.util.ArrayList;
import java.util.List;

public class AllocatorApp {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> retained = new ArrayList<>();
        long start = System.currentTimeMillis();

        for (int i = 0; i < 200_000; i++) {
            byte[] chunk = new byte[1024]; // 1 KB
            if (i % 50 == 0) {
                retained.add(chunk); // keep some objects alive to force real GC work
            }
            if (retained.size() > 2000) {
                retained.remove(0); // let old ones become garbage
            }
        }

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Allocated 200,000 chunks in " + elapsed + " ms");
        System.out.println("Retained list size at end: " + retained.size());
    }
}
```

**How to run (default G1):** `java AllocatorApp.java`

Expected output (timings vary by machine):
```
Allocated 200,000 chunks in 45 ms
Retained list size at end: 2000
```

### Level 2 — Intermediate

**How to run with Shenandoah instead:**
```
javac AllocatorApp.java
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC AllocatorApp
```

(If your JDK build wasn't compiled with Shenandoah support, this flag will fail with "Unrecognized VM option" — Shenandoah must be included at JDK build time; most mainstream OpenJDK builds from JDK 12+ Linux/macOS distributions include it, though not all Windows or vendor builds do.)

Expected output is functionally the same program result:
```
Allocated 200,000 chunks in 52 ms
Retained list size at end: 2000
```

The program's *output* doesn't change — Shenandoah is a drop-in collector swap. What changes is pause behavior, which raw wall-clock timing of the whole program doesn't clearly reveal; Level 3 adds GC logging to actually see it.

### Level 3 — Advanced

```java
// File: AllocatorLogged.java
import java.util.ArrayList;
import java.util.List;

public class AllocatorLogged {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();

        for (int round = 0; round < 5; round++) {
            long roundStart = System.nanoTime();
            for (int i = 0; i < 500_000; i++) {
                byte[] chunk = new byte[512];
                if (i % 20 == 0) retained.add(chunk);
                if (retained.size() > 5000) retained.remove(0);
            }
            long roundMs = (System.nanoTime() - roundStart) / 1_000_000;
            System.out.println("Round " + round + " took " + roundMs + " ms, retained=" + retained.size());
        }
    }
}
```

**How to run, with GC pause logging enabled:**
```
javac AllocatorLogged.java
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -Xlog:gc AllocatorLogged
```

Expected output includes interleaved application progress lines and GC log lines such as:
```
[0.045s][info][gc] GC(0) Concurrent reset 1234K->1234K(4096K) 0.512ms
[0.046s][info][gc] GC(0) Pause Init Mark 0.089ms
[0.102s][info][gc] GC(0) Concurrent marking 1234K->2048K(4096K) 5.612ms
[0.103s][info][gc] GC(0) Pause Final Mark 0.145ms
[0.150s][info][gc] GC(0) Concurrent evacuation ...
Round 0 took 38 ms, retained=5000
...
```

Level 3's `-Xlog:gc` flag prints each GC cycle's phases: note that phases labeled `Concurrent ...` run alongside your program's rounds (their timestamps overlap with round execution), while only the brief `Pause Init Mark` and `Pause Final Mark` phases actually stop application threads — everything else, including the heavy compaction/evacuation work, happens concurrently.

## 6. Walkthrough

1. The JVM starts `AllocatorLogged` with Shenandoah selected via the command-line flags; the GC subsystem initializes its concurrent worker threads before `main` even begins.
2. `main` enters the outer loop (`round = 0`). The inner loop runs 500,000 iterations, each allocating a 512-byte `byte[]` — this is a fast, cheap allocation from the current "young"-style region, not something the pause-sensitive compaction machinery is involved in yet.
3. As allocations accumulate and `retained` grows past its cap, old entries removed via `retained.remove(0)` become garbage — unreachable objects the collector will eventually reclaim.
4. Once heap occupancy crosses an internal threshold, Shenandoah's concurrent GC cycle triggers **in the background**, on its own threads, without stopping `main`'s loop. The log shows this as `Concurrent reset`, `Concurrent marking`, and `Concurrent evacuation` phases — each takes measurable wall-clock time but does *not* block application progress.
5. Only two short synchronization points actually pause application threads: `Pause Init Mark` (briefly stops the world to record initial GC roots before concurrent marking begins) and `Pause Final Mark` (briefly stops the world to finish marking after the concurrent phase). Both are logged with pause durations typically well under a millisecond in the sample output — this is the heap-size-independent guarantee Shenandoah is built around.
6. After the round's 500,000 allocations finish, `roundMs` is computed from `System.nanoTime()`, and `"Round 0 took ... ms, retained=5000"` prints — the timing reflects allocation work plus whatever brief pauses occurred, not a single large stop-the-world compaction.
7. The outer loop repeats for rounds 1 through 4, and each round can trigger its own concurrent GC cycle depending on allocation pressure, visible as additional interleaved `GC(1)`, `GC(2)`, ... log entries between the round-progress lines.

```
main thread:  [--- round 0 allocating ---][--- round 1 allocating ---]...
GC threads:        [Concurrent marking][Concurrent evacuation]   (runs alongside, not blocking)
pauses:            ^Init Mark (brief)                 ^Final Mark (brief)
```

## 7. Gotchas & takeaways

> As an **experimental** feature in Java 12, Shenandoah required `-XX:+UnlockExperimentalVMOptions` and was not included in every JDK build/vendor distribution — attempting to enable it on a build without Shenandoah support fails immediately with an "Unrecognized VM option" error at startup, not a graceful fallback. Always verify your specific JDK distribution includes it before depending on it.

- Shenandoah trades CPU throughput for pause-time consistency: expect somewhat higher CPU usage in exchange for pauses that don't grow with heap size.
- The Brooks-pointer indirection (one extra word per object) is the mechanism that lets application threads keep working while objects are being relocated — a small memory/access overhead for a big latency win.
- It became production-ready (no longer experimental) in later JDK versions — the Java 12 label specifically meant "usable for evaluation, not yet guaranteed stable for production."
- Good fit: large heaps with strict low-latency requirements. Poor fit: workloads that are CPU-throughput-bound where any extra background GC work directly competes with application work.
- Always benchmark with GC logging (`-Xlog:gc`) rather than trusting wall-clock program time alone — pause-time improvements are invisible in total runtime but very visible in per-request latency for real services.
