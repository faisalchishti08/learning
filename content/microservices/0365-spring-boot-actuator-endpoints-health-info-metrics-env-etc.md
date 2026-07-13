---
card: microservices
gi: 365
slug: spring-boot-actuator-endpoints-health-info-metrics-env-etc
title: "Spring Boot Actuator endpoints (health, info, metrics, env, etc.)"
---

## 1. What it is

**Spring Boot Actuator** is a Spring Boot module that exposes a set of ready-made HTTP endpoints for operational visibility into a running application — `/actuator/health` (is the app and its dependencies healthy), `/actuator/info` (build/version metadata), `/actuator/metrics` (application metrics, often exported to Micrometer), `/actuator/env` (current configuration properties), and several more — all wired in automatically just by adding the Actuator dependency, with no custom code required for the basics.

## 2. Why & when

Every service in a microservices system needs at least basic operational visibility — is it up, is it connected to its database, what version is deployed, what's its current configuration — and building this from scratch for every service would be repetitive, error-prone boilerplate. Actuator provides this uniformly: any Spring Boot service that includes the Actuator dependency automatically gets the same set of standard endpoints, in the same format, which is exactly what orchestration platforms (Kubernetes probes), load balancers, and monitoring tools expect to query consistently across every service in a fleet.

Enable Actuator on every Spring Boot service as a baseline. Use `/health` for [liveness and readiness probes](0301-liveness-readiness-probes-via-actuator.md) (already covered in the Resiliency section) that Kubernetes or a load balancer poll to decide whether to route traffic to an instance. Use `/metrics` as the foundation that [Micrometer](0366-micrometer-metrics-facade.md) builds on for exporting to a monitoring backend. Be deliberate about which endpoints are exposed and to whom — `/env` and `/heapdump`, for instance, can leak sensitive configuration or memory contents, so production deployments typically restrict Actuator's more sensitive endpoints to an internal network or require authentication.

## 3. Core concept

Each Actuator endpoint answers a specific operational question by inspecting the running application's own internal state — `/health` aggregates the status of registered `HealthIndicator`s (database connectivity, disk space, custom checks), `/info` surfaces static metadata configured at build time, `/metrics` lists and exposes recorded metric values, `/env` dumps the fully-resolved configuration property sources. Endpoints can be individually enabled, disabled, or restricted via configuration (`management.endpoints.web.exposure.include`).

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics # only expose what's actually needed externally
  endpoint:
    health:
      show-details: when-authorized
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring Boot app with Actuator exposes /health, /info, /metrics, and /env endpoints; Kubernetes queries /health for probes, a monitoring tool queries /metrics, an operator queries /info and /env">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot app + Actuator</text>

  <line x1="280" y1="49" x2="120" y2="90" stroke="#8b949e" marker-end="url(#a365)"/>
  <rect x="20" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/health -&gt; Kubernetes probes</text>

  <line x1="360" y1="49" x2="520" y2="90" stroke="#8b949e" marker-end="url(#a365)"/>
  <rect x="420" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/metrics -&gt; monitoring tool</text>

  <line x1="320" y1="49" x2="320" y2="90" stroke="#8b949e" marker-end="url(#a365)"/>
  <rect x="220" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/info, /env -&gt; operator</text>

  <defs><marker id="a365" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Actuator exposes a uniform set of operational endpoints that different consumers (Kubernetes, monitoring tools, operators) query for different purposes.

## 5. Runnable example

Scenario: a service with hand-rolled, ad-hoc health and metrics endpoints, first shown as inconsistent bespoke code, then rebuilt to mirror Actuator's uniform `/health` and `/info` model with aggregated health indicators, and finally extended to restrict which endpoints are exposed, mirroring production security practice.

### Level 1 — Basic

```java
// File: AdHocHealthEndpoint.java -- a hand-rolled, one-off health check
// with no standard shape -- every service that does this INVENTS its
// own format, inconsistent across the fleet.
import java.util.*;

public class AdHocHealthEndpoint {
    static boolean databaseUp = true;

    static String checkHealth() { // bespoke format -- a DIFFERENT service might return something totally different
        return databaseUp ? "yes we're fine" : "nope, broken";
    }

    public static void main(String[] args) {
        System.out.println("GET /my-custom-health-check -> " + checkHealth());
        System.out.println("Every service inventing its OWN health check format makes automated tooling (Kubernetes, monitoring) hard to build generically.");
    }
}
```

How to run: `java AdHocHealthEndpoint.java`

`checkHealth` returns an arbitrary string with no standard shape — a Kubernetes probe or monitoring tool built to parse this exact wording would break the moment a different service (or even the same service, refactored later) returns a differently-worded response, since there's no shared contract at all.

### Level 2 — Intermediate

```java
// File: ActuatorStyleHealthEndpoint.java -- mirrors Actuator's STANDARD
// /health shape: an aggregated status ("UP"/"DOWN") built from multiple
// named health indicators, in a consistent, predictable structure.
import java.util.*;

public class ActuatorStyleHealthEndpoint {
    interface HealthIndicator { String name(); boolean isHealthy(); }

    static List<HealthIndicator> indicators = List.of(
            new HealthIndicator() { public String name() { return "db"; } public boolean isHealthy() { return true; } },
            new HealthIndicator() { public String name() { return "diskSpace"; } public boolean isHealthy() { return true; } }
    );

    static Map<String, Object> getHealth() { // mirrors the STANDARD Actuator /health JSON shape
        Map<String, String> components = new LinkedHashMap<>();
        boolean overallUp = true;
        for (HealthIndicator ind : indicators) {
            String status = ind.isHealthy() ? "UP" : "DOWN";
            components.put(ind.name(), status);
            if (!ind.isHealthy()) overallUp = false;
        }
        return Map.of("status", overallUp ? "UP" : "DOWN", "components", components);
    }

    public static void main(String[] args) {
        System.out.println("GET /actuator/health -> " + getHealth());
        System.out.println("SAME shape ({status, components}) regardless of WHICH service or WHAT checks it runs -- every service returns THIS structure.");
    }
}
```

