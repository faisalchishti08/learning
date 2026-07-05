---
card: java
gi: 12
slug: amazon-corretto
title: Amazon Corretto
---

## 1. What it is

**Amazon Corretto** is Amazon Web Services' free, production-ready, multi-platform distribution of OpenJDK. It is what runs every Amazon service — from AWS Lambda to Amazon.com's own e-commerce backend. Amazon extracts security backports, performance improvements, and bug fixes from their internal JDK work and publishes them upstream to OpenJDK and as Corretto releases.

Corretto is available at [aws.amazon.com/corretto](https://aws.amazon.com/corretto) for Linux (x64, ARM64, musl), macOS (x64, ARM64), Windows (x64), Docker images, and as `amazoncorretto:` on Docker Hub.

AWS Lambda's default Java runtime is Corretto. AWS CodeBuild's Java managed environment uses Corretto.

## 2. Why & when

AWS created Corretto because:
- They run billions of JVM processes and found OpenJDK GA builds sometimes had stability or performance issues at Amazon-scale.
- They needed a JDK distribution they could patch quickly for security issues without waiting for the next GA release.
- They wanted to provide customers a free, tested JDK that matched what AWS services ran internally.

Use Corretto when:
- Deploying to AWS (Lambda, ECS, EKS, Elastic Beanstalk, CodeBuild) — you get the same JDK your runtime environment uses internally.
- You need free LTS support for Java 8 and 11 beyond Oracle's free window.
- You want Amazon's performance and stability patches (many are contributed back to OpenJDK but available in Corretto releases first).
- You are on ARM64 (AWS Graviton) and want a well-tested native binary.

For non-AWS environments Corretto is still fully valid, but Eclipse Temurin is equally good and more vendor-neutral.

## 3. Core concept

Corretto is built from OpenJDK source with Amazon's patches on top:

```
OpenJDK source (upstream)
       │
       │  Amazon patches (security fixes, performance, backports)
       ▼
Corretto source (on GitHub: github.com/corretto)
       │
       │  Build + test
       ▼
TCK certification (passes Oracle's TCK)
       │
       ▼
Corretto binary
  ├── LTS versions: 8, 11, 17, 21, 25
  ├── Platforms: Linux (glibc), Linux (musl), macOS, Windows
  └── Architectures: x64, ARM64 (Graviton), ...
```

**Amazon-specific contributions that landed back in OpenJDK:**
- Improved shenandoah GC pause reduction work.
- Linux container CPU/memory detection fixes (Java 8u191+).
- Various cryptography and TLS improvements.
- Performance fixes for ARM64 (Graviton).

**Corretto vs Temurin differences:**
| | Corretto | Temurin |
|---|---|---|
| Patches | Amazon's + upstream | OpenJDK upstream only |
| Docker Hub | `amazoncorretto:21` | `eclipse-temurin:21` |
| AWS Lambda default | Yes | No (Corretto is the default) |
| musl (Alpine-compatible) | Yes (`corretto-alpine`) | Yes (`temurin-alpine`) |
| LTS Java 8 free | Yes | Yes |

Both are TCK-certified, free, production-ready OpenJDK distributions. The practical difference is minimal unless you need AWS-specific patches or are debugging an issue on Lambda.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Corretto: OpenJDK + Amazon patches + TCK = production JDK for AWS">
  <defs>
    <marker id="acor" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Columns -->
  <!-- OpenJDK -->
  <rect x="20" y="65" width="120" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OpenJDK</text>
  <text x="80" y="102" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">upstream source</text>
  <line x1="140" y1="90" x2="178" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#acor)"/>

  <!-- Amazon patches -->
  <rect x="180" y="55" width="130" height="70" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="245" y="78" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Amazon</text>
  <text x="245" y="93" fill="#f0883e" font-size="9"  text-anchor="middle" font-family="sans-serif">security patches</text>
  <text x="245" y="107" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">perf backports</text>
  <text x="245" y="118" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Graviton tuning</text>
  <line x1="310" y1="90" x2="348" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#acor)"/>

  <!-- TCK -->
  <rect x="350" y="65" width="100" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="86" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">TCK</text>
  <text x="400" y="101" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">certified</text>
  <line x1="450" y1="90" x2="488" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#acor)"/>

  <!-- Corretto output -->
  <rect x="490" y="55" width="170" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="575" y="80" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Amazon Corretto</text>
  <text x="575" y="97" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">free · TCK-certified</text>
  <text x="575" y="111" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">LTS 8, 11, 17, 21, 25</text>

  <!-- AWS usage row -->
  <text x="350" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">Used by: AWS Lambda · ECS · EKS · CodeBuild · Amazon.com</text>
</svg>

Corretto = OpenJDK + Amazon patches + TCK certification. It's the JDK your AWS Lambda functions already run on.

## 5. Runnable example

Scenario: detect Corretto, recommend the matching AWS service runtime, and verify the ARM64 (Graviton) architecture — essential context when tuning microservices on AWS.

### Level 1 — Basic

```java
// CorrettoCheck.java
public class CorrettoCheck {
    public static void main(String[] args) {
        String vendor  = System.getProperty("java.vendor", "");
        String vendorV = System.getProperty("java.vendor.version", "<n/a>");
        boolean isCorretto = vendor.toLowerCase().contains("amazon");

        System.out.println("Vendor         : " + vendor);
        System.out.println("Vendor version : " + vendorV);
        System.out.println("Corretto?      : " + isCorretto);

        if (isCorretto) {
            System.out.println("Tip: you're running the same JDK as AWS Lambda/ECS internally.");
        } else {
            System.out.println("Not Corretto. For AWS deployments consider: amazoncorretto:<version>");
        }
    }
}
```

**How to run:** `java CorrettoCheck.java`

On Corretto, `java.vendor` is `"Amazon.com Inc."` and `java.vendor.version` is something like `"Corretto-21.0.3.9.1"` — the full Corretto version including Amazon's patch number.

### Level 2 — Intermediate

Same Corretto check extended to recommend the correct AWS Lambda runtime name and Graviton2/Graviton3 considerations for the detected JDK version and architecture.

```java
// CorrettoAwsAdvisor.java
public class CorrettoAwsAdvisor {

    static String lambdaRuntime(int feature) {
        return switch (feature) {
            case 8  -> "java8.al2 (Java 8 on Amazon Linux 2)";
            case 11 -> "java11 (Java 11 on Amazon Linux 2023)";
            case 17 -> "java17 (Java 17 on Amazon Linux 2023)";
            case 21 -> "java21 (Java 21 on Amazon Linux 2023)";
            default -> "custom runtime (no managed runtime for Java " + feature + ")";
        };
    }

    static String gravitonNote(String arch) {
        return switch (arch.toLowerCase()) {
            case "aarch64", "arm64" ->
                "Running on ARM64 (Graviton). Lambda arm64 architecture gives ~20% better price/perf.";
            case "x86_64", "amd64"  ->
                "Running on x86_64. Consider arm64 (Graviton) Lambda for cost reduction.";
            default -> "Architecture: " + arch;
        };
    }

    public static void main(String[] args) {
        int    feature = Runtime.version().feature();
        String arch    = System.getProperty("os.arch", "unknown");
        String vendor  = System.getProperty("java.vendor", "");
        boolean lts    = feature == 8 || feature == 11 || feature == 17 || feature == 21 || feature == 25;

        System.out.println("=== AWS / Corretto Deployment Advisor ===");
        System.out.printf("JDK    : Java %d (%s)%n", feature, vendor);
        System.out.printf("Arch   : %s%n", arch);
        System.out.printf("LTS    : %s%n%n", lts ? "YES" : "NO — not recommended for Lambda");

        System.out.println("AWS Lambda runtime  : " + lambdaRuntime(feature));
        System.out.println("Docker image        : amazoncorretto:" + feature);
        System.out.println("Alpine variant      : amazoncorretto:" + feature + "-al2023-full (Amazon Linux 2023)");
        System.out.println("Architecture note   : " + gravitonNote(arch));
    }
}
```

**How to run:** `java CorrettoAwsAdvisor.java`

Lambda has managed runtimes for Java 8, 11, 17, and 21. For other versions you'd use the Custom Runtime API (`PROVIDED_AL2023`). Graviton (ARM64) Lambda functions cost ~20% less per invocation than equivalent x86-64 functions.

### Level 3 — Advanced

Same AWS advisor grown to a full Corretto deployment profile: version detection, Lambda cold-start optimisation advice, GC recommendation for Lambda workloads, and checking for class-data sharing (CDS) — a JVM feature that dramatically reduces Lambda cold-start time.

```java
// CorrettoDeploymentProfile.java
import java.lang.management.*;
import java.util.*;

public class CorrettoDeploymentProfile {

    record GcRecommendation(String gcName, String useCase, String lambdaNote) {}

    static List<GcRecommendation> gcOptions(int feature) {
        List<GcRecommendation> recs = new ArrayList<>();
        recs.add(new GcRecommendation("G1GC (default)",
            "General purpose, balanced throughput + latency",
            "Lambda default. Good for most workloads."));
        if (feature >= 15) {
            recs.add(new GcRecommendation("ZGC (-XX:+UseZGC)",
                "Ultra-low pause (<1ms), high throughput",
                "Lambda: useful if p99 latency matters; slightly more memory overhead."));
        }
        recs.add(new GcRecommendation("SerialGC (-XX:+UseSerialGC)",
            "Single-threaded, lowest overhead",
            "Lambda: best for small, single-request functions (128–256 MB memory)."));
        return recs;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("╔═══════════════════════════════════════════╗");
        System.out.println("║   Amazon Corretto Deployment Profile      ║");
        System.out.println("╚═══════════════════════════════════════════╝\n");

        int    feature = Runtime.version().feature();
        String vendor  = System.getProperty("java.vendor", "");
        String arch    = System.getProperty("os.arch", "");
        boolean isLts  = Set.of(8, 11, 17, 21, 25).contains(feature);

        System.out.println("[ Runtime ]");
        System.out.printf("  Java    : %d (%s)%n", feature, vendor);
        System.out.printf("  Arch    : %s%n", arch);
        System.out.printf("  LTS     : %s%n", isLts ? "YES" : "NO");
        System.out.printf("  Corretto: %s%n%n", vendor.toLowerCase().contains("amazon") ? "YES" : "NO");

        // GC
        System.out.println("[ Active GC ]");
        ManagementFactory.getGarbageCollectorMXBeans()
            .forEach(gc -> System.out.printf("  %s  (collections=%d, time=%dms)%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime()));

        System.out.println("\n[ GC Recommendations for AWS Lambda ]");
        System.out.printf("  %-25s  %-45s  %s%n", "GC", "Use case", "Lambda note");
        System.out.println("  " + "-".repeat(100));
        for (var r : gcOptions(feature)) {
            System.out.printf("  %-25s  %-45s  %s%n", r.gcName(), r.useCase(), r.lambdaNote());
        }

        // Class Data Sharing
        System.out.println("\n[ Cold-start Optimisation ]");
        System.out.println("  Class Data Sharing (CDS): ");
        System.out.println("    javac + java -Xshare:dump → archive .jsa file");
        System.out.println("    java -Xshare:on -XX:SharedArchiveFile=app.jsa → use archive");
        System.out.println("    Lambda: reduces cold-start time by ~30% for large classpath apps");
        System.out.println("  SnapStart (Lambda Java 11+): freeze JVM after handler init → near-zero cold starts");

        // Virtual thread note
        System.out.println("\n[ Corretto " + feature + " Features ]");
        System.out.printf("  Virtual threads (Loom)   : %s%n", feature >= 21 ? "YES — use for I/O-bound Lambda handlers" : "NO (need Java 21)");
        System.out.printf("  Foreign Memory API (Panama): %s%n", feature >= 22 ? "YES" : "NO (need Java 22)");
        System.out.printf("  Pattern matching          : %s%n", feature >= 21 ? "YES (switch expressions, records)" : "partial");

        // Memory sizing
        System.out.println("\n[ Lambda Memory Sizing ]");
        long maxMem = Runtime.getRuntime().maxMemory() / (1024 * 1024);
        int procs   = Runtime.getRuntime().availableProcessors();
        System.out.printf("  Max heap   : %d MB (JVM sees: container-limited)%n", maxMem);
        System.out.printf("  vCPUs      : %d  (Lambda: 1 vCPU per 1769 MB memory)%n", procs);
        System.out.printf("  GC threads : auto-scaled to %d cores%n", procs);
        System.out.println("  Tip: 512 MB Lambda = 0.29 vCPU; upgrade to 1769 MB for 1 full vCPU.");
    }
}
```

**How to run:** `java CorrettoDeploymentProfile.java`

**Lambda SnapStart** (Java 11+) is an AWS-specific feature that restores a frozen JVM snapshot, achieving near-zero cold-start times — a major advantage of using Corretto on Lambda.

## 6. Walkthrough

Execution in `CorrettoDeploymentProfile.main`:

1. **Runtime detection** — `java.vendor` `"Amazon.com Inc."` confirms Corretto. `Runtime.version().feature()` is the major version; cross-referenced against `Set.of(8, 11, 17, 21, 25)` for LTS classification.

2. **Active GC** — `ManagementFactory.getGarbageCollectorMXBeans()` lists the running GC. On a default Corretto install, G1GC is the default (Java 9+). G1GC reports two beans: `"G1 Young Generation"` and `"G1 Old Generation"`. Each `getCollectionTime()` is the cumulative wall-clock milliseconds spent in GC — in a fresh JVM it's near zero.

3. **GC recommendations** — `gcOptions(feature)` builds a list of `GcRecommendation` records. `SerialGC` is often the best choice for AWS Lambda functions that handle a single request concurrently (Lambda invokes one handler instance per concurrent request) because it eliminates GC thread overhead.

4. **Class Data Sharing (CDS)** — CDS pre-processes class metadata into a shared archive (`.jsa`) file. On Lambda, the JVM loads this archive at startup, skipping class verification for already-processed classes. Combined with **Lambda SnapStart**, this can reduce cold-start time from 3–5 seconds to under 200 ms for a Spring Boot application.

5. **Memory/vCPU** — `Runtime.getRuntime().maxMemory()` returns the JVM's maximum heap in bytes. On Lambda, the JVM correctly reads the cgroup memory limit (Corretto 8u191+). `availableProcessors()` reflects the cgroup CPU quota; at 512 MB Lambda = 0.29 vCPU, so `procs = 1` (fractional CPUs round to 1 for `availableProcessors()`).

Lambda cold-start data flow:
```
Lambda invocation arrives
  → Container cold-start (if new container)
      → Corretto JVM starts
      → Loads class archive (CDS) → fast class loading
      → Spring context initialises (warm class cache from SnapStart snapshot)
      → Handler.handleRequest() called
          → GC: G1/SerialGC manages heap
          → Virtual threads: handle I/O concurrently
  → Response returned
```

## 7. Gotchas & takeaways

> **Lambda SnapStart freezes state at handler init time.** Network connections, random seeds, and timestamps captured during `@PostConstruct` are frozen and replayed. Connections need to be re-established on restore. Use `@SnapshotStart`-aware patterns: establish connections lazily or in `afterRestore()`.

> **Lambda `availableProcessors()` returns at least 1 even on fractional vCPU allocations.** Thread pool sizing based on `availableProcessors()` still works — but `Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())` on a 128 MB Lambda creates 1 thread pool thread, which may be correct or a bottleneck depending on your workload.

- Corretto is AWS's free, TCK-certified OpenJDK distribution — the JDK Lambda, ECS, and CodeBuild use internally.
- For ARM64 (Graviton) workloads, Corretto has well-tested native builds; `amazoncorretto:21-arm64v8` on Docker Hub.
- **Lambda SnapStart** (Java 11+) + CDS → near-zero cold starts. Essential for latency-sensitive Lambda functions.
- **SerialGC** (`-XX:+UseSerialGC`) is often best for small Lambda functions (≤512 MB); G1GC is better for larger, long-lived instances.
- Corretto backports security and performance fixes faster than upstream OpenJDK GAs — useful when you cannot upgrade the major version quickly.
- Free LTS for Java 8 and 11: Corretto provides ongoing patches after Oracle's free Java 8/11 support window ended.
