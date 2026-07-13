---
card: microservices
gi: 375
slug: logback-log4j2-structured-json-logging-with-spring-boot
title: "Logback/Log4j2 structured (JSON) logging with Spring Boot"
---

## 1. What it is

**Logback** and **Log4j2** are the two logging frameworks Spring Boot supports (Logback is the default), and both can be configured to emit **structured JSON** output instead of their traditional human-formatted text lines — either via a JSON encoder/layout (Logback's `LogstashEncoder` or similar, Log4j2's built-in `JsonTemplateLayout`), or, as of recent Spring Boot versions, via built-in `logging.structured.format` configuration that requires no extra dependency at all. This is the concrete Spring Boot mechanism for actually achieving [structured logging](0360-structured-logging.md) in practice.

## 2. Why & when

[Structured logging](0360-structured-logging.md) explained *why* JSON-shaped logs matter for reliable searching and correlation; this topic is *how* you actually get there in a Spring Boot application, since the framework's default configuration produces human-readable text, not JSON, out of the box. Configuring the logging framework's encoder/layout is the one place this decision gets made — get it right once, at the framework configuration level, and every `logger.info(...)` call throughout the entire codebase automatically produces correctly-shaped structured output, with the application code itself never needing to format anything manually.

Configure structured JSON logging as a baseline for any service whose logs feed a [centralized log aggregation](0361-centralized-log-aggregation.md) system — which is essentially every microservice in a real deployment. Include Mapped Diagnostic Context (MDC) values (correlation ID, trace ID) as fields automatically via the encoder configuration, so every log statement picks these up without any code change at each individual call site.

## 3. Core concept

The logging framework's configured encoder or layout is what determines output format; switching from a plain-text pattern to a JSON one is purely a configuration change (an XML/properties file for Logback, similar for Log4j2, or Spring Boot's newer built-in `logging.structured.format=ecs` or `gelf` configuration properties) — no application code that calls `logger.info(...)` needs to change at all, since the framework applies the encoder uniformly to every log statement.

```xml
<!-- Logback logback-spring.xml: swap the encoder, not the application code -->
<encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <includeMdcKeyName>correlationId</includeMdcKeyName>
</encoder>
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same logger.info call, with only the configured encoder changed, produces plain text output in one configuration and structured JSON output in another -- the application code is identical in both cases">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">logger.info("order placed")</text>

  <line x1="280" y1="49" x2="140" y2="90" stroke="#8b949e" marker-end="url(#a375)"/>
  <rect x="20" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Plain-text encoder -&gt; "INFO: order placed"</text>

  <line x1="360" y1="49" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a375)"/>
  <rect x="380" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON encoder -&gt; {"level":"INFO",...}</text>

  <defs><marker id="a375" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The identical logging call produces different output formats depending purely on which encoder is configured — application code never changes.

## 5. Runnable example

Scenario: an order-placement log statement, first with plain-text output (hard to reliably parse), then rebuilt to produce structured JSON output via a swapped encoder with no application code change, and finally extended to automatically include MDC context (correlation ID) in every JSON log entry.

### Level 1 — Basic

```java
// File: PlainTextEncoderOutput.java -- simulates the DEFAULT Logback
// configuration: a plain-text encoder producing human-readable, but
// hard-to-reliably-parse, log lines.
import java.util.*;

public class PlainTextEncoderOutput {
    interface Encoder { String encode(String level, String message); }

    static class PlainTextEncoder implements Encoder { // the DEFAULT Spring Boot encoder shape
        public String encode(String level, String message) { return level + ": " + message; }
    }

    static Encoder encoder = new PlainTextEncoder();

    static void logInfo(String message) { System.out.println(encoder.encode("INFO", message)); } // APPLICATION code

    public static void main(String[] args) {
        logInfo("order placed for order-1");
        System.out.println("Human-readable, but reliably EXTRACTING 'order-1' back out requires fragile regex parsing.");
    }
}
```

How to run: `java PlainTextEncoderOutput.java`

`logInfo` is ordinary application logging code, calling through to whatever `Encoder` is configured. With `PlainTextEncoder` configured, the output is a simple, human-readable sentence — but, exactly as covered in [structured logging](0360-structured-logging.md), reliably extracting a specific field (like the order ID) back out of this text later requires fragile parsing.

### Level 2 — Intermediate

```java
// File: JsonEncoderNoCodeChange.java -- swaps ONLY the configured
// encoder to a JSON one; logInfo's APPLICATION code is IDENTICAL to
// Level 1's -- only the encoder implementation changed.
import java.util.*;

public class JsonEncoderNoCodeChange {
    interface Encoder { String encode(String level, String message); }

    static class PlainTextEncoder implements Encoder {
        public String encode(String level, String message) { return level + ": " + message; }
    }

    static class JsonEncoder implements Encoder { // the NEW configured encoder -- e.g. logback's LogstashEncoder
        public String encode(String level, String message) {
            return "{\"level\":\"" + level + "\",\"message\":\"" + message + "\"}";
        }
    }

    static Encoder encoder = new JsonEncoder(); // ONLY this line changed -- a CONFIGURATION swap, not application code

    static void logInfo(String message) { System.out.println(encoder.encode("INFO", message)); } // IDENTICAL to Level 1

