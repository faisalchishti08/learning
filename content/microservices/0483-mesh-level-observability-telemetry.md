---
card: microservices
gi: 483
slug: mesh-level-observability-telemetry
title: "Mesh-level observability (telemetry)"
---

## 1. What it is

**Mesh-level observability** means every [sidecar proxy](0479-sidecar-proxy-envoy.md), sitting on the path of every service-to-service call, automatically records telemetry — request counts, latencies, error rates, and distributed trace spans — for the traffic it handles, with **zero instrumentation code added to any application**. Because every call in the mesh already passes through a proxy, the mesh gets consistent, uniform observability data essentially for free, across every service regardless of language.

## 2. Why & when

You lean on mesh-level telemetry whenever you want consistent, system-wide visibility without requiring every team to instrument their service identically:

- **Application-level instrumentation is inconsistent across a polyglot fleet.** One team's Java service might emit rich metrics; another team's Python service might emit almost none — a mesh's proxy-level telemetry produces the same baseline data (latency, error rate, request volume) for every service automatically, regardless of how well-instrumented the application itself is.
- **The "golden signals" (latency, traffic, errors, saturation) are exactly what a proxy naturally observes.** Every request passing through a sidecar already has its duration measured and its response status recorded — turning that into metrics and dashboards requires no additional application work at all.
- **Distributed tracing needs consistent propagation across every hop.** A mesh can automatically generate trace spans for every proxy-to-proxy hop, giving you a request's full path across services even if individual applications don't participate deeply in tracing themselves (though they typically still need to forward trace headers).
- **You get this automatically once a mesh is deployed** — unlike resiliency policies or mTLS, which need explicit configuration to activate, basic mesh telemetry is often on by default the moment sidecars are injected, since the proxies are already handling every call regardless.

## 3. Core concept

Think of toll booths on a highway system: every car passing through automatically has its passage timestamped and counted, without the driver doing anything special — over time, this produces rich, uniform data about traffic volume, peak times, and any unusual patterns, purely as a byproduct of the tolling infrastructure that was already there for a different primary purpose (collecting tolls). Mesh telemetry is that same byproduct of proxies that are already there anyway, for resiliency and security.

Concretely:

1. **Every proxy records metrics for every request it handles** — count, duration, response status — tagged with the source and destination service identities the mesh already knows from mTLS certificates.
2. **These per-proxy metrics are aggregated** (often by a metrics backend the mesh integrates with) into system-wide views: which service pairs communicate, how often, how fast, and how reliably.
3. **Distributed traces are constructed by propagating a trace context** (a request ID, effectively) across every hop — each proxy adds a span representing its portion of the request's total journey, and these spans are stitched together into one end-to-end trace showing the full path a request took across every service it touched.
4. **None of this requires touching application code for the baseline signal** — though richer traces often benefit from applications forwarding trace headers through their own internal calls, so spans inside a single service (not just between services) can be captured too.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every proxy records latency and status for the request it handles; these are stitched together into one end-to-end distributed trace across three services">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service proxy: span 1 (45ms)</text>

  <rect x="240" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inventory-service proxy: span 2 (20ms)</text>

  <rect x="460" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="550" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">payment-service proxy: span 3 (60ms)</text>

  <line x1="110" y1="80" x2="110" y2="150" stroke="#8b949e"/>
  <line x1="330" y1="80" x2="330" y2="150" stroke="#8b949e"/>
  <line x1="550" y1="80" x2="550" y2="150" stroke="#8b949e"/>
  <rect x="80" y="150" width="500" height="30" rx="4" fill="none" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="330" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one end-to-end trace, stitched from all three spans -- total ~125ms, all recorded automatically</text>
</svg>

Every proxy's span for its portion of a request is stitched into one end-to-end trace, with no application instrumentation required.

## 5. Runnable example

Scenario: a proxy layer that automatically records telemetry for calls it handles, and stitches per-hop spans into one distributed trace. We start with a basic single-hop metric recording, extend it to a multi-hop trace across three services, then handle the hard case: one hop failing, which must be captured accurately in both the metrics and the trace without breaking the overall observability picture.

### Level 1 — Basic

