---
card: spring-boot
gi: 193
slug: metrics-with-micrometer
title: Metrics with Micrometer
---

## 1. What it is

**Micrometer** is the metrics instrumentation library Spring Boot uses — a vendor-neutral facade, similar to SLF4J but for metrics. Spring Boot auto-configures a `MeterRegistry` that collects counters, gauges, timers, and distribution summaries from your code and from auto-instrumented infrastructure (JVM, HTTP, DataSource, cache). The registry ships data to your monitoring system (Prometheus, Datadog, Graphite, etc.) via a pluggable registry implementation.

## 2. Why & when

Without metrics you're flying blind: you know the service is up, but you don't know if it's slow, overloaded, or degrading. Micrometer answers:
- "How many requests per second is this endpoint handling?" (counter + timer)
- "What is the p99 response time for `POST /orders`?" (timer with histogram)
- "How full is the DB connection pool?" (gauge)
- "How many items are in the work queue?" (gauge)

Add Micrometer to every production service. The `starter-actuator` already includes `micrometer-core`; add a registry dependency (`micrometer-registry-prometheus`) to ship data.

## 3. Core concept

Micrometer **meter types**:

| Meter | Description | Example |
|---|---|---|
| `Counter` | monotonically increasing count | Total HTTP requests served |
| `Gauge` | current value snapshot | Queue depth, connection pool size |
| `Timer` | duration + count + throughput | HTTP request latency |
| `DistributionSummary` | distribution of values (not time) | Request payload sizes in bytes |
| `LongTaskTimer` | measure tasks still in progress | Active background jobs |
| `FunctionCounter` | wrap an external counter | Kafka consumer lag (external counter) |

All meters have:
- A **name** (dot-separated: `http.server.requests`).
- **Tags** (key-value pairs for dimensions): `method=GET`, `status=200`, `uri=/api/orders`.

Tags are the key to useful metrics — they let you filter and group in Grafana/Prometheus.

`MeterRegistry` is the central registry. Inject it into any Spring bean.

## 4. Diagram

<svg viewBox="0 0 700 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code instruments meters via MeterRegistry; registry collects and ships to monitoring back-end">
  <!-- Application layer -->
  <rect x="10" y="30" width="200" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Application</text>
  <text x="110" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Counter.builder("orders.created")</text>
  <text x="110" y="85" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  .tags("status","ok").register(reg)</text>
  <text x="110" y="107" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Timer.builder("order.latency")</text>
  <text x="110" y="121" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  .publishPercentiles(0.95)</text>
  <text x="110" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  .register(reg)</text>
  <text x="110" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ JVM, HTTP, DB auto-meters</text>

  <!-- Arrow to registry -->
  <line x1="213" y1="105" x2="268" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#mma)"/>

  <!-- MeterRegistry -->
  <rect x="273" y="65" width="155" height="80" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">MeterRegistry</text>
  <text x="350" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Counter / Timer / Gauge</text>
  <text x="350" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">with tags</text>
  <text x="350" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CompositeMeterRegistry</text>

  <!-- Arrow to back-ends -->
  <line x1="431" y1="90" x2="492" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#mmb)"/>
  <line x1="431" y1="105" x2="492" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#mmb)"/>
  <line x1="431" y1="120" x2="492" y2="145" stroke="#79c0ff" stroke-width="2" marker-end="url(#mmb)"/>

  <!-- Back-ends -->
  <rect x="496" y="46" width="185" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="588" y="66" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Prometheus (/actuator/prometheus)</text>

  <rect x="496" y="88" width="185" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="588" y="108" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Datadog / Graphite / InfluxDB</text>

  <rect x="496" y="130" width="185" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="588" y="150" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">/actuator/metrics (JSON)</text>

  <text x="350" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">One instrumentation API; back-end is swapped by changing the registry dependency</text>

  <defs>
    <marker id="mma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mmb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Instrument once with Micrometer; route to any monitoring back-end by swapping the registry.

## 5. Runnable example

