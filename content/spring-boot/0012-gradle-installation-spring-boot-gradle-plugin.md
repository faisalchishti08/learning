---
card: spring-boot
gi: 12
slug: gradle-installation-spring-boot-gradle-plugin
title: Gradle installation & Spring Boot Gradle plugin
---

## 1. What it is

**Gradle** is the second major Java build tool (after Maven) and the build system of choice for Android and many large monorepos. For Spring Boot, Gradle's role is identical to Maven's — dependency management, compilation, testing, and fat JAR packaging — but the configuration language is Groovy DSL or **Kotlin DSL** (`.kts` files) rather than XML.

**`spring-boot-gradle-plugin`** is the Gradle equivalent of `spring-boot-maven-plugin`. Applied to a Gradle project, it:

1. Adds a `bootJar` task that packages a fat JAR (equivalent to `mvn package`).
2. Adds a `bootRun` task to run the application (equivalent to `mvn spring-boot:run`).
3. Adds a `bootBuildImage` task to build an OCI (Docker) image using Cloud Native Buildpacks.
4. Integrates with the `io.spring.dependency-management` plugin to import the `spring-boot-dependencies` BOM — giving you the same "no version numbers" experience as Maven's `starter-parent`.

## 2. Why & when

Choose Gradle over Maven when:
- Your project is **multi-module** with complex build logic — Gradle's incremental build is faster than Maven's at scale.
- Your team prefers **Kotlin/Groovy DSL** over XML.
- You're working on an **Android** project (Gradle is mandatory there).
- You want **build caching** out of the box — Gradle's daemon + build cache can be significantly faster in CI.

Choose Maven when:
- Your team knows Maven well and has no strong reason to switch.
- Your organization has Maven-centric tooling or a corporate Nexus/Artifactory setup tuned for Maven.

For Spring Boot specifically, both are fully supported. **start.spring.io** lets you choose either. The resulting code is identical; only the build files differ.

**Gradle Wrapper (`gradlew`):** Like Maven Wrapper, Gradle Wrapper (`gradlew` / `gradlew.bat`) downloads the correct Gradle version on first run. Always commit it.

## 3. Core concept

A minimal Spring Boot Gradle project (Kotlin DSL) has two files beyond source code:

**`settings.gradle.kts`** — declares the project name:
```kotlin
rootProject.name = "my-app"
```

**`build.gradle.kts`** — the entire build:
```kotlin
plugins {
    id("org.springframework.boot") version "3.3.4"      // Spring Boot plugin
    id("io.spring.dependency-management") version "1.1.6" // BOM import
    kotlin("jvm") version "1.9.25"  // or java for non-Kotlin
}

group = "com.example"
version = "0.0.1-SNAPSHOT"

repositories { mavenCentral() }

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")  // no version!
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}
```

That's it — identical simplicity to the Maven POM. The `io.spring.dependency-management` plugin imports the Spring Boot BOM, so no versions are needed on Spring ecosystem dependencies.

**Key Gradle tasks:**

| Task | Maven equivalent | Purpose |
|---|---|---|
| `./gradlew bootRun` | `./mvnw spring-boot:run` | Run the app |
| `./gradlew test` | `./mvnw test` | Run tests |
| `./gradlew bootJar` | `./mvnw package` | Build fat JAR |
| `./gradlew dependencies` | `./mvnw dependency:tree` | Show dependency tree |
| `./gradlew bootBuildImage` | (no direct equivalent) | Build Docker image |

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Gradle Spring Boot build pipeline showing source files, plugins, tasks, and output artifacts">
  <!-- Source -->
  <rect x="20" y="100" width="140" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="124" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Source Code</text>
  <text x="90" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">src/main/java</text>
  <text x="90" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">+ resources</text>

  <line x1="160" y1="130" x2="200" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#garr)"/>

  <!-- Gradle + plugin -->
  <rect x="200" y="60" width="260" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="86" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Gradle + Spring Boot Plugin</text>
  <rect x="216" y="96" width="228" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">io.spring.dependency-management</text>
  <rect x="216" y="132" width="100" height="24" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="266" y="149" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">bootJar task</text>
  <rect x="328" y="132" width="116" height="24" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="386" y="149" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">bootRun task</text>
  <rect x="216" y="164" width="228" height="24" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="330" y="181" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">bootBuildImage (Docker via Buildpacks)</text>

  <!-- Arrow right to outputs -->
  <line x1="460" y1="130" x2="500" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#garr2)"/>

  <!-- Outputs -->
  <rect x="500" y="60" width="148" height="140" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="574" y="86" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Outputs</text>
  <rect x="516" y="96" width="116" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="574" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">build/libs/app.jar</text>
  <rect x="516" y="132" width="116" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="574" y="151" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Running app</text>
  <rect x="516" y="168" width="116" height="24" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="574" y="184" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Docker image</text>

  <defs>
    <marker id="garr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="garr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Source code flows through the Gradle Spring Boot plugin to produce a fat JAR, a running application, or a Docker image — chosen by which task you invoke.

## 5. Runnable example

