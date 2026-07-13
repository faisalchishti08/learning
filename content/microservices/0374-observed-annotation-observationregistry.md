---
card: microservices
gi: 374
slug: observed-annotation-observationregistry
title: "@Observed annotation & ObservationRegistry"
---

## 1. What it is

Micrometer's **`@Observed`** annotation, backed by an **`ObservationRegistry`**, lets a single annotation on a method produce *both* a metric (a Timer, tracking count and duration) *and* a tracing span for that method's execution, in one unified step — instead of separately wiring up [Micrometer metrics](0366-micrometer-metrics-facade.md) and [Micrometer Tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md) by hand for the same operation. `Observation` is Micrometer's unifying abstraction: one recorded "observation" of something happening can simultaneously feed multiple observability concerns (metrics, tracing, and potentially logging) through registered handlers, rather than requiring separate manual instrumentation for each.

## 2. Why & when

Manually instrumenting a method for both a metric and a trace span means writing (and keeping in sync) two separate pieces of code around the same operation — a `Timer.record(...)` call and a `tracer.nextSpan()...end()` block, both wrapping the identical method body. This is redundant and easy to let drift out of sync (one gets updated, the other forgotten). `@Observed` collapses this into one declarative annotation: mark the method, and both the metric and the span are produced together, consistently, from a single `Observation` recording.

Use `@Observed` on service methods where you want both a metric and a trace span with minimal boilerplate — a natural fit for key business operations (`placeOrder`, `chargePayment`) where you'll want both "how often and how long does this take" (the metric) and "where does this fit in the request's trace" (the span) without writing separate instrumentation for each.

## 3. Core concept

An `Observation` represents one occurrence of something worth observing — starting it, optionally attaching context (tags), and stopping it. Registered `ObservationHandler`s (a `TimerObservationHandler`, a tracing-specific handler) each react to the observation's lifecycle (start, stop) and record their own respective form of telemetry from it — a metric handler records a Timer measurement, a tracing handler starts and ends a span — all driven from the single observation, without the application code needing to interact with either concern directly.

```java
@Observed(name = "order.place", contextualName = "placing-order")
public void placeOrder(Order order) { /* ... */ } // produces BOTH a Timer metric AND a trace span, from ONE annotation
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Observation is started and stopped around a method; a metrics handler and a tracing handler both react to it, producing a Timer metric and a trace span respectively, from the same single recording">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">One Observation (start/stop)</text>

  <line x1="280" y1="49" x2="140" y2="90" stroke="#8b949e" marker-end="url(#a374)"/>
  <rect x="20" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Metrics handler -&gt; Timer</text>

  <line x1="360" y1="49" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a374)"/>
  <rect x="380" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Tracing handler -&gt; Span</text>

  <text x="320" y="150" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">ONE observation, TWO handlers, TWO forms of telemetry, from ONE annotation.</text>

  <defs><marker id="a374" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One Observation's start/stop lifecycle drives multiple registered handlers, each producing its own form of telemetry from the same recording.

## 5. Runnable example

Scenario: an order-placement method, first manually instrumented with separate, duplicated metric and tracing code, then rebuilt with a unified Observation abstraction driving both from one recording, and finally extended to show adding a third handler (a structured log entry) with no change to the instrumented method itself.

### Level 1 — Basic

```java
// File: ManualDuplicateInstrumentation.java -- separate, MANUALLY
// duplicated code for the metric AND the trace span, wrapping the SAME
// method body -- easy for the two to drift out of sync over time.
public class ManualDuplicateInstrumentation {
    static long timerTotalDurationMs = 0;
    static int timerCount = 0;
    static java.util.List<String> recordedSpans = new java.util.ArrayList<>();

    static void placeOrder(String orderId) throws InterruptedException {
        long start = System.currentTimeMillis();       // metric instrumentation, part 1
        String spanId = "span-" + orderId;              // tracing instrumentation, part 1 (SEPARATE code)

        Thread.sleep(50); // the actual business logic

        long duration = System.currentTimeMillis() - start; // metric instrumentation, part 2
        timerTotalDurationMs += duration; timerCount++;
        recordedSpans.add(spanId + " duration=" + duration + "ms"); // tracing instrumentation, part 2 (SEPARATE code)
    }

