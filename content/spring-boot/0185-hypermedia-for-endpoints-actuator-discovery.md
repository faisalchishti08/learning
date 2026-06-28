---
card: spring-boot
gi: 185
slug: hypermedia-for-endpoints-actuator-discovery
title: Hypermedia for endpoints (/actuator discovery)
---

## 1. What it is

When you request `GET /actuator` (the Actuator base path), Spring Boot returns a **HAL (Hypertext Application Language) JSON document** listing all currently exposed endpoints and their full URLs. This is Actuator's built-in **discovery mechanism** — instead of hard-coding `/actuator/health`, clients can discover the correct URL dynamically from the root document.

Spring Boot adds the HAL browser dependency automatically when `spring-boot-starter-actuator` is present alongside `spring-hateoas`.

## 2. Why & when

**Why hypermedia for Actuator:**
- Operational tools and scripts that consume Actuator should query the discovery document first, then follow `_links` — this way they remain correct even if the base path or individual endpoint paths change.
- Kubernetes health checks are pinned to specific paths by the platform; for other consumers (dashboards, ops scripts), discovery is more robust.

**When it matters:**
- You change `management.endpoints.web.base-path` or rename endpoints via `path-mapping` — scripts using hard-coded `/actuator/health` break; scripts using the discovery document adapt automatically.
- You build tooling that supports multiple Spring Boot services with different configurations.

**When it doesn't matter:**
- Prometheus scrape configs need a fixed path (`/actuator/prometheus`) and can't follow links.
- Kubernetes probes need `/actuator/health/liveness` exactly.

## 3. Core concept

`GET /actuator` returns:

```json
{
  "_links": {
    "self": { "href": "http://localhost:8080/actuator", "templated": false },
    "health": { "href": "http://localhost:8080/actuator/health", "templated": false },
    "health-path": { "href": "http://localhost:8080/actuator/health/{*path}", "templated": true },
    "info": { "href": "http://localhost:8080/actuator/info", "templated": false },
    "metrics": { "href": "http://localhost:8080/actuator/metrics", "templated": false },
    "metrics-requiredMetricName": { "href": "http://localhost:8080/actuator/metrics/{requiredMetricName}", "templated": true }
  }
}
```

Key points:
- The `self` link is the discovery root.
- `"templated": true` means the URL contains a URI template variable (`{path}`, `{name}`) — clients must substitute the variable.
- The HAL format (`_links`) is the default; `spring-hateoas` on the classpath enables the HAL browser UI.
- Only **exposed** endpoints appear in the discovery document.
- `EndpointRequest.toLinks()` in Spring Security targets this discovery root path (for auth rules).

## 4. Diagram

<svg viewBox="0 0 720 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client fetches GET /actuator discovery document, receives _links map, then follows hrefs to specific endpoints">
  <!-- Client -->
  <rect x="10" y="75" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="65" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client</text>
  <text x="65" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ops script / tool</text>

  <!-- Step 1: discover -->
  <line x1="123" y1="90" x2="228" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hma)"/>
  <text x="175" y="83" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">1. GET /actuator</text>

  <!-- Actuator root -->
  <rect x="233" y="55" width="220" height="95" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="343" y="76" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator (HAL)</text>
  <text x="343" y="94" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">_links.health.href</text>
  <text x="343" y="109" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">_links.metrics.href</text>
  <text x="343" y="124" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">_links.info.href</text>
  <text x="343" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(only exposed endpoints)</text>

  <!-- Response back -->
  <line x1="233" y1="107" x2="137" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hmb)"/>
  <text x="185" y="120" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">2. returns _links map</text>

  <!-- Step 3: follow links -->
  <line x1="123" y1="118" x2="228" y2="138" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#hma)"/>
  <text x="175" y="145" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">3. follow href from _links</text>

  <!-- Specific endpoints -->
  <rect x="458" y="45" width="245" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="580" y="64" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Specific Endpoints</text>
  <text x="580" y="82" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health  → {"status":"UP"}</text>
  <text x="580" y="99" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/metrics → {"names":[...]}</text>
  <text x="580" y="116" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/info    → {"build":{...}}</text>
  <line x1="457" y1="100" x2="456" y2="100"/>
  <line x1="456" y1="100" x2="456" y2="100"/>

  <line x1="456" y1="100" x2="460" y2="100" stroke="#6db33f" stroke-width="1"/>
  <line x1="453" y1="100" x2="456" y2="100" stroke="#6db33f" stroke-width="1" marker-end="url(#hmb)"/>

  <!-- arrow from actuator root to specific endpoints -->
  <line x1="456" y1="100" x2="458" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hmb)"/>

  <text x="360" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Clients that discover dynamically remain correct when paths change</text>

  <defs>
    <marker id="hma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="hmb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Fetch the discovery document first, then follow `_links` — the document self-updates when endpoints are added or paths change.

