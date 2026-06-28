---
card: spring-boot
gi: 264
slug: spring-initializr-usage-from-cli-ide
title: Spring Initializr usage from CLI / IDE
---

## 1. What it is

**Spring Initializr** is a web service (hosted at `start.spring.io`) that generates a ready-to-use Spring Boot project skeleton — `pom.xml`/`build.gradle`, directory structure, a main class, and a test class — based on your selections. You choose the build tool, language, Spring Boot version, Java version, and dependencies ("starters").

You can use it via:

1. **Web browser** — `start.spring.io`
2. **Spring Boot CLI** — `spring init --dependencies=web,data-jpa myapp`
3. **IntelliJ IDEA** — `New Project → Spring` (built-in wizard backed by Initializr)
4. **VS Code** — Spring Initializr Java Support extension (`Ctrl+Shift+P → Spring Initializr`)
5. **Eclipse / STS** — `New → Spring Starter Project` (Spring Tool Suite)
6. **HTTP / curl** — `curl https://start.spring.io/starter.zip -d dependencies=web,actuator -o demo.zip`
7. **Internal Initializr** — companies host their own instance with corporate starters pre-configured

All of these call the same REST API under the hood.

## 2. Why & when

Initializr exists because creating a Spring Boot project from scratch involves:
- Choosing the right parent POM version.
- Finding and adding correct starter coordinates.
- Creating the package directory structure.
- Writing a valid `@SpringBootApplication` main class.
- Setting up a test class.

Initializr does all of this in seconds. The generated project compiles and runs immediately — no manual setup. Use it at the start of every new Spring Boot project rather than copying an old one (which carries stale dependencies and configurations).

## 3. Core concept

Spring Initializr is a REST API service. The key endpoint:

```
GET/POST https://start.spring.io/starter.zip
```

Parameters:
- `type` — `maven-project` or `gradle-project`
- `language` — `java`, `kotlin`, `groovy`
- `bootVersion` — e.g., `3.3.0`
- `javaVersion` — `17`, `21`, `23`
- `groupId`, `artifactId`, `name`, `description`, `packageName`
- `dependencies` — comma-separated starter IDs (`web`, `data-jpa`, `actuator`, `devtools`, etc.)

The response is a ZIP file. Initializr renders it from **Mustache templates** that are parameterised with your choices. You can also view the project metadata API at `start.spring.io/metadata/config` (JSON describing all available options and their defaults).

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Initializr accessed from multiple clients: web, CLI, IDE, curl">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Initializr server -->
  <rect x="265" y="90" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="115" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Initializr</text>
  <text x="350" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">start.spring.io API</text>

  <!-- Clients -->
  <rect x="10" y="30" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="53" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Web browser</text>

  <rect x="10" y="90" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="113" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">spring init CLI</text>

  <rect x="10" y="150" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="173" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">curl / scripts</text>

  <rect x="560" y="30" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="53" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">IntelliJ IDEA</text>

  <rect x="560" y="90" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="113" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">VS Code</text>

  <rect x="560" y="150" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="173" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Eclipse / STS</text>

  <!-- Left arrows -->
  <line x1="140" y1="48" x2="263" y2="107" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="140" y1="108" x2="263" y2="118" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="140" y1="168" x2="263" y2="133" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Right arrows -->
  <line x1="437" y1="107" x2="558" y2="48" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="437" y1="118" x2="558" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="437" y1="133" x2="558" y2="168" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="218" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All clients call the same REST API → receive a ZIP with ready-to-run project</text>
</svg>

Multiple entry points, one API; all produce the same ready-to-compile project ZIP.

## 5. Runnable example

