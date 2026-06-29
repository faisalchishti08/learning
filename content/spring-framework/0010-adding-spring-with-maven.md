---
card: spring-framework
gi: 10
slug: adding-spring-with-maven
title: Adding Spring with Maven
---

## 1. What it is

To use Spring Boot in a Maven project you add a single parent POM and one or more starters. The **Spring Boot parent POM** manages all dependency versions through a Bill of Materials (BOM), so you never specify individual version numbers for Spring Framework, Spring Security, Jackson, Hibernate, or dozens of other curated libraries.

The two patterns:

**Pattern 1 — Spring Boot parent (most common):**
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.1</version>
</parent>
```
Inherits: dependency management, plugin management, Java source/target version, resource filtering, encoding.

**Pattern 2 — Import BOM (when you already have a parent):**
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.4.1</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```
Imports only the version management (not plugin config).

After either setup, add starters — the transitive dependency bundles that pull in everything for a feature:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <!-- No <version> needed — managed by parent/BOM -->
</dependency>
```

## 2. Why & when

Before Spring Boot, adding Spring Framework to a Maven project required manually specifying compatible versions for `spring-core`, `spring-beans`, `spring-context`, `spring-webmvc`, `spring-tx`, Jackson, Hibernate, SLF4J, and many more. Getting them all compatible was error-prone.

Boot's BOM solves the **version alignment problem**: every library in the curated set is tested together before a Boot release. The BOM is the single source of truth for "which version of Hibernate works with which version of Spring ORM works with which version of Spring Boot."

**You should use `spring-boot-starter-parent`** for standalone services, microservices, or any project that doesn't already inherit from a corporate parent POM.

**You should use `spring-boot-dependencies` BOM import** when your project must inherit from a company-wide parent POM (enforcing code style, plugin versions, repository mirrors, etc.). The import adds version management only — you keep your own plugin and property configuration.

## 3. Core concept

A **starter** is a convenience POM with no code of its own. It declares `<dependencies>` that pull in all the JARs needed for a feature. `spring-boot-starter-web` pulls in:

```
spring-boot-starter-web
  ├── spring-boot-starter        (core Boot auto-config)
  │     └── spring-boot
  │     └── spring-boot-autoconfigure
  ├── spring-boot-starter-json   (Jackson databind + datatype-jsr310)
  ├── spring-boot-starter-tomcat (embedded Tomcat)
  └── spring-webmvc              (DispatcherServlet, @Controller, @RequestMapping)
```

The `spring-boot-maven-plugin` does the heavy lifting at build time:
- `mvn spring-boot:run` — starts the app with a hot-reload-friendly classloader.
- `mvn package` — builds a **fat JAR** (also called "über-JAR") with all dependencies nested inside the JAR under `BOOT-INF/lib/`. Run with `java -jar target/myapp.jar`.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Maven dependency flow from parent BOM through starter to application JARs">
  <defs>
    <marker id="ma" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Parent POM -->
  <rect x="230" y="10" width="240" height="42" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="28" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-boot-starter-parent</text>
  <text x="350" y="44" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">version: 3.4.1 — manages ALL versions</text>

  <!-- Starter -->
  <rect x="230" y="78" width="240" height="42" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="96" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-boot-starter-web</text>
  <text x="350" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no &lt;version&gt; — inherited from parent</text>

  <!-- Resolved JARs -->
  <rect x="30"  y="150" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="105" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-webmvc</text>
  <text x="105" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">6.1.4 (auto)</text>

  <rect x="200" y="150" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="275" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jackson-databind</text>
  <text x="275" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2.17.2 (auto)</text>

  <rect x="370" y="150" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="445" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">tomcat-embed-core</text>
  <text x="445" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">10.1.19 (auto)</text>

  <rect x="540" y="150" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="615" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-auto</text>
  <text x="615" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">config</text>

  <!-- Arrows -->
  <line x1="350" y1="52" x2="350" y2="76" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="310" y1="120" x2="180" y2="148" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>
  <line x1="340" y1="120" x2="310" y2="148" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>
  <line x1="370" y1="120" x2="445" y2="148" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>
  <line x1="395" y1="120" x2="580" y2="148" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>

  <!-- Fat JAR label -->
  <rect x="200" y="210" width="300" height="32" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="350" y="230" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">mvn package → fat JAR with all JARs nested inside</text>
</svg>

One parent POM manages all versions; one starter pulls all transitive JARs; one Maven command builds a self-contained deployable.

## 5. Runnable example

A REST API for product management — built progressively using Maven conventions.

### Level 1 — Basic

The minimal `pom.xml` and main class needed to run a Spring Boot REST endpoint.

```java
// SpringMavenDemo.java — run with: java SpringMavenDemo.java
// Simulates the minimal Maven pom.xml + @SpringBootApplication structure.
// In a real project: create via https://start.spring.io or:
//   mvn archetype:generate -DarchetypeGroupId=org.springframework.boot
//                          -DarchetypeArtifactId=spring-boot-starter-parent