```java
// File: GradleStructureDemo.java
// Prints a typical Spring Boot Gradle project structure and build.gradle.kts skeleton.
// Run: java GradleStructureDemo.java

public class GradleStructureDemo {

    public static void main(String[] args) {
        System.out.println("=== Minimal Spring Boot Gradle (Kotlin DSL) project ===\n");

        System.out.println("my-app/");
        System.out.println("├── gradle/wrapper/gradle-wrapper.jar");
        System.out.println("├── gradle/wrapper/gradle-wrapper.properties");
        System.out.println("├── gradlew          (Unix)");
        System.out.println("├── gradlew.bat      (Windows)");
        System.out.println("├── settings.gradle.kts");
        System.out.println("├── build.gradle.kts");
        System.out.println("└── src/");
        System.out.println("    ├── main/java/com/example/MyApp.java");
        System.out.println("    ├── main/resources/application.properties");
        System.out.println("    └── test/java/com/example/MyAppTest.java");

        System.out.println("\n=== settings.gradle.kts ===\n");
        System.out.println("""
            rootProject.name = "my-app"
            """);

        System.out.println("=== build.gradle.kts ===\n");
        System.out.println("""
            plugins {
                // (1) Spring Boot plugin — adds bootJar, bootRun, bootBuildImage tasks
                id("org.springframework.boot") version "3.3.4"

                // (2) Spring dependency-management — imports spring-boot-dependencies BOM
                id("io.spring.dependency-management") version "1.1.6"

                // (3) Java plugin — compilation, test, jar tasks
                java
            }

            group   = "com.example"
            version = "0.0.1-SNAPSHOT"

            java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }

            repositories { mavenCentral() }

            dependencies {
                // No version needed — managed by io.spring.dependency-management
                implementation("org.springframework.boot:spring-boot-starter-web")
                testImplementation("org.springframework.boot:spring-boot-starter-test")
            }
            """);

        System.out.println("=== Common Gradle commands ===");
        System.out.println("  ./gradlew bootRun          — start the app");
        System.out.println("  ./gradlew test             — run all tests");
        System.out.println("  ./gradlew bootJar          — build fat JAR → build/libs/*.jar");
        System.out.println("  ./gradlew bootBuildImage   — build Docker image (no Dockerfile needed)");
        System.out.println("  ./gradlew dependencies     — show full dependency tree");
        System.out.println("  java -jar build/libs/my-app-0.0.1-SNAPSHOT.jar  — run fat JAR");
    }
}
```

**How to run:** `java GradleStructureDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`id("org.springframework.boot") version "3.3.4"` (1)** — applies the Spring Boot Gradle plugin. This registers the `bootJar`, `bootRun`, and `bootBuildImage` tasks. The version here is the *plugin* version — always match it to your Spring Boot version.
- **`id("io.spring.dependency-management") version "1.1.6"` (2)** — the Spring dependency-management plugin imports `spring-boot-dependencies` as a BOM into Gradle's dependency resolution. Without this, every dependency in `build.gradle.kts` would need an explicit version.
- **`java` (3)** — Gradle's built-in Java plugin adds `compileJava`, `test`, and `jar` tasks. `bootJar` is built on top of `jar`.
- **`java { toolchain { ... } }`** — Gradle Toolchains select the correct JDK version for compilation. `JavaLanguageVersion.of(21)` means Gradle will find or download JDK 21 from a toolchain provider. This is cleaner than setting `sourceCompatibility = 17` manually because it also affects the JVM that runs tests.
- **No version on dependencies** — same as Maven's `starter-parent` effect. The `io.spring.dependency-management` plugin resolves versions from the BOM.
- **`bootBuildImage`** — unique to the Gradle plugin (and available in Maven too via `spring-boot:build-image`). Uses Cloud Native Buildpacks to create an OCI image without a `Dockerfile`. The image is layer-optimised for Spring Boot fat JARs.

## 7. Gotchas & takeaways

> **Both `spring-boot-gradle-plugin` and `io.spring.dependency-management` are required for the "no version" experience.** Omitting `io.spring.dependency-management` means the BOM isn't imported, and Gradle will complain that versions are missing for Spring Boot starters. They work as a pair.

> **`bootJar` disables the standard `jar` task by default.** This prevents accidentally shipping the thin JAR without embedded dependencies. If you need both (e.g., publishing an API artifact to Nexus while also deploying a fat JAR), re-enable `jar` explicitly:
> ```kotlin
> tasks.getByName<Jar>("jar") { enabled = true; archiveClassifier.set("plain") }
> ```

- The Gradle Wrapper (`gradlew`) must be committed — it ensures every developer and CI job uses the same Gradle version.
- Always match the `org.springframework.boot` plugin version to the Spring Boot version you want.
- Use `./gradlew dependencies --configuration runtimeClasspath` to diagnose version conflicts.
- `bootBuildImage` produces a Docker image directly, no `Dockerfile` needed — useful for straightforward deployments.
- Maven vs Gradle for Spring Boot: both excellent; prefer whichever your team knows or whichever start.spring.io generates for you.
