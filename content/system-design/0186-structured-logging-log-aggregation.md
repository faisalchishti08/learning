---
card: system-design
gi: 186
slug: structured-logging-log-aggregation
title: Structured logging & log aggregation
---

## 1. What it is

**Structured logging** writes log entries as machine-parseable data (typically JSON), with consistent named fields (`timestamp`, `level`, `service`, `userId`, `message`), instead of a free-form human-readable sentence. **Log aggregation** collects these structured logs from every server and service instance into one centralized, searchable store (like Elasticsearch or a managed logging service), so you can search and filter across your whole fleet at once, instead of SSH-ing into individual machines to grep local log files.

## 2. Why & when

A plain-text log line like `"User 17 failed to log in at 10:32"` is easy for a human to read once, but hard to reliably search, filter, or aggregate across millions of similar lines — you cannot cleanly query "show me every failed login for user 17 in the last hour" without fragile text parsing. Structured logging with consistent field names turns every log entry into a queryable record instead. Log aggregation is essential the moment you have more than one server: without it, diagnosing an issue means manually checking logs on every individual machine that might have handled the relevant request, which does not scale. Use both together for any system running more than a handful of instances, or where operational log analysis is a regular need.

## 3. Core concept

- **Structured fields, not free text:** every log entry has a level (`INFO`, `ERROR`), a timestamp, a service name, and any relevant contextual fields (a user ID, an order ID, a request ID) — all as separate, named fields, not embedded inside a sentence.
- **Correlation ID / request ID:** a unique ID generated at the start of a request and included in every log line produced while handling it, letting you retrieve every log entry related to one specific request across every service it touched — the foundation [distributed tracing](0188-distributed-tracing-correlation-ids.md) builds on.
- **Log levels used consistently:** `DEBUG` for fine-grained diagnostic detail, `INFO` for normal operational events, `WARN` for recoverable problems, `ERROR` for failures needing attention — using these consistently is what makes filtering by severity actually useful.
- **Centralized ingestion pipeline:** logs are shipped (via an agent, or written directly) from every instance into a central aggregation system, which indexes them for fast search across the whole fleet.
- **Retention and cost tradeoff:** storing every log line forever is expensive; most systems apply retention policies (keep detailed logs for days, summarized/sampled data for longer) similar to [storage tiering](0157-hot-warm-cold-storage-tiers.md).

## 4. Diagram

```
   service-A               service-B               service-C
      |                       |                       |
      | log: {ts, level,      | log: {ts, level,      | log: {ts, level,
      |  requestId: "r1",     |  requestId: "r1",     |  requestId: "r1",
      |  message: "..."}      |  message: "..."}      |  message: "..."}
      |                       |                       |
      +-----------------------+-----------------------+
                              |
                    centralized log aggregator (indexed, searchable)
                              |
              query: "requestId = r1" -> every log line from EVERY
                                          service that touched this
                                          one request, in order
```
*Caption: every log entry carries the same request ID as it flows through multiple services, letting a single query reconstruct the full story of one request.*

## 5. Runnable example

**Level 1 — Basic.** Write a structured log entry as a JSON-shaped record instead of a free-text sentence.

**Level 2 — Include a correlation ID across multiple services.** Tag every log line from one request with the same ID.

**Level 3 — Query the aggregated logs by correlation ID and by severity.** Reconstruct a single request's full story across services.

