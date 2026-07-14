---
card: microservices
gi: 550
slug: spring-cloud-sleuth-micrometer-tracing-tracing
title: "Spring Cloud Sleuth → Micrometer Tracing (tracing)"
---

## 1. What it is

**Spring Cloud Sleuth** was Spring's original library for automatic [distributed tracing](0525-lack-of-observability.md) instrumentation — generating and propagating trace/span IDs through a request's journey across services, and adding them to logs automatically. As of Spring Boot 3, Sleuth's functionality has been absorbed into **Micrometer Tracing**, a more general observability library (already used for metrics via Micrometer) that now also handles tracing, with bridges to actual tracing backends like Zipkin or OpenTelemetry. The underlying goal is unchanged from what was discussed conceptually for [lack of observability](0525-lack-of-observability.md): automatically propagate a correlation ID through every service hop a request touches, without every service having to implement that propagation by hand.

## 2. Why & when

You add tracing instrumentation whenever a request's journey spans multiple services and you need to reconstruct that journey to diagnose latency or failures:

- **Manually propagating a correlation ID through every service call, as shown conceptually earlier, requires every single service to remember to read an incoming trace ID and pass it along to every outgoing call** — a real, error-prone amount of boilerplate to get right consistently across an entire fleet, and easy for one team's service to quietly break the chain.
- **Micrometer Tracing (and, before it, Sleuth) automates this instrumentation** — it hooks into Spring's own HTTP client and server infrastructure (RestTemplate, WebClient, Spring MVC, WebFlux) so trace and span IDs are generated, propagated in headers, and added to log output automatically, without application code needing to touch trace IDs directly at every call site.
- **The migration from Sleuth to Micrometer Tracing (Spring Boot 3+) reflects a broader consolidation**: Micrometer already provided the metrics instrumentation story for Spring Boot applications (feeding into Prometheus, and other metrics backends), and folding tracing into the same library gives one consistent instrumentation API for both metrics and traces, rather than two separately-maintained instrumentation libraries.
- **You need this instrumentation the moment you have more than one service in the request path you care about diagnosing** — a single monolithic service has less need for propagated trace IDs (a debugger or single log stream is often enough), but any multi-service request path benefits immediately from automatic, consistent trace propagation.

## 3. Core concept

Recall the courier-package analogy from [lack of observability](0525-lack-of-observability.md): a single tracking number that follows a package through every courier's system, letting you reconstruct the entire journey instead of three separate, disconnected records. Micrometer Tracing is the mechanism that automatically stamps that same tracking number onto the package at every handoff, without any courier needing to manually remember to copy it forward — it's baked into the couriers' shared shipping infrastructure (Spring's own HTTP client/server code) so every courier participating in that infrastructure automatically propagates the tracking number correctly, with zero extra effort per courier.

Concretely:

1. **A trace ID is generated once, at the first service that receives an externally-originated request** (or read from an incoming request that already carries one, if this service is itself downstream of another traced call).
2. **A span ID is generated for each individual unit of work** within that trace — one span per service hop, and potentially finer-grained spans for specific operations within a service (a database call, a specific method).
3. **Both IDs are automatically propagated in outgoing HTTP headers** (`traceparent`/`tracestate`, following the W3C Trace Context standard, which Micrometer Tracing uses by default) whenever an instrumented client (`RestTemplate`, `WebClient`) makes a downstream call — application code never manually sets these headers.
4. **Both IDs are automatically added to log output** (via MDC — Mapped Diagnostic Context — integration), so every log line emitted while processing a given request includes its trace and span ID, letting log-aggregation tooling filter for "every log line from every service, for this one request" trivially.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Micrometer Tracing automatically generates and propagates trace and span IDs through headers across service hops, and stamps them into log output via MDC, without application code touching them directly">
  <rect x="20" y="70" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <text x="95" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">trace=abc, span=1</text>

  <rect x="250" y="70" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <text x="325" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">trace=abc, span=2</text>

  <rect x="480" y="70" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="555" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Pricing Service</text>
  <text x="555" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">trace=abc, span=3</text>

  <line x1="170" y1="95" x2="250" y2="95" stroke="#8b949e" marker-end="url(#a13)"/>
  <line x1="400" y1="95" x2="480" y2="95" stroke="#8b949e" marker-end="url(#a13)"/>
  <text x="330" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SAME trace ID propagated automatically via headers; each hop logs it via MDC</text>
  <defs><marker id="a13" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

