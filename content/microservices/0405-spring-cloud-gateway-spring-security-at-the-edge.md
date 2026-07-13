---
card: microservices
gi: 405
slug: spring-cloud-gateway-spring-security-at-the-edge
title: "Spring Cloud Gateway + Spring Security at the edge"
---

## 1. What it is

**Spring Cloud Gateway** is Spring's reactive API gateway, and combining it with Spring Security turns it into the concrete implementation of [edge authentication at the gateway](0382-edge-authentication-at-the-gateway.md): a single, reactive front door that authenticates every incoming request — via OAuth2 login, a validated bearer token, or another mechanism — before routing it onward to the actual backend service. Because Spring Cloud Gateway is built on Spring WebFlux, its security configuration uses the reactive variant of Spring Security ([Spring Security for reactive (WebFlux) services](0409-spring-security-for-reactive-webflux-services.md)) rather than the servlet-based `SecurityFilterChain` used elsewhere in this section.

## 2. Why & when

You reach for Spring Cloud Gateway with Spring Security specifically when you want centralized, edge-level enforcement in front of many backend services, rather than duplicating authentication logic in every one of them:

- **A single choke point simplifies the system.** Instead of every downstream service independently validating a user's session or token, the gateway does it once, and downstream services can trust what arrives — provided the internal network itself is also secured, per [zero-trust networking](0380-zero-trust-networking.md) (a gateway check is not a substitute for internal security, just a complementary layer).
- **It's the natural home for OAuth2 login** when a system's downstream services are pure resource servers ([OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md)) with no browser-facing login flow of their own — the gateway plays the client role covered in [Spring Security OAuth2 Client](0402-spring-security-oauth2-client-login-token-relay.md).
- **Reactive, non-blocking request handling matters at the edge**, where the gateway may be handling a very high volume of concurrent connections and can't afford a thread-per-request model — this is why Spring Cloud Gateway is WebFlux-based rather than servlet-based.
- **Routing decisions and security decisions often need to be co-located** — a route that requires a specific scope, or that should only forward traffic from an authenticated session, is naturally expressed where the route itself is defined.

You need this the moment you're standing up an API gateway in front of more than a couple of services and want authentication enforced consistently, in one place, rather than trusting every team to implement it correctly and identically.

## 3. Core concept

Think of the gateway as a building's single staffed entrance in front of many separate tenant offices: the entrance guard checks ID once, at the door, and issues a visitor badge; tenants inside don't re-check ID from scratch, they just glance at the badge. Spring Cloud Gateway with Spring Security plays exactly that role — one `SecurityWebFilterChain` at the edge, and routes behind it that assume the badge (an `Authentication`) is already validated by the time a request reaches them.

The essential pieces:

1. **`SecurityWebFilterChain`** — the reactive counterpart to `SecurityFilterChain`, configured via `ServerHttpSecurity` instead of `HttpSecurity`.

```java
@Configuration
@EnableWebFluxSecurity
public class GatewaySecurityConfig {

    @Bean
    public SecurityWebFilterChain gatewaySecurityChain(ServerHttpSecurity http) {
        return http
            .authorizeExchange(ex -> ex
                .pathMatchers("/actuator/health").permitAll()
                .pathMatchers("/orders/**").authenticated()
                .anyExchange().authenticated())
            .oauth2Login(Customizer.withDefaults())          // browser-facing login at the edge
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults())) // for API clients presenting tokens directly
            .build();
    }
}
```

