---
card: spring-boot
gi: 22
slug: maven-starter-parent
title: Maven starter parent
---

## 1. What it is

`spring-boot-starter-parent` is the recommended parent POM for Spring Boot Maven projects. It is a POM artifact (no Java code) that provides a curated set of plugin configurations, resource filtering rules, compiler settings, and — via its own parent `spring-boot-dependencies` — the full dependency management BOM.

**What it configures automatically:**

| Configuration | Value |
|---|---|
| Java source and target | `${java.version}` (defaults to 17) |
| Default encoding | UTF-8 for all source/resource files |
| `maven-compiler-plugin` | Pre-configured for annotation processing |
| `maven-surefire-plugin` | Runs JUnit 5 tests (no extra config) |
| `maven-failsafe-plugin` | For integration tests (`*IT.java`) |
| `spring-boot-maven-plugin` | Added; `repackage` goal bound to `package` phase |
| Resource filtering | Enabled for `application.properties` with `@...@` delimiters |
| Dependency management | Via `spring-boot-dependencies` BOM |

With `starter-parent`, your POM needs almost nothing: just coordinates, dependencies, and your business-specific configuration.

## 2. Why & when

`starter-parent` eliminates the Maven plugin configuration that every Spring Boot project needs identically. Without it, you'd write the same boilerplate in every `pom.xml`:

```xml
<!-- Without starter-parent — you'd need ALL of this -->
<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <version>3.13.0</version>
      <configuration><release>17</release></configuration>
    </plugin>
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
    <!-- ... surefire, failsafe, resources ... -->
  </plugins>
</build>
```

Use `starter-parent` for every new Spring Boot Maven project. The only exception is if you already have a corporate parent POM — then import `spring-boot-dependencies` BOM instead (see gi 21).

## 3. Core concept

`spring-boot-starter-parent` is a layered POM:

```
spring-boot-starter-parent
  inherits from:
    spring-boot-dependencies   ← dependency management BOM (400+ versions)
  adds:
    plugin management          ← maven-compiler, surefire, failsafe, boot plugin
    resource filtering         ← @project.version@ style tokens in .properties files
    java.version property      ← compile target, defaults to 17
```

