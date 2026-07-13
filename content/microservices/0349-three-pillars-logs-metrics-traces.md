---
card: microservices
gi: 349
slug: three-pillars-logs-metrics-traces
title: "Three pillars: logs, metrics, traces"
---

## 1. What it is

The **three pillars of observability** are **logs** (discrete, timestamped records of individual events — "order-1 was placed at 10:02:03"), **metrics** (aggregated numeric measurements over time — "requests per second," "p99 latency," "error count") and **traces** (the end-to-end path a single request took as it moved through multiple services, with timing at each step). Each pillar answers a different kind of question, and in a microservices system, you typically need all three together to understand what's actually happening.

## 2. Why & when

In a monolith, understanding a slow or broken request often just meant reading a stack trace or a log file in one place. In microservices, a single user-facing request can fan out across five, ten, or more services, and no single log file, metric, or process has the full picture on its own. Logs tell you *what happened* in detail, but a mountain of per-service logs doesn't by itself show you *how slow* things are trending, or *which specific request* touched which specific services. Metrics tell you *how the system is trending* in aggregate ("error rate is up 3x since 10am"), but not *which individual request* failed or why. Traces tell you *the path and timing of one specific request* across every service it touched, but tracing every request in full detail at high volume is often too expensive to do continuously.

Use all three together: metrics as your always-on, cheap, aggregate early-warning system (something is wrong); traces to pinpoint exactly where in a specific request's path the problem occurred (this is where); logs, correlated to that specific trace, to see the precise detail of what happened at that point (this is why). Reach for one pillar in isolation only for a narrow, specific question (a metric dashboard for a general health check; a single service's logs for a very localized bug), but rely on their combination for understanding cross-service behavior.

## 3. Core concept

