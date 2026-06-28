---
card: spring-boot
gi: 182
slug: cors-for-endpoints
title: CORS for endpoints
---

## 1. What it is

**CORS (Cross-Origin Resource Sharing)** for Actuator endpoints controls which browser origins can make cross-origin requests to the management endpoints. Spring Boot Actuator has its own CORS configuration separate from the main application's CORS settings — configured via `management.endpoints.web.cors.*` properties. It is disabled by default; adding `allowed-origins` enables it.

## 2. Why & when

Actuator endpoints are typically consumed by server-side monitoring tools (Prometheus, Grafana agent, ops scripts) over HTTP — these are not browser requests and CORS does not apply to them. CORS only matters when a **browser-based dashboard** (a React/Angular monitoring UI running at a different origin) calls Actuator endpoints directly from JavaScript.

**When to enable:**
- You have an internal web dashboard at `https://ops.internal` that calls `https://myservice:8081/actuator/health` via `fetch()`.
- You are building a custom developer tool that runs in the browser and reads metrics directly.

**When to leave disabled:**
- All your Actuator consumers are server-to-server (Prometheus, ops scripts, k8s probes) — no CORS needed.
- You proxy Actuator traffic through a backend (backend-for-frontend pattern) — CORS is on the proxy, not Actuator.

## 3. Core concept

Actuator CORS is configured via properties (not a `WebMvcConfigurer`):

```properties
management.endpoints.web.cors.allowed-origins=https://ops.internal
management.endpoints.web.cors.allowed-methods=GET,POST
management.endpoints.web.cors.allowed-headers=*
management.endpoints.web.cors.allow-credentials=true
management.endpoints.web.cors.max-age=1800
```

These properties wire a `CorsConfiguration` onto the `WebMvcEndpointHandlerMapping` (or `WebFluxEndpointHandlerMapping` in reactive apps) that serves Actuator endpoints — separate from any CORS you configure for your application controllers via `@CrossOrigin` or `WebMvcConfigurer.addCorsMappings`.

Key points:
- `allowed-origins` is **required** to enable CORS — without it, all cross-origin requests are blocked.
- `allow-credentials=true` requires a specific origin list, not `*` (browser security restriction).
- Applies to **all exposed** Actuator endpoints; you cannot set CORS per endpoint via properties.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser at ops.internal sends preflight OPTIONS then GET to actuator; CORS header allows or denies">
  <!-- Browser -->
  <rect x="10" y="65" width="120" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="70" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ops.internal</text>
  <text x="70" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fetch('/actuator/health')</text>

  <!-- Preflight -->
  <line x1="133" y1="85" x2="268" y2="85" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#cra)"/>
  <text x="200" y="78" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">OPTIONS (preflight)</text>

  <!-- Actuator CORS handler -->
  <rect x="273" y="52" width="220" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="383" y="74" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Actuator CORS Config</text>
  <text x="383" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">allowed-origins: ops.internal</text>
  <text x="383" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">allowed-methods: GET,POST</text>
  <text x="383" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(management.endpoints.web.cors.*)</text>

  <!-- Response with CORS header -->
  <line x1="273" y1="100" x2="138" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#crb)"/>
  <text x="205" y="117" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Access-Control-Allow-Origin: ops.internal</text>

  <!-- Actual GET -->
  <line x1="133" y1="122" x2="268" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cra)"/>
  <text x="200" y="135" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">GET /actuator/health</text>

  <!-- Response -->
  <line x1="273" y1="130" x2="138" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#crb)"/>
  <text x="200" y="148" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">200 OK {"status":"UP"}</text>

  <!-- Blocked origin -->
  <rect x="510" y="65" width="170" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="595" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">malicious.io</text>
  <text x="595" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fetch('/actuator/env')</text>
  <text x="595" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ browser blocks (no CORS header)</text>

  <text x="350" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Browser enforces CORS; Prometheus/curl are not browsers and ignore CORS headers entirely</text>

  <defs>
    <marker id="cra" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="crb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The browser sends a preflight OPTIONS; Actuator responds with the CORS allow-origin header; browser proceeds or blocks.

## 5. Runnable example

