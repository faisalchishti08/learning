---
card: spring-boot
gi: 81
slug: configurationproperties-vs-value
title: "@ConfigurationProperties vs @Value"
---

## 1. What it is

Spring Boot provides two mechanisms for injecting externalized configuration values into your beans:

- **`@Value("${key}")`** — a Spring Framework annotation that injects a single property value at the point of injection (field, constructor parameter, or method parameter). The expression inside the annotation is an interpolation expression that Spring's `PropertySourcesPlaceholderConfigurer` resolves against the current `Environment`.
- **`@ConfigurationProperties(prefix = "…")`** — a Spring Boot annotation that binds a whole group of properties, identified by a shared prefix, to a typed Java object (POJO or Java record). The binding is done by name matching between property keys and field/setter names.

They are not mutually exclusive, but they serve different purposes and have significantly different capabilities. Choosing the right one matters for readability, safety, and maintainability.

## 2. Why & when

`@Value` is the quickest way to grab a single config string. It works fine — but it scales poorly. As soon as you have three or four related properties you'll be writing `@Value("${db.url}")`, `@Value("${db.username}")`, `@Value("${db.password}")` all over a class, with no structure, no validation, and no IDE support.

`@ConfigurationProperties` was designed for exactly that scenario. It keeps all related configuration in one place, gives you type safety, supports JSR-303 validation, relaxed binding, metadata generation, and works cleanly with records since Spring Boot 2.6.

**Use `@Value` when:**
- You need exactly one or two simple, independent values.
- You're in a context where `@ConfigurationProperties` can't be used easily (e.g. a `@Bean` factory method parameter with no dedicated properties class).
- You need SpEL expressions (e.g. `@Value("#{systemProperties['java.home']}")`).

**Use `@ConfigurationProperties` when:**
- You have a group of related properties that belong together logically.
- You want type conversion, relaxed binding, or JSR-303 validation.
- You want IDE auto-complete via metadata generation.
- You're building a library or starter and exposing a documented configuration namespace.

## 3. Core concept

