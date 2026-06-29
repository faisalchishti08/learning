---
card: spring-framework
gi: 12
slug: spring-bom-bill-of-materials-for-dependency-management
title: Spring BOM (Bill of Materials) for dependency management
---

## 1. What it is

A **Bill of Materials (BOM)** is a special Maven POM with `<packaging>pom</packaging>` and a `<dependencyManagement>` section that declares the versions of a coordinated set of libraries. You import the BOM into your project; from that point on, you declare dependencies in that library set without specifying versions — the BOM supplies them.

**Spring Boot's BOM** (`spring-boot-dependencies`) lists versions for:
- All Spring Framework modules (`spring-core`, `spring-webmvc`, `spring-data-*`, …)
- Spring Security, Spring Data, Spring Batch, Spring Cloud (via sub-BOMs)
- Third-party libraries: Hibernate, Jackson, Micrometer, Mockito, JUnit 5, PostgreSQL JDBC, Flyway, Liquibase, Logback, SLF4J, and ~300 more.

Every library in the BOM has been **integration-tested together** by the Spring team before a Boot release. This is the BOMs core value: it is not just a version list, it is a verified compatibility matrix.

**Maven import:**
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.4.1</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

**Gradle import (native platform):**
```kotlin
dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:3.4.1"))
}
```

## 2. Why & when

**Without a BOM:** adding Spring MVC to a project requires knowing that `spring-webmvc:6.1.4` depends on `spring-core:6.1.4`, `spring-beans:6.1.4`, `spring-context:6.1.4`, `spring-aop:6.1.4`, and `spring-expression:6.1.4` — all at the *same* version. Getting one wrong causes `ClassNotFoundException`, `NoSuchMethodError`, or `IncompatibleClassChangeError` at runtime.

**With a BOM:** you declare `spring-boot-starter-web` and the BOM resolves every transitive dependency to a compatible version automatically.

**When to use directly vs. via parent POM:**
- `spring-boot-starter-parent` (the parent POM) includes `spring-boot-dependencies` (the BOM) inside its own `<dependencyManagement>`. If you use the parent, the BOM is already active.
- Use the BOM directly (`<scope>import</scope>` or Gradle `platform()`) when: you already have a corporate parent POM you cannot change, you are building a library (libraries should not inherit from `spring-boot-starter-parent`), or you need to compose multiple BOMs.

## 3. Core concept

A BOM works through Maven's `<dependencyManagement>` inheritance and import mechanism:

1. `spring-boot-dependencies.pom` declares: `<jackson-databind.version>2.17.2</jackson-databind.version>` and `<dependency>com.fasterxml.jackson.core:jackson-databind:${jackson-databind.version}</dependency>`.
2. You import it: Maven copies every entry in its `<dependencyManagement>` into yours.
3. You declare: `<dependency>com.fasterxml.jackson.core:jackson-databind</dependency>` (no version).
4. Maven sees this dependency already has a version in `<dependencyManagement>` → uses `2.17.2`.

**Version conflict resolution order** (Maven):**

| Priority | Source | Notes |
|---|---|---|
| 1 (highest) | Explicit `<version>` in your `<dependency>` | Overrides BOM |
| 2 | `<dependencyManagement>` in your POM | Direct declaration wins over import |
| 3 | BOM import | Applied in import order; first wins |
| 4 | Transitive dependency versions | Lowest priority |

