---
card: java
gi: 768
slug: region-pinning-for-g1
title: Region pinning for G1
---

## 1. What it is

**Java 22** (JEP 423) adds **region pinning** to the G1 garbage collector, eliminating a long-standing restriction: previously, G1 had to **disable garbage collection entirely** for the whole heap while any thread was inside JNI critical code (a native method holding a direct pointer into Java heap memory via `GetPrimitiveArrayCritical` or similar). With region pinning, G1 can instead **pin** just the specific heap regions containing memory a JNI critical section is actively using, leaving every other region free to be collected normally — meaning a long-running JNI critical section no longer stalls garbage collection across the entire heap, only for the small set of regions it actually touches.

## 2. Why & when

JNI critical sections exist so native code can get a direct, unmanaged pointer into a Java array's memory — useful for performance-sensitive native interop, like calling into a native image-processing or numerics library on a Java array without copying data first. But garbage collection, including G1's mostly-concurrent collection, generally needs to be able to move objects around in memory (compaction), and a native pointer obtained via a JNI critical section would be invalidated if the collector moved the underlying memory out from under it. Before this JEP, G1's answer was blunt: block garbage collection for the *entire heap* for as long as *any* thread held a JNI critical section open, on the theory that pausing everything was simpler and safer than tracking which specific memory needed protecting. That blunt approach becomes a real throughput and latency problem exactly when it matters most: an application making frequent or long-running JNI critical calls (numeric libraries, hardware-accelerated codecs, certain database drivers) could stall G1's collection cycles heap-wide, working directly against G1's whole design goal of predictable, low pause times. Region pinning fixes this precisely: G1 now pins only the heap regions actually referenced by an active JNI critical section, letting collection proceed normally everywhere else — meaningful for any application combining G1 (the JDK's default collector) with JNI-critical-heavy native interop.

## 3. Core concept

```
# No application code change required — this is a G1 internal behavior improvement.
# Before Java 22: a JNI critical section anywhere stalls G1 collection heap-wide.
# Java 22+: G1 pins only the specific regions the critical section touches.

java -XX:+UseG1GC -Xlog:gc MyNativeInteropApp
```

