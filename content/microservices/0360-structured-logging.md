---
card: microservices
gi: 360
slug: structured-logging
title: "Structured logging"
---

## 1. What it is

**Structured logging** means writing log entries as machine-parseable structured data (typically JSON), with distinct, consistently-named fields — `timestamp`, `level`, `service`, `correlationId`, `message`, and any relevant context as additional fields — instead of free-form text sentences that a human wrote for other humans to read. A structured log line looks like `{"timestamp": "...", "level": "ERROR", "service": "order-service", "correlationId": "corr-abc", "orderId": "order-1", "message": "payment failed"}` rather than `"ERROR: payment failed for order order-1 (corr-abc) at ..."`.

## 2. Why & when

Free-form text logs are easy to write and easy for a human to read one at a time, but they're expensive and unreliable to search, filter, and aggregate at scale — finding "every error for this specific order ID, across every service" in plain text logs means writing fragile regular expressions that break the moment someone tweaks a log message's wording. Structured logs solve this by making every field independently queryable: a log aggregation system (Elasticsearch, Loki, a cloud logging service) can filter on `correlationId = "corr-abc"` or `orderId = "order-1"` reliably, regardless of how the human-readable `message` field is worded, because the fields are data, not embedded substrings of a sentence.

Adopt structured logging as the default for any service in a microservices system — this is essentially a baseline requirement for the [three pillars](0349-three-pillars-logs-metrics-traces.md) of observability to actually work together at scale, since correlating logs by [correlation ID](0351-correlation-ids-request-ids.md) or trace ID depends on those identifiers being reliably, precisely extractable, which structured fields provide and free-text parsing does not.

## 3. Core concept

Every log entry is emitted as a structured record (JSON is the common choice) with a consistent, agreed set of standard fields present on every line (timestamp, level, service name, correlation/trace ID) plus whatever additional context fields are relevant to that specific event — never embedding identifiers or values *inside* the human-readable message string where they'd be hard to reliably extract.

```java
Map<String, Object> logEntry = Map.of(
    "timestamp", Instant.now().toString(), "level", "ERROR", "service", "order-service",
    "correlationId", correlationId, "orderId", orderId, "message", "payment failed");
// serialized to JSON, one line per entry
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unstructured text log on the left is hard to reliably parse with a regex; structured JSON log on the right has explicit, independently queryable fields for timestamp, level, correlationId, orderId, and message">
  <rect x="20" y="20" width="280" height="130" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="45" fill="#f85149" font-size="10.5" text-anchor="middle" font-family="sans-serif">Unstructured text</text>
  <text x="160" y="70" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"ERROR: payment failed</text>
  <text x="160" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">for order order-1 (corr-abc)"</text>
  <text x="160" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fragile regex needed to search</text>

  <rect x="340" y="20" width="280" height="130" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="480" y="45" fill="#3fb950" font-size="10.5" text-anchor="middle" font-family="sans-serif">Structured JSON</text>
  <text x="480" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">level: "ERROR"</text>
  <text x="480" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">correlationId: "corr-abc"</text>
  <text x="480" y="96" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orderId: "order-1"</text>
  <text x="480" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">each field directly queryable</text>
</svg>

Structured fields are reliably and independently queryable; free-text sentences require fragile parsing that breaks with wording changes.

## 5. Runnable example

Scenario: a payment-failure event, first logged as free text (fragile to search reliably), then rebuilt as structured JSON-style entries with consistent fields, and finally extended to show a realistic query against structured logs finding exactly the right entries, something the free-text version can't do reliably.

### Level 1 — Basic

```java
// File: UnstructuredTextLogging.java -- logs as free-form sentences;
// extracting a specific field back OUT requires fragile string parsing.
import java.util.*;
import java.util.regex.*;

public class UnstructuredTextLogging {
    static List<String> logs = new ArrayList<>();

    static void logPaymentFailure(String correlationId, String orderId, String reason) {
        logs.add("ERROR: payment failed for order " + orderId + " (corr=" + correlationId + "): " + reason);
    }

