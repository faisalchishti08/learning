---
card: spring-cloud
gi: 23
slug: health-indicator-security
title: "Health indicator & security"
---

## 1. What it is

The Config Server exposes its own health status through a dedicated `ConfigServerHealthIndicator` — surfaced via Spring Boot Actuator's `/actuator/health` endpoint — reporting whether it can actually reach its backend (a Git remote, Vault, a database) for at least one configured application. Separately, since Config Server exposes potentially sensitive configuration over HTTP by default, it needs its own access control layered on, typically via Spring Security.

```yaml
management:
  endpoint:
    health:
      show-details: always
spring:
  cloud:
    config:
      server:
        health:
          repositories:
            payment-service:
              label: main
```

## 2. Why & when

The earlier cards described the Config Server as answering "what's the config for X" correctly — this card addresses two operational concerns that don't show up until the server is actually running in production: is it *healthy* (can it reach its backend right now), and is it *secure* (can only authorized clients reach it at all). Both are easy to overlook when first setting up a Config Server locally, since local development rarely surfaces backend connectivity failures or unauthorized access attempts.

Reach for Config Server health and security configuration when:

- Deploying a Config Server to production — an unreachable backend should be visible in health checks (and ideally alerting) before it causes every dependent service's startup to fail mysteriously.
- Exposing the Config Server's HTTP endpoints beyond a fully trusted internal network — authentication is not optional once the server is reachable by anything other than known, trusted clients.
- Diagnosing why a specific application's configuration requests are failing — the health indicator can be scoped to check specific `{application}/{label}` combinations, not just generic backend reachability.

## 3. Core concept

```
 GET /actuator/health
 -> { "status": "UP", "components": { "configServer": { "status": "UP", "details": { "repositories": [...] } } } }

 GET /actuator/health   (Git remote is unreachable)
 -> { "status": "DOWN", "components": { "configServer": { "status": "DOWN", "details": { "error": "..." } } } }

 WITHOUT security:
   GET /payment-service/production  -> 200 OK, full config, ANYONE who can reach the port

 WITH Spring Security configured:
   GET /payment-service/production  (no credentials) -> 401 Unauthorized
   GET /payment-service/production  (valid credentials) -> 200 OK, full config
```

Health surfaces backend connectivity as a first-class, monitorable signal; security gates every configuration request behind authentication.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An authentication gate rejects unauthenticated requests before they reach the backend, while a separate health check probes the backend directly">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /payment-service/production</text>

  <line x1="240" y1="42" x2="300" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a43)"/>

  <rect x="310" y="20" width="140" height="45" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">auth check</text>

  <line x1="380" y1="65" x2="380" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a43)"/>

  <rect x="310" y="100" width="140" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="127" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">backend fetch</text>

  <rect x="20" y="100" width="220" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="127" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /actuator/health -- probes backend directly</text>

  <line x1="240" y1="122" x2="300" y2="122" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a43)"/>

  <defs><marker id="a43" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Configuration requests pass through an authentication gate before reaching the backend; health checks probe the backend directly, independent of that gate.

## 5. Runnable example

The scenario: operating a Config Server safely in production, evolving from a health check with no actual backend connectivity verification, to a health indicator that genuinely probes backend reachability, to a combined health-plus-security setup rejecting unauthenticated requests before they ever reach the (potentially unhealthy) backend at all.

### Level 1 — Basic

Show a naive "health check" that reports healthy unconditionally — the gap a real health indicator closes.

```java
public class ConfigHealthLevel1 {
    public static void main(String[] args) {
        FakeHealthCheck healthCheck = new FakeHealthCheck();
        System.out.println("Health status: " + healthCheck.status()); // ALWAYS "UP" -- meaningless
        // Even if the actual Git remote is completely unreachable, this reports healthy.
    }
}

class FakeHealthCheck {
    String status() { return "UP"; } // never actually checks anything
}
```

How to run: `java ConfigHealthLevel1.java`

`status()` returns `"UP"` unconditionally — it never actually verifies the backend is reachable, meaning a real outage would go completely undetected by this "health check."

### Level 2 — Intermediate

Add a health indicator that genuinely probes backend connectivity before reporting status.

```java
public class ConfigHealthLevel2 {
    public static void main(String[] args) {
        Backend healthyBackend = new Backend(true);
        Backend brokenBackend = new Backend(false);

        ConfigServerHealthIndicator indicator1 = new ConfigServerHealthIndicator(healthyBackend);
        System.out.println("Healthy backend -> " + indicator1.health());

        ConfigServerHealthIndicator indicator2 = new ConfigServerHealthIndicator(brokenBackend);
        System.out.println("Broken backend -> " + indicator2.health());
    }
}

class Backend {
    private final boolean reachable;
    Backend(boolean reachable) { this.reachable = reachable; }
    boolean probe(String application, String label) {
        if (!reachable) throw new RuntimeException("connection refused");
        return true;
    }
}

// Mirrors Spring Cloud Config's ConfigServerHealthIndicator: actually attempts to resolve a known repository.
class ConfigServerHealthIndicator {
    private final Backend backend;
    ConfigServerHealthIndicator(Backend backend) { this.backend = backend; }

    String health() {
        try {
            backend.probe("payment-service", "main");
            return "UP";
        } catch (RuntimeException e) {
            return "DOWN: " + e.getMessage();
        }
    }
}
```

