---
card: spring-boot
gi: 196
slug: timed-observation-api
title: "@Timed / Observation API"
---

## 1. What it is

Spring Boot 3 provides two annotation/API-level approaches for adding metrics without manually wiring `MeterRegistry`:

- **`@Timed`** — annotate a method; Spring AOP wraps it with a `Timer` recording duration and call count. Requires `TimedAspect` bean.
- **`Observation API`** (Micrometer 1.10+ / Spring Boot 3) — a higher-level abstraction that records **both metrics and traces** from one observation block. An `ObservationRegistry` is auto-configured; instrument code with `Observation.start(...)`.

## 2. Why & when

**`@Timed`:** the simplest way to add request latency metrics to a service method — one annotation, no `MeterRegistry` injection needed. Best for straightforward before/after timing.

**Observation API:** when you need **unified metrics + tracing**. Instead of writing separate Micrometer and OpenTelemetry/Brave instrumentation, one `Observation` generates both a timer metric and a distributed trace span. Spring Boot auto-configures this bridge.

**When to use which:**
- Greenfield code in Spring Boot 3: prefer `Observation API` — it's the strategic path and gives both metrics and traces.
- Quick timing of a method: `@Timed` is simpler.
- Complex business flows with nested spans: `Observation API`.

## 3. Core concept

**`@Timed`:**
```java
@Configuration
public class TimedAspectConfig {
    @Bean TimedAspect timedAspect(MeterRegistry registry) {
        return new TimedAspect(registry);
    }
}

@Service
public class OrderService {
    @Timed(value = "orders.create", percentiles = {0.5, 0.95},
           description = "Time to create an order")
    public Order createOrder(OrderRequest req) { ... }
}
```

**Observation API:**
```java
@Service
public class OrderService {
    private final ObservationRegistry observationRegistry;

    public Order createOrder(OrderRequest req) {
        return Observation.createNotStarted("orders.create", observationRegistry)
            .highCardinalityKeyValue("orderId", req.getId())
            .observe(() -> {
                // code here is timed + traced automatically
                return processOrder(req);
            });
    }
}
```

`Observation` lifecycle: `start()` → `observe(Supplier)` → `stop()`. Tags added via `lowCardinalityKeyValue` (appear on metrics) and `highCardinalityKeyValue` (appear only on trace spans — too many unique values for metric tags).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Timed uses AOP to wrap method with Timer; Observation API feeds both MeterRegistry (metrics) and Tracer (spans)">
  <!-- @Timed path -->
  <rect x="10" y="35" width="145" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="82" y="57" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Timed</text>
  <text x="82" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AOP proxy wraps</text>
  <text x="82" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">method call</text>

  <line x1="158" y1="65" x2="225" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#toa)"/>

  <rect x="230" y="40" width="120" height="50" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="290" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">MeterRegistry</text>
  <text x="290" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Timer only</text>

  <!-- Observation path -->
  <rect x="10" y="120" width="145" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="82" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Observation API</text>
  <text x="82" y="156" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Observation.observe()</text>
  <text x="82" y="169" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ObservationRegistry</text>

  <line x1="158" y1="148" x2="225" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#tob)"/>
  <line x1="158" y1="148" x2="225" y2="165" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#tob)"/>

  <!-- MeterRegistry -->
  <rect x="230" y="105" width="120" height="40" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="290" y="122" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">MeterRegistry</text>
  <text x="290" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Timer metric</text>

  <!-- Tracer -->
  <rect x="230" y="150" width="120" height="40" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="290" y="167" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Tracer</text>
  <text x="290" y="181" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Span (trace)</text>

  <!-- Outputs -->
  <line x1="353" y1="65" x2="420" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#toa)"/>
  <rect x="425" y="48" width="250" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="550" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">/actuator/metrics/orders.create</text>

  <line x1="353" y1="125" x2="420" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#tob)"/>
  <rect x="425" y="82" width="250" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="550" y="104" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">/actuator/metrics/orders.create</text>

  <line x1="353" y1="170" x2="420" y2="152" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#tob)"/>
  <rect x="425" y="134" width="250" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="550" y="156" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Trace span → Zipkin/Jaeger/OTLP</text>

  <defs>
    <marker id="toa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="tob" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`@Timed` produces a metric only; `Observation` produces both a metric and a trace span from one instrumentation point.

## 5. Runnable example

