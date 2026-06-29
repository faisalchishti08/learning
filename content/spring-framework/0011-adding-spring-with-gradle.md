---
card: spring-framework
gi: 11
slug: adding-spring-with-gradle
title: Adding Spring with Gradle
---

## 1. What it is

To use Spring Boot in a Gradle project you apply the **Spring Boot plugin** and (optionally) the **Spring Dependency Management plugin**, then declare starters as dependencies.

**Groovy DSL (`build.gradle`):**
```groovy
plugins {
    id 'org.springframework.boot' version '3.4.1'
    id 'io.spring.dependency-management' version '1.1.6'
    id 'java'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

**Kotlin DSL (`build.gradle.kts`):**
```kotlin
plugins {
    id("org.springframework.boot") version "3.4.1"
    id("io.spring.dependency-management") version "1.1.6"
    java
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}
```

The `io.spring.dependency-management` plugin imports the Spring Boot BOM automatically — no version numbers needed for any Spring-managed dependency.

## 2. Why & when

Gradle is the build system of choice for Android and is preferred by many backend teams for its incremental compilation, caching, and performance advantages over Maven on large projects. Spring Boot supports Gradle equally to Maven.

**Use Gradle when:**
- Your team already uses Gradle.
- You need fine-grained incremental builds (Gradle's build cache is more powerful than Maven's).
- You are building Android alongside server-side code.
- You prefer a concise, programmable DSL over XML.

The `io.spring.dependency-management` plugin replicates Maven's BOM import behaviour. Without it you would need to specify every Spring library version manually.

**Alternative: Gradle's native BOM support** (no plugin needed, Gradle 5.0+):
```kotlin
dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:3.4.1"))
    implementation("org.springframework.boot:spring-boot-starter-web")
}
```
This uses Gradle's `platform()` directive to import the BOM, bypassing the need for `io.spring.dependency-management`. The result is identical; the plugin approach is more common in Spring documentation because it mirrors the Maven parent-POM experience.

## 3. Core concept

The `org.springframework.boot` plugin adds three key capabilities:

1. **Fat JAR / bootJar task:** replaces the standard `jar` task with `bootJar`, which builds a self-contained executable JAR with all dependencies nested at `BOOT-INF/lib/`. Run with `java -jar build/libs/app.jar`.

2. **`bootRun` task:** starts the application directly from Gradle using the project's classpath (no JAR needed). Equivalent to Maven's `spring-boot:run`.

3. **`bootBuildImage` task:** builds a Docker OCI image using Cloud Native Buildpacks without writing a `Dockerfile`. Requires Docker.

Key Gradle tasks for Spring Boot:

| Task | Equivalent Maven goal | What it does |
|---|---|---|
| `./gradlew bootRun` | `mvn spring-boot:run` | Starts the app |
| `./gradlew build` | `mvn package` | Compiles, tests, builds fat JAR |
| `./gradlew bootJar` | `mvn package -DskipTests` | Builds fat JAR only |
| `./gradlew bootBuildImage` | (no equivalent) | Builds Docker OCI image |
| `./gradlew dependencies` | `mvn dependency:tree` | Shows dependency tree |
| `./gradlew test` | `mvn test` | Runs unit tests |

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Gradle Spring Boot plugin flow from build.gradle through plugin and BOM to fat JAR output">
  <defs>
    <marker id="ga" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- build.gradle -->
  <rect x="10" y="80" width="150" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">build.gradle</text>
  <text x="85" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">plugins { sb 3.4.1 }</text>
  <text x="85" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">impl starter-web</text>
  <text x="85" y="152" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">testImpl starter-test</text>

  <!-- Plugins -->
  <rect x="200" y="45" width="165" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="282" y="62" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot plugin</text>
  <text x="282" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bootJar, bootRun, bootBuildImage</text>

  <rect x="200" y="105" width="165" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="282" y="122" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">dependency-management</text>
  <text x="282" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">imports spring-boot-dependencies BOM</text>

  <!-- Resolved deps -->
  <rect x="415" y="45" width="270" height="105" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="66" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Resolved at version</text>
  <text x="550" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring-webmvc:6.1.4</text>
  <text x="550" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jackson-databind:2.17.2</text>
  <text x="550" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tomcat-embed-core:10.1.19</text>
  <text x="550" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hibernate-core:6.4.4</text>
  <text x="550" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(all from BOM — no versions in build.gradle)</text>

  <!-- Fat JAR output -->
  <rect x="200" y="170" width="165" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="282" y="188" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">./gradlew bootJar</text>
  <text x="282" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">build/libs/app-1.0.jar</text>

  <!-- Arrows -->
  <line x1="160" y1="110" x2="198" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="160" y1="130" x2="198" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="365" y1="100" x2="413" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="282" y1="150" x2="282" y2="168" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
</svg>

Two plugins do the work: `spring-boot` adds tasks, `dependency-management` adds the BOM. Both together let you write starters without versions.

## 5. Runnable example

A notification service built with Spring Boot / Gradle patterns — the same service grows through three levels of build configuration.

### Level 1 — Basic

Minimal Gradle setup equivalent to `start.spring.io` output.

```java
// GradleDemo.java — run with: java GradleDemo.java
// Shows the minimal Gradle build file and Spring Boot application structure.

