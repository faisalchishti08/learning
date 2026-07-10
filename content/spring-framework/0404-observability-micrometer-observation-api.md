---
card: spring-framework
gi: 404
slug: observability-micrometer-observation-api
title: "Observability (Micrometer Observation API)"
---

## 1. What it is

The Micrometer Observation API is a vendor-neutral instrumentation layer that Spring Framework itself uses internally (in `RestClient`, `WebClient`, scheduled tasks, and more) to record what's happening during an operation once, and emit it as *both* a metric and a trace span. An `Observation` wraps a unit of work — start it, run the work, stop it — and Micrometer's registered `ObservationHandler`s decide what to actually do with that information (send it to Prometheus, to a distributed tracer, to logs).

```java
Observation.createNotStarted("order.process", observationRegistry)
        .observe(() -> orderService.process(order));
```

## 2. Why & when

Before this API, instrumenting an operation for metrics (Micrometer's `Timer`/`Counter`) and instrumenting it for tracing (a tracer's span API) were two separate pieces of code wrapping the same logic — easy to add one and forget the other, and easy for them to drift apart in what they actually measure. The Observation API exists to unify them: instrument once, and both a metric and a trace span come out automatically, correlated with each other.

This matters directly to the rest of Spring's ecosystem: Spring Framework 6 and Spring Boot 3 instrument their own core operations (HTTP client calls via `RestClient`/`WebClient`, `@Scheduled` executions, and more) using this exact API, which is why enabling observability in a Spring Boot application (by adding Micrometer Tracing and a metrics/tracing backend) automatically yields spans and metrics for those built-in operations without you writing any instrumentation code for them yourself.

Use the Observation API directly when:

- You want your own custom operations (a business-critical method, a batch job step) to produce both a metric and a trace span from one instrumentation point, consistent with how the framework instruments its own operations.
- You're building a reusable library and want consumers to get observability "for free" the same way Spring's own HTTP clients do.

## 3. Core concept

```
 Observation.createNotStarted("order.process", registry)
        |
        v
   .observe(() -> { ... work ... })
        |
        +--> start()  -----> ObservationHandler(s) notified: onStart
        |
        v
     [ your work runs here ]
        |
        +--> stop()   -----> ObservationHandler(s) notified: onStop
        |
        v
   ObservationHandler implementations decide what happens:
      - a metrics handler records a Timer/Counter
      - a tracing handler starts/finishes a trace span
      - both fire from the SAME start/stop lifecycle
```

An `Observation` doesn't know or care whether it becomes a metric, a trace, both, or neither — that's entirely up to which `ObservationHandler`s are registered on the `ObservationRegistry`, which is exactly why the same instrumentation code produces different signals depending on what's on the classpath and configured.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Observation lifecycle fans out to both a metrics handler and a tracing handler">
  <rect x="10" y="80" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Observation.observe()</text>

  <rect x="260" y="30" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Metrics handler -&gt; Timer</text>

  <rect x="260" y="135" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="163" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Tracing handler -&gt; Span</text>

  <line x1="180" y1="95" x2="255" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="180" y1="105" x2="255" y2="150" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One instrumentation call, two correlated signals — the same start/stop timestamps back both the metric and the span.

## 5. Runnable example

### Level 1 — Basic

Create and run an `Observation` with a simple metrics-only handler that logs when the observation starts and stops, to see the raw lifecycle before layering on real metrics.

```java
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationHandler;
import io.micrometer.observation.ObservationRegistry;

public class ObservationBasic {

    public static void main(String[] args) {
        ObservationRegistry registry = ObservationRegistry.create();
        registry.observationConfig().observationHandler(new ObservationHandler<Observation.Context>() {
            @Override
            public boolean supportsContext(Observation.Context context) { return true; }

            @Override
            public void onStart(Observation.Context context) {
                System.out.println("START  " + context.getName());
            }

            @Override
            public void onStop(Observation.Context context) {
                System.out.println("STOP   " + context.getName() + " (" + context.getDuration() + "ns)");
            }
        });

        Observation.createNotStarted("order.process", registry)
                .observe(() -> {
                    System.out.println("Processing order...");
                    try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                });
    }
}
```

How to run: add `io.micrometer:micrometer-observation` to the classpath, then `java ObservationBasic.java`.

