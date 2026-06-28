---
card: spring-boot
gi: 180
slug: securing-endpoints
title: Securing endpoints
---

## 1. What it is

Spring Boot Actuator endpoints can expose sensitive operational data (env, beans, heapdump) that should never be public. **Securing endpoints** means using Spring Security to require authentication and/or role-based authorization before those endpoints respond. When `spring-security` is on the classpath alongside `spring-boot-starter-actuator`, a `SecurityFilterChain` for the management endpoints is auto-configured — you extend it with your own rules.

## 2. Why & when

Without security, any client that can reach your server can:
- Read all environment properties including secrets (`/actuator/env`).
- Download a heap dump containing passwords and API keys (`/actuator/heapdump`).
- Change log levels (`/actuator/loggers` POST) or shut the service down (`/actuator/shutdown`).

**Always** secure Actuator endpoints in production. The minimum viable approach:
1. Restrict to a management port on an internal network (not routed to the public internet).
2. Require HTTP Basic or token auth for any publicly reachable management endpoint.

## 3. Core concept

Spring Boot does **not** auto-lock Actuator behind auth when Spring Security is added — it leaves your `SecurityFilterChain` in control. You must add the rules yourself.

Typical pattern: add a `SecurityFilterChain` bean that matches `EndpointRequest.toAnyEndpoint()` and requires a role:

```java
@Bean
SecurityFilterChain actuatorSecurity(HttpSecurity http) throws Exception {
    http.securityMatcher(EndpointRequest.toAnyEndpoint())
        .authorizeHttpRequests(auth -> auth
            .requestMatchers(EndpointRequest.to(HealthEndpoint.class, InfoEndpoint.class)).permitAll()
            .anyRequest().hasRole("ACTUATOR"))
        .httpBasic(withDefaults());
    return http.build();
}
```

Key Spring Security matchers for Actuator:
- `EndpointRequest.toAnyEndpoint()` — matches all Actuator paths.
- `EndpointRequest.to(HealthEndpoint.class)` — matches `/actuator/health` only.
- `EndpointRequest.toLinks()` — matches the `/actuator` discovery link.