```java
// InitializrDemo.java — run with: java InitializrDemo.java
// Shows all ways to use Spring Initializr: CLI, curl, and IDE workflows.
// No actual HTTP calls are made — prints the exact commands.

public class InitializrDemo {

    public static void main(String[] args) {
        System.out.println("=== Spring Initializr Usage from CLI / IDE ===\n");
        printCliExamples();
        printCurlExamples();
        printIdeWorkflows();
        printApiExploration();
    }

    static void printCliExamples() {
        System.out.println("--- spring init CLI ---");
        System.out.println("""
            # Minimal: web + devtools, Maven, Java 21 (defaults)
            spring init --dependencies=web,devtools myapp
            cd myapp && mvn spring-boot:run

            # Full spec:
            spring init \\
              --build=gradle \\
              --language=java \\
              --boot-version=3.3.0 \\
              --java-version=21 \\
              --group-id=com.acme \\
              --artifact-id=order-service \\
              --name=OrderService \\
              --description="Order management microservice" \\
              --package-name=com.acme.order \\
              --dependencies=web,data-jpa,actuator,devtools,validation,flyway \\
              order-service

            # List all available starter IDs:
            spring init --list

            # Use an internal Initializr (corporate):
            spring init --target=https://initializr.mycompany.com/starter.zip \\
              --dependencies=web,company-security-starter myapp
            """);
    }

    static void printCurlExamples() {
        System.out.println("--- curl (scripting / CI scaffolding) ---");
        System.out.println("""
            # Download and unzip in one step:
            curl https://start.spring.io/starter.zip \\
              -d type=maven-project \\
              -d language=java \\
              -d bootVersion=3.3.0 \\
              -d baseDir=myapp \\
              -d groupId=com.example \\
              -d artifactId=myapp \\
              -d javaVersion=21 \\
              -d dependencies=web,actuator,devtools \\
              -o myapp.zip && unzip myapp.zip

            # View project metadata (all options):
            curl -s https://start.spring.io/metadata/config | python3 -m json.tool | head -60

            # Generate Kotlin + Gradle project:
            curl https://start.spring.io/starter.zip \\
              -d type=gradle-project \\
              -d language=kotlin \\
              -d dependencies=web,data-jpa \\
              -o myapp-kotlin.zip
            """);
    }

    static void printIdeWorkflows() {
        System.out.println("--- IDE integration ---");
        System.out.println("""
            IntelliJ IDEA (Ultimate or with Spring plugin):
              File → New → Project → Spring
              Select: Maven/Gradle, Java version, Spring Boot version
              Search and add dependencies in the "Dependencies" panel
              Finish → project is created and indexed immediately

            VS Code (Spring Initializr Java Support extension):
              Ctrl+Shift+P → "Spring Initializr: Create a Maven Project"
              Follow the prompt wizard — same fields as the web UI
              Extension calls start.spring.io and extracts the ZIP locally

            Eclipse / Spring Tool Suite:
              File → New → Spring Starter Project
              Same wizard, backed by start.spring.io or a custom server
              STS auto-detects and imports the generated project

            IntelliJ CE (free):
              No built-in Spring wizard; use File → New → Project from Version Control
              or generate via CLI/web and import as existing Maven/Gradle project
            """);
    }

    static void printApiExploration() {
        System.out.println("--- Exploring the Initializr API ---");
        System.out.println("""
            # All available dependencies:
            curl -s https://start.spring.io/dependencies | python3 -c "
            import json,sys
            data = json.load(sys.stdin)
            for grp in data['dependencies']['values']:
                print(grp['name'])
                for dep in grp['values']:
                    print(f'  {dep[\"id\"]:35} {dep[\"name\"]}')
            "

            # All available Spring Boot versions:
            curl -s https://start.spring.io/actuator/info | python3 -m json.tool

            # Generate and inspect without unzipping:
            curl -s https://start.spring.io/starter.zip \\
              -d dependencies=web -d type=maven-project \\
              | unzip -p - '*/pom.xml'
            """);
    }
}
```

**How to run:** `java InitializrDemo.java`

## 6. Walkthrough

- **`spring init --list`** — contacts `start.spring.io` and downloads the full dependency catalog. Starters are grouped by category (Core, Web, Template Engines, SQL, NoSQL, Messaging, etc.) with their IDs and descriptions. IDs like `web`, `data-jpa`, and `actuator` are what you pass to `--dependencies`.
- **`--target=https://initializr.mycompany.com`** — companies host private Initializr instances with additional starters for internal libraries (company security, logging, tracing). The CLI `--target` flag redirects all Initializr commands to that server.
- **curl `| unzip -p - '*/pom.xml'`** — pipes the downloaded ZIP directly to `unzip` and prints a specific file without writing to disk. Useful in CI scripts that need to inspect generated files without storing the whole ZIP.
- **VS Code extension** — `vscjava.vscode-spring-initializr` (Spring Initializr Java Support) in the VS Code marketplace. After installing, the command palette (`Ctrl+Shift+P`) exposes `Spring Initializr: Create Maven/Gradle Project` with a multi-step wizard.
- **`metadata/config` endpoint** — returns JSON describing all options (dependency groups, versions, language choices, java versions) that the Initializr supports. IDEs parse this to populate their wizard dropdowns dynamically, so they always show current options.

## 7. Gotchas & takeaways

> **The generated project uses the exact dependency versions managed by the Spring Boot BOM** — you don't need to specify versions for most starters. Adding `<version>` to a managed starter is unnecessary and can cause version conflicts. Only add versions for dependencies not managed by the BOM.

> **`spring init` creates a directory, not a ZIP, when you omit the `.zip` extension.** `spring init myapp` → creates and extracts the project into `myapp/`. `spring init myapp.zip` → saves the ZIP file. Most of the time you want the directory form.

- Use `spring init --list` before starting a new project to see all available starters — the list is comprehensive and you may find relevant starters you didn't know existed.
- The `spring-boot-starter-*` naming convention: every "starter" dependency auto-configures a specific technology; you pick only the ones you need.
- After generation, open the project in your IDE and check that the Java SDK version matches what was specified in `pom.xml` / `build.gradle`.
- The web UI (`start.spring.io`) has a dependency search box — type "kafka" and it shows all Kafka-related starters. Very useful for discovery.
- The CLI `--dependencies` flag is the same as clicking checkboxes on the web UI — same IDs, same result.
