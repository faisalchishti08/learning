---
card: spring-cloud
gi: 107
slug: correlation-ids-in-logs
title: "Correlation IDs in logs"
---

## 1. What it is

Micrometer Tracing automatically inserts the current `traceId` and `spanId` into every log statement's MDC (Mapped Diagnostic Context) for the duration of an active span, and Spring Boot's default log pattern includes those values in every log line's output — so ordinary `log.info(...)` calls, with no special tracing-aware code, automatically carry a searchable correlation identifier linking that log line to its exact place in a distributed trace.

```
2026-07-11T10:15:32.104 INFO [order-service,80f198ee56343ba864fe8b2a57d3eff7,e457b5a2e4d86bd1] 1 --- [nio-8080-exec-1] c.e.OrderService : processing order 42
```

```properties
logging.pattern.level=%5p [${spring.application.name},%X{traceId},%X{spanId}]
```

## 2. Why & when

A trace's span tree (from an earlier card) shows *timing and structure* — which services were involved, how long each took — but the actual diagnostic detail of *what happened* (an exception's message and stack trace, a specific business decision that was made, a validation failure) still lives in each service's own application logs, written by ordinary `log.info`/`log.error` calls that have no inherent connection to any specific trace. Correlation IDs bridge this gap: because the current trace's `traceId` and `spanId` are automatically available in MDC while a span is active, and Spring Boot's log pattern renders them into every log line, searching a centralized log aggregator (Splunk, ELK, Loki) for one specific `traceId` instantly surfaces every log line, from every service, that was written while handling that one particular trace — turning otherwise-disconnected per-service logs into a single, chronologically-correlated view of one request's full journey.

Reach for correlation-ID-aware log analysis when:

- Debugging a specific failed or slow request whose `traceId` is already known (from a trace viewer, an error report, or a support ticket) — searching centralized logs for that exact `traceId` immediately surfaces every relevant log line across every service it touched, without manually guessing which services were involved or scanning each one's logs separately.
- Correlating a business-level log message (a specific validation error, a specific pricing decision) with the broader distributed trace it occurred within — the shared `traceId` is what makes that correlation possible without any custom application-level correlation logic.
- Building alerting or analysis tooling that needs to connect "this log pattern occurred" with "in this specific trace, at this specific span" — the MDC-injected `traceId`/`spanId` pair is the join key between raw application logs and the structured trace data stored in a tracing backend.

## 3. Core concept

```
 span becomes active (auto-instrumentation, or a manual Tracer.withSpan call)
        |
        v
 Micrometer Tracing populates MDC:
   MDC.put("traceId", "80f198ee...")
   MDC.put("spanId",  "e457b5a2...")
        |
        v
 EVERY log.info/error/warn call during this span's lifetime automatically includes these values
 (the logging framework's pattern layout renders %X{traceId} / %X{spanId} into the output)
        |
        v
 span ends -> MDC entries cleared/restored (so unrelated later log lines don't inherit a stale traceId)
```

No application code needs to explicitly pass a `traceId` into a `log.info` call — the MDC population and pattern rendering happen entirely outside the call site, purely because a span happens to be active at that moment.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="While a span is active every ordinary log statement automatically has the traceId and spanId injected via MDC so a log search across many services for one traceId reconstructs every log line belonging to one request">
  <rect x="20" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">active span</text>
  <text x="110" y="56" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">MDC: traceId, spanId</text>

  <rect x="250" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">log.info("processing order")</text>
  <text x="340" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">pattern auto-includes %X{traceId}</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="550" y="48" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">centralized log store</text>

  <defs><marker id="a107" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a107)"/>
  <line x1="430" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a107)"/>
  <text x="320" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">search "traceId=80f198ee..." across ALL services' logs -&gt; every line for THIS request</text>
</svg>

MDC injection is invisible at the call site — `log.info` never mentions tracing, yet its output always carries the current trace's identifiers.

## 5. Runnable example

