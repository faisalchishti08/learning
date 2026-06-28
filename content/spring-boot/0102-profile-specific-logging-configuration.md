---
card: spring-boot
gi: 102
slug: profile-specific-logging-configuration
title: Profile-specific logging configuration
---

## 1. What it is

Spring Boot lets you set **different logging configuration per environment** without separate Logback XML files, using the same profile mechanisms you already know from application configuration:

**Via properties (simplest):** put `logging.level.*` and `logging.pattern.*` in profile-specific property files:

```properties
# application-dev.properties
logging.level.root=DEBUG
logging.level.com.example=TRACE

# application-prod.properties
logging.level.root=WARN
logging.structured.format.file=ecs
```

**Via `logback-spring.xml`** using `<springProfile>` blocks for configurations that properties cannot express (custom appenders, JSON encoders, async wrappers).

**Via profile-specific Logback XML files:** name separate files `logback-dev.xml`, `logback-prod.xml`, and then activate one by setting `logging.config=classpath:logback-${spring.profiles.active}.xml` — rarely needed and harder to maintain.

## 2. Why & when

Different environments have fundamentally different logging needs:

| Environment | Need |
|---|---|
| `dev` | Verbose debug output, human-readable, coloured console |
| `test` | Minimal noise, only `ERROR` or `WARN` so test output is readable |
| `staging` | Info-level, structured JSON to file so QA can search logs |
| `prod` | Warn-level, structured ECS JSON, errors-only file appender, no colour |

Duplicating a full Logback XML file per environment is error-prone — a change to one file must be applied to all others. The profile-specific properties approach keeps one `logback-spring.xml` (or no XML at all for simple cases) and delegates environment differences to `application-{profile}.properties`.

## 3. Core concept

Two complementary mechanisms, used together:

**1. Profile-specific property files** — simplest, covers level changes and pattern changes:
```
application.properties          → root=INFO, default pattern
application-dev.properties      → root=DEBUG, com.example=TRACE
application-prod.properties     → root=WARN, structured.format.file=ecs
```

**2. `<springProfile>` in `logback-spring.xml`** — covers structural changes (which appenders, async vs. sync):
```xml
<springProfile name="dev">
  <root level="DEBUG"><appender-ref ref="CONSOLE"/></root>
</springProfile>

<springProfile name="prod">
  <root level="WARN">
    <appender-ref ref="ASYNC_CONSOLE"/>
    <appender-ref ref="ERROR_FILE"/>
  </root>
</springProfile>
```

Combine both: use properties for level tuning (which needs no Logback XML), use `<springProfile>` for structural differences (which requires XML). Never duplicate the level configuration in both — pick one source of truth per concern.

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Profile-specific logging: dev profile loads DEBUG levels and console appender; prod loads WARN levels and structured file appender">
  <rect x="8" y="8" width="664" height="274" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile-Specific Logging Configuration</text>

  <!-- Dev column -->
  <text x="160" y="56" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile: dev</text>

  <rect x="30" y="66" width="260" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application-dev.properties</text>
  <text x="160" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.level.root=DEBUG</text>
  <text x="160" y="113" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.level.com.example=TRACE</text>

  <rect x="30" y="138" width="260" height="44" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="160" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">logback-spring.xml springProfile "!prod"</text>
  <text x="160" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">CONSOLE appender (human-readable)</text>

  <rect x="30" y="198" width="260" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="212" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Result: DEBUG everything, colour on</text>
  <text x="160" y="226" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">console only, no file output</text>

  <!-- Prod column -->
  <text x="520" y="56" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile: prod</text>

  <rect x="390" y="66" width="260" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="520" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application-prod.properties</text>
  <text x="520" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.level.root=WARN</text>
  <text x="520" y="113" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.structured.format.file=ecs</text>

  <rect x="390" y="138" width="260" height="44" rx="6" fill="#0d1117" stroke="#f0883e" stroke-width="1"/>
  <text x="520" y="155" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">logback-spring.xml springProfile "prod"</text>
  <text x="520" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">ASYNC_CONSOLE + ERROR_FILE appenders</text>

  <rect x="390" y="198" width="260" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="212" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Result: WARN root, JSON file, errors</text>
  <text x="520" y="226" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">to separate file, async console</text>

  <!-- Shared base -->
  <rect x="200" y="254" width="280" height="22" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="269" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application.properties: logging.level.root=INFO (base default)</text>
</svg>

Properties handle level differences; `<springProfile>` in XML handles structural differences.

## 5. Runnable example

