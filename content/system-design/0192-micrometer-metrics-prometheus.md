---
card: system-design
gi: 192
slug: micrometer-metrics-prometheus
title: Micrometer metrics + Prometheus
---

## 1. What it is

**Micrometer** is a vendor-neutral metrics facade for Java applications — you record [counters, gauges, and histograms](0187-metrics-counters-gauges-histograms.md) through Micrometer's API, and it forwards them to whichever monitoring backend you configure. **Prometheus** is one such backend: a time-series database that periodically *scrapes* (pulls) metrics from an HTTP endpoint your application exposes, rather than the application pushing metrics to it. Spring Boot auto-configures Micrometer with a Prometheus registry out of the box, exposing a `/actuator/prometheus` endpoint automatically.

## 2. Why & when

Hand-rolling metric collection means either bolting on a specific vendor's SDK directly (locking you into that vendor's API everywhere in your code) or reinventing counters and gauges yourself. Micrometer decouples your application code from any specific metrics backend — you write `Counter.builder("orders.created").register(registry).increment()` once, and switching from Prometheus to another backend later needs only a configuration change, not a rewrite of every instrumented line. Use Micrometer in any Spring Boot application that needs metrics, and Prometheus specifically when you want a pull-based, self-hosted (or managed) time-series backend that is the de facto standard in the Kubernetes/cloud-native ecosystem.

## 3. Core concept

- **`MeterRegistry`:** the central object you register and record metrics through; Spring Boot auto-configures one, and multiple registries can be active simultaneously (e.g. Prometheus and another backend at once).
- **`Counter`, `Gauge`, `Timer`, `DistributionSummary`:** Micrometer's core meter types, directly corresponding to the counter/gauge/histogram concepts, plus a `Timer` specifically for measuring durations with built-in percentile support.
- **Pull-based scraping:** unlike a push-based system, Prometheus itself initiates the collection, calling your application's `/actuator/prometheus` endpoint on a schedule (e.g. every 15 seconds) and storing whatever the current metric values are at that moment.
- **Tags (dimensions):** every meter can carry key-value tags (e.g. `endpoint=/checkout`, `status=200`), directly matching the labeling concept covered under metrics generally, letting Prometheus queries slice by any tag combination.
- **`@Timed` annotation:** Spring Boot's AOP-based `@Timed` annotation automatically wraps a method with timing instrumentation, recording a `Timer` metric without manual `start`/`stop` calls in your business logic.

## 4. Diagram

```
   Spring Boot application
        |
   Counter.builder("orders.created").tag("status","success").register(registry).increment()
        |
        v
   MeterRegistry (Micrometer) --------> Prometheus MeterRegistry implementation
                                                |
                                    exposes GET /actuator/prometheus
                                    (text format: orders_created_total{status="success"} 42)
                                                |
                              Prometheus server scrapes this endpoint every 15s
                                                |
                                    stores the time series, queryable via PromQL
```
*Caption: your code only ever talks to Micrometer's registry; Prometheus pulls the current metric values from an HTTP endpoint on its own schedule.*

## 5. Runnable example

This models Micrometer's registry API and Prometheus-style text exposition in-process; the "How to run" note shows the real dependency and endpoint.

**Level 1 — Basic.** Register and increment a tagged counter through a registry, modeling `MeterRegistry`.

**Level 2 — A `Timer`-style metric, recording durations.** Model recording individual timed operations.

**Level 3 — Expose the current metric state in Prometheus's text format.** Model what a scrape of `/actuator/prometheus` would return.