```java
// MicrometerDemo.java — demonstrates Counter, Timer, Gauge, and tag-based querying
// How to run: java MicrometerDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: inject MeterRegistry; meters auto-export to /actuator/metrics

import java.util.*;
import java.util.concurrent.atomic.*;
import java.util.function.ToDoubleFunction;

public class MicrometerDemo {

    // --- Simplified Micrometer-style API ---
    record Tag(String key, String value) {}

    static class SimpleMeterRegistry {
        final Map<String, Double> counters = new LinkedHashMap<>();
        final Map<String, List<Long>> timers = new LinkedHashMap<>();
        final Map<String, Double> gaugeValues = new LinkedHashMap<>();

        String key(String name, Tag... tags) {
            StringBuilder sb = new StringBuilder(name);
            for (Tag t : tags) sb.append("[").append(t.key()).append("=").append(t.value()).append("]");
            return sb.toString();
        }

        void increment(String name, Tag... tags) {
            counters.merge(key(name, tags), 1.0, Double::sum);
        }

        void recordMs(String name, long ms, Tag... tags) {
            timers.computeIfAbsent(key(name, tags), k -> new ArrayList<>()).add(ms);
        }

        <T> void gauge(String name, T obj, ToDoubleFunction<T> fn, Tag... tags) {
            gaugeValues.put(key(name, tags), fn.applyAsDouble(obj));
        }

        void printMetrics() {
            System.out.println("\n--- Counter metrics ---");
            counters.forEach((k, v) -> System.out.printf("  %s = %.0f%n", k, v));
            System.out.println("\n--- Timer metrics (ms) ---");
            timers.forEach((k, samples) -> {
                LongSummaryStatistics s = samples.stream().mapToLong(Long::longValue).summaryStatistics();
                System.out.printf("  %s  count=%d  mean=%.1f  max=%d%n",
                        k, s.getCount(), s.getAverage(), s.getMax());
            });
            System.out.println("\n--- Gauge metrics ---");
            gaugeValues.forEach((k, v) -> System.out.printf("  %s = %.1f%n", k, v));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Micrometer Metrics Demo ===\n");
        SimpleMeterRegistry registry = new SimpleMeterRegistry();

        // 1. Counter: track order events by status
        registry.increment("orders.created", new Tag("status", "success"), new Tag("channel", "web"));
        registry.increment("orders.created", new Tag("status", "success"), new Tag("channel", "web"));
        registry.increment("orders.created", new Tag("status", "success"), new Tag("channel", "mobile"));
        registry.increment("orders.created", new Tag("status", "error"),   new Tag("channel", "web"));

        // 2. Timer: measure HTTP request latency
        long[] latencies = {12, 45, 23, 350, 18, 67, 14, 890, 33, 21};
        for (long l : latencies) {
            String status = l > 500 ? "500" : "200";
            registry.recordMs("http.server.requests", l,
                    new Tag("method", "POST"), new Tag("uri", "/orders"), new Tag("status", status));
        }

        // 3. Gauge: track queue depth (snapshot of current state)
        AtomicInteger queueDepth = new AtomicInteger(142);
        registry.gauge("orders.queue.size", queueDepth, AtomicInteger::doubleValue);

        AtomicInteger connPoolActive = new AtomicInteger(7);
        registry.gauge("hikaricp.connections.active", connPoolActive, AtomicInteger::doubleValue);

        registry.printMetrics();

        System.out.println("\n--- Querying /actuator/metrics ---");
        System.out.println("GET /actuator/metrics/orders.created");
        System.out.println("GET /actuator/metrics/orders.created?tag=status:success&tag=channel:web");
        System.out.println("GET /actuator/metrics/http.server.requests?tag=status:500");
    }
}
```

**How to run:** `java MicrometerDemo.java`

## 6. Walkthrough

- **Counter**: `increment` is called four times with different tag combinations. Tags create dimensional sub-metrics — you can filter by `status=success` in Grafana to see only successful orders, or by `channel=mobile` to compare channels.
- **Timer**: ten latency samples recorded with `status` tags. The min/mean/max summary simulates Micrometer's `TimeWindowMax` and percentile calculations. In production, add `publishPercentiles(0.95, 0.99)` to enable p95/p99 histograms.
- **Gauge**: `AtomicInteger` reference is passed with a reader function. Micrometer polls the gauge value each time the registry flushes — the value is always current. Useful for queue depths, pool sizes, and any "current level" metric.
- **`/actuator/metrics` query**: the `?tag=` filter lets you narrow to a specific dimension — equivalent to `http_server_requests_total{status="500"}` in PromQL.

## 7. Gotchas & takeaways

> Never use **unbounded tag cardinality** — e.g., `tag("userId", userId)`. Each unique tag value creates a new time series. Millions of users = millions of time series = OOM in your monitoring system. Tags should have a **small, finite number of values** (status codes, method names, endpoints).

> `Gauge` reads the value **at scrape time** — it doesn't accumulate. If the underlying variable is updated between scrapes, the intermediate values are lost. Use `Counter` for "how many times did X happen" and `Gauge` for "what is the current level of X".

- `starter-actuator` includes `micrometer-core`. Add `micrometer-registry-prometheus` to expose `/actuator/prometheus` for Prometheus scraping.
- Use `MeterBinder` (implement and register as `@Bean`) to extract metrics from an external library that doesn't know about Micrometer.
- `management.metrics.enable.jvm=false` disables a family of auto-instrumented metrics.
- `management.metrics.tags.application=order-service` adds a global tag to all meters — useful for multi-service Grafana dashboards.
- `Timer.Sample.start(registry)` captures a start time; call `.stop(timer)` at the end to record duration even across async boundaries.
