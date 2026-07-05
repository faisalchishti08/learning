---
card: java
gi: 16
slug: long-term-support-lts-releases
title: Long-Term Support (LTS) releases
---

## 1. What it is

A **Long-Term Support (LTS) release** of Java is a feature release that vendors commit to patching for multiple years — covering security vulnerabilities, critical bug fixes, and performance improvements — long after the 6-month active support window closes. LTS releases exist because enterprises cannot upgrade major Java versions every 6 months; they need a stable platform for 2–5 year product lifecycles.

Current LTS versions: **Java 8, 11, 17, 21, 25** (and future even-major releases). Starting with Java 17, Oracle and most major vendors publish LTS releases on a 2-year cadence (previously 3 years).

## 2. Why & when

The six-month cadence produces non-LTS releases that enterprises cannot safely adopt: upgrading a production platform every 6 months is operationally costly and risky. LTS solves this by providing a stable foundation:

- Java 17 (September 2021) — most widely deployed LTS after Java 8.
- Java 21 (September 2023) — brings virtual threads (Project Loom), sequenced collections, pattern matching.
- Java 25 (September 2025) — expected to include Valhalla value types and further Loom improvements.

Use LTS when:
- Running services in production with long deployment windows.
- Distributing libraries or frameworks that users run for years.
- Your organisation's change-control process makes frequent upgrades impractical.
- You need a predictable security-patch target for your CI/CD pipeline.

## 3. Core concept

LTS is a **vendor promise**, not a language feature. OpenJDK itself does not define LTS — each distribution decides how long it supports each version:

| Version | Oracle JDK | Temurin (community) | Amazon Corretto | Azul Zulu |
|---|---|---|---|---|
| Java 8 | paid (OTN) | until 2026 | until 2026 | until 2030 |
| Java 11 | paid (OTN) | until 2027 | until 2027 | until 2032 |
| Java 17 | free (NFTC) until ~2029 | until 2027 | until 2029 | until 2032 |
| Java 21 | free (NFTC) until ~2031 | until 2029 | until 2030 | until 2034 |

**Patch releases** for LTS versions follow a quarterly schedule (typically January, April, July, October). The version string tells you exactly which patch you're on: `21.0.3+9` means Java 21, minor 0, patch 3, build 9.

**Upgrade from LTS to LTS** is the recommended path: go from 17 → 21, not 17 → 18 → 19 → 20 → 21. Each LTS-to-LTS gap is small enough (2 years of changes) to be manageable.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LTS patch support windows compared to non-LTS short windows">
  <!-- Timeline spine -->
  <line x1="30" y1="90" x2="670" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Java 17 LTS support bar -->
  <rect x="30" y="70" width="240" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="86"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 17 LTS (2021–2027+)</text>
  <text x="150" y="101" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">quarterly patches · free (NFTC)</text>

  <!-- Non-LTS short windows -->
  <rect x="280" y="78" width="55" height="24" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="307" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">18 (6mo)</text>

  <rect x="345" y="78" width="55" height="24" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="372" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">19 (6mo)</text>

  <rect x="410" y="78" width="55" height="24" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="437" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">20 (6mo)</text>

  <!-- Java 21 LTS support bar -->
  <rect x="475" y="70" width="200" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="575" y="86"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 21 LTS (2023–2029+)</text>
  <text x="575" y="101" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">quarterly patches · free (NFTC)</text>

  <!-- Labels -->
  <text x="150" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2021       2022       2023</text>
  <text x="575" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2023       2024 ...  2029</text>
  <text x="372" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">18/19/20: 6-month EOL</text>

  <!-- Upgrade arrow -->
  <line x1="270" y1="90" x2="473" y2="90" stroke="#6db33f" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="372" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">recommended: upgrade LTS → LTS</text>
</svg>

LTS releases get multi-year patch bars. Non-LTS releases get a 6-month gap. The recommended path skips non-LTS entirely.

## 5. Runnable example

Scenario: a program that queries the running JDK's patch level and reports whether it's behind on security patches.

### Level 1 — Basic

```java
// LtsPatchLevel.java
public class LtsPatchLevel {
    public static void main(String[] args) {
        Runtime.Version v = Runtime.version();
        System.out.println("Version string : " + v);
        System.out.println("Feature (major): " + v.feature());
        System.out.println("Interim (minor): " + v.interim());
        System.out.println("Update (patch) : " + v.update());
        System.out.println("Patch (build)  : " + v.patch());
        System.out.println();
        System.out.println("LTS?           : " + isLts(v.feature()));
    }

    static boolean isLts(int feature) {
        return feature == 8 || feature == 11 || feature == 17 || feature == 21 || feature == 25;
    }
}
```

**How to run:** `java LtsPatchLevel.java`

`Runtime.Version` fields: `feature` = major (21), `interim` = minor (usually 0 since Java 9), `update` = patch (e.g. 3 for 21.0.3), `patch` = emergency patch (usually 0). The quarterly security update increments `update`.

### Level 2 — Intermediate

