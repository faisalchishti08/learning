---
card: system-design
gi: 188
slug: distributed-tracing-correlation-ids
title: Distributed tracing & correlation IDs
---

## 1. What it is

**Distributed tracing** tracks a single request as it flows through multiple services, recording a **span** for each unit of work (a service call, a database query) with its start time, duration, and a link to its parent span, all sharing one **trace ID** for the whole request. A **correlation ID** is the simpler foundation this builds on: a single ID attached to every [log](0186-structured-logging-log-aggregation.md) line and passed along to every downstream call, so you can find every log entry for one request — tracing adds structured timing and parent-child relationships on top of that same idea.

## 2. Why & when

In a microservices system, a single user-facing request might touch five, ten, or more separate services before returning a response. When something is slow or fails, you need to know *which* of those services was the actual bottleneck or point of failure — a correlation ID lets you find the relevant log lines, but distributed tracing goes further, showing you the exact timing breakdown: how long each service spent, which calls happened in parallel versus in sequence, and where the time actually went. Use correlation IDs as a baseline for any system with more than one service; add full distributed tracing once you need to understand *timing* relationships across services, not just find related log lines.

## 3. Core concept

- **Trace ID:** one ID generated for the entire request, shared by every span within it, letting you retrieve the complete trace as a single unit.
- **Span:** a single unit of work within the trace — one service call, one database query — with its own start time, duration, and a `spanId`; it also records its `parentSpanId`, linking it to whatever span triggered it.
- **Trace context propagation:** the trace ID and current span ID must be passed along with every outgoing call (typically as HTTP headers) so the next service can create its own child span linked to the correct parent, rather than starting an unrelated, disconnected trace.
- **Waterfall visualization:** a trace is commonly displayed as a waterfall diagram, showing each span as a horizontal bar positioned by its start time and sized by its duration, immediately revealing which spans ran in parallel and which one was the slowest.
- **Sampling:** tracing every single request in a very high-traffic system can be expensive to store; many systems sample only a fraction of requests (e.g. 1%) for full tracing, while still logging every request at a lighter level.

## 4. Diagram

```
   trace-id: t1

   span: api-gateway         [=========================================] 0-500ms
     span: orders-service      [==========================]              50-350ms
       span: db-query-orders      [======]                                60-110ms
       span: payments-service        [==================]                140-330ms
         span: db-query-payments        [====]                            160-200ms

   waterfall reveals: payments-service (190ms) is the actual bottleneck,
   NOT the top-level api-gateway call itself
```
*Caption: nested spans, all sharing one trace ID, show exactly how much time each service and sub-call consumed, and which ones overlapped.*

## 5. Runnable example

**Level 1 — Basic.** Generate a trace ID and create a span with a start and end time.

**Level 2 — Propagate the trace context to child spans.** Nest spans with parent-child links across simulated service calls.

**Level 3 — Build a waterfall view and identify the bottleneck span.** Find the span that consumed the most of the total request time.