The scenario: model MDC-based log correlation — a thread-local-style context automatically injected into every log line while a span is active, then queried across multiple services' simulated log output to reconstruct one request's full story. Start with plain, uncorrelated logging, then add MDC injection, then simulate multiple interleaved traces across services and demonstrate searching by `traceId` cleanly separates them.

### Level 1 — Basic

Plain logging with no correlation — the baseline problem correlation IDs solve.

```java
import java.util.*;

public class CorrelationIdsLevel1 {
    static List<String> logOutput = new ArrayList<>();

    static void log(String message) {
        logOutput.add(message); // no trace context attached AT ALL
    }

    public static void main(String[] args) {
        log("processing order 42");
        log("payment charged for order 42");
        log("processing order 99"); // a DIFFERENT, unrelated request's log line, indistinguishable at a glance
        log("payment charged for order 99");

        for (String line : logOutput) System.out.println(line);
    }
}
```

How to run: `java CorrelationIdsLevel1.java`

Nothing in this output distinguishes which log lines belong to the same request — a human reader can infer it from the order text, but a program (or a log search across thousands of interleaved lines from many concurrent requests) has no reliable identifier to group by.

### Level 2 — Intermediate

Add MDC-style context: a per-thread map automatically consulted by `log`, populated once per "span" and cleared afterward.

```java
import java.util.*;

public class CorrelationIdsLevel2 {
    static Map<String, String> mdc = new HashMap<>(); // stands in for a real MDC (thread-local in practice)
    static List<String> logOutput = new ArrayList<>();

    static void log(String message) {
        String traceId = mdc.getOrDefault("traceId", "-");
        logOutput.add("[traceId=" + traceId + "] " + message); // automatically injected, no call-site change needed
    }

    static void withSpan(String traceId, Runnable work) {
        mdc.put("traceId", traceId);
        try {
            work.run();
        } finally {
            mdc.remove("traceId"); // cleared when the span ends -- prevents leaking into unrelated later logs
        }
    }

    public static void main(String[] args) {
        withSpan("trace-A", () -> {
            log("processing order 42");
            log("payment charged for order 42");
        });

        withSpan("trace-B", () -> {
            log("processing order 99");
            log("payment charged for order 99");
        });

        for (String line : logOutput) System.out.println(line);
    }
}
```

How to run: `java CorrelationIdsLevel2.java`

Every `log` call inside the first `withSpan("trace-A", ...)` block automatically carries `traceId=trace-A`, and every call inside the second block automatically carries `traceId=trace-B` — the `log` method's own code never changed between the two calls; only the ambient MDC context differed, exactly mirroring how the same `log.info(...)` call site in a real application produces differently-tagged output depending purely on which span happens to be active at the moment it runs.

### Level 3 — Advanced

Simulate multiple services, each writing to their own log stream, with interleaved log lines from concurrent traces — then reconstruct one full request's cross-service story purely by searching for its `traceId`.

```java
import java.util.*;

public class CorrelationIdsLevel3 {
    static Map<String, String> mdc = new HashMap<>();
    static List<String> centralizedLogStore = new ArrayList<>(); // models one aggregated log index across ALL services

    static void log(String service, String message) {
        String traceId = mdc.getOrDefault("traceId", "-");
        centralizedLogStore.add("service=" + service + " traceId=" + traceId + " msg=\"" + message + "\"");
    }

    static void withSpan(String traceId, Runnable work) {
        mdc.put("traceId", traceId);
        try { work.run(); } finally { mdc.remove("traceId"); }
    }

    static List<String> searchByTraceId(String traceId) {
        return centralizedLogStore.stream().filter(line -> line.contains("traceId=" + traceId)).toList();
    }

    public static void main(String[] args) {
        // two DIFFERENT requests, interleaved across TWO services, exactly as concurrent traffic would produce
        withSpan("trace-A", () -> log("gateway", "received order request"));
        withSpan("trace-B", () -> log("gateway", "received order request"));
        withSpan("trace-A", () -> log("order-service", "validated order 42"));
        withSpan("trace-B", () -> log("order-service", "validated order 99"));
        withSpan("trace-A", () -> log("payment-service", "charged order 42"));
        withSpan("trace-B", () -> log("payment-service", "charged order 99"));

        System.out.println("-- full log for trace-A, reconstructed across all 3 services --");
        for (String line : searchByTraceId("trace-A")) System.out.println(line);
    }
}
```

