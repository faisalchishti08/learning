---
card: spring-cloud
gi: 103
slug: opentelemetry-integration
title: "OpenTelemetry integration"
---

## 1. What it is

`micrometer-tracing-bridge-otel` plugs the OpenTelemetry SDK in as the concrete tracer implementation underneath Micrometer Tracing's neutral API, and an OTLP (OpenTelemetry Protocol) exporter ships spans to any OTLP-compatible backend — Jaeger, Zipkin (via its OTLP-compatible ingest), Grafana Tempo, or a commercial observability vendor — all through one vendor-neutral wire protocol rather than a backend-specific format.

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-exporter-otlp</artifactId>
</dependency>
```

```properties
management.otlp.tracing.endpoint=http://localhost:4318/v1/traces
management.tracing.sampling.probability=1.0
```

## 2. Why & when

OpenTelemetry has become the industry-standard, vendor-neutral specification for telemetry (traces, metrics, and logs) across the observability ecosystem — choosing the OpenTelemetry bridge means an application's spans are exported in the OTLP format that essentially every modern observability backend (open-source and commercial alike) already accepts natively, avoiding lock-in to any one backend's proprietary ingest format. Where the Brave/Zipkin combination (the previous card) targets specifically Zipkin as the viewing backend, the OpenTelemetry bridge targets the broader, standardized ecosystem — the same OTLP export can be pointed at Jaeger, Tempo, or a commercial vendor's collector without changing which bridge dependency is on the classpath.

Reach for the OpenTelemetry bridge when:

- The target backend is anything other than Zipkin specifically — Jaeger, Grafana Tempo, or most commercial observability platforms consume OTLP natively, making the OpenTelemetry bridge the more direct, standards-aligned path.
- Building new applications without a strong existing reason to prefer Brave — OpenTelemetry is the actively evolving industry standard, and starting new work aligned with it avoids a future migration that an existing Brave-based application might eventually need to make anyway.
- Telemetry beyond just tracing — metrics, logs — is also planned to eventually flow through OpenTelemetry's unified collector model; keeping tracing on the same OTLP-based path as those other signals simplifies the overall observability pipeline architecture.

## 3. Core concept

```
 application span creation (via the neutral Tracer API)
        |
        v
 OpenTelemetry SDK (bridged in via micrometer-tracing-bridge-otel)
   -- creates/manages spans, applies sampling, batches for export
        |
        v
 OTLP exporter
   -- serializes spans using the OpenTelemetry Protocol (protobuf or JSON over HTTP, or gRPC)
        |
        v
 ANY OTLP-compatible backend: Jaeger, Tempo, Zipkin (via OTLP), commercial vendors
   -- one WIRE FORMAT, many possible destinations, chosen purely by endpoint configuration
```

Because OTLP is a standardized protocol rather than a Zipkin-specific format, switching backends is often just an endpoint URL change, with no export-format translation needed on either side.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application using the OpenTelemetry bridge exports spans via OTLP to a collector which can forward them to Jaeger, Grafana Tempo, or a commercial vendor depending purely on collector configuration">
  <rect x="20" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">app + OTel bridge</text>
  <text x="95" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">exports via OTLP</text>

  <rect x="230" y="20" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="315" y="48" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">OTel Collector (optional)</text>

  <rect x="460" y="10" width="150" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="535" y="30" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Jaeger</text>
  <rect x="460" y="50" width="150" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="535" y="70" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Grafana Tempo</text>
  <rect x="460" y="90" width="150" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="535" y="110" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">commercial vendor</text>

  <defs><marker id="a103" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="43" x2="230" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a103)"/>
  <line x1="400" y1="35" x2="460" y2="25" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a103)"/>
  <line x1="400" y1="43" x2="460" y2="65" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a103)"/>
  <line x1="400" y1="50" x2="460" y2="105" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a103)"/>
</svg>

One OTLP export, potentially fanned out (via an optional collector) to multiple backends simultaneously, with no application-side changes needed to add or swap a destination.

## 5. Runnable example

The scenario: model span export via a neutral OTLP-shaped payload, routed to different simulated backends purely by endpoint configuration — proving the export format itself doesn't change per backend. Start with export to one backend, then add a second backend reachable via the same export code, then add sampling so only a configured fraction of spans are exported at all, mirroring real-world sampling.probability configuration.

### Level 1 — Basic

A span exported in a neutral OTLP-shaped structure to a single backend.

```java
import java.util.*;