How to run: `java ConfigHealthLevel2.java`

`health()` actually calls `backend.probe(...)` — for `healthyBackend` this succeeds and reports `"UP"`; for `brokenBackend` the probe throws, and `health()` catches it and reports `"DOWN"` with the underlying error, giving genuine, actionable signal instead of the meaningless always-`"UP"` from Level 1.

### Level 3 — Advanced

Add authentication gating requests before they even reach the (possibly unhealthy) backend, and show both concerns working together: an unauthenticated request never even triggers a backend probe, while an authenticated one does and correctly reflects backend health.

```java
import java.util.*;

public class ConfigHealthLevel3 {
    public static void main(String[] args) {
        Backend backend = new Backend(true);
        SecuredConfigServer server = new SecuredConfigServer(backend, Set.of("valid-token-abc"));

        System.out.println("Unauthenticated request: " + server.handleRequest("payment-service", "production", null));
        System.out.println("Wrong token: " + server.handleRequest("payment-service", "production", "wrong-token"));
        System.out.println("Valid token: " + server.handleRequest("payment-service", "production", "valid-token-abc"));

        System.out.println("Health check (no auth needed for health): " + new ConfigServerHealthIndicator(backend).health());
    }
}

class Backend {
    private final boolean reachable;
    Backend(boolean reachable) { this.reachable = reachable; }
    boolean probe(String application, String label) {
        if (!reachable) throw new RuntimeException("connection refused");
        return true;
    }
    Map<String, String> fetch(String application, String profile) {
        return Map.of("db.pool.size", "50"); // simplified: real config
    }
}

class ConfigServerHealthIndicator {
    private final Backend backend;
    ConfigServerHealthIndicator(Backend backend) { this.backend = backend; }
    String health() {
        try { backend.probe("payment-service", "main"); return "UP"; }
        catch (RuntimeException e) { return "DOWN: " + e.getMessage(); }
    }
}

// Gates config requests behind authentication BEFORE touching the backend at all.
class SecuredConfigServer {
    private final Backend backend;
    private final Set<String> validTokens;
    SecuredConfigServer(Backend backend, Set<String> validTokens) { this.backend = backend; this.validTokens = validTokens; }

    String handleRequest(String application, String profile, String presentedToken) {
        if (presentedToken == null || !validTokens.contains(presentedToken)) {
            return "401 Unauthorized"; // backend NEVER consulted for an unauthenticated request
        }
        return "200 OK: " + backend.fetch(application, profile);
    }
}
```

How to run: `java ConfigHealthLevel3.java`

`handleRequest` checks `presentedToken` against `validTokens` *before* calling `backend.fetch` at all — an unauthenticated or wrongly-authenticated request is rejected immediately, never triggering any backend access, while a validly authenticated request proceeds to fetch and return the actual configuration; the health check, by contrast, runs independently of this authentication gate, since operators typically need to see backend health even without full config-read credentials.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `handleRequest` calls run with no token, a wrong token, and the correct token respectively.

The first two calls both fail the `presentedToken == null || !validTokens.contains(...)` check and return immediately with `"401 Unauthorized"` — `backend.fetch` is never invoked for either:

```
Unauthenticated request: 401 Unauthorized
Wrong token: 401 Unauthorized
```

The third call presents `"valid-token-abc"`, which *is* in `validTokens`, so the check passes and `backend.fetch("payment-service", "production")` actually runs, returning the configuration map:

```
Valid token: 200 OK: {db.pool.size=50}
```

The final call, `new ConfigServerHealthIndicator(backend).health()`, runs independently of `SecuredConfigServer`'s authentication logic entirely — it directly probes `backend`, which succeeds since it was constructed with `reachable = true`:

```
Health check (no auth needed for health): UP
```

In a real production deployment, this split matters operationally: `/actuator/health` is commonly left more permissively accessible (often on a separate management port, still access-controlled but with different rules) so monitoring and orchestration systems (load balancers, Kubernetes liveness probes) can check it without needing full configuration-read credentials, while the actual `/{application}/{profile}` configuration endpoints require genuine authentication, since they can expose sensitive values.

## 7. Gotchas & takeaways

> Gotcha: configuring the health indicator to probe a specific `{application}/{label}` (as shown in the YAML at the top of this card) means health depends on that *specific* repository/branch being reachable — if the referenced application or label is renamed or removed from the backend, the health check itself starts failing for a reason unrelated to genuine backend connectivity, which can be confusing to diagnose.

> Gotcha: it's easy to secure the `/{application}/{profile}` endpoints while forgetting that `/actuator/refresh`, `/actuator/env`, and other Actuator endpoints on the same Config Server application need their own access control decisions too — securing one part of the surface doesn't automatically secure the rest, and Actuator endpoints in particular can expose or allow changing sensitive server-side state if left open.

- The Config Server's health indicator genuinely probes backend connectivity (Git, Vault, a database) rather than just reporting the application process is running — critical for catching backend outages before they cause confusing downstream config-fetch failures.
- Config Server exposes potentially sensitive configuration over HTTP and needs explicit authentication configured — it is not secure by default.
- Health and security are typically handled with different access rules: health checks often need to remain reachable by monitoring/orchestration tooling, while actual configuration endpoints require genuine credentials.
- Securing configuration endpoints doesn't automatically secure other exposed surfaces (Actuator's `/refresh`, `/env`, and similar) — each needs its own deliberate access-control decision.
