---
card: spring-cloud
gi: 33
slug: health-checks-status
title: "Health checks & status"
---

## 1. What it is

By default, Eureka considers an instance "healthy" purely based on whether it's heartbeating — an instance can be internally broken (its database connection pool exhausted, a critical dependency unreachable) and Eureka would still report it `UP`, because it's still sending heartbeats. Health check integration replaces that with a real check: wiring Eureka to Spring Boot Actuator's `/actuator/health` endpoint, so an instance's *reported* status reflects its *actual* application health, not just process liveness.

```properties
eureka.client.healthcheck.enabled=true
```

## 2. Why & when

Heartbeating only proves the process is alive and the network path to Eureka works — it says nothing about whether the application can actually serve traffic. An instance whose database connection died is still a running JVM sending heartbeats every 30 seconds, so without health check integration Eureka keeps advertising it as `UP`, and callers keep routing traffic to an instance that will fail every request.

Turn on health check propagation when:

- The application has real dependencies (database, downstream services, message queues) whose failure should take the instance out of rotation, not just crash detection.
- You're already using Spring Boot Actuator's health indicators (database, disk space, custom checks) and want that same signal to drive discoverability, not just an ops dashboard.
- You want callers to stop being routed to an instance the moment it becomes unhealthy, rather than waiting for it to crash outright and get evicted via lease expiry (which can take up to 90 seconds).

## 3. Core concept

```
 Without health check propagation:
   process alive + heartbeating -> Eureka reports UP
   (even if /actuator/health reports DOWN internally)

 With health check propagation:
   Eureka polls/receives /actuator/health status
   -> maps it to Eureka status: UP, DOWN, OUT_OF_SERVICE, UNKNOWN
   -> only UP instances are returned to discovery queries
```

Health check integration makes Eureka's reported status track the application's actual ability to serve traffic, not merely its process liveness.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance's actuator health endpoint feeds its Eureka status, so a failing dependency marks it DOWN and removes it from discovery results even though it is still heartbeating">
  <rect x="30" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">orders-service</text>
  <text x="120" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">/actuator/health -&gt; DOWN</text>

  <line x1="210" y1="55" x2="380" y2="55" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a33)"/>
  <text x="295" y="45" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">status propagates</text>

  <rect x="390" y="30" width="180" height="50" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.5"/>
  <text x="480" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server</text>
  <text x="480" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance status: DOWN</text>

  <rect x="230" y="130" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="154" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">discovery query excludes it</text>
  <line x1="480" y1="80" x2="340" y2="128" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a33)"/>

  <defs><marker id="a33" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

An unhealthy dependency inside the instance flows through to its Eureka status, removing it from discovery before it ever fails a real caller's request.

## 5. Runnable example

The scenario: an order service instance whose health depends on its database connection. Start with heartbeat-only status, then wire in an actual health check, then add graceful `OUT_OF_SERVICE` draining for planned maintenance.

### Level 1 — Basic

Heartbeat-only status — the gap this feature closes.

```java
public class HealthChecksLevel1 {
    static class Instance {
        String name;
        boolean heartbeating = true;
        boolean databaseReachable = false; // internally broken!

        String eurekaStatus() {
            return heartbeating ? "UP" : "DOWN"; // ignores databaseReachable entirely
        }
    }

    public static void main(String[] args) {
        Instance orders1 = new Instance();
        orders1.name = "orders-service-1";

        System.out.println(orders1.name + " -> Eureka reports: " + orders1.eurekaStatus());
        // "UP" -- even though its database is down and every real request will fail
    }
}
```

How to run: `java HealthChecksLevel1.java`

`eurekaStatus()` only looks at `heartbeating`, so a database outage is invisible to Eureka: callers keep getting routed to `orders-service-1` and every request fails, even though the instance is technically "alive."

### Level 2 — Intermediate

Wire in an actual health check, mapping actuator-style health to Eureka status.

```java
public class HealthChecksLevel2 {
    enum HealthStatus { UP, DOWN }
    enum EurekaStatus { UP, DOWN, OUT_OF_SERVICE, UNKNOWN }

    static class Instance {
        String name;
        boolean heartbeating = true;
        boolean databaseReachable;
        boolean healthcheckEnabled; // eureka.client.healthcheck.enabled

        HealthStatus actuatorHealth() {
            // mirrors a real /actuator/health aggregate: DOWN if any critical indicator is DOWN
            return databaseReachable ? HealthStatus.UP : HealthStatus.DOWN;
        }

        EurekaStatus eurekaStatus() {
            if (!heartbeating) return EurekaStatus.DOWN;
            if (!healthcheckEnabled) return EurekaStatus.UP; // Level 1 behavior when disabled
            return actuatorHealth() == HealthStatus.UP ? EurekaStatus.UP : EurekaStatus.DOWN;
        }
    }

    public static void main(String[] args) {
        Instance orders1 = new Instance();
        orders1.name = "orders-service-1";
        orders1.databaseReachable = false;
        orders1.healthcheckEnabled = true;

        System.out.println(orders1.name + " -> Eureka reports: " + orders1.eurekaStatus());
        // now correctly DOWN, because the wired-in health check reflects the real dependency failure
    }
}
```

How to run: `java HealthChecksLevel2.java`

`eurekaStatus()` now consults `actuatorHealth()` when `healthcheckEnabled` is true, and `actuatorHealth()` reflects the real `databaseReachable` flag — so a broken database dependency now correctly flips the reported Eureka status to `DOWN`, taking the instance out of discovery results instead of silently failing every routed request.

