---
card: spring-boot
gi: 21
slug: spring-boot-dependencies-bom
title: spring-boot-dependencies BOM
---

## 1. What it is

`spring-boot-dependencies` is the concrete Maven artifact that embodies the Spring Boot BOM. It is a POM-type artifact with no Java code — only a massive `<dependencyManagement>` section pinning ~400 library versions tested together for a given Spring Boot release.

**Maven coordinates:**
```xml
<groupId>org.springframework.boot</groupId>
<artifactId>spring-boot-dependencies</artifactId>
<version>3.3.4</version>
<type>pom</type>
```

`spring-boot-starter-parent` itself inherits from `spring-boot-dependencies`. So when you inherit `starter-parent`, you're getting `spring-boot-dependencies` transitively. When you have a corporate parent POM and can't inherit `starter-parent`, you import `spring-boot-dependencies` directly in your `<dependencyManagement>` block.

The two approaches:

| Approach | When | Configuration |
|---|---|---|
| Inherit `spring-boot-starter-parent` | New project, no corporate parent | `<parent>spring-boot-starter-parent</parent>` |
| Import `spring-boot-dependencies` BOM | Corporate parent POM already set | `<dependencyManagement>` + `<scope>import</scope>` |

Both give you the same version management; the BOM import approach doesn't give you the plugin configurations that `starter-parent` provides (you add those manually).

## 2. Why & when

**When you have a corporate parent POM**, you can't use `spring-boot-starter-parent` because Maven allows only one parent. Your corporate parent might enforce internal repository mirrors, code style, Checkstyle, and common plugin versions. You keep that parent and import the Spring Boot BOM alongside it:

```xml
<parent>
  <groupId>com.mycompany</groupId>
  <artifactId>company-parent</artifactId>
  <version>2.1.0</version>
</parent>

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

This is the canonical pattern for enterprise Spring Boot projects. The tradeoff is that you also need to explicitly configure the `spring-boot-maven-plugin` (starter-parent does this for you automatically).

## 3. Core concept

The `spring-boot-dependencies` BOM defines properties for every managed version, then uses those properties in the `<dependencyManagement>` section:

```xml
<!-- Inside spring-boot-dependencies POM (simplified) -->
<properties>
  <jackson-bom.version>2.17.2</jackson-bom.version>
  <hibernate.version>6.5.2.Final</hibernate.version>
  <tomcat.version>10.1.28</tomcat.version>
  <!-- 400+ more -->
</properties>

