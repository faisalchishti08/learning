---
card: microservices
gi: 228
slug: spring-boot-externalized-configuration-properties-yaml-env-a
title: "Spring Boot externalized configuration (properties/YAML, env, args)"
---

## 1. What it is

Spring Boot's externalized configuration is its built-in mechanism for pulling settings from multiple sources — `application.properties`/`application.yaml` files, environment variables, command-line arguments, and more — into a single, unified property set that application code accesses uniformly, with a well-defined [precedence order](0226-configuration-precedence-overrides.md) among those sources baked directly into the framework.

## 2. Why & when

The general problem of [externalized configuration](0218-externalized-configuration-12-factor.md) and [configuration precedence](0226-configuration-precedence-overrides.md) is one every non-trivial application faces, and hand-rolling a solution — reading files, checking environment variables, merging them with a custom precedence rule — is exactly the kind of boilerplate a framework should absorb. Spring Boot does this: it automatically discovers `application.properties`/`application.yaml`, layers in environment variables and command-line arguments with a documented precedence, and exposes the merged result through a consistent API (`Environment`, `@Value`, `@ConfigurationProperties`), so application code never needs to know or care which specific source a given value ultimately came from.

Use Spring Boot's built-in externalized configuration for essentially every setting in a Spring Boot application — it's the framework's standard, idiomatic mechanism, and fighting it by implementing custom configuration loading duplicates functionality the framework already provides reliably.

## 3. Core concept

Spring Boot resolves each property by checking its configured sources in a documented precedence order — command-line arguments and environment variables generally outrank properties/YAML files, which outrank defaults — merging everything into a single `Environment` abstraction that the rest of the application reads from uniformly.

```java
// application.yaml
// order:
//   timeout-ms: 3000

@RestController
public class OrderController {
    @Value("${order.timeout-ms}") // Spring resolves this from WHICHEVER source wins, transparently
    int timeoutMs;

    @Autowired
    Environment environment; // the LOWER-LEVEL API, for programmatic access to the SAME merged properties

    @GetMapping("/config-check")
    String checkConfig() {
        return "timeoutMs=" + timeoutMs + ", raw=" + environment.getProperty("order.timeout-ms");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Command-line arguments, environment variables, and application.yaml all feed into Spring Boot's merged Environment abstraction, following a documented precedence order, and application code reads the single merged result via @Value or Environment" >
  <rect x="20" y="15" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="37" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Command-line args</text>

  <rect x="20" y="60" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Environment vars</text>

  <rect x="20" y="105" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="127" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">application.yaml</text>

  <rect x="255" y="55" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="330" y="93" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">merged, precedence-aware</text>

  <rect x="470" y="55" width="150" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Value / @ConfigurationProperties</text>
  <text x="545" y="93" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">application code</text>

  <line x1="170" y1="32" x2="253" y2="65" stroke="#8b949e" marker-end="url(#arr228)"/>
  <line x1="170" y1="77" x2="253" y2="80" stroke="#8b949e" marker-end="url(#arr228)"/>
  <line x1="170" y1="122" x2="253" y2="95" stroke="#8b949e" marker-end="url(#arr228)"/>
  <line x1="405" y1="82" x2="468" y2="82" stroke="#8b949e" marker-end="url(#arr228)"/>

  <defs>
    <marker id="arr228" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every source feeds one merged Environment; application code reads from that single, precedence-resolved result.

## 5. Runnable example

Scenario: a plain Java program that starts hand-rolling the exact multi-source resolution logic Spring Boot automates (to make the mechanism explicit), refactors to show the equivalent Spring Boot annotated code doing the same job declaratively, and finally demonstrates `@ConfigurationProperties`-style type-safe binding of a whole group of related settings, rather than reading individual keys one by one.

### Level 1 — Basic

```java
// File: HandRolledPrecedenceResolution.java -- manually implements the
// SAME kind of source-merging Spring Boot's Environment does internally,
// to make the underlying mechanism explicit before seeing it declaratively.
import java.util.*;

public class HandRolledPrecedenceResolution {
    static String resolve(String key, Map<String, String> envVars, Map<String, String> yamlProps, String defaultValue) {
        if (envVars.containsKey(key)) return envVars.get(key); // env vars OUTRANK yaml, in Spring Boot's default order
        if (yamlProps.containsKey(key)) return yamlProps.get(key);
        return defaultValue;
    }

    public static void main(String[] args) {
        Map<String, String> envVars = Map.of(); // simulating: ORDER_TIMEOUT_MS not set
        Map<String, String> yamlProps = Map.of("order.timeout-ms", "3000"); // from application.yaml

        String timeoutMs = resolve("order.timeout-ms", envVars, yamlProps, "1000");
        System.out.println("Resolved order.timeout-ms = " + timeoutMs + " (from application.yaml, since env var wasn't set)");
        System.out.println("Spring Boot's @Value(\"${order.timeout-ms}\") does exactly this merging, automatically.");
    }
}
```

**How to run:** `javac HandRolledPrecedenceResolution.java && java HandRolledPrecedenceResolution` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SpringBootStyleValueInjection.java (illustrative Spring Boot snippet)
// -- the SAME resolution, expressed declaratively via @Value; Spring
// Boot performs the source-merging internally, so this class contains
// NO manual precedence logic at all.
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@RestController
public class OrderConfigController {

    @Value("${order.timeout-ms:1000}") // "${key:default}" -- Spring Boot resolves key from ALL sources, or uses 1000
    int timeoutMs;

    @GetMapping("/order-config")
    public String showConfig() {
        return "order.timeout-ms resolved to: " + timeoutMs;
        // application.yaml:
        //   order:
        //     timeout-ms: 3000
        // Running with: java -jar app.jar --order.timeout-ms=7000
        // -- the COMMAND-LINE value (7000) wins over application.yaml's 3000, per Spring Boot's documented precedence.
    }
}
```

