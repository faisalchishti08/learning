---
card: microservices
gi: 229
slug: configurationproperties-type-safe-binding
title: "@ConfigurationProperties type-safe binding"
---

## 1. What it is

`@ConfigurationProperties` is a Spring Boot annotation that binds a whole group of related, prefixed configuration keys onto the fields of a plain Java object in one pass, converting string values to their declared field types automatically, rather than resolving each setting individually with `@Value`.

## 2. Why & when

Reading configuration one `@Value("${key}")` field at a time, as [Spring Boot's externalized configuration](0228-spring-boot-externalized-configuration-properties-yaml-env-a.md) allows, works fine for a handful of unrelated settings, but scales poorly once a feature has many related settings that logically belong together (a set of retry parameters, a group of connection-pool tunables): each one needs its own `@Value` annotation, its own type conversion is implicit and easy to get subtly wrong (a typo'd key silently resolves to `null` or the default, with no compile-time check), and there's no single object representing "this feature's configuration" that can be passed around, tested, or validated as a unit. `@ConfigurationProperties` solves this by binding an entire prefixed group into one strongly typed class, checked and converted in one place.

Use `@ConfigurationProperties` for any group of two or more related settings, especially ones benefiting from validation, nested structure (a list or a map of sub-configurations), or being passed around as a single, cohesive object. A single, standalone setting with no siblings is often simpler left as a plain `@Value`.

## 3. Core concept

`@ConfigurationProperties(prefix = "...")` scans the merged configuration `Environment` for every key starting with that prefix, and binds each suffix onto a matching field (converting kebab-case keys like `retry-count` to camelCase fields like `retryCount` automatically), including nested objects and collections when the field types support it.

```java
@ConfigurationProperties(prefix = "order.retry")
public class RetryProperties {
    private int maxAttempts = 3;       // binds "order.retry.max-attempts"
    private long backoffMs = 500;      // binds "order.retry.backoff-ms"
    private List<String> retryableStatusCodes = List.of("503", "504"); // binds a YAML LIST

    // getters/setters ...
}
// application.yaml:
// order:
//   retry:
//     max-attempts: 5
//     backoff-ms: 1000
//     retryable-status-codes: [429, 503, 504]
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A YAML block of prefixed keys under order.retry binds in one pass onto the fields of a single RetryProperties object, with each key converted to its matching field's type" >
  <rect x="20" y="20" width="260" height="110" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="40" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">application.yaml</text>
  <text x="35" y="60" fill="#8b949e" font-size="7" font-family="monospace">order.retry.max-attempts: 5</text>
  <text x="35" y="78" fill="#8b949e" font-size="7" font-family="monospace">order.retry.backoff-ms: 1000</text>
  <text x="35" y="96" fill="#8b949e" font-size="7" font-family="monospace">order.retry.retryable-status-codes:</text>
  <text x="45" y="112" fill="#8b949e" font-size="7" font-family="monospace">[429, 503, 504]</text>

  <rect x="380" y="35" width="240" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">RetryProperties</text>
  <text x="395" y="74" fill="#8b949e" font-size="7" font-family="monospace">int maxAttempts = 5</text>
  <text x="395" y="90" fill="#8b949e" font-size="7" font-family="monospace">long backoffMs = 1000</text>
  <text x="395" y="106" fill="#8b949e" font-size="7" font-family="monospace">List&lt;String&gt; retryableStatusCodes</text>

  <line x1="285" y1="75" x2="378" y2="75" stroke="#8b949e" marker-end="url(#arr229)"/>

  <defs>
    <marker id="arr229" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One prefixed YAML block binds, in one pass, onto one strongly typed object — including its list field.

## 5. Runnable example

Scenario: a retry feature that starts reading each of its related settings individually via separate `@Value` fields (verbose, error-prone, no single cohesive object), refactors to bind the same settings as one `@ConfigurationProperties` group, and finally adds validation constraints plus a nested list field, demonstrating type-safe binding of a whole structured configuration group in a single pass.

### Level 1 — Basic

```java
// File: SeparateValueFields.java (illustrative Spring Boot snippet) --
// EACH related retry setting needs its OWN @Value field; nothing groups
// them as one cohesive "retry configuration" object.
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class RetryHandler {
    @Value("${order.retry.max-attempts:3}")
    int maxAttempts; // ONE separate resolution

    @Value("${order.retry.backoff-ms:500}")
    long backoffMs; // ANOTHER separate resolution -- no shared object groups these together

    void describe() {
        System.out.println("maxAttempts=" + maxAttempts + ", backoffMs=" + backoffMs);
        System.out.println("Two related settings, resolved via TWO independent @Value fields.");
    }
}
```

**How to run:** as part of a Spring Boot app, inject `RetryHandler` and call `describe()`; conceptually equivalent to running `javac`/`java` on a plain class with the two fields hard-set to their defaults for local inspection.

### Level 2 — Intermediate

```java
// File: GroupedConfigurationProperties.java (illustrative Spring Boot snippet)
// -- the SAME two settings, now bound as ONE cohesive, prefixed group
// via @ConfigurationProperties -- a single object represents the whole
// "retry configuration" concept.
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "order.retry") // binds ALL "order.retry.*" keys onto THIS object
public class RetryProperties {
    private int maxAttempts = 3;  // binds "order.retry.max-attempts"
    private long backoffMs = 500; // binds "order.retry.backoff-ms"

