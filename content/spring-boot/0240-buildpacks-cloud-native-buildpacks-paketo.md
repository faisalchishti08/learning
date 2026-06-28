---
card: spring-boot
gi: 240
slug: buildpacks-cloud-native-buildpacks-paketo
title: Buildpacks (Cloud Native Buildpacks / Paketo)
---

## 1. What it is

Cloud Native Buildpacks (CNB) is an OCI-image-building standard that turns application source code (or a compiled JAR) into a container image without writing a Dockerfile. The Paketo Buildpacks project provides a set of open-source buildpacks for Java, Node.js, Go, and more. Spring Boot integrates with Paketo via the `spring-boot:build-image` Maven goal and the `bootBuildImage` Gradle task.

## 2. Why & when

Dockerfiles require expertise to write well — correct base images, layer ordering, non-root users, JVM flags. Buildpacks encode these best practices automatically. Use buildpacks when you want production-grade images with minimal configuration, security patches applied transparently (rebasing), and consistent image structure across a fleet of services.

## 3. Core concept

The CNB lifecycle runs three phases:

1. **Detect** — each buildpack checks whether it applies (e.g., is there a JAR? a `pom.xml`?).
2. **Build** — chosen buildpacks contribute layers to the image (JRE, memory calculator, Spring Boot layer structure).
3. **Export** — layers are assembled into an OCI image and pushed to a registry.

The Spring Boot buildpack uses `layertools` internally — you get layered image layers without writing a single `COPY` instruction. The image includes the Paketo memory calculator, which auto-tunes JVM heap size based on container limits.

```
spring-boot:build-image
  └── builder image (paketobuildpacks/builder-jammy-base)
      ├── bellsoft-liberica-buildpack  (JRE)
      ├── spring-boot-buildpack        (layer extraction, AOT)
      └── ...
```

## 4. Diagram

<svg viewBox="0 0 640 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="290" fill="#1c2430" rx="10"/>
  <!-- Input -->
  <rect x="20" y="60" width="150" height="80" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="88" text-anchor="middle" fill="#8b949e">Input</text>
  <text x="95" y="108" text-anchor="middle" fill="#e6edf3" font-size="12">myapp.jar</text>
  <text x="95" y="126" text-anchor="middle" fill="#8b949e" font-size="11">(Spring Boot fat JAR)</text>
  <!-- CNB phases -->
  <rect x="210" y="40" width="220" height="220" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="68" text-anchor="middle" fill="#6db33f">CNB Lifecycle</text>
  <rect x="225" y="80" width="190" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="105" text-anchor="middle" fill="#6db33f" font-size="12">1. Detect (find applicable BPs)</text>
  <rect x="225" y="128" width="190" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="153" text-anchor="middle" fill="#6db33f" font-size="12">2. Build (BPs add layers)</text>
  <rect x="225" y="176" width="190" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="201" text-anchor="middle" fill="#6db33f" font-size="12">3. Export (OCI image)</text>
  <text x="320" y="244" text-anchor="middle" fill="#8b949e" font-size="11">No Dockerfile needed</text>
  <!-- Output -->
  <rect x="470" y="60" width="150" height="130" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="545" y="88" text-anchor="middle" fill="#79c0ff">OCI Image</text>
  <text x="545" y="108" text-anchor="middle" fill="#8b949e" font-size="11">JRE layer</text>
  <text x="545" y="126" text-anchor="middle" fill="#8b949e" font-size="11">dependencies layer</text>
  <text x="545" y="144" text-anchor="middle" fill="#8b949e" font-size="11">application layer</text>
  <text x="545" y="166" text-anchor="middle" fill="#8b949e" font-size="11">+ memory calculator</text>
  <!-- arrows -->
  <line x1="170" y1="100" x2="208" y2="140" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ad)"/>
  <line x1="430" y1="150" x2="468" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ad)"/>
  <defs>
    <marker id="ad" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_Buildpacks detect the app type, layer the image automatically, and export an OCI image — no Dockerfile._

## 5. Runnable example

