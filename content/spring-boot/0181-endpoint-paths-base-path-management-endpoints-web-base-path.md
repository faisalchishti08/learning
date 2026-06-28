---
card: spring-boot
gi: 181
slug: endpoint-paths-base-path-management-endpoints-web-base-path
title: Endpoint paths & base path (management.endpoints.web.base-path)
---

## 1. What it is

By default, all Actuator endpoints are nested under `/actuator` — e.g., `/actuator/health`, `/actuator/metrics`. The **base path** is the common prefix before the endpoint ID. You can change it with `management.endpoints.web.base-path`, change an individual endpoint's path segment with `management.endpoints.web.path-mapping.<id>`, or move all management traffic to a dedicated port and path with `management.server.port` and `management.server.base-path`.

## 2. Why & when

**Why change the base path:**
- Conflict: your application already uses `/actuator` for something.
- Security-by-obscurity: change from `/actuator` to something less predictable (not a substitute for auth, but adds a layer).
- API gateway routing: prefix all management traffic with `/mgmt` so gateway rules can route it to an internal target.
- Kubernetes: expose liveness/readiness probes on the same port as the app but under a different path than the app routes.

**Why use a management port:**
- Run business traffic on port 8080 and management on port 8081. The firewall allows 8080 externally but only allows 8081 from the internal monitoring subnet. This eliminates the need for HTTP auth on Actuator.

## 3. Core concept

Key properties:

| Property | Default | Effect |
|---|---|---|
| `management.endpoints.web.base-path` | `/actuator` | Prefix for all endpoint IDs |
| `management.endpoints.web.path-mapping.<id>` | (none) | Rename one endpoint's URL segment |
| `management.server.port` | same as `server.port` | Run management on a different port |
| `management.server.base-path` | `/` | Base path **on the management port** |
| `management.server.address` | (all interfaces) | Bind management to a specific IP |

Setting `management.server.port` causes Spring Boot to spin up a **second embedded server** dedicated to management endpoints. The main server loses access to `/actuator` entirely.

Setting `management.endpoints.web.base-path=/` on the management port (with `management.server.port` set) exposes endpoints directly as `/health`, `/metrics`, etc. — common in platforms that scrape fixed paths.

## 4. Diagram

