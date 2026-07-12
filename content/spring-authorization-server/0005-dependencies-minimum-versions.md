---
card: spring-authorization-server
gi: 5
slug: dependencies-minimum-versions
title: "Dependencies & minimum versions"
---

## 1. What it is

`spring-security-oauth2-authorization-server` is the single Maven/Gradle coordinate that pulls in Spring Authorization Server, but it has real, non-negotiable minimum version requirements on the Spring Security and Spring Framework versions beneath it — since it relies on `SecurityFilterChain`/`HttpSecurity` DSL capabilities and reactive/servlet infrastructure that only exist from certain baseline versions onward. Spring Boot's dependency management (via `spring-boot-starter-parent` or the BOM) handles this alignment automatically for most applications, resolving compatible versions of every transitive dependency together, rather than requiring a developer to hand-pick a compatible version matrix.

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>  <!-- a version KNOWN to align with a compatible Spring Authorization Server release -->
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.security</groupId>
        <artifactId>spring-security-oauth2-authorization-server</artifactId>
        <!-- NO explicit version needed -- Spring Boot's dependency management resolves it -->
    </dependency>
</dependencies>
```

## 2. Why & when

Every prior card's DSL (`OAuth2AuthorizationServerConfigurer`, `RegisteredClient`) only exists starting from specific Spring Security versions, and Spring Authorization Server's own releases are versioned and tested against corresponding Spring Boot/Spring Security baselines — mixing an old Spring Boot parent with a manually-forced, newer Spring Authorization Server version (or vice versa) risks subtle incompatibilities: missing classes, unexpected `NoSuchMethodError`s at runtime, or configuration that compiles but behaves incorrectly because the underlying Spring Security version doesn't fully support what the authorization server library expects. Letting Spring Boot's own dependency management resolve compatible versions together is the reliable way to avoid this entirely, rather than treating each dependency's version as an independent choice.

Reach for understanding minimum version requirements specifically when:

- Setting up a new project — starting from a current Spring Boot parent version (or Spring Initializr, which defaults to one) is the simplest way to guarantee a compatible baseline, rather than assembling dependency versions manually.
- Upgrading an existing application's Spring Boot version — checking that the corresponding Spring Authorization Server version (resolved transitively) still supports whatever configuration the application relies on is a reasonable pre-upgrade check, especially across major version boundaries.
- Debugging a `NoSuchMethodError`, `ClassNotFoundException`, or unexpected behavior specifically after a partial or manual dependency version override — version misalignment between Spring Boot's managed versions and a manually-forced dependency is a common, if often overlooked, root cause.
- Contributing to or evaluating a project that manages dependencies without Spring Boot's parent/BOM mechanism (a non-Boot Spring application) — here, version alignment must be verified manually against the project's own compatibility documentation, since no automatic resolution exists.

## 3. Core concept

```
Dependency resolution WITHOUT Spring Boot's managed versions (manual, error-prone):
    spring-security-oauth2-authorization-server: 1.3.0  <-- picked independently
    spring-security-core:                        5.7.0  <-- picked independently, TOO OLD
    -- MISMATCH: the authorization server version expects Spring Security features
       that don't exist in 5.7.0 -- compiles, but fails at RUNTIME unpredictably

Dependency resolution WITH Spring Boot's managed versions (the recommended path):
    spring-boot-starter-parent: 3.2.0
        -> manages spring-security-oauth2-authorization-server: (a KNOWN-COMPATIBLE version)
        -> manages spring-security-core:                        (a KNOWN-COMPATIBLE version)
        -> EVERY transitive dependency resolved as a TESTED, COHERENT set

