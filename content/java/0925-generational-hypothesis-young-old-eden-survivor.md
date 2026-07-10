---
card: java
gi: 925
slug: generational-hypothesis-young-old-eden-survivor
title: Generational hypothesis (young/old/eden/survivor)
---

## 1. What it is

The generational hypothesis is the empirical observation, borne out across decades of real-world measurement, that "most objects die young" — the overwhelming majority of objects allocated in a typical program become garbage very shortly after they're created (a loop's temporary variable, a short-lived request object), while a comparatively small minority survive for a long time (caches, long-lived data structures, singletons). Most mainstream garbage collectors exploit this directly by dividing the [heap](0911-heap.md) into generations: the **young generation** — further split into an **eden** space (where new objects are initially allocated) and (usually two) **survivor** spaces (where objects that survive at least one collection get copied to) — is collected frequently and cheaply, since most of what it holds is expected to already be garbage; the **old generation** holds objects that have survived enough young-generation collections to be "promoted," and is collected far less often, since its contents are expected to mostly still be alive.

## 2. Why & when

This generational split matters because it lets the collector focus its effort where the payoff is highest: since young-generation objects mostly die quickly, a young-generation ("minor") collection can be extremely fast — it only needs to find and copy the small number of *surviving* objects, treating everything else as immediately reclaimable, rather than doing the more expensive work of examining the entire heap. Understanding this explains why object allocation rate (not just total live-object memory) is a genuinely important performance metric — a program allocating huge numbers of short-lived objects triggers frequent (though individually cheap) minor collections — and why objects that unexpectedly survive many young-generation collections (get promoted to the old generation) when they were only ever meant to be short-lived is a specific, recognizable performance anti-pattern worth watching for, since old-generation collections are typically far more expensive and impactful on program pause times than minor collections.

## 3. Core concept

```
Young generation (small, collected frequently, "minor GC")
  Eden       -- where new objects are FIRST allocated
  Survivor 0 -- objects that survived at least 1 minor GC, copied here
  Survivor 1 -- alternates roles with Survivor 0 across collections (a "copying" collector detail)

Old generation (large, collected infrequently, "major/full GC")
  -- objects PROMOTED after surviving enough young-generation collections (an age threshold)
```

A typical object's life: allocated in Eden → survives a minor GC, copied to a survivor space → survives several more minor GCs, bouncing between the two survivor spaces → eventually promoted to the old generation, if it lives long enough — or, far more commonly, simply never survives even the first minor GC at all, reclaimed immediately.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="New objects allocated into Eden; survivors of a minor GC copied to a survivor space; objects surviving enough collections eventually promoted into the old generation, which is collected far less often">
  <rect x="20" y="20" width="380" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="210" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Young generation (frequent, cheap minor GC)</text>
  <rect x="40" y="55" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Eden (new objects)</text>
  <rect x="200" y="55" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="245" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Survivor 0</text>
  <rect x="300" y="55" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="345" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Survivor 1</text>

  <rect x="440" y="20" width="180" height="90" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="530" y="40" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Old generation</text>
  <text x="530" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">infrequent, expensive</text>
  <text x="530" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">major/full GC</text>

  <line x1="180" y1="75" x2="200" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>
  <line x1="390" y1="75" x2="436" y2="60" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#a52)"/>
  <text x="410" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">promoted only after surviving several minor GCs</text>
  <defs><marker id="a52" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Most objects die in Eden and are never promoted; a small minority survive long enough to graduate all the way to the old generation, which is collected far less frequently.*

## 5. Runnable example

Scenario: observing generational behavior directly through GC logging, growing from a baseline demonstrating frequent minor GCs for short-lived allocations, to introducing genuinely long-lived objects to observe promotion, to measuring the cost difference between minor and major collections directly.

### Level 1 — Basic

```java
public class FrequentMinorGcs {
    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 2000; i++) {
            byte[][] shortLived = new byte[1000][]; // ALL of this is garbage almost immediately
            for (int j = 0; j < shortLived.length; j++) {
                shortLived[j] = new byte[1024]; // 1KB each, dies at the end of THIS iteration
            }
            // nothing here retains `shortLived` past this point -- pure garbage generation
        }
        System.out.println("done -- generated and discarded roughly 2GB of short-lived garbage");
    }
}
```

