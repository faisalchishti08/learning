---
card: spring-framework
gi: 9
slug: release-versions-support-timelines
title: Release versions & support timelines
---

## 1. What it is

Spring Framework and Spring Boot follow predictable versioning and support lifecycles managed by the Spring team (VMware/Broadcom). Understanding the release cadence prevents you from shipping on an unsupported version or being surprised by an EOL.

**Spring Framework release lifecycle:**

| Version | GA date | OSS Support EOL | Commercial support |
|---|---|---|---|
| 5.3.x | Oct 2020 | Dec 2024 | Nov 2027 (VMware) |
| 6.0.x | Nov 2022 | Aug 2024 | Dec 2026 |
| 6.1.x | Nov 2023 | Feb 2025 | Dec 2026 |
| 6.2.x | Nov 2024 | Late 2025 | Dec 2027 (projected) |

**Spring Boot release lifecycle (tracks Framework):**

| Version | GA date | OSS Support EOL | Built on Framework |
|---|---|---|---|
| 2.7.x | May 2022 | Nov 2023 | Spring 5.3.x |
| 3.0.x | Nov 2022 | May 2024 | Spring 6.0.x |
| 3.1.x | May 2023 | Nov 2024 | Spring 6.0.x |
| 3.2.x | Nov 2023 | Nov 2025 | Spring 6.1.x |
| 3.3.x | May 2024 | Nov 2025 | Spring 6.1.x |
| 3.4.x | Nov 2024 | Nov 2026 | Spring 6.2.x |

OSS support EOL = no more free patch releases, no security fixes to the open-source branch.

## 2. Why & when

Running on an EOL Spring version is a security and compliance risk. Spring regularly publishes CVE fixes (e.g., Spring4Shell / CVE-2022-22965 affected Spring MVC < 5.3.18). After EOL, those fixes only reach commercial subscribers.

The cadence also tells you how often to plan upgrades:
- Spring Boot releases a new minor every **6 months** (May and November).
- Each minor is supported for **12 months** of OSS support.
- LTS-equivalent versions (those aligned with a JDK LTS) tend to receive commercial support extensions.
- The current "safe" target for new projects is always the latest GA minor of Spring Boot 3.x.

**Semantic versioning in Spring:**
- `3.2.4` — `MAJOR.MINOR.PATCH`
- PATCH releases: backwards-compatible bug and security fixes. Upgrade freely.
- MINOR releases: may contain deprecations and new features. Smooth upgrades expected within the same major.
- MAJOR releases (2→3): breaking changes. Requires migration guide.

## 3. Core concept

Spring follows a **train release model** where Spring Framework and Spring Boot GA dates are coordinated with the JDK LTS calendar:

```
JDK 17 LTS (Sep 2021)
   → Spring Framework 6.0 (Nov 2022) — JDK 17 baseline
   → Spring Boot 3.0 (Nov 2022)

JDK 21 LTS (Sep 2023)
   → Spring Framework 6.1 (Nov 2023) — JDK 21 improvements
   → Spring Boot 3.2 (Nov 2023)

JDK 25 LTS (2025, projected)
   → Spring Framework 7.x (projected ~2025–2026)
```

Each Spring project (Security, Data, Batch, Cloud) has its own version number but aligns with the Framework/Boot generation. Spring Boot's BOM (Bill of Materials) locks compatible versions of all ecosystem projects, so you only manage one version number: `spring-boot.version`.

**Milestone releases:**

| Suffix | Meaning | Use in production? |
|---|---|---|
| `M1`, `M2` … | Milestone — feature-complete, not final | No |
| `RC1`, `RC2` … | Release Candidate — final API, bug fixes only | No |
| (no suffix) | General Availability — stable | Yes |
| `SNAPSHOT` | Daily development build | Never |

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot version timeline showing support windows for 2.7, 3.0, 3.1, 3.2, 3.3 on a horizontal axis">
  <defs>
    <marker id="ta" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Axis -->
  <line x1="30" y1="200" x2="670" y2="200" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ta)"/>

  <!-- Year labels -->
  <text x="80"  y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2022</text>
  <text x="220" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2023</text>
  <text x="360" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2024</text>
  <text x="500" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2025</text>
  <text x="640" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2026</text>

  <!-- Boot 2.7 -->
  <rect x="30" y="10" width="260" height="28" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="160" y="29" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Boot 2.7 (EOL Nov 2023)</text>

  <!-- Boot 3.0 -->
  <rect x="75" y="48" width="205" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="177" y="67" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Boot 3.0 (EOL May 2024)</text>

  <!-- Boot 3.1 -->
  <rect x="145" y="86" width="210" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Boot 3.1 (EOL Nov 2024)</text>

  <!-- Boot 3.2 (current recommended) -->
  <rect x="215" y="124" width="280" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="355" y="143" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Boot 3.2 (EOL Nov 2025) ← recommended</text>

  <!-- Boot 3.3 -->
  <rect x="290" y="162" width="280" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="181" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Boot 3.3 (EOL Nov 2025)</text>

  <!-- Today marker -->
  <line x1="360" y1="5" x2="360" y2="200" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="5,4"/>
  <text x="360" y="4" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">~now (mid-2025)</text>
