---
card: spring-boot
gi: 97
slug: custom-log-configuration-logback-spring-xml-log4j2
title: "Custom log configuration (logback-spring.xml, log4j2)"
---

## 1. What it is

Spring Boot's default Logback configuration handles most needs through `application.properties`. When you need capabilities that properties cannot express — custom appenders, async wrappers, per-environment encoder switching, TCP/socket outputs — you supply a **custom Logback configuration file**.

Spring Boot recognises two filenames on the classpath:
- **`logback.xml`** — standard Logback file, loaded directly by Logback **before** the Spring `Environment` is ready.
- **`logback-spring.xml`** — Spring Boot's extended variant, loaded **by Spring** after the environment is prepared. This unlocks Spring Boot extensions (`<springProfile>`, `<springProperty>`) and profile-aware configuration.

**Always prefer `logback-spring.xml`** over `logback.xml` when using Spring Boot.

For Log4j2, the equivalent extended name is `log4j2-spring.xml` (or `log4j2-spring.yaml` / `log4j2-spring.json`).

## 2. Why & when

Use a custom configuration file when:
- You need an **async appender** to decouple logging from application threads.
- You need a **socket/TCP appender** to stream logs to Logstash or Graylog.
- You need **different encoders per environment** (human-readable in dev, JSON in prod) controlled by Spring profiles.
- You want a **rolling policy** with parameters not exposed by `logging.logback.rollingpolicy.*`.
- You need **multiple appenders** — e.g., all logs to console, errors-only to a separate file.
- You want to use **Logback's MDC (Mapped Diagnostic Context)** with custom fields injected by a filter.

If `application.properties`-based configuration covers your needs, avoid the XML file — it's another thing to maintain and review.

## 3. Core concept

Minimal `logback-spring.xml` structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <!-- Import Spring Boot defaults (colour, standard pattern, base levels) -->
  <include resource="org/springframework/boot/logging/logback/defaults.xml"/>
  <include resource="org/springframework/boot/logging/logback/console-appender.xml"/>

  <!-- Override or extend as needed -->
  <root level="INFO">
    <appender-ref ref="CONSOLE"/>
  </root>
</configuration>
```

Key `<include>` resources from Spring Boot:
| Resource | What it provides |
|---|---|
| `defaults.xml` | Standard patterns, converter classes, colour support |
| `console-appender.xml` | `CONSOLE` appender (stdout, pattern from `defaults.xml`) |
| `file-appender.xml` | `FILE` rolling appender (uses `LOG_FILE` property) |
| `base.xml` | Includes both `defaults.xml` and `console-appender.xml` |

When you provide `logback-spring.xml`, Spring Boot stops applying its own auto-configuration — **your file is the complete configuration**. Include the Spring Boot defaults to avoid starting from scratch.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two paths: properties-based config feeds into Spring Boot defaults; custom logback-spring.xml bypasses defaults but can include them">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Properties vs. Custom XML Configuration</text>

  <!-- Left: properties path -->
  <rect x="30" y="55" width="270" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="74" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">application.properties</text>
  <text x="165" y="91" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logging.level.*, logging.pattern.*, logging.file.*</text>

  <defs><marker id="cl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="100" x2="165" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cl)"/>

  <rect x="30" y="122" width="270" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="141" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot auto-config</text>
  <text x="165" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">base.xml + defaults.xml applied</text>

  <!-- Right: custom XML path -->
  <rect x="380" y="55" width="270" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="515" y="74" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">logback-spring.xml</text>
  <text x="515" y="91" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">full control — async, socket, multi-appender</text>

  <line x1="515" y1="100" x2="515" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cl)"/>

  <rect x="380" y="122" width="270" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="141" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot loads your file</text>
  <text x="515" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">auto-config skipped; SpringProfile available</text>

  <!-- Both merge at Logback -->
  <line x1="165" y1="167" x2="290" y2="197" stroke="#8b949e" stroke-width="1" marker-end="url(#cl)"/>
  <line x1="515" y1="167" x2="390" y2="197" stroke="#8b949e" stroke-width="1" marker-end="url(#cl)"/>

  <rect x="200" y="200" width="280" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="219" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace" font-weight="bold">Logback LoggerContext</text>
  <text x="340" y="235" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">routes log events to configured appenders</text>
</svg>

Custom XML gives full Logback power; include Spring Boot's defaults to keep colour and standard patterns.

## 5. Runnable example

```java
// CustomLogConfig.java — run: java CustomLogConfig.java  (JDK 17+)
// Shows what a logback-spring.xml configures and prints the equivalent
// XML you would write, plus explains each section's purpose.

public class CustomLogConfig {

