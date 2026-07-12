---
card: microservices
gi: 34
slug: spring-initializr-for-bootstrapping-a-service
title: Spring Initializr for bootstrapping a service
---

## 1. What it is

**Spring Initializr** (start.spring.io) is a project generator: given a small set of choices — build tool (Maven or Gradle), language, Spring Boot version, and a list of dependencies ("starters," see the next tutorial) — it generates a complete, ready-to-run project skeleton: build file, application class with a working `main` method, standard directory layout, and a basic test class. In a microservices system where new services get created far more often than in a monolith (where the project structure is usually set up once), Initializr turns "set up a new service's boilerplate" from a manual, error-prone, half-remembered process into a repeatable, few-seconds operation.

## 2. Why & when

Manually assembling a new Java service's project structure — the correct build file syntax, the right starting dependency versions that are actually compatible with each other, a correctly annotated main class, a working test setup — is exactly the kind of repetitive, detail-sensitive work that's easy to get subtly wrong by hand, especially the fifth or tenth time a team spins up a new service. Initializr encodes the "correct, current, compatible" answer to all of that, generated fresh each time, so a new service starts from a known-good baseline rather than a copy-pasted, possibly-stale template.

Use Initializr (or your organization's customized internal version of it, common in larger companies to also inject internal conventions — standard logging setup, standard health-check configuration) every time a genuinely new service is created. For an existing service, its build file is maintained directly rather than regenerated.

## 3. Core concept

Initializr's job, reduced to its essence, is a template-generation function: given a small set of inputs (project metadata, chosen dependencies), it deterministically produces a set of output files.

```
inputs:  { groupId, artifactId, buildTool, springBootVersion, dependencies: [web, actuator, ...] }
                                |
                          Initializr
                                |
outputs: { build file (pom.xml or build.gradle), Application.java, ApplicationTests.java, folder structure }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Initializr takes project metadata and a dependency list as input and produces a complete, ready-to-run project skeleton as output">
  <rect x="30" y="50" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Inputs</text>
  <text x="120" y="93" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">groupId, artifactId,</text>
  <text x="120" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">dependencies: [web, actuator]</text>

  <rect x="250" y="60" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Initializr</text>

  <rect x="420" y="50" width="190" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="515" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Outputs</text>
  <text x="515" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">pom.xml, Application.java,</text>
  <text x="515" y="102" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ApplicationTests.java, folders</text>

  <line x1="210" y1="85" x2="250" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a34)"/>
  <line x1="380" y1="85" x2="420" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a34)"/>
  <defs><marker id="a34" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A deterministic function: choices in, a complete project skeleton out.

## 5. Runnable example

Scenario: modeling Initializr's generation logic in plain Java — first producing a minimal skeleton, then adding dependency-driven file content, then generating two genuinely different services from the same generator to show the repeatability benefit.

### Level 1 — Basic

```java
// File: MinimalGenerator.java -- a MINIMAL model of what Initializr does:
// given a project name, produce the two core files' CONTENT as strings.
public class MinimalGenerator {
    static String generateBuildFile(String artifactId) {
        return "<project>\n  <artifactId>" + artifactId + "</artifactId>\n  <parent>spring-boot-starter-parent</parent>\n</project>";
    }

    static String generateApplicationClass(String artifactId) {
        String className = Character.toUpperCase(artifactId.charAt(0)) + artifactId.substring(1) + "Application";
        return "@SpringBootApplication\npublic class " + className + " {\n    public static void main(String[] args) {\n        SpringApplication.run(" + className + ".class, args);\n    }\n}";
    }

    public static void main(String[] args) {
        System.out.println("--- pom.xml ---");
        System.out.println(generateBuildFile("orders-service"));
        System.out.println("--- Application class ---");
        System.out.println(generateApplicationClass("orders-service"));
    }
}
```

**How to run:** `javac MinimalGenerator.java && java MinimalGenerator` (JDK 17+).

Expected output:
```
--- pom.xml ---
<project>
  <artifactId>orders-service</artifactId>
  <parent>spring-boot-starter-parent</parent>
</project>
--- Application class ---
@SpringBootApplication
public class Orders-serviceApplication {
    public static void main(String[] args) {
        SpringApplication.run(Orders-serviceApplication.class, args);
    }
}
```

This produces recognizable project skeleton content from just a name — but notice `Orders-serviceApplication` isn't valid Java (a class name can't contain a hyphen); a real generator needs to handle that conversion correctly, which the next level fixes.

### Level 2 — Intermediate

```java
// File: DependencyDrivenGenerator.java -- fix the naming issue AND make
// generated content depend on WHICH dependencies were chosen.
import java.util.*;

public class DependencyDrivenGenerator {
    static String toClassName(String artifactId) {
        // "orders-service" -> "OrdersService" -- a real generator must handle this kind of conversion correctly
        String[] parts = artifactId.split("-");
        StringBuilder sb = new StringBuilder();
        for (String part : parts) sb.append(Character.toUpperCase(part.charAt(0))).append(part.substring(1));
        return sb.toString();
    }

    static String generateBuildFile(String artifactId, List<String> dependencies) {
        StringBuilder deps = new StringBuilder();
        for (String dep : dependencies) deps.append("  <dependency>spring-boot-starter-").append(dep).append("</dependency>\n");
        return "<project>\n  <artifactId>" + artifactId + "</artifactId>\n" + deps + "</project>";
    }

    static String generateApplicationClass(String artifactId) {
        String className = toClassName(artifactId) + "Application";
        return "@SpringBootApplication\npublic class " + className + " {\n    public static void main(String[] args) {\n        SpringApplication.run(" + className + ".class, args);\n    }\n}";
    }

    public static void main(String[] args) {
        System.out.println(generateBuildFile("orders-service", List.of("web", "actuator")));
        System.out.println(generateApplicationClass("orders-service"));
    }
}
```

**How to run:** `javac DependencyDrivenGenerator.java && java DependencyDrivenGenerator` (JDK 17+).

Expected output:
```
<project>
  <artifactId>orders-service</artifactId>
  <dependency>spring-boot-starter-web</dependency>
  <dependency>spring-boot-starter-actuator</dependency>
</project>
@SpringBootApplication
public class OrdersServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrdersServiceApplication.class, args);
    }
}
```

`toClassName` now correctly converts `"orders-service"` into the valid Java identifier `OrdersService`, and the generated build file includes exactly the dependencies (`web`, `actuator`) that were requested — this is the shape of Initializr's real behavior: output driven directly by the specific choices made for this specific service.

### Level 3 — Advanced

```java
// File: GenerateTwoDifferentServices.java -- run the SAME generator TWICE
// with different inputs, producing TWO genuinely different, correct services.
import java.util.*;

