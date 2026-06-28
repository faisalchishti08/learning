---
card: spring-boot
gi: 241
slug: spring-boot-build-image-goal
title: spring-boot:build-image goal
---

## 1. What it is

`spring-boot:build-image` is a Maven goal (and `bootBuildImage` in Gradle) provided by the Spring Boot build plugin. It builds an OCI-compatible container image from your application using Cloud Native Buildpacks — no Dockerfile required. It is the recommended way to produce production-ready container images from Spring Boot projects.

## 2. Why & when

Writing a correct, optimised, and secure Dockerfile requires significant expertise. `spring-boot:build-image` delegates to Paketo Buildpacks, which embed best practices (JRE-only images, layered structure, memory auto-tuning, non-root user). Use it whenever you want a production-grade image with minimal configuration. Switch to a manual Dockerfile only when you need something buildpacks cannot provide.

## 3. Core concept

The goal wraps the CNB `lifecycle` tool, which runs inside a Docker container. Key configuration points in `pom.xml`:

```xml
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
  <configuration>
    <image>
      <name>${project.artifactId}:${project.version}</name>
      <builder>paketobuildpacks/builder-jammy-base</builder>
      <env>
        <BP_JVM_VERSION>21</BP_JVM_VERSION>
      </env>
      <publish>false</publish>
    </image>
  </configuration>
</plugin>
```

Useful properties (all configurable via system properties on the CLI too):
- `spring-boot.build-image.imageName` — image name/tag
- `spring-boot.build-image.builder` — builder image
- `spring-boot.build-image.pullPolicy` — `ALWAYS` / `IF_NOT_PRESENT` / `NEVER`
- `spring-boot.build-image.publish` — push to registry after build

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="270" fill="#1c2430" rx="10"/>
  <!-- Maven/Gradle -->
  <rect x="20" y="60" width="150" height="80" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="88" text-anchor="middle" fill="#8b949e">mvnw / gradlew</text>
  <text x="95" y="108" text-anchor="middle" fill="#6db33f" font-size="12">spring-boot:</text>
  <text x="95" y="126" text-anchor="middle" fill="#6db33f" font-size="12">build-image</text>
  <!-- Docker -->
  <rect x="210" y="40" width="210" height="190" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="68" text-anchor="middle" fill="#79c0ff">Docker (on build machine)</text>
  <rect x="225" y="82" width="180" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="105" text-anchor="middle" fill="#8b949e" font-size="12">Paketo builder image</text>
  <rect x="225" y="125" width="180" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="148" text-anchor="middle" fill="#6db33f" font-size="12">CNB lifecycle runs</text>
  <rect x="225" y="168" width="180" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="315" y="191" text-anchor="middle" fill="#6db33f" font-size="12">detect → build → export</text>
  <!-- Output -->
  <rect x="460" y="60" width="160" height="130" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="540" y="88" text-anchor="middle" fill="#6db33f">OCI Image</text>
  <text x="540" y="112" text-anchor="middle" fill="#8b949e" font-size="11">Loaded into local Docker</text>
  <text x="540" y="132" text-anchor="middle" fill="#8b949e" font-size="11">or pushed to registry</text>
  <text x="540" y="152" text-anchor="middle" fill="#8b949e" font-size="11">if publish=true</text>
  <text x="540" y="172" text-anchor="middle" fill="#8b949e" font-size="11">+ Paketo labels</text>
  <!-- arrows -->
  <line x1="170" y1="100" x2="208" y2="140" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ae)"/>
  <line x1="420" y1="145" x2="458" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ae)"/>
  <defs>
    <marker id="ae" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`spring-boot:build-image` delegates to Paketo inside Docker and produces a registry-ready OCI image._

## 5. Runnable example

