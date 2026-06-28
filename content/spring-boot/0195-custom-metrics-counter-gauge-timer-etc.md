---
card: spring-boot
gi: 195
slug: custom-metrics-counter-gauge-timer-etc
title: Custom metrics (Counter, Gauge, Timer, etc.)
---

## 1. What it is

While Micrometer auto-instruments JVM, HTTP, and DataSource metrics, custom business metrics require you to inject a `MeterRegistry` and record values yourself. Spring Boot's auto-configured `MeterRegistry` bean is available for injection anywhere in your application. You create meters using the fluent builder API: `Counter.builder(...)`, `Timer.builder(...)`, `Gauge.builder(...)`, etc.

## 2. Why & when

Auto-instrumented metrics tell you about the framework layer (HTTP requests, GC pauses, pool sizes). Custom metrics tell you about the **business layer** that only your application understands:
- "How many orders were placed this minute?" (counter)
- "What is the current fraud-score threshold?" (gauge)
- "How long did the PDF generation take?" (timer)
- "What is the distribution of order values?" (distribution summary)

Add custom metrics wherever business events happen: service methods, event listeners, scheduled tasks, message consumers.

## 3. Core concept

```java
@Service
public class OrderService {

    private final Counter ordersCreated;
    private final Timer   orderLatency;
    private final AtomicInteger activeOrders = new AtomicInteger(0);

    public OrderService(MeterRegistry registry) {
        this.ordersCreated = Counter.builder("orders.created")
            .description("Number of orders placed")
            .tag("channel", "web")
            .register(registry);

        this.orderLatency = Timer.builder("orders.processing.time")
            .description("Order processing latency")
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);

        Gauge.builder("orders.active", activeOrders, AtomicInteger::get)
            .description("Currently active orders")
            .register(registry);
    }

    public Order createOrder(OrderRequest req) {
        return orderLatency.record(() -> {
            activeOrders.incrementAndGet();
            try {
                Order order = processOrder(req);
                ordersCreated.increment();
                return order;
            } finally {
                activeOrders.decrementAndGet();
            }
        });
    }
}
```

Key API patterns:
- **Counter**: `counter.increment()` or `counter.increment(n)`.
- **Timer**: `timer.record(Runnable)`, `timer.record(Duration)`, or `Timer.Sample.start(registry).stop(timer)`.
- **Gauge**: wraps an existing object — Micrometer polls the function at scrape time.
- **DistributionSummary**: `summary.record(double)` for non-time distributions (bytes, dollars).

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four meter types: Counter increments, Timer records duration, Gauge reads current value, DistributionSummary records sizes">
  <!-- Counter -->
  <rect x="10" y="30" width="155" height="75" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Counter</text>
  <text x="87" y="68" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">orders.created</text>
  <text x="87" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">monotonically ↑</text>
  <text x="87" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">counter.increment()</text>

  <!-- Timer -->
  <rect x="175" y="30" width="155" height="75" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="252" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Timer</text>
  <text x="252" y="68" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">orders.processing.time</text>
  <text x="252" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">count + total + max</text>
  <text x="252" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">timer.record(Callable)</text>

  <!-- Gauge -->
  <rect x="340" y="30" width="155" height="75" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="417" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Gauge</text>
  <text x="417" y="68" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">orders.active</text>
  <text x="417" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">current level snapshot</text>
  <text x="417" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Gauge.builder(obj, fn)</text>

  <!-- DistributionSummary -->
  <rect x="505" y="30" width="165" height="75" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="587" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">DistributionSummary</text>
  <text x="587" y="68" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">order.value.dollars</text>
  <text x="587" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">non-time histogram</text>
  <text x="587" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">summary.record(amount)</text>

  <!-- All feed into registry -->
  <line x1="87"  y1="108" x2="87"  y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cma)"/>
  <line x1="252" y1="108" x2="252" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cma)"/>
  <line x1="417" y1="108" x2="417" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cmb)"/>
  <line x1="587" y1="108" x2="587" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cmb)"/>

  <!-- MeterRegistry -->
  <rect x="50" y="140" width="590" height="42" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="166" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">MeterRegistry (auto-injected by Spring Boot)</text>

  <defs>
    <marker id="cma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cmb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

All four meter types register with the `MeterRegistry`; Spring Boot routes them to configured monitoring back-ends.

## 5. Runnable example

