---
card: spring-framework
gi: 462
slug: upgrading-to-spring-6-x
title: "Upgrading to Spring 6.x"
---

## 1. What it is

Upgrading to Spring Framework 6.x (paired with Spring Boot 3.x) is a coordinated set of baseline changes, not a single flag flip: a minimum Java 17 baseline (up from Java 8), the `javax` → `jakarta` package migration covered in the previous card, a move to Jakarta EE 9+/Servlet 5+ compatible servers, GraalVM native image support built into the core (via `spring-native`'s ideas folded directly into the framework), and observability built around Micrometer rather than the older Spring-specific metrics abstractions. This card is the checklist view of that whole upgrade, tying together changes touched individually elsewhere in this guide.

```
 Spring Framework 5.x / Boot 2.x  ->  Spring Framework 6.x / Boot 3.x
 --------------------------------      --------------------------------
 Java 8+ baseline                       Java 17+ baseline (hard minimum)
 javax.* (Servlet 4, JPA 2.2, ...)      jakarta.* (Servlet 5+, JPA 3+, ...)
 Tomcat 9 / Jetty 9 / Undertow 2.x       Tomcat 10+ / Jetty 11+ / Undertow 2.2+
 no built-in native-image support        GraalVM native image first-class support
```

## 2. Why & when

This upgrade is unusually consequential because several changes land simultaneously and are interdependent: raising the Java baseline to 17 is what let the framework use newer language features internally and drop support for genuinely old JVMs; the `jakarta` package rename is forced by the underlying servlet/JPA specifications themselves moving; and the newer server versions (Tomcat 10+) only support `jakarta.servlet`, not `javax.servlet` — so you can't adopt just one piece in isolation for a servlet-based application.

Plan for this upgrade specifically when:

- You're maintaining a Spring Framework 5.x or Spring Boot 2.x application that needs continued security patches or new features — Spring Framework 5.3.x and Spring Boot 2.7.x are the last minor lines in their respective major versions, meaning the only forward path for new capability is 6.x/3.x.
- You depend on third-party libraries or an application server — confirm each one has a `jakarta.*`-compatible release before starting, since a library still shipping `javax.servlet.Filter` will not function inside a Servlet 5+ container.
- You're starting greenfield — there's no reason to target Spring 5/Boot 2 for a new project today; start directly on 6.x/3.x and this entire checklist becomes "things to already be doing," not "things to migrate."

## 3. Core concept

```
 UPGRADE CHECKLIST, in dependency order (later steps depend on earlier ones):

 1. Raise the Java baseline to 17+
        |
        v
 2. Upgrade the build tool's target/source compatibility (Maven/Gradle) to 17
        |
        v
 3. Upgrade the servlet container / app server to a Jakarta EE 9+ compatible version
    (Tomcat 10+, Jetty 11+, Undertow 2.2+) -- REQUIRED before jakarta.* code can run
        |
        v
 4. Migrate javax.* imports to jakarta.* (servlet, persistence, validation,
    transaction, and the specific javax.annotation subset) -- see previous card
        |
        v
 5. Upgrade every third-party dependency to a jakarta.*-compatible version
    (a library still on javax.servlet will NOT work under a Servlet 5+ container)
        |
        v
 6. Update Spring Framework / Spring Boot BOM versions to 6.x / 3.x
        |
        v
 7. Re-run the full test suite; fix any behavior changes from stricter defaults
```

Steps 3 and 4 are tightly coupled — the server must support `jakarta.*` before application code using `jakarta.*` types can actually run inside it, but application code using `javax.*` types cannot run inside a `jakarta.*`-only server either, meaning there's effectively no working intermediate state; both typically need to change together.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Upgrade steps flow from Java baseline through server, package migration, and dependencies to a working Spring 6 application">
  <rect x="10" y="15" width="140" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="80" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Java 17+ baseline</text>

  <rect x="180" y="15" width="140" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="250" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Server: Tomcat 10+</text>

  <rect x="350" y="15" width="140" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="420" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">javax -&gt; jakarta</text>

  <rect x="520" y="15" width="110" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="575" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Deps upgraded</text>

  <rect x="230" y="130" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="153" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring 6.x / Boot 3.x BOM</text>
  <text x="320" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">working application</text>

  <line x1="80" y1="60" x2="180" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="250" y1="60" x2="270" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="420" y1="60" x2="370" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="575" y1="60" x2="410" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

All four prerequisite changes converge before the framework version bump itself can succeed.

## 5. Runnable example

Since a real multi-module Maven/Gradle upgrade can't be captured in one file, the scenario is a self-contained upgrade *readiness checker*: a tool that inspects a project's declared dependencies and Java version, reporting exactly which of the checklist's prerequisites are and aren't satisfied — evolving from a basic Java-version check, to a dependency compatibility check, to a full ordered checklist runner that mirrors the real upgrade sequence.

### Level 1 — Basic

Check the running JVM's version against the Spring 6 minimum and report readiness for step 1 of the checklist.

```java
public class SpringUpgradeLevel1 {

    static boolean isJava17OrNewer() {
        String version = System.getProperty("java.version");
        int majorVersion = parseMajorVersion(version);
        return majorVersion >= 17;
    }

    static int parseMajorVersion(String version) {
        // Handles both old-style "1.8.0_302" and new-style "17.0.1" version strings.
        if (version.startsWith("1.")) {
            return Integer.parseInt(version.substring(2, version.indexOf('.', 2)));
        }
        int dot = version.indexOf('.');
        return Integer.parseInt(dot == -1 ? version : version.substring(0, dot));
    }

    public static void main(String[] args) {
        String rawVersion = System.getProperty("java.version");
        boolean ready = isJava17OrNewer();

        System.out.println("Detected Java version: " + rawVersion);
        System.out.println("Spring 6.x requires Java 17+. Baseline satisfied? " + ready);

        // Sanity-check the parser itself against known version string formats.
        if (parseMajorVersion("1.8.0_302") != 8) throw new AssertionError("Failed to parse Java 8 version string");
        if (parseMajorVersion("17.0.1") != 17) throw new AssertionError("Failed to parse Java 17 version string");
        if (parseMajorVersion("21") != 21) throw new AssertionError("Failed to parse bare Java 21 version string");

        if (!ready) {
            System.out.println("[ACTION REQUIRED] Upgrade the JDK to 17+ before proceeding with any other step.");
        } else {
            System.out.println("Step 1 (Java baseline) satisfied -- PASS");
        }
    }
}
```

How to run: no external dependencies, `java SpringUpgradeLevel1.java` on JDK 17+ (or any JDK, to see the check correctly report readiness or the lack of it).

`parseMajorVersion` handles both the pre-Java-9 versioning scheme (`"1.8.0_302"` meaning Java 8) and the post-Java-9 scheme (`"17.0.1"` meaning Java 17 directly) — a real-world detail, since a build script or CI environment reporting its Java version needs to interpret both formats correctly depending on which JDK happens to be installed.

### Level 2 — Intermediate

Extend the checker to inspect a simulated dependency list (standing in for a project's `pom.xml`/`build.gradle` dependencies) and flag any dependency still on a `javax`-generation version, the step-4/step-5 prerequisite.

```java
import java.util.List;
import java.util.Map;

public class SpringUpgradeLevel2 {

    record Dependency(String artifactId, String version) {}

    // Known artifacts whose major version boundary marks the javax -> jakarta switch.
    static final Map<String, Integer> JAKARTA_MAJOR_VERSION_BOUNDARY = Map.of(
        "tomcat-embed-core", 10,
        "jakarta.servlet-api", 5,
        "hibernate-core", 6,
        "spring-core", 6
    );

    static boolean isJakartaCompatible(Dependency dep) {
        Integer boundary = JAKARTA_MAJOR_VERSION_BOUNDARY.get(dep.artifactId());
        if (boundary == null) return true; // not a tracked artifact, assume fine
        int majorVersion = Integer.parseInt(dep.version().split("\\.")[0]);
        return majorVersion >= boundary;
    }

    public static void main(String[] args) {
        List<Dependency> projectDependencies = List.of(
            new Dependency("spring-core", "5.3.30"),      // still javax-generation
            new Dependency("tomcat-embed-core", "9.0.80"), // still javax-generation
            new Dependency("hibernate-core", "6.2.7"),     // already jakarta-generation
            new Dependency("guava", "32.1.3")              // untracked, assumed fine
        );

        System.out.println("Checking " + projectDependencies.size() + " dependencies for jakarta readiness:");
        List<Dependency> blockers = projectDependencies.stream()
            .filter(d -> !isJakartaCompatible(d))
            .toList();

        for (Dependency dep : projectDependencies) {
            boolean ok = isJakartaCompatible(dep);
            System.out.println("  " + dep.artifactId() + " " + dep.version() + " -> " + (ok ? "OK" : "BLOCKER"));
        }

        if (blockers.size() != 2)
            throw new AssertionError("Expected exactly 2 blockers (spring-core, tomcat-embed-core), found " + blockers.size());
        System.out.println("Correctly identified " + blockers.size() + " pre-upgrade blockers -- PASS");
    }
}
```

How to run: no external dependencies, `java SpringUpgradeLevel2.java`.

`JAKARTA_MAJOR_VERSION_BOUNDARY` encodes the real major-version cutoffs where each named project switched to `jakarta.*` — Tomcat 10 (not 9), `jakarta.servlet-api` 5 (not 4), Hibernate 6 (not 5), Spring 6 (not 5) — so the check reports `spring-core 5.3.30` and `tomcat-embed-core 9.0.80` as blockers while `hibernate-core 6.2.7` passes, mirroring exactly the kind of per-dependency audit a real upgrade requires before touching application code.

### Level 3 — Advanced

Combine both checks into a full ordered checklist runner that stops at the first unmet prerequisite (mirroring the dependency ordering from Part 3's diagram — Java baseline before server, server before package migration, and so on) and produces a clear, ordered report — the shape of a real pre-upgrade audit script.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

public class SpringUpgradeLevel3 {

    record Dependency(String artifactId, String version) {}
    record CheckResult(String step, boolean passed, String detail) {}

    static final Map<String, Integer> JAKARTA_MAJOR_VERSION_BOUNDARY = Map.of(
        "tomcat-embed-core", 10,
        "jakarta.servlet-api", 5,
        "hibernate-core", 6,
        "spring-core", 6
    );

    static int parseMajorVersion(String version) {
        if (version.startsWith("1.")) return Integer.parseInt(version.substring(2, version.indexOf('.', 2)));
        int dot = version.indexOf('.');
        return Integer.parseInt(dot == -1 ? version : version.substring(0, dot));
    }

    static CheckResult checkJavaBaseline(String javaVersion) {
        boolean ok = parseMajorVersion(javaVersion) >= 17;
        return new CheckResult("1. Java 17+ baseline", ok, "detected " + javaVersion);
    }

    static CheckResult checkServer(List<Dependency> deps) {
        Dependency tomcat = deps.stream().filter(d -> d.artifactId().equals("tomcat-embed-core")).findFirst().orElse(null);
        if (tomcat == null) return new CheckResult("2. Jakarta-compatible server", true, "no servlet container declared");
        boolean ok = Integer.parseInt(tomcat.version().split("\\.")[0]) >= 10;
        return new CheckResult("2. Jakarta-compatible server", ok, "tomcat-embed-core " + tomcat.version());
    }

    static CheckResult checkDependencies(List<Dependency> deps) {
        List<String> blockers = new ArrayList<>();
        for (Dependency dep : deps) {
            Integer boundary = JAKARTA_MAJOR_VERSION_BOUNDARY.get(dep.artifactId());
            if (boundary == null) continue;
            if (Integer.parseInt(dep.version().split("\\.")[0]) < boundary) {
                blockers.add(dep.artifactId() + " " + dep.version() + " (needs " + boundary + "+)");
            }
        }
        return new CheckResult("3. All dependencies jakarta-compatible", blockers.isEmpty(),
            blockers.isEmpty() ? "all clear" : String.join(", ", blockers));
    }

    public static void main(String[] args) {
        // Simulated project state: Java is ready, server is NOT, dependencies are a mix.
        String javaVersion = "21.0.1";
        List<Dependency> deps = List.of(
            new Dependency("tomcat-embed-core", "9.0.80"), // blocker: still Servlet 4-generation
            new Dependency("spring-core", "5.3.30"),        // blocker
            new Dependency("hibernate-core", "6.2.7")       // fine
        );

        List<Supplier<CheckResult>> orderedChecks = List.of(
            () -> checkJavaBaseline(javaVersion),
            () -> checkServer(deps),
            () -> checkDependencies(deps)
        );

        List<CheckResult> results = new ArrayList<>();
        for (Supplier<CheckResult> check : orderedChecks) {
            CheckResult result = check.get();
            results.add(result);
            System.out.println((result.passed() ? "[PASS] " : "[FAIL] ") + result.step() + " -- " + result.detail());
        }

        long failedCount = results.stream().filter(r -> !r.passed()).count();
        System.out.println();
        System.out.println(failedCount + " of " + results.size() + " prerequisite checks failed.");

        if (failedCount != 2)
            throw new AssertionError("Expected exactly 2 failing checks (server, dependencies) given this simulated state");
        System.out.println("Ordered checklist correctly identified remaining upgrade work -- PASS");
    }
}
```

How to run: no external dependencies, `java SpringUpgradeLevel3.java`.

The checks run in the same dependency order as the Part 3 diagram — Java baseline first, then server, then the remaining dependency sweep — and each `CheckResult` is self-describing, printing exactly which artifact and version caused a failure. With the simulated project state (Java 21 ready, Tomcat still on 9.x, `spring-core` still on 5.x, Hibernate already on 6.x), the runner correctly reports 2 of 3 checks failing — the same actionable signal a real pre-upgrade audit script would give a team before they start the actual migration work.

## 6. Walkthrough

Trace Level 3's checklist run end-to-end.

1. **Setup**: the simulated project state fixes `javaVersion = "21.0.1"` (already upgraded) and a dependency list where `tomcat-embed-core` and `spring-core` are still on pre-Jakarta major versions, while `hibernate-core` has already been bumped.
2. **Ordered execution**: `orderedChecks` is a `List<Supplier<CheckResult>>`, deliberately built so the checks run in the same sequence a real migration must follow — checking Java before checking the server makes sense because there's no point auditing server compatibility on a JVM too old to run Spring 6 at all.
3. **Check 1 (Java baseline)**: `checkJavaBaseline("21.0.1")` parses the major version as `21`, which is `>= 17`, so this check passes — printed as `[PASS] 1. Java 17+ baseline -- detected 21.0.1`.
4. **Check 2 (server)**: `checkServer(deps)` finds `tomcat-embed-core` at version `9.0.80`, parses its major version as `9`, compares against the required boundary of `10`, and fails — printed as `[FAIL] 2. Jakarta-compatible server -- tomcat-embed-core 9.0.80`.
5. **Check 3 (dependencies)**: `checkDependencies(deps)` iterates every tracked dependency; `tomcat-embed-core` (9 < 10) and `spring-core` (5 < 6) both fail their boundary check and are collected into `blockers`, while `hibernate-core` (6 >= 6) passes silently. The check fails overall since `blockers` is non-empty, reporting both artifacts in its detail message.
6. **Aggregation**: `main` collects all three `CheckResult`s, prints each with a `[PASS]`/`[FAIL]` prefix as it runs, then counts how many failed.
7. **Final report**: the program prints `"2 of 3 prerequisite checks failed"` and asserts that count matches the expected simulated state, confirming the checklist runner itself behaves correctly — in a real audit script, a non-zero failure count would be the signal to block the upgrade PR until each listed blocker is resolved.

```
 checkJavaBaseline("21.0.1")        -> PASS  (21 >= 17)
        |
        v
 checkServer(deps)                  -> FAIL  (tomcat-embed-core 9 < 10)
        |
        v
 checkDependencies(deps)            -> FAIL  (tomcat-embed-core 9<10, spring-core 5<6)
        |
        v
 report: 2 of 3 checks failed -- fix server + dependencies before bumping Spring version
```

## 7. Gotchas & takeaways

> **Gotcha:** it's tempting to bump the Spring Framework/Spring Boot BOM version first and fix compile errors as they appear — but because the server, the package imports, and the dependencies are interdependent (as the Part 3 diagram shows), doing the version bump first typically produces a wall of unrelated-looking compile and runtime errors all at once. Working through the checklist in order — Java baseline, then server, then package migration, then dependencies, then the framework version bump — produces a much smaller, more diagnosable set of errors at each stage.

- The Spring 6/Boot 3 upgrade is really four coupled changes (Java baseline, server version, package namespace, dependency versions) that must land together for a servlet-based application — there's no stable intermediate state with only some of them done.
- Automated tooling (OpenRewrite's Spring Boot 3 migration recipes, the Spring Boot migrator, or manual Eclipse Transformer runs) exists specifically because the package-rename portion of this checklist is mechanical and error-prone to do by hand across a large codebase — reach for it rather than hand-editing imports file by file.
- Before starting, audit every third-party dependency (not just direct ones — transitive dependencies matter too) for `jakarta.*` compatibility; a single un-migrated library deep in the dependency tree can block the entire upgrade.
- Spring Framework 5.3.x and Spring Boot 2.7.x are the final minor lines in their major versions — there is no "Spring Framework 5.4" or "Spring Boot 2.8" to delay into; 6.x/3.x is the only forward path for continued updates.