Same patch-level check extended to compare against a known minimum security patch level (simulating a CI policy that rejects out-of-date JDKs).

```java
// LtsPatchPolicy.java
import java.util.*;

public class LtsPatchPolicy {

    // Minimum update numbers for each LTS version (approximate — update quarterly)
    static final Map<Integer, Integer> MIN_PATCH = Map.of(
        8,  401,  // Java 8u401 (Jan 2024 CPU)
        11, 22,   // Java 11.0.22 (Jan 2024 CPU)
        17, 11,   // Java 17.0.11 (Apr 2024 CPU)
        21, 3     // Java 21.0.3 (Apr 2024 CPU)
    );

    public static void main(String[] args) {
        Runtime.Version v = Runtime.version();
        int feature = v.feature();
        int update  = feature == 8
            ? parseJava8Update(v.toString())
            : v.update();

        System.out.println("=== JDK Patch Policy Check ===");
        System.out.printf("Running: Java %d (update %d)%n", feature, update);
        System.out.printf("LTS    : %s%n", isLts(feature) ? "YES" : "NO — consider LTS");

        if (!isLts(feature)) {
            System.out.println("Non-LTS: no quarterly patches. Upgrade to LTS recommended.");
            return;
        }

        Integer minPatch = MIN_PATCH.get(feature);
        if (minPatch == null) {
            System.out.println("No minimum patch policy defined for Java " + feature + ". Update the policy table.");
            return;
        }

        if (update >= minPatch) {
            System.out.printf("PASS: update %d >= minimum %d%n", update, minPatch);
        } else {
            System.out.printf("FAIL: update %d < minimum %d. Apply latest CPU (Critical Patch Update).%n",
                update, minPatch);
        }
    }

    static boolean isLts(int f) { return f == 8 || f == 11 || f == 17 || f == 21 || f == 25; }

    static int parseJava8Update(String version) {
        // Java 8 format: "1.8.0_401" → update = 401
        try {
            String[] parts = version.split("[._]");
            return parts.length >= 4 ? Integer.parseInt(parts[3]) : 0;
        } catch (NumberFormatException e) { return 0; }
    }
}
```

**How to run:** `java LtsPatchPolicy.java`

This is the kind of gate a security team embeds in their CI pipeline to ensure no service ships with an outdated JDK patch level.

### Level 3 — Advanced

Same policy check grown to a full LTS version management report: all installed JVMs on the system (probed via `PATH`), patch level assessment for each, and a recommendation matrix.

```java
// LtsVersionReport.java
import java.util.*;
import java.io.*;

public class LtsVersionReport {

    record JvmInfo(String path, int feature, int update, boolean lts, String raw) {}

    // Approximate latest quarterly update numbers (Jan 2025 snapshot)
    static final Map<Integer, Integer> LATEST_PATCH = new LinkedHashMap<>(Map.of(
        8, 432, 11, 26, 17, 13, 21, 5, 25, 1
    ));

    public static void main(String[] args) throws Exception {
        System.out.println("╔════════════════════════════════════════════╗");
        System.out.println("║         LTS Version Management Report      ║");
        System.out.println("╚════════════════════════════════════════════╝\n");

        // Probe the currently running JVM
        Runtime.Version v = Runtime.version();
        List<JvmInfo> jvms = new ArrayList<>();
        jvms.add(buildInfo(System.getProperty("java.home"), v));

        // Also try to find other java executables on PATH
        for (String path : System.getenv("PATH").split(File.pathSeparator)) {
            File javaExe = new File(path, "java");
            if (javaExe.exists() && !javaExe.getAbsolutePath().equals(
                    new File(System.getProperty("java.home"), "bin/java").getAbsolutePath())) {
                JvmInfo info = probeExternalJvm(javaExe.getAbsolutePath());
                if (info != null && jvms.stream().noneMatch(j -> j.feature() == info.feature())) {
                    jvms.add(info);
                }
            }
        }

        System.out.printf("%-6s  %-5s  %-7s  %-5s  %-8s  %-8s  %s%n",
            "Feature", "LTS?", "Update", "Latest", "Patch?", "Status", "Path");
        System.out.println("-".repeat(90));

        for (JvmInfo jvm : jvms) {
            Integer latest = LATEST_PATCH.get(jvm.feature());
            boolean upToDate = latest != null && jvm.update() >= latest;
            String patchStr = latest == null ? "unknown" : (upToDate ? "UP TO DATE" : "BEHIND");
            String status = !jvm.lts() ? "non-LTS" : (upToDate ? "OK" : "UPDATE");

            System.out.printf("%-6d  %-5s  %-7d  %-5s  %-8s  %-8s  %s%n",
                jvm.feature(), jvm.lts() ? "YES" : "no",
                jvm.update(), latest != null ? String.valueOf(latest) : "?",
                patchStr, status, jvm.path());
        }

        System.out.println("\n[ Recommendations ]");
        for (JvmInfo jvm : jvms) {
            if (!jvm.lts()) {
                System.out.println("  Java " + jvm.feature() + ": migrate to LTS (21 or 25)");
            } else {
                Integer latest = LATEST_PATCH.get(jvm.feature());
                if (latest != null && jvm.update() < latest) {
                    System.out.println("  Java " + jvm.feature() + ": apply patch update " + latest);
                } else {
                    System.out.println("  Java " + jvm.feature() + ": up to date");
                }
            }
        }
    }

    static JvmInfo buildInfo(String home, Runtime.Version v) {
        int update = v.feature() == 8 ? parseJava8Update(v.toString()) : v.update();
        return new JvmInfo(home, v.feature(), update, isLts(v.feature()), v.toString());
    }

    static JvmInfo probeExternalJvm(String path) {
        try {
            ProcessBuilder pb = new ProcessBuilder(path, "-version");
            pb.redirectErrorStream(true);
            Process p = pb.start();
            String output = new String(p.getInputStream().readAllBytes());
            p.waitFor();
            // parse "openjdk version \"21.0.3\" ..." or "java version \"1.8.0_401\""
            java.util.regex.Matcher m = java.util.regex.Pattern
                .compile("\"([0-9._]+)\"").matcher(output);
            if (m.find()) {
                String verStr = m.group(1);
                Runtime.Version rv = Runtime.Version.parse(verStr.startsWith("1.") ?
                    verStr.substring(2) : verStr);
                int update = rv.feature() == 8 ? parseJava8Update(verStr) : rv.update();
                return new JvmInfo(path, rv.feature(), update, isLts(rv.feature()), verStr);
            }
        } catch (Exception e) { /* skip unreachable JVMs */ }
        return null;
    }

    static boolean isLts(int f) { return f == 8 || f == 11 || f == 17 || f == 21 || f == 25; }

    static int parseJava8Update(String v) {
        try {
            String[] p = v.split("[._]");
            return p.length >= 4 ? Integer.parseInt(p[3]) : 0;
        } catch (NumberFormatException e) { return 0; }
    }
}
```