public class SpringMavenDemo {

    // In a real Spring Boot project the pom.xml looks like:
    /*
    <project>
        <parent>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-parent</artifactId>
            <version>3.4.1</version>
        </parent>

        <groupId>com.example</groupId>
        <artifactId>product-api</artifactId>
        <version>1.0-SNAPSHOT</version>
        <packaging>jar</packaging>

        <properties>
            <java.version>17</java.version>
        </properties>

        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web</artifactId>
            </dependency>
        </dependencies>

        <build>
            <plugins>
                <plugin>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-maven-plugin</artifactId>
                </plugin>
            </plugins>
        </build>
    </project>
    */

    // The resulting application class structure:
    record Product(int id, String name, double price) {}

    // @SpringBootApplication = @Configuration + @EnableAutoConfiguration + @ComponentScan
    // @RestController + @GetMapping → DispatcherServlet routes HTTP to this method
    static class ProductController {
        // @GetMapping("/products")
        java.util.List<Product> listProducts() {
            return java.util.List.of(
                new Product(1, "Laptop",  1299.99),
                new Product(2, "Monitor",  449.99)
            );
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Maven Project Structure ===\n");
        System.out.println("pom.xml:  declares parent + starters (no individual versions)");
        System.out.println("src/main/java/.../Application.java:  @SpringBootApplication main class");
        System.out.println("src/main/resources/application.properties:  config");
        System.out.println();
        System.out.println("Build commands:");
        System.out.println("  mvn spring-boot:run       — run with hot reload");
        System.out.println("  mvn package               — build fat JAR to target/");
        System.out.println("  java -jar target/app.jar  — run the fat JAR");
        System.out.println();
        System.out.println("What spring-boot-starter-web pulls in:");
        System.out.println("  spring-webmvc (DispatcherServlet, @Controller)");
        System.out.println("  spring-web (HttpMessageConverter, RestTemplate)");
        System.out.println("  spring-boot-starter-json (Jackson)");
        System.out.println("  spring-boot-starter-tomcat (embedded Tomcat 10.x)");

        System.out.println("\nSimulated GET /products response:");
        new ProductController().listProducts()
            .forEach(p -> System.out.println("  " + p));
    }
}
```

How to run: `java SpringMavenDemo.java`

In a real project `mvn spring-boot:run` would start an embedded Tomcat on port 8080. The controller would respond to `curl http://localhost:8080/products` with a JSON array. The only Maven configuration needed is the parent POM + one starter.

### Level 2 — Intermediate

Add the test scope, actuator, and JPA starters — and show how dependency scopes work in Maven.

```java
// SpringMavenV2.java — run with: java SpringMavenV2.java
// Shows pom.xml with multiple starters, scopes, and the version management benefit.

import java.util.*;

public class SpringMavenV2 {

    // pom.xml additions:
    /*
    <dependencies>
        <!-- Web layer — compile scope (default) -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Data + JPA — compile scope; pulls Hibernate 6 + HikariCP connection pool -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>

        <!-- H2 for development/testing — runtime scope (not on compile classpath) -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Actuator — health, metrics, info endpoints — compile scope -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- Test scope — not bundled in fat JAR -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    */

    // What each starter pulls in:
    record StarterSummary(String starter, String scope, List<String> keyDeps) {}

    public static void main(String[] args) {
        List<StarterSummary> starters = List.of(
            new StarterSummary("spring-boot-starter-web", "compile",
                List.of("spring-webmvc", "spring-boot-starter-tomcat", "jackson-databind")),
            new StarterSummary("spring-boot-starter-data-jpa", "compile",
                List.of("spring-data-jpa", "spring-orm", "hibernate-core:6.4.x", "HikariCP")),
            new StarterSummary("h2", "runtime",
                List.of("h2:2.x (H2 in-memory DB — not on compile classpath)")),
            new StarterSummary("spring-boot-starter-actuator", "compile",
                List.of("spring-boot-actuator", "micrometer-core",
                    "endpoints: /actuator/health, /actuator/metrics")),
            new StarterSummary("spring-boot-starter-test", "test",
                List.of("junit-jupiter:5.x", "mockito-core", "spring-test", "assertj-core",
                    "NOT bundled in fat JAR"))
        );

        System.out.println("=== Maven Starters — What Gets Pulled In ===\n");
        for (StarterSummary s : starters) {
            System.out.printf("%-45s [%s]%n", s.starter(), s.scope());
            s.keyDeps().forEach(d -> System.out.println("    → " + d));
            System.out.println();
        }

        System.out.println("=== Version management benefit ===");
        System.out.println("  All versions above are managed by spring-boot-starter-parent:3.4.1");
        System.out.println("  You never write: <version>6.4.4.Final</version> for Hibernate");
        System.out.println("  You never write: <version>5.3.25</version> for Spring Framework");
        System.out.println("  Boot's BOM guarantees all these versions work together.");
        System.out.println("\n  mvn dependency:tree | grep spring  → shows full resolved tree");
    }
}
```

How to run: `java SpringMavenV2.java`

The `runtime` scope for H2 means the database driver is not available during compilation — you code against JDBC/JPA interfaces, not H2 specifics. The `test` scope keeps test libraries out of the fat JAR, reducing its size.

### Level 3 — Advanced

Multi-module Maven project structure — parent POM + `api` module + `service` module, showing how Spring Boot's BOM propagates across the hierarchy.

```java
// SpringMavenV3.java — run with: java SpringMavenV3.java
// Shows multi-module Maven project with Spring Boot BOM inheritance.

import java.util.*;

public class SpringMavenV3 {

    record Module(String artifactId, String packaging, String parent,
                  List<String> dependencies, String notes) {}

    public static void main(String[] args) {
        System.out.println("=== Multi-module Maven project with Spring Boot ===\n");

        // Root parent POM (packaging=pom, no code)
        Module root = new Module(
            "order-platform",       "pom",
            "spring-boot-starter-parent:3.4.1",
            List.of("<modules>: api, service, gateway"),
            "Declares spring-boot-starter-parent as parent; no code here");

        // API module (shared DTOs/interfaces, no Spring Boot dependency)
        Module api = new Module(
            "order-platform-api",   "jar",
            "order-platform",
            List.of("No starters — just domain records and interfaces"),
            "Packaged as a plain JAR; consumed by service module");

        // Service module (the Spring Boot app)
        Module service = new Module(
            "order-platform-service", "jar",
            "order-platform",
            List.of(
                "spring-boot-starter-web",
                "spring-boot-starter-data-jpa",
                "order-platform-api (sibling module)"),
            "Has @SpringBootApplication; fat JAR is built here");

        // Gateway module (another Spring Boot app — reactive)
        Module gateway = new Module(
            "order-platform-gateway", "jar",
            "order-platform",
            List.of("spring-boot-starter-webflux", "spring-cloud-starter-gateway"),
            "Separate Boot app — routes traffic to service module");

        for (Module m : List.of(root, api, service, gateway)) {
            System.out.printf("Module: %s (packaging=%s)%n", m.artifactId(), m.packaging());
            System.out.printf("  Parent:       %s%n", m.parent());
            System.out.printf("  Dependencies: %s%n", m.dependencies());
            System.out.printf("  Notes:        %s%n%n", m.notes());
        }

        System.out.println("=== Build commands ===");
        System.out.println("  mvn install                          — build all modules");
        System.out.println("  mvn -pl order-platform-service package — build only the service");
        System.out.println("  mvn -pl order-platform-service spring-boot:run — run the service");
        System.out.println("  mvn versions:display-dependency-updates — show available upgrades");
        System.out.println("  mvn dependency:tree -Dincludes=org.springframework — show Spring tree");

        System.out.println("\n=== BOM propagation in a multi-module project ===");
        System.out.println("  root pom inherits spring-boot-starter-parent:3.4.1");
        System.out.println("  → api pom inherits from root → no Spring deps, but BOM available");
        System.out.println("  → service pom inherits from root → spring-boot-starter-web (version from BOM)");
        System.out.println("  → gateway pom inherits from root → spring-boot-starter-webflux (version from BOM)");
        System.out.println("  One version bump in root pom.xml upgrades all modules together.");
    }
}
```

How to run: `java SpringMavenV3.java`

The multi-module layout is the standard pattern for microservice platforms: a root parent manages the BOM, shared domain objects live in the API module, and each service module inherits the BOM automatically without repeating the parent declaration.

## 6. Walkthrough

**Level 1 — what happens when you run `mvn package`:**

1. Maven reads `pom.xml`. `<parent>spring-boot-starter-parent:3.4.1</parent>` triggers a download of the parent POM chain: `spring-boot-starter-parent` → `spring-boot-dependencies` (the BOM).
2. `<dependency>spring-boot-starter-web` (no version) → Maven looks up the version in the BOM: `spring-boot-starter-web:3.4.1`. Maven resolves all transitive dependencies, again using BOM versions.
3. Compilation: all resolved JARs are on the classpath. `ProductController` compiles against Spring MVC APIs.
4. `spring-boot-maven-plugin` runs in the `package` phase. It reads the application JAR and all dependency JARs, and produces a fat JAR where:
   - Your classes are at `BOOT-INF/classes/`
   - All dependency JARs are at `BOOT-INF/lib/`
   - `org.springframework.boot.loader.JarLauncher` is the JAR manifest's `Main-Class`
5. `java -jar target/product-api-1.0-SNAPSHOT.jar` launches `JarLauncher`, which builds a special classloader that reads from `BOOT-INF/`, then calls your `@SpringBootApplication` main.

**Request/response in the running app (Level 1):**
```
GET /products HTTP/1.1

→ Tomcat servlet container receives the request
→ DispatcherServlet (configured by spring-boot-starter-web auto-config)
→ Routes to ProductController.listProducts() via @GetMapping("/products")
→ Return value [Product(1,...), Product(2,...)] passed to Jackson MessageConverter
→ Serialised as JSON array: [{"id":1,"name":"Laptop","price":1299.99},...]

HTTP/1.1 200 OK
Content-Type: application/json
[{"id":1,"name":"Laptop","price":1299.99},{"id":2,"name":"Monitor","price":449.99}]
```

**Level 2 — scopes in the fat JAR:**
- `compile` → inside `BOOT-INF/lib/` in the fat JAR.
- `runtime` (H2) → inside `BOOT-INF/lib/` — available at runtime but not referenced at compile time.
- `test` → NOT in the fat JAR. Only present during `mvn test` and `mvn verify`.
- `provided` → NOT in the fat JAR. Assumes the runtime container provides it (e.g., Tomcat when deploying a WAR to an external Tomcat instead of embedded).

## 7. Gotchas & takeaways

> **Never specify `<version>` for Spring starters if you use the parent POM or BOM import.** Specifying a version overrides the BOM-managed version, which can cause version mismatches (e.g., `spring-boot-starter-web:3.4.1` but `spring-boot-autoconfigure:3.3.5`). Let the BOM manage all Spring ecosystem versions.

> **`spring-boot-starter-parent` sets `<java.version>17</java.version>` by default in Spring Boot 3.x.** If you need Java 21, override it: `<properties><java.version>21</java.version></properties>`. This sets both `maven.compiler.source` and `maven.compiler.target`.

- `mvn dependency:tree` is the fastest way to understand what a starter pulls in transitively.
- Exclude transitive dependencies with `<exclusions>` — e.g., exclude `spring-boot-starter-logging` to use Log4j2 instead of Logback.
- `spring-boot-maven-plugin` must be present for `spring-boot:run` and fat-JAR packaging; without it `mvn package` produces a plain JAR that can't boot.
- `mvn versions:use-latest-releases -DincludesParent=true` can auto-bump the parent version — run in a feature branch and test before merging.
- Spring Initializr (`start.spring.io`) generates the correct `pom.xml` scaffold; always the fastest starting point for a new project.
