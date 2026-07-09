---
card: java
gi: 639
slug: epsilon-gc-no-op
title: Epsilon GC (no-op)
---

## 1. What it is

**Epsilon GC** is a **no-op garbage collector** introduced experimentally in Java 11. Unlike all other GCs, Epsilon **never reclaims memory** — it allocates objects until the heap is exhausted, at which point the JVM terminates with an `OutOfMemoryError`. This seemingly useless behaviour has specific, valuable use cases: performance testing (measuring the true cost of GC by eliminating it), short-lived jobs (where the JVM exits before collection is needed), and latency-critical applications where GC pauses are unacceptable and memory is known to be sufficient. Epsilon is enabled with `-XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC`.

## 2. Why & when

GC tuning is hard, and measuring its impact is harder. By providing a zero-GC baseline, Epsilon lets you answer: "How much throughput does GC cost me?" or "How bad would latency be without GC pauses?" Beyond benchmarking, Epsilon is perfect for jobs that allocate a bounded amount of memory and then exit — no time wasted on collection. Use it for: performance experiments, unit-testing GC-sensitive code, short-lived batch jobs, and serverless functions where the JVM lives only milliseconds.

## 3. Core concept

```bash
# Run a program with Epsilon GC (no garbage collection)
java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx256m MyApp.java

# The program will allocate until heap is full, then crash with OutOfMemoryError
# No GC pauses, no memory reclaimed — pure allocation speed
```

Epsilon implements the GC interface but does nothing: allocation bumps a pointer, and when the heap is full, the JVM exits. This is intentionally simple — the point is what it *doesn't* do.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Epsilon GC allocates but never reclaims — heap fills and JVM exits">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="150" height="45" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="95" y="38" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">Allocation</text>
  <text x="95" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">pointer bump — no GC</text>

  <text x="185" y="45" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="200" y="18" width="160" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="280" y="36" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Heap fills linearly</text>
  <text x="280" y="50" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">no collections, no pauses</text>
  <text x="280" y="62" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">fastest possible allocation</text>

  <text x="375" y="45" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="395" y="20" width="145" height="45" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="467" y="38" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Heap exhausted</text>
  <text x="467" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">OutOfMemoryError</text>

  <text x="20" y="95" fill="#8b949e" font-size="9" font-family="sans-serif">Use cases: performance baseline, short-lived jobs, latency-sensitive apps with bounded memory</text>
  <text x="20" y="113" fill="#f85149" font-size="9" font-family="sans-serif">Enable: -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx N (set heap limit)</text>
</svg>

Epsilon GC is the simplest possible memory manager: allocate until you can't, then stop. It's a diagnostic and performance-baseline tool, not a production GC.

## 5. Runnable example

Scenario: measuring allocation throughput and demonstrating Epsilon's behaviour — starting with basic observation, extending to throughput comparison, and finally demonstrating the OOM boundary.

### Level 1 — Basic

```java
// File: EpsilonDemo.java
public class EpsilonDemo {
    public static void main(String[] args) {
        System.out.println("Running with: " +
            System.getProperty("java.vm.name") + " " +
            System.getProperty("java.version"));

        // Allocate until we run out of memory
        int count = 0;
        try {
            while (true) {
                byte[] chunk = new byte[1024 * 1024]; // 1 MB
                count++;
                if (count % 100 == 0) {
                    System.out.println("Allocated: " + count + " MB");
                }
            }
        } catch (OutOfMemoryError e) {
            System.out.println("OutOfMemoryError after " + count + " MB allocated");
            System.out.println("(Epsilon GC never reclaimed — heap filled completely)");
        }
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx256m EpsilonDemo.java`

Expected output:
```
Running with: OpenJDK 64-Bit Server VM 17.0...
Allocated: 100 MB
Allocated: 200 MB
OutOfMemoryError after ~240 MB allocated
(Epsilon GC never reclaimed — heap filled completely)
```