2. **Route configuration** — declared either in `application.yml` or via a `RouteLocator` bean, mapping incoming paths to backend service URIs, independent of (but enforced after) the security chain.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders-route
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - TokenRelay=          # forwards the caller's access token downstream -- see 0406
```

3. **Both `oauth2Login` and `oauth2ResourceServer` can coexist** on the same gateway: browser traffic goes through the login flow and gets a session; API clients that already hold a bearer token skip login and are validated directly as a resource server would — Spring Security picks the right path per request, based on whether credentials are already present.
4. **The gateway is a single point of failure for authentication**, which is precisely why it must be paired with internal defenses, not treated as sufficient alone — this is the same "defense in depth" theme from [microservices security challenges](0378-microservices-security-challenges-larger-attack-surface.md) applied specifically to the edge.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An external request reaches Spring Cloud Gateway, passes through its reactive security web filter chain for authentication and authorization, and only then is routed to the matching backend service; a request that fails the security chain never reaches any route" font-family="sans-serif">
  <rect x="10" y="90" width="100" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">External</text>
  <text x="60" y="127" fill="#8b949e" font-size="8" text-anchor="middle">client</text>

  <rect x="160" y="30" width="200" height="170" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="260" y="50" fill="#e6edf3" font-size="11" text-anchor="middle">Spring Cloud Gateway</text>
  <rect x="180" y="65" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="260" y="83" fill="#e6edf3" font-size="9" text-anchor="middle">SecurityWebFilterChain</text>
  <text x="260" y="97" fill="#8b949e" font-size="8" text-anchor="middle">authenticate + authorize</text>
  <rect x="180" y="120" width="160" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="260" y="138" fill="#e6edf3" font-size="9" text-anchor="middle">Route matching</text>
  <text x="260" y="152" fill="#8b949e" font-size="8" text-anchor="middle">Path=/orders/**</text>

  <rect x="440" y="60" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="485" y="84" fill="#e6edf3" font-size="9" text-anchor="middle">order-service</text>
  <rect x="440" y="130" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="485" y="154" fill="#e6edf3" font-size="9" text-anchor="middle">payment-service</text>

  <rect x="180" y="210" width="160" height="26" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="260" y="228" fill="#f85149" font-size="9" text-anchor="middle">401 / 403 -- never routed</text>

  <line x1="110" y1="115" x2="160" y2="85" stroke="#8b949e" marker-end="url(#gw)"/>
  <line x1="260" y1="105" x2="260" y2="120" stroke="#8b949e" marker-end="url(#gw)"/>
  <line x1="340" y1="80" x2="440" y2="80" stroke="#6db33f" marker-end="url(#gw)"/>
  <line x1="340" y1="140" x2="440" y2="150" stroke="#6db33f" marker-end="url(#gw)"/>
  <line x1="260" y1="105" x2="260" y2="210" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#gw)"/>

  <defs>
    <marker id="gw" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Security runs before routing at the edge — a request that fails authentication or authorization never reaches route matching, let alone a backend service.

## 5. Runnable example

Scenario: a gateway in front of `order-service` and `payment-service`. We model route-only forwarding with no security first, then add an edge authentication check before routing, then add per-route authorization so different paths require different scopes — mirroring `authorizeExchange`'s path-specific rules.

### Level 1 — Basic

```java
// File: RouteOnlyNoSecurity.java -- a gateway that ONLY routes, with no
// security check at all -- the naive starting point this topic exists to fix.
import java.util.*;

public class RouteOnlyNoSecurity {
    static final Map<String, String> ROUTES = Map.of(
            "/orders", "order-service",
            "/payments", "payment-service"
    );

    static String routeRequest(String path) {
        for (Map.Entry<String, String> route : ROUTES.entrySet()) {
            if (path.startsWith(route.getKey())) {
                return "-> forwarded to " + route.getValue() + " (NO security check performed)";
            }
        }
        return "404 Not Found";
    }

    public static void main(String[] args) {
        System.out.println(routeRequest("/orders/42"));
        System.out.println(routeRequest("/payments/99")); // ANYONE reaches payment-service, unauthenticated
    }
}
```

How to run: `java RouteOnlyNoSecurity.java`

`routeRequest` matches a path prefix and forwards, with no notion of "who is calling" at all — every request, authenticated or not, reaches `payment-service` identically. This is the exact gap Spring Cloud Gateway's `SecurityWebFilterChain` closes: routing logic and security logic are separate concerns, but security must run *first*.

### Level 2 — Intermediate

```java
// File: SecurityBeforeRouting.java -- adds an edge authentication check
// that runs BEFORE route matching, mirroring authorizeExchange(...).anyExchange()
// .authenticated() sitting in front of the gateway's route resolution.
import java.util.*;