The improvement is entirely inside G1's implementation — there's no new API, flag to enable it (it's on by default with G1 in Java 22+), or code change needed to benefit from it.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before region pinning, a JNI critical section anywhere blocks G1 collection across the whole heap; with region pinning, only the specific regions the critical section touches are pinned, leaving the rest of the heap collectible" >
  <rect x="20" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Before Java 22</text>
  <text x="160" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">entire heap blocked during JNI critical</text>
  <text x="160" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">section, regardless of which region it touches</text>

  <rect x="340" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 22+: region pinning</text>
  <text x="480" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only the specific region(s) touched</text>
  <text x="480" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">by the critical section are pinned</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The rest of the heap continues to be collected normally while a JNI critical section is active</text>
</svg>

*A narrow pin replaces a heap-wide freeze — collection keeps working everywhere else.*

## 5. Runnable example

Scenario: a native array-processing workload combined with ongoing background allocation, growing from a simple JNI critical call into a workload that demonstrates collection continuing to make progress elsewhere on the heap.

### Level 1 — Basic

```java
public class JniCriticalBasic {
    public static void main(String[] args) {
        int[] data = new int[1_000_000];
        for (int i = 0; i < data.length; i++) data[i] = i;

        long sum = sumArray(data);
        System.out.println("sum: " + sum);
    }

    // A plain Java sum — stands in for what a JNI critical section would do
    // natively (this entry focuses on the GC behavior, not on writing actual
    // native/JNI glue code, which is a separate, more involved setup).
    static long sumArray(int[] data) {
        long total = 0;
        for (int value : data) total += value;
        return total;
    }
}
```

**How to run:** `java -XX:+UseG1GC JniCriticalBasic.java` (JDK 22+).

This is a plain summation over a 1,000,000-element array, standing in conceptually for what a real JNI critical section would do with a directly-pinned pointer into the same array's memory — the point here is to establish the workload shape before reasoning about GC behavior around it.

### Level 2 — Intermediate

```java
import java.util.*;

public class JniCriticalWithAllocation {
    static volatile long sink; // prevent dead-code elimination of the background work

    public static void main(String[] args) throws InterruptedException {
        int[] data = new int[10_000_000];
        for (int i = 0; i < data.length; i++) data[i] = i;

        Thread backgroundAllocator = new Thread(() -> {
            List<byte[]> garbage = new ArrayList<>();
            for (int i = 0; i < 5000; i++) {
                garbage.add(new byte[10_000]); // steady stream of short-lived allocation
                if (garbage.size() > 100) garbage.remove(0);
                sink += garbage.size();
            }
        });
        backgroundAllocator.start();

        long sum = sumArray(data); // the long-running "critical section" equivalent
        backgroundAllocator.join();

        System.out.println("sum: " + sum);
    }

    static long sumArray(int[] data) {
        long total = 0;
        for (int value : data) total += value;
        return total;
    }
}
```

**How to run:** `java -XX:+UseG1GC -Xlog:gc JniCriticalWithAllocation.java`.

The real-world concern added: a **background thread continuously allocating and discarding memory** runs concurrently with the long array-processing operation — under pre-region-pinning G1 behavior, a genuinely long-held JNI critical section over `data` would have stalled collection of the background thread's garbage heap-wide; with region pinning, `-Xlog:gc` output would show collection cycles continuing to run and reclaim the background allocator's garbage in regions other than the one(s) holding `data`, even while a critical-section-equivalent operation is in progress.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class JniCriticalConcurrent {
    static long sumArray(int[] data) {
        long total = 0;
        for (int value : data) total += value;
        return total;
    }

    public static void main(String[] args) throws Exception {
        final int ARRAY_COUNT = 4;
        int[][] arrays = new int[ARRAY_COUNT][];
        for (int a = 0; a < ARRAY_COUNT; a++) {
            arrays[a] = new int[5_000_000];
            for (int i = 0; i < arrays[a].length; i++) arrays[a][i] = i + a;
        }

        try (var executor = Executors.newFixedThreadPool(ARRAY_COUNT)) {
            List<Future<Long>> sumFutures = new ArrayList<>();
            for (int[] array : arrays) {
                sumFutures.add(executor.submit(() -> sumArray(array)));
            }

            // Meanwhile, generate steady allocation pressure from the main thread
            List<byte[]> churn = new ArrayList<>();
            for (int i = 0; i < 20000; i++) {
                churn.add(new byte[5_000]);
                if (churn.size() > 200) churn.remove(0);
            }

            long total = 0;
            for (Future<Long> f : sumFutures) total += f.get();
            System.out.println("total: " + total + ", churn size: " + churn.size());
        }
    }
}
```

**How to run:** `java -XX:+UseG1GC -Xlog:gc:file=g1.log JniCriticalConcurrent.java`.

This adds the production-flavored hard case: **four concurrent long-running array operations** (standing in for four threads each holding their own JNI critical section over a different large array) running alongside continuous allocation churn on the main thread — the realistic shape of a service that both processes data via native interop and continues normal request-handling allocation at the same time, which is exactly the scenario region pinning is designed to keep responsive.

## 6. Walkthrough

Tracing the GC-relevant behavior of `JniCriticalConcurrent.main` (conceptually, since the "critical section" here is simulated with plain Java loops rather than actual native code):

1. `main` allocates four large `int[]` arrays (5,000,000 elements each) and submits one long-running "critical-section-equivalent" summation task per array to a fixed thread pool.
2. While those four tasks run (each looping over its own large array), the main thread simultaneously runs a churn loop, continuously allocating and discarding 5,000-byte buffers — generating a steady stream of short-lived garbage.
3. Under the pre-region-pinning G1 behavior, if the four summation tasks were genuine JNI critical sections, **any one of them being active would have blocked G1 collection across the entire heap** — meaning the main thread's churn garbage would pile up uncollected until every critical section finished, risking heap exhaustion or a very large deferred collection once they all released.
4. Under Java 22's region-pinning behavior, G1 instead pins only the heap regions containing each of the four large arrays actively being summed — every other region, including the ones holding the main thread's discarded churn buffers, remains fully collectible. `-Xlog:gc` output (written to `g1.log`) would show collection cycles running and reclaiming churn garbage throughout the run, not just in a burst after all four summations finish.
5. Once all four `Future<Long>` results are collected via `.get()`, `main` prints the combined total and the churn list's final size.

Expected output:
```
total: <some large sum>, churn size: 200
```

(The exact sum depends on the arrays' contents; the meaningful, observable difference from region pinning is in the accompanying `g1.log` GC cycle timing and frequency, not in this program's printed values — the printed output would be identical with or without region pinning, since it's a GC *efficiency* improvement, not a correctness-visible one.)

## 7. Gotchas & takeaways

> **Gotcha:** region pinning is a G1-internal improvement, not something application code interacts with directly — there's no new flag to pass or API to call. If you want to *observe* its effect, you need to compare GC log behavior (collection frequency and heap-wide pause characteristics) between workloads with and without long-held JNI critical sections, not look for any change in your own code's behavior or output.

- No application-visible API — this is purely a G1 collector internals improvement, enabled automatically with G1 in Java 22+.
- Fixes a long-standing throughput and latency risk: previously, any active JNI critical section blocked G1 collection across the *entire* heap, not just the memory it touched.
- Most relevant to applications combining G1 (the JDK's default collector) with JNI-critical-heavy native interop — numeric libraries, hardware-accelerated codecs, certain native database or hardware drivers.
- Use `-Xlog:gc` (or a dedicated log file) to observe collection cycle frequency directly if you suspect JNI-critical-related GC stalls in a workload predating this fix.
- Complements other G1 and [generational ZGC](0749-generational-zgc.md) throughput work as part of the JDK's ongoing effort to reduce GC-related stalls across a wide range of real workload shapes.
