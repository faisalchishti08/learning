---
card: spring-boot
gi: 178
slug: built-in-endpoints-list-health-info-metrics-env-beans-mappin
title: "Built-in endpoints list (health, info, metrics, env, beans, mappings, etc.)"
---

## 1. What it is

Spring Boot Actuator ships with **15+ built-in endpoints**, each exposing a different operational view of the running application. The most commonly used are `/actuator/health` (service status), `/actuator/info` (build/git metadata), `/actuator/metrics` (Micrometer counters and timers), `/actuator/env` (resolved environment properties), `/actuator/beans` (Spring bean registry), and `/actuator/mappings` (HTTP route table).

Each endpoint is a self-contained Spring bean; you need no code to enable them — just expose them in configuration.

## 2. Why & when

**`/health`** — used by Kubernetes liveness/readiness probes, load balancers, and on-call dashboards. This is the single most important Actuator endpoint.

**`/info`** — populated by `build-info.properties` (Maven/Gradle plugin) and `git.properties` (git-commit-id plugin). Answers "which version/commit is running?".

**`/metrics`** — Micrometer integration. Core for observability: request counts, latency histograms, JVM heap, DB connection pool sizes, Kafka consumer lag, etc.

**`/env`** — resolves the full property hierarchy. Invaluable for debugging "why is this property value not what I set?".

**`/beans`** — lists every Spring bean, its type, scope, and dependencies. Use when diagnosing "is this bean registered?".

**`/mappings`** — lists every `@RequestMapping` handler. Use when diagnosing 404 or wrong-handler routing.

## 3. Core concept

| Endpoint | Default exposed | HTTP methods | Key use |
|---|---|---|---|
| `health` | yes | GET | Liveness/readiness, sub-system status |
| `info` | yes | GET | Build version, git SHA, custom fields |
| `metrics` | no | GET | Metric names list; `/metrics/{name}` for value |
| `env` | no | GET | Resolved property value + source |
| `beans` | no | GET | Full bean registry |
| `mappings` | no | GET | All HTTP handler mappings |
| `conditions` | no | GET | Auto-config conditions (which fired / why not) |
| `configprops` | no | GET | All `@ConfigurationProperties` bound values |
| `loggers` | no | GET/POST | Read and change log levels at runtime |
| `threaddump` | no | GET | JVM thread dump |
| `heapdump` | no | GET | Binary heap dump (download) |
| `httptrace` | no | GET | Last 100 HTTP request/response pairs |
| `scheduledtasks` | no | GET | All `@Scheduled` task definitions |
| `caches` | no | GET/DELETE | Cache names and entries |
| `shutdown` | no | POST | Graceful shutdown (disabled by default) |

Response format: JSON by default; some endpoints accept `Accept: text/plain`.

## 4. Diagram

<svg viewBox="0 0 720 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Actuator endpoints grouped by concern: health, observability, inspection, and runtime control">
  <!-- /actuator root -->
  <rect x="290" y="88" width="130" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="355" y="113" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator</text>

  <!-- Health group -->
  <line x1="290" y1="100" x2="200" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
  <rect x="60" y="35" width="136" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="128" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Health &amp; Status</text>
  <text x="128" y="67" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/health  /info</text>

  <!-- Observability group -->
  <line x1="310" y1="88" x2="265" y2="38" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
  <rect x="190" y="18" width="136" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="258" y="35" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Observability</text>
  <text x="258" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/metrics  /httptrace  /loggers</text>

  <!-- Inspection group -->
  <line x1="400" y1="88" x2="450" y2="38" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
  <rect x="390" y="18" width="136" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="458" y="35" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Inspection</text>
  <text x="458" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/beans  /env  /mappings  /conditions</text>

  <!-- Runtime control group -->
  <line x1="420" y1="108" x2="545" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#bb)"/>
  <rect x="548" y="48" width="136" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="616" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Runtime Control</text>
  <text x="616" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/loggers (POST)  /shutdown</text>

  <!-- Profiling group -->
  <line x1="355" y1="130" x2="355" y2="162" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ba)"/>
  <rect x="248" y="165" width="218" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="357" y="182" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Profiling</text>
  <text x="357" y="197" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/threaddump  /heapdump  /scheduledtasks</text>

  <defs>
    <marker id="ba" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="bb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Actuator endpoints grouped by concern — health/status, observability, inspection, runtime control, and profiling.

## 5. Runnable example