The same trace ID is generated once and propagated automatically across every hop, with every service's logs stamped with it via MDC.

## 5. Runnable example

Scenario: propagating a trace ID across two service hops. We start with a plain Java model of manual propagation (the boilerplate this automates), extend it to an MDC-based logging model, then show the real Micrometer Tracing configuration and its effect on log output.

### Level 1 — Basic

```java
// File: ManualTraceIdPropagation.java -- models the BOILERPLATE manual
// trace ID propagation requires: every method must accept and pass
// along the trace ID explicitly.
public class ManualTraceIdPropagation {
    static void gatewayHandle(String traceId) {
        System.out.println("[Gateway] trace=" + traceId + " request received");
        orderServiceHandle(traceId); // MUST remember to pass it along, every single call
    }
    static void orderServiceHandle(String traceId) {
        System.out.println("[OrderService] trace=" + traceId + " processing order");
        pricingServiceHandle(traceId); // easy to FORGET this parameter in a real, larger codebase
    }
    static void pricingServiceHandle(String traceId) {
        System.out.println("[PricingService] trace=" + traceId + " computing price");
    }

    public static void main(String[] args) {
        gatewayHandle("abc123");
        System.out.println("Every method signature had to explicitly carry traceId -- error-prone at scale.");
    }
}
```

How to run: `java ManualTraceIdPropagation.java`

Every method must explicitly accept and forward `traceId` — in a real codebase with many methods and call sites, it's easy for one method to forget to pass it along, silently breaking the trace's continuity from that point onward. This is exactly the boilerplate automatic instrumentation eliminates.

### Level 2 — Intermediate

```java
// File: MdcBasedPropagation.java -- models storing the trace ID in a
// THREAD-LOCAL context (MDC-style) so it doesn't need to be an explicit
// parameter on every method -- closer to how real instrumentation works.
public class MdcBasedPropagation {
    static ThreadLocal<String> currentTraceId = new ThreadLocal<>(); // models MDC

    static void log(String service, String message) {
        System.out.println("[" + service + "] trace=" + currentTraceId.get() + " " + message);
    }

    static void gatewayHandle() {
        currentTraceId.set("abc123"); // set ONCE, at the entry point
        log("Gateway", "request received");
        orderServiceHandle(); // no explicit traceId parameter needed anymore
    }
    static void orderServiceHandle() {
        log("OrderService", "processing order"); // reads from the SAME thread-local context automatically
        pricingServiceHandle();
    }
    static void pricingServiceHandle() {
        log("PricingService", "computing price");
    }

    public static void main(String[] args) {
        gatewayHandle();
        currentTraceId.remove();
    }
}
```

How to run: `java MdcBasedPropagation.java`

`currentTraceId` (a `ThreadLocal`, modeling MDC) is set once at the entry point; every subsequent `log` call reads it automatically, without any method needing an explicit `traceId` parameter — this is the core idea behind MDC-based log correlation, which Micrometer Tracing wires up automatically for real Spring applications.

### Level 3 — Advanced

```java
// File: MicrometerTracingRealShape.java -- the REAL Micrometer Tracing
// shape: automatic instrumentation requires ZERO manual trace ID code at
// all -- just the dependency and configuration.
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MicrometerTracingRealShape {

    @RestController
    static class OrderController {
        private static final Logger log = LoggerFactory.getLogger(OrderController.class);
        private final RestTemplate restTemplate;

        OrderController(RestTemplate restTemplate) { this.restTemplate = restTemplate; }

        @GetMapping("/orders/{id}")
        public String getOrder(@PathVariable String id) {
            log.info("Processing order {}", id); // NO trace ID code here -- Micrometer Tracing adds it to the log pattern automatically
            String price = restTemplate.getForObject("http://pricing-service/prices/" + id, String.class);
            // the OUTGOING call above automatically carries the current trace/span ID in its headers,
            // via Micrometer Tracing's instrumentation of RestTemplate -- no manual header-setting code
            return "{\"orderId\":\"" + id + "\",\"price\":" + price + "}";
        }
    }

    // logback-spring.xml / application.yml pattern typically includes:
    //   logging.pattern.level: "%5p [${spring.application.name:},%X{traceId:-},%X{spanId:-}]"
    // -- this is what stamps EVERY log line with the current trace/span ID automatically.
}
```

