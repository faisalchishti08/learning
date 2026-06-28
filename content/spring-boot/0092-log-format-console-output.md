---
card: spring-boot
gi: 92
slug: log-format-console-output
title: Log format & console output
---

## 1. What it is

Spring Boot's **default console log format** is a fixed pattern that provides the most useful fields in a compact line. Every log message written to the console looks like:

```
2026-06-28T10:15:30.123Z  INFO 12345 --- [main] com.example.MyService  : Order 42 processed
│                         │    │     │    │                        │
timestamp (ISO-8601)   level  PID  ---  thread name          logger name         message
```

The format is configured by Spring Boot's bundled Logback configuration (`defaults.xml`) and applied to the `ConsoleAppender`. You can override individual parts or the entire format through properties, without touching XML.

## 2. Why & when

A structured, consistent log format matters because logs are not just for reading — they are also parsed by log aggregators (ELK stack, Datadog, CloudWatch). A predictable format means tools can extract level, timestamp, and service name without custom parsers.

Spring Boot's default format is chosen to be:
- **Human-readable** in a terminal during development.
- **Parse-friendly** — fixed-width level field, consistent separators.
- **Contextual** — thread name is visible (critical in reactive or async code), and the logger name identifies the exact class that logged the message.

You need to understand the format to know what each field means when debugging, and to know which properties tweak each part.

## 3. Core concept

Default console pattern (Spring Boot 3.x):
```
%d{yyyy-MM-dd'T'HH:mm:ss.SSSXXX} %5p ${PID:- } --- %t %-40logger{39} : %m%n
```

| Token | What it produces |
|---|---|
| `%d{…}` | Timestamp in ISO-8601 format |
| `%5p` | Log level, right-aligned in 5 chars (`INFO`, `WARN `, `ERROR`, `DEBUG`, `TRACE`) |
| `${PID}` | OS process ID |
| `---` | Fixed separator |
| `%t` | Thread name |
| `%-40logger{39}` | Logger name (class name), left-padded to 40 chars, max 39 chars abbreviated |
| `%m%n` | Message + newline |

