---
card: spring-boot
gi: 246
slug: building-a-native-image-with-buildpacks
title: Building a native image with Buildpacks
---

## 1. What it is

**Cloud Native Buildpacks** (CNB) are a standardised way to turn source code or compiled artifacts into OCI-compliant container images without writing a Dockerfile. The **Paketo Buildpacks** implementation (the default Spring Boot uses) includes a dedicated **native-image buildpack** that installs GraalVM, runs AOT processing, invokes `native-image`, and packages the result into a minimal container — all inside a Docker daemon on your machine.

Spring Boot exposes this via a single Maven or Gradle goal:

```
mvn -Pnative spring-boot:build-image
./gradlew bootBuildImage
```

You get a production-ready OCI image without installing GraalVM locally, without writing a Dockerfile, and without managing multi-stage build scripts.

## 2. Why & when

Use Buildpacks for native images when:

- You don't want to install GraalVM locally (CI agents or developer laptops vary).
- You want an opinionated, security-hardened base image managed by Paketo (regular CVE patches).
- You need reproducible builds: the same buildpack version + same source always produces the same image layers.
- You prefer a push-button experience over managing `native-image` flags manually.

Use **GraalVM Native Build Tools** (direct `native-image` invocation) instead when:
- You need fine-grained control over the native-image command line.
- You cannot run Docker (some restricted CI environments).
- You want the native binary as a file (not a container image).

## 3. Core concept

A **buildpack** is a specialised program that detects what kind of project it's looking at, installs the right toolchain, and outputs image layers. Several buildpacks are composed into a **builder image** (the Paketo `paketobuildpacks/builder-jammy-tiny` image). Each buildpack is responsible for one concern.

For a Spring Boot native build, the builder does:

1. **Detect** — recognises a Spring Boot fat-jar.
2. **GraalVM buildpack** — downloads and installs GraalVM CE or Oracle GraalVM into the build container.
3. **Spring Boot buildpack** — runs `spring-boot:process-aot` to generate AOT sources.
4. **Native-image buildpack** — invokes `native-image` with the AOT-generated hints.
5. **Layer buildpack** — copies the native binary into a minimal `scratch`-like runtime image.

The result is a multi-layer OCI image: the tiny runtime layer (≈20 MB) plus the native binary (≈60–150 MB depending on app size).

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Buildpack pipeline converting Spring Boot jar to native OCI image">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Developer machine box -->
  <rect x="5" y="10" width="150" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="35" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Developer</text>
  <text x="80" y="53" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">mvn -Pnative</text>
  <text x="80" y="69" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot:build-image</text>

  <!-- Docker / builder -->
  <rect x="190" y="5" width="340" height="170" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="28" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Builder Container (Paketo)</text>

  <rect x="205" y="40" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="275" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GraalVM buildpack</text>
  <text x="275" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">installs GraalVM JDK</text>

  <rect x="360" y="40" width="155" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="437" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot buildpack</text>
  <text x="437" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs process-aot</text>

  <rect x="205" y="95" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="275" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">native-image buildpack</text>
  <text x="275" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compiles native binary</text>

  <rect x="360" y="95" width="155" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="437" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Layer buildpack</text>
  <text x="437" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">packages OCI layers</text>

  <!-- OCI image output -->
  <rect x="560" y="70" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="625" y="94" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">OCI Image</text>
  <text x="625" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">myapp:latest</text>

  <!-- arrows -->
  <line x1="155" y1="50" x2="188" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="345" y1="57" x2="358" y2="57" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="345" y1="112" x2="358" y2="112" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="515" y1="112" x2="558" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>

  <text x="350" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No Dockerfile, no local GraalVM — Docker daemon on host machine is the only prerequisite</text>
</svg>

Buildpacks run inside Docker; your machine only needs Docker and a JDK to invoke the Maven/Gradle goal.

## 5. Runnable example