The general rule: NEVER manually override an individual Spring Security-related
dependency's version inside a Spring Boot project without a very specific, understood
reason -- doing so opts OUT of the compatibility guarantees Spring Boot's own
dependency management otherwise provides for the entire stack at once.
```

The practical takeaway is almost always "let Spring Boot manage it" rather than "understand every individual version number" — the BOM mechanism exists precisely to make that unnecessary for the overwhelming majority of applications.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting manually picked independent dependency versions which risk a mismatch between spring authorization server and spring security core against spring boots managed dependency version resolution which resolves every transitive dependency as one tested coherent set">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="160" y="42" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Manual version selection</text>
  <text x="160" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">spring-security-oauth2-authorization-server: 1.3.0</text>
  <text x="160" y="83" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">spring-security-core: 5.7.0 (picked separately)</text>
  <text x="160" y="110" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">RISK: version mismatch</text>
  <text x="160" y="128" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">compiles, fails unpredictably at RUNTIME</text>

  <rect x="330" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot managed versions</text>
  <text x="475" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">spring-boot-starter-parent: 3.2.0</text>
  <text x="475" y="83" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; manages EVERY related dependency together</text>
  <text x="475" y="110" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">GUARANTEE: a tested, coherent version set</text>
  <text x="475" y="128" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">for the WHOLE Spring Security stack at once</text>

  <defs></defs>
</svg>

Letting one BOM manage every related dependency's version together is what closes off an entire class of subtle, hard-to-diagnose incompatibility.

## 5. Runnable example

The scenario: model a dependency resolver checking compatibility between manually-specified versions versus a BOM-managed set, growing from a single mismatch detection into a full BOM-driven resolution, then into demonstrating the actual runtime symptom a version mismatch produces (a missing method), motivating why alignment matters beyond just "it compiles."

### Level 1 — Basic

Detect a version mismatch between two related dependencies.

```java
import java.util.*;

public class DependenciesLevel1 {
    record VersionRequirement(String artifact, String minimumCompatibleVersion) {}

    static boolean isCompatible(String actualVersion, String minimumRequired) {
        // simplistic numeric comparison, sufficient for this illustrative model
        return compareVersions(actualVersion, minimumRequired) >= 0;
    }

    static int compareVersions(String v1, String v2) {
        String[] parts1 = v1.split("\\.");
        String[] parts2 = v2.split("\\.");
        for (int i = 0; i < Math.max(parts1.length, parts2.length); i++) {
            int p1 = i < parts1.length ? Integer.parseInt(parts1[i]) : 0;
            int p2 = i < parts2.length ? Integer.parseInt(parts2[i]) : 0;
            if (p1 != p2) return Integer.compare(p1, p2);
        }
        return 0;
    }

    public static void main(String[] args) {
        VersionRequirement requirement = new VersionRequirement("spring-security-core", "6.1.0");

        System.out.println("spring-security-core 6.2.0 compatible: " + isCompatible("6.2.0", requirement.minimumCompatibleVersion()));
        System.out.println("spring-security-core 5.7.0 compatible: " + isCompatible("5.7.0", requirement.minimumCompatibleVersion()));
    }
}
```

**How to run:** save as `DependenciesLevel1.java`, run `java DependenciesLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
spring-security-core 6.2.0 compatible: true
spring-security-core 5.7.0 compatible: false
```

`isCompatible` mirrors the core question every dependency alignment check answers: is the actual resolved version at or above what a given library actually requires — an older `spring-security-core` version, even if it compiles against the authorization server library's API surface, may lack the underlying feature the newer library actually depends on internally.

### Level 2 — Intermediate

Model BOM-style resolution: one parent version managing every related dependency's version together, guaranteeing compatibility across the whole set.

```java
import java.util.*;

public class DependenciesLevel2 {
    static class SpringBootBom {
        private final Map<String, String> managedVersions;
        SpringBootBom(Map<String, String> managedVersions) { this.managedVersions = managedVersions; }

        // mirrors Spring Boot's dependency management resolving a version for an UNVERSIONED dependency
        String resolveVersion(String artifactId) {
            String version = managedVersions.get(artifactId);
            if (version == null) throw new NoSuchElementException("no managed version for: " + artifactId);
            return version;
        }
    }

