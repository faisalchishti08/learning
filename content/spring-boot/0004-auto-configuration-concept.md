---
card: spring-boot
gi: 4
slug: auto-configuration-concept
title: Auto-configuration concept
---

## 1. What it is

**Auto-configuration** is Spring Boot's mechanism for automatically creating and wiring beans based on what it finds on the classpath, in the environment, and in your own application context — without you writing a single `@Bean` method for common infrastructure.

When Spring Boot starts, it reads the list of auto-configuration classes registered in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (the modern format) or `spring.factories` (older). Each class is annotated with `@ConditionalOn*` guards that say "only activate if these conditions are true." If the conditions match, the class's `@Bean` methods fire and infrastructure beans appear in your `ApplicationContext`.

Examples of what auto-configuration produces automatically:

- `DataSourceAutoConfiguration` → creates a `DataSource` when `spring-boot-starter-data-jpa` is on the classpath and you've provided `spring.datasource.url`.
- `WebMvcAutoConfiguration` → registers `DispatcherServlet`, content negotiation, message converters when Spring Web is on the classpath.
- `SecurityAutoConfiguration` → sets up a default login page and HTTP Basic auth when Spring Security is present.

## 2. Why & when

Before auto-configuration, a Spring JPA project needed a manual Java config class like:

```java
@Bean public DataSource dataSource() { ... }
@Bean public LocalContainerEntityManagerFactoryBean entityManagerFactory() { ... }
@Bean public JpaTransactionManager transactionManager() { ... }
```

That's 15–30 lines of boilerplate that looks the same in every project. Auto-configuration replaces this with **zero lines** in the common case. You get a correctly configured, pooled, transaction-managed JPA setup from `spring.datasource.url=jdbc:postgresql://...` alone.

Know about auto-configuration when:
- Something isn't wiring up as expected (run with `--debug` to see the conditions report).
- You want to replace an auto-configured bean with your own implementation.
- You're writing a library that should integrate seamlessly with Spring Boot projects.

## 3. Core concept

Auto-configuration is conditional bean registration. The `@ConditionalOn*` annotations are the key:

| Annotation | Fires when |
|---|---|
| `@ConditionalOnClass(Foo.class)` | `Foo` is present on the classpath |
| `@ConditionalOnMissingBean(Bar.class)` | No `Bar` bean was declared by the user |
| `@ConditionalOnProperty("my.feature.enabled")` | Property is `true` (or the specified value) |
| `@ConditionalOnWebApplication` | Running as a web application |

The order of evaluation is: your `@Bean` declarations first, then auto-configuration. `@ConditionalOnMissingBean` is the guarantee that your bean wins when you declare one — the auto-configured fallback only appears if you didn't.

Full sequence at startup:
1. `@SpringBootApplication` triggers `@EnableAutoConfiguration`.
2. Spring Boot loads all auto-configuration class names from `AutoConfiguration.imports`.
3. For each, Spring evaluates the `@Conditional*` annotations.
4. Classes whose conditions pass have their `@Bean` methods called.
5. Resulting beans join the `ApplicationContext` alongside your own beans.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Auto-configuration decision flow: classpath check leads to conditional bean registration">
  <!-- Start node -->
  <ellipse cx="340" cy="30" rx="120" ry="22" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="35" fill="#1c2430" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot starts</text>

  <line x1="340" y1="52" x2="340" y2="72" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Load auto-config list -->
  <rect x="200" y="72" width="280" height="36" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="95" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Load AutoConfiguration.imports list</text>

  <line x1="340" y1="108" x2="340" y2="128" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Diamond: evaluate conditions -->
  <polygon points="340,128 460,170 340,212 220,170" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="166" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Conditions</text>
  <text x="340" y="182" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">pass?</text>

  <!-- Yes path -->
  <line x1="340" y1="212" x2="340" y2="232" stroke="#6db33f" stroke-width="2"/>
  <rect x="210" y="232" width="260" height="36" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="248" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Register @Beans in ApplicationContext</text>
  <text x="298" y="220" fill="#6db33f" font-size="11" font-family="sans-serif">YES</text>

  <!-- No path -->
  <line x1="460" y1="170" x2="560" y2="170" stroke="#8b949e" stroke-width="2"/>
  <rect x="560" y="154" width="100" height="32" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="610" y="175" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Skip</text>
  <text x="490" y="163" fill="#8b949e" font-size="11" font-family="sans-serif">NO</text>
</svg>

Each auto-configuration class is independently evaluated; only those whose `@Conditional*` annotations all pass contribute beans to the context.

