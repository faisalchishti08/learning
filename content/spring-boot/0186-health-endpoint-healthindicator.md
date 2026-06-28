---
card: spring-boot
gi: 186
slug: health-endpoint-healthindicator
title: Health endpoint & HealthIndicator
---

## 1. What it is

The **`/actuator/health`** endpoint reports whether the application and its dependencies are healthy. It aggregates the results of all registered `HealthIndicator` beans — each checks one sub-system (database, Redis, disk space, message broker) and reports `UP`, `DOWN`, `OUT_OF_SERVICE`, or `UNKNOWN`. The overall status is the worst status across all indicators.

You write custom `HealthIndicator` beans to add checks for dependencies Spring doesn't know about.

## 2. Why & when

`/actuator/health` is the single most important Actuator endpoint:
- **Kubernetes liveness probe**: `kubelet` calls it; if it returns non-2xx, the pod is restarted.
- **Kubernetes readiness probe**: return `OUT_OF_SERVICE` during startup or maintenance to stop traffic without restarting.
- **Load balancer health check**: remove a node from rotation if health degrades.

Custom `HealthIndicator`s are useful for:
- External APIs your service depends on (payment gateway, email provider).
- Custom connection pools or queues.
- License checks, feature dependencies.

## 3. Core concept

Implementing a custom `HealthIndicator`:

```java
@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        try {
            boolean ok = paymentClient.ping();   // your check
            return ok
                ? Health.up().withDetail("responseTimeMs", 12).build()
                : Health.down().withDetail("reason", "no response").build();
        } catch (Exception e) {
            return Health.down(e).build();  // includes exception message
        }
    }
}
```

Spring Boot auto-detects any bean implementing `HealthIndicator`. The bean name (minus the `HealthIndicator` suffix) becomes the component name in the JSON response.

Status aggregation order (worst wins): `DOWN` > `OUT_OF_SERVICE` > `UNKNOWN` > `UP`.

Properties:
- `management.endpoint.health.show-details=always|when-authorized|never` — controls whether component details appear.
- `management.endpoint.health.show-components=always` — show component names without their details.

**Reactive variant:** implement `ReactiveHealthIndicator` returning `Mono<Health>` for WebFlux apps.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GET /actuator/health aggregates results from multiple HealthIndicator beans and returns overall status">
  <!-- Multiple indicators -->
  <rect x="10" y="30" width="155" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="87" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DiskSpaceHealthIndicator</text>

  <rect x="10" y="68" width="155" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="87" y="88" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DataSourceHealthIndicator</text>

  <rect x="10" y="106" width="155" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="87" y="126" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">RedisHealthIndicator</text>

  <rect x="10" y="144" width="155" height="32" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="87" y="164" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PaymentGatewayIndicator (custom)</text>

  <!-- Arrows to aggregator -->
  <line x1="168" y1="46" x2="255" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hia)"/>
  <line x1="168" y1="84" x2="255" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hia)"/>
  <line x1="168" y1="122" x2="255" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hia)"/>
  <line x1="168" y1="160" x2="255" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hib)"/>

  <!-- Aggregator -->
  <rect x="260" y="72" width="155" height="62" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="337" y="96" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Aggregation</text>
  <text x="337" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">worst status wins</text>
  <text x="337" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DOWN &gt; OUT_OF_SVC &gt; UP</text>

  <!-- Arrow to response -->
  <line x1="418" y1="103" x2="480" y2="103" stroke="#6db33f" stroke-width="2" marker-end="url(#hia)"/>

  <!-- Response box -->
  <rect x="485" y="45" width="200" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">GET /actuator/health</text>
  <text x="485" y="83" fill="#6db33f" font-size="8" font-family="monospace">  status: "UP"</text>
  <text x="485" y="97" fill="#6db33f" font-size="8" font-family="monospace">  components:</text>
  <text x="485" y="111" fill="#6db33f" font-size="8" font-family="monospace">    db: UP</text>
  <text x="485" y="125" fill="#6db33f" font-size="8" font-family="monospace">    diskSpace: UP</text>
  <text x="485" y="139" fill="#6db33f" font-size="8" font-family="monospace">    redis: UP</text>
  <text x="485" y="153" fill="#79c0ff" font-size="8" font-family="monospace">    paymentGateway: UP</text>

  <defs>
    <marker id="hia" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="hib" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each `HealthIndicator` bean contributes one component; the worst status across all components becomes the top-level status.

## 5. Runnable example

