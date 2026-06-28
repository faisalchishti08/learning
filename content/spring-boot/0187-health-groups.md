---
card: spring-boot
gi: 187
slug: health-groups
title: Health groups
---

## 1. What it is

**Health groups** let you partition `HealthIndicator`s into named subsets, each accessible at `/actuator/health/<group-name>`. The most common built-in groups are `liveness` and `readiness` (enabled via `management.endpoint.health.probes.enabled=true`), used as Kubernetes probes. You can also define custom groups to target specific sub-systems for different monitoring tools.

## 2. Why & when

A single `/actuator/health` aggregates everything. That's too coarse when:
- **Kubernetes liveness** should only check JVM state (is the app alive?) — not whether an external Redis is up. A Redis outage should not cause a pod restart.
- **Kubernetes readiness** should check external dependencies — if the DB is down, stop routing traffic but don't restart.
- **Team-specific checks**: the payments team wants `/actuator/health/payments` that only includes payment-related indicators, separate from infrastructure health.

## 3. Core concept

Define groups in `application.properties`:

```properties
management.endpoint.health.group.liveness.include=ping,livenessState
management.endpoint.health.group.readiness.include=readinessState,db,redis
management.endpoint.health.group.payments.include=paymentGateway,fxRates
management.endpoint.health.group.payments.show-details=always
```

Each group:
- Has an `include` (or `exclude`) list of `HealthIndicator` IDs.
- Can override `show-details` and `show-components` independently.
- Can set a custom `status.http-mapping` (e.g., map `OUT_OF_SERVICE` → 503 for the readiness group).

Built-in groups (auto-created when `management.endpoint.health.probes.enabled=true`):
- `liveness` → `/actuator/health/liveness` → includes `livenessState` (managed by `ApplicationAvailability`).
- `readiness` → `/actuator/health/readiness` → includes `readinessState` + all normal `HealthIndicator`s.

Accessing a group: `GET /actuator/health/liveness` returns the aggregated status for only that group's indicators.

## 4. Diagram

<svg viewBox="0 0 720 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="All HealthIndicators split into named groups: liveness, readiness, payments; each group has its own endpoint">
  <!-- Indicators -->
  <rect x="10" y="20" width="155" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="37" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">livenessState</text>

  <rect x="10" y="52" width="155" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">readinessState</text>

  <rect x="10" y="84" width="155" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">db</text>

  <rect x="10" y="116" width="155" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">redis</text>

  <rect x="10" y="148" width="155" height="25" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="87" y="165" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">paymentGateway</text>

  <rect x="10" y="180" width="155" height="25" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="87" y="197" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">fxRates</text>

  <!-- Group: liveness -->
  <rect x="215" y="10" width="170" height="50" rx="7" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">liveness group</text>
  <text x="300" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health/liveness</text>

  <!-- Group: readiness -->
  <rect x="215" y="75" width="170" height="65" rx="7" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">readiness group</text>
  <text x="300" y="111" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health/readiness</text>
  <text x="300" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">readinessState + db + redis</text>

  <!-- Group: payments -->
  <rect x="215" y="155" width="170" height="50" rx="7" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">payments group</text>
  <text x="300" y="191" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health/payments</text>

  <!-- Lines -->
  <line x1="168" y1="33" x2="212" y2="33" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hga)"/>
  <line x1="168" y1="65" x2="212" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hga)"/>
  <line x1="168" y1="97" x2="212" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hga)"/>
  <line x1="168" y1="130" x2="212" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hga)"/>
  <line x1="168" y1="160" x2="212" y2="172" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hgb)"/>
  <line x1="168" y1="192" x2="212" y2="185" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hgb)"/>

  <!-- k8s probe callout -->
  <rect x="420" y="30" width="270" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="555" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Kubernetes probes</text>
  <text x="555" y="68" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">livenessProbe: /actuator/health/liveness</text>
  <text x="555" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">readinessProbe: /actuator/health/readiness</text>
  <text x="555" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">management.endpoint.health.probes.enabled=true</text>

  <defs>
    <marker id="hga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="hgb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Groups partition indicators; liveness and readiness probes are the canonical Kubernetes use case.

## 5. Runnable example