**BOM composition:** you can import multiple BOMs. If both declare a version for the same artifact, the first import wins:
```xml
<dependencyManagement>
    <dependencies>
        <!-- Your override BOM wins -->
        <dependency>
            <groupId>com.example</groupId><artifactId>version-overrides-bom</artifactId>
            <version>1.0</version><type>pom</type><scope>import</scope>
        </dependency>
        <!-- Spring Boot BOM fills in the rest -->
        <dependency>
            <groupId>org.springframework.boot</groupId><artifactId>spring-boot-dependencies</artifactId>
            <version>3.4.1</version><type>pom</type><scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BOM import flow: spring-boot-dependencies BOM supplies versions to project POM, which declares starters without versions">
  <defs>
    <marker id="ba" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="bw" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- BOM box -->
  <rect x="10" y="60" width="260" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="140" y="82" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-boot-dependencies:3.4.1</text>
  <text x="140" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(the BOM — packaging=pom)</text>
  <text x="140" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-webmvc → 6.1.4</text>
  <text x="140" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">jackson-databind → 2.17.2</text>
  <text x="140" y="152" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hibernate-core → 6.4.4.Final</text>
  <text x="140" y="168" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">junit-jupiter → 5.10.1</text>
  <text x="140" y="184" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">…300+ more…</text>

  <!-- Project pom -->
  <rect x="330" y="60" width="250" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="455" y="82" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Your project pom.xml</text>
  <text x="455" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;dependency&gt;</text>
  <text x="455" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-web  (no version)</text>
  <text x="455" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-data-jpa  (no version)</text>
  <text x="455" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">postgresql  (no version)</text>
  <text x="455" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">junit:5.10.1 — explicit</text>
  <text x="455" y="174" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">↑ overrides BOM: explicit wins</text>

  <!-- Import arrow -->
  <line x1="270" y1="130" x2="328" y2="130" stroke="#79c0ff" stroke-width="2" marker-end="url(#ba)"/>
  <text x="299" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">import</text>

  <!-- Resolved JAR label -->
  <rect x="245" y="225" width="210" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="243" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Maven resolves versions — no conflicts</text>

  <line x1="455" y1="200" x2="420" y2="223" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
  <line x1="140" y1="200" x2="280" y2="223" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
</svg>

The BOM is the compatibility matrix. Your project declares what it needs; the BOM supplies compatible versions.

## 5. Runnable example

A library + application pair showing BOM usage at each level of complexity.

### Level 1 — Basic

Simulate how Maven resolves versions from a BOM — the core mechanism.

```java
// BomDemo.java — run with: java BomDemo.java
// Simulates what Maven's dependencyManagement/BOM does at build time.

import java.util.*;

public class BomDemo {

    // Simulates spring-boot-dependencies BOM entries
    static final Map<String, String> BOM = new LinkedHashMap<>(Map.of(
        "org.springframework:spring-webmvc",              "6.1.4",
        "com.fasterxml.jackson.core:jackson-databind",    "2.17.2",
        "org.hibernate.orm:hibernate-core",               "6.4.4.Final",
        "org.junit.jupiter:junit-jupiter",                "5.10.1",
        "org.postgresql:postgresql",                      "42.7.3",
        "io.micrometer:micrometer-core",                  "1.12.4",
        "ch.qos.logback:logback-classic",                 "1.5.6",
        "org.assertj:assertj-core",                       "3.25.3"
    ));

    // Project declares dependencies WITHOUT versions
    record DeclaredDep(String coordinate, String explicitVersion) {
        boolean hasExplicit() { return explicitVersion != null; }
    }

    static final List<DeclaredDep> PROJECT_DEPS = List.of(
        new DeclaredDep("org.springframework:spring-webmvc",           null),   // from BOM
        new DeclaredDep("com.fasterxml.jackson.core:jackson-databind", null),   // from BOM
        new DeclaredDep("org.postgresql:postgresql",                   null),   // from BOM
        new DeclaredDep("org.junit.jupiter:junit-jupiter",             "5.11.0") // explicit override
    );

    public static void main(String[] args) {
        System.out.println("=== BOM Version Resolution ===\n");
        System.out.printf("%-50s %-15s %s%n", "Artifact", "Source", "Version");
        System.out.println("-".repeat(75));

        for (DeclaredDep dep : PROJECT_DEPS) {
            String resolvedVersion;
            String source;
            if (dep.hasExplicit()) {
                resolvedVersion = dep.explicitVersion();
                source = "explicit";
            } else {
                resolvedVersion = BOM.get(dep.coordinate());
                source = resolvedVersion != null ? "BOM" : "MISSING — build error!";
            }
            System.out.printf("%-50s %-15s %s%n", dep.coordinate(), source, resolvedVersion);
        }

        System.out.println("\nConclusion:");
        System.out.println("  spring-webmvc, jackson-databind, postgresql: versions from BOM");
        System.out.println("  junit-jupiter 5.11.0: explicit override wins over BOM's 5.10.1");
        System.out.println("  No version mismatches possible for BOM-managed artifacts.");
    }
}
```

How to run: `java BomDemo.java`

The explicit `5.11.0` overrides the BOM's `5.10.1` for `junit-jupiter`. All other artifacts use BOM versions. In a real Maven build, declaring a version in `<dependency>` always wins over `<dependencyManagement>`.

### Level 2 — Intermediate

Build a multi-BOM composition — corporate security BOM overlaid on Spring Boot BOM.

```java
// BomDemoV2.java — run with: java BomDemoV2.java
// BOM composition: corporate override BOM + Spring Boot BOM + conflict resolution.

