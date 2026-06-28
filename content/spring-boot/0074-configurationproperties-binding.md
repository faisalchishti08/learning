---
card: spring-boot
gi: 74
slug: configurationproperties-binding
title: "@ConfigurationProperties (binding)"
---

## 1. What it is

`@ConfigurationProperties` is Spring Boot's mechanism for mapping a whole namespace of properties — everything under a given prefix — onto a single Java class. Instead of injecting properties one at a time with `@Value("${app.timeout}")`, you annotate a class with `@ConfigurationProperties(prefix = "app")`, add fields with matching names, and Spring Boot fills in every field automatically.

The result is a **strongly-typed configuration object** that lives in the Spring context like any other bean. You can inject it, validate it, test it, and document it in one place rather than scattering `@Value` annotations across dozens of classes.

In one sentence: **`@ConfigurationProperties` binds an entire prefix of properties onto a Java class, giving you type-safe, structured, and validatable configuration.**

## 2. Why & when

`@Value` works fine for a single property but becomes unwieldy fast:

- You can't group related properties logically.
- Refactoring a property key means hunting through every `@Value` annotation in the codebase.
- Type conversion is manual — you parse strings yourself.
- There's no built-in validation; a misspelled key silently injects `null`.

`@ConfigurationProperties` solves all of these:

- **Grouping** — all `app.*` properties live in one class; the structure mirrors the YAML tree.
- **Type safety** — Spring auto-converts strings to `int`, `Duration`, `List<String>`, `Map<String, Integer>`, etc.
- **Validation** — add JSR-303 annotations (`@NotNull`, `@Min`) and Spring validates at startup; bad config fails fast.
- **IDE support** — Spring Boot's annotation processor generates `spring-configuration-metadata.json`, which gives you autocompletion and documentation inside IntelliJ and VS Code.
- **Testability** — you can construct and populate the class in a unit test without starting a full Spring context.

Reach for `@ConfigurationProperties` whenever you have **more than two or three related properties**, whenever you want validation, or whenever you're building a library or auto-configuration that others will configure.

## 3. Core concept

Spring Boot uses a **`ConfigurationPropertiesBindingPostProcessor`** to process every `@ConfigurationProperties` bean during context refresh. The processor:

1. Reads the `prefix` from the annotation.
2. Scans the Spring `Environment` (which aggregates all property sources: `application.yml`, env vars, command-line args, etc.) for keys that start with that prefix.
3. Strips the prefix, canonicalises the remaining segment (lowercase, kebab-case), and finds the matching field or setter on the class.
4. Converts the raw string value to the field's Java type using Spring's `ConversionService`.
5. If `@Validated` is present, runs JSR-303 validation and throws a `BindException` on failure.

The binding is **relaxed** (see tutorial 77 for the full rules), so `app.myTimeout`, `app.my-timeout`, `app.my_timeout`, and `APP_MY_TIMEOUT` all bind to a field named `myTimeout`.

An important subtlety: `@ConfigurationProperties` does not scan for properties with `@Value`-style `${...}` interpolation expressions — it uses a structural binding model. The class describes its expected shape; Spring fulfils it.

## 4. Diagram

<svg viewBox="0 0 660 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@ConfigurationProperties binding pipeline from Environment to Java object fields">

  <!-- property sources column -->
  <rect x="20" y="20" width="150" height="270" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Environment</text>
  <text x="95" y="66" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(property sources)</text>
  <rect x="35" y="76" width="120" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95" y="93" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">application.yml</text>
  <rect x="35" y="110" width="120" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95" y="127" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">env vars</text>
  <rect x="35" y="144" width="120" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95" y="161" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">cmd-line args</text>
  <rect x="35" y="178" width="120" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95" y="195" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">system props</text>

  <!-- arrow to binder -->
  <line x1="170" y1="155" x2="245" y2="155" stroke="#6db33f" stroke-width="2" marker-end="url(#b1)"/>
  <text x="207" y="147" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">prefix filter</text>

  <!-- binder box -->
  <rect x="245" y="110" width="155" height="90" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="322" y="135" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">BindingPostProcessor</text>
  <text x="322" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">relaxed key lookup</text>
  <text x="322" y="172" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">type conversion</text>
  <text x="322" y="189" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">JSR-303 validation</text>

  <!-- arrow to class -->
  <line x1="400" y1="155" x2="475" y2="155" stroke="#79c0ff" stroke-width="2" marker-end="url(#b2)"/>
  <text x="437" y="147" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">sets fields</text>

  <!-- Java class box -->
  <rect x="475" y="80" width="165" height="150" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="557" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">AppProperties</text>
  <text x="557" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationProperties</text>
  <text x="557" y="140" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">(prefix = "app")</text>
  <line x1="490" y1="150" x2="630" y2="150" stroke="#8b949e" stroke-width="0.8"/>
  <text x="557" y="168" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">String name</text>
  <text x="557" y="184" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">int timeout</text>
  <text x="557" y="200" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">List&lt;String&gt; tags</text>
  <text x="557" y="218" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Duration ttl</text>

  <defs>
    <marker id="b1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The `BindingPostProcessor` filters the `Environment` to keys under `"app"`, converts each value to the field's type, then populates the `AppProperties` bean — all before the first `@Service` or `@Controller` receives that bean.