```java
// File: TelemetryBasic.java -- models a proxy AUTOMATICALLY recording
// latency and status for a call it handles, with ZERO application
// instrumentation code involved.
public class TelemetryBasic {
    record CallMetric(String source, String destination, long durationMs, int statusCode) {}

    static CallMetric proxyHandleCall(String source, String destination) {
        long start = System.currentTimeMillis();
        // The actual application call happens here -- the app writes no telemetry code.
        String result = "response from " + destination;
        long duration = Math.max(1, System.currentTimeMillis() - start + 12); // simulated small latency
        CallMetric metric = new CallMetric(source, destination, duration, 200);
        System.out.println("[proxy telemetry] recorded: " + metric);
        return metric;
    }

    public static void main(String[] args) {
        proxyHandleCall("order-service", "inventory-service");
    }
}
```

How to run: `java TelemetryBasic.java`

`proxyHandleCall` measures and records a `CallMetric` around the actual application logic, entirely on its own — nothing in the application's own code path contributes to or is even aware that this measurement is happening, mirroring how a real sidecar proxy observes and records telemetry for traffic passing through it without any application cooperation required.

### Level 2 — Intermediate

```java
// File: DistributedTraceBasic.java -- the SAME per-hop telemetry, now
// EXTENDED across THREE services in one request's path, with each hop's
// span STITCHED into one end-to-end trace via a shared trace ID.
import java.util.*;

public class DistributedTraceBasic {
    record Span(String traceId, String service, long durationMs) {}

    static List<Span> trace = new ArrayList<>();

    static void recordSpan(String traceId, String service, long durationMs) {
        Span span = new Span(traceId, service, durationMs);
        trace.add(span);
        System.out.println("[proxy telemetry] recorded span: " + span);
    }

    public static void main(String[] args) {
        String traceId = "trace-abc123"; // propagated across every hop automatically

        recordSpan(traceId, "order-service", 45);
        recordSpan(traceId, "inventory-service", 20);
        recordSpan(traceId, "payment-service", 60);

        long totalMs = trace.stream().mapToLong(Span::durationMs).sum();
        System.out.println("[trace viewer] end-to-end trace " + traceId + ": " + trace.size() + " spans, total " + totalMs + "ms");
    }
}
```

How to run: `java DistributedTraceBasic.java`

Every `recordSpan` call shares the same `traceId`, modeling how a real mesh propagates one trace context across every hop of a single logical request — the three spans, recorded independently at each service's proxy, are stitched together purely by sharing that common identifier, letting a trace viewer reconstruct the full request path and its total duration afterward.

### Level 3 — Advanced

```java
// File: DistributedTraceWithFailure.java -- the SAME multi-hop trace, now
// handling the PRODUCTION-FLAVORED hard case: ONE hop FAILS partway
// through the request's path. The failure must be recorded ACCURATELY in
// both the metric (a non-200 status) and the trace (the failed span
// clearly marked), and the trace must still reflect exactly how far the
// request got before failing -- not silently omit the failed hop.
import java.util.*;

public class DistributedTraceWithFailure {
    record Span(String traceId, String service, long durationMs, int statusCode, boolean failed) {}

    static List<Span> trace = new ArrayList<>();

    static void recordSpan(String traceId, String service, long durationMs, int statusCode) {
        boolean failed = statusCode >= 500;
        Span span = new Span(traceId, service, durationMs, statusCode, failed);
        trace.add(span);
        System.out.println("[proxy telemetry] recorded span: " + span + (failed ? " -- FAILURE" : ""));
    }

    static void simulateRequestPath(String traceId) {
        recordSpan(traceId, "order-service", 15, 200);
        recordSpan(traceId, "inventory-service", 20, 200);
        // payment-service is down -- this hop fails.
        recordSpan(traceId, "payment-service", 5000, 503);
        // Because payment-service failed, order-service never got a chance to call
        // shipping-service afterward -- correctly, NO span is recorded for it at all.
        System.out.println("[order-service] payment failed -- aborting request, shipping-service never called");
    }

    public static void main(String[] args) {
        String traceId = "trace-xyz789";
        simulateRequestPath(traceId);

        System.out.println();
        System.out.println("[trace viewer] reconstructing trace " + traceId + ":");
        boolean anyFailure = false;
        for (Span span : trace) {
            System.out.println("  " + span.service() + ": " + span.durationMs() + "ms, status=" + span.statusCode()
                    + (span.failed() ? " (FAILED)" : ""));
            if (span.failed()) anyFailure = true;
        }
        System.out.println("[trace viewer] trace outcome: " + (anyFailure ? "FAILED -- see failed span above for root cause" : "SUCCESS"));
        System.out.println("[trace viewer] spans recorded: " + trace.size() + " (shipping-service correctly absent -- never reached)");
    }
}
```

