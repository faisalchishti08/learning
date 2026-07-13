---
card: microservices
gi: 353
slug: trace-context-w3c-trace-context-b3-headers
title: "Trace context (W3C Trace Context, B3 headers)"
---

## 1. What it is

**W3C Trace Context** and **B3** are two standardized HTTP header formats for propagating [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) context (the trace ID, the current span ID, and sampling decision) between services. W3C Trace Context uses a single `traceparent` header (plus an optional `tracestate` for vendor-specific extensions); B3 (from Zipkin) uses either a single `b3` header or several separate `X-B3-*` headers. Standardizing the format matters because it lets services written with different tracing libraries, or even different vendors' tracing tools, correctly participate in the same trace.

## 2. Why & when

If every team or every tracing library invented its own header names and formats for propagating trace context, a request passing through a service using tool A and then a service using tool B would break the trace — tool B's library wouldn't recognize tool A's custom headers and would start a brand-new, disconnected trace instead of correctly continuing the existing one. Standardized formats solve this: any library that reads and writes `traceparent` (W3C) or the B3 headers correctly interoperates with any other library doing the same, regardless of vendor.

Use whichever standard your tracing infrastructure and libraries default to — W3C Trace Context is the modern, broadly-adopted standard (and what OpenTelemetry uses by default), while B3 remains common in systems built around Zipkin or older Spring Cloud Sleuth deployments. If you're integrating with an existing system using one format, or bridging two systems that each expect a different one, you may need explicit format conversion at the boundary — most modern tracing libraries support reading and writing both.

## 3. Core concept

The W3C `traceparent` header packs four fields into one string: `version-traceId-spanId-flags`, e.g. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` — a version byte, a 32-hex-character trace ID, a 16-hex-character (parent/current) span ID, and flags (bit 0 indicates whether this trace is sampled). B3's single-header form packs similar fields (`traceId-spanId-sampled-parentSpanId`) into one `b3` header, or spreads them across separate `X-B3-TraceId`, `X-B3-SpanId`, `X-B3-Sampled`, and `X-B3-ParentSpanId` headers.

```java
// W3C: version-traceId-spanId-flags
String traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01";
// B3 single header: traceId-spanId-sampled-parentSpanId
String b3 = "4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-1";
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service A using OpenTelemetry sends a request with a traceparent header; Service B using a different vendor's library reads the SAME standardized header and correctly continues the same trace">
  <rect x="20" y="60" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service A (OpenTelemetry)</text>

  <line x1="220" y1="80" x2="330" y2="80" stroke="#79c0ff" marker-end="url(#a353)"/>
  <text x="275" y="70" fill="#79c0ff" font-size="8" font-family="sans-serif">traceparent header</text>

  <rect x="340" y="60" width="220" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="450" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service B (different vendor)</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Because BOTH speak the SAME standard header format, the trace continues correctly across the vendor boundary.</text>

  <defs><marker id="a353" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

A standardized header format lets services using different tracing libraries or vendors correctly continue the same trace.

## 5. Runnable example

Scenario: two services using incompatible custom trace-propagation headers (breaking the trace at the boundary), then fixed by adopting a shared W3C Trace Context-style `traceparent` header, and finally extended to parse and validate that header's fields correctly, including the sampling flag.

### Level 1 — Basic

```java
// File: IncompatibleCustomHeaders.java -- Service A uses its OWN custom
// header name; Service B expects a DIFFERENT custom header name -- the
// trace breaks at the boundary.
import java.util.*;

public class IncompatibleCustomHeaders {
    static Map<String, String> serviceAOutgoingHeaders(String myTraceId) {
        return Map.of("X-MyCompany-Trace", myTraceId); // Service A's OWN invented header name
    }

    static String serviceBExtractTraceId(Map<String, String> incomingHeaders) {
        return incomingHeaders.get("X-Trace-Id"); // Service B looks for a DIFFERENT header name!
    }

    public static void main(String[] args) {
        Map<String, String> headersFromA = serviceAOutgoingHeaders("trace-abc123");
        System.out.println("Service A sent: " + headersFromA);

        String traceIdSeenByB = serviceBExtractTraceId(headersFromA);
        System.out.println("Service B extracted trace ID: " + traceIdSeenByB
                + " -- NULL! Service B's library doesn't recognize Service A's custom header, trace is BROKEN here.");
    }
}
```

How to run: `java IncompatibleCustomHeaders.java`

`serviceAOutgoingHeaders` sends `"X-MyCompany-Trace"`, but `serviceBExtractTraceId` looks specifically for `"X-Trace-Id"` — a different name entirely. The extraction returns `null`, meaning Service B has no idea this request is part of an existing trace and would start a completely new, disconnected one — exactly the interoperability failure standardized formats exist to prevent.

### Level 2 — Intermediate

```java
// File: W3CTraceparentInteroperates.java -- BOTH services use the
// STANDARD W3C traceparent header format; regardless of which tracing
// library each one uses internally, the header format itself lets them interoperate.
import java.util.*;

public class W3CTraceparentInteroperates {
    static String buildTraceparent(String traceId, String spanId, boolean sampled) {
        return "00-" + traceId + "-" + spanId + "-" + (sampled ? "01" : "00"); // version-traceId-spanId-flags
    }

    static Map<String, String> serviceAOutgoingHeaders(String traceId, String spanId) {
        return Map.of("traceparent", buildTraceparent(traceId, spanId, true)); // STANDARD header name
    }

    static String serviceBExtractTraceId(Map<String, String> incomingHeaders) {
        String traceparent = incomingHeaders.get("traceparent"); // Service B looks for the SAME standard name
        if (traceparent == null) return null;
        String[] parts = traceparent.split("-");
        return parts[1]; // the traceId field
    }

    public static void main(String[] args) {
        Map<String, String> headersFromA = serviceAOutgoingHeaders("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7");
        System.out.println("Service A sent: " + headersFromA);

        String traceIdSeenByB = serviceBExtractTraceId(headersFromA);
        System.out.println("Service B extracted trace ID: " + traceIdSeenByB
                + " -- CORRECTLY extracted, because BOTH speak the standard traceparent format.");
    }
}
```

