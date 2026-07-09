---
card: java
gi: 673
slug: zgc-on-macos-windows
title: ZGC on macOS & Windows
---

## 1. What it is

**Java 14** brought the **Z Garbage Collector (ZGC)** — previously available only on Linux since its experimental debut in Java 11 — to **macOS** (JEP 364) and **Windows** (JEP 365), both shipped as **experimental** ports. ZGC's core design (region-based, mostly-concurrent, colored-pointer technique for tracking object state without stop-the-world barriers) didn't change; what changed is that the platform-specific low-level memory-management primitives ZGC relies on (multi-mapping the same physical memory to several virtual addresses, used for its colored-pointer scheme) were implemented against macOS's and Windows' respective virtual memory APIs, which differ substantially from Linux's. Before this, choosing ZGC meant being locked into Linux deployment; from Java 14 onward, the same `-XX:+UseZGC` flag works — still experimentally — on all three major desktop/server operating systems.

## 2. Why & when

ZGC's low-pause-time, large-heap-friendly design is valuable well beyond Linux-only server deployments — development workstations (frequently macOS or Windows), CI environments, and desktop-adjacent Java applications all benefit from being able to test and tune against the same collector that might run in a Linux production environment, without needing a Linux VM or container just to experiment with ZGC's behavior. Cross-platform parity also matters for library and framework authors who need to verify their code behaves correctly under different collectors across the operating systems their users actually develop on. Reach for `-XX:+UseZGC` on macOS or Windows (with `-XX:+UnlockExperimentalVMOptions` still required in Java 14, since the port was released as experimental on both new platforms just as it was on Linux) when you want to develop, test, or benchmark against ZGC locally without needing a separate Linux environment, or when you're deploying a latency-sensitive Java application directly on Windows or macOS Server hardware.

## 3. Core concept

```bash
# Linux — ZGC available since Java 11 (experimental)
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx4g MyApp

# macOS — ZGC available since Java 14 (experimental, JEP 364)
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx4g MyApp

# Windows — ZGC available since Java 14 (experimental, JEP 365)
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx4g MyApp
```

The command line is identical across all three platforms — the JEPs delivered platform *parity*, not a different API or flag surface; the difference is entirely in the JVM's internal, OS-specific virtual-memory implementation underneath.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZGC available on Linux since Java 11; Java 14 adds macOS and Windows support with the same flags and behavior">
  <rect x="10" y="15" width="180" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Linux</text>
  <text x="100" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ZGC since Java 11</text>
  <text x="100" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">-XX:+UseZGC</text>

  <rect x="220" y="15" width="180" height="120" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">macOS</text>
  <text x="310" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ZGC since Java 14</text>
  <text x="310" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">-XX:+UseZGC</text>
  <text x="310" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(JEP 364)</text>

  <rect x="430" y="15" width="180" height="120" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Windows</text>
  <text x="520" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ZGC since Java 14</text>
  <text x="520" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">-XX:+UseZGC</text>
  <text x="520" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(JEP 365)</text>
</svg>

Java 14 closes the platform gap: the same experimental collector, the same flags, now available everywhere developers actually run the JDK.

## 5. Runnable example

Scenario: verifying ZGC is actually active and observing its behavior on whichever platform you're on — first confirming the collector selection via a diagnostic flag, then running an allocation-heavy workload under ZGC to observe its low-pause-time behavior via GC logging, then a version that fails gracefully with a clear message if run against a JDK build lacking ZGC support, illustrating why cross-platform availability specifically mattered.

### Level 1 — Basic

```java
// File: GcCheck.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.List;

public class GcCheck {
    public static void main(String[] args) {
        List<GarbageCollectorMXBean> beans = ManagementFactory.getGarbageCollectorMXBeans();
        System.out.println("Active garbage collectors:");
        for (GarbageCollectorMXBean bean : beans) {
            System.out.println("  " + bean.getName());
        }
    }
}
```

**How to run (works identically on Linux, macOS, or Windows from Java 14 onward):**
```
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC GcCheck.java
```