    public static void main(String[] args) {
        logInfo("order placed for order-1");
        System.out.println("Same logInfo() call, same application code -- but NOW produces machine-parseable JSON, purely from swapping the encoder.");
    }
}
```

How to run: `java JsonEncoderNoCodeChange.java`

`logInfo`'s implementation is byte-for-byte identical to Level 1's. The only change anywhere is which `Encoder` implementation `encoder` is assigned — swapping to `JsonEncoder` immediately changes every single log statement's output format to structured JSON, without touching a single line of the actual logging call sites throughout the application, exactly mirroring how a real `logback-spring.xml` configuration change affects the whole application uniformly.

### Level 3 — Advanced

```java
// File: JsonEncoderWithMdcContext.java -- the JSON encoder AUTOMATICALLY
// includes MDC (Mapped Diagnostic Context) values like correlationId in
// EVERY log entry, with NO change needed at individual logInfo call sites.
import java.util.*;

public class JsonEncoderWithMdcContext {
    static Map<String, String> mdc = new HashMap<>(); // simulates Logback/Log4j2's MDC

    interface Encoder { String encode(String level, String message); }

    static class JsonEncoderWithMdc implements Encoder {
        public String encode(String level, String message) {
            StringBuilder sb = new StringBuilder("{\"level\":\"" + level + "\",\"message\":\"" + message + "\"");
            for (Map.Entry<String, String> entry : mdc.entrySet()) { // AUTOMATICALLY pulls in whatever is currently in MDC
                sb.append(",\"").append(entry.getKey()).append("\":\"").append(entry.getValue()).append("\"");
            }
            return sb.append("}").toString();
        }
    }

    static Encoder encoder = new JsonEncoderWithMdc();

    static void logInfo(String message) { System.out.println(encoder.encode("INFO", message)); } // call site NEVER mentions correlationId directly

    public static void main(String[] args) {
        mdc.put("correlationId", "corr-42"); // set ONCE, e.g. by a filter at the start of request handling

        logInfo("order placed for order-1");   // automatically includes correlationId
        logInfo("payment charged for order-1"); // automatically includes correlationId TOO -- no repeated code

        System.out.println("Neither logInfo() call mentions correlationId directly -- the encoder pulls it from MDC automatically, for EVERY log line.");
    }
}
```

How to run: `java JsonEncoderWithMdcContext.java`

`mdc.put("correlationId", "corr-42")` is set once — standing in for a servlet filter or similar mechanism setting the correlation ID at the start of request handling. Both subsequent `logInfo` calls automatically include `"correlationId":"corr-42"` in their JSON output, entirely through `JsonEncoderWithMdc`'s loop over the current MDC contents — neither individual `logInfo` call, nor `logInfo`'s own implementation, ever references `correlationId` directly, demonstrating that this context propagation happens transparently at the encoder/framework level, not through repeated application-level plumbing at every log statement.

## 6. Walkthrough

Trace `JsonEncoderWithMdcContext.main` in order. **First**, `mdc.put("correlationId", "corr-42")` runs, inserting one entry into the `mdc` map that stands in for the logging framework's thread-scoped diagnostic context.

**Next**, `logInfo("order placed for order-1")` runs, calling `encoder.encode("INFO", "order placed for order-1")`. Inside `JsonEncoderWithMdc.encode`, a `StringBuilder` starts with the level and message fields, then the `for` loop iterates `mdc.entrySet()`, finding the one `correlationId` entry and appending `,"correlationId":"corr-42"` to the output before closing the JSON object.

**Then**, `logInfo("payment charged for order-1")` runs the same way: `encoder.encode` builds a fresh `StringBuilder` for this new message, and the same `for` loop over `mdc.entrySet()` finds the *same* `correlationId` entry (since it was set once and never cleared), automatically including it in this second log entry too.

**Finally**, `main` prints a closing observation: neither `logInfo` call, nor `logInfo`'s own single-line implementation, contains any reference to `correlationId` at all — the field appeared in both JSON outputs purely because the encoder itself reads from the shared `mdc` context every time it runs, meaning any future log statement anywhere in the application would automatically pick up the same context with zero additional code.

```
mdc = {correlationId: "corr-42"}   (set once, e.g. by a request filter)
logInfo("order placed...")   -> encoder reads mdc -> {"level":"INFO","message":"order placed...","correlationId":"corr-42"}
logInfo("payment charged...") -> encoder reads mdc -> {"level":"INFO","message":"payment charged...","correlationId":"corr-42"}
```

## 7. Gotchas & takeaways

> Forgetting to clear MDC values at the end of request handling (or between reused pooled threads) can leak one request's correlation ID into a completely unrelated later request's log lines, especially in thread-pooled server environments — always clear MDC in a `finally` block (or rely on a framework-provided filter that does this automatically) at the end of request processing.

- Logback and Log4j2 can both emit structured JSON output by configuring the appropriate encoder/layout — a pure configuration change requiring no application code modifications.
- This is the concrete mechanism that actually delivers [structured logging](0360-structured-logging.md) in a Spring Boot application, letting every existing `logger.info(...)` call site automatically produce correctly-shaped output.
- Configuring the encoder to automatically include MDC values (correlation ID, trace ID) means every log statement picks up that context transparently, without repeated per-call-site plumbing.
- Always clear MDC context at the end of request handling to avoid leaking one request's context into a later, unrelated request that happens to reuse the same thread.
