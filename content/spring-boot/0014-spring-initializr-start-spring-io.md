---
card: spring-boot
gi: 14
slug: spring-initializr-start-spring-io
title: Spring Initializr (start.spring.io)
---

## 1. What it is

The **Spring Initializr** at [start.spring.io](https://start.spring.io) is a web-based project generator that creates a ready-to-build Spring Boot project in seconds. You choose your preferences (build tool, language, Spring Boot version, Java version, dependencies), click **Generate**, and download a ZIP containing a complete project with the correct directory structure, build file, and a minimal main class.

It is also available:
- **In IntelliJ IDEA** — `File → New → Project → Spring Initializr`
- **In VS Code** — Spring Boot Extension Pack → `Spring Initializr: Create a Gradle Project`
- **Via CLI** — `spring init --dependencies=web,data-jpa my-app`
- **As a REST API** — `curl https://start.spring.io/starter.zip -d dependencies=web -o demo.zip`

The Initializr is not just a convenience — it **ensures correctness**. It knows which combinations of Spring Boot version + Java version + dependencies are valid and generates a project that builds cleanly out of the box.

## 2. Why & when

Before the Initializr, starting a Spring project meant:
- Finding the right parent POM version manually.
- Googling "Spring Boot starter web groupId" to get the exact coordinates.
- Creating `src/main/java/.../` directories by hand.
- Writing a minimal `@SpringBootApplication` main class from memory.
- Figuring out which Maven plugin version to use.

The Initializr eliminates all of this. Use it for **every new Spring Boot project** — even experienced developers always start from here. There is no correct reason to create the POM or Gradle file manually when start.spring.io does it correctly in 10 seconds.

**Use the Initializr when:**
- Starting any new Spring Boot project.
- Adding a module to an existing multi-module project (generate, copy the relevant bits).
- Checking what a correct `pom.xml` or `build.gradle.kts` should look like for a given set of dependencies.

## 3. Core concept

The Initializr's configuration form has these key choices:

| Field | Common choices |
|---|---|
| **Project** | Maven or Gradle (Kotlin DSL) |
| **Language** | Java, Kotlin, or Groovy |
| **Spring Boot** | Latest GA (pick this; avoid SNAPSHOT/RC for production) |
| **Group** | Your organisation's package prefix, e.g. `com.example` |
| **Artifact** | The project name, e.g. `order-service` |
| **Java** | 21 (recommended for new projects) |
| **Dependencies** | What to add, e.g. Spring Web, Spring Data JPA, H2 |

The most critical part of the form is **Dependencies** — this determines which `spring-boot-starter-*` entries appear in your build file. The search box accepts natural language: type "web" and you see `Spring Web (spring-boot-starter-web)`, type "postgres" and you see `PostgreSQL Driver`.

After generating, the project contains:
- `pom.xml` or `build.gradle.kts` (complete, correct)
- `src/main/java/.../Application.java` (minimal main class)
- `src/main/resources/application.properties` (empty, ready to fill)
- `src/test/java/.../ApplicationTests.java` (smoke test that loads the context)
- `mvnw` / `gradlew` wrappers

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Initializr workflow from form choices through ZIP download to IDE import and running application">
  <!-- Step 1 -->
  <rect x="20" y="80" width="140" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="104" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">1. Configure</text>
  <text x="90" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">start.spring.io</text>
  <text x="90" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Maven + Java 21</text>
  <text x="90" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Web + JPA</text>

  <line x1="160" y1="120" x2="190" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#initArr)"/>

  <!-- Step 2 -->
  <rect x="190" y="80" width="140" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="260" y="104" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">2. Generate</text>
  <text x="260" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Click Generate</text>
  <text x="260" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Download .zip</text>

  <line x1="330" y1="120" x2="360" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#initArr2)"/>

  <!-- Step 3 -->
  <rect x="360" y="80" width="140" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="104" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">3. Import</text>
  <text x="430" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Unzip → IDE</text>
  <text x="430" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Open pom.xml</text>
  <text x="430" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">or build.gradle.kts</text>

  <line x1="500" y1="120" x2="530" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#initArr3)"/>

  <!-- Step 4 -->
  <rect x="530" y="80" width="110" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="104" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">4. Run</text>
  <text x="585" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">./mvnw</text>
  <text x="585" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot:run</text>
  <text x="585" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">:8080 ✓</text>

  <defs>
    <marker id="initArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="initArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="initArr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Four steps, under two minutes, from zero to a running Spring Boot application.

## 5. Runnable example

```java
// File: InitializrApiDemo.java
// Calls the Initializr's public REST API to download a minimal project.
// Run: java InitializrApiDemo.java
// Requires: internet connection + JDK 17+

import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.io.*;
import java.util.zip.*;

public class InitializrApiDemo {

    public static void main(String[] args) throws Exception {
        // The Spring Initializr exposes a REST API
        String url = "https://start.spring.io/starter.zip"
            + "?type=maven-project"
            + "&language=java"
            + "&bootVersion=3.3.4"
            + "&baseDir=demo"
            + "&groupId=com.example"
            + "&artifactId=demo"
            + "&name=demo"
            + "&description=Demo+project"
            + "&packageName=com.example.demo"
            + "&packaging=jar"
            + "&javaVersion=21"
            + "&dependencies=web";   // spring-boot-starter-web

        System.out.println("Calling Spring Initializr API...");
        System.out.println(url.replace("&", "\n  &"));
        System.out.println();

        var client  = HttpClient.newHttpClient();
        var request = HttpRequest.newBuilder(URI.create(url))
            .header("Accept", "application/zip")
            .GET().build();

        var response = client.send(request, HttpResponse.BodyHandlers.ofByteArray());
        System.out.println("Response: HTTP " + response.statusCode());

        if (response.statusCode() == 200) {
            Path zipPath = Path.of("demo.zip");
            Files.write(zipPath, response.body());
            System.out.println("Downloaded: demo.zip (" + response.body().length + " bytes)");

            // List the top-level files in the zip
            System.out.println("\nFiles in demo.zip:");
            try (var zis = new ZipInputStream(new FileInputStream("demo.zip"))) {
                ZipEntry entry;
                while ((entry = zis.getNextEntry()) != null) {
                    System.out.println("  " + entry.getName());
                }
            }

            Files.delete(zipPath); // clean up
            System.out.println("\nProject structure is ready to unzip and open in your IDE.");
        } else {
            System.out.println("Error: " + new String(response.body()));
        }
    }
}
```

**How to run:** `java InitializrApiDemo.java` (JDK 17+, internet connection required).

Expected output (abridged):
```
Calling Spring Initializr API...
https://start.spring.io/starter.zip?type=maven-project
  &language=java
  &bootVersion=3.3.4
  ...

Response: HTTP 200
Downloaded: demo.zip (67892 bytes)

Files in demo.zip:
  demo/
  demo/.gitignore
  demo/mvnw
  demo/mvnw.cmd
  demo/pom.xml
  demo/src/main/java/com/example/demo/DemoApplication.java
  demo/src/main/resources/application.properties
  demo/src/test/java/com/example/demo/DemoApplicationTests.java

Project structure is ready to unzip and open in your IDE.
```

## 6. Walkthrough

- **REST API URL parameters** — the Initializr exposes a standard REST endpoint. `type=maven-project` selects Maven; `dependencies=web,data-jpa` (comma-separated) adds multiple starters. The same form you fill in on the website is translated to these query parameters.
- **`HttpClient.newHttpClient()`** — Java 11's built-in HTTP client. No external libraries needed for a simple GET request.
- **`HttpResponse.BodyHandlers.ofByteArray()`** — we receive the raw ZIP bytes into a `byte[]` so we can write them to disk with `Files.write`.
- **`ZipInputStream`** — reads the ZIP entries without extracting. We use it to list what the Initializr generated. In real usage you'd extract with `Files.copy(zis, destPath, StandardCopyOption.REPLACE_EXISTING)` inside the loop.
- **`Files.delete(zipPath)`** — cleans up the temp file. In a real tool you'd keep the ZIP or extract it to a chosen directory.

## 7. Gotchas & takeaways

> **Always choose the latest stable GA for new projects, not SNAPSHOT or RC.** The version selector on start.spring.io may default to a SNAPSHOT if the page is visited just before a release. Verify the version ends in `.RELEASE` or is a pure numeric string like `3.3.4` — not `-SNAPSHOT` or `-M2`.

> **Explore tab is often overlooked.** After generating, click the **Explore** button on start.spring.io to preview all generated files before downloading. This is useful for checking exactly what goes into `pom.xml` for a given set of dependencies.

- Use start.spring.io for every new Spring Boot project — never write a `pom.xml` from scratch.
- Add dependencies via the search box: type "web", "jpa", "security", "redis", "actuator".
- IDE integrations (IntelliJ, VS Code) offer the same Initializr UI embedded in the new-project wizard.
- The REST API (`https://start.spring.io/starter.zip?...`) is automatable — useful in scaffolding scripts.
- `spring init --list` (CLI) shows all available dependencies and their IDs for scripted generation.
