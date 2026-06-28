---
card: spring-boot
gi: 242
slug: cds-class-data-sharing-training-runs
title: CDS (Class Data Sharing) & training runs
---

## 1. What it is

Class Data Sharing (CDS) is a JVM feature that pre-processes class metadata into a shared archive file (`.jsa`). At startup, the JVM maps this archive into memory instead of re-loading and parsing each class from disk. Spring Boot 3.3 added first-class support for CDS via the `spring-boot:process-aot` pipeline and a built-in training-run mechanism that generates the archive automatically.

## 2. Why & when

JVM startup time for a medium Spring Boot application is typically 2-5 seconds. Much of that is class loading and JIT warmup. CDS alone can cut startup time by 30-60% by eliminating the class-loading phase for classes that are always used. It is the pragmatic middle ground between a standard JVM launch (slow start) and a GraalVM native image (fast start, complex build).

## 3. Core concept

CDS workflow has two phases:

1. **Training run** — start the JVM with `-Xshare:dump` (or use `spring-boot:process-aot`). The JVM loads all classes, serialises metadata into `application.jsa`, and exits.
2. **Production run** — start with `-XX:SharedArchiveFile=application.jsa -Xshare:on`. The JVM memory-maps the archive and skips class parsing.

Spring Boot 3.3+ provides `CDS` support out of the box. The `spring-boot:process-aot` goal (already required for native images) also generates the CDS archive. On the executable JAR, you can use:

```
java -Dspring.context.exit=on-refresh -jar myapp.jar   # training run
java -XX:SharedArchiveFile=application.jsa -jar myapp.jar  # production
```

Or with `layertools` in Docker: the Paketo Spring Boot buildpack applies CDS automatically.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="280" fill="#1c2430" rx="10"/>
  <!-- Training run -->
  <rect x="20" y="40" width="270" height="100" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="68" text-anchor="middle" fill="#8b949e">Training Run (once)</text>
  <rect x="35" y="82" width="240" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="155" y="102" text-anchor="middle" fill="#e6edf3" font-size="12">java -Dspring.context.exit=on-refresh</text>
  <text x="155" y="118" text-anchor="middle" fill="#e6edf3" font-size="12">     -jar myapp.jar</text>
  <!-- Archive -->
  <rect x="155" y="168" width="160" height="50" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="235" y="192" text-anchor="middle" fill="#6db33f">application.jsa</text>
  <text x="235" y="210" text-anchor="middle" fill="#8b949e" font-size="11">class metadata archive</text>
  <!-- Production run -->
  <rect x="350" y="40" width="270" height="100" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="485" y="68" text-anchor="middle" fill="#6db33f">Production Run</text>
  <rect x="365" y="82" width="240" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="102" text-anchor="middle" fill="#6db33f" font-size="12">java -XX:SharedArchiveFile=app.jsa</text>
  <text x="485" y="118" text-anchor="middle" fill="#6db33f" font-size="12">     -jar myapp.jar</text>
  <!-- timing -->
  <rect x="350" y="180" width="270" height="70" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="208" text-anchor="middle" fill="#79c0ff">30-60% faster startup</text>
  <text x="485" y="230" text-anchor="middle" fill="#8b949e" font-size="11">classes memory-mapped, not re-parsed</text>
  <!-- arrows -->
  <line x1="155" y1="142" x2="200" y2="166" stroke="#8b949e" stroke-width="1.5" marker-end="url(#af)"/>
  <line x1="275" y1="195" x2="348" y2="195" stroke="#6db33f" stroke-width="1.5" marker-end="url(#af)"/>
  <defs>
    <marker id="af" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_Training run dumps class metadata; production run maps the archive — class loading is skipped._

## 5. Runnable example