public class GradleDemo {

    // build.gradle.kts (Kotlin DSL — preferred for new projects):
    /*
    plugins {
        id("org.springframework.boot") version "3.4.1"
        id("io.spring.dependency-management") version "1.1.6"
        kotlin("jvm") version "1.9.22"
        kotlin("plugin.spring") version "1.9.22"
    }

    group = "com.example"
    version = "1.0-SNAPSHOT"

    java {
        sourceCompatibility = JavaVersion.VERSION_17
    }

    dependencies {
        implementation("org.springframework.boot:spring-boot-starter-web")
        testImplementation("org.springframework.boot:spring-boot-starter-test")
    }

    tasks.withType<Test> {
        useJUnitPlatform()
    }
    */

    // Equivalent Java (non-Kotlin) build.gradle.kts:
    /*
    plugins {
        id("org.springframework.boot") version "3.4.1"
        id("io.spring.dependency-management") version "1.1.6"
        java
    }

    dependencies {
        implementation("org.springframework.boot:spring-boot-starter-web")
        testImplementation("org.springframework.boot:spring-boot-starter-test")
    }
    */

    record Notification(String to, String message) {}

    static class NotificationService {
        java.util.List<String> sent = new java.util.ArrayList<>();
        void send(Notification n) {
            sent.add("→ " + n.to() + ": " + n.message());
            System.out.println("Sent: " + n.to() + " | " + n.message());
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Gradle + Spring Boot — Level 1 ===\n");
        System.out.println("Directory structure:");
        System.out.println("  build.gradle.kts");
        System.out.println("  settings.gradle.kts  → rootProject.name = \"notification-service\"");
        System.out.println("  src/main/java/com/example/");
        System.out.println("    NotificationApplication.java  (@SpringBootApplication)");
        System.out.println("    NotificationService.java      (@Service)");
        System.out.println("    NotificationController.java   (@RestController)");
        System.out.println("  src/main/resources/application.properties");
        System.out.println("  src/test/java/...");
        System.out.println();
        System.out.println("Key tasks:");
        System.out.println("  ./gradlew bootRun    — start the app");
        System.out.println("  ./gradlew build      — compile + test + bootJar");
        System.out.println("  ./gradlew test       — run JUnit 5 tests");

        System.out.println("\nSimulated notification flow:");
        NotificationService svc = new NotificationService();
        svc.send(new Notification("alice@example.com", "Order confirmed"));
        svc.send(new Notification("bob@example.com",   "Shipment dispatched"));
        System.out.println("Total sent: " + svc.sent.size());
    }
}
```

How to run: `java GradleDemo.java`

`settings.gradle.kts` only needs `rootProject.name`. The Kotlin DSL is recommended for new projects because it gives IDE completion and type-safety inside the build script.

### Level 2 — Intermediate

Multi-project Gradle build + extra configuration (Docker image task, custom JVM args).

```java
// GradleDemoV2.java — run with: java GradleDemoV2.java
// Shows multi-project Gradle build and common Spring Boot plugin configuration.

import java.util.*;

public class GradleDemoV2 {