`observe(Runnable)` starts the observation, runs the lambda, and stops the observation, calling every registered `ObservationHandler`'s `onStart`/`onStop` at the right moments — even though this custom handler does nothing but print, it demonstrates that `Observation` itself is just a lifecycle notifier, not a metrics or tracing implementation on its own.

### Level 2 — Intermediate

Register Micrometer's real metrics handler (`DefaultMeterObservationHandler`) backed by a `SimpleMeterRegistry`, so the same `Observation.observe(...)` call now produces an actual `Timer` metric you can query afterward.

```java
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import io.micrometer.core.instrument.observation.DefaultMeterObservationHandler;

public class ObservationIntermediate {

    public static void main(String[] args) {
        var meterRegistry = new SimpleMeterRegistry();
        var observationRegistry = ObservationRegistry.create();
        observationRegistry.observationConfig()
                .observationHandler(new DefaultMeterObservationHandler(meterRegistry));

        for (int i = 0; i < 3; i++) {
            Observation.createNotStarted("order.process", observationRegistry)
                    .observe(() -> {
                        try { Thread.sleep(20 + (long) (Math.random() * 30)); } catch (InterruptedException ignored) {}
                    });
        }

        var timer = meterRegistry.find("order.process").timer();
        System.out.println("Call count: " + timer.count());
        System.out.println("Total time: " + timer.totalTime(java.util.concurrent.TimeUnit.MILLISECONDS) + "ms");
        System.out.println("Mean time: " + timer.mean(java.util.concurrent.TimeUnit.MILLISECONDS) + "ms");
    }
}
```

How to run: add `io.micrometer:micrometer-observation` and `io.micrometer:micrometer-core` to the classpath, then `java ObservationIntermediate.java`.

`DefaultMeterObservationHandler` is the built-in bridge that turns any `Observation`'s start/stop lifecycle into a Micrometer `Timer` recorded against the observation's name. Running the same observation three times produces a `Timer` with `count() == 3`, and its `mean()` reflects the actual measured durations — proving the metric is genuinely derived from real elapsed time, not just a label.

### Level 3 — Advanced

Add contextual tags (so the same `"order.process"` observation can be broken down by order type or outcome) and a second handler that simulates tracing, showing both signals fire from one instrumentation point and share correlated context — plus error handling, since a failed operation should still be observed.

```java
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.core.instrument.observation.DefaultMeterObservationHandler;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationHandler;
import io.micrometer.observation.ObservationRegistry;

import java.util.concurrent.ThreadLocalRandom;

public class ObservationAdvanced {

    record OrderContext(String orderType) {}

    static class SimpleTracingHandler implements ObservationHandler<Observation.Context> {
        @Override
        public boolean supportsContext(Observation.Context context) { return true; }

        @Override
        public void onStart(Observation.Context context) {
            System.out.println("[trace] span started: " + context.getName() + " tags=" + context.getLowCardinalityKeyValues());
        }

        @Override
        public void onError(Observation.Context context) {
            System.out.println("[trace] span marked as error: " + context.getError());
        }

        @Override
        public void onStop(Observation.Context context) {
            System.out.println("[trace] span finished: " + context.getName() + " duration=" + context.getDuration() + "ns");
        }
    }

    static void processOrder(String orderType, ObservationRegistry registry) {
        Observation observation = Observation.createNotStarted("order.process", registry)
                .lowCardinalityKeyValue("order.type", orderType)
                .contextualName("process-" + orderType);

        observation.observe(() -> {
            if (ThreadLocalRandom.current().nextBoolean()) {
                throw new IllegalStateException("Inventory check failed for " + orderType);
            }
            System.out.println("Order processed: " + orderType);
        });
    }

    public static void main(String[] args) {
        var meterRegistry = new SimpleMeterRegistry();
        var observationRegistry = ObservationRegistry.create();
        observationRegistry.observationConfig()
                .observationHandler(new DefaultMeterObservationHandler(meterRegistry))
                .observationHandler(new SimpleTracingHandler());

        for (String type : new String[]{"standard", "express", "standard"}) {
            try {
                processOrder(type, observationRegistry);
            } catch (IllegalStateException e) {
                System.out.println("Caught and logged: " + e.getMessage());
            }
        }

        meterRegistry.getMeters().forEach(meter ->
                System.out.println("Metric: " + meter.getId()));
    }
}
```