</svg>

Each bar is one support window. Versions left of "now" with ended bars are EOL; upgrade.

## 5. Runnable example

A version-checker utility that determines if a given Spring Boot version is current, upcoming EOL, or already expired.

### Level 1 — Basic

Classify a single version against a hardcoded policy.

```java
// VersionCheckDemo.java — run with: java VersionCheckDemo.java

import java.time.LocalDate;
import java.util.*;

public class VersionCheckDemo {

    record VersionPolicy(String version, LocalDate gaDate, LocalDate eolDate) {
        boolean isSupported(LocalDate today) { return !today.isAfter(eolDate); }
        boolean isNearEol(LocalDate today, int warningDays) {
            return isSupported(today) && today.plusDays(warningDays).isAfter(eolDate);
        }
    }

    static final List<VersionPolicy> BOOT_POLICIES = List.of(
        new VersionPolicy("2.7.x", LocalDate.of(2022, 5, 19),  LocalDate.of(2023, 11, 18)),
        new VersionPolicy("3.0.x", LocalDate.of(2022, 11, 24), LocalDate.of(2024, 5, 24)),
        new VersionPolicy("3.1.x", LocalDate.of(2023, 5, 18),  LocalDate.of(2024, 11, 21)),
        new VersionPolicy("3.2.x", LocalDate.of(2023, 11, 23), LocalDate.of(2025, 11, 21)),
        new VersionPolicy("3.3.x", LocalDate.of(2024, 5, 23),  LocalDate.of(2025, 11, 21)),
        new VersionPolicy("3.4.x", LocalDate.of(2024, 11, 21), LocalDate.of(2026, 11, 20))
    );

    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 6, 29);  // today's date
        int warningDays = 90;

        System.out.println("=== Spring Boot Version Support Status ===");
        System.out.printf("Checked on: %s%n%n", today);
        System.out.printf("%-10s %-12s %-12s %-20s%n", "Version", "GA Date", "EOL Date", "Status");
        System.out.println("-".repeat(58));

        for (VersionPolicy p : BOOT_POLICIES) {
            String status;
            if (!p.isSupported(today)) {
                status = "EOL — upgrade now";
            } else if (p.isNearEol(today, warningDays)) {
                long daysLeft = today.until(p.eolDate()).getDays();
                status = "EOL in " + daysLeft + " days — plan upgrade";
            } else {
                status = "Supported";
            }
            System.out.printf("%-10s %-12s %-12s %-20s%n",
                p.version(), p.gaDate(), p.eolDate(), status);
        }
    }
}
```

How to run: `java VersionCheckDemo.java`

The checker shows each version's status relative to today's date. In a CI pipeline this could fail the build if the project's `spring-boot.version` resolves to an EOL entry.

### Level 2 — Intermediate

Add semantic version parsing and upgrade path recommendation.

