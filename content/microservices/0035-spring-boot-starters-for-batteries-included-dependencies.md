---
card: microservices
gi: 35
slug: spring-boot-starters-for-batteries-included-dependencies
title: "Spring Boot starters for batteries-included dependencies"
---

## 1. What it is

A **Spring Boot starter** is a single dependency (like `spring-boot-starter-web`) that pulls in an entire, pre-verified set of transitive dependencies known to work well together — for `spring-boot-starter-web`, that means an embedded Tomcat, Spring MVC, Jackson (for JSON), and validation libraries, all at compatible versions, from one line in your build file. Instead of a developer manually researching and pinning individual library versions (and hoping they're all mutually compatible), a starter is a "batteries included" bundle: add one line, get a coherent, tested set of capabilities.

## 2. Why & when

Before starters, adding "the ability to build a REST API" to a Java project meant manually selecting an HTTP server library, a JSON library, a validation library, and a web framework, then researching which specific versions of each were known to work correctly together — a genuinely error-prone task, since library compatibility issues are common and often surface only at runtime, not compile time. Starters solve this by having the Spring team curate and test that compatible version set once, centrally, so every service using `spring-boot-starter-web` gets the same known-good combination.

Reach for a starter whenever you need a *capability* (build a web API, talk to a relational database, publish messages to a queue) rather than manually selecting individual libraries — this is the normal, default way to add functionality to a Spring Boot service. Add an individual library directly, bypassing a starter, only when you have a specific, deliberate reason a starter's bundled choices don't fit (needing a different JSON library than Jackson, for instance).

## 3. Core concept

A starter is fundamentally a dependency-resolution shortcut: one declared dependency expands, transitively, into several actual library dependencies.

```
spring-boot-starter-web  (ONE line in your build file)
        |
        +--> spring-webmvc
        +--> embedded Tomcat
        +--> Jackson (JSON)
        +--> spring-boot-starter-validation
        +--> ... (all at compatible, tested versions)
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One starter dependency declaration expands into several individual, version-compatible library dependencies">
  <rect x="240" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web</text>

  <g fill="#1c2430" stroke="#79c0ff" font-family="sans-serif">
    <rect x="30" y="110" width="110" height="35" rx="5"/>
    <text x="85" y="132" fill="#e6edf3" font-size="8" text-anchor="middle">spring-webmvc</text>
    <rect x="160" y="110" width="110" height="35" rx="5"/>
    <text x="215" y="132" fill="#e6edf3" font-size="8" text-anchor="middle">embedded Tomcat</text>
    <rect x="290" y="110" width="90" height="35" rx="5"/>
    <text x="335" y="132" fill="#e6edf3" font-size="8" text-anchor="middle">Jackson</text>
    <rect x="400" y="110" width="110" height="35" rx="5"/>
    <text x="455" y="132" fill="#e6edf3" font-size="8" text-anchor="middle">validation</text>
  </g>
  <line x1="320" y1="75" x2="85" y2="110" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="75" x2="215" y2="110" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="75" x2="335" y2="110" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="75" x2="455" y2="110" stroke="#8b949e" stroke-width="1"/>
</svg>

One starter declaration expands into a curated, tested set of individual library versions.

## 5. Runnable example

Scenario: modeling a starter's dependency-resolution behavior — first showing the manual approach and its version-mismatch risk, then a starter's bundled, pre-verified resolution, then combining multiple starters for a realistic service.

### Level 1 — Basic

```java
// File: ManualDependencySelection.java -- models manually picking individual
// library versions, WITHOUT any curated compatibility guarantee.
import java.util.*;

public class ManualDependencySelection {
    record Library(String name, String version) { }

    static List<Library> manuallySelectedWebDependencies() {
        // a developer researches and picks each version INDEPENDENTLY -- no guarantee they're compatible
        return List.of(
            new Library("spring-webmvc", "6.1.0"),
            new Library("tomcat-embed-core", "9.0.80"), // picked WITHOUT checking compatibility with spring-webmvc 6.1
            new Library("jackson-databind", "2.15.0")
        );
    }

    public static void main(String[] args) {
        for (Library lib : manuallySelectedWebDependencies()) {
            System.out.println(lib.name() + " " + lib.version() + " (compatibility with the others: UNVERIFIED)");
        }
    }
}
```

**How to run:** `javac ManualDependencySelection.java && java ManualDependencySelection` (JDK 17+).

Expected output:
```
spring-webmvc 6.1.0 (compatibility with the others: UNVERIFIED)
tomcat-embed-core 9.0.80 (compatibility with the others: UNVERIFIED)
jackson-databind 2.15.0 (compatibility with the others: UNVERIFIED)
```

Each version was chosen independently, with no single source confirming they actually work together; in reality, Spring 6.1 expects a Tomcat 10.x line, not 9.0.x, which is exactly the kind of subtle, easy-to-miss incompatibility a starter is built to prevent.

### Level 2 — Intermediate

```java
// File: StarterResolution.java -- a starter resolves to a CURATED,
// PRE-VERIFIED set of compatible versions, from ONE declared dependency.
import java.util.*;

public class StarterResolution {
    record Library(String name, String version) { }

    // stands in for Spring Boot's dependency management -- a KNOWN-GOOD, tested combination
    static Map<String, List<Library>> starterCatalog = Map.of(
        "spring-boot-starter-web", List.of(
            new Library("spring-webmvc", "6.1.0"),
            new Library("tomcat-embed-core", "10.1.16"), // the CORRECT, tested match for spring-webmvc 6.1
            new Library("jackson-databind", "2.15.3")
        )
    );

    static List<Library> resolveStarter(String starterName) {
        return starterCatalog.getOrDefault(starterName, List.of());
    }

    public static void main(String[] args) {
        System.out.println("declared: spring-boot-starter-web (ONE line)");
        for (Library lib : resolveStarter("spring-boot-starter-web")) {
            System.out.println("  resolved: " + lib.name() + " " + lib.version() + " (verified compatible by Spring Boot's team)");
        }
    }
}
```

**How to run:** `javac StarterResolution.java && java StarterResolution` (JDK 17+).

Expected output:
```
declared: spring-boot-starter-web (ONE line)
  resolved: spring-webmvc 6.1.0 (verified compatible by Spring Boot's team)
  resolved: tomcat-embed-core 10.1.16 (verified compatible by Spring Boot's team)
  resolved: jackson-databind 2.15.3 (verified compatible by Spring Boot's team)
```

`resolveStarter("spring-boot-starter-web")` returns a version set the Spring Boot team has already tested together — notably `tomcat-embed-core 10.1.16`, the version actually compatible with `spring-webmvc 6.1.0`, unlike Level 1's mismatched `9.0.80` guess.

### Level 3 — Advanced

```java
// File: MultipleStartersForRealService.java -- a realistic service combines
// SEVERAL starters, each resolving its own coherent bundle, all coexisting.
import java.util.*;

public class MultipleStartersForRealService {
    record Library(String name, String version) { }

    static Map<String, List<Library>> starterCatalog = Map.of(
        "spring-boot-starter-web", List.of(
            new Library("spring-webmvc", "6.1.0"), new Library("tomcat-embed-core", "10.1.16"), new Library("jackson-databind", "2.15.3")
        ),
        "spring-boot-starter-data-jpa", List.of(
            new Library("hibernate-core", "6.4.1"), new Library("spring-data-jpa", "3.2.0"), new Library("HikariCP", "5.1.0")
        ),
        "spring-boot-starter-actuator", List.of(
            new Library("micrometer-core", "1.12.0"), new Library("spring-boot-actuator", "3.2.0")
        )
    );

    static List<Library> resolveAll(List<String> declaredStarters) {
        List<Library> resolved = new ArrayList<>();
        for (String starter : declaredStarters) resolved.addAll(starterCatalog.getOrDefault(starter, List.of()));
        return resolved;
    }

    public static void main(String[] args) {
        // OrdersService needs: a REST API, database access, and health/metrics -- THREE capabilities, THREE starters
        List<String> ordersServiceStarters = List.of("spring-boot-starter-web", "spring-boot-starter-data-jpa", "spring-boot-starter-actuator");

        System.out.println("OrdersService declares " + ordersServiceStarters.size() + " starters:");
        for (String starter : ordersServiceStarters) System.out.println("  " + starter);

        List<Library> allResolved = resolveAll(ordersServiceStarters);
        System.out.println("resolving to " + allResolved.size() + " individually-versioned libraries, all pre-verified compatible");
    }
}
```

**How to run:** `javac MultipleStartersForRealService.java && java MultipleStartersForRealService` (JDK 17+).

Expected output:
```
OrdersService declares 3 starters:
  spring-boot-starter-web
  spring-boot-starter-data-jpa
  spring-boot-starter-actuator
resolving to 8 individually-versioned libraries, all pre-verified compatible
```

The production-flavored payoff: `OrdersService` declares just 3 starter dependencies, matching its 3 actual needs (REST API, database access, observability), and `resolveAll` expands those into 8 individually-versioned libraries — each bundle internally coherent, and all 8 chosen from version sets the Spring Boot team has tested to work together, without `OrdersService`'s team needing to research or pin a single one of those 8 versions by hand.

## 6. Walkthrough

1. `resolveAll(ordersServiceStarters)` iterates over the three declared starter names: `"spring-boot-starter-web"`, `"spring-boot-starter-data-jpa"`, `"spring-boot-starter-actuator"`.
2. For each one, it looks up `starterCatalog.getOrDefault(starter, List.of())`, retrieving that starter's own pre-defined, coherent list of `Library` records, and appends all of them to the growing `resolved` list.
3. `spring-boot-starter-web` contributes 3 libraries, `spring-boot-starter-data-jpa` contributes 3 more, and `spring-boot-starter-actuator` contributes 2 — for a total of `3 + 3 + 2 = 8` libraries in the final `resolved` list.
4. The final print confirms `allResolved.size()` is `8` — a concrete number showing exactly how much manual version research and compatibility-checking was avoided by declaring 3 starters instead of 8 individual library dependencies.
5. Crucially, each of the 8 resolved libraries came from its own starter's already-tested bundle — `hibernate-core` and `HikariCP`, for instance, were chosen together specifically because they're known to work well as a pair within `spring-boot-starter-data-jpa`, not picked independently the way `ManualDependencySelection` picked its libraries in Level 1.

```
declared starters:  [web, data-jpa, actuator]  (3 lines in a build file)
        |
resolveAll expands each starter's own bundle:
  web       -> 3 libraries (all mutually compatible)
  data-jpa  -> 3 libraries (all mutually compatible)
  actuator  -> 2 libraries (all mutually compatible)
        |
total: 8 individually-versioned libraries, ZERO manual version research needed
```

## 7. Gotchas & takeaways

> **Gotcha:** a starter's curated version set is chosen for the *starter's own internal* compatibility, not automatically guaranteed compatible with every other library you might separately add outside any starter. Manually adding an unrelated library alongside several starters can still reintroduce the exact version-conflict risk starters are designed to eliminate — check compatibility explicitly whenever adding a dependency outside the starter ecosystem.

- A Spring Boot starter is a single declared dependency that expands into a curated, pre-tested set of individual library versions known to work correctly together.
- Starters exist specifically to eliminate the error-prone manual work of researching and pinning individually compatible library versions — a task that's easy to get subtly wrong, especially across many services created by different engineers.
- Combine multiple starters freely for a service needing several distinct capabilities (web API, database access, observability) — each starter's bundle stays internally coherent regardless of how many other starters are also declared.
- Adding a library outside the starter ecosystem alongside your starters bypasses their compatibility guarantee for that specific library — verify compatibility manually in that case, since starters can't protect against a dependency they don't know about.