How to run: `java CorrelationIdsLevel3.java`

`searchByTraceId("trace-A")` filters the interleaved, six-line `centralizedLogStore` down to exactly the three lines belonging to `trace-A` — one from `gateway`, one from `order-service`, one from `payment-service` — cleanly separated from `trace-B`'s three lines despite both traces' log lines having been interleaved and written in the order the (simulated) concurrent requests actually executed; this is precisely the operation a real log aggregator performs when an operator searches for one `traceId` across a fleet's combined log output.

## 6. Walkthrough

Trace `searchByTraceId("trace-A")` in Level 3.

1. Before this call, `centralizedLogStore` holds six lines total, in the exact interleaved order they were written: `gateway/trace-A`, `gateway/trace-B`, `order-service/trace-A`, `order-service/trace-B`, `payment-service/trace-A`, `payment-service/trace-B`.
2. `searchByTraceId("trace-A")` calls `.stream().filter(line -> line.contains("traceId=trace-A"))` over that full list.
3. The filter predicate evaluates `true` for exactly three lines — the `gateway`, `order-service`, and `payment-service` lines that were written while `mdc.get("traceId")` was `"trace-A"` — and `false` for the other three, which were written while it was `"trace-B"`.
4. `.toList()` collects the three matching lines into a new list, in their original relative order (`gateway` first, then `order-service`, then `payment-service`) — this ordering is preserved because `filter` doesn't reorder elements, it only removes non-matching ones, so the resulting three lines still read in the same chronological/causal sequence the real request actually executed in.
5. The `for` loop prints exactly those three lines — a clean, complete, cross-service reconstruction of `trace-A`'s full journey, with `trace-B`'s interleaved lines entirely absent from the output, despite both traces having been logged concurrently and mixed together in the raw store.

```
centralizedLogStore (raw, interleaved):
  gateway/trace-A, gateway/trace-B, order-service/trace-A, order-service/trace-B, payment-service/trace-A, payment-service/trace-B

searchByTraceId("trace-A") filters to:
  gateway/trace-A, order-service/trace-A, payment-service/trace-A     <- trace-B lines correctly excluded
```

## 7. Gotchas & takeaways

> **Gotcha:** MDC context is thread-local by nature — if application code hands work off to a different thread (a `CompletableFuture`, a thread pool executor, an async `@Async` method) without deliberately propagating the current MDC context to that new thread, log lines written from within that new thread lose the `traceId`/`spanId` correlation entirely, appearing as `traceId=-` (or whatever the uncorrelated default renders as) even though they're genuinely part of the same logical request. Async work needs explicit MDC (and trace context) propagation, which Micrometer Tracing provides hooks for, but which isn't automatic across arbitrary thread boundaries.

- Correlation IDs require zero changes to ordinary `log.info`/`log.error` call sites — the injection happens entirely through MDC population (driven by span lifecycle) and the log pattern's rendering of `%X{traceId}`/`%X{spanId}`, both configured once, globally, rather than per call site.
- The practical payoff is searchability: one `traceId` search across a centralized log aggregator instantly reconstructs a complete, cross-service, chronologically-ordered view of one specific request, without needing to know in advance which services that request touched.
- MDC is cleared when a span ends specifically to prevent a stale `traceId` from leaking into unrelated log lines written after that span's work has finished — proper cleanup (the `finally` block in the examples above) is essential to keeping correlation accurate rather than misleading.
- Asynchronous or thread-hopping code paths are the primary place correlation silently breaks — verifying that MDC/trace context propagation is correctly configured for any `@Async`, thread pool, or reactive-scheduler boundary in an application is worth deliberate attention rather than assuming it "just works" everywhere by default.
