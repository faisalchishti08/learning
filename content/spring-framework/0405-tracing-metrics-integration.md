---
card: spring-framework
gi: 405
slug: tracing-metrics-integration
title: "Tracing & metrics integration"
---

## 1. What it is

Building on the Observation API from the previous card, this is about how Spring wires *real* tracing and metrics backends into that abstraction: Micrometer Tracing (with a bridge to Brave/Zipkin or OpenTelemetry) supplies the actual span-recording implementation, and Micrometer's `MeterRegistry` (with a bridge to Prometheus, CloudWatch, or another metrics backend) supplies the actual metrics-recording implementation. Once both are on the classpath and configured, every `Observation` in the application — including the ones Spring's own `RestClient`/`WebClient`/`@Scheduled` create internally — automatically produces real, exportable traces and metrics.

```java
@Bean
ObservationRegistry observationRegistry(List<ObservationHandler<?>> handlers) {
    ObservationRegistry registry = ObservationRegistry.create();
    handlers.forEach(h -> registry.observationConfig().observationHandler(h));
    return registry;
}
```

## 2. Why & when

The previous card showed that `Observation` is neutral about *what* consumes its lifecycle events — this card is about actually connecting that lifecycle to systems that store and let you query the results: a tracing backend (Zipkin, Jaeger, or an OpenTelemetry collector) for request-flow visualization across services, and a metrics backend (Prometheus, Datadog, CloudWatch) for aggregated dashboards and alerting.

You need this integration whenever:

- You're running more than one service and need to see how a single request flows across them — distributed tracing is what stitches together the spans from each service into one coherent trace, using a shared trace ID propagated through headers.
- You need dashboards and alerts on request latency, error rate, or throughput — metrics backends are built for aggregation and time-series querying in a way raw logs aren't.
- You want the two correlated: jumping from a slow-looking metric straight to an example trace that shows *why* it was slow, which is exactly what shared Observation-derived context enables.

Spring Boot's auto-configuration handles most of this wiring automatically once you add the right starters (`micrometer-tracing-bridge-brave` or `-otel`, plus `micrometer-registry-prometheus` or similar) — but understanding the underlying `ObservationRegistry` composition is what lets you add custom observability or debug why something isn't showing up.

## 3. Core concept

```
                    ObservationRegistry
                    (one per application)
                            |
          registered handlers, composed:
                            |
        +-------------------+-------------------+
        |                                        |
 Tracing handler                          Metrics handler
 (Brave or OTel bridge)                   (MeterRegistry bridge)
        |                                        |
        v                                        v
   Zipkin / Jaeger /                    Prometheus / CloudWatch /
   OTel collector                       Datadog / ...
        |                                        |
        +--------------- correlated by ----------+
              shared trace ID / span context
```

Both destinations are fed by the exact same `Observation` lifecycle events — a trace and its corresponding metric share timing and tags because they're derived from the same underlying instrumentation call, not two independently maintained pieces of code.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request flowing through two services produces linked spans in a tracing backend, correlated with metrics from both">
  <rect x="10" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Service A</text>

  <rect x="230" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Service B</text>

  <line x1="160" y1="43" x2="225" y2="43" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="195" y="35" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">trace-id propagated</text>

  <rect x="120" y="120" width="150" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="195" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Zipkin: one trace,</text>
  <text x="195" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2 linked spans</text>

  <rect x="340" y="120" width="150" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="415" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Prometheus: 2 sets</text>
  <text x="415" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">of per-service metrics</text>

  <line x1="85" y1="66" x2="180" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="305" y1="66" x2="220" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="85" y1="66" x2="380" y2="115" stroke="#8b949e" stroke-width="1"/>
  <line x1="305" y1="66" x2="440" y2="115" stroke="#8b949e" stroke-width="1"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The propagated trace ID is what lets a tracing backend stitch spans from two independent services into one coherent picture of a single request.

## 5. Runnable example

### Level 1 — Basic

Wire a real Brave tracer into an `ObservationRegistry` and print the trace/span IDs produced by a single observation — no external Zipkin server needed, since Brave can report spans to an in-memory logging reporter for this demo.