    public static void main(String[] args) {
        // mirrors what spring-boot-starter-parent:3.2.0 manages internally
        SpringBootBom bom = new SpringBootBom(Map.of(
                "spring-security-oauth2-authorization-server", "1.2.0",
                "spring-security-core", "6.2.0",
                "spring-security-config", "6.2.0",
                "spring-security-web", "6.2.0"));

        List<String> dependenciesNeeded = List.of(
                "spring-security-oauth2-authorization-server", "spring-security-core",
                "spring-security-config", "spring-security-web");

        System.out.println("resolved, GUARANTEED-compatible versions:");
        for (String artifact : dependenciesNeeded) {
            System.out.println("  " + artifact + ": " + bom.resolveVersion(artifact));
        }
    }
}
```

**How to run:** save as `DependenciesLevel2.java`, run `java DependenciesLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
resolved, GUARANTEED-compatible versions:
  spring-security-oauth2-authorization-server: 1.2.0
  spring-security-core: 6.2.0
  spring-security-config: 6.2.0
  spring-security-web: 6.2.0
```

What changed: rather than each dependency's version being an independent choice, `SpringBootBom.resolveVersion` looks up a version from *one* managed set, guaranteeing every related artifact resolves to a version that was tested together — this is precisely why omitting explicit versions on `spring-security-*` dependencies inside a Spring Boot project (letting the parent/BOM resolve them) is the recommended, safer default over specifying each version by hand.

### Level 3 — Advanced

Demonstrate the actual runtime consequence of a version mismatch — a method the authorization server library expects to exist on an older, incompatible `spring-security-core` version simply isn't there, surfacing as a `NoSuchMethodError`-equivalent failure only when that specific code path executes, not at compile time.

```java
import java.util.*;

public class DependenciesLevel3 {
    // mirrors an OLDER spring-security-core version -- missing a method a newer authorization server library needs
    static class OldSpringSecurityCore {
        // does NOT have the method the newer library calls -- simulates an ABSENT API
    }

    static class NewSpringSecurityCore {
        String newFeatureIntroducedInLaterVersion() { return "reactive-context-aware-security-context-holder"; }
    }

    static class NoSuchMethodSimulationException extends RuntimeException {
        NoSuchMethodSimulationException(String message) { super(message); }
    }

    // mirrors spring-security-oauth2-authorization-server calling a method it ASSUMES exists
    static String authorizationServerStartup(Object springSecurityCoreInstance) {
        if (springSecurityCoreInstance instanceof NewSpringSecurityCore newCore) {
            return "startup succeeded, using: " + newCore.newFeatureIntroducedInLaterVersion();
        }
        // the OLD version has no equivalent method -- this is what a REAL mismatch looks like:
        // NOT a compile error (both were on the classpath and "matched" the DECLARED dependency),
        // but a runtime failure the moment the incompatible code path actually executes
        throw new NoSuchMethodSimulationException(
                "NoSuchMethodError (simulated): the resolved spring-security-core version is too old "
                        + "for spring-security-oauth2-authorization-server's actual runtime requirements");
    }