```java
// StructuredLoggingDemo.java
import java.util.*;

public class StructuredLoggingDemo {

    static class LogEntry {
        final long timestamp;
        final String level, service, requestId, message;
        LogEntry(long ts, String level, String service, String requestId, String message) {
            this.timestamp = ts; this.level = level; this.service = service; this.requestId = requestId; this.message = message;
        }
        public String toString() {
            return "{ts=" + timestamp + ", level=" + level + ", service=" + service + ", requestId=" + requestId + ", message=\"" + message + "\"}";
        }
    }

    // Level 1: the centralized log aggregator - a simple, growing, queryable list.
    static List<LogEntry> aggregatedLogs = new ArrayList<>();

    static void log(long ts, String level, String service, String requestId, String message) {
        LogEntry entry = new LogEntry(ts, level, service, requestId, message);
        aggregatedLogs.add(entry); // Level 1: shipped to the central aggregator, not left on a local disk
    }

    // Level 3: query by correlation ID - reconstruct one request's full story across every service.
    static List<LogEntry> queryByRequestId(String requestId) {
        List<LogEntry> results = new ArrayList<>();
        for (LogEntry entry : aggregatedLogs) if (entry.requestId.equals(requestId)) results.add(entry);
        results.sort((a, b) -> Long.compare(a.timestamp, b.timestamp));
        return results;
    }

    static List<LogEntry> queryByLevel(String level) {
        List<LogEntry> results = new ArrayList<>();
        for (LogEntry entry : aggregatedLogs) if (entry.level.equals(level)) results.add(entry);
        return results;
    }

    public static void main(String[] args) {
        // Level 2: the SAME requestId, "r1", flows across three different services handling one user request.
        String requestId = "r1";
        log(100, "INFO", "api-gateway", requestId, "received request for /checkout");
        log(105, "INFO", "orders-service", requestId, "creating order for user-17");
        log(110, "WARN", "payments-service", requestId, "payment provider responded slowly (2100ms)");
        log(115, "INFO", "payments-service", requestId, "payment charged successfully");
        log(120, "INFO", "api-gateway", requestId, "returned 200 OK to client");

        // An UNRELATED request, "r2", also logged around the same time - must not get mixed into r1's story.
        log(102, "ERROR", "orders-service", "r2", "failed to create order: inventory service timeout");

        System.out.println("all logs for requestId=r1, in order:");
        for (LogEntry entry : queryByRequestId("r1")) System.out.println("  " + entry);

        System.out.println("all WARN-or-worse logs across the whole fleet (level=WARN):");
        for (LogEntry entry : queryByLevel("WARN")) System.out.println("  " + entry);
    }
}
```

**How to run:** save as `StructuredLoggingDemo.java`, then run `java StructuredLoggingDemo.java`.

## 6. Walkthrough

1. Each call to `log(...)` constructs a `LogEntry` with explicit, separate fields (`level`, `service`, `requestId`, `message`) and appends it to `aggregatedLogs` — this models every log line being structured data from the moment it is created, and immediately shipped to a central store rather than staying on a per-service local disk.
2. Five log entries are written with `requestId = "r1"`, from three different "services" (`api-gateway`, `orders-service`, `payments-service`), each at a slightly later timestamp — modeling one real user request flowing through multiple services, each contributing its own log lines to the same shared aggregator.
3. A sixth entry uses a different `requestId`, `"r2"`, representing a completely unrelated request that happens to be logged around the same time — this tests that querying will not accidentally mix unrelated requests together.
4. `queryByRequestId("r1")` filters `aggregatedLogs` down to only entries whose `requestId` equals `"r1"`, then sorts by `timestamp`; the result is exactly the five `r1` entries, in chronological order, correctly excluding the `r2` entry entirely — reconstructing this one request's complete, ordered story across all three services from a single query.
5. `queryByLevel("WARN")` filters instead by severity, finding only the single `payments-service` entry about the slow provider response — demonstrating a completely different, orthogonal way to slice the same aggregated log data, impossible to do reliably against unstructured free-text log lines.

## 7. Gotchas & takeaways

> Gotcha: generating the correlation ID *inside* each individual service, rather than once at the entry point and passing it through every downstream call, produces a different, unrelated ID per service for what is really one logical request — defeating the entire purpose of correlation. The ID must be generated (or received from an incoming header) at the very first point of entry, and explicitly propagated to every downstream call from there.

- Structured logging turns log lines into queryable, filterable data instead of free text that only a human can meaningfully read.
- A correlation/request ID, propagated consistently across every service a request touches, is what lets you reconstruct one request's full story from aggregated logs.
- Centralized aggregation is what makes cross-fleet log search practical at all, once a system runs more than a handful of instances.
- Related concepts: [Distributed tracing & correlation IDs](0188-distributed-tracing-correlation-ids.md) (the more structured, timing-aware evolution of this same correlation idea), [Metrics (counters, gauges, histograms)](0187-metrics-counters-gauges-histograms.md) (a complementary observability signal, aggregated numerically rather than searched as individual events), [Micrometer Tracing (OpenTelemetry)](0193-micrometer-tracing-opentelemetry.md) (a concrete Java implementation of correlation-ID propagation).
