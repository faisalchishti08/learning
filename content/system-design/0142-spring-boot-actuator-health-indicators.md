---
card: system-design
gi: 142
slug: spring-boot-actuator-health-indicators
title: Spring Boot Actuator health indicators
---

## 1. What it is

**Spring Boot Actuator** exposes production-ready monitoring endpoints for a Spring Boot application, including `/actuator/health` — the concrete implementation of the [health check](0132-health-checks-heartbeats.md) concept for a Spring app. A **health indicator** is a component that reports whether one specific part of the application (a database connection, a disk, a custom dependency) is healthy; Actuator aggregates every registered indicator's status into one overall `/actuator/health` response.

## 2. Why & when

A load balancer or Kubernetes needs a real, meaningful health endpoint to decide whether to route traffic to an instance — not just "is the process running," but "can this instance actually do its job right now." Actuator's `/actuator/health` endpoint, backed by health indicators, provides exactly this out of the box for common dependencies (a `DataSource`, a `DiskSpaceHealthIndicator`), and lets you add custom indicators for anything else your service depends on. Use it in every Spring Boot service that will run behind a load balancer or orchestrator — it is the standard mechanism, requiring no custom endpoint code for the common cases.

## 3. Core concept

- **Built-in indicators:** Actuator auto-configures indicators for common dependencies already on the classpath — a `DataSource` (database connectivity), disk space, and others — with zero custom code required.
- **Custom `HealthIndicator`:** implement the `HealthIndicator` interface (or extend `AbstractHealthIndicator`) and override `health()` to return `Health.up()` or `Health.down()`, optionally with details — Spring registers it automatically as a bean.
- **Aggregation:** the overall `/actuator/health` status is `UP` only if every registered indicator reports `UP`; if any indicator reports `DOWN`, the aggregate status is `DOWN`.
- **Liveness vs readiness groups:** Actuator distinguishes `/actuator/health/liveness` ("is the process alive, should it be restarted if not") from `/actuator/health/readiness` ("is it ready to receive traffic right now") — matching the [liveness vs readiness](0132-health-checks-heartbeats.md) distinction, letting Kubernetes use each for its own separate purpose.
- **Health details exposure:** by default, detailed information (why something is down) is only shown to authorized users, not exposed publicly — a security consideration, since health details can reveal internal architecture.

## 4. Diagram

```
GET /actuator/health

  Aggregated response built from every registered HealthIndicator:

  +-------------------+       +---------------------+
  | db (DataSource)   | UP    | diskSpace            | UP
  +-------------------+       +---------------------+
  +-------------------+       +---------------------+
  | paymentsGateway    | DOWN  | (custom indicator)   |
  | (custom indicator) |       |                       |
  +-------------------+       +---------------------+

  Overall status: DOWN (because paymentsGateway is DOWN,
  even though db and diskSpace are both UP)

  Load balancer sees DOWN -> removes this instance from rotation
```
*Caption: the overall health status is DOWN if even one registered indicator reports DOWN, regardless of how many others report UP.*

## 5. Runnable example

**Level 1 — Basic.** Model built-in-style indicators (database, disk) and aggregate their status.

**Level 2 — Custom `HealthIndicator`.** Add a custom indicator for an external dependency, and show it affecting the aggregate.

**Level 3 — Liveness vs readiness groups.** Separate indicators into liveness and readiness groups, matching Actuator's real behavior.

