---
card: spring-boot
gi: 29
slug: third-party-starters
title: Third-party starters
---

## 1. What it is

**Third-party starters** are community-built Spring Boot starters that integrate libraries not covered by the official Spring Boot starters. They follow the naming convention `{name}-spring-boot-starter` (note: prefix not suffix, to distinguish them from official `spring-boot-starter-{name}` starters).

Well-known examples:

| Library | Third-party starter | Publisher |
|---|---|---|
| MyBatis ORM | `mybatis-spring-boot-starter` | MyBatis team |
| Apache Camel | `camel-spring-boot-starter` | Apache |
| jOOQ | `jooq-spring-boot-starter` | jOOQ |
| AWS SDK | `spring-cloud-aws-starter` | Spring Cloud (AWS) |
| Bucket4j rate limiting | `bucket4j-spring-boot-starter` | community |
| OpenAPI / Swagger | `springdoc-openapi-starter-webmvc-ui` | springdoc.org |
| JHipster | `jhipster-framework` | JHipster team |

Each third-party starter ships its own auto-configuration classes and registers them in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`, so Spring Boot discovers and applies them exactly like official auto-configurations.

## 2. Why & when

Third-party starters exist because:
- The Spring team can't bundle every library in the ecosystem.
- Library authors want first-class Spring Boot integration without waiting for Spring to add it.
- Auto-configuration for a library requires deep knowledge of that library — the library's own team is best placed to write it.

Use a third-party starter when:
- You need a library that doesn't have an official Spring Boot starter (e.g., a specific ORM, a monitoring library, a cloud provider SDK).
- The library's documentation recommends its own starter.
- You want to avoid writing boilerplate integration code (that the starter already provides).

**Risk considerations:** Unlike official starters, third-party starters:
- May not align their versions with the Spring Boot release cycle.
- May lag on Spring Boot major version support (e.g., Boot 3.x / Spring Framework 6 support may arrive months after Boot 3.0's release).
- Vary in quality and maintenance activity.

## 3. Core concept

A third-party starter is structured identically to an official one:

```
mybatis-spring-boot-starter
  ├── mybatis-spring-boot-autoconfigure/   ← the actual auto-config
  │     src/main/resources/
  │     META-INF/spring/
  │       org.springframework.boot.autoconfigure.AutoConfiguration.imports
  │         → org.mybatis.spring.boot.autoconfigure.MybatisAutoConfiguration
  │
  └── mybatis-spring-boot-starter/        ← the thin dependency bundle
        pom.xml (depends on autoconfigure + mybatis-spring + spring-boot-starter-jdbc)
```

The `AutoConfiguration.imports` file is how Spring Boot discovers the starter's auto-configuration. When Spring Boot starts, it loads all files at this path from all JARs on the classpath and applies each listed class if its conditions pass.

**Checking third-party starter compatibility:**
1. Find the starter's GitHub page and check which Spring Boot version it targets.
2. Check whether the BOM manages it: `mvn dependency:tree | grep mybatis` or `./gradlew dependencies | grep mybatis`.
3. If in the BOM, add with no version; if not, check the starter's documentation for the compatible version.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Third-party starter structure and discovery mechanism via AutoConfiguration.imports file in the JAR">
  <!-- Your pom.xml -->
  <rect x="20" y="80" width="160" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="104" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Your pom.xml</text>
  <text x="100" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">mybatis-spring-boot-</text>
  <text x="100" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">starter:3.0.3</text>
  <text x="100" y="152" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(must specify version)</text>

  <line x1="180" y1="120" x2="220" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#tpArr)"/>

  <!-- Starter JAR -->
  <rect x="220" y="50" width="200" height="140" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="74" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">mybatis-spring-boot-starter</text>
  <rect x="236" y="84" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">mybatis-spring-boot-autoconfigure</text>
  <rect x="236" y="110" width="168" height="40" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="126" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">META-INF/spring/</text>
  <text x="320" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AutoConfiguration.imports</text>
  <rect x="236" y="156" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="171" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">mybatis-spring + spring-boot-starter-jdbc</text>

  <line x1="420" y1="120" x2="460" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#tpArr2)"/>
  <text x="440" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">discover</text>

  <!-- Auto-config fires -->
  <rect x="460" y="80" width="180" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="104" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Auto-config fires</text>
  <text x="550" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">MybatisAutoConfiguration</text>
  <text x="550" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">registers SqlSessionFactory,</text>
  <text x="550" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">MapperScannerConfigurer</text>

  <defs>
    <marker id="tpArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="tpArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Third-party starter JARs contain `AutoConfiguration.imports`; Spring Boot discovers and applies those classes exactly like official ones.

## 5. Runnable example

```java
// File: ThirdPartyStarterDemo.java
// Shows how Spring Boot discovers third-party starter auto-configurations.
// Run: java ThirdPartyStarterDemo.java

