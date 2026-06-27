---
card: spring-boot
gi: 25
slug: gradle-plugin-bootrun-bootjar-bootwar
title: Gradle plugin (bootRun, bootJar, bootWar)
---

## 1. What it is

The **Spring Boot Gradle plugin** (`org.springframework.boot`) is the Gradle equivalent of the Spring Boot Maven plugin. Applied to a Gradle project, it registers three core tasks:

| Task | Command | Equivalent Maven goal | Purpose |
|---|---|---|---|
| `bootRun` | `./gradlew bootRun` | `spring-boot:run` | Compile and run without packaging |
| `bootJar` | `./gradlew bootJar` | `spring-boot:repackage` | Create executable fat JAR |
| `bootWar` | `./gradlew bootWar` | `spring-boot:repackage` (WAR) | Create executable WAR (for external container) |
| `bootBuildImage` | `./gradlew bootBuildImage` | `spring-boot:build-image` | Create OCI image via Buildpacks |
| `bootRun` with args | See below | `spring-boot:run -Dargs` | Run with profiles, JVM flags |

The plugin also:
- Disables the standard `jar` task by default (prevents accidentally shipping the thin JAR).
- Configures `bootJar` to produce a layered fat JAR.
- Integrates with the `io.spring.dependency-management` plugin for BOM support.

## 2. Why & when

Use `bootRun` during development — it's faster than `bootJar` because it skips the packaging step. Gradle's incremental compilation means only changed classes are recompiled between runs.

Use `bootJar` in CI and before production deployments — it produces the same self-contained fat JAR that `java -jar` runs.

Use `bootWar` only when deploying to an external servlet container (a legacy use case). The WAR file includes an embedded Tomcat but marks its servlet-api dependencies as `provided` so the external container's Tomcat takes precedence.

The Gradle plugin is identical in capability to the Maven plugin; choose one based on your team's preference or existing infrastructure.

## 3. Core concept

**Plugin application in `build.gradle.kts`:**

```kotlin
plugins {
    id("org.springframework.boot") version "3.3.4"
    id("io.spring.dependency-management") version "1.1.6"
    java
}
```

**Configuring `bootRun`:**

```kotlin
tasks.named<org.springframework.boot.gradle.tasks.run.BootRun>("bootRun") {
    args("--spring.profiles.active=dev")
    jvmArgs("-Xmx256m", "-Dspring.output.ansi.enabled=always")
    environment("MY_VAR", "myvalue")
}
```

**Configuring `bootJar`:**

```kotlin
tasks.named<org.springframework.boot.gradle.tasks.bundling.BootJar>("bootJar") {
    archiveFileName.set("app.jar")  // fixed name instead of default with version suffix
    layered {
        enabled.set(true)           // enable layered JAR for Docker caching (default: true)
    }
}
```

**`bootWar` setup:**

```kotlin
plugins { war }  // adds 'war' task; bootWar extends it

tasks.named<org.springframework.boot.gradle.tasks.bundling.BootWar>("bootWar") {
    mainClass.set("com.example.App")
}
```

**`bootBuildImage`:**

```kotlin
tasks.named<org.springframework.boot.gradle.tasks.bundling.BootBuildImage>("bootBuildImage") {
    imageName.set("my-registry.io/order-service:${project.version}")
    publish.set(true)              // push to registry after build
    docker {
        publishRegistry {
            url.set("https://my-registry.io")
            username.set(providers.environmentVariable("REGISTRY_USER").orNull)
            password.set(providers.environmentVariable("REGISTRY_PASS").orNull)
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Gradle Spring Boot plugin tasks and their outputs for development, CI, and container deployment">
  <!-- Source -->
  <rect x="20" y="80" width="120" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="106" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Source</text>
  <text x="80" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">src/main/java</text>

  <line x1="140" y1="110" x2="180" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#gradArr)"/>

  <!-- Plugin box -->
  <rect x="180" y="40" width="280" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="64" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot Gradle Plugin</text>

  <rect x="196" y="76" width="120" height="26" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="256" y="94" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">bootRun</text>

  <rect x="196" y="110" width="120" height="26" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="256" y="128" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">bootJar</text>

  <rect x="196" y="144" width="120" height="26" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="256" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">bootWar</text>

  <rect x="328" y="76" width="120" height="26" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="388" y="94" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">bootBuildImage</text>

  <line x1="460" y1="110" x2="500" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#gradArr2)"/>

  <!-- Outputs -->
  <rect x="500" y="40" width="148" height="140" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="574" y="64" fill="#e6edf3" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Outputs</text>
  <text x="574" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Running on :8080</text>
  <text x="574" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">build/libs/app.jar</text>
  <text x="574" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">build/libs/app.war</text>
  <text x="574" y="148" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">OCI image</text>
  <text x="574" y="164" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">in Docker daemon</text>

  <defs>
    <marker id="gradArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="gradArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Four tasks, four use cases: `bootRun` for development, `bootJar` for CI artifacts, `bootWar` for legacy containers, `bootBuildImage` for Docker.

## 5. Runnable example

```java
// File: GradlePluginTasksDemo.java
// Illustrates the Gradle plugin tasks and their key configuration options.
// Run: java GradlePluginTasksDemo.java