Without Epsilon, a normal GC would have collected the unreachable `chunk` arrays long before OOM. With Epsilon, no collection occurs — memory fills linearly until exhaustion.

### Level 2 — Intermediate

```java
// File: EpsilonThroughput.java
import java.util.*;

public class EpsilonThroughput {
    public static void main(String[] args) {
        System.out.println("=== Allocation throughput test ===\n");
        System.out.println("Allocating 10M integers per iteration...\n");

        // This test measures raw allocation speed
        // Run with Epsilon to eliminate GC overhead from measurement
        int iterations = 5;
        long totalNs = 0;

        for (int iter = 0; iter < iterations; iter++) {
            long start = System.nanoTime();

            // Allocate objects that become garbage immediately
            for (int i = 0; i < 10_000_000; i++) {
                Object obj = new Object();
                // obj becomes unreachable immediately (no GC to collect it with Epsilon)
            }

            long time = System.nanoTime() - start;
            totalNs += time;
            System.out.printf("  Iteration %d: %,d ns%n", iter + 1, time);
        }

        long avg = totalNs / iterations;
        System.out.printf("\nAverage allocation time: %,d ns per 10M objects%n", avg);
        System.out.println("\nRun this with different GCs to compare allocation overhead:");
        System.out.println("  -XX:+UseEpsilonGC   (no GC — baseline)");
        System.out.println("  -XX:+UseG1GC        (default — compare)");
        System.out.println("  -XX:+UseSerialGC    (single-threaded — compare)");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx512m EpsilonThroughput.java`

Expected output:
```
=== Allocation throughput test ===

Allocating 10M integers per iteration...

  Iteration 1: ... ns
  Iteration 2: ... ns
  ...

Average allocation time: ... ns per 10M objects

Run this with different GCs to compare allocation overhead:
  -XX:+UseEpsilonGC   (no GC — baseline)
  -XX:+UseG1GC        (default — compare)
  -XX:+UseSerialGC    (single-threaded — compare)
```

The real-world concern: benchmarking. Epsilon provides the "zero-GC" baseline — how fast is allocation without any collection overhead? Compare with other GCs to measure their impact on throughput-latency trade-offs.

### Level 3 — Advanced

```java
// File: EpsilonAdvanced.java
public class EpsilonAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Epsilon GC — Use Cases and Limitations ===\n");

        printSection("1. Performance baseline",
            "Run the same workload with Epsilon vs G1/ZGC/Shenandoah.",
            "The difference in throughput = GC overhead.",
            "The difference in latency = GC pause impact.");

        printSection("2. Short-lived jobs",
            "Jobs that allocate a known, bounded amount of memory and exit.",
            "Example: a CLI tool that processes one file and exits.",
            "GC is wasted work — the memory is freed when the JVM exits anyway.");

        printSection("3. Latency-critical apps (with bounded memory)",
            "If you KNOW your app fits in Xmx without GC,",
            "Epsilon eliminates the last source of unpredictable pauses.",
            "But: you MUST guarantee no OOM — one bad input and the JVM dies.");

        printSection("4. Testing & debugging",
            "Unit tests that verify memory behaviour.",
            "Stress tests: does your app handle OOM gracefully?",
            "Reproduce memory leaks: with Epsilon, leaks crash immediately.");

        printSection("Key facts",
            "Flag: -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC",
            "Epsilon allocates: yes (fast — pointer bump in TLAB)",
            "Epsilon collects: never",
            "Epsilon compacts: never",
            "Epsilon pauses: none (0 ms) — because it does nothing",
            "Epsilon is EXPERIMENTAL in Java 11, production-ready in later versions");

        // Demonstrate a practical use: measuring object allocation rate
        System.out.println("\n=== Object allocation rate measurement ===\n");

        long start = System.nanoTime();
        int count = 0;
        try {
            // Allocate small objects as fast as possible
            while (true) {
                Object o = new Object();
                count++;
                if (count % 10_000_000 == 0) {
                    long elapsed = System.nanoTime() - start;
                    double rate = count / (elapsed / 1_000_000_000.0);
                    System.out.printf("  %,d objects allocated (rate: %,.0f obj/s)%n",
                        count, rate);
                    if (count >= 50_000_000) break;  // stop before OOM
                }
            }
        } catch (OutOfMemoryError e) {
            System.out.println("  OOM after " + count + " objects");
        }
    }

    static void printSection(String title, String... lines) {
        System.out.println(title);
        for (String line : lines) {
            System.out.println("  " + line);
        }
        System.out.println();
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx512m EpsilonAdvanced.java`

