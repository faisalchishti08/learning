---
card: spring-boot
gi: 13
slug: spring-boot-cli-installation
title: Spring Boot CLI installation
---

## 1. What it is

The **Spring Boot CLI** (Command Line Interface) is an optional command-line tool that lets you run Groovy scripts as Spring Boot applications — without a Maven or Gradle project, without a `main` method, and without a compilation step. It's the fastest possible path from idea to running Spring Boot code.

Example: create a file `hello.groovy` with:

```groovy
@RestController
class HelloController {
    @RequestMapping("/") String home() { "Hello from CLI!" }
}
```

Run it with `spring run hello.groovy`. A full Spring MVC web application starts on port 8080. No `pom.xml`, no imports, no boilerplate.

The CLI is also useful for:
- **Quick experiments** with Spring APIs without scaffolding a project.
- **Checking Spring Boot behaviour** against a stripped-down script.
- **Groovy-based automation** that needs Spring features (scheduling, REST clients).

Note: the CLI is *optional*. Most Spring Boot development uses Maven or Gradle projects. The CLI is a power-user convenience tool, not a prerequisite.

## 2. Why & when

**Why the CLI exists:** Spring Boot's value proposition is "minimal setup." The CLI takes this to its logical extreme — literally zero project structure required. It's the fastest way to test a Spring concept or share a reproducible snippet.

**Use the CLI when:**
- You want to try out a new Spring feature without creating a project.
- You're writing a script that uses Spring's `@Scheduled`, `@Autowired`, or HTTP client support.
- You're in a demo or teaching context where project scaffolding wastes time.

**Don't use the CLI for production applications.** Production code belongs in a proper Maven/Gradle project with dependency management, CI, and test coverage.

## 3. Core concept

The CLI works in three phases:

1. **Detection** — reads your Groovy source, scans for annotations like `@RestController`, `@Component`, `@Grab`, and infers which dependencies to auto-import.
2. **Dependency resolution** — uses the same `spring-boot-dependencies` BOM to download the right JARs (cached in `~/.groovy/grapes`). `@Grab` annotations in your script can add extra dependencies.
3. **Execution** — compiles the Groovy script on the fly and runs it inside a Spring Boot `ApplicationContext`, starting an embedded Tomcat if web annotations are found.

**Installation options (pick one):**

| Method | Command | Best for |
|---|---|---|
| SDKMAN | `sdk install springboot` | Mac / Linux — recommended |
| Homebrew | `brew install springboot` | Mac |
| Scoop | `scoop install springboot` | Windows |
| Manual ZIP | Download from spring.io/tools | Any platform |

After installation: `spring --version` should print `Spring CLI v3.x.x`.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot CLI flow from Groovy script through auto-import and dependency resolution to running application">
  <!-- Groovy script -->
  <rect x="20" y="80" width="140" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="104" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">hello.groovy</text>
  <text x="90" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@RestController</text>

  <!-- Arrow -->
  <line x1="160" y1="110" x2="200" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#cliArr)"/>
  <text x="178" y="103" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">spring run</text>

  <!-- CLI box -->
  <rect x="200" y="50" width="240" height="120" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="76" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot CLI</text>
  <rect x="216" y="86" width="208" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. Detect annotations</text>
  <rect x="216" y="118" width="208" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. Resolve + download JARs</text>
  <rect x="216" y="150" width="208" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. Compile + run Groovy</text>

  <!-- Arrow -->
  <line x1="440" y1="110" x2="490" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#cliArr2)"/>

  <!-- Running app -->
  <rect x="490" y="80" width="150" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="104" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Running App</text>
  <text x="565" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">localhost:8080</text>

  <defs>
    <marker id="cliArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cliArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`spring run hello.groovy` does detection, dependency download, compilation, and app startup — all invisible to the developer.

## 5. Runnable example

