---
card: spring-boot
gi: 99
slug: switching-to-log4j2-java-util-logging
title: Switching to Log4j2 / Java Util Logging
---

## 1. What it is

Spring Boot ships Logback as the default logging backend, but it supports switching to **Log4j2** or **Java Util Logging (JUL)** as alternatives. The switch is a pure dependency change — application code stays the same because all code uses the SLF4J API.

**To switch to Log4j2:**
1. Exclude `spring-boot-starter-logging` from every starter.
2. Add `spring-boot-starter-log4j2`.

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <exclusions>
    <exclusion>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-logging</artifactId>
    </exclusion>
  </exclusions>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-log4j2</artifactId>
</dependency>
```

Spring Boot then auto-detects Log4j2 and applies its own default configuration, supports `log4j2-spring.xml` for custom config, and exposes the same `logging.level.*` and `logging.group.*` properties.

**Java Util Logging** is supported by adding `jul-to-slf4j` (already on the classpath via `spring-boot-starter-logging`) — Spring Boot bridges JUL to SLF4J automatically.

## 2. Why & when

Most teams stay with Logback. Switch to Log4j2 when:
- **Async logging performance** is critical — Log4j2's `AsyncLogger` (using LMAX Disruptor) is significantly faster than Logback's `AsyncAppender` under very high throughput.
- Your organisation standardises on Log4j2 (common in enterprises that adopted it before Spring Boot).
- You need Log4j2-specific features: `printf`-style parameters, lazy message evaluation with lambdas, or JMX-based runtime reconfiguration.
- You are integrating with a logging library that provides a Log4j2 plugin (Gelf, Kafka appenders).

Stay with Logback when:
- You have no performance complaints with the current setup.
- Your team is more familiar with Logback XML syntax.
- You don't need Log4j2-specific appenders.

**Important:** Log4j 1.x is end-of-life and has known security vulnerabilities. Do not confuse Log4j 1.x with Log4j2 — they are different projects.

## 3. Core concept

Spring Boot's `LoggingSystem` abstraction detects which logging backend is on the classpath:

```
Classpath scan order (first match wins):
  1. logback-classic  → LogbackLoggingSystem
  2. log4j2-core      → Log4J2LoggingSystem
  3. java.util.logging → JavaLoggingSystem (always available)
```

After the switch, Log4j2 reads configuration from `log4j2-spring.xml` (Spring Boot extended, preferred) or `log4j2.xml` (standard). Log4j2's configuration file syntax differs from Logback's:

```xml
<!-- log4j2-spring.xml -->
<Configuration status="WARN">
  <Appenders>
    <Console name="CONSOLE" target="SYSTEM_OUT">
      <PatternLayout pattern="%d{yyyy-MM-dd'T'HH:mm:ss.SSSXXX} %5p %X{pid} --- [%t] %-40.40c : %m%n"/>
    </Console>
  </Appenders>
  <Loggers>
    <Root level="info">
      <AppenderRef ref="CONSOLE"/>
    </Root>
  </Loggers>
</Configuration>
```

Log4j2's true async loggers (via LMAX Disruptor) require adding the `disruptor` dependency and declaring loggers with `<AsyncRoot>` or `<AsyncLogger>`.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side: Logback default setup on the left vs Log4j2 setup on the right, showing same SLF4J API top, different backend">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Logback (default) vs. Log4j2 (alternative)</text>

  <!-- Divider -->
  <line x1="340" y1="48" x2="340" y2="240" stroke="#30363d" stroke-width="1" stroke-dasharray="4 3"/>

  <!-- SLF4J (shared) -->
  <rect x="140" y="50" width="400" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="340" y="73" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">SLF4J API  — application code unchanged</text>

  <!-- Left: Logback -->
  <rect x="30" y="102" width="280" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="117" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">spring-boot-starter-logging</text>
  <text x="170" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logback-classic (default, auto-configured)</text>

  <rect x="30" y="150" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="170" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logback-spring.xml  (optional)</text>

  <rect x="60" y="192" width="220" height="30" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="212" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Logback backend</text>

  <!-- Right: Log4j2 -->
  <rect x="370" y="102" width="280" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="510" y="117" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">spring-boot-starter-log4j2</text>
  <text x="510" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">excludes starter-logging; adds log4j2-core</text>

  <rect x="370" y="150" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="510" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">log4j2-spring.xml  (optional)</text>

  <rect x="400" y="192" width="220" height="30" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="212" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Log4j2 backend (faster async)</text>

  <rect x="30" y="232" width="620" height="20" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="246" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both backends: same logging.level.* / logging.group.* properties work via Spring Boot's LoggingSystem abstraction</text>
</svg>

The SLF4J API layer means zero application-code changes when switching backends.

## 5. Runnable example

```java
// SwitchingLogging.java — run: java SwitchingLogging.java  (JDK 17+)
// Shows the pom.xml dependency change required and why application code is unaffected.

public class SwitchingLogging {

