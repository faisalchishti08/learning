---
card: spring-boot
gi: 98
slug: logback-extensions-springprofile-springproperty
title: "Logback extensions (springProfile, springProperty)"
---

## 1. What it is

Spring Boot adds two custom XML elements to Logback's configuration language, available only in `logback-spring.xml`:

1. **`<springProfile name="…">`** — conditionally includes a block of Logback configuration based on which Spring profiles are active. Acts like `#if profile_active` inside the XML.

2. **`<springProperty scope="…" name="…" source="…" defaultValue="…"/>`** — reads a value from the Spring `Environment` (including all property sources: `application.properties`, environment variables, etc.) and exposes it as a Logback property. Bridges Spring's configuration into Logback's world.

Both are loaded by `LogbackLoggingSystem` during context preparation — after the Spring `Environment` is ready but before the application context is refreshed. This is why `logback.xml` (loaded by Logback directly, before Spring) cannot use them.

## 2. Why & when

The challenge with Logback XML is that it's a static configuration loaded early. Without Spring Boot's extensions, you can't:
- Use a production log level only in production — you'd need separate Logback XML files.
- Read `logging.file.name` from `application.properties` into a Logback `<file>` element.
- Use Spring profiles to toggle between a human-readable pattern and a JSON encoder.

`<springProfile>` solves the first and third problems. `<springProperty>` solves the second. Together they make one `logback-spring.xml` file serve all environments, pulling environment-specific values from the Spring `Environment` rather than hardcoding them.

## 3. Core concept

**`<springProfile>`** accepts a profile expression identical to `@Profile`:
- `name="prod"` — active when `prod` is active.
- `name="!prod"` — active when `prod` is NOT active.
- `name="prod | staging"` — active when either is active.
- `name="prod &amp; cloud"` — active when both are active (XML entity for `&`).

`<springProfile>` can wrap any Logback element: `<appender>`, `<appender-ref>`, `<root>`, `<logger>`, `<include>`, etc.

**`<springProperty>`** maps a Spring Environment key to a Logback property:
```xml
<springProperty scope="context" name="LOG_DIR"
                source="logging.file.path"
                defaultValue="/var/log/app"/>
```

| Attribute | Meaning |
|---|---|
| `scope` | `context` (shared), `local` (this config only), or `system` (JVM system property) |
| `name` | The Logback property name (`${LOG_DIR}`) |
| `source` | The Spring Environment key (`logging.file.path`) |
| `defaultValue` | Used if the key is absent from the Environment |

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="springProfile conditionally activates XML blocks; springProperty reads from Spring Environment into Logback">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot Logback Extensions</text>

  <!-- springProperty -->
  <rect x="30" y="52" width="290" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="175" y="70" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">&lt;springProperty&gt;</text>
  <text x="50" y="90" fill="#e6edf3" font-size="9" font-family="monospace">&lt;springProperty name="LOG_DIR"</text>
  <text x="50" y="104" fill="#e6edf3" font-size="9" font-family="monospace">  source="logging.file.path"</text>
  <text x="50" y="118" fill="#e6edf3" font-size="9" font-family="monospace">  defaultValue="/var/log"/&gt;</text>
  <text x="175" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ ${LOG_DIR} usable in appenders</text>

  <!-- Arrow from Spring Environment -->
  <rect x="360" y="70" width="270" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="86" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Spring Environment</text>
  <text x="495" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application.properties + env vars + etc.</text>

  <defs><marker id="ea" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <line x1="358" y1="90" x2="323" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>
  <text x="340" y="84" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">reads</text>

  <!-- springProfile -->
  <rect x="30" y="170" width="600" height="80" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="340" y="188" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">&lt;springProfile&gt;</text>

  <rect x="50" y="196" width="260" height="44" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="180" y="213" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;springProfile name="!prod"&gt;</text>
  <text x="180" y="229" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">  &lt;root level="DEBUG"/&gt;</text>
  <text x="180" y="243" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;/springProfile&gt;</text>

  <rect x="370" y="196" width="240" height="44" rx="5" fill="#0d1117" stroke="#f0883e" stroke-width="1"/>
  <text x="490" y="213" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">&lt;springProfile name="prod"&gt;</text>
  <text x="490" y="229" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">  &lt;root level="WARN"/&gt;</text>
  <text x="490" y="243" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">&lt;/springProfile&gt;</text>
</svg>

`<springProperty>` imports values from the Spring Environment; `<springProfile>` enables conditional blocks.

## 5. Runnable example