    // settings.gradle.kts for a multi-module project:
    /*
    rootProject.name = "notification-platform"
    include("notification-api", "notification-service", "notification-gateway")
    */

    // Root build.gradle.kts (shared config):
    /*
    plugins {
        id("org.springframework.boot") version "3.4.1" apply false  // applied per-module
        id("io.spring.dependency-management") version "1.1.6" apply false
    }
    subprojects {
        apply(plugin = "io.spring.dependency-management")
        dependencyManagement {
            imports { mavenBom("org.springframework.boot:spring-boot-dependencies:3.4.1") }
        }
    }
    */

    // notification-service/build.gradle.kts:
    /*
    plugins {
        id("org.springframework.boot")
        java
    }
    dependencies {
        implementation("org.springframework.boot:spring-boot-starter-web")
        implementation("org.springframework.boot:spring-boot-starter-data-jpa")
        implementation(project(":notification-api"))
        runtimeOnly("com.h2database:h2")
        testImplementation("org.springframework.boot:spring-boot-starter-test")
    }

    // Configure bootJar fat JAR metadata
    tasks.bootJar {
        archiveFileName.set("notification-service.jar")
        manifest {
            attributes["Implementation-Version"] = project.version
        }
    }

    // Configure bootRun JVM options
    tasks.bootRun {
        jvmArgs("-Xmx512m", "-Dspring.profiles.active=dev")
    }

    // Build Docker OCI image via Cloud Native Buildpacks (no Dockerfile needed)
    tasks.bootBuildImage {
        imageName.set("notification-service:${project.version}")
        environment.set(mapOf("BP_JVM_VERSION" to "17"))
    }
    */

    record Module(String name, boolean hasBootPlugin, List<String> deps) {}

    public static void main(String[] args) {
        List<Module> modules = List.of(
            new Module("notification-api",
                false,
                List.of("Plain Java — domain records, interfaces (no Spring starters)")),
            new Module("notification-service",
                true,
                List.of("spring-boot-starter-web", "spring-boot-starter-data-jpa",
                    "project(:notification-api)", "h2 (runtimeOnly)")),
            new Module("notification-gateway",
                true,
                List.of("spring-boot-starter-webflux", "spring-cloud-starter-gateway"))
        );

        System.out.println("=== Multi-project Gradle build ===\n");
        for (Module m : modules) {
            System.out.printf("Module: %-30s Spring Boot plugin: %s%n", m.name(), m.hasBootPlugin() ? "YES" : "no");
            m.deps().forEach(d -> System.out.println("  dep: " + d));
            System.out.println();
        }

        System.out.println("Build commands:");
        System.out.println("  ./gradlew build                             — build all modules");
        System.out.println("  ./gradlew :notification-service:bootRun     — run service only");
        System.out.println("  ./gradlew :notification-service:bootJar     — fat JAR for service");
        System.out.println("  ./gradlew :notification-service:bootBuildImage — Docker OCI image");
        System.out.println("  ./gradlew :notification-api:jar             — plain JAR for API module");

        System.out.println("\nGradle caching advantage:");
        System.out.println("  Unchanged modules are not recompiled — Gradle's build cache");
        System.out.println("  means a change in notification-service does not rebuild api.");
        System.out.println("  CI can share the build cache across machines for faster pipelines.");
    }
}
```

How to run: `java GradleDemoV2.java`

`apply false` in the root `plugins` block registers the plugin version without applying it. Each sub-module opts in with `apply(plugin = "org.springframework.boot")`. This prevents the `bootJar` task from appearing in the API module (which should produce a plain JAR).

### Level 3 — Advanced

Custom Spring Boot Gradle plugin configuration: conditional profiles, Gradle build cache integration, dependency constraints, and the `bootBuildImage` + OCI metadata.

```java
// GradleDemoV3.java — run with: java GradleDemoV3.java
// Full advanced Gradle config: profiles, constraints, Docker OCI, build cache.

import java.util.*;

public class GradleDemoV3 {