```java
// File: CliConceptDemo.java
// Demonstrates the idea behind Spring Boot CLI's "run a single file" pattern.
// Run: java CliConceptDemo.java

import java.util.*;

public class CliConceptDemo {

    // Simulates what Spring Boot CLI does to a minimal Groovy script
    static String groovyScript = """
        @RestController
        class Hello {
            @GetMapping("/") String home() { "Hello!" }
        }
        """;

    // Simulates annotation detection
    static List<String> detectAnnotations(String script) {
        var found = new ArrayList<String>();
        for (var annotation : List.of("@RestController", "@Component",
                                      "@GetMapping", "@Scheduled", "@Grab")) {
            if (script.contains(annotation)) found.add(annotation);
        }
        return found;
    }

    // Simulates dependency inference from annotations
    static List<String> inferDependencies(List<String> annotations) {
        var deps = new ArrayList<String>();
        boolean needsWeb = annotations.stream()
            .anyMatch(a -> a.contains("Controller") || a.contains("Mapping"));
        if (needsWeb) deps.add("spring-boot-starter-web");
        deps.add("spring-boot-starter");  // always needed
        return deps;
    }

    public static void main(String[] args) {
        System.out.println("spring run hello.groovy");
        System.out.println();

        System.out.println("Step 1: Detect annotations");
        var annotations = detectAnnotations(groovyScript);
        annotations.forEach(a -> System.out.println("  found: " + a));

        System.out.println();
        System.out.println("Step 2: Infer & download dependencies");
        var deps = inferDependencies(annotations);
        deps.forEach(d -> System.out.println("  resolving: " + d + " (cached in ~/.groovy/grapes)"));

        System.out.println();
        System.out.println("Step 3: Compile Groovy → bytecode → run in ApplicationContext");
        System.out.println("  Started HelloController on http://localhost:8080");
        System.out.println();
        System.out.println("No pom.xml. No main() method. No imports. 3 lines of code.");
    }
}
```

**How to run:** `java CliConceptDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
spring run hello.groovy

Step 1: Detect annotations
  found: @RestController
  found: @GetMapping

Step 2: Infer & download dependencies
  resolving: spring-boot-starter-web (cached in ~/.groovy/grapes)
  resolving: spring-boot-starter (cached in ~/.groovy/grapes)

Step 3: Compile Groovy → bytecode → run in ApplicationContext
  Started HelloController on http://localhost:8080

No pom.xml. No main() method. No imports. 3 lines of code.
```

## 6. Walkthrough

- **`groovyScript` string** — represents what a developer writes. Note the absence of `import` statements — the CLI adds them based on annotation detection. In real Groovy, `@RestController` implies `import org.springframework.web.bind.annotation.*`; the CLI adds it silently.
- **`detectAnnotations`** — scans for known Spring annotations. The CLI's actual implementation is more sophisticated, using Groovy's AST (Abstract Syntax Tree) rather than string search, but the concept is the same.
- **`inferDependencies`** — maps annotation types to starter dependencies. `@RestController` / `@GetMapping` → web starter. `@Scheduled` → nothing extra (already in core starter). `@Grab("com.google.guava:guava:32.0.0")` → CLI passes it to Grape (Groovy's dependency downloader).
- **Step 3** — the CLI uses Groovy's `GroovyClassLoader` to compile and load the script class, then wraps it in a Spring `ApplicationContext`. Web-related annotations trigger an embedded server start.

## 7. Gotchas & takeaways

> **First run is slow.** The CLI downloads JARs on first use. Subsequent runs use the Groovy Grape cache (`~/.groovy/grapes`). Expect 30–60 seconds the first time, under 5 seconds after that.

> **The CLI does not support Maven or Gradle projects.** `spring run` only works with `.groovy` files. For a real project (`.java` files, `pom.xml`), use `./mvnw spring-boot:run` instead. Don't confuse the two use cases.

- Install via SDKMAN (`sdk install springboot`) on Mac/Linux — the simplest path.
- `spring --version` confirms installation is working.
- `spring run hello.groovy` = Groovy script → running Spring Boot app in seconds, no project structure needed.
- CLI is for experiments and demos, not production services.
- `spring shell` opens an interactive REPL for trying Spring APIs line by line.
