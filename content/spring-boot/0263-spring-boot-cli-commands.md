---
card: spring-boot
gi: 263
slug: spring-boot-cli-commands
title: Spring Boot CLI commands
---

## 1. What it is

The **Spring Boot CLI** (`spring`) is a command-line tool for quickly prototyping Spring Boot applications, running Groovy scripts, and managing project scaffolding — without needing a full Maven or Gradle project setup.

Core CLI commands:

| Command | What it does |
|---|---|
| `spring run app.groovy` | Run a Groovy Spring Boot script without any build file |
| `spring init` | Scaffold a new Spring Boot project (same as start.spring.io) |
| `spring shell` | Drop into an interactive shell for multiple commands |
| `spring test` | Run Groovy tests |
| `spring jar` | Package a Groovy script into a self-contained JAR |
| `spring help` | Show all commands and their options |

## 2. Why & when

The CLI is useful for:

- **Quick prototypes** — type `spring run app.groovy` and have a running web server in 30 seconds, no `pom.xml` required.
- **Scripting** — write small utilities in Groovy that use Spring's DI and auto-configuration.
- **Project scaffolding** — `spring init` creates a ready-to-use Maven or Gradle project, equivalent to using start.spring.io but from the terminal.
- **Demos and workshops** — show Spring concepts without project boilerplate.

The CLI is less useful for:
- Production applications (use Maven/Gradle).
- Teams that don't use Groovy.
- CI/CD pipelines (where a proper build tool is expected).

Spring Boot 3.x still supports the CLI but its primary use case has shifted toward `spring init`; Groovy script execution is a secondary feature. Most developers encounter the CLI through `spring init`.

## 3. Core concept

The CLI wraps Spring Boot's Groovy compiler integration. A Groovy script can omit imports for common Spring classes; the CLI adds them automatically via a `CompilerAutoConfiguration`. A minimal web app:

```groovy
// app.groovy — run with: spring run app.groovy
@RestController
class App {
    @GetMapping("/")
    String hello() { "Hello from Spring Boot CLI" }
}
```

The CLI detects `@RestController` and automatically adds:
- `spring-boot-starter-web` to the classpath.
- The Spring Boot application runner.
- All necessary imports.

For `spring init`, the CLI calls the Spring Initializr REST API (`start.spring.io`) and downloads a zip of the scaffolded project, equivalent to clicking "Generate" on the web UI.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot CLI: run Groovy scripts, scaffold projects, or interact via shell">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- CLI -->
  <rect x="240" y="90" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="110" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">spring (CLI)</text>
  <text x="350" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Installed via SDKMan / Homebrew</text>

  <!-- Outputs -->
  <rect x="30" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring run app.groovy</text>
  <text x="110" y="66" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Groovy → running server</text>

  <rect x="30" y="100" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring init</text>
  <text x="110" y="136" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">→ Maven/Gradle project ZIP</text>

  <rect x="30" y="170" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="190" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring jar app.groovy</text>
  <text x="110" y="206" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">→ executable JAR</text>

  <rect x="510" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="600" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring shell</text>
  <text x="600" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Interactive REPL</text>

  <rect x="510" y="100" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="600" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring test</text>
  <text x="600" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Run Groovy test scripts</text>

  <line x1="240" y1="110" x2="192" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="240" y1="120" x2="192" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="240" y1="130" x2="192" y2="192" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="460" y1="110" x2="508" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="460" y1="120" x2="508" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
</svg>

The `spring` CLI is a single entry point for running scripts, scaffolding projects, and packaging Groovy apps as JARs.

## 5. Runnable example