    public int getMaxAttempts() { return maxAttempts; }
    public void setMaxAttempts(int maxAttempts) { this.maxAttempts = maxAttempts; }
    public long getBackoffMs() { return backoffMs; }
    public void setBackoffMs(long backoffMs) { this.backoffMs = backoffMs; }
}

// elsewhere:
// @Autowired RetryProperties retryProperties;
// retryProperties.getMaxAttempts(); retryProperties.getBackoffMs();
// -- ONE object, injectable, passable, and testable as a SINGLE cohesive unit.
```

**How to run:** as part of a Spring Boot app with `@EnableConfigurationProperties(RetryProperties.class)`: `./mvnw spring-boot:run`, with `application.yaml` defining `order.retry.max-attempts: 5` and `order.retry.backoff-ms: 1000`.

### Level 3 — Advanced

```java
// File: ValidatedNestedRetryProperties.java (illustrative Spring Boot snippet)
// -- adds VALIDATION and a NESTED LIST field, showing type-safe binding
// of a genuinely structured configuration group in one pass.
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.*;
import java.util.List;

@ConfigurationProperties(prefix = "order.retry")
@Validated
public class ValidatedRetryProperties {

    @Min(1) @Max(10)
    private int maxAttempts = 3; // VALIDATED range -- startup fails if this is out of bounds

    @Positive
    private long backoffMs = 500;

    @NotEmpty
    private List<String> retryableStatusCodes = List.of("503", "504"); // a NESTED LIST, bound from YAML

    public int getMaxAttempts() { return maxAttempts; }
    public void setMaxAttempts(int maxAttempts) { this.maxAttempts = maxAttempts; }
    public long getBackoffMs() { return backoffMs; }
    public void setBackoffMs(long backoffMs) { this.backoffMs = backoffMs; }
    public List<String> getRetryableStatusCodes() { return retryableStatusCodes; }
    public void setRetryableStatusCodes(List<String> retryableStatusCodes) { this.retryableStatusCodes = retryableStatusCodes; }
}