## 5. Runnable example

```java
// File: AutoConfigDemo.java
// Simulates the @ConditionalOnClass + @ConditionalOnMissingBean pattern.
// Run: java AutoConfigDemo.java

import java.util.*;

public class AutoConfigDemo {

    // --- Simulated classpath check ---
    static final Set<String> CLASSPATH = Set.of(
        "org.postgresql.Driver",      // Postgres JDBC driver is present
        "com.zaxxer.hikari.HikariCP"  // HikariCP pool is present
    );

    interface DataSource { String describe(); }

    // What the USER might declare (takes priority)
    static Optional<DataSource> userDefinedDataSource() {
        // Return empty to simulate: user did NOT declare their own DataSource
        return Optional.empty();
    }

    // What AUTO-CONFIGURATION would register — only if conditions pass
    static Optional<DataSource> autoConfigureDataSource() {
        // @ConditionalOnClass — HikariCP on classpath?
        if (!CLASSPATH.contains("com.zaxxer.hikari.HikariCP")) {
            System.out.println("[AutoConfig] SKIP DataSource — HikariCP not on classpath");
            return Optional.empty();
        }
        // @ConditionalOnMissingBean — user didn't already declare one?
        if (userDefinedDataSource().isPresent()) {
            System.out.println("[AutoConfig] SKIP DataSource — user bean already present");
            return Optional.empty();
        }
        System.out.println("[AutoConfig] REGISTER HikariCP DataSource (conditions passed)");
        return Optional.of(() -> "HikariCP pool -> jdbc:postgresql://localhost/mydb");
    }

    public static void main(String[] args) {
        System.out.println("=== Classpath: " + CLASSPATH);
        System.out.println();

        DataSource ds = userDefinedDataSource()
            .or(AutoConfigDemo::autoConfigureDataSource)
            .orElseThrow(() -> new RuntimeException("No DataSource available"));

        System.out.println("Active DataSource: " + ds.describe());
    }
}
```

**How to run:** `java AutoConfigDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Classpath: [org.postgresql.Driver, com.zaxxer.hikari.HikariCP]

[AutoConfig] REGISTER HikariCP DataSource (conditions passed)
Active DataSource: HikariCP pool -> jdbc:postgresql://localhost/mydb
```

Try changing `userDefinedDataSource()` to return `Optional.of(() -> "Custom pool")` and re-run — the auto-config skips, and your bean wins.

## 6. Walkthrough

- **`CLASSPATH` set** — simulates `@ConditionalOnClass`. Spring Boot uses the actual JVM classpath at runtime; we fake it with a `Set<String>` for demonstration.
- **`userDefinedDataSource()`** — returns `Optional.empty()` to simulate "user hasn't declared a `DataSource` bean." In real Spring, `@ConditionalOnMissingBean` queries the `ApplicationContext` to check this.
- **`autoConfigureDataSource()`** — mirrors the logic inside `DataSourceAutoConfiguration`. Two guards: is HikariCP available (classpath check), and did the user already register a `DataSource` (missing-bean check)? Only if both pass does it register the auto-configured bean.
- **`Optional.or(...)`** — chains the two sources cleanly: user bean first, auto-configured bean as fallback. This is exactly Spring Boot's priority model — your beans override auto-configured ones.
- **The test**: change `userDefinedDataSource()` to return a `Optional.of(...)` and the auto-config skips. This is the "your bean wins" guarantee in action.

## 7. Gotchas & takeaways

> **Run with `--debug` to see the auto-configuration conditions report.** Every auto-configuration class that was evaluated gets logged with either "matched" or "did not match" and the reason. This is the first thing to check when something isn't wiring up.

> **`@ConditionalOnMissingBean` matches by type, not by name.** Declaring a `@Bean` of the exact same type as the auto-configured bean is enough to suppress it. You don't need to name the bean the same way.

> **Auto-config fires AFTER your beans.** Your `@Bean` methods in `@Configuration` classes always run before auto-configuration classes are processed. This is why `@ConditionalOnMissingBean` reliably detects your overrides.

- Auto-configuration = conditional bean registration triggered by classpath, properties, and missing beans.
- `@ConditionalOnClass` + `@ConditionalOnMissingBean` are the two most common guards.
- Your own `@Bean` declarations always beat auto-configured ones — you never need to "disable" auto-config to override a single bean.
- To exclude an entire auto-configuration class: `@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)`.
- `spring.autoconfigure.exclude` property achieves the same exclusion without code changes.
