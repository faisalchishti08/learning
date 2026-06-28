---
card: spring-boot
gi: 101
slug: structured-logging-ecs-logstash-gelf
title: Structured logging (ECS, Logstash, GELF)
---

## 1. What it is

**Structured logging** means emitting log events as machine-parseable documents (typically JSON) rather than human-readable text strings. Instead of:

```
2026-06-28T10:15:30.123Z  INFO 12345 --- [main] c.e.OrderService : Order 42 processed in 52ms
```

you emit:

```json
{"@timestamp":"2026-06-28T10:15:30.123Z","log.level":"INFO","process.pid":12345,"message":"Order 42 processed in 52ms","logger_name":"c.e.OrderService","thread_name":"main","order.id":42,"duration_ms":52}
```

Spring Boot 3.4+ has native support for three structured logging formats controlled by a single property:

```properties
logging.structured.format.console=ecs          # Elastic Common Schema (ECS)
logging.structured.format.console=logstash     # Logstash JSON
logging.structured.format.console=gelf         # Graylog Extended Log Format
logging.structured.format.file=ecs             # independent setting for file output
```

Before Spring Boot 3.4, structured logging required third-party Logback encoders (`logstash-logback-encoder`, `logback-gelf`).

## 2. Why & when

Human-readable text logs are designed for eyeballs. Log aggregators (Elasticsearch, Splunk, CloudWatch, Loki) work far better with structured data:
- **Indexable fields** — search `order.id:42` instead of `grep "Order 42"`.
- **No parsing needed** — the aggregator ingests JSON directly; regex fragility disappears.
- **MDC fields become first-class** — `traceId`, `userId`, `orderId` added to the Mapped Diagnostic Context appear as queryable JSON fields, not buried in a message string.
- **Consistent schema** — ECS defines a standard field vocabulary (e.g. `log.level`, not `severity`), so queries work across services.

Use structured logging when logs are consumed by a log aggregation platform. Keep human-readable format in local development (or use both: structured to file, human-readable to console).

## 3. Core concept

**ECS (Elastic Common Schema)** output example:
```json
{
  "@timestamp": "2026-06-28T10:15:30.123Z",
  "log.level": "INFO",
  "process.pid": 12345,
  "process.thread.name": "main",
  "log.logger": "com.example.OrderService",
  "message": "Order 42 processed",
  "service.name": "order-service",
  "ecs.version": "8.11"
}
```

**Logstash JSON** output example:
```json
{
  "@timestamp": "2026-06-28T10:15:30.123Z",
  "@version": "1",
  "message": "Order 42 processed",
  "logger_name": "com.example.OrderService",
  "thread_name": "main",
  "level": "INFO",
  "level_value": 20000
}
```

**GELF (Graylog Extended Log Format)** output example:
```json
{
  "version": "1.1",
  "timestamp": 1719569730.123,
  "short_message": "Order 42 processed",
  "level": 6,
  "host": "app-server-1",
  "_logger": "com.example.OrderService",
  "_thread": "main"
}
```