    public static void main(String[] args) throws InterruptedException {
        placeOrder("order-1");
        System.out.println("Metric: count=" + timerCount + ", totalDuration=" + timerTotalDurationMs + "ms");
        System.out.println("Spans: " + recordedSpans);
        System.out.println("TWO separate blocks of instrumentation code, both wrapping the SAME logic -- easy to forget updating one when the other changes.");
    }
}
```

How to run: `java ManualDuplicateInstrumentation.java`

`placeOrder` contains two entirely separate pieces of instrumentation code — one tracking timing for a metric, another tracking a span — both manually wrapped around the same `Thread.sleep(50)` business logic. If a future change needs to add a third concern (say, structured logging), a third separate block would need to be added, and any of the three could be accidentally left out of sync if the method is refactored later.

### Level 2 — Intermediate

```java
// File: UnifiedObservationAbstraction.java -- ONE Observation-style
// wrapper drives BOTH the metric and the trace span from a SINGLE
// start/stop lifecycle, mirroring @Observed's unifying model.
import java.util.*;
import java.util.function.*;

public class UnifiedObservationAbstraction {
    interface ObservationHandler { void onStart(String name); void onStop(String name, long durationMs); }

    static class MetricsHandler implements ObservationHandler {
        Map<String, Long> totalDurations = new HashMap<>();
        Map<String, Integer> counts = new HashMap<>();
        public void onStart(String name) {}
        public void onStop(String name, long durationMs) {
            totalDurations.merge(name, durationMs, Long::sum);
            counts.merge(name, 1, Integer::sum);
        }
    }

    static class TracingHandler implements ObservationHandler {
        List<String> recordedSpans = new ArrayList<>();
        public void onStart(String name) { System.out.println("  [tracing] span started: " + name); }
        public void onStop(String name, long durationMs) { recordedSpans.add(name + " duration=" + durationMs + "ms"); }
    }

    static List<ObservationHandler> handlers = List.of(new MetricsHandler(), new TracingHandler());

    static void observe(String name, Runnable body) throws Exception { // mirrors @Observed's core mechanism
        handlers.forEach(h -> h.onStart(name));
        long start = System.currentTimeMillis();
        body.run();
        long duration = System.currentTimeMillis() - start;
        handlers.forEach(h -> h.onStop(name, duration));
    }

    static void placeOrder(String orderId) throws Exception {
        observe("order.place", () -> { try { Thread.sleep(50); } catch (InterruptedException ignored) {} }); // ONE wrapper, BOTH concerns handled
    }

    public static void main(String[] args) throws Exception {
        placeOrder("order-1");

        MetricsHandler metrics = (MetricsHandler) handlers.get(0);
        TracingHandler tracing = (TracingHandler) handlers.get(1);
        System.out.println("Metric: count=" + metrics.counts.get("order.place") + ", totalDuration=" + metrics.totalDurations.get("order.place") + "ms");
        System.out.println("Spans: " + tracing.recordedSpans);
        System.out.println("ONE 'observe' call produced BOTH -- no duplicated instrumentation code in placeOrder itself.");
    }
}
```

How to run: `java UnifiedObservationAbstraction.java`

`observe` is the single mechanism that starts and stops one logical observation, notifying every registered `ObservationHandler` at each lifecycle point. `placeOrder`'s own code calls `observe` exactly once, wrapping its business logic — both the `MetricsHandler` (accumulating duration and count) and the `TracingHandler` (recording a span) react independently to that same single observation, with `placeOrder` itself containing no separate, duplicated instrumentation code for either concern.

### Level 3 — Advanced

```java
// File: AddThirdHandlerNoMethodChange.java -- adds a THIRD handler (a
// structured log entry) to the SAME observation mechanism, with ZERO
// change to placeOrder's own code -- demonstrating the real value of
// the unified Observation model: new observability concerns are added
// by registering a NEW handler, not by touching every instrumented method.
import java.util.*;

public class AddThirdHandlerNoMethodChange {
    interface ObservationHandler { void onStart(String name); void onStop(String name, long durationMs); }

    static class MetricsHandler implements ObservationHandler {
        Map<String, Integer> counts = new HashMap<>();
        public void onStart(String name) {}
        public void onStop(String name, long durationMs) { counts.merge(name, 1, Integer::sum); }
    }

    static class TracingHandler implements ObservationHandler {
        List<String> recordedSpans = new ArrayList<>();
        public void onStart(String name) {}
        public void onStop(String name, long durationMs) { recordedSpans.add(name + " duration=" + durationMs + "ms"); }
    }

    // The NEW, THIRD handler -- added WITHOUT touching placeOrder or the 'observe' mechanism's callers at all.
    static class StructuredLogHandler implements ObservationHandler {
        List<String> logEntries = new ArrayList<>();
        public void onStart(String name) { logEntries.add("{\"event\":\"start\",\"operation\":\"" + name + "\"}"); }
        public void onStop(String name, long durationMs) { logEntries.add("{\"event\":\"stop\",\"operation\":\"" + name + "\",\"durationMs\":" + durationMs + "}"); }
    }

