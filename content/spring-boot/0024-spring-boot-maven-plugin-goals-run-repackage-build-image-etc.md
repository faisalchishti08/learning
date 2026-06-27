---
card: spring-boot
gi: 24
slug: spring-boot-maven-plugin-goals-run-repackage-build-image-etc
title: Spring Boot Maven plugin (goals: run, repackage, build-image, etc.)
---

## 1. What it is

The **Spring Boot Maven plugin** (`spring-boot-maven-plugin`) is the Maven plugin that bridges your Maven project and Spring Boot's packaging and runtime needs. It provides specific *goals* — Maven tasks you can run directly or that are bound to build phases.

**Key goals:**

| Goal | Command | What it does |
|---|---|---|
| `spring-boot:run` | `./mvnw spring-boot:run` | Compiles and runs the app in the same JVM as Maven |
| `spring-boot:repackage` | (auto-runs on `./mvnw package`) | Repackages the thin JAR into a fat JAR with all dependencies |
| `spring-boot:build-image` | `./mvnw spring-boot:build-image` | Builds a layered OCI/Docker image using Buildpacks |
| `spring-boot:build-info` | (bind to generate-resources phase) | Writes `build-info.properties` read by Actuator's `/info` |
| `spring-boot:start` / `stop` | Used in integration tests | Starts the app as a background process |

The plugin is shipped as part of Spring Boot itself and versioned together with it (`3.3.4` plugin for Spring Boot 3.3.4).

## 2. Why & when

**`spring-boot:run`** vs `java -jar`:
- `spring-boot:run` runs without packaging — fast iteration in development. It uses Maven's classpath directly, including `src/main/resources` as a live directory.
- `java -jar` runs the packaged fat JAR. Use in CI, staging, production.

**`spring-boot:repackage`** is the most important goal. Without it, `mvn package` produces a thin JAR that can't run standalone (it's missing all dependency JARs). The plugin's `repackage` goal transforms it into a self-contained fat JAR. By default it's already bound to the `package` lifecycle phase when you inherit `spring-boot-starter-parent`, so `mvn package` triggers it automatically.

**`spring-boot:build-image`** is the Dockerless Docker build — it uses Cloud Native Buildpacks to produce an OCI image without requiring Docker or a `Dockerfile`. The image is layered correctly for Spring Boot (base layer → dependencies layer → application layer), making CI rebuilds fast because only the application layer changes on each build.

## 3. Core concept

**Lifecycle binding:**

The `repackage` goal is bound to Maven's `package` phase:

```
mvn package
  → compile (javac)
  → test (surefire)
  → package (jar:jar → thin JAR first, then spring-boot:repackage replaces it with fat JAR)
```

`spring-boot:run` doesn't touch the lifecycle — it compiles and runs in one shot, skipping the JAR creation entirely.

**`spring-boot:run` properties:**
```bash
# Skip tests and run faster
./mvnw spring-boot:run -DskipTests

# Pass Spring Boot arguments (e.g., activate profile)
./mvnw spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=dev"

# Pass JVM arguments
./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-Xmx256m"
```

**`build-image` customisation** in `pom.xml`:
```xml
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
  <configuration>
    <image>
      <name>my-registry.example.com/order-service:${project.version}</name>
    </image>
  </configuration>
</plugin>
```

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot Maven plugin goals and when each is used in the development and deployment workflow">
  <!-- Title -->
  <text x="330" y="22" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot Maven Plugin — Goal Map</text>

  <!-- Development path -->
  <rect x="20" y="36" width="200" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="58" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Development</text>
  <rect x="36" y="68" width="168" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="120" y="87" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">./mvnw spring-boot:run</text>
  <text x="120" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Fast: no fat JAR produced</text>

  <!-- Arrow -->
  <line x1="220" y1="76" x2="260" y2="120" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2"/>

  <!-- Production build path -->
  <rect x="230" y="36" width="200" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="58" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">CI / Production JAR</text>
  <rect x="246" y="68" width="168" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="330" y="87" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">./mvnw package</text>
  <text x="330" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot:repackage auto-runs</text>

  <!-- Arrow -->
  <line x1="330" y1="116" x2="330" y2="152" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Docker image path -->
  <rect x="440" y="36" width="200" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="58" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Docker / Container</text>
  <rect x="456" y="68" width="168" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="540" y="87" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">./mvnw build-image</text>
  <text x="540" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Buildpacks, no Dockerfile</text>

  <!-- Bottom outputs -->
  <rect x="120" y="152" width="420" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="172" fill="#e6edf3" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Outputs</text>
  <text x="180" y="196" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">target/*.jar (fat JAR)</text>
  <text x="330" y="196" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">|</text>
  <text x="470" y="196" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Docker image in local registry</text>
</svg>

