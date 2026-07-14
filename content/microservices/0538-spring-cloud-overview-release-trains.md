---
card: microservices
gi: 538
slug: spring-cloud-overview-release-trains
title: "Spring Cloud overview & release trains"
---

## 1. What it is

**Spring Cloud** is an umbrella project made up of many independently-versioned sub-projects (Config, Gateway, OpenFeign, Stream, LoadBalancer, Circuit Breaker, and more), each solving one specific distributed-systems concern, unified under a single **release train** — a named version (like `2023.0.x`, codenamed alphabetically after "Leyton" or similar release names) that specifies exactly which compatible version of each sub-project works together with a given Spring Boot version. Rather than picking each sub-project's version independently and hoping they're compatible, you declare one release train version in your build, and every Spring Cloud dependency you pull in resolves to a version known to work together.

## 2. Why & when

You need to understand release trains because Spring Cloud's modular structure creates a real version-compatibility problem that the release train mechanism exists specifically to solve:

- **Spring Cloud isn't one library — it's dozens of separately-developed sub-projects**, each with its own release cadence, its own versioning scheme, and its own dependencies on specific Spring Framework and Spring Boot versions. Picking compatible versions of, say, Spring Cloud Gateway and Spring Cloud OpenFeign independently, by hand, without a coordinating mechanism, is error-prone and easy to get subtly wrong.
- **A release train version is a single, well-tested combination.** Declaring `spring-cloud.version=2023.0.3` (via Spring Boot's dependency management, typically through a BOM import) fixes every individual Spring Cloud sub-project's version to one that's been verified to work correctly with that release train and with a specific range of compatible Spring Boot versions.
- **Each Spring Boot major/minor version has a specific range of compatible Spring Cloud release trains** — using a Spring Cloud release train not intended for your Spring Boot version is a common source of confusing, hard-to-diagnose startup failures (bean definition conflicts, missing classes, subtly incompatible auto-configuration), so checking the compatibility matrix before upgrading either one independently is essential.
- **You reach for the release train mechanism the moment you add more than one Spring Cloud dependency to a project** — importing the Spring Cloud BOM (Bill of Materials) once, at the release-train level, and then adding individual `spring-cloud-starter-*` dependencies without their own version numbers, is the standard, correct pattern; specifying individual Spring Cloud sub-project versions by hand defeats the purpose of the release train entirely.

## 3. Core concept

Think of a large orchestra where each musician's individual sheet music (the notes for cello, violin, trumpet) evolves and gets revised somewhat independently over time by different composers, but a concert only actually works if everyone is playing from sheet music intended for the *same performance* — mixing this season's cello part with a completely different season's trumpet part could technically still produce sound, but likely dissonant, uncoordinated noise. A "release train" is the conductor's single, curated program for one specific concert: it specifies exactly which version of every instrument's sheet music belongs together for this particular performance, so nobody has to independently verify compatibility between every possible pairing of parts.

Concretely:

1. **The Spring Cloud BOM (Bill of Materials)** is imported once in your build tool's dependency management section, specifying a single release train version (e.g., `2023.0.3`).
2. **Every subsequent `spring-cloud-starter-*` dependency you add is declared *without* its own version number** — Maven/Gradle resolves its actual version from the imported BOM, guaranteeing it's the version known to be compatible with everything else in that same release train.
3. **Release trains have their own compatibility matrix against Spring Boot versions** — published in Spring's own documentation, mapping "Spring Boot 3.2.x pairs with Spring Cloud 2023.0.x," "Spring Boot 3.1.x pairs with Spring Cloud 2022.0.x," and so on; upgrading Spring Boot without also checking (and likely upgrading) the paired Spring Cloud release train is a common source of avoidable breakage.
4. **Individual sub-projects (Config, Gateway, Stream, etc.) still have their own individual version numbers under the hood** — the release train doesn't erase those, it just pins all of them to a jointly-tested combination, so you rarely need to think about any individual sub-project's version directly.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single Spring Cloud release train version pins compatible versions of many independent sub-projects together, and itself maps to a compatible range of Spring Boot versions">
  <rect x="20" y="20" width="620" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Release train: Spring Cloud 2023.0.x (paired with Spring Boot 3.2.x)</text>

  <rect x="20" y="90" width="130" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="111" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Config: v4.1.0</text>
  <rect x="170" y="90" width="130" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="235" y="111" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Gateway: v4.1.0</text>
  <rect x="320" y="90" width="130" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="385" y="111" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OpenFeign: v4.1.0</text>
  <rect x="470" y="90" width="170" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="111" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LoadBalancer: v4.1.0</text>

  <line x1="85" y1="90" x2="330" y2="60" stroke="#8b949e"/>
  <line x1="235" y1="90" x2="330" y2="60" stroke="#8b949e"/>
  <line x1="385" y1="90" x2="330" y2="60" stroke="#8b949e"/>
  <line x1="555" y1="90" x2="330" y2="60" stroke="#8b949e"/>

  <text x="330" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">import the BOM once; individual starters resolve their version from it automatically</text>
</svg>

One release train version pins many independently-versioned sub-projects to a jointly-tested, mutually compatible combination.

## 5. Runnable example

Scenario: configuring a project's dependencies to use a Spring Cloud release train correctly. We start with a plain Java model illustrating what "unpinned, independently-chosen versions" risk, extend it to a model of BOM-style version resolution, then show the real Maven/Gradle configuration shape.

### Level 1 — Basic

```java
// File: UnpinnedVersionsRisk.java -- models the RISK of picking each
// sub-project's version INDEPENDENTLY, with no coordinating mechanism.
import java.util.*;

public class UnpinnedVersionsRisk {
    record Dependency(String name, String version) {}

    static boolean isKnownCompatiblePair(Dependency a, Dependency b) {
        // in reality, compatibility between ARBITRARY independently-chosen versions
        // is NOT guaranteed and often undocumented -- this simulates an incompatible pairing
        return a.version().equals(b.version());
    }

    public static void main(String[] args) {
        Dependency config = new Dependency("spring-cloud-config", "4.1.0");
        Dependency gateway = new Dependency("spring-cloud-gateway", "4.0.2"); // picked independently, slightly older
        System.out.println("Config: " + config + ", Gateway: " + gateway);
        System.out.println("Known compatible? " + isKnownCompatiblePair(config, gateway) + " -- versions don't match, compatibility is NOT guaranteed");
    }
}
```

How to run: `java UnpinnedVersionsRisk.java`

`config` and `gateway` were picked independently, with slightly different versions — nothing here verifies whether `4.1.0` and `4.0.2` are actually known to work together, since there's no shared coordinating mechanism. In a real project, this is exactly the risk of specifying individual Spring Cloud sub-project versions by hand rather than through a release train's BOM.

### Level 2 — Intermediate

```java
// File: BomResolutionModel.java -- models the BOM idea: ONE release
// train version resolves EVERY sub-project's version automatically,
// guaranteeing a known-compatible combination.
import java.util.*;

public class BomResolutionModel {
    static Map<String, Map<String, String>> releaseTrainVersions = Map.of(
        "2023.0.3", Map.of("spring-cloud-config", "4.1.0", "spring-cloud-gateway", "4.1.0", "spring-cloud-openfeign", "4.1.0")
    );

    // resolves a sub-project's ACTUAL version from the release train, not from an independent choice
    static String resolve(String releaseTrain, String subProject) {
        return releaseTrainVersions.get(releaseTrain).get(subProject);
    }

    public static void main(String[] args) {
        String releaseTrain = "2023.0.3"; // declared ONCE
        System.out.println("Config resolves to: " + resolve(releaseTrain, "spring-cloud-config"));
        System.out.println("Gateway resolves to: " + resolve(releaseTrain, "spring-cloud-gateway"));
        System.out.println("OpenFeign resolves to: " + resolve(releaseTrain, "spring-cloud-openfeign"));
        System.out.println("All three resolved from ONE release train declaration -- guaranteed to be a known-compatible combination.");
    }
}
```

How to run: `java BomResolutionModel.java`

`releaseTrainVersions` models the BOM: declaring `"2023.0.3"` once resolves every individual sub-project to the specific version known to work together within that release train — no individual version numbers are chosen by hand, eliminating exactly the risk demonstrated in Level 1.

### Level 3 — Advanced

```java
// File: MavenBomConfigShape.java -- NOT executable Java, but the REAL
// Maven pom.xml shape release trains actually use in practice, shown
// here as a documented string constant for illustration.
public class MavenBomConfigShape {
    static final String POM_XML_SNIPPET = """
        <properties>
            <spring-cloud.version>2023.0.3</spring-cloud.version>
        </properties>

        <dependencyManagement>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.cloud</groupId>
                    <artifactId>spring-cloud-dependencies</artifactId>
                    <version>${spring-cloud.version}</version>
                    <type>pom</type>
                    <scope>import</scope>
                </dependency>
            </dependencies>
        </dependencyManagement>

        <dependencies>
            <!-- NO version specified here -- resolved from the imported BOM above -->
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-config</artifactId>
            </dependency>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-starter-gateway</artifactId>
            </dependency>
        </dependencies>
        """;

    public static void main(String[] args) {
        System.out.println(POM_XML_SNIPPET);
        System.out.println("Both starters above resolve their ACTUAL version from spring-cloud-dependencies 2023.0.3 -- no independent version numbers chosen.");
    }
}
```

How to run: `java MavenBomConfigShape.java` (prints the illustrative pom.xml snippet); in a real Maven project, this exact `dependencyManagement` block, placed in a real `pom.xml`, is what actually pins every subsequently-declared `spring-cloud-starter-*` dependency's version via BOM import — the equivalent in Gradle uses `implementation platform("org.springframework.cloud:spring-cloud-dependencies:2023.0.3")`.

Note that `spring-cloud-starter-config` and `spring-cloud-starter-gateway` in the `<dependencies>` section have no `<version>` tag at all — Maven resolves their actual versions by consulting the imported `spring-cloud-dependencies` BOM declared in `<dependencyManagement>`, guaranteeing both starters come from the same jointly-tested `2023.0.3` release train, exactly the mechanism the plain-Java model in Level 2 simulated.

## 6. Walkthrough

Trace what happens when Maven resolves dependencies for a project using the `pom.xml` shape from Level 3, end to end:

1. **Maven reads the `<dependencyManagement>` section first.** It finds an `import`-scoped dependency on `spring-cloud-dependencies` version `2023.0.3` (itself resolved from the `${spring-cloud.version}` property) — this pulls in that BOM's own internal list of every Spring Cloud sub-project and its exact, jointly-tested version for this release train.
2. **Maven then reads the `<dependencies>` section**, finding `spring-cloud-starter-config` and `spring-cloud-starter-gateway`, neither with an explicit `<version>`.
3. **For each unversioned dependency, Maven consults the imported BOM's version list** (populated in step 1) and finds the matching entry — say, `spring-cloud-starter-config` resolves to `4.1.0` and `spring-cloud-starter-gateway` also resolves to `4.1.0` (or whatever specific versions the `2023.0.3` release train's BOM actually specifies for each).
4. **Both dependencies, plus their own transitive dependencies (also resolved via the same BOM), are downloaded and added to the project's classpath** — critically, both came from the *same* release train's coordinated set, so they're guaranteed by Spring's own testing to work correctly together, unlike the Level 1 scenario where `4.1.0` and `4.0.2` were chosen independently with no such guarantee.
5. **At application startup, Spring Boot's auto-configuration for each of these starters activates**, and because they originate from a mutually-compatible release train, their interactions (Config Client talking to Config Server, Gateway routing through discovery) work as documented — the entire point of pinning to one release train rather than mixing independently-chosen sub-project versions.

## 7. Gotchas & takeaways

> **Gotcha:** upgrading your project's Spring Boot version without also checking (and likely upgrading) the paired Spring Cloud release train is one of the most common sources of confusing startup failures in Spring Cloud projects — each release train has a documented compatible Spring Boot version range, and using a Spring Cloud release train intended for an older or newer Spring Boot version than what your project actually uses often produces obscure bean-definition or auto-configuration errors that don't obviously point back to a version mismatch.

- Import the Spring Cloud BOM (`spring-cloud-dependencies`) once, at a chosen release train version, and add individual `spring-cloud-starter-*` dependencies without their own version numbers — let the BOM resolve them.
- Never specify individual Spring Cloud sub-project versions by hand alongside a BOM import — doing so overrides the BOM's carefully-tested pairing and reintroduces the exact compatibility risk the release train exists to prevent.
- Check Spring's official compatibility matrix before upgrading Spring Boot or the Spring Cloud release train independently — the two are versioned separately but tightly coupled in compatibility.
- Release train names follow a year.minor numbering scheme (having moved on from the earlier alphabetic codename convention) — treat the release train version, not any individual sub-project's version number, as the primary thing you track and upgrade deliberately.
