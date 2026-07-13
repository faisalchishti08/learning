---
card: microservices
gi: 376
slug: legacy-spring-cloud-sleuth-replaced-by-micrometer-tracing-aw
title: "Legacy Spring Cloud Sleuth (replaced by Micrometer Tracing) awareness"
---

## 1. What it is

**Spring Cloud Sleuth** was Spring's original tracing solution — automatically instrumenting Spring components (web controllers, RestTemplate/WebClient calls, messaging) to create spans and propagate trace context, built directly on Brave. As of Spring Boot 3 / Spring Cloud 2022.0, Sleuth was replaced by **Micrometer Tracing**, covered earlier as [the tracing facade with Brave/OpenTelemetry bridges](0369-micrometer-tracing-brave-opentelemetry-bridges.md) — Sleuth's automatic instrumentation capabilities were absorbed into Micrometer Tracing's own auto-configuration, and Sleuth itself is no longer actively developed for new Spring Boot versions.

## 2. Why & when

This is purely historical and migration awareness, not a pattern to newly adopt: any Spring Boot 2.x codebase still on Spring Cloud Sleuth will encounter this transition when upgrading to Spring Boot 3.x, since Sleuth's dependencies and auto-configuration classes don't carry forward — the equivalent capability now comes from Micrometer Tracing plus a bridge dependency (Brave or OpenTelemetry). Recognizing this history matters mainly for two practical reasons: understanding why older tutorials, Stack Overflow answers, or internal documentation referencing "Sleuth" don't directly apply to a modern Spring Boot 3.x project, and knowing what to actually change when migrating a legacy service.

If you encounter a codebase using Spring Cloud Sleuth today, treat it as a signal that the project is either still on Spring Boot 2.x or has an outdated tracing setup that needs updating — the concrete migration is: remove the `spring-cloud-starter-sleuth` dependency, add `micrometer-tracing-bridge-brave` (to keep the same underlying tracer with minimal disruption) or `micrometer-tracing-bridge-otel` (to move to OpenTelemetry), and update any code that referenced Sleuth's specific APIs directly to use Micrometer Tracing's `Tracer`/`Span` interfaces instead.

## 3. Core concept

Conceptually, nothing about *what* tracing does changed — spans, trace context propagation, and the trace/span model from [distributed tracing concepts](0352-distributed-tracing-concepts-trace-span-context-propagation.md) are identical before and after this transition. What changed is *which library* provides the facade and auto-instrumentation: Sleuth was itself a somewhat Brave-specific facade with its own auto-configuration; Micrometer Tracing is a more general facade (supporting both Brave and OpenTelemetry as interchangeable bridges) that also became the shared foundation used across the broader Micrometer/Spring Boot observability stack.

```java
// Spring Cloud Sleuth (LEGACY, Spring Boot 2.x): its OWN Tracer API
Tracer sleuthTracer; // from org.springframework.cloud.sleuth

// Micrometer Tracing (CURRENT, Spring Boot 3.x): the REPLACEMENT facade
io.micrometer.tracing.Tracer tracer; // same CONCEPT, different, more general API/library
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Timeline: Spring Boot 2.x used Spring Cloud Sleuth's own tracing facade built on Brave; Spring Boot 3.x replaces this with Micrometer Tracing, which can bridge to either Brave or OpenTelemetry">
  <rect x="20" y="60" width="270" height="60" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot 2.x</text>
  <text x="155" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Cloud Sleuth (on Brave)</text>

  <line x1="290" y1="90" x2="360" y2="90" stroke="#8b949e" marker-end="url(#a376)"/>

  <rect x="370" y="60" width="270" height="60" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="505" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot 3.x</text>
  <text x="505" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Micrometer Tracing (Brave OR OTel bridge)</text>

  <defs><marker id="a376" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Sleuth's role was absorbed into Micrometer Tracing, which generalizes the same tracing facade concept across both Brave and OpenTelemetry.

## 5. Runnable example

Scenario: a service creating spans, first shown mimicking Sleuth's legacy, Brave-specific API shape, then migrated to Micrometer Tracing's replacement facade, and finally extended to show the migration is purely a dependency/configuration change, with the calling code's structure staying conceptually identical.

### Level 1 — Basic

```java
// File: LegacySleuthStyleApi.java -- mimics Spring Cloud Sleuth's OWN,
// somewhat Brave-specific API shape, as it would have looked in a
// Spring Boot 2.x codebase.
import java.util.*;

