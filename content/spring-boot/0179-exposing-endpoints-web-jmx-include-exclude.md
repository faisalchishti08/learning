---
card: spring-boot
gi: 179
slug: exposing-endpoints-web-jmx-include-exclude
title: Exposing endpoints (web/JMX include/exclude)
---

## 1. What it is

A Spring Boot Actuator endpoint has two orthogonal states: **enabled** (the bean exists and can answer queries) and **exposed** (it is accessible over HTTP or JMX). By default all endpoints are enabled but only `health` and `info` are exposed over HTTP. **Exposing** is controlled by `management.endpoints.web.exposure.include/exclude` (HTTP) and `management.endpoints.jmx.exposure.include/exclude` (JMX).

## 2. Why & when

Separating "enabled" from "exposed" gives a defence-in-depth security model:
- `beans`, `env`, and `configprops` can expose internal structure or secrets — keep them disabled over HTTP in production.
- Internal operations (Kubernetes pod-to-pod, ops tooling) can reach a management port not exposed to the public internet.
- JMX exposure is for local tooling (VisualVM, JConsole) or monitoring agents running on the same host.

**Common patterns:**
- Dev: `include=*` — expose everything on localhost.
- Prod (single-port): `include=health,info,prometheus` — minimum needed for monitoring.
- Prod (split-port): expose `*` on `management.server.port=8081`, nothing extra on `8080`.

## 3. Core concept

Four properties control exposure:

```
management.endpoints.web.exposure.include = health,info     # comma-separated or *
management.endpoints.web.exposure.exclude = env,beans       # exclude takes precedence over include
management.endpoints.jmx.exposure.include = *
management.endpoints.jmx.exposure.exclude = shutdown
```

**Precedence rule:** `exclude` beats `include`. `include=*` but `exclude=shutdown` → everything exposed except shutdown.

**Enabling vs exposing:**
```
management.endpoint.shutdown.enabled = true    # enables the bean (default false for shutdown)
management.endpoints.web.exposure.include = shutdown  # exposes it over HTTP
```
Both are needed for sensitive endpoints like `shutdown`.

