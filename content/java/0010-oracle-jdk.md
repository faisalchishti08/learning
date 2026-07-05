---
card: java
gi: 10
slug: oracle-jdk
title: Oracle JDK
---

## 1. What it is

**Oracle JDK** is Oracle Corporation's commercial distribution of the Java Development Kit, built from OpenJDK source. It is the original "official" Java distribution — what developers downloaded from java.sun.com / java.oracle.com for decades. Since Oracle's acquisition of Sun in 2010, Oracle JDK has gone through several licensing changes that profoundly affect whether you can use it for free in production.

As of **Oracle JDK 17 (September 2021)**, Oracle moved back to the **Oracle No-Fee Terms and Conditions (NFTC)** license — free for commercial use including production. Before that, JDK 9–16 required a paid subscription for production use (under the Oracle Technology Network license). JDK 8 is still under a complex licensing situation.

## 2. Why & when

Oracle JDK matters because:
- **GraalVM** is distributed by Oracle and shares the Oracle JDK lineage.
- **Oracle support contracts** — enterprises that need guaranteed long-term patches beyond the community LTS window pay Oracle for JDK support (up to 10 years on LTS releases).
- **Flight Recorder & Mission Control** — these profiling tools (historically Oracle JDK-only) are now open-sourced in OpenJDK but are most mature in the Oracle distribution.
- **Legacy policy** — many enterprise procurement policies approved "Oracle JDK" by name; switching requires a policy change even when the code is identical.