Logs are discrete events, one line per occurrence, rich in detail but expensive to store and search at scale (and not naturally aggregated). Metrics are numeric time series, cheap to store and query in aggregate, but they lose all per-event detail — they can tell you *that* errors increased, never *which* request caused a particular error. Traces are structured as a tree of **spans** (a span represents one unit of work, like one service's handling of one request), linked together into a single trace that shows the whole request's path and per-step timing — rich in cross-service detail, but usually sampled (not captured for every request) because capturing everything is costly at scale.

```java
record LogEvent(Instant timestamp, String message, Map<String,String> context) {}
record MetricPoint(String name, double value, Instant timestamp, Map<String,String> labels) {}
record Span(String traceId, String spanId, String service, Instant start, Duration duration) {}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three columns: Logs (discrete events, what happened), Metrics (aggregated numbers, how the system trends), Traces (one request's path across services, where it went)">
  <rect x="20" y="20" width="185" height="140" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="112" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Logs</text>
  <text x="112" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">discrete events</text>
  <text x="112" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">WHAT happened</text>

  <rect x="228" y="20" width="185" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Metrics</text>
  <text x="320" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">aggregated numbers</text>
  <text x="320" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">HOW it's trending</text>

  <rect x="435" y="20" width="185" height="140" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="528" y="45" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Traces</text>
  <text x="528" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">one request's full path</text>
  <text x="528" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">WHERE it went wrong</text>
</svg>

Each pillar answers a different question; together they let you notice a problem, locate it, and understand it in detail.

## 5. Runnable example

Scenario: a slow checkout request across two services, first observed with only logs scattered across two services (hard to connect), then with a metric revealing the overall trend, and finally with a trace tying both together end-to-end with per-step timing.

### Level 1 — Basic

```java
// File: LogsOnlyScatteredAcrossServices.java -- each service logs its own
// events independently; connecting them across services is manual and hard.
import java.util.*;

public class LogsOnlyScatteredAcrossServices {
    static List<String> orderServiceLogs = new ArrayList<>();
    static List<String> paymentServiceLogs = new ArrayList<>();

    static void handleCheckout(String orderId) {
        orderServiceLogs.add("[order-service] received checkout request for " + orderId);
        orderServiceLogs.add("[order-service] calling payment-service...");
        chargePayment(orderId);
        orderServiceLogs.add("[order-service] checkout complete for " + orderId);
    }

    static void chargePayment(String orderId) {
        paymentServiceLogs.add("[payment-service] processing charge (no idea WHICH order-service request this is for!)");
        paymentServiceLogs.add("[payment-service] charge succeeded");
    }

    public static void main(String[] args) {
        handleCheckout("order-1");
        System.out.println("order-service logs: " + orderServiceLogs);
        System.out.println("payment-service logs: " + paymentServiceLogs);
        System.out.println("Nothing LINKS these two log sets together -- with many concurrent checkouts, this becomes unreadable.");
    }
}
```

How to run: `java LogsOnlyScatteredAcrossServices.java`

Both services log their own events, but `paymentServiceLogs` has no reference back to `"order-1"` or to `order-service`'s specific request — with only one checkout happening, a human could guess the connection, but with many concurrent checkouts, there's no reliable way to tell which payment-service log lines belong to which order-service request.

### Level 2 — Intermediate

```java
// File: MetricRevealsTrend.java -- a metric aggregates checkout LATENCY
// across many requests, revealing a trend that individual logs can't show.
import java.util.*;

public class MetricRevealsTrend {
    static List<Long> checkoutLatenciesMs = new ArrayList<>(); // the raw data behind the metric

    static void recordCheckoutLatency(long latencyMs) { checkoutLatenciesMs.add(latencyMs); }

    static double p99LatencyMs() { // a typical metric: 99th percentile latency
        List<Long> sorted = new ArrayList<>(checkoutLatenciesMs);
        Collections.sort(sorted);
        int index = (int) Math.ceil(0.99 * sorted.size()) - 1;
        return sorted.get(Math.max(index, 0));
    }

    public static void main(String[] args) {
        for (int i = 0; i < 98; i++) recordCheckoutLatency(120); // 98 normal, fast checkouts
        recordCheckoutLatency(4000);  // one slow one
        recordCheckoutLatency(4200);  // another slow one

        System.out.println("Total checkouts recorded: " + checkoutLatenciesMs.size());
        System.out.println("p99 latency: " + p99LatencyMs() + "ms -- the METRIC reveals something is wrong in aggregate,");
        System.out.println("but does NOT tell us WHICH specific checkout was slow, or WHY.");
    }
}
```

How to run: `java MetricRevealsTrend.java`

`p99LatencyMs` computes the 99th-percentile latency across all recorded checkouts, revealing that *some* checkouts are taking 4+ seconds even though most are fast — this is exactly the kind of aggregate signal a metric provides cheaply and continuously. But the metric alone can't say which specific checkout(s) were slow or what caused the slowness; that requires a trace.

### Level 3 — Advanced

```java
// File: TraceTiesItAllTogether.java -- a SINGLE trace ID links spans
// across BOTH services for the same checkout request, with per-step
// timing, tying the "where" and the "why" together end-to-end.
import java.util.*;

public class TraceTiesItAllTogether {
    record Span(String traceId, String service, String operation, long startMs, long durationMs) {}
    static List<Span> spans = new ArrayList<>(); // the trace, as a flat list of spans sharing one traceId

    static void handleCheckout(String traceId, String orderId, long baseTimeMs) {
        long start = baseTimeMs;
        spans.add(new Span(traceId, "order-service", "handleCheckout", start, 10));
        chargePayment(traceId, orderId, start + 10);
        spans.add(new Span(traceId, "order-service", "completeCheckout", start + 10 + 3900, 20));
    }

    static void chargePayment(String traceId, String orderId, long startMs) {
        spans.add(new Span(traceId, "payment-service", "chargePayment", startMs, 3900)); // the SLOW step, now VISIBLE
    }

    static void printTrace(String traceId) {
        System.out.println("Trace " + traceId + " (chronological, across BOTH services):");
        spans.stream().filter(s -> s.traceId().equals(traceId))
                .sorted(Comparator.comparingLong(Span::startMs))
                .forEach(s -> System.out.println("  [" + s.service() + "] " + s.operation()
                        + " -- started at t=" + s.startMs() + "ms, took " + s.durationMs() + "ms"));
    }

    public static void main(String[] args) {
        handleCheckout("trace-abc123", "order-1", 0);
        printTrace("trace-abc123");
        System.out.println("The trace shows EXACTLY where the time went: payment-service's chargePayment took 3900ms of the total.");
    }
}
```

How to run: `java TraceTiesItAllTogether.java`

Every `Span` created during this one checkout — in both `order-service` and `payment-service` — shares the same `traceId`, `"trace-abc123"`. `printTrace` filters and sorts all spans for that trace by start time, printing a chronological, cross-service view of exactly what happened and how long each step took. Unlike Level 1's disconnected logs or Level 2's aggregate metric, this trace immediately shows that `payment-service`'s `chargePayment` span took `3900ms` — the specific step, in the specific request, responsible for the slowness the metric had only hinted at in aggregate.

## 6. Walkthrough

Trace `TraceTiesItAllTogether.main` in order. **First**, `handleCheckout("trace-abc123", "order-1", 0)` runs: it creates a `Span` for `order-service`'s `"handleCheckout"` operation, starting at `t=0` and lasting `10ms`, and appends it to `spans`.

**Next**, `chargePayment("trace-abc123", "order-1", 10)` is called (using `start + 10 = 10` as the new start time). Inside, it creates a `Span` for `payment-service`'s `"chargePayment"` operation, starting at `t=10ms` and lasting `3900ms` — this is the slow step — and appends it to `spans`, still tagged with the same `traceId`.

**Back in `handleCheckout`**, after `chargePayment` returns, a final `Span` is created for `order-service`'s `"completeCheckout"` operation, starting at `t = 10 + 3900 = 3910ms` and lasting `20ms`, and appended to `spans`.

**Then**, `printTrace("trace-abc123")` runs: it filters `spans` down to only those matching this trace ID (all three qualify), sorts them by `startMs`, and prints each in chronological order — `handleCheckout` at `t=0`, `chargePayment` at `t=10`, `completeCheckout` at `t=3910` — showing the full cross-service path and timing of this one specific request.

**Finally**, `main` prints a summary line pointing directly at `chargePayment`'s `3900ms` duration as the dominant contributor to the overall checkout latency — information no single service's logs or the aggregate metric alone could pinpoint this precisely.

```
Trace trace-abc123:
  [order-service]   handleCheckout    t=0ms,    10ms
  [payment-service] chargePayment     t=10ms,   3900ms  <-- the slow step, now VISIBLE and LOCATED
  [order-service]   completeCheckout  t=3910ms, 20ms
```

## 7. Gotchas & takeaways

> Relying on only one pillar leaves a real blind spot: logs alone can't show aggregate trends or cross-service timing; metrics alone can't identify which specific request or step caused a problem; traces alone (especially if sampled) can miss a rare issue entirely if that particular request wasn't captured. Production observability setups deliberately combine all three, often correlated via a shared identifier (see [correlation IDs](0351-correlation-ids-request-ids.md)).

- Logs answer "what happened" in fine-grained detail for a specific event; metrics answer "how is the system trending" in cheap aggregate; traces answer "where did this specific request go, and how long did each step take."
- In microservices, no single pillar gives the full picture on its own — a request spanning multiple services needs all three, ideally correlated together.
- A typical diagnostic flow: metrics flag that something is wrong in aggregate, a trace pinpoints which service and step is responsible, and correlated logs at that point provide the exact detail of why.
- The next several topics build on this foundation: [correlation IDs](0351-correlation-ids-request-ids.md) tie logs and traces together, and [distributed tracing concepts](0352-distributed-tracing-concepts-trace-span-context-propagation.md) formalize the trace/span model shown here.