Three goals for three scenarios: `run` for development speed, `package` for the deployable artifact, `build-image` for containers.

## 5. Runnable example

```java
// File: MavenPluginGoalsDemo.java
// Illustrates what each Spring Boot Maven plugin goal does.
// Run: java MavenPluginGoalsDemo.java

import java.util.*;

public class MavenPluginGoalsDemo {

    record PluginGoal(String command, String phase, String input, String output, String use) {}

    public static void main(String[] args) {
        var goals = List.of(
            new PluginGoal(
                "./mvnw spring-boot:run",
                "N/A (direct)",
                "src/main/java (compiled on-the-fly)",
                "Running process on :8080",
                "Development — skip packaging, run immediately"
            ),
            new PluginGoal(
                "./mvnw package",
                "package (auto)",
                "target/my-app.jar (thin JAR)",
                "target/my-app.jar (fat JAR, replaces thin)",
                "CI/production — repackage goal fires automatically"
            ),
            new PluginGoal(
                "./mvnw spring-boot:build-image",
                "N/A (direct)",
                "target/my-app.jar (fat JAR must exist first)",
                "OCI image in local Docker daemon",
                "Container deployment — no Dockerfile needed"
            ),
            new PluginGoal(
                "./mvnw spring-boot:build-info",
                "generate-resources",
                "pom.xml metadata",
                "target/classes/META-INF/build-info.properties",
                "Actuator /info endpoint: version, build time, git info"
            )
        );

        System.out.println("=== Spring Boot Maven Plugin Goals ===\n");

        for (var goal : goals) {
            System.out.println("Command : " + goal.command());
            System.out.println("Phase   : " + goal.phase());
            System.out.println("Input   : " + goal.input());
            System.out.println("Output  : " + goal.output());
            System.out.println("Use for : " + goal.use());
            System.out.println();
        }

        System.out.println("=== build-image output example ===");
        System.out.println("Successfully built image 'docker.io/library/my-app:0.0.1-SNAPSHOT'");
        System.out.println("Layer breakdown:");
        System.out.println("  Layer 1: run (JRE + OS)          — cached, changes rarely");
        System.out.println("  Layer 2: dependencies             — cached until deps change");
        System.out.println("  Layer 3: spring-boot-loader       — cached");
        System.out.println("  Layer 4: application (your code)  — rebuilt every time");
        System.out.println("→ Only layer 4 uploads on code-only changes");
    }
}
```

**How to run:** `java MavenPluginGoalsDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`spring-boot:run`** — the plugin compiles your sources using `maven-compiler-plugin` (if not already compiled), then forks a JVM with the full Maven classpath. This is why `src/main/resources` changes are picked up without repackaging — Maven's classpath includes the raw resources directory.
- **`package` + automatic `repackage`** — Maven's `package` phase calls `jar:jar` first (produces the thin JAR), then the `repackage` goal (bound to the same phase by the plugin) replaces it with the fat JAR. The thin JAR is archived as `*-plain.jar` so it's not lost.
- **`build-image` layer caching** — Cloud Native Buildpacks split the fat JAR into four layers. When you change only application code, only the "application" layer is rebuilt and pushed to the registry. For a 50 MB fat JAR, this might mean uploading only 100 KB instead of the full 50 MB on every CI build.
- **`build-info`** — writes a `.properties` file read by `BuildInfoEndpoint` (Actuator's `/info` endpoint). Contains `build.version`, `build.time`, `build.artifact`, `build.group`. Add `git-commit-id-maven-plugin` to also get git SHA in `/info`.

## 7. Gotchas & takeaways

> **`spring-boot:build-image` requires Docker to be running locally.** It connects to the Docker daemon to push the final image. Without Docker, the goal fails with a connection error. In Docker-free CI environments (like some GitHub Actions runners), use `spring-boot:build-image -Dspring-boot.build-image.publish=true` with a remote registry configuration.

> **`spring-boot:run` and `java -jar` use different classpaths.** `spring-boot:run` runs against the Maven compile-scope classpath; `java -jar` loads from the fat JAR's `BOOT-INF/lib/`. A class present in `test` scope only (`<scope>test</scope>`) is visible in `spring-boot:run` when run with `-Dspring-boot.run.fork=false` but not in the fat JAR. This is a source of "works locally, fails in production" bugs.

- `./mvnw package` → fat JAR ready to deploy (repackage fires automatically with starter-parent).
- `./mvnw spring-boot:run` → fastest inner-loop development command; no fat JAR produced.
- `./mvnw spring-boot:build-image` → OCI image with no Dockerfile; layered for efficient caching.
- Always match plugin version to Spring Boot version: `<version>3.3.4</version>` for Boot 3.3.4.
- Add `spring-boot:build-info` to the `generate-resources` phase to populate Actuator's `/info` endpoint automatically.
