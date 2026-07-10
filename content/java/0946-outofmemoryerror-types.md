---
card: java
gi: 946
slug: outofmemoryerror-types
title: OutOfMemoryError types
---

## 1. What it is

`OutOfMemoryError` is not a single, undifferentiated failure — the JVM throws it with a specific message describing *which* memory region was exhausted, and each message points at a genuinely different root cause and fix. The most common variants are: **`Java heap space`** (the heap itself is full of live, reachable objects — a genuine [memory leak](0938-memory-leaks-in-managed-memory.md) or simply an undersized `-Xmx`); **`GC overhead limit exceeded`** (the JVM detects it's spending an excessive proportion of total time doing garbage collection while reclaiming very little each time — a specific heuristic meant to fail fast rather than let an application limp along, spending, say, 98% of its time in GC for a vanishingly small return); **`Metaspace`** (class metadata has exhausted the space reserved for it — commonly from dynamically generating and loading huge numbers of classes without ever unloading them, a classic symptom in applications using heavy dynamic proxying or certain application-server class-loading patterns); **`unable to create new native thread`** (the operating system refused to create another OS-level thread for the JVM, typically because the process has already created too many threads relative to available memory or the OS's per-process thread limit — this is a *native*, not heap, resource exhaustion); and **`Direct buffer memory`** (native, off-heap memory reserved for `ByteBuffer.allocateDirect` or similar has been exhausted, independent of the regular heap entirely).

## 2. Why & when

Correctly reading the specific `OutOfMemoryError` message is the single most important first step in diagnosing it, because the fixes for these variants are almost entirely non-overlapping: raising `-Xmx` helps `Java heap space` and `GC overhead limit exceeded` (if the underlying issue really is just an undersized heap for a legitimately large live-data volume), but does nothing whatsoever for `unable to create new native thread` (which is about the OS thread limit and per-thread stack memory, not the heap) or `Metaspace` (which needs `-XX:MaxMetaspaceSize` raised, or, better, finding and fixing whatever is generating unbounded numbers of classes). Recognizing `GC overhead limit exceeded` specifically as its own signal matters because it usually means the application *could* keep technically running (each collection does reclaim a little) but is doing so at a ratio of GC time to useful work so poor that the JVM has decided failing fast and loud is more useful than limping along invisibly slow — treating this identically to a plain heap-space exhaustion (just raising `-Xmx` without also investigating *why* so little gets reclaimed each cycle) often just delays the same failure rather than fixing it.

## 3. Core concept

```
OutOfMemoryError message                 -> which resource        -> typical real cause
--------------------------------------------------------------------------------------------
"Java heap space"                        -> heap                  -> leak, or -Xmx too small
"GC overhead limit exceeded"             -> heap (GC efficiency)   -> collecting constantly,
                                                                       reclaiming almost nothing
"Metaspace"                              -> class metadata area    -> unbounded dynamic class
                                                                       generation/loading
"unable to create new native thread"     -> OS threads / native mem -> too many threads created,
                                                                       OS or ulimit exhausted
"Direct buffer memory"                   -> native off-heap buffers -> ByteBuffer.allocateDirect
                                                                       never released/GC'd promptly
```

Each row above requires a genuinely different fix — the message text itself is the single most important clue, and should always be read carefully before reaching for any specific remedy.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five distinct memory regions of a JVM process, each capable of independently triggering a differently-worded OutOfMemoryError when exhausted" >
  <rect x="20" y="30" width="110" height="130" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Heap</text>
  <text x="75" y="100" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"Java heap space"</text>
  <text x="75" y="115" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"GC overhead limit"</text>

  <rect x="145" y="30" width="110" height="130" fill="#1c2430" stroke="#79c0ff"/>
  <text x="200" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Metaspace</text>
  <text x="200" y="100" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"Metaspace"</text>

  <rect x="270" y="30" width="110" height="130" fill="#1c2430" stroke="#8b949e"/>
  <text x="325" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OS threads</text>
  <text x="325" y="100" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"unable to create</text>
  <text x="325" y="112" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">new native thread"</text>

  <rect x="395" y="30" width="110" height="130" fill="#1c2430" stroke="#e6edf3"/>
  <text x="450" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Direct buffers</text>
  <text x="450" y="100" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"Direct buffer</text>
  <text x="450" y="112" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">memory"</text>

  <text x="320" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each region fails independently -- the error message names exactly which one</text>
