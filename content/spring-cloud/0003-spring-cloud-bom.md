---
card: spring-cloud
gi: 3
slug: spring-cloud-bom
title: "Spring Cloud BOM"
---

## 1. What it is

The Spring Cloud BOM (Bill of Materials) — the `spring-cloud-dependencies` artifact — is a Maven/Gradle mechanism for importing an entire release train's compatible version set in one declaration, so every individual `spring-cloud-*` dependency added afterward doesn't need its own explicit version.

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-dependencies</artifactId>
            <version>2024.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-gateway</artifactId>
        <!-- no version needed -- resolved from the imported BOM -->
    </dependency>
</dependencies>
```

## 2. Why & when

The previous card explained *why* release trains exist — one version number for a compatible bundle. The BOM is the concrete mechanism that makes declaring that one version actually work in a build file: it's a `pom`-typed, `import`-scoped dependency that injects version numbers for every Spring Cloud artifact into the build's dependency management, without adding any of them to the classpath itself.

Reach for the BOM when:

- Setting up any project that uses more than one Spring Cloud starter — declaring the BOM once means every `spring-cloud-starter-*` dependency omits its version.
- Upgrading a project's Spring Cloud train version — changing the BOM's version is the single edit that cascades to every sub-project dependency, rather than hunting down and updating each one individually.
- You want to guarantee the same compatible version set the previous card described is actually what gets resolved, not just documented intent.

## 3. Core concept

```
 <dependencyManagement>
   <dependency> spring-cloud-dependencies:2024.0.0, type=pom, scope=import </dependency>
 </dependencyManagement>
   -> imports version numbers for EVERY spring-cloud-* artifact, but adds NOTHING to the classpath yet

 <dependencies>
   <dependency> spring-cloud-starter-gateway </dependency>     -- version resolved from the BOM
   <dependency> spring-cloud-starter-config </dependency>       -- version ALSO resolved from the BOM
 </dependencies>
   -> these DO get added to the classpath, at whatever version the BOM specified for train 2024.0.0
```

`dependencyManagement`/`import` supplies version numbers without adding dependencies; the actual `dependencies` block is where artifacts get added, picking up those managed versions automatically.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A BOM import supplies a version catalog which two unversioned dependency declarations both draw from">
  <rect x="220" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">BOM import (version catalog)</text>

  <line x1="270" y1="60" x2="150" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a24)"/>
  <line x1="370" y1="60" x2="490" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a24)"/>

  <rect x="30" y="105" width="240" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring-cloud-starter-gateway (no version)</text>

  <rect x="370" y="105" width="240" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring-cloud-starter-config (no version)</text>

  <defs><marker id="a24" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The BOM supplies a version catalog that multiple unversioned dependency declarations draw from.

## 5. Runnable example

The scenario: modeling BOM-based version resolution for a build, evolving from repeating an explicit version on every dependency (the maintenance burden the BOM removes), to a BOM-backed resolver supplying versions automatically, to an upgrade scenario showing a single BOM version bump cascading to every dependency at once.

### Level 1 — Basic

Show the repeated-explicit-version baseline — the maintenance burden across many dependency declarations.

```java
import java.util.*;

public class BomLevel1 {
    public static void main(String[] args) {
        List<Dependency> dependencies = List.of(
            new Dependency("spring-cloud-starter-gateway", "4.1.5"),  // version repeated here
            new Dependency("spring-cloud-starter-config", "4.1.3"),    // and here
            new Dependency("spring-cloud-starter-openfeign", "4.1.3")  // and here
        );
        // Upgrading means finding and editing EVERY one of these version strings individually.
        for (Dependency d : dependencies) System.out.println(d.artifactId + " -> " + d.version);
    }
}

class Dependency {
    String artifactId, version;
    Dependency(String artifactId, String version) { this.artifactId = artifactId; this.version = version; }
}
```

How to run: `java BomLevel1.java`

Every dependency carries its own explicit version string — upgrading the Spring Cloud train means finding and editing each one individually, and missing even one leaves the build with a mismatched, potentially incompatible version.

### Level 2 — Intermediate

Add a BOM-backed resolver: dependencies are declared *without* a version, and the version comes from a single imported catalog instead.

```java
import java.util.*;

public class BomLevel2 {
    public static void main(String[] args) {
        Bom bom = new Bom("2024.0.0", Map.of(
            "spring-cloud-starter-gateway", "4.1.5",
            "spring-cloud-starter-config", "4.1.3",
            "spring-cloud-starter-openfeign", "4.1.3"
        ));

        List<String> declaredDependencies = List.of(
            "spring-cloud-starter-gateway",     // no version declared here
            "spring-cloud-starter-config",       // or here
            "spring-cloud-starter-openfeign"     // or here
        );

        System.out.println("Resolved using BOM " + bom.trainVersion + ":");
        for (String artifactId : declaredDependencies) {
            System.out.println("  " + artifactId + " -> " + bom.resolve(artifactId));
        }
    }
}