Alternative: use `management.server.port` to isolate Actuator traffic at the network layer, removing the need for HTTP auth on those endpoints (the network is the auth boundary).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Incoming request hits Spring Security filter chain; health and info pass, others require ACTUATOR role">
  <!-- Request -->
  <rect x="10" y="85" width="100" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP Request</text>

  <!-- Arrow -->
  <line x1="113" y1="105" x2="170" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sca)"/>

  <!-- Security Filter Chain -->
  <rect x="175" y="55" width="200" height="105" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="275" y="76" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">SecurityFilterChain</text>
  <text x="275" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">EndpointRequest.toAnyEndpoint()</text>

  <!-- Rule 1: health/info permit -->
  <rect x="188" y="100" width="174" height="22" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="275" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">/health /info → permitAll()</text>

  <!-- Rule 2: others require role -->
  <rect x="188" y="128" width="174" height="22" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="275" y="143" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/* → hasRole("ACTUATOR")</text>

  <!-- Arrow to endpoints -->
  <line x1="378" y1="90" x2="438" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#scb)"/>
  <rect x="442" y="48" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="562" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">/health /info — 200 OK (no auth needed)</text>

  <!-- Arrow to blocked -->
  <line x1="378" y1="130" x2="438" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#scb)"/>
  <rect x="442" y="118" width="240" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="562" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/metrics /env — 401 or 403 without role</text>

  <!-- Arrow to auth success -->
  <line x1="378" y1="150" x2="438" y2="165" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#scb)"/>
  <rect x="442" y="154" width="240" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="562" y="172" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/metrics with ACTUATOR role → 200 OK</text>

  <defs>
    <marker id="sca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="scb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`SecurityFilterChain` sits in front of all Actuator endpoints; rules allow health/info publicly and lock everything else behind a role.

## 5. Runnable example

```java
// ActuatorSecurityDemo.java — simulates the security filter chain for Actuator endpoints
// How to run: java ActuatorSecurityDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-security; declare a SecurityFilterChain bean

import java.util.*;

public class ActuatorSecurityDemo {

    enum Role { ANONYMOUS, ACTUATOR, ADMIN }

    record Request(String path, String method, Role caller) {}

    // Simulates the SecurityFilterChain rules
    static int authorize(Request req) {
        // Rule 1: /health and /info are public
        if (req.path().equals("/actuator/health") || req.path().equals("/actuator/info")) {
            return 200;
        }
        // Rule 2: POST /actuator/shutdown requires ADMIN
        if (req.path().equals("/actuator/shutdown") && "POST".equals(req.method())) {
            return req.caller() == Role.ADMIN ? 200 : 403;
        }
        // Rule 3: all other actuator endpoints require ACTUATOR role
        if (req.path().startsWith("/actuator/")) {
            return (req.caller() == Role.ACTUATOR || req.caller() == Role.ADMIN) ? 200 : 401;
        }
        // Non-actuator paths: not handled here
        return 200;
    }

    static void check(Request req) {
        int status = authorize(req);
        String icon = status == 200 ? "✓" : (status == 401 ? "✗(401)" : "✗(403)");
        System.out.printf("  %s %-10s %-40s caller=%-12s → HTTP %d%n",
                icon, req.method(), req.path(), req.caller(), status);
    }

    public static void main(String[] args) {
        System.out.println("=== Actuator Security Demo ===\n");
        System.out.println("SecurityFilterChain rules:");
        System.out.println("  /health, /info          → permitAll()");
        System.out.println("  /shutdown (POST)         → hasRole(ADMIN)");
        System.out.println("  /actuator/**             → hasRole(ACTUATOR)");
        System.out.println();

        List<Request> requests = List.of(
            new Request("/actuator/health",    "GET",  Role.ANONYMOUS),
            new Request("/actuator/info",      "GET",  Role.ANONYMOUS),
            new Request("/actuator/metrics",   "GET",  Role.ANONYMOUS),
            new Request("/actuator/metrics",   "GET",  Role.ACTUATOR),
            new Request("/actuator/env",       "GET",  Role.ACTUATOR),
            new Request("/actuator/heapdump",  "GET",  Role.ACTUATOR),
            new Request("/actuator/loggers/com.example", "POST", Role.ACTUATOR),
            new Request("/actuator/shutdown",  "POST", Role.ACTUATOR),
            new Request("/actuator/shutdown",  "POST", Role.ADMIN)
        );

        requests.forEach(ActuatorSecurityDemo::check);

        System.out.println("\n--- Spring Boot config snippet ---");
        System.out.println("""
                @Bean
                SecurityFilterChain actuatorSecurity(HttpSecurity http) throws Exception {
                    http.securityMatcher(EndpointRequest.toAnyEndpoint())
                        .authorizeHttpRequests(auth -> auth
                            .requestMatchers(EndpointRequest.to(HealthEndpoint.class,
                                                               InfoEndpoint.class)).permitAll()
                            .requestMatchers(EndpointRequest.to(ShutdownEndpoint.class))
                                            .hasRole("ADMIN")
                            .anyRequest().hasRole("ACTUATOR"))
                        .httpBasic(withDefaults());
                    return http.build();
                }""");
    }
}
```

**How to run:** `java ActuatorSecurityDemo.java`

## 6. Walkthrough

- **`Rule 1`**: health and info return 200 for anonymous callers — these are safe to expose publicly (health has no secrets; info has build metadata).
- **`Rule 2`**: shutdown requires ADMIN — ACTUATOR role alone is insufficient. This prevents ops users from accidentally stopping production.
- **`Rule 3`**: all other actuator endpoints require at least ACTUATOR role — anonymous callers get 401 (not 403, so they know auth is needed).
- The Spring Boot config snippet shows `EndpointRequest.to(...)` matchers — these are Spring Security matchers that know about endpoint bean types, not raw URL strings. They remain correct if `management.endpoints.web.base-path` changes.
- `httpBasic(withDefaults())` is fine for internal services; replace with JWT/OAuth2 for externally reachable endpoints.

## 7. Gotchas & takeaways

> If you define **any** `SecurityFilterChain` bean, Spring Boot's default security auto-config backs off entirely. Make sure your `actuatorSecurity` chain covers actuator paths — the main application chain won't automatically protect them.

> `EndpointRequest.toAnyEndpoint()` uses the configured base path (`management.endpoints.web.base-path`). Hardcoding `/actuator/**` in a raw `antMatcher` breaks when you change the base path.

- Use `EndpointRequest.to(HealthEndpoint.class)` not `"/actuator/health"` — Spring resolves the path from config.
- For Kubernetes probes: allow `/actuator/health/liveness` and `/actuator/health/readiness` without auth; block the parent `/actuator/health` or show only `status` field.
- `management.server.port` network isolation is **better than HTTP auth** — attacker cannot reach port 8081 even without credentials.
- Add `management.endpoint.health.show-details=when-authorized` to show component details only to authenticated users.
- `spring.security.user.name/password` sets the single in-memory user — sufficient for simple internal tool access.