    static Optional<String> extractOrderId(String logLine) { // FRAGILE: depends EXACTLY on the message's wording
        Matcher m = Pattern.compile("for order (\\S+)").matcher(logLine);
        return m.find() ? Optional.of(m.group(1)) : Optional.empty();
    }

    public static void main(String[] args) {
        logPaymentFailure("corr-1", "order-1", "card declined");
        logPaymentFailure("corr-2", "order-2", "insufficient funds");

        System.out.println(logs);
        System.out.println("Extracted orderId from line 1: " + extractOrderId(logs.get(0)));
        System.out.println("This regex BREAKS the moment anyone rewords the log message, e.g. 'for order-id' instead of 'for order'.");
    }
}
```

How to run: `java UnstructuredTextLogging.java`

`extractOrderId` works, but only because its regex happens to exactly match the current wording of `logPaymentFailure`'s message. If a future code change rewords the message even slightly (say, to "for order-id" instead of "for order"), this extraction silently breaks — a fragility that's easy to introduce accidentally and hard to notice until a search stops returning results.

### Level 2 — Intermediate

```java
// File: StructuredJsonLogging.java -- every field is EXPLICIT and
// independently accessible; no parsing of a human sentence required at all.
import java.util.*;

public class StructuredJsonLogging {
    record LogEntry(String level, String service, String correlationId, String orderId, String reason, String message) {}
    static List<LogEntry> logs = new ArrayList<>();

    static void logPaymentFailure(String correlationId, String orderId, String reason) {
        logs.add(new LogEntry("ERROR", "payment-service", correlationId, orderId, reason, "payment failed"));
    }

    public static void main(String[] args) {
        logPaymentFailure("corr-1", "order-1", "card declined");
        logPaymentFailure("corr-2", "order-2", "insufficient funds");

        System.out.println(logs);
        System.out.println("orderId for the first entry: " + logs.get(0).orderId()
                + " -- accessed DIRECTLY as a field, no parsing, no regex, NEVER breaks due to message wording changes.");
    }
}
```

How to run: `java StructuredJsonLogging.java`

`logPaymentFailure` now builds an explicit `LogEntry` record with `orderId`, `correlationId`, and `reason` as their own distinct fields, entirely separate from the free-text `message`. Retrieving `orderId` is a direct field access (`logs.get(0).orderId()`), with no parsing involved at all — changing the wording of `message` in the future has zero effect on this access, unlike Level 1's regex-based extraction.

### Level 3 — Advanced

```java
// File: QueryStructuredLogsReliably.java -- runs a REALISTIC query
// against structured logs (find every ERROR for a specific correlation
// ID, across potentially many entries and fields), demonstrating exactly
// the kind of reliable, field-based search structured logging enables.
import java.util.*;
import java.util.stream.*;

public class QueryStructuredLogsReliably {
    record LogEntry(String level, String service, String correlationId, String orderId, String message) {}
    static List<LogEntry> logs = new ArrayList<>();

    static void log(String level, String service, String correlationId, String orderId, String message) {
        logs.add(new LogEntry(level, service, correlationId, orderId, message));
    }