Expected output:
```
Active garbage collectors:
  ZGC
```

(If ZGC isn't actually active — e.g. the flag was rejected or a different collector took over — this list would show a different name like `G1 Young Generation`, making this a reliable, code-level way to confirm which collector is really running.)

### Level 2 — Intermediate

```java
// File: ZgcWorkload.java
import java.util.ArrayList;
import java.util.List;

public class ZgcWorkload {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> churn = new ArrayList<>();
        long start = System.currentTimeMillis();
        for (int round = 0; round < 20; round++) {
            for (int i = 0; i < 50_000; i++) {
                churn.add(new byte[512]);
                if (churn.size() > 20_000) churn.remove(0);
            }
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Workload completed in " + elapsed + " ms, final retained: " + churn.size());
    }
}
```

**How to run with GC logging enabled:**
```
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xlog:gc -Xmx1g ZgcWorkload.java
```

Expected output includes interleaved application and GC log lines, with ZGC pause durations typically staying under a millisecond regardless of platform:
```
[0.045s][info][gc] GC(0) Garbage Collection (Warmup) 128M(12%)->42M(4%)
[0.089s][info][gc] GC(1) Garbage Collection (Allocation Rate) 256M(25%)->51M(5%)
...
Workload completed in 187 ms, final retained: 20000
```

The program's output is unaffected by platform — the same code, the same flags, and comparably low pause behavior are expected whether this runs on Linux, macOS, or Windows, which is the entire point of the platform parity delivered in Java 14.

### Level 3 — Advanced

```java
// File: ZgcGracefulCheck.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.List;

public class ZgcGracefulCheck {
    static boolean isZgcActive() {
        List<GarbageCollectorMXBean> beans = ManagementFactory.getGarbageCollectorMXBeans();
        return beans.stream().anyMatch(b -> b.getName().equals("ZGC"));
    }

    public static void main(String[] args) {
        String os = System.getProperty("os.name");
        String javaVersion = System.getProperty("java.version");

        System.out.println("Running on: " + os + ", Java " + javaVersion);

        if (isZgcActive()) {
            System.out.println("ZGC is active — proceeding with low-pause-sensitive workload.");
            runLowPauseWorkload();
        } else {
            System.out.println("ZGC is NOT active on this JVM invocation.");
            System.out.println("Hint: pass -XX:+UnlockExperimentalVMOptions -XX:+UseZGC");
            System.out.println("(Requires Java 11+ on Linux, or Java 14+ on macOS/Windows.)");
        }
    }

    static void runLowPauseWorkload() {
        long start = System.nanoTime();
        java.util.List<byte[]> data = new java.util.ArrayList<>();
        for (int i = 0; i < 100_000; i++) {
            data.add(new byte[256]);
            if (data.size() > 10_000) data.remove(0);
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Workload finished in " + elapsedMs + " ms with " + data.size() + " retained objects.");
    }
}
```

**How to run:** `java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC ZgcGracefulCheck.java` (or without the ZGC flags, to see the fallback path).

Expected output with ZGC active:
```
Running on: Mac OS X, Java 14
ZGC is active — proceeding with low-pause-sensitive workload.
Workload finished in 34 ms with 10000 retained objects.
```

Expected output without the ZGC flags (default collector active instead):
```
Running on: Mac OS X, Java 14
ZGC is NOT active on this JVM invocation.
Hint: pass -XX:+UnlockExperimentalVMOptions -XX:+UseZGC
(Requires Java 11+ on Linux, or Java 14+ on macOS/Windows.)
```

Level 3 writes defensive, platform-agnostic code that checks at runtime whether ZGC is actually active (via `GarbageCollectorMXBean`, not just assuming the flags worked) before proceeding — useful for applications that want to adapt behavior or emit clear diagnostics depending on which collector ended up running, especially relevant when the same deployment scripts might target Linux, macOS, or Windows hosts interchangeably.

## 6. Walkthrough

1. `main` reads `os.name` and `java.version` system properties first, purely for diagnostic output — these work identically regardless of collector or platform.
2. `isZgcActive()` is called, which calls `ManagementFactory.getGarbageCollectorMXBeans()` — this returns a list of `GarbageCollectorMXBean` instances, one per garbage collector algorithm actually active in the running JVM (a collector can have multiple beans, e.g. one for young-generation and one for old-generation collection, but ZGC — being a single unified collector — exposes exactly one bean named `"ZGC"`).
3. `.stream().anyMatch(b -> b.getName().equals("ZGC"))` checks whether any of those beans is named exactly `"ZGC"` — if the JVM was started with `-XX:+UseZGC` and that flag was successfully honored (both the flag was recognized by this JDK build *and* the target platform actually supports ZGC), this bean will exist.
4. Assuming ZGC is active, `main` prints the confirmation and calls `runLowPauseWorkload()`. Inside, `System.nanoTime()` records a start time, then a loop performs 100,000 allocations of small `byte[]` arrays into a bounded-size `List`, forcing continuous garbage generation as old entries are evicted via `data.remove(0)` once the list exceeds 10,000 elements — this is deliberately allocation-heavy to exercise the collector.
5. ZGC's concurrent, region-based collection runs in the background throughout this loop, reclaiming the growing amount of garbage produced by evicted `byte[]` arrays without introducing any application-visible stop-the-world pause beyond its characteristic sub-millisecond synchronization points — the exact same mechanism regardless of whether this JVM process is running on Linux, macOS, or Windows, since JEP 364/365 specifically targeted making ZGC's *behavior*, not just its flag acceptance, consistent across platforms.
6. After the loop completes, `elapsedMs` is computed and printed alongside the final retained count, giving a simple, platform-independent measurement of how long the allocation-heavy workload took under whichever collector actually ran.
7. If `isZgcActive()` had instead returned `false` (for instance, if `-XX:+UseZGC` were omitted, or run on a JDK build where ZGC isn't available for that platform), `main` takes the `else` branch, printing an explanatory hint rather than silently running the workload under a potentially different collector and producing misleading pause-time expectations — an example of defensively verifying JVM configuration at runtime rather than assuming command-line flags always take effect as intended.

```
main ──► isZgcActive()? ──► query GarbageCollectorMXBeans ──► name == "ZGC"?
              │yes                                              │no
              ▼                                                 ▼
     runLowPauseWorkload()                          print hint, do not run workload
     (same behavior, any of Linux/macOS/Windows from Java 14+)
```

## 7. Gotchas & takeaways

> Both the macOS and Windows ZGC ports shipped as **experimental** in Java 14 — meaning `-XX:+UnlockExperimentalVMOptions` was still required alongside `-XX:+UseZGC`, matching the same experimental status ZGC had carried on Linux since Java 11. Don't assume "available on more platforms" also meant "production-ready" at this point — experimental status persisted uniformly across all three platforms until ZGC was later marked production-ready.

- The command-line flags (`-XX:+UnlockExperimentalVMOptions -XX:+UseZGC`) are identical across Linux, macOS, and Windows from Java 14 onward — no platform-specific syntax to remember.
- Always verify a collector actually took effect via `GarbageCollectorMXBean` (as shown in Level 3) rather than trusting that a flag was silently accepted — misspelled or unsupported flags can sometimes be ignored rather than causing a hard startup failure, depending on JVM version and flag type.
- This platform expansion specifically enabled local development-machine testing of ZGC behavior (many developers use macOS or Windows workstations) without needing a separate Linux environment just to experiment.
- The underlying implementation differences (how each OS's virtual memory APIs support ZGC's multi-mapping technique) are invisible to application code — you interact with ZGC identically regardless of platform.
- If you're choosing a JDK distribution or vendor build, confirm it actually includes ZGC for your target platform — not every third-party OpenJDK build includes every experimental collector by default, similar to the caveat noted for Shenandoah in [Shenandoah GC (experimental)](0653-shenandoah-gc-experimental.md).