```java
// File: BuildpacksDemo.java
// How to run: java BuildpacksDemo.java
// Shows the Maven/Gradle commands and key configuration options for build-image.
// Actual image build requires: Docker running + ./mvnw spring-boot:build-image

public class BuildpacksDemo {

    public static void main(String[] args) {
        System.out.println("=== Build with Paketo Buildpacks ===");
        System.out.println();
        System.out.println("Maven:");
        System.out.println("  ./mvnw spring-boot:build-image");
        System.out.println("  ./mvnw spring-boot:build-image -Dspring-boot.build-image.imageName=myapp:1.0");
        System.out.println();
        System.out.println("Gradle:");
        System.out.println("  ./gradlew bootBuildImage");
        System.out.println("  ./gradlew bootBuildImage --imageName=myapp:1.0");
        System.out.println();
        System.out.println("=== pom.xml plugin config snippet ===");
        System.out.println("""
                <plugin>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-maven-plugin</artifactId>
                  <configuration>
                    <image>
                      <name>myregistry.io/${project.artifactId}:${project.version}</name>
                      <!-- Pin the builder version for reproducibility -->
                      <builder>paketobuildpacks/builder-jammy-base:0.4.270</builder>
                      <env>
                        <!-- Java version to use -->
                        <BP_JVM_VERSION>21</BP_JVM_VERSION>
                        <!-- Enable Spring AOT processing -->
                        <BP_SPRING_AOT_ENABLED>true</BP_SPRING_AOT_ENABLED>
                      </env>
                    </image>
                  </configuration>
                </plugin>
                """);
        System.out.println("=== Run the built image ===");
        System.out.println("  docker run -p 8080:8080 myapp:1.0");
        System.out.println();
        System.out.println("=== Rebase (security patch without rebuild) ===");
        System.out.println("  pack rebase myapp:1.0 --run-image paketobuildpacks/run-jammy-base:latest");
    }
}
```

**How to run:** `java BuildpacksDemo.java` — prints commands and configuration. Run `./mvnw spring-boot:build-image` in a Spring Boot project to build a real image.

## 6. Walkthrough

1. `./mvnw spring-boot:build-image` — the plugin pulls the Paketo builder image and runs the CNB lifecycle inside a Docker container.
2. **Detect phase** — the Spring Boot buildpack detects `BOOT-INF/layers.idx` in the JAR and activates; the Bellsoft Liberica buildpack detects a Java application.
3. **Build phase** — the JRE buildpack contributes a JRE layer; the Spring Boot buildpack extracts JAR layers and configures `JarLauncher`; the memory calculator buildpack adds a script to auto-size heap at startup.
4. **Export phase** — layers are assembled into an OCI-compliant image and loaded into Docker (or pushed to a registry with `publishImage=true`).
5. `BP_JVM_VERSION=21` — instructs the JRE buildpack to use Java 21. Without this, the buildpack uses the version matching your `source.compatibility`.
6. `pack rebase` — replaces only the base OS layer with a security-patched run image, without rebuilding application layers. This is the key operational advantage of buildpacks over Dockerfiles.

## 7. Gotchas & takeaways

> `spring-boot:build-image` requires Docker to be running on the build machine — it creates a container to run the CNB lifecycle. Remote Docker and Podman are supported but require additional configuration.

> By default, the image is loaded into the local Docker daemon, not pushed to a registry. Set `<publishImage>true</publishImage>` (Maven) or `bootBuildImage { publish = true }` (Gradle) and configure registry credentials.

> Buildpack builder images are large (500 MB+) on first pull. Subsequent builds use the cached builder — only deltas are downloaded.

- Pin `<builder>` to a specific version in CI for reproducible builds; float to `latest` in dev for automatic security updates.
- Use `BP_NATIVE_IMAGE=true` with the GraalVM buildpack to produce a native executable image without a Dockerfile.
- The Paketo memory calculator adjusts heap size automatically at container start — no need to hard-code `-Xmx`.
- `./mvnw spring-boot:build-image -Dspring-boot.build-image.pullPolicy=IF_NOT_PRESENT` skips re-pulling the builder on every build.
