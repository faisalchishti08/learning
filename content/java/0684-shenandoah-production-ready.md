---
card: java
gi: 684
slug: shenandoah-production-ready
title: Shenandoah production-ready
---

## 1. What it is

**Java 15** also promoted **Shenandoah**, the low-pause-time garbage collector originally contributed by Red Hat, from **experimental** to **production-ready** status (JEP 379) — the same release, and the same kind of milestone, as [ZGC's production-ready promotion](0683-zgc-production-ready.md). Shenandoah had been available since Java 12 as an experimental collector (see [Shenandoah GC (experimental)](0653-shenandoah-gc-experimental.md)). Like ZGC, its core algorithm — concurrent evacuation using brooks pointers/forwarding, aiming for pause times that don't scale with heap size — didn't change; what changed is that `-XX:+UseShenandoahGC` no longer needed `-XX:+UnlockExperimentalVMOptions` from Java 15 onward, on JDK builds that include it.

## 2. Why & when

Java 15 shipped two independently developed low-pause collectors — ZGC (Oracle-led) and Shenandoah (Red Hat-led) — both reaching production-ready maturity in the same release, giving Java users a genuine choice between two different concurrent-collection designs rather than a single default answer. Shenandoah's approach (using forwarding pointers embedded via brooks pointers, load barriers, and — this was distinct from ZGC in this era — able to run in heaps as small as those used by G1, not requiring the very large heaps ZGC's overhead profile was originally tuned for) made it a strong option for workloads that wanted low pause times without necessarily needing a massive heap. Reach for `-XX:+UseShenandoahGC` from Java 15 onward when your JDK distribution includes it (notably: not every vendor bundles Shenandoah — check with `java -XX:+PrintFlagsFinal -version | grep Shenandoah` or your vendor's documentation) and you want low, heap-size-independent pause times, especially on moderate-sized heaps where ZGC's design historically carried more relative overhead.

## 3. Core concept

```bash
# Java 12–14: Shenandoah required the experimental unlock flag
java -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -Xmx4g MyApp

# Java 15 onward: Shenandoah is production-ready, no unlock flag needed
java -XX:+UseShenandoahGC -Xmx4g MyApp
```

As with ZGC's promotion, the command line got simpler and the collector's status changed from "experimental, use with caution" to "fully supported," while the collector's underlying algorithm remained the same.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 15 delivers two independently production-ready low-pause collectors: ZGC and Shenandoah, side by side">
  <rect x="40" y="30" width="250" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="55" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">ZGC</text>
  <text x="165" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Oracle-led</text>
  <text x="165" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">experimental since Java 11</text>
  <text x="165" y="120" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">production-ready: Java 15</text>

  <rect x="350" y="30" width="250" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="475" y="55" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">Shenandoah</text>
  <text x="475" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Red Hat-led</text>
  <text x="475" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">experimental since Java 12</text>
  <text x="475" y="120" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">production-ready: Java 15</text>
</svg>

Two distinct low-pause collector implementations both graduated to production-ready status in the same JDK release.

## 5. Runnable example

Scenario: verifying Shenandoah is active, then running an allocation-heavy workload while watching pause behavior via GC logging, then building a defensive startup check that falls back to reporting the active collector by name — useful in environments where Shenandoah may or may not be bundled in the JDK.

### Level 1 — Basic

```java
// File: ShenandoahConfirm.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;

public class ShenandoahConfirm {
    public static void main(String[] args) {
        for (GarbageCollectorMXBean bean : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.println("Active collector: " + bean.getName());
        }
    }
}
```

**How to run (on a JDK build that bundles Shenandoah; Java 15+, no experimental unlock flag needed):**
```
java -XX:+UseShenandoahGC ShenandoahConfirm.java
```

Expected output (Java 15's original Shenandoah exposes one bean named `Shenandoah`; later JDKs split it into separate `Shenandoah Pauses` / `Shenandoah Cycles` beans — either way, the name(s) contain `"Shenandoah"`):
```
Active collector: Shenandoah Pauses
Active collector: Shenandoah Cycles
```

### Level 2 — Intermediate

```java
// File: ShenandoahWorkload.java
import java.util.ArrayList;
import java.util.List;

public class ShenandoahWorkload {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.currentTimeMillis();

        for (int round = 0; round < 30; round++) {
            for (int i = 0; i < 40_000; i++) {
                retained.add(new byte[1024]);
                if (retained.size() > 30_000) retained.remove(0);
            }
        }

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Workload finished in " + elapsed + " ms, retained: " + retained.size());
    }
}
```

**How to run with GC logging:**
```
java -XX:+UseShenandoahGC -Xlog:gc -Xmx512m ShenandoahWorkload.java
```

Expected output shape (Shenandoah's pauses are characteristically short and largely independent of heap size):
```
[0.041s][info][gc] Trigger: Free (12M) is below minimum threshold (25M)
[0.041s][info][gc] Pacer for Evacuation. Used CSet: 8192K, Free: 200704K, Non-Trigger: 100.00%
[0.058s][info][gc] Concurrent reset 17.234ms
[0.075s][info][gc] Pause Init Mark 0.412ms
...
Workload finished in 198 ms, retained: 30000
```

### Level 3 — Advanced

```java
// File: CollectorAwareStartup.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.List;

public class CollectorAwareStartup {
    public static void main(String[] args) {
        List<GarbageCollectorMXBean> beans = ManagementFactory.getGarbageCollectorMXBeans();
        String activeNames = beans.stream()
                .map(GarbageCollectorMXBean::getName)
                .reduce((a, b) -> a + ", " + b)
                .orElse("(none reported)");

        System.out.println("Active GC bean(s): " + activeNames);

        boolean lowPauseCollector = beans.stream()
                .anyMatch(b -> b.getName().contains("Shenandoah") || b.getName().contains("ZGC"));

        if (lowPauseCollector) {
            System.out.println("Low-pause collector detected — safe to enable latency-sensitive request handling.");
        } else {
            System.out.println("Standard throughput-oriented collector detected (e.g. G1) — "
                    + "consider -XX:+UseShenandoahGC or -XX:+UseZGC if this service is latency-sensitive.");
        }
    }
}
```

**How to run (try with different collector flags to see the branch change):**
```
java -XX:+UseShenandoahGC CollectorAwareStartup.java
java -XX:+UseG1GC CollectorAwareStartup.java
```

Expected output with Shenandoah (bean names vary by JDK version — Java 15 exposes one `Shenandoah` bean, later JDKs split it into `Shenandoah Pauses` / `Shenandoah Cycles`):
```
Active GC bean(s): Shenandoah Pauses, Shenandoah Cycles
Low-pause collector detected — safe to enable latency-sensitive request handling.
```

Expected output with G1 (the exact set of G1 beans reported has also varied slightly across JDK versions):
```
Active GC bean(s): G1 Young Generation, G1 Concurrent GC, G1 Old Generation
Standard throughput-oriented collector detected (e.g. G1) — consider -XX:+UseShenandoahGC or -XX:+UseZGC if this service is latency-sensitive.
```

Level 3 writes a small piece of **collector-aware startup logic** — checking which collector actually ended up active (not assuming the requested flag was honored) and branching application behavior accordingly, useful for services that want to log a warning, adjust internal timeout budgets, or simply record which GC strategy is in effect for later diagnostics.

## 6. Walkthrough

1. `main` retrieves the full list of `GarbageCollectorMXBean`s active in this JVM and joins their names into a single readable string via `.reduce((a, b) -> a + ", " + b)`, defaulting to `"(none reported)"` if the list were ever empty (which shouldn't happen in practice — every JVM has at least one collector active — but the `.orElse(...)` avoids relying on that assumption silently).
2. `beans.stream().anyMatch(b -> b.getName().contains("Shenandoah") || b.getName().contains("ZGC"))` checks whether *either* of the two low-pause collectors from Java 15's dual production-ready promotion is the one actually running, using `contains` rather than exact equality so it tolerates any bean-naming variations across JDK versions (mirroring the same defensive pattern used for [ZGC's own bean-name check](0683-zgc-production-ready.md)).
3. If a low-pause collector is detected, `main` prints a message suggesting the application can safely lean into latency-sensitive behavior — the semantic point being that code can make *runtime* decisions based on which collector actually ended up active, rather than assuming a fixed deployment configuration always holds.
4. If neither Shenandoah nor ZGC is active (for instance, if G1 — the default — is running because no low-pause flag was passed, or because this JDK build doesn't bundle either collector), the `else` branch prints a suggestion instead, without failing or crashing — a graceful degradation path appropriate for a startup diagnostic rather than a hard requirement.
5. Running the exact same program twice, once with `-XX:+UseShenandoahGC` and once with `-XX:+UseG1GC`, demonstrates both branches: the first run reports Shenandoah's bean(s) (named `Shenandoah` on Java 15, or split into `Shenandoah Pauses` / `Shenandoah Cycles` on later JDKs) and takes the low-pause branch; the second reports G1's generational beans and takes the throughput-oriented branch.
6. This pattern — detect, don't assume — is the practical lesson Java 15's simultaneous ZGC/Shenandoah promotion teaches operationally: with two production-ready low-pause options now available side by side with G1, application and platform code that cares about GC behavior should verify what's actually running rather than hard-coding assumptions based on deployment configuration alone.

```
main ──► list GarbageCollectorMXBeans
              │
   any bean name contains "Shenandoah" or "ZGC"?
        │yes                              │no
        ▼                                 ▼
  low-pause branch                 throughput-oriented branch
  (Shenandoah or ZGC active)       (e.g. G1 active)
```

## 7. Gotchas & takeaways

> Not every JDK distribution bundles Shenandoah — unlike ZGC, which Oracle's OpenJDK builds always include, Shenandoah's inclusion depends on the vendor (Red Hat's builds and several others include it; some minimal or Oracle-specific builds have historically excluded it). Passing `-XX:+UseShenandoahGC` on a build that lacks it fails at JVM startup with an "unrecognized VM option" style error — always confirm your specific JDK distribution includes it before depending on it in a deployment plan.

- Java 15 promoted **both** ZGC and Shenandoah to production-ready in the same release — a rare case of two competing, independently developed collectors reaching the same maturity milestone simultaneously.
- Shenandoah's design historically supported effective low-pause behavior across a wider range of heap sizes than ZGC's era-15 design, which was more specifically tuned for very large heaps — useful context when the heap in question is only a few gigabytes rather than tens or hundreds.
- As with any collector check, verify the actually active collector via `GarbageCollectorMXBean` rather than trusting that a requested flag silently took effect — this matters even more with Shenandoah, given its inconsistent availability across vendors.
- The choice between Shenandoah and ZGC for a specific workload is best made empirically (via representative load testing), not from documentation alone — both have matured and changed characteristics across JDK releases since this Java 15 milestone.
- Production-ready status affects vendor support commitments too — check your specific JDK vendor's documentation for what "supported" means contractually for Shenandoah in your distribution.