    public static void main(String[] args) {
        System.out.println("--- aligned versions (Spring Boot managed) ---");
        String result = authorizationServerStartup(new NewSpringSecurityCore());
        System.out.println(result);

        System.out.println("--- misaligned versions (manually forced, too old) ---");
        try {
            authorizationServerStartup(new OldSpringSecurityCore());
        } catch (NoSuchMethodSimulationException e) {
            System.out.println("STARTUP FAILED: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `DependenciesLevel3.java`, run `java DependenciesLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- aligned versions (Spring Boot managed) ---
startup succeeded, using: reactive-context-aware-security-context-holder
--- misaligned versions (manually forced, too old) ---
STARTUP FAILED: NoSuchMethodError (simulated): the resolved spring-security-core version is too old for spring-security-oauth2-authorization-server's actual runtime requirements
```

What changed: `authorizationServerStartup` models the real failure mode of a version mismatch — it isn't caught at compile time (both `OldSpringSecurityCore` and `NewSpringSecurityCore` are valid Java objects the code accepts), but fails the moment a code path specific to the newer version's capabilities actually executes, exactly mirroring how a real `NoSuchMethodError` from a mismatched transitive dependency version typically only surfaces once a specific, version-dependent feature is actually exercised at runtime, not during a routine compile-and-test cycle that never happens to reach it.

## 6. Walkthrough

Trace the misaligned-versions failure from Level 3, then the aligned case for contrast, tying both to a real dependency-resolution scenario.

**Step 1 — a developer, working around a dependency conflict, manually forces an older `spring-security-core` version:**
```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-core</artifactId>
    <version>5.7.0</version>  <!-- FORCED, overriding Spring Boot's managed version -->
</dependency>
```
This corresponds to `authorizationServerStartup(new OldSpringSecurityCore())` in Level 3.

**Step 2 — the application compiles successfully.** Both the forced `spring-security-core:5.7.0` and `spring-security-oauth2-authorization-server` (whatever version Spring Boot's parent manages) are present on the classpath, and nothing about compilation itself detects the mismatch — Java's compiler only checks that referenced classes/methods exist *somewhere* on the classpath at compile time, using whatever version happens to be there.

**Step 3 — the application starts, and most functionality appears to work.** Ordinary authentication, most Spring Security features function normally, since they don't depend on whatever specific, newer capability the mismatch actually affects.

**Step 4 — the authorization server's specific configuration path executes**, corresponding to `authorizationServerStartup` being called — and only *here* does the missing method (or class, or behavior) the older `spring-security-core` doesn't provide actually get invoked, throwing what would be a real `NoSuchMethodError` in production.

**Step 5 — contrast: letting Spring Boot's dependency management resolve the version instead.** Removing the manual `<version>` override lets the parent/BOM supply a version tested specifically against the resolved `spring-security-oauth2-authorization-server` version — corresponding to `authorizationServerStartup(new NewSpringSecurityCore())` succeeding cleanly.

```
manual override: spring-security-core FORCED to 5.7.0
        |
        v
compiles fine (compiler doesn't know about the RUNTIME mismatch)
        |
        v
application starts, MOST features work normally
        |
        v
authorization-server-specific code path executes -> NoSuchMethodError (only NOW does the problem surface)

vs.

no override: Spring Boot's BOM resolves spring-security-core to a COMPATIBLE version
        |
        v
EVERYTHING works, including the authorization-server-specific code path
```

## 7. Gotchas & takeaways

> **Gotcha:** a version mismatch of this kind frequently does *not* surface immediately — it can pass code review, compile cleanly, and even work correctly through routine manual testing if the specific, version-dependent code path isn't exercised until later (a rarely-hit configuration branch, an edge case in token introspection). This delayed-failure characteristic is exactly why "just force whatever version resolves the immediate dependency conflict" is a risky habit — the actual consequence may not appear until well after the change that introduced it.

- `spring-security-oauth2-authorization-server` has real minimum version requirements on Spring Security and Spring Framework beneath it — these aren't arbitrary, but reflect genuine API/feature dependencies.
- Spring Boot's dependency management (via `spring-boot-starter-parent` or the BOM) resolves every related Spring Security dependency's version together as a tested, coherent set — this is the reliable default, not something to routinely override.
- Manually forcing an individual dependency's version, without understanding the full compatibility matrix, risks a mismatch that compiles cleanly but fails unpredictably at runtime, only when a specific, version-dependent code path actually executes.
- New projects should start from a current Spring Boot parent version (or Spring Initializr's default) rather than assembling a dependency version matrix by hand.
- When upgrading Spring Boot versions in an existing project, verifying that the transitively-resolved Spring Authorization Server version still supports the application's existing configuration is a reasonable pre-upgrade sanity check, especially across major version boundaries.