How to run: `java ActuatorStyleHealthEndpoint.java`

`getHealth` aggregates every registered `HealthIndicator` into a consistent `{status, components}` structure, exactly mirroring Actuator's real `/health` response shape. Any tool built to parse `{"status": "UP"/"DOWN", "components": {...}}` works identically across every service using this same standard shape, regardless of what specific checks each individual service happens to register.

### Level 3 — Advanced

```java
// File: RestrictedEndpointExposure.java -- mirrors production practice:
// only SOME endpoints are exposed externally (health, info), while
// sensitive ones (env, which can leak secrets/config) are restricted or
// require authorization, exactly like management.endpoints.web.exposure.include.
import java.util.*;

public class RestrictedEndpointExposure {
    static Set<String> exposedEndpoints = Set.of("health", "info"); // mirrors management.endpoints.web.exposure.include
    static Map<String, String> allEndpointsData = Map.of(
            "health", "{\"status\":\"UP\"}",
            "info", "{\"version\":\"1.4.2\"}",
            "env", "{\"DB_PASSWORD\":\"super-secret-value\"}" // SENSITIVE -- must NOT be exposed publicly
    );

    static String requestEndpoint(String endpointName, boolean isInternalNetwork) {
        if (!exposedEndpoints.contains(endpointName) && !isInternalNetwork) {
            return "403 Forbidden -- endpoint '" + endpointName + "' is not exposed externally";
        }
        return "200 OK -- " + allEndpointsData.get(endpointName);
    }

    public static void main(String[] args) {
        System.out.println("External request to /actuator/health: " + requestEndpoint("health", false));
        System.out.println("External request to /actuator/env: " + requestEndpoint("env", false));
        System.out.println("Internal-network request to /actuator/env: " + requestEndpoint("env", true));
        System.out.println("Restricting sensitive endpoints like /env externally is EXACTLY why production configs limit exposure explicitly.");
    }
}
```

How to run: `java RestrictedEndpointExposure.java`

`requestEndpoint` checks whether the requested endpoint is in the `exposedEndpoints` allowlist; if not, it only permits the request when it originates from the internal network (`isInternalNetwork=true`). An external request to `/health` succeeds (it's allowlisted), but an external request to `/env` is rejected with a `403`, since `/env` can leak secrets like database passwords — the exact reason production Spring Boot configurations deliberately restrict which Actuator endpoints are exposed publicly, often keeping sensitive ones accessible only from an internal network or behind additional authorization.

## 6. Walkthrough

Trace `RestrictedEndpointExposure.main` in order. **First**, `requestEndpoint("health", false)` runs: `exposedEndpoints.contains("health")` is `true`, so the `if` condition (`!contains && !isInternalNetwork`) is `false` regardless of the second operand, and the method proceeds to return the actual health data with a `200 OK`.

**Next**, `requestEndpoint("env", false)` runs: `exposedEndpoints.contains("env")` is `false`, so `!contains` is `true`; combined with `!isInternalNetwork` (also `true`, since `isInternalNetwork` is `false`), the full `if` condition is `true` — the method returns a `403 Forbidden` message without ever touching `allEndpointsData.get("env")`.

**Then**, `requestEndpoint("env", true)` runs: `exposedEndpoints.contains("env")` is still `false`, so `!contains` is still `true`, but this time `isInternalNetwork` is `true`, making `!isInternalNetwork` `false` — the overall `&&` condition is now `false`, so the `if` branch is skipped, and the method proceeds to return the actual (sensitive) `env` data.

**Finally**, `main` prints all three results, showing that `/health` is freely accessible externally, `/env` is correctly blocked for external requests, and the same `/env` endpoint is correctly permitted only when the request originates from the internal network — demonstrating exactly the kind of endpoint-level exposure control real Spring Boot Actuator deployments rely on to avoid leaking sensitive configuration data.

```
requestEndpoint(health, external)  -> allowlisted -> 200 OK
requestEndpoint(env, external)     -> NOT allowlisted, NOT internal -> 403 Forbidden
requestEndpoint(env, internal)     -> NOT allowlisted, but IS internal -> 200 OK (sensitive data, restricted access)
```

## 7. Gotchas & takeaways

> Exposing `/actuator/env` or `/actuator/heapdump` without restriction on a public-facing endpoint is a real, well-known security risk — these can leak database passwords, API keys, and other sensitive configuration or memory contents to anyone who can reach the URL. Always explicitly configure `management.endpoints.web.exposure.include` and restrict sensitive endpoints to an internal network or an authenticated management port.

- Spring Boot Actuator provides ready-made, standardized operational endpoints (`/health`, `/info`, `/metrics`, `/env`, and more) automatically, with no custom code needed for the basics.
- This uniformity is exactly what lets orchestration platforms, load balancers, and monitoring tools query every service in a fleet the same way, regardless of what each service internally does.
- `/health` aggregates multiple named health indicators into a consistent `{status, components}` shape; `/metrics` is the foundation [Micrometer](0366-micrometer-metrics-facade.md) builds on for exporting to a monitoring backend.
- Deliberately restrict which endpoints are exposed and to whom — sensitive endpoints like `/env` or `/heapdump` should never be freely accessible on a public-facing network.