How to run: requires `micrometer-tracing-bridge-brave` (or `-otel`) plus `spring-boot-starter-actuator`, and a tracing backend exporter (e.g., `zipkin-reporter-brave` to export to Zipkin); run via `mvn spring-boot:run`, call `GET /orders/42`, and observe the log output automatically prefixed with the current trace and span IDs, with zero trace-related code written in `OrderController` itself.

`log.info("Processing order {}", id)` contains no trace ID reference at all — the `logging.pattern.level` configuration (using `%X{traceId}`/`%X{spanId}`, reading from MDC) is what stamps every log line with the current values, populated automatically by Micrometer Tracing's instrumentation. The outgoing `restTemplate.getForObject(...)` call to `pricing-service` similarly carries trace propagation headers automatically, since `RestTemplate` is instrumented transparently once the tracing dependencies are present.

## 6. Walkthrough

Trace a request to `GET /orders/42` against the Level 3 controller, end to end, assuming this is the first service to receive the request (no incoming trace context):

1. **The request arrives at `OrderController.getOrder`.** Micrometer Tracing's instrumentation of Spring MVC's request-handling pipeline detects there's no existing trace context on the incoming request, so it generates a brand-new trace ID (say, `abc123`) and a root span ID (say, `span-1`), storing both in the current thread's MDC context.
2. **`log.info("Processing order {}", id)` executes.** The configured log pattern reads `%X{traceId}` and `%X{spanId}` from MDC, producing a log line like `INFO [order-service,abc123,span-1] Processing order 42`.
3. **`restTemplate.getForObject("http://pricing-service/prices/42", String.class)` is called.** Because `RestTemplate` is instrumented, before the actual HTTP request is sent, Micrometer Tracing creates a new child span (say, `span-2`, still under trace `abc123`) representing this specific outbound call, and adds `traceparent`/`tracestate` headers (W3C Trace Context format) to the request carrying `abc123` and the new span ID.
4. **`pricing-service` receives this request.** Its own Micrometer Tracing instrumentation reads the incoming `traceparent` header, recognizing this request is *part of* an existing trace (`abc123`) rather than starting a new one — it creates its own span (say, `span-3`) as a child of `span-2`, and stores `traceId=abc123, spanId=span-3` in its own MDC context.
5. **Any logging `pricing-service` performs while handling this request** is automatically stamped with `trace=abc123, span=span-3` — even though `pricing-service` is a completely separate application, its logs share the same trace ID as `order-service`'s logs for this one request, letting log-aggregation tooling query "every log line for trace `abc123`" and see the full, correlated journey across both services.
6. **`pricing-service`'s response flows back to `order-service`**, which builds and returns its own response; both applications' logs, though physically separate log streams, are now correlatable via the shared `abc123` trace ID, and (if a tracing backend like Zipkin is configured) the individual spans can be assembled into a visual waterfall trace showing exactly how long each hop took — precisely the outcome the [lack of observability](0525-lack-of-observability.md) discussion described as the value of assembled tracing, here achieved with zero manual trace-ID code anywhere in either application.

## 7. Gotchas & takeaways

> **Gotcha:** trace propagation only works automatically through *instrumented* clients and frameworks — a call made through an uninstrumented HTTP client (a raw `java.net.http.HttpClient` used directly without Micrometer's instrumentation wired in, for instance) silently breaks the trace chain at that point, since no headers are added and the downstream service starts a brand-new, disconnected trace instead of continuing the existing one; verify that every outbound call path in your application actually goes through an instrumented client.

- Micrometer Tracing (the Spring Boot 3+ successor to Spring Cloud Sleuth) automates trace and span ID generation, header propagation, and MDC-based log stamping, eliminating the manual propagation boilerplate that would otherwise be required at every service hop.
- It follows the W3C Trace Context standard (`traceparent`/`tracestate` headers) by default, and bridges to actual tracing backends (Zipkin, OpenTelemetry) for span collection and visualization.
- Automatic instrumentation only covers instrumented clients and frameworks — any uninstrumented outbound call path breaks trace continuity silently, worth auditing explicitly rather than assuming every call is covered.
- Combining trace propagation with structured, MDC-stamped logging is what makes cross-service log correlation practical at scale — this is the concrete mechanism behind the correlation-ID concept discussed for [lack of observability](0525-lack-of-observability.md).