    public static void main(String[] args) {
        System.out.println("=== Dependency change to switch to Log4j2 ===\n");
        System.out.println("""
<!-- pom.xml: exclude Logback, add Log4j2 starter -->

<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <exclusions>
    <exclusion>
      <!-- Remove Logback + SLF4J bridges that came with starter-logging -->
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-logging</artifactId>
    </exclusion>
  </exclusions>
</dependency>

<!-- Add Log4j2 autoconfiguration -->
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-log4j2</artifactId>
</dependency>

<!-- Optional: LMAX Disruptor for async loggers (truly lock-free) -->
<dependency>
  <groupId>com.lmax</groupId>
  <artifactId>disruptor</artifactId>
  <version>3.4.4</version>
</dependency>
""");

        System.out.println("=== Your application code: UNCHANGED ===\n");
        System.out.println("""
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderService {
    // This line is identical whether Logback or Log4j2 is on the classpath
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    public void processOrder(long id) {
        log.info("Processing order {}", id);   // same SLF4J call, different backend
    }
}
""");

        System.out.println("=== log4j2-spring.xml (equivalent to logback-spring.xml) ===\n");
        System.out.println("""
<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="WARN">
  <Properties>
    <Property name="LOG_PATTERN">
      %d{yyyy-MM-dd'T'HH:mm:ss.SSSXXX} %5p ${sys:PID} --- [%t] %-40.40c : %m%n
    </Property>
  </Properties>
  <Appenders>
    <Console name="CONSOLE" target="SYSTEM_OUT">
      <PatternLayout pattern="${LOG_PATTERN}"/>
    </Console>
    <!-- Log4j2 AsyncAppender using LMAX Disruptor (add disruptor jar) -->
    <Async name="ASYNC_CONSOLE">
      <AppenderRef ref="CONSOLE"/>
    </Async>
  </Appenders>
  <Loggers>
    <Logger name="com.example" level="debug" additivity="false">
      <AppenderRef ref="ASYNC_CONSOLE"/>
    </Logger>
    <Root level="warn">
      <AppenderRef ref="ASYNC_CONSOLE"/>
    </Root>
  </Loggers>
</Configuration>
""");

        System.out.println("application.properties: logging.level.* still works (same as Logback)");
        System.out.println("  logging.level.root=warn");
        System.out.println("  logging.level.com.example=debug");
    }
}
```

**How to run:** `java SwitchingLogging.java`

## 6. Walkthrough

- **Dependency exclusion** — `spring-boot-starter-logging` is a transitive dependency of every Spring Boot starter. You must exclude it from at least one starter; Maven/Gradle then removes it transitively. Adding it back as a direct dependency would bring Logback back. The easiest pattern is to exclude it from your primary starter (`spring-boot-starter-web`, `spring-boot-starter-data-jpa`, etc.).
- **`spring-boot-starter-log4j2`** brings `log4j2-core`, the SLF4J-to-Log4j2 bridge (`log4j-slf4j2-impl`), and the JUL-to-Log4j2 bridge. Spring Boot's `Log4J2LoggingSystem` then picks it up automatically.
- **`Logger log = LoggerFactory.getLogger(…)`** — this line is SLF4J API. At runtime, SLF4J's `StaticLoggerBinder` (Log4j2's binding) routes `getLogger` calls to Log4j2's `LogManager`. The application class never imports `org.apache.logging.log4j`.
- **`log4j2-spring.xml`** — note the `<Properties>` block (not Logback's `<property>`), `<Configuration>` root (not `<configuration>`), and `<Logger>`/`<Root>` inside `<Loggers>` (not directly under the root element). The structure is similar but the XML elements are different.
- **`<Async name="ASYNC_CONSOLE">`** in Log4j2 uses the LMAX Disruptor ring buffer (if on classpath) for lock-free inter-thread event passing, which is faster than Logback's `AsyncAppender` queue under contention.
- **`logging.level.*` properties** — still work because Spring Boot's `Log4J2LoggingSystem` reads them and calls the Log4j2 API to set levels, just as `LogbackLoggingSystem` does for Logback.

## 7. Gotchas & takeaways

> **You must exclude `spring-boot-starter-logging` from every starter, not just one.** If two starters bring in `spring-boot-starter-logging` and you only exclude it from one, the second still pulls it in. In practice, Maven/Gradle dependency resolution usually deduplicates this, but always verify with `mvn dependency:tree | grep logback` that no Logback JARs remain on the classpath.

> **Log4j 1.x is not Log4j2.** `log4j:log4j:1.2.x` (Log4j 1) is end-of-life and has critical CVEs. `org.apache.logging.log4j:log4j-core` (Log4j 2) is the modern, actively maintained project. The `log4shell` vulnerability (CVE-2021-44228) affected Log4j2 but was patched in 2.17.1+; Spring Boot 2.6+ and all 3.x versions use patched versions.

- The switch is reversible: swap the dependency back; no application code changes needed.
- True async logging (`<AsyncRoot>` or `-Dlog4j2.contextSelector=org.apache.logging.log4j.core.async.AsyncLoggerContextSelector`) requires the `com.lmax:disruptor` JAR on the classpath.
- Log4j2 supports configuration file polling — it can reload `log4j2-spring.xml` when it changes on disk, without a restart. Set `<Configuration monitorInterval="30">` for 30-second polling.
- Both Logback and Log4j2 support the same `logging.level.*` and `logging.group.*` Spring Boot properties — switching backends does not require changes to `application.properties`.
- For Java Util Logging (JUL): Spring Boot bridges JUL to SLF4J automatically via `jul-to-slf4j`. You rarely need to configure JUL directly; just set `logging.level.*` as usual and all JUL output routes through Logback/Log4j2.
