---
card: spring-boot
gi: 28
slug: starters-list-naming-convention-spring-boot-starter
title: Starters list & naming convention (spring-boot-starter-*)
---

## 1. What it is

A **Spring Boot starter** is a Maven/Gradle dependency that bundles a curated set of libraries for a specific capability. All official starters follow the naming convention `spring-boot-starter-{feature}` under the `org.springframework.boot` group.

**Official starter categories (selected):**

| Category | Starter | Key libraries included |
|---|---|---|
| Web | `spring-boot-starter-web` | Spring MVC, Tomcat, Jackson |
| Reactive web | `spring-boot-starter-webflux` | Spring WebFlux, Netty, Reactor |
| Data JPA | `spring-boot-starter-data-jpa` | Spring Data JPA, Hibernate, HikariCP |
| Data MongoDB | `spring-boot-starter-data-mongodb` | Spring Data MongoDB, MongoDB driver |
| Data Redis | `spring-boot-starter-data-redis` | Spring Data Redis, Lettuce |
| Security | `spring-boot-starter-security` | Spring Security, filters, crypto |
| Testing | `spring-boot-starter-test` | JUnit 5, Mockito, AssertJ, Spring Test |
| Actuator | `spring-boot-starter-actuator` | Micrometer, health, metrics |
| Batch | `spring-boot-starter-batch` | Spring Batch, H2 (for job repo) |
| Cache | `spring-boot-starter-cache` | Spring Cache abstraction |
| Mail | `spring-boot-starter-mail` | JavaMail, Spring email support |
| Validation | `spring-boot-starter-validation` | Hibernate Validator, Jakarta Validation |
| AMQP | `spring-boot-starter-amqp` | Spring AMQP, RabbitMQ client |
| Kafka | `spring-boot-starter-kafka` | Spring Kafka, Kafka client |
| Thymeleaf | `spring-boot-starter-thymeleaf` | Thymeleaf template engine |
| DevTools | `spring-boot-devtools` | Hot reload, live restart (dev only) |

The full list is in the Spring Boot reference documentation, Appendix E: Starters.

## 2. Why & when

**The naming convention is a contract.** Any dependency named `spring-boot-starter-{feature}` under `org.springframework.boot` is:
- Officially maintained by the Spring team.
- Tested with the corresponding Spring Boot release.
- Version-managed via the BOM (no `<version>` tag needed).

Third-party starters (not from Spring) follow a different convention: `{name}-spring-boot-starter`. For example:
- `mybatis-spring-boot-starter` — MyBatis
- `camel-spring-boot-starter` — Apache Camel

The reversed naming (`name-spring-boot-starter` vs `spring-boot-starter-name`) distinguishes community starters from official ones and prevents naming conflicts.

Know the starter list when:
- Starting a project on start.spring.io (search by feature name).
- Diagnosing missing auto-configuration (the right starter might not be added).
- Reviewing a `pom.xml` that lacks a dependency you'd expect.

## 3. Core concept

Every starter follows a consistent structure:

1. A near-empty POM with carefully chosen `<dependencies>`.
2. An optional `spring-boot-autoconfigure` fragment that registers auto-configuration classes.
3. The starter's `<dependency>` entries pull in the actual libraries.

There is also `spring-boot-starter` (no feature suffix) — the *core* starter that every other starter depends on. It includes:
- `spring-boot` (core framework)
- `spring-boot-autoconfigure`
- `spring-boot-starter-logging` (Logback + SLF4J)
- `spring-core` (Spring Framework core)
- `snakeyaml` (YAML parsing for `application.yml`)

You never add `spring-boot-starter` directly — it's a transitive dependency of every other starter.

**Starter selection strategy:** Add only the starters you need. Spring Boot's auto-configuration only fires for libraries on the classpath, so unnecessary starters add JAR weight and can enable auto-configuration you don't want.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot starters organised by category: web, data, messaging, infrastructure, and testing">
  <!-- Core -->
  <rect x="240" y="20" width="180" height="32" rx="6" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-starter (core)</text>

  <!-- Web column -->
  <rect x="20" y="68" width="140" height="160" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="88" fill="#79c0ff" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Web</text>
  <text x="90" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-web</text>
  <text x="90" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-webflux</text>
  <text x="90" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-thymeleaf</text>
  <text x="90" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-validation</text>
  <text x="90" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-security</text>

  <!-- Data column -->
  <rect x="175" y="68" width="140" height="160" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="245" y="88" fill="#79c0ff" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Data</text>
  <text x="245" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-data-jpa</text>
  <text x="245" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-data-mongodb</text>
  <text x="245" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-data-redis</text>
  <text x="245" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-data-cassandra</text>
  <text x="245" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-jdbc</text>

  <!-- Messaging column -->
  <rect x="330" y="68" width="140" height="160" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="88" fill="#79c0ff" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Messaging</text>
  <text x="400" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-amqp</text>
  <text x="400" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-kafka</text>
  <text x="400" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-batch</text>
  <text x="400" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-mail</text>
  <text x="400" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-integration</text>

  <!-- Ops column -->
  <rect x="485" y="68" width="160" height="160" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="88" fill="#79c0ff" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Ops / Test</text>
  <text x="565" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-actuator</text>
  <text x="565" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-test</text>
  <text x="565" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-devtools (dev only)</text>
  <text x="565" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-cache</text>
  <text x="565" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-aop</text>

  <!-- "All depend on core" label -->
  <text x="330" y="248" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All starters transitively depend on spring-boot-starter (core)</text>