```java
// MicrometerPrometheusDemo.java
import java.util.*;

public class MicrometerPrometheusDemo {

    // Level 1: a tagged counter, modeling Micrometer's Counter + tags.
    static class TaggedCounter {
        final String name;
        final Map<String, Long> countsByTagValue = new LinkedHashMap<>();
        TaggedCounter(String name) { this.name = name; }
        void increment(String tagValue) { countsByTagValue.merge(tagValue, 1L, Long::sum); }
    }

    // Level 2: a Timer-style metric - records individual durations, and can report a percentile.
    static class TimerMetric {
        final String name;
        final List<Long> recordedDurationsMs = new ArrayList<>();
        TimerMetric(String name) { this.name = name; }
        void record(long durationMs) { recordedDurationsMs.add(durationMs); }
        long percentile(double p) {
            List<Long> sorted = new ArrayList<>(recordedDurationsMs);
            Collections.sort(sorted);
            return sorted.get((int) Math.min(sorted.size() - 1, sorted.size() * p));
        }
    }

    static Map<String, TaggedCounter> counters = new LinkedHashMap<>();
    static Map<String, TimerMetric> timers = new LinkedHashMap<>();

    static void incrementCounter(String name, String status) {
        counters.computeIfAbsent(name, TaggedCounter::new).increment(status);
    }

    static void recordTimer(String name, long durationMs) {
        timers.computeIfAbsent(name, TimerMetric::new).record(durationMs);
    }

    // Level 3: expose the current state in Prometheus's plain-text exposition format.
    static String scrapeEndpoint() {
        StringBuilder sb = new StringBuilder();
        for (TaggedCounter counter : counters.values()) {
            for (Map.Entry<String, Long> entry : counter.countsByTagValue.entrySet()) {
                sb.append(counter.name.replace(".", "_")).append("_total{status=\"").append(entry.getKey()).append("\"} ").append(entry.getValue()).append("\n");
            }
        }
        for (TimerMetric timer : timers.values()) {
            sb.append(timer.name.replace(".", "_")).append("_count ").append(timer.recordedDurationsMs.size()).append("\n");
            sb.append(timer.name.replace(".", "_")).append("_p99_ms ").append(timer.percentile(0.99)).append("\n");
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        // Level 1: increment a tagged counter, as @Timed/Counter instrumentation would in a real controller.
        incrementCounter("orders.created", "success");
        incrementCounter("orders.created", "success");
        incrementCounter("orders.created", "success");
        incrementCounter("orders.created", "failure");

        // Level 2: record request durations, as @Timed would automatically do around a controller method.
        int[] sampleDurations = {45, 50, 48, 60, 400}; // one slow outlier
        for (int d : sampleDurations) recordTimer("http.server.requests", d);

        // Level 3: simulate Prometheus scraping the exposed endpoint.
        System.out.println("--- GET /actuator/prometheus (what Prometheus scrapes) ---");
        System.out.println(scrapeEndpoint());
    }
}
```

**How to run:** save as `MicrometerPrometheusDemo.java`, then run `java MicrometerPrometheusDemo.java`. (Real Spring Boot: add `micrometer-registry-prometheus` and `spring-boot-starter-actuator`; inject `MeterRegistry` and call `Counter.builder("orders.created").tag("status", "success").register(registry).increment()`, or annotate a controller method with `@Timed("http.server.requests")` — Spring exposes the resulting metrics automatically at `/actuator/prometheus`.)

## 6. Walkthrough

1. `incrementCounter("orders.created", "success")` is called three times and once with `"failure"`; each call resolves (or creates) the `TaggedCounter` for `"orders.created"` and merges into `countsByTagValue`, ending with `{"success": 3, "failure": 1}` — this models one counter metric, sliced by a `status` tag, exactly as Micrometer's tagged `Counter` works.
2. Five durations are recorded via `recordTimer`, four fast (45-60ms) and one slow outlier (400ms), all added to `recordedDurationsMs` for the `"http.server.requests"` timer.
3. `scrapeEndpoint()` iterates every registered counter and timer, formatting each into Prometheus's plain-text exposition format — for the counter, it emits one line per tag value (`orders_created_total{status="success"} 3` and `orders_created_total{status="failure"} 1`), directly reflecting the tag-based slicing recorded in step 1.
4. For the timer, `scrapeEndpoint` emits both a count line and a `p99` line; `timer.percentile(0.99)` sorts the durations and picks the value at roughly the 99th-percentile position, which — with only 5 samples — lands on the slow `400ms` outlier, correctly surfacing it even though it is a single value among mostly-fast requests.
5. The printed output is exactly the shape Prometheus expects when it performs its periodic scrape of `/actuator/prometheus` — no push happens from the application at all; the metrics simply sit ready, in this exposition format, waiting for the next scrape to pull them.

## 7. Gotchas & takeaways

> Gotcha: using a high-cardinality value (like a raw user ID or request ID) as a Micrometer tag creates a new, permanent time series in Prometheus for every distinct tag value ever seen — this "cardinality explosion" can silently overwhelm Prometheus's storage and query performance; reserve tags for genuinely low-cardinality dimensions (status codes, endpoint names, regions), exactly the same caution that applies to labels generally.

- Micrometer decouples instrumentation code from any specific metrics backend, so switching backends later needs configuration changes, not code rewrites.
- Prometheus's pull-based model means your application only needs to expose current metric state at an endpoint; Prometheus itself controls the scrape schedule.
- Tags let one metric be sliced along multiple dimensions, but only when kept to low-cardinality values.
- Related concepts: [Metrics (counters, gauges, histograms)](0187-metrics-counters-gauges-histograms.md) (the underlying concepts Micrometer implements as a Java API), [Spring Boot Actuator endpoints](0194-spring-boot-actuator-endpoints.md) (the mechanism exposing `/actuator/prometheus` in the first place), [Micrometer Tracing (OpenTelemetry)](0193-micrometer-tracing-opentelemetry.md) (Micrometer's companion library for distributed tracing, using the same instrumentation philosophy).