Expected output:
```
=== Epsilon GC — Use Cases and Limitations ===

1. Performance baseline
  Run the same workload with Epsilon vs G1/ZGC/Shenandoah.
  The difference in throughput = GC overhead.
  The difference in latency = GC pause impact.

2. Short-lived jobs
  Jobs that allocate a known, bounded amount of memory and exit.
  ...

=== Object allocation rate measurement ===

  10,000,000 objects allocated (rate: ... obj/s)
  20,000,000 objects allocated (rate: ... obj/s)
  ...
```

The production-flavoured hard cases: (1) Epsilon is a **diagnostic tool**, not a production GC for general workloads — only use it when you explicitly want "no GC" behaviour. (2) Epsilon works best with `-Xmx` set appropriately — too low and you OOM immediately; too high and you waste memory (since nothing is ever reclaimed). (3) In later JDK versions (15+), Epsilon is no longer experimental — the `-XX:+UnlockExperimentalVMOptions` flag is not needed.

## 6. Walkthrough

Tracing Epsilon GC's behaviour during `new byte[1024 * 1024]` in a loop:

1. JVM starts with `-XX:+UseEpsilonGC -Xmx256m`. Epsilon initialises the heap as one contiguous space of 256 MB.

2. First allocation: `new byte[1048576]` (1 MB). Epsilon's TLAB (Thread-Local Allocation Buffer) has space — it bumps the pointer by 1 MB and returns the memory. No GC activity. Heap used: 1 MB.

3. Loop repeats. At 100 MB: still bumping the pointer, no GC. At 200 MB: same. The allocation rate is at theoretical maximum — there's zero GC overhead.

4. At approximately 240 MB: the TLAB is exhausted, and the heap has no free space. Epsilon does NOT trigger a collection (it never does). The allocation fails.

5. The JVM throws `OutOfMemoryError: Java heap space`. The error propagates up to the `catch` block or kills the thread/process if uncaught.

6. The JVM shuts down. All memory is released to the OS.

Key insight: Epsilon's "collection" algorithm is literally `return;` — an empty method. The allocation path is as fast as theoretically possible in a managed runtime.

## 7. Gotchas & takeaways

> Epsilon GC is **not a substitute for proper memory management** in production. If you enable it on a long-running server, even a slow memory leak (a few KB/min) will eventually cause an OOM crash. It's a tool for specific scenarios, not a general-purpose GC.

- Epsilon is ideal for **benchmarking** your application's raw speed and for **short-lived containers** (serverless functions, batch jobs) where the JVM exits before GC is needed.
- Epsilon handles only Java heap memory — it does not manage native memory, metaspace, or direct buffers. Those are managed separately and can still cause OOM.
- Epsilon with `-Xmx` set to the machine's physical memory lets you measure the maximum heap your application actually needs. Run with Epsilon, observe where it OOMs — that's your working set size.
- Epsilon is not linked to any specific GC algorithm family — it's its own thing. Don't confuse it with ZGC or Shenandoah, which are low-pause collectors that DO reclaim memory.
- The flag was experimental in Java 11 (`-XX:+UnlockExperimentalVMOptions` required). From Java 15 onward, Epsilon is a standard feature and only needs `-XX:+UseEpsilonGC`.
