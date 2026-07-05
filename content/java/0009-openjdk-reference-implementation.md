---
card: java
gi: 9
slug: openjdk-reference-implementation
title: OpenJDK (reference implementation)
---

## 1. What it is

**OpenJDK** (Open Java Development Kit) is the open-source, GPL-licensed reference implementation of Java SE. When Oracle or the Java community finalises a new Java SE specification, OpenJDK is the canonical implementation that demonstrates what that spec means in code. Every major JDK distribution — Eclipse Temurin, Amazon Corretto, Microsoft Build of OpenJDK, Azul Zulu, Oracle JDK — is built from OpenJDK source.

The project lives at [openjdk.org](https://openjdk.org). It is developed by Oracle, Red Hat, IBM, SAP, Amazon, Microsoft, and community contributors through the **JDK Enhancement Proposal (JEP)** process.

## 2. Why & when

Before OpenJDK (announced 2006, open-sourced 2007), the JDK was proprietary. This mattered because:
- You couldn't ship Java in a Linux distribution without a proprietary license.
- You couldn't study, modify, or redistribute the JVM source.
- Security researchers couldn't audit the implementation.

Today OpenJDK matters because:
- **It is Java.** All compliant JDKs are OpenJDK forks that pass the TCK.
- **Features land here first.** JEPs (new language/JVM features) are developed in OpenJDK Project repositories (Project Loom → virtual threads, Project Panama → native interop, Project Valhalla → value types).
- **You are using it.** If you run Eclipse Temurin, Corretto, or Microsoft JDK, you are running OpenJDK source compiled by a different vendor.

## 3. Core concept

OpenJDK is organised as a **forest of repositories** and governed by the **JEP process**:

```
JEP (Java Enhancement Proposal)
  → Draft → Candidate → Targeted → Integrated → Completed
```

A JEP describes a feature (e.g. JEP 444 — Virtual Threads). It goes through review, is assigned a target release, then merged into the main OpenJDK repository. **Preview features** land in one release gated behind `--enable-preview`; they are finalised (or dropped) in a later release.

Key OpenJDK projects currently active:
- **Project Loom** — virtual threads (`Thread.ofVirtual()`), structured concurrency. Delivered in Java 21.
- **Project Panama** — Foreign Function & Memory API for native interop without JNI. Delivered progressively in Java 19–22.
- **Project Valhalla** — value types (no-identity objects, primitive generics). Still in development.
- **Project Leyden** — ahead-of-time classloading and startup optimisation.
- **Project Babylon** — code reflection and GPU/accelerator targeting.

The **TCK (Technology Compatibility Kit)** is Oracle's test suite; only JDKs that pass it may call themselves "Java SE certified." OpenJDK passes; so do Temurin, Corretto, etc.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OpenJDK is the root; vendor JDK distributions fork from it">
  <defs>
    <marker id="aojdk" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- OpenJDK root -->
  <rect x="240" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="43" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">OpenJDK</text>
  <text x="340" y="59" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GPL-2.0 + Classpath Exception</text>

  <!-- Arrows to distributions -->
  <line x1="290" y1="70" x2="110" y2="138" stroke="#6db33f" stroke-width="1.4" marker-end="url(#aojdk)"/>
  <line x1="320" y1="70" x2="240" y2="138" stroke="#6db33f" stroke-width="1.4" marker-end="url(#aojdk)"/>
  <line x1="340" y1="70" x2="340" y2="138" stroke="#6db33f" stroke-width="1.4" marker-end="url(#aojdk)"/>
  <line x1="360" y1="70" x2="440" y2="138" stroke="#6db33f" stroke-width="1.4" marker-end="url(#aojdk)"/>
  <line x1="390" y1="70" x2="570" y2="138" stroke="#6db33f" stroke-width="1.4" marker-end="url(#aojdk)"/>

  <!-- Distribution boxes -->
  <rect x="30"  y="140" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Eclipse Temurin</text>
  <text x="110" y="177" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(Adoptium, free)</text>

  <rect x="200" y="140" width="130" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="265" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Amazon Corretto</text>
  <text x="265" y="177" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(AWS, free)</text>

  <rect x="340" y="140" width="100" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="390" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Oracle JDK</text>
  <text x="390" y="177" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(licensed)</text>

  <rect x="450" y="140" width="110" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Azul Zulu</text>
  <text x="505" y="177" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(free community)</text>

  <rect x="570" y="140" width="100" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="620" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Microsoft JDK</text>
  <text x="620" y="177" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(free)</text>
</svg>

All major JDK distributions are compiled from OpenJDK source; they differ only in vendor patches, support terms, and packaging.

## 5. Runnable example

Scenario: a program that identifies its own JDK distribution (OpenJDK vs Oracle JDK vs others), checks whether a preview feature is available, and reads an OpenJDK-sourced system property — demonstrating how to reason about which OpenJDK fork you're running.

### Level 1 — Basic

```java
// OpenJdkInfo.java
public class OpenJdkInfo {
    public static void main(String[] args) {
        System.out.println("Runtime:  " + System.getProperty("java.runtime.name"));
        System.out.println("Version:  " + System.getProperty("java.version"));
        System.out.println("Vendor:   " + System.getProperty("java.vendor"));
        System.out.println("VM:       " + System.getProperty("java.vm.name"));
        System.out.println("Build:    " + System.getProperty("java.runtime.version"));
        System.out.println();
        System.out.println("Is OpenJDK? " + System.getProperty("java.vm.name", "").contains("OpenJDK"));
    }
}
```

**How to run:** `java OpenJdkInfo.java`

If you're on Eclipse Temurin or Corretto, `java.vm.name` will contain `"OpenJDK"`. Oracle JDK also reports `"Java HotSpot(TM)"` but its `java.vendor` is `"Oracle Corporation"`. The vendor + VM name together identify the distribution.

### Level 2 — Intermediate

Same scenario extended to detect the OpenJDK distribution by probing vendor-specific system properties and checking if a Project Loom feature (virtual threads, Java 21+) is available.

```java
// OpenJdkDistribution.java
import java.util.Map;
import java.util.LinkedHashMap;

public class OpenJdkDistribution {

    enum Distro {
        ECLIPSE_TEMURIN, AMAZON_CORRETTO, MICROSOFT_JDK, AZUL_ZULU, ORACLE_JDK, GRAALVM, UNKNOWN;

        static Distro detect() {
            String vendor = System.getProperty("java.vendor", "").toLowerCase();
            String vm     = System.getProperty("java.vm.name", "").toLowerCase();
            if (vendor.contains("eclipse") || vendor.contains("adoptium")) return ECLIPSE_TEMURIN;
            if (vendor.contains("amazon"))   return AMAZON_CORRETTO;
            if (vendor.contains("microsoft")) return MICROSOFT_JDK;
            if (vendor.contains("azul"))     return AZUL_ZULU;
            if (vm.contains("graalvm") || vendor.contains("graalvm")) return GRAALVM;
            if (vendor.contains("oracle"))   return ORACLE_JDK;
            return UNKNOWN;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== OpenJDK Distribution Probe ===");
        System.out.printf("Distribution : %s%n", Distro.detect());

        Map<String, String> props = new LinkedHashMap<>();
        for (String k : new String[]{"java.version","java.vendor","java.vm.name",
                                     "java.runtime.name","java.vendor.version"}) {
            props.put(k, System.getProperty(k, "<not set>"));
        }
        props.forEach((k,v) -> System.out.printf("  %-24s : %s%n", k, v));

        // Loom (Project Loom → virtual threads, Java 21+)
        int feature = Runtime.version().feature();
        System.out.println("\nJEP features by version:");
        System.out.printf("  JEP 444 Virtual Threads (Loom)     : %s (need Java 21, have %d)%n",
            feature >= 21 ? "AVAILABLE" : "NOT available", feature);
        System.out.printf("  JEP 454 Foreign Function API (Panama): %s (need Java 22, have %d)%n",
            feature >= 22 ? "AVAILABLE" : "NOT available", feature);
        System.out.printf("  JEP 456 Unnamed Classes (preview)   : %s (need Java 21+)%n",
            feature >= 21 ? "check --enable-preview" : "NOT available");
    }
}
```

**How to run:** `java OpenJdkDistribution.java`

`java.vendor.version` is a vendor-specific string (e.g. `"Corretto-21.0.3.9.1"` for Corretto). It is not present on all distributions.

### Level 3 — Advanced

Same distribution-detection scenario grown to demonstrate: detecting distribution, verifying TCK pass (heuristically), probing a specific JEP feature at runtime, and using virtual threads if available.

```java
// OpenJdkAudit.java
import java.util.*;
import java.lang.reflect.*;
import java.lang.management.*;

public class OpenJdkAudit {

    public static void main(String[] args) throws Exception {
        System.out.println("╔════════════════════════════════════╗");
        System.out.println("║       OpenJDK Distribution Audit   ║");
        System.out.println("╚════════════════════════════════════╝\n");

        // ── Distribution fingerprint ──────────────────────────
        String vendor  = System.getProperty("java.vendor", "");
        String vmName  = System.getProperty("java.vm.name", "");
        String runtime = System.getProperty("java.runtime.name", "");
        String vendorV = System.getProperty("java.vendor.version", "<n/a>");

        System.out.println("[ Distribution ]");
        System.out.println("  Vendor          : " + vendor);
        System.out.println("  Vendor version  : " + vendorV);
        System.out.println("  VM              : " + vmName);
        System.out.println("  Runtime         : " + runtime);
        System.out.println("  OpenJDK lineage : " + (vmName.contains("OpenJDK") || runtime.contains("OpenJDK")));

        // ── TCK pass heuristic ────────────────────────────────
        // Real TCK is private; we check a few well-defined behaviours
        System.out.println("\n[ TCK Heuristics ]");
        checkTck("String.chars() returns IntStream",
            () -> "hello".chars().count() == 5);
        checkTck("Collections.unmodifiableList throws UnsupportedOperationException",
            () -> {
                try { Collections.unmodifiableList(new ArrayList<>()).add("x"); return false; }
                catch (UnsupportedOperationException e) { return true; }
            });
        checkTck("Thread.currentThread().isVirtual() exists (Java 21+)",
            () -> {
                try {
                    Thread.class.getMethod("isVirtual");
                    return true;
                } catch (NoSuchMethodException e) { return Runtime.version().feature() < 21; }
            });

        // ── JEP feature probe ─────────────────────────────────
        System.out.println("\n[ JEP Feature Probe ]");
        int feature = Runtime.version().feature();
        boolean hasVT = feature >= 21;
        System.out.println("  Virtual Threads (JEP 444, Java 21): " + (hasVT ? "YES" : "NO"));
        if (hasVT) {
            long start = System.nanoTime();
            List<Thread> vthreads = new ArrayList<>();
            for (int i = 0; i < 100; i++) {
                int id = i;
                vthreads.add(Thread.ofVirtual().start(() -> {
                    // each does a tiny bit of "work"
                    long dummy = 0;
                    for (int j = 0; j < 1000; j++) dummy += j;
                }));
            }
            for (Thread t : vthreads) t.join();
            long ms = (System.nanoTime() - start) / 1_000_000;
            System.out.printf("  100 virtual threads completed in %dms%n", ms);
        }

        // ── GC report ─────────────────────────────────────────
        System.out.println("\n[ GC (platform config) ]");
        ManagementFactory.getGarbageCollectorMXBeans()
            .forEach(gc -> System.out.printf("  %-32s  pools=%s%n",
                gc.getName(), Arrays.toString(gc.getMemoryPoolNames())));
    }

    static void checkTck(String name, java.util.concurrent.Callable<Boolean> check) {
        try {
            boolean pass = check.call();
            System.out.printf("  %-55s %s%n", name, pass ? "PASS" : "FAIL");
        } catch (Exception e) {
            System.out.printf("  %-55s ERROR: %s%n", name, e.getMessage());
        }
    }
}
```

**How to run:** `java OpenJdkAudit.java`

The 100 virtual threads completing in under 10 ms demonstrates Project Loom's lightweight scheduler — the same work would take much longer with 100 platform threads due to context-switch overhead.

## 6. Walkthrough

Execution in `OpenJdkAudit.main`:

1. **Distribution fingerprint** — `java.vendor`, `java.vm.name`, `java.runtime.name` are set by the JVM launcher at startup. On Temurin: `"Eclipse Adoptium"` / `"OpenJDK 64-Bit Server VM"`. On Corretto: `"Amazon.com Inc."` / `"OpenJDK 64-Bit Server VM"`. Both say `"OpenJDK"` in vm name.

2. **TCK heuristics** — three behavioural checks that every spec-compliant JVM must pass:
   - `"hello".chars().count() == 5`: `String.chars()` (Java 9 API) must return an `IntStream` of code points; `.count()` must be `5`.
   - `Collections.unmodifiableList(...)` must throw `UnsupportedOperationException` on mutating operations — a contract in the Java SE spec.
   - `Thread.class.getMethod("isVirtual")` exists on Java 21+; if `feature < 21` the absence is correct.

3. **Virtual threads** — `Thread.ofVirtual().start(runnable)` schedules 100 virtual threads. Each runs a tight loop. The JVM's scheduler (ForkJoinPool by default) multiplexes these onto a small number of OS threads. All 100 complete in under 10 ms because they never block on I/O; the scheduler never has to park them.

4. **GC report** — `getGarbageCollectorMXBeans()` lists the active GC collectors. On a default JDK 21 install you'll see `"G1 Young Generation"` and `"G1 Old Generation"` (G1GC is default since Java 9). On a `-XX:+UseZGC` JVM you'd see `"ZGC Cycles"`.

Request-style flow:
```
main entry
  → read JVM properties (String values, set by launcher)
  → run TCK checks (method calls → boolean results)
  → spawn 100 virtual threads (Thread.ofVirtual)
      each thread: run loop, complete
  → join all threads
  → query GC MXBeans
  → print report
```

## 7. Gotchas & takeaways

> **All major free JDK distributions are OpenJDK builds.** Switching from Oracle JDK to Temurin or Corretto requires zero source changes — they are the same bytecode, same JVM, same API. The difference is vendor support terms and backport cadence.

> **Preview features require `--enable-preview` at compile AND run time.** A class compiled with `javac --enable-preview --release 21` must also be run with `java --enable-preview`. Forgetting the runtime flag gives `Error: LinkageError occurred while loading main class`.

- OpenJDK is GPL-2.0 + Classpath Exception — you can ship OpenJDK-based programs without GPL-contaminating your app.
- All compliant JDKs (Temurin, Corretto, Zulu, Microsoft, Oracle JDK) are OpenJDK forks that pass the TCK.
- New features arrive via JEPs: draft → candidate → targeted → integrated → completed.
- Active projects: Loom (virtual threads ✓ Java 21), Panama (FFI ✓ Java 22), Valhalla (value types, upcoming), Leyden (startup speed).
- Virtual threads (`Thread.ofVirtual()`) are the biggest concurrency change since Java 5's `java.util.concurrent`.
- Use `Runtime.version().feature()` to gate code on JEP features at runtime.
