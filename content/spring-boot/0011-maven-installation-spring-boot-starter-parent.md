---
card: spring-boot
gi: 11
slug: maven-installation-spring-boot-starter-parent
title: Maven installation & spring-boot-starter-parent
---

## 1. What it is

**Apache Maven** is the most widely used Java build tool. For Spring Boot projects, Maven does four things: downloads dependencies from Maven Central, compiles source code, runs tests, and packages the application into a fat JAR.

**`spring-boot-starter-parent`** is a special Maven parent POM that every Spring Boot Maven project inherits from. It brings:

1. **Dependency management** via `spring-boot-dependencies` BOM — pins hundreds of library versions so you never write `<version>` tags for Spring ecosystem libraries.
2. **Plugin configuration** — pre-configures the `spring-boot-maven-plugin` (for fat JAR packaging and `spring-boot:run`), the compiler plugin (Java 17 source/target), the surefire plugin (for `mvn test`), and others.
3. **Resource filtering** — `application.properties` / `application.yml` get `@project.version@`-style token expansion automatically.
4. **Sensible defaults** — UTF-8 encoding, standard directory layout.

A Spring Boot Maven project has one mandatory parent declaration and almost no other boilerplate.

## 2. Why & when

Without `spring-boot-starter-parent`, you would need to:
- Find and specify compatible versions for every Spring, Hibernate, Jackson, and Micrometer artifact manually.
- Configure the `spring-boot-maven-plugin` to produce a fat JAR.
- Set `<source>17</source>` and `<target>17</target>` on the Maven compiler plugin yourself.
- Import the `spring-boot-dependencies` BOM under `<dependencyManagement>` if you don't want to inherit the parent.

Declare `spring-boot-starter-parent` in **every new Spring Boot Maven project**. The only case where you'd skip it is if your organization has a corporate parent POM — in that case, import `spring-boot-dependencies` as a BOM inside `<dependencyManagement>` instead.

## 3. Core concept

The Maven POM hierarchy for a Spring Boot project:

```
Your pom.xml  →  spring-boot-starter-parent  →  spring-boot-dependencies
                                                  (BOM: pinned versions for ~400 libraries)
```

The `spring-boot-starter-parent` POM declares `<parent>spring-boot-dependencies</parent>`, which is a BOM (Bill of Materials) — a POM that only contains `<dependencyManagement>` with pinned versions. When your `pom.xml` inherits `starter-parent`, you get all those version pins.

A minimal working `pom.xml`:

```xml
<project>
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.4</version>
  </parent>

  <groupId>com.example</groupId>
  <artifactId>my-app</artifactId>
  <version>0.0.1-SNAPSHOT</version>

  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
      <!-- No <version> needed — starter-parent manages it -->
    </dependency>
  </dependencies>
</project>
```

That's a complete, functional Spring Boot web application POM. No plugin declarations, no version numbers, no dependency management section.

**Maven Wrapper (`mvnw`):** The Spring Initializr generates an `mvnw` shell script (Unix) and `mvnw.cmd` (Windows) alongside your project. These wrapper scripts download the correct Maven version automatically, meaning developers don't need Maven installed globally. Always commit these files.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Maven POM hierarchy showing your project inheriting from starter-parent which inherits from spring-boot-dependencies BOM">
  <!-- Your pom.xml -->
  <rect x="220" y="20" width="220" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="46" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Your pom.xml</text>
  <text x="330" y="64" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;parent&gt; spring-boot-starter-parent</text>

  <!-- Arrow down -->
  <line x1="330" y1="80" x2="330" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#mvarr)"/>
  <text x="346" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">inherits</text>

  <!-- starter-parent -->
  <rect x="160" y="110" width="340" height="64" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="134" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-starter-parent</text>
  <text x="330" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">compiler 17 · maven-surefire · spring-boot-maven-plugin</text>
  <text x="330" y="166" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;parent&gt; spring-boot-dependencies</text>

  <!-- Arrow down -->
  <line x1="330" y1="174" x2="330" y2="204" stroke="#79c0ff" stroke-width="2" marker-end="url(#mvarr2)"/>
  <text x="346" y="194" fill="#8b949e" font-size="10" font-family="sans-serif">inherits</text>

  <!-- BOM -->
  <rect x="100" y="204" width="460" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="228" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-dependencies (BOM)</text>
  <text x="330" y="248" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;dependencyManagement&gt; — pins ~400 library versions (Hibernate, Jackson, Micrometer…)</text>

  <defs>
    <marker id="mvarr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mvarr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Three POMs, one inheritance chain. You write the top; `starter-parent` and the BOM do the rest.

## 5. Runnable example

