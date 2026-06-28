---
card: spring-boot
gi: 239
slug: dockerfiles-layered-images
title: Dockerfiles & layered images
---

## 1. What it is

A Dockerfile is a text recipe that defines the steps for building a Docker container image. Combined with Spring Boot's layered JAR format, a multi-stage Dockerfile produces an optimally cached image: a builder stage extracts layers from the fat JAR, and a minimal runtime stage copies each extracted directory as its own Docker layer.

## 2. Why & when

Use a hand-crafted Dockerfile when you need fine-grained control over the build — custom JVM arguments, non-root users, specific base image versions, additional native tools, or bespoke startup scripts. If full control is not needed, `spring-boot:build-image` (Buildpacks) is simpler. Choose a Dockerfile when Buildpacks cannot accommodate your requirements.

## 3. Core concept

Multi-stage Dockerfile flow for Spring Boot:

1. **Stage 1 (builder)** — JRE image, copy fat JAR, run `layertools extract`.
2. **Stage 2 (runtime)** — minimal JRE image, `COPY --from=builder` each layer directory, set `ENTRYPOINT`.

Only Stage 2 ends up in the final image; the builder stage is discarded. Each `COPY` instruction in Stage 2 becomes an independent Docker layer:

```
Image layer 1: base JRE (eclipse-temurin:21-jre-alpine) — never changes
Image layer 2: COPY dependencies/     — changes when pom.xml changes
Image layer 3: COPY spring-boot-loader/ — changes on Boot version bump
Image layer 4: COPY snapshot-dependencies/ — changes for SNAPSHOT deps
Image layer 5: COPY application/      — changes on every code commit
```

On a typical code commit, only layer 5 (~100 KB) needs pushing to the registry.

## 4. Diagram

<svg viewBox="0 0 640 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="290" fill="#1c2430" rx="10"/>
  <!-- Stage 1 -->
  <rect x="20" y="30" width="240" height="130" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="56" text-anchor="middle" fill="#8b949e">Stage 1 (builder)</text>
  <rect x="35" y="68" width="210" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="87" text-anchor="middle" fill="#e6edf3" font-size="12">eclipse-temurin:21-jre</text>
  <rect x="35" y="102" width="210" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="121" text-anchor="middle" fill="#8b949e" font-size="12">COPY myapp.jar</text>
  <rect x="35" y="136" width="210" height="20" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="151" text-anchor="middle" fill="#6db33f" font-size="12">layertools extract</text>
  <!-- Arrow -->
  <line x1="260" y1="145" x2="295" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#ac)"/>
  <text x="277" y="138" text-anchor="middle" fill="#8b949e" font-size="11">discarded</text>
  <!-- Stage 2 -->
  <rect x="300" y="30" width="320" height="245" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="56" text-anchor="middle" fill="#6db33f">Stage 2 (runtime image)</text>
  <rect x="315" y="68" width="290" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="87" text-anchor="middle" fill="#8b949e" font-size="12">eclipse-temurin:21-jre-alpine  ← base layer</text>
  <rect x="315" y="102" width="290" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="118" text-anchor="middle" fill="#8b949e" font-size="12">COPY dependencies/   ✓ cached</text>
  <rect x="315" y="130" width="290" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="146" text-anchor="middle" fill="#8b949e" font-size="12">COPY spring-boot-loader/  ✓ cached</text>
  <rect x="315" y="158" width="290" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="174" text-anchor="middle" fill="#8b949e" font-size="12">COPY snapshot-dependencies/  (sometimes)</text>
  <rect x="315" y="186" width="290" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="460" y="202" text-anchor="middle" fill="#6db33f" font-size="12">COPY application/  ← rebuilt every commit</text>
  <rect x="315" y="214" width="290" height="22" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="230" text-anchor="middle" fill="#79c0ff" font-size="12">ENTRYPOINT [java, JarLauncher]</text>
  <text x="460" y="262" text-anchor="middle" fill="#8b949e" font-size="11">only application layer is pushed per commit</text>
  <defs>
    <marker id="ac" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_Multi-stage Dockerfile: builder extracts layers, runtime image caches all but `application/`._

## 5. Runnable example

