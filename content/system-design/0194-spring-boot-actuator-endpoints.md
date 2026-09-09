---
card: system-design
gi: 194
slug: spring-boot-actuator-endpoints
title: Spring Boot Actuator endpoints
---

## 1. What it is

**Spring Boot Actuator** exposes a set of built-in HTTP endpoints, each surfacing a different piece of operational information about a running application: `/actuator/health` (is the app healthy?), `/actuator/metrics` (application metrics), `/actuator/prometheus` (metrics in Prometheus format), `/actuator/env` (current configuration), and several more. Adding the `spring-boot-starter-actuator` dependency enables these automatically, giving you production-ready operational visibility with no custom code required for the basics.

## 2. Why & when

Building your own health-check endpoint, metrics endpoint, and configuration-inspection endpoint from scratch for every Spring Boot application is repetitive and easy to get subtly wrong (for example, exposing sensitive configuration values that should stay hidden). Actuator provides these as a standard, well-tested, configurable feature — you get [health checks](0132-health-checks-heartbeats.md), metrics ([Micrometer](0192-micrometer-metrics-prometheus.md) integration), and diagnostic endpoints out of the box, and can extend them with custom health indicators or metrics specific to your application. Use Actuator in any Spring Boot service intended to run in production, since load balancers, Kubernetes, and monitoring systems all commonly integrate directly with its standard endpoints.

## 3. Core concept

- **`/actuator/health`:** aggregates the status of registered `HealthIndicator`s (database connectivity, disk space, custom checks you add) into one overall `UP`/`DOWN` status — this is what a load balancer or Kubernetes liveness/readiness probe typically checks.
- **Custom `HealthIndicator`:** implementing this interface lets you add application-specific health logic (e.g. "can we reach our critical downstream dependency?") that gets automatically folded into the overall `/health` aggregate status.
- **`/actuator/metrics` and `/actuator/prometheus`:** expose the [Micrometer](0192-micrometer-metrics-prometheus.md)-collected metrics, either browsable individually (`/actuator/metrics/http.server.requests`) or in Prometheus's scrapeable text format.
- **Endpoint exposure control:** by default, only `/health` is exposed over HTTP; other endpoints (`/env`, `/beans`, `/mappings`) must be explicitly enabled via `management.endpoints.web.exposure.include`, since many of them can leak sensitive internal details if left open carelessly.
- **Readiness vs. liveness groups:** Actuator supports separate health groups (`/actuator/health/liveness`, `/actuator/health/readiness`) matching Kubernetes' distinction between "is the process alive" and "is it ready to receive traffic" — a subtly different question a single flat health check cannot answer on its own.

## 4. Diagram

```
   GET /actuator/health
        |
        v
   aggregate ALL registered HealthIndicators:
     - db: UP (connection successful)
     - diskSpace: UP (85GB free)
     - customDownstreamCheck: DOWN (payment provider unreachable)
        |
        v
   overall status: DOWN   (any DOWN indicator makes the whole aggregate DOWN)
        |
        v
   load balancer / Kubernetes readiness probe sees DOWN
        |
        v
   traffic is routed AWAY from this instance until it recovers
```
*Caption: the overall health status aggregates every registered indicator; a single failing dependency is enough to mark the whole instance unhealthy and stop routing traffic to it.*

## 5. Runnable example

This models Actuator's health aggregation and endpoint-exposure logic in-process; the "How to run" note shows the real dependency and configuration.

**Level 1 — Basic.** Register health indicators and aggregate their status into an overall health result.

**Level 2 — A custom `HealthIndicator` checking a real downstream dependency.** Fold its result into the overall aggregate.

**Level 3 — Separate readiness and liveness groups.** Show a case where the process is alive but not ready to serve traffic.

