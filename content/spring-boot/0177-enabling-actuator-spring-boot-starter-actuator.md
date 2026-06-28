---
card: spring-boot
gi: 177
slug: enabling-actuator-spring-boot-starter-actuator
title: Enabling Actuator (spring-boot-starter-actuator)
---

## 1. What it is

**Spring Boot Actuator** adds production-ready features to a Spring Boot application: health checks, metrics, environment inspection, thread dumps, HTTP request traces, and more — all accessible over HTTP or JMX. Enabling it is a single dependency: add `spring-boot-starter-actuator` to your build file. That's it — no additional code required.

## 2. Why & when

A running service is a black box without operational visibility. Actuator turns it transparent:
- Ops teams can hit `/actuator/health` to know if the service is up.
- Prometheus scrapes `/actuator/prometheus` for metrics.
- Developers hit `/actuator/beans` to inspect which beans are in the Spring context.

Add Actuator to **every production service**. The overhead is negligible; the visibility is invaluable. You control which endpoints are exposed, so there's no security risk from adding the dependency alone.

## 3. Core concept

Actuator works through **management endpoints** — each is a small component that responds to requests (HTTP or JMX) and reports on some aspect of the application.

When you add `spring-boot-starter-actuator`:
1. Auto-configuration registers all built-in endpoint beans (`HealthEndpoint`, `MetricsEndpoint`, `InfoEndpoint`, etc.).
2. A separate servlet/filter mapping exposes them on the HTTP path `/actuator` (or `/actuator/<id>`).
3. By default, only `/actuator/health` and `/actuator/info` are exposed over HTTP for security. All others are enabled but not exposed — you opt in per endpoint.

Key properties:
- `management.endpoints.web.exposure.include=*` — expose all endpoints over HTTP.
- `management.server.port=8081` — run Actuator on a separate port (common in production: expose only to internal networks).
- `management.endpoints.enabled-by-default=true` — enabled by default; set `false` and enable selectively.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot Actuator: dependency added, auto-config registers endpoints, HTTP exposes them">
  <!-- App -->
  <rect x="10" y="65" width="150" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot App</text>
  <text x="85" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ starter-actuator</text>
  <text x="85" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">auto-config wires</text>
  <text x="85" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">endpoint beans</text>

  <!-- Arrow -->
  <line x1="163" y1="100" x2="228" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#aa)"/>

  <!-- Actuator Layer -->
  <rect x="233" y="40" width="200" height="125" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="333" y="62" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator</text>
  <text x="333" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/health  (exposed)</text>
  <text x="333" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/info    (exposed)</text>
  <text x="333" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/metrics (hidden)</text>
  <text x="333" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/env     (hidden)</text>
  <text x="333" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/beans   (hidden)</text>

  <!-- Consumers -->
  <line x1="436" y1="75" x2="490" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ab)"/>
  <rect x="494" y="50" width="180" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="584" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Load balancer / k8s probe</text>

  <line x1="436" y1="100" x2="490" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ab)"/>
  <rect x="494" y="85" width="180" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="584" y="105" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Prometheus / Grafana</text>

  <line x1="436" y1="130" x2="490" y2="140" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ab)"/>
  <rect x="494" y="125" width="180" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="584" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Developer / ops tooling</text>

  <text x="350" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Default: only /health and /info exposed; opt-in per endpoint or expose all</text>

  <defs>
    <marker id="aa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ab" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

One dependency wires all endpoints; ops teams and monitoring tools query them at runtime.

## 5. Runnable example

