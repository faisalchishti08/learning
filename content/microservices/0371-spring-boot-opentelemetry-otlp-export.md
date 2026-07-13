---
card: microservices
gi: 371
slug: spring-boot-opentelemetry-otlp-export
title: "Spring Boot + OpenTelemetry (OTLP) export"
---

## 1. What it is

**OTLP** (OpenTelemetry Protocol) is the standard wire format OpenTelemetry uses to export telemetry data — traces, metrics, and logs — from an application to a collector or observability backend. A Spring Boot application configured with the [OpenTelemetry bridge](0369-micrometer-tracing-brave-opentelemetry-bridges.md) and an OTLP exporter sends its spans (and optionally metrics) over OTLP to an **OpenTelemetry Collector**, which can then further route that data to whatever specific backend(s) an organization actually uses (Jaeger, Prometheus, a commercial vendor), all without the application itself needing to know or care about that final destination.

## 2. Why & when

Without a standard export protocol, an application exporting traces would need to speak whatever specific format each individual backend vendor requires, directly — coupling the application to that vendor. OTLP decouples this: the application exports in one standard format to a Collector, and the Collector (a separate, centrally-managed piece of infrastructure) handles fanning that data out to one or more actual backends, converting formats as needed. This means switching or adding observability backends becomes a Collector configuration change, not an application redeploy.

Configure Spring Boot's OTLP exporter (`management.otlp.tracing.endpoint`, and similarly for metrics) whenever your organization has (or is adopting) an OpenTelemetry Collector as the central point where telemetry data is received and routed — this is increasingly the default modern setup, since it cleanly separates "how the application exports data" from "where that data ultimately ends up," letting platform teams change or add backends without touching every application's code or configuration.

## 3. Core concept

The application batches recorded spans and periodically sends them, in OTLP's protobuf-over-gRPC or JSON-over-HTTP format, to a configured Collector endpoint. The Collector receives this data, applies any configured processing (sampling, filtering, enrichment), and exports it onward to one or more configured backends — the application's only job is producing correctly-formatted OTLP data and knowing the Collector's address; everything downstream of that is the Collector's responsibility, configured independently.

```yaml
management:
  otlp:
    tracing:
      endpoint: http://otel-collector:4318/v1/traces # application only needs to know THIS
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot app exports spans via OTLP to a Collector; the Collector fans out to Jaeger, Prometheus, and a commercial vendor -- the application only ever configures the Collector's address">
  <rect x="20" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="85" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring Boot app</text>

  <line x1="170" y1="80" x2="240" y2="80" stroke="#8b949e" marker-end="url(#a371)"/>
  <text x="205" y="70" fill="#8b949e" font-size="8" font-family="sans-serif">OTLP</text>
  <rect x="250" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="85" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">OTel Collector</text>

  <line x1="400" y1="70" x2="480" y2="30" stroke="#3fb950" marker-end="url(#a371b)"/>
  <rect x="490" y="15" width="120" height="30" rx="5" fill="#1c2430" stroke="#3fb950"/>
  <text x="550" y="34" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Jaeger</text>

  <line x1="400" y1="90" x2="480" y2="130" stroke="#f0883e" marker-end="url(#a371c)"/>
  <rect x="490" y="115" width="120" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Vendor backend</text>

  <defs>
    <marker id="a371" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a371b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a371c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

The application exports OTLP to one Collector; the Collector fans data out to one or more actual backends, independently of the application.

## 5. Runnable example

Scenario: an application exporting traces directly to a specific vendor's proprietary format, first tightly coupled, then rebuilt to export standard OTLP to a Collector, and finally shown with the Collector fanning that same data out to two different backends without any application change.

### Level 1 — Basic

```java
// File: DirectVendorExport.java -- the application exports spans in a
// SPECIFIC vendor's own proprietary format, directly to that vendor;
// adding or switching backends means changing the APPLICATION.
import java.util.*;

public class DirectVendorExport {
    record Span(String name, String traceId) {}

    static void exportDirectlyToVendorX(Span span) { // TIED to Vendor X's specific format/endpoint
        System.out.println("Sent span '" + span.name() + "' in VENDOR X's proprietary format directly to Vendor X's API.");
    }

    public static void main(String[] args) {
        exportDirectlyToVendorX(new Span("chargePayment", "trace-abc"));
        System.out.println("Adding a SECOND backend (or switching vendors) means changing THIS application's export code directly.");
    }
}
```

How to run: `java DirectVendorExport.java`

`exportDirectlyToVendorX` formats and sends the span specifically for one vendor's proprietary ingestion API. If the organization later wants to add a second backend, or switch vendors entirely, this application-level export code itself would need to change — exactly the coupling OTLP and a Collector are designed to avoid.

### Level 2 — Intermediate

```java
// File: OtlpToCollector.java -- the application exports in the
// STANDARD OTLP format to ONE Collector endpoint; it has NO idea what
// backend(s) the Collector will ultimately forward the data to.
import java.util.*;

public class OtlpToCollector {
    record Span(String name, String traceId) {}
    record OtlpBatch(List<Span> spans) {} // standard OTLP-shaped batch, vendor-agnostic

    static List<OtlpBatch> collectorReceivedBatches = new ArrayList<>(); // simulates the Collector's inbound endpoint

    static void exportViaOtlp(Span span) { // the application's ONLY job: send standard OTLP to the Collector
        OtlpBatch batch = new OtlpBatch(List.of(span));
        collectorReceivedBatches.add(batch); // simulates sending to http://otel-collector:4318/v1/traces
        System.out.println("Sent span '" + span.name() + "' via STANDARD OTLP to the Collector -- app doesn't know or care what happens next.");
    }