```java
// HealthGroupsDemo.java — simulates health groups and their separate aggregation
// How to run: java HealthGroupsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: management.endpoint.health.group.<name>.include=<id1>,<id2>

import java.util.*;

public class HealthGroupsDemo {

    record Health(String status, Map<String, Object> details) {
        static Health up()   { return new Health("UP",   Map.of()); }
        static Health down() { return new Health("DOWN", Map.of()); }
        static Health up(String k, Object v) { return new Health("UP", Map.of(k, v)); }
    }

    // All registered HealthIndicators
    static final Map<String, Health> allIndicators = new LinkedHashMap<>();

    static {
        allIndicators.put("livenessState",  Health.up("reason", "CORRECT"));
        allIndicators.put("readinessState", Health.up("reason", "ACCEPTING_TRAFFIC"));
        allIndicators.put("db",             Health.up("database", "PostgreSQL"));
        allIndicators.put("redis",          Health.down());              // Redis is down
        allIndicators.put("paymentGateway", Health.up("responseMs", 42));
        allIndicators.put("fxRates",        Health.up("source", "ECB"));
    }

    // Group definitions (management.endpoint.health.group.<name>.include=...)
    static final Map<String, List<String>> groups = new LinkedHashMap<>(Map.of(
        "liveness",  List.of("livenessState"),
        "readiness", List.of("readinessState", "db", "redis"),
        "payments",  List.of("paymentGateway", "fxRates")
    ));

    static String aggregateStatus(List<String> ids) {
        List<String> order = List.of("DOWN", "OUT_OF_SERVICE", "UNKNOWN", "UP");
        String worst = "UP";
        for (String id : ids) {
            Health h = allIndicators.getOrDefault(id, new Health("UNKNOWN", Map.of()));
            if (order.indexOf(h.status()) < order.indexOf(worst)) worst = h.status();
        }
        return worst;
    }

    static void printGroup(String name, List<String> ids) {
        String status = aggregateStatus(ids);
        System.out.printf("%nGET /actuator/health/%s%n", name);
        System.out.printf("  { \"status\": \"%s\", \"components\": {%n", status);
        for (String id : ids) {
            Health h = allIndicators.getOrDefault(id, new Health("UNKNOWN", Map.of()));
            System.out.printf("      \"%s\": { \"status\": \"%s\"%s }%n",
                    id, h.status(),
                    h.details().isEmpty() ? "" : ", \"details\": " + h.details());
        }
        System.out.println("  } }");
        System.out.printf("  => HTTP %s%n", status.equals("UP") ? "200 OK" : "503 SERVICE_UNAVAILABLE");
    }

    public static void main(String[] args) {
        System.out.println("=== Health Groups Demo ===\n");
        System.out.println("State: redis=DOWN (payment gateway and JVM are UP)\n");

        // Print each group
        groups.forEach(HealthGroupsDemo::printGroup);

        System.out.println("\n--- Kubernetes effect ---");
        System.out.println("liveness  (livenessState=UP)  → 200 → pod NOT restarted");
        System.out.println("readiness (redis=DOWN)         → 503 → pod removed from load balancer");
        System.out.println("=> Correct: traffic stops but no unnecessary restart");

        System.out.println("\n--- application.properties ---");
        System.out.println("management.endpoint.health.probes.enabled=true");
        System.out.println("management.endpoint.health.group.readiness.include=readinessState,db,redis");
        System.out.println("management.endpoint.health.group.payments.include=paymentGateway,fxRates");
        System.out.println("management.endpoint.health.group.payments.show-details=always");
    }
}
```

**How to run:** `java HealthGroupsDemo.java`

## 6. Walkthrough

- **`allIndicators`** seeds the state: `redis=DOWN` simulates a Redis outage while JVM and payment gateway are healthy.
- **`liveness` group**: only `livenessState` — JVM alive state. Redis down has no effect → 200. Kubernetes does not restart the pod.
- **`readiness` group**: includes `readinessState + db + redis`. `redis=DOWN` → worst status = DOWN → 503. Kubernetes removes pod from service. Pod stays running.
- **`payments` group**: independent check for the payments team — `paymentGateway` and `fxRates` are both UP → 200. Payments team knows their dependencies are healthy even during the Redis incident.
- HTTP status codes: `UP` → 200, `DOWN`/`OUT_OF_SERVICE` → 503, `UNKNOWN` → 200 by default (configurable per group with `status.http-mapping`).

## 7. Gotchas & takeaways

> `management.endpoint.health.probes.enabled=true` creates `liveness` and `readiness` groups **automatically**, but the `readiness` group includes all `HealthIndicator`s by default. You must **explicitly narrow** it if you don't want infrastructure indicators (Redis, DB) to prevent traffic.

> A Kubernetes liveness probe that includes an external dependency (DB health) causes **cascading restarts** during an outage — every pod restarts simultaneously, making recovery slower. Always keep liveness group minimal.

- `management.endpoint.health.group.<name>.include=*` includes all indicators in the group; `exclude` removes specific ones.
- Per-group detail visibility: `management.endpoint.health.group.payments.show-details=always`.
- Per-group HTTP status mapping: `management.endpoint.health.group.readiness.status.http-mapping.out-of-service=503`.
- Signal graceful shutdown to Kubernetes: set `readinessState` to `REFUSING_TRAFFIC` before shutting down — `readiness` probe returns DOWN, traffic stops, then the pod terminates cleanly.