```java
// SpringProfileProperty.java — run: java SpringProfileProperty.java  (JDK 17+)
// Simulates the evaluation logic behind <springProfile> and <springProperty>.

import java.util.*;

public class SpringProfileProperty {

    // Simulated Spring Environment
    static final Map<String, String> ENVIRONMENT = new LinkedHashMap<>(Map.of(
        "logging.file.path", "/var/log/myapp",
        "app.log.max-size",  "50MB",
        "spring.application.name", "order-service"
    ));

    static Set<String> activeProfiles = new HashSet<>();

    // Simulates <springProperty> resolution
    static String springProperty(String source, String defaultValue) {
        return ENVIRONMENT.getOrDefault(source, defaultValue);
    }

    // Simulates <springProfile name="…"> evaluation
    static boolean springProfile(String expression) {
        // Support: "prod", "!prod", "prod | staging", "prod & cloud" (simplified)
        if (expression.contains("|")) {
            return Arrays.stream(expression.split("\\|"))
                         .anyMatch(p -> springProfile(p.trim()));
        }
        if (expression.contains("&")) {
            return Arrays.stream(expression.split("&"))
                         .allMatch(p -> springProfile(p.trim()));
        }
        if (expression.startsWith("!")) return !activeProfiles.contains(expression.substring(1));
        return activeProfiles.contains(expression);
    }

    static void applyLogbackConfig() {
        // Resolve <springProperty> values
        String logDir     = springProperty("logging.file.path", "/tmp");
        String maxSize    = springProperty("app.log.max-size",  "10MB");
        String appName    = springProperty("spring.application.name", "app");

        System.out.println("=== Resolved springProperty values ===");
        System.out.printf("  ${LOG_DIR}  = %s  (source: logging.file.path)%n", logDir);
        System.out.printf("  ${MAX_SIZE} = %s  (source: app.log.max-size)%n", maxSize);
        System.out.printf("  ${APP_NAME} = %s  (source: spring.application.name)%n", appName);

        System.out.println("\n=== Evaluating <springProfile> blocks ===");
        System.out.printf("  Active profiles: %s%n", activeProfiles);

        if (springProfile("!prod")) {
            System.out.println("  <springProfile name='!prod'> block is ACTIVE");
            System.out.println("    → root level=DEBUG; console-only appender");
        } else {
            System.out.println("  <springProfile name='!prod'> block is INACTIVE");
        }

        if (springProfile("prod")) {
            System.out.println("  <springProfile name='prod'> block is ACTIVE");
            System.out.printf("    → root level=WARN; file=%s/%s.log maxSize=%s%n",
                    logDir, appName, maxSize);
        } else {
            System.out.println("  <springProfile name='prod'> block is INACTIVE");
        }

        if (springProfile("prod | staging")) {
            System.out.println("  <springProfile name='prod | staging'> block is ACTIVE");
            System.out.println("    → ERROR_FILE appender enabled");
        }
    }

    public static void main(String[] args) {
        System.out.println("========== Non-prod context ==========");
        activeProfiles = Set.of("dev");
        applyLogbackConfig();

        System.out.println("\n========== Production context ==========");
        activeProfiles = Set.of("prod");
        applyLogbackConfig();

        System.out.println("\n========== Staging context ==========");
        activeProfiles = Set.of("staging");
        applyLogbackConfig();
    }
}
```

**How to run:** `java SpringProfileProperty.java`

## 6. Walkthrough

- `springProperty("logging.file.path", "/tmp")` mirrors `<springProperty source="logging.file.path" defaultValue="/tmp"/>`. The Environment holds the value set in `application.properties` or an environment variable like `LOGGING_FILE_PATH`; the property receives whichever is present.
- `springProfile("!prod")` returns `true` when `prod` is not in `activeProfiles`. In the `dev` context, this block is active (root level `DEBUG`); in the `prod` context it is inactive.
- `springProfile("prod | staging")` simulates `<springProfile name="prod | staging">` — a block active in either environment. In real Logback XML, the `|` must be used as a literal pipe character (no XML entity needed).
- The `prod` context shows the file appender using the resolved `${LOG_DIR}` and `${APP_NAME}` — values read from the Spring Environment at XML-parse time. This is the key advantage over plain Logback: the XML references runtime configuration from `application.properties`.
- The `staging` context: `!prod` is active (same config as dev), but `prod | staging` is also active (error file enabled). This illustrates how multiple `<springProfile>` blocks can match simultaneously and combine additively.

## 7. Gotchas & takeaways

> **`<springProfile>` and `<springProperty>` only work in `logback-spring.xml`, not `logback.xml`.** The standard `logback.xml` is loaded by Logback's own initialisation, before Spring Boot has prepared the `Environment`. Spring Boot's extensions are injected into Logback by `LogbackLoggingSystem`, which only runs when the Spring Boot lifecycle is active.

> **In XML, `&` must be written as `&amp;` in attribute values.** `<springProfile name="prod &amp; cloud">` is AND; `<springProfile name="prod | cloud">` is OR. The `|` does not need escaping. Forgetting `&amp;` causes XML parse errors.

- `<springProperty scope="context" …>` makes the property available to all appenders and encoders in the file; `scope="local"` limits it to the current `<configuration>` block.
- `defaultValue` in `<springProperty>` is evaluated only when the source key is absent from the Environment — useful for local dev defaults that are overridden by environment variables in production.
- You can use `<springProperty>` to read any Spring Environment key, not just `logging.*` — `spring.application.name`, `server.port`, custom properties — all are accessible.
- `<springProfile>` blocks can nest inside appenders, loggers, and the root element, giving fine-grained conditional control over every Logback element.
- Profile expressions in `<springProfile>` follow the same rules as Spring's `@Profile` annotation, including the `!` negation and `|`/`&` compound operators.