```java
// HealthIndicatorDemo.java — builds and aggregates custom HealthIndicators
// How to run: java HealthIndicatorDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: implement HealthIndicator, mark @Component — Spring auto-detects it

import java.util.*;

public class HealthIndicatorDemo {

    // Mirrors Spring's Health object
    record Health(String status, Map<String, Object> details) {
        static Health up(Map<String, Object> d)   { return new Health("UP",              d); }
        static Health down(Map<String, Object> d)  { return new Health("DOWN",            d); }
        static Health unknown(Map<String, Object> d){ return new Health("UNKNOWN",         d); }
        static Health outOfService()               { return new Health("OUT_OF_SERVICE", Map.of()); }
    }

    // Simulated HealthIndicator implementations
    interface HealthIndicator { Health health(); }

    static HealthIndicator diskSpace(long freeBytes) {
        return () -> freeBytes > 10_000_000L
            ? Health.up(Map.of("free", freeBytes, "threshold", 10_000_000))
            : Health.down(Map.of("free", freeBytes, "threshold", 10_000_000));
    }

    static HealthIndicator database(boolean canQuery) {
        return () -> canQuery
            ? Health.up(Map.of("database", "PostgreSQL", "validationQuery", "isValid()"))
            : Health.down(Map.of("error", "Connection refused"));
    }

    static HealthIndicator paymentGateway(int responseMs) {
        return () -> {
            if (responseMs < 0)  return Health.down(Map.of("error", "timeout"));
            if (responseMs > 5000) return new Health("UNKNOWN", Map.of("responseMs", responseMs));
            return Health.up(Map.of("responseMs", responseMs));
        };
    }

    // Aggregation: worst status wins
    static final List<String> STATUS_ORDER = List.of("DOWN", "OUT_OF_SERVICE", "UNKNOWN", "UP");
    static int severity(String status) { return STATUS_ORDER.size() - 1 - STATUS_ORDER.indexOf(status); }

    static Map<String, Object> aggregate(Map<String, HealthIndicator> indicators) {
        Map<String, Object> components = new LinkedHashMap<>();
        String overall = "UP";
        for (var entry : indicators.entrySet()) {
            Health h = entry.getValue().health();
            components.put(entry.getKey(), Map.of("status", h.status(), "details", h.details()));
            if (severity(h.status()) > severity(overall)) overall = h.status();
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", overall);
        result.put("components", components);
        return result;
    }

    public static void main(String[] args) {
        System.out.println("=== Health Endpoint & HealthIndicator Demo ===\n");

        // Scenario 1: all healthy
        System.out.println("--- Scenario 1: All healthy ---");
        var h1 = aggregate(new LinkedHashMap<>(Map.of(
            "diskSpace",      diskSpace(5_000_000_000L),
            "db",             database(true),
            "paymentGateway", paymentGateway(42)
        )));
        h1.forEach((k, v) -> System.out.println(k + ": " + v));

        // Scenario 2: DB down
        System.out.println("\n--- Scenario 2: Database DOWN ---");
        var h2 = aggregate(new LinkedHashMap<>(Map.of(
            "diskSpace",      diskSpace(5_000_000_000L),
            "db",             database(false),
            "paymentGateway", paymentGateway(42)
        )));
        h2.forEach((k, v) -> System.out.println(k + ": " + v));

        // Scenario 3: payment gateway slow (UNKNOWN)
        System.out.println("\n--- Scenario 3: Payment gateway UNKNOWN ---");
        var h3 = aggregate(new LinkedHashMap<>(Map.of(
            "diskSpace",      diskSpace(5_000_000_000L),
            "db",             database(true),
            "paymentGateway", paymentGateway(6000)
        )));
        h3.forEach((k, v) -> System.out.println(k + ": " + v));
    }
}
```

**How to run:** `java HealthIndicatorDemo.java`

## 6. Walkthrough

- **`diskSpace`**: checks available bytes against a threshold. Real `DiskSpaceHealthIndicator` reads the OS filesystem.
- **`database`**: simulates a JDBC `connection.isValid()` call. Real `DataSourceHealthIndicator` executes a validation query.
- **`paymentGateway`**: custom indicator — negative response → DOWN, very slow → UNKNOWN, fast → UP. In Spring Boot this bean would be named `PaymentGatewayHealthIndicator`; the component appears as `paymentGateway`.
- **`aggregate`**: iterates all indicators, collects statuses, applies the severity ordering — `DOWN` (severity 3) beats `UNKNOWN` (2) beats `UP` (0). The worst status becomes the overall.
- **Scenario 2**: `db=DOWN` makes overall `DOWN` — Kubernetes liveness probe gets a 503, triggers pod restart.
- **Scenario 3**: `paymentGateway=UNKNOWN` makes overall `UNKNOWN` — an ambiguous state; your `StatusAggregator` can map `UNKNOWN` to any HTTP status you choose.

## 7. Gotchas & takeaways

> `show-details=never` (the default) only returns `{"status":"UP"}` — no component details. Kubernetes probes need only the status; the details are for human operators. Enable them with `show-details=when-authorized`.

> A slow `HealthIndicator` (e.g., waiting 30 seconds for a timeout) **blocks the health endpoint response**. Set a timeout on your health checks and return `UNKNOWN` on timeout rather than hanging.

- `management.health.<id>.enabled=false` disables a specific built-in indicator (e.g., `management.health.redis.enabled=false` when Redis is optional).
- Implement `HealthContributor` (composite) for indicators that report multiple sub-checks under one name.
- `management.endpoint.health.probes.enabled=true` enables `/actuator/health/liveness` and `/actuator/health/readiness` — these are the Kubernetes probe paths.
- Spring Boot 2.3+: a `DOWN` liveness = pod restart; a `DOWN` readiness = pod removed from service without restart.
- Return `Health.down(exception).build()` to include the exception message in details — visible to ops when `show-details=always`.