```java
// TimedObservationDemo.java — demonstrates @Timed semantics and Observation API lifecycle
// How to run: java TimedObservationDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: @Timed requires TimedAspect @Bean; ObservationRegistry is auto-configured

import java.util.*;
import java.util.concurrent.Callable;

public class TimedObservationDemo {

    // Simulate timer: stores (name, durationMs, tags)
    record TimerSample(String name, long ms, Map<String,String> tags) {}
    // Simulate trace span
    record Span(String name, long ms, Map<String,String> highCardTags) {}

    static final List<TimerSample> metrics = new ArrayList<>();
    static final List<Span>        spans   = new ArrayList<>();

    // --- @Timed simulation (AOP proxy wraps the method) ---
    static <T> T timed(String timerName, Map<String,String> tags, Callable<T> method) throws Exception {
        long start = System.currentTimeMillis();
        try {
            T result = method.call();
            long ms = System.currentTimeMillis() - start;
            metrics.add(new TimerSample(timerName, ms, Map.copyOf(tags)));
            System.out.printf("[@Timed] %s  tags=%s  duration=%dms%n", timerName, tags, ms);
            return result;
        } catch (Exception e) {
            long ms = System.currentTimeMillis() - start;
            Map<String,String> errTags = new HashMap<>(tags);
            errTags.put("exception", e.getClass().getSimpleName());
            metrics.add(new TimerSample(timerName, ms, errTags));
            throw e;
        }
    }

    // --- Observation API simulation ---
    static <T> T observe(String name, Map<String,String> lowCard, Map<String,String> highCard,
                          Callable<T> block) throws Exception {
        long start = System.currentTimeMillis();
        T result = block.call();
        long ms = System.currentTimeMillis() - start;
        // Metrics: use LOW cardinality tags only
        metrics.add(new TimerSample(name, ms, Map.copyOf(lowCard)));
        // Trace span: use HIGH cardinality tags (unique per request)
        Map<String,String> spanTags = new HashMap<>(lowCard);
        spanTags.putAll(highCard);
        spans.add(new Span(name, ms, Map.copyOf(spanTags)));
        System.out.printf("[Observation] metric: %s tags=%s duration=%dms%n", name, lowCard, ms);
        System.out.printf("              span:   %s tags=%s duration=%dms%n", name, spanTags, ms);
        return result;
    }

    // Simulated business methods
    static String createOrderTimed(String channel) throws Exception {
        return timed("orders.create",
                Map.of("channel", channel),
                () -> { Thread.sleep(20); return "ORDER-123"; });
    }

    static String createOrderObserved(String orderId, String channel) throws Exception {
        return observe("orders.create",
                Map.of("channel", channel),         // low cardinality → metrics
                Map.of("order.id", orderId),        // high cardinality → trace only
                () -> { Thread.sleep(20); return orderId; });
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== @Timed / Observation API Demo ===\n");

        System.out.println("--- @Timed (metrics only) ---");
        createOrderTimed("web");
        createOrderTimed("mobile");

        System.out.println("\n--- Observation API (metrics + traces) ---");
        createOrderObserved("ORDER-001", "web");
        createOrderObserved("ORDER-002", "mobile");

        System.out.println("\n--- Collected metrics (" + metrics.size() + " samples) ---");
        metrics.forEach(m -> System.out.printf("  metric: %s[%s] = %dms%n", m.name(), m.tags(), m.ms()));

        System.out.println("\n--- Collected spans (" + spans.size() + " spans) ---");
        spans.forEach(s -> System.out.printf("  span:   %s  tags=%s  duration=%dms%n",
                s.name(), s.highCardTags(), s.ms()));

        System.out.println("\n--- Key difference ---");
        System.out.println("order.id is HIGH cardinality → in span but NOT in metric tag");
        System.out.println("Keeps metric cardinality bounded while trace has full context");
    }
}
```

**How to run:** `java TimedObservationDemo.java`

## 6. Walkthrough

- **`timed()`** simulates `TimedAspect`: wraps the method call, records duration, adds `exception` tag on failure. In Spring Boot, `@Timed` on a method does this automatically when `TimedAspect` is a bean.
- **`observe()`** demonstrates the key Observation API distinction: low-cardinality tags (small fixed set like `channel=web`) go to **metrics**; high-cardinality tags (unique per call like `order.id=ORDER-001`) go only to the **trace span**. This prevents metric explosion.
- The output shows two metrics samples (one from `@Timed`, one from `Observation`) and two spans (only from `Observation`).
- `order.id` appears in `spanTags` (trace) but not in `lowCard` (metrics) — this is the fundamental Observation API safety contract.

## 7. Gotchas & takeaways

> `@Timed` **requires `TimedAspect` as a `@Bean`** — it's not auto-configured. Without it, the annotation is silently ignored, no timer is recorded, no error is thrown.

> `Observation.lowCardinalityKeyValue` vs `highCardinalityKeyValue`: low-cardinality values (method, status, channel) go into metric tags; high-cardinality (user IDs, order IDs, trace IDs) go only into spans. Using high-cardinality values as metric tags explodes series cardinality.

- Spring Boot 3 auto-configures `ObservationRegistry`; inject it directly.
- `@Observed` (from `micrometer-observation-annotation`) is the annotation equivalent of the `Observation API` — requires `ObservedAspect @Bean`.
- `ObservationTextPublisher` logs observations to SLF4J — useful for debugging without a tracing back-end.
- HTTP client and server instrumentation in Spring Boot 3 already uses Observations — your custom business logic should too for consistent trace context propagation.
- `Observation.createNotStarted(...).start()` gives you explicit control; `.observe(Callable)` is the shortcut.