**Resource filtering** is a useful feature: `@project.version@` in `application.properties` expands to the Maven project version at build time. Spring Boot uses `@` as the delimiter (instead of Maven's default `${}`), because `${}` conflicts with Spring's own property syntax:

```properties
# src/main/resources/application.properties
spring.application.version=@project.version@
info.app.name=@project.name@
```

After `mvn package`, the bundled `application.properties` has the actual version string.

**Overriding a plugin version:** `starter-parent` pins plugin versions in `<pluginManagement>`. Override them in your POM's `<build><plugins>`:

```xml
<properties>
  <maven-compiler-plugin.version>3.13.0</maven-compiler-plugin.version>
  <java.version>21</java.version>
</properties>
```

**Inheriting from `starter-parent` in a multi-module project:** the parent POM of a multi-module Maven project can itself inherit `spring-boot-starter-parent`, and all child modules automatically get the Spring Boot BOM and plugin config.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="What starter-parent provides: BOM from spring-boot-dependencies plus plugin config, resource filtering, and compiler settings">
  <!-- starter-parent box -->
  <rect x="190" y="20" width="280" height="44" rx="8" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="47" fill="#1c2430" font-size="14" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-starter-parent</text>

  <!-- Arrows to two groups -->
  <line x1="240" y1="64" x2="140" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="420" y1="64" x2="520" y2="100" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Left: from spring-boot-dependencies -->
  <rect x="20" y="100" width="240" height="120" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="122" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">From spring-boot-dependencies</text>
  <text x="140" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(inherited parent)</text>
  <rect x="36" y="150" width="208" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">400+ dependency versions</text>
  <rect x="36" y="176" width="208" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="191" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">No version tags needed</text>

  <!-- Right: starter-parent additions -->
  <rect x="400" y="100" width="240" height="120" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="122" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Starter-parent additions</text>
  <rect x="416" y="132" width="208" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot-maven-plugin config</text>
  <rect x="416" y="158" width="208" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="173" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">maven-compiler (Java 17)</text>
  <rect x="416" y="184" width="208" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="199" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Resource filtering + UTF-8</text>
</svg>

`starter-parent` = dependency version management (from `spring-boot-dependencies`) + plugin and compiler configuration.

## 5. Runnable example

```java
// File: StarterParentDemo.java
// Shows what an effective POM looks like when starter-parent is used.
// Run: java StarterParentDemo.java

public class StarterParentDemo {

    public static void main(String[] args) {
        System.out.println("=== Minimal pom.xml with spring-boot-starter-parent ===\n");

        System.out.println("""
            <project>
              <modelVersion>4.0.0</modelVersion>

              <parent>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-parent</artifactId>
                <version>3.3.4</version>
              </parent>

              <groupId>com.example</groupId>
              <artifactId>order-service</artifactId>
              <version>1.0.0-SNAPSHOT</version>

              <!-- Override Java version (21 instead of default 17) -->
              <properties>
                <java.version>21</java.version>
              </properties>

              <dependencies>
                <dependency>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-starter-web</artifactId>
                  <!-- no version: managed by starter-parent → BOM -->
                </dependency>
                <dependency>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-starter-data-jpa</artifactId>
                </dependency>
                <dependency>
                  <groupId>org.postgresql</groupId>
                  <artifactId>postgresql</artifactId>
                  <!-- no version: managed by BOM -->
                  <scope>runtime</scope>
                </dependency>
                <dependency>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-starter-test</artifactId>
                  <scope>test</scope>
                </dependency>
              </dependencies>
              <!-- No <build> section needed — starter-parent configures the plugin -->
            </project>
            """);

        System.out.println("=== What starter-parent auto-configured (not written above) ===\n");
        var autoConfig = new String[][]{
            {"spring-boot-maven-plugin",  "3.3.4",   "bootable fat JAR on mvn package"},
            {"maven-compiler-plugin",     "3.13.0",  "Java 21 source/target (from <java.version>)"},
            {"maven-surefire-plugin",     "3.2.5",   "JUnit 5 test runner"},
            {"maven-failsafe-plugin",     "3.2.5",   "integration test runner (*IT.java)"},
            {"maven-resources-plugin",    "3.3.1",   "UTF-8 encoding + @...@ token expansion"},
        };
        System.out.printf("  %-34s %-10s %s%n", "Plugin", "Version", "Purpose");
        System.out.println("  " + "-".repeat(72));
        for (var row : autoConfig) {
            System.out.printf("  %-34s %-10s %s%n", row[0], row[1], row[2]);
        }
    }
}
```

**How to run:** `java StarterParentDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`<parent>spring-boot-starter-parent</parent>`** — the only POM block you need. Everything in the "auto-configured" table appears in `spring-boot-starter-parent`'s own `<pluginManagement>` and is inherited automatically.
- **`<java.version>21</java.version>`** — overrides the default 17. `starter-parent` reads this property in its `maven-compiler-plugin` configuration. This is the idiomatic way to change the Java version; adding `<configuration><release>21</release></configuration>` to the compiler plugin directly also works but is redundant if you use starter-parent.
- **`postgresql` with no version** — PostgreSQL's JDBC driver (`org.postgresql:postgresql`) is in the Spring Boot BOM since 3.0. You get the correct version without specifying it.
- **No `<build>` section** — this is the key benefit. In a vanilla Maven project, you'd need at minimum a `<build><plugins>` section for the Spring Boot plugin. `starter-parent` injects this via `<pluginManagement>`, and because the plugin is already bound to the `package` phase, `mvn package` automatically produces a fat JAR.

## 7. Gotchas & takeaways

> **`<java.version>` is a Spring property, not a standard Maven property.** Maven's standard property for the compiler is `maven.compiler.release`. `spring-boot-starter-parent` reads `<java.version>` and sets `maven.compiler.release` for you. If you're not using `starter-parent`, use `<maven.compiler.release>21</maven.compiler.release>` directly.

> **Resource filtering with `@` delimiters is enabled by default in `src/main/resources`** but not in `src/test/resources`. In test resources, use `@` tokens for values you want expanded at build time; use `${...}` for Spring properties that should remain as-is at build time.

- One `<parent>` block replaces ~50 lines of plugin configuration.
- Change Java version via `<java.version>` property (e.g., `21`).
- The `spring-boot-maven-plugin` is pre-bound to the `package` phase — `mvn package` produces the fat JAR automatically.
- `@project.version@` in `application.properties` expands to the Maven `<version>` at build time.
- To see the full effective POM (all defaults merged): `mvn help:effective-pom`.