public class SecurityBeforeRouting {
    record Authentication(String principal, Set<String> authorities) {}

    static final Map<String, String> VALID_TOKENS = Map.of("token-alice", "alice", "token-bob", "bob");
    static final Map<String, String> ROUTES = Map.of("/orders", "order-service", "/payments", "payment-service");

    static Authentication authenticate(String bearerToken) {
        String principal = VALID_TOKENS.get(bearerToken);
        return principal == null ? null : new Authentication(principal, Set.of("SCOPE_read"));
    }

    static String handleRequest(String path, String bearerToken) {
        Authentication auth = authenticate(bearerToken);
        if (auth == null) {
            return "401 Unauthorized -- rejected BEFORE route matching, " + path + " never reached";
        }
        for (Map.Entry<String, String> route : ROUTES.entrySet()) {
            if (path.startsWith(route.getKey())) {
                return "-> forwarded to " + route.getValue() + " as authenticated user '" + auth.principal() + "'";
            }
        }
        return "404 Not Found";
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("/payments/99", "token-alice"));
        System.out.println(handleRequest("/payments/99", "invalid-token"));
    }
}
```

How to run: `java SecurityBeforeRouting.java`

`handleRequest` now calls `authenticate` first; only a request that produces a non-null `Authentication` ever reaches the routing loop, mirroring how `SecurityWebFilterChain` sits ahead of Spring Cloud Gateway's route-matching filters in the reactive filter chain. The rejected call never even evaluates `ROUTES`, exactly matching the diagram's dashed "never routed" path — this is the structural fix Level 1 was missing.

### Level 3 — Advanced

```java
// File: PerRoutePathAuthorization.java -- adds PER-ROUTE authorization: not
// just "authenticated", but "authenticated AND holds the scope this specific
// path requires" -- mirroring multiple .pathMatchers(...) rules with
// DIFFERENT required authorities inside authorizeExchange(...).
import java.util.*;

public class PerRoutePathAuthorization {
    record Authentication(String principal, Set<String> authorities) {}
    record RouteRule(String pathPrefix, String backend, String requiredAuthority) {}

    static final Map<String, Authentication> TOKEN_STORE = Map.of(
            "token-alice", new Authentication("alice", Set.of("SCOPE_orders:read")),
            "token-ops",   new Authentication("ops-bot", Set.of("SCOPE_orders:read", "SCOPE_payments:write"))
    );

    static final List<RouteRule> ROUTES = List.of(
            new RouteRule("/orders", "order-service", "SCOPE_orders:read"),
            new RouteRule("/payments", "payment-service", "SCOPE_payments:write")
    );

