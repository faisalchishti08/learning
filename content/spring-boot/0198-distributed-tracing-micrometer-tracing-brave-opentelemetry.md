---
card: spring-boot
gi: 198
slug: distributed-tracing-micrometer-tracing-brave-opentelemetry
title: Distributed tracing (Micrometer Tracing — Brave/OpenTelemetry)
---

## 1. What it is

**Distributed tracing** records the full journey of a request across multiple services as a tree of **spans**. Each span captures the start time, duration, and context of one unit of work. Spring Boot 3 integrates distributed tracing via **Micrometer Tracing** — a vendor-neutral façade backed by either **Brave** (Zipkin's tracing library) or **OpenTelemetry**. Adding the appropriate dependency auto-configures `Tracer`, propagates trace context through HTTP headers, and exports spans to a back-end.

## 2. Why & when

A single user request in a microservices system might touch 5 services, 2 databases, and a message broker. Metrics and logs tell you something is slow; distributed tracing tells you **which service and which call** is causing the slowdown.

**When tracing pays off:**
- Latency outliers: "Why does p99 POST /checkout take 8 seconds?"
- Cascading failures: "Which downstream service is timing out and causing the cascade?"
- Cross-service debugging: "Does this request reach service B at all?"

**Not worth it for:**
- Single-service applications with no downstream calls.
- Very high-throughput systems where 100% sampling is unaffordable (use probabilistic sampling, e.g., 10%).

## 3. Core concept

Key terms:
- **Trace**: the complete request journey, identified by a `traceId`.
- **Span**: one unit of work within a trace. Has a `spanId` and a parent `spanId`.
- **Context propagation**: the `traceId` and `spanId` are injected into outbound HTTP headers (`traceparent` for OTLP/W3C, `X-B3-TraceId` for Zipkin B3) and extracted from inbound headers.

Spring Boot 3 dependencies:

| Goal | Dependencies |
|---|---|
| Brave + Zipkin | `spring-boot-starter-actuator` + `micrometer-tracing-bridge-brave` + `zipkin-reporter-brave` |
| OpenTelemetry + Zipkin | `micrometer-tracing-bridge-otel` + `opentelemetry-exporter-zipkin` |
| OpenTelemetry + OTLP (Jaeger/Grafana) | `micrometer-tracing-bridge-otel` + `opentelemetry-exporter-otlp` |

Key properties:
- `management.tracing.sampling.probability=1.0` — sample 100% (for dev); use 0.1 (10%) in production.
- `management.zipkin.tracing.endpoint=http://zipkin:9411/api/v2/spans` — Zipkin reporter URL.
- Logs automatically include `traceId` and `spanId` when `micrometer-tracing` is on the classpath.

## 4. Diagram

<svg viewBox="0 0 720 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Request enters API gateway, traceId created, propagated via HTTP headers through three services, spans exported to Zipkin">
  <!-- Client -->
  <rect x="10" y="85" width="80" height="38" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="109" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Browser</text>

  <!-- Arrow -->
  <line x1="92" y1="104" x2="135" y2="104" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dta)"/>

  <!-- Service A -->
  <rect x="140" y="60" width="140" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="81" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">API Service</text>
  <text x="210" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">traceId: abc123</text>
  <text x="210" y="111" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">spanId:  s1</text>
  <text x="210" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">span: root (0-120ms)</text>
  <text x="210" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">propagates headers →</text>

  <!-- Arrow with trace header -->
  <line x1="283" y1="104" x2="340" y2="104" stroke="#6db33f" stroke-width="1.5" marker-end="url(#dtb)"/>
  <text x="311" y="97" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">traceparent</text>

  <!-- Service B -->
  <rect x="345" y="60" width="140" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="415" y="81" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Order Service</text>
  <text x="415" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">traceId: abc123</text>
  <text x="415" y="111" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">spanId:  s2  parent: s1</text>
  <text x="415" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">span: (15-90ms)</text>
  <text x="415" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">propagates headers →</text>

  <!-- Arrow -->
  <line x1="488" y1="104" x2="545" y2="104" stroke="#6db33f" stroke-width="1.5" marker-end="url(#dtb)"/>

  <!-- Service C -->
  <rect x="550" y="60" width="140" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="620" y="81" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Inventory Svc</text>
  <text x="620" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">traceId: abc123</text>
  <text x="620" y="111" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">spanId:  s3  parent: s2</text>
  <text x="620" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">span: (20-85ms)</text>

  <!-- Export to Zipkin -->
  <line x1="210" y1="153" x2="210" y2="180" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#dtc)"/>
  <line x1="415" y1="153" x2="415" y2="180" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#dtc)"/>
  <line x1="620" y1="153" x2="620" y2="180" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#dtc)"/>

  <rect x="130" y="183" width="540" height="18" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="400" y="196" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Zipkin / Jaeger / Grafana Tempo — shows full trace tree for traceId=abc123</text>

  <defs>
    <marker id="dta" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="dtb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="dtc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

