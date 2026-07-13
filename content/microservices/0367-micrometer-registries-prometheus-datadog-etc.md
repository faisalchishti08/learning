---
card: microservices
gi: 367
slug: micrometer-registries-prometheus-datadog-etc
title: "Micrometer registries (Prometheus, Datadog, etc.)"
---

## 1. What it is

A **Micrometer registry** is the concrete implementation behind Micrometer's `MeterRegistry` interface that determines how recorded metrics actually reach a specific monitoring backend — a `PrometheusMeterRegistry` exposes metrics on a `/actuator/prometheus` endpoint for Prometheus to scrape (pull-based); a `DatadogMeterRegistry` periodically pushes metrics to Datadog's API (push-based); other registries exist for CloudWatch, New Relic, InfluxDB, and more. Adding the right registry dependency and a small amount of configuration is typically all that's needed — no application code changes at all, exactly the point of [Micrometer's facade design](0366-micrometer-metrics-facade.md).

## 2. Why & when

Different monitoring backends have fundamentally different models for receiving metrics: Prometheus expects to periodically *pull* (scrape) an HTTP endpoint that exposes current metric values in its own text format; Datadog and several other SaaS platforms expect the application to periodically *push* metrics to their API. A registry implementation absorbs this difference entirely — application code calling `registry.counter(...).increment()` never needs to know or care whether the underlying registry is pull-based or push-based; that's the registry's job, configured once, separately from the metrics-recording code.

Choose the registry matching your organization's monitoring backend, add its dependency, and configure it (an endpoint path for pull-based registries, an API key and step interval for push-based ones) — this is almost entirely configuration, not code. Multiple registries can even be active simultaneously (a `CompositeMeterRegistry`) if you need to export the same metrics to more than one backend at once, again with no change to the application code recording them.

## 3. Core concept

A pull-based registry (Prometheus) maintains an in-memory snapshot of current metric values and serves them on demand when the monitoring system's scraper makes an HTTP request. A push-based registry (Datadog and similar) runs its own internal timer that periodically (every "step" interval, commonly 10 or 60 seconds) sends the current metric values to the backend's API proactively, without waiting to be asked.

```java
// Pull-based: registry exposes an endpoint; Prometheus scrapes it periodically.
PrometheusMeterRegistry prometheusRegistry = new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);

// Push-based: registry itself pushes on a timer; nobody scrapes it.
DatadogMeterRegistry datadogRegistry = new DatadogMeterRegistry(datadogConfig, Clock.SYSTEM);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pull-based: Prometheus periodically scrapes an HTTP endpoint the registry exposes. Push-based: the registry itself proactively sends metrics to Datadog's API on a timer, with nobody scraping anything">
  <rect x="30" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Pull-based (Prometheus)</text>
  <text x="165" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">app exposes /actuator/prometheus</text>
  <text x="165" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Prometheus SCRAPES it periodically</text>

  <rect x="340" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="475" y="45" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Push-based (Datadog)</text>
  <text x="475" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">registry itself PUSHES on a timer</text>
  <text x="475" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">nobody scrapes anything</text>
</svg>

Pull-based registries expose an endpoint for the backend to scrape; push-based registries proactively send data to the backend on their own timer.

## 5. Runnable example

Scenario: the same order-counting metric, first shown with a hand-rolled, backend-agnostic approach that doesn't actually deliver data anywhere, then rebuilt as a simulated pull-based (Prometheus-style) registry, and finally rebuilt as a simulated push-based (Datadog-style) registry, with identical application code for both.

### Level 1 — Basic

```java
// File: NoDeliveryMechanism.java -- a counter is recorded, but there's
// NO registry actually delivering it anywhere -- the data just sits,
// invisible to any monitoring backend.
import java.util.*;

public class NoDeliveryMechanism {
    static Map<String, Integer> counters = new HashMap<>();

    static void recordOrderPlaced() { counters.merge("orders.placed", 1, Integer::sum); }

    public static void main(String[] args) {
        recordOrderPlaced();
        recordOrderPlaced();
        System.out.println("Counters recorded: " + counters);
        System.out.println("But NOTHING exposes this data to Prometheus, Datadog, or ANY monitoring backend -- it's invisible outside this process.");
    }
}
```

How to run: `java NoDeliveryMechanism.java`

`counters` correctly accumulates the recorded values in memory, but nothing here makes that data reachable by any external monitoring system — no HTTP endpoint to scrape, no outbound push to any API. This is metrics recording with no actual registry behind it.

### Level 2 — Intermediate

```java
// File: PullBasedRegistry.java -- a simulated PROMETHEUS-style registry:
// it exposes a snapshot on demand (via a simulated HTTP GET), waiting
// PASSIVELY to be scraped rather than sending anything proactively.
import java.util.*;

public class PullBasedRegistry {
    static class PrometheusStyleRegistry {
        Map<String, Integer> counters = new HashMap<>();
        void incrementCounter(String name) { counters.merge(name, 1, Integer::sum); } // just updates in-memory state