```java
// ActuatorEndpointsDemo.java — simulates the response format of key Actuator endpoints
// How to run: java ActuatorEndpointsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add starter-actuator; expose endpoints via management.endpoints.web.exposure.include

import java.util.*;

public class ActuatorEndpointsDemo {

    public static void main(String[] args) {
        System.out.println("=== Built-in Actuator Endpoints Demo ===\n");

        // GET /actuator/health
        System.out.println("GET /actuator/health");
        System.out.println("""
                {
                  "status": "UP",
                  "components": {
                    "db":     { "status": "UP", "details": { "database": "PostgreSQL", "validationQuery": "isValid()" } },
                    "redis":  { "status": "UP", "details": { "version": "7.0.8" } },
                    "diskSpace": { "status": "UP", "details": { "total": 499963174912, "free": 123456789 } }
                  }
                }""");

        // GET /actuator/info
        System.out.println("\nGET /actuator/info");
        System.out.println("""
                {
                  "build": { "version": "2.1.0", "artifact": "my-service", "time": "2025-06-01T10:00:00Z" },
                  "git":   { "commit": { "id": "abc1234", "time": "2025-05-30T08:30:00Z" }, "branch": "main" }
                }""");

        // GET /actuator/metrics  (list all metric names)
        System.out.println("\nGET /actuator/metrics");
        System.out.println("""
                {
                  "names": [ "http.server.requests", "jvm.memory.used", "jvm.gc.pause",
                             "process.cpu.usage", "hikaricp.connections.active",
                             "spring.kafka.listener.seconds", "cache.gets" ]
                }""");

        // GET /actuator/metrics/http.server.requests
        System.out.println("\nGET /actuator/metrics/http.server.requests");
        System.out.println("""
                {
                  "name": "http.server.requests",
                  "measurements": [ { "statistic": "COUNT", "value": 4821 },
                                    { "statistic": "TOTAL_TIME", "value": 96.42 },
                                    { "statistic": "MAX",        "value": 0.342 } ],
                  "availableTags": [
                    { "tag": "method", "values": ["GET","POST"] },
                    { "tag": "status", "values": ["200","404","500"] },
                    { "tag": "uri",    "values": ["/api/orders","/api/products"] }
                  ]
                }""");

        // GET /actuator/env/spring.datasource.url  (sanitised)
        System.out.println("\nGET /actuator/env/spring.datasource.url");
        System.out.println("""
                {
                  "property": {
                    "source": "Config resource 'class path resource [application.properties]'",
                    "value": "jdbc:postgresql://db:5432/mydb"
                  }
                }""");

        // POST /actuator/loggers/com.example  (change log level at runtime)
        System.out.println("\nPOST /actuator/loggers/com.example");
        System.out.println("Body: { \"configuredLevel\": \"DEBUG\" }");
        System.out.println("Response: 204 No Content — log level changed at runtime, no restart needed");
    }
}
```

**How to run:** `java ActuatorEndpointsDemo.java` — prints simulated responses for the six most-used endpoints.

## 6. Walkthrough

- **`/health`**: the `components` block appears when `management.endpoint.health.show-details=always`. Each component is a `HealthIndicator` bean. `status` aggregates to the worst sub-status (one `DOWN` → whole status `DOWN`).
- **`/info`**: populated by the Spring Boot Maven/Gradle plugin (`spring-boot:build-info` goal) generating `build-info.properties`, and `git-commit-id-maven-plugin` generating `git.properties`. Zero hand-coded Java.
- **`/metrics`** two-step: first call lists names; second call `/metrics/{name}` returns measurements + available filter tags. Tag filter: `?tag=status:200` narrows to 200 responses only.
- **`/env`** masks sensitive values — any property whose name contains `password`, `secret`, `key`, or `token` is shown as `"****"`. A custom `EnvironmentEndpointWebExtension` can adjust the sanitizer.
- **`/loggers` POST**: changes log level in the live JVM. Survives until restart. The most useful runtime debugging trick with zero redeploy.

## 7. Gotchas & takeaways

> `/actuator/heapdump` **downloads a full JVM heap dump** — potentially gigabytes and containing sensitive data. Never expose this endpoint publicly.

> `/actuator/env` shows **resolved property values including secrets** (unless sanitised). Restrict it to internal networks or authenticated users via Spring Security.

- Enable build info: Maven `<goal>build-info</goal>` in `spring-boot-maven-plugin`; Gradle `bootBuildInfo` task.
- `/actuator/conditions` is the most useful debugging tool for "why didn't auto-config fire?" — check the `negativeMatches` block.
- `/actuator/caches` supports DELETE to evict individual cache entries at runtime — useful during incidents.
- Use `management.info.env.enabled=true` to allow `info.*` properties from `application.properties` to appear in `/actuator/info`.
- Metrics require Micrometer on the classpath — `starter-actuator` includes `micrometer-core`; add `micrometer-registry-prometheus` for Prometheus scraping.
