---
card: spring-boot
gi: 203
slug: cloud-foundry-support
title: Cloud Foundry support
---

## 1. What it is

When a Spring Boot application runs on **Cloud Foundry (CF)**, Actuator auto-configures Cloud Foundry-specific behaviour. CF's platform exposes its own `management` API endpoints under `/{contextPath}/cloudfoundryapplication` that CF security can access. Spring Boot maps its Actuator endpoints to this path and handles CF-specific token-based authorization automatically. The CF platform uses these endpoints for health checking, app instance management, and the Apps Manager UI.

## 2. Why & when

Cloud Foundry needs to reach Actuator endpoints to:
1. **Health check** the app (CF replaces unhealthy instances automatically).
2. **Show app details** in Apps Manager (memory, CPU, heap, environment).
3. **Manage instances** — stop, restart, or scale.

Without the CF-specific integration, Apps Manager can't display live metrics or perform management actions. The integration is automatic — no configuration needed when running on CF. It also handles the CF UAA (User Account and Authentication) JWT token validation that secures the management API.

## 3. Core concept

CF integration adds a separate management endpoint at `/{app-root}/cloudfoundryapplication` in addition to the standard `/actuator` path:

| Path | Purpose |
|---|---|
| `/cloudfoundryapplication` | CF platform endpoint — secured by CF JWT tokens |
| `/actuator` | Standard Spring Boot Actuator — secured by your app's security |

**All built-in Actuator endpoints** are exposed on the CF path by default (unlike the standard path which exposes only `health` and `info` by default).

Key properties:
```properties
# Disable CF integration (e.g., in dev when running CF locally):
management.cloudfoundry.enabled=false
# Skip SSL validation (for CF in development with self-signed certs):
management.cloudfoundry.skip-ssl-validation=true
```