```java
// VersionCheckV2.java — run with: java VersionCheckV2.java
import java.time.LocalDate;
import java.util.*;

public class VersionCheckV2 {

    record SemVer(int major, int minor, int patch) implements Comparable<SemVer> {
        static SemVer parse(String v) {
            String[] p = v.split("\\.");
            return new SemVer(Integer.parseInt(p[0]), Integer.parseInt(p[1]),
                p.length > 2 ? Integer.parseInt(p[2]) : 0);
        }
        @Override public int compareTo(SemVer o) {
            int c = Integer.compare(major, o.major);
            if (c != 0) return c;
            c = Integer.compare(minor, o.minor);
            return c != 0 ? c : Integer.compare(patch, o.patch);
        }
        @Override public String toString() { return major + "." + minor + "." + patch; }
    }

    record VersionInfo(SemVer version, LocalDate eolDate, boolean isCurrent) {}

    static final List<VersionInfo> VERSIONS = List.of(
        new VersionInfo(SemVer.parse("3.0.13"), LocalDate.of(2024, 5, 24),  false),
        new VersionInfo(SemVer.parse("3.1.12"), LocalDate.of(2024, 11, 21), false),
        new VersionInfo(SemVer.parse("3.2.7"),  LocalDate.of(2025, 11, 21), true),
        new VersionInfo(SemVer.parse("3.3.2"),  LocalDate.of(2025, 11, 21), true),
        new VersionInfo(SemVer.parse("3.4.1"),  LocalDate.of(2026, 11, 20), true)
    );

    static Optional<VersionInfo> recommend(SemVer current) {
        return VERSIONS.stream()
            .filter(VersionInfo::isCurrent)
            .max(Comparator.comparing(VersionInfo::version));
    }

    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 6, 29);

        List<SemVer> projectVersions = List.of(
            SemVer.parse("2.7.18"),
            SemVer.parse("3.1.8"),
            SemVer.parse("3.2.5"),
            SemVer.parse("3.4.1")
        );

        System.out.println("=== Upgrade Path Recommendations ===\n");
        for (SemVer pv : projectVersions) {
            Optional<VersionInfo> match = VERSIONS.stream()
                .filter(v -> v.version().major() == pv.major() && v.version().minor() == pv.minor())
                .findFirst();

            boolean eol = match.map(v -> today.isAfter(v.eolDate())).orElse(true);
            VersionInfo recommended = recommend(pv).orElseThrow();

            System.out.printf("Project uses: %s%n", pv);
            if (eol) {
                System.out.printf("  Status:      EOL%n");
                if (pv.major() < 3)
                    System.out.printf("  Action:      Major upgrade required: 2.x → 3.x (Jakarta EE migration)%n");
                else
                    System.out.printf("  Action:      Patch/minor upgrade: bump to %s%n", recommended.version());
            } else {
                long months = today.until(match.get().eolDate()).getMonths();
                System.out.printf("  Status:      Supported (%d months remaining)%n", months);
                if (!pv.equals(recommended.version()))
                    System.out.printf("  Recommended: upgrade patch to %s%n", recommended.version());
            }
            System.out.println();
        }
    }
}
```

How to run: `java VersionCheckV2.java`

Patch upgrades within a supported minor are free (backwards compatible). Minor upgrades within Boot 3.x require checking the migration notes. Major upgrades (2→3) require the Jakarta EE migration.

### Level 3 — Advanced

Full CI gate: parse `pom.xml` (simulated), check the spring-boot version, flag EOL, recommend upgrade, fail the build with exit code 1.

```java
// VersionCheckV3.java — run with: java VersionCheckV3.java
// Simulates a CI build gate that reads pom.xml and fails on EOL Spring Boot versions.

import java.time.*;
import java.util.*;

public class VersionCheckV3 {

    record Policy(String majorMinor, LocalDate eolDate, String notes) {}
    record PomDependency(String groupId, String artifactId, String version) {}

    static final List<Policy> POLICIES = List.of(
        new Policy("2.7", LocalDate.of(2023, 11, 18), "EOL — migrate to Boot 3.x"),
        new Policy("3.0", LocalDate.of(2024,  5, 24), "EOL — migrate to Boot 3.2+"),
        new Policy("3.1", LocalDate.of(2024, 11, 21), "EOL — migrate to Boot 3.2+"),
        new Policy("3.2", LocalDate.of(2025, 11, 21), "Supported — current LTS-equivalent"),
        new Policy("3.3", LocalDate.of(2025, 11, 21), "Supported"),
        new Policy("3.4", LocalDate.of(2026, 11, 20), "Supported — latest GA")
    );

    // Simulated pom.xml <properties> section
    static final Map<String, String> POM_PROPERTIES = Map.of(
        "spring-boot.version",         "3.1.8",      // stale — EOL
        "spring-security.version",     "6.1.6",
        "spring-data-bom.version",     "2023.0.6",
        "java.version",                "17",
        "project.build.sourceEncoding","UTF-8"
    );

    // Simulated pom.xml dependencies
    static final List<PomDependency> POM_DEPS = List.of(
        new PomDependency("org.springframework.boot", "spring-boot-starter-web",  "${spring-boot.version}"),
        new PomDependency("org.springframework.boot", "spring-boot-starter-data-jpa", "${spring-boot.version}"),
        new PomDependency("org.springframework.security", "spring-security-core", "${spring-security.version}")
    );

    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 6, 29);
        boolean buildFail = false;

        System.out.println("=== Spring Dependency Version Gate ===");
        System.out.println("  Build date: " + today);

        // Resolve ${property} references
        String bootVersion = POM_PROPERTIES.get("spring-boot.version");
        System.out.println("  spring-boot.version = " + bootVersion);

        // Determine major.minor
        String[] parts = bootVersion.split("\\.");
        String majorMinor = parts[0] + "." + parts[1];

        Optional<Policy> policy = POLICIES.stream()
            .filter(p -> p.majorMinor().equals(majorMinor))
            .findFirst();

        if (policy.isEmpty()) {
            System.out.println("  WARN: Unknown Boot version " + bootVersion + " — no policy found");
        } else {
            Policy p = policy.get();
            boolean eol = today.isAfter(p.eolDate());
            long daysOverdue = eol ? p.eolDate().until(today).getDays() : 0;
            long daysRemaining = eol ? 0 : today.until(p.eolDate()).getDays();

            System.out.println("  EOL date: " + p.eolDate());
            System.out.println("  Notes:    " + p.notes());

            if (eol) {
                System.out.println("\n  FAIL: Spring Boot " + bootVersion + " reached EOL "
                    + daysOverdue + " days ago.");
                System.out.println("  FAIL: Security patches are no longer published to the OSS branch.");
                System.out.println("  ACTION: Upgrade spring-boot.version to 3.4.x in pom.xml");
                buildFail = true;
            } else if (daysRemaining < 90) {
                System.out.println("  WARN: EOL in " + daysRemaining + " days — plan upgrade within this sprint.");
            } else {
                System.out.println("  OK: " + daysRemaining + " days of OSS support remaining.");
            }
        }

        System.out.println("\n=== Dependency inventory ===");
        POM_DEPS.forEach(d -> System.out.printf("  %-45s %s%n",
            d.groupId() + ":" + d.artifactId(),
            d.version().replace("${spring-boot.version}", bootVersion)));

        System.out.println("\n=== Result ===");
        if (buildFail) {
            System.out.println("  BUILD FAILED — EOL Spring version in use. Upgrade before merging.");
            System.exit(1);  // non-zero exit code fails CI
        } else {
            System.out.println("  BUILD PASSED — Spring version within support window.");
        }
    }
}
```