```java
// File: BuildImageGoalDemo.java
// How to run: java BuildImageGoalDemo.java
// Prints all key CLI options and pom.xml configuration for spring-boot:build-image.

public class BuildImageGoalDemo {

    public static void main(String[] args) {
        System.out.println("=== Common CLI invocations ===");
        System.out.println();
        // Basic build
        System.out.println("# Build image with default name (artifactId:version)");
        System.out.println("./mvnw spring-boot:build-image");
        System.out.println();
        // Custom name
        System.out.println("# Override image name");
        System.out.println("./mvnw spring-boot:build-image \\");
        System.out.println("  -Dspring-boot.build-image.imageName=myregistry.io/myapp:latest");
        System.out.println();
        // Skip pulling builder every time
        System.out.println("# Skip re-pulling builder image (faster in CI with warm cache)");
        System.out.println("./mvnw spring-boot:build-image \\");
        System.out.println("  -Dspring-boot.build-image.pullPolicy=IF_NOT_PRESENT");
        System.out.println();
        // Publish to registry
        System.out.println("# Build AND push to registry");
        System.out.println("./mvnw spring-boot:build-image \\");
        System.out.println("  -Dspring-boot.build-image.imageName=myregistry.io/myapp:1.0 \\");
        System.out.println("  -Dspring-boot.build-image.publish=true");
        System.out.println();
        // Gradle equivalent
        System.out.println("=== Gradle equivalents ===");
        System.out.println("./gradlew bootBuildImage");
        System.out.println("./gradlew bootBuildImage --imageName=myapp:1.0");
        System.out.println();
        System.out.println("=== Full pom.xml configuration ===");
        System.out.println("""
                <plugin>
                  <groupId>org.springframework.boot</groupId>
                  <artifactId>spring-boot-maven-plugin</artifactId>
                  <configuration>
                    <image>
                      <!-- image name: can use Maven properties -->
                      <name>${docker.registry}/${project.artifactId}:${project.version}</name>
                      <!-- pin builder for reproducible CI builds -->
                      <builder>paketobuildpacks/builder-jammy-base:0.4.270</builder>
                      <env>
                        <BP_JVM_VERSION>21</BP_JVM_VERSION>
                        <!-- enable AOT ahead-of-time processing -->
                        <BP_SPRING_AOT_ENABLED>true</BP_SPRING_AOT_ENABLED>
                      </env>
                      <!-- push after build -->
                      <publish>false</publish>
                      <!-- skip pulling builder if already present -->
                      <pullPolicy>IF_NOT_PRESENT</pullPolicy>
                    </image>
                  </configuration>
                </plugin>
                """);
    }
}
```

**How to run:** `java BuildImageGoalDemo.java` — prints all invocation patterns. Run `./mvnw spring-boot:build-image` in a real Spring Boot project to build an image.

## 6. Walkthrough

1. The goal triggers the Spring Boot Maven plugin, which communicates with the Docker daemon via the Docker socket.
2. It pulls the Paketo builder image (first time only, unless `pullPolicy=ALWAYS`).
3. Inside a Docker container, the CNB lifecycle runs detect, build, and export phases.
4. The Spring Boot buildpack calls `layertools extract` internally, splitting the JAR into layers.
5. The Bellsoft Liberica buildpack contributes a JRE layer matching `BP_JVM_VERSION`.
6. The image is exported as OCI layers and loaded into the local Docker daemon. If `publish=true`, it's also pushed to the configured registry.
7. The final image is tagged with the configured name and has standard Paketo labels (`io.buildpacks.*`) recording build metadata.

## 7. Gotchas & takeaways

> `spring-boot:build-image` skips the `package` phase by default if the JAR is already built. Run `./mvnw package spring-boot:build-image` to ensure the latest code is compiled before building the image.

> Registry authentication for `publish=true` must be configured in Maven's `settings.xml` `<servers>` section — Docker credentials (`~/.docker/config.json`) are not read automatically by the Maven plugin.

> The goal requires Docker to be running. On CI systems that don't allow DinD (Docker-in-Docker), consider Buildah, Kaniko, or a remote Docker host.

- Image name defaults to `${project.artifactId}:${project.version}` — always override with a registry prefix for production pushes.
- `BP_SPRING_AOT_ENABLED=true` triggers Spring Boot's AOT engine during the build phase, improving startup time.
- Combine with Maven's `<executions>` to auto-build the image as part of `mvn install` in CI: `<goals><goal>build-image</goal></goals>`.
- The Paketo memory calculator inside the image auto-computes heap size on startup — no `-Xmx` needed in `JAVA_TOOL_OPTIONS`.
