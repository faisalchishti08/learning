---
card: spring-boot
gi: 23
slug: maven-without-the-parent-pom
title: Maven without the parent POM
---

## 1. What it is

**Maven without the parent POM** means using `spring-boot-dependencies` as a BOM import inside your own `<dependencyManagement>` block rather than inheriting `spring-boot-starter-parent`. This pattern is required when your project must inherit a corporate or platform parent POM — Maven only allows one `<parent>`, so you can't inherit `starter-parent` at the same time.

The result: you keep your corporate parent, get all of Spring Boot's version management, but must manually configure the plugins that `starter-parent` would have provided automatically.

## 2. Why & when

**When to use this pattern:**
- Your organisation has a `company-parent` POM that enforces code quality, internal repository settings, or standard plugin versions.
- You're building a sub-module that already has a project-level parent and needs Spring Boot.
- You're integrating Spring Boot into an existing Maven project that predates Spring Boot.

**What you lose vs `starter-parent`:**
- Automatic `spring-boot-maven-plugin` configuration (must add it manually).
- Automatic `maven-compiler-plugin` configuration (must set `maven.compiler.release`).
- Resource filtering with `@...@` delimiters (must configure `maven-resources-plugin` manually).
- Surefire/Failsafe plugin auto-setup for JUnit 5 (usually fine without it for JUnit 5).

**What you keep:**
- All version management for Spring ecosystem libraries (same as starter-parent).
- No version tags needed on spring-boot-starter-* dependencies.

## 3. Core concept

The minimal `pom.xml` structure for Spring Boot without a parent:

```xml
<project>
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>com.mycompany</groupId>
    <artifactId>company-parent</artifactId>
    <version>5.1.0</version>
  </parent>

  <groupId>com.example</groupId>
  <artifactId>order-service</artifactId>
  <version>1.0.0-SNAPSHOT</version>

  <!-- (1) Import BOM for version management -->
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

  <!-- (2) Declare dependencies without versions (managed by BOM) -->
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
  </dependencies>

  <!-- (3) Manually configure the Spring Boot Maven plugin -->
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
        <version>3.3.4</version>
        <executions>
          <execution>
            <goals><goal>repackage</goal></goals>
          </execution>
        </executions>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <configuration>
          <release>21</release>  <!-- must set explicitly without starter-parent -->
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

The BOM import in step (1) gives you the same dependency version management as `starter-parent`. Steps (2) and (3) are what you'd have gotten for free with `starter-parent`.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of starter-parent approach vs no-parent BOM import approach showing what is automatic vs manual">
  <!-- Headers -->
  <text x="165" y="22" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">With starter-parent</text>
  <text x="495" y="22" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Without parent (BOM import)</text>

  <!-- Comparison rows -->
  <rect x="20" y="30" width="620" height="26" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ BOM version management (automatic)</text>
  <line x1="330" y1="30" x2="330" y2="56" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ BOM version management (via import)</text>

  <rect x="20" y="60" width="620" height="26" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ boot plugin auto-configured</text>
  <line x1="330" y1="60" x2="330" y2="86" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="78" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">⚠ must declare plugin manually</text>

  <rect x="20" y="90" width="620" height="26" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ Java 17 compiler (via java.version)</text>
  <line x1="330" y1="90" x2="330" y2="116" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="108" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">⚠ must set maven.compiler.release</text>

  <rect x="20" y="120" width="620" height="26" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="138" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ @...@ resource filtering</text>
  <line x1="330" y1="120" x2="330" y2="146" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="138" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">⚠ configure resources plugin manually</text>

  <rect x="20" y="150" width="620" height="26" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">✗ can't use corporate parent</text>
  <line x1="330" y1="150" x2="330" y2="176" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="168" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ corporate parent preserved</text>

  <rect x="20" y="180" width="620" height="26" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="198" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Best for: new standalone projects</text>
  <line x1="330" y1="180" x2="330" y2="206" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="198" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Best for: enterprise / multi-parent</text>
</svg>

Both deliver the same dependency versions; the no-parent path trades auto-config convenience for the ability to keep a corporate parent.

## 5. Runnable example

```java
// File: NoParentPomDemo.java
// Compares what must be written manually vs what starter-parent provides.
// Run: java NoParentPomDemo.java

