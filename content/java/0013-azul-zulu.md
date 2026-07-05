---
card: java
gi: 13
slug: azul-zulu
title: Azul Zulu
---

## 1. What it is

**Azul Zulu** is a free, open-source, TCK-certified OpenJDK distribution published by Azul Systems. It covers a wider version matrix than most other free distributions — Azul publishes Zulu builds for Java 6, 7, 8, 11, 17, 21, and every non-LTS version in between — making it popular in environments that need old Java versions actively maintained.

Azul also offers **Zulu Prime** (formerly Zing), a commercially supported JVM with a C4 (Continuously Concurrent Compacting Collector) garbage collector that achieves sub-millisecond GC pauses at heap sizes up to terabytes.

Available at [azul.com/downloads](https://azul.com/downloads) and on Docker Hub as `azul/zulu-openjdk`.

## 2. Why & when

Use Azul Zulu when:
- You need free, maintained builds for **Java 6 or 7** (no other major vendor provides free current builds for these).
- You need builds for unusual platforms: Azul supports x64, ARM32, ARM64, and musl variants.
- You want a commercially backed vendor offering paid support without switching JDK vendors.
- You are evaluating **Zulu Prime** for low-latency applications (trading, gaming, telecom) where GC pauses are unacceptable.

For mainstream Java 17/21 on x64 Linux, Zulu is functionally identical to Temurin and Corretto.

## 3. Core concept

Azul Zulu Community (free) vs Azul Zulu Prime (paid):

| | Zulu Community | Zulu Prime |
|---|---|---|
| License | GPL-2.0 + CPE (free) | Commercial |
| GC | HotSpot (G1, ZGC, etc.) | Azul C4 (pauseless) |
| Max heap | Standard JVM limits | Multi-terabyte |
| JVM | OpenJDK HotSpot | Azul JVM (LLVM-based JIT) |
| Use case | Standard production | Ultra-low-latency systems |

The **C4 collector** uses a region-based compacting algorithm that runs concurrently — the application never stops to compact the heap. This is the "continuously concurrent" part. G1GC and ZGC have sub-millisecond pauses on modest heaps; C4 maintains those pauses even at 1 TB heap sizes, which is where it differentiates.

**Platform breadth** is Zulu's biggest differentiator in the free tier: Azul maintains Zulu builds for Java 6 through current across Linux glibc, Linux musl, macOS, Windows, ARM32, ARM64 — more combinations than any other vendor.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Azul Zulu: two tiers — community free builds and Prime paid pauseless GC">
  <defs>
    <marker id="azl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- OpenJDK source -->
  <rect x="20" y="85" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="101" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OpenJDK</text>
  <text x="80" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">upstream source</text>
  <line x1="140" y1="105" x2="178" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#azl)"/>

  <!-- Zulu Community -->
  <rect x="180" y="55" width="200" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="280" y="78" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Zulu Community</text>
  <text x="280" y="95" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">free · GPL-2.0 + CPE</text>
  <text x="280" y="109" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Java 6–25+ · widest platform</text>
  <text x="280" y="119" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">HotSpot JVM · G1/ZGC/SerialGC</text>

  <!-- Zulu Prime -->
  <rect x="400" y="55" width="260" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="530" y="78" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Zulu Prime (commercial)</text>
  <text x="530" y="95" fill="#f0883e" font-size="9"  text-anchor="middle" font-family="sans-serif">paid · commercial license</text>
  <text x="530" y="109" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Azul JVM · C4 GC (pauseless)</text>
  <text x="530" y="119" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">up to TB heaps · sub-ms pauses</text>

  <!-- use cases -->
  <text x="280" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Legacy Java 6/7 · multi-platform</text>
  <text x="530" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">HFT · gaming · telecom · analytics</text>
</svg>

Zulu Community = free broad-version OpenJDK. Zulu Prime = paid pauseless GC for extreme latency requirements.

## 5. Runnable example

Scenario: detect Zulu, identify which GC is running, and benchmark GC pauses — relevant when evaluating Zulu Community vs Zulu Prime.

### Level 1 — Basic

```java
// ZuluCheck.java
public class ZuluCheck {
    public static void main(String[] args) {
        String vendor  = System.getProperty("java.vendor", "");
        String vendorV = System.getProperty("java.vendor.version", "<n/a>");
        String vmName  = System.getProperty("java.vm.name", "");
        boolean isZulu = vendor.toLowerCase().contains("azul");

        System.out.println("Vendor         : " + vendor);
        System.out.println("Vendor version : " + vendorV);
        System.out.println("VM name        : " + vmName);
        System.out.println("Azul Zulu?     : " + isZulu);

        if (isZulu && vmName.contains("Zing")) {
            System.out.println("JVM type : Zulu Prime (Azul JVM with C4 GC)");
        } else if (isZulu) {
            System.out.println("JVM type : Zulu Community (HotSpot + standard GCs)");
        }
    }
}
```

**How to run:** `java ZuluCheck.java`

On Zulu Community, `java.vendor` is `"Azul Systems, Inc."` and `java.vm.name` is `"OpenJDK 64-Bit Server VM"`. On Zulu Prime, the VM name contains `"Zing"`.

### Level 2 — Intermediate

Same check extended to measure GC pause times — comparing the active GC's collection times and informing whether Zulu Prime's C4 GC would provide benefit.

```java
// GcPauseCheck.java
import java.lang.management.*;
import java.util.*;

public class GcPauseCheck {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== GC Pause Analysis ===");
        System.out.println("JVM  : " + System.getProperty("java.vm.name"));
        System.out.println("Java : " + Runtime.version());
        System.out.println();

        // Allocate to force some GC activity
        List<byte[]> sink = new ArrayList<>();
        long allocStart = System.nanoTime();
        for (int i = 0; i < 5000; i++) {
            sink.add(new byte[10 * 1024]);   // 10 KB per allocation = 50 MB total
            if (i % 500 == 0) sink.clear();  // allow GC to collect periodically
        }
        long allocMs = (System.nanoTime() - allocStart) / 1_000_000;

        System.out.println("Allocated and freed ~50 MB in " + allocMs + " ms");
        System.out.println();

        // Report GC beans
        System.out.printf("%-35s  %8s  %10s%n", "GC name", "Count", "Total time");
        System.out.println("-".repeat(60));
        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.printf("%-35s  %8d  %8d ms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime());
        }

        String vmName = System.getProperty("java.vm.name", "");
        System.out.println();
        if (vmName.contains("Zing")) {
            System.out.println("C4 GC (Zulu Prime): pauses should be <1 ms even under pressure.");
        } else {
            long totalGcMs = ManagementFactory.getGarbageCollectorMXBeans()
                .stream().mapToLong(GarbageCollectorMXBean::getCollectionTime).sum();
            if (totalGcMs > 100) {
                System.out.println("GC time >100 ms — consider ZGC (-XX:+UseZGC) or Zulu Prime for lower latency.");
            } else {
                System.out.println("GC pauses acceptable. Zulu Prime would only help at much larger heap sizes.");
            }
        }
    }
}
```

**How to run:** `java GcPauseCheck.java`

The allocation/free loop is designed to trigger minor GC cycles. `getCollectionTime()` accumulates wall-clock pause milliseconds. On G1GC with a 50 MB workload this is typically 5–50 ms. C4 would show near-zero.

### Level 3 — Advanced

Same GC analysis grown to a latency histogram — showing the distribution of allocation pause impacts, the key metric for deciding whether Zulu Prime is worth paying for.

```java
// LatencyHistogram.java
import java.lang.management.*;
import java.util.*;

public class LatencyHistogram {

    static final int SAMPLES = 2000;
    static final int BUCKET_COUNT = 10;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("╔═══════════════════════════════════════════╗");
        System.out.println("║      GC Latency Histogram (allocation)    ║");
        System.out.println("╚═══════════════════════════════════════════╝");
        System.out.println("JVM: " + System.getProperty("java.vm.name"));
        System.out.println();

        long[] latencies = new long[SAMPLES];
        List<byte[]> held = new ArrayList<>();

        // Warm up JIT first
        for (int w = 0; w < 200; w++) held.add(new byte[1024]);
        held.clear();

        // Measure allocation latency SAMPLES times
        for (int i = 0; i < SAMPLES; i++) {
            long t0 = System.nanoTime();
            held.add(new byte[32 * 1024]);   // 32 KB each = ~64 MB total
            latencies[i] = System.nanoTime() - t0;
            if (held.size() > 100) held.subList(0, 50).clear();  // free half periodically
        }
        held.clear();

        Arrays.sort(latencies);
        long p50 = latencies[SAMPLES * 50 / 100];
        long p95 = latencies[SAMPLES * 95 / 100];
        long p99 = latencies[SAMPLES * 99 / 100];
        long max = latencies[SAMPLES - 1];

        System.out.printf("Allocation latency over %d samples:%n", SAMPLES);
        System.out.printf("  p50 : %6d µs%n", p50 / 1000);
        System.out.printf("  p95 : %6d µs%n", p95 / 1000);
        System.out.printf("  p99 : %6d µs%n", p99 / 1000);
        System.out.printf("  max : %6d µs%n", max / 1000);

        // ASCII histogram
        System.out.println("\nHistogram (µs):");
        long bucketSize = Math.max(1, (max / 1000) / BUCKET_COUNT);
        int[] buckets = new int[BUCKET_COUNT + 1];
        for (long l : latencies) {
            int b = (int) Math.min(BUCKET_COUNT, (l / 1000) / bucketSize);
            buckets[b]++;
        }
        int maxCount = Arrays.stream(buckets).max().getAsInt();
        for (int b = 0; b <= BUCKET_COUNT; b++) {
            int barLen = buckets[b] * 40 / maxCount;
            System.out.printf("  %4d-%-4d µs |%-40s| %d%n",
                b * bucketSize, (b+1) * bucketSize,
                "█".repeat(barLen), buckets[b]);
        }

        System.out.println("\nConclusion:");
        if (max / 1000 > 10_000) {
            System.out.println("  High max pause (>" + max/1_000_000 + "ms). Zulu Prime C4 eliminates these outliers.");
        } else {
            System.out.println("  Pauses within " + max/1000 + " µs. Standard GCs acceptable for most workloads.");
        }

        // GC stats
        System.out.println("\nGC summary:");
        ManagementFactory.getGarbageCollectorMXBeans()
            .forEach(gc -> System.out.printf("  %-35s  count=%d  time=%dms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime()));
    }
}
```

**How to run:** `java LatencyHistogram.java`

The histogram reveals the long-tail latency distribution that average metrics hide. If `max` exceeds 10 ms and you're building a low-latency system, Zulu Prime's C4 GC (or ZGC in standard OpenJDK) is worth evaluating.

## 6. Walkthrough

Execution in `LatencyHistogram.main`:

1. **JIT warm-up** — 200 allocations before measuring prime the JIT compiler for the measurement loop. Without warm-up, the first few samples would be inflated by interpreter overhead, not GC.

2. **Measurement loop** — each iteration records the nanosecond time before and after a 32 KB allocation. `held.add(...)` keeps the allocation reachable (preventing immediate GC collection). Every 100 allocations, 50 are released to force GC. `System.nanoTime()` resolution is typically 100–1000 ns, so sub-microsecond pauses show as 0.

3. **Percentile calculation** — `Arrays.sort(latencies)` enables index-based percentile extraction: `p99 = latencies[SAMPLES * 99 / 100]`. p50 (median) represents "normal" performance; p99 is what 1% of requests experience; max is the worst observed — the tail that breaks SLAs.

4. **ASCII histogram** — `bucketSize = max / BUCKET_COUNT` divides the latency range into equal buckets. Each sample is assigned to `bucket = latency_µs / bucketSize`. Bar length is proportional to count, scaled to 40 chars.

5. **GC beans** — after measurement, `GarbageCollectorMXBeans` reports total GC time. If this is large relative to total elapsed time, GC is a significant overhead.

On G1GC with a modest heap, typical output:
```
p50 :      2 µs   ← most allocations are instant (nursery fast-path)
p95 :     15 µs
p99 :   4200 µs   ← occasional minor GC pauses appear here
max :  18000 µs   ← a major GC cycle (18 ms)
```

Zulu Prime C4 would compress p99 and max to <1 ms even at 10× the heap size.

## 7. Gotchas & takeaways

> **Zulu Community and Temurin are functionally equivalent for Java 17/21.** The only practical reason to choose Zulu Community over Temurin for modern Java is platform breadth (ARM32, legacy Java 6/7). Both pass the TCK and both are free.

> **Zulu Prime's C4 GC is a different JVM, not just a different GC.** You cannot switch `-XX:+UseC4` on a standard HotSpot JVM; you must install Zulu Prime's Azul JVM binary.

- Zulu Community: free, GPL-2.0 + CPE, broadest version matrix (Java 6–current), widest platform support.
- Zulu Prime: paid, C4 GC, pauseless at any heap size — for HFT, gaming, telecom, analytics.
- `java.vendor` = `"Azul Systems, Inc."` on both Zulu Community and Zulu Prime.
- `java.vm.name` contains `"Zing"` on Zulu Prime; `"OpenJDK"` on Zulu Community.
- For legacy Java 6/7 with free security patches, Zulu is the only major vendor providing them.
- GC pause evaluation: use `GarbageCollectorMXBean.getCollectionTime()` and a latency histogram to quantify whether Zulu Prime's C4 is needed.
