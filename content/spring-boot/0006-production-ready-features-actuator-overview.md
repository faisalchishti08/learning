---
card: spring-boot
gi: 6
slug: production-ready-features-actuator-overview
title: Production-ready features (Actuator) overview
---

## 1. What it is

**Spring Boot Actuator** adds production-readiness to your application by exposing a set of built-in HTTP and JMX endpoints that reveal the internal state of a running application. Add the dependency, get operational visibility immediately.

Key built-in endpoints (all under `/actuator` by default):

| Endpoint | What it shows |
|---|---|
| `/actuator/health` | Application health status (UP/DOWN/OUT_OF_SERVICE) |
| `/actuator/info` | App version, git commit, custom info |
| `/actuator/metrics` | JVM, HTTP, datasource, custom metrics |
| `/actuator/env` | All resolved properties and their source |
| `/actuator/loggers` | Current log levels; can change them at runtime |
| `/actuator/threaddump` | All threads and their stack traces |
| `/actuator/httptrace` | Last 100 HTTP request/response pairs |
| `/actuator/beans` | Every bean in the ApplicationContext |
| `/actuator/mappings` | All `@RequestMapping` routes |
| `/actuator/shutdown` | Graceful shutdown (disabled by default) |

Actuator also exposes a Micrometer-based metrics facade that integrates with Prometheus, Datadog, New Relic, Graphite, and dozens of other monitoring systems.

## 2. Why & when

An application running in production is a black box. If `GET /orders` starts returning 500s, you need to know: is the database down? Is the thread pool saturated? Which deployment version is running? Is the JVM running out of heap?

Without Actuator you'd need to:
- SSH into the server and read log files.
- Restart to change a log level.
- Re-deploy to update version info.

Actuator answers these questions via HTTP, without a deployment. This makes it essential for:

- **Health checks in Kubernetes/ECS** — the `/actuator/health` endpoint is the standard liveness and readiness probe target.
- **Monitoring dashboards** — `/actuator/metrics` feeds Prometheus, which drives Grafana.
- **Incident response** — `/actuator/loggers` lets you turn on `DEBUG` on a misbehaving package in prod and back to `WARN` after, with no restart.
- **Configuration audits** — `/actuator/env` shows the resolved value of every property and where it came from.

## 3. Core concept

Actuator endpoints are Spring MVC (or WebFlux) controllers registered automatically when you add `spring-boot-starter-actuator`. The framework:

1. Creates an `ActuatorEndpointHandlerMapping` alongside your app's `RequestMappingHandlerMapping`.
2. Registers all `@Endpoint`-annotated classes (Spring's own + any custom ones you write).
3. Secures them — by default only `/health` and `/info` are exposed over HTTP; the rest require explicit opt-in.

**Health indicators** are the most commonly used feature. Spring Boot auto-registers `HealthIndicator` beans for every datasource, Redis connection, Elasticsearch cluster, etc. it manages. They are queried each time `/actuator/health` is called:

- A `DataSourceHealthIndicator` runs `SELECT 1` against your database.
- A `DiskSpaceHealthIndicator` checks that the disk isn't nearly full.
- Status aggregates: if any indicator reports DOWN, the top-level status is DOWN, and a Kubernetes liveness probe fails → Pod restarts.

**Micrometer** is the metrics abstraction layer — a vendor-neutral API. Your code calls `counter.increment()` or `timer.record(...)`, and Micrometer routes the data to whichever registry is configured (Prometheus, Datadog, etc.).

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Actuator architecture showing application internals exposed via HTTP endpoints to monitoring tools">
  <!-- Application box -->
  <rect x="20" y="40" width="280" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="64" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot App</text>

  <rect x="36" y="74" width="248" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="93" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Business Logic + Spring Beans</text>

  <rect x="36" y="110" width="108" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="90" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Health Indicators</text>
  <rect x="156" y="110" width="128" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="220" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Micrometer Metrics</text>

  <rect x="36" y="146" width="248" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="165" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Actuator Endpoints /actuator/*</text>

  <!-- HTTP arrow out -->
  <line x1="300" y1="160" x2="350" y2="160" stroke="#6db33f" stroke-width="2" marker-end="url(#actarr)"/>
  <text x="320" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP</text>

  <!-- Consumers box -->
  <rect x="354" y="40" width="300" height="180" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="504" y="64" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Consumers</text>

  <rect x="370" y="74" width="124" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="432" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Kubernetes Probes</text>

  <rect x="506" y="74" width="132" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="572" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Prometheus/Grafana</text>

  <rect x="370" y="110" width="124" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="432" y="129" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">On-call Engineer</text>

  <rect x="506" y="110" width="132" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="572" y="129" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">APM Tools</text>

  <rect x="370" y="146" width="268" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="504" y="165" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CI/CD pipelines (smoke tests)</text>

  <defs>
    <marker id="actarr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Actuator bridges your app's internals to the outside world — monitoring systems, orchestrators, and engineers — all via HTTP without code changes.

## 5. Runnable example

```java
// File: ActuatorDemo.java
// Demonstrates the health-indicator pattern in pure Java.
// Run: java ActuatorDemo.java

import java.util.*;

public class ActuatorDemo {

    enum Status { UP, DOWN, OUT_OF_SERVICE }

    record Health(Status status, Map<String, Object> details) {
        static Health up(Map<String, Object> d)   { return new Health(Status.UP,   d); }
        static Health down(Map<String, Object> d) { return new Health(Status.DOWN, d); }
    }

    // Simulates DataSourceHealthIndicator
    static Health checkDatabase() {
        // Pretend: SELECT 1 succeeded in 3ms
        boolean dbReachable = true;
        if (dbReachable) {
            return Health.up(Map.of("database", "PostgreSQL", "query", "SELECT 1", "ms", 3));
        }
        return Health.down(Map.of("error", "Connection refused", "host", "db:5432"));
    }

    // Simulates DiskSpaceHealthIndicator
    static Health checkDisk() {
        long freeGb = 42L;
        long thresholdGb = 1L;
        if (freeGb > thresholdGb) {
            return Health.up(Map.of("freeGb", freeGb, "thresholdGb", thresholdGb));
        }
        return Health.down(Map.of("freeGb", freeGb, "thresholdGb", thresholdGb));
    }

    // Aggregate — mirrors /actuator/health response
    static void printHealth() {
        var indicators = Map.of("db", checkDatabase(), "diskSpace", checkDisk());

        boolean allUp = indicators.values().stream()
            .allMatch(h -> h.status() == Status.UP);
        Status overall = allUp ? Status.UP : Status.DOWN;

        System.out.println("GET /actuator/health");
        System.out.println("{");
        System.out.println("  \"status\": \"" + overall + "\",");
        System.out.println("  \"components\": {");
        indicators.forEach((name, health) -> {
            System.out.println("    \"" + name + "\": {");
            System.out.println("      \"status\": \"" + health.status() + "\",");
            System.out.println("      \"details\": " + health.details());
            System.out.println("    }");
        });
        System.out.println("  }");
        System.out.println("}");
        System.out.println();
        System.out.println("HTTP response code: " + (overall == Status.UP ? "200 OK" : "503 Service Unavailable"));
    }

    public static void main(String[] args) {
        printHealth();
    }
}
```

**How to run:** `java ActuatorDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
GET /actuator/health
{
  "status": "UP",
  "components": {
    "db": {
      "status": "UP",
      "details": {database=PostgreSQL, ms=3, query=SELECT 1}
    }
    "diskSpace": {
      "status": "UP",
      "details": {freeGb=42, thresholdGb=1}
    }
  }
}

HTTP response code: 200 OK
```

## 6. Walkthrough

- **`Health` record** — mirrors Spring Boot's `Health` class. An immutable value object with a `Status` enum and a details map.
- **`checkDatabase()`** — simulates what `DataSourceHealthIndicator` does: attempts a lightweight query against the datasource and reports `UP` with query time, or `DOWN` with the error.
- **`checkDisk()`** — mirrors `DiskSpaceHealthIndicator`: checks free space against a threshold.
- **Aggregation logic** — if all component indicators are `UP`, the overall status is `UP`. Any `DOWN` makes the aggregate `DOWN`. Real Spring Boot uses `CompositeHealthContributor` for this, with additional status like `UNKNOWN` and `OUT_OF_SERVICE`.
- **HTTP code** — `200 OK` for `UP`, `503 Service Unavailable` for `DOWN`. Kubernetes liveness probes key off the HTTP status code; a `503` tells Kubernetes to restart the pod.

In a real Spring Boot app, adding `spring-boot-starter-actuator` to `pom.xml` and `management.endpoints.web.exposure.include=health,info,metrics` to `application.properties` is all it takes.

## 7. Gotchas & takeaways

> **All endpoints except `/health` and `/info` are disabled over HTTP by default.** This is intentional — `/actuator/env` shows all property values including secrets, and `/actuator/beans` exposes your app's internals. Always review what you expose. In production, put Actuator behind a separate management port (`management.server.port=8081`) firewalled from the public internet.

> **Health endpoint has two layers:** a simple `{ "status": "UP" }` and a detailed view. The detailed view (with component breakdown) requires `management.endpoint.health.show-details=always` or authenticated access. Never expose full details to anonymous public traffic.

- Add `spring-boot-starter-actuator` and visit `/actuator/health` to instantly see application health.
- Expose additional endpoints via `management.endpoints.web.exposure.include=health,info,metrics,loggers`.
- `/actuator/loggers/{package}` accepts `POST {"configuredLevel":"DEBUG"}` to change log levels live without restart.
- Kubernetes readiness probe: `GET /actuator/health/readiness`, liveness probe: `GET /actuator/health/liveness`.
- Add Micrometer Prometheus registry (`micrometer-registry-prometheus`) to feed `/actuator/prometheus` for Grafana dashboards.
