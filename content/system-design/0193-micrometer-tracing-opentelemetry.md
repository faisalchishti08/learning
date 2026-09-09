---
card: system-design
gi: 193
slug: micrometer-tracing-opentelemetry
title: Micrometer Tracing (OpenTelemetry)
---

## 1. What it is

**Micrometer Tracing** is Spring's vendor-neutral facade for [distributed tracing](0188-distributed-tracing-correlation-ids.md) in Java applications, playing the same role for traces that Micrometer plays for metrics — you instrument code once through its API, and it forwards spans to whichever tracing backend you configure. **OpenTelemetry** is the industry-standard specification (and set of libraries) for representing and exporting traces, metrics, and logs in a vendor-neutral format; Micrometer Tracing commonly uses the OpenTelemetry bridge to actually create and export spans to a backend like Zipkin, Jaeger, or a cloud tracing service.

## 2. Why & when

Instrumenting every service with a specific tracing vendor's proprietary SDK creates the same lock-in problem metrics vendors created before Micrometer existed — switching tracing backends later would mean touching every instrumented call site. Micrometer Tracing, bridged through OpenTelemetry's vendor-neutral span model, lets you instrument once and export to any OpenTelemetry-compatible backend via configuration. Use it in any Spring Boot microservice architecture where you need the trace propagation and span-timing benefits described under distributed tracing, implemented with a standard, swappable-backend Java library rather than hand-rolled trace-context passing.

## 3. Core concept

- **`Tracer` and `Span`:** Micrometer Tracing's core API — `tracer.nextSpan().name("process-order").start()` creates a new span, which you later `.end()`, mirroring the span concept from distributed tracing directly.
- **Automatic instrumentation for common calls:** Spring Boot auto-instruments outgoing `RestTemplate`/`WebClient` HTTP calls and incoming requests automatically, creating and propagating spans without manual code at every call site.
- **Context propagation via HTTP headers:** the trace context (trace ID, current span ID) is automatically added as headers (following the W3C Trace Context standard, `traceparent`) on outgoing calls, and automatically read from incoming request headers to continue an existing trace — this is the actual mechanism behind the propagation described under distributed tracing.
- **OpenTelemetry exporters:** configuring an exporter (e.g. an OTLP exporter pointing at a collector) determines where the finished spans actually go; changing backends is a matter of swapping the exporter configuration, not re-instrumenting code.
- **Sampling configuration:** `management.tracing.sampling.probability` controls what fraction of traces are actually recorded and exported, balancing observability detail against the volume and cost of storing every single trace.

## 4. Diagram

```
   service-A                                          service-B
        |                                                   |
   Tracer.nextSpan("call-service-B").start()                |
        |                                                   |
        |-- HTTP GET /api/data ------------------------------->|
        |   header: traceparent: 00-<traceId>-<spanId>-01     |
        |                                                    | Tracer reads incoming
        |                                                    | traceparent header,
        |                                                    | starts a CHILD span
        |                                                    |
        |<-------------------------------- response ----------|
   span.end()                                          child span.end()
        |
        v
   both spans exported (via OpenTelemetry) to the SAME trace in the backend
```
*Caption: Micrometer Tracing automatically attaches and reads the W3C `traceparent` header, so context propagation across services needs no manual header handling in application code.*

## 5. Runnable example

This models Micrometer Tracing's span creation and header-based context propagation in-process; the "How to run" note shows the real Spring configuration.

**Level 1 — Basic.** Create and end a span via a `Tracer`-style API.

**Level 2 — Propagate trace context via a `traceparent`-style header on an outgoing call.** Automatically continue the trace on the receiving side.

**Level 3 — Apply sampling: only a configured fraction of traces are actually recorded.** Show unsampled traces skipping span creation entirely.