CF sets these environment variables automatically at runtime:
- `VCAP_APPLICATION` — app metadata (name, id, CF instance index, URIs).
- `VCAP_SERVICES` — bound service credentials (DB, message broker, etc.).

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CF Router sends traffic to Spring Boot app; CF Platform accesses /cloudfoundryapplication with UAA JWT; Apps Manager reads health and metrics; standard /actuator remains for operator access">
  <!-- CF Platform -->
  <rect x="10" y="20" width="145" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="82" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Cloud Foundry</text>
  <text x="82" y="56" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Apps Manager</text>
  <text x="82" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">health / metrics</text>
  <text x="82" y="84" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Platform API</text>
  <text x="82" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instance management</text>

  <!-- CF arrow to CF endpoint -->
  <line x1="157" y1="55" x2="250" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cfa)"/>
  <text x="205" y="63" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">UAA JWT token</text>

  <!-- Spring Boot App -->
  <rect x="255" y="30" width="255" height="145" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="382" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot App (on CF)</text>

  <!-- CF endpoint inside -->
  <rect x="272" y="62" width="220" height="40" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="382" y="79" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/cloudfoundryapplication/**</text>
  <text x="382" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">all endpoints, CF JWT auth</text>

  <!-- Standard actuator inside -->
  <rect x="272" y="112" width="220" height="40" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="382" y="129" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/**</text>
  <text x="382" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">your app's security (health, info default)</text>

  <!-- CF Router / User traffic -->
  <rect x="10" y="140" width="145" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82" y="158" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CF Router</text>
  <text x="82" y="172" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">user / API traffic</text>

  <line x1="157" y1="160" x2="253" y2="132" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cfb)"/>

  <!-- VCAP env vars -->
  <rect x="525" y="55" width="145" height="65" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="597" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">CF Environment</text>
  <text x="597" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">VCAP_APPLICATION</text>
  <text x="597" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">VCAP_SERVICES</text>
  <text x="597" y="117" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(auto-injected by CF)</text>

  <line x1="512" y1="82" x2="527" y2="82" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#cfb)"/>

  <defs>
    <marker id="cfa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="cfb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

CF platform accesses `/cloudfoundryapplication` with UAA tokens; your app's `/actuator` remains governed by your own security configuration.

## 5. Runnable example

```java
// CloudFoundryDemo.java — simulates CF environment variable parsing and endpoint routing
// How to run: java CloudFoundryDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot on CF: no configuration needed; CF integration is auto-configured

import java.util.*;

public class CloudFoundryDemo {

    // Simulates VCAP_APPLICATION parsing
    record VcapApplication(String name, String id, int instanceIndex, List<String> uris, String spaceId) {}

    // Simulates a bound service from VCAP_SERVICES
    record VcapService(String name, String label, String plan, Map<String, String> credentials) {}

    static VcapApplication parseVcapApplication(Map<String, String> env) {
        // In real Spring Boot, spring-boot-starter-cloud-connectors / CloudFoundryConnector handles this
        // VCAP_APPLICATION is a JSON object injected by CF at container start
        return new VcapApplication(
            env.getOrDefault("app_name", "unknown"),
            env.getOrDefault("application_id", "?"),
            Integer.parseInt(env.getOrDefault("instance_index", "0")),
            List.of(env.getOrDefault("application_uris", "").split(",")),
            env.getOrDefault("space_id", "?")
        );
    }

    // Simulates CF JWT token validation (Spring Boot handles this automatically)
    static boolean validateCfToken(String token, String appId) {
        // In real CF: validates UAA JWT, checks 'application_id' claim matches this app
        return token.startsWith("Bearer ") && token.contains(appId);
    }

    // Simulates CF endpoint routing
    static String routeRequest(String path, String token, String appId, boolean cfEnabled) {
        if (path.startsWith("/cloudfoundryapplication")) {
            if (!cfEnabled) return "404 Not Found (CF integration disabled)";
            if (!validateCfToken(token, appId)) return "401 Unauthorized (invalid CF token)";
            String endpoint = path.replace("/cloudfoundryapplication/", "");
            return "200 OK [CF] endpoint=" + endpoint + " (all actuators exposed)";
        } else if (path.startsWith("/actuator")) {
            boolean isPublic = path.equals("/actuator/health") || path.equals("/actuator/info");
            return isPublic ? "200 OK endpoint=" + path.replace("/actuator/","") :
                    "401 Unauthorized (requires app security role)";
        }
        return "200 OK (application traffic)";
    }

    public static void main(String[] args) {
        System.out.println("=== Cloud Foundry Support Demo ===\n");

        // Simulate CF environment variables
        Map<String, String> vcapApp = new LinkedHashMap<>();
        vcapApp.put("app_name", "order-service");
        vcapApp.put("application_id", "abc-123-def-456");
        vcapApp.put("instance_index", "0");
        vcapApp.put("application_uris", "order-service.cfapps.io,order.example.com");
        vcapApp.put("space_id", "space-xyz-789");

        VcapApplication app = parseVcapApplication(vcapApp);
        System.out.println("VCAP_APPLICATION parsed:");
        System.out.println("  name:          " + app.name());
        System.out.println("  application_id:" + app.id());
        System.out.println("  instance_index:" + app.instanceIndex());
        System.out.println("  uris:          " + app.uris());
        System.out.println("  space_id:      " + app.spaceId());

        // VCAP_SERVICES
        VcapService db = new VcapService("mydb", "p.mysql", "small-100mb",
                Map.of("uri","mysql://user:pass@host:3306/mydb","username","user"));
        System.out.println("\nVCAP_SERVICES bound services:");
        System.out.printf("  %s (%s %s)  credentials.uri=%s%n",
                db.name(), db.label(), db.plan(), db.credentials().get("uri"));

        // Route simulation
        System.out.println("\n--- Request routing ---");
        String appId   = "abc-123-def-456";
        String cfToken = "Bearer abc-123-def-456-valid-jwt";
        String badToken = "Bearer wrong-token";
        boolean cfEnabled = true;

        String[][] reqs = {
            {"/api/orders",                       "",         "User traffic"},
            {"/actuator/health",                  "",         "Public actuator (allowed)"},
            {"/actuator/env",                     "",         "Secured actuator (blocked)"},
            {"/cloudfoundryapplication/health",   cfToken,    "CF platform health check"},
            {"/cloudfoundryapplication/metrics",  cfToken,    "CF platform metrics"},
            {"/cloudfoundryapplication/env",      cfToken,    "CF platform env (all endpoints exposed)"},
            {"/cloudfoundryapplication/health",   badToken,   "CF bad token"},
        };

        for (String[] r : reqs) {
            System.out.printf("  %-48s => %s%n", r[0], routeRequest(r[0], r[1], appId, cfEnabled));
        }

        System.out.println("\n--- Disable CF integration ---");
        System.out.println("management.cloudfoundry.enabled=false");
        System.out.println("  => " + routeRequest("/cloudfoundryapplication/health", cfToken, appId, false));

        System.out.println("\n--- application.properties ---");
        System.out.println("# skip SSL validation for CF development env:");
        System.out.println("management.cloudfoundry.skip-ssl-validation=true");
        System.out.println("# disable CF integration entirely:");
        System.out.println("management.cloudfoundry.enabled=false");
    }
}
```

**How to run:** `java CloudFoundryDemo.java`

## 6. Walkthrough

- **`parseVcapApplication`**: in a real CF container, `VCAP_APPLICATION` is a JSON string. Spring Boot reads it via the CF environment post-processors and makes it available via `@Value("${vcap.application.name}")`.
- **`VCAP_SERVICES`**: Spring Boot auto-configures DataSource, Redis, RabbitMQ, etc. from bound CF services using `spring-cloud-connectors` or Spring Boot's CF-specific auto-configuration. Credentials come from this JSON.
- **`routeRequest`**: shows that `/cloudfoundryapplication/**` exposes **all** Actuator endpoints (not just `health` and `info`), secured by CF's UAA JWT. The `/actuator/**` path remains under your own security rules.
- **Invalid CF token**: returns `401` — CF's platform will mark the app instance as unhealthy if this check fails.
- The properties at the end are for the rare cases where you need to adjust CF integration behavior.

## 7. Gotchas & takeaways

> CF integration is **enabled by default** when `spring-boot-starter-actuator` is on the classpath and the app detects it is running on CF (by checking for `VCAP_APPLICATION`). If you run locally with the CF env vars set, CF security will be active — use `management.cloudfoundry.enabled=false` to turn it off locally.

> The `/cloudfoundryapplication` path exposes **all built-in Actuator endpoints** regardless of your `management.endpoints.web.exposure.include` setting. This is intentional — the CF platform needs full access. Protect this by ensuring CF's UAA token validation is intact (never set `skip-ssl-validation=true` in production).

- `VCAP_APPLICATION` and `VCAP_SERVICES` are available as Spring Boot properties: `${vcap.application.name}`, `${vcap.services.mydb.credentials.uri}`.
- CF health checks use the `/cloudfoundryapplication/health` endpoint; ensure `management.health.defaults.enabled=true`.
- Spring Boot auto-configures DataSource, Redis, and RabbitMQ from `VCAP_SERVICES` bindings without any code change.