public class GenerateTwoDifferentServices {
    static String toClassName(String artifactId) {
        String[] parts = artifactId.split("-");
        StringBuilder sb = new StringBuilder();
        for (String part : parts) sb.append(Character.toUpperCase(part.charAt(0))).append(part.substring(1));
        return sb.toString();
    }

    record ProjectSpec(String artifactId, List<String> dependencies) { }

    static Map<String, String> generateProject(ProjectSpec spec) {
        Map<String, String> files = new LinkedHashMap<>();
        StringBuilder deps = new StringBuilder();
        for (String dep : spec.dependencies()) deps.append("  <dependency>spring-boot-starter-").append(dep).append("</dependency>\n");
        files.put("pom.xml", "<project>\n  <artifactId>" + spec.artifactId() + "</artifactId>\n" + deps + "</project>");

        String className = toClassName(spec.artifactId()) + "Application";
        files.put(className + ".java", "@SpringBootApplication\npublic class " + className + " {\n    public static void main(String[] args) { SpringApplication.run(" + className + ".class, args); }\n}");
        return files;
    }

    public static void main(String[] args) {
        ProjectSpec ordersSpec = new ProjectSpec("orders-service", List.of("web", "actuator", "data-jpa"));
        ProjectSpec notificationsSpec = new ProjectSpec("notifications-service", List.of("web", "amqp")); // DIFFERENT deps entirely

        for (ProjectSpec spec : List.of(ordersSpec, notificationsSpec)) {
            System.out.println("=== generating " + spec.artifactId() + " ===");
            Map<String, String> files = generateProject(spec);
            for (String fileName : files.keySet()) System.out.println("  generated: " + fileName);
        }
    }
}
```

**How to run:** `javac GenerateTwoDifferentServices.java && java GenerateTwoDifferentServices` (JDK 17+).

Expected output:
```
=== generating orders-service ===
  generated: pom.xml
  generated: OrdersServiceApplication.java