**How to run:** as part of a Spring Boot app: `./mvnw spring-boot:run` then `curl localhost:8080/order-config`; add `--order.timeout-ms=7000` to the run command to see the command-line override take effect.

### Level 3 — Advanced

```java
// File: TypeSafeConfigurationPropertiesGroup.java (illustrative Spring Boot snippet)
// -- binds a WHOLE group of related settings into one type-safe, validated
// object via @ConfigurationProperties, rather than one @Value per key.
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.*;

@ConfigurationProperties(prefix = "order") // binds ALL "order.*" keys into this ONE object
@Validated
public class OrderProperties {

    @NotNull
    @Positive
    private Integer timeoutMs = 1000; // default, used if "order.timeout-ms" is absent from every source

    @NotNull
    private Integer retryCount = 3; // "order.retry-count"

    // getters/setters omitted for brevity

    // application.yaml:
    //   order:
    //     timeout-ms: 3000
    //     retry-count: 5
    // -- BOTH fields bound in ONE pass, type-checked and validated (@Positive rejects a negative timeout at startup)
}

// elsewhere, injected as a normal bean:
// @Autowired OrderProperties orderProperties;
// orderProperties.getTimeoutMs(); orderProperties.getRetryCount();
```

**How to run:** as part of a Spring Boot app with `@EnableConfigurationProperties(OrderProperties.class)` (or component-scanned via `@ConfigurationPropertiesScan`): `./mvnw spring-boot:run`; supplying `order.timeout-ms=-5` in `application.yaml` causes startup to fail immediately due to the `@Positive` validation constraint.

## 6. Walkthrough

1. **Level 1, making the mechanism explicit** — `resolve` checks `envVars` before `yamlProps`, mirroring Spring Boot's own documented precedence (environment variables generally outrank properties/YAML files); with `envVars` empty for this key, resolution falls through to `yamlProps`, returning `"3000"` — this is the exact kind of source-merging logic Spring Boot performs internally so application code never has to write it.
2. **Level 2, the declarative equivalent** — `@Value("${order.timeout-ms:1000}")` tells Spring Boot to resolve `order.timeout-ms` from its full, precedence-ordered set of sources, falling back to the literal default `1000` only if no source defines it at all; `OrderConfigController` contains no manual merging logic whatsoever — Spring Boot performs it before this field is ever populated.
3. **Level 2, precedence in action** — the comment shows `application.yaml` defining `timeout-ms: 3000`, but running the application with `--order.timeout-ms=7000` on the command line causes `timeoutMs` to resolve to `7000` instead, demonstrating Spring Boot's real precedence order (command-line arguments outranking properties/YAML files) exactly as Level 1's hand-rolled version modeled the env-vars-outrank-YAML case.
4. **Level 3, grouping related settings** — `@ConfigurationProperties(prefix = "order")` tells Spring Boot to bind every configuration key starting with `order.` onto matching fields of `OrderProperties` in one pass, rather than requiring a separate `@Value` annotation (and a separate resolution) for each individual key.
5. **Level 3, type safety and validation together** — `timeoutMs` and `retryCount` are declared as `Integer` fields, so Spring Boot converts the underlying string configuration values to the correct type automatically, and `@Positive`/`@NotNull` are checked as part of Spring's validation machinery at startup — a negative `order.timeout-ms` value causes the application to fail to start with a clear validation error, rather than allowing an invalid value to silently reach application logic.
6. **Level 3, consuming the bound group** — once `OrderProperties` is registered as a bean, other components inject it directly (`@Autowired OrderProperties orderProperties`) and call typed getters (`orderProperties.getTimeoutMs()`), reading a fully resolved, validated, type-safe view of the `order.*` configuration group without ever touching raw property strings or individual `@Value` lookups.

## 7. Gotchas & takeaways

> **Gotcha:** relaxed binding means `order.timeout-ms` in YAML, `ORDER_TIMEOUT_MS` as an environment variable, and `order.timeoutMs` in a properties file all bind to the same `timeoutMs` field — convenient, but it means a typo in *any* of these naming conventions silently fails to bind rather than throwing an error at the point of the typo; verify actual resolved values (e.g., via the `/actuator/env` endpoint) when a bound property doesn't seem to be taking effect, rather than assuming the naming convention was followed correctly.

- Spring Boot's externalized configuration automatically merges multiple sources (properties/YAML files, environment variables, command-line arguments) into one `Environment`, following a documented precedence order, so application code never manually merges sources itself.
- `@Value("${key:default}")` resolves a single property from the merged, precedence-ordered result, with an optional literal fallback.
- `@ConfigurationProperties`, covered in more depth [next](0229-configurationproperties-type-safe-binding.md), binds a whole prefixed group of related settings into one type-safe, validated object in a single pass, rather than one `@Value` per key.
- This built-in mechanism is Spring Boot's standard, idiomatic way to handle configuration — implementing custom source-merging logic duplicates functionality the framework already provides reliably.
- Spring Boot's "relaxed binding" tolerates several naming conventions for the same logical property, which is convenient but can mask typos — verify actual resolved values when a property doesn't seem to be taking effect as expected.