    // Full notification-service/build.gradle.kts:
    /*
    plugins {
        id("org.springframework.boot")
        id("io.spring.dependency-management")
        java
    }

    group = "com.example"
    version = "2.0.0"

    java { sourceCompatibility = JavaVersion.VERSION_17 }

    configurations {
        compileOnly { extendsFrom(configurations.annotationProcessor.get()) }
    }

    dependencies {
        implementation("org.springframework.boot:spring-boot-starter-web")
        implementation("org.springframework.boot:spring-boot-starter-data-jpa")
        implementation("org.springframework.boot:spring-boot-starter-actuator")
        implementation("io.micrometer:micrometer-registry-prometheus")

        compileOnly("org.projectlombok:lombok")
        annotationProcessor("org.projectlombok:lombok")

        runtimeOnly("org.postgresql:postgresql")

        testImplementation("org.springframework.boot:spring-boot-starter-test")
        testImplementation("com.h2database:h2")       // H2 for tests only

        // Explicit version constraint (override BOM default)
        constraints {
            implementation("org.postgresql:postgresql:42.7.3") {
                because("CVE fix: 42.7.3 patches connection-string injection")
            }
        }
    }

    tasks.bootRun {
        args("--spring.profiles.active=local")
        jvmArgs("-Xms256m", "-Xmx512m", "-Dfile.encoding=UTF-8")
    }

    tasks.bootJar {
        archiveFileName.set("notification-service.jar")
        layered {
            application {
                intoLayer("spring-boot-loader") { include("org/springframework/boot/loader/**") }
                intoLayer("application")
            }
            dependencies {
                intoLayer("snapshot-dependencies") { include("*:*:*SNAPSHOT") }
                intoLayer("dependencies")
            }
            layerOrder.addAll("dependencies", "spring-boot-loader",
                              "snapshot-dependencies", "application")
        }
    }

    tasks.bootBuildImage {
        imageName.set("notification-service:${project.version}")
        environment.set(mapOf(
            "BP_JVM_VERSION" to "17",
            "BP_SPRING_CLOUD_BINDINGS_DISABLED" to "true"
        ))
        buildCache {
            volume {
                name.set("gradle-build-cache")
                // CI shares this volume across agents for layer caching
            }
        }
    }

    // Gradle build cache (gradle.properties):
    // org.gradle.caching=true
    // org.gradle.parallel=true
    // org.gradle.daemon=true
    */

    record BuildPhase(String phase, String gradleTask, String output, String notes) {}