## 5. Runnable example

```java
// src/main/resources/application.yml
// (add this to your resources — not Java code)
//
// app:
//   name: my-service
//   timeout: 30
//   tags:
//     - web
//     - api
//   ttl: 5m

// src/main/java/com/example/config/AppProperties.java
package com.example.config;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.convert.DurationUnit;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Component
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    @NotBlank
    private String name;

    @Min(1)
    private int timeout;

    private List<String> tags;

    @DurationUnit(ChronoUnit.MINUTES)
    private Duration ttl;

    public String getName()               { return name; }
    public void setName(String name)      { this.name = name; }
    public int getTimeout()               { return timeout; }
    public void setTimeout(int timeout)   { this.timeout = timeout; }
    public List<String> getTags()             { return tags; }
    public void setTags(List<String> tags)    { this.tags = tags; }
    public Duration getTtl()                  { return ttl; }
    public void setTtl(Duration ttl)          { this.ttl = ttl; }
}

// src/main/java/com/example/ConfigPropsApp.java
package com.example;

import com.example.config.AppProperties;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class ConfigPropsApp {

    public static void main(String[] args) {
        SpringApplication.run(ConfigPropsApp.class, args);
    }

    @Bean
    CommandLineRunner run(AppProperties props) {
        return args -> {
            System.out.println("name    = " + props.getName());
            System.out.println("timeout = " + props.getTimeout() + "s");
            System.out.println("tags    = " + props.getTags());
            System.out.println("ttl     = " + props.getTtl());
        };
    }
}
```

**How to run:** create `src/main/resources/application.yml` with the YAML block shown in the comment, then run `./mvnw spring-boot:run`. Expected output:

```
name    = my-service
timeout = 30s
tags    = [web, api]
ttl     = PT5M
```

To see validation in action, remove the `name` value from `application.yml` and restart — Spring Boot will refuse to start and print the constraint violation message.

## 6. Walkthrough

- **`@ConfigurationProperties(prefix = "app")`** — registers this class as a properties binding target. Spring will read every key starting with `app.` from the `Environment`.
- **`@Component`** — makes the class a Spring bean so it can be injected into other beans. An alternative to `@Component` is `@EnableConfigurationProperties`; see tutorial 76.
- **`@Validated`** — activates JSR-303 validation after binding completes. Without this, `@NotBlank` and `@Min` are inert.
- **`@NotBlank private String name`** — if `app.name` is absent or blank, binding fails with a `BindValidationException` before the application finishes starting.
- **`@Min(1) private int timeout`** — Spring converts the string `"30"` to the `int` `30` automatically. The conversion is handled by `ConversionService`.
- **`List<String> tags`** — Spring maps the YAML sequence into a `List<String>` without any extra configuration.
- **`@DurationUnit(ChronoUnit.MINUTES) private Duration ttl`** — Spring Boot's `DurationConverter` parses `"5m"` into `Duration.ofMinutes(5)`. Without the annotation, the string must follow ISO-8601 (e.g., `PT5M`).
- **`CommandLineRunner`** — injects `AppProperties` just like any other bean and prints the bound values.

## 7. Gotchas & takeaways

> If you add a new field to a `@ConfigurationProperties` class but forget to add a setter, Spring **silently skips it** — the field stays at its default value (`null` for objects, `0` for primitives) with no warning. Always double-check that every field you expect to be bound has a working setter (or switch to constructor binding, covered in tutorial 75).

> Deleting a property key from `application.yml` without removing the `@NotNull` / `@NotBlank` constraint on the corresponding field will crash startup. This is usually what you want — but it can be surprising when rotating config in a running cluster.

- `@ConfigurationProperties` binds an entire namespace; `@Value` binds a single key. Mix them only when necessary.
- Spring Boot generates `spring-configuration-metadata.json` automatically when you add `spring-boot-configuration-processor` as an annotation processor dependency — adds IDE autocompletion for free.
- The class does not need to be a Spring component itself; you can register it via `@EnableConfigurationProperties(AppProperties.class)` on a `@Configuration` class (cleaner in library code).
- Nested objects are supported: a field of type `DatabaseConfig` whose class has its own getters/setters binds to `app.database.*` properties automatically.
- `@ConfigurationProperties` classes are ordinary POJOs — you can unit-test them by constructing an instance, setting fields manually, and asserting on them without any Spring context.