// application.yaml:
// order:
//   retry:
//     max-attempts: 15        # INVALID -- exceeds @Max(10), fails startup with a clear validation error
//     backoff-ms: 1000
//     retryable-status-codes: [429, 503, 504]
```

**How to run:** as part of a Spring Boot app with `@EnableConfigurationProperties(ValidatedRetryProperties.class)`: `./mvnw spring-boot:run`; with `max-attempts: 15` in `application.yaml` as shown, startup fails immediately with a `ConfigurationPropertiesBindException` naming the violated constraint; correcting it to a value between 1 and 10 lets the application start normally.

## 6. Walkthrough

1. **Level 1, the fragmentation problem** — `maxAttempts` and `backoffMs` are each resolved by their own independent `@Value` annotation; nothing in `RetryHandler` represents "the retry configuration" as a single, cohesive concept — a third related setting would mean a third, equally independent `@Value` field, with no structural relationship enforced between any of them.
2. **Level 2, one prefix, one object** — `@ConfigurationProperties(prefix = "order.retry")` tells Spring Boot to scan the merged `Environment` for every key beginning with `order.retry.` and bind each matching suffix (`max-attempts`, `backoff-ms`) onto `RetryProperties`'s corresponding field, converting the kebab-case YAML key to the camelCase Java field name and the string value to the field's declared type (`int`, `long`) automatically.
3. **Level 2, the object as a unit** — once registered, `RetryProperties` is injectable as a single bean; code depending on retry configuration now depends on one typed object (`RetryProperties`) rather than two independently resolved primitive fields, making it straightforward to pass, mock in a test, or extend with a new related field later.
4. **Level 3, validating the bound values** — `@Validated` on the class, combined with `@Min(1) @Max(10)` on `maxAttempts` and `@Positive` on `backoffMs`, tells Spring Boot to run Jakarta Bean Validation against the bound values immediately after binding, at application startup — this is validation happening once, structurally, rather than requiring every consumer of `RetryProperties` to separately re-check that `maxAttempts` is sane.
5. **Level 3, the nested list field** — `retryableStatusCodes` is a `List<String>`, and Spring Boot's relaxed binding supports YAML's list syntax (`[429, 503, 504]`) directly, converting it into a populated `List<String>` without any manual parsing code in `ValidatedRetryProperties` itself; `@NotEmpty` additionally ensures this list isn't accidentally left empty.
6. **Level 3, the fail-fast validation outcome** — with `max-attempts: 15` in the YAML (violating `@Max(10)`), Spring Boot's binding process throws a `ConfigurationPropertiesBindException` during application startup, before any request-handling code ever runs, naming the specific field and constraint that failed — this is the same fail-fast principle from [externalized configuration](0218-externalized-configuration-12-factor.md) applied specifically to a structured, validated configuration group: a misconfiguration is caught immediately and clearly, rather than silently accepted and only causing problems later when retry logic actually executes with an unreasonable `maxAttempts` value.

## 7. Gotchas & takeaways

> **Gotcha:** `@ConfigurationProperties` classes need either a registered bean definition (via `@EnableConfigurationProperties(RetryProperties.class)`, `@ConfigurationPropertiesScan`, or being annotated `@Component` alongside the `@ConfigurationProperties` annotation) — declaring the annotation alone on a plain class that Spring never registers as a bean silently does nothing, with no error indicating the binding never happened; verify the properties class actually appears as a bean if injected values seem to stay at their field defaults.

- `@ConfigurationProperties` binds a whole prefixed group of related configuration keys onto one strongly typed object in a single pass, rather than resolving each setting individually via separate `@Value` fields.
- It supports automatic type conversion (strings to `int`, `long`, `List`, nested objects) and relaxed binding between YAML's kebab-case keys and Java's camelCase field names.
- Combined with `@Validated` and Jakarta Bean Validation annotations, it enforces configuration correctness once, at startup, rather than requiring every consumer to independently re-validate the same values.
- It's the right choice for any group of two or more related settings, especially ones with nested structure or validation needs; a single standalone setting is often simpler left as a plain `@Value`.
- The class must actually be registered as a Spring bean for binding to occur at all — an annotated class that's never registered silently never gets populated, which is a common, hard-to-spot source of "my configuration isn't binding" confusion.