How to run: same dependencies as Level 2, then `java ObservationAdvanced.java`.

`lowCardinalityKeyValue("order.type", orderType)` attaches a tag both the metrics handler (as a `Timer` tag, enabling breakdowns like "average duration for express orders") and the tracing handler (as a span attribute) can see — one piece of context, consumed by both signals. When `processOrder`'s lambda throws, `observe(...)` still calls `onError` then `onStop` on every handler before re-throwing, which is why a failed order still shows up as a completed (if errored) span and a recorded (if failed) timer entry rather than vanishing from observability entirely.

## 6. Walkthrough

Trace one call to `ObservationAdvanced.processOrder("express", registry)` where the random check happens to throw:

1. **Observation built (not started).** `Observation.createNotStarted("order.process", registry)` creates an `Observation` in an unstarted state, then `.lowCardinalityKeyValue(...)` and `.contextualName(...)` attach metadata to its `Context` before anything runs — this metadata will be visible to every handler at every lifecycle stage.
2. **`observe(Runnable)` starts it.** Internally this calls `observation.start()`, which invokes `onStart(context)` on every registered handler in order: first `DefaultMeterObservationHandler` (which begins timing), then `SimpleTracingHandler` (which prints `"[trace] span started: order.process tags=[tag(order.type=express)]"`).
3. **The wrapped work runs.** Inside the lambda, `ThreadLocalRandom.current().nextBoolean()` happens to return `true`, so `IllegalStateException("Inventory check failed for express")` is thrown.
4. **Error path.** `observe(...)`'s internal try/catch catches the exception, records it on the `Observation.Context` via `context.setError(...)`, and calls `onError(context)` on every handler — `SimpleTracingHandler` prints `"[trace] span marked as error: java.lang.IllegalStateException: Inventory check failed for express"`.
5. **Stop, regardless of outcome.** `observation.stop()` runs next (in a `finally`-equivalent path), calling `onStop(context)` on every handler: `DefaultMeterObservationHandler` finalizes the `Timer` recording (this failed call still counts toward `order.process`'s timer statistics, tagged `order.type=express`), and `SimpleTracingHandler` prints the finished-span line with the measured duration.
6. **Re-throw.** After all handlers have observed the stop, `observe(...)` re-throws the original `IllegalStateException` out to the caller — `processOrder`'s caller in `main` catches it in its own `try/catch` and prints `"Caught and logged: ..."`.
7. **Final metrics dump.** After all three orders (including any that threw) have been processed, `meterRegistry.getMeters()` prints the accumulated `Timer` for `order.process` — its count reflects all three calls, successful or not, because every one of them completed its `Observation` lifecycle.

```
observe(lambda)
   -> start()  -> onStart on [metrics handler, tracing handler]
   -> run lambda -> throws IllegalStateException
   -> setError(ex) -> onError on [metrics handler, tracing handler]
   -> stop()   -> onStop  on [metrics handler, tracing handler]
   -> re-throw IllegalStateException
caller catches and logs
```

## 7. Gotchas & takeaways

> Gotcha: an `Observation` that is started but never stopped (e.g., because you call `observation.start()` manually and an exception skips the corresponding `observation.stop()`) leaves the metrics handler's timer running indefinitely and never finalizes a trace span — always prefer `observation.observe(...)` (which guarantees stop-on-exception via its internal try/finally) over manual `start()`/`stop()` pairs unless you have a specific reason to manage the lifecycle yourself, and if you do, wrap it in try/finally.

- The Observation API's value is instrumenting once and getting both metrics and traces, correlated, instead of maintaining two separate instrumentation code paths that can drift apart.
- Spring Framework and Spring Boot already instrument their own built-in operations (`RestClient`, `WebClient`, `@Scheduled`) with this API — enabling Micrometer Tracing plus a metrics backend gives you observability for those for free, no extra code required.
- Use `lowCardinalityKeyValue` for tags with a small, bounded set of possible values (order type, HTTP method) — high-cardinality tags (user IDs, order IDs) blow up metrics storage and belong only on trace spans, via `highCardinalityKeyValue`, not on metrics tags.
- Always use `observe(...)` rather than manual `start()`/`stop()` calls unless you specifically need to hold the observation open across asynchronous boundaries, in which case wrap the manual lifecycle in try/finally to guarantee `stop()` always runs.