```java
// DistributedTracingDemo.java
import java.util.*;

public class DistributedTracingDemo {

    static class Span {
        final String traceId, spanId, parentSpanId, serviceName;
        final long startMs;
        long endMs = -1;
        Span(String traceId, String spanId, String parentSpanId, String serviceName, long startMs) {
            this.traceId = traceId; this.spanId = spanId; this.parentSpanId = parentSpanId;
            this.serviceName = serviceName; this.startMs = startMs;
        }
        long durationMs() { return endMs - startMs; }
    }

    static List<Span> allSpans = new ArrayList<>();
    static int spanCounter = 0;

    // Level 1 & 2: start a new span, linked to its parent (null for the root span).
    static Span startSpan(String traceId, String parentSpanId, String serviceName, long nowMs) {
        Span span = new Span(traceId, "span-" + (++spanCounter), parentSpanId, serviceName, nowMs);
        allSpans.add(span);
        System.out.println("  started span " + span.spanId + " (" + serviceName + "), parent=" + parentSpanId);
        return span;
    }

    static void endSpan(Span span, long nowMs) {
        span.endMs = nowMs;
        System.out.println("  ended span " + span.spanId + " (" + span.serviceName + "), duration=" + span.durationMs() + "ms");
    }

    // Level 3: find the span within a trace that took the longest - the actual bottleneck.
    static Span findBottleneck(String traceId) {
        Span slowest = null;
        for (Span s : allSpans) {
            if (s.traceId.equals(traceId) && (slowest == null || s.durationMs() > slowest.durationMs())) slowest = s;
        }
        return slowest;
    }

    public static void main(String[] args) {
        String traceId = "trace-t1";

        // Level 2: propagate the trace context - each downstream call creates a CHILD span of its caller.
        Span gatewaySpan = startSpan(traceId, null, "api-gateway", 0);
        Span ordersSpan = startSpan(traceId, gatewaySpan.spanId, "orders-service", 50);
        Span dbOrdersSpan = startSpan(traceId, ordersSpan.spanId, "db-query-orders", 60);
        endSpan(dbOrdersSpan, 110);
        Span paymentsSpan = startSpan(traceId, ordersSpan.spanId, "payments-service", 140);
        Span dbPaymentsSpan = startSpan(traceId, paymentsSpan.spanId, "db-query-payments", 160);
        endSpan(dbPaymentsSpan, 200);
        endSpan(paymentsSpan, 330);
        endSpan(ordersSpan, 350);
        endSpan(gatewaySpan, 500);

        System.out.println("total request duration: " + gatewaySpan.durationMs() + "ms");
        Span bottleneck = findBottleneck(traceId);
        System.out.println("bottleneck span: " + bottleneck.serviceName + " (" + bottleneck.durationMs() + "ms) - not the top-level gateway span itself");
    }
}
```

**How to run:** save as `DistributedTracingDemo.java`, then run `java DistributedTracingDemo.java`.

## 6. Walkthrough

1. `startSpan(traceId, null, "api-gateway", 0)` creates the root span, `gatewaySpan`, with `parentSpanId = null` — it has no parent, since it is the entry point of the whole trace.
2. `startSpan(traceId, gatewaySpan.spanId, "orders-service", 50)` creates `ordersSpan`, explicitly passing `gatewaySpan.spanId` as its parent — this models the trace context (trace ID plus current span ID) being propagated from the gateway to the orders service on the outgoing call, so the new span is correctly linked as a child rather than starting an unrelated trace.
3. `dbOrdersSpan` and `paymentsSpan` are both created as children of `ordersSpan` (both pass `ordersSpan.spanId` as their parent), modeling the orders service making two separate downstream calls — one to its own database, and one to the payments service — both nested under the same parent.
4. `dbPaymentsSpan` is created as a child of `paymentsSpan`, one level deeper still, modeling the payments service's own database call; `endSpan` calls at each level record the actual end time, so each span's `durationMs()` reflects real elapsed time for that specific unit of work: `dbOrdersSpan` took `110-60=50ms`, while `paymentsSpan` took `330-140=190ms`.
5. `findBottleneck(traceId)` scans every span sharing this `traceId` and returns whichever has the largest `durationMs()`; despite `gatewaySpan` having the longest *absolute* duration (500ms, since it spans the entire request), the bottleneck search correctly identifies `paymentsSpan` (190ms) as the true bottleneck among the actual units of work — exactly the kind of insight a waterfall trace view is built to surface, which neither a single log line nor a top-level total-duration number could reveal on its own.

## 7. Gotchas & takeaways

> Gotcha: a service that fails to propagate the incoming trace context to its own outgoing calls (forgetting to pass the trace ID and parent span ID header along) causes the trace to silently "break" at that point — the downstream calls still happen and still get logged, but they start a brand-new, disconnected trace instead of continuing the original one, making it look (incorrectly) like that part of the request never happened, from the trace's point of view.

- Distributed tracing extends correlation IDs with structured timing and parent-child span relationships, showing exactly where time was spent across a multi-service request.
- Trace context (trace ID plus current span ID) must be explicitly propagated on every outgoing call, or the trace breaks at that point.
- The slowest individual span, not the top-level request duration, is usually what actually needs investigation when diagnosing latency.
- Related concepts: [Structured logging & log aggregation](0186-structured-logging-log-aggregation.md) (the simpler correlation-ID foundation this builds on), [Micrometer Tracing (OpenTelemetry)](0193-micrometer-tracing-opentelemetry.md) (a concrete Java implementation of this exact propagation), [Tail latency & percentiles (p50/p95/p99)](0126-tail-latency-percentiles-p50-p95-p99.md) (traces are often what you drill into once a percentile metric flags a problem).