Spring Boot also supports **ANSI colour output** on terminals that support it (off by default in CI environments that don't detect colour support). Levels are coloured: `ERROR`=red, `WARN`=yellow, `INFO`=green, `DEBUG`=green, `TRACE`=green.

Properties for tuning console output:
```properties
# Disable ANSI colour
spring.output.ansi.enabled=never

# Change the entire pattern
logging.pattern.console=%d{HH:mm:ss} %-5level %logger{36} - %msg%n
```

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of a Spring Boot console log line annotated with field names">
  <rect x="8" y="8" width="664" height="224" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Anatomy of a Spring Boot Log Line</text>

  <!-- Log line -->
  <rect x="20" y="48" width="640" height="36" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="71" fill="#e6edf3" font-size="10.5" text-anchor="middle" font-family="monospace">2026-06-28T10:15:30.123Z  INFO 12345 --- [main] c.e.demo.OrderService      : Order 42 processed</text>

  <!-- Annotations -->
  <line x1="85" y1="84" x2="85" y2="104" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">timestamp</text>

  <line x1="260" y1="84" x2="260" y2="104" stroke="#6db33f" stroke-width="1"/>
  <text x="260" y="116" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">level</text>

  <line x1="300" y1="84" x2="300" y2="104" stroke="#8b949e" stroke-width="1"/>
  <text x="300" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PID</text>

  <line x1="330" y1="84" x2="330" y2="104" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">---</text>

  <line x1="367" y1="84" x2="367" y2="104" stroke="#79c0ff" stroke-width="1"/>
  <text x="367" y="116" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">thread</text>

  <line x1="462" y1="84" x2="462" y2="104" stroke="#f0883e" stroke-width="1"/>
  <text x="462" y="116" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">logger name</text>

  <line x1="580" y1="84" x2="580" y2="104" stroke="#e6edf3" stroke-width="1"/>
  <text x="580" y="116" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">message</text>

  <!-- Customisation hints -->
  <rect x="20" y="130" width="305" height="82" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="172" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Property overrides</text>
  <text x="30" y="164" fill="#e6edf3" font-size="9" font-family="monospace">logging.pattern.console=</text>
  <text x="30" y="178" fill="#e6edf3" font-size="9" font-family="monospace">  %d{HH:mm:ss} %-5level %logger{36}</text>
  <text x="30" y="192" fill="#e6edf3" font-size="9" font-family="monospace">spring.output.ansi.enabled=always</text>
  <text x="30" y="206" fill="#e6edf3" font-size="9" font-family="monospace">logging.pattern.dateformat=yyyy-MM-dd</text>

  <rect x="355" y="130" width="305" height="82" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="507" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">ANSI colour by level</text>
  <text x="375" y="164" fill="#f85149" font-size="10" font-family="monospace">ERROR → red</text>
  <text x="375" y="178" fill="#e3b341" font-size="10" font-family="monospace">WARN  → yellow</text>
  <text x="375" y="192" fill="#6db33f" font-size="10" font-family="monospace">INFO  → green</text>
  <text x="375" y="206" fill="#8b949e" font-size="10" font-family="monospace">DEBUG / TRACE → cyan / blue</text>
</svg>

The fixed-width level field and consistent separator `---` make each line grep-friendly.

## 5. Runnable example

```java
// LogFormat.java — run: java LogFormat.java  (JDK 17+)
// Simulates Spring Boot's default console log format so you can see each field clearly.

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

public class LogFormat {

    static final DateTimeFormatter TS =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSXXX");

    // Simulate the Logback ConsoleAppender pattern:
    // %d{...} %5p ${PID} --- %t %-40logger{39} : %m%n
    static void log(String level, String loggerName, String msg) {
        String ts      = ZonedDateTime.now().format(TS);
        String pid     = String.valueOf(ProcessHandle.current().pid());
        String thread  = Thread.currentThread().getName();
        // Abbreviate: com.example.demo.OrderService → c.e.demo.OrderService (39 chars max)
        String abbrev  = abbreviate(loggerName, 39);
        System.out.printf("%-30s %5s %5s --- [%-15s] %-40s : %s%n",
                ts, level, pid, thread, abbrev, msg);
    }

    static String abbreviate(String name, int max) {
        if (name.length() <= max) return name;
        String[] parts = name.split("\\.");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length - 1; i++)
            sb.append(parts[i].charAt(0)).append('.');
        sb.append(parts[parts.length - 1]);
        return sb.length() <= max ? sb.toString() : sb.substring(sb.length() - max);
    }

    public static void main(String[] args) throws InterruptedException {
        String svc = "com.example.demo.OrderService";
        String repo = "com.example.demo.repository.ProductRepository";

        log("INFO",  svc,  "Application started");
        log("DEBUG", svc,  "Entering processOrder(orderId=42)");
        log("INFO",  svc,  "Processing order 42 for customer alice");
        log("WARN",  repo, "Slow query: findByStatus took 3412ms");
        log("ERROR", svc,  "Failed to reserve stock: item 'WIDGET-7' out of stock");
        log("INFO",  svc,  "Order 42 completed in 3450ms");

        System.out.println();
        System.out.println("--- Custom pattern: logging.pattern.console=%d{HH:mm:ss} %-5level %logger{36} - %msg%n ---");
        // Compact pattern example
        String ts = ZonedDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
        System.out.printf("%s %-5s %s - %s%n", ts, "INFO",  abbreviate(svc, 36), "Compact format output");
        System.out.printf("%s %-5s %s - %s%n", ts, "WARN",  abbreviate(repo, 36), "Compact format output");
    }
}
```

**How to run:** `java LogFormat.java`

## 6. Walkthrough

- `DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSXXX")` — Spring Boot 3.x uses ISO-8601 with timezone offset by default. `XXX` produces `+00:00` or `Z` for UTC. Spring Boot 2.x used `yyyy-MM-dd HH:mm:ss.SSS` (no timezone); the 3.x change improves log correlation across zones.
- `%5s` for the level field — right-aligned in 5 characters. `INFO` is 4 chars + 1 space; `WARN` is 4 chars + 1 space; `ERROR` is 5 chars exactly. This alignment lets you `grep` for ` WARN ` or `ERROR` as fixed-column patterns.
- `%-15s` for thread name — left-aligned, padded to 15. Spring MVC uses `[nio-8080-exec-1]`; Spring WebFlux uses `[reactor-http-nio-2]`; test threads are `[main]`. Thread name quickly tells you the concurrency model.
- `abbreviate(loggerName, 39)` — the Logback `logger{39}` conversion replaces package components with their first letter, keeping the class name intact: `com.example.demo.OrderService` → `c.e.demo.OrderService`. This prevents the logger column from overrunning 40 chars while preserving enough to identify the class.
- The `INFO`/`DEBUG`/`WARN`/`ERROR` lines illustrate how level filtering works — in production, `DEBUG` would be suppressed by the root level; the `WARN` for a slow query is the first thing an on-call engineer notices.

## 7. Gotchas & takeaways

> **Spring Boot 3.x changed the default timestamp format to ISO-8601 with timezone.** If you parse log files with a fixed regex expecting `yyyy-MM-dd HH:mm:ss.SSS`, those regexes will break on 3.x logs. Update parsers or override with `logging.pattern.dateformat=yyyy-MM-dd HH:mm:ss.SSS`.

> **ANSI colour is enabled by default when a TTY is detected, disabled in non-TTY environments (CI, piped output).** Force it on with `spring.output.ansi.enabled=always` or off with `never`. Some CI systems set `TERM=dumb` which Spring Boot respects.

- The logger name field is the fully qualified class name, abbreviated by default to 39 chars — always pass `MyClass.class` to `getLogger` so the name is accurate after refactoring.
- `%-40logger{39}` means "print the logger name abbreviated to 39 chars, left-padded to 40 columns" — the two numbers are different (padding vs. max length).
- `logging.pattern.console` overrides the entire console pattern; `logging.pattern.dateformat` overrides only the timestamp format.
- The `---` separator is a fixed string, not functional — it just visually separates PID+thread from logger+message, making the output easier to scan.
- In structured logging mode (Spring Boot 3.4+), the console format changes entirely — JSON instead of the human-readable pattern.