import java.util.*;

public class BomDemoV2 {

    record BomEntry(String coordinate, String version, String bomName) {}

    // Corporate security BOM — overrides specific CVE-patched versions
    static final List<BomEntry> CORP_BOM = List.of(
        new BomEntry("org.postgresql:postgresql",          "42.7.4", "corp-security-bom"),
        new BomEntry("ch.qos.logback:logback-classic",    "1.5.8",  "corp-security-bom"),
        new BomEntry("org.yaml:snakeyaml",                "2.2",    "corp-security-bom")
    );

    // Spring Boot BOM (selected entries)
    static final List<BomEntry> BOOT_BOM = List.of(
        new BomEntry("org.springframework:spring-webmvc",             "6.1.4",      "spring-boot-dependencies"),
        new BomEntry("com.fasterxml.jackson.core:jackson-databind",   "2.17.2",     "spring-boot-dependencies"),
        new BomEntry("org.postgresql:postgresql",                      "42.7.3",     "spring-boot-dependencies"),  // older
        new BomEntry("ch.qos.logback:logback-classic",                "1.5.6",      "spring-boot-dependencies"),  // older
        new BomEntry("org.yaml:snakeyaml",                            "2.2",        "spring-boot-dependencies"),
        new BomEntry("io.micrometer:micrometer-core",                 "1.12.4",     "spring-boot-dependencies"),
        new BomEntry("org.junit.jupiter:junit-jupiter",               "5.10.1",     "spring-boot-dependencies")
    );

    public static void main(String[] args) {
        System.out.println("=== Multi-BOM Composition (Corp BOM overrides Spring Boot BOM) ===\n");

        // Maven applies BOMs in order; first declaration of a coordinate wins
        // Corp BOM is imported first → its versions take precedence
        Map<String, BomEntry> resolved = new LinkedHashMap<>();

        System.out.println("Applying corp-security-bom (first — higher priority):");
        for (BomEntry e : CORP_BOM) {
            resolved.put(e.coordinate(), e);
            System.out.println("  " + e.coordinate() + " = " + e.version());
        }

        System.out.println("\nApplying spring-boot-dependencies (second — fills gaps):");
        for (BomEntry e : BOOT_BOM) {
            if (resolved.containsKey(e.coordinate())) {
                System.out.println("  SKIPPED (corp BOM wins): " + e.coordinate()
                    + " [corp=" + resolved.get(e.coordinate()).version()
                    + ", boot=" + e.version() + "]");
            } else {
                resolved.put(e.coordinate(), e);
                System.out.println("  " + e.coordinate() + " = " + e.version());
            }
        }

        System.out.println("\n=== Final resolved versions ===");
        System.out.printf("%-50s %-15s %s%n", "Coordinate", "Version", "BOM");
        System.out.println("-".repeat(80));
        resolved.values().forEach(e ->
            System.out.printf("%-50s %-15s %s%n", e.coordinate(), e.version(), e.bomName()));

        System.out.println("\nSecurity impact:");
        System.out.println("  postgresql: 42.7.3 (Boot) → 42.7.4 (corp) — CVE-2024-xyz patched");
        System.out.println("  logback:    1.5.6  (Boot) → 1.5.8  (corp) — log injection fix");
    }
}
```

How to run: `java BomDemoV2.java`

The corporate security BOM is listed first in `<dependencyManagement>` so its versions win. The Spring Boot BOM fills in everything else. This is the standard enterprise pattern for applying security patches without waiting for Boot's next release.

### Level 3 — Advanced

Full BOM conflict diagnosis: detect version mismatches, explain resolution, and flag unsafe overrides — exactly what `mvn dependency:tree -Dverbose` shows.

```java
// BomDemoV3.java — run with: java BomDemoV3.java
// Full dependency conflict resolution with verbose explanation and safety checks.