```java
// SpringCliDemo.java — run with: java SpringCliDemo.java
// Shows CLI installation, key commands with examples, and the
// Groovy auto-import mechanism. (No CLI binary required to run this demo.)

public class SpringCliDemo {

    public static void main(String[] args) {
        System.out.println("=== Spring Boot CLI Commands ===\n");
        printInstallation();
        printGroovyExample();
        printKeyCommands();
        printInitExamples();
    }

    static void printInstallation() {
        System.out.println("--- Installation ---");
        System.out.println("""
            # SDKMan (recommended — manages multiple versions):
            sdk install springboot
            spring --version

            # Homebrew (macOS):
            brew tap spring-io/tap
            brew install spring-boot

            # Manual: download spring-boot-cli-3.x.x-bin.zip from
            #         https://repo.maven.apache.org/maven2/org/springframework/boot/spring-boot-cli/
            #         and add bin/ to PATH
            """);
    }

    static void printGroovyExample() {
        System.out.println("--- Minimal Groovy web app (save as app.groovy) ---");
        System.out.println("""
            // app.groovy
            // CLI auto-adds: import, @SpringBootApplication, spring-boot-starter-web
            @RestController
            class App {
                @GetMapping("/hello")
                String hello(@RequestParam(defaultValue = "World") String name) {
                    "Hello, ${name}! Running on Spring Boot CLI."
                }

                @GetMapping("/time")
                Map time() {
                    [timestamp: System.currentTimeMillis(), thread: Thread.currentThread().name]
                }
            }

            // Run: spring run app.groovy
            // Test: curl http://localhost:8080/hello?name=CLI
            """);
    }

    static void printKeyCommands() {
        System.out.println("--- Key CLI commands ---");
        String[][] cmds = {
            {"spring run app.groovy",
             "Run a Groovy Spring Boot script (auto-resolves dependencies)"},
            {"spring run *.groovy",
             "Run multiple Groovy scripts as one application"},
            {"spring run app.groovy -- --server.port=9090",
             "Pass Spring properties after '--'"},
            {"spring jar myapp.jar app.groovy",
             "Package Groovy script as self-contained JAR"},
            {"spring test app-test.groovy",
             "Run Groovy test scripts with @SpringApplicationConfiguration"},
            {"spring shell",
             "Interactive shell (tab completion for all commands)"},
            {"spring help run",
             "Detailed help for a specific command"},
            {"spring grab",
             "Pre-download dependencies for offline use"},
        };
        for (var c : cmds) {
            System.out.printf("  %-50s  %s%n", c[0], c[1]);
        }
        System.out.println();
    }

    static void printInitExamples() {
        System.out.println("--- spring init: scaffold a new project ---");
        System.out.println("""
            # List available dependencies:
            spring init --list

            # Create a Maven project with web + JPA + devtools:
            spring init --dependencies=web,data-jpa,devtools myapp

            # Gradle project, Java 21, Spring Boot 3.3:
            spring init \\
              --build=gradle \\
              --java-version=21 \\
              --boot-version=3.3.0 \\
              --dependencies=web,data-jpa,actuator,validation \\
              --group-id=com.example \\
              --artifact-id=demo \\
              --name=Demo \\
              myapp.zip

            # Unzip and start:
            unzip myapp.zip -d myapp && cd myapp && ./gradlew bootRun

            # Short form (most flags have single-char aliases):
            spring init -d=web,actuator -n=MyApp -a=myapp myapp
            """);
    }
}
```

**How to run:** `java SpringCliDemo.java`

## 6. Walkthrough

- **Groovy auto-imports** — the CLI's `CompilerAutoConfiguration` intercepts Groovy compilation and adds `@SpringBootApplication`, imports for `@RestController`, `@GetMapping`, `@RequestParam`, etc. You don't write them. The CLI also resolves Maven dependencies based on annotations it finds (e.g., `@RestController` implies `spring-boot-starter-web`).
- **`spring run app.groovy -- --server.port=9090`** — arguments after `--` are passed to the Spring application, not to the CLI itself. Without `--`, `--server.port=9090` would be interpreted as a CLI flag.
- **`spring jar`** — packages the Groovy script and all its resolved dependencies into a fat JAR with a standard `MANIFEST.MF`. The result is runnable with `java -jar myapp.jar` without the CLI installed.
- **`spring init --list`** — shows all available starter IDs (the values for `--dependencies`). The list is fetched from `start.spring.io` and matches what you see on the web UI.
- **`spring init` without args** — creates a `demo.zip` with the defaults (Maven, Java, `spring-boot-starter` only). Usually you'll at least add `-d=web`.

## 7. Gotchas & takeaways

> **The CLI's Groovy execution is not suitable for production** — dependencies are downloaded dynamically (from Maven Central), imports are implicit, and the build process is non-reproducible compared to Maven/Gradle. Use the CLI for prototyping; export to a proper project for production.

> **`spring init` contacts `start.spring.io` by default.** If you're behind a corporate proxy or firewall, set `HTTPS_PROXY` or configure the CLI to point at an internal Initializr instance with `spring init --target=http://internal-initializr/starter.zip ...`.

- SDKMan makes CLI version management easy — `sdk install springboot 3.3.0` and `sdk use springboot 3.3.0`.
- The `spring shell` interactive mode supports tab-completion for all command options — useful for exploring `spring init` options.
- `spring run --watch app.groovy` — automatically restarts the Groovy app when the source file changes (built-in watch mode, no DevTools needed for Groovy scripts).
- The CLI's `-cp` flag adds extra classpath entries: `spring run -cp mylib.jar app.groovy`.
