---
card: spring-boot
gi: 235
slug: layertools-extracting-layers
title: Layertools & extracting layers
---

## 1. What it is

`layertools` is a built-in jar mode in Spring Boot's executable JAR. Running `java -Djarmode=layertools -jar myapp.jar` activates a small CLI that can list layers and extract them into separate directories. It is used inside a multi-stage Dockerfile to split the fat JAR into individual Docker layers before `COPY`ing each one into the final image.

## 2. Why & when

Building a Docker image from a fat JAR in a single `COPY` instruction copies everything as one layer. Even a one-line code change forces Docker to push the entire 100 MB blob. The `layertools extract` command is the bridge between a layered JAR and an optimally layered Docker image — you call it in the build stage, then `COPY --from=build` each directory in a separate instruction.

## 3. Core concept

`layertools` supports two sub-commands:

```
list    — print the layers defined in BOOT-INF/layers.idx
extract — extract each layer into a named subdirectory
```

After `extract`, you get directories named after each layer:

```
./dependencies/
./spring-boot-loader/
./snapshot-dependencies/
./application/
```

A multi-stage Dockerfile uses the builder image to extract, then the runtime image to `COPY` each directory as a separate layer:

```dockerfile
FROM eclipse-temurin:21-jre AS builder
WORKDIR /app
COPY target/myapp.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="300" fill="#1c2430" rx="10"/>
  <!-- Stage 1 -->
  <rect x="20" y="30" width="270" height="240" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="58" text-anchor="middle" fill="#8b949e">Stage 1: builder</text>
  <rect x="35" y="70" width="240" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="155" y="93" text-anchor="middle" fill="#e6edf3" font-size="12">COPY myapp.jar</text>
  <rect x="35" y="115" width="240" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="138" text-anchor="middle" fill="#6db33f" font-size="12">layertools extract</text>
  <rect x="35" y="160" width="240" height="90" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="155" y="182" text-anchor="middle" fill="#8b949e" font-size="11">./dependencies/</text>
  <text x="155" y="200" text-anchor="middle" fill="#8b949e" font-size="11">./spring-boot-loader/</text>
  <text x="155" y="218" text-anchor="middle" fill="#8b949e" font-size="11">./snapshot-dependencies/</text>
  <text x="155" y="236" text-anchor="middle" fill="#6db33f" font-size="11">./application/</text>
  <!-- Arrow -->
  <line x1="292" y1="150" x2="318" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#a9)"/>
  <!-- Stage 2 -->
  <rect x="320" y="30" width="300" height="240" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="470" y="58" text-anchor="middle" fill="#6db33f">Stage 2: runtime image</text>
  <rect x="335" y="70" width="270" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="91" text-anchor="middle" fill="#8b949e" font-size="12">COPY --from=builder dependencies/ ✓ cached</text>
  <rect x="335" y="108" width="270" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="129" text-anchor="middle" fill="#8b949e" font-size="12">COPY --from=builder loader/         ✓ cached</text>
  <rect x="335" y="146" width="270" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="167" text-anchor="middle" fill="#8b949e" font-size="12">COPY --from=builder snapshot-deps/  ✓ cached</text>
  <rect x="335" y="184" width="270" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="205" text-anchor="middle" fill="#6db33f" font-size="12">COPY --from=builder application/  ← rebuilt</text>
  <rect x="335" y="222" width="270" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="245" text-anchor="middle" fill="#79c0ff" font-size="12">ENTRYPOINT [java, JarLauncher]</text>
  <defs>
    <marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`layertools extract` splits the JAR; each `COPY` becomes a cached Docker layer._

## 5. Runnable example

```java
// File: LayertoolsDemo.java
// How to run: java LayertoolsDemo.java
// Shows the layertools commands and expected output format.
// To really run layertools: java -Djarmode=layertools -jar myapp.jar list

import java.io.File;

public class LayertoolsDemo {

    public static void main(String[] args) throws Exception {
        System.out.println("=== layertools list (expected output) ===");
        System.out.println("dependencies");
        System.out.println("spring-boot-loader");
        System.out.println("snapshot-dependencies");
        System.out.println("application");

        System.out.println("\n=== layertools extract (run then inspect) ===");
        System.out.println("Command: java -Djarmode=layertools -jar myapp.jar extract");
        System.out.println("Creates directories:");
        String[] layers = {"dependencies", "spring-boot-loader", "snapshot-dependencies", "application"};
        for (String layer : layers) {
            System.out.printf("  ./%s/%n", layer);
        }

        System.out.println("\n=== Verify extraction (simulated) ===");
        // In a real run after extract, check the directories exist
        for (String layer : layers) {
            File dir = new File(layer);
            System.out.printf("  %s: %s%n", layer, dir.exists() ? "EXISTS" : "(not yet extracted)");
        }

        System.out.println("\n=== Dockerfile pattern ===");
        System.out.println("FROM eclipse-temurin:21-jre AS builder");
        System.out.println("WORKDIR /app");
        System.out.println("COPY target/myapp.jar app.jar");
        System.out.println("RUN java -Djarmode=layertools -jar app.jar extract");
        System.out.println();
        System.out.println("FROM eclipse-temurin:21-jre");
        System.out.println("WORKDIR /app");
        for (String layer : layers) {
            System.out.printf("COPY --from=builder /app/%s/ ./%n", layer);
        }
        System.out.println("ENTRYPOINT [\"java\", \"org.springframework.boot.loader.launch.JarLauncher\"]");
    }
}
```

**How to run:** `java LayertoolsDemo.java` — prints the expected layertools output and Dockerfile template. For real extraction: `java -Djarmode=layertools -jar target/myapp.jar extract`.

## 6. Walkthrough

1. `java -Djarmode=layertools -jar myapp.jar list` — activates the layertools mode; prints layer names from `BOOT-INF/layers.idx` in order (lowest to highest change frequency).
2. `java -Djarmode=layertools -jar myapp.jar extract` — extracts each layer into a corresponding directory in the current working directory.
3. In the Dockerfile builder stage, these commands run before the final image is assembled.
4. Each `COPY --from=builder /app/<layer>/ ./` in the runtime stage becomes a distinct Docker layer. Docker caches layers by content hash — unchanged layers are never re-transmitted to the registry.
5. `ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]` — starts the app using the launcher, which finds classes from the extracted directories now on the classpath.

## 7. Gotchas & takeaways

> `layertools` is embedded in the Boot JAR itself (in `BOOT-INF/` or at the root for some versions). It is NOT a separate tool to install — it activates via `-Djarmode=layertools`.

> The extract command writes to the **current directory**. In a Dockerfile `RUN` instruction the working directory (`WORKDIR`) must be set before running extract, or the layers land in the filesystem root.

> `ENTRYPOINT` in the runtime image must use `JarLauncher` explicitly — there is no `app.jar` in the runtime stage, only extracted directories.

- Use `extract --destination /target-dir` to write to a specific path instead of the current directory.
- The pattern works identically with `WarLauncher` for WAR deployments.
- Combine with Docker BuildKit (`DOCKER_BUILDKIT=1`) for parallel layer builds and better caching.
- Buildpacks (`spring-boot:build-image`) do all of this automatically — you only need the manual Dockerfile approach for full Dockerfile control.