**MDC integration:** fields added to `org.slf4j.MDC` automatically appear as extra JSON fields in all three formats:
```java
MDC.put("orderId", "42");
MDC.put("customerId", "alice");
log.info("Order processed");
// JSON output includes: "orderId": "42", "customerId": "alice"
```

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Structured vs text logging: text goes to console for humans; structured JSON goes to log aggregator for machines">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Structured vs. Text Logging</text>

  <!-- Application -->
  <rect x="260" y="50" width="160" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="73" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">log.info("…")</text>

  <defs><marker id="sl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="87" x2="160" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#sl)"/>
  <line x1="400" y1="87" x2="520" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#sl)"/>

  <!-- Text console -->
  <rect x="30" y="117" width="270" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Console (text, for humans)</text>
  <text x="165" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.pattern.console=…</text>
  <text x="165" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ terminal, local dev</text>

  <!-- Structured file -->
  <rect x="380" y="117" width="270" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="515" y="135" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">File (JSON, for machines)</text>
  <text x="515" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">logging.structured.format.file=ecs</text>
  <text x="515" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ Filebeat → Elasticsearch</text>

  <!-- Aggregator -->
  <line x1="515" y1="174" x2="515" y2="194" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sl)"/>
  <rect x="380" y="196" width="270" height="44" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="215" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Log aggregator</text>
  <text x="515" y="231" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Kibana dashboard | Grafana Loki | Splunk</text>

  <!-- Example JSON snippet -->
  <rect x="30" y="192" width="270" height="54" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="165" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ECS field example</text>
  <text x="40"  y="222" fill="#e6edf3" font-size="8.5" font-family="monospace">"log.level":"INFO","message":"…"</text>
  <text x="40"  y="236" fill="#e6edf3" font-size="8.5" font-family="monospace">"orderId":"42","customerId":"alice"</text>
</svg>

Text to console for humans; structured JSON to file for aggregators — controlled by two independent properties.

## 5. Runnable example

```java
// StructuredLogging.java — run: java StructuredLogging.java  (JDK 17+)
// Simulates ECS, Logstash, and GELF structured log output formats.

import java.time.*;
import java.time.format.*;
import java.util.*;

public class StructuredLogging {

    enum Format { ECS, LOGSTASH, GELF }

    static final DateTimeFormatter ISO = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSXXX")
            .withZone(ZoneOffset.UTC);

    record LogEvent(String level, String logger, String thread, String message,
                    Map<String, String> mdcFields) {}

    static String formatEcs(LogEvent e, long pid) {
        Instant now = Instant.now();
        String ts = ISO.format(now);
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"@timestamp\":\"").append(ts).append("\"");
        sb.append(",\"log.level\":\"").append(e.level()).append("\"");
        sb.append(",\"process.pid\":").append(pid);
        sb.append(",\"process.thread.name\":\"").append(e.thread()).append("\"");
        sb.append(",\"log.logger\":\"").append(e.logger()).append("\"");
        sb.append(",\"message\":\"").append(e.message()).append("\"");
        sb.append(",\"ecs.version\":\"8.11\"");
        e.mdcFields().forEach((k, v) -> sb.append(",\"").append(k).append("\":\"").append(v).append("\""));
        sb.append("}");
        return sb.toString();
    }

    static String formatLogstash(LogEvent e) {
        Instant now = Instant.now();
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"@timestamp\":\"").append(ISO.format(now)).append("\"");
        sb.append(",\"@version\":\"1\"");
        sb.append(",\"message\":\"").append(e.message()).append("\"");
        sb.append(",\"logger_name\":\"").append(e.logger()).append("\"");
        sb.append(",\"thread_name\":\"").append(e.thread()).append("\"");
        sb.append(",\"level\":\"").append(e.level()).append("\"");
        int levelValue = Map.of("ERROR",40000,"WARN",30000,"INFO",20000,"DEBUG",10000,"TRACE",5000)
                .getOrDefault(e.level(), 0);
        sb.append(",\"level_value\":").append(levelValue);
        e.mdcFields().forEach((k, v) -> sb.append(",\"").append(k).append("\":\"").append(v).append("\""));
        sb.append("}");
        return sb.toString();
    }

    static String formatGelf(LogEvent e, String host) {
        double ts = Instant.now().toEpochMilli() / 1000.0;
        int syslogLevel = Map.of("ERROR",3,"WARN",4,"INFO",6,"DEBUG",7,"TRACE",7)
                .getOrDefault(e.level(), 6);
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"version\":\"1.1\"");
        sb.append(",\"timestamp\":").append(String.format("%.3f", ts));
        sb.append(",\"short_message\":\"").append(e.message()).append("\"");
        sb.append(",\"level\":").append(syslogLevel);
        sb.append(",\"host\":\"").append(host).append("\"");
        sb.append(",\"_logger\":\"").append(e.logger()).append("\"");
        sb.append(",\"_thread\":\"").append(e.thread()).append("\"");
        e.mdcFields().forEach((k, v) -> sb.append(",\"_").append(k).append("\":\"").append(v).append("\""));
        sb.append("}");
        return sb.toString();
    }

    public static void main(String[] args) {
        long pid = ProcessHandle.current().pid();
        Map<String, String> mdc = Map.of("orderId", "42", "customerId", "alice");
        LogEvent e = new LogEvent("INFO", "com.example.OrderService",
                "main", "Order 42 processed in 52ms", mdc);

        System.out.println("=== ECS (Elastic Common Schema) ===");
        System.out.println(formatEcs(e, pid));

        System.out.println("\n=== Logstash JSON ===");
        System.out.println(formatLogstash(e));

        System.out.println("\n=== GELF (Graylog Extended Log Format) ===");
        System.out.println(formatGelf(e, "app-server-1"));

        System.out.println("\n=== Spring Boot 3.4+ property to enable ===");
        System.out.println("logging.structured.format.console=ecs   # or logstash or gelf");
        System.out.println("logging.structured.format.file=ecs       # independent from console");
    }
}
```