</svg>

*Five independent memory regions, each capable of exhaustion on its own — the specific error message names exactly which one failed.*

## 5. Runnable example

Scenario: deliberately reproduce three distinct `OutOfMemoryError` variants on the same conceptual "growing service" theme, to make the diagnostic distinction concrete — starting with basic heap exhaustion, then the GC-overhead-limit variant specifically, then the very different native-thread-exhaustion variant, confirming each needs its own independent fix.

### Level 1 — Basic

```java
import java.util.*;

public class HeapSpaceExhaustion {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        try {
            for (int i = 0; i < 1_000_000; i++) {
                retained.add(new byte[100_000]); // ~100GB if it all succeeded -- will fail well before that
            }
        } catch (OutOfMemoryError e) {
            System.out.println("caught: " + e.getMessage());
            System.out.println("retained before failure: " + retained.size());
        }
    }
}
```

**How to run:** `java -Xmx128m HeapSpaceExhaustion.java` (JDK 17+).

Expected output:
```
caught: Java heap space
retained before failure: 1273
```

The message is exactly `Java heap space` — the plainest, most common variant: the heap genuinely cannot hold this much simultaneously-live data, and the direct fix (if this retention pattern is intentional and correct) is simply raising `-Xmx`, or (if it isn't) fixing whatever is retaining more than intended, exactly as with a [memory leak](0938-memory-leaks-in-managed-memory.md).

### Level 2 — Intermediate

```java
import java.util.*;

public class GcOverheadLimitExceeded {
    public static void main(String[] args) {
        List<Object> retained = new ArrayList<>();
        try {
            long i = 0;
            while (true) {
                // Deliberately retain almost everything while allocating a LOT --
                // this pattern makes each GC cycle reclaim only a tiny fraction,
                // triggering the "GC overhead limit exceeded" heuristic before
                // plain heap exhaustion would otherwise occur.
                retained.add(new int[]{(int) i});
                if (i % 7 == 0 && retained.size() > 1000) {
                    retained.remove(0); // remove JUST enough to keep GC "working," reclaiming very little
                }
                i++;
            }
        } catch (OutOfMemoryError e) {
            System.out.println("caught: " + e.getMessage());
            System.out.println("retained size at failure: " + retained.size());
        }
    }
}
```

**How to run:** `java -Xmx64m GcOverheadLimitExceeded.java` (JDK 17+; the specific message that appears depends on collector behavior and can sometimes still show as `Java heap space` on some collectors — the underlying pattern of "very high GC-time ratio, very low reclaim rate" is what this example is built to trigger).

Expected output shape (illustrative — exact message can vary by JVM/collector version):
```
caught: GC overhead limit exceeded
retained size at failure: 8214
```

The real-world concern added: this is a distinct diagnosis from plain heap exhaustion — the JVM isn't just "full," it's spending almost all of its time in GC while reclaiming almost nothing each cycle, which is exactly the signal that simply raising `-Xmx` (without also investigating why so little gets reclaimed) would likely just delay an identical failure at a larger scale, rather than genuinely fix the underlying retention pattern.

### Level 3 — Advanced

```java
public class NativeThreadExhaustion {
    public static void main(String[] args) {
        int created = 0;
        try {
            for (int i = 0; i < 200_000; i++) {
                Thread t = new Thread(() -> {
                    try { Thread.sleep(60_000); } catch (InterruptedException ignored) {}
                });
                t.start(); // each new platform thread reserves its own native stack -- see -Xss
                created++;
            }
        } catch (OutOfMemoryError e) {
            System.out.println("caught: " + e.getMessage());
            System.out.println("threads created before failure: " + created);
        }
    }
}
```

**How to run:** `java -Xss1m NativeThreadExhaustion.java` (JDK 17+; a larger `-Xss` per thread makes the OS/process thread-and-memory limit bind sooner, making the failure reproducible in a reasonable time — the exact count before failure varies significantly by OS and configured limits, e.g. `ulimit -u` on Linux).

Expected output shape (illustrative — exact count depends heavily on OS thread limits and available memory):
```
caught: unable to create new native thread
threads created before failure: 32741
```

The production-flavored hard case: raising `-Xmx` here would do absolutely nothing, since the heap was never the constrained resource — the failure is in OS-level thread creation, governed by the operating system's process thread limit and the memory reserved per thread's native stack (`-Xss`, plus other native, per-thread bookkeeping); the actual fixes are lowering the number of concurrently created platform threads (a bounded thread pool instead of one-thread-per-task), reducing `-Xss` if threads don't need a large stack, raising the OS-level thread/process limits if genuinely justified, or switching to virtual threads (which use dramatically less native resource per logical thread) for this kind of massively-concurrent workload.

## 6. Walkthrough

Tracing `GcOverheadLimitExceeded.main` end to end, since it's the least intuitive of the three:

1. The loop allocates a new small `int[]` array on almost every iteration, appending it to `retained` — but only very occasionally (`i % 7 == 0`, and only once `retained` already has over 1000 entries) does it remove a single element from the front, which is a deliberately tiny amount of reclamation relative to the allocation rate.
2. As `retained` grows, the young-generation collector runs repeatedly, but because the vast majority of what's in memory is genuinely still reachable via `retained`, each collection reclaims only a small fraction of the heap it examines — the ratio of "GC work done" to "memory actually freed" grows steadily worse over the run.
3. HotSpot has an internal heuristic, specifically checking for this pattern: if the JVM has spent an excessive proportion of recent total time in garbage collection (informally, something like 98%) while reclaiming only a very small fraction of the heap each time, it concludes the application is effectively in a death spiral — technically still running, but making negligible actual progress — and deliberately throws `OutOfMemoryError: GC overhead limit exceeded` rather than allowing the process to continue silently consuming CPU on GC while doing almost no useful application work.
4. This is a *deliberate, designed* fail-fast behavior, distinct from simply running out of heap space outright — the heap in this scenario might not even be completely full at the moment of failure; what triggers the error is the GC-time-to-reclaimed-memory ratio, not raw occupancy.
5. The caught `OutOfMemoryError`'s message is printed, along with `retained.size()` at the moment of failure — confirming the diagnosis requires recognizing that the *specific wording* of the exception (`GC overhead limit exceeded`, not `Java heap space`) is the clue pointing at a fundamentally different root cause: not "too little heap for legitimately needed live data," but "spending nearly all CPU time on GC that accomplishes almost nothing," which calls for investigating *why* reclamation is so ineffective (an aggressive retention pattern, exactly as constructed here) rather than simply enlarging the heap and hoping the same underlying inefficiency doesn't recur at a larger scale.

## 7. Gotchas & takeaways

> **Gotcha:** `-XX:-UseGCOverheadLimit` (disabling the heuristic entirely) is available but almost never the right fix — it doesn't solve the underlying inefficiency, it just removes the JVM's fail-fast safety net, letting the application continue silently burning nearly all its CPU on GC instead of failing loudly and immediately; treat the error as a genuine, actionable signal to investigate retention patterns, not an overly-aggressive check to disable.

- `OutOfMemoryError`'s message names the specific exhausted resource — `Java heap space`, `GC overhead limit exceeded`, `Metaspace`, `unable to create new native thread`, and `Direct buffer memory` are the common variants, each with a largely non-overlapping fix.
- `Java heap space` means the heap is genuinely full of live, reachable data — check for a [memory leak](0938-memory-leaks-in-managed-memory.md) first, then consider raising `-Xmx` if the retention is legitimate.
- `GC overhead limit exceeded` is a deliberate fail-fast heuristic: the JVM detected it was spending almost all its time on GC while reclaiming almost nothing — the fix is investigating *why* reclamation is so ineffective, not just enlarging the heap.
- `unable to create new native thread` is an OS-level, native-memory failure entirely unrelated to the heap — raising `-Xmx` does nothing; the fix involves the thread-creation pattern, `-Xss`, or OS-level thread limits.
- Always read the exact `OutOfMemoryError` message before choosing a fix — applying a heap-space fix to a native-thread or metaspace failure (or vice versa) wastes effort and leaves the real problem unaddressed.
- See [JVM flags (-Xms/-Xmx/-Xss)](0939-jvm-flags-xms-xmx-xss.md) for the sizing flags most directly relevant to several of these variants, and [heap dumps & analysis](0940-heap-dumps-analysis.md) for the tool used to investigate a genuine `Java heap space` failure's root cause in detail.