```java
// ActuatorHealthDemo.java
import java.util.*;

public class ActuatorHealthDemo {

    enum Status { UP, DOWN }
    record Health(Status status, String details) {}

    interface HealthIndicator { Health health(); }

    // Level 1: built-in-style indicators.
    static class DataSourceHealthIndicator implements HealthIndicator {
        boolean databaseReachable;
        DataSourceHealthIndicator(boolean databaseReachable) { this.databaseReachable = databaseReachable; }
        public Health health() {
            return databaseReachable ? new Health(Status.UP, "database connection OK")
                                      : new Health(Status.DOWN, "cannot reach database");
        }
    }

    static class DiskSpaceHealthIndicator implements HealthIndicator {
        long freeBytes;
        DiskSpaceHealthIndicator(long freeBytes) { this.freeBytes = freeBytes; }
        public Health health() {
            return freeBytes > 10_000_000 ? new Health(Status.UP, "free space: " + freeBytes)
                                           : new Health(Status.DOWN, "low disk space: " + freeBytes);
        }
    }

    // Level 2: a custom HealthIndicator for an application-specific external dependency.
    static class PaymentsGatewayHealthIndicator implements HealthIndicator {
        boolean gatewayHealthy;
        PaymentsGatewayHealthIndicator(boolean gatewayHealthy) { this.gatewayHealthy = gatewayHealthy; }
        public Health health() {
            return gatewayHealthy ? new Health(Status.UP, "payments gateway responding")
                                  : new Health(Status.DOWN, "payments gateway timeout");
        }
    }

    static Status aggregate(Map<String, HealthIndicator> indicators) {
        for (var entry : indicators.entrySet()) {
            Health h = entry.getValue().health();
            System.out.println("  " + entry.getKey() + ": " + h.status() + " (" + h.details() + ")");
            if (h.status() == Status.DOWN) return Status.DOWN; // ANY down indicator makes the aggregate DOWN
        }
        return Status.UP;
    }

    public static void main(String[] args) {
        // Level 1 & 2: register indicators, including the custom one, and aggregate.
        Map<String, HealthIndicator> indicators = new LinkedHashMap<>();
        indicators.put("db", new DataSourceHealthIndicator(true));
        indicators.put("diskSpace", new DiskSpaceHealthIndicator(50_000_000));
        indicators.put("paymentsGateway", new PaymentsGatewayHealthIndicator(false)); // custom indicator, DOWN

        System.out.println("GET /actuator/health:");
        Status overall = aggregate(indicators);
        System.out.println("overall status: " + overall + " (DOWN because paymentsGateway is DOWN, even though db/diskSpace are UP)");

        // Level 3: liveness vs readiness groups - different indicators serve different purposes.
        Map<String, HealthIndicator> livenessGroup = Map.of("diskSpace", indicators.get("diskSpace")); // "should this pod be restarted?"
        Map<String, HealthIndicator> readinessGroup = Map.of(
            "db", indicators.get("db"), "paymentsGateway", indicators.get("paymentsGateway")); // "can it serve traffic?"

        System.out.println("GET /actuator/health/liveness:");
        System.out.println("liveness status: " + aggregate(livenessGroup) + " (process itself is fine, no restart needed)");

        System.out.println("GET /actuator/health/readiness:");
        System.out.println("readiness status: " + aggregate(readinessGroup) + " (NOT ready - load balancer should not route traffic here)");
    }
}
```

**How to run:** save as `ActuatorHealthDemo.java`, then run `java ActuatorHealthDemo.java`. (A real Spring Boot app gets `db` and `diskSpace` indicators automatically from `spring-boot-starter-actuator` with no code; a custom one is a `@Component implements HealthIndicator` bean, and liveness/readiness groups are configured via `management.endpoint.health.group.readiness.include=...` in `application.yml`.)

## 6. Walkthrough

1. `DataSourceHealthIndicator` and `DiskSpaceHealthIndicator` model Actuator's built-in indicators, each implementing the same `HealthIndicator` interface and returning `Health.UP` or `Health.DOWN` based on their own simple check.
2. `PaymentsGatewayHealthIndicator` models a custom indicator a developer would add for an application-specific dependency; it is constructed with `gatewayHealthy = false`, representing a real outage in an external payments provider.
3. `aggregate` iterates every registered indicator, printing each one's individual status, and returns `Status.DOWN` the moment it finds any indicator reporting `DOWN` — modeling Actuator's real aggregation rule that one failing component brings down the overall reported status.
4. The Level 1/2 output shows `db` and `diskSpace` both `UP`, but `paymentsGateway` `DOWN`, and the final `overall` status printed as `DOWN` — confirming that a single failing custom indicator, alongside otherwise-healthy built-in ones, correctly drives the whole `/actuator/health` endpoint to report the instance as unhealthy.
5. Level 3 splits the same indicators into `livenessGroup` (just disk space — a genuine "should the process be killed and restarted" concern) and `readinessGroup` (database and the payments gateway — "can this instance serve real traffic right now"). Aggregating each group separately shows liveness reporting `UP` (the process itself is fine) while readiness reports `DOWN` (traffic should not be routed here) — exactly the distinction that lets an orchestrator restart a process only when truly necessary, while still pulling it out of load-balancer rotation for a lesser, readiness-only problem.

## 7. Gotchas & takeaways

> Gotcha: putting a slow, deep dependency check (a check that makes its own network call to a payments gateway) into the *liveness* group instead of the *readiness* group can cause an orchestrator to kill and restart a perfectly healthy process, purely because an unrelated external dependency is temporarily slow or down — liveness should generally check only "is this process itself functioning," while readiness checks "can it currently serve real requests."

- Spring Boot Actuator's `/actuator/health` endpoint aggregates every registered `HealthIndicator`'s status, reporting the whole instance as down if even one indicator reports down.
- Built-in indicators cover common dependencies automatically; a custom `HealthIndicator` bean lets you add checks for any application-specific dependency with minimal code.
- Liveness and readiness groups let Kubernetes (or any orchestrator) distinguish "should this process be restarted" from "should traffic be routed here," using different, appropriately-scoped sets of indicators for each.
- Related concepts: [Health checks & heartbeats](0132-health-checks-heartbeats.md) (the general concept this implements concretely in Spring Boot), [Single points of failure elimination](0133-single-points-of-failure-elimination.md) (health checks are what let redundancy actually route around a failure).