| Feature | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| Scope | Single value per annotation | All properties under a prefix |
| Binding style | Exact key match only | Relaxed binding (camelCase, kebab-case, SCREAMING_SNAKE) |
| Type conversion | Limited (Spring's basic converters) | Full `ConversionService` incl. `Duration`, `DataSize` |
| Validation (`@Validated`) | Not supported | Supported via JSR-303 / Jakarta Validation |
| Default values | In the expression: `${key:default}` | In the Java field initialiser |
| IDE auto-complete | None | Via `spring-boot-configuration-processor` |
| Metadata generation | No | Yes (automatically from annotation processor) |
| Immutable / record-style | No | Yes (Java records, `@ConstructorBinding`) |
| SpEL expressions | Yes (`#{…}`) | No |
| Works without Spring Boot | Yes (Spring Framework) | No (Spring Boot only) |
| Nested objects | No | Yes |

**Relaxed binding** is one of the most practical advantages of `@ConfigurationProperties`. A field named `maxRetryCount` is automatically matched to all of: `max-retry-count` (kebab-case in `.properties`), `maxRetryCount` (camelCase in YAML), `MAX_RETRY_COUNT` (environment variable), and `MAX-RETRY-COUNT`. `@Value` requires the exact key name.

## 4. Diagram

<svg viewBox="0 0 700 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison: @Value on the left for single key injection, @ConfigurationProperties on the right for grouped prefix binding">
  <rect x="10" y="10" width="680" height="320" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="350" y="38" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Value  vs  @ConfigurationProperties</text>

  <!-- Divider -->
  <line x1="350" y1="50" x2="350" y2="310" stroke="#30363d" stroke-width="1" stroke-dasharray="4 3"/>

  <!-- LEFT: @Value -->
  <text x="185" y="68" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">@Value</text>

  <rect x="30" y="80" width="290" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="175" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="175" y="118" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">app.timeout=30000</text>

  <line x1="175" y1="136" x2="175" y2="158" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4 3"/>

  <rect x="30" y="160" width="290" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="175" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Value("${app.timeout}")</text>
  <text x="175" y="198" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">private long timeout;</text>
  <text x="175" y="225" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">✗ No relaxed binding</text>
  <text x="175" y="241" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">✗ No Duration auto-convert</text>

  <rect x="50" y="262" width="250" height="34" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="175" y="282" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Fine for 1-2 values; brittle at scale</text>

  <!-- RIGHT: @ConfigurationProperties -->
  <text x="523" y="68" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">@ConfigurationProperties</text>

  <rect x="368" y="80" width="300" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="518" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="518" y="116" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.timeout=30s</text>
  <text x="518" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.max-retry-count=3</text>
  <text x="518" y="144" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.admin-email=ops@co.io</text>

  <line x1="518" y1="162" x2="518" y2="178" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4 3"/>

  <rect x="368" y="180" width="300" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="518" y="198" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationProperties("app")</text>
  <text x="518" y="214" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Duration timeout;        // "30s"→PT30S</text>
  <text x="518" y="228" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">int maxRetryCount;       // relaxed</text>
  <text x="518" y="242" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">String adminEmail;       // @Email ok</text>

  <rect x="388" y="262" width="260" height="34" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="518" y="282" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Structured, validated, IDE-complete</text>
</svg>

`@Value` is a direct, surgical injection; `@ConfigurationProperties` treats configuration as a typed domain object with its own structure and constraints.

## 5. Runnable example

```java
// src/main/java/com/example/demo/AppProperties.java
package com.example.demo;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;

/**
 * Demonstrates @ConfigurationProperties: groups, type conversion,
 * relaxed binding, and validation in one place.
 */
@Component
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    @NotBlank
    private String name;

    /** Property key "app.connect-timeout" → matches this camelCase field (relaxed binding). */
    private Duration connectTimeout = Duration.ofSeconds(5);

    @Min(1)
    private int maxRetryCount = 3;

    @Email
    private String adminEmail;

    public String getName()                     { return name; }
    public void setName(String n)               { this.name = n; }
    public Duration getConnectTimeout()         { return connectTimeout; }
    public void setConnectTimeout(Duration d)   { this.connectTimeout = d; }
    public int getMaxRetryCount()               { return maxRetryCount; }
    public void setMaxRetryCount(int r)         { this.maxRetryCount = r; }
    public String getAdminEmail()               { return adminEmail; }
    public void setAdminEmail(String e)         { this.adminEmail = e; }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/ReportService.java
package com.example.demo;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Demonstrates @Value for a single, standalone property
 * that doesn't belong to the "app" group.
 */
@Service
public class ReportService {

    /**
     * Using @Value with an interpolation expression and a default.
     * The ":pdf" after the colon is the fallback if "report.format" is absent.
     */
    private final String reportFormat;

    public ReportService(@Value("${report.format:pdf}") String reportFormat) {
        this.reportFormat = reportFormat;
    }

    public String getReportFormat() { return reportFormat; }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/DemoApplication.java
package com.example.demo;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {

    @Autowired AppProperties app;
    @Autowired ReportService report;

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("App name      : " + app.getName());
        System.out.println("Connect timeout: " + app.getConnectTimeout());
        System.out.println("Max retries   : " + app.getMaxRetryCount());
        System.out.println("Admin email   : " + app.getAdminEmail());
        System.out.println("Report format : " + report.getReportFormat());
    }
}
```

`application.properties`:

```properties
# @ConfigurationProperties group — relaxed binding, type conversion
app.name=my-service
app.connect-timeout=10s
app.max-retry-count=5
app.admin-email=admin@example.com

# Standalone value consumed by @Value
report.format=xlsx
```

**How to run:** `./mvnw spring-boot:run`. All values are printed. Remove `report.format` from the file — the app still starts because the `@Value` expression provides a default of `"pdf"`.

## 6. Walkthrough

- **`AppProperties`** uses `@ConfigurationProperties(prefix = "app")`. Every property whose key starts with `app.` is a candidate for binding into this class.
- **Relaxed binding in action** — the property key `app.connect-timeout` (kebab-case) maps to the Java field `connectTimeout` (camelCase) automatically. With `@Value` you'd have to write `@Value("${app.connect-timeout}")` — the exact key, no flexibility.
- **`Duration connectTimeout`** — the string `"10s"` from the properties file is automatically converted to `Duration.ofSeconds(10)`. There is no equivalent automatic conversion in `@Value`; you'd receive a raw `String` and have to call `Duration.parse` yourself.
- **`@Validated` + `@Email` + `@Min`** — because `@Validated` is present, Spring Boot validates all constraints after binding. An invalid `adminEmail` or a `maxRetryCount` less than 1 causes the app to exit before the first request is served.
- **`ReportService` with `@Value`** — the constructor parameter annotation `@Value("${report.format:pdf}")` injects a single standalone value. The `:pdf` suffix inside the interpolation expression is the default value — Spring Boot uses it when `report.format` is absent. This is appropriate here because `report.format` is a lone, unrelated property with no siblings.
- **Default values** — in `AppProperties`, `connectTimeout` is initialised to `Duration.ofSeconds(5)` in the field declaration. If `app.connect-timeout` is absent from all property sources the Java default is used. In `@Value` the default lives inside the expression string, which is less visible and harder to test.

## 7. Gotchas & takeaways

> **`@Value` does not support relaxed binding.** The key in the expression must match the property source key character-for-character. If your `.properties` file uses `my-service.max-connections` and your `@Value` says `${my.service.maxConnections}`, you'll get a `BeanCreationException`. Use `@ConfigurationProperties` instead.

> **`@Value` injects `null` silently when a property is missing — unless you add a default or use `@NotNull`.** The failure surfaces later, often as a `NullPointerException` inside a business method. `@ConfigurationProperties` with `@Validated` catches missing required properties at startup.

- `@Value` cannot inject `Duration` or `DataSize` — it injects the raw `String` value. You must convert manually.
- `@ConfigurationProperties` fields can have Java-level defaults; `@Value` defaults live inside the annotation string.
- IDE auto-complete (in IntelliJ, VS Code with the Spring extension, etc.) works for `@ConfigurationProperties` when `spring-boot-configuration-processor` is on the classpath. `@Value` keys are opaque strings — no auto-complete.
- For library / starter authors, `@ConfigurationProperties` is essentially mandatory: it enables metadata generation and gives library users discoverable, documented properties.
- Both mechanisms are ultimately backed by Spring's `Environment` and `PropertySources`, so they read from the same sources (files, environment variables, system properties) in the same precedence order.