**How to run:** `java LtsVersionReport.java`

This program scans `PATH` for additional `java` executables, probes their version, and reports a full patch-status table — useful for developers managing multiple JDK installations via `jenv`, `sdkman`, or Homebrew.

## 6. Walkthrough

Execution in `LtsVersionReport.main`:

1. **Current JVM** — `Runtime.version()` returns the running JVM's version. `buildInfo` extracts `feature` (major) and `update` (patch). Java 8 is special: its version format is `"1.8.0_432"` where `_432` is the update number — `parseJava8Update` handles this.

2. **PATH scan** — `System.getenv("PATH").split(File.pathSeparator)` splits on `:` (Unix) or `;` (Windows). For each directory, it checks if `java` executable exists. If found and not the current JVM, `probeExternalJvm` runs `java -version` in a subprocess.

3. **`probeExternalJvm`** — `ProcessBuilder("java", "-version")` runs the external JVM and captures stderr+stdout (redirected together). The regex `"([0-9._]+)"` extracts the version string from the `java version "21.0.3"` output. `Runtime.Version.parse()` parses it — handles both `"1.8.0_432"` (Java 8 style) and `"21.0.3"` (modern style) after stripping the `1.` prefix.

4. **Patch comparison** — `LATEST_PATCH` maps known quarterly CPU (Critical Patch Update) numbers. `update >= latest` means the JVM has received the latest security patches. This is a snapshot; in production tooling, you'd fetch the latest patch numbers from an API or vulnerability database.

5. **Recommendations** — a final pass over the discovered JVMs emits specific upgrade actions.

State flow:
```
Runtime.version()  → current JVM version (in memory, instant)
PATH.split(":") → list of directories
  → File("java").exists() → check filesystem
  → ProcessBuilder("java -version") → subprocess → stdout text
  → regex match → version string
  → Version.parse() → structured object
  → compare update vs LATEST_PATCH[feature]
  → print table + recommendations
```

## 7. Gotchas & takeaways

> **"LTS" is a vendor commitment, not a JVM flag.** The JVM itself does not know or care whether it's an LTS release. LTS means a vendor promises quarterly patches. If your vendor stops publishing patches for your LTS version, you are effectively on a non-LTS regardless of the version number.

> **Java 8 patch versioning uses `1.8.0_NNN`, not `8.0.NNN`.** Code that calls `v.update()` on a Java 8 runtime returns 0 because `update` is the second component of the modern `feature.interim.update.patch` scheme, not the legacy `_` suffix. Always special-case Java 8.

- LTS versions: 8, 11, 17, 21, 25 (and future even-major numbers on 2-year cadence from Java 17+).
- LTS patch releases follow a quarterly schedule — apply them within 30 days of release for security compliance.
- Quarterly CPU (Critical Patch Update) increments the `update` component of the version: `21.0.3 → 21.0.4`.
- `Runtime.version().update()` gives the patch number on Java 9+. Java 8 needs special string parsing.
- Upgrade path: always LTS → LTS (skip the intermediate non-LTS releases).
- Check vendor-specific EOL dates — community (Temurin) LTS support is shorter than Oracle paid support.
