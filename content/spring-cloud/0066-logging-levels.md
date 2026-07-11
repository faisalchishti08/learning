---
card: spring-cloud
gi: 66
slug: logging-levels
title: "Logging levels"
---

## 1. What it is

Feign has its own logging configuration, independent of Spring's usual `logging.level.*` mechanism for most beans: a Feign client's log level (`NONE`, `BASIC`, `HEADERS`, `FULL`) controls how much detail about each request and response gets logged, configured either globally, per-client, or via a `Logger.Level` bean — and critically, the Logback/SLF4J logger for the client's package must *also* be set to at least `DEBUG` for anything to actually print, since Feign's own level is a filter on top of that.

```properties
logging.level.com.example.clients.BillingClient=DEBUG

feign.client.config.billing-service.logger-level=full
```

```java
@Bean
Logger.Level feignLoggerLevel() {
    return Logger.Level.BASIC; // applies globally unless overridden per-client
}
```

## 2. Why & when

Feign calls are, from the outside, just method calls on an interface — without logging, there's no visibility into the actual HTTP requests and responses happening underneath. The four levels form a genuine tradeoff between visibility and noise/overhead: `NONE` is silent, `BASIC` logs just the method, URL, and response status/time (cheap, usually enough for production), `HEADERS` adds request/response headers, and `FULL` logs headers, body, and metadata for both request and response — extremely detailed, but expensive and potentially sensitive.

Choose the level based on the situation:

- `NONE` (the default) for production traffic where Feign call logging isn't actively needed — avoids the overhead and log volume entirely.
- `BASIC` for routine production visibility — enough to see call volume, latency, and success/failure per client without excessive log noise.
- `HEADERS` when diagnosing an issue that plausibly involves headers — a missing correlation ID, an authentication header not being sent correctly.
- `FULL` only for deep, temporary debugging of a specific issue, and only when the payloads involved don't contain sensitive data (or with deliberate redaction) — it's the most useful for understanding exactly what went wrong, and the most expensive and risky to leave on.

## 3. Core concept

```
 Feign logger level (BASIC/HEADERS/FULL) is a FILTER on top of the underlying SLF4J/Logback level

 for a log line to actually appear, BOTH must allow it:
   1. the client's SLF4J logger must be at DEBUG (or lower) --  logging.level.com.example.clients.BillingClient=DEBUG
   2. Feign's own configured level must be BASIC or higher for that category of information

 NONE  < BASIC  < HEADERS < FULL   (each level includes everything the previous one logs, plus more)
```

Two separate configuration systems have to agree before any Feign request/response detail actually appears in logs.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Feign log line only appears if both the SLF4J logger level for the client and Feign's own configured logger level allow it, forming an AND gate between two independent settings">
  <rect x="30" y="30" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="140" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">SLF4J logger: DEBUG?</text>
  <text x="140" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">logging.level.com.example...</text>

  <rect x="30" y="110" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="140" y="132" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Feign level: BASIC+?</text>
  <text x="140" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">feign.client.config...logger-level</text>

  <rect x="360" y="70" width="90" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AND</text>

  <rect x="500" y="70" width="120" height="50" rx="8" fill="#1c2430" stroke="#e6edf3" stroke-width="1"/>
  <text x="560" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">log line printed</text>

  <line x1="250" y1="55" x2="358" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a66)"/>
  <line x1="250" y1="135" x2="358" y2="105" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a66)"/>
  <line x1="450" y1="95" x2="498" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a66)"/>

  <defs><marker id="a66" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both gates must be open — neither setting alone is sufficient to produce Feign request/response log output.

## 5. Runnable example

The scenario: model Feign's two-layer logging gate for `BillingClient`. Start with a single combined level (the misconception), then split it into the correct two independent gates, then simulate the four log levels' actual output detail for a real call.

### Level 1 — Basic

A single combined "logging on/off" flag — the incorrect mental model this card corrects.

```java
public class FeignLoggingLevel1 {
    static boolean loggingEnabled = true; // WRONG model: treats logging as one single switch

    static void logCall(String method, String url, int status) {
        if (loggingEnabled) {
            System.out.println(method + " " + url + " -> " + status);
        }
    }

    public static void main(String[] args) {
        logCall("GET", "/invoices/42", 200);
    }
}
```

How to run: `java FeignLoggingLevel1.java`

This treats Feign logging as one single on/off switch — in reality, as the next level shows, there are two independent gates that both have to pass.

### Level 2 — Intermediate

Split into the two correct independent gates: the SLF4J logger level and Feign's own configured level, both required.

```java
public class FeignLoggingLevel2 {
    enum Slf4jLevel { INFO, DEBUG } // simplified -- real SLF4J has more levels
    enum FeignLevel { NONE, BASIC, HEADERS, FULL }

    static Slf4jLevel slf4jLevel = Slf4jLevel.INFO; // NOT set to DEBUG -- a common misconfiguration
    static FeignLevel feignLevel = FeignLevel.FULL;  // Feign itself IS configured verbosely

    static void logCall(String method, String url, int status) {
        boolean slf4jAllows = slf4jLevel == Slf4jLevel.DEBUG;
        boolean feignAllows = feignLevel != FeignLevel.NONE;
        if (slf4jAllows && feignAllows) {
            System.out.println(method + " " + url + " -> " + status);
        } else {
            System.out.println("(nothing logged -- slf4jAllows=" + slf4jAllows + ", feignAllows=" + feignAllows + ")");
        }
    }

    public static void main(String[] args) {
        logCall("GET", "/invoices/42", 200);
        // prints NOTHING, even though feignLevel is FULL -- because the SLF4J logger itself is still at INFO
    }
}
```