**How to run:** `java StructuredLogging.java`

## 6. Walkthrough

- `formatEcs` produces the Elastic Common Schema format. Key ECS field names use dot notation (`log.level`, `process.pid`, `log.logger`) rather than underscores — these map to Elasticsearch nested objects in the `log.*` and `process.*` namespaces defined by ECS.
- `formatLogstash` mirrors the `logstash-logback-encoder` library's default output — historically the most common way to get structured logging before Spring Boot 3.4 native support. `level_value` is a numeric priority used for ordering.
- `formatGelf` produces Graylog's input format. Note: `timestamp` is Unix epoch in seconds (double), not ISO-8601 — GELF has its own timestamp convention. Custom fields are prefixed with `_` (mandatory in GELF spec). `level` is a syslog numeric level (0=EMERG, 3=ERROR, 6=INFO).
- **MDC fields** (`orderId`, `customerId`) appear in all three formats — in ECS as top-level fields, in GELF as `_orderId`. This is the primary reason to use structured logging: `orderId` is an indexed field in Kibana, not buried in a message string.
- In real Spring Boot 3.4+, the property `logging.structured.format.console=ecs` replaces the text `ConsoleAppender` with a JSON-producing one. The application code is unchanged — MDC fields are automatically included.

## 7. Gotchas & takeaways

> **`logging.structured.format.console=ecs` disables ANSI colour and the human-readable pattern.** The console emits one JSON object per line. In local development, consider keeping `console` as text and setting `logging.structured.format.file=ecs` so the aggregated file is structured while your terminal remains readable.

> **GELF's custom field `_` prefix is mandatory in the spec but differs from ECS and Logstash.** If you later switch from GELF to ECS, MDC field names in Kibana queries change (`_orderId` → `orderId`). Standardise on one format early.

- In Spring Boot < 3.4, structured logging requires `logstash-logback-encoder` as a dependency and a custom `logback-spring.xml` with a JSON encoder.
- MDC fields (`MDC.put(key, value)`) appear automatically in structured output — no changes to logger call sites needed. Always clean up with `MDC.remove(key)` or `MDC.clear()` at request end (typically in a servlet filter or WebFlux filter).
- `spring.application.name` is included in ECS output as `service.name` automatically — set this property in every service for clear identification in multi-service Kibana views.
- Structured log lines are longer than text lines. At very high log volume, JSON overhead (key repetition, quotes) increases storage cost — weigh against the query benefits.
- Test structured logging with `spring.output.ansi.enabled=NEVER` and `logging.structured.format.console=ecs` in your test `application.properties` to validate MDC fields are present before deploying.