public class LegacySleuthStyleApi {
    // Simulates org.springframework.cloud.sleuth.Tracer's shape (Sleuth-specific).
    static class SleuthStyleTracer {
        List<String> spans = new ArrayList<>();
        Object nextSpan() { return new Object(); } // Sleuth's OWN span type
        void tag(Object span, String key, String value) { spans.add(key + "=" + value); } // Sleuth-SPECIFIC method
    }

    static SleuthStyleTracer tracer = new SleuthStyleTracer();

    static void chargePayment(String orderId) {
        Object span = tracer.nextSpan();
        tracer.tag(span, "orderId", orderId);
        System.out.println("Recorded span using LEGACY Sleuth-style API: " + tracer.spans);
    }

    public static void main(String[] args) {
        chargePayment("order-1");
        System.out.println("This exact API shape does NOT carry forward when upgrading to Spring Boot 3.x -- Sleuth is GONE there.");
    }
}
```

How to run: `java LegacySleuthStyleApi.java`

`SleuthStyleTracer` mimics the shape of Spring Cloud Sleuth's own tracing API as it existed in Spring Boot 2.x. Any application code written directly against Sleuth's specific classes and methods like this would need to change when the project upgrades to Spring Boot 3.x, since Sleuth's dependencies and auto-configuration are no longer present there.

### Level 2 — Intermediate

```java
// File: MigratedToMicrometerTracing.java -- the SAME chargePayment
// operation, migrated to Micrometer Tracing's REPLACEMENT facade API --
// conceptually identical tracing behavior, different library/API.
import java.util.*;

public class MigratedToMicrometerTracing {
    // Simulates io.micrometer.tracing.Tracer's shape (the REPLACEMENT).
    interface Tracer { Span nextSpan(); }
    interface Span { Span tag(String key, String value); void end(); }

    static class MicrometerStyleTracer implements Tracer {
        List<String> recordedTags = new ArrayList<>();
        public Span nextSpan() {
            return new Span() {
                public Span tag(String key, String value) { recordedTags.add(key + "=" + value); return this; }
                public void end() {}
            };
        }
    }

    static Tracer tracer = new MicrometerStyleTracer();

    static void chargePayment(String orderId) {
        Span span = tracer.nextSpan();
        span.tag("orderId", orderId); // conceptually the SAME action as Sleuth's tracer.tag(span, ...), different API SHAPE
        span.end();
        System.out.println("Recorded span using CURRENT Micrometer Tracing API: "
                + ((MicrometerStyleTracer) tracer).recordedTags);
    }

    public static void main(String[] args) {
        chargePayment("order-1");
        System.out.println("SAME conceptual tracing behavior as Level 1 -- but this is the API that ACTUALLY works on Spring Boot 3.x.");
    }
}
```

How to run: `java MigratedToMicrometerTracing.java`

The overall shape of `chargePayment` is conceptually identical to Level 1's — get a span, tag it, finish it — but every specific type and method now comes from the `Tracer`/`Span` interfaces mirroring Micrometer Tracing's real API, not Sleuth's. This is the actual migration a Spring Boot 2.x-to-3.x upgrade requires: the *behavior* stays the same, but the *specific library and API surface* being called changes.

### Level 3 — Advanced

```java
// File: MigrationIsConfigOnlyNoBehaviorChange.java -- demonstrates that
// the underlying TRACING BEHAVIOR (spans nesting correctly, context
// propagating) is UNCHANGED across the migration -- what changed is
// PURELY which dependency/bridge is on the classpath, not the tracing
// MODEL itself.
import java.util.*;

public class MigrationIsConfigOnlyNoBehaviorChange {
    interface Tracer { Span nextSpan(String name, String parentSpanId); }
    interface Span { String id(); void end(); }

    // The SAME tracer/span MODEL works whether backed by "Brave-bridge" or "OTel-bridge" config underneath.
    static class MicrometerTracer implements Tracer {
        int nextId = 1;
        List<String> spanLog = new ArrayList<>();
        public Span nextSpan(String name, String parentSpanId) {
            String id = "span-" + (nextId++);
            spanLog.add(name + " [" + id + "], parent=" + parentSpanId);
            return () -> id; // Span::id via lambda; end() default no-op below via anonymous impl instead
        }
    }

    static void runOrderFlow(Tracer tracer) {
        Span rootSpan = tracer.nextSpan("gateway", null); // root: no parent
        Span orderSpan = tracer.nextSpan("order-service", rootSpan.id()); // child of gateway
        Span paymentSpan = tracer.nextSpan("payment-service", orderSpan.id()); // grandchild
        paymentSpan.end(); orderSpan.end(); rootSpan.end();
    }