import java.util.*;

public class GradlePluginTasksDemo {

    record GradleTask(String name, String command, String output, String devOrProd, String notes) {}

    public static void main(String[] args) {
        var tasks = List.of(
            new GradleTask("bootRun",
                "./gradlew bootRun",
                "Running app on :8080",
                "Development",
                "Incremental build; skip packaging; reload on class change with DevTools"),
            new GradleTask("bootJar",
                "./gradlew bootJar",
                "build/libs/app-0.0.1.jar (fat JAR)",
                "CI / Production",
                "Same as mvn package; standard Jar task is disabled automatically"),
            new GradleTask("bootWar",
                "./gradlew bootWar",
                "build/libs/app-0.0.1.war",
                "Legacy container",
                "Requires 'war' plugin; extend SpringBootServletInitializer in main class"),
            new GradleTask("bootBuildImage",
                "./gradlew bootBuildImage",
                "docker.io/library/app:0.0.1 (OCI image)",
                "Container / Kubernetes",
                "No Dockerfile needed; layered for cache efficiency; requires Docker daemon"),
            new GradleTask("bootRunTests",
                "./gradlew test",
                "test results in build/reports/tests",
                "CI",
                "Standard Gradle test task; Spring Boot doesn't change test invocation")
        );

        System.out.println("=== Spring Boot Gradle Plugin Tasks ===\n");
        for (var task : tasks) {
            System.out.println("Task      : " + task.name());
            System.out.println("Command   : " + task.command());
            System.out.println("Output    : " + task.output());
            System.out.println("Use in    : " + task.devOrProd());
            System.out.println("Notes     : " + task.notes());
            System.out.println();
        }

        System.out.println("=== build.gradle.kts (Kotlin DSL) ===");
        System.out.println("""
            plugins {
                id("org.springframework.boot") version "3.3.4"
                id("io.spring.dependency-management") version "1.1.6"
                java
            }

            tasks.named<BootRun>("bootRun") {
                args("--spring.profiles.active=dev")
                jvmArgs("-Xmx256m")
            }

            tasks.named<BootJar>("bootJar") {
                archiveFileName.set("app.jar")  // fixed name for scripts
            }
            """);
    }
}
```

**How to run:** `java GradlePluginTasksDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`bootRun`** — Gradle compiles only changed files (incremental compilation) and then forks a JVM with the Gradle-managed classpath. Combined with `spring-boot-devtools` on the classpath, class changes trigger automatic restarts without re-running `bootRun`.
- **`bootJar`** — disables the standard `jar` task so only the fat JAR is produced. The output file is in `build/libs/`. Fixed name via `archiveFileName.set("app.jar")` is useful in Docker `CMD` instructions so the name doesn't need to be updated on every version bump.
- **`bootWar`** — requires the `war` plugin applied separately. The WAR contains `WEB-INF/lib/` (dependencies) and an embedded Tomcat that's activated when run with `java -jar` but ignored when deployed to an external container.
- **`bootBuildImage`** — calls the Buildpacks runtime to analyse the fat JAR and construct a multi-layer OCI image. The Paketo Java buildpack is the default; it automatically sets JVM memory settings, adds a health check, and layers for caching.
- **`test`** — unchanged from standard Gradle; the Spring Boot plugin doesn't modify test execution. `@SpringBootTest` in your test class triggers the full application context loading.

## 7. Gotchas & takeaways

> **`bootJar` disables `jar` by default.** This prevents shipping the thin JAR accidentally. If you need the thin JAR for inter-module dependencies (e.g., module A is a library used by module B), re-enable it:
> ```kotlin
> tasks.named<Jar>("jar") { enabled = true; archiveClassifier.set("plain") }
> ```

> **`bootRun` does not read from the fat JAR.** Config files outside `src/main/resources` on disk are picked up because `bootRun` runs against the source tree. When you switch to `java -jar`, only config files inside the JAR or next to it on disk are used. Test with `java -jar build/libs/app.jar` before releasing.

- Use `./gradlew bootRun` for development; `./gradlew bootJar` for deployment artifacts.
- Match the plugin version to the Spring Boot version in `build.gradle.kts`.
- `archiveFileName.set("app.jar")` gives a stable JAR name for Docker `CMD` lines.
- `bootBuildImage` needs Docker daemon running; customise the image name via `imageName.set(...)`.
- `./gradlew dependencies --configuration runtimeClasspath` shows the full dependency tree resolved by the BOM.