public class OtelIntegrationLevel1 {
    record OtlpSpan(String traceId, String spanId, String name, long durationMs) {}

    // stands in for ANY OTLP-compatible backend -- Jaeger, Tempo, etc. all accept this same shape
    interface OtlpBackend { void ingest(OtlpSpan span); }

    static class JaegerBackend implements OtlpBackend {
        public void ingest(OtlpSpan span) { System.out.println("Jaeger received via OTLP: " + span.name()); }
    }

    public static void main(String[] args) {
        OtlpBackend backend = new JaegerBackend();
        OtlpSpan span = new OtlpSpan("trace-1", "span-1", "GET /orders", 45);

        backend.ingest(span);
    }
}
```

How to run: `java OtelIntegrationLevel1.java`

`OtlpSpan` and the `OtlpBackend` interface are deliberately backend-neutral — nothing about the span's shape mentions Jaeger specifically, mirroring how a real OTLP payload is identical regardless of which OTLP-compatible system eventually receives it.

### Level 2 — Intermediate

Add a second backend implementation and export the same span data to either one, purely by which `OtlpBackend` is configured — proving one export path serves multiple destinations.

```java
import java.util.*;

public class OtelIntegrationLevel2 {
    record OtlpSpan(String traceId, String spanId, String name, long durationMs) {}
    interface OtlpBackend { void ingest(OtlpSpan span); }

    static class JaegerBackend implements OtlpBackend {
        public void ingest(OtlpSpan span) { System.out.println("Jaeger received: " + span.name()); }
    }
    static class TempoBackend implements OtlpBackend {
        public void ingest(OtlpSpan span) { System.out.println("Grafana Tempo received: " + span.name()); }
    }

    // the export function itself is IDENTICAL regardless of which backend is passed in
    static void exportSpan(OtlpBackend backend, OtlpSpan span) {
        backend.ingest(span);
    }

    public static void main(String[] args) {
        OtlpSpan span = new OtlpSpan("trace-1", "span-1", "GET /orders", 45);

        exportSpan(new JaegerBackend(), span);
        exportSpan(new TempoBackend(), span); // SAME span, SAME exportSpan code, different endpoint config
    }
}
```

How to run: `java OtelIntegrationLevel2.java`

`exportSpan` never branches on which backend type it received — this mirrors how, in a real Spring Boot application, switching `management.otlp.tracing.endpoint` from a Jaeger collector's address to a Tempo collector's address requires zero application code changes, only a configuration property update.

### Level 3 — Advanced

Add sampling: only a configured fraction of spans are actually exported, mirroring `management.tracing.sampling.probability`, and track the resulting export rate to confirm it approximates the configured probability over many spans.

```java
import java.util.*;

public class OtelIntegrationLevel3 {
    record OtlpSpan(String traceId, String spanId, String name, long durationMs) {}
    interface OtlpBackend { void ingest(OtlpSpan span); }

    static class JaegerBackend implements OtlpBackend {
        int received = 0;
        public void ingest(OtlpSpan span) { received++; }
    }

    // models the SDK's sampler: a per-span probabilistic decision made BEFORE export
    static class ProbabilisticSampler {
        double probability;
        Random random;
        ProbabilisticSampler(double probability, long seed) { this.probability = probability; this.random = new Random(seed); }
        boolean shouldSample() { return random.nextDouble() < probability; }
    }

    static void exportSpanIfSampled(OtlpBackend backend, ProbabilisticSampler sampler, OtlpSpan span) {
        if (sampler.shouldSample()) backend.ingest(span); // only sampled spans actually reach the backend/network
    }