    public static void main(String[] args) {
        System.out.println("--- Configured as if backed by Brave (post-migration) ---");
        MicrometerTracer braveBackedTracer = new MicrometerTracer();
        runOrderFlow(braveBackedTracer);
        braveBackedTracer.spanLog.forEach(s -> System.out.println("  " + s));

        System.out.println("--- Configured as if backed by OpenTelemetry (post-migration, DIFFERENT bridge) ---");
        MicrometerTracer otelBackedTracer = new MicrometerTracer();
        runOrderFlow(otelBackedTracer); // IDENTICAL calling code -- runOrderFlow never changes
        otelBackedTracer.spanLog.forEach(s -> System.out.println("  " + s));

        System.out.println("SAME tracing MODEL (parent/child spans) in BOTH cases -- only the underlying bridge configuration differs, which THIS code never even sees.");
    }
}
```

How to run: `java MigrationIsConfigOnlyNoBehaviorChange.java`

`runOrderFlow` is written once, entirely against the `Tracer`/`Span` facade, with no reference to Brave or OpenTelemetry anywhere. Running it against two separately-constructed `MicrometerTracer` instances (standing in for two different bridge configurations) produces the identical parent/child span structure both times — `gateway` as root, `order-service` as its child, `payment-service` as the grandchild — demonstrating that the actual tracing *model* (what Sleuth provided, and what Micrometer Tracing continues to provide) never changed across this migration; only the specific library implementing that model underneath did.

## 6. Walkthrough

Trace `MigrationIsConfigOnlyNoBehaviorChange.main` in order. **First**, `braveBackedTracer` is constructed, and `runOrderFlow(braveBackedTracer)` runs: `tracer.nextSpan("gateway", null)` creates `span-1` with no parent, logging `"gateway [span-1], parent=null"`. `tracer.nextSpan("order-service", rootSpan.id())` creates `span-2` with parent `"span-1"`, logging accordingly. `tracer.nextSpan("payment-service", orderSpan.id())` creates `span-3` with parent `"span-2"`. All three `.end()` calls run but do nothing observable in this simplified model.

**Next**, `braveBackedTracer.spanLog` is printed, showing the three logged entries in creation order, correctly reflecting the gateway→order-service→payment-service parent chain.

**Then**, `otelBackedTracer` is constructed as a *fresh*, separate `MicrometerTracer` instance, and `runOrderFlow(otelBackedTracer)` runs — calling the exact same `runOrderFlow` method, with no code path difference whatsoever from the first call. Because `nextId` starts fresh at `1` for this new instance, the spans are again `span-1`, `span-2`, `span-3`, with the identical parent relationships logged.

**Finally**, `otelBackedTracer.spanLog` is printed, showing the same structural pattern as the first run — `main` closes with an observation confirming that `runOrderFlow`'s code never differed between the two "bridge configurations," and the resulting span structure was identical both times, illustrating that the Sleuth-to-Micrometer-Tracing migration is fundamentally a dependency and configuration change, not a change to how tracing conceptually works.

```
runOrderFlow(braveBackedTracer):  gateway[span-1,parent=null] -> order-service[span-2,parent=span-1] -> payment-service[span-3,parent=span-2]
runOrderFlow(otelBackedTracer):   gateway[span-1,parent=null] -> order-service[span-2,parent=span-1] -> payment-service[span-3,parent=span-2]
IDENTICAL structure from IDENTICAL calling code -- only the underlying bridge differs, invisibly to runOrderFlow.
```

## 7. Gotchas & takeaways

> Searching for Sleuth-specific configuration properties or annotations while working on a Spring Boot 3.x project is a common source of confusion for anyone whose prior experience predates this migration — those properties simply don't exist anymore; the equivalent configuration now lives under Micrometer Tracing's own property namespace and bridge dependency.

- Spring Cloud Sleuth was Spring's original, Brave-specific tracing facade for Spring Boot 2.x; it has been replaced by [Micrometer Tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md) in Spring Boot 3.x.
- The underlying tracing *concepts* (spans, trace context propagation, parent/child relationships) are unchanged — what changed is which library implements and exposes them.
- Migrating a legacy codebase means removing the Sleuth dependency, adding a Micrometer Tracing bridge (Brave or OpenTelemetry), and updating any code referencing Sleuth's specific API classes.
- This is purely historical/migration awareness — new projects should use Micrometer Tracing directly and never need to interact with Sleuth at all.