    public static void main(String[] args) {
        String targetCorrelationId = "corr-42";

        log("INFO", "order-service", targetCorrelationId, "order-1", "checkout received");
        log("INFO", "order-service", "corr-99", "order-2", "checkout received"); // DIFFERENT request, different correlationId
        log("INFO", "payment-service", targetCorrelationId, "order-1", "charging card");
        log("ERROR", "payment-service", targetCorrelationId, "order-1", "card declined");
        log("INFO", "order-service", targetCorrelationId, "order-1", "checkout failed, notifying customer");
        log("ERROR", "inventory-service", "corr-99", "order-2", "out of stock"); // UNRELATED error, different request

        // A realistic, RELIABLE query: every log entry for ONE specific request, across ALL services, in order.
        List<LogEntry> requestTimeline = logs.stream()
                .filter(entry -> entry.correlationId().equals(targetCorrelationId))
                .toList();

        System.out.println("Full timeline for correlationId=" + targetCorrelationId + " (across ALL services):");
        requestTimeline.forEach(e -> System.out.println("  [" + e.service() + "] " + e.level() + ": " + e.message()));

        long errorCountForThisRequest = requestTimeline.stream().filter(e -> e.level().equals("ERROR")).count();
        System.out.println("Errors specifically for THIS request: " + errorCountForThisRequest
                + " -- reliably found by filtering on the correlationId FIELD, unaffected by any of the other unrelated log entries.");
    }
}
```

How to run: `java QueryStructuredLogsReliably.java`

The query `logs.stream().filter(entry -> entry.correlationId().equals(targetCorrelationId))` reliably isolates exactly the four log entries belonging to `"corr-42"`'s request, across `order-service` and `payment-service`, while correctly excluding the two entries belonging to the unrelated `"corr-99"` request — including its own `ERROR` entry, which has nothing to do with the request being investigated. This kind of precise, cross-service, field-based filtering is exactly what structured logging is designed to make reliable, at any log volume, without depending on message wording at all.

## 6. Walkthrough

Trace `QueryStructuredLogsReliably.main` in order. **First**, six `log` calls populate `logs`: four tagged with `correlationId="corr-42"` (spanning `order-service` and `payment-service`, including one `ERROR`), and two tagged with `correlationId="corr-99"` (an unrelated request, also including its own `ERROR`).

**Next**, the stream filter `entry -> entry.correlationId().equals(targetCorrelationId)` runs against all six entries. For each of the four `"corr-42"` entries, the equality check is `true`, so they're included in `requestTimeline`. For each of the two `"corr-99"` entries, the check is `false`, so they're excluded — critically, this exclusion applies even to the `"corr-99"` `ERROR` entry, which never appears in `requestTimeline` despite being an error, because it belongs to a different request entirely.

**Then**, `requestTimeline.forEach(...)` prints all four matching entries in their original insertion order, showing the full cross-service timeline for `"corr-42"`'s request: a checkout received, a card charge attempted, a card decline error, and a failure notification.

**Finally**, `errorCountForThisRequest` filters `requestTimeline` (already narrowed to just this request) down to entries where `level().equals("ERROR")`, finding exactly `1` — the card-decline error — correctly excluding `"corr-99"`'s unrelated `ERROR` from this count, since that entry was never part of `requestTimeline` in the first place.

```
logs: [corr-42: INFO, corr-99: INFO, corr-42: INFO, corr-42: ERROR, corr-42: INFO, corr-99: ERROR]
filter(correlationId == "corr-42") -> requestTimeline: [4 entries, spanning order-service + payment-service]
count(level == "ERROR") within requestTimeline -> 1  (correctly excludes corr-99's unrelated ERROR)
```

## 7. Gotchas & takeaways

> Mixing structured and unstructured logging within the same service — some log statements emitting JSON, others still emitting free-text sentences — undermines the whole benefit, since any query or aggregation tool relying on structured fields will simply miss the unstructured entries entirely, creating gaps that are easy to overlook until an investigation comes up mysteriously incomplete.

- Structured logging emits each log entry as machine-parseable data (typically JSON) with consistent, named fields, rather than a free-form sentence a human wrote for other humans.
- This makes filtering and aggregating logs by any field — especially a [correlation ID](0351-correlation-ids-request-ids.md) or trace ID — reliable and precise, unlike text-parsing approaches that break whenever message wording changes.
- Every log entry should include a baseline set of standard fields (timestamp, level, service, correlation/trace ID) plus event-specific context fields, never embedding identifiers only inside the free-text message.
- This is foundational infrastructure for the [three pillars](0349-three-pillars-logs-metrics-traces.md) of observability to work together at scale — correlating logs, metrics, and traces depends on reliably extractable, structured identifiers.