One `traceId` ties all spans across services; each service creates its own span and exports it to the tracing back-end.

## 5. Runnable example

```java
// DistributedTracingDemo.java — simulates trace propagation across three services
// How to run: java DistributedTracingDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot 3: add micrometer-tracing-bridge-brave + zipkin-reporter-brave; auto-wires Tracer

import java.util.*;

public class DistributedTracingDemo {

    record Span(String traceId, String spanId, String parentSpanId,
                String service, String operation, long startMs, long durationMs) {}

    static final List<Span> collectedSpans = new ArrayList<>();
    static long clock = 0;

    static String newSpanId() { return "s" + (collectedSpans.size() + 1); }

    // Simulate HTTP call with trace context propagation
    static Map<String, String> propagateHeaders(String traceId, String spanId) {
        // W3C traceparent header (OpenTelemetry) or X-B3-TraceId (Brave/Zipkin)
        return Map.of(
            "traceparent", "00-" + traceId + "-" + spanId + "-01",
            "X-B3-TraceId", traceId,
            "X-B3-SpanId",  spanId,
            "X-B3-Sampled", "1"
        );
    }

    static String extractTraceId(Map<String, String> headers) {
        return headers.getOrDefault("X-B3-TraceId", UUID.randomUUID().toString().replace("-",""));
    }
    static String extractParentSpanId(Map<String, String> headers) {
        return headers.getOrDefault("X-B3-SpanId", null);
    }

    // Simulates a service handling a request and creating a child span
    static String handleRequest(String service, String operation,
                                 Map<String, String> inboundHeaders, long workMs,
                                 java.util.function.Supplier<String> work) {
        String traceId  = extractTraceId(inboundHeaders);
        String parentId = extractParentSpanId(inboundHeaders);
        String spanId   = newSpanId();
        long   start    = clock;
        clock += workMs;
        collectedSpans.add(new Span(traceId, spanId, parentId, service, operation, start, workMs));
        System.out.printf("[%s] span=%s parent=%s traceId=%s operation=%s (%dms)%n",
                service, spanId, parentId, traceId, operation, workMs);
        String result = work.get();
        // Log entry automatically includes traceId via MDC (in real Spring Boot)
        System.out.printf("  LOG[traceId=%s spanId=%s]: %s completed%n", traceId, spanId, operation);
        return result;
    }

    public static void main(String[] args) {
        System.out.println("=== Distributed Tracing Demo ===\n");
        String traceId = "abc123def456abc1"; // Generated by first service

        // 1. API Service receives request (no inbound trace headers — root span)
        String s1 = "s1";
        Map<String, String> rootHeaders = Map.of("X-B3-TraceId", traceId);
        handleRequest("api-service", "POST /checkout", rootHeaders, 15, () -> {

            // 2. API calls Order Service — propagates trace context
            Map<String, String> toOrder = propagateHeaders(traceId, s1);
            System.out.println("\n  [api-service] outbound call to order-service");
            System.out.println("  headers: " + toOrder);
            handleRequest("order-service", "createOrder", toOrder, 75, () -> {

                // 3. Order Service calls Inventory
                Map<String, String> toInv = propagateHeaders(traceId, "s2");
                System.out.println("\n    [order-service] outbound call to inventory-service");
                handleRequest("inventory-service", "checkStock", toInv, 65, () -> "OK");

                return "order-created";
            });
            return "checkout-complete";
        });

        System.out.println("\n--- Collected Spans (sent to Zipkin/Jaeger) ---");
        System.out.printf("%-8s %-8s %-12s %-20s %-22s %5s%n",
                "TraceId", "SpanId", "ParentId", "Service", "Operation", "ms");
        System.out.println("-".repeat(85));
        collectedSpans.forEach(s ->
            System.out.printf("%-8s %-8s %-12s %-20s %-22s %5d%n",
                    s.traceId().substring(0,8), s.spanId(), s.parentSpanId() != null ? s.parentSpanId() : "ROOT",
                    s.service(), s.operation(), s.durationMs()));

        System.out.println("\n--- Trace tree (visualised in Zipkin) ---");
        System.out.println("api-service POST /checkout       [=====15ms] → s1");
        System.out.println("  order-service createOrder      [========75ms] → s2 (parent s1)");
        System.out.println("    inventory-service checkStock  [======65ms] → s3 (parent s2)");
        System.out.println("\nLogs in all three services contain traceId=abc123def456abc1");
        System.out.println("Search Kibana/Splunk for that traceId to correlate all log lines");
    }
}
```

