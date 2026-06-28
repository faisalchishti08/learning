---
card: spring-boot
gi: 189
slug: custom-healthindicator
title: Custom HealthIndicator
---

## 1. What it is

A **custom `HealthIndicator`** is a Spring bean you write to add application-specific health checks to `/actuator/health`. Implement the `HealthIndicator` interface (or `ReactiveHealthIndicator` for WebFlux), override `health()`, and return a `Health` object. Spring Boot auto-detects it, names it from the class name (strips the `HealthIndicator` suffix), and includes it in the aggregated health response.

## 2. Why & when

Auto-configured indicators cover infrastructure (DB, Redis, Kafka). Custom indicators cover **application-specific dependencies** that Spring doesn't know about:
- A downstream REST API your service calls.
- A third-party payment or email provider SDK.
- A license or quota check (e.g., "API rate limit is not exhausted").
- A custom connection pool or resource handle.

Write a custom indicator whenever you want a failing external dependency to surface in the health endpoint automatically.

## 3. Core concept

```java
@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {

    private final PaymentClient client;

    public PaymentGatewayHealthIndicator(PaymentClient client) {
        this.client = client;
    }

    @Override
    public Health health() {
        try {
            long start = System.currentTimeMillis();
            boolean ok = client.ping();
            long ms = System.currentTimeMillis() - start;

            return ok
                ? Health.up().withDetail("responseTimeMs", ms).build()
                : Health.down().withDetail("reason", "ping returned false").build();

        } catch (Exception ex) {
            return Health.down(ex).build();  // includes exception message in details
        }
    }
}
```

`Health` builder methods:
- `Health.up()` — status `UP`.
- `Health.down()` — status `DOWN`.
- `Health.down(exception)` — status `DOWN` + exception message in details.
- `Health.outOfService()` — status `OUT_OF_SERVICE` (maintenance, not a failure).
- `Health.unknown()` — status `UNKNOWN` (check inconclusive).
- `.withDetail(key, value)` — add a detail entry.
- `.withDetails(map)` — add multiple detail entries.
- `.build()` — create the `Health` object.

