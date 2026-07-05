---
card: java
gi: 11
slug: eclipse-temurin-adoptium
title: Eclipse Temurin (Adoptium)
---

## 1. What it is

**Eclipse Temurin** is the open-source, TCK-certified OpenJDK distribution produced by the **Eclipse Adoptium** working group. It is the community's answer to the question: "which free JDK should I use?" Temurin is built from OpenJDK source, tested against Oracle's Technology Compatibility Kit (TCK), and published under the GPL-2.0 + Classpath Exception license — free for all uses including commercial production.

Before the Eclipse Foundation rebrand, Temurin was known as **AdoptOpenJDK** (Adopt = OpenJDK community-built, later migrated to Adoptium). The working group includes Microsoft, IBM, Red Hat, Azul, iJUG, and others.

Available at [adoptium.net](https://adoptium.net) for all major platforms and LTS versions (8, 11, 17, 21, 25).

## 2. Why & when

The challenge before AdoptOpenJDK (circa 2017) was that Oracle's JDK had licensing restrictions and no other vendor published a free, tested, multi-platform binary. The community filled the gap.

Use Eclipse Temurin when:
- You want a free, production-ready JDK with no licensing concerns.
- You need a docker base image: `eclipse-temurin:21` is the most widely used OpenJDK Docker image.
- You need a consistent JDK across macOS (Apple Silicon + Intel), Windows, Linux (x64 + ARM64 + s390x + ppc64le).
- You want LTS support backed by a vendor-neutral foundation.
- Your existing workflow used `adoptopenjdk:...` Docker images (Temurin is the direct successor).

Temurin is the default recommended JDK for Spring Boot, Jakarta EE, and most Java frameworks in their documentation.

## 3. Core concept

Temurin's build pipeline is fully open-source and auditable at github.com/adoptium. Key properties:

**TCK certification** — Temurin passes Oracle's TCK before each release, meaning it is a spec-compliant Java SE implementation. Not all OpenJDK builds are TCK-tested; Temurin is.

**API/AQ (AQAvit)** — In addition to the TCK, Adoptium runs its own test suite (AQAvit) covering security, load, functional, and extended-verification tests. This is above and beyond what the TCK requires.

**Release schedule** — Temurin tracks OpenJDK GA (General Availability) releases closely, usually publishing within days. LTS releases (8, 11, 17, 21, 25) receive extended patches coordinated by the working group.

**Variant flavours:**
| Image | Description |
|---|---|
| JDK | Full development kit (javac + java + all tools) |
| JRE | Runtime only (java command, no javac) — smaller |
| Alpine / Slim | Minimal Linux base — smaller Docker images |
| Full | Larger image with more debug tooling |

**Docker images:** `eclipse-temurin:21` (JDK), `eclipse-temurin:21-jre`, `eclipse-temurin:21-jdk-alpine`.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Temurin build pipeline: OpenJDK source to TCK to binary">
  <defs>
    <marker id="atm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Source -->
  <rect x="20" y="80" width="120" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OpenJDK</text>
  <text x="80" y="114" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">source (GPL)</text>

  <line x1="140" y1="102" x2="180" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#atm)"/>

  <!-- Build -->
  <rect x="182" y="80" width="100" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="232" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Build</text>
  <text x="232" y="114" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Adoptium CI</text>

  <line x1="282" y1="102" x2="322" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#atm)"/>

  <!-- TCK + AQAvit -->
  <rect x="324" y="70" width="120" height="64" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.8"/>
  <text x="384" y="92" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">TCK</text>
  <text x="384" y="107" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">spec compliance</text>
  <text x="384" y="121" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">+ AQAvit tests</text>

  <line x1="444" y1="102" x2="484" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#atm)"/>

  <!-- Distribution -->
  <rect x="486" y="70" width="174" height="64" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="573" y="92" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Eclipse Temurin</text>
  <text x="573" y="107" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">TCK-certified binary</text>
  <text x="573" y="121" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">GPL-2.0 + CPE (free)</text>

  <!-- Platforms -->
  <text x="486" y="155" fill="#8b949e" font-size="9" font-family="sans-serif">Linux x64 · ARM64 · s390x · ppc64le</text>
  <text x="486" y="168" fill="#8b949e" font-size="9" font-family="sans-serif">macOS x64 · ARM64 · Windows x64</text>
</svg>

Temurin: OpenJDK source → Adoptium CI build → TCK + AQAvit → certified binary for 8+ platforms.

## 5. Runnable example

Scenario: identify whether we're running on Temurin, log the distribution, and print a recommended Docker base image for the detected JDK version.

### Level 1 — Basic

```java
// TemurinCheck.java
public class TemurinCheck {
    public static void main(String[] args) {
        String vendor  = System.getProperty("java.vendor", "");
        String runtime = System.getProperty("java.runtime.name", "");
        boolean isTemurin = vendor.toLowerCase().contains("eclipse")
                         || vendor.toLowerCase().contains("adoptium");

        System.out.println("Vendor  : " + vendor);
        System.out.println("Runtime : " + runtime);
        System.out.println("Temurin : " + isTemurin);
        if (!isTemurin) {
            System.out.println("Tip: consider switching to Eclipse Temurin for a free, TCK-certified JDK.");
        }
    }
}
```

**How to run:** `java TemurinCheck.java`

On Eclipse Temurin, `java.vendor` is `"Eclipse Adoptium"`. The `runtime` includes `"OpenJDK Runtime Environment Temurin-21.x.x"`.

### Level 2 — Intermediate

Same Temurin check extended to recommend the correct `eclipse-temurin` Docker image tag for the detected JDK version — useful in CI pipelines that need to match the local dev JDK to the production container image.

```java
// TemurinDockerTag.java
public class TemurinDockerTag {

    static String dockerTag(int feature, boolean jreOnly) {
        String suffix = jreOnly ? "-jre" : "";
        return "eclipse-temurin:" + feature + suffix;
    }

    static String alpineTag(int feature) {
        return "eclipse-temurin:" + feature + "-jdk-alpine";
    }

    public static void main(String[] args) {
        int feature    = Runtime.version().feature();
        String vendor  = System.getProperty("java.vendor", "");
        String arch    = System.getProperty("os.arch", "");
        boolean isLts  = feature == 8 || feature == 11 || feature == 17 || feature == 21 || feature == 25;

        System.out.println("=== Temurin Docker Image Advisor ===");
        System.out.printf("Running: Java %d on %s (%s)%n", feature, vendor, arch);
        System.out.printf("LTS release: %s%n%n", isLts ? "YES" : "NO — consider using LTS for production");

        System.out.println("Recommended Docker base images:");
        System.out.printf("  Spring Boot app  : FROM %-35s  (full JRE)%n", dockerTag(feature, true));
        System.out.printf("  Minimal container: FROM %-35s  (Alpine JDK)%n", alpineTag(feature));
        System.out.printf("  Build stage (CI) : FROM %-35s  (full JDK)%n", dockerTag(feature, false));

        if (!isLts) {
            System.out.println("\nWARNING: Java " + feature + " is not an LTS release.");
            System.out.println("  Temurin LTS options: 8, 11, 17, 21, 25");
        }
    }
}
```

**How to run:** `java TemurinDockerTag.java`

Using `eclipse-temurin:21-jre` in production reduces image size (no compiler, no javadoc, no jshell) from ~400 MB to ~170 MB. Alpine variants are even smaller (~80 MB) but lack `glibc` — watch for native library issues.

### Level 3 — Advanced

Same advisor grown to a full Temurin environment audit: detect distribution, recommend Docker image, check if architecture-specific images are available, and verify that the current JDK is suitable for containerised Spring Boot deployment.

```java
// TemurinAudit.java
import java.util.*;

public class TemurinAudit {

    record DockerRecommendation(String purpose, String image, String notes) {}

    static String vendor() { return System.getProperty("java.vendor", "unknown"); }
    static int    feature(){ return Runtime.version().feature(); }
    static String arch()   { return System.getProperty("os.arch", "unknown"); }
    static String os()     { return System.getProperty("os.name", "unknown"); }

    // Supported Temurin platforms (as of 2025)
    static final Set<String> SUPPORTED_ARCHES = Set.of(
        "amd64", "x86_64", "aarch64", "arm64", "s390x", "ppc64le"
    );

    // LTS versions Temurin publishes
    static final Set<Integer> LTS_VERSIONS = Set.of(8, 11, 17, 21, 25);

    static String normaliseArch(String arch) {
        return switch (arch.toLowerCase()) {
            case "x86_64", "amd64"       -> "amd64";
            case "aarch64", "arm64"      -> "arm64";
            case "s390x"                 -> "s390x";
            case "ppc64le"               -> "ppc64le";
            default                      -> arch;
        };
    }

    static List<DockerRecommendation> recommendations(int feat, String archNorm) {
        boolean supArch = SUPPORTED_ARCHES.contains(archNorm);
        String archSuffix = supArch && !archNorm.equals("amd64") ? "/" + archNorm : "";
        return List.of(
            new DockerRecommendation(
                "Spring Boot / Jakarta EE",
                "eclipse-temurin:" + feat + "-jre" + archSuffix,
                "JRE-only; ~170 MB; no javac"),
            new DockerRecommendation(
                "Multi-stage build (builder)",
                "eclipse-temurin:" + feat + "-jdk" + archSuffix,
                "Full JDK; use in FROM ... AS build stage"),
            new DockerRecommendation(
                "Minimal / Alpine",
                "eclipse-temurin:" + feat + "-jdk-alpine",
                "~80 MB; musl libc; verify native libs work"),
            new DockerRecommendation(
                "Debug / observability",
                "eclipse-temurin:" + feat + "-jdk" + archSuffix,
                "Includes jcmd, jstack, jmap, jfr for JFR profiling")
        );
    }

    public static void main(String[] args) {
        int  feat     = feature();
        String archN  = normaliseArch(arch());
        boolean isLts = LTS_VERSIONS.contains(feat);
        boolean isTem  = vendor().toLowerCase().contains("eclipse") || vendor().toLowerCase().contains("adoptium");

        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║        Temurin Deployment Audit          ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        System.out.println("[ Runtime ]");
        System.out.printf("  JDK     : Java %d (%s)%n", feat, vendor());
        System.out.printf("  Arch    : %s (normalised: %s)%n", arch(), archN);
        System.out.printf("  OS      : %s%n", os());
        System.out.printf("  Temurin : %s%n", isTem ? "YES" : "NO — " + vendor());
        System.out.printf("  LTS     : %s%n%n", isLts ? "YES" : "NO — production risk");

        if (!isLts) {
            System.out.printf("  [WARN] Java %d is NOT an LTS release. Use 8/11/17/21/25 in production.%n%n", feat);
        }
        if (!SUPPORTED_ARCHES.contains(archN)) {
            System.out.printf("  [WARN] arch '%s' may not have a native Temurin image — verify.%n%n", archN);
        }

        System.out.println("[ Docker Image Recommendations ]");
        System.out.printf("  %-32s  %-48s  %s%n", "Purpose", "Image", "Notes");
        System.out.println("  " + "-".repeat(110));
        for (var r : recommendations(feat, archN)) {
            System.out.printf("  %-32s  %-48s  %s%n", r.purpose(), r.image(), r.notes());
        }

        System.out.println("\n[ Production Readiness ]");
        System.out.println("  Free for production     : YES (GPL-2.0 + CPE)");
        System.out.println("  TCK certified           : YES");
        System.out.println("  AQAvit tested           : YES");
        System.out.println("  JFR available (Java 11+): " + (feat >= 11 ? "YES" : "NO"));
        System.out.println("  Virtual threads (Java 21+): " + (feat >= 21 ? "YES" : "NO"));
    }
}
```

**How to run:** `java TemurinAudit.java`

The `record DockerRecommendation` (Java 16+) holds structured output cleanly. `normaliseArch` maps OS-reported architecture strings to Docker's canonical naming (`aarch64 → arm64`, `x86_64 → amd64`).

## 6. Walkthrough

Execution in `TemurinAudit.main`:

1. **`feature()` + `arch()`** — `Runtime.version().feature()` returns the major version integer (e.g. `21`). `System.getProperty("os.arch")` returns the JVM-reported CPU architecture string — this varies: macOS Apple Silicon reports `"aarch64"`, older macOS reports `"x86_64"`, some JVMs report `"amd64"` for x86-64. `normaliseArch` maps to a consistent string.

2. **Temurin detection** — `vendor()` is `"Eclipse Adoptium"` on Temurin. The second `contains("adoptium")` check handles older Temurin builds that reported slightly different strings.

3. **LTS check** — `LTS_VERSIONS.contains(feat)` uses an immutable `Set` for O(1) lookup. Non-LTS Java versions (18, 19, 20, 22, 23…) go end-of-life in 6 months — flagging this prevents silent production upgrades to unsupported versions.

4. **`recommendations(feat, archN)`** returns a `List` of `DockerRecommendation` records. The `archSuffix` adds `/arm64` for ARM builds: Docker Hub multi-arch images use `eclipse-temurin:21-jre/arm64` syntax for explicit arch targeting.

5. **Production readiness table** — a simple checklist. `feat >= 11` gates JFR (added to OpenJDK in Java 11); `feat >= 21` gates virtual threads (JEP 444). Both are architecture-independent Temurin features.

Docker multi-stage build pattern (what the recommendations enable):
```
# Build stage — needs javac
FROM eclipse-temurin:21-jdk AS builder
COPY . /app
RUN cd /app && ./mvnw package -DskipTests

# Runtime stage — JRE only, smaller
FROM eclipse-temurin:21-jre
COPY --from=builder /app/target/app.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

This produces a final image of ~170 MB instead of ~500 MB (full JDK).

## 7. Gotchas & takeaways

> **Alpine (`eclipse-temurin:*-alpine`) uses musl libc, not glibc.** Some native libraries (certain JDBC drivers with native components, some cryptographic providers) require glibc and silently fail or crash on Alpine. Test your full application on the Alpine image before using it in production.

> **`adoptopenjdk:` Docker images are deprecated.** The old AdoptOpenJDK images (`adoptopenjdk:11-jdk-hotspot`) still exist but receive no updates. Migrate to `eclipse-temurin:11` which is maintained.

- Eclipse Temurin = the reference free, TCK-certified OpenJDK distribution for production use.
- Docker: use `eclipse-temurin:21-jre` for runtime, `eclipse-temurin:21-jdk` for builds, `-alpine` for smallest images.
- Multi-arch: Temurin publishes binaries for x64, ARM64, s390x, ppc64le — the same tag works on all architectures.
- LTS releases (8, 11, 17, 21, 25) are the right choice for long-lived services.
- JFR (Java 11+) and virtual threads (Java 21+) are available on Temurin — no Oracle JDK needed.
- AQAvit testing is Temurin's extra quality bar beyond the standard TCK — it covers security, load, and extended functional tests.
