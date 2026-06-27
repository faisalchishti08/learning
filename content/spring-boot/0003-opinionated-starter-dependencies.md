---
card: spring-boot
gi: 3
slug: opinionated-starter-dependencies
title: Opinionated 'starter' dependencies
---

## 1. What it is

A **Spring Boot starter** is a single Maven/Gradle dependency that pulls in a complete, pre-tested set of libraries for a capability. Instead of manually listing ten compatible JARs, you add one starter and get them all at the right versions.

Examples:

| Starter | What it includes |
|---|---|
| `spring-boot-starter-web` | Spring MVC, embedded Tomcat, Jackson JSON, validation |
| `spring-boot-starter-data-jpa` | Spring Data JPA, Hibernate ORM, HikariCP connection pool |
| `spring-boot-starter-security` | Spring Security core, web security filters, authentication support |
| `spring-boot-starter-test` | JUnit 5, Mockito, AssertJ, Spring Test, Testcontainers support |
| `spring-boot-starter-actuator` | Health checks, metrics, HTTP endpoint exposure |

The name pattern is always `spring-boot-starter-{feature}`. Third-party libraries ship their own starters too (e.g., `mybatis-spring-boot-starter`).

## 2. Why & when

**Before starters**, adding JPA to a Spring project meant hunting for compatible versions of Spring ORM, Spring TX, Hibernate core, Hibernate validator, HikariCP or c3p0, and SLF4J. Get one version wrong and you'd see cryptic `NoSuchMethodError` at runtime.

Starters solve two problems simultaneously:

1. **Dependency compatibility** — Spring Boot's release train tests hundreds of library combinations. `spring-boot-starter-data-jpa` 3.3.x guarantees Hibernate 6.x + HikariCP 5.x + Spring Data 3.3.x all working together.
2. **Discoverability** — Instead of knowing ten artifact IDs, you know one. The starter's transitive dependencies tell you what's included.

Use starters **every time** you add a Spring Boot capability. Even when you want only one library from a bundle (e.g., just Jackson), use the appropriate starter so you stay within the tested compatibility matrix.

## 3. Core concept

A starter is simply a near-empty POM (Maven) or a metadata-only module with carefully chosen dependencies declared as `compile`/`implementation` scope. There's almost no code in a starter — it's a dependency recipe.

The key mechanism is **spring-boot-starter-parent** (or the BOM it imports, `spring-boot-dependencies`). This parent POM declares `<dependencyManagement>` blocks pinning hundreds of library versions. When you add `spring-boot-starter-web`, you get:

```
spring-boot-starter-web
  └─ spring-boot-starter              (core Spring Boot)
  │    └─ spring-boot
  │    └─ spring-boot-autoconfigure
  │    └─ spring-boot-starter-logging (Logback)
  │    └─ spring-core
  ├─ spring-boot-starter-tomcat       (embedded Tomcat 10)
  ├─ spring-web                       (Spring MVC)
  ├─ spring-webmvc
  └─ jackson-databind                 (JSON)
```

All at versions that are tested to work together — you never specify a version number for any of them.

Exclusions are supported when you need an alternative: swap Tomcat for Jetty by excluding `spring-boot-starter-tomcat` and adding `spring-boot-starter-jetty`.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Starter dependency tree showing spring-boot-starter-web pulling in Tomcat, Spring MVC, and Jackson">
  <!-- Root starter -->
  <rect x="230" y="20" width="200" height="38" rx="7" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="44" fill="#1c2430" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web</text>

  <!-- Connecting lines down -->
  <line x1="220" y1="76" x2="220" y2="96" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="330" y1="58" x2="330" y2="96" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="76" x2="440" y2="96" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="140" y1="76" x2="140" y2="96" stroke="#8b949e" stroke-width="1.5"/>
  <!-- Horizontal line -->
  <line x1="140" y1="76" x2="440" y2="76" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="330" y1="58" x2="330" y2="76" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Child boxes -->
  <rect x="20" y="96" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="118" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">spring-boot-starter</text>

  <rect x="200" y="96" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="118" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">starter-tomcat</text>

  <rect x="360" y="96" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="420" y="118" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">spring-webmvc</text>

  <rect x="500" y="96" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="118" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">jackson-databind</text>

  <!-- Grandchild rows -->
  <line x1="100" y1="130" x2="100" y2="155" stroke="#8b949e" stroke-width="1"/>
  <rect x="20" y="155" width="160" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot + logback + slf4j</text>

  <line x1="270" y1="130" x2="270" y2="155" stroke="#8b949e" stroke-width="1"/>
  <rect x="200" y="155" width="140" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="270" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">tomcat-embed-core</text>

  <!-- Version badge area -->
  <rect x="160" y="220" width="340" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="237" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">spring-boot-dependencies BOM</text>
  <text x="330" y="252" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">pins ALL versions — you specify none</text>