import java.util.*;

public class ThirdPartyStarterDemo {

    record StarterInfo(String artifact, String source, String version,
                       String inBom, String autoConfigClass) {}

    public static void main(String[] args) {
        var starters = List.of(
            new StarterInfo(
                "mybatis-spring-boot-starter",
                "MyBatis team",
                "3.0.3",
                "Yes (spring-boot-dependencies 3.x BOM)",
                "MybatisAutoConfiguration"
            ),
            new StarterInfo(
                "springdoc-openapi-starter-webmvc-ui",
                "springdoc.org",
                "2.5.0",
                "No — specify version manually",
                "SpringDocWebMvcActuatorAutoConfiguration"
            ),
            new StarterInfo(
                "camel-spring-boot-starter",
                "Apache Camel",
                "4.7.0",
                "No — use Camel BOM instead",
                "CamelAutoConfiguration"
            ),
            new StarterInfo(
                "bucket4j-spring-boot-starter",
                "community",
                "0.12.7",
                "No — specify version manually",
                "Bucket4JAutoConfiguration"
            )
        );

        System.out.println("=== Third-Party Spring Boot Starters ===\n");
        System.out.printf("  %-44s %-12s %-6s %s%n",
            "Artifact", "Version", "In BOM?", "Auto-Config Class");
        System.out.println("  " + "-".repeat(100));

        for (var s : starters) {
            System.out.printf("  %-44s %-12s %-6s %s%n",
                s.artifact(), s.version(), s.inBom().startsWith("Yes") ? "Yes" : "No",
                s.autoConfigClass());
        }

        System.out.println();
        System.out.println("=== How Spring Boot discovers third-party auto-config ===");
        System.out.println("1. At startup, Spring Boot reads ALL jars on classpath.");
        System.out.println("2. For each jar, looks for:");
        System.out.println("     META-INF/spring/org.springframework.boot.autoconfigure");
        System.out.println("                     .AutoConfiguration.imports");
        System.out.println("3. Each class listed there is evaluated for @Conditional* guards.");
        System.out.println("4. Passing classes register their @Beans in ApplicationContext.");
        System.out.println("5. No manual registration needed — the file does the wiring.");

        System.out.println();
        System.out.println("=== Checklist for adopting a third-party starter ===");
        List.of(
            "Check it targets your Spring Boot version (README/CHANGELOG)",
            "Verify version is in BOM; otherwise find the right version from docs",
            "Read its auto-configuration to understand what beans it creates",
            "Run with --debug and confirm the auto-config applied (or was skipped)",
            "Add it to your test suite — integration test the connection/behaviour"
        ).forEach(step -> System.out.println("  [ ] " + step));
    }
}
```

**How to run:** `java ThirdPartyStarterDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`StarterInfo` record** — captures the key facts a developer needs to evaluate a third-party starter: source, version to use, whether the BOM manages it, and which auto-config class to check when debugging.
- **`in BOM?` column** — the most important decision point. If it's in the Spring Boot BOM (like `mybatis-spring-boot-starter` 3.x), you add it without a version. If not (like `springdoc-openapi`), you must check the library's documentation for the compatible version against your Spring Boot version.
- **Discovery explanation** — steps 1-5 describe exactly what Spring Boot's `AutoConfigurationImportSelector` does. The `AutoConfiguration.imports` file is the contract between the third-party library and Spring Boot's discovery mechanism.
- **Checklist** — a practical evaluation flow: checking compatibility first prevents the most common issue (adding a Spring Boot 2.x-only starter to a Spring Boot 3.x project).

## 7. Gotchas & takeaways

> **Spring Boot 3.x broke many third-party starters.** The `javax.*` → `jakarta.*` namespace change in Boot 3.0 required every starter to be updated. If you're on Boot 3.x and a third-party starter hasn't been updated, you'll get `ClassNotFoundException` at startup. Check the starter's GitHub issues and changelog for Boot 3.x compatibility before adopting.

> **The old `spring.factories` auto-configuration registration is deprecated in Boot 3.x.** Starters written for Boot 2.x register auto-configurations in `META-INF/spring.factories` under the key `org.springframework.boot.autoconfigure.EnableAutoConfiguration`. Spring Boot 3.x prefers `AutoConfiguration.imports`. Old-format starters still work but may generate deprecation warnings.

- Third-party starters use `{name}-spring-boot-starter` naming (prefix, not suffix).
- Always check that the starter supports your Spring Boot version before adding it.
- Some third-party starters are in the Spring Boot BOM (e.g., MyBatis); most are not — check the BOM appendix first.
- Run with `--debug` after adding any new starter to verify its auto-configuration applied correctly.
- For popular integrations not covered by official starters (OpenAPI UI, rate limiting), third-party starters are the right tool; just validate compatibility first.