import java.util.*;

public class NoParentPomDemo {

    record ConfigItem(String name, String withParent, String withoutParent) {}

    public static void main(String[] args) {
        var items = List.of(
            new ConfigItem("BOM version management",
                "automatic (parent inherits BOM)",
                "must add <dependencyManagement><scope>import</scope>"),
            new ConfigItem("spring-boot-maven-plugin",
                "automatic (pre-configured in parent)",
                "must declare with <executions><goal>repackage</goal>"),
            new ConfigItem("Java version",
                "<java.version>21</java.version> only",
                "<maven.compiler.release>21</maven.compiler.release>"),
            new ConfigItem("Resource @token@ filtering",
                "automatic",
                "configure maven-resources-plugin manually"),
            new ConfigItem("Corporate parent POM",
                "not possible (Maven has one parent)",
                "preserved — corporate parent still active")
        );

        System.out.println("=== starter-parent vs no-parent BOM import ===\n");
        System.out.printf("%-35s %-30s %s%n", "Feature", "With starter-parent", "Without parent");
        System.out.println("-".repeat(110));

        for (var item : items) {
            System.out.printf("%-35s %-30s %s%n",
                item.name(), item.withParent(), item.withoutParent());
        }

        System.out.println();
        System.out.println("=== Minimum extra XML needed (no-parent path) ===");
        System.out.println("""
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
            <build><plugins>
              <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <version>3.3.4</version>
                <executions><execution>
                  <goals><goal>repackage</goal></goals>
                </execution></executions>
              </plugin>
            </plugins></build>
            """);
        System.out.println("That's it — no other differences in day-to-day use.");
    }
}
```

**How to run:** `java NoParentPomDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`ConfigItem` record** — holds the comparison for one configuration feature. Records are ideal for immutable data transfer objects with multiple fields; Java 16+ generates the constructor, accessors, `equals`, `hashCode`, and `toString` automatically.
- **BOM row** — the critical one. Without `starter-parent`, you must write the `<dependencyManagement>` block yourself. Once it's there, all subsequent spring-boot-starter-* entries need no version.
- **Plugin row** — `spring-boot-maven-plugin` must have an explicit `<executions><execution><goals><goal>repackage</goal></goals>` block; otherwise `mvn package` produces only the thin JAR, not the fat JAR.
- **Java version row** — `starter-parent` translates `<java.version>21</java.version>` to the `maven-compiler-plugin`'s `<release>21</release>`. Without the parent, use `<maven.compiler.release>21</maven.compiler.release>` directly in `<properties>`.
- **Corporate parent row** — the reason this pattern exists. Maven 3.x allows exactly one parent; you can't have both. The `<dependencyManagement>` import is the workaround.

## 7. Gotchas & takeaways

> **Both `<type>pom</type>` and `<scope>import</scope>` are mandatory.** Omitting either causes a build failure. `<type>pom</type>` tells Maven this is a BOM artifact, not a JAR. `<scope>import</scope>` tells Maven to merge the BOM's `<dependencyManagement>` into your project's `<dependencyManagement>`.

> **The Spring Boot plugin version in `<build>` must match the BOM version.** If you import BOM 3.3.4 but declare plugin version 3.2.0, you may get inconsistent behaviour. Set the plugin version to exactly the same value as the BOM version you imported.

- No-parent path = BOM import + manual plugin config + manual compiler config.
- Use this when a corporate parent POM is required.
- The BOM gives identical version management to `starter-parent`; only the plugin configuration differs.
- Remember both `<type>pom</type>` and `<scope>import</scope>` on the BOM dependency — easy to forget one.
- `mvn help:effective-pom | grep 'artifactId\|version'` quickly verifies that the plugin is registered and the BOM is applied.