</svg>

One `spring-boot-starter-web` entry in your POM pulls the entire tested tree; `spring-boot-dependencies` pins every version.

## 5. Runnable example

```java
// File: StarterDemo.java
// Pure Java 17 demo showing the "curated bundle" concept.
// Run: java StarterDemo.java

import java.util.List;
import java.util.Map;

public class StarterDemo {

    // Simulates what a starter does: bundles a fixed set of compatible versions
    record Library(String artifact, String version) {}

    static List<Library> webStarterDependencies() {
        // These are the actual transitive deps of spring-boot-starter-web 3.3.x
        return List.of(
            new Library("spring-boot",              "3.3.4"),
            new Library("spring-boot-autoconfigure","3.3.4"),
            new Library("spring-webmvc",            "6.1.12"),
            new Library("tomcat-embed-core",        "10.1.28"),
            new Library("jackson-databind",         "2.17.2"),
            new Library("logback-classic",          "1.5.7")
        );
    }

    public static void main(String[] args) {
        System.out.println("You added ONE dependency: spring-boot-starter-web");
        System.out.println("You get THESE pre-tested libraries:\n");

        var deps = webStarterDependencies();
        int maxLen = deps.stream().mapToInt(l -> l.artifact().length()).max().orElse(0);
        for (var lib : deps) {
            System.out.printf("  %-" + maxLen + "s  %s%n", lib.artifact(), lib.version());
        }

        System.out.println();
        System.out.println("Total: " + deps.size() + " libraries, 0 version conflicts.");
        System.out.println("Version you had to specify in pom.xml: 0");
    }
}
```

**How to run:** `java StarterDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
You added ONE dependency: spring-boot-starter-web
You get THESE pre-tested libraries:

  spring-boot               3.3.4
  spring-boot-autoconfigure 3.3.4
  spring-webmvc             6.1.12
  tomcat-embed-core         10.1.28
  jackson-databind          2.17.2
  logback-classic           1.5.7

Total: 6 libraries, 0 version conflicts.
Version you had to specify in pom.xml: 0
```

## 6. Walkthrough

- **`record Library`** — Java 16+ records are a concise way to model immutable data. Each `Library` has an `artifact` and a `version`. This mimics a Maven dependency entry.
- **`webStarterDependencies()`** — returns the real transitive dependencies of `spring-boot-starter-web` 3.3.4. In a real Maven build, you'd only write `<artifactId>spring-boot-starter-web</artifactId>` and Maven resolves this entire list.
- **`maxLen` calculation** — uses streams and `mapToInt` to find the longest artifact name so the output columns line up. A minor aesthetic detail worth knowing: `String.format` with `%-Ns` left-justifies a string in N characters.
- **`0 version conflicts`** — the key benefit. The `spring-boot-dependencies` BOM pins all these to versions that are tested together. You can't accidentally bring in `jackson-databind 2.14` alongside a Spring 6 artifact that needs 2.17+.

The takeaway: a starter is a recipe. The ingredients are the transitive JARs. The chef (Spring Boot's release team) tested the recipe end-to-end.

## 7. Gotchas & takeaways

> **Starters use `compile` scope, not `optional`.** Everything in a starter lands on your runtime classpath. If you add `spring-boot-starter-web` but only want the web framework without embedded Tomcat (e.g., you're deploying to an external server), explicitly exclude `spring-boot-starter-tomcat` and add `javax.servlet-api` with `provided` scope.

> **Don't mix Spring Boot versions.** If you add a Spring Boot 3.x starter alongside a library that requires Spring 5.x APIs, you'll get `NoClassDefFoundError` or `IncompatibleClassChangeError` at runtime. Always inherit from `spring-boot-starter-parent` or import `spring-boot-dependencies` BOM to let Spring Boot manage all Spring library versions.

- One starter = one capability = dozens of compatible libraries — you write one line.
- Version numbers for any library in the Spring Boot ecosystem are managed by the BOM; omit them.
- Starters are composable: add `spring-boot-starter-web` + `spring-boot-starter-data-jpa` + `spring-boot-starter-security` in any combination.
- To swap Tomcat for Jetty: exclude `spring-boot-starter-tomcat`, add `spring-boot-starter-jetty`.
- `mvn dependency:tree` or `./gradlew dependencies` reveals exactly which JARs a starter brought in.
