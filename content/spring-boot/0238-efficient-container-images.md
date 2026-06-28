---
card: spring-boot
gi: 238
slug: efficient-container-images
title: Efficient container images
---

## 1. What it is

An efficient container image is one that starts fast, is small, and pushes only changed layers to a registry. For Spring Boot applications, efficiency comes from three practices: choosing a minimal base image (e.g., `eclipse-temurin:21-jre-alpine` rather than a full JDK), using layered JARs so Docker caches the dependency layer, and keeping image layer count low to minimise registry storage.

## 2. Why & when

Unoptimised Spring Boot images typically run 400-600 MB. Pulling such an image on a cold node adds tens of seconds to startup time in Kubernetes. Efficient images mean faster pod scheduling, lower registry costs, smaller attack surface, and quicker CI feedback loops. Every team running Boot in containers should apply these practices.

## 3. Core concept

Key decisions for image efficiency:

| Decision | Inefficient | Efficient |
|---|---|---|
| Base image | Full JDK (500 MB) | JRE-only or Distroless (200 MB) |
| Layer strategy | Single fat-JAR layer | Layered JAR — deps cached |
| Build stage | One stage | Multi-stage (builder + runtime) |
| JVM flags | None | `-XX:+UseContainerSupport` (default JDK 17+) |
| App model | Fat JAR | Exploded or native image |

`-XX:+UseContainerSupport` (on by default in JDK 8u191+ and JDK 10+) reads cgroup CPU and memory limits instead of host values, preventing the JVM from allocating more heap than the container is allowed.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="280" fill="#1c2430" rx="10"/>
  <!-- Inefficient -->
  <rect x="20" y="30" width="240" height="220" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="58" text-anchor="middle" fill="#8b949e">Inefficient Image (~540 MB)</text>
  <rect x="35" y="70" width="210" height="160" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="100" text-anchor="middle" fill="#8b949e" font-size="12">ubuntu:20.04 + OpenJDK (full)</text>
  <text x="140" y="124" text-anchor="middle" fill="#8b949e" font-size="12">COPY myapp.jar /app/</text>
  <text x="140" y="148" text-anchor="middle" fill="#8b949e" font-size="12">— single 150 MB blob —</text>
  <text x="140" y="172" text-anchor="middle" fill="#8b949e" font-size="11">Pushed entirely on every change</text>
  <text x="140" y="200" text-anchor="middle" fill="#8b949e" font-size="11">No layer caching</text>
  <!-- Efficient -->
  <rect x="300" y="30" width="320" height="220" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="58" text-anchor="middle" fill="#6db33f">Efficient Image (~220 MB)</text>
  <rect x="315" y="70" width="290" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="93" text-anchor="middle" fill="#8b949e" font-size="12">eclipse-temurin:21-jre-alpine (JRE only) ✓ cached</text>
  <rect x="315" y="112" width="290" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="133" text-anchor="middle" fill="#8b949e" font-size="12">Layer: dependencies/            ✓ cached</text>
  <rect x="315" y="149" width="290" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="460" y="170" text-anchor="middle" fill="#8b949e" font-size="12">Layer: spring-boot-loader/      ✓ cached</text>
  <rect x="315" y="186" width="290" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="460" y="207" text-anchor="middle" fill="#6db33f" font-size="12">Layer: application/   ← only this pushed (~100 KB)</text>
  <defs/>
</svg>

_Efficient images use a minimal JRE base and layered JARs — most builds push only the tiny `application` layer._

## 5. Runnable example

```java
// File: ContainerImageAdvice.java
// How to run: java ContainerImageAdvice.java
// Prints efficiency checklist and sample Dockerfile for a Spring Boot app.

public class ContainerImageAdvice {

    static final String EFFICIENT_DOCKERFILE = """
            # ---- Stage 1: Extract layers from the fat JAR ----
            FROM eclipse-temurin:21-jre AS builder
            WORKDIR /app
            COPY target/*.jar app.jar
            RUN java -Djarmode=layertools -jar app.jar extract

            # ---- Stage 2: Minimal runtime image ----
            FROM eclipse-temurin:21-jre-alpine
            WORKDIR /app

            # Non-root user for least privilege
            RUN addgroup -S spring && adduser -S spring -G spring
            USER spring:spring

            # Copy each layer — Docker caches independently
            COPY --from=builder /app/dependencies/ ./
            COPY --from=builder /app/spring-boot-loader/ ./
            COPY --from=builder /app/snapshot-dependencies/ ./
            COPY --from=builder /app/application/ ./

            # Container-aware JVM settings
            ENV JAVA_TOOL_OPTIONS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75"

            EXPOSE 8080
            ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
            """;

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Container Image Efficiency Checklist ===");
        System.out.println();
        String[] checks = {
            "[✓] Use JRE-only base image (eclipse-temurin:21-jre-alpine)",
            "[✓] Multi-stage build — builder stage discarded from final image",
            "[✓] Layered JAR extract — dependency layer cached between builds",
            "[✓] Non-root user — reduces attack surface",
            "[✓] -XX:+UseContainerSupport — respect cgroup memory/CPU limits",
            "[✓] -XX:MaxRAMPercentage=75 — leave headroom for non-heap memory",
            "[✓] EXPOSE 8080 — documents the service port",
        };
        for (String c : checks) System.out.println("  " + c);
        System.out.println();
        System.out.println("=== Efficient Dockerfile ===");
        System.out.print(EFFICIENT_DOCKERFILE);
        System.out.println();
        System.out.println("Build:  docker build -t myapp .");
        System.out.println("Run:    docker run -p 8080:8080 myapp");
    }
}
```

**How to run:** `java ContainerImageAdvice.java` — prints the checklist and Dockerfile.

## 6. Walkthrough

1. **Builder stage** — `eclipse-temurin:21-jre` copies the fat JAR and runs `layertools extract`, producing four directories.
2. **Runtime stage** — `eclipse-temurin:21-jre-alpine` uses Alpine Linux (~7 MB) instead of Debian (~80 MB), cutting the base by ~70 MB.
3. **Non-root user** — `RUN addgroup/adduser` + `USER spring:spring` ensures the process runs without host root privileges.
4. **Four `COPY` instructions** — each layer gets its own Docker layer. Unchanged layers (deps, loader) are cache hits; only `application/` is rebuilt and pushed.
5. **`JAVA_TOOL_OPTIONS`** — `UseContainerSupport` is default in JDK 17+ but explicit declaration documents intent. `MaxRAMPercentage=75` keeps 25% for off-heap buffers, GC overhead, and OS.
6. **`JarLauncher`** as `ENTRYPOINT` — directly launches the app from extracted layers; no intermediate shell process.

## 7. Gotchas & takeaways

> `eclipse-temurin:21-jre-alpine` uses musl libc, not glibc. Some native libraries (BouncyCastle, certain JDBC drivers) require glibc. If you see linker errors, switch to `eclipse-temurin:21-jre` (Debian-based).

> `-XX:MaxRAMPercentage` and `-Xmx` are mutually exclusive for heap sizing — don't use both. Prefer `MaxRAMPercentage` in containers so the limit adapts when the container spec changes.

> Do not use the `latest` tag for base images in production — tag pinning (`21.0.5_11-jre-alpine`) makes builds reproducible.

- Distroless images (`gcr.io/distroless/java21`) are even smaller and have no shell — great for security, harder to debug.
- `docker history myapp:latest` shows layer sizes — verify the `application` layer is the only one changing.
- Use `docker scout` or `trivy` to scan the image for CVEs after building.
- Buildpacks (`spring-boot:build-image`) apply these practices automatically; use a manual Dockerfile only for full control.
