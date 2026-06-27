---
card: spring-boot
gi: 20
slug: dependency-management-the-spring-boot-bom
title: Dependency management & the Spring Boot BOM
---

## 1. What it is

**Dependency management** in Spring Boot means you declare which *capabilities* you need (e.g., web, JPA, security) without specifying library version numbers. A single **BOM** (Bill of Materials) — `spring-boot-dependencies` — pins compatible versions for every library in the Spring ecosystem.

BOM stands for *Bill of Materials*, borrowed from manufacturing: a list of every component needed for a product with exact specifications. In Maven and Gradle, a BOM is a special POM file whose sole content is a `<dependencyManagement>` block pinning hundreds of `groupId:artifactId:version` triples.

When you import the Spring Boot BOM:
- `spring-boot-starter-web` resolves to a specific, tested version automatically.
- `jackson-databind`, `hibernate-core`, `HikariCP`, `Micrometer`, and ~400 other libraries also resolve automatically.
- You never write a `<version>` tag for anything in the Spring ecosystem.

## 2. Why & when

**The dependency hell problem:** Java projects can have hundreds of transitive dependencies. Library A requires `jackson 2.14`; library B requires `jackson 2.17`. Maven picks one, and if it's the wrong one, you get `NoSuchMethodError` at runtime — not at compile time, not on startup, but when the code path that uses the mismatched API finally executes.

Spring Boot's BOM solves this by being a *pre-tested compatibility matrix*. The Spring team:
1. Picks a set of library versions that work together.
2. Tests them extensively.
3. Publishes the results as the BOM.

You import the BOM once. All `spring-boot-starter-*` dependencies use BOM-managed versions. Third-party libraries that Spring Boot knows about (Flyway, Liquibase, Testcontainers, etc.) are also in the BOM.

Always use the BOM in Spring Boot projects. The only alternative — manually pinning every version — works but requires constant maintenance and deep knowledge of library compatibility.

## 3. Core concept

The BOM is a POM with type `pom`. In Maven, import it in `<dependencyManagement>`:

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-dependencies</artifactId>
      <version>3.3.4</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

After this import, add any Spring Boot starter without a `<version>`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <!-- no <version> -->
</dependency>
```

**How version resolution works:**
1. Maven sees `spring-boot-starter-web` with no version.
2. It looks in `<dependencyManagement>` sections, including imported BOMs.
3. The BOM says `spring-boot-starter-web:3.3.4` — Maven uses that.
4. `spring-boot-starter-web` depends on `spring-webmvc`; the BOM says `spring-webmvc:6.1.12` — Maven uses that too.

The BOM wins only for un-versioned dependencies. If you explicitly write `<version>2.14.0</version>` for Jackson, your explicit version overrides the BOM — useful when you need a newer patch but risky for compatibility.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BOM resolution diagram showing your POM requesting spring-boot-starter-web without a version and the BOM providing the correct version">
  <!-- Your POM -->
  <rect x="20" y="80" width="200" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="104" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Your pom.xml</text>
  <text x="120" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web</text>
  <text x="120" y="138" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;!-- no version! --&gt;</text>
  <text x="120" y="152" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">imports spring-boot-dependencies</text>

  <!-- Arrow to BOM -->
  <line x1="220" y1="120" x2="260" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#bomArr)"/>
  <text x="238" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lookup</text>

  <!-- BOM -->
  <rect x="260" y="40" width="200" height="160" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="360" y="64" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-dependencies</text>
  <text x="360" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(BOM v3.3.4)</text>
  <rect x="276" y="90" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">starter-web: 3.3.4</text>
  <rect x="276" y="116" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="131" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">spring-webmvc: 6.1.12</text>
  <rect x="276" y="142" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="157" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">jackson-databind: 2.17.2</text>
  <rect x="276" y="168" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">… 400+ more entries</text>

  <!-- Arrow to resolved -->
  <line x1="460" y1="120" x2="500" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#bomArr2)"/>
  <text x="480" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolved</text>

  <!-- Resolved box -->
  <rect x="500" y="80" width="148" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="574" y="104" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Resolved</text>
  <text x="574" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">starter-web 3.3.4</text>
  <text x="574" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">webmvc 6.1.12</text>
  <text x="574" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jackson 2.17.2</text>

  <defs>
    <marker id="bomArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="bomArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

You declare the capability; the BOM supplies the version. The BOM is the single source of truth for the entire dependency graph.

## 5. Runnable example

```java
// File: BomDemo.java
// Shows how a BOM eliminates version conflicts through a pre-tested compatibility matrix.
// Run: java BomDemo.java

import java.util.*;

public class BomDemo {

    // Simulates a BOM entry: groupId:artifactId → version
    record BomEntry(String groupId, String artifactId, String version) {
        String key() { return groupId + ":" + artifactId; }
    }