**JMX:** in Spring Boot 3 JMX exposure defaults to `health` only (Spring Boot 2 defaulted to `*`). Set `spring.jmx.enabled=true` if you need JMX at all.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Enabled endpoints filtered by include/exclude rules before being exposed over HTTP or JMX">
  <!-- All endpoints -->
  <rect x="10" y="50" width="130" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="75" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">All Endpoints</text>
  <text x="75" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">health  info</text>
  <text x="75" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">metrics  env</text>
  <text x="75" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">beans  mappings</text>
  <text x="75" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">conditions loggers</text>
  <text x="75" y="146" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">threaddump  heapdump</text>
  <text x="75" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">shutdown  configprops</text>

  <!-- Arrow to filter -->
  <line x1="143" y1="115" x2="205" y2="115" stroke="#6db33f" stroke-width="2" marker-end="url(#ea)"/>

  <!-- Filter box -->
  <rect x="210" y="75" width="160" height="82" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Exposure Filter</text>
  <text x="290" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">include: health,info,</text>
  <text x="290" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  metrics,prometheus</text>
  <text x="290" y="142" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">exclude: env,shutdown</text>

  <!-- Arrow to HTTP -->
  <line x1="373" y1="95" x2="435" y2="70" stroke="#6db33f" stroke-width="2" marker-end="url(#ea)"/>
  <rect x="440" y="48" width="240" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="67" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP /actuator/*</text>
  <text x="560" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/health  /info  /metrics  /prometheus</text>

  <!-- Arrow to JMX -->
  <line x1="373" y1="140" x2="435" y2="155" stroke="#79c0ff" stroke-width="2" marker-end="url(#eb)"/>
  <rect x="440" y="133" width="240" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JMX MBeans</text>
  <text x="560" y="169" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">include=*  exclude=shutdown</text>

  <text x="350" y="198" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">exclude always beats include; HTTP and JMX have independent include/exclude lists</text>

  <defs>
    <marker id="ea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="eb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

HTTP and JMX have separate include/exclude lists; the filter runs at request time, not at startup.

## 5. Runnable example

```java
// ExposureConfigDemo.java — simulates include/exclude endpoint exposure rules
// How to run: java ExposureConfigDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: set management.endpoints.web.exposure.include/exclude in application.properties

import java.util.*;

public class ExposureConfigDemo {

    static final List<String> ALL_ENDPOINTS = List.of(
            "health", "info", "metrics", "env", "beans", "mappings",
            "conditions", "configprops", "loggers", "threaddump",
            "heapdump", "httptrace", "scheduledtasks", "caches", "shutdown");

    // Simulates Spring Boot's exposure resolution
    static Set<String> resolveExposed(String include, String exclude) {
        Set<String> result = new LinkedHashSet<>();
        // include
        if ("*".equals(include)) {
            result.addAll(ALL_ENDPOINTS);
        } else {
            Arrays.stream(include.split(",")).map(String::trim)
                  .filter(ALL_ENDPOINTS::contains).forEach(result::add);
        }
        // exclude takes precedence
        if (!"".equals(exclude)) {
            Arrays.stream(exclude.split(",")).map(String::trim).forEach(result::remove);
        }
        return result;
    }

    static void printScenario(String label, String include, String exclude) {
        System.out.println("\n--- " + label + " ---");
        System.out.println("include=" + include + "  exclude=" + exclude);
        Set<String> exposed = resolveExposed(include, exclude);
        System.out.println("Exposed (" + exposed.size() + "): " + exposed);
        Set<String> hidden = new LinkedHashSet<>(ALL_ENDPOINTS);
        hidden.removeAll(exposed);
        System.out.println("Hidden  (" + hidden.size() + "): " + hidden);
    }

    public static void main(String[] args) {
        System.out.println("=== Actuator Endpoint Exposure Demo ===");

        printScenario("Default (Spring Boot out-of-box)",
                "health,info", "");

        printScenario("Dev machine — expose everything",
                "*", "");

        printScenario("Prod minimal — monitoring only",
                "health,info,metrics,prometheus", "");

        printScenario("Prod — expose all but sensitive",
                "*", "env,beans,configprops,heapdump,shutdown");

        printScenario("Expose all, exclude shutdown only",
                "*", "shutdown");

        System.out.println("\n--- JMX vs HTTP independence ---");
        System.out.println("HTTP: management.endpoints.web.exposure.include=health,metrics");
        System.out.println("JMX:  management.endpoints.jmx.exposure.include=*");
        System.out.println("=> health and metrics on HTTP; all endpoints on JMX (for local tooling)");
    }
}
```

**How to run:** `java ExposureConfigDemo.java`

## 6. Walkthrough

- **`resolveExposed`** mirrors Spring Boot's `EndpointExposureOutcomeContributor` logic: start from the include set, then subtract the exclude set.
- **`"*"` include**: resolves to all enabled endpoints. In real Spring Boot, disabled endpoints (`shutdown` by default) are not in the pool regardless.
- **Prod minimal**: only the four endpoints monitoring systems need. `/prometheus` requires `micrometer-registry-prometheus`.
- **Prod — expose all but sensitive**: `*` minus `env, beans, configprops, heapdump, shutdown` leaves useful endpoints (metrics, loggers, mappings) while hiding data-leak risks.
- **JMX independence**: HTTP and JMX are controlled separately. You can have JMX fully open for local ops tooling while HTTP is locked down to `health` + `metrics` only.

## 7. Gotchas & takeaways

> `management.endpoints.web.exposure.include=*` **does NOT expose `shutdown`** — because `shutdown` is *disabled* (not just hidden). Set `management.endpoint.shutdown.enabled=true` first, then add it to the include list.

> In Spring Boot 3, the default JMX exposure changed from `*` to `health` only. If your monitoring relied on JMX MBeans for other endpoints, add `management.endpoints.jmx.exposure.include=*` explicitly.

- Wildcard `*` in YAML must be quoted: `include: "*"` (bare `*` is a YAML alias character).
- Exclude beats include: `include=*,exclude=env` safely hides `env` even when `*` is set.
- `management.server.port=8081` + firewall rule is the safest production pattern — expose `*` on the management port but block it from public traffic.
- `management.endpoint.<id>.enabled=false` disables a specific endpoint entirely (removes the bean); useful to disable even JMX access.
- Check currently exposed endpoints: `GET /actuator` returns a HAL JSON document listing all exposed endpoints and their hrefs.