The component name in the JSON response: `PaymentGatewayHealthIndicator` → `paymentGateway`.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom HealthIndicator bean checks external API and returns Health object; aggregator includes it in /actuator/health">
  <!-- Bean -->
  <rect x="10" y="55" width="240" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="78" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Component</text>
  <text x="130" y="94" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PaymentGatewayHealthIndicator</text>
  <text x="130" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements HealthIndicator</text>
  <text x="130" y="128" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Health health() {</text>
  <text x="130" y="142" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  client.ping() → UP/DOWN</text>

  <!-- Arrow to external dep -->
  <line x1="253" y1="105" x2="328" y2="90" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#chia)"/>
  <rect x="332" y="60" width="130" height="60" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="397" y="85" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Payment API</text>
  <text x="397" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">external dependency</text>

  <!-- Arrow to aggregator -->
  <line x1="253" y1="118" x2="490" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#chib)"/>
  <text x="375" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Health.up() / Health.down()</text>

  <!-- Aggregator -->
  <rect x="495" y="65" width="175" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="582" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator/health</text>
  <text x="582" y="103" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">paymentGateway: UP</text>
  <text x="582" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  responseTimeMs: 42</text>
  <text x="582" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(auto-included)</text>

  <defs>
    <marker id="chia" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="chib" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The bean is auto-detected; `health()` is called on each GET of `/actuator/health`, and the result appears under `components.paymentGateway`.

## 5. Runnable example

```java
// CustomHealthIndicatorDemo.java — full custom HealthIndicator implementation
// How to run: java CustomHealthIndicatorDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: @Component class implementing HealthIndicator auto-appears in /actuator/health

import java.util.*;

public class CustomHealthIndicatorDemo {

    // Mirrors Spring's Health class
    record Health(String status, Map<String, Object> details) {
        static Builder status(String s) { return new Builder(s); }
        static Builder up()           { return new Builder("UP"); }
        static Builder down()         { return new Builder("DOWN"); }
        static Builder outOfService() { return new Builder("OUT_OF_SERVICE"); }
        static Builder unknown()      { return new Builder("UNKNOWN"); }
        static Health down(Exception e) {
            return new Health("DOWN", Map.of("error", e.getMessage()));
        }

        static class Builder {
            final String status;
            final Map<String, Object> details = new LinkedHashMap<>();
            Builder(String s) { this.status = s; }
            Builder withDetail(String k, Object v) { details.put(k, v); return this; }
            Health build() { return new Health(status, Map.copyOf(details)); }
        }
    }

    // === Custom HealthIndicator 1: external HTTP API ===
    static Health paymentGatewayHealth(boolean reachable, long responseMs) {
        if (!reachable) return Health.down().withDetail("error", "connection refused").build();
        if (responseMs > 5000) return Health.unknown().withDetail("responseMs", responseMs).build();
        return Health.up().withDetail("responseMs", responseMs).build();
    }

    // === Custom HealthIndicator 2: license check ===
    static Health licenseHealth(int usedSeats, int maxSeats) {
        int pct = usedSeats * 100 / maxSeats;
        Health.Builder b = pct < 90 ? Health.up() : pct < 100 ? Health.unknown() : Health.outOfService();
        return b.withDetail("usedSeats", usedSeats)
                .withDetail("maxSeats", maxSeats)
                .withDetail("usagePercent", pct)
                .build();
    }

    // === Custom HealthIndicator 3: downstream queue depth ===
    static Health queueHealth(int depth, int maxDepth) {
        return depth < maxDepth
            ? Health.up().withDetail("queueDepth", depth).build()
            : Health.down().withDetail("queueDepth", depth)
                           .withDetail("maxDepth", maxDepth)
                           .withDetail("reason", "queue full — consumers lagging").build();
    }

    static void printHealth(String component, Health h) {
        System.out.printf("  %-20s status=%-12s details=%s%n", component, h.status(), h.details());
    }

    public static void main(String[] args) {
        System.out.println("=== Custom HealthIndicator Demo ===\n");

        // Scenario 1: all healthy
        System.out.println("--- Scenario 1: Healthy system ---");
        printHealth("paymentGateway", paymentGatewayHealth(true, 42));
        printHealth("license",        licenseHealth(80, 100));
        printHealth("orderQueue",     queueHealth(150, 1000));

        // Scenario 2: payment gateway down
        System.out.println("\n--- Scenario 2: Payment gateway unreachable ---");
        printHealth("paymentGateway", paymentGatewayHealth(false, -1));
        printHealth("license",        licenseHealth(80, 100));
        printHealth("orderQueue",     queueHealth(150, 1000));

        // Scenario 3: license approaching limit
        System.out.println("\n--- Scenario 3: License at 95%, queue backing up ---");
        printHealth("paymentGateway", paymentGatewayHealth(true, 150));
        printHealth("license",        licenseHealth(95, 100));
        printHealth("orderQueue",     queueHealth(1000, 1000));

        // Scenario 4: exception during health check
        System.out.println("\n--- Scenario 4: Health check throws ---");
        try {
            throw new RuntimeException("NullPointerException in payment client");
        } catch (Exception e) {
            printHealth("paymentGateway", Health.down(e));
        }

        System.out.println("\n--- Class naming convention ---");
        System.out.println("PaymentGatewayHealthIndicator → component name: 'paymentGateway'");
        System.out.println("LicenseHealthIndicator        → component name: 'license'");
        System.out.println("OrderQueueHealthIndicator     → component name: 'orderQueue'");
    }
}
```

**How to run:** `java CustomHealthIndicatorDemo.java`

## 6. Walkthrough

- **`paymentGatewayHealth`**: three states: DOWN (unreachable), UNKNOWN (too slow), UP (fast response). The response-time detail is visible to ops in the health response when `show-details=always`.
- **`licenseHealth`**: uses `outOfService()` for 100% seat usage — this signals "stop sending traffic" without implying a failure that needs restarting.
- **`queueHealth`**: a full queue means consumers are lagging. `down()` with a descriptive `reason` detail makes the alert actionable.
- **Exception scenario**: `Health.down(exception)` captures the exception message automatically — avoids losing the root cause in the health detail.
- **Naming**: Spring strips the `HealthIndicator` suffix from the class name and camelCases the remainder. `OrderQueueHealthIndicator` → `orderQueue`. No configuration needed.

## 7. Gotchas & takeaways

> Every call to `GET /actuator/health` runs **all `health()` methods synchronously**. If your payment gateway has a 30-second timeout, the health endpoint will take 30 seconds to respond. Always set short timeouts (< 2 s) inside health checks and return `UNKNOWN` on timeout.

> `Health.down(exception)` includes the **exception message and stack trace in the details** — visible to anyone who can see health details. Sanitise sensitive messages in the catch block before adding them.

- For WebFlux: implement `ReactiveHealthIndicator` returning `Mono<Health>` — Spring calls `health()` non-blockingly.
- `CompositeHealthContributor.fromMap(...)` groups multiple related checks under one component with sub-indicators.
- `@ConditionalOnProperty("myapp.payments.health.enabled")` on the `@Component` lets ops disable a slow health check without redeploying.
- Test: inject a mock `PaymentClient`, call `indicator.health()`, assert the `status` and detail values — no Spring context needed.