    public static void main(String[] args) {
        System.out.println("=== logback-spring.xml: async console + error file + JSON in prod ===");
        System.out.println();

        String xml = """
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

  <!-- Inherit Spring Boot colours and standard patterns -->
  <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

  <!-- Property resolved from Spring Environment -->
  <springProperty name="LOG_FILE" source="logging.file.name" defaultValue="logs/app.log"/>

  <!-- 1. CONSOLE appender (sync, all levels) -->
  <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>${CONSOLE_LOG_PATTERN}</pattern>
      <charset>UTF-8</charset>
    </encoder>
  </appender>

  <!-- 2. FILE appender: errors-only, rolling -->
  <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
      <level>ERROR</level>
    </filter>
    <file>${LOG_FILE}.error</file>
    <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
      <fileNamePattern>${LOG_FILE}.error.%d{yyyy-MM-dd}.%i.gz</fileNamePattern>
      <maxFileSize>20MB</maxFileSize>
      <maxHistory>30</maxHistory>
    </rollingPolicy>
    <encoder>
      <pattern>${FILE_LOG_PATTERN}</pattern>
    </encoder>
  </appender>

  <!-- 3. ASYNC wrapper for CONSOLE (non-blocking) -->
  <appender name="ASYNC_CONSOLE" class="ch.qos.logback.classic.AsyncAppender">
    <queueSize>512</queueSize>
    <discardingThreshold>0</discardingThreshold>
    <appender-ref ref="CONSOLE"/>
  </appender>

  <!-- 4. Profile-specific root configuration -->
  <springProfile name="!prod">
    <root level="INFO">
      <appender-ref ref="ASYNC_CONSOLE"/>
    </root>
  </springProfile>

  <springProfile name="prod">
    <root level="WARN">
      <appender-ref ref="ASYNC_CONSOLE"/>
      <appender-ref ref="ERROR_FILE"/>
    </root>
  </springProfile>

</configuration>
""";
        System.out.println(xml);

        System.out.println("Key decisions in this file:");
        System.out.println("  • Include defaults.xml: keeps Spring Boot colour and pattern variables");
        System.out.println("  • <springProperty>: reads logging.file.name from application.properties");
        System.out.println("  • ERROR_FILE: ThresholdFilter keeps only ERROR; separate from INFO file");
        System.out.println("  • AsyncAppender: 512-event queue; discardingThreshold=0 means no drops");
        System.out.println("  • springProfile !prod: async console + INFO; prod adds ERROR_FILE + WARN root");
    }
}
```

**How to run:** `java CustomLogConfig.java`

Place the printed XML content (starting `<?xml`) in `src/main/resources/logback-spring.xml`.

## 6. Walkthrough

- `<include resource="org/springframework/boot/logging/logback/defaults.xml"/>` — imports `${CONSOLE_LOG_PATTERN}`, `${FILE_LOG_PATTERN}`, and the `%clr` (ANSI colour) converter class. Without this include, your pattern string cannot reference Spring Boot's variables.
- `<springProperty name="LOG_FILE" source="logging.file.name" …/>` — reads a value from the Spring `Environment` (all property sources, including active profile files and environment variables) and makes it available as a Logback property `${LOG_FILE}`. This is a Spring Boot extension; `logback.xml` cannot do this.
- `ThresholdFilter` on `ERROR_FILE` — acts as a minimum-level gate. Events below `ERROR` are dropped before reaching the file appender. This creates a dedicated errors-only file without duplicating appender configuration.
- `AsyncAppender` wraps `CONSOLE`. Log events are placed in a 512-element queue by the application thread; a dedicated worker thread drains the queue to `CONSOLE`. `discardingThreshold=0` means the worker does not start dropping events when the queue is 80% full (the default 20% discard-on-full policy is disabled).
- `<springProfile name="!prod">` / `<springProfile name="prod">` — Spring Boot extensions that conditionally include XML blocks based on active profiles. This replaces the old (now deprecated) `<springProfile>` syntax in `logback.xml`.

## 7. Gotchas & takeaways

> **`logback.xml` is loaded before the Spring `Environment` exists.** This means `<springProperty>` and `<springProfile>` do not work in `logback.xml`. Always use `logback-spring.xml` in Spring Boot projects.

> **Once you provide `logback-spring.xml`, Spring Boot's auto-configuration steps aside entirely.** The `logging.level.*`, `logging.pattern.*`, and `logging.logback.rollingpolicy.*` properties in `application.properties` are still read by Spring Boot, but they are applied only if your XML file uses the corresponding Spring Boot default appenders. If you define your own `CONSOLE` appender without referencing `${CONSOLE_LOG_PATTERN}`, the pattern property has no effect.

- Place `logback-spring.xml` in `src/main/resources/` — Spring Boot finds it on the classpath automatically.
- Always `<include resource="org/springframework/boot/logging/logback/defaults.xml"/>` as the first line unless you want to start from a blank Logback config.
- For `AsyncAppender`, always pair it with the log shutdown hook (or Logback's `<shutdownHook>`) to avoid losing events on JVM exit.
- `<discardingThreshold>0</discardingThreshold>` disables event dropping; the default value of 20 drops events below WARN when the queue is 80% full — which can cause you to lose INFO logs during spikes.
- Log4j2's equivalent file is `log4j2-spring.xml`. Switching to Log4j2 requires removing `spring-boot-starter-logging` and adding `spring-boot-starter-log4j2`.