```java
// MicrometerTracingDemo.java
import java.util.*;

public class MicrometerTracingDemo {

    static class Span {
        final String traceId, spanId, name;
        long startMs, endMs;
        Span(String traceId, String spanId, String name, long startMs) {
            this.traceId = traceId; this.spanId = spanId; this.name = name; this.startMs = startMs;
        }
    }

    static List<Span> exportedSpans = new ArrayList<>();
    static int spanCounter = 0;

    // Level 1: Tracer-style API - start a span.
    static Span startSpan(String traceId, String name, long nowMs) {
        Span span = new Span(traceId, "span-" + (++spanCounter), name, nowMs);
        System.out.println("  [Tracer] started span \"" + name + "\" (trace=" + traceId + ", span=" + span.spanId + ")");
        return span;
    }

    static void endSpan(Span span, long nowMs) {
        span.endMs = nowMs;
        exportedSpans.add(span); // Level 2: exported via the configured OpenTelemetry exporter
        System.out.println("  [Tracer] ended span \"" + span.name + "\", exported to backend");
    }

    // Level 2: automatic header propagation, modeling the W3C traceparent header.
    static String buildTraceparentHeader(Span currentSpan) {
        return "00-" + currentSpan.traceId + "-" + currentSpan.spanId + "-01";
    }

    // The RECEIVING side automatically reads the header and starts a CHILD span in the SAME trace.
    static Span receiveRequestAndStartChildSpan(String traceparentHeader, String childSpanName, long nowMs) {
        String[] parts = traceparentHeader.split("-");
        String traceId = parts[1]; // the SAME trace ID is reused - this is what makes it one continuous trace
        return startSpan(traceId, childSpanName, nowMs);
    }

    // Level 3: sampling - only a configured fraction of NEW traces are actually recorded at all.
    static double samplingProbability = 0.5;
    static Random random = new Random(42); // fixed seed for reproducible demo output

    static boolean shouldSample() {
        return random.nextDouble() < samplingProbability;
    }

    public static void main(String[] args) {
        // Level 1 & 2: service-A makes a call to service-B, propagating trace context via a header.
        String traceId = "trace-abc123";
        Span serviceASpan = startSpan(traceId, "call-service-B", 0);
        String header = buildTraceparentHeader(serviceASpan);
        System.out.println("  outgoing HTTP header: traceparent: " + header);

        // service-B receives the request and reads the SAME trace ID from the header.
        Span serviceBSpan = receiveRequestAndStartChildSpan(header, "handle-request", 10);
        endSpan(serviceBSpan, 60);
        endSpan(serviceASpan, 70);

        System.out.println("both spans share the same trace ID: " + serviceASpan.traceId.equals(serviceBSpan.traceId));

        // Level 3: simulate several NEW, unrelated traces - only some fraction get sampled and recorded at all.
        int totalTraces = 10, sampledCount = 0;
        for (int i = 0; i < totalTraces; i++) {
            if (shouldSample()) {
                sampledCount++;
                Span sampled = startSpan("trace-new-" + i, "some-operation", 100);
                endSpan(sampled, 150);
            } else {
                System.out.println("  trace-new-" + i + ": NOT sampled - no span created at all, zero overhead");
            }
        }
        System.out.println("sampled " + sampledCount + "/" + totalTraces + " new traces (target probability: " + samplingProbability + ")");
    }
}
```

**How to run:** save as `MicrometerTracingDemo.java`, then run `java MicrometerTracingDemo.java`. (Real Spring Boot: add `micrometer-tracing-bridge-otel` and an exporter like `opentelemetry-exporter-otlp`; inject `Tracer` and call `tracer.nextSpan().name("call-service-B").start()`, or rely on Spring's automatic instrumentation of `RestTemplate`/`WebClient`, which propagates the `traceparent` header without any manual code.)

## 6. Walkthrough

1. `startSpan(traceId, "call-service-B", 0)` creates `serviceASpan` with the given `traceId` and a fresh `spanId`; `buildTraceparentHeader(serviceASpan)` formats these into a `"00-<traceId>-<spanId>-01"` string, modeling the real W3C `traceparent` header format that Spring's HTTP client instrumentation attaches automatically.
2. `receiveRequestAndStartChildSpan(header, "handle-request", 10)` splits the header string to extract the `traceId` portion, then calls `startSpan` again — but crucially reuses the *extracted* `traceId` rather than generating a new one, exactly modeling how the receiving service's automatic instrumentation continues the existing trace instead of starting an unrelated one.
3. `serviceASpan.traceId.equals(serviceBSpan.traceId)` confirms both spans genuinely share the same trace ID, despite being created by what represent two entirely separate services in two separate method calls — this is the propagation mechanism working correctly.
4. The sampling loop calls `shouldSample()` ten times; with `samplingProbability = 0.5` and a fixed random seed, roughly half the calls return `true` — for those, a full span is created and ended (incurring the cost of tracing); for the rest, the loop prints a "NOT sampled" message and creates no span object at all.
5. The final printed ratio (`sampledCount / totalTraces`) approximates the configured `samplingProbability`, demonstrating that sampling genuinely skips instrumentation overhead for the unsampled fraction, rather than merely discarding already-created spans after the fact — an important distinction for keeping tracing overhead low at high request volume.

## 7. Gotchas & takeaways

> Gotcha: setting `management.tracing.sampling.probability` to different values across different services in the same architecture can produce broken or incomplete traces — if service-A samples a trace (creating spans) but a downstream service-B independently decides, based on its own separate sampling decision, not to record its part, the resulting trace has gaps; sampling decisions should be made consistently for a given trace, typically at the entry point, and propagated (not re-decided) at each downstream service.

- Micrometer Tracing decouples tracing instrumentation from any specific backend, mirroring what Micrometer does for metrics, via the OpenTelemetry standard.
- Automatic HTTP header propagation (the `traceparent` header) is what actually implements distributed tracing's context-propagation requirement, without manual code at each call site.
- Sampling should be decided once per trace, typically at the entry point, and honored consistently downstream — not re-decided independently by each service.
- Related concepts: [Distributed tracing & correlation IDs](0188-distributed-tracing-correlation-ids.md) (the underlying concept this library implements), [Micrometer metrics + Prometheus](0192-micrometer-metrics-prometheus.md) (Micrometer's companion library for metrics, following the same vendor-neutral philosophy), [Spring Boot Actuator endpoints](0194-spring-boot-actuator-endpoints.md) (where trace and metrics configuration is commonly exposed and inspected).