    static List<ObservationHandler> handlers = List.of(new MetricsHandler(), new TracingHandler(), new StructuredLogHandler()); // just ADD it to the list

    static void observe(String name, Runnable body) {
        handlers.forEach(h -> h.onStart(name));
        long start = System.currentTimeMillis();
        body.run();
        long duration = System.currentTimeMillis() - start;
        handlers.forEach(h -> h.onStop(name, duration));
    }

    static void placeOrder(String orderId) { // COMPLETELY UNCHANGED from Level 2
        observe("order.place", () -> { try { Thread.sleep(30); } catch (InterruptedException ignored) {} });
    }

    public static void main(String[] args) {
        placeOrder("order-1");

        StructuredLogHandler logs = (StructuredLogHandler) handlers.get(2);
        System.out.println("Structured log entries produced by the NEW handler: " + logs.logEntries);
        System.out.println("placeOrder()'s OWN code never changed -- the new logging concern was added PURELY by registering a new handler.");
    }
}
```

How to run: `java AddThirdHandlerNoMethodChange.java`

`placeOrder`'s implementation is byte-for-byte the same as Level 2's — it still just calls `observe("order.place", ...)` once. The only change anywhere is the addition of `StructuredLogHandler` to the `handlers` list; because `observe` already notifies every handler in that list generically, the new handler automatically starts participating in every existing `observe` call across the whole application, producing structured log entries alongside the metric and span, without a single line of `placeOrder` (or any other instrumented method) needing to change.

## 6. Walkthrough

Trace `AddThirdHandlerNoMethodChange.main` in order. **First**, `placeOrder("order-1")` runs, which calls `observe("order.place", () -> { Thread.sleep(30); })`.

**Inside `observe`**, `handlers.forEach(h -> h.onStart(name))` runs first, calling `onStart("order.place")` on all three handlers in order: `MetricsHandler.onStart` does nothing (its `onStart` is empty), `TracingHandler.onStart` also does nothing here, and `StructuredLogHandler.onStart` appends a `{"event":"start", ...}` JSON-shaped string to its own `logEntries` list.

**Next**, `long start = System.currentTimeMillis()` captures the start time, `body.run()` executes the sleep, and `long duration = System.currentTimeMillis() - start` computes the elapsed time (approximately `30ms`).

**Then**, `handlers.forEach(h -> h.onStop(name, duration))` runs, calling `onStop("order.place", duration)` on all three handlers: `MetricsHandler.onStop` increments its `counts` map for `"order.place"`; `TracingHandler.onStop` appends a span-description string to its `recordedSpans` list; `StructuredLogHandler.onStop` appends a `{"event":"stop", ..., "durationMs":...}` JSON-shaped string to its `logEntries` list.

**Finally**, `main` casts `handlers.get(2)` to `StructuredLogHandler` and prints its `logEntries`, showing both the start and stop log entries produced entirely by this new handler — none of which required any change to `placeOrder` or to the `observe` method's own logic beyond the one-line addition of the new handler to the shared `handlers` list.

```
observe("order.place", body) called by placeOrder (UNCHANGED code)
  -> onStart() called on ALL 3 handlers: Metrics (no-op), Tracing (no-op), StructuredLog (logs "start")
  -> body.run() -- the actual business logic
  -> onStop() called on ALL 3 handlers: Metrics (+1 count), Tracing (+1 span), StructuredLog (logs "stop")
```

## 7. Gotchas & takeaways

> `@Observed`'s convenience depends on the correct `ObservationHandler`s actually being registered and configured in the application's `ObservationRegistry` — annotating a method with `@Observed` but forgetting to include, say, the tracing handler in the registry's configuration means that method will silently produce metrics but no spans, without any error indicating the gap.

- `@Observed` and `ObservationRegistry` unify metric and tracing instrumentation (and potentially more) into a single annotation and a single `Observation` recording, instead of requiring separately hand-written code for each concern.
- Registered `ObservationHandler`s each react independently to an observation's start/stop lifecycle, producing their own respective form of telemetry.
- Adding a new observability concern (like structured logging tied to observations) means registering a new handler, not modifying every already-instrumented method.
- This builds directly on both [Micrometer's metrics facade](0366-micrometer-metrics-facade.md) and [Micrometer Tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md), unifying what would otherwise be two separate instrumentation mechanisms into one.