import java.util.*;
import java.util.stream.*;

public class BomDemoV3 {

    record Version(int major, int minor, int patch) implements Comparable<Version> {
        static Version parse(String v) {
            String cleaned = v.replaceAll("[^0-9.]", "").replaceAll("\\.+", ".");
            String[] p = (cleaned + ".0.0").split("\\.");
            return new Version(
                Integer.parseInt(p[0]),
                Integer.parseInt(p[1]),
                Integer.parseInt(p[2]));
        }
        @Override public int compareTo(Version o) {
            int c = Integer.compare(major, o.major);
            if (c != 0) return c;
            c = Integer.compare(minor, o.minor);
            return c != 0 ? c : Integer.compare(patch, o.patch);
        }
        @Override public String toString() { return major + "." + minor + "." + patch; }
        boolean isMajorDifferentFrom(Version o) { return major != o.major; }
    }

    record DepRequest(String coordinate, String requestedBy, String versionStr) {
        Version version() { return Version.parse(versionStr); }
    }

    public static void main(String[] args) {
        // Multiple sources claim different versions for the same artifact
        List<DepRequest> requests = List.of(
            new DepRequest("com.fasterxml.jackson.core:jackson-databind", "spring-boot-dependencies BOM", "2.17.2"),
            new DepRequest("com.fasterxml.jackson.core:jackson-databind", "quarkus-jackson:3.0",          "2.16.0"),
            new DepRequest("com.fasterxml.jackson.core:jackson-databind", "your pom.xml",                 "2.15.0"),
            new DepRequest("org.springframework:spring-webmvc",           "spring-boot-dependencies BOM", "6.1.4"),
            new DepRequest("org.springframework:spring-webmvc",           "some-old-lib:1.0",             "5.3.30"),
            new DepRequest("org.hibernate.orm:hibernate-core",            "spring-boot-dependencies BOM", "6.4.4"),
            new DepRequest("org.hibernate.orm:hibernate-core",            "direct dep",                   "6.4.4")
        );

        // Group by coordinate — simulate Maven's conflict resolution
        Map<String, List<DepRequest>> byCoordinate = requests.stream()
            .collect(Collectors.groupingBy(DepRequest::coordinate, LinkedHashMap::new, Collectors.toList()));

        System.out.println("=== Dependency Conflict Resolution Report ===\n");

        for (Map.Entry<String, List<DepRequest>> entry : byCoordinate.entrySet()) {
            String coord = entry.getKey();
            List<DepRequest> claims = entry.getValue();

            // Maven picks the version from the highest-priority source (pom > import BOM > transitive)
            // Here we simulate: explicit wins > BOM wins > transitive
            DepRequest winner = claims.stream()
                .filter(r -> r.requestedBy().equals("your pom.xml"))
                .findFirst()
                .orElse(claims.stream()
                    .filter(r -> r.requestedBy().contains("BOM"))
                    .findFirst()
                    .orElse(claims.get(0)));

            boolean hasConflict = claims.stream()
                .anyMatch(c -> !c.versionStr().equals(winner.versionStr()));

            System.out.printf("%-55s → %s (winner: %s)%n",
                coord, winner.versionStr(), winner.requestedBy());

            if (hasConflict) {
                System.out.println("  CONFLICT detected:");
                claims.stream()
                    .filter(c -> !c.versionStr().equals(winner.versionStr()))
                    .forEach(c -> {
                        Version w = Version.parse(winner.versionStr());
                        Version l = Version.parse(c.versionStr());
                        String risk = w.isMajorDifferentFrom(l) ? "HIGH (major version difference!)" : "low";
                        System.out.printf("    [%s] wanted %s — OVERRIDDEN — risk: %s%n",
                            c.requestedBy(), c.versionStr(), risk);
                    });
            } else {
                System.out.println("  No conflict.");
            }
            System.out.println();
        }

        System.out.println("=== Diagnosis ===");
        System.out.println("  jackson-databind: your pom.xml wants 2.15.0 (older than BOM's 2.17.2)");
        System.out.println("    → UNSAFE: you are downgrading below the BOM-tested version");
        System.out.println("    → Remove <version> from your pom.xml and let BOM manage it");
        System.out.println();
        System.out.println("  spring-webmvc: some-old-lib wants Spring 5.x but BOM provides Spring 6.x");
        System.out.println("    → HIGH RISK: Spring 5 → 6 is a major version change (javax → jakarta)");
        System.out.println("    → Replace some-old-lib with a Spring 6 compatible version");
        System.out.println("    → Or exclude spring-webmvc from some-old-lib's transitive deps");
        System.out.println();
        System.out.println("  hibernate-core: no conflict — both claims agree on 6.4.4");
        System.out.println("    → Safe: consistent versions from all requesters");
    }
}
```

How to run: `java BomDemoV3.java`

The HIGH risk flag for `spring-webmvc` shows a Spring 5 vs Spring 6 conflict — a `javax.servlet.*` vs `jakarta.servlet.*` issue that would cause `ClassNotFoundException` at runtime. The diagnosis output maps directly to what `mvn dependency:tree -Dverbose` prints in practice.

## 6. Walkthrough

**Level 1 — resolution algorithm:**
Maven iterates `PROJECT_DEPS`. For each without an explicit version, it checks `dependencyManagement` (the BOM import). The BOM contains `org.springframework:spring-webmvc` → `6.1.4`. Maven sets this version. For `junit-jupiter` with explicit `5.11.0`, Maven uses `5.11.0` — the `<dependency>` version beats `<dependencyManagement>`.

**Level 2 — BOM composition:**
`CORP_BOM` is looped first, populating `resolved`. When `BOOT_BOM` is looped, `postgresql` is already in `resolved` (from corp BOM) → `SKIPPED`. All Boot-BOM-only artifacts (spring-webmvc, jackson, micrometer, junit) are added. Final resolution: `postgresql=42.7.4` (corp), `logback=1.5.8` (corp), everything else from Boot.

**Level 3 — conflict resolution for `jackson-databind`:**
Three claimants: `your pom.xml → 2.15.0`, `BOM → 2.17.2`, `quarkus → 2.16.0`. Winner algorithm: explicit pom.xml wins → `2.15.0`. But `2.15.0 < 2.17.2` (BOM tested version) — this is a downgrade, which is flagged as unsafe. The correct action: remove the explicit `<version>` from your `<dependency>` so the BOM's `2.17.2` applies.

For `spring-webmvc`: winner is BOM's `6.1.4`. `some-old-lib` wants `5.3.30` — major version difference, HIGH risk. Action: `mvn dependency:tree` to find `some-old-lib`, add `<exclusions>` for `spring-webmvc`, or upgrade `some-old-lib` to a Spring 6-compatible version.

## 7. Gotchas & takeaways

> **Explicitly overriding a BOM version to an older version is almost always wrong.** If you declare `<jackson-databind.version>2.15.0</jackson-databind.version>` (a BOM property) but the BOM is `3.4.1` (which bundles `2.17.2`), you will run Jackson `2.15.0` with Spring 6 / Jackson module code that may depend on `2.17.x` APIs. The downgrade appears to work until a specific deserialization path fails silently or throws at runtime.

> **`mvn dependency:tree -Dverbose` is your diagnostic tool.** It shows every artifact, its resolved version, and the path through the dependency graph that caused the resolution. Lines marked `(version managed from ...)` show BOM overrides; lines marked `(omitted for conflict with ...)` show discarded versions. Read it before assuming a BOM problem.

- The BOM does not add dependencies to your project. It only pre-populates `<dependencyManagement>`. You must still declare `<dependency>spring-boot-starter-web</dependency>` to actually use web functionality.
- You can override a BOM-managed version by declaring the property the BOM uses: `<properties><jackson-databind.version>2.17.4</jackson-databind.version></properties>`. This upgrades above the BOM's version — safer than downgrading.
- `spring-boot-starter-parent` uses `spring-boot-dependencies` (the BOM) internally via `<dependencyManagement><scope>import</scope>`. If you use the parent, the BOM is already active.
- For Gradle, prefer `platform()` over `io.spring.dependency-management` plugin in new projects. The plugin is more Maven-BOM-compatible but adds a Gradle build-script dependency; `platform()` is native Gradle.
- Libraries (JAR artifacts) should NOT inherit from `spring-boot-starter-parent`. They should use `<scope>import</scope>` or `platform()` instead, to avoid polluting their own users' dependency management.