    public static void main(String[] args) {
        exportViaOtlp(new Span("chargePayment", "trace-abc"));
        System.out.println("Collector received: " + collectorReceivedBatches);
        System.out.println("Adding/switching backends now happens ENTIRELY in Collector configuration -- ZERO application changes needed.");
    }
}
```

How to run: `java OtlpToCollector.java`

`exportViaOtlp` sends a vendor-agnostic `OtlpBatch` to `collectorReceivedBatches`, standing in for the application sending standard OTLP data to a Collector's endpoint. The application-level code has no knowledge of, or reference to, any specific downstream vendor at all — that decision now lives entirely in the (separately configured and managed) Collector.

### Level 3 — Advanced

```java
// File: CollectorFansOutToTwoBackends.java -- the SAME OTLP export from
// the application is received by the Collector, which then fans it out
// to TWO different backends -- entirely a COLLECTOR-side concern, with
// ZERO application code involved in that decision.
import java.util.*;

public class CollectorFansOutToTwoBackends {
    record Span(String name, String traceId) {}
    record OtlpBatch(List<Span> spans) {}

    static List<String> jaegerReceivedSpans = new ArrayList<>();
    static List<String> vendorReceivedSpans = new ArrayList<>();

    static void exportViaOtlp(OtlpBatch batch) { // application's export, UNCHANGED from Level 2
        System.out.println("App sent OTLP batch with " + batch.spans().size() + " span(s) to the Collector.");
        collectorReceiveAndFanOut(batch); // simulates the Collector's own internal processing
    }

    // ALL of this fan-out logic lives in the COLLECTOR, entirely separate from the application.
    static void collectorReceiveAndFanOut(OtlpBatch batch) {
        for (Span span : batch.spans()) {
            jaegerReceivedSpans.add(span.name());   // Collector forwards to Jaeger
            vendorReceivedSpans.add(span.name());   // Collector ALSO forwards to a commercial vendor
        }
        System.out.println("  Collector fanned the batch out to BOTH Jaeger and the commercial vendor.");
    }

    public static void main(String[] args) {
        exportViaOtlp(new OtlpBatch(List.of(new Span("chargePayment", "trace-abc"))));

        System.out.println("Jaeger received: " + jaegerReceivedSpans);
        System.out.println("Vendor received: " + vendorReceivedSpans);
        System.out.println("The APPLICATION's export code never changed -- adding the second backend was PURELY a Collector-side configuration change.");
    }
}
```

How to run: `java CollectorFansOutToTwoBackends.java`

`exportViaOtlp` is identical to Level 2's version — the application's export logic hasn't changed at all. The new behavior lives entirely in `collectorReceiveAndFanOut`, standing in for the Collector's own configured processing pipeline, which forwards the same received batch to both `jaegerReceivedSpans` and `vendorReceivedSpans`. Both backends end up with the span data, but the application itself never had to be modified, redeployed, or even made aware that a second backend now exists — exactly the decoupling OTLP plus a Collector architecture is designed to provide.

## 6. Walkthrough

Trace `CollectorFansOutToTwoBackends.main` in order. **First**, `exportViaOtlp(new OtlpBatch(...))` runs with a batch containing one `Span`. It prints a message confirming the application sent this batch to the Collector, then calls `collectorReceiveAndFanOut(batch)` — standing in for the network call that would, in reality, deliver this OTLP data to a separately-running Collector process.

**Inside `collectorReceiveAndFanOut`**, the loop iterates the one span in `batch.spans()`. For it, `jaegerReceivedSpans.add(span.name())` runs, appending `"chargePayment"` to that list; then `vendorReceivedSpans.add(span.name())` runs, appending the same `"chargePayment"` to the *other* list. A confirmation message prints noting the fan-out to both destinations.

**Back in `main`**, both `jaegerReceivedSpans` and `vendorReceivedSpans` are printed, each showing the one span name — demonstrating that a single OTLP export from the application resulted in the data reaching two independent backends, purely due to how the (separately configured) Collector processed it.

**Finally**, `main` prints a closing observation: `exportViaOtlp`'s own code is exactly what it was in Level 2, completely unchanged — the addition of a second backend was accomplished entirely through Collector-side configuration (adding a second export target in the Collector's own config), with zero corresponding change required in the application.

```
app: exportViaOtlp(batch with 1 span) -> sends via OTLP to Collector
Collector: collectorReceiveAndFanOut(batch) -> forwards to Jaeger AND to Vendor, independently
Result: jaegerReceivedSpans=[chargePayment], vendorReceivedSpans=[chargePayment]
Application code: UNCHANGED from the single-backend version.
```

## 7. Gotchas & takeaways

> Running an application's OTLP exporter without a Collector in between, pointed directly at a single backend's own OTLP-compatible ingestion endpoint, still works — but it forfeits the fan-out and vendor-independence benefits a Collector provides; that configuration is really just "direct vendor export using a standard wire format" rather than the fully decoupled architecture OTLP plus a Collector enables.

- OTLP is the standard wire format OpenTelemetry uses to export traces (and metrics, logs) from an application, typically to a centrally-managed Collector.
- The Collector, not the application, is responsible for routing, filtering, and fanning telemetry data out to one or more actual observability backends.
- This decoupling means adding, removing, or switching backends is a Collector configuration change, requiring zero application code changes or redeploys.
- Spring Boot's OTLP exporter configuration (`management.otlp.tracing.endpoint`) is the concrete setting that connects an application's [OpenTelemetry-bridged tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md) to this whole pipeline.