How to run: `java W3CTraceparentInteroperates.java`

Both `serviceAOutgoingHeaders` and `serviceBExtractTraceId` use the same standard header name, `"traceparent"`, and the same standard field layout (`version-traceId-spanId-flags`). Service B correctly extracts the trace ID Service A generated, even though the two "services" here represent potentially completely different tracing library implementations — the shared *format*, not a shared library, is what makes this work.

### Level 3 — Advanced

```java
// File: ParseTraceparentWithSamplingFlag.java -- fully parses a
// traceparent header into its four structured fields, including the
// SAMPLING flag, which determines whether this request's spans should
// actually be recorded and exported (see sampling strategies).
import java.util.*;

public class ParseTraceparentWithSamplingFlag {
    record TraceContext(String version, String traceId, String parentSpanId, boolean sampled) {}

    static TraceContext parseTraceparent(String header) {
        String[] parts = header.split("-");
        if (parts.length != 4) throw new IllegalArgumentException("malformed traceparent: " + header);
        String version = parts[0];
        String traceId = parts[1];
        String spanId = parts[2];
        boolean sampled = (Integer.parseInt(parts[3], 16) & 0x01) == 1; // bit 0 of the flags byte
        return new TraceContext(version, traceId, spanId, sampled);
    }

    static String buildTraceparent(String traceId, String spanId, boolean sampled) {
        return "00-" + traceId + "-" + spanId + "-" + (sampled ? "01" : "00");
    }

    public static void main(String[] args) {
        String sampledHeader = buildTraceparent("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7", true);
        String unsampledHeader = buildTraceparent("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7", false);

        TraceContext sampledContext = parseTraceparent(sampledHeader);
        TraceContext unsampledContext = parseTraceparent(unsampledHeader);

        System.out.println("Sampled header parsed: " + sampledContext + " -- this service SHOULD record and export its spans for this trace.");
        System.out.println("Unsampled header parsed: " + unsampledContext + " -- this service should SKIP detailed span recording (still propagate the header though).");
    }
}
```

How to run: `java ParseTraceparentWithSamplingFlag.java`

`parseTraceparent` splits the header on `-` and extracts all four W3C fields, including converting the hex flags byte into a boolean `sampled` value by checking bit 0. The two constructed headers differ only in their final flags byte (`01` versus `00`), and parsing each correctly recovers the intended sampling decision — a downstream service reading `sampled=false` knows it should still propagate the trace context onward (so any *other* service further down the chain has the option to sample), but should skip the overhead of recording and exporting its own detailed spans for this particular, unsampled trace.

## 6. Walkthrough

Trace `ParseTraceparentWithSamplingFlag.main` in order. **First**, `buildTraceparent` is called twice, producing two header strings identical except for their final segment: `"...-01"` for the sampled case and `"...-00"` for the unsampled case.

**Next**, `parseTraceparent(sampledHeader)` runs: `header.split("-")` produces four parts (`"00"`, the trace ID, the span ID, and `"01"`). `version`, `traceId`, and `spanId` are assigned directly from the first three parts. `sampled` is computed as `(Integer.parseInt("01", 16) & 0x01) == 1` — `Integer.parseInt("01", 16)` evaluates to `1`, and `1 & 0x01` is `1`, which equals `1`, so `sampled` is `true`.

**Then**, `parseTraceparent(unsampledHeader)` runs the same way, except its fourth part is `"00"`. `Integer.parseInt("00", 16)` evaluates to `0`, and `0 & 0x01` is `0`, which does not equal `1`, so `sampled` is `false`.

**Finally**, `main` prints both parsed `TraceContext` records and explains what each sampling decision means for a receiving service: a `sampled=true` context means this service should record and export detailed span data for this trace, while `sampled=false` means it should skip that overhead for this particular trace but still forward the (unsampled) context onward, since propagation and the sampling decision are two separate concerns.

```
buildTraceparent(..., sampled=true)  -> "00-<traceId>-<spanId>-01"
buildTraceparent(..., sampled=false) -> "00-<traceId>-<spanId>-00"
parse("...-01") -> flags=01 -> 01 & 0x01 = 1 -> sampled=true
parse("...-00") -> flags=00 -> 00 & 0x01 = 0 -> sampled=false
```

## 7. Gotchas & takeaways

> Mixing W3C Trace Context and B3 across a system without an explicit bridge (a service that reads one format and writes the other where they meet) silently breaks trace continuity at that boundary — the two formats are not directly compatible without translation, even though they express similar underlying information.

- W3C Trace Context (`traceparent`/`tracestate`) and B3 (`b3` or `X-B3-*` headers) are standardized formats for propagating trace ID, span ID, and sampling decisions across service boundaries.
- Standardization matters specifically because it lets services using different tracing libraries or vendors correctly continue the same trace, rather than each starting a disconnected one.
- The sampling flag embedded in these headers determines whether a given trace's spans should be recorded and exported by receiving services, independent of whether the context itself continues to propagate.
- W3C Trace Context is the modern default (used by OpenTelemetry); B3 remains common in Zipkin-centric or legacy Spring Cloud Sleuth deployments — bridge explicitly if a system mixes both.