<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>com.fasterxml.jackson</groupId>
      <artifactId>jackson-bom</artifactId>
      <version>${jackson-bom.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
    <!-- Imports jackson-bom, which in turn manages all Jackson artifacts -->
  </dependencies>
</dependencyManagement>
```

**Overriding a managed version** via the property name (Maven only):
```xml
<properties>
  <!-- Override just Jackson, keeping everything else BOM-managed -->
  <jackson-bom.version>2.18.0</jackson-bom.version>
</properties>
```

In Gradle with the `io.spring.dependency-management` plugin, the equivalent is:
```kotlin
extra["jackson-bom.version"] = "2.18.0"
```

The property name to use for each library is in the Spring Boot reference docs' "Appendix F: Dependency Versions" table.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two paths to using spring-boot-dependencies: inheriting starter-parent vs importing the BOM directly">
  <!-- Title -->
  <text x="330" y="22" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Two ways to use spring-boot-dependencies</text>

  <!-- Path 1 -->
  <rect x="20" y="36" width="290" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="60" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Path 1: Inherit starter-parent</text>

  <rect x="36" y="72" width="258" height="36" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="165" y="89" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">&lt;parent&gt;</text>
  <text x="165" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">spring-boot-starter-parent 3.3.4</text>

  <text x="165" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Gets transitively:</text>
  <rect x="36" y="140" width="258" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="159" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-dependencies (BOM)</text>

  <text x="165" y="190" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">+ plugin defaults</text>
  <text x="165" y="206" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">+ compiler Java 17 settings</text>
  <text x="165" y="222" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Best for new projects</text>

  <!-- Path 2 -->
  <rect x="350" y="36" width="290" height="200" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="60" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Path 2: Import BOM directly</text>

  <rect x="366" y="72" width="258" height="56" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="495" y="89" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">&lt;dependencyManagement&gt;</text>
  <text x="495" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">spring-boot-dependencies 3.3.4</text>
  <text x="495" y="117" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">type=pom scope=import</text>

  <text x="495" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Corporate parent stays:</text>
  <rect x="366" y="156" width="258" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">com.mycompany:company-parent</text>

  <text x="495" y="206" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Must add plugins manually</text>
  <text x="495" y="222" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Required for enterprise projects</text>
</svg>

Both paths end up with the same managed dependency versions. Path 1 also gives plugin configuration for free; Path 2 requires manual plugin setup.

## 5. Runnable example

```java
// File: BomImportDemo.java
// Demonstrates the two BOM usage patterns and what each provides.
// Run: java BomImportDemo.java

import java.util.*;

public class BomImportDemo {

    record DependencyVersion(String artifact, String version, String source) {}

    // Simulates dependency resolution for Path 1: inheriting starter-parent
    static List<DependencyVersion> resolveWithStarterParent() {
        // starter-parent gives us:
        // a) BOM versions (same as path 2)
        // b) Plugin defaults (compiler 17, surefire, spring-boot-maven-plugin)
        return List.of(
            new DependencyVersion("spring-boot-starter-web",  "3.3.4",       "BOM (via starter-parent)"),
            new DependencyVersion("spring-webmvc",            "6.1.12",      "BOM (via starter-parent)"),
            new DependencyVersion("jackson-databind",         "2.17.2",      "BOM (via starter-parent)"),
            new DependencyVersion("spring-boot-maven-plugin", "3.3.4",       "starter-parent plugin config"),
            new DependencyVersion("maven-compiler-plugin",    "3.13.0",      "starter-parent plugin config")
        );
    }

    // Simulates dependency resolution for Path 2: direct BOM import
    static List<DependencyVersion> resolveWithBomImport() {
        // BOM import gives us:
        // a) BOM versions (same as path 1)
        // b) Corporate parent's plugin config
        // c) Must add spring-boot-maven-plugin manually
        return List.of(
            new DependencyVersion("spring-boot-starter-web",  "3.3.4",       "BOM (spring-boot-dependencies)"),
            new DependencyVersion("spring-webmvc",            "6.1.12",      "BOM (spring-boot-dependencies)"),
            new DependencyVersion("jackson-databind",         "2.17.2",      "BOM (spring-boot-dependencies)"),
            new DependencyVersion("spring-boot-maven-plugin", "3.3.4",       "⚠ must declare manually"),
            new DependencyVersion("company-checkstyle-rules", "4.2.0",       "corporate parent")
        );
    }

    public static void main(String[] args) {
        System.out.println("=== Path 1: <parent>spring-boot-starter-parent</parent> ===");
        printDeps(resolveWithStarterParent());

        System.out.println();
        System.out.println("=== Path 2: import spring-boot-dependencies BOM ===");
        printDeps(resolveWithBomImport());

        System.out.println();
        System.out.println("Dependency versions: identical.");
        System.out.println("Plugin config: Path 1 automatic, Path 2 manual.");
    }

    static void printDeps(List<DependencyVersion> deps) {
        for (var d : deps) {
            System.out.printf("  %-36s %-14s [%s]%n", d.artifact(), d.version(), d.source());
        }
    }
}
```

**How to run:** `java BomImportDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`resolveWithStarterParent()`** — includes both BOM-managed versions and plugin configurations that `starter-parent` auto-configures. The `spring-boot-maven-plugin` and `maven-compiler-plugin` are pre-set — you don't write them in your POM.
- **`resolveWithBomImport()`** — the dependency versions are identical, but the `spring-boot-maven-plugin` shows as `"⚠ must declare manually"` because the BOM only manages dependency versions, not plugin configuration. You'd add it explicitly in `<build><plugins>`.
- **`company-checkstyle-rules`** — appears in Path 2 because the corporate parent contributes this; `starter-parent` would have been in the way if you'd inherited it. This illustrates why enterprises need the BOM import approach.
- **Print formatting** — `%-36s %-14s` left-justifies strings in fixed-width columns. A useful pattern for CLI tools that present tabular data.

## 7. Gotchas & takeaways

> **`<scope>import</scope>` only works inside `<dependencyManagement>`.** Attempting to import a BOM as a regular dependency (in `<dependencies>`) causes a build error. The `import` scope is special and exclusive to `<dependencyManagement>`.

> **BOMs are composable.** You can import multiple BOMs. If two BOMs manage the same artifact, the first import wins in Maven. Import the Spring Boot BOM first; the corporate BOM's version overrides the Spring Boot one for any overlap, which is usually undesirable.

- `spring-boot-dependencies` is the actual BOM artifact; `spring-boot-starter-parent` is a POM that inherits from it and adds plugin config on top.
- Use `starter-parent` for new projects; use direct BOM import when a corporate parent must be preserved.
- `<type>pom</type>` and `<scope>import</scope>` are mandatory for BOM imports.
- Override a single version via the property name from the Spring Boot docs appendix (e.g., `<jackson-bom.version>2.18.0</jackson-bom.version>`).
- `mvn help:effective-pom` shows the full merged POM including all BOM-managed versions — useful for auditing.