```java
// ActuatorDemo.java
import java.util.*;
import java.util.function.*;

public class ActuatorDemo {

    enum Status { UP, DOWN }

    static class HealthResult {
        final String name;
        final Status status;
        final String detail;
        HealthResult(String name, Status status, String detail) { this.name = name; this.status = status; this.detail = detail; }
    }

    // Level 1: registered health indicators - each one just a supplier of a HealthResult.
    static Map<String, Supplier<HealthResult>> healthIndicators = new LinkedHashMap<>();

    static void registerHealthIndicator(String name, Supplier<HealthResult> check) {
        healthIndicators.put(name, check);
    }

    // Aggregate ALL registered indicators - any single DOWN makes the whole result DOWN.
    static Status aggregateHealth(Collection<Supplier<HealthResult>> indicators) {
        Status overall = Status.UP;
        for (Supplier<HealthResult> indicator : indicators) {
            HealthResult result = indicator.get();
            System.out.println("  " + result.name + ": " + result.status + " (" + result.detail + ")");
            if (result.status == Status.DOWN) overall = Status.DOWN;
        }
        return overall;
    }

    public static void main(String[] args) {
        // Level 1: standard indicators, always healthy in this example.
        registerHealthIndicator("db", () -> new HealthResult("db", Status.UP, "connection pool responsive"));
        registerHealthIndicator("diskSpace", () -> new HealthResult("diskSpace", Status.UP, "85GB free"));

        // Level 2: a CUSTOM HealthIndicator checking a real downstream dependency.
        boolean[] paymentProviderReachable = {false}; // simulate an outage
        registerHealthIndicator("paymentProvider", () -> paymentProviderReachable[0]
            ? new HealthResult("paymentProvider", Status.UP, "responded in 45ms")
            : new HealthResult("paymentProvider", Status.DOWN, "connection timeout"));

        System.out.println("GET /actuator/health:");
        Status overallHealth = aggregateHealth(healthIndicators.values());
        System.out.println("overall status: " + overallHealth);

        // Level 3: separate readiness/liveness groups - the process is ALIVE but not READY.
        System.out.println("GET /actuator/health/liveness (is the JVM process itself alive?):");
        List<Supplier<HealthResult>> livenessIndicators = List.of(
            () -> new HealthResult("processAlive", Status.UP, "JVM running normally"));
        Status liveness = aggregateHealth(livenessIndicators);
        System.out.println("liveness: " + liveness);

        System.out.println("GET /actuator/health/readiness (is it ready to serve REAL traffic?):");
        List<Supplier<HealthResult>> readinessIndicators = List.of(
            healthIndicators.get("db"), healthIndicators.get("paymentProvider"));
        Status readiness = aggregateHealth(readinessIndicators);
        System.out.println("readiness: " + readiness + " (process is alive, but NOT ready - traffic should be withheld)");
    }
}
```

**How to run:** save as `ActuatorDemo.java`, then run `java ActuatorDemo.java`. (Real Spring Boot: add `spring-boot-starter-actuator`, implement `HealthIndicator` for a custom check (`@Component class PaymentProviderHealthIndicator implements HealthIndicator { public Health health() { ... } }`), and configure `management.endpoint.health.group.readiness.include=db,paymentProvider` in `application.yml` to define custom readiness groups.)

## 6. Walkthrough

1. `registerHealthIndicator("db", ...)` and `registerHealthIndicator("diskSpace", ...)` both register suppliers that always return `Status.UP` with a specific detail message, modeling two standard, healthy indicators.
2. `registerHealthIndicator("paymentProvider", ...)` registers a supplier whose result depends on the mutable `paymentProviderReachable[0]` flag, currently `false` — this models a custom `HealthIndicator` actually checking a real downstream dependency, which happens to be experiencing an outage in this run.
3. `aggregateHealth(healthIndicators.values())` calls every registered supplier in turn, printing each result; since `db` and `diskSpace` are `UP` but `paymentProvider` is `DOWN`, the loop's `if (result.status == Status.DOWN) overall = Status.DOWN` sets the running `overall` variable to `DOWN` on that one failing check, and it stays `DOWN` for the rest of the loop — the final aggregate reflects that single failure, exactly matching how a real `/actuator/health` aggregate works.
4. The liveness check uses a separate, deliberately minimal list of indicators (just "is the process running"), which stays `UP` regardless of the payment provider's status — this models the Kubernetes liveness distinction: the JVM process itself is perfectly fine and should not be restarted.
5. The readiness check, by contrast, explicitly includes `paymentProvider` in its indicator list, and its aggregate comes back `DOWN` — modeling the readiness distinction: even though the process is alive and should not be killed, it genuinely should not receive new traffic right now, since a dependency it needs is unavailable; a load balancer or Kubernetes readiness probe watching this specific endpoint would correctly route traffic elsewhere.

## 7. Gotchas & takeaways

> Gotcha: exposing Actuator endpoints like `/actuator/env` or `/actuator/heapdump` publicly, without authentication, can leak sensitive configuration values (database passwords, API keys present in environment variables) or even memory contents to anyone who can reach the endpoint — always restrict Actuator's sensitive endpoints to an internal network or require authentication, and only expose what is genuinely needed externally (typically just `/health`).

- Actuator's `/health` endpoint aggregates every registered health indicator; a single `DOWN` indicator marks the whole instance unhealthy.
- Custom `HealthIndicator`s let you fold application-specific dependency checks into this same standard aggregation mechanism.
- Liveness and readiness are genuinely different questions — a process can be perfectly alive while still correctly reporting itself as not ready for traffic.
- Related concepts: [Health checks & heartbeats](0132-health-checks-heartbeats.md) (the general pattern Actuator's health endpoint implements), [Micrometer metrics + Prometheus](0192-micrometer-metrics-prometheus.md) (what powers Actuator's `/metrics` and `/prometheus` endpoints), [Secrets management & rotation](0180-secrets-management-rotation.md) (relevant to why exposing `/actuator/env` carelessly is a real security risk).