// Stands in for the spring-cloud-dependencies BOM.
class Bom {
    String trainVersion;
    Map<String, String> versions;
    Bom(String trainVersion, Map<String, String> versions) { this.trainVersion = trainVersion; this.versions = versions; }
    String resolve(String artifactId) { return versions.get(artifactId); }
}
```

How to run: `java BomLevel2.java`

`declaredDependencies` carries no version information at all — every version is resolved through `bom.resolve(...)`, mirroring exactly how a real Maven/Gradle build resolves unversioned `spring-cloud-starter-*` dependencies against the imported BOM's managed versions.

### Level 3 — Advanced

Show an upgrade scenario: swap the BOM's train version, and every dependency's resolved version updates automatically — the single-point-of-change payoff the BOM provides.

```java
import java.util.*;

public class BomLevel3 {
    public static void main(String[] args) {
        Map<String, Bom> availableTrains = Map.of(
            "2023.0.0", new Bom("2023.0.0", Map.of(
                "spring-cloud-starter-gateway", "4.0.9", "spring-cloud-starter-config", "4.0.7")),
            "2024.0.0", new Bom("2024.0.0", Map.of(
                "spring-cloud-starter-gateway", "4.1.5", "spring-cloud-starter-config", "4.1.3"))
        );

        List<String> declaredDependencies = List.of("spring-cloud-starter-gateway", "spring-cloud-starter-config");

        System.out.println("--- Before upgrade (BOM = 2023.0.0) ---");
        printResolved(availableTrains.get("2023.0.0"), declaredDependencies);

        System.out.println("--- After upgrade (BOM = 2024.0.0, ONE line changed) ---");
        printResolved(availableTrains.get("2024.0.0"), declaredDependencies);
    }

    static void printResolved(Bom bom, List<String> declaredDependencies) {
        for (String artifactId : declaredDependencies) {
            System.out.println("  " + artifactId + " -> " + bom.resolve(artifactId));
        }
    }
}

class Bom {
    String trainVersion;
    Map<String, String> versions;
    Bom(String trainVersion, Map<String, String> versions) { this.trainVersion = trainVersion; this.versions = versions; }
    String resolve(String artifactId) { return versions.get(artifactId); }
}
```

How to run: `java BomLevel3.java`

`declaredDependencies` — the list of artifact ids a project actually depends on — never changes between the "before" and "after" runs; only the `Bom` instance passed to `printResolved` changes, mirroring how a real upgrade is just editing the BOM's version string in `pom.xml`, with every dependent artifact's resolved version updating automatically as a consequence.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two `Bom` instances are prepared, keyed by train version, each with its own version map for the same two artifact ids.

`printResolved(availableTrains.get("2023.0.0"), declaredDependencies)` resolves both artifacts against the older train:

```
--- Before upgrade (BOM = 2023.0.0) ---
  spring-cloud-starter-gateway -> 4.0.9
  spring-cloud-starter-config -> 4.0.7
```

`printResolved(availableTrains.get("2024.0.0"), declaredDependencies)` resolves the *same* `declaredDependencies` list, but against the newer train's version map:

```
--- After upgrade (BOM = 2024.0.0, ONE line changed) ---
  spring-cloud-starter-gateway -> 4.1.5
  spring-cloud-starter-config -> 4.1.3
```

The list of dependencies a project declares stays completely stable across the upgrade — only the BOM reference changes. In a real `pom.xml`, this is genuinely a one-line edit (the `<version>` inside the `spring-cloud-dependencies` import), and Maven's dependency resolution recomputes every managed version from that single change the next time the build runs, exactly as modeled here by swapping which `Bom` object gets passed in.

## 7. Gotchas & takeaways

> Gotcha: the BOM import must use `<type>pom</type>` and `<scope>import</scope>` in Maven — omitting either, or accidentally declaring it as a normal dependency instead of a `dependencyManagement` import, either fails the build or (worse) silently pulls in the BOM's own transitive dependencies rather than just its version catalog.

> Gotcha: a dependency declared *without* a version, but for an artifact the imported BOM doesn't happen to manage, still fails to resolve — the BOM only supplies versions for artifacts it explicitly lists; it's not a wildcard fallback for arbitrary unversioned dependencies.

- The Spring Cloud BOM (`spring-cloud-dependencies`) is imported once via `dependencyManagement`, supplying compatible versions for every `spring-cloud-*` artifact without adding anything to the classpath itself.
- Individual `spring-cloud-starter-*` dependencies are then declared without an explicit version, resolving automatically against the imported BOM's catalog.
- Upgrading the Spring Cloud train version is a single edit to the BOM's version — every dependent artifact's resolved version updates as a consequence, with no need to hunt down individual version strings.
- The BOM only supplies versions for artifacts it explicitly manages — it doesn't provide a fallback for unrelated or unmanaged dependencies.