```java
// File: MavenStructureDemo.java
// Prints a typical Spring Boot Maven project structure and pom.xml skeleton.
// Run: java MavenStructureDemo.java

public class MavenStructureDemo {

    static void printTree(String indent, String... lines) {
        for (String line : lines) System.out.println(indent + line);
    }

    public static void main(String[] args) {
        System.out.println("=== Minimal Spring Boot Maven project ===\n");

        // Project directory tree
        System.out.println("my-app/");
        printTree("├── ", ".mvn/wrapper/maven-wrapper.properties");
        printTree("├── ", "mvnw", "mvnw.cmd");
        printTree("├── ", "pom.xml");
        printTree("└── src/");
        printTree("    ├── main/");
        printTree("    │   ├── java/com/example/MyApp.java");
        printTree("    │   └── resources/application.properties");
        printTree("    └── test/");
        printTree("        └── java/com/example/MyAppTest.java");

        System.out.println("\n=== pom.xml (minimum required) ===\n");
        System.out.println("""
            <project>
              <modelVersion>4.0.0</modelVersion>

              <!-- (1) Inherit Spring Boot's defaults + dependency management -->
              <parent>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-parent</artifactId>
                <version>3.3.4</version>
              </parent>

              <groupId>com.example</groupId>
              <artifactId>my-app</artifactId>
              <version>0.0.1-SNAPSHOT</version>

              <dependencies>
                <!-- (2) No <version> tag needed — managed by starter-parent -->
                <dependency>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-starter-web</artifactId>
                </dependency>
                <dependency>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-starter-test</artifactId>
                  <scope>test</scope>
                </dependency>
              </dependencies>
            </project>""");

        System.out.println("\n=== Common Maven commands ===");
        System.out.println("  ./mvnw spring-boot:run   — start the app (hot-reload friendly)");
        System.out.println("  ./mvnw test              — run all tests");
        System.out.println("  ./mvnw package           — build fat JAR → target/my-app-0.0.1-SNAPSHOT.jar");
        System.out.println("  ./mvnw dependency:tree   — see all transitive dependencies");
        System.out.println("  java -jar target/my-app-0.0.1-SNAPSHOT.jar  — run the fat JAR");
    }
}
```

**How to run:** `java MavenStructureDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`(1) <parent>` declaration** — this single block gives you everything: managed dependency versions, plugin defaults, UTF-8 encoding, and Java 17 compilation. Change only the `<version>` when upgrading Spring Boot.
- **`(2) No <version>` on dependencies** — because `spring-boot-starter-parent` imports `spring-boot-dependencies` as a BOM, Maven finds the correct version for `spring-boot-starter-web` automatically. Adding `<version>3.3.4</version>` yourself would work but is redundant and creates drift risk.
- **`<scope>test</scope>`** — `spring-boot-starter-test` is test-only; it includes JUnit 5, Mockito, AssertJ, and Spring Test. Marking it `test` keeps it out of the production JAR.
- **`./mvnw spring-boot:run`** — the `spring-boot-maven-plugin` (pre-configured by `starter-parent`) starts your app in the same JVM as Maven, enabling fast iteration. It watches for class file changes when run with `-Dspring-boot.run.fork=false`.
- **`./mvnw package`** — produces the fat JAR in `target/`. The filename follows `<artifactId>-<version>.jar`. This is the artifact you ship.
- **`.mvn/wrapper/`** — the Maven Wrapper configuration. `mvnw` downloads Maven 3.9.x (or whatever version is pinned in `maven-wrapper.properties`) on first run. Commit these files; never add them to `.gitignore`.

## 7. Gotchas & takeaways

> **If you already have a corporate parent POM, don't fight it.** Import `spring-boot-dependencies` as a BOM inside `<dependencyManagement>` instead of inheriting `spring-boot-starter-parent`. You lose the plugin auto-configuration but keep the version management:
> ```xml
> <dependencyManagement>
>   <dependencies>
>     <dependency>
>       <groupId>org.springframework.boot</groupId>
>       <artifactId>spring-boot-dependencies</artifactId>
>       <version>3.3.4</version>
>       <type>pom</type>
>       <scope>import</scope>
>     </dependency>
>   </dependencies>
> </dependencyManagement>
> ```

> **Never specify `<version>` for Spring Boot managed libraries.** If you override a version that `spring-boot-dependencies` already manages, you lose the compatibility guarantee. Only override when you've tested that the newer version is compatible.

- `spring-boot-starter-parent` provides: version management + plugin defaults + compiler settings.
- You only write `<parent>`, your `<groupId>`/`<artifactId>`, and your `<dependencies>` — nothing else.
- Commit `mvnw`, `mvnw.cmd`, and `.mvn/` so CI works without a system Maven installation.
- `./mvnw spring-boot:run` for development, `./mvnw package` + `java -jar` for production.
- Override a managed version only as a last resort; test thoroughly when you do.
