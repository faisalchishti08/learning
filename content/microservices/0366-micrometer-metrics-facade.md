---
card: microservices
gi: 366
slug: micrometer-metrics-facade
title: "Micrometer metrics facade"
---

## 1. What it is

**Micrometer** is a vendor-neutral metrics facade for Java (built into Spring Boot) — application code records metrics (counters, gauges, timers) against Micrometer's own API, and a separately configured **registry** determines where those metrics actually get sent (Prometheus, Datadog, CloudWatch, and others). This is the same design idea as SLF4J for logging: write against one stable API, and swap the underlying implementation without touching application code.

## 2. Why & when

If application code recorded metrics directly against a specific vendor's client library (say, Prometheus's client directly), switching monitoring backends later — or, more commonly, supporting multiple backends across different environments or during a migration — would mean rewriting every metric-recording call site throughout the codebase. Micrometer exists precisely to prevent this: application code depends only on Micrometer's stable `MeterRegistry` API, and the actual destination is determined by which registry implementation is configured and wired in, entirely separately from the metric-recording code itself.

Use Micrometer as the default way to record any custom application metric in a Spring Boot service — this is what [Spring Boot Actuator's `/metrics` endpoint](0365-spring-boot-actuator-endpoints-health-info-metrics-env-etc.md) is built on, and what feeds whatever registry (see [Micrometer registries](0367-micrometer-registries-prometheus-datadog-etc.md)) your monitoring backend requires. Writing metric-recording code directly against a specific vendor's library, bypassing Micrometer, defeats this portability and should be avoided unless that vendor's library offers something Micrometer genuinely cannot express.

## 3. Core concept

Application code obtains a `MeterRegistry` (injected by Spring) and uses it to create and update meters — `registry.counter("orders.placed").increment()`, `registry.timer("checkout.duration").record(...)` — entirely independent of what backend that registry is actually configured to export to. Swapping backends means changing configuration (which registry implementation is on the classpath and configured), not changing any of these call sites.

```java
@Component
class OrderMetrics {
    private final Counter ordersPlaced;
    OrderMetrics(MeterRegistry registry) { this.ordersPlaced = registry.counter("orders.placed"); }
    void recordOrderPlaced() { ordersPlaced.increment(); } // works identically regardless of the backend
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls the same Micrometer MeterRegistry API; depending on configuration, the SAME call exports to Prometheus in one environment and Datadog in another, with no code change">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Application: MeterRegistry API</text>

  <line x1="280" y1="49" x2="140" y2="90" stroke="#8b949e" marker-end="url(#a366)"/>
  <rect x="20" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Prometheus registry (env A)</text>

  <line x1="360" y1="49" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a366)"/>
  <rect x="380" y="90" width="240" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Datadog registry (env B)</text>

  <text x="320" y="150" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">SAME application code, DIFFERENT backend, based purely on configuration.</text>

  <defs><marker id="a366" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Application code records metrics against one stable facade API; the configured registry determines the actual backend destination.

## 5. Runnable example

Scenario: an order-counting metric, first recorded directly against a simulated vendor-specific client (tightly coupled), then rebuilt against a facade interface matching Micrometer's model, and finally shown running unchanged against two different simulated registries, demonstrating true backend portability.

### Level 1 — Basic

```java
// File: DirectVendorClientCoupling.java -- application code calls a
// SPECIFIC vendor's client library directly; switching backends means
// rewriting every call site.
import java.util.*;

public class DirectVendorClientCoupling {
    // Simulates a SPECIFIC vendor's client API, e.g. Prometheus's own client library.
    static class PrometheusSpecificClient {
        Map<String, Integer> counters = new HashMap<>();
        void incrementPrometheusCounter(String name) { counters.merge(name, 1, Integer::sum); } // Prometheus-SPECIFIC method name/shape
    }

    static PrometheusSpecificClient prometheusClient = new PrometheusSpecificClient();

    static void recordOrderPlaced() {
        prometheusClient.incrementPrometheusCounter("orders_placed"); // TIED to this ONE vendor's API directly
    }

    public static void main(String[] args) {
        recordOrderPlaced();
        recordOrderPlaced();
        System.out.println("Prometheus counters: " + prometheusClient.counters);
        System.out.println("To switch to a DIFFERENT vendor, EVERY call site using 'prometheusClient' directly would need rewriting.");
    }
}
```

How to run: `java DirectVendorClientCoupling.java`

`recordOrderPlaced` calls `prometheusClient.incrementPrometheusCounter` directly — a method name and API shape specific to this one simulated vendor's client. If the team later needed to switch to a different backend, every call site coupled this tightly to `PrometheusSpecificClient` would need to be found and rewritten.

### Level 2 — Intermediate

```java
// File: FacadeBasedRecording.java -- application code depends ONLY on a
// stable FACADE interface (mirroring Micrometer's MeterRegistry); the
// actual backend implementation is injected separately.
import java.util.*;

public class FacadeBasedRecording {
    interface MeterRegistry { void incrementCounter(String name); } // the STABLE facade -- mirrors Micrometer's own API

    static class OrderMetrics {
        private final MeterRegistry registry; // depends ONLY on the facade, never a specific vendor
        OrderMetrics(MeterRegistry registry) { this.registry = registry; }
        void recordOrderPlaced() { registry.incrementCounter("orders.placed"); }
    }

    // ONE concrete implementation -- could be swapped for a different one with NO change above.
    static class InMemoryRegistry implements MeterRegistry {
        Map<String, Integer> counters = new HashMap<>();
        public void incrementCounter(String name) { counters.merge(name, 1, Integer::sum); }
    }

    public static void main(String[] args) {
        InMemoryRegistry registry = new InMemoryRegistry();
        OrderMetrics metrics = new OrderMetrics(registry); // registry INJECTED, not hardcoded inside OrderMetrics

        metrics.recordOrderPlaced();
        metrics.recordOrderPlaced();

        System.out.println("Counters: " + registry.counters);
        System.out.println("OrderMetrics.recordOrderPlaced() NEVER mentions a specific vendor -- only the facade interface.");
    }
}
```

How to run: `java FacadeBasedRecording.java`

`OrderMetrics` depends only on the `MeterRegistry` interface, never on `InMemoryRegistry` specifically — `InMemoryRegistry` is just one implementation, injected in via the constructor. `recordOrderPlaced`'s code would work completely unchanged if a different `MeterRegistry` implementation were substituted, exactly mirroring how real Micrometer-based application code never mentions Prometheus, Datadog, or any other specific vendor by name.

### Level 3 — Advanced

```java
// File: SameCodeTwoRegistries.java -- the IDENTICAL OrderMetrics class
// runs unchanged against TWO DIFFERENT simulated registry implementations
// (Prometheus-like and Datadog-like), proving true backend portability.
import java.util.*;

public class SameCodeTwoRegistries {
    interface MeterRegistry { void incrementCounter(String name); }

    static class OrderMetrics { // the ONE piece of application code -- completely vendor-agnostic
        private final MeterRegistry registry;
        OrderMetrics(MeterRegistry registry) { this.registry = registry; }
        void recordOrderPlaced() { registry.incrementCounter("orders.placed"); }
    }

    static class PrometheusStyleRegistry implements MeterRegistry {
        Map<String, Integer> counters = new HashMap<>();
        public void incrementCounter(String name) {
            counters.merge(name, 1, Integer::sum);
            System.out.println("  [Prometheus-style registry] internally stores as a scrapeable time series");
        }
    }

    static class DatadogStyleRegistry implements MeterRegistry {
        List<String> submittedMetrics = new ArrayList<>();
        public void incrementCounter(String name) {
            submittedMetrics.add(name + "+1");
            System.out.println("  [Datadog-style registry] internally PUSHES the metric to a remote API");
        }
    }

    public static void main(String[] args) {
        System.out.println("--- Environment A: configured with Prometheus-style registry ---");
        MeterRegistry prometheusRegistry = new PrometheusStyleRegistry();
        OrderMetrics metricsA = new OrderMetrics(prometheusRegistry); // SAME OrderMetrics class
        metricsA.recordOrderPlaced();

        System.out.println("--- Environment B: configured with Datadog-style registry ---");
        MeterRegistry datadogRegistry = new DatadogStyleRegistry();
        OrderMetrics metricsB = new OrderMetrics(datadogRegistry); // SAME OrderMetrics class, DIFFERENT registry
        metricsB.recordOrderPlaced();

        System.out.println("OrderMetrics.recordOrderPlaced() is IDENTICAL code in both environments -- only the injected registry differs.");
    }
}
```

How to run: `java SameCodeTwoRegistries.java`

`OrderMetrics` is defined exactly once, with no reference to either `PrometheusStyleRegistry` or `DatadogStyleRegistry` anywhere in its own code. `metricsA` is constructed with a `PrometheusStyleRegistry`, and calling `recordOrderPlaced` on it triggers that registry's internal, scrape-oriented behavior; `metricsB` is constructed with a `DatadogStyleRegistry`, and calling the identical method on it triggers that registry's internal, push-oriented behavior instead. The application-level metric-recording logic never changed at all — only the injected registry implementation did, exactly the portability Micrometer's real facade design provides.

## 6. Walkthrough

Trace `SameCodeTwoRegistries.main` in order. **First**, `prometheusRegistry` is created as a `PrometheusStyleRegistry`, and `metricsA` is constructed by injecting it into a new `OrderMetrics` instance. Calling `metricsA.recordOrderPlaced()` invokes `registry.incrementCounter("orders.placed")` — since `registry` here refers to the injected `PrometheusStyleRegistry`, its `incrementCounter` implementation runs: it updates `counters` via `merge` and prints a message describing its Prometheus-style, scrape-based internal behavior.

**Next**, `datadogRegistry` is created as a `DatadogStyleRegistry`, and `metricsB` is constructed by injecting *this* registry into a *separate* new `OrderMetrics` instance. Calling `metricsB.recordOrderPlaced()` invokes the exact same line of code inside `OrderMetrics` — `registry.incrementCounter("orders.placed")` — but this time `registry` refers to the `DatadogStyleRegistry` instance, so its `incrementCounter` implementation runs instead: it appends to `submittedMetrics` and prints a message describing its Datadog-style, push-based internal behavior.

**Both calls execute the identical source line** inside `OrderMetrics.recordOrderPlaced()` — the only thing that differed between the two invocations was which concrete `MeterRegistry` object had been injected at construction time, not any change to `OrderMetrics`'s own code.

**Finally**, `main` prints a closing observation confirming exactly this: the application-level metric-recording method is byte-for-byte identical in both environments, and only the registry configuration determines whether the metric ultimately becomes a Prometheus-scrapeable time series or a Datadog API push.

```
metricsA = new OrderMetrics(PrometheusStyleRegistry)  -> recordOrderPlaced() -> Prometheus-style storage
metricsB = new OrderMetrics(DatadogStyleRegistry)     -> recordOrderPlaced() -> Datadog-style push
SAME OrderMetrics.recordOrderPlaced() code in both cases -- only the injected registry differs.
```

## 7. Gotchas & takeaways

> Recording a metric directly against a specific vendor's client library anywhere in application code — even just once, for "a quick fix" — reintroduces the exact coupling Micrometer exists to prevent, and that one call site becomes a hidden obstacle the next time the team needs to switch or add a monitoring backend. Route every metric through Micrometer's `MeterRegistry`, with no exceptions.

- Micrometer is a vendor-neutral facade: application code records metrics against its stable `MeterRegistry` API, and the configured registry implementation determines the actual backend destination.
- This mirrors SLF4J's role for logging — write against one API, swap the implementation via configuration, without touching call sites.
- Spring Boot wires Micrometer in automatically, and it's what [Actuator's `/metrics` endpoint](0365-spring-boot-actuator-endpoints-health-info-metrics-env-etc.md) is built on.
- [Micrometer registries](0367-micrometer-registries-prometheus-datadog-etc.md) (Prometheus, Datadog, and others) are the concrete implementations that determine where recorded metrics actually end up, entirely independent of the application code that records them.