```java
import brave.Tracing;
import brave.handler.SpanHandler;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import io.micrometer.tracing.brave.bridge.BraveTracer;
import io.micrometer.tracing.handler.DefaultTracingObservationHandler;

public class TracingBasic {

    public static void main(String[] args) {
        Tracing tracing = Tracing.newBuilder()
                .localServiceName("demo-service")
                .addSpanHandler(new SpanHandler() {
                    @Override
                    public boolean end(brave.propagation.TraceContext context, brave.handler.MutableSpan span, Cause cause) {
                        System.out.println("Reported span: name=" + span.name()
                                + " traceId=" + context.traceIdString()
                                + " spanId=" + context.spanIdString()
                                + " durationMicros=" + span.finishTimestamp());
                        return true;
                    }
                })
                .build();

        var braveTracer = new BraveTracer(tracing.tracer(),
                new brave.propagation.ThreadLocalCurrentTraceContext.Builder().build(),
                new io.micrometer.tracing.brave.bridge.BraveBaggageManager());

        ObservationRegistry registry = ObservationRegistry.create();
        registry.observationConfig().observationHandler(new DefaultTracingObservationHandler(braveTracer));

        Observation.createNotStarted("order.process", registry)
                .observe(() -> System.out.println("Processing order..."));

        tracing.close();
    }
}
```

How to run: add `io.micrometer:micrometer-observation`, `io.micrometer:micrometer-tracing`, `io.micrometer:micrometer-tracing-bridge-brave`, and `io.zipkin.brave:brave` to the classpath, then `java TracingBasic.java`.

`DefaultTracingObservationHandler` is Micrometer Tracing's bridge: it turns `Observation` start/stop events into real Brave span start/finish calls. The custom `SpanHandler` intercepts finished spans and prints their trace/span IDs — in a real deployment, this handler would instead be a Zipkin HTTP reporter shipping spans to a Zipkin server, but the underlying span data is identical.

### Level 2 — Intermediate

Add a metrics side alongside tracing, and nest a child observation inside a parent one — simulating a controller method that calls a service method, each producing its own span but sharing one trace, exactly how request-flow tracing works across method boundaries within one service.

```java
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.core.instrument.observation.DefaultMeterObservationHandler;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import io.micrometer.tracing.brave.bridge.BraveTracer;
import io.micrometer.tracing.handler.DefaultTracingObservationHandler;
import brave.Tracing;

public class TracingIntermediate {

    static ObservationRegistry buildRegistry(SimpleMeterRegistry meterRegistry, Tracing tracing) {
        var braveTracer = new BraveTracer(tracing.tracer(),
                new brave.propagation.ThreadLocalCurrentTraceContext.Builder().build(),
                new io.micrometer.tracing.brave.bridge.BraveBaggageManager());

        ObservationRegistry registry = ObservationRegistry.create();
        registry.observationConfig()
                .observationHandler(new DefaultMeterObservationHandler(meterRegistry))
                .observationHandler(new DefaultTracingObservationHandler(braveTracer));
        return registry;
    }

    static void controllerHandle(ObservationRegistry registry) {
        Observation.createNotStarted("http.controller", registry).observe(() -> {
            System.out.println("Controller received request");
            serviceProcess(registry); // nested observation: child span, same trace
        });
    }

    static void serviceProcess(ObservationRegistry registry) {
        Observation.createNotStarted("order.service.process", registry).observe(() -> {
            System.out.println("Service processing order");
        });
    }

    public static void main(String[] args) {
        var meterRegistry = new SimpleMeterRegistry();
        var tracing = Tracing.newBuilder()
                .localServiceName("demo-service")
                .addSpanHandler(new brave.handler.SpanHandler() {
                    @Override
                    public boolean end(brave.propagation.TraceContext context, brave.handler.MutableSpan span, Cause cause) {
                        System.out.println("Span: " + span.name() + " traceId=" + context.traceIdString()
                                + " spanId=" + context.spanIdString() + " parentId=" + context.parentIdString());
                        return true;
                    }
                }).build();

        ObservationRegistry registry = buildRegistry(meterRegistry, tracing);
        controllerHandle(registry);

        meterRegistry.getMeters().forEach(m -> System.out.println("Metric: " + m.getId()));
        tracing.close();
    }
}
```