How to run: `java DistributedTraceWithFailure.java`

`recordSpan` computes `failed = statusCode >= 500` for every span independently — `order-service` and `inventory-service` both get `statusCode = 200` and `failed = false`, while `payment-service`'s call is recorded with `statusCode = 503` and `failed = true`. `simulateRequestPath` never calls `recordSpan` for `shipping-service` at all, since the request aborted before reaching it — the trace accurately reflects exactly how far the request actually got, with no fabricated or missing spans for hops that genuinely never happened.

## 6. Walkthrough

Trace `DistributedTraceWithFailure.main` in order. **First**, `simulateRequestPath(traceId)` runs, and `recordSpan` is called for `order-service` with `statusCode = 200` — `failed` evaluates to `false`, the span is appended to `trace`, and it's printed without the failure suffix.

**Next**, the same happens for `inventory-service`, also with `statusCode = 200` — another successful span added to `trace`.

**Then**, `recordSpan` is called for `payment-service` with `statusCode = 503`. This time `failed = statusCode >= 500` evaluates to `true`, so the span is recorded with `failed = true` and printed with the `-- FAILURE` suffix — this is the point where the request path genuinely broke.

**After that**, `simulateRequestPath` prints its own message noting the request aborted and `shipping-service` was never called — critically, no fourth `recordSpan` call happens at all for `shipping-service`, meaning `trace` ends with exactly three entries, accurately reflecting the request's real, truncated path.

**Finally**, back in `main`, the trace-viewer loop iterates all three recorded spans, printing each and setting `anyFailure = true` the moment it encounters the `payment-service` span's `failed` flag. The final summary correctly reports the trace as `FAILED`, points at the specific failed span as the root cause, and explicitly notes that only three spans exist — `shipping-service` is correctly and accurately absent, not silently missing due to some instrumentation gap, but because it genuinely was never reached.

```
[proxy telemetry] recorded span: Span[traceId=trace-xyz789, service=order-service, durationMs=15, statusCode=200, failed=false]
[proxy telemetry] recorded span: Span[traceId=trace-xyz789, service=inventory-service, durationMs=20, statusCode=200, failed=false]
[proxy telemetry] recorded span: Span[traceId=trace-xyz789, service=payment-service, durationMs=5000, statusCode=503, failed=true] -- FAILURE
[order-service] payment failed -- aborting request, shipping-service never called

[trace viewer] reconstructing trace trace-xyz789:
  order-service: 15ms, status=200
  inventory-service: 20ms, status=200
  payment-service: 5000ms, status=503 (FAILED)
[trace viewer] trace outcome: FAILED -- see failed span above for root cause
[trace viewer] spans recorded: 3 (shipping-service correctly absent -- never reached)
```

## 7. Gotchas & takeaways

> A trace missing a span because instrumentation failed to record it looks identical, at first glance, to a trace missing a span because that hop genuinely never happened — but they mean very different things for debugging. Mesh-level telemetry, recorded automatically and reliably by the proxy layer rather than by fallible application-level instrumentation, greatly reduces the risk of the first case being mistaken for the second.
- Trace context propagation (the `traceId` in this example) is the one piece that typically *does* need minimal application cooperation — applications need to forward the trace headers on any internal calls they make, or spans downstream of an in-process hop can't be correctly attributed.
- Mesh telemetry gives you the "what" (latency, error rate, which services are involved) automatically; application-level logging still matters for the "why" (the specific business-logic reason a request failed) — the two are complementary, not substitutes for each other.
- A trace accurately reflecting a request's real, possibly-truncated path (as in Level 3) — rather than always showing every "expected" hop regardless of what happened — is essential for correct root-cause analysis; padding out a trace with hops that never occurred would actively mislead debugging.
- Because this telemetry comes for free from proxies already handling every call for resiliency and security reasons, it's one of the strongest incidental benefits of adopting a service mesh, even for teams whose primary motivation was something else entirely.