## 5. Runnable example

```java
// ActuatorDiscoveryDemo.java — simulates the /actuator HAL discovery document
// How to run: java ActuatorDiscoveryDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: GET /actuator returns this structure automatically

import java.util.*;

public class ActuatorDiscoveryDemo {

    record Link(String href, boolean templated) {}

    // Simulate building the discovery document from exposed endpoints
    static Map<String, Link> buildDiscoveryDocument(String basePath, List<String> exposedIds,
                                                     Map<String, String> pathMappings) {
        Map<String, Link> links = new LinkedHashMap<>();
        // self link
        links.put("self", new Link(basePath, false));

        for (String id : exposedIds) {
            String segment = pathMappings.getOrDefault(id, id);
            String href = basePath + "/" + segment;
            links.put(id, new Link(href, false));

            // Endpoints with @Selector produce a templated link too
            if (Set.of("health", "metrics", "loggers", "caches", "features").contains(id)) {
                links.put(id + "-path", new Link(href + "/{*path}", true));
            }
        }
        return links;
    }

    static void printDiscovery(String scenario, String basePath, List<String> exposed,
                                Map<String, String> pathMappings) {
        System.out.println("\n--- " + scenario + " ---");
        Map<String, Link> doc = buildDiscoveryDocument(basePath, exposed, pathMappings);
        System.out.println("GET " + basePath);
        System.out.println("{");
        System.out.println("  \"_links\": {");
        doc.forEach((key, link) ->
            System.out.printf("    \"%s\": { \"href\": \"%s\", \"templated\": %s },%n",
                    key, link.href(), link.templated()));
        System.out.println("  }");
        System.out.println("}");
    }

    public static void main(String[] args) {
        System.out.println("=== Actuator Discovery (/actuator HAL document) Demo ===");

        // Default Spring Boot setup
        printDiscovery("Default (health, info exposed)",
                "http://localhost:8080/actuator",
                List.of("health", "info"),
                Map.of());

        // All endpoints exposed
        printDiscovery("All endpoints exposed",
                "http://localhost:8080/actuator",
                List.of("health", "info", "metrics", "loggers", "features"),
                Map.of());

        // Custom base path + renamed health
        printDiscovery("Custom base path + health renamed to alive",
                "http://localhost:8080/mgmt",
                List.of("health", "info", "metrics"),
                Map.of("health", "alive"));

        System.out.println("\n--- Client discovery pattern ---");
        System.out.println("1. GET /actuator                        → receive _links");
        System.out.println("2. Extract _links.health.href           → 'http://host/actuator/health'");
        System.out.println("3. GET <href>                           → { status: UP }");
        System.out.println("=> Client survives base-path and rename changes");
    }
}
```

**How to run:** `java ActuatorDiscoveryDemo.java`

## 6. Walkthrough

- **`buildDiscoveryDocument`** mirrors what `WebMvcEndpointHandlerMapping` returns at `GET /actuator`. It builds a `_links` map where each key is the endpoint `id` and the value is the absolute `href`.
- **Templated links**: endpoints that accept a `@Selector` parameter (health components, metric names) get two entries: a non-templated base URL and a templated URL with `{*path}` for dynamic segments.
- **Custom base path scenario**: when `management.endpoints.web.base-path=/mgmt`, the discovery document still works — the hrefs reflect the actual configured path. Clients using the discovery document just follow the new href.
- **Renamed endpoint**: `health` → `alive` (via `path-mapping.health=alive`) — the discovery document updates the href to `/mgmt/alive`; hard-coded clients break, discovery-based clients don't.

## 7. Gotchas & takeaways

> The discovery document only lists **currently exposed** endpoints. If you add a new endpoint mid-process (via `management.endpoints.web.exposure.include` change + context refresh), the document updates dynamically.

> HAL browser (`/actuator` rendered as HTML with navigation) requires `spring-hateoas` on the classpath AND the `application/hal+json` content type. A plain `Accept: application/json` request gets the same data without the browser UI.

- `EndpointRequest.toLinks()` in a `SecurityFilterChain` matches the discovery path — you can permit it without auth while still requiring auth for the actual endpoints.
- `management.endpoints.web.discovery.enabled=false` disables the discovery document if you don't want the `GET /actuator` root to be accessible.
- Templated links follow RFC 6570 URI templates — clients should use a URI template library to substitute variables safely.
- The `self` link always reflects the current base path — use it to verify your configuration is correct after deployment.
