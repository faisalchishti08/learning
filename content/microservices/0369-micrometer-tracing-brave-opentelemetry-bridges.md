---
card: microservices
gi: 369
slug: micrometer-tracing-brave-opentelemetry-bridges
title: "Micrometer Tracing (Brave / OpenTelemetry bridges)"
---

## 1. What it is

**Micrometer Tracing** is a vendor-neutral tracing facade for Spring applications — mirroring [Micrometer's metrics facade](0366-micrometer-metrics-facade.md), but for [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) instead of metrics. Application code creates spans and records tracing context against Micrometer Tracing's own stable API, and a configured **bridge** (to Brave, Zipkin's tracer library, or to OpenTelemetry) determines which actual tracing implementation and export format is used underneath, without application code needing to reference either directly.

## 2. Why & when

Two major tracing ecosystems exist in the Java world — Brave (Zipkin's tracer, older, still widely deployed) and OpenTelemetry (the newer, now-dominant industry standard). Application code that called Brave's API directly would need rewriting to move to OpenTelemetry, and vice versa — exactly the coupling problem [Micrometer's metrics facade](0366-micrometer-metrics-facade.md) solves for metrics. Micrometer Tracing exists to solve the same problem for tracing: write against one stable facade, and switch the underlying bridge (Brave or OpenTelemetry) via configuration and dependencies, not code changes.

Use Micrometer Tracing as the default way to create custom spans or access tracing context in Spring application code, rather than depending on Brave's or OpenTelemetry's APIs directly. Choose the OpenTelemetry bridge for new projects, since it's the modern, broadly-adopted standard (and the one that naturally leads into [OTLP export](0371-spring-boot-opentelemetry-otlp-export.md)); the Brave bridge remains relevant for systems already invested in a Zipkin-centric tracing infrastructure.

## 3. Core concept

Micrometer Tracing's `Tracer` interface exposes span creation and management (`tracer.nextSpan()`, `span.tag(...)`, `span.end()`) as a stable API; the configured bridge (a `brave-micrometer-tracing-bridge` or `micrometer-tracing-bridge-otel` dependency) implements that interface using the corresponding underlying tracer, handling the actual span recording, context propagation format (see [W3C Trace Context / B3](0353-trace-context-w3c-trace-context-b3-headers.md)), and export mechanics.

```java
@Autowired Tracer tracer; // Micrometer Tracing's OWN facade interface, never Brave or OTel directly
Span span = tracer.nextSpan().name("chargePayment").start();
try (Tracer.SpanInScope ignored = tracer.withSpan(span)) {
    chargePayment(order);
} finally { span.end(); }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls the same Micrometer Tracing Tracer API; depending on which bridge is configured, spans are recorded via Brave or via OpenTelemetry, with no application code change">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Application: Tracer API</text>

  <line x1="280" y1="49" x2="140" y2="90" stroke="#8b949e" marker-end="url(#a369)"/>
  <rect x="20" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Brave bridge</text>

  <line x1="360" y1="49" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a369)"/>
  <rect x="380" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OpenTelemetry bridge</text>

  <text x="320" y="150" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">SAME application code, DIFFERENT tracing implementation, based purely on configuration.</text>

  <defs><marker id="a369" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Application code creates spans against one stable facade; the configured bridge determines whether Brave or OpenTelemetry actually implements tracing underneath.

## 5. Runnable example

Scenario: a checkout operation, first instrumented directly against a simulated vendor-specific tracer API (tightly coupled), then rebuilt against a facade interface matching Micrometer Tracing's model, and finally shown running unchanged against two different simulated bridges.

### Level 1 — Basic

```java
// File: DirectBraveApiCoupling.java -- application code calls a
// SPECIFIC tracer library's API directly; switching to a different
// tracing implementation means rewriting every call site.
import java.util.*;

public class DirectBraveApiCoupling {
    // Simulates Brave's OWN specific span API shape.
    static class BraveSpecificSpan {
        String name; List<String> tags = new ArrayList<>();
        void braveSpecificTag(String key, String value) { tags.add(key + "=" + value); } // Brave-SPECIFIC method name
    }

    static void chargePayment(String orderId) {
        BraveSpecificSpan span = new BraveSpecificSpan();
        span.name = "chargePayment";
        span.braveSpecificTag("orderId", orderId); // TIED directly to Brave's API shape
        System.out.println("Recorded span (Brave-specific): " + span.name + " tags=" + span.tags);
    }

    public static void main(String[] args) {
        chargePayment("order-1");
        System.out.println("Switching to OpenTelemetry would require rewriting EVERY call site using 'BraveSpecificSpan' directly.");
    }
}
```

How to run: `java DirectBraveApiCoupling.java`

`chargePayment` constructs and tags a span using `BraveSpecificSpan`'s own method names directly — a shape specific to this one simulated tracer library. Moving to a different tracing implementation would require finding and rewriting every call site coupled this tightly to Brave's specific API.

### Level 2 — Intermediate

```java
// File: FacadeBasedTracing.java -- application code depends ONLY on a
// stable FACADE interface (mirroring Micrometer Tracing's Tracer); the
// actual tracer implementation is injected separately.
import java.util.*;

public class FacadeBasedTracing {
    interface Tracer { Span nextSpan(String name); } // the STABLE facade -- mirrors Micrometer Tracing's own API
    interface Span { void tag(String key, String value); void end(); }

    static void chargePayment(Tracer tracer, String orderId) { // depends ONLY on the facade, never a specific vendor
        Span span = tracer.nextSpan("chargePayment");
        span.tag("orderId", orderId);
        span.end();
    }

    // ONE concrete implementation -- could be swapped for a different one with NO change above.
    static class InMemoryTracer implements Tracer {
        List<String> recordedSpans = new ArrayList<>();
        public Span nextSpan(String name) {
            List<String> tags = new ArrayList<>();
            return new Span() {
                public void tag(String key, String value) { tags.add(key + "=" + value); }
                public void end() { recordedSpans.add(name + " " + tags); }
            };
        }
    }

    public static void main(String[] args) {
        InMemoryTracer tracer = new InMemoryTracer();
        chargePayment(tracer, "order-1"); // tracer INJECTED, not hardcoded inside chargePayment

        System.out.println("Recorded spans: " + tracer.recordedSpans);
        System.out.println("chargePayment() NEVER mentions a specific tracing vendor -- only the facade interface.");
    }
}
```

How to run: `java FacadeBasedTracing.java`

`chargePayment` depends only on the `Tracer` and `Span` interfaces, never on `InMemoryTracer` specifically — that's just one implementation, passed in as a parameter. This mirrors real Micrometer Tracing-based code, which never mentions Brave or OpenTelemetry by name.

### Level 3 — Advanced

```java
// File: SameCodeTwoBridges.java -- the IDENTICAL chargePayment function
// runs unchanged against TWO DIFFERENT simulated bridge implementations
// (Brave-style and OpenTelemetry-style), proving true tracing portability.
import java.util.*;

public class SameCodeTwoBridges {
    interface Tracer { Span nextSpan(String name); }
    interface Span { void tag(String key, String value); void end(); }

    static void chargePayment(Tracer tracer, String orderId) { // the ONE piece of application code -- vendor-agnostic
        Span span = tracer.nextSpan("chargePayment");
        span.tag("orderId", orderId);
        span.end();
    }

    static class BraveBridgeTracer implements Tracer {
        public Span nextSpan(String name) {
            return new Span() {
                List<String> tags = new ArrayList<>();
                public void tag(String key, String value) { tags.add(key + "=" + value); }
                public void end() { System.out.println("  [Brave bridge] exported span '" + name + "' " + tags + " in Zipkin format"); }
            };
        }
    }

    static class OtelBridgeTracer implements Tracer {
        public Span nextSpan(String name) {
            return new Span() {
                List<String> tags = new ArrayList<>();
                public void tag(String key, String value) { tags.add(key + "=" + value); }
                public void end() { System.out.println("  [OpenTelemetry bridge] exported span '" + name + "' " + tags + " via OTLP"); }
            };
        }
    }

    public static void main(String[] args) {
        System.out.println("--- Configured with Brave bridge ---");
        chargePayment(new BraveBridgeTracer(), "order-1"); // SAME chargePayment function

        System.out.println("--- Configured with OpenTelemetry bridge ---");
        chargePayment(new OtelBridgeTracer(), "order-2"); // SAME chargePayment function, DIFFERENT bridge

        System.out.println("chargePayment() is IDENTICAL code in both cases -- only the injected Tracer implementation differs.");
    }
}
```

How to run: `java SameCodeTwoBridges.java`

`chargePayment` is defined exactly once, with no reference to either `BraveBridgeTracer` or `OtelBridgeTracer`. Calling it with a `BraveBridgeTracer` produces a span exported in a Zipkin-style format; calling the identical function with an `OtelBridgeTracer` produces a span exported via OTLP instead. The application-level tracing logic never changed — only the injected bridge implementation did, exactly the portability Micrometer Tracing's real facade design provides between Brave and OpenTelemetry.

## 6. Walkthrough

Trace `SameCodeTwoBridges.main` in order. **First**, `chargePayment(new BraveBridgeTracer(), "order-1")` runs: inside `chargePayment`, `tracer.nextSpan("chargePayment")` calls `BraveBridgeTracer.nextSpan`, which returns an anonymous `Span` implementation closing over an empty `tags` list. `span.tag("orderId", "order-1")` runs, adding `"orderId=order-1"` to that span's `tags`. `span.end()` runs, printing a message describing the Brave-bridge-style export.

**Next**, `chargePayment(new OtelBridgeTracer(), "order-2")` runs: this time `tracer.nextSpan("chargePayment")` calls `OtelBridgeTracer.nextSpan` instead, returning a *different* anonymous `Span` implementation with its own `tags` list. `span.tag("orderId", "order-2")` runs, adding `"orderId=order-2"` to this span's tags. `span.end()` runs, printing a message describing the OpenTelemetry-bridge-style export instead.

**In both cases**, the exact same three lines inside `chargePayment` executed — `tracer.nextSpan(...)`, `span.tag(...)`, `span.end()` — with the only difference being which concrete `Tracer` implementation was passed in as the `tracer` parameter, determining which `nextSpan` implementation actually ran and, consequently, which export format was used.

**Finally**, `main` prints a closing observation confirming that `chargePayment`'s source code is identical in both cases — only the injected tracer implementation determined whether the resulting span was exported via Brave/Zipkin or via OpenTelemetry/OTLP.

```
chargePayment(BraveBridgeTracer, order-1)  -> nextSpan/tag/end -> exported via Brave (Zipkin format)
chargePayment(OtelBridgeTracer, order-2)   -> nextSpan/tag/end -> exported via OpenTelemetry (OTLP)
SAME chargePayment() code in both cases -- only the injected Tracer differs.
```

## 7. Gotchas & takeaways

> Mixing direct calls to Brave's API in some parts of a codebase with Micrometer Tracing's facade in others creates spans that may not correctly nest or propagate context together, since they're using potentially different underlying span models — commit to the facade consistently across the whole application, rather than mixing direct vendor API usage with facade usage.

- Micrometer Tracing is a vendor-neutral facade for distributed tracing, mirroring Micrometer's metrics facade design — application code depends only on its stable `Tracer`/`Span` API.
- A configured bridge (Brave or OpenTelemetry) determines the actual underlying tracing implementation and export format, entirely separate from application code.
- Choose the OpenTelemetry bridge for new work, since it's the modern industry standard and leads naturally into [OTLP export](0371-spring-boot-opentelemetry-otlp-export.md); use the Brave bridge only for systems already invested in Zipkin-centric infrastructure.
- This same facade-and-bridge pattern is what lets [context propagation across threads and reactive code](0370-context-propagation-across-threads-reactive-micrometer-conte.md) work consistently regardless of which underlying tracer is configured.