=== generating notifications-service ===
  generated: pom.xml
  generated: NotificationsServiceApplication.java
```

The production-flavored payoff: the exact same `generateProject` function, given two different `ProjectSpec` inputs, correctly produces two entirely separate, correctly-named service skeletons — `OrdersServiceApplication.java` with JPA data-access dependencies, and `NotificationsServiceApplication.java` with messaging (`amqp`) dependencies instead. Neither generation run needed any manual naming or dependency-list bookkeeping; the generator's logic handled both correctly from the same, small set of rules.

## 6. Walkthrough

1. `generateProject(ordersSpec)` runs first: it builds the `deps` string by looping over `spec.dependencies()` (`web`, `actuator`, `data-jpa`), producing three `<dependency>` lines, and stores the resulting `pom.xml` content under the key `"pom.xml"` in `files`.
2. It then computes `className = toClassName("orders-service") + "Application"`, which resolves to `"OrdersServiceApplication"`, and stores the generated Java source under that filename.
3. `generateProject(notificationsSpec)` runs next, completely independently — a fresh `files` map, built from `notificationsSpec`'s own `artifactId` (`"notifications-service"`) and its own dependency list (`web`, `amqp`), producing `"NotificationsServiceApplication.java"` and a `pom.xml` with only the two requested dependencies.
4. The outer loop prints just the generated filenames for each spec, showing that both runs produced a complete, correctly-named project skeleton, driven entirely by each spec's own inputs — no manual intervention, no copy-pasting a template and editing it by hand, and no risk of accidentally leaving a stale dependency from a previous service's setup.

```
ProjectSpec(orders-service, [web, actuator, data-jpa])
        |
   generateProject -> pom.xml (3 deps) + OrdersServiceApplication.java

ProjectSpec(notifications-service, [web, amqp])
        |
   generateProject -> pom.xml (2 deps) + NotificationsServiceApplication.java
```

## 7. Gotchas & takeaways

> **Gotcha:** Initializr generates a *starting point*, not a finished, production-ready service — the generated skeleton still needs the team's actual business logic, proper testing, and typically some organization-specific conventions (logging format, standard health-check configuration) layered on top. Many organizations maintain a customized internal Initializr instance specifically to bake those conventions into every generated project automatically, so teams don't have to remember to add them by hand each time.

- Spring Initializr generates a complete, correctly-structured project skeleton from a small set of choices — build tool, Spring Boot version, and a dependency list — turning new-service bootstrapping into a fast, repeatable operation.
- This matters disproportionately in microservices, where new services are created far more often than in a monolith, making manual, error-prone project setup a real recurring cost worth eliminating.
- The generator's core logic is deterministic: the same inputs always produce the same, correct output — critical for consistency across many services created by different engineers at different times.
- Organizations at scale often run a customized internal Initializr to bake in company-specific conventions (standard logging, standard health checks) automatically, beyond what the public start.spring.io provides by default.
