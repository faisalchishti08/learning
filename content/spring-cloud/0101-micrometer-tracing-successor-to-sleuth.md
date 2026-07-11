---
card: spring-cloud
gi: 101
slug: micrometer-tracing-successor-to-sleuth
title: "Micrometer Tracing (successor to Sleuth)"
---

## 1. What it is

Micrometer Tracing is the tracing instrumentation facade that replaced Spring Cloud Sleuth starting with Spring Boot 3 — it provides the same core job Sleuth did (automatically creating and propagating spans across web requests, messaging, and scheduled tasks) but as a vendor-neutral API, with separate bridge dependencies (`micrometer-tracing-bridge-brave` for Zipkin/Brave, `micrometer-tracing-bridge-otel` for OpenTelemetry) plugging in the actual tracer implementation underneath, mirroring how Micrometer itself already decouples application metrics code from any specific metrics backend.

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

```java
@Autowired Tracer tracer;

Span span = tracer.nextSpan().name("processOrder").start();
try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
    // work traced by this span
} finally {
    span.end();
}
```

## 2. Why & when

Spring Cloud Sleuth was tightly coupled to Brave (Zipkin's tracer library) as its underlying implementation, which meant switching to a different tracing backend, or aligning with the broader industry's move toward OpenTelemetry as a standard, required significant rework. Micrometer Tracing addresses this the same way Micrometer's metrics API already addressed the equivalent problem for metrics: application and framework code (Spring MVC's auto-instrumentation, Spring Cloud Stream's auto-instrumentation, and so on) is written once against the neutral `Tracer` API, and a bridge dependency — swappable independently of that code — determines whether spans actually flow to Brave/Zipkin or to OpenTelemetry underneath.

Reach for Micrometer Tracing when:

- Building or maintaining a Spring Boot 3+ application that needs distributed tracing — Micrometer Tracing is the current, actively maintained tracing facade; Sleuth is in maintenance mode and not the starting point for new work.
- Migrating an existing Spring Boot 2 application (that used Sleuth) forward to Spring Boot 3 — understanding Micrometer Tracing's API differences from Sleuth's is a prerequisite for that migration (a later card covers this specifically).
- Choosing or later switching tracing backends — because instrumentation code is written against the neutral `Tracer` API rather than directly against Brave or OpenTelemetry types, switching the bridge dependency later doesn't require rewriting instrumentation code that was written correctly against the abstraction.

## 3. Core concept

```
 application/framework code:
   Tracer.nextSpan().name("...").start() / tracer.withSpan(span) / span.end()
   -- written ONCE, against the neutral Micrometer Tracing API

 bridge dependency determines the ACTUAL tracer underneath:
   micrometer-tracing-bridge-brave  -> Brave -> Zipkin
   micrometer-tracing-bridge-otel   -> OpenTelemetry SDK -> Zipkin, Jaeger, or any OTLP-compatible backend

 SAME instrumentation code, different bridge dependency = different backend, zero code changes
```

Auto-configuration (Spring Boot's own web, messaging, and scheduling instrumentation) already calls this neutral API internally, so most applications get spans automatically without writing any `Tracer` calls directly — the API shown above matters mainly for custom, manually-created spans.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls the neutral Micrometer Tracing API which is bridged to either Brave and Zipkin or OpenTelemetry depending purely on which bridge dependency is present on the classpath">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Micrometer Tracing</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Tracer API (neutral)</text>

  <rect x="60" y="120" width="200" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="160" y="140" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">bridge-brave</text>
  <text x="160" y="154" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; Brave -&gt; Zipkin</text>

  <rect x="380" y="120" width="200" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="480" y="140" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">bridge-otel</text>
  <text x="480" y="154" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; OpenTelemetry SDK</text>

  <defs><marker id="a101" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="170" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a101)"/>
  <line x1="360" y1="66" x2="470" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a101)"/>
</svg>

Same neutral API at the top; the bridge dependency underneath is a build-time choice, not an application code choice.

## 5. Runnable example

The scenario: model a minimal `Tracer` facade with a swappable backend "bridge," used identically by application code regardless of which bridge is active — proving that switching backends doesn't require touching instrumentation code. Start with a single hardcoded backend, then introduce the bridge abstraction, then swap bridges at runtime to show identical calling code producing output routed to two different backends.

### Level 1 — Basic

Application code directly calling a Brave-shaped API — no abstraction yet, modeling how Sleuth-era code (and pre-Micrometer-Tracing designs generally) coupled instrumentation directly to one tracer implementation.

```java
public class MicrometerTracingLevel1 {
    // stands in for Brave's own tracer API, called DIRECTLY
    static class BraveStyleTracer {
        void startSpan(String name) { System.out.println("[Brave] span started: " + name); }
        void endSpan(String name) { System.out.println("[Brave] span reported to Zipkin: " + name); }
    }

    public static void main(String[] args) {
        BraveStyleTracer tracer = new BraveStyleTracer();

        tracer.startSpan("processOrder");
        // ... business logic here ...
        tracer.endSpan("processOrder");
    }
}
```

How to run: `java MicrometerTracingLevel1.java`

`main` calls `BraveStyleTracer` methods directly — if the backend ever needed to change to OpenTelemetry, every call site referencing `BraveStyleTracer` would need rewriting, which is exactly the coupling Micrometer Tracing's neutral API exists to remove.

### Level 2 — Intermediate