```java
// BuildpackDemo.java — run with: java BuildpackDemo.java
// Prints the exact commands and pom.xml configuration needed to build
// a Spring Boot native image using Buildpacks, then validates prerequisites.

import java.io.File;

public class BuildpackDemo {

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Native Image via Buildpacks ===\n");

        checkPrerequisites();
        printMavenSetup();
        printGradleSetup();
        printUsefulCommands();
    }

    static void checkPrerequisites() {
        System.out.println("--- Prerequisite check ---");
        checkCmd("docker", "docker version --format '{{.Server.Version}}'", "Docker daemon");
        checkCmd("mvn", "mvn --version", "Maven");
        System.out.println();
    }

    static void checkCmd(String cmd, String fullCmd, String label) {
        // Try to find the binary on PATH (cross-platform check)
        boolean found = new File("/usr/local/bin/" + cmd).exists()
            || new File("/usr/bin/" + cmd).exists()
            || System.getenv("PATH") != null && System.getenv("PATH").contains(cmd);
        System.out.printf("  %-15s : %s%n", label, found ? "likely present" : "NOT FOUND — install it");
    }

    static void printMavenSetup() {
        System.out.println("--- pom.xml (spring-boot-starter-parent required) ---");
        System.out.println("""
            <parent>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-starter-parent</artifactId>
              <version>3.3.0</version>
            </parent>

            <!-- Build command: -->
            <!--   mvn -Pnative spring-boot:build-image            -->
            <!-- Custom image name: -->
            <!--   mvn -Pnative spring-boot:build-image            -->
            <!--     -Dspring-boot.build-image.imageName=myorg/app -->
            """);
    }

    static void printGradleSetup() {
        System.out.println("--- build.gradle ---");
        System.out.println("""
            plugins {
              id 'org.springframework.boot'         version '3.3.0'
              id 'io.spring.dependency-management'  version '1.1.4'
              id 'org.graalvm.buildtools.native'    version '0.10.2'
            }

            // Build command:
            //   ./gradlew bootBuildImage
            // Custom image name:
            //   bootBuildImage { imageName = 'myorg/app:latest' }
            """);
    }

    static void printUsefulCommands() {
        System.out.println("--- Run the produced image ---");
        System.out.println("  docker run --rm -p 8080:8080 myapp:latest");
        System.out.println("  # Startup in < 100 ms — no JVM, direct OS executable");
        System.out.println();
        System.out.println("--- Override builder (e.g. to use ARM builder) ---");
        System.out.println("  mvn -Pnative spring-boot:build-image \\");
        System.out.println("    -Dspring-boot.build-image.builder=paketobuildpacks/builder-jammy-base");
    }
}
```

**How to run:** `java BuildpackDemo.java`

## 6. Walkthrough

- **`checkPrerequisites()`** — heuristically tests for Docker and Maven. The real prerequisite at runtime is the Docker daemon; without it `build-image` fails with `connection refused on /var/run/docker.sock`.
- **`printMavenSetup()`** — shows the minimal `pom.xml`. The key points: inherit `spring-boot-starter-parent` and activate `-Pnative`. The `build-image` goal talks to Docker; no local GraalVM binary is needed.
- **`printGradleSetup()`** — Gradle's equivalent. `org.graalvm.buildtools.native` adds the `nativeCompile` and `bootBuildImage` (in native mode) tasks. The Gradle task respects the same Paketo builder image.
- **`printUsefulCommands()`** — `docker run` launches the native binary directly. Startup time is typically 50–200 ms; compare to 2–6 s for JVM mode.
- **Builder override** — `paketobuildpacks/builder-jammy-base` is larger but includes libc shared libraries some native apps need. `builder-jammy-tiny` is the smallest (musl-free, no shell).

## 7. Gotchas & takeaways

> **Build time is long.** Native compilation via Buildpacks typically takes 5–15 minutes because GraalVM must be downloaded inside the container (cached after first run) and `native-image` itself is memory-intensive. Allocate at least 8 GB RAM to Docker Desktop.

> **The resulting image architecture matches the builder, not your host.** If you build on an Apple Silicon Mac and the builder uses `linux/amd64`, the image won't run natively on your Mac — use `--platform linux/amd64` or run on an amd64 CI agent.

- No Dockerfile and no local GraalVM = the main appeal of Buildpacks.
- First build is slow (downloads GraalVM); subsequent builds reuse cached layers.
- Image size: expect ~80–200 MB total (tiny OS layer + native binary) vs. ~300–500 MB for a JVM image.
- Use `spring-boot.build-image.imageName` property to control registry/tag.
- The `paketobuildpacks/builder-jammy-tiny` builder produces the smallest image; use `-base` if native code needs system libraries.
- Test the image with `docker run` before pushing to a registry — native failures surface as startup crashes, not JVM exceptions.