```java
// ActuatorEnablingDemo.java — shows what Actuator auto-configures and which endpoints exist
// How to run: java ActuatorEnablingDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-actuator in pom.xml / build.gradle

import java.util.*;

public class ActuatorEnablingDemo {

    // Simulates the endpoint registry that Actuator auto-config builds
    record Endpoint(String id, String path, boolean exposedByDefault, String description) {}

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Actuator — Enabling Demo ===\n");

        List<Endpoint> endpoints = List.of(
            new Endpoint("health",       "/actuator/health",       true,  "Liveness/readiness status"),
            new Endpoint("info",         "/actuator/info",         true,  "Application info from build/git"),
            new Endpoint("metrics",      "/actuator/metrics",      false, "Micrometer metrics"),
            new Endpoint("env",          "/actuator/env",          false, "Environment properties"),
            new Endpoint("beans",        "/actuator/beans",        false, "All Spring beans"),
            new Endpoint("mappings",     "/actuator/mappings",     false, "HTTP handler mappings"),
            new Endpoint("conditions",   "/actuator/conditions",   false, "Auto-config conditions report"),
            new Endpoint("configprops",  "/actuator/configprops",  false, "Bound @ConfigurationProperties"),
            new Endpoint("threaddump",   "/actuator/threaddump",   false, "Current thread dump"),
            new Endpoint("heapdump",     "/actuator/heapdump",     false, "Heap dump download"),
            new Endpoint("loggers",      "/actuator/loggers",      false, "Logger levels (GET/POST)"),
            new Endpoint("httptrace",    "/actuator/httptrace",    false, "Last 100 HTTP exchanges"),
            new Endpoint("prometheus",   "/actuator/prometheus",   false, "Prometheus scrape target"),
            new Endpoint("shutdown",     "/actuator/shutdown",     false, "Graceful shutdown (disabled by default)")
        );

        System.out.println("Dependency: spring-boot-starter-actuator");
        System.out.println("Build: Maven → <dependency>, Gradle → implementation\n");

        System.out.printf("%-14s %-35s %-10s %s%n", "Endpoint ID", "URL", "HTTP Exposed", "Description");
        System.out.println("-".repeat(90));
        endpoints.forEach(e ->
            System.out.printf("%-14s %-35s %-10s %s%n",
                    e.id(), e.path(),
                    e.exposedByDefault() ? "YES (default)" : "no — opt-in",
                    e.description()));

        System.out.println("\n--- Key properties ---");
        System.out.println("management.endpoints.web.exposure.include=*         # expose all");
        System.out.println("management.endpoints.web.exposure.include=health,info,metrics");
        System.out.println("management.server.port=8081                          # separate port");
        System.out.println("management.endpoint.health.show-details=always       # full health output");
        System.out.println("management.endpoint.shutdown.enabled=true            # enable shutdown");
    }
}
```

**How to run:** `java ActuatorEnablingDemo.java` — prints the full endpoint registry and key properties.

## 6. Walkthrough

- The `Endpoint` list mirrors exactly what `ActuatorAutoConfiguration` + `WebMvcActuatorManagementContextConfiguration` register when the starter is present.
- `exposedByDefault=true` for only `health` and `info` — this is a deliberate security posture. `env`, `beans`, and `configprops` could expose secrets.
- `management.server.port=8081` is the production best practice: expose `8080` to the public internet, `8081` only on the internal network (VPC, pod network).
- `management.endpoint.shutdown.enabled=true` must be set explicitly — it's disabled even when `include=*` because triggering it terminates the process.
- `prometheus` endpoint appears only when `micrometer-registry-prometheus` is also on the classpath; the actuator infrastructure is separate from the registry.

## 7. Gotchas & takeaways

> `management.endpoints.web.exposure.include=*` **does not enable disabled endpoints** — it only exposes already-enabled ones over HTTP. `shutdown` is disabled by default; you must set `management.endpoint.shutdown.enabled=true` separately.

> Adding `starter-actuator` in a **reactive WebFlux** app uses `WebFluxActuatorAutoConfiguration` instead of MVC — the endpoints still work but the filter chain differs.

- Maven: `<artifactId>spring-boot-starter-actuator</artifactId>` (no version — managed by Spring Boot BOM).
- Gradle: `implementation 'org.springframework.boot:spring-boot-starter-actuator'`.
- `/actuator` (the discovery endpoint) lists all currently exposed endpoints with their href — useful for tooling.
- For Kubernetes: `management.endpoint.health.probes.enabled=true` exposes `/actuator/health/liveness` and `/actuator/health/readiness` automatically.
- Actuator endpoints work over JMX too — exposed by default on JMX, controllable via `management.endpoints.jmx.exposure.*`.