```java
// ProfileLogging.java — run: java ProfileLogging.java  (JDK 17+)
// Simulates profile-specific logging configuration resolution and shows what each profile gets.

import java.util.*;

public class ProfileLogging {

    record LogConfig(String rootLevel, String exampleLevel, String appenderSetup,
                     String format, boolean colour) {}

    // Simulates application.properties base values
    static LogConfig base() {
        return new LogConfig("INFO", "INFO", "CONSOLE only", "text", true);
    }

    // Simulates application-dev.properties overlaying base
    static LogConfig devOverlay(LogConfig base) {
        return new LogConfig(
            "DEBUG",              // logging.level.root=DEBUG
            "TRACE",              // logging.level.com.example=TRACE
            "CONSOLE only",       // <springProfile name="!prod"> → CONSOLE
            "text",               // no structured format
            true                  // ANSI colour on
        );
    }

    // Simulates application-prod.properties overlaying base
    static LogConfig prodOverlay(LogConfig base) {
        return new LogConfig(
            "WARN",               // logging.level.root=WARN
            "WARN",               // no override → inherits root
            "ASYNC_CONSOLE + ERROR_FILE",  // <springProfile name="prod">
            "ecs",                // logging.structured.format.file=ecs
            false                 // spring.output.ansi.enabled=NEVER (or DETECT in CI)
        );
    }

    static LogConfig testOverlay(LogConfig base) {
        return new LogConfig(
            "WARN",               // only show problems in test output
            "INFO",               // com.example at INFO to see service activity
            "CONSOLE only",
            "text",
            false                 // no colour in CI
        );
    }

    static void print(String profile, LogConfig cfg) {
        System.out.printf("Profile: %-10s | root=%-5s | com.example=%-5s | %s | format=%-8s | colour=%s%n",
                profile, cfg.rootLevel(), cfg.exampleLevel(),
                cfg.appenderSetup(), cfg.format(), cfg.colour());
    }

    public static void main(String[] args) {
        LogConfig b = base();
        System.out.println("=== Effective logging configuration per profile ===");
        print("(none)",  b);
        print("dev",     devOverlay(b));
        print("prod",    prodOverlay(b));
        print("test",    testOverlay(b));

        System.out.println("\n=== Property file sources ===");
        System.out.println("application.properties:");
        System.out.println("  logging.level.root=INFO");
        System.out.println("  logging.pattern.console=${CONSOLE_LOG_PATTERN}");
        System.out.println("application-dev.properties:");
        System.out.println("  logging.level.root=DEBUG");
        System.out.println("  logging.level.com.example=TRACE");
        System.out.println("application-prod.properties:");
        System.out.println("  logging.level.root=WARN");
        System.out.println("  logging.structured.format.file=ecs");
        System.out.println("  spring.output.ansi.enabled=NEVER");
        System.out.println("application-test.properties:");
        System.out.println("  logging.level.root=WARN");
        System.out.println("  logging.level.com.example=INFO");

        System.out.println("\n=== logback-spring.xml <springProfile> for structural differences ===");
        System.out.println("""
  <springProfile name="!prod">
    <root level="${logging.level.root:-INFO}">
      <appender-ref ref="CONSOLE"/>
    </root>
  </springProfile>

  <springProfile name="prod">
    <root level="${logging.level.root:-WARN}">
      <appender-ref ref="ASYNC_CONSOLE"/>
      <appender-ref ref="ERROR_FILE"/>
    </root>
  </springProfile>
""");
    }
}
```

**How to run:** `java ProfileLogging.java`

## 6. Walkthrough

- `base()` represents `application.properties` — the shared defaults for all environments. `root=INFO` is a safe default: noisy enough for useful information, quiet enough not to overwhelm.
- `devOverlay` sets `root=DEBUG` and `com.example=TRACE`. In Spring Boot, `application-dev.properties` is loaded on top of `application.properties` when `dev` is active, so these two values replace the base. All other keys (`logging.pattern.console`) are unchanged.
- `prodOverlay` sets `root=WARN` — third-party library noise is silenced. `logging.structured.format.file=ecs` switches the file appender to JSON without touching the XML. `spring.output.ansi.enabled=NEVER` strips ANSI codes from console output in production (where logs go to a log aggregator, not a terminal).
- `testOverlay` uses `root=WARN` so tests don't emit Spring/Hibernate chatter, but keeps `com.example=INFO` so business-logic logging is visible when a test fails and you're reading the output. Use `@TestPropertySource(properties = "logging.level.root=WARN")` in Spring tests or a dedicated `application-test.properties`.
- The `<springProfile name="prod">` block adds `ASYNC_CONSOLE` and `ERROR_FILE` — structural appender changes that cannot be expressed through properties alone.

## 7. Gotchas & takeaways

> **Avoid setting `logging.level.*` in both `application.properties` and `logback-spring.xml` for the same logger.** The property file takes effect after the XML is parsed, potentially overriding the XML level — but only for levels set via the `LoggingSystem` abstraction. Structural changes (which appender a logger uses) come only from the XML. Separate concerns: levels in properties, structure in XML.

> **In a test that uses `@SpringBootTest`, the profile is set by `@ActiveProfiles("test")`.** A corresponding `application-test.properties` is automatically loaded. You do not need to set `logging.level` in each test class — put shared test logging config in this file.

- The simplest approach: no XML, all logging config in profile-specific properties. Works for 80% of applications.
- Add `logback-spring.xml` only when you need features properties cannot express: async wrappers, JSON encoders, socket appenders, or per-logger appender routing.
- `logging.level.root=WARN` in `application-test.properties` is the most impactful single change for readable test output.
- Profile-specific logging applies to `@SpringBootTest` integration tests too — make sure your `test` profile has the level configuration you want to see in CI output.
- Check `/actuator/loggers` endpoint to verify the effective configuration in a running instance matches your intended profile-specific settings.