**How to run:** `java -Xlog:gc FrequentMinorGcs.java` (JDK 17+; `-Xlog:gc` enables basic GC logging, showing each collection event).

Expected output shape (many minor/"young" GC events, each fast, reflecting that essentially all this data dies immediately and is cheap to reclaim):
```
[0.045s][info][gc] GC(0) Pause Young ... 4M->1M(64M) 2.1ms
[0.089s][info][gc] GC(1) Pause Young ... 5M->1M(64M) 1.8ms
[0.130s][info][gc] GC(2) Pause Young ... 5M->1M(64M) 1.9ms
...
done -- generated and discarded roughly 2GB of short-lived garbage
```

Notice these are all "Young" (minor) GC events, each fast (a few milliseconds), and each reclaims almost all of the memory it examines — directly reflecting the generational hypothesis: this short-lived allocation pattern is exactly what young-generation collection is optimized for.

### Level 2 — Intermediate

```java
import java.util.*;

public class ObservingPromotion {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> longLived = new ArrayList<>(); // GENUINELY kept alive for the whole program

        for (int i = 0; i < 2000; i++) {
            for (int j = 0; j < 1000; j++) {
                byte[] shortLived = new byte[1024]; // still mostly short-lived garbage, as before
            }
            if (i % 100 == 0) {
                longLived.add(new byte[100_000]); // a SMALL number of genuinely long-lived objects
            }
        }
        System.out.println("long-lived objects retained: " + longLived.size());
        System.out.println("(these SURVIVED enough minor GCs to be PROMOTED to the old generation)");
    }
}
```

**How to run:** `java -Xlog:gc ObservingPromotion.java` (JDK 17+).

Expected output shape (still mostly minor GCs, but note the "after" heap size in later collections trending upward, reflecting genuinely retained, promoted objects accumulating in the old generation):
```
[0.048s][info][gc] GC(0) Pause Young ... 4M->1M(64M) 2.0ms
[0.095s][info][gc] GC(1) Pause Young ... 5M->1M(64M) 1.9ms
...
[0.900s][info][gc] GC(15) Pause Young ... 6M->2M(64M) 2.3ms
...
long-lived objects retained: 20
(these SURVIVED enough minor GCs to be PROMOTED to the old generation)
```

The real-world concern added: a small number of genuinely long-lived objects (retained in `longLived`, an `ArrayList` that lives for the program's entire duration) survive repeated minor GCs and eventually get promoted to the old generation — the "after" heap size in later minor GC log lines creeps up slightly compared to earlier ones, reflecting this small but genuinely accumulating population of promoted, still-alive objects that minor GCs must now account for (even though they don't directly collect the old generation).

### Level 3 — Advanced

```java
import java.util.*;

public class MinorVsMajorGcCost {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> longLived = new ArrayList<>();

        long start = System.nanoTime();
        for (int i = 0; i < 5000; i++) {
            for (int j = 0; j < 1000; j++) {
                byte[] shortLived = new byte[1024];
            }
            longLived.add(new byte[50_000]); // MORE aggressive retention, to eventually force a major/full GC
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total elapsed (including all GC pauses): " + elapsedMs + "ms");
        System.out.println("check the -Xlog:gc output above for the contrast between");
        System.out.println("many fast 'Pause Young' events and any slower 'Pause Full' event");
    }
}
```

**How to run:** `java -Xlog:gc:time,uptime MinorVsMajorGcCost.java` (JDK 17+; the exact `-Xlog:gc` format/detail can vary across JDK versions and the specific garbage collector in use — adjust flags as needed for your JVM to see individual pause durations clearly).

Expected output shape (many fast "Pause Young" events, and — once the old generation itself starts filling up from all the accumulated long-lived retention — at least one noticeably slower "Pause Full" event):
```
[0.05s] GC(0) Pause Young ... 2.1ms
[0.09s] GC(1) Pause Young ... 1.9ms
...
[2.10s] GC(48) Pause Full (Ergonomics) ... 145ms
...
total elapsed (including all GC pauses): 2850ms
check the -Xlog:gc output above for the contrast between
many fast 'Pause Young' events and any slower 'Pause Full' event
```