    // Simulates the spring-boot-dependencies BOM (subset)
    static final List<BomEntry> SPRING_BOOT_BOM_3_3_4 = List.of(
        new BomEntry("org.springframework.boot", "spring-boot-starter-web",      "3.3.4"),
        new BomEntry("org.springframework",       "spring-webmvc",               "6.1.12"),
        new BomEntry("com.fasterxml.jackson.core","jackson-databind",             "2.17.2"),
        new BomEntry("com.zaxxer",               "HikariCP",                     "5.1.0"),
        new BomEntry("org.hibernate.orm",        "hibernate-core",               "6.5.2.Final"),
        new BomEntry("org.apache.tomcat.embed",  "tomcat-embed-core",            "10.1.28"),
        new BomEntry("org.flywaydb",             "flyway-core",                  "10.15.2"),
        new BomEntry("io.micrometer",            "micrometer-core",              "1.13.4")
    );

    static Optional<String> resolveVersion(String groupId, String artifactId) {
        return SPRING_BOOT_BOM_3_3_4.stream()
            .filter(e -> e.groupId().equals(groupId) && e.artifactId().equals(artifactId))
            .map(BomEntry::version)
            .findFirst();
    }

    public static void main(String[] args) {
        System.out.println("=== Dependency resolution via Spring Boot BOM 3.3.4 ===\n");

        var requested = List.of(
            new String[]{"org.springframework.boot", "spring-boot-starter-web"},
            new String[]{"com.fasterxml.jackson.core", "jackson-databind"},
            new String[]{"org.hibernate.orm", "hibernate-core"},
            new String[]{"org.apache.tomcat.embed", "tomcat-embed-core"},
            new String[]{"io.micrometer", "micrometer-core"},
            new String[]{"com.example", "my-custom-library"}  // not in BOM
        );

        System.out.printf("%-42s %-24s %s%n", "Dependency", "BOM Version", "Status");
        System.out.println("-".repeat(80));

        for (var dep : requested) {
            var ver = resolveVersion(dep[0], dep[1]);
            System.out.printf("%-42s %-24s %s%n",
                dep[0] + ":" + dep[1],
                ver.orElse("(not managed)"),
                ver.isPresent() ? "✓ no <version> needed" : "⚠ must specify version manually");
        }

        System.out.println();
        System.out.println("Libraries in Spring Boot 3.3.4 BOM: 400+");
        System.out.println("Version conflicts caused by BOM libraries: 0");
    }
}
```

**How to run:** `java BomDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Dependency resolution via Spring Boot BOM 3.3.4 ===

Dependency                                 BOM Version              Status
--------------------------------------------------------------------------------
org.springframework.boot:spring-boot-... 3.3.4                    ✓ no <version> needed
com.fasterxml.jackson.core:jackson-da... 2.17.2                   ✓ no <version> needed
org.hibernate.orm:hibernate-core         6.5.2.Final              ✓ no <version> needed
org.apache.tomcat.embed:tomcat-embed-... 10.1.28                  ✓ no <version> needed
io.micrometer:micrometer-core           1.13.4                   ✓ no <version> needed
com.example:my-custom-library           (not managed)            ⚠ must specify version manually

Libraries in Spring Boot 3.3.4 BOM: 400+
Version conflicts caused by BOM libraries: 0
```

## 6. Walkthrough

- **`BomEntry` record** — models a single BOM entry. A real BOM POM has hundreds of these as `<dependency>` elements inside `<dependencyManagement>`.
- **`SPRING_BOOT_BOM_3_3_4`** — a representative subset of the real Spring Boot 3.3.4 BOM. The actual BOM manages over 400 artifacts.
- **`resolveVersion`** — simulates what Maven does when it encounters a dependency with no `<version>`. It walks up the POM hierarchy and checks every `<dependencyManagement>` block, including imported BOMs, for a matching entry.
- **`com.example:my-custom-library`** — not in the BOM, so it returns `(not managed)`. You *must* specify a version for libraries outside the BOM. This is the only time you write a `<version>` tag in a Spring Boot project.
- **"0 version conflicts"** — the key value. The BOM's versions are tested together; you get this guarantee for free.

## 7. Gotchas & takeaways

> **Overriding a BOM version is allowed but risky.** If you write `<jackson.version>2.18.0</jackson.version>` in `<properties>`, Maven uses that version for all Jackson artifacts instead of the BOM-managed version. This can break compatibility with Spring Framework 6 if Jackson 2.18 has an API change. Only override when you've verified compatibility (e.g., a security patch for a specific CVE).

> **The BOM does not automatically add dependencies.** It only manages versions. You still need to declare `<dependency>` entries for every library you use — the BOM just means those entries don't need version numbers.

- Import the BOM once via `spring-boot-starter-parent` or `spring-boot-dependencies` + `<scope>import</scope>`.
- Omit `<version>` for any library listed in the BOM — Maven/Gradle resolves it automatically.
- `mvn dependency:tree` or `./gradlew dependencies` reveals the exact resolved version of every library.
- For libraries outside the BOM, always specify a version — the BOM can't manage what it doesn't know about.
- Upgrading Spring Boot version = upgrading the BOM = getting new tested versions of 400+ libraries in one change.