```java
// ActuatorCorsDemo.java — simulates CORS preflight and actual request validation
// How to run: java ActuatorCorsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: set management.endpoints.web.cors.* properties

import java.util.*;

public class ActuatorCorsDemo {

    // Simulated Actuator CORS configuration
    static final Set<String> allowedOrigins = Set.of("https://ops.internal", "https://grafana.internal");
    static final Set<String> allowedMethods = Set.of("GET", "POST");
    static final boolean allowCredentials = true;
    static final int maxAge = 1800;

    // Simulate CORS preflight check (browser sends OPTIONS before the real request)
    static Map<String, String> handlePreflight(String origin, String requestMethod) {
        Map<String, String> responseHeaders = new LinkedHashMap<>();
        if (!allowedOrigins.contains(origin)) {
            System.out.printf("  [CORS] BLOCKED — origin '%s' not in allowed list%n", origin);
            return responseHeaders; // no CORS headers → browser blocks
        }
        if (!allowedMethods.contains(requestMethod)) {
            System.out.printf("  [CORS] BLOCKED — method '%s' not allowed%n", requestMethod);
            return responseHeaders;
        }
        responseHeaders.put("Access-Control-Allow-Origin", origin);
        responseHeaders.put("Access-Control-Allow-Methods", String.join(",", allowedMethods));
        responseHeaders.put("Access-Control-Allow-Credentials", String.valueOf(allowCredentials));
        responseHeaders.put("Access-Control-Max-Age", String.valueOf(maxAge));
        System.out.printf("  [CORS] OK — origin '%s' allowed for %s%n", origin, requestMethod);
        return responseHeaders;
    }

    static void request(String origin, String method, String path) {
        System.out.printf("%nRequest: %s %s  (Origin: %s)%n", method, path, origin);
        // 1. Preflight
        System.out.println("  Preflight OPTIONS:");
        Map<String, String> headers = handlePreflight(origin, method);
        if (headers.isEmpty()) {
            System.out.println("  Browser blocks request (no CORS response headers)");
            return;
        }
        // 2. Actual request proceeds
        System.out.println("  Actual request: 200 OK");
        System.out.println("  Response CORS headers: " + headers);
    }

    public static void main(String[] args) {
        System.out.println("=== Actuator CORS Demo ===");
        System.out.println("\nAllowed origins: " + allowedOrigins);
        System.out.println("Allowed methods: " + allowedMethods);

        request("https://ops.internal",     "GET",  "/actuator/health");
        request("https://grafana.internal", "GET",  "/actuator/metrics");
        request("https://malicious.io",     "GET",  "/actuator/env");      // blocked
        request("https://ops.internal",     "DELETE", "/actuator/caches"); // blocked (method)
        request("https://ops.internal",     "POST", "/actuator/loggers/com.example");

        System.out.println("\n--- Properties for this config ---");
        System.out.println("management.endpoints.web.cors.allowed-origins=https://ops.internal,https://grafana.internal");
        System.out.println("management.endpoints.web.cors.allowed-methods=GET,POST");
        System.out.println("management.endpoints.web.cors.allow-credentials=true");
        System.out.println("management.endpoints.web.cors.max-age=1800");
        System.out.println("\nNote: CORS is irrelevant for Prometheus/curl — they are not browsers.");
    }
}
```

**How to run:** `java ActuatorCorsDemo.java`

## 6. Walkthrough

- **`handlePreflight`** simulates the `DefaultCorsProcessor` Spring uses for Actuator endpoints. It checks origin against the allowed list and method against allowed methods.
- **`ops.internal GET /health`**: passes both checks — CORS headers returned; browser proceeds.
- **`malicious.io GET /env`**: origin not in list — no CORS headers; browser blocks the request before it even reaches the server. Note: a `curl` command from `malicious.io` would still succeed because `curl` is not a browser and ignores CORS.
- **`ops.internal DELETE /caches`**: origin allowed but `DELETE` is not in `allowedMethods` — preflight rejected.
- **`max-age=1800`**: browser caches the preflight result for 30 minutes — subsequent same-origin/method requests skip the OPTIONS round trip.

## 7. Gotchas & takeaways

> CORS is a **browser security mechanism** — it has zero effect on curl, Prometheus, k8s probes, or any non-browser client. Do not rely on CORS as a security control for server-to-server calls.

> `allowed-origins=*` with `allow-credentials=true` is **invalid** — browsers refuse this combination. Use a specific origin list when credentials are needed.

- These properties configure CORS specifically for Actuator's `WebMvcEndpointHandlerMapping`. Your application's `WebMvcConfigurer.addCorsMappings` does NOT apply to Actuator.
- `management.endpoints.web.cors.allowed-origin-patterns=https://*.internal` — Spring 5.3+ supports wildcard patterns as an alternative to `allowed-origins`.
- If you expose Actuator on `management.server.port` and serve the browser dashboard separately, CORS applies because the ports differ (different origin).
- In reactive (WebFlux) apps, the same `management.endpoints.web.cors.*` properties configure `WebFluxEndpointHandlerMapping` CORS automatically.