This adds the production-flavored hard case: aggressive enough long-lived-object retention to eventually exhaust the old generation's own capacity, forcing a "Pause Full" (major/full) collection — directly contrasting the cost of the many small, fast minor collections (a few milliseconds each, reclaiming young-generation garbage) against the comparatively much larger pause of even a single full collection (potentially tens or hundreds of milliseconds, since it must examine the much larger old generation) — concretely demonstrating why minimizing unnecessary promotion of genuinely short-lived data (keeping it dying in the young generation, where collection is cheap) is a meaningful practical performance consideration.

## 6. Walkthrough

Reasoning through the cost asymmetry observed in `MinorVsMajorGcCost.main`:

1. Every iteration of the outer loop allocates 1000 short-lived `byte[1024]` arrays — these are allocated in Eden, and since nothing retains a reference to any of them past their single loop iteration, essentially all of them are already garbage by the time the next minor GC runs.
2. Each minor GC, triggered when Eden fills up, needs to trace only the (comparatively very small) set of objects that are actually still reachable at that moment — mostly just whatever's briefly in flight, plus anything already promoted to a survivor space or the old generation, without needing to scan or reclaim old-generation objects at all — this is exactly why these events are fast, typically a few milliseconds.
3. Meanwhile, each outer iteration also adds a genuinely long-lived `byte[50_000]` array to `longLived`, which is never released — these objects survive every minor GC they're present for (since they remain genuinely reachable via `longLived`), and after surviving enough consecutive minor collections (crossing an age threshold the collector tracks), they get promoted from the young generation's survivor space into the old generation.
4. As this promotion accumulates over thousands of iterations, the old generation itself gradually fills up — eventually, it reaches a point where the collector must perform a full (major) collection, which — unlike a minor collection — needs to examine the old generation's much larger population of objects to determine what's still reachable and reclaim what isn't.
5. This full collection is measurably, often dramatically, more expensive than any individual minor collection, precisely because it's operating over a larger, less selectively-curated portion of the heap — the "Pause Full" event's duration in the log output directly reflects this increased cost.
6. The overall program's total elapsed time (`2850ms` in the illustrative output) is the sum of actual computation time plus every GC pause encountered along the way — the single (or few) full GC pauses, despite being rare events, can meaningfully contribute to that total, disproportionately to how often they occur, exactly because each one costs so much more than any individual minor GC.

## 7. Gotchas & takeaways

> **Gotcha:** an object that's logically meant to be short-lived but is accidentally retained slightly too long (a reference held in a collection that isn't cleared promptly, a cache with no eviction policy) can get unnecessarily promoted into the old generation — once there, it not only occupies old-generation space until an eventual full GC reclaims it, but also adds to the population that any future full GC must examine, compounding the cost; this is a genuinely common, if often subtle, source of avoidable GC pressure in long-running services.

- The generational hypothesis — most objects die young, a few live long — is the empirical basis for splitting the heap into a young generation (Eden plus survivor spaces, collected frequently and cheaply) and an old generation (collected far less often, but more expensively per collection).
- Objects are allocated in Eden; those that survive a minor collection get copied to a survivor space; objects surviving enough consecutive minor collections are promoted to the old generation.
- Minor (young) GCs are fast specifically because they only need to trace the small population of genuinely-surviving objects; major/full GCs are far more expensive since they examine the old generation's much larger, less selectively-curated population.
- Unnecessarily retaining logically-short-lived objects (forcing premature promotion) is a real, avoidable source of increased GC pressure — minimizing this is a meaningful, practical performance consideration for allocation-heavy, long-running programs.
- See [reachability & GC roots](0926-reachability-gc-roots.md) for exactly what determines whether any given object counts as "still alive" during a collection, and [mark-sweep/mark-compact/copying](0928-mark-sweep-mark-compact-copying.md) for the actual algorithms collectors use to identify and reclaim garbage within each generation.