You use Oracle JDK when:
- Your organisation has an Oracle support agreement.
- You need extended-patch-window LTS support beyond what the community provides.
- You are building with GraalVM (Oracle's high-performance JDK with native image compilation).

For everyone else, a free OpenJDK distribution (Temurin, Corretto) is functionally identical.

## 3. Core concept

Oracle JDK and OpenJDK have been technically nearly identical since Java 11 (when Oracle began contributing Oracle JDK-specific code back to OpenJDK). Before Java 11, Oracle JDK included a handful of components not in OpenJDK:

| Component | Pre-Java 11 | Java 11+ |
|---|---|---|
| Java Flight Recorder (JFR) | Oracle JDK only | OpenJDK (open-sourced) |
| Java Mission Control (JMC) | Oracle JDK only | OpenJDK (separate project) |
| Font rendering | Oracle JDK included fonts | Same |
| Cryptographic libraries | Slightly different | Aligned |
| GraalVM (optional) | Oracle distribution | Separate Oracle GraalVM project |

**License history (important):**
```
Java ≤ 8u202 (2019)   : BCL (Binary Code License) — free for personal use
Java 8u211 – 16       : Oracle Technology Network license — paid for production
Java 17+              : NFTC — free for commercial use including production
Java 8 LTS (OTN)      : Still requires paid subscription for updates
OpenJDK builds        : Always GPL-2.0 + CPE, always free
```

**The practical rule:** if you need Java 17 or later, Oracle JDK is free. If you need Java 8 LTS patches beyond 8u202, use Amazon Corretto or Azul Zulu (free OpenJDK-based LTS for Java 8).

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Oracle JDK licensing timeline from Java 8 to Java 17+">
  <defs>
    <marker id="aojt" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <!-- Timeline spine -->
  <line x1="40" y1="100" x2="650" y2="100" stroke="#8b949e" stroke-width="2" marker-end="url(#aojt)"/>

  <!-- Java 8 era -->
  <rect x="40" y="65" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java 8 (2014)</text>
  <text x="120" y="103" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">BCL: free personal</text>
  <text x="120" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">≤8u202: free production</text>

  <!-- Java 9-16 era -->
  <rect x="215" y="65" width="180" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="305" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java 9–16 (2017–2021)</text>
  <text x="305" y="103" fill="#f85149" font-size="9"  text-anchor="middle" font-family="sans-serif">OTN: paid for production</text>
  <text x="305" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">OpenJDK builds: free</text>

  <!-- Java 17+ era -->
  <rect x="410" y="65" width="230" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="525" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java 17+ (2021–present)</text>
  <text x="525" y="103" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">NFTC: free for production</text>
  <text x="525" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">+ Oracle support available</text>

  <!-- Version markers -->
  <text x="120" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">8u202</text>
  <line x1="120" y1="115" x2="120" y2="145" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="410" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java 17</text>
  <line x1="410" y1="115" x2="410" y2="145" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2"/>
</svg>

Oracle JDK licensing changed three times; Java 17+ (NFTC) is free for commercial use. Older versions have complex rules.

## 5. Runnable example

Scenario: detect whether the running JDK is Oracle JDK, and determine which license applies — important for compliance auditing in enterprise environments.

### Level 1 — Basic

```java
// OracleJdkCheck.java
public class OracleJdkCheck {
    public static void main(String[] args) {
        String vendor  = System.getProperty("java.vendor", "");
        String vmName  = System.getProperty("java.vm.name", "");
        boolean isOracle = vendor.toLowerCase().contains("oracle");

        System.out.println("Vendor : " + vendor);
        System.out.println("VM     : " + vmName);
        System.out.println("Oracle JDK? " + isOracle);
        if (isOracle) {
            System.out.println("License note: check Oracle JDK version for applicable terms.");
        } else {
            System.out.println("Non-Oracle JDK: likely GPL-2.0 + CPE (free for production).");
        }
    }
}
```

**How to run:** `java OracleJdkCheck.java`

On Oracle JDK the vendor string contains `"Oracle Corporation"`. On Temurin/Corretto it contains `"Eclipse Adoptium"` / `"Amazon.com Inc."`.

### Level 2 — Intermediate

Same Oracle JDK check extended to emit a compliance verdict based on version + vendor — useful as a CI gate to prevent accidentally shipping a paid-license JDK into a production environment.

```java
// OracleJdkCompliance.java
public class OracleJdkCompliance {

    enum License { FREE, PAID, UNKNOWN }

    static License oracleLicense(int feature) {
        if (feature <= 8)  return License.UNKNOWN;  // depends on update number (8u202 boundary)
        if (feature <= 16) return License.PAID;     // OTN license era
        return License.FREE;                         // NFTC: Java 17+
    }

    public static void main(String[] args) {
        String vendor  = System.getProperty("java.vendor", "");
        String version = System.getProperty("java.version", "");
        int feature    = Runtime.version().feature();
        boolean isOracle = vendor.toLowerCase().contains("oracle") &&
                           !System.getProperty("java.vm.name","").contains("GraalVM CE");

        System.out.println("=== Oracle JDK Compliance Check ===");
        System.out.println("Vendor  : " + vendor);
        System.out.println("Version : " + version + " (feature release " + feature + ")");
        System.out.println("Oracle JDK detected: " + isOracle);

        if (isOracle) {
            License lic = oracleLicense(feature);
            System.out.println("License : " + lic);
            switch (lic) {
                case FREE    -> System.out.println("  OK: Oracle JDK 17+ is free under NFTC including production.");
                case PAID    -> System.out.println("  WARNING: Oracle JDK 9-16 requires paid subscription for production use.");
                case UNKNOWN -> System.out.println("  CHECK: Java 8 compliance depends on update version. ≤8u202 was free; ≥8u211 requires license.");
            }
        } else {
            System.out.println("Non-Oracle distribution: free for production use (GPL-2.0 + CPE).");
        }
    }
}
```

**How to run:** `java OracleJdkCompliance.java`

This kind of check is useful in CI: fail the build if an engineer accidentally configured Oracle JDK 11 (paid era) in the Docker base image.

### Level 3 — Advanced

Same compliance scenario grown to probe Oracle JDK–specific features (JFR, Mission Control availability) and demonstrate Java Flight Recorder — the production-grade profiling tool that was Oracle JDK–exclusive until Java 11.

```java
// OracleJdkFeatures.java
import java.io.*;
import java.nio.file.*;
import java.lang.management.*;
import java.util.*;

public class OracleJdkFeatures {

    public static void main(String[] args) throws Exception {
        System.out.println("╔══════════════════════════════════════╗");
        System.out.println("║    Oracle JDK Features Probe         ║");
        System.out.println("╚══════════════════════════════════════╝\n");

        // ── Distribution ────────────────────────────────────────
        String vendor  = System.getProperty("java.vendor", "");
        boolean isOracle = vendor.toLowerCase().contains("oracle");
        System.out.println("[ Distribution ]");
        System.out.println("  Vendor     : " + vendor);
        System.out.println("  Oracle JDK : " + isOracle);
        System.out.println("  Version    : " + Runtime.version());

        // ── Java Flight Recorder (JFR) ──────────────────────────
        // JFR was Oracle JDK-only until Java 11; now in all OpenJDK builds
        System.out.println("\n[ Java Flight Recorder (JFR) ]");
        boolean hasJfr = hasClass("jdk.jfr.FlightRecorder");
        System.out.println("  jdk.jfr available: " + hasJfr);
        if (hasJfr) {
            // Start a short JFR recording
            Class<?> fr   = Class.forName("jdk.jfr.FlightRecorder");
            Class<?> conf = Class.forName("jdk.jfr.Configuration");
            var configs = (List<?>) conf.getMethod("getConfigurations").invoke(null);
            System.out.println("  JFR configurations: " + configs.stream()
                .map(c -> { try { return (String)c.getClass().getMethod("getName").invoke(c); } catch (Exception e) { return "?"; } })
                .toList());
            System.out.println("  JFR is ready. In production: jcmd <pid> JFR.start  to record.");
        }

        // ── GraalVM detection ────────────────────────────────────
        System.out.println("\n[ GraalVM / Oracle-specific JIT ]");
        boolean isGraal = System.getProperty("java.vm.name","").contains("GraalVM") ||
                          hasClass("org.graalvm.compiler.core.GraalCompiler");
        System.out.println("  GraalVM JIT (JVMCI): " + isGraal);
        System.out.println("  HotSpot JIT:         " + !isGraal);

        // ── Platform threads vs virtual threads ──────────────────
        System.out.println("\n[ Concurrency ]");
        int feature = Runtime.version().feature();
        System.out.println("  Platform threads  : always available");
        System.out.println("  Virtual threads   : " + (feature >= 21 ? "YES (Java 21+)" : "NO (need Java 21+)"));
        if (feature >= 21) {
            long[] results = new long[5];
            List<Thread> vt = new ArrayList<>();
            for (int i = 0; i < 5; i++) {
                final int idx = i;
                vt.add(Thread.ofVirtual().name("vt-" + i).start(() -> results[idx] = Thread.currentThread().threadId()));
            }
            for (Thread t : vt) t.join();
            System.out.println("  Virtual thread IDs: " + Arrays.toString(results));
        }

        // ── Summary ──────────────────────────────────────────────
        System.out.println("\n[ License Summary ]");
        int feat = Runtime.version().feature();
        if (!isOracle) {
            System.out.println("  Free OpenJDK distribution — no license concern.");
        } else if (feat >= 17) {
            System.out.println("  Oracle JDK " + feat + " — NFTC license, FREE for production.");
        } else if (feat >= 9) {
            System.out.println("  Oracle JDK " + feat + " — OTN license, PAID for production. Upgrade to 17+.");
        } else {
            System.out.println("  Oracle JDK 8 — check update version. Use Corretto/Temurin for free LTS.");
        }
    }

    static boolean hasClass(String name) {
        try { Class.forName(name); return true; } catch (ClassNotFoundException e) { return false; }
    }
}
```

**How to run:** `java OracleJdkFeatures.java`

JFR (`jdk.jfr`) is available on all JDK 11+ distributions (not just Oracle JDK). The probe reflects the historical reality that JFR was once a paid Oracle differentiator.

## 6. Walkthrough

Execution in `OracleJdkFeatures.main`:

1. **Distribution detection** — `java.vendor` is set by the JVM launcher. On Oracle JDK it contains `"Oracle Corporation"`; on OpenJDK builds it contains the vendor name (Eclipse Adoptium, Amazon.com Inc., etc.). `!vmName.contains("GraalVM CE")` excludes GraalVM Community Edition (which is free and not the commercial Oracle JDK).

2. **JFR probe** — `Class.forName("jdk.jfr.FlightRecorder")` checks if the JFR module (`jdk.jfr`) is on the module path. On a full JDK this always succeeds from Java 11+. `Configuration.getConfigurations()` returns built-in recording profiles: `"default"` (low-overhead, suitable for always-on production recording) and `"profile"` (higher-detail for debugging).

3. **GraalVM detection** — GraalVM replaces HotSpot's JIT with its own Graal compiler via the JVMCI (JVM Compiler Interface). Probing the class `org.graalvm.compiler.core.GraalCompiler` detects it; absence means standard HotSpot C2.

4. **Virtual threads** — `Thread.ofVirtual().name("vt-" + i).start(...)` creates named virtual threads. `Thread.currentThread().threadId()` returns a unique ID per virtual thread, different from the carrier platform thread ID. Virtual threads can have the same carrier thread ID at different moments (the scheduler unmounts/remounts them), but their own `threadId()` is stable.

5. **License summary** — classifies the running JDK into the three license eras. On a CI system this block could `System.exit(1)` when `isOracle && feat < 17` to fail the build.

Data state:
```
main()
  → vendor string (JVM property, set at launch)
  → Class.forName probe (classloader lookup, no object instantiation)
  → JFR Configuration.getConfigurations() (reflection call → List<Configuration>)
  → Thread.ofVirtual × 5 (JVM scheduler, virtual thread table)
  → join all threads (barrier)
  → license verdict (if/else on vendor + feature)
```

## 7. Gotchas & takeaways

> **Oracle JDK 8 update numbers matter.** 8u201 and earlier were free; 8u211 and later require an Oracle license for production. The boundary is not the major version (8) but the update number. Many organisations unknowingly ran unlicensed Java 8 after 2019.

> **Java Flight Recorder is no longer Oracle JDK–exclusive.** It was open-sourced and added to OpenJDK in Java 11. Any JDK 11+ distribution — Temurin, Corretto, Zulu — ships JFR. You do not need Oracle JDK for JFR.

- Oracle JDK 17+ (NFTC): free for commercial/production. Oracle JDK 9–16 (OTN): paid. Java 8: check the update number.
- Oracle JDK and OpenJDK are technically nearly identical since Java 11; the difference is vendor patches and support terms.
- **JFR (Java Flight Recorder)** is available on all JDK 11+ distributions; use `jcmd <pid> JFR.start` to record in production.
- For free, long-term Java 8 support, use Amazon Corretto 8 or Azul Zulu 8.
- GraalVM (Oracle JDK variant) provides native image compilation, additional languages, and a different JIT — it is a superset of Oracle JDK, not just a different version.
- In enterprise procurement, verify that Oracle JDK is version 17+ (or covered by an existing Oracle support contract) before using it in production.