### Level 3 — Advanced

Add `OUT_OF_SERVICE`, a manually-set status used for graceful draining during planned maintenance or a rolling deploy, which takes priority over the automatic health-derived status.

```java
import java.util.*;

public class HealthChecksLevel3 {
    enum HealthStatus { UP, DOWN }
    enum EurekaStatus { UP, DOWN, OUT_OF_SERVICE, UNKNOWN }

    static class Instance {
        String name;
        boolean heartbeating = true;
        boolean databaseReachable = true;
        boolean healthcheckEnabled = true;
        EurekaStatus manualOverride; // null = no override; set by ops for draining

        HealthStatus actuatorHealth() {
            return databaseReachable ? HealthStatus.UP : HealthStatus.DOWN;
        }

        EurekaStatus eurekaStatus() {
            if (manualOverride != null) return manualOverride; // manual override wins over everything
            if (!heartbeating) return EurekaStatus.DOWN;
            if (!healthcheckEnabled) return EurekaStatus.UP;
            return actuatorHealth() == HealthStatus.UP ? EurekaStatus.UP : EurekaStatus.DOWN;
        }
    }

    static List<Instance> discover(List<Instance> all) {
        return all.stream().filter(i -> i.eurekaStatus() == EurekaStatus.UP).toList();
    }

    public static void main(String[] args) {
        Instance orders1 = new Instance(); orders1.name = "orders-service-1";
        Instance orders2 = new Instance(); orders2.name = "orders-service-2";
        List<Instance> fleet = List.of(orders1, orders2);

        System.out.println("before maintenance, discoverable: " + names(discover(fleet)));

        orders1.manualOverride = EurekaStatus.OUT_OF_SERVICE; // ops drains orders1 for a rolling deploy
        System.out.println("draining orders1, discoverable: " + names(discover(fleet)));

        // deploy finishes, orders1 comes back
        orders1.manualOverride = null;
        System.out.println("back in rotation, discoverable: " + names(discover(fleet)));
    }

    static List<String> names(List<Instance> instances) {
        return instances.stream().map(i -> i.name).toList();
    }
}
```

How to run: `java HealthChecksLevel3.java`

`manualOverride` is checked first in `eurekaStatus()`, ahead of both heartbeat and actuator health — this models a real operator or deploy pipeline calling Eureka's `PUT /eureka/apps/{app}/{id}/status?value=OUT_OF_SERVICE` endpoint to pull an instance out of rotation *before* taking it down for maintenance, rather than waiting for a crash to remove it. `discover()` only returns instances whose status is `UP`, so `orders1` disappears from results the instant it's marked `OUT_OF_SERVICE`, and reappears the instant the override is cleared.

## 6. Walkthrough

Trace Level 3's three `println` calls in order.

1. `discover(fleet)` runs first with no overrides set — both instances have `heartbeating=true`, `healthcheckEnabled=true`, and `databaseReachable=true`, so `eurekaStatus()` falls through to `actuatorHealth() == UP`, returning `UP` for both. The filter keeps both, printing `[orders-service-1, orders-service-2]`.
2. `orders1.manualOverride = OUT_OF_SERVICE` runs — this models an operator or CI/CD pipeline issuing a status-override call ahead of a planned deploy, deliberately pulling the instance out of rotation while it's still perfectly healthy and still running, so in-flight requests can drain naturally instead of being cut off mid-request.
3. `discover(fleet)` runs again — for `orders1`, `eurekaStatus()` now hits the `manualOverride != null` branch first and returns `OUT_OF_SERVICE` immediately, without even checking heartbeat or actuator health. The filter drops it, printing only `[orders-service-2]`.
4. `orders1.manualOverride = null` runs — this models the deploy pipeline restoring the instance to normal status once the new version is confirmed healthy.
5. `discover(fleet)` runs a third time — `orders1` falls through to its real health-derived status again (`UP`, since its database is fine), and both instances are discoverable once more: `[orders-service-1, orders-service-2]`.

```
manualOverride == OUT_OF_SERVICE  ---->  always wins, short-circuits everything else
manualOverride == null:
    heartbeating? no -> DOWN
    healthcheckEnabled? no -> UP (Level 1 behavior)
    actuatorHealth() == UP? -> UP, else DOWN
```

## 7. Gotchas & takeaways

> **Gotcha:** `eureka.client.healthcheck.enabled=true` alone doesn't magically make Eureka aware of custom health indicators — it wires the *aggregate* `/actuator/health` status into Eureka's reported status. If a custom `HealthIndicator` bean isn't correctly included in that aggregate (e.g. it's registered but its contribution is filtered out by `management.endpoint.health.show-details` or group configuration), Eureka never sees it either.

- Heartbeat-only status only proves the process is alive; health-check-integrated status proves the application can actually do its job — always prefer the latter for anything with real dependencies.
- `OUT_OF_SERVICE` is the correct mechanism for planned maintenance and rolling deploys — it lets in-flight requests finish and new requests avoid the instance, instead of the abrupt cutoff a crash-and-evict cycle produces.
- A manual status override takes priority over both heartbeat and health-check-derived status — use it deliberately, and remember to clear it, or the instance stays invisible even after it's healthy again.
- Combining health-check propagation with a short `lease-renewal-interval-in-seconds` (from the earlier instance/client configuration card) gives the fastest possible "unhealthy instance leaves rotation" behavior.