**How to run:** `java DistributedTracingDemo.java`

## 6. Walkthrough

- **`propagateHeaders`** builds W3C `traceparent` and Zipkin `X-B3-*` headers. In Spring Boot, `RestTemplate`, `WebClient`, and `RestClient` automatically inject these headers on outbound calls.
- **Root span** (api-service): no parent — this is the entry point. In real Zipkin, it appears at the top of the trace waterfall.
- **Child spans**: order-service and inventory-service extract the `traceId` and `parentSpanId` from inbound headers (auto-extracted by Spring Boot's `ServerHttpObservationFilter`). Each creates its own span linked to the parent.
- **Log correlation**: the `LOG[traceId=...]` lines simulate what Spring Boot's MDC integration does — every log statement automatically includes `traceId` and `spanId` when Micrometer Tracing is on the classpath.
- **Span export**: all spans are sent asynchronously to Zipkin (or OTLP endpoint) — the application thread is not blocked by the export.

## 7. Gotchas & takeaways

> `management.tracing.sampling.probability=1.0` (100% sampling) is fine in dev but **catastrophically expensive in production** at high throughput. Use 0.1 (10%) or configure head-based sampling — 1000 RPS × 100% × 10 spans/trace = 1 million spans/second exported.

> Trace context propagation works automatically for `RestTemplate`, `WebClient`, and `RestClient` — but **not for raw `java.net.HttpURLConnection`** or third-party HTTP clients without instrumentation. Wrap those calls with a manual `Observation`.

- Maven: `micrometer-tracing-bridge-brave` + `zipkin-reporter-brave` for Brave/Zipkin.
- Maven: `micrometer-tracing-bridge-otel` + `opentelemetry-exporter-otlp` for OpenTelemetry/OTLP (Jaeger, Grafana Tempo).
- Logs automatically include `traceId`/`spanId` in the `%mdc{traceId}` field when using Logback + Micrometer Tracing.
- `@NewSpan` annotation (from `spring-cloud-sleuth` replaced by Micrometer) creates a child span around a method — use `Observation` API in Spring Boot 3 instead.
- `Baggage` API propagates custom key-value pairs (e.g., `userId`, `tenantId`) through the trace without adding them to every metric tag.