How to run: `java FeignLoggingLevel2.java`

Even with `feignLevel` set to the most verbose `FULL`, nothing actually prints, because `slf4jLevel` is still `INFO`, not `DEBUG` — this is exactly the real-world gotcha where someone configures `feign.client.config.billing-service.logger-level=full` and is confused when no logs appear, having forgotten the separate `logging.level.com.example.clients.BillingClient=DEBUG` setting.

### Level 3 — Advanced

Fix the SLF4J level and simulate all four Feign log levels' actual output detail for the same call, showing the genuine escalating verbosity.

```java
public class FeignLoggingLevel3 {
    enum Slf4jLevel { INFO, DEBUG }
    enum FeignLevel { NONE, BASIC, HEADERS, FULL }

    static Slf4jLevel slf4jLevel = Slf4jLevel.DEBUG; // correctly set this time

    static void logCall(FeignLevel feignLevel, String method, String url, int status, long durationMs,
                         String reqHeaders, String reqBody, String respHeaders, String respBody) {
        boolean slf4jAllows = slf4jLevel == Slf4jLevel.DEBUG;
        if (!slf4jAllows || feignLevel == FeignLevel.NONE) return;

        StringBuilder sb = new StringBuilder();
        sb.append(method).append(" ").append(url).append(" -> ").append(status).append(" (").append(durationMs).append("ms)");
        if (feignLevel == FeignLevel.HEADERS || feignLevel == FeignLevel.FULL) {
            sb.append("\n  request headers: ").append(reqHeaders).append("\n  response headers: ").append(respHeaders);
        }
        if (feignLevel == FeignLevel.FULL) {
            sb.append("\n  request body: ").append(reqBody).append("\n  response body: ").append(respBody);
        }
        System.out.println(sb);
    }

    public static void main(String[] args) {
        String reqHeaders = "Authorization: Bearer ***";
        String reqBody = "(none, GET request)";
        String respHeaders = "Content-Type: application/json";
        String respBody = "{\"id\":\"42\",\"amount\":199.99}";

        for (FeignLevel level : FeignLevel.values()) {
            System.out.println("-- level=" + level + " --");
            logCall(level, "GET", "/invoices/42", 200, 45, reqHeaders, reqBody, respHeaders, respBody);
        }
    }
}
```

How to run: `java FeignLoggingLevel3.java`

With `slf4jLevel` correctly set to `DEBUG`, the four Feign levels now produce genuinely escalating output: `NONE` prints nothing at all, `BASIC` prints just the method/URL/status/duration line, `HEADERS` adds the request and response header lines, and `FULL` adds the request and response body content on top of everything `HEADERS` already includes — exactly matching each level's documented scope.

## 6. Walkthrough

Trace the loop in Level 3.

1. For `FeignLevel.NONE`, `logCall` checks `!slf4jAllows || feignLevel == NONE` — `slf4jAllows` is `true`, but `feignLevel == NONE` is also `true`, so the `||` makes the whole condition `true`, and the method returns immediately without printing anything.
2. For `FeignLevel.BASIC`, the early-return condition is `false` (neither clause is true), so execution continues. The `StringBuilder` appends the method, URL, status, and duration. Neither the `HEADERS`-or-`FULL` check nor the `FULL`-only check matches `BASIC`, so nothing further is appended — the printed line is exactly the one-line summary.
3. For `FeignLevel.HEADERS`, the base line is built the same way, and this time `feignLevel == HEADERS || feignLevel == FULL` evaluates `true` (first clause), so the request and response header lines are appended. The `FULL`-only body check still doesn't match, so bodies are excluded.
4. For `FeignLevel.FULL`, the base line and the headers are appended exactly as for `HEADERS` (since the same `HEADERS || FULL` check passes), and additionally the `feignLevel == FULL` check now passes too, appending both the request and response body content — the single most detailed, complete log entry of the four.
5. The escalating output directly demonstrates each level's real, documented meaning: each level is a strict superset of the previous one's detail, letting an operator dial verbosity up only as far as actually needed for a given debugging task.

```
NONE:    (nothing printed)
BASIC:   GET /invoices/42 -> 200 (45ms)
HEADERS: GET /invoices/42 -> 200 (45ms)
           request headers: ...
           response headers: ...
FULL:    GET /invoices/42 -> 200 (45ms)
           request headers: ...
           response headers: ...
           request body: ...
           response body: ...
```

## 7. Gotchas & takeaways

> **Gotcha:** setting a Feign client's `logger-level` to `FULL` without also raising the corresponding SLF4J/Logback logger to `DEBUG` produces silent, confusing "nothing logs" behavior — exactly what Level 2 demonstrated. This is one of the most common real-world points of confusion when first configuring Feign logging; always check both settings together.

- Feign logging requires two independent settings to agree — the SLF4J/Logback logger level for the client class/package, and Feign's own configured `Logger.Level` — missing either one means no log output regardless of how the other is set.
- `FULL` logs complete request and response bodies, which can include sensitive data (auth tokens, PII, financial details) — never leave it enabled in production without deliberate consideration of what's actually being logged and where those logs are stored.
- `BASIC` is usually the right default for routine production observability — enough to see per-client call volume, latency, and success/failure without excessive log volume or sensitive-data exposure risk.
- Per-client configuration (`feign.client.config.billing-service.logger-level=full`) lets one specific client be debugged verbosely while every other client in the same application stays at its normal, quieter level — no need to enable verbose logging application-wide just to investigate one client's behavior.