</svg>

Every official starter is under `org.springframework.boot:spring-boot-starter-{feature}`; third-party starters follow `{name}-spring-boot-starter`.

## 5. Runnable example

```java
// File: StarterCatalogDemo.java
// Prints a categorised starter catalog matching the official Spring Boot starters.
// Run: java StarterCatalogDemo.java

import java.util.*;

public class StarterCatalogDemo {

    record Starter(String feature, String key, String includes) {}

    public static void main(String[] args) {
        var catalog = new LinkedHashMap<String, List<Starter>>();

        catalog.put("Web", List.of(
            new Starter("Spring Web",       "web",       "MVC, Tomcat, Jackson"),
            new Starter("Spring WebFlux",   "webflux",   "WebFlux, Netty, Reactor"),
            new Starter("Thymeleaf",        "thymeleaf", "Thymeleaf template engine"),
            new Starter("Validation",       "validation","Hibernate Validator, Jakarta Validation")
        ));
        catalog.put("Data", List.of(
            new Starter("Spring Data JPA",  "data-jpa",  "Hibernate, HikariCP, Spring Data"),
            new Starter("Spring Data Redis","data-redis","Lettuce client, Spring Data Redis"),
            new Starter("Spring Data MongoDB","data-mongodb","MongoDB driver, Spring Data"),
            new Starter("JDBC",             "jdbc",      "Spring JDBC, HikariCP")
        ));
        catalog.put("Security", List.of(
            new Starter("Spring Security",  "security",  "Filters, auth, crypto")
        ));
        catalog.put("Messaging", List.of(
            new Starter("AMQP (RabbitMQ)", "amqp",      "Spring AMQP, RabbitMQ client"),
            new Starter("Apache Kafka",     "kafka",     "Spring Kafka, kafka-clients"),
            new Starter("Spring Batch",     "batch",     "Spring Batch, H2 for job repo")
        ));
        catalog.put("Ops / Testing", List.of(
            new Starter("Actuator",         "actuator",  "Micrometer, health, metrics"),
            new Starter("Test",             "test",      "JUnit 5, Mockito, AssertJ, Spring Test"),
            new Starter("DevTools",         "devtools",  "Hot reload (development only)")
        ));

        System.out.println("=== Spring Boot Official Starters ===");
        System.out.println("All: org.springframework.boot:spring-boot-starter-{key}\n");

        catalog.forEach((category, starters) -> {
            System.out.println("[" + category + "]");
            for (var s : starters) {
                System.out.printf("  %-30s %-20s %s%n",
                    s.feature(), "starter-" + s.key(), s.includes());
            }
            System.out.println();
        });

        System.out.println("Third-party starters follow: {name}-spring-boot-starter");
        System.out.println("  e.g. mybatis-spring-boot-starter, camel-spring-boot-starter");
    }
}
```

**How to run:** `java StarterCatalogDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **`LinkedHashMap`** — preserves insertion order so categories print in the order they were added. A plain `HashMap` would print in arbitrary order, making the output confusing.
- **`Starter` record** — three fields: `feature` (human name), `key` (the suffix after `spring-boot-starter-`), `includes` (the key libraries bundled). This structure mirrors the real starter documentation table.
- **`catalog.forEach`** — iterates over entries in insertion order (because `LinkedHashMap`). The lambda receives category name and starter list. This is a clean functional alternative to nested `for` loops.
- **Format string** — `%-30s %-20s %s` left-justifies the first two columns in 30 and 20 characters respectively, making the table scannable at a glance.
- **Third-party note** — the naming distinction matters: `mybatis-spring-boot-starter` has `mybatis` first, indicating it's from the MyBatis project, not from the Spring team.

## 7. Gotchas & takeaways

> **`spring-boot-devtools` should be `optional` in Maven or `developmentOnly` in Gradle.** If it lands in the production fat JAR, it enables auto-restart and developer-friendly settings that are inappropriate (and slower) in production. Maven: `<optional>true</optional>`; Gradle: `developmentOnly("org.springframework.boot:spring-boot-devtools")`.

> **Adding a starter doesn't activate its feature — it adds the libraries.** Spring Boot's auto-configuration then uses `@ConditionalOnClass` to detect those libraries and wires them up. If auto-config for a starter doesn't fire, check that you've actually added the starter (not just the raw library JAR) and run with `--debug` to see the conditions report.

- Official starters: `org.springframework.boot:spring-boot-starter-{feature}` — no version needed.
- Third-party starters: `{name}-spring-boot-starter` — must specify a version; look for one in the Spring Boot BOM appendix first.
- Add only the starters you need; unused starters bloat the classpath and can trigger unexpected auto-configuration.
- `spring-boot-devtools` must be marked `optional` (Maven) or `developmentOnly` (Gradle) to stay out of production JARs.
- Full starter list: Spring Boot reference documentation → Appendix E: Starters.