```java
// CustomMetricsDemo.java — Counter, Timer, Gauge, DistributionSummary in action
// How to run: java CustomMetricsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: inject MeterRegistry; use Counter/Timer/Gauge/DistributionSummary builders

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.function.ToDoubleFunction;

public class CustomMetricsDemo {

    // ---- Simplified meter implementations ----
    static class SimpleCounter {
        double count = 0;
        final String name; final Map<String,String> tags;
        SimpleCounter(String name, Map<String,String> tags) { this.name=name; this.tags=tags; }
        void increment() { count++; }
        void increment(double n) { count += n; }
    }

    static class SimpleTimer {
        final List<Long> samples = new ArrayList<>();
        final String name;
        SimpleTimer(String name) { this.name = name; }
        <T> T record(java.util.concurrent.Callable<T> fn) throws Exception {
            long start = System.nanoTime();
            T result = fn.call();
            samples.add((System.nanoTime() - start) / 1_000_000L);
            return result;
        }
        LongSummaryStatistics stats() { return samples.stream().mapToLong(Long::longValue).summaryStatistics(); }
    }

    static class SimpleGauge {
        final String name;
        final java.util.function.DoubleSupplier reader;
        SimpleGauge(String name, java.util.function.DoubleSupplier reader) {
            this.name = name; this.reader = reader;
        }
        double value() { return reader.getAsDouble(); }
    }

    static class SimpleDistributionSummary {
        final List<Double> samples = new ArrayList<>();
        final String name;
        SimpleDistributionSummary(String name) { this.name = name; }
        void record(double amount) { samples.add(amount); }
        DoubleSummaryStatistics stats() { return samples.stream().mapToDouble(Double::doubleValue).summaryStatistics(); }
    }

    // ---- Business service using custom metrics ----
    static final AtomicInteger activeOrders = new AtomicInteger(0);
    static final SimpleCounter ordersCreated = new SimpleCounter("orders.created", Map.of("channel","web"));
    static final SimpleCounter orderErrors   = new SimpleCounter("orders.errors",  Map.of("reason","payment_failed"));
    static final SimpleTimer   orderTimer    = new SimpleTimer("orders.processing.time");
    static final SimpleGauge   activeGauge   = new SimpleGauge("orders.active", activeOrders::doubleValue);
    static final SimpleDistributionSummary orderValues =
            new SimpleDistributionSummary("orders.value.dollars");

    static String processOrder(double amount) throws Exception {
        activeOrders.incrementAndGet();
        Thread.sleep(new Random().nextInt(50) + 10); // simulate work 10-60ms
        activeOrders.decrementAndGet();
        return "ORDER-" + System.currentTimeMillis();
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Custom Metrics Demo ===\n");

        // Process 10 orders
        double[] amounts = {49.99, 199.00, 14.50, 349.95, 89.99, 24.99, 599.00, 12.00, 74.95, 129.99};
        for (double amount : amounts) {
            try {
                String id = orderTimer.record(() -> processOrder(amount));
                ordersCreated.increment();
                orderValues.record(amount);
                System.out.printf("  Processed %s  amount=$%.2f%n", id, amount);
            } catch (Exception e) {
                orderErrors.increment();
            }
        }

        System.out.println("\n--- Metrics Report (as /actuator/metrics would show) ---");

        // Counter
        System.out.printf("%nCounter  '%s' [%s]%n", ordersCreated.name, ordersCreated.tags);
        System.out.printf("  count = %.0f%n", ordersCreated.count);

        // Timer
        LongSummaryStatistics ts = orderTimer.stats();
        System.out.printf("%nTimer    '%s'%n", orderTimer.name);
        System.out.printf("  count=%d  mean=%.1fms  max=%dms%n",
                ts.getCount(), ts.getAverage(), ts.getMax());

        // Gauge (current snapshot)
        System.out.printf("%nGauge    '%s'%n", activeGauge.name);
        System.out.printf("  current value = %.0f (all orders done)%n", activeGauge.value());

        // DistributionSummary
        DoubleSummaryStatistics ds = orderValues.stats();
        System.out.printf("%nDistSummary '%s'%n", orderValues.name);
        System.out.printf("  count=%d  mean=$%.2f  max=$%.2f  total=$%.2f%n",
                ds.getCount(), ds.getAverage(), ds.getMax(), ds.getSum());

        System.out.println("\n--- Real Spring Boot usage ---");
        System.out.println("Counter.builder(\"orders.created\").tag(\"channel\",\"web\").register(registry).increment();");
        System.out.println("timer.record(() -> processOrder(req));");
        System.out.println("Gauge.builder(\"orders.active\", queue, Collection::size).register(registry);");
        System.out.println("summary.record(order.getTotal().doubleValue());");
    }
}
```

**How to run:** `java CustomMetricsDemo.java`

## 6. Walkthrough

- **Counter `ordersCreated`**: increments once per successful order. Tagged with `channel=web`. In Prometheus: `orders_created_total{channel="web"}`.
- **Timer `orderTimer`**: wraps the entire `processOrder` call including the simulated `Thread.sleep`. Reports count, mean, and max. In production, add `.publishPercentiles(0.95, 0.99)` for SLO tracking.
- **Gauge `activeGauge`**: wraps `activeOrders.doubleValue()`. After processing all orders, `activeOrders=0`. Micrometer reads this lazily at scrape time — not when you create the gauge.
- **DistributionSummary `orderValues`**: records dollar amounts. Reports count, mean, max, and total. Not time-based — use for any non-duration numerical distribution (payload sizes, queue depths, dollar amounts).
- The final printout simulates what `GET /actuator/metrics/orders.created` returns.

## 7. Gotchas & takeaways

> Calling `Counter.builder(...).register(registry)` multiple times with the **same name and tags** returns the same meter instance — Micrometer de-duplicates. Do not cache the returned `Counter` to avoid unnecessary re-registration overhead; let the registry handle identity.

> `Gauge` survives only as long as the object it references. If the `AtomicInteger` is garbage-collected, the gauge silently disappears from the registry. Hold a strong reference to the gauged object for the lifetime of the application.

- `MeterBinder` is the right pattern for library authors — implement it and register via `@Bean` so users don't need to call `register()` manually.
- `Timer.Sample.start(registry)` + `sample.stop(timer)` works across async boundaries (e.g., start before a `CompletableFuture`, stop in the callback).
- Avoid registering meters in loops — meters should be registered once (e.g., in the constructor) and reused.
- `DistributionSummary.builder(...).publishPercentileHistogram(true)` enables Prometheus-compatible histogram buckets for `histogram_quantile()` queries.
- `LongTaskTimer` is for measuring tasks still in progress — use it for background jobs, not per-request latency.