Introduce a neutral `Tracer` interface (modeling Micrometer Tracing's own API) with one concrete `Brave`-backed implementation — application code now calls the interface, not the implementation directly.

```java
public class MicrometerTracingLevel2 {
    interface Tracer { // models the neutral io.micrometer.tracing.Tracer API
        void startSpan(String name);
        void endSpan(String name);
    }

    static class BraveBridge implements Tracer {
        public void startSpan(String name) { System.out.println("[Brave bridge] span started: " + name); }
        public void endSpan(String name) { System.out.println("[Brave bridge] reported to Zipkin: " + name); }
    }

    // application code depends ONLY on the Tracer interface, never on BraveBridge directly
    static void processOrder(Tracer tracer) {
        tracer.startSpan("processOrder");
        // ... business logic ...
        tracer.endSpan("processOrder");
    }

    public static void main(String[] args) {
        Tracer tracer = new BraveBridge(); // the ONE line that decides which backend is active
        processOrder(tracer);
    }
}
```

How to run: `java MicrometerTracingLevel2.java`

`processOrder` is typed to accept `Tracer`, the neutral interface — it has no reference to `BraveBridge` anywhere in its own body, meaning `processOrder`'s code would compile and run identically against any other `Tracer` implementation, unchanged.

### Level 3 — Advanced

Add a second bridge (OpenTelemetry-style) and swap between them purely by changing which implementation is constructed — `processOrder` (and any other instrumentation code) remains completely untouched across both runs.

```java
public class MicrometerTracingLevel3 {
    interface Tracer {
        void startSpan(String name);
        void endSpan(String name);
    }

    static class BraveBridge implements Tracer {
        public void startSpan(String name) { System.out.println("[Brave bridge] span started: " + name); }
        public void endSpan(String name) { System.out.println("[Brave bridge] reported to Zipkin: " + name); }
    }

    static class OtelBridge implements Tracer {
        public void startSpan(String name) { System.out.println("[OTel bridge] span started: " + name); }
        public void endSpan(String name) { System.out.println("[OTel bridge] reported via OTLP exporter: " + name); }
    }

    // IDENTICAL instrumentation code -- reused, unmodified, against EITHER bridge below
    static void processOrder(Tracer tracer) {
        tracer.startSpan("processOrder");
        tracer.startSpan("chargePayment"); // a nested span, still through the same neutral interface
        tracer.endSpan("chargePayment");
        tracer.endSpan("processOrder");
    }

    public static void main(String[] args) {
        System.out.println("-- running with Brave bridge --");
        processOrder(new BraveBridge());

        System.out.println("-- running with OpenTelemetry bridge --");
        processOrder(new OtelBridge()); // ONLY this constructor call changed
    }
}
```

How to run: `java MicrometerTracingLevel3.java`

`processOrder`'s source code is byte-for-byte identical in both calls — the only difference between the two runs is which `Tracer` implementation was constructed and passed in, exactly mirroring how switching `micrometer-tracing-bridge-brave` for `micrometer-tracing-bridge-otel` in a real Spring Boot application's dependencies changes where spans end up, without touching any `@Observed` method, `Tracer.nextSpan()` call, or other instrumentation code.

## 6. Walkthrough

Trace the second `processOrder` call in Level 3.

1. `processOrder(new OtelBridge())` is called — a new `OtelBridge` instance is constructed and passed as the `tracer` parameter.
2. Inside `processOrder`, `tracer.startSpan("processOrder")` executes — because `tracer`'s runtime type is `OtelBridge`, this dispatches to `OtelBridge.startSpan`, printing `"[OTel bridge] span started: processOrder"`.
3. `tracer.startSpan("chargePayment")` runs next, again dispatching to `OtelBridge.startSpan`, printing `"[OTel bridge] span started: chargePayment"` — this models a nested span, created while `"processOrder"`'s span is still active.
4. `tracer.endSpan("chargePayment")` dispatches to `OtelBridge.endSpan`, printing the reporting message for the inner span first.
5. `tracer.endSpan("processOrder")` dispatches to `OtelBridge.endSpan` last, printing the reporting message for the outer span — spans end in the reverse order they started, `chargePayment` before `processOrder`, exactly mirroring real nested span lifecycle management.
6. Every one of these four calls went through the exact same four lines of `processOrder` source code that ran during the first (`BraveBridge`) call — only the object being called on differed, which is the entire point: application-level instrumentation code never needed to know or care which bridge was actually active underneath it.

```
processOrder(tracer):
  tracer.startSpan("processOrder")     <- dispatches to whichever bridge was passed in
  tracer.startSpan("chargePayment")    <- nested span, same dispatch mechanism
  tracer.endSpan("chargePayment")      <- ends inner span first
  tracer.endSpan("processOrder")       <- ends outer span last
same 4 calls, 2 different bridges, SAME processOrder source both times
```

## 7. Gotchas & takeaways

> **Gotcha:** exactly one tracing bridge (`bridge-brave` or `bridge-otel`) should be on the classpath at a time — having both present simultaneously, without deliberately intending a dual-export setup, produces ambiguous or duplicated span reporting, since Micrometer Tracing's auto-configuration expects a single active tracer implementation to bind to.

- Micrometer Tracing is the current, actively maintained successor to Spring Cloud Sleuth in Spring Boot 3+ — new tracing work should target Micrometer Tracing's API directly, not Sleuth's.
- The neutral `Tracer` API is what most auto-instrumentation (Spring MVC, Spring Cloud Stream, `@Scheduled` methods) already calls internally, so most applications get correctly-propagated spans for web requests, messages, and scheduled tasks with zero manual `Tracer` calls at all — manual calls matter mainly for custom spans around specific business logic.
- Switching tracing backends (Brave/Zipkin to OpenTelemetry, or vice versa) is a dependency swap, not an instrumentation rewrite, exactly as long as instrumentation code was written against the neutral API rather than reaching into a bridge-specific type directly.
- The following cards in this section cover the two concrete bridges (Brave/Zipkin, OpenTelemetry) and the propagation formats (B3, W3C) each one typically uses in more depth — Micrometer Tracing itself is the shared foundation both build on.