    public static void main(String[] args) {
        System.out.println("=== Advanced Gradle + Spring Boot build ===\n");

        List<BuildPhase> phases = List.of(
            new BuildPhase("compile", "compileJava",
                "build/classes/ — compilation cache keyed on source hash",
                "Cached: unchanged classes not recompiled"),
            new BuildPhase("test", "test",
                "build/reports/tests/ (HTML) + build/test-results/ (XML)",
                "H2 for tests; PostgreSQL for runtime (runtimeOnly)"),
            new BuildPhase("fat JAR", "bootJar",
                "build/libs/notification-service.jar — layered layout",
                "Layered JAR for Docker: dependencies layer cached across builds"),
            new BuildPhase("Docker image", "bootBuildImage",
                "Docker local registry: notification-service:2.0.0",
                "Cloud Native Buildpacks — no Dockerfile; JRE auto-selected"),
            new BuildPhase("run local", "bootRun",
                "http://localhost:8080 — profile=local",
                "JVM args from tasks.bootRun; no fat JAR needed")
        );

        System.out.printf("%-12s %-22s %-45s%n", "Phase", "Task", "Output");
        System.out.println("-".repeat(82));
        phases.forEach(p -> System.out.printf("%-12s %-22s %-45s%n   %s%n%n",
            p.phase(), p.gradleTask(), p.output(), "Note: " + p.notes()));

        System.out.println("=== Dependency constraints (version override) ===");
        System.out.println("  constraints { implementation(\"org.postgresql:postgresql:42.7.3\") }");
        System.out.println("  → overrides BOM version 42.7.1 with security-patched 42.7.3");
        System.out.println("  → BOM still manages all other dependencies");
        System.out.println("  → 'because' string is shown in dependency insight report");
        System.out.println("     (./gradlew dependencyInsight --dependency postgresql)");

        System.out.println("\n=== Layered JAR for Docker cache efficiency ===");
        System.out.println("  Layer 1: dependencies       (rarely changes → cached in Docker)");
        System.out.println("  Layer 2: spring-boot-loader (never changes → cached)");
        System.out.println("  Layer 3: snapshot-deps      (changes often)");
        System.out.println("  Layer 4: application        (changes every build → only layer rebuilt)");
        System.out.println("  Result: Docker push sends only layer 4 on code changes");
    }
}
```

How to run: `java GradleDemoV3.java`

Layered JARs are the key Docker optimisation: each Docker `COPY` instruction corresponds to one JAR layer. Dependencies change only when `build.gradle` changes; the application layer changes on every code change. Kubernetes deployments push only the changed layer, cutting push times from minutes to seconds.

## 6. Walkthrough

**`./gradlew bootJar` execution flow:**

1. **`compileJava`** — Gradle checks its build cache. If no source files changed since the last build, the cached class files are restored and `compileJava` is skipped. Cache key is a hash of source files + compiler options.

2. **`processResources`** — copies `src/main/resources/` to `build/resources/main/`. `application.properties` is copied as-is.

3. **`bootJar`** — assembles the fat JAR:
   - `BOOT-INF/classes/` ← compiled application classes.
   - `BOOT-INF/lib/` ← all `implementation` and `runtimeOnly` JARs. No `testImplementation` JARs.
   - `org/springframework/boot/loader/` ← the JarLauncher class.
   - `META-INF/MANIFEST.MF` → `Main-Class: org.springframework.boot.loader.launch.JarLauncher`, `Start-Class: com.example.NotificationApplication`.

4. **`java -jar build/libs/notification-service.jar`** — JVM loads `JarLauncher`. JarLauncher creates a `LaunchedURLClassLoader` that reads from `BOOT-INF/` inside the JAR. It then calls `NotificationApplication.main()`, which calls `SpringApplication.run()`, which starts `ApplicationContext`, auto-configures everything, and starts embedded Tomcat on port 8080.

**Constraint override flow (Level 3):**
```
BOM declares: org.postgresql:postgresql:42.7.1
constraints block:  org.postgresql:postgresql:42.7.3

→ Gradle conflict resolution: constraint wins over BOM
→ ./gradlew dependencyInsight --dependency postgresql shows:
    postgresql:42.7.3 (forced by constraint: CVE fix)
```

**Docker image build (`bootBuildImage`):**
1. Gradle calls Paketo Buildpacks via the Docker daemon.
2. Buildpacks detect `BOOT-INF/` → selects the Spring Boot buildpack.
3. `BP_JVM_VERSION=17` → selects JDK/JRE 17 base image.
4. Buildpacks produce an OCI image with optimal layer ordering.
5. Image pushed to local Docker registry as `notification-service:2.0.0`.

## 7. Gotchas & takeaways

> **`io.spring.dependency-management` plugin vs `platform()` BOM import.** The plugin approach (`id("io.spring.dependency-management")`) applies the BOM globally to all Gradle configurations. The `platform()` approach applies only to the configuration you declare it in. For most Spring Boot projects the plugin is simpler; for multi-project builds where you need per-configuration control, `platform()` is more explicit.

> **`bootRun` uses the development classpath, not the fat JAR.** `./gradlew bootRun` starts the app with all `implementation` and `runtimeOnly` dependencies on the classpath directly (no JAR packing). This is faster to start and supports Gradle's continuous build mode (`--continuous` flag for auto-restart on file change).

- Kotlin DSL (`build.gradle.kts`) is preferred for new projects: IDE completion, refactoring support, type safety. Groovy DSL (`build.gradle`) still works but lacks tooling.
- `./gradlew bootRun --args='--server.port=9090'` passes Spring application arguments at the command line — same as `java -jar app.jar --server.port=9090`.
- Gradle wrapper (`gradlew` / `gradlew.bat`) pins the Gradle version. Commit `gradle/wrapper/gradle-wrapper.properties` to version control; never rely on a globally installed Gradle.
- `./gradlew :notification-service:dependencies --configuration implementation` shows only the compile-time dependency tree for a specific module.
- `./gradlew bootBuildImage` requires a running Docker daemon. For CI environments without Docker, build the fat JAR and let the CI platform build the image with a `Dockerfile`.