```java
// File: CdsDemo.java
// How to run: java CdsDemo.java
// Illustrates CDS commands and configuration.
// For real CDS: build a Spring Boot JAR and follow the commands printed below.

import java.lang.management.ManagementFactory;
import java.util.List;

public class CdsDemo {

    public static void main(String[] args) {
        // Check if this JVM started with a CDS archive
        List<String> jvmArgs = ManagementFactory.getRuntimeMXBean().getInputArguments();
        boolean cdsActive = jvmArgs.stream()
                .anyMatch(a -> a.contains("SharedArchiveFile") || a.contains("Xshare:on"));

        System.out.println("JVM args: " + jvmArgs);
        System.out.println("CDS archive active: " + cdsActive);

        System.out.println("\n=== CDS workflow for Spring Boot ===");
        System.out.println();
        System.out.println("Step 1 — Training run (generates application.jsa):");
        System.out.println("  java -Dspring.context.exit=on-refresh \\");
        System.out.println("       -XX:ArchiveClassesAtExit=application.jsa \\");
        System.out.println("       -jar target/myapp.jar");
        System.out.println();
        System.out.println("Step 2 — Production run (uses application.jsa):");
        System.out.println("  java -XX:SharedArchiveFile=application.jsa \\");
        System.out.println("       -jar target/myapp.jar");
        System.out.println();
        System.out.println("Step 3 — Verify archive is used:");
        System.out.println("  java -Xshare:on -verbose:class \\");
        System.out.println("       -XX:SharedArchiveFile=application.jsa \\");
        System.out.println("       -jar target/myapp.jar 2>&1 | grep 'shared'");
        System.out.println();
        System.out.println("=== Docker Dockerfile with CDS ===");
        System.out.println("""
                FROM eclipse-temurin:21-jre-alpine AS cds-builder
                WORKDIR /app
                COPY target/myapp.jar app.jar
                # Training run: load context then exit, dumping CDS archive
                RUN java -Dspring.context.exit=on-refresh \\
                         -XX:ArchiveClassesAtExit=application.jsa \\
                         -jar app.jar || true

                FROM eclipse-temurin:21-jre-alpine
                WORKDIR /app
                COPY --from=cds-builder /app/app.jar ./
                COPY --from=cds-builder /app/application.jsa ./
                ENTRYPOINT ["java", \\
                  "-XX:SharedArchiveFile=application.jsa", \\
                  "-jar", "app.jar"]
                """);
    }
}
```

**How to run:** `java CdsDemo.java` — prints CDS workflow and Dockerfile. Run the printed commands against a real Spring Boot JAR to generate and use a CDS archive.

## 6. Walkthrough

1. `ManagementFactory.getRuntimeMXBean().getInputArguments()` — reads JVM arguments at runtime. Checking for `SharedArchiveFile` confirms the CDS archive was applied.
2. **Training run** — `-Dspring.context.exit=on-refresh` tells Spring Boot to exit after the `ApplicationContext` is refreshed (before accepting traffic). `-XX:ArchiveClassesAtExit=application.jsa` dumps the CDS archive on exit.
3. **Production run** — `-XX:SharedArchiveFile=application.jsa` tells the JVM to map the archive at startup. Classes in the archive are not re-parsed — metadata is ready immediately.
4. **Verification** — `-verbose:class` combined with `grep 'shared'` shows which classes were loaded from the shared archive vs. disk.
5. **Docker pattern** — the training run happens in a separate build stage; the final image contains both the JAR and the archive, keeping the workflow reproducible.

## 7. Gotchas & takeaways

> The CDS archive is **JVM-specific**. An archive generated with JDK 21.0.3 will not be compatible with JDK 21.0.4 — regenerate after every JVM version update.

> The archive captures the class list at training time. If your application loads classes conditionally (feature flags, profiles), the training run profile must match production as closely as possible.

> `spring.context.exit=on-refresh` exits before the web server starts — the training run never binds to a port. This is intentional: the goal is to capture class loading, not to serve requests.

- Spring Boot 3.3+ has `spring-boot:process-aot` which combines AOT compilation and CDS generation in one step.
- On JDK 21+, AppCDS (Application CDS) is the preferred mechanism — it captures the full application class list, not just JDK classes.
- Startup improvement of 30-60% is typical for Boot apps; exact gains depend on the number of classes loaded.
- Native images (GraalVM) offer better startup improvement (~10x) but require AOT compilation and have reflection limitations.