<svg viewBox="0 0 700 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Main server on port 8080 serves app routes; management server on port 8081 serves actuator under configurable base path">
  <!-- Internet traffic -->
  <rect x="10" y="65" width="110" height="35" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Public traffic</text>

  <line x1="123" y1="82" x2="180" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ppa)"/>

  <!-- Main server -->
  <rect x="185" y="48" width="170" height="68" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="270" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Main Server :8080</text>
  <text x="270" y="85" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/api/**  →  controllers</text>
  <text x="270" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(no /actuator here)</text>

  <!-- Internal traffic -->
  <rect x="10" y="145" width="110" height="35" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="65" y="167" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Monitoring / ops</text>

  <line x1="123" y1="162" x2="180" y2="162" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ppb)"/>

  <!-- Management server -->
  <rect x="185" y="130" width="170" height="68" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Mgmt Server :8081</text>
  <text x="270" y="166" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/mgmt/health</text>
  <text x="270" y="181" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/mgmt/metrics  /mgmt/env</text>

  <!-- Config box -->
  <rect x="395" y="80" width="285" height="85" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="537" y="99" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">application.properties</text>
  <text x="537" y="116" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">management.server.port=8081</text>
  <text x="537" y="131" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">management.server.base-path=/mgmt</text>
  <text x="537" y="146" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">management.endpoints.web.exposure.include=*</text>

  <text x="350" y="205" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">management.server.port isolates Actuator onto a port not reachable from the internet</text>

  <defs>
    <marker id="ppa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ppb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Management traffic on a separate port means the network is the access control; no HTTP auth needed on the management path.

## 5. Runnable example

```java
// EndpointPathsDemo.java — shows how base-path and path-mapping affect endpoint URLs
// How to run: java EndpointPathsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: set management.* properties in application.properties

import java.util.*;

public class EndpointPathsDemo {

    record Config(String basePath, Map<String, String> pathMappings) {}

    static List<String> buildUrls(Config config, List<String> endpointIds) {
        List<String> urls = new ArrayList<>();
        for (String id : endpointIds) {
            String segment = config.pathMappings().getOrDefault(id, id);
            urls.add(config.basePath() + "/" + segment);
        }
        // Discovery root
        urls.add(0, config.basePath());
        return urls;
    }

    static void scenario(String label, String props, Config config, List<String> ids) {
        System.out.println("\n--- " + label + " ---");
        System.out.println("Properties:\n  " + props.replace("\n", "\n  "));
        System.out.println("Resulting paths:");
        buildUrls(config, ids).forEach(u -> System.out.println("  " + u));
    }

    public static void main(String[] args) {
        List<String> ids = List.of("health", "info", "metrics", "env");

        System.out.println("=== Endpoint Paths & Base Path Demo ===");

        // Default
        scenario("Default",
                "# (no override — base-path defaults to /actuator)",
                new Config("/actuator", Map.of()),
                ids);

        // Custom base path
        scenario("Custom base path",
                "management.endpoints.web.base-path=/mgmt",
                new Config("/mgmt", Map.of()),
                ids);

        // Root base path on management port (Prometheus-style)
        scenario("Root base-path on management port (Prometheus scrape)",
                "management.server.port=8081\nmanagement.server.base-path=/",
                new Config("", Map.of()),
                ids);

        // Path mapping — rename individual endpoints
        scenario("Rename health → alive",
                "management.endpoints.web.path-mapping.health=alive",
                new Config("/actuator", Map.of("health", "alive")),
                ids);

        // Both: custom base + rename
        scenario("Custom base + rename env → environment",
                "management.endpoints.web.base-path=/ops\n" +
                "management.endpoints.web.path-mapping.env=environment",
                new Config("/ops", Map.of("env", "environment")),
                ids);

        System.out.println("\n--- Split-port setup summary ---");
        System.out.println("server.port=8080                      # application traffic");
        System.out.println("management.server.port=8081            # ops/monitoring traffic");
        System.out.println("management.server.base-path=/          # paths: /health /metrics etc.");
        System.out.println("management.server.address=127.0.0.1   # bind to loopback only");
    }
}
```

**How to run:** `java EndpointPathsDemo.java`

## 6. Walkthrough

- **Default**: all endpoints under `/actuator/{id}`. The discovery document at `GET /actuator` lists them all.
- **Custom base path**: `management.endpoints.web.base-path=/mgmt` — every endpoint moves to `/mgmt/{id}`. Useful when `/actuator` conflicts with an application route.
- **Root base-path**: `base-path=/` with `management.server.port=8081` gives paths `/health`, `/metrics` directly on port 8081 — common for Prometheus targets that expect fixed paths.
- **Path mapping**: rename just one endpoint (`health` → `alive`) without changing others. Used when gateway rules expect `/alive` as the health check URL.
- **`management.server.address=127.0.0.1`**: binds the management server to loopback only — accessible from the same host (sidecar agent, monitoring agent) but not from the network.

## 7. Gotchas & takeaways

> When `management.server.port` is set, **the main server (`server.port`) no longer serves `/actuator`**. Security rules on the main `SecurityFilterChain` have no effect on management endpoints — the management server uses its own filter chain.

> Setting `management.endpoints.web.base-path=/` without `management.server.port` puts Actuator endpoints at the root of the main server: `/health`, `/metrics`, etc. — they may conflict with application routes.

- `management.server.base-path` only works when `management.server.port` is also set.
- Kubernetes probes point to the pod's IP directly, so they can reach any port; use `management.endpoint.health.probes.enabled=true` and expose `/health/liveness` + `/health/readiness`.
- Prometheus scrape config: `scrape_configs: - metrics_path: /actuator/prometheus` when on the same port.
- The `/actuator` discovery document updates its `href` values when the base path changes — always use the discovery document to find endpoint URLs dynamically.