How to run: `java VersionCheckV3.java` (exits with code 1 because Spring Boot 3.1.8 is past EOL on 2026-06-29)

This gate runs in CI after `mvn dependency:resolve` to confirm the resolved `spring-boot.version` is within its OSS support window. Real implementations use plugins like `versions-maven-plugin` or dedicated tools like `snyk`, `dependabot`, or `renovatebot`.

## 6. Walkthrough

**Level 1 — version status logic:**
`today.isAfter(eolDate)` → EOL. `today.plusDays(90).isAfter(eolDate)` → near-EOL warning. Otherwise supported. Spring 3.2.x's EOL is November 2025 — on 2026-06-29 it is already past EOL, shown as "EOL — upgrade now".

**Level 2 — upgrade path:**
`SemVer.parse("2.7.18")` → `{major=2, minor=7, patch=18}`. `recommend()` finds the latest `isCurrent` version by comparing `SemVer` (lexicographic on major, minor, patch). A 2.x project gets "Major upgrade required" because 3.x requires Jakarta EE migration. A 3.1.x project gets "upgrade to 3.4.1".

**Level 3 — CI gate flow:**
1. `POM_PROPERTIES.get("spring-boot.version")` → `"3.1.8"`.
2. `majorMinor = "3.1"` → `Policy(eolDate=2024-11-21)`.
3. `today.isAfter(2024-11-21)` → true → `daysOverdue = 585`.
4. Prints `FAIL: reached EOL 585 days ago`.
5. `System.exit(1)` — the CI step fails; the PR cannot merge.

**In real CI:**
```yaml
# GitHub Actions step
- name: Spring version gate
  run: java VersionCheckV3.java
  # Fails pipeline if exit code != 0
```

Or use `versions-maven-plugin:display-dependency-updates` to print available upgrades, and `renovatebot` to auto-create PRs for patch upgrades.

## 7. Gotchas & takeaways

> **SNAPSHOT versions are never stable.** `3.4.0-SNAPSHOT` is the nightly build of the development branch — API can change overnight. Never use SNAPSHOT in a production `pom.xml`. If you must test a pre-release, use a milestone (`M1`) or release candidate (`RC1`), pin it explicitly, and have a plan to switch to GA.

> **Spring Boot's BOM locks all ecosystem project versions.** When you declare `<parent>spring-boot-starter-parent:3.4.1</parent>`, the BOM pins compatible versions of Spring Framework, Spring Security, Spring Data, Hibernate, Jackson, Micrometer, etc. Do not override individual Spring ecosystem versions unless you have a specific reason — mismatched versions cause subtle runtime failures.

- `spring.io/projects` shows the current support status for every Spring project; the "Support" tab is the authoritative source.
- Commercial support (VMware SpringOne/Broadcom) extends the lifecycle 3–5 years beyond OSS EOL — useful for enterprises that can't upgrade every 12 months.
- Security CVEs for EOL versions are still published on GitHub Security Advisories, but fixes are only backported to commercially-supported branches.
- Patch-level upgrades (3.2.5 → 3.2.7) require only bumping `spring-boot.version` and re-testing. Budget one sprint per year for minor version upgrades (3.2 → 3.3).
- Renovate Bot / Dependabot can automate patch upgrades by watching for new patch releases and opening PRs automatically.