    public static void main(String[] args) {
        JaegerBackend backend = new JaegerBackend();
        ProbabilisticSampler sampler = new ProbabilisticSampler(0.25, 42); // export ~25% of spans

        int totalSpans = 10_000;
        for (int i = 0; i < totalSpans; i++) {
            exportSpanIfSampled(backend, sampler, new OtlpSpan("trace-" + i, "span-" + i, "GET /orders", 45));
        }

        double actualRate = (double) backend.received / totalSpans;
        System.out.println("configured probability: 0.25, actual export rate: " + actualRate);
    }
}
```

How to run: `java OtelIntegrationLevel3.java`

Out of `10,000` generated spans, roughly `2,500` (an actual rate close to `0.25`) are actually passed to `backend.ingest`, because `sampler.shouldSample()` gates every export call — the other roughly `7,500` spans are dropped before ever reaching the (simulated) network, exactly mirroring how `management.tracing.sampling.probability` controls the fraction of a real application's traces that actually consume export bandwidth and backend storage, trading complete trace coverage for reduced overhead.

## 6. Walkthrough

Trace the sampling loop in Level 3.

1. `sampler = new ProbabilisticSampler(0.25, 42)` is constructed with a fixed seed, so its sequence of `random.nextDouble()` calls is deterministic and reproducible across runs.
2. The `for` loop runs `10,000` times, each iteration creating a fresh `OtlpSpan` and calling `exportSpanIfSampled(backend, sampler, span)`.
3. Inside `exportSpanIfSampled`, `sampler.shouldSample()` calls `random.nextDouble()`, producing a value uniformly distributed between `0.0` and `1.0`, and compares it against `probability = 0.25` — roughly one in four calls produces a value less than `0.25`, so roughly one in four calls to `shouldSample()` returns `true`.
4. When `shouldSample()` returns `true`, `backend.ingest(span)` runs, incrementing `backend.received` by one — this is the only path by which a span actually reaches the (simulated) backend.
5. When `shouldSample()` returns `false` (roughly three out of every four calls), `exportSpanIfSampled` does nothing further — that span's data is discarded immediately, without any network call or backend storage cost.
6. After all `10,000` iterations, `backend.received` holds the count of sampled-and-exported spans — dividing by `totalSpans` gives `actualRate`, which prints close to `0.25`, confirming the sampler's long-run behavior matches its configured probability even though each individual span's fate is an independent random decision.

```
10,000 spans generated
  each: sampler.shouldSample() -- independent ~25% chance of true
  true  -> backend.ingest(span)  -> backend.received++
  false -> span discarded, no export at all

after all 10,000: backend.received / 10,000 ≈ 0.25  (matches configured probability)
```

## 7. Gotchas & takeaways

> **Gotcha:** the sampling decision for a trace should be made once, at the trace's root span, and propagated to every child span across every service the trace touches — sampling independently at each service (each service flipping its own coin for whether to export its own span) produces incomplete, fragmented traces where some spans of a single logical request are exported and others aren't, defeating the purpose of reconstructing a full trace tree. Real tracing systems propagate the sampling decision itself as part of the trace context precisely to avoid this.

- The OpenTelemetry bridge's core value is standardization: one OTLP export format works against essentially any modern tracing backend, avoiding the backend-specific coupling a proprietary export format would create.
- Sampling exists specifically to control overhead — exporting and storing 100% of spans on a high-throughput service can be prohibitively expensive; a well-chosen sampling probability preserves enough trace data for meaningful analysis while keeping export volume manageable.
- Because OTLP is a shared protocol, adding, removing, or switching *destination* backends (Jaeger, Tempo, a vendor) is typically a configuration change (the endpoint URL) rather than a code or dependency change, once the OpenTelemetry bridge itself is in place.
- Choosing between the Brave/Zipkin bridge (previous card) and the OpenTelemetry bridge (this card) is primarily a backend-ecosystem decision — both sit underneath the same neutral Micrometer Tracing API, so application-level instrumentation code is unaffected either way.