How to run: same dependencies as Level 1 plus `io.micrometer:micrometer-core`, then `java TracingIntermediate.java`.

Because `serviceProcess`'s observation starts *while* `controllerHandle`'s observation is still active (it's called from inside the outer `observe(...)` lambda), Micrometer Tracing automatically makes the inner span a child of the outer one — both spans share the same `traceId`, and the inner span's `parentId` matches the outer span's `spanId`. This is exactly the parent-child relationship a tracing UI uses to render a request's call tree, and it happens automatically from lexical nesting, with no manual span-linking code.

### Level 3 — Advanced

Production tracing/metrics setups need error tagging so failed operations are visibly distinguishable in dashboards, and need to work correctly across asynchronous boundaries where the "current" observation must be explicitly propagated rather than relying on simple call-stack nesting.

```java
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.core.instrument.observation.DefaultMeterObservationHandler;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import io.micrometer.tracing.brave.bridge.BraveTracer;
import io.micrometer.tracing.handler.DefaultTracingObservationHandler;
import brave.Tracing;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;

public class TracingAdvanced {

    static ObservationRegistry buildRegistry(SimpleMeterRegistry meterRegistry, Tracing tracing) {
        var braveTracer = new BraveTracer(tracing.tracer(),
                new brave.propagation.ThreadLocalCurrentTraceContext.Builder().build(),
                new io.micrometer.tracing.brave.bridge.BraveBaggageManager());
        ObservationRegistry registry = ObservationRegistry.create();
        registry.observationConfig()
                .observationHandler(new DefaultMeterObservationHandler(meterRegistry))
                .observationHandler(new DefaultTracingObservationHandler(braveTracer));
        return registry;
    }

    static CompletableFuture<Void> processAsync(ObservationRegistry registry, java.util.concurrent.Executor executor) {
        // Capture the current observation on the calling thread, before crossing the async boundary.
        Observation parent = registry.getCurrentObservation();

        return CompletableFuture.runAsync(() -> {
            // Explicitly re-establish it on the worker thread — thread locals don't cross automatically.
            Observation child = Observation.createNotStarted("async.charge-payment", registry)
                    .parentObservation(parent);

            child.observe(() -> {
                if (ThreadLocalRandom.current().nextInt(3) == 0) {
                    throw new IllegalStateException("Payment gateway timeout");
                }
                System.out.println(Thread.currentThread().getName() + " charged payment");
            });
        }, executor);
    }

    public static void main(String[] args) {
        var meterRegistry = new SimpleMeterRegistry();
        var tracing = Tracing.newBuilder().localServiceName("demo-service").build();
        ObservationRegistry registry = buildRegistry(meterRegistry, tracing);
        var executor = Executors.newFixedThreadPool(2);

        Observation.createNotStarted("http.checkout", registry).observe(() -> {
            System.out.println("Checkout started");
            try {
                processAsync(registry, executor).join();
            } catch (Exception e) {
                System.out.println("Async payment failed: " + e.getCause().getMessage());
            }
        });

        long errorCount = meterRegistry.find("async.charge-payment")
                .tag("error", "IllegalStateException").timers().stream().mapToLong(t -> t.count()).sum();
        System.out.println("Recorded payment errors: " + errorCount);

        executor.shutdown();
        tracing.close();
    }
}
```

How to run: same dependencies as Level 2, then `java TracingAdvanced.java`.

`registry.getCurrentObservation()` reads the observation active on the calling thread before the work hops onto a different thread via `CompletableFuture.runAsync`; `.parentObservation(parent)` explicitly re-links the child observation to it once inside the async task, since Micrometer's context propagation is thread-local by default and does not automatically follow work across executor threads. `DefaultMeterObservationHandler` automatically tags the resulting `Timer` with an `error` tag whenever the observed block throws, which is what makes `meterRegistry.find(...).tag("error", "IllegalStateException")` a meaningful, queryable metric slice.

## 6. Walkthrough

Trace `TracingAdvanced.main` end to end:

1. **Outer observation starts.** `Observation.createNotStarted("http.checkout", registry).observe(...)` begins; `DefaultTracingObservationHandler` starts a Brave span named `http.checkout` and makes it the "current" observation/span for this thread.
2. **Synchronous work.** `"Checkout started"` prints on the main thread, still inside the `http.checkout` span.
3. **Async dispatch.** `processAsync` reads `registry.getCurrentObservation()` — this correctly captures the `http.checkout` observation, since it's called synchronously from within its `observe(...)` block. `CompletableFuture.runAsync(..., executor)` then schedules the actual work on a pool thread and returns immediately.
4. **Worker thread picks up the task.** On a separate `pool-*` thread, `Observation.createNotStarted("async.charge-payment", registry).parentObservation(parent)` explicitly attaches the new observation as a child of the captured `http.checkout` observation — without this explicit link, the new thread would have no "current" observation at all, and the resulting span would incorrectly appear as a new, disconnected trace root.
5. **Random failure.** Roughly one in three runs, `ThreadLocalRandom.current().nextInt(3) == 0` is true, and the lambda throws `IllegalStateException("Payment gateway timeout")`.
6. **Error recorded, then propagated.** `child.observe(...)` catches the exception internally, calls each handler's `onError` (tagging both the span and the eventual `Timer` metric with the error type), calls `onStop`, and then re-throws — `CompletableFuture.runAsync`'s returned future completes exceptionally as a result.
7. **Join surfaces the failure.** Back on the main thread, `processAsync(...).join()` re-throws the async exception wrapped in a `CompletionException`; the `catch` block in `main` unwraps it via `.getCause()` and prints `"Async payment failed: Payment gateway timeout"`.
8. **Outer span still completes cleanly.** Because the `try/catch` in step 7 handled the exception, `http.checkout`'s own `observe(...)` block returns normally — the outer span finishes without an error tag, even though its child span does carry one, correctly reflecting that checkout itself handled the payment failure gracefully.
9. **Metrics query.** After the run, `meterRegistry.find("async.charge-payment").tag("error", "IllegalStateException")` finds the `Timer` entries specifically tagged with that error (only present on runs where the random failure actually happened) and sums their counts.

```
http.checkout (main thread)
   |
   +--> processAsync: capture current observation
   |
   +--> [pool thread] async.charge-payment (child of http.checkout)
   |         success -> no error tag
   |         OR
   |         failure -> onError -> error=IllegalStateException tag -> re-throw
   |
   join() -> unwrap CompletionException -> catch -> log
http.checkout completes normally (its own span has no error)
```

## 7. Gotchas & takeaways

> Gotcha: thread-local context (both the "current trace" for tracing and the "current observation" for the Observation API) does not automatically cross thread boundaries — spawning work onto a new thread (a raw `Thread`, an `ExecutorService`, or an unwrapped `CompletableFuture.runAsync`) without explicitly propagating the parent context produces orphaned spans that show up as disconnected trace roots instead of children of the request that spawned them, exactly the failure mode Level 3's `parentObservation(...)` call avoids.

- Tracing and metrics both derive from the same `Observation` lifecycle, which is why a trace and its corresponding metric share timing and tags — instrument once, get both, correlated.
- Nested `observe(...)` calls on the same thread automatically become parent-child spans in the trace; explicit `parentObservation(...)` linking is required only when crossing thread/async boundaries.
- Configure error tagging (automatic with `DefaultMeterObservationHandler`) so failed operations are queryable as their own metric slice, not just visible as gaps or spikes in overall latency.
- In a real Spring Boot application, most of this wiring (registry composition, Brave/OTel bridge, exporter configuration) is handled by auto-configuration once the right starters are on the classpath — understanding the manual wiring here is what lets you debug or extend it when the defaults aren't enough.