        String handleScrapeRequest() { // simulates Prometheus's periodic GET /actuator/prometheus
            StringBuilder sb = new StringBuilder();
            counters.forEach((name, value) -> sb.append(name).append(" ").append(value).append("\n"));
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        PrometheusStyleRegistry registry = new PrometheusStyleRegistry();
        registry.incrementCounter("orders.placed");
        registry.incrementCounter("orders.placed");

        System.out.println("Registry updated in-memory; nothing sent anywhere YET.");
        System.out.println("--- Prometheus's scraper makes its periodic GET request ---");
        String scrapedData = registry.handleScrapeRequest();
        System.out.println("Scraped response:\n" + scrapedData);
    }
}
```

How to run: `java PullBasedRegistry.java`

`incrementCounter` only updates in-memory state — no data is sent anywhere at that moment. Only when `handleScrapeRequest` is explicitly called (simulating Prometheus's periodic incoming GET request) does the registry actually produce output — the delivery happens passively, on the *scraper's* schedule, not the application's.

### Level 3 — Advanced

```java
// File: PushBasedRegistry.java -- a simulated DATADOG-style registry: it
// runs its OWN internal timer and PROACTIVELY sends data on a fixed step
// interval, with NOBODY scraping anything -- the IDENTICAL application
// code from Level 2's pattern works unchanged here too.
import java.util.*;

public class PushBasedRegistry {
    interface MeterRegistry { void incrementCounter(String name); }

    static class OrderMetrics { // identical shape to the facade example -- APPLICATION code, backend-agnostic
        private final MeterRegistry registry;
        OrderMetrics(MeterRegistry registry) { this.registry = registry; }
        void recordOrderPlaced() { registry.incrementCounter("orders.placed"); }
    }

    static class DatadogStyleRegistry implements MeterRegistry {
        Map<String, Integer> pendingCounters = new HashMap<>();
        List<String> pushedBatches = new ArrayList<>();

        public void incrementCounter(String name) { pendingCounters.merge(name, 1, Integer::sum); }

        void runStepIntervalPush() { // simulates the registry's OWN internal timer firing, e.g. every 10 seconds
            if (pendingCounters.isEmpty()) { System.out.println("  [push timer fired] nothing new to push"); return; }
            String batch = pendingCounters.toString();
            pushedBatches.add(batch);
            System.out.println("  [push timer fired] PUSHED to Datadog API: " + batch);
            pendingCounters.clear(); // reset for the next interval
        }
    }

    public static void main(String[] args) {
        DatadogStyleRegistry registry = new DatadogStyleRegistry();
        OrderMetrics metrics = new OrderMetrics(registry); // SAME OrderMetrics shape as Level 2's Prometheus example would use

        metrics.recordOrderPlaced();
        metrics.recordOrderPlaced();
        System.out.println("Two orders recorded; nothing pushed YET -- waiting for the registry's own internal timer.");

        registry.runStepIntervalPush(); // simulates the timer firing, e.g. after 10 seconds pass
        registry.runStepIntervalPush(); // fires again with NOTHING new -- correctly pushes nothing

        System.out.println("All pushed batches so far: " + registry.pushedBatches);
    }
}
```

How to run: `java PushBasedRegistry.java`

`recordOrderPlaced` (via `OrderMetrics`, exactly the same shape application code would use regardless of backend) only accumulates into `pendingCounters` — nothing is sent at that moment. `runStepIntervalPush`, standing in for the registry's own internal timer firing, is what actually triggers delivery: the first call finds accumulated data and pushes it (then clears it for the next interval); the second call, run immediately after with nothing new accumulated, correctly pushes nothing. This demonstrates the defining difference from Level 2: delivery here happens on the *registry's own* schedule, entirely independent of any external scraper.

## 6. Walkthrough

Trace `PushBasedRegistry.main` in order. **First**, `metrics.recordOrderPlaced()` is called twice. Each call invokes `registry.incrementCounter("orders.placed")`, which runs `pendingCounters.merge("orders.placed", 1, Integer::sum)` — after both calls, `pendingCounters` holds `{"orders.placed": 2}`. Nothing has been pushed or sent anywhere yet.

**Next**, `registry.runStepIntervalPush()` is called for the first time, standing in for the registry's internal timer firing after its configured step interval elapses. `pendingCounters.isEmpty()` is `false` (it holds one entry), so the method builds `batch` from `pendingCounters.toString()`, appends it to `pushedBatches`, prints a confirmation, and clears `pendingCounters` back to empty.

**Then**, `runStepIntervalPush()` is called a second time, immediately after, simulating the next timer tick. This time `pendingCounters.isEmpty()` is `true` (it was just cleared and nothing new was recorded in between), so the method takes the early-return branch, printing that there's nothing new to push and leaving `pushedBatches` unchanged.

**Finally**, `main` prints `registry.pushedBatches`, which contains exactly one entry — the batch pushed during the first timer firing — demonstrating that delivery happened proactively, on the registry's own internal schedule, entirely decoupled from when the application code happened to record its metrics.

```
recordOrderPlaced() x2  -> pendingCounters={orders.placed: 2}, nothing pushed yet
runStepIntervalPush() #1 -> pendingCounters NOT empty -> PUSH {orders.placed: 2} -> pendingCounters cleared
runStepIntervalPush() #2 -> pendingCounters IS empty  -> nothing to push, correctly skipped
pushedBatches: ["{orders.placed=2}"]
```

## 7. Gotchas & takeaways

> Configuring a push-based registry's step interval too short relative to your actual metric-recording volume can generate excessive outbound network traffic and backend ingestion costs; too long, and your dashboards and alerts lag behind reality by however long that interval is. Tune the step interval deliberately, matching your actual latency and cost requirements.

- A Micrometer registry (Prometheus, Datadog, CloudWatch, and others) is the concrete implementation determining how recorded metrics actually reach a monitoring backend — pull-based (scraped on demand) or push-based (sent proactively on a timer).
- Application code recording metrics through Micrometer's facade never needs to know or care which model the configured registry uses.
- Multiple registries can be active simultaneously via a composite registry, exporting the same recorded metrics to more than one backend without any change to the recording code.
- This registry layer is what actually backs [Actuator's `/metrics` endpoint](0365-spring-boot-actuator-endpoints-health-info-metrics-env-etc.md) and every [custom meter](0368-custom-meters-counter-gauge-timer-distributionsummary.md) an application records.