```java
// File: DockerfileGenerator.java
// How to run: java DockerfileGenerator.java [app-name] [java-version]
// Example:    java DockerfileGenerator.java myservice 21
// Prints an optimised multi-stage Dockerfile for a Spring Boot app.

public class DockerfileGenerator {

    public static void main(String[] args) {
        String appName = args.length > 0 ? args[0] : "myapp";
        String javaVersion = args.length > 1 ? args[1] : "21";
        String baseImage = "eclipse-temurin:" + javaVersion + "-jre-alpine";

        String dockerfile = """
                # ======================================================
                # Multi-stage Spring Boot Dockerfile
                # Generated for: %s (Java %s)
                # ======================================================

                # ---- Stage 1: Layer extraction ----
                FROM eclipse-temurin:%s-jre AS builder
                WORKDIR /app
                COPY target/%s.jar app.jar
                RUN java -Djarmode=layertools -jar app.jar extract --destination /extracted

                # ---- Stage 2: Minimal runtime image ----
                FROM %s
                WORKDIR /app

                # Non-root user
                RUN addgroup -S spring && adduser -S spring -G spring
                USER spring:spring

                # Layers from least to most frequently changed
                COPY --from=builder /extracted/dependencies/ ./
                COPY --from=builder /extracted/spring-boot-loader/ ./
                COPY --from=builder /extracted/snapshot-dependencies/ ./
                COPY --from=builder /extracted/application/ ./

                ENV JAVA_TOOL_OPTIONS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75"
                EXPOSE 8080
                ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
                """.formatted(appName, javaVersion, javaVersion, appName, baseImage);

        System.out.println(dockerfile);
        System.out.println("# Build:  docker build -t " + appName + " .");
        System.out.println("# Run:    docker run -p 8080:8080 " + appName);
    }
}
```

**How to run:** `java DockerfileGenerator.java myservice 21` — generates an optimised Dockerfile for `myservice`.

## 6. Walkthrough

1. **Stage 1 (`builder`)** — uses `eclipse-temurin:21-jre` (doesn't need JDK for extraction). Copies the fat JAR and runs `layertools extract --destination /extracted`, placing each layer in a subdirectory.
2. **Stage 2 (`runtime`)** — starts from `eclipse-temurin:21-jre-alpine` (smaller). The builder stage is not included in the final image.
3. **Non-root user** — `addgroup/adduser` creates a dedicated `spring` user. `USER spring:spring` drops privileges before any `COPY` or `ENTRYPOINT`.
4. **Four `COPY --from=builder`** — each maps to a Docker image layer. Docker computes a hash of each layer's content; unchanged layers are cache hits and never re-uploaded.
5. **`JAVA_TOOL_OPTIONS`** — applies JVM flags globally (also caught by JVM launched by scripts inside the container). `UseContainerSupport` reads cgroup limits; `MaxRAMPercentage=75` prevents OOM.
6. **`ENTRYPOINT`** — exec-form (JSON array) avoids a shell wrapper, so signals like `SIGTERM` reach the JVM directly for graceful shutdown.

## 7. Gotchas & takeaways

> Exec-form `ENTRYPOINT ["java", "..."]` vs. shell-form `ENTRYPOINT java ...`: shell-form wraps in `/bin/sh -c`, which becomes the PID 1 — Docker `stop` sends `SIGTERM` to the shell, not the JVM, and graceful shutdown may not trigger. Always use exec-form.

> The order of `COPY` instructions determines Docker cache invalidation. Putting the most-stable layer first (dependencies) and least-stable last (application) is critical — reversing the order defeats the cache.

> `--destination /extracted` in `layertools extract` writes to an explicit path, avoiding working-directory confusion in complex multi-stage builds.

- `docker build --progress=plain .` shows which layers hit the cache (`CACHED`) vs. rebuild.
- `.dockerignore` should exclude `target/*.jar.original`, `src/`, `.git/`, etc. to keep the build context small.
- For secrets in build steps, use Docker BuildKit's `--secret` flag — never `ARG`/`ENV` for credentials.
- Combine with `HEALTHCHECK` instruction so Kubernetes readiness probes align with Docker's built-in health reporting.