    static String handleRequest(String path, String bearerToken) {
        Authentication auth = TOKEN_STORE.get(bearerToken);
        if (auth == null) return "401 Unauthorized -- no valid credentials presented";

        for (RouteRule route : ROUTES) {
            if (path.startsWith(route.pathPrefix())) {
                if (!auth.authorities().contains(route.requiredAuthority())) {
                    return "403 Forbidden -- '" + auth.principal() + "' lacks " + route.requiredAuthority()
                            + " required for " + route.pathPrefix() + "/**";
                }
                return "-> forwarded to " + route.backend() + " as '" + auth.principal() + "'";
            }
        }
        return "404 Not Found";
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("/orders/42", "token-alice"));   // has orders:read -- allowed
        System.out.println(handleRequest("/payments/1", "token-alice"));  // lacks payments:write -- denied
        System.out.println(handleRequest("/payments/1", "token-ops"));    // has payments:write -- allowed
    }
}
```

How to run: `java PerRoutePathAuthorization.java`

`ROUTES` now carries a `requiredAuthority` per path prefix, mirroring separate `.pathMatchers("/orders/**").hasAuthority("SCOPE_orders:read")` and `.pathMatchers("/payments/**").hasAuthority("SCOPE_payments:write")` rules inside a single `authorizeExchange` block. Alice authenticates successfully for both requests (she holds a valid token), but is only *authorized* for `/orders/**` — her call to `/payments/1` is rejected with `403`, distinct from an unauthenticated `401`, exactly matching the distinction Spring Security enforces between "who are you" and "what are you allowed to do." The `ops-bot` token, holding the payments scope, succeeds where Alice's did not.

## 6. Walkthrough

Trace `PerRoutePathAuthorization.main`'s second call: `handleRequest("/payments/1", "token-alice")`. **First**, `TOKEN_STORE.get("token-alice")` returns alice's `Authentication`, whose `authorities` is `{"SCOPE_orders:read"}` — so the `auth == null` check fails to trigger, and execution continues past authentication (alice *is* a known caller).

**Next**, the loop over `ROUTES` begins. The first `RouteRule` has `pathPrefix = "/orders"`; `"/payments/1".startsWith("/orders")` is `false`, so this rule is skipped.

**Then**, the second `RouteRule` has `pathPrefix = "/payments"`; `"/payments/1".startsWith("/payments")` is `true`, so this rule matches. Inside, `auth.authorities().contains("SCOPE_payments:write")` is checked against alice's authorities (`{"SCOPE_orders:read"}`), which does **not** contain `"SCOPE_payments:write"` — so the condition `!auth.authorities().contains(...)` is `true`, and the method returns a `403 Forbidden` message naming exactly which authority was missing and for which route.

**Finally**, `main` prints that `403` message. Compare this to the third call, `handleRequest("/payments/1", "token-ops")`: the same route matches, but `ops-bot`'s authorities *do* include `"SCOPE_payments:write"`, so the authorization check passes and the request is forwarded.

```
-> forwarded to order-service as 'alice'
403 Forbidden -- 'alice' lacks SCOPE_payments:write required for /payments/**
-> forwarded to payment-service as 'ops-bot'
```

Sample HTTP shapes at the gateway:

```
GET /payments/1 HTTP/1.1
Authorization: Bearer token-alice

HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "access_denied", "message": "insufficient_scope: SCOPE_payments:write required"}
```

```
GET /payments/1 HTTP/1.1
Authorization: Bearer token-ops

HTTP/1.1 200 OK   (forwarded internally to payment-service)
```

## 7. Gotchas & takeaways

> Treating the gateway's authentication check as the *only* security boundary is a common and dangerous mistake: if any backend service is reachable directly (a misconfigured network policy, an internal debugging port left open, a service mesh misconfiguration), an attacker who reaches it bypasses the gateway entirely. The gateway centralizes convenience, not the whole security model — internal services still need their own checks, per [zero-trust networking](0380-zero-trust-networking.md).

- Spring Cloud Gateway's security configuration is reactive (`ServerHttpSecurity`, `SecurityWebFilterChain`) because the gateway itself runs on WebFlux — see [Spring Security for reactive (WebFlux) services](0409-spring-security-for-reactive-webflux-services.md) for the general reactive security model this builds on.
- Security must run before routing, not after — a request that fails authentication or authorization should never reach route matching, let alone a backend service.
- `oauth2Login` (for browsers) and `oauth2ResourceServer` (for API clients presenting tokens directly) can coexist on the same gateway security chain, letting one edge component serve both traffic shapes.
- Per-route authorization (different required scopes for different paths) belongs at the edge specifically because it's the one place that sees every route's traffic and can enforce consistent policy without trusting every backend team to replicate it correctly.
- Once the gateway authenticates a caller, forwarding that identity onward — rather than making downstream services re-authenticate from scratch — is the job of [token relay filter in gateway / WebClient](0406-token-relay-filter-in-gateway-webclient.md), covered next.
